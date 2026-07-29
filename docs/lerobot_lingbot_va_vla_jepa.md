# LeRobot 世界模型向策略：`lingbot_va` 与 `vla_jepa`

> 面向：在本机摸清 **LingBot-VA** / **VLA-JEPA** 的依赖、显存、训评路径（相对 FastWAM）  
> 对照：[FastWAM hands-on](./lerobot_wam_handson.md) · [ACT+SmolVLA 全栈](./lerobot_act_smolvla_fullstack.md) · [模型矩阵](./lerobot_model_benchmark_matrix.md)  
> 核实环境（2026-07-10）：LeRobot `~/Documents/Foundation/main/lerobot` **0.6.1**；本机偏好 `push_to_hub=false`；**未**大规模下载权重（Hub API 查体积）。

**注册名（代码核实）：**

| 字符串 | Config | Policy | 工厂 |
| --- | --- | --- | --- |
| `lingbot_va` | `@PreTrainedConfig.register_subclass("lingbot_va")` → `LingBotVAConfig` | `LingBotVAPolicy.name = "lingbot_va"` | `factory.py` |
| `vla_jepa` | `@PreTrainedConfig.register_subclass("vla_jepa")` → `VLAJEPAConfig` | `VLAJEPAPolicy.name = "vla_jepa"` | `factory.py` |

官方文档：`main/lerobot/docs/source/lingbot_va.mdx`、`vla_jepa.mdx`（与 `policies/*/README.md` 同步）。

---

## 0. 一页对照（相对 FastWAM / SmolVLA）

| | **lingbot_va** | **vla_jepa** | **fastwam** | **smolvla** |
| --- | --- | --- | --- | --- |
| 定位 | 自回归 **video+action** 世界模型（推理仍想象未来 latent） | VLA + **训时** V-JEPA2 世界模型损失 | 训时 video+action；**推理直接出动作** | 小 VLA |
| 骨干 | Wan2.2 双流 DiT **~5B** + 冻 VAE/UMT5 | **Qwen3-VL-2B** + DiT-B + V-JEPA2（训） | Wan2.2-TI2V-5B + Action DiT | SmolVLM ~0.45B |
| LeRobot ckpt 体积（Hub） | `model.safetensors` **~10.2 GB** | **~6.2 GB** | `fastwam_base` **~12 GB** | `smolvla_base` **~0.9 GB** |
| 额外冻结权重 | `wan_pretrained_path`：VAE+UMT5 **~20 GB**（默 CPU 文本塔） | 构造时再拉 `Qwen/...`、训时拉 `facebook/vjepa2-...` | T5+VAE 等（成品合计常 ~26 GB） | 通常已在 ckpt |
| 文档推理显存 | **约 18–24 GB**（UMT5 放 CPU） | 官方未写死；骨干 2B 级，远小于 LingBot/FastWAM | 官方复现 **1×H20 140 GB** | 数 GB 级 |
| 本机 16GB | ❌ 推理也紧/不够 | ⚠️ 可能勉强 eval（建议关世界模型）；训仍吃紧 | ❌ | ✅ |
| 与 FastWAM 一句话 | **同族 Wan 栈，但推理做 AR 未来帧+动作去噪 + KV 闭环反馈** | **世界模型只服务训练；推理 = Qwen+动作头 flow matching** | （对照基准） | — |

```text
lingbot_va 推理：观测 → VAE latent → AR 块（video FM ~20步 + action FM ~50步）→ KV cache + 真关键帧回灌
vla_jepa  推理：观测+语言 → Qwen3-VL → DiT-B flow matching（~4步）→ action chunk（不用 JEPA）
fastwam   推理：观测 → Wan/MoT → infer_action（不做 test-time 未来帧想象）
```

---

## 1. 上手依赖

### 1.1 `pyproject.toml` extras（已核实）

| Extra | 展开依赖 | 解析到的包约束 |
| --- | --- | --- |
| `lingbot_va` | `transformers-dep` + `diffusers-dep` + `accelerate-dep` | `transformers>=5.4,<5.6`；`diffusers>=0.27.2,<0.36`；`accelerate>=1.14,<2` |
| `vla_jepa` | `transformers-dep` + `diffusers-dep` + `qwen-vl-utils-dep` | 同上 transformers/diffusers；`qwen-vl-utils>=0.0.11,<0.1` |

代码入口：`require_package("diffusers"/"transformers", extra="lingbot_va"|"vla_jepa")`。

### 1.2 额外系统 / 可选依赖

| 项 | lingbot_va | vla_jepa |
| --- | --- | --- |
| CUDA | 需要（文档面向单卡 24–32 GB 推理） | 需要；论文训 **8×A100** |
| `flash-attn` | **可选**：`--policy.attn_mode=flashattn`；默认推理 `torch` SDPA | 未作为 extra 要求 |
| 训练 attention | **必须** `--policy.attn_mode=flex`（flex-attention；默认 `torch` 仅推理） | 无此开关 |
| LoRA / PEFT | 全量 5B+AdamW **塞不进** 24–32 GB；文档要求 `--policy.use_peft=true` → 另装 **`lerobot[peft]`**（`peft>=0.18,<1`） | 可用 `freeze_qwen`；PEFT 非文档主路径 |
| 仿真 extra | LIBERO：`[libero]`；RoboTwin：Docker/`robotwin` 栈（SAPIEN+CuRobo） | LIBERO：`[libero]`；**无** `simplerenv` env type |
| dtype | 默认 `bfloat16`（需 Ampere+ 较稳） | 默认 `torch_dtype=bfloat16` |

### 1.3 安装命令

```bash
cd ~/Documents/Foundation/main/lerobot

# LingBot-VA（训 LoRA 时加上 peft）
pip install -e ".[lingbot_va,libero]"
pip install -e ".[lingbot_va,peft,libero]"   # 推荐 finetune

# VLA-JEPA
pip install -e ".[vla_jepa,libero]"
```

---

## 2. 模型参数量与显存

### 2.1 lingbot_va

| 组件 | 来源 | 量级 |
| --- | --- | --- |
| 可训 DiT | `WanTransformer3DModel`（30 层，hidden=24×128=3072，`ffn_dim=14336`） | 文档 **~5B**；Hub `model.safetensors` **~10.18 GB** |
| 冻 VAE | `AutoencoderKLWan`，`z_dim=48` | 上游 `robbyant/*` 内 `vae/` **~2.8 GB** |
| 冻文本 | UMT5-XXL，`d_model=4096` | `text_encoder/` 合计 **~11.4 GB**；默认 `text_encoder_device=cpu` |
| 上游整包 | `robbyant/lingbot-va-base` | Hub 合计 **~24.4 GB**（含 transformer 分片） |

| 场景 | 文档 / 配置结论 |
| --- | --- |
| 推理（闭环 eval） | **约 18–24 GB VRAM**（5B DiT + VAE；UMT5 在 CPU） |
| 训练全量 AdamW | **单卡 24–32 GB 不够** → LoRA/`use_peft` 和/或 optimizer offload |
| 开环 `eval_loss` | 同训时 forward，显存接近训练（LoRA 时好一些） |

### 2.2 vla_jepa

| 组件 | 配置默认 | 量级 |
| --- | --- | --- |
| VLM | `Qwen/Qwen3-VL-2B-Instruct` | **~2B**；Hub 单独权重 **~4.3 GB** |
| 动作头 | `action_model_type=DiT-B`（768 / 12 heads） | 相对小 |
| 世界模型 | `facebook/vjepa2-vitl-fpc64-256` + `ActionConditionedVideoPredictor` | **仅训练**用；编码器 Hub **~1.3 GB** safetensors |
| LeRobot 成品 ckpt | `lerobot/VLA-JEPA-*` | `model.safetensors` **~6.16 GB**（含 Qwen+头+predictor 等） |

| 场景 | 依据 |
| --- | --- |
| 推理 | 文档：**只用 Qwen + action head**；JEPA 不参与 `predict_action`。若 ckpt 仍 `enable_world_model=true`，构造时仍会加载 JEPA——评测可显式 `--policy.enable_world_model=false` 省显存 |
| 训练 | 论文：**8×A100**，per-GPU `batch_size=32`（global 256）；LeRobot 复现 LIBERO 示例 `steps=30000` |
| 官方 VRAM 数字 | **LeRobot `vla_jepa.mdx` 未写死单卡 GB**；相对 LingBot/FastWAM 明显更轻 |

### 2.3 量级对照表（磁盘 / 显存墙）

| 模型 | 骨干参数（文档） | 主 ckpt 磁盘 | 额外下载 | 推理显存（文档） | 16GB 本机 |
| --- | --- | --- | --- | --- | --- |
| SmolVLA | ~0.45B | ~0.9 GB | 少 | 数 GB | ✅ |
| vla_jepa | Qwen **2B** + DiT-B | ~6.2 GB | Qwen/JEPA 可能再解析 | 未写死；2B 级 | ⚠️ |
| lingbot_va | DiT **~5B** | ~10.2 GB | 冻模块 ~20 GB | **18–24 GB** | ❌ |
| FastWAM | Wan **5B** 级 + Action DiT | base ~12 GB | T5+VAE 等 | 成品合计常 ~26 GB；复现 H20 **140 GB** | ❌ |

---

## 3. 训练

### 3.1 lingbot_va

| 项 | 值 |
| --- | --- |
| `policy.type` | `lingbot_va` |
| 关键字段（`LingBotVAConfig`） | `wan_pretrained_path`（默认 `robbyant/lingbot-va-base`）、`attn_mode`、`dtype`、`text_encoder_device`、`obs_cam_keys`、`camera_layout`、`height/width`、`action_per_frame`、`frame_chunk_size`、`used_action_channel_ids`、`image_hflip`、`save_predicted_video`、`use_peft` |
| Hub 底座 | `lerobot/lingbot_va_base`（真机多相机布局；`height×width=256×320`） |
| 评测/继续训常用 | `lerobot/lingbot_va_libero_long`、`lerobot/lingbot_va_robotwin` |
| 冻权重源 | ckpt 内 `wan_pretrained_path`：LIBERO 成品指向 `robbyant/lingbot-va-posttrain-libero-long` 等 |
| 推荐数据 | 文档占位 `<your LeRobot-format dataset>`；LIBERO 生态常用 `HuggingFaceVLA/libero`（需相机窗 + `frame_chunk_size * action_per_frame` 动作） |
| 损失 | 双流 flow-matching：`latent_loss + action_loss` |

**最小训骨架（本地不推 Hub）：**

```bash
lerobot-train \
  --policy.path=lerobot/lingbot_va_libero_long \
  --policy.attn_mode=flex \
  --policy.use_peft=true \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --dataset.repo_id=HuggingFaceVLA/libero \
  --batch_size=1 \
  --steps=1000 \
  --output_dir=outputs/train/lingbot_va_smoke \
  --job_name=lingbot_va_smoke
```

要点：动作是 **EEF 位姿布局（30 维槽位）**，不是关节；相机顺序敏感（见 §5）。

### 3.2 vla_jepa

| 项 | 值 |
| --- | --- |
| `policy.type` | `vla_jepa` |
| 关键字段（`VLAJEPAConfig`） | `qwen_model_name`、`jepa_encoder_name`、`chunk_size`/`n_action_steps`（默认 7）、`enable_world_model`、`world_model_loss_weight`、`freeze_qwen`、`reinit_modules`、`num_video_frames`、`action_model_type`、`gripper_*`、`torch_dtype` |
| Hub 预训练底座 | `lerobot/VLA-JEPA-Pretrain`（DROID 1.0.1） |
| LIBERO 成品 | `lerobot/VLA-JEPA-LIBERO` |
| SimplerEnv 成品 | `lerobot/VLA-JEPA-SimplerEnv`（权重有；LeRobot **无**对应 `env.type`） |
| 推荐数据 | 文档：`HuggingFaceVLA/libero`；从零示例 `dataset.repo_id=your_org/your_dataset` |
| 损失 | action flow-matching +（可选）JEPA `wm_loss * 0.1` |

**最小训骨架：**

```bash
lerobot-train \
  --policy.path=lerobot/VLA-JEPA-Pretrain \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --dataset.repo_id=HuggingFaceVLA/libero \
  --steps=30000 \
  --output_dir=outputs/train/vla_jepa_libero \
  --job_name=vla_jepa_libero
```

只训动作头：`--policy.freeze_qwen=true`（会自动关掉世界模型）。  
跨 embodiment：`--policy.reinit_modules='["model.action_model.action_encoder","model.action_model.action_decoder","model.action_model.state_encoder"]'`。

---

## 4. 测试 / 评测

### 4.1 开环（两模型相同机制）

LeRobot **没有**独立 `lerobot-eval-openloop` CLI。开环 = 训练循环里对 hold-out 调 `policy.forward` → 日志 **`eval_loss`**：

```bash
lerobot-train \
  --policy.path=<ckpt> \
  --dataset.repo_id=<data> \
  --dataset.eval_split=0.1 \
  --eval_steps=100 \
  --steps=100 \
  --batch_size=1 \
  --policy.push_to_hub=false \
  --output_dir=outputs/openloop_smoke
```

（字段名以本机 `lerobot-train --help` 为准；与 FastWAM / FAQ 笔记一致。）

### 4.2 闭环仿真

| Policy | 支持的 `env.type`（官方文档） | 备注 |
| --- | --- | --- |
| `lingbot_va` | **`libero`**、**`robotwin`** | 流式 KV：**必须** `--eval.batch_size=1` |
| `vla_jepa` | **`libero`**（文档给出） | 示例可用 `--eval.batch_size=5`；SimplerEnv **仅有权重** |

**lingbot_va · LIBERO：**

```bash
lerobot-eval \
  --policy.path=lerobot/lingbot_va_libero_long \
  --policy.device=cuda \
  --env.type=libero --env.task=libero_10 \
  --env.observation_height=128 --env.observation_width=128 \
  --eval.n_episodes=50 --eval.batch_size=1 \
  --output_dir=outputs/eval/lingbot_va_libero
```

**lingbot_va · RoboTwin（需仿真栈 / Docker）：**

```bash
lerobot-eval \
  --policy.path=lerobot/lingbot_va_robotwin \
  --policy.device=cuda \
  --env.type=robotwin --env.task=beat_block_hammer --env.action_mode=ee \
  --eval.n_episodes=10 --eval.batch_size=1 \
  --output_dir=outputs/eval/lingbot_va_robotwin
```

可选：`--policy.save_predicted_video=true` 写出想象视频 `pred_episode_*.mp4`。

**vla_jepa · LIBERO：**

```bash
lerobot-eval \
  --policy.path=lerobot/VLA-JEPA-LIBERO \
  --env.type=libero \
  --env.task=libero_spatial,libero_object,libero_goal,libero_10 \
  --eval.n_episodes=10 \
  --eval.batch_size=5 \
  --output_dir=outputs/eval/vla_jepa_libero
```

文档期望成功率（各 suite 100 ep）：spatial 95% / object 100% / goal 98% / libero_10 93% / overall **96.5%**。

### 4.3 Hub 权重 id（API 已确认存在）

| Repo | 用途 | `model.safetensors` |
| --- | --- | --- |
| `lerobot/lingbot_va_base` | 预训练底座 | ~10.18 GB |
| `lerobot/lingbot_va_libero_long` | LIBERO-Long 后训 | ~10.18 GB |
| `lerobot/lingbot_va_robotwin` | RoboTwin 后训 | ~10.18 GB |
| `robbyant/lingbot-va-base` 等 | 冻 VAE/UMT5（及上游整包） | 整包 ~24 GB |
| `lerobot/VLA-JEPA-Pretrain` | DROID 预训练 | ~6.16 GB |
| `lerobot/VLA-JEPA-LIBERO` | LIBERO 评测/继续训 | ~6.16 GB |
| `lerobot/VLA-JEPA-SimplerEnv` | SimplerEnv 后训权重 | ~6.16 GB |
| Collection | [`lerobot/VLA-JEPA`](https://huggingface.co/collections/lerobot/vla-jepa) | — |

### 4.4 特殊坑

**lingbot_va**

| 坑 | 说明 |
| --- | --- |
| `batch_size=1` | 流式 KV + 观测关键帧回灌只实现了单环境 |
| `attn_mode` | 训=`flex`；推=`torch`（或可选 `flashattn`） |
| 相机顺序 | LIBERO：`image`（agentview）→ `image2`（wrist）；RoboTwin：`head/left/right` + `camera_layout=robotwin_tshape` |
| `image_hflip` | LIBERO 成品 Hub config 为 **`true`**（抵消 env 水平翻转）；默认类属性是 `false`——以 ckpt 为准 |
| 分辨率 | LIBERO 评测文档 **128×128**；base/robotwin 常 **256×320** |
| 动作槽 | 固定 30 维 EEF 布局；`used_action_channel_ids` 选通道；关节数据需重映射 |
| RoboTwin | `--env.action_mode=ee`；CuRobo IK；非关节直出 |
| 磁盘 | 除 10 GB DiT 外还要拉 ~20 GB 冻权重 |

**vla_jepa**

| 坑 | 说明 |
| --- | --- |
| 夹爪 | 默认 `pre_snap_gripper_action` + `binarize_gripper_action`（dim=6）；无二值夹爪机器人要关掉 |
| `n_action_steps` | 默认 7（= `chunk_size`）；改协议时保持 `n_action_steps <= chunk_size` |
| 相机数 | 世界模型默认 2 view（`jepa_tubelet_size=2`）；单相机会 duplicate；>2 只取前 2 给 JEPA |
| `enable_world_model` | 训时可关；`freeze_qwen=true` 会强制关 |
| `reinit_modules` | 动作/状态维变化时必须声明，否则 shape mismatch |
| SimplerEnv | 有 ckpt，**无** LeRobot `env.type=simpler*` |
| dtype | `bfloat16`；归一化 ACTION=`MIN_MAX`，STATE=`MEAN_STD` |

---

## 5. 与 FastWAM 一句话差异

| Policy | 相对 FastWAM |
| --- | --- |
| **lingbot_va** | 同属 Wan2.2 视频扩散族，但推理是 **自回归双流去噪（未来 video latent + action）+ KV cache 真关键帧闭环**；FastWAM 训时保视频、**推理只 `infer_action`、不做 test-time 想象**。 |
| **vla_jepa** | **Qwen3-VL VLA + 仅训练期 V-JEPA2 潜空间世界模型**；推理路径与「视频 DiT 世界模型出动作」无关，更接近带辅助损失的小/中型 VLA。 |

---

## 6. 代码地图

| | lingbot_va | vla_jepa |
| --- | --- | --- |
| Config | `policies/lingbot_va/configuration_lingbot_va.py` | `policies/vla_jepa/configuration_vla_jepa.py` |
| Policy | `modeling_lingbot_va.py` | `modeling_vla_jepa.py` |
| 核心模块 | `utils.py`（Wan DiT / VAE / UMT5） | `qwen_interface.py`、`action_head.py`、`world_model.py` |
| Processor | `processor_lingbot_va.py`（动作 QUANTILES 反归一化） | `processor_vla_jepa.py`（clip / pre-snap / binarize gripper） |
| 测试 | `tests/policies/lingbot_va/` | `tests/policies/vla_jepa/` |
| Extra | `pyproject.toml` → `[lingbot_va]` | `[vla_jepa]` |

---

## 7. 本机建议（RTX 5080 16GB）

| 目标 | 建议 |
| --- | --- |
| 只摸清接口 | `pip install -e ".[…]"` + `make_policy_config` / `--help` + Hub `config.json`（本笔记路径） |
| 真跑 lingbot_va | 换 **≥24 GB**（推理）或更大 + LoRA（训练） |
| 真跑 vla_jepa | 优先 `lerobot-eval` + `enable_world_model=false` 冒烟；全量带 JEPA 训按多卡预算 |
| 对照小模型 | 继续 [SmolVLA 全栈](./lerobot_act_smolvla_fullstack.md) |

---

## 参考

- 官方：`docs/source/lingbot_va.mdx`、`docs/source/vla_jepa.mdx`
- 上游： [Robbyant/lingbot-va](https://github.com/Robbyant/lingbot-va) · 论文 [VLA-JEPA arXiv:2602.10098](https://arxiv.org/abs/2602.10098)
- 同目录：[lerobot_wam_handson.md](./lerobot_wam_handson.md)（FastWAM）
