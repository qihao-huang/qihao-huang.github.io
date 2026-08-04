# 估算FastWAM训练与测试时长
_Exported on 2026/8/4 at GMT+8 11:19:11 from Cursor (3.14.7)_

---

**User**

请基于已知信息，对 FastWAM（论文：Fast-WAM: Do World Action Models Need Test-time Future Imagination?，arXiv:2603.16666；代码库：https://github.com/yuantianyuan01/FastWAM）估算其"单次完整训练配置"所需的训练时长，以及"测试/评测"所需的时长，给出有依据的估算范围（而不是拍脑袋），并说明估算方法和假设。

## 已知信息（来自论文与README，你可以直接使用，无需重新调研）

**模型规模与结构**：
- 基于 Wan2.2-5B 视频DiT backbone（复用其预训练文本编码器T5和视频VAE）
- 额外增加一个隐藏维度 d_a=1024 的 Action Expert（约1B参数）
- 总参数量约 6B（Mixture-of-Transformer架构，视频分支与动作分支共享注意力）
- action horizon h=32，视频帧时间下采样4倍，每个chunk 9帧视频
- 训练用 flow matching loss（同时训练动作和视频共训练目标），AdamW lr=1e-4, weight decay=0.01, cosine退火, 混合精度训练，梯度裁剪1.0
- 推理时用10步去噪 + CFG scale=1.0

**训练配置（来自README及论文Experiment Setup）**：
- LIBERO: 4个suite (Spatial/Object/Goal/Long)，每suite 500条demo，共训练 20k steps，官方用 8×GPU (DeepSpeed ZeRO-1, `train_zero1.sh`)
- RoboTwin 2.0: 50+任务，2500条干净场景demo + 25000条强域随机化demo，共训练 30k steps，官方用 64×GPU
- 真实机器人任务(叠毛巾): 60小时遥操作数据，训练30k steps
- 训练前需要先做:
  1. preprocess_action_dit_backbone.py 预处理ActionDiT backbone(从Wan2.2插值而来)
  2. precompute_text_embeds.py 预计算T5文本embedding缓存(单卡或`torchrun --nproc_per_node=8`多卡)

**推理/测试配置**：
- 论文中所有延迟数据在单张 NVIDIA RTX 5090D V2 32GB GPU上测得: Fast-WAM本身约190ms/action chunk推理延迟(单次前向,10步去噪)
- 对比: Fast-WAM-IDM(先生成视频再生成动作)延迟810ms
- LIBERO评测: 2000 trials覆盖40个任务(4 suite × 10 task)，不同随机种子；官方评测脚本默认 MULTIRUN.num_gpus=8 并行
- RoboTwin评测: 50+任务，每任务100 trials，覆盖clean和randomized两种设置(即每任务200次rollout)；官方评测脚本默认 MULTIRUN.num_gpus=8 并行

## 你需要完成的估算任务

### 1. 训练时长估算
请估算：
- **LIBERO单次完整训练**(8卡, 20k steps)大约需要多少小时/天
- **RoboTwin单次完整训练**(64卡, 30k steps)大约需要多少小时/天
- 需要说明每个训练step大约耗时多少秒的估算依据。可以通过以下方式获取依据（按优先级）：
  a) 搜索FastWAM的GitHub仓库(issues、README、代码注释)是否有训练时长/吞吐量(steps/sec 或 samples/sec)的直接说明
  b) 搜索Wan2.2-5B官方仓库/论文/博客中关于该backbone的训练/推理吞吐量数据(在何种GPU上，多大batch size, 多少步/秒)，作为类比估算基础
  c) 基于6B参数量、常见DiT/Transformer模型在H100/A100/RTX 4090/5090等GPU上的每步训练时间的一般经验数据（结合flow matching训练每step只需1次forward+backward，不同于扩散模型采样需多步）进行合理估算
  d) 如果找不到直接数据，请基于模型FLOPs估算（用6B参数、典型batch size、H100/A100算力峰值和常见MFU(模型算力利用率30-50%)进行fermi估算），并明确注明这是理论估算而非实测

- 同时需要考虑：预处理步骤(preprocess_action_dit_backbone.py, precompute_text_embeds.py)各自大约耗时多久（这两步通常是一次性的、相对训练本身较短，但仍需给出估算或说明其量级）

### 2. 测试/评测时长估算
请估算：
- **单次action chunk推理**: 已知190ms（这个是已知值，直接引用）
- **LIBERO完整评测**(2000 trials, 8卡并行)大约需要多少小时。需要考虑：单个trial/episode包含多个action chunk的推理(需要估算一个episode平均需要多少次推理调用，可参考LIBERO任务的典型episode长度，通常几百步，因此需要 步数/action_horizon 次chunk推理)，以及仿真环境本身的step仿真开销(不仅仅是模型推理时间，因为LIBERO/RoboTwin基于MuJoCo等物理仿真，其env.step()也有耗时)
- **RoboTwin完整评测**(50+任务×200 trials, 8卡并行)大约需要多少小时
- 请说明这里的不确定性来源（比如仿真环境的实际吞吐量因任务复杂度、渲染分辨率、CPU性能而异，是本估算中最大的不确定因素）

### 3. 总结
给出一个总的时间预算表格：训练(LIBERO/RoboTwin/真实机器人)、评测(LIBERO/RoboTwin)、单次推理，附上估算的时间范围（给出下限-上限，而不是单一数值），并清晰说明每个数字的估算方法和可信度(高/中/低)。

## 输出要求
用中文输出一份简洁但有理有据的估算报告，使用markdown表格汇总所有时间估算，并列出你在调研中查阅到的具体依据链接(如果查到了GitHub issue、Wan2.2仓库的吞吐量数据等，请附上链接)。如果关键数据缺失只能用理论推算，请诚实说明这一点，不要给用户过度自信的假数据。

---

**Cursor**

# FastWAM 训练/评测时长估算报告

## 0. 方法论说明

由于论文和 README 均**未直接公布** steps/sec 或 GPU-hours，本估算采用三级证据强度：

| 优先级 | 方法 | 本报告采用情况 |
|---|---|---|
| ① 直接实测数据 | FastWAM GitHub issues 中用户自述的训练耗时 | ✅ 找到 1 条关键数据（issue #65） |
| ② 类比数据 | Wan2.2-5B 官方/社区训练吞吐量 | ⚠️ 找到的数据训练范式差异大，只作交叉校验 |
| ③ Fermi/FLOPs 理论估算 | 6B 参数 × batch × 序列长度 / GPU 算力 × MFU | ✅ 作为量级校验 |
| ④ 仿真环境公开参数 | LIBERO/RoboTwin 官方 episode 长度、fps | ✅ 用于评测时长推算 |

以下所有数字均为**估算区间**，非实测值，已标注置信度。

---

## 1. 训练时长估算

### 1.1 关键证据：GitHub issue #65 的真实训练记录

在 [issue #65](https://github.com/yuantianyuan01/FastWAM/issues/65) 中，用户 `PKUduz` 报告：用 **2节点×8卡=16×NVIDIA L20X(143GB)**，per-GPU batch=16（global batch=256），训练 **117,415 步耗时约 3 天(72小时)**。

由此反推单 step 墙钟耗时（该配置下，16卡并行做一次 step）：

$$
t_{step} \approx \frac{72\times3600\text{s}}{117415} \approx 2.2\text{ s/step}
$$

因为官方 RoboTwin 配置的 **per-GPU batch 同样是 16**（[issue #8](https://github.com/yuantianyuan01/FastWAM/issues/8) 确认 global batch=1024=16×64），若假设官方使用同档位或更快的 GPU，单 step 耗时应在 **1.5–3.7 s/step** 区间（下限对应用更快的 H100/A100 级別GPU，上限对应 64 卡规模下 ZeRO-1 通信开销增大）。

### 1.2 Fermi/FLOPs 交叉校验

- 6B 参数，估计视频+动作联合序列长度 L≈3000–4000 tokens/样本（9帧×压缩后的空间token + h=32动作token，3摄像头384分辨率拼接）
- 每 GPU batch=16，训练一步 FLOPs（前向+反向≈6×N×L×B）≈ 2×10¹⁵ FLOPs
- H100 密集BF16峰值≈990TFLOPS，MFU 30–40%→ 有效 300–400TFLOPS
- 理论单步时间 ≈ **4–7 s/step**（H100级）

该理论值比 issue #65 的经验值（2.2s，且是在较弱的 L20X 上测得）**高出2-3倍**，说明实际实现（FlashAttention、算子融合、序列长度实际更短等）比朴素 Fermi 假设更高效，但两者**量级一致（个位数秒/step）**，可互相印证——这给了"每 step 若干秒"这一数量级中等置信度。

⚠️ Wan2.2-5B 生态另一条数据（[quanhaol/Wan2.2-TI2V-5B-Turbo](https://github.com/quanhaol/Wan2.2-TI2V-5B-Turbo)）：16×A100训练4000步耗时48小时，折合 **43s/step**，但这是 Self-Forcing 蒸馏训练（每步含多次自回归视频rollout），与 FastWAM 单次 flow-matching 前向+反向的训练目标**完全不同、不可比**，仅作为"同规模DiT训练确实是多GPU-天量级"的背景参考，不纳入主估算。

### 1.3 训练时长估算结果

| 训练任务 | 配置 | Step耗时假设 | **估算总时长** | 置信度 |
|---|---|---|---|---|
| **LIBERO** | 8×GPU, 20k steps, ZeRO-1 | 分辨率224×2cam，token量少于RoboTwin，估计0.9–1.8s/step | **4–12 小时** | 中低（从RoboTwin经验值按分辨率/相机数缩放外推，无直接数据点） |
| **RoboTwin** | 64×GPU, 30k steps, ZeRO-1, global batch 1024 | 1.5–3.7s/step（issue #65 经验值±GPU/规模不确定性） | **12–30 小时**（约0.5–1.3天） | 中（有真实用户训练记录直接外推） |
| **真实机器人(叠毛巾)** | GPU数未知（假设与LIBERO类似的单节点8卡），30k steps，60h遥操作数据 | 与RoboTwin同量级相机/分辨率 | **12–24 小时** | 低（GPU数量为假设值，README未给出） |

### 1.4 预处理步骤（一次性，非重复开销）

| 步骤 | 性质 | 估算耗时 | 置信度 |
|---|---|---|---|
| `preprocess_action_dit_backbone.py` | 从Wan2.2权重插值生成ActionDiT初始化，单进程权重级操作，I/O(加载/保存~10-20GB checkpoint)为主，几乎无迭代训练 | **5–30 分钟** | 低-中 |
| `precompute_text_embeds.py`（LIBERO） | T5前向缓存，任务指令数量少（~40任务） | **5–15 分钟** | 低-中 |
| `precompute_text_embeds.py`（RoboTwin） | 任务更多（50+任务+域随机化指令变体），支持8卡`torchrun`并行 | **10–30 分钟** | 低-中 |

这两步相对主训练（数小时到一天）确实是"量级更小"的一次性开销，符合README描述。

---

## 2. 测试/评测时长估算

### 2.1 单次推理（已知值，直接引用）

- Fast-WAM 单次 action chunk 推理：**190 ms**（单张RTX 5090D V2 32GB，10步去噪+CFG=1.0，论文实测值，**高置信度**）

### 2.2 关键仿真环境参数（用于推算每 episode 推理次数）

| 环境 | fps | 最大episode步数 | 来源 |
|---|---|---|---|
| LIBERO (Spatial/Object/Goal/Long) | 渲染80fps | 280/280/300/520 | [LeRobot libero.py](https://github.com/huggingface/lerobot/blob/main/src/lerobot/envs/libero.py) |
| RoboTwin 2.0 | 25fps | 300 | [HuggingFace RoboTwin文档](https://huggingface.co/docs/lerobot/main/robotwin) |

关键发现：FastWAM RoboTwin 评测配置中有 `EVALUATION.skip_get_obs_within_replan=true`（[README](https://github.com/yuantianyuan01/FastWAM/blob/main/README.md)），即**一次推理对应一个h=32步的"replan window"**，窗口内只执行动作、不做RGB渲染（仅在窗口边界重新渲染获取观测），这**直接印证了"步数/action_horizon=每episode推理次数"的估算方法**，且说明官方评测已针对渲染开销做了优化。

### 2.3 LIBERO评测时长估算

- 2000 trials，8卡并行 → 每卡约250 trials（假设串行执行，无进一步向量化并行的确认信息）
- 平均实际episode长度（早停成功情形通常短于max）估计 150–350 步 → 每episode推理次数 ≈ 5–11 次
- 单trial耗时 = 推理耗时(5-11×0.19s≈0.9-2.1s) + MuJoCo仿真/渲染耗时(150-350步×0.015-0.04s/步≈2.3-14s) + env reset开销(0.5-2s)
  ≈ **3.6–18 秒/trial**
- 总时长 = 250 trials/卡 × (3.6–18s) ≈ **0.25–1.25 小时**，取整估算区间：

**LIBERO完整评测 ≈ 0.3–2 小时**（置信度：中低）

### 2.4 RoboTwin评测时长估算

- 50个任务 × (100 clean + 100 randomized) = 约 **10,000 trials**，8卡并行 → 每卡约1250-1325 trials
- 最长300步(25fps)，因`skip_get_obs_within_replan`优化，物理step本身很轻（~1-5ms/步，无渲染），仅在每个chunk边界(约3-10次/episode)才做一次渲染+推理
- 单trial耗时 ≈ 物理仿真(300步×0.001-0.005s≈0.3-1.5s) + chunk渲染+推理(3-10×(0.01-0.05渲染+0.19推理)≈0.6-2.4s) + env/场景reset(双臂+域随机化场景较复杂，估计1-3s)
  ≈ **2–7 秒/trial**
- 总时长 = 1300 trials/卡 × (2-7s) ≈ **0.7–2.5 小时**，但考虑50个不同任务资产加载、复杂双臂动力学场景重置等额外开销，向上适当放宽：

**RoboTwin完整评测 ≈ 1.5–8 小时**（置信度：中低）

### 2.5 不确定性来源说明（评测部分是本报告置信度最低的部分）

1. **仿真环境实际吞吐量未知**：LIBERO用MuJoCo、RoboTwin用SAPIEN，实际env.step()+渲染耗时高度依赖CPU核心数、GPU渲染后端（EGL vs OSMesa）、场景复杂度，可能有数倍差异
2. **并行粒度未知**：不确定"8卡并行"是否等于"8个串行环境同时跑"，还是每卡内部还有多环境向量化（若有向量化，实际耗时可显著低于本估算）
3. **平均episode实际长度未知**：论文只给出最大步数，未给出成功/失败情形下的平均实际步数分布
4. **env/场景reset开销未知**：尤其RoboTwin域随机化场景（如物体位置、光照、纹理变化）的reset成本无直接数据

---

## 3. 总时间预算汇总表

| 类别 | 项目 | 估算时长范围 | 关键依据 | 置信度 |
|---|---|---|---|---|
| 预处理 | ActionDiT backbone插值 | 5–30 分钟 | 权重级操作，I/O主导（推理） | 低-中 |
| 预处理 | T5文本embedding缓存(LIBERO) | 5–15 分钟 | 任务指令数量少 | 低-中 |
| 预处理 | T5文本embedding缓存(RoboTwin) | 10–30 分钟 | 任务更多但仍为纯前向 | 低-中 |
| 训练 | **LIBERO**(8卡, 20k steps) | **4–12 小时** | 按RoboTwin经验值×分辨率/相机数缩放外推 | 中低 |
| 训练 | **RoboTwin**(64卡, 30k steps) | **12–30 小时**(约0.5–1.3天) | GitHub issue #65真实训练记录直接外推 + FLOPs交叉校验 | **中** |
| 训练 | **真实机器人**叠毛巾(30k steps) | **12–24 小时** | 与RoboTwin同量级，GPU数为假设 | 低 |
| 推理 | **单次action chunk** | **190 ms**（已知） | 论文实测(单卡RTX 5090D V2) | **高**(实测) |
| 评测 | **LIBERO**(2000 trials, 8卡) | **0.3–2 小时** | LIBERO官方episode长度 + h=32推算推理次数 | 中低 |
| 评测 | **RoboTwin**(约10000 trials, 8卡) | **1.5–8 小时** | RoboTwin fps=25/300步官方参数 + skip_get_obs优化确认chunk执行方式 | 中低 |

**要点提炼**：
- 训练时长中，**RoboTwin这一档估算置信度最高**，因为有 GitHub issue 里用户实测的真实训练耗时数据可直接外推；LIBERO和真实机器人训练则是缺少直接数据点、靠比例缩放得出的中低置信度估算。
- 评测时长的最大不确定性来源是**仿真环境本身的吞吐量和并行粒度**，而非模型推理（190ms相对于整个rollout只是次要开销，尤其RoboTwin默认开启了跳过chunk内渲染的优化后更是如此）。
- 所有区间均为 Fermi 级估算，如需精确数字，仍需在实际硬件上跑通 `train_zero1.sh` / `run_libero_manager.py` / `run_robotwin_manager.py` 做小规模计时外推（例如跑100 steps记录wall-clock时间，再线性外推到全量steps）。

## 参考链接

- [FastWAM GitHub仓库/README](https://github.com/yuantianyuan01/FastWAM)
- [issue #65：RoboTwin训练117k步耗时3天(16卡)](https://github.com/yuantianyuan01/FastWAM/issues/65)
- [issue #8：官方RoboTwin训练64卡/global batch 1024](https://github.com/yuantianyuan01/FastWAM/issues/8)
- [issue #60：评测MULTIRUN.num_gpus机制](https://github.com/yuantianyuan01/FastWAM/issues/60)
- [论文全文 arXiv:2603.16666](https://arxiv.org/html/2603.16666v2)
- [RoboTwin 2.0官方参数(fps=25, episode_length=300)](https://huggingface.co/docs/lerobot/main/robotwin)
- [LIBERO各suite最大步数(LeRobot实现)](https://github.com/huggingface/lerobot/blob/main/src/lerobot/envs/libero.py)
- [Wan2.2官方仓库/推理效率表](https://github.com/Wan-Video/Wan2.2)（背景参考，未直接用于训练时长估算）
- [Wan2.2-TI2V-5B-Turbo：16×A100训练4000步/48小时](https://github.com/quanhaol/Wan2.2-TI2V-5B-Turbo)（不同训练范式，仅作背景交叉参考）

