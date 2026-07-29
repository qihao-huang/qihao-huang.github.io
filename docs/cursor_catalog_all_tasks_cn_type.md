# Catalog all tasks CN+type
_Exported on 2026/7/29 at GMT+8 13:57:39 from Cursor (3.13.10)_

---

**User**

User wants: 统一整理所有任务的类型 + 中文翻译，聚合分类。

Workspace: /home/sany/Documents/Foundation

Deliverable: a clear Chinese reference (tables) covering:

1. **TARGET 50** (eval): atomic_seen (18) + composite_seen (16) + composite_unseen (16)
   For each task: English name | 中文翻译 | 家族(Atomic/Composite) | 集合(seen/unseen) | 运动类型(贴夹具操作 / 仅导航 / 轮臂结合跨区)

2. **聚合分类** summary counts by:
   - Atomic vs Composite
   - Seen vs Unseen  
   - 运动类型三分类
   - Optional: theme (开关门、取放、电器、导航、烹饪、清洗、整理…)

3. If feasible briefly list **pretrain300** scale: how many atomic vs composite in Human300 / PRETRAINING_TASKS, and how many 轮臂结合 (use heuristics from dining/navigate patterns) — don't need full 300 Chinese names unless easy.

Sources:
- sims/robocasa/robocasa/utils/dataset_registry.py TARGET_TASKS, PRETRAINING_TASKS
- docs/cursor_list_robocasa_scenes_langs.md if useful
- Prior classification: 轮臂结合 ≈ DeliverStraw, StoreLeftoversInBowl, ArrangeBreadBasket, GarnishPancake, SteamInMicrowave (+ more if found); NavigateKitchen = 仅导航

Write Chinese translations that are natural (CloseFridge→关冰箱, DeliverStraw→递吸管到餐区, etc.).

Also if the parallel agent criteria differ, prefer thorough TARGET coverage.

Output in chat as markdown tables. Optionally suggest saving to docs/ — but do NOT write files unless you create docs/robocasa_task_catalog.md (user asked 整理 — creating one doc is OK and helpful). If you write a file, path: /home/sany/Documents/Foundation/docs/robocasa_task_catalog.md and add one line to docs/README.md index.

Prefer writing the docs file so it's durable.

---

**Cursor**

先从源码和现有文档里把 TARGET 50 与 pretrain 任务清单拉齐，再做中文翻译与聚合分类。

继续用启发式扫 dining/跨区线索，并核对 TARGET 50 的运动类型分类。

已对齐并行代理的轮臂判定；正在写入完整中文任务目录文档。

已写入 [`docs/robocasa_task_catalog.md`](docs/robocasa_task_catalog.md)，并在 `docs/README.md` 加了索引行。要点如下。

### TARGET50 聚合

| 维度 | 计数 |
|------|------|
| Atomic / Composite | **18 / 32** |
| Seen / Unseen | **34 / 16**（无 atomic_unseen） |
| 贴夹具 / 仅导航 / 轮臂结合 | **43 / 1 / 6** |

**轮臂结合（6）**：DeliverStraw、GetToastedBread、StoreLeftoversInBowl、SteamInMicrowave（边缘）、ArrangeBreadBasket、GarnishPancake  
**仅导航（1）**：NavigateKitchen

### 运动类型（摘录）

| English | 中文 | 家族 | 集合 | 运动类型 |
|---------|------|------|------|----------|
| CloseFridge | 关冰箱 | Atomic | seen | 贴夹具操作 |
| NavigateKitchen | 厨房内导航 | Atomic | seen | 仅导航 |
| DeliverStraw | 递吸管到餐区 | Composite | seen | 轮臂结合跨区 |
| StoreLeftoversInBowl | 剩菜装碗入冰箱 | Composite | seen | 轮臂结合跨区 |
| SteamInMicrowave | 微波炉蒸蔬菜 | Composite | seen | 轮臂结合跨区（边缘） |
| ArrangeBreadBasket | 面包篮摆到餐区 | Composite | unseen | 轮臂结合跨区 |
| GarnishPancake | 给煎饼加草莓装饰 | Composite | unseen | 轮臂结合跨区 |

其余 43 个为贴夹具；完整 50 行表见文档。

### pretrain300 / Human300

| 项 | 数量 |
|----|------|
| 总任务 | **300**（65 atomic + 235 composite） |
| 仅导航 | **1** |
| 轮臂结合（dining/跨站启发式） | **≈50（≈17%）** |

与并行统计一致：TARGET 严格跨站为 6；`PortionHotDogs` / `RecycleBottlesByType` 仅标为 dining 长台边缘（未计入 6）。单独评测轮臂：

```bash
--env.task=DeliverStraw,GetToastedBread,StoreLeftoversInBowl,SteamInMicrowave,ArrangeBreadBasket,GarnishPancake
```

