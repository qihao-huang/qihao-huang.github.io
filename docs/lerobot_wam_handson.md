# LeRobot WAM 系列 Hands-on（本地调研版）

> 面向：在本机用 LeRobot **摸清 WAM / FastWAM 能跑什么、不能跑什么**  
> 对照：[ACT+SmolVLA 全栈](./lerobot_act_smolvla_fullstack.md) · [lingbot_va / vla_jepa](./lerobot_lingbot_va_vla_jepa.md) · [FAQ](./lerobot_faq_cheatsheet.md) · [模型矩阵](./lerobot_model_benchmark_matrix.md)  
> 原则：先弄清 **注册名 / Hub / 显存墙**，再谈训评；本机 **不推 Hub**，不默认大规模下载。

核实环境（2026-07-10）：

| 项 | 状态 / 路径 |
| --- | --- |
| LeRobot | `~/Documents/Foundation/main/lerobot`，conda `lerobot`，**0.6.1** |
| `policy.type=wam` | **不存在** |
| `policy.type=fastwam` | **已注册**（`FastWAMConfig` / `FastWAMPolicy`） |
| 本机 FastWAM / Wan 权重缓存 | **无**（未下载） |
| 本机 GPU | RTX 5080 **16GB**（对 FastWAM 全量训/评 **不够**） |

---

## 0. 结论先看

| 问题 | 答案 |
| --- | --- |
| LeRobot 里有没有叫 `wam` 的 policy？ | **没有**。全局注册表只有 **`fastwam`**。 |
| 「WAM 系列」在本仓库指什么？ | **LeRobot 内置 = FastWAM**；工作区 `WAM/` 下还有上游 FastWAM、UnifoLM-WMA 等，**不走** `lerobot-train/eval`。 |
| 和 SmolVLA 比？ | 同是「语言+视觉→动作」，但 FastWAM 是 **Wan2.2 视频世界模型 + Action DiT（MoT）**，训时有 **video+action** 双损失；推理 **直接出动作**，不做 test-time 未来帧想象。 |
| 本机 16GB 能否像 SmolVLA 一样 smoke 训/评？ | **基本不能**。成品 ckpt 仅权重就约 **26GB**（DiT 12 + T5 11 + VAE 2.8）；官方复现写 **1×H20 140GB**。 |
| 最小可做的事 | 装 `[fastwam]`、确认 registry/`--help`、读 Hub `config.json`；真训评需更大显存机或上游仓库。 |

```text
观测 (双相机拼接 + state + 语言 task)
        │
        ▼
   FastWAM (Wan VAE/T5 + Video DiT ⟷ Action DiT / MoT)
        │
   ┌────┴────┐
   ▼         ▼
训练：video flow + action flow    推理：infer_action → action chunk
(开环 eval_loss)                  (闭环 lerobot-eval success)
```

---

## 1. 代码地图（已核实）

| 角色 | 路径 / 符号 |
| --- | --- |
| Config | `src/lerobot/policies/fastwam/configuration_fastwam.py` → `@PreTrainedConfig.register_subclass("fastwam")` → `FastWAMConfig` |
| Policy | `modeling_fastwam.py` → `FastWAMPolicy`（`name = "fastwam"`） |
| Processor | `processor_fastwam.py` → `make_fastwam_pre_post_processors`；LIBERO 夹爪 `FastWAMActionToggleProcessorStep` |
| 核心模型 | `wan/modular.py` → `FastWAM`（`training_loss` / `infer_action`） |
| 工厂 | `policies/factory.py`：`get_policy_class("fastwam")`、processor 分支 |
| 官方文档 | `docs/source/fastwam.mdx`、`policies/fastwam/README.md` |
| Extra | `pyproject.toml` → `[fastwam]` = `transformers` + `diffusers` |
| 测试 | `tests/policies/fastwam/test_fastwam_policy.py` |

**注册名探测（本机已跑）：**

```text
PreTrainedConfig 已知 type 含: act, diffusion, ..., fastwam, ..., smolvla, vla_jepa, ...
make_policy_config("wam") → ValueError: Policy type 'wam' is not available.
```

**工作区其它「WAM」但非 LeRobot policy：**

| 目录 | 是什么 | 与 `lerobot-*` |
| --- | --- | --- |
| `WAM/FastWAM/` | 论文官方训练/评测仓库 | 独立 conda / scripts，不共用 CLI |
| `WAM/unifolm-world-model-action/` | Unitree UnifoLM-**WMA**（World-Model-Action） | 独立栈 |
| `WAM/cosmos`、`DreamDojo`、`Motus` 等 | 其它世界模型相关 | 非 `policy.type=fastwam` |

同属「世界模型向」且 **已进 LeRobot** 的还有（**不是** `fastwam`）：

| `policy.type` | 定位 | 官方文档 | 本地调研笔记 |
| --- | --- | --- | --- |
| `lingbot_va` | Wan2.2 上自回归 video-action，闭环 KV cache | `docs/source/lingbot_va.mdx` | [lingbot_va + vla_jepa](./lerobot_lingbot_va_vla_jepa.md) |
| `vla_jepa` | Qwen3-VL + V-JEPA2 + flow-matching 动作头 | `docs/source/vla_jepa.mdx` | 同上 |

本笔记 hands-on 主路径只覆盖 **FastWAM**；另两模型见上表链接。

---

## 2. FastWAM 是什么（相对 SmolVLA）

| | **FastWAM** | **SmolVLA** |
| --- | --- | --- |
| `policy.type` | `fastwam` | `smolvla` |
| 定位 | World Action Model：训时保视频建模，**推理直接预测动作** | 小 VLA：VLM + Action Expert |
| 骨干 | Wan2.2-TI2V-5B（VAE + Video DiT）+ Action DiT，MoT 路由 | SmolVLM + flow-matching expert |
| 默认底座 | `lerobot/fastwam_base`（`FastWAMConfig.base_model_id`） | `lerobot/smolvla_base` |
| 语言 | UMT5（`google/umt5-xxl` / Wan Diffusers 文本塔） | SmolVLM tokenizer |
| 视觉输入 | `image_size=(224,448)`：多相机 **宽拼接**（2×224→448） | 多相机独立喂 VLM |
| 动作 | `action_horizon=32`，默认 `n_action_steps=32` | `chunk_size=50`，默认 `n_action_steps=50` |
| 训练损失 | `λ_video * loss_video + λ_action * loss_action`（flow / 速度场类） | 主要是 action flow matching |
| 推理 | `infer_action`（**不**迭代生成未来观测） | 去噪出动作 chunk |
| Attention | DiT 用 **SDPA**；`flash-attn` 包对 FastWAM **无效**（MoT 要任意 bool mask） | 走 VLM/expert 各自路径 |
| LIBERO 成品 | `ZibinDong/fastwam_libero_uncond_2cam224`（非 `lerobot/` 命名空间） | `lerobot/smolvla_libero` |
| 本机 16GB | ❌ 全量训/评不现实 | ✅ smoke / 正式 finetune 可行 |

论文：[Fast-WAM: Do World Action Models Need Test-time Future Imagination?](https://arxiv.org/abs/2603.16666)

默认配置要点（`FastWAMConfig`）：

| 字段 | 默认 | 备注 |
| --- | --- | --- |
| `action_dim` / `proprio_dim` | 7 / 8 | 对齐 LIBERO |
| `num_video_frames` / `action_video_freq_ratio` | 33 / 4 | 子采样后 `model_video_frames=9`（须 `T%4==1`） |
| `torch_dtype` | `bfloat16` | 评测文档常改 `float32` |
| `loss` | `lambda_video=1, lambda_action=1` | 冻 video expert 时建议 `lambda_video=0` |
| `freeze_video_expert` | `False` | 只训 action expert 时可开，**仍难塞进 16GB** |
| `toggle_action_dimensions` | `[]` | LIBERO 成品 ckpt 为 `[-1]`（夹爪符号约定） |
| `base_model_id` | `lerobot/fastwam_base` | 兼容默认 DiT 配置时，`__post_init__` 会自动把 `pretrained_path` 指到 base |

---

## 3. Hub 权重与数据

### 3.1 模型（已用 Hub API 核实存在）

| Repo | 用途 | 体积粗估 |
| --- | --- | --- |
| [`lerobot/fastwam_base`](https://huggingface.co/lerobot/fastwam_base) | LeRobot 底座；`type=fastwam`；双相机 `image`/`image2` + state | `model.safetensors` **~12.0 GB** |
| [`ZibinDong/fastwam_libero_uncond_2cam224`](https://huggingface.co/ZibinDong/fastwam_libero_uncond_2cam224) | LIBERO 评测成品（文档主推） | **~26.2 GB**（含 DiT 12 + UMT5 11 + VAE 2.8 + tokenizer/stats） |
| [`Wan-AI/Wan2.2-TI2V-5B`](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B) / `-Diffusers` | 从零初始化 / 组件来源 | 很大；训时还会拉 |
| [`yuanty/fastwam`](https://huggingface.co/yuanty/fastwam) | 上游官方发布集合 | 上游仓库用，非 LeRobot 唯一入口 |

成品 ckpt 的 `config.json` 要点：`toggle_action_dimensions=[-1]`，`image_size=[224,448]`，`n_action_steps=32`（评测时文档常 **覆盖为 10**）。

### 3.2 数据

| 数据 | 用途 |
| --- | --- |
| `HuggingFaceVLA/libero` | LeRobot 侧 finetune（与 SmolVLA/ACT 相同主数据；本机缓存路径见 fullstack） |
| `yuanty/LIBERO-fastwam` 等 | **上游 FastWAM 仓库**用的预处理数据，不是 `lerobot-train` 默认 `repo_id` |

闭环评测 **不需要** 下完整训练 demo，但需要 LIBERO 仿真 + `libero-assets`（同 SmolVLA）。

---

## 4. 环境

```bash
conda activate lerobot
cd ~/Documents/Foundation/main/lerobot

pip install -e ".[fastwam,libero]"   # transformers + diffusers + LIBERO

hf auth login
wandb login                          # 可选
export MUJOCO_GL=egl                 # 无头仿真
# 若 SSL 不稳：export HF_ENDPOINT=https://hf-mirror.com
```

本机已确认：`transformers` / `diffusers` 可 import；`lerobot-train --help` 正常。

本地实验固定：

```bash
--policy.push_to_hub=false
--wandb.enable=true
```

---

## 5. 训练（可复制命令；本机勿盲目开跑）

### 5.1 心智：`type=fastwam` vs `path=...`

| 写法 | 行为 |
| --- | --- |
| `--policy.type=fastwam` | 默认会挂上 `lerobot/fastwam_base`（配置兼容时自动 `pretrained_path`） |
| `--policy.path=lerobot/fastwam_base` | 显式从底座 finetune（更清晰，推荐） |
| 只改结构导致与 base 不兼容 | 可能 **不会** 自动加载 base → 近似从零（极重） |

### 5.2 Smoke（少 steps；仍会拉 ~12GB+ 底座与 Wan/T5 组件）

> **警告：** 在 16GB 上大概率 **OOM**。下列命令用于「有 ≥40–80GB+ 显存」或远程大卡时的最小复现骨架；本机最多 `--help` / 极短确认。

```bash
cd ~/Documents/Foundation

lerobot-train \
  --policy.path=lerobot/fastwam_base \
  --dataset.repo_id=HuggingFaceVLA/libero \
  --dataset.episodes="[0,1,2,3,4,5,6,7,8,9]" \
  --dataset.eval_split=0.1 \
  --eval_steps=50 \
  --steps=100 \
  --batch_size=1 \
  --save_freq=100 \
  --env_eval_freq=0 \
  --log_freq=10 \
  --policy.device=cuda \
  --policy.torch_dtype=bfloat16 \
  --policy.action_dim=7 \
  --policy.proprio_dim=8 \
  --policy.action_horizon=32 \
  --policy.n_action_steps=10 \
  --policy.image_size='[224,448]' \
  --policy.use_gradient_checkpointing=true \
  --policy.freeze_video_expert=true \
  --policy.loss.lambda_video=0 \
  --policy.loss.lambda_action=1 \
  --output_dir=outputs/smoke_fastwam_libero_10ep \
  --job_name=smoke_fastwam_libero_10ep \
  --policy.push_to_hub=false \
  --wandb.enable=true
```

说明：

- `freeze_video_expert=true` + `lambda_video=0`：少训 video 塔、减优化器状态；**权重仍巨大**。
- 开环评测：靠 `--eval_steps` + `--dataset.eval_split` → 日志 `eval_loss`（以及 `loss_video` / `loss_action` 若未关掉 video）。
- 训练中闭环：保持 `--env_eval_freq=0`，训完再 `lerobot-eval`。

### 5.3 正式 finetune（参考官方文档量级）

官方 `fastwam.mdx` 示例量级：`steps=300000`，`batch_size=8` —— 面向多卡 / 大显存，**不是** 5080 本地档。

```bash
lerobot-train \
  --policy.path=lerobot/fastwam_base \
  --dataset.repo_id=HuggingFaceVLA/libero \
  --dataset.eval_split=0.05 \
  --eval_steps=2000 \
  --steps=300000 \
  --batch_size=8 \
  --save_freq=5000 \
  --env_eval_freq=0 \
  --policy.type=fastwam \
  --policy.action_dim=7 \
  --policy.proprio_dim=8 \
  --policy.action_horizon=32 \
  --policy.n_action_steps=10 \
  --policy.image_size='[224,448]' \
  --policy.device=cuda \
  --output_dir=outputs/train/fastwam_libero \
  --job_name=fastwam_libero \
  --policy.push_to_hub=false \
  --wandb.enable=true
```

---

## 6. 开环评测

与 ACT/SmolVLA 相同机制：训练循环里 `eval_steps` 在 hold-out 上算 **`eval_loss`**，**不是** success rate。

| 方式 | 命令要点 | 指标 |
| --- | --- | --- |
| 训练中开环 | `--dataset.eval_split=... --eval_steps=N` | `eval_loss` |
| 训后只想看 loss | 继续短训 / 或自写 dataloader 调 `policy.forward`（无单独 `lerobot-eval-openloop` CLI） | 同上 |

看日志字段：`loss`、`loss_video`、`loss_action`、`eval_loss`（字段以实际 wandb/终端为准）。

---

## 7. 闭环仿真评测（LIBERO）

### 7.1 官方成品（跳过自训）

文档主推权重：`ZibinDong/fastwam_libero_uncond_2cam224`。

**冒烟（少 episode；仍会下载 ~26GB 权重）：**

```bash
export MUJOCO_GL=egl

lerobot-eval \
  --policy.path=ZibinDong/fastwam_libero_uncond_2cam224 \
  --policy.device=cuda \
  --policy.torch_dtype=float32 \
  --policy.n_action_steps=10 \
  --env.type=libero \
  --env.task=libero_spatial \
  --env.observation_height=256 \
  --env.observation_width=256 \
  --eval.batch_size=1 \
  --eval.n_episodes=2 \
  --seed=0 \
  --env.episode_length=300 \
  --output_dir=outputs/eval/fastwam_libero_spatial_smoke
```

**单 suite 更接近文档（每任务多 ep；官方表用 500 ep/suite）：**

```bash
lerobot-eval \
  --policy.path=ZibinDong/fastwam_libero_uncond_2cam224 \
  --policy.device=cuda \
  --policy.torch_dtype=float32 \
  --policy.n_action_steps=10 \
  --env.type=libero \
  --env.task=libero_spatial \
  --env.observation_height=256 \
  --env.observation_width=256 \
  --eval.batch_size=1 \
  --eval.n_episodes=50 \
  --seed=0 \
  --env.episode_length=300
```

LIBERO-10：

```bash
--env.task=libero_10 --env.episode_length=600
```

文档公布成功率（该 ckpt）：

| Suite | Success | n_episodes |
| --- | ---: | ---: |
| libero_spatial | 97.6% | 500 |
| libero_object | 99.0% | 500 |
| libero_goal | 95.0% | 500 |
| libero_10 | 94.0% | 500 |
| **average** | **96.4%** | 2000 |

### 7.2 自训 ckpt

```bash
lerobot-eval \
  --policy.path=/path/to/outputs/.../checkpoints/XXXXXX/pretrained_model \
  --policy.device=cuda \
  --policy.n_action_steps=10 \
  --env.type=libero \
  --env.task=libero_spatial \
  --env.observation_height=256 \
  --env.observation_width=256 \
  --eval.batch_size=1 \
  --eval.n_episodes=2 \
  --env.episode_length=300
```

若自训未带 toggle，而要对齐官方 LIBERO 夹爪约定，可显式：

```bash
--policy.toggle_action_dimensions='[-1]'
```

### 7.3 分辨率：224 vs 256

| 来源 | `observation_height/width` |
| --- | --- |
| `libero` env 默认 | **256** |
| `fastwam.mdx` Usage 示例 | 224 |
| README / Results 复现行 | **256** |

模型内部会按 `image_size` 再 resize/拼接；复现官方表优先跟 **256 + `n_action_steps=10`**。

---

## 8. 坑与限制（优先读）

1. **没有 `policy.type=wam`**：只有 `fastwam`；搜到的 `WAM/` 目录是旁路研究代码。
2. **显存墙（本机 5080 16GB）**：成品评测权重合计 ~26GB；官方写 **H20 140GB**。不要按 SmolVLA 的预期在本机硬跑。
3. **首次加载极重**：除 `model.safetensors` 外还要 VAE、UMT5；`fastwam_base` 本身 ~12GB，且可能再触达 Wan Diffusers。
4. **`n_action_steps`**：ckpt 默认常为 32；文档复现用 **10**。务必在 `lerobot-eval` 显式覆盖。
5. **夹爪 toggle**：LIBERO 成品 `toggle_action_dimensions=[-1]`；自训若忘了，闭环可能系统性差一截。
6. **双相机宽拼接**：策略期望 `observation.images.image` + `image2`，高度 224、宽度和为 448；`set_dataset_feature_metadata` 会按数据集相机数均分宽度。
7. **视觉不做 MEAN_STD**：`VISUAL=IDENTITY`，避免被数据集亮度 std 拉爆；图像在进 VAE 前由模型映射到 `[-1,1]`。
8. **语言必需**：训练 batch 要有 `task`（或预计算 `context`/`context_mask`），否则 `forward` 报错。
9. **flash-attn 无用**：MoT 任意 mask → 只用 SDPA。
10. **开环 ≠ 闭环**：`eval_loss` 下降不代表 LIBERO success；闭环必须 `lerobot-eval`。
11. **命名空间**：成品在 `ZibinDong/...`，不是 `lerobot/fastwam_libero`；不要按 SmolVLA 命名习惯瞎猜。
12. **上游仓库**：要复现论文全套预处理/Deepspeed，用 `WAM/FastWAM/`，不要假设与 LeRobot CLI 参数一一对应。

---

## 9. 建议路径（相对 SmolVLA）

| 阶段 | 建议 |
| --- | --- |
| 本机 16GB | 继续用 ACT / SmolVLA 跑通全栈；FastWAM **只读文档 + 确认 registry** |
| 有大显存 | 先 `lerobot-eval` 成品 ckpt 冒烟 → 再 `fastwam_base` 短 finetune → 再闭环 |
| 只要论文数字 | 直接评 `ZibinDong/fastwam_libero_uncond_2cam224`，不必自训 |
| 研究 UnifoLM-WMA 等 | 进 `WAM/unifolm-world-model-action/`，勿与 `policy.type=fastwam` 混为一谈 |

---

## 10. 最小命令速查

```bash
# 1) 依赖
pip install -e ".[fastwam,libero]"

# 2) 确认注册（本机已通过）
python -c "from lerobot.policies import make_policy_config, get_policy_class; \
c=make_policy_config('fastwam'); print(c.type, get_policy_class('fastwam'))"

# 3) 闭环冒烟（需大显存 + 会下载 ~26GB）
export MUJOCO_GL=egl
lerobot-eval \
  --policy.path=ZibinDong/fastwam_libero_uncond_2cam224 \
  --policy.device=cuda --policy.torch_dtype=float32 \
  --policy.n_action_steps=10 \
  --env.type=libero --env.task=libero_spatial \
  --env.observation_height=256 --env.observation_width=256 \
  --eval.batch_size=1 --eval.n_episodes=2 \
  --seed=0 --env.episode_length=300

# 4) 训练骨架（需大显存）
lerobot-train \
  --policy.path=lerobot/fastwam_base \
  --dataset.repo_id=HuggingFaceVLA/libero \
  --steps=100 --batch_size=1 --env_eval_freq=0 \
  --policy.device=cuda --policy.push_to_hub=false
```

---

## 11. 参考

- LeRobot 文档：`main/lerobot/docs/source/fastwam.mdx`
- 策略 README：`main/lerobot/src/lerobot/policies/fastwam/README.md`
- 论文 / 主页 / 上游：arXiv:2603.16666 · [Project](https://yuantianyuan01.github.io/FastWAM/) · [Code](https://github.com/yuantianyuan01/FastWAM)
- 本机 SmolVLA 对照流程：[lerobot_act_smolvla_fullstack.md](./lerobot_act_smolvla_fullstack.md)
