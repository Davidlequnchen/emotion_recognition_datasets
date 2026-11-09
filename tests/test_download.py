"""Tiny HTTP/archive regression tests; no datasets or accounts are downloaded."""
from contextlib import contextmanager
import copy
import errno
import hashlib
import http.server
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import threading
import unittest
from unittest import mock
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("dataset_downloader", ROOT / "download.py")
downloader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(downloader)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def archive_bytes(files, extra=None):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as package:
        for name, content in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            package.addfile(member, io.BytesIO(content))
        if extra is not None:
            member, content = extra
            package.addfile(member, io.BytesIO(content) if content is not None else None)
    return output.getvalue()


def manifest_for(files, archive=None):
    data = archive if archive is not None else archive_bytes(files)
    split = len(data) // 2
    chunks = [data[:split], data[split:]]
    parts = [{"asset": "toy.tar.gz.part{:03d}".format(i), "size": len(value), "sha256": digest(value)}
             for i, value in enumerate(chunks)]
    manifest = {
        "schema_version": 1, "repository": "fixture/datasets", "release_tag": "fixture-v1",
        "datasets": {"toy": {"name": "Toy dataset", "source": "local fixture", "storage": "release",
            "files": [{"path": name, "size": len(value), "sha256": digest(value)} for name, value in files.items()],
            "archive": {"format": "tar.gz", "size": len(data), "sha256": digest(data), "parts": parts}},
            "external": {"name": "External fixture", "storage": "external", "source": "https://example.invalid/source",
                         "files": []}}
    }
    return manifest, {part["asset"]: value for part, value in zip(parts, chunks)}


class State:
    def __init__(self, assets):
        self.assets = assets
        self.requests = []
        self.ignore_range = False
        self.bad_range = False
        self.first_416 = False
        self.corrupt = False
        self.truncate_first = False


@contextmanager
def local_server(state):
    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass

        def do_GET(self):
            state.requests.append((self.path, self.headers.get("Range"), self.headers.get("Authorization")))
            data = state.assets.get(self.path.lstrip("/"))
            if data is None:
                self.send_error(404)
                return
            if state.first_416 and len(state.requests) == 1:
                self.send_response(416)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            offset = 0
            raw = self.headers.get("Range")
            if raw and not state.ignore_range:
                offset = int(raw.removeprefix("bytes=").removesuffix("-"))
                self.send_response(206)
                self.send_header("Content-Range", "bytes {}-{}/{}".format(
                    offset + 1 if state.bad_range else offset, len(data) - 1, len(data)))
            else:
                self.send_response(200)
            data = data[offset:]
            if state.corrupt:
                data = bytes(value ^ 1 for value in data)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if state.truncate_first and len(state.requests) == 1:
                self.wfile.write(data[:19])
                self.wfile.flush()
                self.close_connection = True
            else:
                self.wfile.write(data)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:{}".format(server.server_port)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


class DatasetDownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.files = {"audio/clip.wav": bytes(range(256)) * 64, "labels.csv": b"clip,emotion\nclip.wav,happy\n", "empty.txt": b""}
        self.manifest, self.assets = manifest_for(self.files)
        self.target = self.root / "toy/audio/clip.wav"
        quiet = mock.patch("sys.stdout", new_callable=io.StringIO)
        quiet.start()
        self.addCleanup(quiet.stop)
        wait = mock.patch.object(downloader.time, "sleep")
        wait.start()
        self.addCleanup(wait.stop)

    @contextmanager
    def session(self, state=None, **options):
        state = state or State(self.assets)
        with local_server(state) as base:
            with mock.patch.object(downloader, "asset_url", side_effect=lambda repository, tag, asset: base + "/" + asset):
                yield downloader.Downloader(self.manifest, self.root, **options), state

    def write_existing(self):
        for name, data in self.files.items():
            path = self.root / "toy" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def test_fresh_multipart_archive_restore_and_cleanup(self):
        with self.session() as (client, state):
            self.assertTrue(client.run(["toy"]))
            for name, value in self.files.items():
                self.assertEqual((self.root / "toy" / name).read_bytes(), value)
            self.assertEqual(len(state.requests), 2)
            self.assertEqual(list(client.cache.iterdir()), [])

    def test_verified_dataset_skips_network_and_keeps_unknown_files(self):
        self.write_existing()
        unknown = self.root / "toy/user-notes.txt"
        unknown.write_bytes(b"keep this")
        with self.session() as (client, state):
            client.run(["toy"])
            self.assertEqual(state.requests, [])
            self.assertFalse(client.cache.exists())
        self.assertEqual(unknown.read_bytes(), b"keep this")

    def test_restore_keeps_unknown_and_valid_existing_files(self):
        self.write_existing()
        untouched = self.root / "toy/labels.csv"
        inode = untouched.stat().st_ino
        self.target.write_bytes(b"needs repair")
        unknown = self.root / "toy/my-extra.wav"
        unknown.write_bytes(b"unlisted audio")
        with self.session() as (client, state):
            client.run(["toy"])
        self.assertEqual(self.target.read_bytes(), self.files["audio/clip.wav"])
        self.assertEqual(untouched.stat().st_ino, inode)
        self.assertEqual(unknown.read_bytes(), b"unlisted audio")

    @staticmethod
    def cross_device_replace(source, destination):
        if any(part.startswith("extract-toy-") for part in source.parts):
            raise OSError(errno.EXDEV, "fixture cache is on another filesystem")
        return DatasetDownloadTests.original_replace(source, destination)

    original_replace = Path.replace

    def test_cross_device_cache_copies_and_verifies_before_atomic_install(self):
        self.write_existing()
        self.target.write_bytes(b"old clip needs replacement")
        labels = self.root / "toy/labels.csv"
        labels_inode = labels.stat().st_ino
        unknown = self.root / "toy/user-notes.txt"
        unknown.write_bytes(b"unknown content stays")
        with self.session() as (client, _):
            with mock.patch.object(Path, "replace", self.cross_device_replace):
                client.run(["toy"])
        self.assertEqual(self.target.read_bytes(), self.files["audio/clip.wav"])
        self.assertEqual(labels.stat().st_ino, labels_inode)
        self.assertEqual(unknown.read_bytes(), b"unknown content stays")
        self.assertEqual(list(self.target.parent.glob(".dataset-install-*.downloading")), [])

    def test_corrupt_cross_device_copy_preserves_old_target_and_cleans_temporary(self):
        self.write_existing()
        self.target.write_bytes(b"old clip must survive")
        unknown = self.root / "toy/user-notes.txt"
        unknown.write_bytes(b"unknown content stays")
        def corrupt_copy(source, destination, length):
            destination.write(b"corrupt copy")
        with self.session() as (client, _):
            with mock.patch.object(Path, "replace", self.cross_device_replace), \
                    mock.patch.object(downloader.shutil, "copyfileobj", side_effect=corrupt_copy):
                with self.assertRaisesRegex(downloader.DownloadError, "Copied dataset file failed SHA-256"):
                    client.run(["toy"])
        self.assertEqual(self.target.read_bytes(), b"old clip must survive")
        self.assertEqual(unknown.read_bytes(), b"unknown content stays")
        self.assertEqual(list(self.target.parent.glob(".dataset-install-*.downloading")), [])

    def test_non_cross_device_install_error_does_not_fallback_or_modify_target(self):
        self.write_existing()
        self.target.write_bytes(b"old clip must survive")
        def denied_replace(source, destination):
            if any(part.startswith("extract-toy-") for part in source.parts):
                raise OSError(errno.EACCES, "fixture permission error")
            return DatasetDownloadTests.original_replace(source, destination)
        with self.session() as (client, _):
            with mock.patch.object(Path, "replace", denied_replace), \
                    mock.patch.object(downloader.shutil, "copyfileobj") as copy_file:
                with self.assertRaises(OSError) as error:
                    client.run(["toy"])
                self.assertEqual(error.exception.errno, errno.EACCES)
                copy_file.assert_not_called()
        self.assertEqual(self.target.read_bytes(), b"old clip must survive")

    def test_range_resume(self):
        part = self.manifest["datasets"]["toy"]["archive"]["parts"][0]
        with self.session(workers=1) as (client, state):
            client.cache.mkdir(parents=True)
            (client.cache / (part["asset"] + ".partial")).write_bytes(self.assets[part["asset"]][:23])
            client.run(["toy"])
            self.assertEqual(state.requests[0][1], "bytes=23-")
            self.assertEqual(self.target.read_bytes(), self.files["audio/clip.wav"])

    def test_ignored_range_restarts_download(self):
        state = State(self.assets)
        state.ignore_range = True
        part = self.manifest["datasets"]["toy"]["archive"]["parts"][0]
        with self.session(state, workers=1) as (client, _):
            client.cache.mkdir(parents=True)
            (client.cache / (part["asset"] + ".partial")).write_bytes(b"outdated prefix")
            client.run(["toy"])
            self.assertEqual(self.target.read_bytes(), self.files["audio/clip.wav"])

    def test_interrupted_transfer_resumes(self):
        state = State(self.assets)
        state.truncate_first = True
        with self.session(state, workers=1) as (client, _):
            client.run(["toy"])
            self.assertIsNone(state.requests[0][1])
            self.assertEqual(state.requests[1][1], "bytes=19-")

    def test_bad_content_range_is_rejected(self):
        state = State(self.assets)
        state.bad_range = True
        part = self.manifest["datasets"]["toy"]["archive"]["parts"][0]
        with self.session(state, workers=1) as (client, _):
            client.cache.mkdir(parents=True)
            (client.cache / (part["asset"] + ".partial")).write_bytes(b"partial")
            with self.assertRaisesRegex(downloader.DownloadError, "Invalid Content-Range"):
                client.run(["toy"])
            self.assertFalse(self.target.exists())

    def test_416_discards_invalid_partial_and_retries(self):
        state = State(self.assets)
        state.first_416 = True
        part = self.manifest["datasets"]["toy"]["archive"]["parts"][0]
        with self.session(state, workers=1) as (client, _):
            client.cache.mkdir(parents=True)
            (client.cache / (part["asset"] + ".partial")).write_bytes(b"partial")
            client.run(["toy"])
            self.assertEqual(state.requests[0][1], "bytes=7-")
            self.assertIsNone(state.requests[1][1])

    def test_corrupt_download_preserves_existing_dataset(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b"existing clip")
        state = State(self.assets)
        state.corrupt = True
        with self.session(state, workers=1) as (client, _):
            with self.assertRaisesRegex(downloader.DownloadError, "SHA-256 mismatch"):
                client.run(["toy"])
        self.assertEqual(self.target.read_bytes(), b"existing clip")

    def test_archive_checksum_failure_preserves_existing_dataset(self):
        self.manifest["datasets"]["toy"]["archive"]["sha256"] = digest(b"wrong archive")
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b"existing clip")
        with self.session() as (client, _):
            with self.assertRaisesRegex(downloader.DownloadError, "archive failed SHA-256"):
                client.run(["toy"])
        self.assertEqual(self.target.read_bytes(), b"existing clip")

    def test_archive_member_checksum_failure_changes_no_existing_files(self):
        self.manifest["datasets"]["toy"]["files"][1]["sha256"] = digest(b"wrong labels")
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b"existing clip")
        with self.session() as (client, _):
            with self.assertRaisesRegex(downloader.DownloadError, "member failed SHA-256"):
                client.run(["toy"])
        self.assertEqual(self.target.read_bytes(), b"existing clip")
        self.assertFalse((self.root / "toy/labels.csv").exists())

    def assert_bad_archive(self, name, kind=tarfile.REGTYPE, content=b"x", linkname=""):
        member = tarfile.TarInfo(name)
        member.type = kind
        member.linkname = linkname
        member.size = len(content) if content is not None else 0
        package = archive_bytes(self.files, (member, content))
        self.manifest, self.assets = manifest_for(self.files, package)
        self.target.parent.mkdir(parents=True, exist_ok=True)
        self.target.write_bytes(b"old original")
        with self.session() as (client, _):
            with self.assertRaises((downloader.DownloadError, ValueError)):
                client.run(["toy"])
        self.assertEqual(self.target.read_bytes(), b"old original")
        self.assertFalse((self.root / "toy/labels.csv").exists())

    def test_archive_rejects_unexpected_members(self):
        self.assert_bad_archive("surprise.txt")

    def test_archive_rejects_traversal(self):
        self.assert_bad_archive("../escape")
        self.assertFalse((self.root / "escape").exists())

    def test_archive_rejects_absolute_member(self):
        self.assert_bad_archive("/absolute")

    def test_archive_rejects_hidden_member(self):
        self.assert_bad_archive(".gitattributes")

    def test_archive_rejects_symlink(self):
        self.assert_bad_archive("symlink", tarfile.SYMTYPE, None, "audio/clip.wav")

    def test_archive_rejects_hardlink(self):
        self.assert_bad_archive("hardlink", tarfile.LNKTYPE, None, "audio/clip.wav")

    def test_archive_rejects_duplicate_members(self):
        self.assert_bad_archive("labels.csv", tarfile.REGTYPE, self.files["labels.csv"])

    def test_archive_rejects_missing_members(self):
        self.manifest, self.assets = manifest_for(self.files, archive_bytes({"audio/clip.wav": self.files["audio/clip.wav"]}))
        with self.session() as (client, _):
            with self.assertRaisesRegex(downloader.DownloadError, "missing"):
                client.run(["toy"])
        self.assertFalse(self.target.exists())

    def test_manifest_rejects_path_traversal_and_file_parent_conflicts(self):
        for name in ("../escape", "/absolute", "audio/../escape", ".gitattributes", "a\\b", "a//b", "a/./b"):
            bad = copy.deepcopy(self.manifest)
            bad["datasets"]["toy"]["files"][0]["path"] = name
            with self.subTest(name=name), self.assertRaises(ValueError):
                downloader.Downloader(bad, self.root)
        bad = copy.deepcopy(self.manifest)
        bad["datasets"]["toy"]["files"].append({"path": "audio", "size": 0, "sha256": digest(b"")})
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            downloader.Downloader(bad, self.root)

    def test_target_symlink_is_not_replaced_or_followed(self):
        outside = self.root / "elsewhere"
        outside.mkdir()
        (self.root / "toy").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            downloader.Downloader(self.manifest, self.root)
        self.assertEqual(list(outside.iterdir()), [])

    def test_verify_only_is_offline_and_creates_no_cache(self):
        with self.session() as (client, state):
            self.assertFalse(client.run(["toy"], verify_only=True))
            self.write_existing()
            self.assertTrue(client.run(["toy"], verify_only=True))
            self.assertEqual(state.requests, [])
            self.assertFalse(client.cache.exists())

    def test_external_selection_is_explicit(self):
        with self.session() as (client, state):
            with self.assertRaisesRegex(downloader.DownloadError, "original sources"):
                client.run(["external"])
            with self.assertRaisesRegex(downloader.DownloadError, "setup_datasets.py"):
                client.run(["toy", "external"])
            self.assertEqual(state.requests, [])
        self.assertEqual(downloader.selected_keys(self.manifest, []), ["toy"])
        self.assertEqual(downloader.selected_keys(self.manifest, [], list_only=True), ["toy", "external"])
        self.assertEqual(downloader.selected_keys(self.manifest, [], all_datasets=True), ["toy", "external"])

    def test_cli_list_verify_and_ca_passthrough(self):
        path = self.root / "manifest.json"
        path.write_text(json.dumps(self.manifest))
        self.assertEqual(downloader.main(["--manifest", str(path), "--list"]), 0)
        self.assertEqual(downloader.main(["--manifest", str(path), "--root", str(self.root), "--verify-only"]), 1)
        self.write_existing()
        self.assertEqual(downloader.main(["--manifest", str(path), "--root", str(self.root), "--verify-only"]), 0)
        ca = self.root / "company roots.pem"
        with mock.patch.object(downloader, "create_ssl_context", return_value=downloader.create_ssl_context()) as context:
            self.assertEqual(downloader.main(["--manifest", str(path), "--root", str(self.root), "--verify-only", "--ca-bundle", str(ca)]), 0)
            context.assert_called_once_with(ca)

    def test_certificate_failure_is_not_retried(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b"existing clip")
        part = self.manifest["datasets"]["toy"]["archive"]["parts"][0]
        with self.session(workers=1) as (client, state):
            import ssl
            error = urllib.error.URLError(ssl.SSLCertVerificationError(1, "self-signed certificate"))
            with mock.patch.object(client.opener, "open", side_effect=error) as request:
                with self.assertRaisesRegex(downloader.DownloadError, "truststore"):
                    client.download_part(part)
                self.assertEqual(request.call_count, 1)
        self.assertEqual(self.target.read_bytes(), b"existing clip")


if __name__ == "__main__":
    unittest.main(verbosity=2)
