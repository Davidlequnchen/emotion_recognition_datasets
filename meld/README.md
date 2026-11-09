# MELD: test split audio

This note was added by this project; it is not part of the dataset.

- Source: the authors' [MELD repository](https://github.com/declare-lab/MELD) and
  [Hugging Face release](https://huggingface.co/datasets/declare-lab/MELD), `MELD.Raw.tar.gz`.
- Scope: the complete test split, 2,610 utterances. Training and development audio and all videos are omitted.
- Labels: `test_sent_emo.csv`, preserved byte for byte from the authors' repository at commit
  `e8cedf27b5d2877e198332c957127e16eb214afe`. Its SHA-256 is pinned in `scripts/common/download_data.py`.
- Changes: ffmpeg extracted each test video's audio as 16 kHz, mono PCM16 WAV in
  `audio/dia<Dialogue_ID>_utt<Utterance_ID>.wav`. Source archives and videos were deleted after conversion.
- Integrity: every label row has exactly one corresponding WAV; all 2,610 WAVs have readable headers and nonzero
  frames.
- Licence: the upstream repository uses GPL-3.0. The recordings are derived from the television series
  *Friends*; the repository's code licence is not an independent licence grant for that source television audio.

`SHA256SUMS` records the SHA-256 of the converted audio and the original test labels.
