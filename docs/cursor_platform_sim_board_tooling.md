# Platform sim/board/tooling
_Exported on 2026/7/29 at GMT+8 13:56:57 from Cursor (3.13.10)_

---

**User**

Answer in Simplified Chinese with a clear comparison table.

For each embodiment, report: **仿真** | **榜单/标准评测** | **工具链/数据/开源支持** | 备注（成熟度）

Platforms:
1. PandaOmron (RoboCasa)
2. Tiago (PAL)
3. Fetch
4. Stretch (Hello Robot)
5. Mobile ALOHA / AgileX Cobot Magic / Tracer
6. LeKiwi
7. Galaxea R1 / R1Pro
8. AgiBot wheeled dual-arm (Genie / AgiBot World G-series)

For each cell use: 有 / 弱 / 无 / 部分 — with 1 short phrase what exists.

Examples of what to look for:
- Sim: Isaac/MuJoCo/Habitat/Gazebo/robosuite
- Leaderboard: RoboCasa365, OVMM, EBench, BEHAVIOR, public SR tables
- Tooling: LeRobot, ROS2 nav, teleop (JoyLo), HF datasets, official SDK

Also answer: which 1–2 are best for "open sim + leaderboard + tooling" vs "real data scale".

Use WebSearch. Cite 1–2 links per platform when possible. Be accurate.

---

**Cursor**

我先按各 embodiment 查仿真、榜单与工具链证据，再汇总成对比表。

## Embodiment 对比（仿真 | 榜单 | 工具链 | 成熟度）

评级：**有 / 弱 / 无 / 部分** + 一句存在什么。

| Embodiment | 仿真 | 榜单/标准评测 | 工具链/数据/开源支持 | 备注（成熟度） |
|---|---|---|---|---|
| **1. PandaOmron (RoboCasa)** | **有** — robosuite/MuJoCo 厨房仿真 | **有** — RoboCasa365 公开 SR 榜 | **有** — LeRobot 原生、HF demo、GR00T/RLinf | 开源「仿真+榜单+IL」最完整 |
| **2. Tiago (PAL)** | **有** — 官方 Gazebo + MuJoCo Menagerie | **弱** — 早期 BEHAVIOR 真机实验，无常设 IL 榜 | **有** — ROS2 Nav2/MoveIt；LeRobot/HF 弱 | 经典工业/科研 ROS 栈，非 VLA 主战场 |
| **3. Fetch** | **有** — Gazebo；Habitat `hab_fetch`/HAB | **部分** — Habitat 重排历史基准；OVMM 已转向 Stretch | **部分** — ROS/Gazebo 老栈；现代 LeRobot 弱 | 遗留学术平台，硬件生态萎缩 |
| **4. Stretch (Hello Robot)** | **有** — Habitat OVMM + Stretch AI sim | **有** — HomeRobot OVMM 挑战/EvalAI | **有** — home-robot、stretch_ai、LeRobot fork、ROS2 | 开放词表移动操作标杆；数据规模中等 |
| **5. Mobile ALOHA / Cobot Magic / Tracer** | **部分** — Stanford/AgileX MuJoCo Mobile ALOHA | **无** — 无主流公开 SR 总榜 | **有** — Mobile ALOHA 开源、遥操作、RoboCOIN/HF LeRobot 数据 | 强真实遥操采集；仿真/评测弱于 RoboCasa |
| **6. LeKiwi** | **部分** — 官方 URDF；社区 MuJoCo（Ekumen 等） | **无** — 无标准挑战榜 | **有** — LeRobot 一等公民文档/CLI、社区 HF 数据 | 低成本教学/入门最佳；非大规模基准 |
| **7. Galaxea R1 / R1Pro** | **有** — Isaac/ManipSim；OmniGibson（JoyLo） | **部分** — BEHAVIOR Challenge 主用 R1/R1-Pro；ManipSim 内建 SR 表 | **有** — JoyLo、Open-World ~500h LeRobot、GalaxeaVLA | 仿真+真实双轨成熟；公开总榜弱于 RoboCasa365 |
| **8. AgiBot 轮式双臂 (Genie / G 系)** | **有** — Genie Sim 3.0（数字孪生评测） | **有** — AgiBot World Challenge / GenieSim 多维榜；EWMBench（世界模型） | **有** — AgiBot World ≥100万轨迹级 HF 数据、SDK/挑战工具 | **真实数据规模最大**；开源友好但偏厂商生态 |

---

### 主要依据链接（每平台 1–2 个）

1. [RoboCasa365 Leaderboard](https://robocasa.ai/leaderboard.html) · [LeRobot RoboCasa 文档](https://huggingface.co/docs/lerobot/main/en/robocasa)  
2. [PAL tiago_simulation (Gazebo)](https://github.com/pal-robotics/tiago_simulation/) · [MuJoCo Menagerie pal_tiago](https://github.com/google-deepmind/mujoco_menagerie/tree/main/pal_tiago)  
3. [fetch_gazebo](https://github.com/fetchrobotics/fetch_gazebo/) · [Habitat hab_fetch](https://huggingface.co/datasets/ai-habitat/hab_fetch)  
4. [HomeRobot OVMM Challenge](https://aihabitat.org/challenge/2023_homerobot_ovmm/) · [stretch_ai](https://github.com/hello-robot/stretch_ai/)  
5. [AgileX Cobot Magic](https://global.agilex.ai/products/cobot-magic) · [MuJoCo Mobile ALOHA 教程](https://www.hackster.io/agilexrobotics/simulate-mobile-aloha-in-mujoco-dc485f)  
6. [LeKiwi 硬件仓库](https://github.com/SIGRobotics-UIUC/LeKiwi) · [LeRobot LeKiwi 文档](https://huggingface.co/docs/lerobot/lekiwi)  
7. [BEHAVIOR Challenge / JoyLo→R1](https://behavior.stanford.edu/challenge/) · [Galaxea Open-World Dataset](https://huggingface.co/datasets/OpenGalaxea/Galaxea-Open-World-Dataset)  
8. [Genie Sim / Challenge](http://github.com/AgibotTech/genie_sim) · [AgiBotWorld-Beta（~100万轨迹）](https://huggingface.co/datasets/agibot-world/AgiBotWorld-Beta)

---

### 怎么选（1–2 个）

| 目标 | 首选 | 次选 |
|---|---|---|
| **开源仿真 + 榜单 + 工具链** | **PandaOmron / RoboCasa365**（LeRobot 原生、可提交公开 SR） | **Stretch + OVMM**（Habitat 挑战 + home-robot/stretch_ai 端到端） |
| **真实数据规模** | **AgiBot Genie / G 系**（百万级轨迹、Genie Sim 挑战闭环） | **Galaxea R1 系**（Open-World ~500h + BEHAVIOR/JoyLo 评测路径） |

**补充：** 若既要「有榜」又要「有真实移动双臂数据」，Galaxea（BEHAVIOR + Open-World）是折中；若只追开源可复现仿真排行，直接上 RoboCasa365。

