# NVIDIA Isaac GR00T N1.7 项目分析

这是 NVIDIA 的开源 **VLA (Vision-Language-Action)** 基础模型项目，目标是让人形/双臂机器人具备跨本体（cross-embodiment）的通用操作能力。以下从算法、架构、设计、数据四个维度拆解，并给出一条推荐的入门阅读路径。

---

## 1. 核心算法：VLM 主干 + Flow Matching 扩散动作头

模型是"看图/读语言 → 生成动作序列"的两段式结构：

```
图像+语言 → [VLM Backbone] → 视觉语言特征(vl_embeds)
                                     ↓ cross-attention
状态(state) → [State Encoder] ─┐
                                ├→ [DiT 扩散头] → 去噪动作序列 (action chunk)
噪声动作(noisy action) ────────┘
```

**关键算法是 Flow Matching（流匹配）**，而非常见的 DDPM 扩散：
- 训练时（`gr00t/model/gr00t_n1d7/gr00t_n1d7.py:228-235`）：从 Beta 分布采样时间 `t`，对真实动作 `actions` 与高斯噪声 `noise` 做线性插值 `noisy = (1-t)*noise + t*actions`，目标不是预测噪声而是预测**速度场** `velocity = actions - noise`，用 MSE 监督。
- 推理时（`get_action_with_features`，同文件 397-435 行）：从纯噪声出发，用固定步数（默认 `num_inference_timesteps=4`）做 **Euler 积分**：`actions += dt * pred_velocity`，只需 4 步就能生成一整段动作序列，比传统 100 步 DDPM 快得多——这是它能做到实时/高频控制的关键。
- 还实现了 **RTC（Real-Time Chunking）**：推理时可以把上一次预测的动作块的尾部作为"inpainting"约束，用指数斜坡（`vel_strength`）控制哪些时间步被冻结、哪些渐进去噪，从而在连续控制时让新旧动作块平滑衔接，避免动作突变（同文件 358-394 行）。

---

## 2. 系统架构

### 2.1 VLM 主干（Backbone）
- `gr00t/model/modules/qwen3_backbone.py`：N1.7 的一大变化是从上一代的 Eagle 换成 **Cosmos-Reason2-2B（Qwen3-VL 架构）**，支持原生分辨率图像（不需要 padding）。
- 只取 LLM 的前 `select_layer`（默认第 12 层，见 `configs/model/gr00t_n1d7.py:47`）的隐藏状态作为视觉语言特征，后面的层直接被物理删除（`qwen3_backbone.py:158-159`）以节省显存和算力——本质上把 VLM 当一个"感知编码器"用，不需要它自己生成文本。
- 有专门的 RoPE 频率重建逻辑（`_reset_rotary_inv_freq`），处理 meta-device 加载和 FA2/SDPA 数值一致性问题，这是工程上比较细节但重要的坑。

### 2.2 动作头（Action Head，`gr00t/model/gr00t_n1d7/gr00t_n1d7.py` + `gr00t/model/modules/dit.py`）
- **DiT（Diffusion Transformer）**：标准的 AdaLN-Zero 条件 Transformer block（时间步 embedding 通过 SiLU+Linear 生成 scale/shift）。
- **AlternateVLDiT**：N1.7 用的变体，让 DiT 的 cross-attention 交替关注"文本 token"和"图像 token"（`attend_text_every_n_blocks` 控制频率），并在偶数层插入自注意力层（interleave），比统一注意力更高效地融合多模态上下文。
- **State/Action Encoder**（`gr00t/model/modules/embodiment_conditioned_mlp.py`）：这是实现"一个模型服务多种机器人"的核心技巧——`CategorySpecificLinear`/`CategorySpecificMLP` 为每个 embodiment（最多 32 种，`max_num_embodiments`）维护独立的权重矩阵 `[num_categories, in, out]`，forward 时按 `embodiment_id` 索引选权重，这样不同机器人的状态/动作维度和物理意义可以互不干扰地共享同一个 Transformer 主干。
- Loss 只在 `action_mask` 标记的有效维度上计算 MSE（不同机器人动作维度不同，padding 部分被 mask 掉）。

### 2.3 多本体 Projector 索引
`processing_gr00t_n1d7.py` 里的 `_PROJECTOR_INDEX_GROUPS` 是另一层多本体隔离机制：把不同数据集/子任务但物理上是"同一个机器人"的 embodiment tag 分到同一个 projector 槽位（如 `real_g1_*` 预训练和 `unitree_g1_full_body_*` 后训练共享槽位 25），新机器人接入时只需分配一个新槽位号。

---

## 3. 关键设计决策

| 设计 | 位置 | 目的 |
|---|---|---|
| **相对末端执行器动作空间（Relative EEF）** | `getting_started/finetune_new_embodiment.md`, `state_action/pose.py`, `action_chunking.py` | N1.7 最大的改动：动作表示为相对当前位姿的增量而非绝对目标位姿，跨机器人/跨人类视频统一动作语义，是迁移学习的关键 |
| **人类视频预训练** | README | 因为动作是相对表示，20K 小时 EgoScale 人类第一视角视频可以和机器人数据共用同一套动作语义参与预训练 |
| **State Dropout（默认 0.8）** | `gr00t_n1d7.py:219-226`, `configs/model/gr00t_n1d7.py:118` | 训练时以高概率把 state 输入整体置零，防止模型过度依赖本体感受、退化成"复制上一帧状态"，提升纯视觉泛化能力 |
| **Embodiment Tag 体系** | `gr00t/data/embodiment_tags.py` | 三层标签：预训练标签（基座模型直接可用）、后训练标签（需要微调 checkpoint）、微调专用标签（`NEW_EMBODIMENT` 给自定义机器人用），决定 modality 解析、归一化统计量、projector 选择 |
| **Server-Client 部署架构** | `gr00t/policy/server_client.py`, `gr00t/eval/run_gr00t_server.py` | 策略跑在 GPU 服务器，机器人/仿真端只需轻量 ZMQ 客户端，解耦推理算力和控制端 |
| **ReplayPolicy** | `gr00t/policy/replay_policy.py` | 不加载模型，直接回放数据集里的真实动作，用于调试环境接线是否正确 |

---

## 4. 数据格式与训练数据流

### 4.1 数据格式：GR00T LeRobot v2 + `modality.json`
```
my_dataset/
  meta/info.json, episodes.jsonl, tasks.jsonl, modality.json   # modality.json是GR00T特有的
  data/chunk-000/*.parquet     # 逐帧 state/action
  videos/chunk-000/*.mp4       # 逐 episode 视频
```
`modality.json` 把拼接的 state/action 数组拆分成命名字段（如 `x,y,z,gripper`），并声明哪些是相对/绝对、EEF/关节类型（`ActionRepresentation`, `ActionType` 见 `configs/data/embodiment_configs.py`）。

### 4.2 数据管线（重点看这三个文件）
1. **`gr00t/data/dataset/sharded_single_step_dataset.py`**：把每个 episode 拆成"单时间步"样本，按 `episode_sampling_rate` 抽样后打散分配到大小均衡的 shard 里（贪心平衡算法），保证每个 shard 内部episode/时间步都足够多样。
2. **`gr00t/data/dataset/sharded_mixture_dataset.py`**：多数据集混合训练时按 `mix_ratio` / `ds_weights_alpha`（幂律加权）采样，并且用加权公式合并各数据集的统计量（均值方差加权合并公式在 `merge_statistics` 里）。
3. **`gr00t/data/state_action/state_action_processor.py`**：统一处理 state/action 的归一化（min-max 到 [-1,1] 或 mean-std）与绝对→相对动作转换，训练/推理路径共用，保证一致性。

### 4.3 完整流程
```
LeRobot 数据集 → DatasetFactory.build() → ShardedSingleStepDataset(每个embodiment/数据集)
   → ShardedMixtureDataset(混合采样) → Gr00tN1d7DataCollator(图像增强+VLM tokenize)
   → Gr00tN1d7.forward() → backbone → action_head(flow matching loss)
```

---

## 5. 建议的入门阅读顺序

1. **先跑起来**：`README.md` 的 Zero-Shot Inference 一节 + `getting_started/GR00T_inference.ipynb`（用 `demo_data/droid_sample`，不用下载额外数据）。
2. **理解 Policy API**：`getting_started/policy.md`（观测/动作格式、embodiment tag 用法）+ `gr00t/policy/policy.py`, `gr00t/policy/gr00t_policy.py`。
3. **理解数据格式**：`getting_started/data_config.md` + `getting_started/data_preparation.md` + 打开一个 `demo_data/` 下的样例看 `meta/modality.json`。
4. **理解模型**（本次分析已覆盖核心）：`gr00t/model/gr00t_n1d7/gr00t_n1d7.py` → `gr00t/model/modules/dit.py` → `gr00t/model/modules/embodiment_conditioned_mlp.py`。
5. **理解训练**：`examples/SO100/README.md`（一个完整的"接入新机器人"实战案例）+ `gr00t/experiment/launch_finetune.py` + `getting_started/finetune_new_embodiment.md`。
6. **理解评测**：`gr00t/eval/open_loop_eval.py`（离线对比预测 vs 真值）和 `gr00t/eval/run_gr00t_server.py`（在线闭环评测）。

`AGENTS.md` 里有仓库的开发规范（uv 包管理、ruff lint、pytest 标记 gpu/not gpu），如果你要动代码可以先看一眼。
