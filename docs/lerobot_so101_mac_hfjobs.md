# SO-ARM101 + Mac + HF Jobs 指南

> 场景：Mac（M2 Pro / 16GB 统一内存）遥操 **SO-ARM101**，ACT / SmolVLA finetune 与真机 rollout；可选 Linux RTX 5080 或 Hugging Face Jobs。  
> 仿真 LIBERO 全栈仍以 [fullstack](./lerobot_act_smolvla_fullstack.md) + Linux GPU 为主。

---

## 1. 可行性总览

| 环节 | ACT | SmolVLA |
|------|-----|---------|
| Mac 遥操采集 | ✅ 常见、够用 | ✅ 同左（采集不吃模型） |
| Mac 本地 finetune | ✅ **推荐** | ⚠️ 勉强（batch 1–2，易紧） |
| 真机 `lerobot-rollout` | ✅ 轻松 | ⚠️ 能跑，更慢/更吃内存 |
| Linux 5080 训 | ✅ | ✅ 更舒服 |
| HF Jobs 训 | ✅ 很合适 | ✅ 需 ≥16GB 显存实例 |

**推荐工作流：** Mac 采集 → 先 ACT 在 Mac（或 Jobs）训 → 真机 rollout 验链路 → 需要再上 SmolVLA（大训放 5080 / Jobs，ckpt 拷回 Mac rollout）。

---

## 2. Mac vs Linux GPU（能做什么）

| 事项 | Mac (MPS) | Linux + 5080 |
|------|-----------|--------------|
| 装 LeRobot、读数据、改代码 | ✅ | ✅ |
| ACT 小规模训 | ⚠️ 可，较慢 | ✅ |
| SmolVLA 正经 finetune | ❌ 不现实 / 仅冒烟 | ✅ |
| PushT 等轻仿真 eval | ✅ | ✅ |
| LIBERO 正式闭环评测 | ❌ 不够实用 | ✅（`MUJOCO_GL=egl`） |
| `--policy.device=cuda` | ❌ → 用 `mps`/`cpu` | ✅ |
| `groot` 等 CUDA extras | 残缺 | ✅ |

**单独 rollout / 轻量 eval：** 真机 rollout 多数够；LIBERO 正式四 suite 评测仍应用 Linux GPU。

---

## 3. 数据量与磁盘（单任务真机）

| 目标 | ACT | SmolVLA |
|------|-----|---------|
| 冒烟 / 能动 | **10–20** ep | **20–50** |
| 单任务较稳（常 >70%） | **40–80** 干净演示 | **50–150**（语言写清） |
| 多物体/多场景 | 100+，按失败补数 | 往往更多 |

质量 > 数量：相机固定、灯光稳、策略一致；卡在某阶段就专录 10–20 条。

| 内容 | ~50 ep | ~100 ep |
|------|--------|---------|
| 数据集（2 路相机视频+parquet） | **约 1–5 GB** | **约 2–10 GB** |
| ACT checkpoint | **约 50–200 MB** | 同左 |
| SmolVLA finetune 权重 | **约 0.8–1 GB** | 同左 |
| 中间 ckpt / 输出 | 再预留 **2–10 GB** | 同左 |

起步粗估：**每 50 ep 预留 ~5GB 数据 + ~1GB 模型**。

---

## 4. Hugging Face Jobs

**可行**，尤其适合「Mac 采集 → 云上训 → 拉回 Mac rollout」。

| | ACT | SmolVLA |
|--|-----|---------|
| Jobs | ✅ 小 GPU 即可 | ✅ 选 **≥16GB** 显存 |
| 前提 | 数据在 Hub（LeRobot 格式） | 同左；`lerobot-train` |
| 注意 | `HF_TOKEN`、依赖、超时 | batch 仍可能 1–4 |

适合：短任务、可复现、不占本机。  
不适合：长时间交互调试；**采集 / 真机 rollout 仍在 Mac**（要 USB）。

LeRobot 0.6+ 支持云训练入口（`--job.target` 一类）；具体参数以当前版本文档为准。

---

## 5. Mac 上 ACT / SmolVLA 注意点

**遥操：** 串口权限、相机分辨率别开太高（省统一内存）。SO-101（Feetech）是文档常见路径；robot type 常为 `so101_follower` 一类（以你安装的 LeRobot 文档为准）。

**ACT：** `--policy.device=mps`；几十～上百 ep 实用。

**SmolVLA：** `batch_size=1–2`、`freeze_vision_encoder=true`、`train_expert_only=true` 先冒烟；仍可能 OOM。首次还需 SmolVLM 骨干缓存（约 2–3GB）。

**Rollout：** 只推理；ACT 稳。SmolVLA 延迟高时可降分辨率或 RTC（若版本支持）。

---

## 6. 与仿真路径的分工

| 目标 | 机器 |
|------|------|
| 真机采集 / ACT 小训 / 真机 rollout | Mac |
| LIBERO / 大 VLA 训与正式 eval | Linux 5080 |
| 不想占本机的中等训 | HF Jobs（数据先上 Hub） |

本地实验阶段可不推 Hub；上 Jobs 前需要把 dataset push 到 Hub。
