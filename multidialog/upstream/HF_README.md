---
license: cc-by-nc-4.0
task_categories:
- audio-to-audio
- text-generation
- audio-classification
- video-classification
language:
- en
size_categories:
- 1K<n<10K
# configs:
#   - config_name: default
#     data_files:
#       - split: test_freq
#         path: test_freq/*, metadata.jsonl
---
## **"Let's Go Real Talk: Spoken Dialogue Model for Face-to-Face Conversation", accepted to ACL 2024 (oral presentation).** 

**Audio files have been newly processed and re-uploaded on 7/11/2024. Please download the files again for an updated version.

- **Homepage:** https://multidialog.github.io
- **Paper:** https://arxiv.org/pdf/2406.07867
- **Audio Dataset:** https://huggingface.co/datasets/IVLLab/MultiDialog (this repository)
- **Video Dataset:** https://drive.google.com/drive/u/1/folders/1RPMwVHU34yX0R_HbxAWmxF2EHy961HA3

## Dataset Description

- **Homepage:** https://multidialog.github.io
- **Repository:** https://github.com/MultiDialog/MultiDialog
- **Paper:** https://arxiv.org/pdf/2406.07867
- **Point of Contact:** [jinny960812@kaist.ac.kr](mailto:jinny960812@kaist.ac.kr)
- **Point of Contact:** [chaewonkim@kaist.ac.kr](mailto:chaewonkim@kaist.ac.kr)

## Dataset Description
This dataset includes manually annotated metadata linking audio files to transcriptions, emotions, and other attributes. For access to video files of MultiDialog, download them [here](https://drive.google.com/drive/folders/1RPMwVHU34yX0R_HbxAWmxF2EHy961HA3?usp=sharing).

### Dataset Statistics
|                       | train   | valid_freq | valid_rare | test_freq | test_rare | Total    |
|-----------------------|---------|---------|---------|---------|---------|----------|
| \# dialogues          | 7,011   | 448     | 443     | 450     | 381     | 8,733    |
| \# utterance          | 151,645 | 8,516   | 9,556   | 9,811   | 8,331   | 187,859  |
| avg \# utterance/dialogue  | 21.63   | 19.01   | 21.57   | 21.80   | 21.87   | 21.51    |
| avg length/utterance (s)  | 6.50    | 6.23    | 6.40    | 6.99    | 6.49    | 6.51     |
| avg length/dialogue (min)  | 2.34    | 1.97    | 2.28    | 2.54    | 2.36    | 2.33     |
| total length (hr)  | 273.93  | 14.74   | 17.00   | 19.04   | 15.01   | 339.71   |


### Example Usage
There are 'train', 'test_freq', 'test_rare', 'valid_freq', and 'valid_rare' splits. Below is an example usage. 
```python
from datasets import load_dataset

MultiD = load_dataset("IVLLab/MultiDialog", "valid_freq", use_auth_token=True)

# see structure
print(MultiD)

# load audio sample on the fly
audio_input = MultiD["valid_freq"][0]["audio"]  # first decoded audio sample
transcription = MultiD["valid_freq"][0]["value"]  # first transcription
```

### Supported Tasks
- `multimodal dialogue generation` : The dataset can be used to train an end-to-end multimodal 
- `automatic-speech-recognition`: The dataset can be used to train a model for Automatic Speech Recognition (ASR). 
- `text-to-speech`: The dataset can also be used to train a model for Text-To-Speech (TTS).

### Languages
Multidialog contains audio and transcription data in English.

### Gold Emotion Dialogue Subset
We provide a gold emotion dialogue subset in the MultiDialog dataset, a more reliable resource for studying emotional dynamics in conversations. 
We classify dialogues from actors that exhibit emotion accuracy above 40% as gold emotion dialogue. Please use dialogues from actors with the following ids: a, b, c, e, f, g, i, j, and k.


## Dataset Structure
### Data Instances
```python
{
    'file_name': 't_ffa55df6-114d-4b36-87a1-7af6b8b63d9b/t_ffa55df6-114d-4b36-87a1-7af6b8b63d9b_0k.wav'
    'conv_id': 't_ffa55df6-114d-4b36-87a1-7af6b8b63d9b', 
    'utterance_id': 0,
    'from': 'gpt', 
    'audio': 
        {
            # in streaming mode 'path' will be 't_ffa55df6-114d-4b36-87a1-7af6b8b63d9b/t_ffa55df6-114d-4b36-87a1-7af6b8b63d9b_0k.wav'
            'path': '/home/user/.cache/huggingface/datasets/downloads/extracted/cache_id/t_ffa55df6-114d-4b36-87a1-7af6b8b63d9b/t_ffa55df6-114d-4b36-87a1-7af6b8b63d9b_0k.wav, 
            'array': array([0.0005188 , 0.00085449, 0.00012207, ..., 0.00125122, 0.00076294, 0.00036621], dtype=float32), 
            'sampling_rate': 16000
        },
    'value': 'Are you a football fan?', 
    'emotion': 'Neutral', 
    'original_full_path': 'valid_freq/t_ffa55df6-114d-4b36-87a1-7af6b8b63d9b/t_ffa55df6-114d-4b36-87a1-7af6b8b63d9b_0k.wav'
}
```

### Data Fields
* file_name (string) - relative file path to the audio sample in the specific split directory.
* conv_id (string) - unique identifier for each conversation.
* utterance_id (float) -  uterrance index.
* from (string) - who the message is from (human, gpt).
* audio (Audio feature) - a dictionary containing the path to the audio, the decoded audio array, and the sampling rate.
In non-streaming mode (default), the path point to the locally extracted audio. In streaming mode, the path is the relative path of an audio.
segment inside its archive (as files are not downloaded and extracted locally).
* value (string) - transcription of the utterance.
* emotion (string) - the emotion of the utterance.
* original_full_path (string) - the relative path to the original full audio sample in the original data directory.

* speaker_id can be obtained from the last letter of 'file_name' excluding '.wav' (e.g. 'k' in the above example)

Emotion is assigned from the following labels: 
"Neutral", "Happy", "Fear", "Angry", "Disgusting", "Surprising", "Sad"




