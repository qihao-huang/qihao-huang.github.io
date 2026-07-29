# VLA 的 SFT 与 RL（LeRobot 核实版）

> 用途：弄清 **VLA / IL 栈里「SFT」和「RL」分别指什么、LeRobot 能跑哪条**，以及 **WAM（FastWAM）能不能做 RL**。  
> 对照：[ACT+SmolVLA 全栈](./lerobot_act_smolvla_fullstack.md) · [WAM hands-on](./lerobot_wam_handson.md) · [模型矩阵](./lerobot_model_benchmark_matrix.md) · [FAQ](./lerobot_faq_cheatsheet.md)  
> 核实：`main/lerobot`（约 0.6.1，2026-07-10）；以代码与 `docs/source/*` 为准，不替代官方文档。

---

## 结论先看

| 问题 | 答案 |
|------|------|
| VLA 的 **SFT** 在 LeRobot 里是什么？ | 在 demo 上做 **行为克隆 / supervised finetune**，入口几乎都是 **`lerobot-train`**（离线、有监督损失）。 |
| VLA 的 **RL** 在 LeRobot 里怎么做？ | **主路径 = HIL-SERL**：`gaussian_actor` + **SAC** + actor/learner +（可选）reward classifier；**不是**给 SmolVLA/π0/FastWAM 挂 RL API。 |
| ACT / SmolVLA / π0 / GR00T / FastWAM / lingbot_va / vla_jepa 能做 RL 吗？ | **在 LeRobot 内：都不能**（无接 SAC/actor-learner）。它们只有 **SFT/BC**（`lerobot-train`）。 |
| FastWAM 的 video+action diffusion 算 SFT 吗？ | **算**（演示数据上的监督多目标训练）；**不算 RL**。 |
| LeRobot 里 FastWAM 能不能做 RL？ | **目前不能**（无文档、无代码钩子）。上游 `WAM/FastWAM` 同样是监督训评，无 RL 管线。 |
| 想做「VLA + online RL」？ | 工作区另有 **RLinf**（OpenVLA 等），**不走** `lerobot-train` / HIL-SERL。 |
| 16GB 优先？ | **SFT → SmolVLA**；RL（HIL-SERL）更吃交互与工程，不是「换个 VLA type」就能上。 |

```text
【SFT / BC】demo dataset ──► lerobot-train ──► ACT / SmolVLA / π0 / FastWAM / …
【RL / HIL】demo + online rollouts ──► reward_classifier（可选）
                                    ──► lerobot.rl.learner + lerobot.rl.actor
                                    ──► policy.type=gaussian_actor + algorithm=sac
【VLA+RL 另栈】RLinf / 上游论文栈（非本笔记主路径）
```

---

## 1. SFT 在 VLA 里指什么

### 1.1 含义

在机器人 / VLA 语境里，**SFT（Supervised Fine-Tuning）** 通常就是：

- 用人类（或脚本）采集的 **demonstration**；
- 以 **行为克隆（BC）** 或等价监督目标（L1、flow-matching MSE、diffusion 速度场等）拟合 `obs (+ language) → action`；
- 对已有 **foundation / base** 权重做 **finetune**（SmolVLA、π0、GR00T…），或对小模型 **从零训**（ACT 常见）。

它与「带 reward、在线交互、策略梯度 / Q-learning」的 **RL** 相对。LeRobot README 把这类模型归在 **Imitation Learning / VLAs / World Models**，训练入口统一为离线 `lerobot-train`。

### 1.2 与 `lerobot-train` 的关系

| 项 | 说明 |
|----|------|
| 入口 | CLI `lerobot-train` → `src/lerobot/scripts/lerobot_train.py` |
| 数据 | `LeRobotDataset`（Hub `repo_id` 或本地） |
| 优化 | 对 batch 算 policy `forward` 的监督 loss，反向传播 |
| 评测 | 训练中开环 `eval_loss`；闭环另用 `lerobot-eval`（见 FAQ） |
| 旁路 | 同一脚本也可训 **reward model**（`--reward_model.type=...`），那是给 RL 供奖励，本身仍是监督分类/回归 |

**典型 VLA SFT 流程（SmolVLA / π0 一类）：**

1. 装对应 extra（如 `[smolvla]`、`[pi]`）。
2. 准备 demo（自采或 Hub，如 `HuggingFaceVLA/libero`）。
3. `--policy.path=<base>` 加载预训练，再 `--dataset.repo_id=...` finetune。
4. 可选 `lerobot-eval` 看闭环 success。

ACT 无通用 `act_base`，多为 **从零 BC**；SmolVLA **必须**从 `lerobot/smolvla_base`（或已有 finetuned）出发才有意义。细节见 [fullstack](./lerobot_act_smolvla_fullstack.md)。

### 1.3 各模型「监督目标」一句话

| 模型 | 监督目标（SFT/BC 侧） |
|------|----------------------|
| ACT | CVAE + L1（+ KL） |
| SmolVLA | Action expert **flow matching** |
| π0 / π0.5 | Flow matching / 相关 VLA 动作头（LeRobot 适配 OpenPI） |
| GR00T | 多模态 VLA finetune（LeRobot `groot`） |
| FastWAM | **`λ_video·L_video + λ_action·L_action`**（视频+动作 flow） |
| lingbot_va | 自回归 video-action 监督 |
| vla_jepa | VLM + world model + flow-matching 动作头监督 |

---

## 2. RL 在 VLA/IL 栈里怎么做（LeRobot）

### 2.1 官方归类

`main/lerobot/README.md`：

| 类别 | 内容 |
|------|------|
| **Reinforcement Learning** | **HIL-SERL**、**TDMPC**（QC-FQL coming soon） |
| **Reward Models** | reward classifier / SARM / TOPReward / Robometer（给 RL 或离线奖励） |
| **VLAs / World Models** | SmolVLA、π0、GR00T、FastWAM… → **走 IL/SFT，不在 RL 表** |

### 2.2 主路径：HIL-SERL（真机 / gym_hil）

文档：`docs/source/hilserl.mdx`、`hilserl_sim.mdx`。

流水线：

1. **采 demo**（`gym_manipulator` / 真机 + 遥操作）。
2. （推荐）**训 reward classifier**：`lerobot-train` + `--reward_model.type=reward_classifier`，用于自动成功判定 / 稠密奖励。
3. **Actor–Learner 在线 SAC**：
   - `python -m lerobot.rl.learner --config_path ...`
   - `python -m lerobot.rl.actor --config_path ...`
4. 人可随时介入（gamepad / space），纠正探索 → **Human-in-the-Loop**。

| 组件 | 注册名 / 模块 | 说明 |
|------|----------------|------|
| Policy | `policy.type=gaussian_actor` | 高斯 actor + 观测编码器；**不是** VLA |
| Algorithm | `algorithm.type=sac` | `lerobot/rl/algorithms/sac/`；工厂目前 **仅注册 `sac`** |
| 数据混合 | `mixer=online_offline` | online replay + offline demo 混合（**RLPD 风格混合**；代码未命名为 `rlpd`） |
| Env | `HILSerlRobotEnv` / `gym_hil` | 末端空间 + 可选 IK、crop、干预 |

**要点：** HIL-SERL **不**把 SmolVLA/π0 当 actor。硬件指南里写的 `sac` 指这套 RL 栈；CLI 策略类型是 **`gaussian_actor`**。

### 2.3 其它 RL 相关

| 路径 | 入口 | 与 VLA |
|------|------|--------|
| **TDMPC** | `policy.type=tdmpc`，可用 `lerobot-train` 在带 reward 的离线数据上训 | 独立小模型 MPC/RL；**非** VLA |
| **Reward models** | `lerobot-train` + `reward_model.type∈{reward_classifier,sarm,topreward,robometer}` | 为 HIL-SERL / 下游 RL 供奖励；**不**更新 VLA 权重 |
| **QC-FQL** | README：coming soon | — |

### 2.4 哪些 policy「接了 RL API」

| 接了 | 只有 SFT/BC（`lerobot-train`） |
|------|--------------------------------|
| `gaussian_actor`（+ SAC actor/learner） | `act`, `diffusion`, `vqbet`, `smolvla`, `pi0`, `pi05`, `pi0_fast`, `groot`, `fastwam`, `lingbot_va`, `vla_jepa`, `xvla`, `eo1`, … |
| `tdmpc`（自身含 RL 形式损失 / MPC） | 上表其余 VLA/WAM |

代码核实：`SACAlgorithm` 类型注解要求 `GaussianActorPolicy`；`smolvla` / `pi0` / `fastwam` / `groot` 等目录内 **无** `rl.` / SAC / actor-learner 引用。

### 2.5 工作区其它：RLinf（一笔）

`main/RLinf/` 提供 **VLA 的 online RL**（如 ManiSkill 上 OpenVLA / OpenVLA-OFT + PPO；RoboCasa 上 **π₀ + PPO CloseDrawer**），与 LeRobot HIL-SERL **平行**。若目标是「大 VLA + 仿真 RL」，看 RLinf；**不是**改 `policy.type=smolvla` 就能进 `lerobot.rl`。  
RoboCasa 双栈步骤与代码路径见 [`robocasa_lerobot_rlinf_handson.md`](./robocasa_lerobot_rlinf_handson.md)。

---

## 3. 对照表：模型 × SFT × RL

| 模型 | SFT / BC | RL（LeRobot） | 一句话 |
|------|:--------:|:-------------:|--------|
| **ACT** | ✅ | ❌ | 经典 IL；`lerobot-train` 从零或续训；无 HIL-SERL 挂钩。 |
| **SmolVLA** | ✅ | ❌ | 小 VLA；从 `smolvla_base` finetune；16GB 友好。 |
| **π0 / π0.5** | ✅ | ❌ | 大 VLA SFT；训显存常需 24–40GB+；无 LeRobot RL API。 |
| **GR00T** | ✅ | ❌ | LeRobot `groot` 做 benchmark finetune；无 RL 钩子。 |
| **FastWAM** | ✅ | ❌ | 监督 video+action；见下节。**LeRobot 内不能做 RL。** |
| **lingbot_va** | ✅ | ❌ | Wan 自回归 video-action；仅 `lerobot-train`。 |
| **vla_jepa** | ✅ | ❌ | Qwen3-VL + V-JEPA2 + 动作头；仅 SFT。 |
| **gaussian_actor** | 部分* | ✅ | *可用 offline demo 预热，但主路径是 **SAC 在线**（HIL-SERL）。 |
| **tdmpc** | 部分† | ✅† | †离线/带 reward 数据上的 model-based RL；非 VLA。 |
| **reward_classifier 等** | ✅（训 RM） | 支撑 RL | 不直接控机器人；给 HIL-SERL 供奖励。 |

图例：✅ = 官方路径可用；❌ = 本仓库无接；「部分」= 有监督/离线成分但定位不是 VLA-SFT。

---

## 4. WAM 专节（FastWAM）

### 4.1 训练目标算不算 SFT？

**算（监督 / BC 族），不算 RL。**

- LeRobot：`FastWAM.training_loss` → `λ_video * loss_video + λ_action * loss_action`（flow / 速度场类），数据来自 **LeRobot demo**。
- 推理：`infer_action` **直接出动作**，不做 test-time 未来帧想象。
- 入口：与其它 policy 一样，`lerobot-train --policy.type=fastwam`（或 `policy.path=...`）。

因此：FastWAM 的「训」= **带世界模型辅助损失的 supervised finetune / BC**，不是 reward-driven RL。

### 4.2 有无 RL / 闭环 fine-tune 钩子？

| 来源 | RL？ |
|------|------|
| LeRobot `policies/fastwam/`、`docs/source/fastwam.mdx` | **无** RL、无 actor-learner、无 SAC 适配 |
| 上游 `WAM/FastWAM/`（`scripts/train.py`、README） | **监督训 + 闭环评测**；无 RL 训练章节；第三方 RoboTwin 提到 RLinf 分支属 **仿真平台**，不是 FastWAM 本体 RL |
| HIL-SERL | 只认 `gaussian_actor`，**不能**把 FastWAM 当 actor |

### 4.3 结论（明确）

> **目前在 LeRobot 里，FastWAM / WAM 只能做 SFT（监督 video+action），不能做 RL。**  
> 若需要 VLA/WAM 类模型的 online RL，需另栈（如 RLinf 或自研），本仓库未提供现成钩子。

更多训评命令与 16GB 墙见 [lerobot_wam_handson.md](./lerobot_wam_handson.md)。

---

## 5. 有限显存实践建议（16GB）

| 目标 | 建议 |
|------|------|
| 先跑通 VLA **SFT** | **SmolVLA**：`batch_size=2–4`，可 `freeze_vision_encoder` / LoRA；见 fullstack smoke。 |
| ACT | 显存极低，适合先验证数据与 eval 管线。 |
| π0 / π0.5 / GR00T **训** | 16GB 通常不够 full FT；可只做 **eval** 现成 ckpt，或上更大卡 / HF Jobs。 |
| FastWAM **训/评** | 权重体量远超 16GB；本机以读配置 / registry 为主，真训需大显存。 |
| **RL（HIL-SERL）** | 瓶颈常是 **真机/仿真交互、人介入、工程配置**，不是「再塞一个 VLA」。`gaussian_actor` 本身相对轻，但整条 actor-learner + 相机 + 干预流程重。 |
| Reward classifier | 可用 `lerobot-train` 在 16GB 上训小分类器，再接到 HIL env。 |

---

## 6. 可复制命令骨架

本地默认加 `--policy.push_to_hub=false`（或配置里关闭 push）。

### 6.1 SFT（SmolVLA smoke）

```bash
cd ~/Documents/Foundation/main/lerobot

lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=HuggingFaceVLA/libero \
  --dataset.episodes="[0,1,2,3,4,5,6,7,8,9]" \
  --dataset.eval_split=0.1 \
  --steps=1000 \
  --batch_size=2 \
  --eval_steps=200 \
  --env_eval_freq=0 \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --output_dir=../../outputs/smoke_smolvla_sft \
  --job_name=smoke_smolvla_sft \
  --wandb.enable=false
```

FastWAM 的 SFT 骨架（需大显存，仅示意）：

```bash
lerobot-train \
  --dataset.repo_id=<your-org/your-dataset> \
  --policy.type=fastwam \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --batch_size=1 \
  --steps=1000 \
  --output_dir=../../outputs/smoke_fastwam_sft
```

### 6.2 RL（HIL-SERL 最小双进程）

需先：`pip install -e ".[hilserl]"`，并准备 **同一份** train JSON（含 `policy.type=gaussian_actor`、`algorithm.type=sac`、env、可选 offline dataset）。示例配置见官方 Hub：`lerobot/config_examples`（RL / HIL）。

```bash
# 终端 1：learner
python -m lerobot.rl.learner --config_path /path/to/train_config_hilserl.json

# 终端 2：actor（需 learner 已起）
python -m lerobot.rl.actor --config_path /path/to/train_config_hilserl.json
```

Reward classifier（SFT 训 RM，供后续 RL）：

```bash
lerobot-train --config_path /path/to/reward_classifier_train_config.json
```

仿真预演：`docs/source/hilserl_sim.mdx`（`gym_hil` + 同 actor/learner）。

---

## 相关路径

| 路径 | 内容 |
|------|------|
| `main/lerobot/src/lerobot/scripts/lerobot_train.py` | SFT / reward model 训练入口 |
| `main/lerobot/src/lerobot/rl/` | actor、learner、SAC、buffer、online_offline mixer |
| `main/lerobot/docs/source/hilserl.mdx` | HIL-SERL 真机工作流 |
| `main/lerobot/docs/source/hilserl_sim.mdx` | 仿真 HIL |
| `main/lerobot/docs/source/smolvla.mdx` / `fastwam.mdx` / `pi0.mdx` … | 各 policy SFT 文档 |
| `main/lerobot/src/lerobot/policies/gaussian_actor/` | RL 用 policy |
| `main/lerobot/src/lerobot/policies/fastwam/` | WAM 监督实现 |
| `WAM/FastWAM/` | 上游监督训评（非 LeRobot RL） |
| `main/RLinf/` | 另栈 VLA-RL（含 RoboCasa π₀+PPO） |

官方文档索引：<https://huggingface.co/docs/lerobot>（hilserl、smolvla、fastwam、hardware_guide）。
