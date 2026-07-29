# 模型 & 数据全景清单

> 快照日期：2026-07-15。磁盘 `/dev/nvme0n1p2`：937G，已用 808G（91%），剩 82G——偏紧，扩容前谨慎新增大权重/数据集。

四个物理存放位置，合计约 **345GB**（不含 `Foundation/models`/`outputs` 之外的训练中间产物）。

## 1. `~/.cache/huggingface/hub` — 51GB（HF 标准缓存，基础/参考模型）

真正有内容的（其余几百个是社区仓库的空壳，只抓了 config 没权重，可忽略/清理）：

| 模型 | 大小 | 用途 |
|---|---|---|
| `nvidia/gr00t17-lerobot-libero_spatial-640` | 12G | GR00T N1.7 LIBERO-spatial 微调 |
| `lerobot/pi05_libero_finetuned` | 7.0G | π0.5 LIBERO 微调 |
| `nvidia/GR00T-N1.7-DROID` | 6.5G | GR00T N1.7 DROID 基座 |
| `nvidia/GR00T-N1.7-3B` | 6.5G | GR00T N1.7 底座 |
| `nvidia/Cosmos-Reason2-2B` | 4.6G | Cosmos 推理模型 |
| `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` | 1.9G | 视觉底座 |
| `nvidia/smolvla-arena-gr1-microwave` | 1.2G | Arena × SmolVLA 微调 |
| `lerobot/smolvla_*`（libero/robotwin/pusht/vlabench/robocasa/metaworld/robocerebra） | 每个 ~865-892M | SmolVLA 各任务微调 |
| `*/act_*`（pusht/libero，含社区仓库） | 每个 ~198M | ACT 策略 |

**清理建议**：几百个 `models--<用户名>--smolvla_*` / `act_*` 空壳（各 12-28K），像是之前批量探测公开仓库留下的元数据，无实际权重，删了不影响任何加载路径，只是省目录混乱，空间意义不大（合计几 MB）。

## 2. `~/.cache/huggingface/lerobot` — 109GB（LeRobot 专用缓存，**数据集为主**）

| 内容 | 大小 |
|---|---|
| `lerobot/robotwin_unified`（数据集） | **75G** — 最大头 |
| `hub/datasets--HuggingFaceVLA--libero` | 33G |
| `lerobot/robocerebra_unified` | 1.5G |
| aloha_sim 系列 + pusht | ~230M |

## 3. `~/.cache/huggingface/datasets` — 70GB

| 内容 | 大小 |
|---|---|
| `parquet/`（HF `datasets` 库的 arrow/parquet 缓存） | 70G |

## 4. `Foundation/data/` — 106GB（手动下载的大模型，不走 HF 标准缓存，注意别和 hub 混放）

| 目录 | 大小 | 说明 |
|---|---|---|
| `FluxVLAData/FluxVLAEngine/` | 48G | `gr00t_qwen3vl_0.6b_libero` / `gr00t_eagle_3b_libero_10_full_finetune_bs64` / `dreamzero_libero_10_*` 等 LIBERO 微调 checkpoint |
| `Qwen/`（2.5-7B / VL-3B-Instruct / 2.5-3B） | 27G | VLM 底座 |
| `openvla/openvla-7b-finetuned-libero-10` | 15G | OpenVLA LIBERO 微调 |
| `timm/`（`ViT-SO400M-14-SigLIP` / `vit_large_patch14_reg4_dinov2.lvd142m`） | 8.9G | 视觉编码器 |
| `nvidia/GR00T-N1.5-3B` | 5.1G | 旧版 GR00T 底座 |
| `google/siglip2-base-patch16-224` | 1.5G | 视觉编码器 |

## 5. `Foundation/models/` — 11GB（手改/迁移后可直接加载的策略，见 [`README.md`](../models/README.md)）

| 目录 | 大小 |
|---|---|
| `GR00T-N1.7-LIBERO/`（含 `libero_10`，2026-07-15 补全下载） | 6.5G |
| `SO101_Cube_pick_place_smolvla_migrated` | 1.7G |
| `smolvla_svla_so101_pickplace_migrated` | 1.7G |
| `smolvla_pusht_n3puiol_migrated` | 931M |
| `act_pusht_ssaito_migrated` | 198M |

`main/Isaac-GR00T/checkpoints/GR00T-N1.7-LIBERO` 是指向 `models/GR00T-N1.7-LIBERO` 的 symlink，不是独立拷贝。

## 6. `Foundation/outputs/` — 16GB（本地训练产出）

- `train/smolvla_libero_ft_bs_2/checkpoints` — 13G
- `train/act_libero_local_bs64/checkpoints` — 2.9G
- 各 `eval/*/videos` — 每个几十 MB（评估录像，非模型权重）

## 相关笔记

- 本机关键路径约定（模型放哪、缓存放哪）：[README.md](./README.md) 末尾「本机关键路径」表
- 下载脚本约定（重试/断点续传）：`tools/hf_download_one.sh`、`tools/gr00t17_libero_*_download.sh`
