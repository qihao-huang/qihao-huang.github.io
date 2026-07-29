# LeRobot 全栈入门：ACT + SmolVLA（本地实验版）

> 面向：在本机（RTX 5080 16GB）用 LeRobot **摸清 ACT / SmolVLA 全流程**  
> 主线：**环境 → 数据 → 开环训练 → wandb → 仿真评测 →（可选）真机**  
> 原则：这个阶段 **不推 Hub**，全部本地；先 smoke，再加长。

相关笔记（互补，非重复）：[索引](./README.md) · [FAQ](./lerobot_faq_cheatsheet.md) · [模型/Benchmark 对照](./lerobot_model_benchmark_matrix.md) · [SO-101 / Mac / Jobs](./lerobot_so101_mac_hfjobs.md)

你当前机器上已有的进度（可对照）：


| 项                 | 状态 / 路径                                                                                   |
| ----------------- | ----------------------------------------------------------------------------------------- |
| LeRobot           | `~/Documents/Foundation/main/lerobot`，conda env `lerobot`，版本 ~0.6.1                       |
| ACT smoke         | 已完成：`~/Documents/Foundation/outputs/smoke_act_libero_10ep/checkpoints/001000/`            |
| LIBERO 数据         | 后台下载中，缓存 `~/.cache/huggingface/lerobot/hub/datasets--HuggingFaceVLA--libero`（全量约 65–70GB） |
| `smolvla_base`    | 已有本地权重：`~/.cache/huggingface/hub/models--lerobot--smolvla_base`                           |
| 现成 LIBERO SmolVLA | Hub 上有 `lerobot/smolvla_libero`（从 base finetune，**不是** base 本身）                           |


---



## 0. 先建立心智模型

```text
观测 (图像 + 状态 [+ 语言])
        │
        ▼
   Policy (ACT / SmolVLA)
        │
        ▼
   动作 chunk (未来 k 步)
        │
   ┌────┴────┐
   ▼         ▼
开环监督    闭环执行
(train loss) (仿真/真机 success)
```


| 概念        | 在 LeRobot 里是什么                       | 看什么指标              |
| --------- | ------------------------------------ | ------------------ |
| **开环**    | 数据集 hold-out 上算 `eval_loss`          | L1 / loss，不是成功率    |
| **闭环**    | `lerobot-eval` 或真机 `lerobot-rollout` | success rate       |
| **steps** | 优化步数（主控制旋钮）                          | 命令用 `--steps`      |
| **epch**  | 数据过了几遍                               | 日志里的 `epch`        |
| **ep**    | 累计采到的 episode 计数                     | 不是「数据集有多少 episode」 |




### ACT vs SmolVLA（选型）


|       | ACT                                 | SmolVLA                   |
| ----- | ----------------------------------- | ------------------------- |
| 定位    | 轻量模仿学习，从零训                          | 小 VLA，从底座 finetune        |
| 参数量   | ~52M（你这次实测）                         | ~450M + VLM               |
| 语言    | 通常不需要                               | 需要 task 文本                |
| 预训练   | **无** `act_base`；只有 ResNet ImageNet | 必须 `lerobot/smolvla_base` |
| 损失    | L1 + KL（CVAE）                       | Flow matching 速度场回归       |
| 显存（训） | ~2GB，很轻松                            | 16GB 建议 batch 2–4，或 LoRA  |
| 适合    | 先跑通全栈、单任务                           | 多任务 / 语言条件 / 迁移           |


**推荐顺序：先 ACT 全流程 → 再 SmolVLA finetune → 再仿真对比。**

---



## 1. 环境

```bash
conda activate lerobot
cd ~/Documents/Foundation/main/lerobot

# 若尚未装齐
pip install -e ".[training,smolvla,libero]"

hf auth login          # 拉公开数据/模型
wandb login            # 看曲线
export MUJOCO_GL=egl   # 无头仿真
```

常用 CLI：


| 命令                    | 用途              |
| --------------------- | --------------- |
| `lerobot-train`       | 离线训练 / finetune |
| `lerobot-eval`        | 仿真闭环评测          |
| `lerobot-rollout`     | 真机部署 / DAgger   |
| `lerobot-dataset-viz` | 看数据集            |


本地实验固定加：

```bash
--policy.push_to_hub=false
--wandb.enable=true
```

不必写 `--policy.repo_id=...`（那是推 Hub 用的）。

---



## 2. 数据：HuggingFaceVLA/libero



### 它是什么？

- 合并了 **Spatial + Object + Goal + Libero-10**（约 40 tasks / 1693 episodes）
- **不是**四个独立下载包
- 全量约 **65–70GB**（双相机视频为主）



### 和 `--env.task=...` 的区别


| 参数                                        | 作用                        |
| ----------------------------------------- | ------------------------- |
| `--dataset.repo_id=HuggingFaceVLA/libero` | **训练数据**                  |
| `--env.task=libero_spatial,...`           | **仿真评测**选 suite，不负责下 demo |




### 下载（系统后台，断线可续）

你已有后台脚本/进程时，看进度：

```bash
tail -f ~/Documents/Foundation/logs/libero_download.log
du -sh ~/.cache/huggingface/lerobot/hub/datasets--HuggingFaceVLA--libero
```

手动续传示例：

```bash
mkdir -p ~/Documents/Foundation/logs
setsid nohup hf download HuggingFaceVLA/libero \
  --repo-type dataset \
  --cache-dir ~/.cache/huggingface/lerobot/hub \
  > ~/Documents/Foundation/logs/libero_download.log 2>&1 &
echo $! > ~/Documents/Foundation/logs/libero_download.pid
```



### Smoke 不必等全量

```bash
--dataset.episodes="[0,1,2,3,4,5,6,7,8,9]"
```

注意：`eval_split` 会按 task 划走部分 episode，日志里 `num_episodes` 可能 **小于 10**（你 ACT smoke 曾出现 train=4）。这是正常的。

---



## 3. ACT 全流程



### 3.1 模型在干什么？

- 输入：多相机图像 + 本体状态
- 输出：未来 `chunk_size` 步动作（默认常 100）
- 训练：`loss ≈ L1(动作) + kl_weight * KL(z)`  
  - **L1**：开环模仿  
  - **KL**：CVAE 隐变量正则（默认 `use_vae=True`, `kl_weight=10`）
- **没有** HF 上的通用 `act_base`；只有 ResNet18 ImageNet 骨干会自动下



### 3.2 Smoke（你已跑通）

```bash
cd ~/Documents/Foundation   # 注意：output_dir 相对 cwd

lerobot-train \
  --policy.type=act \
  --dataset.repo_id=HuggingFaceVLA/libero \
  --dataset.episodes="[0,1,2,3,4,5,6,7,8,9]" \
  --dataset.eval_split=0.1 \
  --eval_steps=200 \
  --steps=1000 \
  --batch_size=8 \
  --save_freq=1000 \
  --env_eval_freq=0 \
  --log_freq=20 \
  --output_dir=outputs/smoke_act_libero_10ep \
  --job_name=smoke_act_libero_10ep \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --wandb.enable=true
```

产物绝对路径：

```text
/home/sany/Documents/Foundation/outputs/smoke_act_libero_10ep/checkpoints/001000/pretrained_model/
  ├── config.json
  ├── model.safetensors          # ~197MB
  ├── policy_preprocessor*.json
  └── train_config.json
```



### 3.3 读日志字段

```text
step:800 smpl:6K ep:22 epch:5.43 loss:2.266 ... eval_loss=0.6343
```


| 字段          | 含义              |
| ----------- | --------------- |
| `step`      | 优化步             |
| `epch`      | 数据过了几遍（≈ epoch） |
| `ep`        | 累计 episode 采样计数 |
| `loss`      | 训练总损失（L1+KL）    |
| `eval_loss` | hold-out 开环损失   |


换算：`epochs ≈ steps / ceil(num_frames / batch_size)`。  
你 smoke：`1179 frames / 8 ≈ 147 steps/epoch`，`1000 steps ≈ 6–7 epoch`。

### 3.4 wandb

- 项目默认：`lerobot`
- 默认 `log_freq=200`，前几分钟可能只有 System 硬件面板
- 看 **Charts**：`train/loss`、`train/l1_loss`、`train/kld_loss`、`eval/eval_loss`
- 下次加 `--log_freq=20` 更早出曲线



### 3.5 正式一点的 ACT（等数据更全后）

```bash
lerobot-train \
  --policy.type=act \
  --dataset.repo_id=HuggingFaceVLA/libero \
  --dataset.eval_split=0.05 \
  --eval_steps=2000 \
  --steps=50000 \
  --batch_size=16 \
  --save_freq=5000 \
  --env_eval_freq=0 \
  --log_freq=100 \
  --output_dir=outputs/train/act_libero \
  --job_name=act_libero \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --wandb.enable=true
```

---



## 4. SmolVLA 全流程



### 4.1 模型在干什么？

- VLM（SmolVLM）编码图像 + 语言 + 状态
- **Action Expert** 用 **flow matching** 从噪声去噪出动作 chunk
- `smolvla_base`：在大量 **SO100 社区真机数据**上预训练，**没有**在 LIBERO 上训过
- 开源已有 LIBERO 成品：`lerobot/smolvla_libero`（评测可直接用）



### 4.2 先准备底座（若未下完）

```bash
hf download lerobot/smolvla_base
# 若 SSL 不稳：
# export HF_ENDPOINT=https://hf-mirror.com
```

SmolVLA 首次建模型时还可能再拉 VLM 权重（如 `HuggingFaceTB/SmolVLM2-500M-Video-Instruct`），属正常。

### 4.3 Smoke finetune（本地）

```bash
cd ~/Documents/Foundation

lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=HuggingFaceVLA/libero \
  --dataset.episodes="[0,1,2,3,4,5,6,7,8,9]" \
  --dataset.eval_split=0.1 \
  --eval_steps=200 \
  --steps=1000 \
  --batch_size=2 \
  --save_freq=1000 \
  --env_eval_freq=0 \
  --log_freq=20 \
  --policy.freeze_vision_encoder=false \
  --policy.train_expert_only=false \
  --policy.scheduler_decay_steps=1000 \
  --output_dir=outputs/smoke_smolvla_libero_10ep \
  --job_name=smoke_smolvla_libero_10ep \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --wandb.enable=true
```

要点：

- 用 `--policy.path=lerobot/smolvla_base`，不要只写 `--policy.type=smolvla`（后者近似从零，弱）
- 16GB：`batch_size=2` 更稳；OOM 再降或改 LoRA
- 短跑务必把 `scheduler_decay_steps` 调到接近 `steps`



### 4.4 正式 finetune（参考）

```bash
lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=HuggingFaceVLA/libero \
  --dataset.eval_split=0.05 \
  --eval_steps=2000 \
  --steps=20000 \
  --batch_size=4 \
  --save_freq=5000 \
  --env_eval_freq=0 \
  --log_freq=100 \
  --policy.freeze_vision_encoder=false \
  --policy.train_expert_only=false \
  --policy.scheduler_decay_steps=20000 \
  --output_dir=outputs/train/smolvla_libero \
  --job_name=smolvla_libero \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --wandb.enable=true
```

显存紧时用 LoRA：

```bash
pip install -e ".[peft]"   # 在 main/lerobot 下

lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=HuggingFaceVLA/libero \
  --steps=20000 --batch_size=8 \
  --peft.method_type=LORA --peft.r=64 --peft.lora_alpha=64 \
  --policy.optimizer_lr=1e-3 \
  --policy.push_to_hub=false --wandb.enable=true \
  --output_dir=outputs/train/smolvla_libero_lora \
  --policy.device=cuda
```



### 4.5 只想先看 LIBERO 上限（跳过自训）

```bash
export MUJOCO_GL=egl
lerobot-eval \
  --policy.path=lerobot/smolvla_libero \
  --env.type=libero \
  --env.task=libero_spatial \
  --eval.batch_size=1 \
  --eval.n_episodes=2 \
  --policy.device=cuda \
  --output_dir=outputs/eval/smolvla_libero_official_smoke
```

---



## 5. 仿真闭环评测（真正的「好不好」）

开环 `eval_loss` 下降 ≠ 会做任务。闭环用：

```bash
export MUJOCO_GL=egl

# 冒烟 2 episode
lerobot-eval \
  --policy.path=/home/sany/Documents/Foundation/outputs/smoke_act_libero_10ep/checkpoints/001000/pretrained_model \
  --env.type=libero \
  --env.task=libero_spatial \
  --eval.batch_size=1 \
  --eval.n_episodes=2 \
  --policy.device=cuda \
  --output_dir=/home/sany/Documents/Foundation/outputs/eval/act_libero_smoke

# 正式一点：单 suite 每任务 10 episode
lerobot-eval \
  --policy.path=.../pretrained_model \
  --env.type=libero \
  --env.task=libero_spatial \
  --eval.batch_size=1 \
  --eval.n_episodes=10 \
  --policy.device=cuda
```

多 suite（慢，接近论文协议）：

```bash
--env.task=libero_spatial,libero_object,libero_goal,libero_10 \
--env.max_parallel_tasks=1
```

依赖：`pip install -e ".[libero]"`（你环境里已有 `hf_libero`）。

训练中周期性仿真会很慢，日常建议：

```bash
--env_eval_freq=0
```

训完再单独 `lerobot-eval`。

---



## 6. 建议学习路径（按天）



### Day 1 — 跑通 ACT（你已基本完成）

1. 环境 + wandb
2. 10 episode ACT smoke
3. 看懂 `loss` / `l1` / `kld` / `epch`
4. 找到本地 `pretrained_model`



### Day 2 — 开环 vs 闭环

1. 对 ACT checkpoint 跑 `lerobot-eval` smoke（2 episode）
2. 对比：开环 `eval_loss` 低，但闭环可能仍差（数据太少时正常）
3. 用官方 `lerobot/smolvla_libero` 跑一次 eval，建立「好模型」基线



### Day 3 — SmolVLA

1. 确认 `smolvla_base` 完整
2. 10 episode SmolVLA smoke finetune
3. 同 suite 对比 ACT vs 你的 SmolVLA vs 官方 `smolvla_libero`



### Day 4 — 加长与消融

1. 等 LIBERO 全量下完
2. ACT 50k / SmolVLA 20k
3. 解冻视觉 vs freeze；LoRA vs full
4. 记录 success rate 表



### Day 5+ — 真机（可选）

同一套 checkpoint，换：

```bash
lerobot-rollout \
  --strategy.type=base \
  --policy.path=.../pretrained_model \
  --robot.type=so101_follower \
  ...
```

---



## 7. 代码地图（想读源码时）


| 主题      | 路径                                                                      |
| ------- | ----------------------------------------------------------------------- |
| 训练入口    | `src/lerobot/scripts/lerobot_train.py`                                  |
| 评测入口    | `src/lerobot/scripts/lerobot_eval.py`（CLI: `lerobot-eval`）              |
| ACT     | `src/lerobot/policies/act/`                                             |
| SmolVLA | `src/lerobot/policies/smolvla/`（核心类 `VLAFlowMatching`）                  |
| 策略工厂    | `src/lerobot/policies/factory.py`                                       |
| 训练配置    | `src/lerobot/configs/train.py`（`log_freq`/`eval_steps`/`env_eval_freq`） |
| 官方文档    | `docs/source/act.mdx`、`smolvla.mdx`、`libero.mdx`                        |
| 示例脚本    | `examples/tutorial/act/`、`examples/tutorial/smolvla/`                   |


---



## 8. 常见坑（你已经踩过的）

1. **缺** `repo_id`：默认想 push Hub → 加 `--policy.push_to_hub=false`
2. **HF SSL /** `hf` **路径错乱**：用 conda 里的 `hf`，必要时镜像；下载用 `nohup/setsid`
3. **进度条总量一直涨**：`incomplete total`，最终 ~70GB，不是死循环
4. **wandb 只有硬件**：等第一个 `log_freq` 点，或 `--log_freq=20`
5. `episodes=10` **但 train 只有 4**：`eval_split` + 未下完视频分片
6. **ACT 不用下 base；SmolVLA 必须下** `smolvla_base`
7. `output_dir` **相对启动时的 cwd**（你在 `~/Documents/Foundation` 启动 → 输出在该目录下）
8. **GPU-Util 0% 但占着显存**：常卡在 `data_s` 解码，不是模型太大

---



## 9. 一张对照表：你现在该敲哪条命令


| 目标                   | 命令要点                                                                                           |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| ACT 已训好的本地评测         | `--policy.path=.../smoke_act_libero_10ep/checkpoints/001000/pretrained_model` + `lerobot-eval` |
| SmolVLA smoke 训      | `--policy.path=lerobot/smolvla_base` + 10 episodes + `batch_size=2`                            |
| 官方 SmolVLA LIBERO 基线 | `--policy.path=lerobot/smolvla_libero` + `lerobot-eval`                                        |
| 看下载                  | `du -sh .../datasets--HuggingFaceVLA--libero` + `tail` 日志                                      |
| 本地不推送                | 永远带 `--policy.push_to_hub=false`                                                               |


---



## 10. 最小成功标准（摸清全栈 = 这些都做过一遍）

- [ ] ACT：train → 本地 checkpoint → wandb 看到 `train/l1_loss` & `kld_loss`  
- [ ] ACT：`lerobot-eval` 至少跑通 1–2 episode（不要求高成功率）  
- [ ] SmolVLA：从 `smolvla_base` finetune 出本地 checkpoint  
- [ ] 官方 `smolvla_libero`：`lerobot-eval` smoke  
- [ ] 能口头说清：开环 loss vs 闭环 success、steps vs epch、ACT L1+KL vs SmolVLA flow matching、base 不含 LIBERO  

做完以上，你就不是「会抄命令」，而是真的摸清了 LeRobot 里 ACT/SmolVLA 的全栈闭环。

---



## 参考链接

- ACT 文档：`main/lerobot/docs/source/act.mdx`  
- SmolVLA 文档：`main/lerobot/docs/source/smolvla.mdx`  
- LIBERO：`main/lerobot/docs/source/libero.mdx`  
- AGENT_GUIDE：`main/lerobot/AGENT_GUIDE.md`  
- 模型：`[lerobot/smolvla_base](https://huggingface.co/lerobot/smolvla_base)`、`[lerobot/smolvla_libero](https://huggingface.co/lerobot/smolvla_libero)`  
- 数据：`[HuggingFaceVLA/libero](https://huggingface.co/datasets/HuggingFaceVLA/libero)`  
- 论文：ACT [arXiv:2304.13705](https://arxiv.org/abs/2304.13705)，SmolVLA [arXiv:2506.01844](https://arxiv.org/abs/2506.01844)

