# MultiDialog：官方两个 test split，保留原件并限定评测队列

2026-11-10 核验。**已采用为第 16 个数据集，baseline 待跑**。只下载 `test_freq` 和 `test_rare`，没有下载全部 32.706 GB 音频库或视频，也没有启动模型推理或收费服务。

它适合补充英语对话历史实验，但属于**按 TopicalChat 剧本及指定情绪表演的对话**。当前队列通过了结构、音频可读性及文本/时长合理性检查；没有完成逐句听感评价或语义对齐验证，不能称为逐句多人听感 gold。

## 保留范围与默认 baseline 范围

| 范围 | 音频 | 对话 | 实测音频时长 |
| --- | ---: | ---: | ---: |
| 原始 test_freq | 9,810 | 450 | 见 audit.json |
| 原始 test_rare | 8,331 | 381 | 见 audit.json |
| 两个 test 原件合计 | **18,141** | **831** | **32.3997 h** |
| 两位演员均在官方 gold 名单，QC 前 | 7,801 | 359 | 13.4304 h |
| **默认 gold_both + 整对话 QC** | **7,672** | **353** | **13.0958 h** |
| 默认队列中有过去轮次的目标 | **7,319** | 同上 | 比较上下文条件时用相同目标交集 |

默认队列中 test_freq 为 **3,808 条 / 175 段**，test_rare 为 **3,864 条 / 178 段**。保留全部原件不等于全部原件进入默认评测。

原始两个压缩包共 **3,293,811,394 bytes**；WAV 均实测为 **16 kHz、mono、PCM16**，全部头信息与 PCM payload 长度检查通过，没有缺失、重复引用、全零音频、同字节 WAV 或断轮。每段都有两个发布 speaker IDs，两 split 的 dialogue IDs 没有交集；speaker IDs 有重叠，不能称 speaker-disjoint。

官方 README 的 test_freq 为 9,811 条、两 test 共 34.05 h；固定版本实际音频和 JSONL 均为 9,810 + 8,331 条、32.3997 h。**339.71 h 是官方全集数字，本机没有下载或审计全集。** 原论文录制为 48 kHz，HF 2024 年重新处理后的本次下载是 16 kHz，不混用两个口径。

## 标签是什么

JSONL 的 `emotion` 是 TopicalChat 剧本情绪，演员照此表演。实际原文件有八种字符串；按论文 §3.2 将 **`Curious to dive deeper` 并入 `neutral`**，其余规范成当前七类。`from=human/gpt` 是脚本角色字段，不是“GPT 合成了其中一人的音频”；speaker ID 从文件名末尾字母获取。

官方 gold actor 名单为 `a,b,c,e,f,g,i,j,k`，来源是小规模感知检查后选择表达识别率超过 40% 的演员。它不是为每个片段重新生成多人共识标签。默认 `gold_both` 要求整个对话的两位演员都在名单内，避免删除一方后仍声称保留完整双人历史。本地默认队列实际含 IDs `a,b,c,f,g,i`，其中 `a/b` 合计只有 21 条；不能把它描述成均衡覆盖全部 12 位演员。

默认 7,672 条的类别：neutral **5,284**、happy **1,064**、surprised **1,113**、sad **83**、disgusted **67**、angry **35**、fearful **26**。类别明显不均衡，应同时报告宏平均和逐类样本数。

## 为什么还要做本地 QC

可读 WAV 不一定与对应文本正确分段。实际发现过“16 个词只有 0.128 秒”、一段对话许多长句只有 0.192 秒，以及短结束语对应 34–298 秒音频。后三种长片并非纯零或纯尾部静音，具体原因未确定。

在**未运行任何模型、未看任何模型预测前**，根据第一轮源数据检查冻结以下规则（不是声称下载前已盲预注册）：

1. 用 `[A-Za-z0-9]+(?:'[A-Za-z]+)?` 计词；词数 ≥6 且词/秒 >8，标记不合理的文本/音频速度。
2. 音频 >30 秒且词/秒 <0.6，保守标记长音频与稀疏转写的可疑对应。
3. 任一片段触发就排除**整段对话**，使 H0 与各上下文条件使用同一套完整对话；原音频和原标签不改、不删。

规则共标记 **27 条 / 9 段对话**，涉及原始 192 条；其中 6 段属于 QC 前 gold_both，去掉 129 条，保留该候选的 **98.35% 音频、98.33% 对话**。默认队列最长 26.24 秒，最大文本速度 6.27 词/秒。通过筛查只表示没有触发这些结构/时长问题，不能保证每条语义对齐或情绪表达正确。

`qc_exclusions.csv` 列出每条触发片段、文本、时长、词速、原因及原 WAV SHA256；`excluded_dialogues.csv` 列出整段排除范围。`cohort_ids.json` 固定默认 baseline、dialogue 与 context 目标 IDs，附独立 SHA256，规则版本 `2026-11-10-v1`。不要静默改变规则后沿用旧结果缓存。

## 历史输入怎么恢复

在同一 `dialogue_id`、同一 split 内按 `turn_index` 排序，只取目标之前的轮次。索引提供最近三轮路径；全部检查过没有目标自身、未来轮次或跨对话混入。

发布 JSONL 没有 start/end 时间戳，因此这里只能保证**发布轮次顺序上的过去**，没有验证物理时间上的重叠。Haudio/Htext/Hshuffled 应使用相同目标、同一组历史 IDs 和预先约定的长度预算，不给模型历史 gold labels、目标 gold 或演员 gold 筛选分数。两 test split 应作为测试范围保留；提示选择/GEPA 的开发集需另行固定，不边看最终测试分数边改提示。

## 文件与恢复

- `audio/<split>/<conv_id>/*.wav`：全部官方两 test 原始音频，字节未改。
- `upstream/metadata/`、`upstream/HF_README.md`、`upstream/MultiDialog.py`：固定版本原始元数据与说明，未改。
- `utterances.csv`、`dialogues.csv`：规范标签、角色、speaker、时长、过去轮次、gold/QC/默认队列标记。
- `cohort_ids.json`、`qc_exclusions.csv`、`excluded_dialogues.csv`、`audit.json`：冻结范围和完整审计。
- `pilot_examples.json`：从最终 QC 队列选的可复核例子，标签仅用于展示。
- `source_manifest.json`：官方版本和下载包 LFS SHA256；`training_review.json`：八个模型的来源检查，没有据此宣称严格 unseen。
- `review_dataset.py`：标准库只读检查，验证全部 WAV SHA、源 JSONL、标签映射、QC、历史及 cohort hash。

数据仓库拉到含本条目的版本后：

```bash
python3 download.py multidialog
python3 download.py multidialog --verify-only
python3 multidialog/review_dataset.py
```

主项目默认 loader 是 `scripts/common/multidialog_dataset.py` 的 `load_multidialog_records(..., cohort="gold_both")`。`cohort="gold_actor"` 仍做整对话 QC，但只要求目标演员合格；`cohort="all"` 是包含 QC 排除项的原始审计视图，不是默认 baseline。

## 来源与许可

**Se Jin Park, Chae Won Kim, Hyeongseop Rha, Minsu Kim, Joanna Hong, Jeong Hun Yeo, Yong Man Ro. Let's Go Real Talk: Spoken Dialogue Model for Face-to-Face Conversation. ACL 2024.**

- [固定 HF 版本](https://huggingface.co/datasets/IVLLab/MultiDialog/tree/49a79605cf7f07c94f5d6f12ebddfed0be5e7986)
- [正式论文](https://aclanthology.org/2024.acl-long.860/)、[项目页](https://multidialog.github.io/)
- [CC BY-NC 4.0 数据许可](https://creativecommons.org/licenses/by-nc/4.0/)

当前官方数据卡和 API 均明确 **CC BY-NC 4.0**，免费、public、ungated，不是 MIT。旧 Python loader 的 Apache 字符串与数据卡不一致，不能用它把音频改成 Apache；保留代码原有声明，音频及新增索引/审计按 CC BY-NC 4.0 保留署名、来源、许可及更改说明。这里仅新增索引、QC 标记和报告，没有改原始音频/标签，原作者不为本地 QC 结论背书。
