#!/usr/bin/env python3
"""Restore pinned evaluation datasets from verified GitHub Release archives.

Python 3.9+; no Git LFS or model dependencies. Run without arguments to restore
only this repository's nine mirrored datasets. --list also shows external sources.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import errno
import hashlib
import http.client
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tarfile
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from tls import create_ssl_context, certificate_error, certificate_error_message


class DownloadError(Exception):
    """A dataset could not be downloaded or restored safely."""


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def install_staged_file(source, destination, item):
    """Install verified staged bytes, including when the cache is on another filesystem."""
    try:
        source.replace(destination)
        return
    except OSError as exc:
        if exc.errno != errno.EXDEV:
            raise
    descriptor, filename = tempfile.mkstemp(prefix=".dataset-install-", suffix=".downloading",
                                            dir=destination.parent)
    temporary = Path(filename)
    try:
        with os.fdopen(descriptor, "wb") as output:
            with source.open("rb") as stream:
                shutil.copyfileobj(stream, output, length=1024 * 1024)
        if temporary.stat().st_size != item["size"] or sha256(temporary) != item["sha256"]:
            raise DownloadError("Copied dataset file failed SHA-256 verification: " + str(destination))
        # The temporary file shares the destination's filesystem, so replacement stays atomic.
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("Invalid relative path in manifest")
    path = PurePosixPath(value)
    if (not path.parts or path.is_absolute() or path.as_posix() != value
            or any(part.startswith(".") for part in path.parts)
            or any(ord(char) < 32 for char in value)):
        raise ValueError("Unsafe relative path in manifest: " + repr(value))
    return path


def safe_path(root, value):
    path = Path(root).joinpath(*relative_path(value).parts)
    if not path.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError("Path leaves its directory: " + repr(value))
    return path


def dataset_target(root, key, relative):
    """Do not replace a user's symlinks or write through linked dataset folders."""
    path = safe_path(root, key + "/" + relative)
    current = Path(root)
    for part in relative_path(key + "/" + relative).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Dataset target contains a symlink: " + str(current))
    if path.exists() and not path.is_file():
        raise ValueError("Dataset file target is not a regular file: " + str(path))
    return path


def validate_digest_and_size(item, allow_empty=False):
    minimum = 0 if allow_empty else 1
    if (not isinstance(item, dict) or not isinstance(item.get("size"), int)
            or isinstance(item["size"], bool) or item["size"] < minimum):
        raise ValueError("Invalid file size in manifest")
    if not isinstance(item.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
        raise ValueError("Every file and asset must have a lowercase SHA-256")


def validate_manifest(manifest):
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("Unsupported manifest schema_version; expected 1")
    repository = manifest.get("repository", "")
    if (not isinstance(repository, str)
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)
            or any(part in (".", "..") for part in repository.split("/"))):
        raise ValueError("Invalid GitHub repository in manifest")
    tag = manifest.get("release_tag")
    if not isinstance(tag, str) or not tag or any(ord(char) < 32 for char in tag):
        raise ValueError("Invalid release_tag in manifest")
    datasets = manifest.get("datasets")
    if not isinstance(datasets, dict) or not datasets:
        raise ValueError("Manifest must contain datasets")
    assets = set()
    for key, dataset in datasets.items():
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", key):
            raise ValueError("Invalid dataset key")
        if not isinstance(dataset, dict) or dataset.get("storage") not in ("release", "external"):
            raise ValueError("Invalid dataset storage: " + key)
        files = dataset.get("files", [])
        if not isinstance(files, list) or (dataset["storage"] == "release" and not files):
            raise ValueError("Dataset needs a file manifest: " + key)
        paths = set()
        for item in files:
            if not isinstance(item, dict):
                raise ValueError("Invalid dataset file entry")
            path = relative_path(item.get("path")).as_posix()
            if path in paths:
                raise ValueError("Repeated dataset file: " + key + "/" + path)
            paths.add(path)
            validate_digest_and_size(item, allow_empty=True)
        # No file may also be the parent directory of another file.
        for path in paths:
            if any(parent.as_posix() in paths for parent in PurePosixPath(path).parents if parent.as_posix() != "."):
                raise ValueError("Conflicting dataset file paths: " + path)
        if dataset["storage"] == "external":
            if not isinstance(dataset.get("source"), str) or not dataset["source"]:
                raise ValueError("External dataset needs its original source URL: " + key)
            continue
        archive = dataset.get("archive")
        if not isinstance(archive, dict) or archive.get("format") != "tar.gz":
            raise ValueError("Dataset archive must be tar.gz: " + key)
        validate_digest_and_size(archive)
        parts = archive.get("parts")
        if not isinstance(parts, list) or not parts:
            raise ValueError("Dataset archive has no Release assets: " + key)
        total = 0
        for part in parts:
            validate_digest_and_size(part)
            name = part.get("asset")
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
                raise ValueError("Unsafe Release asset name")
            if name in assets:
                raise ValueError("Repeated Release asset: " + name)
            assets.add(name)
            total += part["size"]
        if total != archive["size"]:
            raise ValueError("Release asset sizes do not sum to archive size: " + key)
    return manifest


def asset_url(repository, tag, asset):
    return "https://github.com/{}/releases/download/{}/{}".format(
        repository, urllib.parse.quote(tag, safe=""), urllib.parse.quote(asset, safe=""))


class StripAuthorizationRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        redirected = super().redirect_request(request, response, code, message, headers, new_url)
        if redirected is not None:
            # Never forward GitHub credentials to the release CDN or another host.
            redirected.remove_header("Authorization")
        return redirected


class Downloader:
    def __init__(self, manifest, root, cache_dir=None, workers=2, keep_cache=False,
                 token=None, timeout=60, ca_bundle=None):
        self.manifest = validate_manifest(manifest)
        self.root = Path(root).resolve()
        cache_root = Path(cache_dir).expanduser().resolve() if cache_dir else self.root / ".downloads"
        namespace = hashlib.sha256((manifest["repository"] + "\0" + manifest["release_tag"]).encode()).hexdigest()[:16]
        self.cache = safe_path(cache_root, namespace)
        self.workers = max(1, workers)
        self.keep_cache = keep_cache
        if token and any(ord(char) <= 32 or ord(char) >= 127 for char in token):
            raise ValueError("GitHub token must contain printable ASCII without whitespace")
        self.token = token
        self.timeout = timeout
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=create_ssl_context(ca_bundle)),
            StripAuthorizationRedirect())
        self._api_assets = None
        self._api_lock = threading.Lock()
        # Preflight target paths before network access or filesystem changes.
        for key, dataset in manifest["datasets"].items():
            for item in dataset.get("files", []):
                dataset_target(self.root, key, item["path"])
            if dataset["storage"] == "release":
                safe_path(self.cache, key + ".tar.gz")
                for part in dataset["archive"]["parts"]:
                    safe_path(self.cache, part["asset"])
                    safe_path(self.cache, part["asset"] + ".partial")

    @staticmethod
    def matches(path, item):
        return path.is_file() and path.stat().st_size == item["size"] and sha256(path) == item["sha256"]

    def _request(self, asset, offset):
        headers = {"User-Agent": "emotion-recognition-datasets-downloader/1", "Accept-Encoding": "identity"}
        if offset:
            headers["Range"] = "bytes={}-".format(offset)
        url = asset_url(self.manifest["repository"], self.manifest["release_tag"], asset)
        if self.token:
            url = self._authenticated_asset(asset)
            headers["Authorization"] = "Bearer " + self.token
            headers["Accept"] = "application/octet-stream"
        return urllib.request.Request(url, headers=headers)

    def _authenticated_asset(self, asset):
        with self._api_lock:
            if self._api_assets is None:
                url = "https://api.github.com/repos/{}/releases/tags/{}".format(
                    self.manifest["repository"], urllib.parse.quote(self.manifest["release_tag"], safe=""))
                request = urllib.request.Request(url, headers={
                    "User-Agent": "emotion-recognition-datasets-downloader/1",
                    "Accept": "application/vnd.github+json", "Authorization": "Bearer " + self.token})
                with self.opener.open(request, timeout=self.timeout) as response:
                    release = json.load(response)
                self._api_assets = {item["name"]: item["url"] for item in release.get("assets", [])}
            if asset not in self._api_assets:
                raise DownloadError("Release asset not found: " + asset)
            url = self._api_assets[asset]
            expected = "https://api.github.com/repos/{}/releases/assets/".format(self.manifest["repository"])
            if not isinstance(url, str) or not url.startswith(expected) or not url[len(expected):].isdigit():
                raise DownloadError("Unsafe GitHub API asset URL")
            return url

    def download_part(self, part):
        target = safe_path(self.cache, part["asset"])
        partial = safe_path(self.cache, part["asset"] + ".partial")
        if self.matches(target, part):
            return target
        self.cache.mkdir(parents=True, exist_ok=True)
        if target.exists():
            target.unlink()
        last_error = None
        for attempt in range(3):
            if attempt:
                time.sleep(min(2 ** (attempt - 1), 4))
            try:
                size = partial.stat().st_size if partial.exists() else 0
                if size > part["size"]:
                    partial.unlink()
                    size = 0
                if size == part["size"]:
                    if self.matches(partial, part):
                        partial.replace(target)
                        return target
                    partial.unlink()
                    size = 0
                print("  fetching {} (resume: {:,} bytes)".format(part["asset"], size), flush=True)
                request = self._request(part["asset"], size)
                with self.opener.open(request, timeout=self.timeout) as response:
                    status = response.getcode()
                    if status == 206:
                        match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", response.headers.get("Content-Range", ""))
                        if (not match or int(match[1]) != size or int(match[3]) != part["size"]
                                or not size <= int(match[2]) < part["size"]):
                            raise DownloadError("Invalid Content-Range for " + part["asset"])
                    elif status == 200:
                        # A server may ignore Range: discard the old prefix and start over.
                        size = 0
                    else:
                        raise DownloadError("Unexpected HTTP status {} for {}".format(status, part["asset"]))
                    with partial.open("ab" if status == 206 and size else "wb") as stream:
                        for chunk in iter(lambda: response.read(1024 * 1024), b""):
                            size += len(chunk)
                            if size > part["size"]:
                                raise DownloadError("Release asset exceeds its recorded size: " + part["asset"])
                            stream.write(chunk)
                if partial.stat().st_size != part["size"]:
                    raise DownloadError("Incomplete release asset: " + part["asset"])
                if sha256(partial) != part["sha256"]:
                    partial.unlink()
                    raise DownloadError("SHA-256 mismatch: " + part["asset"])
                partial.replace(target)
                print("  downloaded and verified " + part["asset"], flush=True)
                return target
            except urllib.error.HTTPError as exc:
                last_error = "HTTP {} for {}".format(exc.code, part["asset"])
                if exc.code == 416:
                    if self.matches(partial, part):
                        partial.replace(target)
                        return target
                    if partial.exists():
                        partial.unlink()
                elif exc.code not in (408, 429) and exc.code < 500:
                    break
            except (OSError, urllib.error.URLError, http.client.HTTPException, DownloadError) as exc:
                if certificate_error(exc):
                    raise DownloadError(certificate_error_message(exc)) from exc
                if certificate_error(exc):
                    raise DownloadError(certificate_error_message(exc)) from exc
                last_error = str(exc)
                if partial.exists() and partial.stat().st_size > part["size"]:
                    partial.unlink()
        raise DownloadError("Unable to download {} after at most 3 attempts: {}".format(part["asset"], last_error))

    def dataset_matches(self, key, report=False):
        dataset = self.manifest["datasets"][key]
        missing = []
        for item in dataset.get("files", []):
            if not self.matches(dataset_target(self.root, key, item["path"]), item):
                missing.append(item["path"])
                if not report:
                    return False
        if report:
            if missing:
                print("  MISSING OR INVALID: {} of {:,} files; {}".format(
                    len(missing), len(dataset.get("files", [])), ", ".join(missing[:5])), flush=True)
            else:
                print("  OK: {:,} files".format(len(dataset.get("files", []))), flush=True)
        return not missing and bool(dataset.get("files"))

    def get_archive(self, key, item):
        archive = safe_path(self.cache, key + ".tar.gz")
        if self.matches(archive, item):
            return archive
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            parts = list(pool.map(self.download_part, item["parts"]))
        temporary = safe_path(self.cache, key + ".tar.gz.assembling")
        digest = hashlib.sha256()
        size = 0
        try:
            with temporary.open("wb") as output:
                for part in parts:
                    with part.open("rb") as stream:
                        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                            output.write(chunk)
                            digest.update(chunk)
                            size += len(chunk)
            if size != item["size"] or digest.hexdigest() != item["sha256"]:
                raise DownloadError("Reassembled archive failed SHA-256 verification: " + key)
            temporary.replace(archive)
        finally:
            if temporary.exists():
                temporary.unlink()
        return archive

    def extract_verified(self, key, archive):
        dataset = self.manifest["datasets"][key]
        expected = {item["path"]: item for item in dataset["files"]}
        self.cache.mkdir(parents=True, exist_ok=True)
        # Stage and verify the entire archive before touching any existing dataset file.
        with tempfile.TemporaryDirectory(prefix="extract-" + key + "-", dir=self.cache) as temporary:
            stage = Path(temporary)
            seen = set()
            try:
                with tarfile.open(archive, "r:gz") as package:
                    for member in package:
                        name = relative_path(member.name).as_posix()
                        if not member.isfile() or member.issym() or member.islnk():
                            raise DownloadError("Archive contains a non-regular file: " + name)
                        if name not in expected:
                            raise DownloadError("Archive contains an unexpected file: " + name)
                        if name in seen:
                            raise DownloadError("Archive contains a repeated file: " + name)
                        item = expected[name]
                        if member.size != item["size"]:
                            raise DownloadError("Archive member size mismatch: " + name)
                        destination = safe_path(stage, name)
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        digest = hashlib.sha256()
                        size = 0
                        stream = package.extractfile(member)
                        if stream is None:
                            raise DownloadError("Archive member cannot be read: " + name)
                        with stream, destination.open("xb") as output:
                            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                                size += len(chunk)
                                if size > item["size"]:
                                    raise DownloadError("Archive member exceeds its recorded size: " + name)
                                output.write(chunk)
                                digest.update(chunk)
                        if size != item["size"] or digest.hexdigest() != item["sha256"]:
                            raise DownloadError("Archive member failed SHA-256 verification: " + name)
                        seen.add(name)
                if seen != set(expected):
                    raise DownloadError("Archive is missing {:,} expected file(s): {}".format(
                        len(set(expected) - seen), ", ".join(sorted(set(expected) - seen)[:5])))
            except (tarfile.TarError, EOFError) as exc:
                raise DownloadError("Invalid dataset archive: " + key + ": " + str(exc)) from exc
            # Validate all final paths again, including any newly appeared symlinks, before replacing files.
            destinations = {name: dataset_target(self.root, key, name) for name in expected}
            for name, item in expected.items():
                destination = destinations[name]
                if self.matches(destination, item):
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                safe_path(self.root, key + "/" + name)
                install_staged_file(stage / name, destination, item)
        print("  restored and verified: {} ({:,} files)".format(key, len(expected)), flush=True)

    def restore_dataset(self, key):
        if self.dataset_matches(key):
            print("  already verified: " + key, flush=True)
            return
        dataset = self.manifest["datasets"][key]
        print("  downloading {} ({:.3f} GB archive)".format(key, dataset["archive"]["size"] / 1e9), flush=True)
        archive = self.get_archive(key, dataset["archive"])
        self.extract_verified(key, archive)
        if not self.keep_cache:
            archive.unlink()
            for part in dataset["archive"]["parts"]:
                cached = safe_path(self.cache, part["asset"])
                if cached.exists():
                    cached.unlink()

    def run(self, keys, verify_only=False):
        external = [key for key in keys if self.manifest["datasets"][key]["storage"] == "external"
                    and (not verify_only or not self.manifest["datasets"][key].get("files"))]
        if external:
            detail = "; ".join("{}: {}".format(key, self.manifest["datasets"][key]["source"]) for key in external)
            raise DownloadError("External datasets are downloaded from their original sources, not mirrored here. "
                                "Use the main project's download_data.py --dataset NAME --source, or setup_datasets.py "
                                "with the external dataset key. " + detail)
        valid = True
        for key in keys:
            print(self.manifest["datasets"][key].get("name", key), flush=True)
            if verify_only:
                valid = self.dataset_matches(key, report=True) and valid
            else:
                self.restore_dataset(key)
        return valid


def selected_keys(manifest, wanted, all_datasets=False, list_only=False):
    datasets = manifest["datasets"]
    if wanted == ["all"] or all_datasets:
        return list(datasets)
    if wanted and wanted != ["mirrors"]:
        if len(set(wanted)) != len(wanted):
            raise ValueError("Repeated dataset keys are not allowed")
        unknown = [key for key in wanted if key not in datasets]
        if unknown:
            raise ValueError("Unknown datasets: " + ", ".join(unknown))
        return wanted
    if list_only and not wanted:
        return list(datasets)
    return [key for key, dataset in datasets.items() if dataset["storage"] == "release"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("datasets", nargs="*", metavar="DATASET", help="dataset keys; default: mirrored datasets")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--all", action="store_true", help="select all datasets, including original external sources")
    selection.add_argument("--mirrors", action="store_true", help="select only this repository's mirrored datasets")
    parser.add_argument("--list", action="store_true", help="list datasets, sizes and storage without downloading")
    parser.add_argument("--verify-only", action="store_true", help="verify local files without network access")
    parser.add_argument("--workers", type=int, default=2, help="parallel Release downloads (default: 2)")
    parser.add_argument("--cache-dir", type=Path, help="Release cache; default: .downloads beside this script")
    parser.add_argument("--keep-cache", action="store_true", help="keep downloaded archives and parts after restoration")
    parser.add_argument("--token-env", default="GITHUB_TOKEN", help="optional GitHub API token environment variable")
    parser.add_argument("--ca-bundle", type=Path, help="additional trusted CA certificates in PEM format")
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("manifest.json"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent, help="dataset root; default: this script's directory")
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    if args.datasets and (args.all or args.mirrors):
        parser.error("Use dataset keys or a selection flag, not both")
    try:
        manifest = validate_manifest(json.loads(args.manifest.read_text(encoding="utf-8")))
        wanted = ["mirrors"] if args.mirrors else args.datasets
        keys = selected_keys(manifest, wanted, args.all, args.list)
        if args.list:
            for key in keys:
                dataset = manifest["datasets"][key]
                size = sum(item["size"] for item in dataset.get("files", []))
                print("{}\t{}\t{:.3f} GB\t{}".format(key, dataset["storage"].upper(), size / 1e9, dataset.get("source", "")))
            return 0
        downloader = Downloader(manifest, args.root, args.cache_dir, args.workers,
                                args.keep_cache, os.environ.get(args.token_env), ca_bundle=args.ca_bundle)
        return 0 if downloader.run(keys, args.verify_only) else 1
    except (OSError, ValueError, DownloadError, tarfile.TarError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted. Run the same command again to resume.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
