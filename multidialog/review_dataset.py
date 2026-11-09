"""Read-only verification of the retained audio, source metadata and QC cohort.

Standard library only. Run ``python multidialog/review_dataset.py`` from the
data repository, or pass a restored multidialog directory as the first argument.
No download, model import, inference or metadata rewriting occurs.
"""
import collections
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import wave

ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
GOLD=set('abcefgijk')
WORD_PATTERN=r"[A-Za-z0-9]+(?:'[A-Za-z]+)?"
LABELS={'Neutral':'neutral','Curious to dive deeper':'neutral','Happy':'happy',
        'Sad':'sad','Angry':'angry','Fearful':'fearful','Disgusted':'disgusted','Surprised':'surprised'}


def path_for(relative):
    parts=PurePosixPath(relative).parts
    assert parts and parts[0]=='audio' and not relative.startswith('/')
    assert '\\' not in relative and ':' not in relative
    assert not any(part.startswith('.') for part in parts)
    path=ROOT.joinpath(*parts)
    assert path.resolve().is_relative_to(ROOT)
    return path


def main():
    rows=list(csv.DictReader((ROOT/'utterances.csv').open(encoding='utf-8',newline='')))
    audit=json.loads((ROOT/'audit.json').read_text())
    cohort=json.loads((ROOT/'cohort_ids.json').read_text())
    source={}
    for split in ['test_freq','test_rare']:
        file=ROOT/'upstream/metadata'/split/(split+'_metadata_0000.jsonl')
        for line in file.read_text().splitlines():
            item=json.loads(line)
            source['audio/'+split+'/'+item['file_name']]=item
    assert len(rows)==len(source)==18141
    assert len({row['audio_path'] for row in rows})==len(rows)
    by_path={row['audio_path']:row for row in rows}
    actual_wavs={path.relative_to(ROOT).as_posix() for path in (ROOT/'audio').rglob('*.wav')}
    assert actual_wavs==set(by_path)==set(source)
    flagged_dialogues=set()
    for number,row in enumerate(rows,1):
        item=source[row['audio_path']]
        assert row['raw_emotion']==item['emotion'] and row['emotion']==LABELS[item['emotion']]
        assert row['text']==item['value'] and row['dialogue_id']==item['conv_id']
        assert int(row['turn_index'])==item['utterance_id']
        assert row['speaker_id']==Path(item['file_name']).stem[-1]
        digest=hashlib.sha256()
        path=path_for(row['audio_path'])
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024**2),b''):
                digest.update(chunk)
        assert digest.hexdigest()==row['audio_sha256']
        with wave.open(str(path),'rb') as audio:
            assert audio.getcomptype()=='NONE'
            assert (audio.getframerate(),audio.getnchannels(),audio.getsampwidth())==(16000,1,2)
            assert abs(audio.getnframes()/audio.getframerate()-float(row['duration_s']))<1e-8
        words=len(re.findall(WORD_PATTERN,row['text']))
        rate=words/float(row['duration_s'])
        flags=[]
        if words>=6 and rate>8:flags.append('implausibly_fast_text_audio')
        if float(row['duration_s'])>30 and rate<.6:flags.append('long_audio_sparse_transcript')
        assert row['qc_clip_flags']==';'.join(flags)
        if flags:flagged_dialogues.add(row['dialogue_id'])
        history=json.loads(row['past_3_audio_paths'])
        assert len(history)<=3
        for relative in history:
            past=by_path[relative]
            assert past['dialogue_id']==row['dialogue_id'] and past['split']==row['split']
            assert int(past['turn_index'])<int(row['turn_index'])
        if number%5000==0:print('Verified WAV/source/QC records:',number,flush=True)
    grouped=collections.defaultdict(list)
    for row in rows:grouped[(row['split'],row['dialogue_id'])].append(row)
    selected=[]
    for (split,dialogue),entries in grouped.items():
        ordered=sorted(entries,key=lambda row:int(row['turn_index']))
        assert [int(row['turn_index']) for row in ordered]==list(range(len(entries)))
        speakers={row['speaker_id'] for row in entries}
        assert len(speakers)==2
        eligible=speakers<=GOLD and dialogue not in flagged_dialogues
        for row in entries:
            assert (row['qc_dialogue_excluded']=='True')==(dialogue in flagged_dialogues)
            assert (row['baseline_eligible']=='True')==eligible
            assert (row['context_eligible']=='True')==(eligible and int(row['turn_index'])>0)
            if eligible:selected.append(row)
    selected.sort(key=lambda row:(row['split'],row['dialogue_id'],int(row['turn_index'])))
    assert cohort['baseline_clip_ids']==[row['split']+'/'+row['clip_id'] for row in selected]
    assert cohort['context_target_ids']==[row['split']+'/'+row['clip_id'] for row in selected if int(row['turn_index'])>0]
    expected=cohort.pop('sha256')
    assert hashlib.sha256(json.dumps(cohort,sort_keys=True,separators=(',',':')).encode()).hexdigest()==expected
    assert audit['qc']['default_cohort_sha256']==expected
    assert len(flagged_dialogues)==9 and len(selected)==7672
    assert len({row['dialogue_id'] for row in selected})==353
    print('PASS: raw18141 WAV/source records; default7672 clips/353 dialogues; context7319; no future history; exact QC cohort hash.',flush=True)


if __name__=='__main__':main()
