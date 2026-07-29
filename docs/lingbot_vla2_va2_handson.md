# LingBot-VLA 2.0 / LingBot-VA 2.0 Hands-on

> 面向：在本机把 Robbyant 两条线 **装起来、摸清训评路径、知道显存墙**  
> 对照：[ACT+SmolVLA 全栈](./lerobot_act_smolvla_fullstack.md) · [WAM/FastWAM](./lerobot_wam_handson.md) · [模型矩阵](./lerobot_model_benchmark_matrix.md)  
> 原则：先弄清 **仓库边界 / 环境栈 / 权重依赖**，再谈大规模训评；本机 RTX 5080 **16GB** 对两条线都偏紧。

核实环境（2026-07-10）：

| 项 | 状态 / 路径 |
| --- | --- |
| LingBot-VLA 2.0 | `~/Documents/Foundation/VLA/lingbot-vla-v2`（`Robbyant/lingbot-vla-v2`，shallow） |
| LingBot-VA（含 VA2 paper） | `~/Documents/Foundation/WAM/lingbot-va`（已 `pull` 到含 `LingBot_VA2_paper.pdf`） |
| 本机 GPU | RTX 5080 **16GB** |
| 本机 RoboTwin | `~/Documents/Foundation/sims/RoboTwin`（评测依赖） |
| 独立 `lingbot-va-v2` 仓库 | **不存在**（VA 2.0 仍在 `lingbot-va`） |

---

## 0. 结论先看

| 问题 | 答案 |
| --- | --- |
| 「VLA 2.0」仓库是哪个？ | **`Robbyant/lingbot-vla-v2`** → 本机 `VLA/lingbot-vla-v2` |
| 「VA 2.0」仓库是哪个？ | **没有独立 repo**；仍是 **`Robbyant/lingbot-va`**（最新提交加了 `LingBot_VA2_paper.pdf`） |
| 和旧 `VLA/lingbot-vla` 关系？ | v1 与 v2 **分仓**；v2 换 Qwen3-VL-4B + sparse MoE + 55-D 统一动作 + depth/DINO 蒸馏 |
| 和 LeRobot 关系？ | 上游自带训练栈；LeRobot 另有 `lingbot_va` / 进行中的 `lingbot_vla_v2` 集成，**不等于**直接 `lerobot-train` 复现官方全流程 |
| 本机 16GB 能做什么？ | **装环境 + 读配置 + 下小依赖**；全量 post-train / RoboTwin 闭环评测通常要 **更大显存或多卡**（VA 官方写 RoboTwin eval ~24GB offload） |
| 推荐上手顺序 | ① 装各自 conda ② 下预训练权重 ③ open-loop / i2av 冒烟 ④ 再接 RoboTwin server-client |

```text
LingBot-VLA 2.0 (策略)          LingBot-VA (世界模型+动作)
  图像+语言 → 动作 chunk           图像+语言 → 未来视频 latent + 动作
  Qwen3-VL + MoE action expert     Wan2.2 MoT AR diffusion
  55-D 跨本体统一动作              30-D 双臂 EEF/joint/gripper
  评测：open-loop / RoboTwin / 真机 WS   评测：RoboTwin / LIBERO server-client
```

**易混仓库（不要当成 VA 2.0）：** `Robbyant/lingbot-world-v2` 是游戏向交互世界模型（LingBot-World-Infinity），不是机器人 Video-Action。

---

## 1. 仓库地图

### 1.1 LingBot-VLA 2.0（`VLA/lingbot-vla-v2`）

| 角色 | 路径 |
| --- | --- |
| 环境脚本 | `tools/create_train_env.sh`（conda `lingbotvla`，Py 3.12，torch 2.8.0，flash-attn 2.8.3） |
| 训练入口 | `train.sh` + `tasks/vla/train_lingbotvla.py` |
| 配置说明 | `configs/vla/Training_Config.md`、`docs/config/lingbotvla_config_doc.md` |
| RoboTwin post-train | `configs/vla/robotwin/robotwin.yaml` |
| 真机 post-train | `configs/vla/real_robot/real_robot.yaml` |
| 本体映射 | `configs/robot_configs/*.yaml`（如 `robotwin.yaml`） |
| 部署 | `deploy/lingbot_vla_v2_policy.py`（WebSocket policy server） |
| RoboTwin 一键评测 | `experiment/robotwin/start_robotwin_infer_and_eval.sh` |
| 自定义数据 | `lingbotvla/data/vla_data/README.md` |
| 权重下载 | `scripts/download_hf_model.py` |

### 1.2 LingBot-VA（`WAM/lingbot-va`）

| 角色 | 路径 |
| --- | --- |
| 安装说明 | `README.md` Quick Start、`INSTALL.md` |
| 推理 server | `evaluation/robotwin/launch_server*.sh`、`evaluation/libero/launch_server.sh` |
| 推理 client | `evaluation/robotwin/launch_client*.sh`、`evaluation/libero/launch_client.sh` |
| i2av 生成 | `script/run_launch_va_server_sync.sh` |
| Post-train | `script/run_va_posttrain.sh`（`CONFIG_NAME=robotwin_train` / `libero_train`） |
| 配置 | `wan_va/configs/`（含 `va_libero_cfg.py` 等） |
| VA2 论文 PDF | `LingBot_VA2_paper.pdf`（本地最新提交） |

---

## 2. LingBot-VLA 2.0：安装 → 权重 → 训练 → 评测

### 2.1 安装

```bash
cd ~/Documents/Foundation/VLA/lingbot-vla-v2
# 需已初始化 conda，且 conda activate 可用
bash tools/create_train_env.sh --env-name lingbotvla
# 已有 env 续装：--resume；重建：--recreate
# 本地 flash-attn wheel：
# bash tools/create_train_env.sh --flash-attn-wheel /path/to/flash_attn-....whl
```

脚本会固定：

- Python **3.12** + **torch 2.8.0** / torchvision 0.23 / torchaudio 2.8
- `requirements.txt` + depth 栈（`requirements-depth.txt`、MoGe、lingbot-depth）
- `flash-attn==2.8.3`
- `lerobot` **v0.4.2**（`--no-deps`，与本机 LeRobot 0.6.1 **不要混用同一 env**）
- `pip install -e .`

**注意：** 与 Foundation 里 `conda lerobot`（0.6.1）是两套环境；VLA2 训练请只用 `lingbotvla`。

### 2.2 权重

| 用途 | Hub |
| --- | --- |
| 预训练（native depth） | `robbyant/lingbot-vla-v2-6b` |
| 训练还需要 | `Qwen/Qwen3-VL-4B-Instruct`、`Ruicheng/moge-2-vitb-normal`、以及 ckpt 内 `depth/`、`dino_video/` teacher |

```bash
conda activate lingbotvla
cd ~/Documents/Foundation/VLA/lingbot-vla-v2
python3 scripts/download_hf_model.py \
  --repo_id robbyant/lingbot-vla-v2-6b \
  --local_dir /path/to/lingbot-vla-v2-6b
```

国内可用 ModelScope：`Robbyant/lingbot-vla-v2-6b`。

### 2.3 数据（以 RoboTwin 50 任务为例）

三步（详见 `experiment/robotwin/README.md` + `lingbotvla/data/vla_data/README.md`）：

1. **LeRobot 数据集**（v2.1 / v3.0）：按 RoboTwin → HDF5 → `generate.sh` 转 LeRobot  
2. **Robot config**：`configs/robot_configs/robotwin.yaml`（特征 → 55-D 槽位）  
3. **Norm stats**：官方已给 `assets/norm_stats/robotwin.json`；自定义需重算  

列表文件：`assets/training_data/robotwin.txt`。

### 2.4 Post-train

```bash
conda activate lingbotvla
cd ~/Documents/Foundation/VLA/lingbot-vla-v2
# 先改 configs/vla/robotwin/robotwin.yaml 里的 model_path / tokenizer_path / output_dir
bash train.sh tasks/vla/train_lingbotvla.py ./configs/vla/robotwin/robotwin.yaml \
  --data.train_path assets/training_data/robotwin.txt \
  --data.data_name multi \
  --train.output_dir output/
```

要点（来自 `Training_Config.md`）：

- `config_key: LingbotVLAV2Config`，`moe_implementation: fused`
- `action_dim / max_action_dim / max_state_dim: 55`
- 默认 **FSDP2** + `use_compile` + gradient checkpointing
- RoboTwin 例：`micro_batch_size=1`，`global_batch_size=3`，`max_steps=30000`
- 显存不够：开 `enable_gradient_checkpointing`，加大 `gradient_accumulation_steps`
- Muon optimizer 可关回 AdamW；sequence-wise aux / z-loss 可按任务关掉

真机模板：`configs/vla/real_robot/real_robot.yaml`（含 depth/video distillation 全套路径）。

### 2.5 评测与部署

**Open-loop：**

```bash
export QWEN3_PATH=/path/to/Qwen3-VL-4B-Instruct
python scripts/open_loop_eval.py \
  --model_path /path/to/posttrain_ckpt \
  --robo_name robotwin \
  --data_path /path/to/val_data \
  --use_length 50
```

`--robo_name` 对应 `configs/robot_configs/{name}.yaml`。

**RoboTwin 闭环（需仿真依赖与推理依赖兼容到同一环境）：**

```bash
QWEN3VL_PATH=/path/to/Qwen3-VL-4B-Instruct/ \
EVAL_WORKDIR=/path/to/RoboTwin/ \
bash experiment/robotwin/start_robotwin_infer_and_eval.sh \
  --model_path /path/to/post_training_checkpoint \
  --output_base /path/to/eval_output \
  --num_per_gpu 2
```

本机已有 `sims/RoboTwin`，可把 `EVAL_WORKDIR` 指过去；仍需按脚本要求对齐依赖。

**真机 WebSocket：**

```bash
export QWEN3VL_PATH=/path/to/Qwen3-VL-4B-Instruct
python -m deploy.lingbot_vla_v2_policy \
  --model_path /path/to/posttrain_ckpt \
  --use_compile \
  --use_length 25 \
  --port 8000
```

官方参考：RTX 4090D 上约 **130 ms / 次**（10 denoising steps）。

---

## 3. LingBot-VA（VA 2.0 paper 同仓）：安装 → 权重 → 训练 → 评测

### 3.1 安装

官方要求：**Python 3.10.16**、**PyTorch 2.9.0**、**CUDA 12.6**（与 VLA2 的 3.12/2.8 **必须分 env**）。

```bash
conda create -n lingbotva python=3.10.16 -y
conda activate lingbotva
pip install torch==2.9.0 torchvision==0.24.0 torchaudio==2.9.0 \
  --index-url https://download.pytorch.org/whl/cu126
pip install websockets einops diffusers==0.36.0 transformers==4.55.2 \
  accelerate msgpack opencv-python matplotlib ftfy easydict
pip install flash-attn --no-build-isolation
cd ~/Documents/Foundation/WAM/lingbot-va
# 可选：pip install . 或 poetry install（见 INSTALL.md）
```

Post-train 额外：

```bash
pip install lerobot==0.3.3 scipy wandb --no-deps
```

### 3.2 权重与数据

| 名称 | Hub |
| --- | --- |
| Base | `robbyant/lingbot-va-base` |
| Post-train RoboTwin | `robbyant/lingbot-va-posttrain-robotwin` |
| Post-train LIBERO-Long | `robbyant/lingbot-va-posttrain-libero-long` |
| 数据 RoboTwin | `robbyant/robotwin-clean-and-aug-lerobot` |
| 数据 LIBERO-Long | `robbyant/libero-long-lerobot` |

```bash
huggingface-cli download robbyant/lingbot-va-posttrain-robotwin --local-dir /path/to/ckpt
huggingface-cli download --repo-type dataset \
  robbyant/robotwin-clean-and-aug-lerobot --local-dir /path/to/dataset
```

### 3.3 关键：`attn_mode` 必须改对

权重目录 `transformer/config.json` 里的 `attn_mode`：

| 模式 | 值 |
| --- | --- |
| 训练 | `"flex"` |
| 推理 / 评测 | `"torch"` 或 `"flashattn"` |

训评混用会直接报错。

### 3.4 Post-train

```bash
cd ~/Documents/Foundation/WAM/lingbot-va
NGPU=8 CONFIG_NAME='robotwin_train' bash script/run_va_posttrain.sh
NGPU=8 CONFIG_NAME='libero_train'   bash script/run_va_posttrain.sh
```

自定义数据要点：

1. 转成 LeRobot，并在 `meta/episodes.jsonl` 加 `action_config`  
2. 用 Wan2.2 VAE 抽 `latents/`（镜像 `videos/` 结构）  
3. 动作映射到 **30-D**（左右臂 EEF 7+7、joint 7+7、gripper 1+1；缺维填 0）  
4. 视频参考 ~256×256、5–15 fps  

显存不够：增大 `gradient_accumulation_steps`，目标更大 global batch（如 32/64）。

### 3.5 评测

**RoboTwin 2.0（server / client 同机）：**

1. 按官方装 RoboTwin（本机可基于 `sims/RoboTwin`；上游 README 钉 commit `2eeec322`）  
2. 改 `transformer/config.json` → 推理 `attn_mode`  
3. Server：`bash evaluation/robotwin/launch_server.sh`（多卡用 `*_multigpus.sh`）  
4. Client：`bash evaluation/robotwin/launch_client.sh ${save_root} ${task_name}`  

官方：**单卡 RoboTwin eval ~24GB**（VAE/text_encoder offload）。本机 16GB **大概率不够闭环**，可先做 i2av：

```bash
NGPU=1 CONFIG_NAME='robotwin_i2av' bash script/run_launch_va_server_sync.sh
# 官方：i2av + offload ~18GB
```

**LIBERO：**

```bash
bash evaluation/libero/launch_server.sh
bash evaluation/libero/launch_client.sh
```

---

## 4. 本机可执行的最小路径（16GB）

| 优先级 | 动作 | 预期 |
| --- | --- | --- |
| P0 | 两仓已就位；分建 `lingbotvla` / `lingbotva` env | 环境隔离 |
| P1 | 只读配置 + 确认 `train.sh` / `run_va_posttrain.sh` 参数 | 不占显存 |
| P2 | 下载 **一个** 小/必要权重（先 VA posttrain 或 VLA2-6b，按磁盘选） | 大流量，建议后台 |
| P3 | VLA2：`open_loop_eval` 或 deploy dry-run；VA：`robotwin_i2av` | 冒烟 |
| P4 | 多卡 / ≥24GB 机再跑 RoboTwin 50 任务闭环与 post-train | 正式复现 |

**不要做：** 把 VLA2 的 torch 2.8 / lerobot 0.4.2 和 VA 的 torch 2.9 / lerobot 0.3.3 装进同一个 conda；也不要和 Foundation `lerobot` 0.6.1 混装。

---

## 5. 与工作区其它组件的衔接

| 组件 | 怎么接 |
| --- | --- |
| `sims/RoboTwin` | 两条线评测的仿真端；VLA2 用 `EVAL_WORKDIR`，VA 用 evaluation client |
| `main/lerobot` | 有 `policy.type=lingbot_va` 文档路径；VLA2 上游 PR 向 LeRobot 集成中——**复现论文请优先上游仓** |
| `VLA/lingbot-vla` | v1，保留对照，不要和 v2 目录搞混 |
| `docs/lerobot_wam_handson.md` | LeRobot 内 `fastwam`；与 LingBot-VA 是不同栈 |

---

## 6. 官方链接速查

| | VLA 2.0 | VA |
| --- | --- | --- |
| Code | https://github.com/Robbyant/lingbot-vla-v2 | https://github.com/Robbyant/lingbot-va |
| Paper | arXiv:2607.06403 | arXiv:2601.21998（仓内另有 `LingBot_VA2_paper.pdf`） |
| Site | https://technology.robbyant.com/lingbot-vla-v2 | https://technology.robbyant.com/lingbot-va |
| HF | `robbyant/lingbot-vla-v2-6b` | `robbyant/lingbot-va-*` collection |

---

## 7. 本机路径一览

```text
Foundation/
├── VLA/lingbot-vla-v2/     # 新 clone：VLA 2.0
├── VLA/lingbot-vla/        # 旧 v1
├── WAM/lingbot-va/         # VA（含 VA2 paper PDF）
├── sims/RoboTwin/          # 评测仿真
└── docs/lingbot_vla2_va2_handson.md
```
