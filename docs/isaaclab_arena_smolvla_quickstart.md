# IsaacLab Arena × LeRobot（本机 SmolVLA 评测）

> 对照官方：[NVIDIA IsaacLab Arena & LeRobot](https://huggingface.co/docs/lerobot/envhub_isaaclab_arena)  
> 范围：**只跑 SmolVLA**（本机不跑 π0.5 / GR00T 评测路径）。核实：2026-07-14。

## 结论先看

| 问题 | 答案 |
|------|------|
| conda | `lerobot-arena`（Python **3.11** + Isaac Sim 5.1） |
| 代码 | IsaacLab `sims/IsaacLab`，Arena `sims/IsaacLab-Arena`，LeRobot editable `main/lerobot` |
| 环境变量 | `source tools/lerobot_arena_env.sh` |
| 官方 SmolVLA case | `nvidia/smolvla-arena-gr1-microwave` → GR1 开微波炉 |
| 启动器 | `bash tools/run_arena_smolvla_eval.sh microwave` |
| 为何不写 PI0.5 | 你这边只保 SmolVLA；PI 另需 `TORCH_COMPILE_DISABLE` 等，见官方文档 |
| 3.11 × main/lerobot | 已把 4 处 PEP695（3.12）语法改成 3.11 可解析，否则 `import SmolVLA` 会 SyntaxError |

## 0. 本机是否已就绪

```bash
source /home/sany/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /home/sany/Documents/Foundation/tools/lerobot_arena_env.sh

python - <<'PY'
import isaacsim, isaaclab, isaaclab_arena, lerobot
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.envs.configs import IsaaclabArenaEnv
print("OK", lerobot.__version__)
PY
```

安装/重修走：`bash tools/install_isaac_arena.sh`（日志 `logs/install_isaac_arena.log`，完成标记 `logs/install_isaac_arena.done`）。

官方安装步骤概要与本机一致：conda 3.11 → Isaac Sim 5.1 → IsaacLab v2.3.0 → IsaacLab-Arena `release/0.1.1` → LeRobot `[evaluation]` → 额外 deps + **钉死 `numpy==1.26.0`**。详见 [HF 文档](https://huggingface.co/docs/lerobot/envhub_isaaclab_arena)。

## 1. 预训练 SmolVLA（官方可用）

| Policy | 架构 | 任务 | Hub |
|--------|------|------|-----|
| `smolvla-arena-gr1-microwave` | SmolVLA | GR1 Microwave | [`nvidia/smolvla-arena-gr1-microwave`](https://huggingface.co/nvidia/smolvla-arena-gr1-microwave) |

（同页还有 `nvidia/pi05-arena-gr1-microwave`，本教程跳过。）

该权重观察大致为：

| 项 | 形状 / 键 |
|----|-----------|
| state | `observation.state` dim **54**（`robot_joint_pos`） |
| action | dim **36** |
| camera | `observation.images.robot_pov_cam`（eval 时需 rename） |

## 2. Case A：评测 GR1 Microwave（推荐先跑）

有窗口（本机有 `DISPLAY`）：

```bash
bash /home/sany/Documents/Foundation/tools/run_arena_smolvla_eval.sh microwave
```

等价手工命令（与官方一致，路径/环境变量已本地化）：

```bash
source /home/sany/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /home/sany/Documents/Foundation/tools/lerobot_arena_env.sh
cd /home/sany/Documents/Foundation/main/lerobot

# 若刚装过别的包把 numpy 顶走了，钉回 Isaac 所需版本
pip install -q 'numpy==1.26.0'

lerobot-eval \
  --policy.path=nvidia/smolvla-arena-gr1-microwave \
  --env.type=isaaclab_arena \
  --env.hub_path=nvidia/isaaclab-arena-envs \
  --rename_map='{"observation.images.robot_pov_cam_rgb": "observation.images.robot_pov_cam"}' \
  --policy.device=cuda \
  --env.environment=gr1_microwave \
  --env.embodiment=gr1_pink \
  --env.object=mustard_bottle \
  --env.headless=false \
  --env.enable_cameras=true \
  --env.video=true \
  --env.video_length=10 \
  --env.video_interval=15 \
  --env.state_keys=robot_joint_pos \
  --env.camera_keys=robot_pov_cam_rgb \
  --trust_remote_code=True \
  --eval.batch_size=1 \
  --eval.n_episodes=2
```

无头（远程 / SSH）：

```bash
HEADLESS=1 EPISODES=2 bash tools/run_arena_smolvla_eval.sh microwave
```

预期：进度条里出现 `running_success_rate=...%`（首轮冷启动很慢：拉 EnvHub、下权重、起 Isaac）。

视频目录示例：

```text
outputs/eval/<date>/<timestamp>_isaaclab_arena_smolvla/videos/gr1_microwave_0/eval_episode_*.mp4
```

## 3. Case B（可选）：随机动作冒烟（不加载策略）

只验证 EnvHub + Arena 能 step（官方 `test_env_load_arena` 思路）：

```bash
bash /home/sany/Documents/Foundation/tools/run_arena_smolvla_eval.sh smoke
```

内部用短步数 + `trust_remote_code`，不下载 SmolVLA 权重。

## 4. Case C（可选）：Lightwheel LW-BenchHub SmolVLA

官方同页的第二个 SmolVLA：[LightwheelAI/smolvla-double-piper-pnp](https://huggingface.co/LightwheelAI/smolvla-double-piper-pnp)。  
**本机尚未装 `lw_benchhub`**；需要时：

```bash
conda activate lerobot-arena
source tools/lerobot_arena_env.sh
conda install -y -c conda-forge pinocchio
pip install 'numpy==1.26.0'
sudo apt-get install -y git-lfs && git lfs install
cd /home/sany/Documents/Foundation/sims
git clone https://github.com/LightwheelAI/lw_benchhub
cd lw_benchhub && git lfs pull && pip install -e .
```

再按 [官方 Evaluate SmolVLA（LW-BenchHub）](https://huggingface.co/docs/lerobot/envhub_isaaclab_arena) 跑 `lerobot-eval`（`env.hub_path=LightwheelAI/lw_benchhub_env`，`action_dim=12`，三相机 rename_map）。装好后可用：

```bash
bash tools/run_arena_smolvla_eval.sh piper-pnp
```

## 5. 换物体 / 并行度

| 变量 / flag | 说明 |
|-------------|------|
| `--env.object=power_drill` / `mustard_bottle` / `cracker_box` | 操作物 |
| `--env.embodiment=gr1_pink` | 人形配置 |
| `--eval.batch_size=N` | 并行 env；OOM 时降到 1 |
| `--eval.n_episodes` | 评多少局 |
| `--env.headless=true` | 无窗；**必须**同时 `--env.enable_cameras=true` 才能出相机 |

## 6. 常见坑

| 现象 | 处理 |
|------|------|
| `SyntaxError` / `def f[T]` | 确认用的是已打补丁的 `main/lerobot`；重装 editable：`pip install --ignore-requires-python -e ".[evaluation,smolvla]"` |
| numpy 版本被抬高 | `pip install numpy==1.26.0` |
| EULA | `ACCEPT_EULA=Y PRIVACY_CONSENT=Y`（`lerobot_arena_env.sh` 已带） |
| CUDA OOM | `--eval.batch_size=1` |
| headless 无图 | `--env.headless=true --env.enable_cameras=true` |
| `libGLU.so.1` | `sudo apt install -y libglu1-mesa libxt6` |
| 动作维不符 | Microwave SmolVLA 要 `--env` 默认 GR1 dims；Lightwheel Piper 要 `--env.action_dim=12` |
| RTX 5080 + 相机花屏/非法访问 | 先 `batch_size=1`、短 `n_episodes`；仍崩再试 headless |

## 7. 和 LeIsaac 的关系

| | **IsaacLab Arena**（本文） | **LeIsaac**（`docs/leisaac_quickstart.md`） |
|--|---------------------------|---------------------------------------------|
| 入口 | `lerobot-eval` + EnvHub | `policy_inference.py` + async policy_server |
| 本体 | GR1 等人形 / Arena 任务 | SO101 桌面操作 |
| conda | `lerobot-arena` | `leisaac`（+ server 用 `lerobot` 3.12） |
| 本文 SmolVLA | `nvidia/smolvla-arena-gr1-microwave` | `azazdeaz/smolvla_so101_leisaac_lift_cube` 等 |

## 相关路径

| 用途 | 路径 |
|------|------|
| 启动器 | `tools/run_arena_smolvla_eval.sh` |
| 环境变量 | `tools/lerobot_arena_env.sh` |
| 安装脚本 | `tools/install_isaac_arena.sh` |
| IsaacLab | `sims/IsaacLab` |
| Arena | `sims/IsaacLab-Arena` |
| 官方文档 | https://huggingface.co/docs/lerobot/envhub_isaaclab_arena |
| EnvHub | https://huggingface.co/nvidia/isaaclab-arena-envs |
| 数据集样例 | [`nvidia/Arena-GR1-Manipulation-Task-v3`](https://huggingface.co/datasets/nvidia/Arena-GR1-Manipulation-Task-v3) |
