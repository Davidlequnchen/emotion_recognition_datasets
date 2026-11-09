# THAI-SER: extracted evaluation audio

This note was added by this project; the authors' `README.md` is preserved separately.

- Source: [AIResearch THAI-SER](https://huggingface.co/datasets/airesearch/thai-ser).
- Licence: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); retain attribution and the source
  terms. The authors and collaborating institutions are identified in `README.md`.
- Metadata: `labels.csv` preserves all 27,854 source rows and all non-audio columns. The `annotated` column is
  stored as JSON within the CSV.
- Audio: 22,584 FLAC files in `audio/`, covering assigned emotions Neutral, Angry, Happy and Sad. Each file's
  bytes are extracted unchanged from the studio condenser microphone (`mic_con`) or the online Zoom microphone
  (`mic_zoom`) in the source Parquet files.
- Omitted material: the 5,270 rows assigned Frustrated have no exported audio here because the evaluation models
  have no corresponding class. Other microphone channels and the original Parquet archives are also omitted.
  This is not the complete multi-microphone source release.

The exported four-emotion audio matches every corresponding `labels.csv` row, with no missing or extra clips.
All 22,584 locally extracted clips are committed; the evaluation can further select 11,848 high-agreement clips
using `config/evaluation.yaml`, without changing this stored copy.

`SHA256SUMS` records the SHA-256 of each FLAC, `labels.csv` and the original `README.md`. The local `.gitattributes`
stores extracted audio in ordinary Git instead of applying the source Hugging Face repository's LFS rules.
