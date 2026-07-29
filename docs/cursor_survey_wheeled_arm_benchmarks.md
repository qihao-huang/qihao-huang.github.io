# Survey wheeled-arm benchmarks
_Exported on 2026/7/29 at GMT+8 13:56:21 from Cursor (3.13.10)_

---

**User**

Research survey in **Simplified Chinese** for the user.

Questions:
1. Survey market + academia **wheeled-arm / mobile manipulator** benchmarks and datasets (as comprehensive as practical 2024–2026).
2. Does **decoupled humanoid** (upper body + separate locomotion, e.g. GR1 tabletop, whole-body but not wheeled) count as 轮臂? Give a clear taxonomy.
3. What do VLA/IL models **output** to adapt to different wheeled-arm embodiments and bases? (action spaces: SE2 cmd_vel, Ackermann, joint base, hybrid base_mode+EE, etc.)
4. How can **pure upper-limb manipulation** pretrained models be adapted to wheeled-arm robots?

Include known names: RoboCasa/PandaOmron, Galaxea R1, AgiBot Genie wheeled, BEHAVIOR R1Pro, Mobile ALOHA / AgileX, LeKiwi, Tiago, Fetch, Stretch, Open-X / OXE mobile subsets, Bridge, DROID (mostly fixed?), CALVIN?, Habitat/AI2-THOR mobile manip?, ManiSkill mobile?, SoftBank/PAL TIAGo datasets, RoboCasa NavigateKitchen, etc.

Also check workspace briefly if useful:
- /home/sany/Documents/Foundation/docs/robocasa_task_catalog.md
- robotics/wheeled_decoupled_vla/ if exists
- docs mentioning 轮臂

Structure answer as:
## 轮臂怎么定义 / decoupled 人形算不算
## Benchmark & Dataset 表（名称 | 形态 | 仿真/真机 | 动作空间要点 | 链接或出处）
## 模型输出如何适配不同轮臂与底盘
## 纯上肢模型 → 轮臂 的常见适配路径
## 简要结论与选型建议

Use WebSearch. Be accurate; mark uncertain items. Prefer tables. Cite markdown links.

---

**Cursor**

我来做一轮系统调研：先查工作区相关文档，同时检索 2024–2026 轮臂/移动操作基准与数据集。

工作区侧记：本仓 [`docs/robocasa_task_catalog.md`](docs/robocasa_task_catalog.md) 已把任务分成「贴夹具 / 仅导航 / 轮臂结合」；[`docs/robocasa_lerobot_rlinf_handson.md`](docs/robocasa_lerobot_rlinf_handson.md) 写明 PandaOmron 的 12D 动作与 `base_mode`。`robotics/wheeled_decoupled_vla/` 在索引中有引用，但当前目录未检出实体文件。

---

## 轮臂怎么定义 / decoupled 人形算不算

**实用定义（建议）**：轮臂 = **轮式（或全向/差速）底盘 + 至少一条操作臂**，且策略/数据中 **底盘自由度会被主动控制**（导航或边走边操作）。关键能力是「移动扩大可达工作空间 + 操作」。

| 类别 | 典型形态 | 算不算「轮臂」 | 说明 |
|------|----------|----------------|------|
| **严格轮臂** | PandaOmron、Tiago、Fetch、Stretch、Mobile ALOHA/AgileX、LeKiwi、Galaxea R1/R1Pro、AgiBot 轮式双臂 | **是** | 底盘为轮式，臂+底盘联合控制 |
| **任务级轮臂**（本仓启发式） | RoboCasa 跨区 composite（DeliverStraw 等） | **是（任务层面）** | 同一本体上，只有需要显著底盘位移的任务才算「轮臂结合」 |
| **贴夹具轮臂数据** | RoboCasa 多数 atomic（CloseFridge 等） | **半是** | 本体是轮臂，但演示几乎不走底盘 → 对学「轮臂协同」弱 |
| **可移动台但非控制底盘** | DROID（Franka 装在可推升降桌上） | **否（策略意义）** | 场景可换，动作空间基本是固定臂 |
| **Decoupled 人形（上肢/桌面）** | GR1 tabletop、多数固定腰/固定脚上肢 VLA | **否** | 无轮式底盘；属「上肢操作」 |
| **全身人形（腿式/混合）** | 双足 G1、全身但不轮式 | **否（严格轮臂）** | 可叫 mobile manip / whole-body，底盘动力学不同 |
| **四足+臂** | Spot+arm、部分 OXE quadruped | **否（轮臂）** | 属另一类移动操作 |

**对问题 2 的明确答复**：  
**Decoupled 人形（上肢 + 独立 locomotion，如 GR1 tabletop；或全身但非轮式）不算严格「轮臂」。**  
可算 **「可迁移的上肢先验」**：臂/EE 表示、抓取先验可迁到轮臂，但 **底盘 SE(2)/cmd_vel、Hybrid mode、导航–操作切换** 必须另学或外挂规划。

与本仓一致的三分类（任务，非本体）：

1. **贴夹具操作** — 底盘几乎不动  
2. **仅导航** — 如 NavigateKitchen  
3. **轮臂结合跨区** — 有意义底盘位移 + 操作  

---

## Benchmark & Dataset 表

> 标注：✓ 明确轮臂｜△ 本体可移动但数据偏固定臂｜○ 移动操作但非轮式/形态特殊｜? 公开细节不完全确定  

| 名称 | 形态 | 仿真/真机 | 动作空间要点 | 链接或出处 |
|------|------|-----------|--------------|------------|
| **RoboCasa / RoboCasa365** | PandaOmron（Franka+Omron 全向+torso）✓ | 仿真（MuJoCo/robosuite） | 常用 **12D**：臂 OSC 6 + gripper + base(~3–4) + **base_mode/control_mode**；LeRobot 与 HDF5 索引顺序不同 | [robocasa.ai](https://robocasa.ai/) · [GitHub](https://github.com/robocasa/robocasa) · [LeRobot 文档](https://huggingface.co/docs/lerobot/main/en/robocasa) |
| **NavigateKitchen**（RoboCasa atomic） | 同上 ✓ | 仿真 | 偏底盘导航；本仓标为「仅导航」 | 任务在 RoboCasa 注册表；社区 [HF 子集示例](https://huggingface.co/datasets/jellyho/robocasa365-NavigateKitchen) |
| **EBench** (2026) | 室内 mobile + fixed 统一评测 ✓/混合 | Isaac Sim | 26 任务、多轴诊断；评 π₀/π₀.₅/XVLA/InternVLA-A1 | [主页](https://internrobotics.github.io/EBench-home/) · [arXiv](https://arxiv.org/abs/2606.18239) · [GitHub](https://github.com/InternRobotics/EBench) |
| **MobileManiBench** (2026) | AgiBot 系 G1 夹爪 + XHand 灵巧手移动平台 ✓? | Isaac Sim | 世界系 **(6+D)** 动作；300K 轨迹、RL 自动生成 | [主页](https://dexhand.github.io/MobileManiBench/) · [arXiv](https://arxiv.org/abs/2602.05233) |
| **BEHAVIOR-1K / OmniGibson** | 家居活动；多种移动操作本体 ✓ | 仿真 | 偏高层活动/原语；低层动作因控制器配置而异 | [behavior.stanford.edu](https://behavior.stanford.edu) · [GitHub](https://github.com/StanfordVL/BEHAVIOR-1K) |
| **BEHAVIOR Robot Suite (BRS)** | **Galaxea R1/R1Pro** 轮式双臂+4DoF torso ✓ | 真机为主 | WB-VIMA：**全身关节层级条件**（upstream→downstream）；JoyLo 遥操 | [BRS](https://behavior-robot-suite.github.io/) · [数据 HF](https://huggingface.co/datasets/behavior-robot-suite/data) · [arXiv:2503.05652](https://arxiv.org/abs/2503.05652) |
| **Galaxea Open-World** | R1-Lite 统一本体 ✓ | 真机 500+h | 臂关节 + **chassis twist** + torso twist（LeRobot v2.1） | [HF Dataset](https://huggingface.co/datasets/OpenGalaxea/Galaxea-Open-World-Dataset) |
| **AgiBot World / GO-1** | 百台级双臂轮式人形 ✓ | 真机 ~1M traj | 双臂关节/EE、腰、头、**robot odom 相对位姿**等；不全是纯 cmd_vel | [GitHub](https://github.com/opendrivelab/agibot-world/) · [HF Beta](https://huggingface.co/datasets/agibot-world/AgiBotWorld-Beta) · [论文](https://arxiv.org/pdf/2503.06669) |
| **Mobile ALOHA / AgileX Cobot Magic** | 双臂 + **Tracer 差速** ✓ | 真机 | 臂关节（类 ALOHA）+ **底盘线/角速度**；常与静态 ALOHA **co-train** | [主页](https://mobile-aloha.github.io/) · [CoRL 2024](https://proceedings.mlr.press/v270/fu25b.html) |
| **LeKiwi** | SO-101 + 三全向轮 ✓ | 真机（低成本） | 臂关节 + 轮速/全向底盘；LeRobot 原生 | [GitHub](https://github.com/SIGRobotics-UIUC/LeKiwi) · [Seeed Wiki](https://wiki.seeedstudio.com/lerobot_lekiwi/) |
| **HomeRobot / OVMM** | **Hello Robot Stretch** ✓ | Habitat 仿真 + 真机公寓 | 导航原语 + 操作；Stretch 底盘+伸缩臂；MoManipVLA 评测平台 | [HomeRobot](https://arxiv.org/abs/2306.11565) · Habitat OVMM |
| **ManiSkill / ManiSkill-HAB** | Fetch 等移动操作 ✓ | 仿真（SAPIEN GPU） | 全身低层控制（Pick/Place/Open/Close 链式） | [ManiSkill](https://maniskill.readthedocs.io/) · [MS-HAB](https://arth-shukla.github.io/mshab/) |
| **Habitat / AI2-THOR 移动操作** | Stretch/Fetch 等 ✓ | 仿真 | 常 **分阶段**（nav skill + manip skill）；HAB 早期有 magical grasp | HAB / OVMM 文献 |
| **Tiago / SoftBank·PAL** | 轮式单/双臂 ✓ | 真机为主 | 工业标准：常 `cmd_vel`/`move_base` + 臂关节/笛卡尔；**大规模公开 IL 集少**，多为实验室私有 ? | PAL TIAGo 产品线；无统一 OXE 级公开集 |
| **Fetch / Stretch（通用平台）** | 经典轮臂 ✓ | 真机+仿真 | Fetch：差速+臂；Stretch：差速+升降伸缩 | 各仿真栈自带 |
| **Open-X / OXE** | 22+ 本体混合；**移动子集少** △/○ | 真机聚合 | RT-X 常压成 **EE 7D**；多数子集固定臂；含少量移动/四足 | [OXE](https://robotic-transformer-x.github.io/) · [数据集表](https://docs.google.com/spreadsheets/d/1rPBD77tk60AEIGZrGSODwyyzs5FgCU9Uz3h-3_t2A9g) |
| **Bridge / BridgeData V2** | WidowX 等桌面 △ | 真机 | EE/夹爪；**非轮臂** | Bridge 系列 |
| **DROID** | Franka + **可推桌子**（采集可换场景）△ | 真机 | 关节/EE ~15Hz；**策略上接近固定臂**，非 cmd_vel 轮臂 | [droid-dataset.github.io](https://droid-dataset.github.io/) |
| **CALVIN** | 固定 Franka 桌面 △ | 仿真 | delta EE + gripper；**非轮臂**（常作上肢预训练/评测） | CALVIN 官方；LeRobot 转制社区版 |
| **LaNMP** (2024) | 轮式 + 四足等 ○/✓ | 仿真为主 | 长程语言条件移动操作 | 检索名 LaNMP；细节以论文为准 ? |

**本仓 RoboCasa 规模（便于选型）**：TARGET50 严格「轮臂结合」约 **6/50**；pretrain300 启发式约 **50/300（~17%）**；NavigateKitchen 仅导航 1 个。

---

## 模型输出如何适配不同轮臂与底盘

业界没有统一「轮臂动作标准」；常见是 **把异构底盘压进同一向量布局或统一语义槽**，再由底层控制器解释。

| 输出范式 | 内容 | 典型适配对象 | 备注 |
|----------|------|--------------|------|
| **A. 混合扁平向量** | `[arm…, gripper, base…, (torso), (mode)]` | RoboCasa 12D、π₀ pad 后切片、多数 IL | 最常见；**索引顺序易踩坑**（LeRobot vs HDF5） |
| **B. SE(2) / cmd_vel** | `(vx, vy, ω)` 或差速 `(v, ω)` | Omron 全向、Tracer、Stretch/Fetch 导航层 | 全向有 `vy`；Ackermann 需曲率/转角，**不能硬塞全向策略** |
| **C. 底盘关节速度** | `base_x/y/yaw` 关节速度 | RoboCasa JOINT_VELOCITY_LEGACY | 与 ROS `cmd_vel` 差一层映射 |
| **D. Chassis twist 6D** | 线速度+角速度（常只有效 3） | Galaxea Open-World `action.chassis.velocities` | 冗余维常为 0 |
| **E. Hybrid base_mode + EE** | `mode>0` 臂跟期望底座；`mode<0` 臂锁已实现姿态 | RoboCasa `HybridMobileBase` | **轮臂特有**：防「边走边抖臂」 |
| **F. 纯 EE/关节（底盘外挂）** | VLA 只出臂；底盘由规划器/`move_base` | MoManipVLA、经典导航栈 | 上肢预训练最易接 |
| **G. 统一高维 pad + embodiment mask** | π₀/GR00T 式固定宽 action + 有效维 mask | 跨本体 foundation | 新轮臂：改 modality JSON + 微调头 |
| **H. 分层 / 全身条件** | 先 base/torso，再臂（WB-VIMA） | BRS R1 | 适合高 DoF 轮式人形 |

**跨底盘适配实务**：

1. **语义对齐优先于维数对齐**：`base_yaw_rate` ≠ Ackermann `steering`；差速无侧移，全向策略迁差速需投影。  
2. **频率与坐标系**：底盘常 10–50 Hz；EE delta 相对腕/基座/世界要统一（MobileManiBench 用世界系）。  
3. **mode / 阶段 token**：nav vs manip 显式切换，或学 `base_mode`。  
4. **Co-train 静态臂数据**：Mobile ALOHA 证明静态双臂数据可抬移动任务成功率（主要利臂）。

---

## 纯上肢模型 → 轮臂 的常见适配路径

| 路径 | 做法 | 数据成本 | 适用 |
|------|------|----------|------|
| **1. 动作扩维 + 小样本微调** | 预训练头保留 EE；新增 base 维随机/零初始化，用轮臂 demo LoRA/全量 FT | 中（几十–几百 demo/任务） | RoboCasa、LeKiwi、自有轮臂 |
| **2. Co-training（Mobile ALOHA 式）** | 静态上肢集 + 移动集混训；共享臂动作，底盘仅移动集监督 | 低–中 | 双臂结构相近时 |
| **3. 冻结 VLA + 底盘规划（MoManipVLA）** | VLA 出 EE waypoint；双层优化求可达底盘位姿 | 低（可 ~50 demo 真机） | Stretch/OVMM 类「先到位再操作」 |
| **4. 技能机 / 分层** | 高层：nav 到夹具；低层：固定臂 VLA | 低 | 长程家务；协同边走边抓弱 |
| **5. 仿真轮臂对齐再 sim2real** | RoboCasa/EBench/MS-HAB 上学 12D 或全身，再真机 FT | 中高 | 有同构/近构真机时 |
| **6. 换 modality 槽位的 foundation FT** | GR00T/π₀/`ROBOCASA_PANDA_OMRON` 式 embodiment tag | 中 | 已有官方轮臂 recipe |

**不推荐默认假设**：上肢 7D EE 策略零样本直接控轮臂（缺底盘、缺 mode、观测背景随动）。  
**较稳默认**：路径 **3 或 4** 做基线 → 有数据再上 **1/2/5**。

---

## 简要结论与选型建议

1. **定义**：轮臂 = 轮式底盘 + 臂，且底盘在控制环内；**GR1 tabletop / decoupled 人形 ≠ 轮臂**，只是上肢先验源。  
2. **仿真评测优先**：日常厨房与 hybrid 动作 → **RoboCasa365 + PandaOmron**；诊断移动 vs 灵巧 → **EBench**；大规模自动轨迹 → **MobileManiBench**；公寓重排低层控制 → **ManiSkill-HAB / OVMM(Stretch)**。  
3. **真机数据优先**：研究级全身轮式人形 → **Galaxea / BRS R1Pro**；超大规模 → **AgiBot World**；开源双臂差速 → **Mobile ALOHA/AgileX**；入门低成本 → **LeKiwi**。  
4. **OXE/Bridge/CALVIN/DROID**：作 **上肢/场景多样性** 预训练可以；**不要指望它们教 cmd_vel 轮臂协同**（DROID 尤其是「可推桌子上的固定臂」）。  
5. **动作落地**：优先设计清晰槽位（臂 EE/关节 + SE2/twist + 可选 `base_mode`），底层再映射 Omron/差速/Ackermann；跨栈务必核对索引（本仓 LeRobot vs RLinf 已踩过坑）。  
6. **上肢→轮臂**：无数据用 **VLA waypoint + 底盘规划**；有数据用 **扩维微调 / 静动态 co-train**；要强协同再上 **hybrid 整向量端到端**。

不确定项已标 `?`：TIAGo 公开大数据、LaNMP 细节、MobileManiBench「G1」与市面 AgiBot/Unitree 命名对应关系——引用前建议再对论文/资产库核对一版。

