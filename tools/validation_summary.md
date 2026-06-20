# 论文元数据与标签校验报告

生成时间：2026-06-20T13:19:28
校验论文数：2592
平均置信度：0.959
需人工复核：429 篇

## 1. 各类问题数量统计

| 问题类型 | 数量 |
|---------|------|
| 文件夹与内容不匹配 | 662 |
| 可能遗漏主题 | 556 |
| 疑似误标（零重叠） | 277 |
| 缺少摘要 | 250 |
| 缺少年份 | 179 |
| 重复标题不同 arXiv | 50 |
| 矛盾标签 | 33 |
| 垃圾标题模式 | 16 |
| 标题为文件名回退 | 2 |
| 年份不合理 | 1 |

## 2. 标签层级合理性分析

### 各层覆盖率

- **topic**：35.7% 论文有标签
- **method**：30.3% 论文有标签
- **task**：64.6% 论文有标签
- **modality**：37.5% 论文有标签
- **keyword**：98.7% 论文有标签

### 热门 topic 分布

- 3D Detection：195 篇
- SLAM / Localization：137 篇
- Tracking：132 篇
- World Model：123 篇
- VLA：121 篇
- BEV Perception：107 篇
- End-to-End Driving：92 篇
- Imitation Learning：75 篇
- Motion Planning：71 篇
- Robot Manipulation：57 篇

- 未分类（Uncategorized）：21 篇（65.1% 无有效 topic）
- folder 与 topic 冗余：0 篇（0.0%）
- 疑似误标总数：277

### 疑似误标 Top 标签

- `topic/World Model`：66 次
- `method/Foundation Model`：48 次
- `modality/Camera / Vision`：39 次
- `method/Transformer`：16 次
- `modality/LiDAR`：14 次
- `method/Reinforcement Learning`：12 次
- `topic/Force / Compliance`：10 次
- `method/LLM / VLM`：8 次
- `topic/VLA`：7 次
- `modality/IMU / Proprioception`：6 次
- `task/Segmentation`：6 次
- `topic/3D Detection`：6 次
- `topic/Data Collection`：6 次
- `task/Evaluation`：5 次
- `method/Generative Model`：4 次

### 疑似误标示例

- [method] `Distillation` — DEPTH ANYTHING 3: RECOVERING THE VISUAL SPACE FROM ANY VIEWS（3d-perception/）
- [method] `Foundation Model` — DINO: DETR with Improved DeNoising Anchor Boxes for End-to-End Object Detection（3d-perception/）
- [method] `Foundation Model` — M2BEV: Multi-Camera Joint 3D Detection and Segmentation with Unified Bird’s-Eye （BEV/）
- [method] `Foundation Model` — RoboBEV: Towards Robust Bird’s Eye View Perception under Corruptions（BEV/）
- [method] `Foundation Model` — OpenDriveVLA: Towards End-to-end Autonomous Driving with Large Vision Language A（LLM_AD/）
- [method] `Foundation Model` — Alpamayo-R1: Bridging Reasoning and Action Prediction for Generalizable Autonomo（VLA_E2E/）
- [method] `Foundation Model` — Alpamayo-R1: Bridging Reasoning and Action Prediction for Generalizable Autonomo（VLA_E2E/）
- [method] `Foundation Model` — Poutine: Vision-Language-Trajectory Pre-Training and Reinforcement Learning Post（competition/）
- [method] `Foundation Model` — SelFlow: Self-Supervised Learning of Optical Flow（paper-HKU/）
- [method] `Foundation Model` — 3DMatch: Learning Local Geometric Descriptors from RGB-D Reconstructions（paper-HKU/）
- [method] `Foundation Model` — Published as a conference paper at ICLR 2020（paper-HKU/）
- [method] `Foundation Model` — ExFuse: Enhancing Feature Fusion for Semantic Segmentation（paper-HKU/）
- [method] `Foundation Model` — How Well Do Self-Supervised Models Transfer?（paper-HKU/）
- [method] `Foundation Model` — High-Performance Large-Scale Image Recognition Without Normalization（paper-HKU/）
- [method] `Foundation Model` — UP-DETR: Unsupervised Pre-training for Object Detection with Transformers（paper-HKU/）

## 3. 文件夹分类 vs 内容一致性

- `paper-dynamic-geometry`：349 处不一致
- `BEV`：52 处不一致
- `WM-WAM`：42 处不一致
- `base-paper`：37 处不一致
- `WM`：30 处不一致
- `loop-sim`：26 处不一致
- `paper-video`：21 处不一致
- `humanoid`：14 处不一致
- `V-LLM`：13 处不一致
- `RL`：10 处不一致
- `planner-paper`：10 处不一致
- `sim`：9 处不一致
- `VLA`：9 处不一致
- `3d-perception`：7 处不一致
- `competition`：6 处不一致

## 4. 需人工复核清单（Top 50）

1. **3DV** — 置信度 0.43，文件夹 `paper-topics`，问题：title_is_filename, missing_abstract, missing_pub_year
2. **Di Monocular Piecewise Depth Estimation in Dynamic Scenes by Exploitin** — 置信度 0.59，文件夹 `paper-HKU`，问题：title_is_filename, missing_abstract
3. **Vision-Language-Action Models for Autonomous Driving: Past, Present, a** — 置信度 0.61，文件夹 `survey`，问题：missing_abstract, missing_pub_year, suspicious_tag
4. **1. ⼈形全⾝控制两⼤技术路线（⾏业现状） 路线 1：解耦式控制（主流、⼯程落地多） 下肢、上肢、⼒控、柔顺功能拆分设计，模块独⽴，稳定性强** — 置信度 0.66，文件夹 `force`，问题：suspicious_tag, missing_pub_year, contradictory_tag
5. **BEVFormer: 利用时空Transformer 从多相机** — 置信度 0.66，文件夹 `BEV`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
6. **在线高精矢量化地图构建** — 置信度 0.66，文件夹 `BEV`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
7. **Stereo Vision** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
8. **Stereo and 3D Vision** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
9. **Stereo Vision** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
10. **From Big to Small: Multi-Scale Local Planar Guidance for Monocular Dep** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
11. **基于传统方法的单目深度估计** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
12. **第５６卷 第１９期 激光与光电子学进展 Ｖｏｌ．５６，Ｎｏ．１９** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
13. **3.1.1 基于马尔科夫随机场的深度估计方法** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
14. **31.03.2020 19:16 Uhr Modulbeschreibung #40993 / 1 Seite 1 von 3** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
15. **Pyramidal Implemen tation of the AÆne Lucas Kanade F eature T rac k er** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
16. **Humboldt-Universität zu Berlin Mathematisch-Naturwissenschaftliche Fak** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
17. **第３２卷第９期 计算机应用与软件 Ｖｏｌ３２Ｎｏ．９ ２０１５年９月 ＣｏｍｐｕｔｅｒＡｐｐｌｉｃａｔｉｏｎｓａｎｄＳｏｆｔｗａｒｅ Ｓｅ** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
18. **Stereo Matching** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
19. **Estimating optical ﬂow** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
20. **Stereo Vision II: Dense Stereo Matching** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
21. **Two-View Stereo** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
22. **Estimating optical ﬂow** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
23. **Motion and ﬂow** — 置信度 0.66，文件夹 `paper-dynamic-geometry`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
24. **Deep Learning for Person Re-identification:** — 置信度 0.66，文件夹 `paper-video`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
25. **Towards Fully Convolutional** — 置信度 0.66，文件夹 `paper-video`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
26. **DeepSeek r1 闭门学习讨论｜ Best Ideas Vol 3** — 置信度 0.66，文件夹 `V-LLM`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
27. **Seed2.0 Model Card: Towards Intelligence Frontier for Real-World Compl** — 置信度 0.66，文件夹 `V-LLM`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
28. **Agentic Design Patterns** — 置信度 0.66，文件夹 `V-agent`，问题：missing_abstract, missing_pub_year, folder_content_mismatch
29. **Sparse BEV in Zhijia** — 置信度 0.66，文件夹 `BEV`，问题：missing_abstract, missing_pub_year
30. **Deep Generative Models** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
31. **Who is afraid of non­convex** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
32. **Deep Learning for Seman/c Segmenta/on** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
33. **Research 101 Paper Writing with LaTeX** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
34. **GCN INTRODUCTION AND ITS APPLICATION IN 3D POINT CLOUD SEMANTIC SEGMEN** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
35. **Self-supervised Learning: A** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
36. **语义流网络在语义分割中的应用** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
37. **申抒含 中国科学院自动化研究所 模式识别国家重点实验室** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
38. **Yuxin Wu, Alexander Kirillov, Francisco Massa,** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
39. **Dense 3D Geometry Es.ma.on** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
40. **Large-scale 3D Modeling from Crowdsourced Data** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
41. **Large-scale 3D Modeling from Crowdsourced Data** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
42. **Large-scale 3D Modeling from Crowdsourced Data** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
43. **Large-scale 3D Modeling from Crowdsourced Data** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
44. **Differentiable Rendering for** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
45. **Facing depth estimation in- the-wild with deep networks** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
46. **TRAINING NEURAL NETWORKS WITH TENSOR CORES** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
47. **Facing depth estimation in- the-wild with deep networks** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
48. **Facing depth estimation** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
49. **MIXED PRECISION TRAINING FOR VIDEO SYNTHESIS** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year
50. **September 2019** — 置信度 0.66，文件夹 `paper-HKU`，问题：missing_abstract, missing_pub_year

## 5. 联网校验样本

- ⚠ 需关注 **3DV**
  - 来源：semanticscholar, crossref
- ⚠ 需关注 **Di Monocular Piecewise Depth Estimation in Dynamic Scenes by**
  - 来源：semanticscholar, crossref
  - 标题相似度：0.692
  - 本地：Di Monocular Piecewise Depth Estimation in Dynamic Scenes by Exploiting Superpix
  - 在线：Monocular Piecewise Depth Estimation in Dynamic Scenes by Exploiting Superpixel 
- ✓ 匹配 **Vision-Language-Action Models for Autonomous Driving: Past, **
  - 来源：semanticscholar, crossref
  - 标题相似度：0.778
- ⚠ 需关注 **Sparse BEV in Zhijia**
  - 来源：semanticscholar, crossref
- ⚠ 需关注 **BEVFormer: 利用时空Transformer 从多相机**
  - 来源：semanticscholar, crossref
- ⚠ 需关注 **在线高精矢量化地图构建**
  - 来源：semanticscholar, crossref
- ✓ 匹配 **Deep Generative Models**
  - 来源：semanticscholar, crossref
  - 标题相似度：0.75
- ⚠ 需关注 **Who is afraid of non­convex**
  - 来源：semanticscholar, crossref
- ⚠ 需关注 **Deep Learning for Seman/c Segmenta/on**
  - 来源：semanticscholar, crossref
- ⚠ 需关注 **Research 101 Paper Writing with LaTeX**
  - 来源：semanticscholar, crossref
- ⚠ 需关注 **GCN INTRODUCTION AND ITS APPLICATION IN 3D POINT CLOUD SEMAN**
  - 来源：semanticscholar, crossref
  - 标题相似度：0.556
  - 本地：GCN INTRODUCTION AND ITS APPLICATION IN 3D POINT CLOUD SEMANTIC SEGMENTATION
  - 在线：Learning new representations for 3D point cloud semantic segmentation
- ⚠ 需关注 **Self-supervised Learning: A**
  - 来源：semanticscholar, crossref
- ⚠ 需关注 **语义流网络在语义分割中的应用**
  - 来源：semanticscholar, crossref
- ⚠ 需关注 **申抒含 中国科学院自动化研究所 模式识别国家重点实验室**
  - 来源：semanticscholar, crossref
- ⚠ 需关注 **Yuxin Wu, Alexander Kirillov, Francisco Massa,**
  - 来源：semanticscholar, crossref
- ⚠ 需关注 **Dense 3D Geometry Es.ma.on**
  - 来源：semanticscholar, crossref
- ⚠ 需关注 **Large-scale 3D Modeling from Crowdsourced Data**
  - 来源：semanticscholar, crossref
- ⚠ 需关注 **Large-scale 3D Modeling from Crowdsourced Data**
  - 来源：semanticscholar, crossref
- ⚠ 需关注 **Large-scale 3D Modeling from Crowdsourced Data**
  - 来源：semanticscholar, crossref
- ⚠ 需关注 **Large-scale 3D Modeling from Crowdsourced Data**
  - 来源：semanticscholar, crossref

## 6. 整体结论与改进建议

### 合理的类别设计
- **topic / method / task / modality 四层分离**清晰，覆盖率较高，适合驾驶/具身 AI 领域。
- **folder 层**作为用户手动分类的补充合理，与 FOLDER_TAGS 映射有效。
- **keyword 层**（TF-IDF）能捕捉语料 distinctive 术语，但需归一化大小写。

### 需改进的规则（paper_tagger.py）

1. **收窄过宽 topic**：`Tracking`、`Simulation` 等模式过于宽泛，建议要求更多上下文词（如 multi-object tracking vs generic tracking）。
2. **folder 回退逻辑**：当 folder 已指定 topic 但文本匹配到其他 topic 时，应保留文本匹配结果而非仅追加 folder tag（减少 folder_topic_mismatch）。
3. **keyword 归一化**：合并大小写变体（如 Self-Supervised vs self-supervised），统一为小写或 canonical form。
4. **增加 paper-video / paper-dynamic-geometry 到 FOLDER_TAGS**：目前大量论文在这些 catch-all 文件夹中，缺少 topic 回退。
5. **矛盾检测前置**：对 LLM/VLM、RL 等标签要求最低关键词命中数，避免 regex 误匹配（如单独 `rl\b` 匹配到其他词）。
