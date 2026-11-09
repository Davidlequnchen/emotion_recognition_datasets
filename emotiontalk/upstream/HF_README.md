---
license: cc-by-nc-sa-4.0
language:
- zh
size_categories:
- 100K<n<1M
---

# EmotionTalk: An Interactive Chinese Multimodal Emotion Dataset With Rich Annotations

[![Hugging Face Datasets](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Datasets-yellow)](https://huggingface.co/datasets/BAAI/Emotiontalk)
[![arXiv](https://img.shields.io/badge/arXiv-2502.18913-b31b1b.svg)](https://arxiv.org/pdf/2505.23018)
[![License: CC BY-NC-SA-4.0](https://img.shields.io/badge/License-CC%20BY--SA--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Github](https://img.shields.io/badge/Github-EmotionTalk-blue)](https://github.com/flageval-baai/EmotionTalk)

## Introduction

**EmotionTalk** is an interactive Chinese multimodal emotion dataset with rich annotations. This dataset provides multimodal information from 19 actors participating in dyadic conversation settings, incorporating acoustic, visual, and textual modalities. It includes 23.6 hours of speech (19,250 utterances), annotations for 7 utterance-level emotion categories (happy, surprise, sad, disgust, anger, fear, and neutral), 5-dimensional sentiment labels (negative, weakly negative, neutral, weakly positive, and positive) and 4-dimensional speech captions (speaker, speaking style, emotion and overall). The dataset is released under a **CC BY-NC-SA 4.0 license**, meaning it is available for non-commercial use.

## Dataset Details

This dataset contains 23.6 hours of spontaneous dialogue recordings. Key features of the dataset include:

* **Speakers:** 19 speakers.
* **Audio Format:**  WAV files with a 44.1kHz sampling rate. 
* **Label:**  Happy, angry, sad, disgusted, fear, surprise, neutral. 
* **Annotations:** The dataset includes annotations for each modality.
  * **Text modality:** `data` (each annotator's labeling results), `emotion_result`, `speaker_id`, `file_name` (file path), `content` (transcription).
  * **Audio modality:** `data` (each annotator's labeling results), `emotion_result`, `speaker_id`, `paragraphs` (timestamp), `sourceAttr` (caption), `file_name` (file path), `content` (transcription).
  * **Video modality:** `data` (each annotator's labeling results), `emotion_result`, `speaker_id`, `file_name` (file path).
  * **Multimodal:** `data` (each annotator's labeling results), `emotion_result`, `Continuous label_result`, `speaker_id`, `file_name` (file path).

### Dataset Structure

The dataset file structure is as follows.

```
data
├── audio/*.tar  
├── Text/*.tar  
├── Video/*.tar  
└── Multimodal/*.tar  
```

### Dataset Statistics
The dataset is split into three subsets:
|          | Angry | Disgusted | Fearful | Happy | Neutral | Sad  | Surprised | Total  |
| :------- | :---- | :-------- | :------ | :---- | :------ | :--- | :-------- | :----- |
| Train    | 2950  | 1142      | 672     | 2986  | 5377    | 919  | 1367      | 15413  |
| Val(G01/G12) | 409   | 95        | 125     | 360   | 675     | 111  | 133       | 1908   |
| Test(G03/G15) | 339   | 134       | 125     | 246   | 801     | 123  | 161       | 1929   |
| **Total**| **3698**| **1371** | **922** | **3592**| **6853**| **1153**| **1661** | **19250**|

For more details, please refer to our paper [EmotionTalk](https://arxiv.org/pdf/2505.23018).

## 📚 Cite me

```
@article{sun2025emotiontalk,
  title={EmotionTalk: An Interactive Chinese Multimodal Emotion Dataset With Rich Annotations},
  author={Sun, Haoqin and Wang, Xuechen and Zhao, Jinghua and Zhao, Shiwan and Zhou, Jiaming and Wang, Hui and He, Jiabei and Kong, Aobo and Yang, Xi and Wang, Yequan and others},
  journal={arXiv preprint arXiv:2505.23018},
  year={2025}
}
```