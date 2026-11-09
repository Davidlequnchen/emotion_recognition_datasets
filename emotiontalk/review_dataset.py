import collections
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
import time
import unicodedata
import wave
import argparse

CACHE = Path(__file__).resolve().parent
OUT = CACHE
SOURCE = json.loads((CACHE / 'source_manifest.json').read_text())
ARCHIVE = CACHE / 'Audio.tar'
RESERVE = 20 * 1024 ** 3


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def write_csv(path, rows, columns):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows({key: row.get(key, '') for key in columns} for row in rows)


def extract():
    assert SOURCE.get('actual_sha256') == SOURCE.get('expected_sha256'), 'Archive not verified'
    assert ARCHIVE.stat().st_size == SOURCE['expected_bytes']
    with tarfile.open(ARCHIVE, 'r:') as archive:
        members = archive.getmembers()
        for member in members:
            parts = PurePosixPath(member.name).parts
            if (not parts or parts[0] != 'Audio' or member.name.startswith('/')
                    or any(part in ('..', '.') for part in parts)
                    or '\\' in member.name or ':' in member.name
                    or not (member.isdir() or member.isfile())):
                raise RuntimeError('Unsafe archive member: ' + member.name)
        unpacked = sum(member.size for member in members if member.isfile())
        free = shutil.disk_usage(OUT.parent).free
        print('Unpacked bytes:', unpacked, 'free:', free, 'reserved:', RESERVE, flush=True)
        if free < unpacked + RESERVE:
            raise RuntimeError('Insufficient free space with 20 GiB reserve; await cache cleanup')
        OUT.mkdir(parents=True, exist_ok=True)
        done = 0
        for member in members:
            target = OUT.joinpath(*PurePosixPath(member.name).parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            partial = target.with_name(target.name + '.extract-part')
            with archive.extractfile(member) as source, partial.open('wb') as destination:
                shutil.copyfileobj(source, destination, 1024 * 1024)
            if partial.stat().st_size != member.size:
                raise RuntimeError('Extracted size mismatch: ' + member.name)
            partial.replace(target)
            done += 1
            if done % 10000 == 0:
                print('Extracted files:', done, flush=True)
    print('Extraction complete:', done, 'files', flush=True)


def audit():
    issues = []
    rows = []
    header_errors = []
    wavs = {path.relative_to(OUT).as_posix(): path for path in (OUT / 'Audio/wav').rglob('*.wav')}
    audio_stats = {}
    formats = collections.Counter()
    bytes_total = 0
    duration_total = 0.0
    for i, (relative, path) in enumerate(sorted(wavs.items()), 1):
        bytes_total += path.stat().st_size
        try:
            with wave.open(str(path), 'rb') as audio:
                channels, width, rate, frames = audio.getnchannels(), audio.getsampwidth(), audio.getframerate(), audio.getnframes()
                read_bytes = 0
                while data := audio.readframes(65536):
                    read_bytes += len(data)
                if read_bytes != frames * channels * width:
                    raise ValueError('PCM payload length differs from header')
                stat = {'channels': channels, 'sample_width': width, 'sample_rate': rate,
                        'frames': frames, 'duration_s': frames / rate, 'compression': audio.getcomptype()}
            formats[(channels, width, rate, stat['compression'])] += 1
            duration_total += stat['duration_s']
            audio_stats[relative] = stat
        except Exception as error:
            header_errors.append({'audio_path': relative, 'error': type(error).__name__})
        if i % 5000 == 0:
            print('WAV payloads checked:', i, flush=True)
    rater_counts = collections.Counter()
    confidence = []
    labels = collections.Counter()
    references = collections.Counter()
    mode_disagreements = 0
    weighted_disagreements = 0
    mean_confidence_disagreements = 0
    missing_audio = []
    metadata_duration_diffs = []
    timestamp_duration_diffs = []
    json_paths = sorted((OUT / 'Audio/json').rglob('*.json'))
    for path in json_paths:
        relative_json = path.relative_to(OUT).as_posix()
        try:
            item = json.loads(path.read_text(encoding='utf-8'))
            parts = path.stem.split('_')
            if len(parts) != 4 or not parts[0].startswith('G'):
                raise ValueError('Unexpected clip ID shape')
            group, session, local_speaker, utterance = parts
            dialogue = group + '_' + session
            declared = str(item['file_path'])
            if '\\' in declared or '..' in PurePosixPath(declared).parts or PurePosixPath(declared).is_absolute():
                raise ValueError('Unsafe file_path')
            relative_audio = (PurePosixPath('Audio/wav') / declared).as_posix()
            expected_audio = (PurePosixPath('Audio/wav') / path.relative_to(OUT / 'Audio/json')).with_suffix('.wav').as_posix()
            row_issues = []
            if relative_audio != expected_audio:
                row_issues.append('metadata_audio_path_differs_from_hierarchy')
            if str(item['speaker_id']) != local_speaker:
                row_issues.append('speaker_id_differs_from_filename')
            paragraphs = item['paragraphs']
            start, end = float(paragraphs['startTime']), float(paragraphs['endTime'])
            declared_duration = float(paragraphs['duration'])
            if start < 0 or end <= start:
                row_issues.append('invalid_time_bounds')
            stat = audio_stats.get(relative_audio)
            references[relative_audio] += 1
            if stat is None:
                row_issues.append('missing_or_invalid_audio')
                missing_audio.append(relative_audio)
                stat = {'duration_s': 0, 'channels': 0, 'sample_width': 0, 'sample_rate': 0}
            difference = abs(stat['duration_s'] - declared_duration)
            if difference > .05:
                metadata_duration_diffs.append({'clip': path.stem, 'difference_s': difference})
                row_issues.append('metadata_vs_audio_duration_over_50ms')
            if abs((end-start) - declared_duration) > .005:
                timestamp_duration_diffs.append({'clip': path.stem, 'difference_s': abs((end-start)-declared_duration)})
                row_issues.append('time_bounds_vs_duration_over_5ms')
            final = str(item['emotion_result'])
            labels[final] += 1
            votes = item.get('data', {})
            rater_counts[len(votes)] += 1
            vote_counts = collections.Counter()
            vote_weights = collections.Counter()
            for vote in votes.values():
                label = str(vote['emotion'])
                weight = float(vote['Confidence_degree'])
                confidence.append(weight)
                vote_counts[label] += 1
                vote_weights[label] += weight
            if vote_counts and vote_counts[final] != max(vote_counts.values()):
                mode_disagreements += 1
            if vote_weights and vote_weights[final] != max(vote_weights.values()):
                weighted_disagreements += 1
            mean_confidences = {label: weight / vote_counts[label] for label,weight in vote_weights.items()}
            if mean_confidences and mean_confidences.get(final, -1) < max(mean_confidences.values()) - 1e-8:
                mean_confidence_disagreements += 1
            text = str(item.get('content', ''))
            without_markup = re.sub(r'\[[^\]]*\]', '', text)
            char_count = sum(unicodedata.category(char)[0] not in {'P','Z','C'} for char in without_markup)
            row = {'clip_id': path.stem, 'audio_path': relative_audio, 'json_path': relative_json,
                   'group_id': group, 'dialogue_id': dialogue, 'speaker_id': local_speaker,
                   'speaker_group_key': group + '_' + local_speaker, 'utterance_index': int(utterance),
                   'start_s': start, 'end_s': end, 'duration_s': stat['duration_s'],
                   'sample_rate': stat['sample_rate'], 'channels': stat['channels'],
                   'sample_width': stat['sample_width'], 'text': text, 'emotion': final,
                   'rater_count': len(votes), 'votes_json': json.dumps(dict(vote_counts), sort_keys=True),
                   'confidence_weights_json': json.dumps(dict(vote_weights), sort_keys=True),
                   'split': 'validation' if group in {'G00001','G00012'} else 'test' if group in {'G00003','G00015'} else 'train',
                   'text_without_markup': without_markup, 'nonpunctuation_character_count': char_count,
                   'short_response': stat['duration_s'] <= 2 or char_count <= 8,
                   'issues': ';'.join(row_issues)}
            rows.append(row)
            for reason in row_issues:
                issues.append({'clip': path.stem, 'reason': reason})
        except Exception as error:
            issues.append({'json_path': relative_json, 'reason': 'json_parse_or_schema_' + type(error).__name__})
    grouped = collections.defaultdict(list)
    for row in rows:
        grouped[row['dialogue_id']].append(row)
    dialogues = []
    examples = []
    overlaps = 0
    index_order_errors = []
    duplicate_intervals = []
    for dialogue, entries in sorted(grouped.items()):
        entries.sort(key=lambda row: (row['start_s'], row['end_s'], row['speaker_id'], row['utterance_index']))
        by_speaker = collections.defaultdict(list)
        interval_counts = collections.Counter()
        speaker_count = len({row['speaker_id'] for row in entries})
        for row in entries:
            by_speaker[row['speaker_id']].append(row)
            interval_counts[(row['speaker_id'], row['start_s'], row['end_s'])] += 1
            past = [other for other in entries if not other['issues'] and other['end_s'] <= row['start_s'] + .001]
            past.sort(key=lambda other: (other['end_s'], other['start_s']))
            row['strict_past_count'] = len(past)
            row['previous_audio_path'] = past[-1]['audio_path'] if past else ''
            row['strict_past_audio_json'] = json.dumps([other['audio_path'] for other in past[-3:]])
            row['eligible_history_target'] = bool(past) and not row['issues']
            row['dialogue_speaker_count'] = speaker_count
            row['same_speaker_history_count'] = sum(other['speaker_id'] == row['speaker_id'] for other in past)
            row['other_speaker_history_count'] = sum(other['speaker_id'] != row['speaker_id'] for other in past)
            row['primary_dyadic_history_target'] = row['eligible_history_target'] and speaker_count == 2
            prior_overlaps = [other for other in entries if other['start_s'] < row['start_s'] and other['end_s'] > row['start_s'] + .001]
            row['earlier_turns_overlap_target_start'] = len(prior_overlaps)
            overlaps += bool(prior_overlaps)
        for speaker, speaker_rows in by_speaker.items():
            in_index_order = sorted(speaker_rows, key=lambda row: row['utterance_index'])
            if any(b['start_s'] < a['start_s'] for a,b in zip(in_index_order, in_index_order[1:])):
                index_order_errors.append({'dialogue_id': dialogue, 'speaker_id': speaker})
        for (speaker,start,end), number in interval_counts.items():
            if number > 1:
                duplicate_intervals.append({'dialogue_id': dialogue, 'speaker': speaker, 'start_s': start, 'end_s': end, 'count': number})
        dialogues.append({'dialogue_id': dialogue, 'group_id': entries[0]['group_id'], 'split': entries[0]['split'],
                          'clips': len(entries), 'speaker_count': len(by_speaker),
                          'emotions': ','.join(sorted({row['emotion'] for row in entries})),
                          'emotion_count': len({row['emotion'] for row in entries}),
                          'timeline_duration_s': max(row['end_s'] for row in entries) - min(row['start_s'] for row in entries),
                          'utterance_duration_s': sum(row['duration_s'] for row in entries),
                          'eligible_history_targets': sum(row['eligible_history_target'] for row in entries),
                          'flagged_clips': sum(bool(row['issues']) for row in entries)})
    split_counts = {}
    for split in ['train','validation','test']:
        subset = [row for row in rows if row['split'] == split]
        split_counts[split] = {'clips': len(subset), 'dialogues': len({row['dialogue_id'] for row in subset}),
                               'emotion_counts': dict(collections.Counter(row['emotion'] for row in subset)),
                               'speaker_ids': sorted({row['speaker_id'] for row in subset}),
                               'history_targets': sum(row['eligible_history_target'] for row in subset),
                               'primary_dyadic_history_targets': sum(row['primary_dyadic_history_target'] for row in subset)}
    # Examples are deliberately varied by label and dialogue; they illustrate available data,
    # not measured gains from supplying context.
    used_dialogues = set()
    for emotion in ['neutral','happy','surprised','sad','fearful','disgusted','angry']:
        candidates = [row for row in rows if row['primary_dyadic_history_target'] and row['short_response']
                      and row['emotion'] == emotion and row['split'] == 'test' and '[' not in row['text']]
        candidates.sort(key=lambda row: (row['nonpunctuation_character_count'],row['duration_s'],row['clip_id']))
        candidates = [row for row in candidates if row['dialogue_id'] not in used_dialogues] or candidates
        if candidates:
            row = candidates[0]
            used_dialogues.add(row['dialogue_id'])
            past_paths = json.loads(row['strict_past_audio_json'])
            past_rows = {other['audio_path']:other for other in grouped[row['dialogue_id']]}
            examples.append({'dialogue_id':row['dialogue_id'], 'split':row['split'],
                             'target':{key:row[key] for key in ['clip_id','audio_path','speaker_id','text','emotion','start_s','end_s','duration_s']},
                             'past':[{key:past_rows[path][key] for key in ['clip_id','audio_path','speaker_id','text','emotion','start_s','end_s']} for path in past_paths],
                             'note':'Labels included for audit only; never supply history gold labels or target captions to the model. This example does not prove that context improves classification.'})
    report = {'source': SOURCE, 'audio_files': len(wavs), 'json_files': len(json_paths), 'indexed_rows': len(rows),
              'audio_bytes': bytes_total, 'audio_duration_s': duration_total, 'audio_duration_h': duration_total / 3600,
              'formats': [{'channels': key[0], 'sample_width': key[1], 'sample_rate': key[2], 'compression': key[3], 'clips':value} for key,value in sorted(formats.items())],
              'groups': len({row['group_id'] for row in rows}), 'dialogues': len(dialogues),
              'group_speaker_slots': len({row['speaker_group_key'] for row in rows}),
              'published_unique_speaker_ids': len({row['speaker_id'] for row in rows}),
              'speaker_id_note': '19 published speaker IDs, consistent with the paper actor count; identity was not independently verified by voice. IDs are reused across recording groups.',
              'group_speaker_ids': {group:sorted({row['speaker_id'] for row in rows if row['group_id']==group}) for group in sorted({row['group_id'] for row in rows})},
              'dialogue_speaker_count_distribution': dict(collections.Counter(row['speaker_count'] for row in dialogues)),
              'emotion_counts': dict(labels), 'rater_count_distribution': dict(rater_counts),
              'confidence_min': min(confidence) if confidence else None, 'confidence_max': max(confidence) if confidence else None,
              'final_label_not_unweighted_mode_count': mode_disagreements,
              'final_label_not_confidence_weighted_top_count': weighted_disagreements,
              'final_label_not_mean_confidence_top_count': mean_confidence_disagreements,
              'confidence_values': sorted(set(confidence)),
              'label_aggregation_note':'Gold is the published emotion_result. Paper Eq.1 uses mean confidence per chosen class, with expert review of ambiguous cases. Mode/summed/mean confidence differences are diagnostics, not file corruption.',
              'strict_past_definition': 'Earlier complete turns from the same dialogue, endTime <= target startTime + 1ms; overlapping continuations excluded.',
              'eligible_history_targets': sum(row['eligible_history_target'] for row in rows),
              'nonneutral_history_targets': sum(row['eligible_history_target'] and row['emotion'] != 'neutral' for row in rows),
              'short_nonneutral_history_targets': sum(row['eligible_history_target'] and row['emotion'] != 'neutral' and row['short_response'] for row in rows),
              'primary_dyadic_history_targets': sum(row['primary_dyadic_history_target'] for row in rows),
              'history_targets_with_prior_other_speaker': sum(row['eligible_history_target'] and row['other_speaker_history_count']>0 for row in rows),
              'history_targets_with_prior_same_speaker': sum(row['eligible_history_target'] and row['same_speaker_history_count']>0 for row in rows),
              'single_speaker_dialogues': [row['dialogue_id'] for row in dialogues if row['speaker_count']==1],
              'single_speaker_dialogue_clips': sum(row['clips'] for row in dialogues if row['speaker_count']==1),
              'short_response_definition': 'Audio <=2s or <=8 nonpunctuation/nonspace Unicode characters after removing square-bracket transcript markup.',
              'multi_emotion_dialogues': sum(row['emotion_count']>=2 for row in dialogues),
              'targets_with_earlier_turn_overlap': overlaps,
              'header_errors': header_errors, 'missing_audio': missing_audio,
              'unreferenced_wavs': sorted(set(wavs)-set(references)),
              'duplicate_audio_references': {key:value for key,value in references.items() if value>1},
              'metadata_vs_wav_duration_issues': metadata_duration_diffs,
              'timestamp_internal_duration_issues': timestamp_duration_diffs,
              'speaker_index_time_order_issues': index_order_errors,
              'duplicate_speaker_intervals': duplicate_intervals,
              'issues': issues, 'split_counts': split_counts,
              'split_speaker_overlaps': {a+'__'+b:sorted(set(split_counts[a]['speaker_ids']) & set(split_counts[b]['speaker_ids'])) for a,b in [('train','validation'),('train','test'),('validation','test')]},
              'upstream_discrepancies': ['Audio.tar contains 742 nonempty dialogue directories rather than the paper 744; no files invented to fill the gap.', 'Audio gold label counts differ from the HF README table; paper audio neutral proportion 48.7% agrees with actual Audio/json, while README table neutral proportion 35.6% agrees with paper multimodal labels.', 'Audio WAV formats are mixed: predominantly stereo 44.1 kHz, with mono 44.1 kHz and mono 16 kHz exceptions; resample/downmix at model input time.'],
              'annotation_limitations': ['Published audio-only ratings may include access to earlier turns; not paired isolated-versus-context human ratings.',
                                         'Caption fields are descriptive auxiliary material, not the categorical gold label.',
                                         'Validation and test share published speaker IDs 02 and 13; do not call the three official subsets mutually speaker-disjoint.',
                                         'Eight dialogue IDs contain only one published speaker in Audio.tar; exclude these from primary dyadic analysis.',
                                         'Professional actors performed theme-guided improvisations; this is conversational data collected in a controlled setting, not uncontrolled everyday recordings.']}
    write_json(OUT / 'audit.json', report)
    write_json(OUT / 'pilot_examples.json', examples)
    write_json(OUT / 'source_manifest.json', SOURCE)
    write_csv(OUT / 'utterances.csv', rows, list(rows[0]) if rows else [])
    write_csv(OUT / 'dialogues.csv', dialogues, list(dialogues[0]) if dialogues else [])
    if CACHE != OUT and (CACHE / 'README.md').exists():
        (OUT / 'upstream').mkdir(exist_ok=True)
        shutil.copy2(CACHE / 'README.md', OUT / 'upstream/HF_README.md')
    print(json.dumps({key:report[key] for key in ['audio_files','json_files','indexed_rows','audio_duration_h','groups','dialogues','published_unique_speaker_ids','emotion_counts','eligible_history_targets','primary_dyadic_history_targets','short_nonneutral_history_targets','multi_emotion_dialogues']}, ensure_ascii=False),flush=True)
    print('Issues:',len(issues),'header errors:',len(header_errors),'unreferenced WAV:',len(report['unreferenced_wavs']),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit-only', action='store_true')
    args = parser.parse_args()
    if not args.audit_only:
        extract()
    audit()
