# RoboCasa：LeRobot 训评 × RLinf 后训练（操作手册）

> 用途：从零安装、仿真、SmolVLA finetune/评测，以及 RLinf π₀+PPO 后训练的可复制步骤；并标出应精读的代码路径。  
> 交互版：[robocasa-lerobot-rlinf-flows.canvas.tsx](../../.cursor/projects/home-sany-Documents-Foundation/canvases/robocasa-lerobot-rlinf-flows.canvas.tsx)  
> 官方 LeRobot 文档：`main/lerobot/docs/source/robocasa.mdx`  
> 相关：[`lerobot_vla_sft_rl.md`](./lerobot_vla_sft_rl.md)（SFT vs RL）、[`lerobot_model_benchmark_matrix.md`](./lerobot_model_benchmark_matrix.md)  
> 整理日期：2026-07-28（对话 + canvas）

## 结论先看

| 问题 | 答案 |
|------|------|
| LeRobot 上 RoboCasa 官方模型？ | **几乎只有 SmolVLA**（`lerobot/smolvla_robocasa`） |
| LeRobot 做什么？ | **离线 SFT/BC** + `lerobot-eval` |
| RLinf 做什么？ | **在线 RL**：OpenPI π₀ + **PPO**，公开任务 **CloseDrawer** |
| 机器人？ | **PandaOmron**（Franka 臂 + Omron 全向底盘 + torso） |
| 动作维？ | 两边都是 **12D**，但 **flat 顺序不同，禁止直接互喂** |
| 本机推荐 conda？ | **`lerobot-robocasa`**（与 LIBERO 的 robosuite 隔离） |

```text
【LeRobot】Hub 数据 → lerobot-train(SmolVLA) → lerobot-eval(MuJoCo)
【RLinf】  SFT π₀ → PPO rollout → env/success_once
```

---

## 1. 两条栈对照

| 维度 | LeRobot | RLinf |
|------|---------|-------|
| 范式 | SFT / BC（离线） | Online RL（PPO 微调 π₀） |
| 入口 | `lerobot-train` / `lerobot-eval` | `run_embodiment.sh` |
| 公开任务例 | CloseFridge、`atomic_seen`… | CloseDrawer |
| 权重 | `lerobot/smolvla_robocasa` | `RLinf/RLinf-Pi0-RoboCasa` |
| 状态 | 16D | 25D |
| 相机 | 3×256（Hub 权重常需 rename→camera1/2/3） | 2×224 → base/wrist |
| 动作序 | **底盘优先**：base(4)+mode+ee(6)+grip | **臂优先**：ee(6)+grip+base(3)+torso+mode |
| Env | dict + `PandaOmronKeyConverter` | flat → `robosuite.make` |

---

## 2. 仿真与传感器（学什么）

### 2.1 本体

- **上**：Franka EE 相对位姿增量 6D + 夹爪  
- **中**：`base_mode`（HybridMobileBase）：`>0` 臂随底座期望运动更新；`<0` 臂相对已实现姿态  
- **下**：全向底盘 3D + torso；LeRobot 把 torso 并进 `base_motion[3]`

### 2.2 传感器（无 LiDAR）

| 类型 | 默认 |
|------|------|
| RGB | `robot0_agentview_left/right`、`robot0_eye_in_hand`（挂 `mobilebase0_support` / `robot0_right_hand`） |
| 深度 | 默认关（`camera_depths`） |
| 本体 | base_pos/quat、EE 相对、gripper_qpos |

位姿权威配置：`sims/robocasa/robocasa/utils/camera_utils.py`（`CAM_CONFIGS`）。

---

## 3. LeRobot：安装 → Finetune → 测试

### 3.1 安装（仿真依赖）

```bash
# 推荐：独立环境（勿与 LIBERO 的 robosuite 1.4 混装）
bash /home/sany/Documents/Foundation/tools/install_robocasa_cloned.sh

conda activate lerobot-robocasa
source /home/sany/Documents/Foundation/tools/robocasa_env.sh
export MUJOCO_GL=egl   # 无头服务器必开

cd /home/sany/Documents/Foundation/main/lerobot
```

资产（轻量足够默认评测）：

```bash
python -m robocasa.scripts.setup_macros
python -m robocasa.scripts.download_kitchen_assets \
  --type tex tex_generative fixtures_lw objs_lw
```

| 坑 | 处理 |
|----|------|
| 无 `lerobot[robocasa]` extra | 手装 editable robocasa/robosuite（`--no-deps`） |
| `Probabilities contain NaN` | 只用已下载 registry：`--env.obj_registries=['lightwheel']` |
| XML / 材质失败 | 确保装了 `tex_generative` |

### 3.2 仿真 smoke（验证环境）

```bash
bash /home/sany/Documents/Foundation/tools/run_robocasa_eval_smoke.sh
# 或手动 2 episode：
lerobot-eval \
  --policy.path=lerobot/smolvla_robocasa \
  --env.type=robocasa \
  --env.task=CloseFridge \
  --eval.batch_size=1 \
  --eval.n_episodes=2 \
  --eval.use_async_envs=false \
  --policy.device=cuda \
  '--rename_map={"observation.images.robot0_agentview_left":"observation.images.camera1","observation.images.robot0_eye_in_hand":"observation.images.camera2","observation.images.robot0_agentview_right":"observation.images.camera3"}' \
  --output_dir=./outputs/eval/robocasa_CloseFridge_smoke
```

视频示例目录：`Foundation/outputs/eval/robocasa_CloseFridge_smoke/videos/`。

### 3.3 Finetune（单任务 CloseFridge）

数据：[`pepijn223/robocasa_CloseFridge`](https://huggingface.co/datasets/pepijn223/robocasa_CloseFridge)

```bash
# 本机封装：
bash /home/sany/Documents/Foundation/tools/run_robocasa_train_CloseFridge.sh

# 等价：
cd /home/sany/Documents/Foundation/main/lerobot
lerobot-train \
  --policy.type=smolvla \
  --policy.repo_id=local/smolvla_robocasa_CloseFridge \
  --policy.load_vlm_weights=true \
  --policy.push_to_hub=false \
  --dataset.repo_id=pepijn223/robocasa_CloseFridge \
  --env.type=robocasa \
  --env.task=CloseFridge \
  --output_dir=./outputs/train/smolvla_robocasa_CloseFridge \
  --steps=100000 \
  --batch_size=4 \
  --env_eval_freq=5000 \
  --eval.batch_size=1 \
  --eval.n_episodes=5 \
  --save_freq=10000
```

### 3.4 正式评测

- 单任务建议 **20 episodes**（与公开协议一致）。  
- 多任务：`--env.task=CloseFridge,OpenCabinet,...`  
- 组快捷：`atomic_seen` / `composite_seen` / `composite_unseen` / `pretrain50|100|200|300`（自动设 split）

```bash
lerobot-eval \
  --policy.path=lerobot/smolvla_robocasa \
  --env.type=robocasa \
  --env.task=atomic_seen \
  --eval.n_episodes=20 \
  --eval.use_async_envs=false \
  --policy.device=cuda \
  '--rename_map={"observation.images.robot0_agentview_left":"observation.images.camera1","observation.images.robot0_eye_in_hand":"observation.images.camera2","observation.images.robot0_agentview_right":"observation.images.camera3"}'
```

自训且相机键用原生 `robot0_*` 时，**可不** `rename_map`。

### 3.5 数据流（LeRobot）

```text
Hub LeRobotDataset（12D 底盘优先）
  → lerobot-train (--policy.type=smolvla)
  → ckpt / lerobot/smolvla_robocasa
  → lerobot-eval --env.type=robocasa
       obs: 3 cams + 16D state (+ lang)
       action 12D → convert_action → dict
                 → unmap_action → robot0_{right,gripper,base,torso,base_mode}
                 → HybridMobileBase → MuJoCo
```

---

## 4. RLinf：后训练（π₀ + PPO）

公开配方范围：**CloseDrawer × PandaOmron × OpenPI π₀ × PPO**（无公开 robocasa GRPO yaml）。

### 4.1 安装

```bash
cd /home/sany/Documents/Foundation/main/RLinf
bash requirements/install.sh embodied --model openpi --env robocasa
# 或 Docker：rlinf/rlinf:agentic-rlinf0.3-robocasa → source switch_env openpi

python -m robocasa.scripts.download_kitchen_assets   # ~5GB 级厨房资产
```

中文文档：`main/RLinf/docs/source-zh/rst_source/examples/embodied/robocasa.rst`

### 4.2 下载 SFT 起点并启动 RL

```bash
hf download RLinf/RLinf-Pi0-RoboCasa --local-dir RLinf-Pi0-RoboCasa
# 把 examples/embodiment/config/robocasa_closedrawer_ppo_openpi.yaml
# 里 actor/rollout 的 model_path 指到本地目录

bash examples/embodiment/run_embodiment.sh robocasa_closedrawer_ppo_openpi
```

盯 TensorBoard：`env/success_once`（稀疏成功奖励）；`action chunk` 默认 5。

### 4.3 后训练循环

```text
π₀（常 pad 到 32D）→ 取 action_space 前 N 维
  → prepare_actions_for_robocasa：scatter 进 12D（缺省 DEFAULT，base_mode=-1）
  → RobocasaEnv.chunk_step → robosuite PandaOmron
  → 稀疏 success → PPO（GAE + actor_critic）→ 更新 FSDP actor
```

---

## 5. 动作：臂 + 底盘如何适配（必读）

### 5.1 LeRobot 布局（底盘优先）

`main/lerobot/src/lerobot/envs/robocasa.py` → `convert_action` → `PandaOmronKeyConverter.unmap_action`

| 索引 | 语义 | 落到控制器 |
|------|------|------------|
| 0:3 | base 平移/转向 | `robot0_base` |
| 3:4 | torso | `robot0_torso` |
| 4:5 | control_mode | `robot0_base_mode`（&lt;0.5→-1，否则 +1） |
| 5:8 | EE 位置增量 | `robot0_right[0:3]` |
| 8:11 | EE 旋转增量 | `robot0_right[3:6]` |
| 11:12 | gripper_close | `robot0_right_gripper`（二值 ±1） |

### 5.2 RLinf 布局（臂优先 / 对齐 HDF5）

`main/RLinf/rlinf/envs/robocasa/utils.py` → `ROBOCASA_ACTIONS`  
`prepare_actions_for_robocasa`：`main/RLinf/rlinf/envs/action_utils.py`

| 索引 | 名称 | 语义 |
|------|------|------|
| 0:6 | `rel_pose_6d` | 臂位置 3 + 姿态 3 |
| 6:7 | `gripper` | 夹爪 |
| 7:10 | `base` | 底盘 3D |
| 10:11 | `torso` | 升降 |
| 11:12 | `base_mode` | Hybrid 模式；DEFAULT=-1 |

也可用 `action_space=7d`：只写臂+夹爪，底盘/torso/mode 填默认。

### 5.3 互操作陷阱

同一物理含义、**不同索引顺序**。跨栈必须按 `PandaOmron_modality.json` / `reorder_hdf5_action` 重排，否则会把底盘指令喂给臂。

---

## 6. 模型矩阵（RoboCasa）

| 模型 | 路径 | 训 / 微调 | 测 |
|------|------|-----------|-----|
| **SmolVLA** | `main/lerobot` | `lerobot-train` + CloseFridge 等 | `lerobot-eval` + rename_map |
| ACT / Diffusion | LeRobot 通用 API | 无官方配方 | 无官方 ckpt |
| π₀ / π0.5 | `main/RLinf` | SFT + PPO | `env/success_once` |
| OpenVLA | RLinf 其它 embodied | 非 Robocasa 主线 | — |
| GR00T | `main/Isaac-GR00T` | `ROBOCASA_PANDA_OMRON` finetune | setup_RoboCasa + rollout |
| FluxVLA / AlphaBrain / LDA | `VLA/*` | 多为 GR1 tabletop | 与 LeRobot PandaOmron CLI 不同 |

---

## 7. 建议精读的代码路径（学习顺序）

### A. 仿真 / 传感器 / 控制器（先建立物理心智）

| 优先级 | 路径 | 学什么 |
|--------|------|--------|
| 1 | `sims/robocasa/robocasa/utils/camera_utils.py` | 相机挂点、fovy、随机化 |
| 2 | `sims/robocasa/robocasa/environments/kitchen/kitchen.py` | 如何把 cam_configs 注入 MuJoCo XML |
| 3 | `sims/robosuite/.../composite_controller.py` → `HybridMobileBase` | `base_mode` 如何改臂目标更新方式 |
| 4 | `sims/robocasa/robocasa/wrappers/gym_wrapper.py` | `PandaOmronKeyConverter` obs/action 映射、深度开关 |

### B. LeRobot 封装（训评主路径）

| 优先级 | 路径 | 学什么 |
|--------|------|--------|
| 1 | `main/lerobot/src/lerobot/envs/robocasa.py` | `DEFAULT_CAMERAS`、`convert_action`、16D state、`create_robocasa_envs` |
| 2 | `main/lerobot/src/lerobot/envs/configs.py` → `RoboCasaEnv` | CLI 默认相机/分辨率、features 注册 |
| 3 | `main/lerobot/src/lerobot/scripts/lerobot_train.py` | 通用训练入口 |
| 4 | `main/lerobot/src/lerobot/scripts/lerobot_eval.py` | 通用评测、`rename_map` |
| 5 | `main/lerobot/docs/source/robocasa.mdx` | 官方安装/任务组/评测协议 |
| 6 | `sims/robocasa/.../PandaOmron_modality.json` | 数据集动作切片定义 |
| 7 | `sims/robocasa/robocasa/utils/lerobot_utils.py` | HDF5↔LeRobot 动作重排 |

### C. RLinf 后训练

| 优先级 | 路径 | 学什么 |
|--------|------|--------|
| 1 | `main/RLinf/examples/embodiment/config/robocasa_closedrawer_ppo_openpi.yaml` | 主配方 |
| 2 | `main/RLinf/examples/embodiment/config/env/robocasa_closedrawer.yaml` | 12d/25d/2views |
| 3 | `main/RLinf/rlinf/envs/robocasa/utils.py` | `ROBOCASA_ACTIONS`、DEFAULT |
| 4 | `main/RLinf/rlinf/envs/action_utils.py` → `prepare_actions_for_robocasa` | 32D→12D scatter |
| 5 | `main/RLinf/rlinf/envs/robocasa/robocasa_env.py` | Env step / chunk |
| 6 | `main/RLinf/rlinf/models/embodiment/openpi/policies/robocasa_policy.py` | π₀ 输入输出 |
| 7 | `main/RLinf/examples/embodiment/run_embodiment.sh` | 启动器 |
| 8 | `main/RLinf/docs/source-zh/.../embodied/robocasa.rst` | 中文步骤 |

### D. 本机工具脚本

| 路径 | 用途 |
|------|------|
| `tools/install_robocasa_cloned.sh` | 隔离安装 |
| `tools/robocasa_env.sh` | `ROBOCASA_ROOT` / `MUJOCO_GL` |
| `tools/run_robocasa_train_CloseFridge.sh` | SmolVLA finetune |
| `tools/run_robocasa_eval_smoke.sh` | 评测 smoke |
| `tools/lerobot--smolvla_robocasa_model_download.sh` | 下 Hub 权重 |

---

## 8. 已知坑速查

| 坑 | 处理 |
|----|------|
| Hub SmolVLA 相机键 `camera1/2/3` | eval 加 `rename_map` |
| LeRobot 12D ≠ RLinf 12D 序 | 重排，勿直接互喂 |
| async env + EGL fork | smoke 用 `--eval.use_async_envs=false` |
| 夹爪/mode 连续值 | wrapper 按 0.5 阈值成 ±1 |
| 正式数字 | **20 ep/task**；CI 仅 1 ep smoke |

---

## 相关路径速查

| 项 | 路径 |
|----|------|
| LeRobot | `~/Documents/Foundation/main/lerobot` |
| RLinf | `~/Documents/Foundation/main/RLinf` |
| RoboCasa 仿真 | `~/Documents/Foundation/sims/robocasa` |
| robosuite | `~/Documents/Foundation/sims/robosuite` |
| 评测视频 | `~/Documents/Foundation/outputs/eval/robocasa_*` |
| Canvas | `~/.cursor/projects/home-sany-Documents-Foundation/canvases/robocasa-lerobot-rlinf-flows.canvas.tsx` |
