# World Action Models (WAM) 综合调研报告

> 调研目标：为后续 WAM（World Action Model，结合视频生成/世界模型与机器人动作预测的模型）二次开发提供全面、可落地的技术基础参考。
> 调研原则：**不局限于 FastWAM 引用的文献**，优先覆盖 GitHub star 高、论文引用量大、社区活跃、有大量二次开发/复现/对比工作的项目；同时收录 Google DeepMind、Meta、NVIDIA、Physical Intelligence 等业界巨头的代表性工作，以及 2018 年以来有奠基意义的早期世界模型工作。
> 报告生成时间：2026-08-03。所有 star 数、更新时间均为调研时刻的快照，请以链接页面实时数据为准。

---

## 目录

1. [核心结论摘要（TL;DR）](#1-核心结论摘要tldr)
2. [技术脉络与架构范式演化](#2-技术脉络与架构范式演化)
3. [开源项目全景调研（分级排序）](#3-开源项目全景调研分级排序)
   - 3.1 生态枢纽 / 元框架
   - 3.2 一线大厂基础世界模型 / 平台
   - 3.3 FastWAM 直接相关工作（联合视频-动作 WAM）
   - 3.4 学术界代表性 WAM / VLA-World-Model 工作
   - 3.5 早期奠基性世界模型（RL / 游戏领域）
   - 3.6 未开源或代码不可获得的重要工作（仅供了解思路）
4. [常见数据集调研](#4-常见数据集调研)
5. [开发建议](#5-开发建议)
6. [参考链接汇总](#6-参考链接汇总)

---

## 1. 核心结论摘要（TL;DR）

- **WAM（World Action Model）** 这一术语本身是 2025-2026 年才逐渐清晰化的概念，指"用视频生成/世界模型的能力同时（或串行）建模未来观测与机器人动作"的一类模型，介于纯 VLA（如 OpenVLA、pi0）和纯世界模型（如 Genie、Dreamer）之间。
- 从**生态活跃度**看，目前最值得作为开发基础的分三个层次：
  1. **`huggingface/lerobot`（2.6万+ star）**：机器人学习的事实标准框架，已经原生集成 **FastWAM、LingBot-VA、pi0/pi0.5、GR00T N1.5、SmolVLA** 等策略和标准化的 `LeRobotDataset` 格式，是目前社区资源最丰富、复现成本最低的入口。
  2. **`Physical-Intelligence/openpi`（1.3万+ star）**与**`NVIDIA/Isaac-GR00T`（7700+ star）**：虽然核心不是"联合视频-动作"WAM，但都是目前最活跃、文档最好的通用机器人基座模型，且都在往"世界模型化"方向演进（GR00T N1.5 + FLARE/DreamGen，pi0.5 的 co-training 思路），是理解 WAM 设计动机的最佳参照系。
  3. **`NVIDIA/Cosmos` 系列（主仓 1.1万+ star）**：全球最大规模的开源世界基础模型平台，`cosmos-predict`/`cosmos-transfer`/`cosmos-reason`/`cosmos-policy` 构成了完整的"视频预测→控制策略"技术栈，文档、Cookbook、社区讨论量远超学术小组的一次性代码释出。
- 从**"直接对标 FastWAM 的联合视频-动作 WAM"**这个细分方向看，目前最值得参考的三个代码仓库是 **Motus（清华 thu-ml）**、**LingBot-VA（灵初/Robbyant）**、**DreamZero（NVIDIA GEAR）**——三者都基于 Wan 视频基座（Wan2.1/Wan2.2）、文档详实、License 宽松（Apache-2.0/MIT）、且都以 RoboTwin 2.0 / LIBERO / DROID 为评测基准，可相互交叉验证。
- **Genie（1/2/3）、UniSim** 官方均未开源核心权重与训练代码（Genie 1 有高质量第三方复现 `myscience/open-genie`，UniSim 官方仓库几乎是空壳），只能作为架构思路参考，不能作为开发基础。**FLARE、GR-2、Gen2Act** 三个常被引用的"video-representation-for-policy"工作**均未公开代码**，需要标注清楚以免浪费复现精力。
- Meta 的 **V-JEPA 2 / V-JEPA2-AC**（facebookresearch/vjepa2，4400+ star）代表了与"视频生成"路线平行的**非生成式（JEPA，隐空间预测）**世界模型路线，是唯一一个非扩散/非自回归、真正做到"63小时机器人数据 zero-shot 跨实验室部署"的开源工作，值得作为架构对比的另一极。

---

## 2. 技术脉络与架构范式演化

### 2.1 历史脉络（时间线）

| 阶段 | 时间 | 代表工作 | 核心思想 |
|---|---|---|---|
| **奠基期：RL 世界模型** | 2018-2023 | Ha & Schmidhuber *World Models*（2018）、PlaNet（2019）、Dreamer / DreamerV2 / DreamerV3（2020-2023） | 在游戏/仿真环境中学习紧凑的**隐空间**世界模型（RSSM），在"想象"中训练 actor-critic 策略；不涉及真实视频生成，不面向机器人真实动作 |
| **视频生成介入：Video-as-Plan** | 2022-2024 | UniPi（2023）、AVDC、UniSim（2023）、RoboDreamer（2024）、IRASim（2024） | 用（条件）视频生成模型直接"想象"未来观测序列，把决策问题转化为视频生成问题；动作通常靠额外的逆动力学模型（IDM）或轨迹跟踪器从生成视频中反推 |
| **交互式世界模型 / 无监督隐动作** | 2024 | **Genie**（DeepMind）、iVideoGPT（THU，NeurIPS 2024） | 从无标注视频中学习**隐动作空间**（Latent Action Model），实现"无动作标签"也能训练可控世界模型；为后续大规模无标注视频预训练 WAM 铺路 |
| **视频表征用于策略（不显式生成未来帧）** | 2024 | VPP（Video Prediction Policy）、GR-2、Gen2Act | 利用预训练视频扩散模型的**中间表征**作为策略的视觉特征，推理时不需要真正跑完整个视频生成过程，兼顾"世界知识"与推理效率 |
| **联合视频-动作建模（Joint WAM）** | 2024-2025 | UWM（统一世界模型）、UVA（Unified Video Action）、Vidar、Motus、LingBot-VA、Cosmos Policy | 用同一个 Transformer/DiT 主干，通过共享注意力**同时**对未来视频 token 和动作 token 做扩散/流匹配去噪；这是目前"WAM"一词最常指代的架构，FastWAM 论文称之为范式 A |
| **因果/先视频后动作（Causal WAM）** | 2024-2025 | GR00T-Dreams/DreamGen、Genie Envisioner、部分 Vidar 变体 | 先自回归/扩散生成未来视频（或视频 latent rollout），再基于生成结果条件化动作头；FastWAM 论文称之为范式 B，代表作是用世界模型**生成合成数据**再训练动作头（DreamGen 路线） |
| **统一自回归 VLA + World Model** | 2025 | WorldVLA / RynnVLA-002（阿里达摩院） | 把理解、生成、动作统一到一个自回归 token 词表里（类似多模态 LLM），世界模型的"预测下一帧"和 VLA 的"预测下一动作"共享同一套 next-token-prediction 机制 |
| **隐式世界建模（不生成像素）** | 2025 | DreamVLA（NeurIPS 2025）、FLARE（NVIDIA，未开源） | 不生成显式未来视频帧，而是预测压缩的未来**特征/动态先验**，作为动作头的辅助监督信号，兼顾"世界知识注入"与训练/推理效率 |
| **单次前向 / 训练测试解耦（Single-pass WAM）** | 2026 | **FastWAM** | 训练时仍与视频生成任务联合训练（获取世界知识），但推理时**跳过显式未来预测**，只做一次前向直接输出动作，兼顾"WAM 的知识"与"标准 VLA 的速度"（约 190ms 级延迟） |
| **非生成式（JEPA）世界模型路线** | 2022-2025 | I-JEPA → V-JEPA → **V-JEPA 2 / V-JEPA2-AC**（Meta） | 不在像素空间生成未来帧，而在**隐表征空间**做预测（联合嵌入预测架构），用极少量机器人数据（62小时 DROID）后训练出可零样本跨实验室部署的动作条件预测器 |
| **全模态统一世界基础模型** | 2025-2026 | **NVIDIA Cosmos 3**（Mixture-of-Transformers，融合 Predict/Transfer/Reason/Policy） | 用统一的 MoT 架构把"视觉语言理解（Reasoner）"和"视频/动作生成（Generator）"融为一个模型，一次前向即可同时具备推理、世界生成、动作生成能力，代表了 WAM 概念的"平台化"终局形态 |

### 2.2 三大主流架构范式（FastWAM 论文视角 + 本报告补充）

```
范式 A：联合建模 WAM (Joint-modeling WAM)
  [历史帧+语言] → 共享 Transformer/DiT → 同时去噪【未来视频 token】+【动作 token】
  代表：UWM、UVA、Vidar、Motus、LingBot-VA、Cosmos Policy
  优点：视频与动作互相提供梯度监督，表征共享；训练全程都在"学习世界"
  缺点：推理时仍需生成视频 token（即使只用其部分），延迟高

范式 B：因果/先视频后动作 WAM (Causal / Video-then-Action WAM)
  [历史帧+语言] → 视频生成模型 rollout 未来帧/未来latent → 动作头基于生成结果预测动作
  代表：GR00T-Dreams (DreamGen)、Genie Envisioner、UniSim+IDM、IRASim+planning
  优点：视频生成模块可独立复用/替换（如直接用预训练 Cosmos-Predict），常用于"生成海量合成数据再离线训练动作头"
  缺点：误差沿链条累积；在线推理时需要完整视频 rollout，延迟更高，通常用于数据增广而非实时控制

范式 C：单次前向 WAM (Single-pass WAM, FastWAM)
  训练：[历史帧+语言+动作] 与 [历史帧+语言→未来视频] 联合训练（多任务/MoT）
  推理：[历史帧+语言] → 单次前向 → 动作（不生成未来视频）
  代表：FastWAM
  优点：保留联合训练带来的"世界知识"，同时推理速度接近纯 VLA
  缺点：需要精心设计训练目标权重，避免"世界建模"任务喧宾夺主

附：隐式路线 (Implicit World Modeling)
  不生成像素级未来帧，而是预测紧凑的"未来特征/动态表征"作为辅助监督
  代表：DreamVLA、FLARE（未开源）、V-JEPA2-AC（隐空间而非像素空间）
```

### 2.3 常见视频/世界模型基座

| 基座模型 | 归属 | 参数量 | 被哪些 WAM 采用 |
|---|---|---|---|
| Wan2.1 / Wan2.2（I2V/TI2V） | 阿里通义万相 | 1.3B/5B/14B | FastWAM(5B)、Motus(5B)、LingBot-VA、DreamZero(14B)、Vidar(5B) |
| Cosmos-Predict 1/2/2.5 | NVIDIA | 2B/7B/14B | Cosmos Policy、GR00T-Dreams(DreamGen)、大量 NVIDIA 生态项目 |
| Qwen3-VL / Qwen2.5-VL | 阿里 | 2B/7B | Motus（Qwen3-VL-2B 作为语言/视觉理解分支）、多数 VLA 的 VLM backbone |
| umt5-xxl（文本编码器） | Google | - | DreamZero（配合 Wan2.1） |
| PaliGemma / SigLIP | Google | 3B | pi0/pi0.5、openpi 生态 |

---

## 3. 开源项目全景调研（分级排序）

> 表格字段说明：★ = GitHub Star（调研时快照）；"更新" = 最近一次 push 时间；"许可证" 已尽量核实至仓库 LICENSE 文件原文（而非仅 GitHub 徽章）；"依赖基座" 指其依赖的预训练视频/视觉语言模型；"硬件需求" 为官方 README 明确给出或可推断的训练/推理配置。

### 3.1 生态枢纽 / 元框架（最重要，优先接入）

| 项目 | 链接 | ★ | 许可证 | 更新 | 说明 |
|---|---|---|---|---|---|
| **LeRobot** | [huggingface/lerobot](https://github.com/huggingface/lerobot) | **26,154** | Apache-2.0 | 持续活跃 | Hugging Face 出品的机器人学习**元框架**，统一了 `LeRobotDataset`（Parquet+MP4）数据格式、真实硬件接口（SO-100 等低成本机械臂）与训练/推理脚本。**已原生收录 FastWAM、LingBot-VA、pi0、pi0.5、pi0-FAST、GR00T N1.5、SmolVLA、XVLA 等策略**，是目前社区资源、教程、Discord/论坛讨论量最大的项目，强烈建议作为统一开发底座。 |

### 3.2 一线大厂基础世界模型 / 平台

| 项目 | 链接 | ★ | 许可证 | 更新 | 框架/硬件 | 说明 |
|---|---|---|---|---|---|---|
| **NVIDIA Cosmos（主仓，Cosmos 3）** | [NVIDIA/Cosmos](https://github.com/nvidia/Cosmos) | **11,311** | NVIDIA Open Model License（非纯 Apache/MIT，商用需查阅条款） | 活跃 | PyTorch，MoT 架构，16B(Nano)/64B(Super) | 全球规模最大的开源"世界基础模型"平台，Cosmos 3 将 Predict(生成)/Transfer(可控生成)/Reason(推理)/Policy(动作) 四大能力统一进单一 Mixture-of-Transformers 模型，一次前向可同时输出推理、视频、动作 |
| ├ cosmos-predict2.5 | [nvidia-cosmos/cosmos-predict2.5](https://github.com/nvidia-cosmos/cosmos-predict2.5) | 1,335 | Apache-2.0 | 活跃 | Flow-matching，融合 Text/Image/Video2World | 纯"世界视频预测"子模型，可独立用作 WAM 的视频生成分支 |
| ├ cosmos-transfer2.5 | [nvidia-cosmos/cosmos-transfer2.5](https://github.com/nvidia-cosmos/cosmos-transfer2.5) | ~706 | Apache-2.0 | 活跃 | 多模态条件可控视频生成 | 用于 sim-to-real 域迁移、合成数据增广 |
| ├ cosmos-reason1 | [nvidia-cosmos/cosmos-reason1](https://github.com/nvidia-cosmos/cosmos-reason1) | ~952 | Apache-2.0 | 活跃 | 物理常识推理 VLM | 常作为 WAM 的语言/推理理解分支（Cosmos Policy 即用其做 backbone） |
| ├ cosmos-predict1 | [nvidia-cosmos/cosmos-predict1](https://github.com/nvidia-cosmos/cosmos-predict1) | 454 | Apache-2.0 | 一般 | 上一代 Predict 模型 | 已被 Predict2.5 取代，仅历史参考 |
| **Cosmos Policy** | [nvlabs/cosmos-policy](https://github.com/nvlabs/cosmos-policy) | 847 | Apache-2.0 | 活跃 | PyTorch，基于 Cosmos-Reason1 | 用 Cosmos 生态直接产出动作策略，评测覆盖 LIBERO / RoboCasa / ALOHA，是 Cosmos 系里离"WAM"定义最近的子项目 |
| **NVIDIA Isaac GR00T (N1/N1.5)** | [NVIDIA/Isaac-GR00T](https://github.com/NVIDIA/Isaac-GR00T) | **7,730** | Apache-2.0 | 非常活跃（最近一次 2026-07-30） | PyTorch，DiT 流匹配动作头 + VLM | 通用人形/双臂机器人基础模型，虽核心不生成显式未来视频，但通过 **FLARE**（隐式未来特征预测头）与 **DreamGen**（世界模型合成数据）两条路线深度融合了世界模型思想，文档、Cookbook、社区微调教程非常完善 |
| **openpi (π0 / π0.5 / π0-FAST)** | [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) | **13,122** | Apache-2.0 | 活跃（最近 2026-06-16） | JAX + PyTorch 双实现 | Physical Intelligence 官方开源，是目前被复现/对比最多的通用 VLA 基线之一；pi0.5 引入了协同训练（co-training）与更强的跨场景泛化，是很多 WAM 论文的核心 baseline |
| **V-JEPA 2 / V-JEPA2-AC** | [facebookresearch/vjepa2](https://github.com/facebookresearch/vjepa2) | 4,424 | MIT | 活跃（2026-03） | PyTorch，1.2B 参数 JEPA | Meta 出品，**非生成式**世界模型路线代表：在隐空间（而非像素空间）做视频预测，仅用 62 小时无标签 DROID 机器人视频后训练出可 zero-shot 部署到不同实验室 Franka 机械臂的动作条件预测器（V-JEPA2-AC），是理解"生成式 vs. 判别式/JEPA 式"两条 WAM 技术路线分野的关键参照 |

### 3.3 FastWAM 直接相关工作（联合视频-动作 WAM，用户最初关注列表）

| 项目 | 链接 | ★ | 许可证 | 更新 | 框架 | 依赖基座 | 硬件需求 | 评测环境 | 备注 |
|---|---|---|---|---|---|---|---|---|---|
| **FastWAM** | [yuantianyuan01/FastWAM](https://github.com/yuantianyuan01/FastWAM) | 1,237 | **MIT**（README 徽章显示 Other，但 LICENSE 原文为 MIT） | 活跃 | PyTorch 2.7.1+cu128，DeepSpeed ZeRO-1 | Wan2.2-5B（TI2V） | 单卡推理 RTX 5090D 32GB 可行；训练需多卡 | LIBERO、RoboTwin 2.0 | 用户当前研究对象，"训练联合、推理单次前向"，文档结构清晰，HF 数据集配套完整 |
| **Motus** | [thu-ml/Motus](https://github.com/thu-ml/Motus) | ~1,220 | Apache-2.0 | 活跃 | PyTorch 2.7.1，CUDA 12.8 | Wan2.2-5B + Qwen3-VL-2B | 训练需 A100/H100/B200，>80GB 显存/卡；推理约 24-40GB | RoboTwin 2.0、LeRobotDataset 格式 | 清华 ML 组出品，**文档质量最佳**（独立 DATA_FORMAT.md / TRAINING.md / INFERENCE.md），代码风格规范，License 更宽松，推荐作为主力参考实现之一 |
| **LingBot-VA** | [Robbyant/lingbot-va](https://github.com/Robbyant/lingbot-va) | ~1,716 | Apache-2.0 | 活跃 | Python 3.10.16，PyTorch 2.9.0，CUDA 12.6，**FSDP** 分布式训练 | Wan2.2 VAE | 单卡推理 24GB（i2av 模式 18GB） | RoboTwin 2.0、LIBERO | 灵初智能/Robbyant 出品，已被 LeRobot 收录；FSDP 训练管线对多机扩展友好；注意其 `attn_mode` 需要在训练(flex)/推理(torch|flashattn)间手动切换，是常见踩坑点 |
| **DreamZero** | [dreamzero0/dreamzero](https://github.com/dreamzero0/dreamzero) | ~2,516 | Apache-2.0 | 活跃 | Python 3.11，PyTorch 2.9.1，CUDA 12.9+，DeepSpeed ZeRO-2 | **Wan2.1-I2V-14B-480P** + umt5-xxl | 至少2张 H100/GB200 级 GPU（14B 大模型） | DROID、AgiBot World | NVIDIA GEAR 实验室出品，是目前唯一**从零训练在真实大规模数据（DROID）**上的 14B 级 WAM，算力门槛最高，Star 数增长最快 |
| **UWM (Unified World Model)** | [WeirdLabUW/uwm](https://github.com/WeirdLabUW/uwm) | 数百（API 波动未能精确抓取，建议直接查看仓库页面） | 需查阅仓库 | - | PyTorch | 独立视频扩散 + 动作扩散头，联合去噪 | 中等（学术级单机多卡可训练） | 仿真+真实机操作任务 | 华盛顿大学 WEIRD Lab 出品，是"联合建模范式"较早、代码相对轻量的学术实现，适合理解范式 A 的最小可行实现 |
| **Vidar** | [thu-ml/vidar](https://github.com/thu-ml/vidar) | 42 | 参考论文 Apache-2.0 | 一般 | PyTorch | Wan2.2-TI2V-5B | 中等 | RoboTwin | 清华出品但社区热度低（42★），代码可读性一般，仅建议作为设计思路参考，不建议作为主力复现底座 |
| **UVA (Unified Video Action)** | [ShuangLI59/unified_video_action](https://github.com/ShuangLI59/unified_video_action) | 400 | MIT | 一般 | PyTorch | 轻量视频扩散（非大规模预训练基座） | **低**（提供 Colab/PushT 玩具任务demo，单卡可跑） | PushT、真实机操作 | RSS 2025 论文，**入门友好度最高**——不依赖 14B 级大模型，适合先跑通"联合视频-动作扩散"最小实验，再迁移到大模型 |
| **VPP (Video Prediction Policy)** | [roboterax/video-prediction-policy](https://github.com/roboterax/video-prediction-policy) | 407 | MIT | 一般 | PyTorch | 预训练视频扩散模型的中间表征 | 中等 | CALVIN、真实机 | ICML 2025，代表"范式：视频表征用于策略"而非显式生成，推理时无需完整视频 rollout，速度优势明显 |

### 3.4 学术界代表性 WAM / VLA-World-Model 工作

| 项目 | 链接 | ★ | 许可证 | 更新 | 说明 |
|---|---|---|---|---|---|
| **WorldVLA / RynnVLA-002** | [alibaba-damo-academy/RynnVLA-002](https://github.com/alibaba-damo-academy/RynnVLA-002)（原 WorldVLA 仓库已重定向至此） | 1,106 | Apache-2.0（参考 README） | 活跃（2025-12） | 阿里达摩院出品，统一自回归 VLA + 世界模型，理解/生成/动作共享一套 token 词表，是"自回归统一路线"的代表 |
| **DreamVLA** | [Zhangwenyao1/DreamVLA](https://github.com/Zhangwenyao1/DreamVLA) | 364 | 参考论文 | 活跃（2026-01） | NeurIPS 2025，"隐式世界建模"代表：预测压缩动态先验而非显式像素，兼顾世界知识注入与效率 |
| **Genie Envisioner** | [AgibotTech/Genie-Envisioner](https://github.com/AgibotTech/Genie-Envisioner) | 566 | 参考仓库 | 活跃 | 智元机器人出品，统一的机器人世界基础平台，基于 AgiBot World 数据预训练（GE-Base），支持世界模型驱动的仿真评测 |
| **NVIDIA GR00T-Dreams (DreamGen)** | [NVIDIA/GR00T-Dreams](https://github.com/NVIDIA/GR00T-Dreams) | 593 | Apache-2.0 | 一般（2025-10） | "用世界模型生成合成训练数据"路线的代表作，先用视频世界模型 rollout 出大量新场景/新任务的想象视频，再提取(伪)动作标签训练 GR00T 策略头，属于范式 B |
| **iVideoGPT** | [thuml/iVideoGPT](https://github.com/thuml/iVideoGPT) | 186 | MIT | 活跃（2025-09） | NeurIPS 2024，清华出品，自回归 Transformer + 压缩 VQGAN token 化，是"从无标注视频/动作数据中预训练可扩展世界模型"的代表工作，后续衍生出 RLVR-World |
| **IRASim** | [bytedance/IRASim](https://github.com/bytedance/IRASim) | 159 | Apache-2.0 | 一般（2025-07） | ICCV 2025，字节跳动出品，DiT + 帧级动作条件模块，强调"细粒度动作-帧对齐"，附带独立 Benchmark 和 HuggingFace 数据集 |
| **RoboDreamer** | [UMass-Embodied-AGI/robodreamer](https://github.com/UMass-Embodied-AGI/robodreamer) | 0 | - | 几乎无提交（仅创建于2025-03） | 组合式世界模型思路有一定学术影响，但**代码仓库基本空置**（0 star/0 fork），不具备可复现性，仅作为论文思路参考 |

### 3.5 早期奠基性世界模型（RL / 游戏领域，非机器人真实动作，但对理解 WAM 起源至关重要）

| 项目 | 链接 | ★ | 许可证 | 说明 |
|---|---|---|---|---|
| **World Models（Ha & Schmidhuber, 2018）官方复现** | [hardmaru/WorldModelsExperiments](https://github.com/hardmaru/WorldModelsExperiments) | 718 | - | 原始论文作者仓库，VAE+RNN+进化策略，"世界模型"一词的起点 |
| World Models PyTorch 复现（社区最常用） | [ctallec/world-models](https://github.com/ctallec/world-models) | 699 | MIT | 社区引用/fork 最多的 PyTorch 版本，常被后续教程直接采用 |
| **DreamerV3**（Mastering Diverse Domains through World Models, 2023） | [danijar/dreamerv3](https://github.com/danijar/dreamerv3) | 3,596 | MIT | Danijar Hafner 官方仓库，单一超参数横跨 150+ 任务（含 DayDreamer 机器人真实部署分支），是"隐空间世界模型 + 想象中训练策略"范式的巅峰之作，论文引用量大（DreamerV1系列合计上千次引用），常作为 model-based RL 基线 |

### 3.6 未开源或代码不可获得的重要工作（仅供了解设计思路，不建议作为复现基础）

| 项目 | 归属 | 现状 | 说明 |
|---|---|---|---|
| **Genie（1代）** | Google DeepMind | 官方**未开源**，仅论文+博客 | 11B 参数，从 20万小时无标注游戏视频学习隐动作空间；第三方 PyTorch 复现见 [myscience/open-genie](https://github.com/myscience/open-genie)（292★，MIT，社区较认可的非官方实现） |
| **Genie 2 / Genie 3** | Google DeepMind | 官方**未开源**，仅提供受限 Web 体验（Project Genie） | Genie 2（2024-12，3D 世界生成）、Genie 3（2025-08，实时 720p/24fps 交互世界生成），代表工业界世界模型天花板，但完全闭源，无法用于自建训练 |
| **UniSim** | Google DeepMind | 官方仓库 `universal-simulator/unisim` 存在但**几乎空置**（仅 3★，无实质训练代码释出） | 只能参考论文思路（多数据集编排训练"动作-视频"统一模拟器），实操建议改用 iVideoGPT / IRASim / Cosmos-Predict 等有实际代码的替代方案 |
| **FLARE** | NVIDIA | 官方**未公开独立代码仓库**，仅作为 GR00T N1.5 内部模块提及 | "预测未来隐特征"的辅助监督头，思路可参考 DreamVLA 的公开实现做近似复现 |
| **GR-2** | 字节跳动 ByteDance Research | **未开源** | 大规模视频生成预训练 + GR-1 式动作头，只有论文和项目页 demo 视频 |
| **Gen2Act** | Google DeepMind | **未开源** | "用生成的人类操作视频指导机器人动作"思路，只有论文和项目页 |

---

## 4. 常见数据集调研

| 数据集 | 规模 | 数据形式 | 采集方式 | 下载地址 | 主要用途 | 与 WAM 的适配性 |
|---|---|---|---|---|---|---|
| **LIBERO** | 130 个任务，分 4-5 个套件（Spatial/Object/Goal/Long/90），单套件约50 demo/task | RGB 视频（含手腕相机）+ 关节/末端动作 + 语言指令；单臂（Franka Panda） | 仿真（MuJoCo/robosuite）中人工遥操作采集 | 官方: [libero-project.github.io](https://libero-project.github.io/)；HF: `physical-intelligence/libero` 等社区镜像 | 预训练+微调+**评测 benchmark**（最常用的 sim-to-sim 快速验证集） | **适配性极高**：FastWAM、Motus、LingBot-VA、Cosmos Policy、RynnVLA-002、openpi 均以 LIBERO 作为核心评测集，数据体量小（LeRobot 格式约几GB），是跑通训练/推理管线的首选 |
| **RoboTwin 2.0** | 50+ 双臂协作任务，10万+ 条轨迹（含大量 domain randomization 变体） | RGB(D) 多视角（通常 3 视角）+ 双臂关节/末端动作 + 语言指令 | **仿真生成**（SAPIEN），程序化 domain randomization（光照/纹理/物体位姿） | 官方: [robotwin-platform.github.io](https://robotwin-platform.github.io/)；HF: `TianxingChen/RoboTwin2.0` 等 | 预训练 + 微调 + 评测（双臂场景的主流 benchmark） | **适配性极高**：FastWAM、Motus、LingBot-VA 均以此为核心评测/训练集；需注意 SAPIEN + Vulkan 驱动在无头服务器上的安装踩坑 |
| **CALVIN** | 约 24 小时人类遥操作"自由玩耍"数据，4 个环境（A/B/C/D），34 项子任务，长程语言指令组合 | RGB(D) 多视角 + 末端位姿动作 + 自然语言标注 | 真实/仿真混合的遥操作"play"数据（非任务导向式，长时程自由探索） | 官方: [github.com/mees/calvin](https://github.com/mees/calvin) | 微调 + 语言条件长程任务评测 | 适配性高：VPP、DreamVLA 均以 CALVIN 为评测集，是验证"语言长程理解 + 世界模型"结合能力的经典基准 |
| **SimplerEnv** | 覆盖 Google Robot 与 WidowX/Bridge 两套评测套件，共约十余项任务 | 仅提供**仿真评测环境**（不含用于预训练的原始 demo 数据） | 基于 SAPIEN/ManiSkill 复现真实机器人视觉/物理，用于"真实策略的仿真复现评测"（real-to-sim） | 官方: [github.com/simpler-env/SimplerEnv](https://github.com/simpler-env/SimplerEnv) | **纯评测 benchmark**，用于低成本复现 RT-1/RT-1-X/Octo 等策略在真实机器人上的表现排名，不用于预训练 | 中等：主要用于评测基于 RT-1/Bridge 训练的策略，是否直接支持 WAM 联合视频-动作训练需要额外适配（无原生动作-视频对齐的大规模训练集） |
| **Open X-Embodiment (OXE)** | 100万+ 条轨迹，22种以上机器人本体，527+ 技能，160k+ 任务，来自 60 个数据集聚合 | RGB(有的含深度/多视角) + 各类动作空间（关节/末端/离散） + 语言指令；跨本体（单臂/双臂/移动机器人/灵巧手） | 真实机器人遥操作数据的**大规模跨机构聚合**（RT-1、Bridge、Language-Table 等原始数据集合并统一格式） | 官方: [robotics-transformer-x.github.io](https://robotics-transformer-x.github.io/)；HF/RLDS 格式下载 | **大规模预训练**（跨本体泛化能力的核心来源） | 适配性极高：RT-X、Octo、OpenVLA、pi0、iVideoGPT 预训练均直接使用；是当前"通用机器人基座模型"预训练的事实标准数据源 |
| **BridgeData V2** | 约6万条轨迹，覆盖24个环境、13类技能 | RGB（含多个第三人称视角）+ 末端位姿动作 + 语言指令；单臂（WidowX 250） | 真实机器人**人工遥操作** + 少量脚本化数据 | 官方: [rail-berkeley.github.io/bridgedata](https://rail-berkeley.github.io/bridgedata/) | 预训练 + 微调（OXE 的重要组成子集之一，也可独立使用） | 高：SimplerEnv 的 WidowX/Bridge 评测套件直接基于此数据的环境复现；iVideoGPT、UniSim 等世界模型预训练也采用此数据 |
| **RT-1 / RT-2 数据** | RT-1: 约13万条真实机器人操作轨迹（约700+任务） | RGB + 离散化动作 tokens + 语言指令；单臂（移动操作机器人 Everyday Robots） | 真实机器人遥操作，Google 内部大规模采集 | 数据已并入 OXE；论文: [RT-1](https://robotics-transformer1.github.io/)、[RT-2](https://robotics-transformer2.github.io/) | 预训练（大规模真实数据的早期代表） | 高：IRASim、SimplerEnv 均直接使用 RT-1 数据/环境作为评测对象；RT-2 本身未开源权重，但方法论（VLM 直接输出动作token）被广泛借鉴 |
| **AgiBot World** | Beta 版 100万+ 条轨迹，200+ 任务，100+ 真实场景 | RGB 多视角 + 双臂/灵巧手动作 + 语言指令；人形/双臂机器人 | 真实机器人**人工遥操作**，智元机器人大规模自建采集农场 | 官方: [agibot-world.com](https://agibot-world.com/)；HF: `agibot-world/AgiBotWorld-Beta` | 预训练（面向人形/双臂通用操作的大规模基座数据） | 高：Genie Envisioner（GE-Base）、DreamZero 均直接使用其预训练；是目前中文社区最大规模的开源真机数据集之一 |
| **DROID** | 约7.6万条轨迹/350+小时，564个场景，86类任务，遍布13个机构 | RGB-D 三视角（含腕部相机）+ 末端/关节动作 + 语言指令；单臂（Franka Panda） | 真实机器人遥操作，多机构众包式大规模采集 | 官方: [droid-dataset.github.io](https://droid-dataset.github.io/) | 预训练 + 跨场景泛化能力评测 | **适配性极高**：DreamZero 直接以此从零训练 14B WAM；V-JEPA2-AC 仅用其中62小时数据后训练即可 zero-shot 部署；openpi 预训练数据的重要组成部分 |
| **RoboMIND** | 约10.7万条轨迹，479项任务，96类物体，覆盖4种本体 | RGB(D) 多视角 + 动作 + 语言指令，含"失败演示"标注；多本体（Franka/UR5e/AgileX/天工人形） | 真实机器人遥操作 + 部分失败案例数据 + Isaac Sim 数字孪生环境配套 | 官方: [x-humanoid-robomind.github.io](https://x-humanoid-robomind.github.io/) | 预训练 + 微调（国产多本体基座数据的代表） | 中高：因含数字孪生环境和失败数据，特别适合训练"世界模型+失败恢复"相关的 WAM 变体，但社区案例相对新，直接被引用训练 WAM 的公开工作还较少 |

---

## 5. 开发建议

### 5.1 推荐的二次开发路径（按学习曲线从低到高）

1. **第一步：用 LeRobot 跑通标准 VLA baseline。** 先在 `huggingface/lerobot` 上用 LIBERO（LeRobot 格式，几GB体量）跑通 ACT/Diffusion Policy/pi0 中任意一个策略的训练+评测闭环，熟悉 `LeRobotDataset` 格式和标准评测协议。这一步几乎零踩坑成本，且后续所有 WAM 工作的数据/评测格式都可与之对齐。
2. **第二步：跑通一个"轻量级联合视频-动作"WAM 的最小实现。** 推荐 `UVA`（MIT协议、有 PushT/Colab demo、不依赖14B级大模型），目的是理解范式 A（联合视频-动作扩散）的最小可行架构，而不是一上来就啃 Wan2.2-5B 级别的大模型训练。
3. **第三步：对齐 FastWAM 本身，并交叉参考 Motus / LingBot-VA。** 三者都基于 Wan2.2 系视频基座、都以 RoboTwin 2.0 + LIBERO 为评测集，代码结构和数据格式高度可比，适合相互对照调试（例如 FastWAM 遇到训练不稳定问题时，可以参考 Motus 的 `TRAINING.md` 排查超参）。
4. **第四步（如有充足算力）：尝试 DreamZero 或 Cosmos Policy，体验 14B 级别真机数据从零训练/大规模预训练基座的完整流程。** 这一步对硬件要求陡增（多卡 A100/H100/GB200 级），建议仅在已验证小规模管线可行后再投入。
5. **平行支线：如果关注"非生成式/隐空间"路线，研究 V-JEPA2-AC。** 其代码相对独立、不依赖巨型视频扩散基座，用极少量机器人数据（62小时）即可训练出动作条件预测器，是验证"世界模型是否真的需要生成像素"这一问题的最佳对照实验。

### 5.2 数据集选择建议

- **快速验证管线是否work**：LIBERO（数据小、下载快、社区文档最多）或 UVA 自带的 PushT 玩具任务。
- **验证双臂/多视角能力**：RoboTwin 2.0（但需提前解决 SAPIEN + Vulkan 在服务器/容器环境下的驱动安装问题，这是社区最常见的"卡住"环节）。
- **验证真实机器人泛化能力**：DROID（体量适中、场景/机构多样性好、有 V-JEPA2-AC/DreamZero/openpi 三个不同技术路线的先例可对比）。
- **验证长程语言指令能力**：CALVIN（VPP、DreamVLA 已验证过的经典基准）。
- 不建议一开始就直接用 AgiBot World / OXE 全量做预训练（数据量TB级，下载和存储成本高），建议先用其官方提供的小规模子集/采样版本跑通流程。

### 5.3 常见踩坑与注意事项

1. **License 差异需提前核实**：FastWAM 徽章显示 "Other" 但 LICENSE 原文其实是 MIT；NVIDIA Cosmos 系列使用 "NVIDIA Open Model License"（并非纯 Apache/MIT，商用前需仔细阅读条款）；Motus/UVA/VPP/DreamZero/GR00T/openpi/LeRobot 均为 Apache-2.0 或 MIT，相对更宽松。二次开发/商用前务必逐一核实 LICENSE 原文而非只看 GitHub 徽章。
2. **显存/算力差异巨大，选型前先核算**：Wan2.2-5B 级模型（FastWAM/Motus）训练通常需要 >80GB 显存/卡（A100-80GB/H100/B200），推理可压到 24-32GB 单卡；Wan2.1-14B 级模型（DreamZero）训练需要多张 H100/GB200 级 GPU，个人/小团队应优先选择 5B 级基座起步。
3. **基座模型版本要严格匹配**：Wan2.1 与 Wan2.2 的噪声调度、VAE、文本编码器接口存在差异，务必确认所选 WAM 代码库要求的具体基座版本（如 DreamZero 明确要求 Wan2.1-I2V-14B-480P + umt5-xxl，不能随意替换为 Wan2.2）。
4. **注意力实现模式的训练/推理切换**：LingBot-VA 等项目要求训练用 `flex attention`、推理切回 `torch`/`flashattn`，若在 config 中未手动切换会导致推理报错或结果异常，这是一个常见但容易被忽略的配置项。
5. **依赖版本高度敏感，建议使用官方提供的 lock 文件/精确版本号**：如 LingBot-VA 要求 `diffusers==0.36.0`、`transformers==4.55.2`、`lerobot==0.3.3 --no-deps` 等精确版本，跨项目环境经常冲突，建议用 `uv`/`conda` 为每个 WAM 项目单独建环境，不要共用。
6. **仿真环境安装是常见拦路虎**：RoboTwin 2.0（SAPIEN）在无头服务器/Docker 环境下经常遇到 Vulkan 驱动缺失或版本不匹配问题，建议提前查阅 RoboTwin 官方 Issue 区的环境配置经验帖。
7. **评测协议不完全可比，复现论文数字前需确认设置**：不同工作在"是否见过评测指令(seen/unseen)""是否使用多次rollout取平均""任务成功判定标准"等细节上可能不同（FastWAM 论文中即指出部分 baseline 使用了不同的评测协议），交叉对比时应以自己复现结果为准，不宜直接横向比较论文报告数字。
8. **未开源工作不要花时间"找代码"**：Genie 1/2/3、UniSim（官方仓库实质空置）、FLARE、GR-2、Gen2Act、RoboDreamer（仓库空置）均不具备可复现代码，只应作为架构设计的思路参考，避免在寻找/等待代码开源上消耗过多时间。

---

## 6. 参考链接汇总

### 开源代码仓库
- LeRobot: https://github.com/huggingface/lerobot
- NVIDIA Cosmos（主仓）: https://github.com/nvidia/Cosmos
- Cosmos-Predict2.5: https://github.com/nvidia-cosmos/cosmos-predict2.5
- Cosmos-Transfer2.5: https://github.com/nvidia-cosmos/cosmos-transfer2.5
- Cosmos-Reason1: https://github.com/nvidia-cosmos/cosmos-reason1
- Cosmos-Predict1: https://github.com/nvidia-cosmos/cosmos-predict1
- Cosmos Policy: https://github.com/nvlabs/cosmos-policy
- NVIDIA Isaac GR00T: https://github.com/NVIDIA/Isaac-GR00T
- NVIDIA GR00T-Dreams (DreamGen): https://github.com/NVIDIA/GR00T-Dreams
- openpi (π0/π0.5): https://github.com/Physical-Intelligence/openpi
- V-JEPA2: https://github.com/facebookresearch/vjepa2
- FastWAM: https://github.com/yuantianyuan01/FastWAM
- Motus: https://github.com/thu-ml/Motus
- LingBot-VA: https://github.com/Robbyant/lingbot-va
- DreamZero: https://github.com/dreamzero0/dreamzero
- UWM: https://github.com/WeirdLabUW/uwm
- Vidar: https://github.com/thu-ml/vidar
- UVA: https://github.com/ShuangLI59/unified_video_action
- VPP: https://github.com/roboterax/video-prediction-policy
- WorldVLA / RynnVLA-002: https://github.com/alibaba-damo-academy/RynnVLA-002
- DreamVLA: https://github.com/Zhangwenyao1/DreamVLA
- Genie Envisioner: https://github.com/AgibotTech/Genie-Envisioner
- iVideoGPT: https://github.com/thuml/iVideoGPT
- IRASim: https://github.com/bytedance/IRASim
- RoboDreamer: https://github.com/UMass-Embodied-AGI/robodreamer
- Genie（非官方复现）: https://github.com/myscience/open-genie
- World Models（官方）: https://github.com/hardmaru/WorldModelsExperiments
- World Models（社区常用 PyTorch 版）: https://github.com/ctallec/world-models
- DreamerV3: https://github.com/danijar/dreamerv3

### 论文/项目主页
- FastWAM: https://arxiv.org/pdf/2603.16666
- Genie: https://arxiv.org/abs/2402.15391 ｜ Genie 2: https://deepmind.google/blog/genie-2-a-large-scale-foundation-world-model/ ｜ Genie 3: https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/
- World Models (Ha & Schmidhuber 2018): https://worldmodels.github.io/
- DreamerV3: https://arxiv.org/abs/2301.04104
- UniSim: https://universal-simulator.github.io/ ｜ https://arxiv.org/abs/2310.06114
- iVideoGPT: https://arxiv.org/abs/2405.15223 ｜ https://thuml.github.io/iVideoGPT/
- IRASim: https://arxiv.org/abs/2406.14540 ｜ https://gen-irasim.github.io/
- V-JEPA 2: https://arxiv.org/abs/2506.09985 ｜ https://ai.meta.com/blog/v-jepa-2-world-model-benchmarks/
- π0: https://arxiv.org/abs/2410.24164 ｜ π0.5: https://arxiv.org/abs/2504.16054

### 数据集
- LIBERO: https://libero-project.github.io/
- RoboTwin 2.0: https://robotwin-platform.github.io/
- CALVIN: https://github.com/mees/calvin
- SimplerEnv: https://github.com/simpler-env/SimplerEnv
- Open X-Embodiment: https://robotics-transformer-x.github.io/
- BridgeData V2: https://rail-berkeley.github.io/bridgedata/
- RT-1: https://robotics-transformer1.github.io/ ｜ RT-2: https://robotics-transformer2.github.io/
- AgiBot World: https://agibot-world.com/
- DROID: https://droid-dataset.github.io/
- RoboMIND: https://x-humanoid-robomind.github.io/

### 综述/导航资源
- Awesome Video Action Models: https://github.com/zhiheng-ma/awesome-video-action-models
- Awesome VLA (yueen-ma): https://github.com/yueen-ma/Awesome-VLA
