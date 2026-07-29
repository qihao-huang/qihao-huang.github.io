# LeRobot FAQ / Cheatsheet

> 与 [fullstack](./lerobot_act_smolvla_fullstack.md) 互补：只收概念、对照、坑。命令细节以 fullstack 为准。

---

## 1. 开环 vs 闭环

| | 训练里的 eval | `lerobot-eval` |
|--|----------------|----------------|
| 触发 | `--eval_steps=N`（算 `eval_loss`） | 独立 CLI |
| 数据 | hold-out demo（`--dataset.eval_split`） | 仿真 env 随机 init |
| 指标 | L1 / loss（开环） | **success rate**（闭环） |
| 训练中闭环 | `--env_eval_freq>0` + `--env.type=...` | — |

**Hold-out**：故意留出、不参与梯度的那部分 demo，只用于开环 `eval_loss`。  
**不是**把闭环 rollout 录下来当训练集。

```text
【训练数据】人遥操作 → demo → Hub dataset
【闭环评测】策略控机器人 → 从 init_state rollout → success
```

两套共用同一套仿真任务定义，数据来源不同。

---

## 2. 日志字段

| 字段 | 含义 |
|------|------|
| `step` | 优化步（主旋钮；**没有** `--epochs`） |
| `epch` | 数据过了几遍（≈ epoch，可为小数） |
| `ep` | 累计采样到的 episode 计数（会一直涨） |
| `loss` | 训练总损失 |
| `eval_loss` | hold-out 开环损失 |

换算：`epochs ≈ steps / ceil(num_frames / batch_size)`。

---

## 3. ACT / SmolVLA 损失与权重

| | ACT | SmolVLA |
|--|-----|---------|
| 动作头 | CVAE + L1 | **Flow matching**（`VLAFlowMatching`） |
| 训练损失 | `L1 + kl_weight * KL` | 速度场 MSE |
| HF「base」 | **无**通用 `act_base`（仅 ImageNet ResNet） | 必须 `lerobot/smolvla_base` |
| LIBERO 成品 | 基本无官方 ckpt → **自己训再评** | `lerobot/smolvla_libero` |
| 参数量（本机实测） | ~**52M**（`num_learnable_params≈51.6M`） | ~**0.45B** + SmolVLM 骨干 |
| 训显存（5080） | ~2GB，轻松 | batch 2–4 约 5GB+；可 LoRA / freeze |

**两套 SmolVLA 相关权重别混：**

| 仓库 | 是什么 |
|------|--------|
| `lerobot/smolvla_base` | SO100 社区真机预训练；**未**在 LIBERO 上训 |
| `lerobot/smolvla_libero` | 在 LIBERO 上 finetune 的成品 |
| `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` | 上游 VLM；加载 policy 时可能再拉（排除 onnx 约 2–3GB） |

相机 key：LIBERO 常为 `image`/`image2`，`smolvla_base` 期望 `camera1/2/3` → 训练需 `rename_map`。

---

## 4. LIBERO 数据 vs 评测资产

| 东西 | 用途 | 体积粗估 |
|------|------|----------|
| `HuggingFaceVLA/libero` | **训练** demo | ~**65–70GB** |
| `libero-assets`（仿真场景/STL 等） | **闭环评测** | 远小于训练集；缺了 eval 会卡下载 |
| `--env.task=libero_spatial,...` | 选评测 suite | **不会**去下四个 suite 的训练数据 |

HF 进度条分母一直涨 = `incomplete total`（边扫边累加），不是死循环。

---

## 5. 本地实验固定参数

```bash
--policy.push_to_hub=false
--wandb.enable=true
# 不必写 --policy.repo_id（不推 Hub 时用不上）
export MUJOCO_GL=egl   # Linux 无头仿真
```

`output_dir` 相对**启动时的 cwd**（本机习惯在 `~/Documents/Foundation`）。

---

## 6. 已知坑（本机已踩）

| 坑 | 处理 |
|----|------|
| `hf` 走 `~/.local` 缺 `packaging` | `conda activate lerobot`；`hash -r`；必要时 `~/.local/bin/hf` → conda 的 `hf` |
| wandb 只有硬件面板 | 等 `log_freq`；或 `--log_freq=20` 看 `train/loss` |
| `episodes=10` 但 train 更少 | `eval_split` + 视频分片未齐 |
| SmolVLA 还在下 SmolVLM | 正常；与 `smolvla_base` 是两层 |
| eval 卡在加载 | 常是权重/assets 未下完，不是渲染挂死 |
| GPU-Util 0% 但占显存 | 常卡在 `data_s` 解码 |
| 有线+无线「叠带宽」 | 一条 TCP 只走一张网卡；减并发通常比折腾聚合更有效 |

---

## 7. LeRobot 0.6.x 速记

| 对比 | 结论 |
|------|------|
| 0.6.1 vs 0.6.0 | 几乎仅版本号 bump |
| 0.6.0 vs 0.5.x | 大版本：WM/Reward、更多 benchmark、`lerobot-rollout`、HF Jobs（`--job.target`）、瘦安装 |

破坏性（0.5.1→0.6.0）摘要：`eval_freq`→`env_eval_freq`；GR00T N1.5→N1.7；基础包不再含 training；PyTorch≥2.7。

---

## 8. 框架心智（多模型兼容）

统一契约 + 工厂懒加载 + Processor：

| 层 | 作用 |
|----|------|
| Config 多态 | `--policy.type` / `--policy.path` |
| Factory | `get_policy_class` 按需 import |
| Feature 契约 | `observation.*` / `action` / `task` |
| Processor | 归一化、rename、tokenize；与 ckpt 同存 |
| Reward | 平行的 `PreTrainedRewardModel`，不控机器人 |

交互版：[多模型框架 Canvas](../../.cursor/projects/home-sany-Documents-Foundation/canvases/lerobot-multi-model-architecture.canvas.tsx)（路径以本机 Cursor canvases 为准）。

---

## 9. 磁盘量级（本机曾统计，会变）

| 区域 | 粗量级 |
|------|--------|
| `Foundation/data` | 曾约 ~100GB 级 |
| `~/.cache` 模型/数据相关 | 曾约数十 GB |
| LIBERO 全量 demo | ~70GB |

以 `du -sh` 实时为准。
