# DailyTalk: local context-pilot copy

Downloaded from the authors' official Google Drive on 2026-11-09. Retained after structural audit for **past-only dialogue-context pilots**, not yet added to the project's 13-dataset evaluation or any model loader.

## Sources and licence

- Official project: https://github.com/keonlee9420/DailyTalk
- Paper: https://arxiv.org/abs/2207.01063 (ICASSP 2023)
- Official data folder: https://drive.google.com/drive/folders/1WRt-EprWs-2rmYxoWYT9_13omlhDHcaL
- Original archive: `dailytalk.zip`, file ID `1nPrfJn3TcIVPc0Uf5tiAXUYLJceb_5k-`, 5,341,371,062 bytes.
- Archive SHA-256: `fb68b1bb80c3177b62f0d206686a566e52ece738a57932321747b868bef3a6ea`; all ZIP member CRCs passed.
- DailyTalk audio/data: **Creative Commons Attribution-ShareAlike 4.0**. Preserve attribution and the original terms; a code repository's MIT licence does not relicense the audio. Original notice: `upstream/DailyTalk_README.md`.
- ECSS annotation source: https://github.com/walker-hyf/ECSS (AAAI 2024), commit `c1545fdb12ca56482de4ff3550dc47b81d9fe794`. Its MIT notice is preserved as `upstream/ECSS_LICENSE`; the underlying audio remains CC BY-SA 4.0.
- Exact downloaded metadata URLs, commits, sizes and hashes: `upstream/source_metadata.json`.

## Contents

- `data/<dialogue>/<turn>_<speaker>_d<dialogue>.wav`: original audio, unchanged.
- Matching `.txt`: original per-turn transcript.
- `metadata.json`: original nested dialogue/turn metadata, unchanged.
- `utterances.csv`: derived, explicitly ordered index joining original metadata, audio properties and public ECSS annotations; original and ECSS label columns remain separate.
- `dialogues.csv`: dialogue sizes and ECSS coverage.
- `audit.json`: measured counts, all checks, documented warnings, missing IDs and pilot examples.
- `pilot_examples.json`: a few real past-history/target examples for inspection.
- `upstream/`: source notices and the pinned ECSS frame annotation files, emotion vocabulary and processing code.

## Measured scope

| Item | Result |
|---|---:|
| Dialogues | 2,541 |
| Audio clips and matching TXT files | 23,773 each |
| Actors | 2, one male and one female |
| Total audio duration | 78,026.3277 seconds / 21.67398 hours |
| Audio format | 44,100 Hz, PCM16; 23,720 mono and 53 stereo files |
| WAV bytes | 6,899,868,374 |
| Duration range | 0.50565–17.83669 seconds |
| Median duration | 2.91050 seconds |
| Turns per dialogue | 5–20 |
| Dialogues containing at least two emotion categories | 1,545 |
| Non-neutral targets with at least one earlier turn | 4,495 |
| Short non-neutral targets with history (at most 3 words OR at most 2 seconds) | 1,161 |

All WAV headers and complete PCM payload lengths were read successfully. Metadata dialogue/utterance indices correspond to filenames; turn indices are contiguous from zero. These are real, recorded conversational turns in their published order, not unrelated clips assembled as history. The actors recorded dialogues simultaneously in a studio, following scripts and intended emotion labels; this is performed conversation, not an unprompted natural-interaction corpus.

## What the emotion labels mean

Original category labels are inherited from DailyDialog text, and the actors were directed to follow them. They are not independent voice-only listener votes. The ECSS paper describes additional professional listening/semantic annotation. However, in the **currently public files**, all 23,759 matched ECSS category labels equal the original categories after `no emotion` → `none` normalisation. Do not present them as an empirically different, independent audio-perception category gold set. ECSS adds a usable intensity field (1–3), but no new matched no-history versus with-history human judgments.

| Category | Original count | Public ECSS count |
|---|---:|---:|
| neutral / no emotion / none | 18,966 | 18,952 |
| happiness | 3,856 | 3,856 |
| surprise | 407 | 407 |
| sadness | 301 | 301 |
| anger | 159 | 159 |
| disgust | 66 | 66 |
| fear | 18 | 18 |

Public ECSS is 79.77% neutral. These locally verified version counts differ from some paper tables; use the pinned file counts for this copy. Use per-class support, UAR and macro-F1, not accuracy alone. Do not invent a seven-class label mapping without documenting `none` → `neutral` and other canonical names.

## Documented irregularities and conservative pilot scope

- **Dialogue 1451:** the metadata `turn` total says 19, but its metadata entries and audio contain exactly 10 contiguous turns (0–9). Preserve the original; exclude this dialogue from strict complete-history experiments until clarified upstream.
- **Dialogue 175:** all 14 turns lack ECSS supplemental rows, although original audio, transcripts and inherited labels are present. Exclude it when requiring complete ECSS annotations. No other ECSS IDs are missing or duplicated; no ECSS ID lacks matching audio.
- Excluding these two conversations leaves **2,539 complete dialogues** for a conservative ECSS-backed pilot. Both are all-neutral, so the 1,545 multi-emotion dialogues remain available.
- Eight original TXT/metadata text differences are recorded. They concern punctuation/spacing or number verbalisation, not mismatched audio IDs. Public ECSS text also includes TTS normalisation such as expanded abbreviations; preserve source columns and choose the text condition explicitly.
- Do not silently treat all files as mono; downmix/resample at the model-input stage and record that transformation.

A concrete example is dialogue 9: after a discussion of someone sleeping after pills, the other speaker says they may have given the wrong medicine; the target is a short **“What?”** labelled surprise (`data/9/10_1_d9.wav`, 0.854 s). It supports a useful fixed-target experiment: target alone versus the actual earlier audio/text. Whether context changes human perception still requires new matched-condition ratings.

## Retention decision

**Keep for technical and exploratory context pilots.** There is ample ordered audio, complete speaker/turn metadata and many short/non-neutral targets. Limit claims: only two actors, highly imbalanced labels, performed speech and no independent multi-listener category consensus. This copy alone cannot establish broad speaker generalisation or prove that context makes the model more human-like.
