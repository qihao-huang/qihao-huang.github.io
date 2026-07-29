# List RoboCasa scenes+langs
_Exported on 2026/7/29 at GMT+8 11:16:35 from Cursor (3.13.10)_

---

**User**

User asks (Simplified Chinese answer): 详细列举 RoboCasa 中的场景和指令。

Workspace: /home/sany/Documents/Foundation

Produce a structured, detailed inventory covering:

## 1. Scenes (场景)
- How kitchens/layouts/styles are organized (layout_id, style_id, split pretrain vs target)
- Counts if available (e.g. 2500 pretrain kitchens, 10 target)
- Where defined in code (scenes, fixtures, dataset_registry, kitchen.py)
- What varies per episode vs fixed

## 2. Instructions (指令)
- How `ep_meta["lang"]` is generated
- List atomic_seen / composite_seen / composite_unseen task names (from sims/robocasa/.../dataset_registry.py TARGET_TASKS)
- For as many task classes as practical, show the lang template or example strings from get_ep_meta in atomic/*.py and key composite files
- Note when lang varies per episode (obj_lang, fixture nat_lang, left/right, novel_instructions)
- Mention CloseFridge examples: "Close the fridge door(s)."

## 3. Relationship
- Scene randomization vs instruction text coupling
- What LeRobot uses at eval (task_description from lang)

Read code under:
- sims/robocasa/robocasa/utils/dataset_registry.py (TARGET_TASKS)
- sims/robocasa/robocasa/environments/kitchen/
- sims/robocasa/docs if useful for scene counts
- novel_instructions CSV if present

Output should be usable as a reference table: task → typical instruction pattern. Prefer tables. Concise Chinese. Do not create docs files unless useful; answer in chat.

---

**Cursor**

我先从 RoboCasa 的 `dataset_registry`、厨房环境与任务定义入手，整理场景与指令清单。

继续查场景注册、`get_ep_meta` 语言模板，以及 LeRobot 如何取指令。

## 1. 场景（Scenes）

场景 = **(layout_id, style_id)** 对。Layout 定平面/夹具排布；Style 定纹理与夹具外观（把手、门型、咖啡机型号等）。

| Split | Layout | Style | 组合方式 | 厨房数 |
|-------|--------|-------|----------|--------|
| **pretrain** | 11–60（50） | 11–60（50） | 笛卡尔积 | **2500** |
| **target** | 1–10 | 1–10 | **对角配对** `(i,i)` | **10** |
| all | 1–60 | 1–60 | 全组合 | 3600 |

**代码入口**

| 内容 | 路径 |
|------|------|
| ID/分组 | `/home/sany/Documents/Foundation/sims/robocasa/robocasa/models/scenes/scene_registry.py`（`LAYOUT_GROUPS_TO_IDS`: `-2`=train/`pretrain`, `-1`=test/`target`） |
| split→采样池 | `/home/sany/Documents/Foundation/sims/robocasa/robocasa/utils/env_utils.py`：`pretrain`→`layout_ids=style_ids=-2`；`target`→`zip(range(1,11), range(1,11))` |
| 每 episode 采样 | `kitchen.py` `_setup_model`：`rng.choice(layout_and_style_ids)` |
| 搭建场景 | `kitchen_arena.py` + `scenes/kitchen_layouts/{train\|test}/`、`kitchen_styles/...` |
| 文档计数 | `docs/assets/scenes.md`、`docs/datasets/datasets_overview.md` |

**每 episode 变 vs 相对固定**

| 每 episode 变 | 相对固定（任务级） |
|---------------|-------------------|
| `layout_id` / `style_id` | 任务类与成功判据 |
| 物体实例（`obj_instance_split=pretrain\|target`） | 指令**模板**结构 |
| 夹具引用、物体位姿、干扰物数量 | — |
| 机器人初始位姿噪声 | — |
| 部分任务：门侧 left/right、knob、rack 上下 | — |

Ablation：`5x5`/`5x1` 子集见 `env_utils.KITCHEN_SCENES_5X5`（5 layout × 5 style = 25）。

---

## 2. 指令（Instructions）

### 生成链路

1. 基类 `Kitchen.get_ep_meta()` 设 `ep_meta["lang"]=""`，并写入 `layout_id`/`style_id`/`object_cfgs`/`fixtures` 等。  
2. 各任务子类覆盖 `get_ep_meta()`，填充自然语言。  
3. 可选 `use_novel_instructions=True`：从  
   `robocasa/models/assets/novel_instructions/task_instruction_variants.csv`  
   抽样（约 32 个 **composite target** 任务，每任务 3 个变体）。Atomic 一般不走 CSV。

可变槽位常见：`get_obj_lang()`（物体名）、`fixture.nat_lang`（如 `"fridge"`/`"cabinet"`）、`drawer_side`（left/right）、`knob`、rack 方向、`novel_instructions`。

**CloseFridge 示例**（继承 `ManipulateDoor`）：  
`f"{behavior} the {fxtr.nat_lang} {door_name}."`  
→ 通常为 **"Close the fridge door."**；法式对开门时 `door_name="doors"` → **"Close the fridge doors."**

### TARGET_TASKS 任务列表

来源：`sims/robocasa/robocasa/utils/dataset_registry.py`

| 集合 | 数量 | 任务名 |
|------|------|--------|
| **atomic_seen** | 18 | CloseBlenderLid, CloseFridge, CloseToasterOvenDoor, CoffeeSetupMug, NavigateKitchen, OpenCabinet, OpenDrawer, OpenStandMixerHead, PickPlaceCounterToCabinet, PickPlaceCounterToStove, PickPlaceDrawerToCounter, PickPlaceSinkToCounter, PickPlaceToasterToCounter, SlideDishwasherRack, TurnOffStove, TurnOnElectricKettle, TurnOnMicrowave, TurnOnSinkFaucet |
| **composite_seen** | 16 | DeliverStraw, GetToastedBread, KettleBoiling, LoadDishwasher, PackIdenticalLunches, PreSoakPan, PrepareCoffee, RinseSinkBasin, ScrubCuttingBoard, SearingMeat, SetUpCuttingStation, StackBowlsCabinet, SteamInMicrowave, StirVegetables, StoreLeftoversInBowl, WashLettuce |
| **composite_unseen** | 16 | ArrangeBreadBasket, ArrangeTea, BreadSelection, CategorizeCondiments, CuttingToolSelection, GarnishPancake, GatherTableware, HeatKebabSandwich, MakeIceLemonade, PanTransfer, PortionHotDogs, RecycleBottlesByType, SeparateFreezerRack, WaffleReheat, WashFruitColander, WeighIngredients |

---

### 参考表 A：atomic_seen → 典型指令

| Task | 典型 `lang` 模式 | 每集可变？ |
|------|------------------|------------|
| CloseBlenderLid | `Close the lid blender by securely placing the lid on top.` | 否 |
| CloseFridge | `Close the fridge door(s).` | door/doors（夹具类型） |
| CloseToasterOvenDoor | `Close the toaster oven door.` | 否 |
| CoffeeSetupMug | `Pick the {obj_lang} from the counter and place it under the coffee machine dispenser.` | obj_lang |
| NavigateKitchen | `Navigate to the {target_fixture.nat_lang}.` | 目标夹具名 |
| OpenCabinet | `Open the cabinet door(s).` | door/doors |
| OpenDrawer | `Open the {left\|right} drawer.` | drawer_side |
| OpenStandMixerHead | `Open the stand mixer head.` | 否 |
| PickPlaceCounterToCabinet | `Pick the {obj} from the counter and place it in the cabinet.` | obj |
| PickPlaceCounterToStove | `Pick the {obj} from the plate and place it in the {container}.` | obj/container |
| PickPlaceDrawerToCounter | `Pick the {obj} from the drawer and place it on the counter.` | obj |
| PickPlaceSinkToCounter | `Pick the {obj} from the sink and place it on the {container} located on the counter.` | obj/container |
| PickPlaceToasterToCounter | `Place the toasted item on a plate.` | 否 |
| SlideDishwasherRack | `Fully slide the top dishwasher rack {in\|out}.` | 方向 |
| TurnOffStove | `Turn off the {knob} burner of the stove.` | knob |
| TurnOnElectricKettle | `Press down the lever to turn on the electric kettle.` | 否 |
| TurnOnMicrowave | `Press the start button on the microwave.` | 否 |
| TurnOnSinkFaucet | `Turn on the sink faucet.` | 否 |

### 参考表 B：更多 atomic 模板（非 target，实用）

| Task | 模式 |
|------|------|
| Open/Close Microwave/Oven/Dishwasher/Fridge | `{Open\|Close} the {nat_lang} door(s).` |
| OpenBlenderLid | `Open the blender by taking off the lid and placing it on the counter.` |
| PnP 系列 | `Pick the {obj} from A and place it in/on B`（A/B=cabinet/sink/microwave/drawer/blender…） |
| TurnOn/Off Stove | `{Turn on\|Turn off} the {knob} burner of the stove.` |
| TurnSinkSpout | `Turn the sink spout to the {left\|right}.` |
| AdjustWaterTemperature | `The water … is {hot\|cold}. Adjust … to run the water {cold\|hot}.` |
| NavigateKitchen | 见上 |
| CheesyBread | `Pick up the wedge of cheese and place it on the slice of bread...` |
| MakeIcedCoffee | `Pick up an ice cube and place it in the glass of coffee.` |

### 参考表 C：composite_seen → 典型指令

| Task | 典型模式 | 可变 |
|------|----------|------|
| DeliverStraw | `Take a straw from the drawer… place it inside the glass cup on the dining counter.` | novel |
| GetToastedBread | `Start the toaster. Once the lever pops up, take the bread to the plate…` | novel |
| KettleBoiling | `Pick the kettle… place it on a stove burner. Then turn the burner on.` | novel |
| LoadDishwasher | `Pick up the {dish0} and {dish1}… place them in the dishwasher, and close…` | obj + novel |
| PackIdenticalLunches | `Place one {veg} and one {meat} in each tupperware…` | obj + novel |
| PreSoakPan | `Pick the pan and sponge… into the sink. Then turn on the water.` | novel |
| PrepareCoffee | `Pick the {mug} from the cabinet, place it under the coffee machine… press start.` | obj + novel |
| RinseSinkBasin | `Turn on the sink and manuever the spout to wash all locations of the sink basin.` | novel |
| ScrubCuttingBoard | `Pick up the sponge… scrubbing… cutting board…` | novel |
| SearingMeat | `Grab the pan… on the {knob} burner… place the {meat}… turn the burner on.` | knob/meat + novel |
| SetUpCuttingStation | `Pick up the knife… on the cutting board. Then place the meat…` | novel |
| StackBowlsCabinet | `…stack them… in the open cabinet. Place the smaller bowl on top of the larger bowl.` | novel |
| SteamInMicrowave | `Pick the {veg} from the sink… bowl… microwave… close… start.` | obj + novel |
| StirVegetables | `Put the {veg1} and {veg2} in the pot. Retrieve the spatula and lightly stir…` | obj + novel |
| StoreLeftoversInBowl | `Pick the chicken drumstick and {veg}… bowl. Then put the bowl in the fridge.` | obj + novel |
| WashLettuce | `Wash the lettuce in the sink by running water over it.` | novel |

### 参考表 D：composite_unseen → 典型指令

| Task | 典型模式 |
|------|----------|
| ArrangeBreadBasket | `Open the cabinet, pick up the {bread}… in the basket. Then move the basket to the dining counter.` |
| ArrangeTea | `Pick the kettle… on the tray. Then pick the mug… close the cabinet doors.` |
| BreadSelection | `…select a croissant… Then retrieve a jar of jam…` |
| CategorizeCondiments | `Put the shaker and condiment bottle… next to their counterparts in the cabinet.` |
| CuttingToolSelection | `Place the appropriate cutting tool for cutting the {cat} skin on the cutting board.` |
| GarnishPancake | `Take the strawberry from the fridge and place it on top of the pancake…` |
| GatherTableware | `Gather all objects into one cabinet and sort the glasses and bowls to opposite sides.` |
| HeatKebabSandwich | `Pick up the kebab skewer and baguette… toaster oven… Close… set the timer.` |
| MakeIceLemonade | `Grab a lemon wedge… and one ice cube… put them in the glass of lemonade.` |
| PanTransfer | `Pick up the pan and dump the vegetables… onto the plate. Then return the pan to the stove.` |
| PortionHotDogs | `Place one bun and one sausage from the bowl on each plate.` |
| RecycleBottlesByType | `Move the plastic bottles… to the plastics group, and the glass bottles… to the glass group.` |
| SeparateFreezerRack | `Take the meat container… second highest rack… vegetable container… highest rack…` |
| WaffleReheat | `Open the microwave, place the bowl with waffle… close… turn it on.` |
| WashFruitColander | `Put the colander in the sink, put the {fruit}… turn on the sink…` |
| WeighIngredients | `Pick the {obj} and place it on the digital scale… and close the cabinet.` |

Novel CSV 覆盖几乎全部上表 composite（seen+unseen），**不含** atomic。

---

## 3. 关系：场景随机化 vs 指令；LeRobot

| 关系 | 说明 |
|------|------|
| **弱耦合** | layout/style 改变视觉与夹具几何；多数指令不提具体厨房编号 |
| **中耦合** | 指令里的 `nat_lang`/物体名依赖本局采样到的夹具与物体（同任务、不同 episode 文案可不同） |
| **强耦合（任务逻辑）** | 如 fridge 单门 vs 双门 → door/doors；stove knob 名写入 lang |

**LeRobot eval**（`main/lerobot/src/lerobot/envs/robocasa.py`）：

- `reset()` / 建环境后：`ep_meta = env.get_ep_meta()` → `self.task_description = ep_meta.get("lang", self.task)`
- `lerobot_eval.py`：`observation["task"] = task_description`，策略吃的是 **本局 `lang` 字符串**，不是任务类名 alone。

默认 `split`：LeRobot 包装层在未指定时用 `"all"`；常用评测（如 `atomic_seen`）应配合 `split=target` 以对齐 10 间 held-out 厨房。

