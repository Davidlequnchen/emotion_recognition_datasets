# Emotion recognition datasets

Versioned dataset metadata and verified archive downloads for
[emotion_recognition](https://github.com/Davidlequnchen/emotion_recognition).
The main project pins this repository as its `emotion_recognition/data` submodule.
Git contains source notes, labels/transcripts, checksums, six small CREMA-D smoke-test clips, and the downloader.
Bulk data is stored in GitHub Releases. Git LFS is not used.

## Restore data

Python 3.9+ is enough for the Release downloader. No model environment or hub account is needed.

```bash
python3 download.py                   # restore the ten mirrored datasets
python3 download.py mead thai_ser     # or only selected datasets
python3 download.py dailytalk          # restore the retained dialogue-context pilot candidate
python3 download.py --list            # show the thirteen evaluation copies plus retained pilot candidates
python3 download.py --verify-only     # verify the ten mirrored datasets offline
```

From the main repository root:

```bash
python3 emotion_recognition/scripts/common/setup_datasets.py
```

That command initializes this submodule when needed, preserves an older local data directory, reuses verified
files, and restores missing mirrored data. In a full main-project clone, it can also recover the previously committed dataset files directly from local Git objects (including nEMO legacy parts), avoiding a fresh archive download after Git removes the old tracked paths during migration. Shallow clones use Release downloads when those historical objects are unavailable. Existing external datasets and local ESD data remain on the machine;
ESD is excluded from this catalogue and is never uploaded here. Unknown extra local materials remain in the
preserved backup. Runtime paths stay `data/<dataset>/` inside the emotion-recognition project.

The ten mirror archives total about 15.49 GB of downloads and restore about 18.72 GB of files. Each archive is
split into attachments of at most 1.5 GiB. The downloader resumes interrupted transfers, checks every part and the
complete archive with SHA-256, verifies every extracted file against the manifest before replacing dataset files,
and leaves unrelated local files untouched. Default caches are removed after successful restoration; allow
additional working disk space for the current archive, downloaded parts, and staged extracted files.

## Catalogue

The catalogue contains thirteen evaluation copies plus DailyTalk as a retained context-pilot candidate. Adding a
retained dataset here does not add it to the main evaluation's model loaders or thirteen-dataset scope. Rows do not
represent every upstream video, microphone channel or split. `manifest.json` pins exact file lists, sizes, SHA-256
values and storage sources.

| Dataset | Storage | Local files (GB) | Scope | Source terms |
|---|---|---:|---|---|
| [JL-Corpus](https://www.kaggle.com/datasets/tli725/jl-corpus) (`jl_corpus`) | Release mirror | 0.449 | 2,400 WAVs and matching transcripts; the existing committed scope only | CC0 1.0 |
| [MCAE-SPPS](https://osf.io/9jyzc/) (`mcae_spps`) | Release mirror | 0.807 | 6,675 WAVs and the existing committed source metadata | CC BY-NC 4.0 |
| [nEMO](https://huggingface.co/datasets/amu-cai/nEMO) (`nemo`) | Release mirror | 0.531 | 4,481 clips in two original Parquet files; extracted WAVs are generated locally | CC BY-NC-SA 4.0 |
| [TESS](https://doi.org/10.5683/SP2/E8H2MF) (`tess`) | Release mirror | 0.281 | 2,800 WAVs | CC BY-NC 4.0 |
| [EMOVO](https://dagshub.com/kingabzpro/EMOVO) (`emovo`) | Release mirror | 0.352 | 588 original WAVs | No explicit dataset licence published with this mirror |
| [THAI-SER](https://huggingface.co/datasets/airesearch/thai-ser) (`thai_ser`) | Release mirror | 4.640 | 22,584 four-emotion FLACs and all 27,854 metadata rows; not the full multi-microphone release | CC BY-SA 4.0 |
| [MEAD](https://github.com/uniBruce/Mead) (`mead`) | Release mirror | 4.298 | Part0 audio: 48 actors, 31,729 valid converted 16 kHz mono WAVs | No explicit dataset licence published with the source copy |
| [MELD](https://github.com/declare-lab/MELD) (`meld`) | Release mirror | 0.284 | Test split: 2,610 converted 16 kHz mono WAVs and labels | Upstream repository GPL-3.0; source recordings from Friends retain their own rights |
| [SAVEE](https://cvssp.org/savee/) (`savee`) | Release mirror | 0.163 | 480 WAVs; repository owner confirmed separate public-upload permission on 2026-11-09 | Original licence restricts redistribution; separate upload permission confirmed by repository owner |
| [CREMA-D](https://zenodo.org/records/14646870) (`crema_d`) | Original external source | 0.611 | 7,442 WAVs and labels; the existing source downloader uses the original pinned GitHub release | See the original source licence and notices |
| [MESS](https://zenodo.org/records/3813437) (`mess`) | Original external source | 0.234 | 1,800 WAVs | See the original source licence and notices |
| [RAVDESS](https://zenodo.org/records/1188976) (`ravdess`) | Original external source | 0.590 | Speech audio only: 1,440 WAVs | See the original source licence and notices |
| [Emozionalmente](https://zenodo.org/records/12616095) (`emozionalmente`) | Original external source | 0.732 | v1.1: 6,902 WAVs and source metadata | See the original source licence and notices |
| [DailyTalk](https://github.com/keonlee9420/DailyTalk) (`dailytalk`) | Release mirror; retained pilot | 6.917 | 2,541 ordered dialogues, 23,773 original WAV/TXT pairs and pinned metadata/ECSS supplements; not added to formal evaluation | Audio/data CC BY-SA 4.0; ECSS files retain MIT notices |

Sizes use decimal GB. Each dataset retains its original terms; this repository does not apply one blanket licence
to all recordings. Original source notes and notices are preserved. For SAVEE, the repository owner confirmed
separate public-upload permission on 2026-11-09; that does not grant additional rights to downstream users.

## Four external datasets

CREMA-D, MESS, RAVDESS and Emozionalmente remain available from their original download sources and are not
re-uploaded as Release assets here. Use the source downloader from the main project folder:

```bash
python3 scripts/common/download_data.py --source --dataset mess
python3 scripts/common/download_data.py --source --dataset ravdess
python3 scripts/common/download_data.py --source --dataset emozionalmente
python3 scripts/common/download_data.py --source --dataset crema_d
```

CREMA-D's source mode is controlled by `crema_d: samples|full` in the main project's download_data.yaml; its existing
source downloader uses the original pinned GitHub source. The catalogue also records the Zenodo mirror identified
by the project. MESS, RAVDESS speech audio and Emozionalmente use the already pinned Zenodo records. Set source
mode and `dataset: all` only when explicitly downloading every evaluation source; ESD remains excluded.

## Provenance and included scope

The initial assets in Release `datasets-2026-11-09-v1` archive the nine copies formerly tracked by the main project,
with two transport changes: nEMO's six legacy Git parts are replaced with its two original Parquet files, and nested
Hugging Face `.gitattributes` files are omitted. The nEMO loader can extract WAVs from Parquet locally; duplicate
extracted WAVs and old Git-transfer parts are not redistributed. Existing main-project SHA256SUMS files are
retained where present, alongside this repository's complete manifest.

JL-Corpus contains only the previously committed 2,400 recordings, transcripts and source notes; extra perception
materials and stock photos in the local download are omitted. THAI-SER keeps the four evaluated emotions, MEAD
keeps Part0 audio, and MELD keeps the test split. All archived audio bytes are unchanged from those local copies.

## DailyTalk context-pilot addition

DailyTalk passed the local structural and audio audit on 2026-11-09. Its 23,773 audio files preserve the authors'
bytes, 44.1 kHz PCM16 format, and explicit dialogue/turn/speaker IDs. The copy includes original transcripts and
metadata, pinned ECSS supplemental files and derived ordered indexes; see `dailytalk/README.md` and
`dailytalk/audit.json`.
The two documented irregular dialogues remain in the original copy but are excluded from the conservative
2,539-dialogue ECSS-backed pilot. Current public ECSS categories exactly match original metadata after label-name
normalisation; only intensity adds a new field. This is not an independent second set of perceptual category votes.

The original official ZIP is 5.341 GB; the Release archive here additionally contains the audit and index files.
New assets have an archive-SHA-prefixed name and are appended to the existing Release without replacing any old
asset. Git pins metadata and hashes, not WAVs or the large ZIP. On another machine, pull the main repository and run:

```bash
git submodule update --init --recursive emotion_recognition/data
python3 emotion_recognition/scripts/common/setup_datasets.py dailytalk
python3 emotion_recognition/data/download.py dailytalk --verify-only
```

This restores a research candidate; it does not start model evaluation or change the current thirteen-dataset
benchmark. DailyTalk audio/data remains CC BY-SA 4.0, with upstream source and ECSS notices preserved.

## Company HTTPS certificates

Ordinary laptops need no special TLS configuration. If optional `truststore` is installed, downloads automatically
use the operating system's certificate trust (including installed company roots); otherwise standard Python TLS
is used. Python 3.10+ environments can install the optional helper once:

```bash
python -m pip install -r requirements-download.txt
```

Then rerun the same setup/download command. An explicit `--ca-bundle /path/to/company-ca.pem` or SSL_CERT_FILE is
also supported. Certificate and hostname verification remain enabled; existing verified data and resumable parts
are preserved. If pip itself needs the company CA, IT can provide a PEM bundle for pip's `--cert` option.

## Downloader tests

Run `python3 -m unittest discover -s tests`. Tests use tiny local HTTP/HTTPS and archive fixtures, not remote datasets.
