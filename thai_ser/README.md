---
license: cc-by-sa-4.0
dataset_info:
  features:
  - name: audio_id
    dtype: string
  - name: assigned_emo
    dtype: string
  - name: majority_emo
    dtype: string
  - name: annotated
    sequence:
      sequence: string
  - name: agreement
    dtype: float64
  - name: session_id
    dtype: string
  - name: room_type
    dtype: string
  - name: actor_id
    dtype: string
  - name: actor_gender
    dtype: string
  - name: actor_age
    dtype: int64
  - name: turn_type
    dtype: string
  - name: script_intensity
    dtype: string
  - name: script_trial
    dtype: float64
  - name: script_sent
    dtype: string
  - name: situation_desc
    dtype: string
  - name: situation_turn
    dtype: float64
  - name: mic_clip
    dtype: audio
  - name: mic_con
    dtype: audio
  - name: mic_middle
    dtype: audio
  - name: mic_zoom
    dtype: audio
  splits:
  - name: train
    num_bytes: 14096998742.024
    num_examples: 27854
  download_size: 12707613941
  dataset_size: 14096998742.024
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*.parquet
task_categories:
- audio-classification
language:
- th
tags:
- emotion
- speech
- audio
- SER
pretty_name: THAI-SER
size_categories:
- 10K<n<100K
---

# 🇹🇭 THAI-SER Dataset 🎭

[[📝 Paper (preprint)](https://arxiv.org/abs/2507.09618)]

**Published by:** AI Research Institute of Thailand (AIResearch)

**In collaboration with:**  
- Vidyasirimedhi Institute of Science and Technology (VISTEC)  
- Digital Economy Promotion Agency (depa)  
- Department of Computer Engineering, Faculty of Engineering, Chulalongkorn University  
- Department of Dramatic Arts, Faculty of Arts, Chulalongkorn University

**Sponsored by:** Advanced Info Services Public Company Limited (AIS), and Siam Commercial Bank (SCB)

<div style="display: flex; gap: 10px; align-items: center;">
  <img src="https://assets.brandinside.asia/uploads/2016/08/AIS-logo-1.jpg" alt="ais" style="height:40px;"/>
  <img src="https://www.brandbuffet.in.th/wp-content/uploads/2013/07/SCB-logo.jpg" alt="scb" style="height:40px;"/>
  <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQd1KFE3l9ijJ-7m6YsbivoTXlqbwkc9LIqMmlNTPZu9SvDYZgEDzJkJYVpXBNAsZo-nUI&usqp=CAU" alt="depa" style="height:40px;"/>
  <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSvjS7dr0MvA0FxgsVWNHjqrZbAjVwtLq6hng&s" alt="vistec" style="height:40px;"/>
</div>


**License:** Creative Commons BY-SA 4.0

---

## 🚀 Dataset Overview

THAI-SER is an open Thai speech emotion recognition dataset containing emotional speech utterances in Thai. This dataset includes recordings of professional actors performing scripted and improvised scenarios.

### 🌟 Key Highlights
- **Total Duration:** 41 hours 36 minutes
- **Total Utterances:** 27,854
- **Number of Actors:** 200 (112 female, 88 male)
- **Recording Environments:** Studio (controlled & uncontrolled), Zoom
- **Emotions:** Neutral, Anger, Happiness, Sadness, Frustration
- **Session Types:** Script Session, Improvisation Session

---

## 🎙️ Recording Environments

The dataset comprises recordings from two main environments:

### 🎧 Studio Recordings
- **Studio A:** Noise-controlled, soundproof rooms (`studio001` to `studio018`)
- **Studio B:** Normal rooms without soundproofing (`studio019` to `studio080`)

### 💻 Zoom Recordings
- Online via Zoom and Zencastr (`zoom001` to `zoom020`)

---

## 📝 Session Details

### 📖 Script Session
Actors performed 3 predetermined sentences, each repeated twice per emotion with two emotional intensities (normal and strong), plus a neutral expression.

| Sentence ID | Thai Sentence | English Translation |
|-------------|---------------|---------------------|
| 1 | พรุ่งนี้มันวันหยุดราชการนะรู้รึยัง หยุดยาวด้วย | Do you know tomorrow is a public holiday and it's the long one. |
| 2 | อ่านหนังสือพิมพ์วันนี้รึยัง รู้ไหมเรื่องนั้นกลายเป็นข่าวใหญ่ไปแล้ว | Have you read today's newspaper? That story was the topliner. |
| 3 | ก่อนหน้านี้ก็ยังเห็นทำตัวปกติดี ใครจะไปรู้หล่ะ ว่าเค้าคิดแบบนั้น | He/She was acting normal recently; who would have thought they'd think like that? |

### 🎬 Improvisation Session
Actors improvised conversations according to provided scenarios with specific emotions.

|Scenarios|Actor A|Actor B|
|:-------:|-------|-------|
|1|(Neutral) A hotel receptionist trying to explain and service the customer|(Angry) A angry customer who dissatisfy the hotel services|
|2|(Happy) A person excitingly talking with B about his/her marriage plan|(Happy) A person happily talking with A and help him/her plan his ceremony|
|3|(Sad) A patient feeling depressed|(Neutral) A doctor attempting to talk with A neutrally|
|4|(Angry) A furious boss talking with the employee|(Frustrated) A frustrated person attempting to argue with his/her boss|
|5|(Frustrated) A person frustratingly talk about another person's action|(Sad) A person feeling guilty and sad about his/her action|
|6|(Happy) A happy hotel staffs|(Happy) Happy customer|
|7|(Sad) A sad person who felt unsecured about the incoming marriage|(Frustrated) A person who frustrated about another person's insecureness|
|8|(Frustrated) A frustrated patience|(Neutral) A Doctor talking with the patience|
|9|(Neutral) A worker who assigned to tell his/her co-worker about the company's bad situation|(Sad) An employee feeling sad after listenning|
|10|(Angry) A person raging about another person's behavior |(Angry) A person who feels like being blamed by another person|
|11|(Frustrated) A director who unsatisfied co-worker|(Frustrated) A frustrated person who try their best on the job|
|12|(Happy) A person who gets a new job or promotion|(Sad) A person who desperate in his/her job|
|13|(Neutral) A patient inquire information |(Happy) A happy doctor telling his/her patience more information |
|14|(Angry) A person who upset with his/her work|(Neutral) A calm friend who listened to another person's problem|
|15|(Sad) A person sadly tell another person about a relationship|(Angry) A person who feels angry after listening to another person's bad relationship|

---

## 📋 Data Schema
The dataset includes detailed annotations and actor demographics (see header above).

---

## 📊 Dataset Statistics

| Recording Environment | Session         | Utterances | Duration (hrs) |
|-----------------------|-----------------|------------|----------------|
| Zoom (20)             | Script          | 2,398      | 4.03           |
|                       | Improvisation   | 3,606      | 5.89           |
| Studio (80)           | Script          | 9,582      | 13.69          |
|                       | Improvisation   | 12,268     | 18.01          |
| **Total (100)**       | **Both**        | **27,854** | **41.61**      |

---

## 📄 Paper

The associated research paper will be available soon at [link will be updated soon](null).

---

## 💻 Code for Experiments

Experiment code is available on [GitHub](https://github.com/tann9949/thaiser-experiments/tree/main).

---

## 🔖 Version
- **Version 2.0 (April 15, 2025):** Fixed majority agreement calculation.
- **Version 1.0 (March 26, 2021):** Initial release.

---

📌 **Citation**

Please cite this dataset as:
```
@article{Wongpithayadisai2026,
  author  = {Wongpithayadisai, Jilamika and Chaksangchaichot, Chompakorn and Sangnark, Soravitt and Prakrankamanant, Patawee and Gangwanpongpun, Krit and Boonpunmongkol, Siwa and Milindasuta, Premmarin and Na-Pombejra, Dangkamon and Nutanong, Sarana and Chuangsuwanich, Ekapol},
  title   = {Thai Speech Emotion Recognition ({THAI-SER}) Corpus},
  journal = {Language Resources and Evaluation},
  year    = {2026},
  volume  = {60},
  number  = {3},
  pages   = {59},
  doi     = {10.1007/s10579-026-09932-w},
  url     = {https://doi.org/10.1007/s10579-026-09932-w},
  issn    = {1574-0218}
}
```
