# EmotionTalk：对话上下文候选数据集（已保留）

审计日期：2026-11-09。结论：**适合研究“同一段目标音频，在加入真实过去对话后，模型判断是否改变、是否更接近音频标注”**。已保留官方 Audio.tar 中的全部原始 WAV 和 JSON，没有下载视频或 Multimodal.tar，也没有启动模型推理或任何付费服务。

## 实际下载到了什么

| 项目 | 本地实测 |
| --- | ---: |
| WAV / 对应音频标注 JSON | 各 19,250 个，全部一一对应 |
| 音频总时长 | 23.6025 小时 |
| 有音频的对话 | 742 段 |
| 两位 speaker 均有已发布片段的对话 | 734 段 |
| 只有一位 speaker 有片段的对话 | 8 段，共 169 个片段 |
| 发布的 speaker ID | 19 个，跨录制组复用 |
| 含至少两种音频情绪标签的对话 | 735 段 |
| 存在完整过去轮次的目标 | 18,467 个 |
| 排除单 speaker 对话后的主要候选目标 | 18,306 个 |
| 至少有一个完整过去对方轮次的目标 | 17,713 个 |

每个 WAV 的头信息与全部 PCM payload 均检查通过；没有缺失音频、未配对 WAV、重复音频引用、JSON 解析失败或超过阈值的时长不一致。原始下载包的字节数和 SHA256 与官方 LFS 元数据一致，见 `source_manifest.json`。

原包为 14,811,722,752 bytes；解包后的 WAV 合计 14,750,323,934 bytes。没有为了节省空间而更改音频。18,612 个是 stereo / 44.1 kHz / PCM16，518 个是 mono / 44.1 kHz，120 个是 mono / 16 kHz。运行模型时再按模型要求 downmix / resample；不能假定所有文件格式相同。

## 为什么它能用于上下文实验

JSON 提供 `speaker_id`、转写、同一录制对话内的 `startTime` / `endTime`，文件名含 group、session、speaker 和 utterance index。**按时间戳合并两位 speaker 的片段**，可以恢复相互接话的顺序，而不是任意拼接不同录音。

我们的保守历史规则是：只加入同一 `dialogue_id` 中，`endTime <= 目标 startTime + 1ms` 的完整轮次。1ms 仅作为时间舍入容差。早于目标开始、但仍与目标重叠的轮次，不作为完整过去输入。4,033 个目标开始时存在尚未结束的较早轮次，因此不能简单取文件名的前几个音频。`utterances.csv` 已导出完整过去轮次数、最近三轮路径、同一 speaker / 对方历史轮次数和主要候选标记。

可以先对同一批目标比较：只有目标音频；目标加真实过去音频；目标加打乱的过去音频。这样才能检查帮助是否来自真实对话关系。只给模型音频或实验预先约定的转写，**不提供过去轮次 gold labels、目标 JSON 的 caption 或目标 gold label**。

`pilot_examples.json` 给出七种标签各一个 test 例子。比如 `G00015_53_21_017` 的目标只有“对不起。”，0.885 秒，音频标签为 `sad`；前文包含“你早干嘛去了？……我等了你八年”。这证明有可复核的真实对话内容可以供实验使用，**尚不能证明给出前文一定会提高模型表现**。

## 标签和划分应怎样使用

使用 **Audio/json 中的 `emotion_result`** 作为音频任务的发布 gold label，不使用演员意图或 caption 代替它。实际七类分布如下：

| 标签 | 音频数 |
| --- | ---: |
| neutral | 9,378 |
| angry | 3,820 |
| happy | 2,105 |
| surprised | 1,363 |
| sad | 1,110 |
| disgusted | 818 |
| fearful | 656 |

每个片段均含五位标注者的情绪判断和置信度。原文件置信度取值为 1、3、5、7、9；论文使用相应缩放后的 0.1、0.3、0.5、0.7、0.9，并描述了置信度聚合及争议复核。151 个最终标签不是简单多数票，375 个也不是按文件中各类平均置信度直接取最大值的结果；这是需保留的发布标签与投票诊断差异，不应自行覆盖官方 gold，也不把投票比例说成官方概率。

沿用官方组别划分，`G00001/G00012` 为 validation，`G00003/G00015` 为 test，其余为 train。

| 划分 | 片段数 | 实际对话数 | 双人对话的历史候选目标 |
| --- | ---: | ---: | ---: |
| train | 15,413 | 587 | 14,747 |
| validation | 1,908 | 71 | 1,729 |
| test | 1,929 | 84 | 1,830 |

train 与另外两部分的发布 speaker IDs 不重叠；**validation 与 test 共享 IDs `02`、`13`**。因此不能称三个官方划分互相 speaker-disjoint。19 个发布 ID 与论文演员数一致，但我们没有通过声纹独立验证人的身份。

## 需要在论文中说清楚的限制

- 这是专业演员围绕主题进行的即兴双人对话，属于受控采集的对话数据，不能称为未经安排的日常生活录音。
- 音频标注与其他模态分开进行，但论文附录说明标注平台允许回听过去轮次。因此，音频 gold 不能被称为“人类只听孤立目标句时的判断”。它也没有对同一音频提供“无上下文 / 有上下文”两套人类标签。
- 官方论文写 744 段对话，当前固定版本 Audio.tar 实际只有 742 个非空对话目录；不为凑数补造数据。
- HF README 总表的 neutral 数是 6,853；实际音频标签为 9,378（48.7%），与论文音频模态占比吻合。README 表中比例与论文 multimodal 分布相符，不能直接把该总表当作音频 gold 分布。
- 八个对话在发布音频中只包含一位 speaker 的片段，保留原文件以供复核，主要双人分析用 `primary_dyadic_history_target=True` 排除它们。转写包含重叠、打断、笑声等标记，使用转写时应另行固定清理规则。
- 该数据适合作为中文补充验证，不能与英语 MELD 的差异全归因于上下文；语言、录制方式、类别和标注流程也都不同。

## 文件说明与复核

- `Audio/wav/`、`Audio/json/`：官方 Audio.tar 原始内容，未改动。
- `utterances.csv`：逐片段标签、投票摘要、时间、speaker、划分及安全过去轮次索引。
- `dialogues.csv`：逐对话 speaker 数、情绪种类、时长和候选目标数。
- `audit.json`：完整计数、检查结果、异常清单和限制。
- `pilot_examples.json`：可直接定位到原 WAV / JSON 的例子；其中标签仅用于审计展示。
- `source_manifest.json`：固定上游版本、原包字节数和 SHA256。
- `review_dataset.py`：仅本地标准库审计；可执行 `python emotiontalk/review_dataset.py --audit-only` 重新读取 WAV / JSON 并生成审计表。运行位置为包含 `emotiontalk/` 的目录，不下载数据、不调用模型。
- `upstream/HF_README.md`、`LICENSE-CC-BY-NC-SA-4.0.txt`、`LICENSE_REVIEW.json`：保留来源、许可证和访问条款核实记录。

## 来源、署名与许可

原数据集：**EmotionTalk: An Interactive Chinese Multimodal Emotion Dataset With Rich Annotations**，Haoqin Sun、Jinghua Zhao、Xuechen Wang、Shiwan Zhao、Jiaming Zhou、Hui Wang、Xi Yang、Yequan Wang、Yonghua Lin，Findings of ACL 2026。

- [官方数据及固定版本](https://huggingface.co/datasets/BAAI/Emotiontalk/tree/adbc17fc944e8cf2873643906160c6ca0259ab61)
- [正式论文](https://aclanthology.org/2026.findings-acl.440/)
- [官方代码](https://github.com/flageval-baai/EmotionTalk)
- [CC BY-NC-SA 4.0 许可](https://creativecommons.org/licenses/by-nc-sa/4.0/)

**这不是 MIT 许可。** 原始数据遵循 CC BY-NC-SA 4.0：保留署名、非商业使用、同许可分享。本地新增了索引、审计报告和说明，原始音频 / 标注没有修改；这些随数据提供的派生内容也按同一许可分享。原作者不为本地审计结论背书。HF 当前为免费 automatic gate：访问要求账户登录并同意分享 HF 信息，不涉及订阅或付费下载；当前卡片未发现额外禁止再分发条款，具体核实记录见 `LICENSE_REVIEW.json`。
