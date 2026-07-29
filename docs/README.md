# LeRobot 本地笔记索引

> 来源：对话 [8472a669](../) 中可复用的结构性结论 + 本机实验路径。  
> 不替代官方文档；命令级全流程见 fullstack。

| 文档 | 用途 |
|------|------|
| [blog_smolvla_minimal_vla_16gb.md](./blog_smolvla_minimal_vla_16gb.md) | 有限显存下跑通最小 VLA（SmolVLA）；**仅本地 docs，不上 github.io** |
| [lerobot_act_smolvla_fullstack.md](./lerobot_act_smolvla_fullstack.md) | ACT + SmolVLA **可照着跑**的全栈教程（环境→训→评） |
| [lerobot_wam_handson.md](./lerobot_wam_handson.md) | WAM 系列 / **FastWAM** hands-on：注册名、Hub、训评命令、16GB 显存墙 |
| [lingbot_vla2_va2_handson.md](./lingbot_vla2_va2_handson.md) | **LingBot-VLA 2.0** + **LingBot-VA** 上游仓：安装/权重/训评/16GB 路径 |
| [lerobot_lingbot_va_vla_jepa.md](./lerobot_lingbot_va_vla_jepa.md) | 世界模型向策略 **lingbot_va** / **vla_jepa**：依赖、显存、训评、相对 FastWAM |
| [lerobot_vla_sft_rl.md](./lerobot_vla_sft_rl.md) | **VLA 的 SFT vs RL**：`lerobot-train` / HIL-SERL；模型对照表；**FastWAM 不能做 RL** |
| [lerobot_faq_cheatsheet.md](./lerobot_faq_cheatsheet.md) | 概念速查、开环/闭环、日志字段、已知坑、版本差异 |
| [lerobot_model_benchmark_matrix.md](./lerobot_model_benchmark_matrix.md) | ACT/SmolVLA/π0/π0.5/GR00T 对照；仿真 env 矩阵；评测协议与高分误解 |
| [lerobot_so101_mac_hfjobs.md](./lerobot_so101_mac_hfjobs.md) | SO-ARM101 真机数据量/空间、Mac vs GPU、HF Jobs |
| [local_canvases_inventory.md](./local_canvases_inventory.md) | 本机 / 已发布 Canvas 完整清单 |
| [models_data_inventory.md](./models_data_inventory.md) | 模型 & 数据全景清单：HF 缓存 / `Foundation/data` / `models` / `outputs` 分布与大小 |
| [leisaac_quickstart.md](./leisaac_quickstart.md) | **LeIsaac** 起步：资产、键盘 teleop、SmolVLA 闭环 |
| [wheeled_decoupled_vla_sim_proto.md](../robotics/wheeled_decoupled_vla/wheeled_decoupled_vla_sim_proto.md) | **轮臂 Decoupled VLA**（已迁至 `robotics/wheeled_decoupled_vla/`） |
| [humanoid_coupled_vla_wbc_proto.md](../robotics/humanoid_coupled/humanoid_coupled_vla_wbc_proto.md) | **人形 Coupled VLA→SONIC(BFM)**（`robotics/humanoid_coupled/`；含 WAM 升级） |
| [robotics/README.md](../robotics/README.md) | 产品向 robotics 目录索引（轮臂 / 人形） |
| [isaaclab_arena_smolvla_quickstart.md](./isaaclab_arena_smolvla_quickstart.md) | **IsaacLab Arena × LeRobot**：本机只跑 **SmolVLA**（GR1 microwave 等） |
| [robocasa_lerobot_rlinf_handson.md](./robocasa_lerobot_rlinf_handson.md) | **RoboCasa**：LeRobot SmolVLA 安装/训评 + RLinf π₀ PPO 后训练；臂+底盘动作序与精读代码路径 |
| [robocasa_task_catalog.md](./robocasa_task_catalog.md) | **RoboCasa TARGET50** 中英对照 + Atomic/Composite、seen/unseen、运动类型（贴夹具/仅导航/轮臂）与 pretrain300 规模 |
| [具身智能比赛梳理_2025-2026.md](./具身智能比赛梳理_2025-2026.md) | 2025下半年~2026下半年具身智能国际比赛全景：ICRA/CVPR/NeurIPS/IROS |


### 相关 Canvas（不重复展开）

| 位置 | 说明 |
|------|------|
| Cursor：`~/.cursor/projects/home-sany-Documents-Foundation/canvases/` | 交互版架构 / 评测 / train-eval |
| 已发布：`~/Documents/Foundation/qihao-huang.github.io/canvases/` | 静态 HTML + `catalog.json` |
| 清单笔记 | [local_canvases_inventory.md](./local_canvases_inventory.md) |

落盘对话结论时可用个人 skill：`~/.cursor/skills/save-answer-to-docs/`（触发：「保存回答到 docs」）。

### 本机关键路径

| 项 | 路径 |
|----|------|
| LeRobot | `~/Documents/Foundation/main/lerobot`（conda `lerobot` ~0.6.1） |
| 训练输出 | `~/Documents/Foundation/outputs/` |
| 本地可用模型（migrate / 手改） | `~/Documents/Foundation/models/`（**不要**塞进 `~/.cache/huggingface/hub/`） |
| HF 数据缓存 | `~/.cache/huggingface/lerobot/hub/` |
| HF 模型缓存 | `~/.cache/huggingface/hub/`（仅 Hub 自动下载） |
| 工具脚本 | `~/Documents/Foundation/tools/` |
| 下载 / 安装日志 | `~/Documents/Foundation/logs/`（只放 log；勿放权重） |
