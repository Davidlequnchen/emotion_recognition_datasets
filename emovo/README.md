# EMOVO

This note was added by this project; it is not part of the dataset.

EMOVO is an Italian emotional speech corpus with 588 recordings from six speakers, seven emotions and fourteen
sentences per speaker/emotion. The file names encode the acted emotion, speaker and sentence.

- Paper: Giovanni Costantini, Iacopo Iaderola, Andrea Paoloni and Massimiliano Todisco,
  [EMOVO Corpus: an Italian Emotional Speech Database](https://lrec.elra.info/lrec2014-main-478), LREC 2014.
- Local source: [kingabzpro/EMOVO on DagsHub](https://dagshub.com/kingabzpro/EMOVO), an unofficial mirror used because
  the original `voice.fub.it` download site is unavailable.
- Scope: all 588 WAVs in `audio/`, without resampling or other modifications. Download integrity was checked
  against the combined SHA-256 pinned in `scripts/common/download_data.py`.
- Licence: no explicit dataset licence was published with the downloaded copy. The mirror's availability does
  not establish a separate licence for the recordings.

`SHA256SUMS` records each WAV's SHA-256. No source labels are discarded: the corpus labels are in the file names.
