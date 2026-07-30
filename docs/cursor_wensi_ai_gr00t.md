# 分析 wensi-ai GR00T 改动
_Exported on 2026/7/29 at GMT+8 16:44:10 from Cursor (3.13.10)_

---

**User**

用户上传了两个文件，请先读取它们获取上下文：
1. /home/sany/.cursor/projects/home-sany-Documents-Foundation/uploads/Isaac-GR00T-0.md — 来自 https://github.com/wensi-ai/Isaac-GR00T 的 README
2. /home/sany/.cursor/projects/home-sany-Documents-Foundation/uploads/baselines-1.html — 来自 https://behavior.stanford.edu/challenge/baselines.html

然后：
1. 读取这两个上传文件
2. WebFetch https://github.com/wensi-ai/Isaac-GR00T 获取更多信息（README、commits、diff）
3. WebFetch 或 WebSearch 官方 NVIDIA Isaac-GR00T repo（https://github.com/NVIDIA/Isaac-GR00T）的 BEHAVIOR 相关部分
4. 对比分析 wensi-ai fork 相对于官方 NVIDIA/Isaac-GR00T 做了哪些修改，特别是：
   - 与 BEHAVIOR challenge baseline 的关系
   - 新增/修改的文件、配置、训练脚本
   - 对 R1Pro / OmniGibson 的适配
   - 数据处理 pipeline 变化
   - 模型架构或推理流程变化
5. 结合 baselines.html 的内容，说明这个 fork 在 BEHAVIOR challenge 中的角色

返回中文简体，结构清晰，带具体文件/commit 引用。

---

**Cursor**

GitHub 渲染的源码为空，让我尝试获取 raw 内容。

## wensi-ai/Isaac-GR00T fork 对比分析报告

---

### 1. 总体定位

`wensi-ai/Isaac-GR00T` 是 **2026 BEHAVIOR Challenge 官方 baseline** 之一（另一个是 π0.5 的 OpenPI fork）。它从 `NVIDIA/Isaac-GR00T` fork 而来，工作在 **`behavior` 分支**上，核心目标是将 GR00T N1.7 VLA 模型适配到 BEHAVIOR-1K 仿真环境中的 **R1Pro 双臂人形机器人**，完成 OmniGibson 仿真中的操作任务。

根据 `baselines.html`，该 fork 的作用是：
> 帮助参赛者验证完整的 challenge 工作流 — 加载演示数据集、微调策略、在 OmniGibson 中评估、准备提交结果。

---

### 2. 关键 commits 时间线（`behavior` 分支）

| 日期 | Commit 内容 | 说明 |
|------|------------|------|
| 2026-04-18 | GR00T N1.7 Release | 从上游同步 N1.7 基线 |
| 2026-05-07 ~ 06-12 | SyncBot 系列 | 持续从 NVIDIA/Isaac-GR00T 同步上游修复 |
| **2026-06-25** | add b1k r1 pro modality config | 新增 R1Pro 机器人配置 |
| **2026-06-25** | add websockets dependency | 为 WebSocket 推理服务添加依赖 |
| **2026-06-25** | preserve robot name/observation for eval | 评估时保留 OmniGibson 机器人命名 |
| **2026-06-25** | fix train_b1k: tag resolve, N1.7 base, resume | 修复训练脚本 |
| **2026-06-25** | add LeRobot v3.0 dataset reader | 支持新版数据格式 |
| **2026-06-26** | cache v3.0 parquet tables and video decoders | 数据加载优化 |
| **2026-06-26** | add decode_only_used_frames | 跳过未使用帧，加速数据加载 |
| **2026-06-26** | add baseline instruction draft | 文档 |
| **2026-07-02** | Merge PR #1 | 合并所有 BEHAVIOR 适配 |

---

### 3. 新增/修改的文件清单

#### 3.1 全新文件（官方 repo 不存在）

| 文件路径 | 功能 |
|---------|------|
| `examples/b1k/r1pro.py` | R1Pro 机器人的 modality 配置（state/action 映射） |
| `examples/b1k/r1pro.json` | 同上的 JSON 格式模板，用于部署到数据集 |
| `scripts/b1k/train_b1k.py` | BEHAVIOR challenge 专用训练脚本 |
| `scripts/b1k/serve_b1k.py` | WebSocket 策略服务器启动脚本 |
| `scripts/b1k/deploy_modality.py` | 将 `modality.json` 批量部署到所有任务数据集 |
| `gr00t/eval/eval_b1k_wrapper.py` | B1K 策略包装器（obs 处理 + 动作集成） |
| `gr00t/policy/websocket_b1k_server.py` | 基于 WebSocket + msgpack 的推理服务 |
| `AGENTS.md`, `CLAUDE.md` | AI 辅助开发配置文件 |

#### 3.2 修改的上游文件

- `pyproject.toml` — 添加 `websockets` 依赖，移除重复的 `[tool.uv.sources]` 表
- 数据加载层 — 新增 LeRobot v3.0 reader、parquet 缓存、`decode_only_used_frames` 选项

---

### 4. R1Pro 机器人适配细节

`examples/b1k/r1pro.py` 定义了完整的 R1Pro embodiment：

**State（61 维 proprioception）：**
- `base_qvel` [0:3] — 底盘速度
- `left_arm` [3:10] — 左臂关节 (7)
- `left_gripper` [24:26] — 左夹爪 (2)
- `right_arm` [28:35] — 右臂关节 (7)
- `right_gripper` [49:51] — 右夹爪 (2)
- `torso` [53:57] — 躯干关节 (4)

**Action（23 维绝对关节目标）：**
- `base` [0:3] — 底盘速度命令（绝对）
- `torso` [3:7] — 躯干（相对于 state.torso）
- `left_arm` [7:14] — 左臂（相对于 state.left_arm）
- `left_gripper` [14:15] — 左夹爪（绝对）
- `right_arm` [15:22] — 右臂（相对于 state.right_arm）
- `right_gripper` [22:23] — 右夹爪（绝对）

**Camera：** 3 路 RGB — head（ZED）、left_wrist、right_wrist，均 resize + pad 到 224×224。

该配置注册为 `EmbodimentTag.NEW_EMBODIMENT`，与官方 GR00T 的 fine-tune 自定义 embodiment 流程一致。

---

### 5. 数据处理 Pipeline 变化

| 方面 | 官方 NVIDIA/Isaac-GR00T | wensi-ai fork |
|------|------------------------|---------------|
| 数据格式 | LeRobot v2 | **同时支持 LeRobot v3.0 和 v2.1**（新增 v3.0 reader） |
| Modality 配置 | 手动准备 `modality.json` | `deploy_modality.py` 自动批量部署 + 维度校验 |
| 视频解码 | 全帧解码 | 新增 `--decode-only-used-frames` 跳过未使用帧 |
| 缓存 | 标准 | 新增 parquet 表和 video decoder 的 per-file 缓存 |
| 归一化统计 | 需预计算 | 首次训练时自动生成 `meta/stats.json` |

`deploy_modality.py` 的工作流：遍历 `$DATA_ROOT` 下所有包含 `meta/info.json` 的数据集 → 校验 state=61 维、action=23 维 → 复制 `r1pro.json` 为 `modality.json`。

---

### 6. 模型架构与推理流程变化

**模型架构本身没有改变** — 仍使用 GR00T N1.7（Cosmos-Reason2-2B backbone + diffusion transformer head），微调时冻结 vision encoder 和 LLM，只训练 projector + diffusion action head。

**推理流程的重大变化：**

| 方面 | 官方 | fork |
|------|------|------|
| 通信协议 | ZMQ (server-client) | **WebSocket + msgpack**（与 OmniGibson evaluator 对接） |
| 策略服务器 | `run_gr00t_server.py` | `websocket_b1k_server.py`（新实现） |
| 动作集成 | 无 | **3 种控制模式**（见下） |
| Obs 处理 | 直接传入 | `B1KPolicyWrapper` 自动从 OmniGibson obs 提取 proprio + camera |

**B1KPolicyWrapper 的 3 种控制模式：**
1. **`temporal_ensemble`**（默认）— 每步推理，指数加权平均最近 5 个 action sequence
2. **`receeding_horizon`** — 执行完当前 plan 再重新规划
3. **`receeding_temporal`** — 每 K 步推理一次 + temporal ensemble 平滑

所有模式都对夹爪索引做了特殊处理：夹爪动作直接取最新 rollout 的值而不做平滑。

---

### 7. 训练配置对比

| 参数 | 官方示例 | fork (BEHAVIOR) |
|------|---------|-----------------|
| 基础模型 | `nvidia/GR00T-N1.7-3B` | 相同 |
| Action horizon | 8/16 | **16** |
| Global batch size | 32 | **2048** |
| Max steps | 2000 | **150,000** |
| 推荐 GPU | 1-8 | **8×H100** |
| WandB project | — | `B1K` |
| `use_relative_action` | 取决于 tag | **True**（手臂和躯干相对动作） |
| `tune_llm` / `tune_visual` | 可调 | **False**（冻结） |
| `tune_projector` / `tune_diffusion_model` | 可调 | **True** |

---

### 8. 在 BEHAVIOR Challenge 中的角色

根据 `baselines.html`：

1. **官方 baseline 之一**：与 π0.5 并列作为 2026 BEHAVIOR Challenge 的两个参考实现
2. **提供预训练 checkpoint**：`turning_on_radio` 任务已有可直接评估的 fine-tuned checkpoint（Google Drive 链接）
3. **完整工作流参考**：涵盖数据准备 → 微调 → 推理服务 → OmniGibson 评估的全流程
4. **评估对接**：通过 WebSocket server 与 BEHAVIOR-1K 的 `omnigibson.eval.eval` 评估器通信，评估器在 conda `behavior` 环境中运行

**评估命令**（在 policy server 运行的同时）：
```bash
conda activate behavior
python -m omnigibson.eval.eval \
    --task-name $TASK_NAME \
    --host 127.0.0.1 --port 8000 \
    --output-dir $LOG_PATH --write-video
```

---

### 9. 总结

`wensi-ai/Isaac-GR00T` 是一个**面向 BEHAVIOR 2026 Challenge 的 thin adaptation layer**，主要贡献：
- **未改动 GR00T 核心模型**，仅新增 ~7 个文件做桥接
- **新建 R1Pro embodiment 配置**，将 OmniGibson 的 61 维 proprio + 23 维 action 映射到 GR00T 格式
- **替换通信层为 WebSocket**，适配 BEHAVIOR-1K 评估框架
- **实现 temporal ensemble 等推理策略**，提升闭环控制稳定性
- **扩展数据 pipeline** 支持 LeRobot v3.0 + 按需帧解码优化

