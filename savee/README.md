# SAVEE: audio copy

This note was added by this project; it is not part of the dataset.

- Dataset: Surrey Audio-Visual Expressed Emotion (SAVEE), by Philip Jackson and Sana-Ul Haq,
  [official site](https://cvssp.org/savee/).
- Local source: the unofficial Kaggle mirror
  [ejlok1/surrey-audiovisual-expressed-emotion-savee](https://www.kaggle.com/datasets/ejlok1/surrey-audiovisual-expressed-emotion-savee).
- Scope: all 480 WAVs from the audio-only mirror in `audio/ALL/`, from four male speakers (DC, JE, JK, KL).
  Audio has not been resampled or otherwise modified. Emotion and sentence labels are encoded in file names.
- Integrity: the downloaded archive was checked against the SHA-256 pinned in
  `scripts/common/download_data.py`; `unpacked.json` lists its extracted files and sizes.
- Terms: the [official licence](https://cvssp.org/savee/Register.html), section 2.2, prohibits redistribution to
  third parties. On 2026-11-09 the repository owner confirmed separate permission to upload this copy to this
  public repository. That confirmation does not grant downstream users additional rights under the original
  licence.

`SHA256SUMS` records the SHA-256 of every WAV and the extraction manifest.
