# LeIsaac 起步教程（本机）

> 键盘遥操作 + 可视化；脚本在 `tools/`，日志在 `logs/`。核实：2026-07-14。

## 结论先看

| 问题 | 答案 |
|------|------|
| conda 环境 | `leisaac`（Python 3.11 + Isaac Sim 5.1） |
| 脚本目录 | `~/Documents/Foundation/tools/` |
| 日志 / done | `~/Documents/Foundation/logs/` |
| 起步交互 | 键盘遥操仿真臂；或 SmolVLA 闭环（§7）；轮臂见 `lekiwi` / [wheeled proto](../robotics/wheeled_decoupled_vla/wheeled_decoupled_vla_sim_proto.md) |
| 按 B 后 WASD 无反应 | 再点视口、关中文输入法、**按住**键；`lift` 已默认 `--sensitivity=5` |
| SmolVLA 跑通 | 双终端：`run_leisaac_smolvla_server.sh` → `run_leisaac_smolvla_eval.sh lift` |
| 冷启动 `import isaaclab_tasks` | 可能报 `omni.physics`；跑 teleop 会起 SimulationApp，属正常 |
| `conda activate` 报 `unbound variable` | `leisaac` 的 gcc deactivate hook 与 `set -u` 冲突；启动器用脚本已规避，**勿**在脚本里对 conda activate 开 `set -u` |

## 0. 环境准备

先激活环境，再跑工具脚本（脚本内部也会再 `conda activate`）：

```bash
source /home/sany/miniconda3/etc/profile.d/conda.sh
conda activate leisaac
source /home/sany/Documents/Foundation/tools/leisaac_env.sh
cd /home/sany/Documents/Foundation/sims/leisaac
```

也可不手动 activate，直接：

```bash
bash /home/sany/Documents/Foundation/tools/run_leisaac_demo.sh list
```

本机通常有 `DISPLAY` + GPU，可开 Isaac 窗口。

资产应已有（若缺则跑下载）：

```text
sims/leisaac/assets/robots/so101_follower.usd
sims/leisaac/assets/scenes/table_with_cube/scene.usd
sims/leisaac/assets/scenes/kitchen_with_orange/scene.usd
```

```bash
bash /home/sany/Documents/Foundation/tools/download_leisaac_starter_assets.sh
# 日志: logs/download_leisaac_assets.log
# 完成: logs/download_leisaac_assets.done
```

## 1. Hello：列出任务

```bash
bash /home/sany/Documents/Foundation/tools/run_leisaac_demo.sh list
# 或
cd /home/sany/Documents/Foundation/sims/leisaac
python scripts/environments/list_envs.py
```

本机实测输出（`2026-07-14`，Isaac Sim 5.1 / RTX 5080，headless kit）：

| # | Task Name | Config（简写） |
|---|-----------|----------------|
| 1 | `LeIsaac-SO101-AssembleHamburger-v0` | AssembleHamburgerEnvCfg |
| 2 | `LeIsaac-SO101-AssembleHamburger-BiArm-v0` | AssembleHamburgerBiArmEnvCfg |
| 3 | `LeIsaac-SO101-CleanToyTable-v0` | CleanToyTableEnvCfg |
| 4 | `LeIsaac-SO101-CleanToyTable-BiArm-v0` | CleanToyTableBiArmEnvCfg |
| 5 | `LeIsaac-SO101-CleanToyTable-BiArm-Direct-v0` | CleanToyTableBiArmEnvCfg (direct) |
| 6 | `LeIsaac-LeKiwi-CleanupTrash-v0` | CleanupTrashEnvCfg |
| 7 | `LeIsaac-SO101-FoldCloth-BiArm-v0` | FoldClothBiArmEnvCfg |
| 8 | `LeIsaac-SO101-FoldCloth-BiArm-Direct-v0` | FoldClothBiArmEnvCfg (direct) |
| 9 | `LeIsaac-SO101-LiftCube-v0` | LiftCubeEnvCfg — **起步推荐** |
| 10 | `LeIsaac-SO101-LiftCube-DigitalTwin-v0` | LiftCubeDigitalTwinEnvCfg |
| 11 | `LeIsaac-SO101-LiftCube-Mimic-v0` | LiftCubeMimicEnvCfg |
| 12 | `LeIsaac-SO101-LiftCube-Direct-v0` | LiftCubeEnvCfg (direct) |
| 13 | `LeIsaac-SO101-PickOrange-v0` | PickOrangeEnvCfg — **起步推荐** |
| 14 | `LeIsaac-SO101-PickOrange-Mimic-v0` | PickOrangeMimicEnvCfg |
| 15 | `LeIsaac-SO101-PickOrange-Direct-v0` | PickOrangeEnvCfg (direct) |

> 部分任务还需额外场景资产（toyroom / bedroom 等）；起步只用已下载的 `table_with_cube` + `kitchen_with_orange`。

## 2. 交互 Demo A：抬方块（推荐先跑）

```bash
bash /home/sany/Documents/Foundation/tools/run_leisaac_demo.sh lift
```

等价：

```bash
cd /home/sany/Documents/Foundation/sims/leisaac
source /home/sany/Documents/Foundation/tools/leisaac_env.sh
python scripts/environments/teleoperation/teleop_se3_agent.py \
  --task=LeIsaac-SO101-LiftCube-v0 \
  --teleop_device=keyboard \
  --num_envs=1 --device=cuda --enable_cameras
```

## 3. 交互 Demo B：厨房捡橙子

```bash
bash /home/sany/Documents/Foundation/tools/run_leisaac_demo.sh orange
```

```bash
python scripts/environments/teleoperation/teleop_se3_agent.py \
  --task=LeIsaac-SO101-PickOrange-v0 \
  --teleop_device=keyboard \
  --num_envs=1 --device=cuda --enable_cameras
```

## 4. 交互方式：键盘 vs 真机

当前起步 demo（`--teleop_device=keyboard`）是 **用键盘遥操仿真里的臂**，  
**不会**自动连接 SO-ARM101 真机。

| 模式 | 参数 | 说明 |
|------|------|------|
| 键盘（默认起步） | `--teleop_device=keyboard` | 本机键盘控仿真 SO101 |
| 真机 Leader | `--teleop_device=so101leader --port=/dev/ttyACM0` | USB 接 SO101 Leader，控仿真里的 Follower |

## 5. 键盘操作（必须先按 B）

**输入设备 = 键盘，控制对象 = Isaac 窗口里的仿真臂。**

1. **鼠标左键点一下中间 3D 视口**（不要焦点在 Stage / IsaacLab / Content 侧栏）
2. 确认没有中文输入法占用（切到英文），否则 WASD 无效果
3. 按 **`B`**（大写字母名，实际按 b 即可）→ **开始控制**
4. **按住**下面的键持续移动（点一下只有极小步进，几乎看不出）

| 键 | 作用 |
|----|------|
| **B** | **开始控制**（不按则臂完全不动，只刷新画面） |
| W / S | 前 / 后 |
| A / D | 左转肩 / 右转肩 |
| Q / E | 上 / 下 |
| J / L | 偏航左 / 右 |
| K / I | 俯仰 |
| U / O | 夹爪开 / 合 |
| R | 重置（失败回合） |
| N | 重置（成功回合） |
| Ctrl+C | 退出（在跑脚本的终端） |

动作偏小时加大灵敏度：

```bash
python scripts/environments/teleoperation/teleop_se3_agent.py \
  --task=LeIsaac-SO101-LiftCube-v0 \
  --teleop_device=keyboard \
  --num_envs=1 --device=cuda --enable_cameras \
  --sensitivity=5.0
```

启动成功时，终端会打印 `Teleoperation Controls for keyboard` 表；那是唯一操作说明源。

### 按了 B，其它键仍没反馈？

按下面顺序自查：

| 检查项 | 做法 |
|--------|------|
| 焦点 | 再点一次 **视口中央**；不要点 Stage 树 / 属性面板（点选关节后焦点常被抢走） |
| 输入法 | 关中文 IME / 用英文键盘布局；IME 会吞掉 WASD |
| 按住 | **按住** W 1–2 秒，不要连点；默认步进很小 |
| 灵敏度 | 加 `--sensitivity=5.0` 或 `10` |
| 进程 | 跑 `teleop_se3_agent.py` 的终端还在跑、没有又出现 CUDA `illegal memory access` |
| 真机误区 | 键盘模式下动真机不会影响仿真；真机要用 `so101leader` |

仍不动时：点视口 → `B` → **按住 `W`**，同时看仿真臂是否有一丁点位移；并把终端最后 30 行贴出来便于排查。

有真机 SO101 Leader 时：

```bash
--teleop_device=so101leader --port=/dev/ttyACM0
```

## 6. 无本机窗口（WebRTC）

```bash
bash /home/sany/Documents/Foundation/tools/run_leisaac_demo.sh lift-webrtc
```

## 7. SmolVLA 跑通本环境（策略闭环）

关闭键盘 teleop 后，用 **LeRobot async policy server + LeIsaac `policy_inference.py`** 让 SmolVLA 控仿真臂。

需要 **两个终端**（先 server，再 eval）。

**终端 1 — 策略服务（conda `lerobot` / Python 3.12，不要用 `leisaac`）：**

```bash
bash /home/sany/Documents/Foundation/tools/run_leisaac_smolvla_server.sh
# 或手工:
# conda activate lerobot
# python -m lerobot.async_inference.policy_server --host=127.0.0.1 --port=8080
# 日志: logs/leisaac_smolvla_server.log
```

> `leisaac` 是 Python 3.11，当前 editable `main/lerobot` 含 3.12 语法，在那边起 server 会 `SyntaxError`。Server 只做推理、不需要 Isaac。

**终端 2 — 仿真评测（仍用 `leisaac`）：**

```bash
# LiftCube（与前面键盘 demo 同一 env）
bash /home/sany/Documents/Foundation/tools/run_leisaac_smolvla_eval.sh lift

# 或厨房 PickOrange
bash /home/sany/Documents/Foundation/tools/run_leisaac_smolvla_eval.sh orange
```


默认：

| 子命令 | Task | 默认 Hub checkpoint | 相机映射 |
|--------|------|---------------------|----------|
| `lift` | `LeIsaac-SO101-LiftCube-v0` | `azazdeaz/smolvla_so101_leisaac_lift_cube` | `camera1,2,3`←front |
| `orange` | `LeIsaac-SO101-PickOrange-v0` | `edge-inference/smolvla-so101-pick-orange` | `front,wrist`←front |


可覆盖：

```bash
export POLICY_CKPT=/path/to/your/smolvla/pretrained_model
export POLICY_LANG='your instruction'
export EVAL_ROUNDS=5
bash tools/run_leisaac_smolvla_eval.sh lift
```

仿真中按 **`R`** 重置 episode；`EVAL_ROUNDS` 轮后退出。

注意：

- 这是 **SmolVLA 策略输出 → 仿真 SO101**，不是键盘/真机遥操。
- 默认 Hub 权重现改为 **LeIsaac 任务域** 微调模型（见上表）。真机 SO101（如 `1zsk/...`、`Sa74ll/...`）能跑通链路但 sim 成功率通常很低。
- 官方文档里的 `outputs/smolvla/leisaac-pick-orange/...` 是 **自己采集再训** 的路径；Hub 上社区权重质量参差，仍建议后续用本机 teleop 数据 finetune。
- Hub 上很多旧 SmolVLA 只有 `model.safetensors`、没有 `policy_preprocessor.json`。LeRobot 0.6 必需后者；可用:

```bash
conda activate lerobot
python main/lerobot/src/lerobot/processor/migrate_policy_normalization.py \
  --pretrained-path <hub_or_path> \
  --output-dir models/<name>_migrated
```

评测时用本地路径，例如：`--policy.path=/home/sany/Documents/Foundation/models/<name>_migrated`（约定见 [`docs/README.md`](./README.md) 与 [`models/README.md`](../models/README.md)）。

- 底栏 `DLSS ... (320, 240)` 警告可忽略，与本次 gRPC 报错无关。

等价手工命令（`lift`）：

```bash
# terminal 1（必须 lerobot 环境）
conda activate lerobot
python -m lerobot.async_inference.policy_server --host=127.0.0.1 --port=8080

# terminal 2（leisaac 环境）
conda activate leisaac
cd /home/sany/Documents/Foundation/sims/leisaac
python scripts/evaluation/policy_inference.py \
  --task=LeIsaac-SO101-LiftCube-v0 \
  --eval_rounds=3 \
  --policy_type=lerobot-smolvla \
  --policy_host=127.0.0.1 --policy_port=8080 \
  --policy_checkpoint_path=azazdeaz/smolvla_so101_leisaac_lift_cube \
  --policy_camera_keys=camera1,camera2,camera3 \
  --policy_language_instruction='Pick up the cube and lift it' \
  --policy_action_horizon=50 \
  --device=cuda --enable_cameras --rendering_mode=performance
```

## 8. 建议顺序

1. 确认资产
2. （可选）键盘 `lift` 熟悉场景
3. **SmolVLA**：`run_leisaac_smolvla_server.sh` → `run_leisaac_smolvla_eval.sh lift`

## 相关路径

| 用途 | 路径 |
|------|------|
| 启动器 | `tools/run_leisaac_demo.sh` |
| SmolVLA server | `tools/run_leisaac_smolvla_server.sh` |
| SmolVLA eval | `tools/run_leisaac_smolvla_eval.sh` |
| 环境变量 | `tools/leisaac_env.sh` |
| 下资产 | `tools/download_leisaac_starter_assets.sh` |
| 收尾安装 | `tools/finish_leisaac.sh` |
| 策略推理脚本 | `sims/leisaac/scripts/evaluation/policy_inference.py` |
| 源码 / teleop | `sims/leisaac/scripts/environments/teleoperation/` |
| 键盘映射实现 | `sims/leisaac/source/leisaac/leisaac/devices/keyboard/so101_keyboard.py` |
| 官方文档 | https://lightwheelai.github.io/leisaac/ |
| 兼容 stub（仍可用） | `logs/run_leisaac_demo.sh` → 转调 `tools/` |
