# MEAD: Part0 audio

This note was added by this project; it is not part of the dataset.

- Source: the authors' [MEAD repository](https://github.com/uniBruce/Mead), and its official Google Drive
  [Part0 folder](https://drive.google.com/drive/folders/1GwXP-KpWOxOenOxITTsURJZQ_1pkd4-j).
- Scope: the `audio.tar` files for all 48 actors in Part0, without videos or other parts of MEAD.
- Changes: the source AAC/M4A audio was converted with ffmpeg to 16 kHz, mono PCM16 WAV. Archives and the M4A
  intermediates were deleted by `scripts/common/download_data.py` after conversion.
- Count: 31,729 valid WAVs from 31,734 source entries; five source files contained no audio and could not be
  converted. Every retained WAV has a readable header and nonzero frames.
- Layout: `audio/<actor>/<emotion>/level_<n>/<number>.wav`; labels remain encoded in the directory names.
- Licence: the downloaded release does not include an explicit dataset licence for the recordings.

All locally converted emotions and levels are retained, including contempt. The evaluation loader excludes
contempt and can select its fixed `stratified_8000` subset; this copy is not limited to those 8,000 clips.

`SHA256SUMS` records each converted WAV's SHA-256. It verifies this local conversion, not the original M4A files.
