# 模型 / Benchmark 对照与评测协议

> 与 [fullstack](./lerobot_act_smolvla_fullstack.md) 互补。交互版见 Canvas `vla-benchmark-eval-playbook`（本地 + github.io）。

---

## 1. 总判断（高分从哪来）

公开 LIBERO 表上的高分，主流是：

**强预训练底座 → 在该 benchmark demo 上 finetune / post-train → 同 suite 闭环评 success**

不是 `*_base` 零样本。测的是「适配后执行能力」（新初始状态），**不是**严格 OOD / 跨 suite 零样本。

| 目标 | 要不要自己训 |
|------|----------------|
| 复现官方数字（SmolVLA / π0 / GR00T-LeRobot） | **不用**，评现成 `*_libero*` |
| 看 base 零样本 | 不用训，分数通常很差 |
| ACT LIBERO | **必须自己训**（无官方 LIBERO ckpt） |
| 跨 suite 泛化 | 要自己设计联合训 / hold-out；官方分 suite 权重测的不是这个 |

---

## 2. LIBERO 上模型对照（本机 5080 16GB）

| 模型 | 参数 / 权重 | LIBERO 评测权重 | 推理显存（eval bs=1） | 16GB 结论 |
|------|-------------|-----------------|----------------------|-----------|
| **ACT** | ~52M；ckpt ~50–200MB | 无官方 → 本地 ckpt | 很低 | ✅ 轻松 |
| **SmolVLA** | ~0.45B + SmolVLM | `lerobot/smolvla_libero` | 数 GB 级 | ✅ |
| **π0** | ~4B；BF16 ~8GB | `lerobot/pi0_libero_finetuned` | 实务约 8–12GB | ✅ 基本够 |
| **π0.5** | 同量级 ~4B | `lerobot/pi05_libero_finetuned` | 同档 | ✅ 基本够 |
| **GR00T N1.7** | ~3B；BF16 ~6GB | `nvidia/gr00t17-lerobot-libero_{spatial,object,goal,10}-640` | 官方下限常 **16GB+** | ⚠️ 偏紧（同卡跑 MuJoCo） |

训练显存远高于上表（π/GR00T full FT 常要几十 GB）——与「只做 eval」无关。

### SmolVLA 复现耗时（粗估）

| 路径 | 时间（5080） |
|------|----------------|
| 现成 `smolvla_libero`，论文协议 4 suite × 10 ep/task（共 400 ep），`n_action_steps=1` | **约 4–8 小时** |
| 从 `smolvla_base` 自己 100k finetune 再评 | **约 2–4 天** + 评测 |

坑：`smolvla_libero` 默认 `n_action_steps` 可能是 50；对论文仿真协议需显式 `--policy.n_action_steps=1`。开源 ckpt 常落在 ~70–85%，未必精确锁死论文 87.3%。

### GR00T：suite 与权重

| Suite | 考什么 |
|-------|--------|
| Spatial | 空间关系 |
| Object | 物体种类 |
| Goal | 目标/意图 |
| LIBERO-10 (Long) | 更长多步 |

官方公开的是 **每 suite 一份专精权重**，没有「一个 `gr00t17-lerobot-libero` 打全四 suite」的单模型。

```text
nvidia/GR00T-N1.7-3B          ← 共同底座
        ├─ Isaac 栈 → GR00T-N1.7-LIBERO/{spatial,...}
        └─ LeRobot 栈 → gr00t17-lerobot-libero_*-640
```

LeRobot 版是 **用 LeRobot 重新 finetune**，不是 Isaac 权重无损转格式。

---

## 3. 闭环评测需要什么

| 需要 | 不需要（仅评测时） |
|------|-------------------|
| 策略权重 | 完整 `HuggingFaceVLA/libero` ~70GB |
| LIBERO 仿真包 + **libero-assets** | — |
| MuJoCo + `MUJOCO_GL=egl`（Linux 无头） | — |

可视化：LIBERO 多为离屏渲染；看 case 播 `output_dir/videos/` 下 mp4，一般**没有**实时 GUI。

冒烟规模（1 suite × 1 task × 2 ep）在 5080 上常约 **10–30 分钟**（含首次加载）。

---

## 4. 仿真 env 矩阵（`--env.type=`）

**总判断：** 闭环 eval 一般只需 **policy + env**；要训才下对应 Hub dataset。跨 env 零样本通常不行。

| env.type | 训练数据（Hub） | 常用 base | 常用 finetuned 评测权重 | 备注 / 冲突 |
|---|---|---|---|---|
| `libero` | `HuggingFaceVLA/libero` | `smolvla_base` / `pi0_base` / `pi05_base` | `smolvla_libero`、`pi0_libero_finetuned`、`pi05_libero_finetuned` | 主推；本机已就绪 |
| `libero_plus` | `lerobot/libero_plus` + 资产 | 常从 `smolvla_base` | `smolvla_libero_plus` | 与 vanilla LIBERO **互斥安装** |
| `metaworld` | `lerobot/metaworld_mt50` | `smolvla_base` | `smolvla_metaworld` | 本机可 import |
| `pusht` | `lerobot/pusht` | 无 VLA 惯例；IL 从零 | `diffusion_pusht`、`vqbet_pusht` | 最轻；无官方 `smolvla_pusht` |
| `aloha` | `lerobot/aloha_sim_*` | 无 `act_base` | `act_aloha_sim_*` | 经典自训 ACT |
| `robocasa` | 示例/上游自备 | `smolvla_base` | `smolvla_robocasa` | 无 pyproject extra；`robocasa` pin 旧 lerobot → `--no-deps` |
| `robotwin` | `lerobot/robotwin_unified` | `smolvla_base` | `smolvla_robotwin` | 需单独装 RoboTwin |
| `vlabench` | `VLABench/vlabench_*_lerobot_video` | `smolvla_base` | `smolvla_vlabench` | 需手动装 VLABench |
| `robomme` | `lerobot/robomme` | `smolvla_base` | `smolvla_robomme` | **冲突**：`mani-skill` pin `gymnasium==0.29.1`、`numpy<2` vs lerobot `numpy>=2` → **建议 Docker，本机先跳过** |
| `isaaclab_arena` | `nvidia/Arena-*` 等 | `smolvla_base` / `pi05_base` | `nvidia/smolvla-arena-*` 等 | 需 Isaac Sim/Lab；极重 |
| `gym_manipulator` | 自采 / HIL | — | 无统一官方 IL ckpt | 真机 HIL，非标准仿真榜 |

**RoboCerebra**：无独立 type；复用 `--env.type=libero --env.task=libero_10` + 相机映射；数据 `lerobot/robocerebra_unified`，权重 `lerobot/smolvla_robocerebra`。

Hub 命名惯例：`lerobot/<policy>_<benchmark>`。

### 本机就绪（对话时点）

| 已可用 | 需额外装 |
|--------|----------|
| `libero`、`metaworld`、`pusht`、`aloha` | `libero_plus`、`robocasa`、`vlabench`、`robotwin`、`robomme`、`isaaclab_arena` |

---

## 5. 示例 eval 入口

```bash
export MUJOCO_GL=egl

# SmolVLA（论文向：n_action_steps=1）
lerobot-eval \
  --policy.path=lerobot/smolvla_libero \
  --env.type=libero \
  --env.task=libero_spatial,libero_object,libero_goal,libero_10 \
  --eval.batch_size=1 --eval.n_episodes=10 \
  --env.max_parallel_tasks=1 \
  --policy.n_action_steps=1 --policy.device=cuda

# π0.5（文档复现常 n_action_steps=10）
lerobot-eval --policy.path=lerobot/pi05_libero_finetuned \
  --env.type=libero --env.task=libero_spatial \
  --eval.batch_size=1 --eval.n_episodes=10 \
  --policy.n_action_steps=10 --policy.device=cuda

# GR00T（需 lerobot[groot]；suite ↔ 权重一一对应）
lerobot-eval --policy.type=groot \
  --policy.base_model_path=nvidia/gr00t17-lerobot-libero_spatial-640 \
  --policy.embodiment_tag=libero_sim \
  --env.type=libero --env.task=libero_spatial \
  --eval.n_episodes=10 --policy.device=cuda
```

---

## 6. 信息不足 / 易变项

- 各模型 **精确** 峰值显存随 LeRobot 版本、dtype、是否同卡跑仿真而变；上表为对话调研量级。
- Hub 上权重命名与 CI 用 ckpt 可能更新；以官方 `docs/source/*.mdx` 为准。
- RoboCasa / Isaac 全量资产体积未在对话中精确标定。
