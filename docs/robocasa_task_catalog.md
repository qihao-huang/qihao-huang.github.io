# RoboCasa 任务目录（TARGET50 + pretrain300 规模）

> 来源：`sims/robocasa/robocasa/utils/dataset_registry.py` 的 `TARGET_TASKS` / `PRETRAINING_TASKS`  
> 运动类型为启发式分类（dining↔厨房夹具跨站、显式 navigate、sink→microwave），**非**官方 split。  
> `pretrain300` ≡ Human300（全部带 `pretrain=` 的 human 任务）：65 atomic + 235 composite = **300**。

---

## 运动类型定义

| 运动类型 | 含义 | 典型例子 |
|----------|------|----------|
| **贴夹具操作** | 出生即贴目标夹具/邻域，底盘几乎不动即可完成 | CloseFridge、OpenDrawer、多数 PnP / 邻域 composite |
| **仅导航** | 需要开底盘，但无抓取操作 | NavigateKitchen |
| **轮臂结合跨区** | 有意义的底盘位移 + 手臂操作（跨站：厨房夹具 ↔ dining，或 sink→microwave 等） | DeliverStraw、StoreLeftoversInBowl |

**TARGET50 轮臂结合（6，含 1 个边缘）**：DeliverStraw、GetToastedBread、StoreLeftoversInBowl、SteamInMicrowave（边缘）、ArrangeBreadBasket、GarnishPancake。

未计入严格轮臂：`StackBowlsCabinet`（docstring 写 dining，实现为柜旁 counter）；`PortionHotDogs` / `RecycleBottlesByType`（dining 长台内搬运，另见备注）。

---

## 1. TARGET50 全表

### 1.1 atomic_seen（18）

| English | 中文 | 家族 | 集合 | 运动类型 | 主题 |
|---------|------|------|------|----------|------|
| CloseBlenderLid | 盖上搅拌机盖 | Atomic | seen | 贴夹具操作 | 开关盖 |
| CloseFridge | 关冰箱 | Atomic | seen | 贴夹具操作 | 开关门 |
| CloseToasterOvenDoor | 关多士炉烤箱门 | Atomic | seen | 贴夹具操作 | 开关门 |
| CoffeeSetupMug | 摆咖啡杯到咖啡机下 | Atomic | seen | 贴夹具操作 | 电器 / 取放 |
| NavigateKitchen | 厨房内导航 | Atomic | seen | 仅导航 | 导航 |
| OpenCabinet | 开橱柜 | Atomic | seen | 贴夹具操作 | 开关门 |
| OpenDrawer | 开抽屉 | Atomic | seen | 贴夹具操作 | 开关门 |
| OpenStandMixerHead | 抬起立式搅拌机头 | Atomic | seen | 贴夹具操作 | 开关盖 |
| PickPlaceCounterToCabinet | 台面取物放入橱柜 | Atomic | seen | 贴夹具操作 | 取放 |
| PickPlaceCounterToStove | 台面取物放到灶上 | Atomic | seen | 贴夹具操作 | 取放 |
| PickPlaceDrawerToCounter | 抽屉取物放到台面 | Atomic | seen | 贴夹具操作 | 取放 |
| PickPlaceSinkToCounter | 水槽取物放到台面 | Atomic | seen | 贴夹具操作 | 取放 |
| PickPlaceToasterToCounter | 吐司机取出物放到台面 | Atomic | seen | 贴夹具操作 | 取放 |
| SlideDishwasherRack | 抽拉洗碗机篮架 | Atomic | seen | 贴夹具操作 | 电器 |
| TurnOffStove | 关灶火 | Atomic | seen | 贴夹具操作 | 电器 |
| TurnOnElectricKettle | 打开电热水壶 | Atomic | seen | 贴夹具操作 | 电器 |
| TurnOnMicrowave | 打开微波炉 | Atomic | seen | 贴夹具操作 | 电器 |
| TurnOnSinkFaucet | 打开水龙头 | Atomic | seen | 贴夹具操作 | 电器 |

### 1.2 composite_seen（16）

| English | 中文 | 家族 | 集合 | 运动类型 | 主题 |
|---------|------|------|------|----------|------|
| DeliverStraw | 递吸管到餐区 | Composite | seen | 轮臂结合跨区 | 饮品 / 上菜 |
| GetToastedBread | 取烤面包到餐区 | Composite | seen | 轮臂结合跨区 | 烹饪 / 上菜 |
| KettleBoiling | 烧水壶煮水 | Composite | seen | 贴夹具操作 | 烹饪 |
| LoadDishwasher | 装洗碗机 | Composite | seen | 贴夹具操作 | 清洗 |
| PackIdenticalLunches | 打包相同午餐盒 | Composite | seen | 贴夹具操作 | 整理 / 打包 |
| PreSoakPan | 锅具预浸泡 | Composite | seen | 贴夹具操作 | 清洗 |
| PrepareCoffee | 冲泡咖啡 | Composite | seen | 贴夹具操作 | 饮品 / 电器 |
| RinseSinkBasin | 冲洗水槽盆 | Composite | seen | 贴夹具操作 | 清洗 |
| ScrubCuttingBoard | 擦洗砧板 | Composite | seen | 贴夹具操作 | 清洗 |
| SearingMeat | 煎烤肉类 | Composite | seen | 贴夹具操作 | 烹饪 |
| SetUpCuttingStation | 布置切肉工位 | Composite | seen | 贴夹具操作 | 烹饪 / 整理 |
| StackBowlsCabinet | 橱柜内叠碗 | Composite | seen | 贴夹具操作 | 整理 |
| SteamInMicrowave | 微波炉蒸蔬菜 | Composite | seen | 轮臂结合跨区（边缘） | 烹饪 / 电器 |
| StirVegetables | 翻炒蔬菜 | Composite | seen | 贴夹具操作 | 烹饪 |
| StoreLeftoversInBowl | 剩菜装碗入冰箱 | Composite | seen | 轮臂结合跨区 | 整理 / 收纳 |
| WashLettuce | 洗生菜 | Composite | seen | 贴夹具操作 | 清洗 |

### 1.3 composite_unseen（16）

| English | 中文 | 家族 | 集合 | 运动类型 | 主题 |
|---------|------|------|------|----------|------|
| ArrangeBreadBasket | 面包篮摆到餐区 | Composite | unseen | 轮臂结合跨区 | 整理 / 上菜 |
| ArrangeTea | 布置茶具 | Composite | unseen | 贴夹具操作 | 饮品 / 整理 |
| BreadSelection | 选择面包与果酱 | Composite | unseen | 贴夹具操作 | 烹饪 / 取放 |
| CategorizeCondiments | 归类调味品 | Composite | unseen | 贴夹具操作 | 整理 |
| CuttingToolSelection | 选择合适刀具 | Composite | unseen | 贴夹具操作 | 烹饪 / 取放 |
| GarnishPancake | 给煎饼加草莓装饰 | Composite | unseen | 轮臂结合跨区 | 烹饪 / 上菜 |
| GatherTableware | 归集餐具入柜 | Composite | unseen | 贴夹具操作 | 整理 |
| HeatKebabSandwich | 加热烤肉三明治 | Composite | unseen | 贴夹具操作 | 烹饪 / 电器 |
| MakeIceLemonade | 做冰块柠檬水 | Composite | unseen | 贴夹具操作 | 饮品 |
| PanTransfer | 锅中菜倒到盘 | Composite | unseen | 贴夹具操作 | 烹饪 / 上菜 |
| PortionHotDogs | 热狗分份装盘 | Composite | unseen | 贴夹具操作※ | 整理 / 上菜 |
| RecycleBottlesByType | 按材质分拣瓶子 | Composite | unseen | 贴夹具操作※ | 整理 |
| SeparateFreezerRack | 冷冻架分区存放 | Composite | unseen | 贴夹具操作 | 整理 / 收纳 |
| WaffleReheat | 微波炉复热华夫饼 | Composite | unseen | 贴夹具操作 | 烹饪 / 电器 |
| WashFruitColander | 滤篮洗水果 | Composite | unseen | 贴夹具操作 | 清洗 |
| WeighIngredients | 称重配料 | Composite | unseen | 贴夹具操作 | 烹饪 / 整理 |

※ `PortionHotDogs`、`RecycleBottlesByType`：物体多在 dining 长台上，可能需沿台面短距底盘移动，**未计入**严格「轮臂结合跨区」。若放宽标准，TARGET 轮臂可由 6 扩到 8。

---

## 2. 聚合分类（TARGET50）

### 2.1 Atomic vs Composite

| 家族 | 数量 | 占比 |
|------|------|------|
| Atomic | 18 | 36% |
| Composite | 32 | 64% |
| **合计** | **50** | 100% |

### 2.2 Seen vs Unseen

| 集合 | 数量 | 说明 |
|------|------|------|
| seen（atomic_seen + composite_seen） | 18 + 16 = **34** | 预训练见过的评测任务 |
| unseen（composite_unseen） | **16** | 零样本复合任务 |
| atomic unseen | **0** | TARGET 无 atomic_unseen |

### 2.3 运动类型三分类

| 运动类型 | 数量 | 任务 |
|----------|------|------|
| 贴夹具操作 | **43** | 其余全部 |
| 仅导航 | **1** | NavigateKitchen |
| 轮臂结合跨区 | **6** | DeliverStraw, GetToastedBread, StoreLeftoversInBowl, SteamInMicrowave, ArrangeBreadBasket, GarnishPancake |

| 子集合 | 轮臂结合 | 仅导航 | 贴夹具 |
|--------|----------|--------|--------|
| atomic_seen (18) | 0 | 1 | 17 |
| composite_seen (16) | 4 | 0 | 12 |
| composite_unseen (16) | 2 | 0 | 14 |

### 2.4 主题粗分（TARGET50，可重叠归入主主题）

| 主题 | 约数 | 代表任务 |
|------|------|----------|
| 开关门 / 盖 / 抽屉 | 7 | CloseFridge, OpenCabinet, OpenDrawer, CloseBlenderLid, … |
| 取放（atomic PnP） | 5 | PickPlaceCounterToCabinet / Stove / Drawer / Sink / Toaster |
| 电器控制 | 5 | TurnOnMicrowave, TurnOffStove, TurnOnSinkFaucet, SlideDishwasherRack, TurnOnElectricKettle |
| 导航 | 1 | NavigateKitchen |
| 烹饪 | ~12 | SearingMeat, StirVegetables, SteamInMicrowave, KettleBoiling, HeatKebabSandwich, … |
| 清洗 | ~6 | WashLettuce, PreSoakPan, RinseSinkBasin, ScrubCuttingBoard, WashFruitColander, LoadDishwasher |
| 整理 / 收纳 | ~8 | StackBowlsCabinet, StoreLeftoversInBowl, CategorizeCondiments, GatherTableware, RecycleBottlesByType, … |
| 饮品 / 上菜 | ~6 | DeliverStraw, PrepareCoffee, ArrangeTea, MakeIceLemonade, GarnishPancake, GetToastedBread |

---

## 3. pretrain300 / Human300 规模（摘要）

| 项 | 数量 |
|----|------|
| **pretrain300 总任务** | **300** |
| Atomic | **65** |
| Composite | **235** |
| 仅导航 | **1**（NavigateKitchen） |
| 轮臂结合跨区（启发式） | **≈50（≈17%）** |
| dining 长台边缘（未计入严格轮臂） | ≈13 |

与评测对比：

| | TARGET50 | pretrain300 |
|--|----------|-------------|
| Atomic / Composite | 18 / 32 | 65 / 235 |
| 轮臂结合 | **6（12%）** | **≈50（≈17%）** |
| 仅导航 | 1 | 1 |

### pretrain 各档轮臂数量（同启发式）

| 集合 | 总任务 | 轮臂结合 |
|------|--------|----------|
| pretrain50 | 50 | ≈7 |
| pretrain100 | 100 | ≈7 |
| pretrain200 | 200 | ≈32 |
| pretrain300 | 300 | ≈50 |

**pretrain50/100 轮臂示例（7）**  
DeliverStraw, GetToastedBread, SteamInMicrowave, StoreLeftoversInBowl, ArrangeBuffetDessert, DateNight, PrepareCocktailStation

**pretrain300 轮臂名单（≈50，启发式）**  
AddLemonToFish, AddMarshmallow, AlcoholServingPrep, AlignSilverware, ArrangeBreadBowl, ArrangeBuffetDessert, ArrangeDrinkware, BeverageOrganization, BuildAppetizerPlate, CandleCleanup, ClearReceptaclesForCleaning, CoolKettle, CutBuffetPizza, DateNight, DeliverBrewedCoffee, DeliverStraw, DisplayMeatVariety, DistributeChicken, DivideBuffetTrays, GarnishCupcake, GetToastedBread, HotDogSetup, MatchCupAndDrink, MixedFruitPlatter, OrganizeVegetables, PackFoodByTemp, PlaceBeveragesTogether, PlaceDishesBySink, PortionOnSize, PrepareCocktailStation, PrepareDrinkStation, PrepareStoringLeftovers, RecycleBottlesBySize, RefillCondimentStation, RetrieveIceTray, ReturnHeatedFood, ScalePortioning, SeasoningSpiceSetup, SeasoningSteak, ServeSteak, ServeTea, SetBowlsForSoup, SetupButterPlate, SetupFruitBowl, SetupSodaBowl, SetupWineGlasses, SteamInMicrowave, StoreLeftoversByType, StoreLeftoversInBowl, TongBuffetSetup

> `ServeTea` / `HotDogSetup` 在 **pretrain**，**不在** TARGET50。

---

## 4. 单独评测轮臂结合（TARGET）

```bash
--env.task=DeliverStraw,GetToastedBread,StoreLeftoversInBowl,SteamInMicrowave,ArrangeBreadBasket,GarnishPancake
```

纯导航：

```bash
--env.task=NavigateKitchen
```

---

## 相关文档

- [cursor_list_robocasa_scenes_langs.md](./cursor_list_robocasa_scenes_langs.md) — 场景与 `lang` 指令模板
- [robocasa_lerobot_rlinf_handson.md](./robocasa_lerobot_rlinf_handson.md) — 训评上手
- 源码：`sims/robocasa/robocasa/utils/dataset_registry.py`
