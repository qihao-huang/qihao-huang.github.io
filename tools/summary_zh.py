"""
summary_zh.py — 为每篇论文生成中文总结（离线，基于标题+摘要+标签）。
结构：提出什么方法 → 解决什么问题 → 关键 insight/看法。
"""

from __future__ import annotations
import re

# 规则摘要版本；变更提取逻辑时递增，使旧缓存失效
RULE_VERSION = "v6"

# 标签 → 中文
TAG_ZH: dict[str, str] = {
    "BEV Perception": "鸟瞰图感知",
    "Occupancy Prediction": "占据栅格预测",
    "3D Detection": "三维目标检测",
    "End-to-End Driving": "端到端自动驾驶",
    "Motion Planning": "运动规划",
    "Motion Prediction": "运动预测",
    "World Model": "世界模型",
    "Simulation": "仿真",
    "HD Mapping": "高精地图",
    "Tracking": "目标跟踪",
    "SLAM / Localization": "SLAM与定位",
    "VLA": "视觉-语言-动作模型",
    "Robot Manipulation": "机器人操作",
    "Humanoid Robot": "人形机器人",
    "Dexterous Manipulation": "灵巧操作",
    "Force / Compliance": "力控与柔顺",
    "Teleoperation": "遥操作",
    "Imitation Learning": "模仿学习",
    "Data Collection": "数据采集",
    "Transformer": "Transformer",
    "Diffusion Model": "扩散模型",
    "Reinforcement Learning": "强化学习",
    "Generative Model": "生成模型",
    "NeRF / 3DGS": "NeRF/高斯溅射",
    "Graph Neural Network": "图神经网络",
    "Foundation Model": "基础模型",
    "LLM / VLM": "大语言/视觉语言模型",
    "Self-Supervised": "自监督学习",
    "Distillation": "知识蒸馏",
    "Optimization": "优化方法",
    "Object Detection": "目标检测",
    "Segmentation": "分割",
    "Classification": "分类",
    "Depth Estimation": "深度估计",
    "Pose Estimation": "位姿估计",
    "Grasping": "抓取",
    "Navigation": "导航",
    "Control": "控制",
    "Forecasting": "预测",
    "Reconstruction": "三维重建",
    "Generation": "生成",
    "Benchmark / Dataset": "基准/数据集",
    "Evaluation": "评估",
    "LiDAR": "激光雷达",
    "Camera / Vision": "视觉",
    "Radar": "毫米波雷达",
    "Language": "语言",
    "Tactile": "触觉",
    "IMU / Proprioception": "本体感知",
    "Multi-Modal Fusion": "多模态融合",
    "Computer Vision": "计算机视觉",
    "Robotics": "机器人",
    "Machine Learning": "机器学习",
    "Uncategorized": "综合",
}

# 常见英文词组 → 中文片段
_PHRASE_ZH: list[tuple[str, str]] = [
    (r"constraint[- ]aware", "约束感知"),
    (r"flow matching", "流匹配"),
    (r"mode collapse", "模式坍塌"),
    (r"trajectory generation", "轨迹生成"),
    (r"trajectory hypotheses?", "多样化轨迹"),
    (r"diverse trajectories?", "多样化轨迹"),
    (r"safety[- ]critical", "安全关键"),
    (r"long[- ]tail", "长尾"),
    (r"action prediction", "动作预测"),
    (r"chain of causation", "因果链推理"),
    (r"vision[-–]language[-–]action", "视觉-语言-动作"),
    (r"imitation learning", "模仿学习"),
    (r"end[- ]to[- ]end", "端到端"),
    (r"autonomous driving", "自动驾驶"),
    (r"generative (?:process|approach|model|methods?)", "生成式方法"),
    (r"motion planning", "运动规划"),
    (r"multi[- ]object tracking", "多目标跟踪"),
    (r"data association", "数据关联"),
    (r"video object segmentation", "视频目标分割"),
    (r"object detection", "目标检测"),
    (r"3d object detection", "三维目标检测"),
    (r"chain[- ]of[- ]thought", "思维链"),
    (r"explicit chain[- ]of[- ]thought reasoning", "显式思维链推理"),
    (r"contact[- ]rich tactile", "接触丰富触觉"),
    (r"tactile[- ]reactive", "触觉反馈驱动"),
    (r"dexterous manipulation", "灵巧操作"),
    (r"mix[- ]of[- ]transformer", "混合Transformer"),
    (r"variable[- ]rate", "可变速率"),
    (r"temporal tactile", "时序触觉"),
    (r"vq[- ]vae", "VQ-VAE"),
    (r"post[- ]training", "后训练"),
    (r"egocentric (?:video|data|demonstration)", "第一人称视角数据"),
    (r"human egocentric", "人类第一人称"),
    (r"elementary motor primitives?", "基础运动原语"),
    (r"deformable object", "可变形物体"),
    (r"delicate force control", "精细力控"),
    (r"high[- ]frequency touch", "高频触觉信号"),
    (r"static tactile encoders?", "静态触觉编码器"),
    (r"static cues?", "静态触觉线索"),
    (r"before action prediction", "在动作预测之前"),
    (r"improves generalization", "提升泛化能力"),
    (r"\bimproves\b", "提升"),
    (r"high[- ]frequency tactile", "高频触觉"),
    (r"ignore high[- ]frequency", "忽视高频"),
    (r"denoising training", "去噪训练"),
    (r"anchor initialization", "锚框初始化"),
    (r"look forward twice", "双向前向预测"),
    (r"contrastive way for denoising", "对比去噪训练"),
    (r"improved denoising anchor boxes?", "改进去噪锚框"),
    (r"contrastive way for denoising", "对比去噪训练"),
    (r"mixed query selection", "混合查询选择"),
    (r"sparse spatial[- ]temporal fusion", "稀疏时空融合"),
    (r"multi[- ]view", "多视角"),
    (r"recurrent temporal fusion", "循环时序融合"),
    (r"sparse sensor fusion", "稀疏传感器融合"),
    (r"long range perception", "远距感知"),
    (r"query selection", "查询选择"),
    (r"reinforcement learning", "强化学习"),
    (r"world model", "世界模型"),
    (r"world action model", "世界动作模型"),
    (r"world[-–]action model", "世界-动作模型"),
    (r"test[- ]time future imagination", "测试时未来想象"),
    (r"future imagination", "未来想象"),
    (r"imagine[- ]then[- ]execute", "想象-执行"),
    (r"video denoising", "视频去噪"),
    (r"tactile[- ]reactive", "触觉反馈驱动"),
    (r"multi[- ]traversal", "多趟次"),
    (r"gaussian splatting", "高斯溅射"),
    (r"novel view synthesis", "新视角合成"),
    (r"embodied (?:ai|control)", "具身控制"),
    (r"data engine", "数据引擎"),
    (r"action[- ]centered", "以动作为中心"),
    (r"efficient", "高效"),
    (r"empower", "赋能"),
    (r"point cloud", "点云"),
    (r"bird[''\u2019]?s?[- ]?eye[- ]?view", "鸟瞰图"),
    (r"multi[- ]camera images?", "多相机图像"),
    (r"representations?", "表征"),
    (r"optical flow", "光流"),
    (r"humanoid", "人形机器人"),
    (r"manipulation", "操作"),
    (r"reasoning", "推理"),
    (r"generaliz(?:e|able|ation)", "泛化"),
    (r"sparse supervision", "监督稀疏"),
    (r"physical constraints?", "物理约束"),
    (r"safety (?:and|&) physical constraints?", "安全与物理约束"),
    (r"safety constraints?", "安全约束"),
    (r"planning", "规划"),
    (r"brittle", "脆弱"),
    (r"benchmark", "基准测试"),
    (r"dataset", "数据集"),
    (r"camera motion estimation", "相机运动估计"),
    (r"simultaneous localization and mapping", "同时定位与建图"),
    (r"spatial[- ]temporal fusion", "时空融合"),
    (r"gaussian splatting", "高斯溅射"),
    (r"feed[- ]forward", "前馈"),
    (r"sensor fusion", "传感器融合"),
    (r"cross[- ]embodiment", "跨具身"),
    (r"human hand", "人手"),
    (r"kinesthetic demonstrations?", "动觉演示"),
    (r"force[- ]informed actions?", "力感知动作"),
    (r"universal manipulation interface", "通用操作接口"),
    (r"contact[- ]rich manipulation", "接触丰富操作"),
    (r"in[- ]the[- ]wild", "真实场景"),
    (r"compliant manipulation", "柔顺操作"),
    (r"data collection", "数据采集"),
    (r"policy learning", "策略学习"),
    (r"vision[- ]language navigation", "视觉-语言导航"),
    (r"open[- ]world", "开放世界"),
    (r"metric[- ]scale", "度量尺度"),
    (r"spatio[- ]temporal alignment", "时空对齐"),
    (r"trajectory", "轨迹"),
    (r"generation", "生成"),
    (r"detection", "检测"),
    (r"reconstruction", "重建"),
    (r"fusion", "融合"),
    (r"learning", "学习"),
    (r"training", "训练"),
    (r"rendering", "渲染"),
    (r"parallelism", "并行"),
]

# 领域上下文（标题/摘要）
_CONTEXT_HINTS: list[tuple[str, str]] = [
    (r"end[- ]to[- ]end autonomous driving", "端到端自动驾驶"),
    (r"end[- ]to[- ]end (?:driving|perception|planning|architectures)", "端到端自动驾驶"),
    (r"imitation learning.*autonomous driving|autonomous driving.*imitation learning", "端到端自动驾驶"),
    (r"autonomous driving|autonomous cars|self[- ]driving", "自动驾驶"),
    (r"imitation learning", "模仿学习"),
    (r"3d object detection|multi[- ]view 3d", "三维目标检测"),
    (r"object detection", "目标检测"),
    (r"vision[- ]language navigation|\bVLN\b", "视觉-语言导航"),
    (r"motion planning", "运动规划"),
    (r"gaussian splatting|3dgs", "三维高斯溅射"),
    (r"robot manipulation|manipulation", "机器人操作"),
    (r"humanoid", "人形机器人"),
    (r"slam|localization and mapping", "SLAM与定位"),
    (r"occupancy prediction", "占据预测"),
    (r"world model", "世界模型"),
]

_METHOD_VERBS = r"(?:propose|introduce|present|develop|design|leverage|incorporate|build|train|formulate)"

# 弱摘要检测（与 summary_llm 共享）
_WEAK_SUMMARY_RES: list[tuple[str, str]] = [
    (r"详见摘要", "placeholder"),
    (r"方法见标题", "placeholder"),
    (r"建议阅读摘要", "placeholder"),
    (r"研究工作", "placeholder"),
    (r"《[^》]+》聚焦", "book_focus"),
    (r"聚焦[^。，]{0,10}$", "focus_only"),
    (r"提出，", "empty_method"),
    (r"^提出[A-Z][A-Za-z0-9-]+[。，]", "name_only"),
    (r"^提出[A-Z][A-Za-z0-9-]+，面向[^。]{2,18}。$", "name_context_only"),
    (r"^提出[A-Z][A-Za-z0-9-]+。$", "name_period"),
    (r"针对.{2,48}提出新方法", "generic_new_method"),
    (r"提出新方法", "generic_new_method"),
    (r"相关方法[。.]?$", "xiangguan_method"),
    (r"通过改进[。.]?$", "tongguo_gaijin"),
    (r"通过改进，面向[^。]{0,12}。$", "tongguo_gaijin_only"),
    (r"^综述.{0,20}用于学习[。.]?$", "thin_survey"),
    (r"^[^：]{0,12}：[^。]{0,18}面向评估。$", "eval_only"),
    (r"^提出[A-Z][A-Za-z0-9-]+:\s*[A-Za-z]", "title_echo_en"),
    (r"：[A-Za-z][A-Za-z0-9 -]{8,}相关方法", "subtitle_echo"),
]

_SEMANTIC_MARKERS = re.compile(
    r"(解决|面向|以|用于|实现|涵盖|综述|探讨|发布|介绍|验证|提升|结合|统一|将|从|利用|学习|评估|构建|引入|桥接|恢复|扩展|质疑|指出|无需|通过.{2,}改进|通过.{2,}实现)"
)

# 知名方法名 → 固定高质量摘要（副标题/摘要解析失败时兜底）
_NAMED_PAPER_PRESETS: dict[str, str] = {
    "RT-1": "RT-1：面向大规模真实世界控制的机器人Transformer策略",
    "VR-DAgger": "VR-DAgger：以沉浸式VR采集灵巧操作演示，并用不确定性引导的在策略修正",
    "BC-Z": "BC-Z：基于大规模模仿学习实现零样本任务泛化",
    "SayCan": "SayCan：将大型语言模型语义规划与机器人物理示能结合",
    "Force Policy": "Force Policy：在交互坐标系下学习力-位混合控制策略，用于接触丰富操作",
    "ForceVLA2": "ForceVLA2：将力-位混合控制与力感知融入VLA，用于接触丰富灵巧操作",
    "RoboArena": "RoboArena：跨机构分布式真实场景评估通才机器人策略的平台",
}

# 副标题精确映射（翻译失败时的兜底）
_SUBTITLE_PRESETS: list[tuple[str, str]] = [
    (r"(?i)robotics transformer for real[- ]world control at scale", "面向大规模真实世界控制的机器人Transformer策略"),
    (r"(?i)zero[- ]shot task generalization with robotic imitation learning", "基于大规模模仿学习实现零样本任务泛化"),
    (r"(?i)immersive vr for dexterous data collection and uncertainty[- ]guided on[- ]policy correction",
     "以沉浸式VR采集灵巧操作演示，并用不确定性引导的在策略修正"),
    (r"(?i)grounding language in robotic affordances", "将大型语言模型语义规划与机器人物理示能结合"),
    (r"(?i)do world action models need test[- ]time future imagination", "探讨世界动作模型是否仍需测试时未来想象"),
    (r"(?i)an efficient action[- ]centered world[-–]action model", "高效的以动作为中心的世界-动作模型"),
    (r"(?i)world models as data engine to empower embodied ai", "将世界模型作为数据引擎赋能具身智能"),
    (r"(?i)tactile[- ]reactive dexterous manipulation", "触觉反馈驱动的灵巧操作"),
    (r"(?i)multi[- ]traversal gaussian splatting", "多趟次高斯溅射场景重建"),
    (r"(?i)lifting any 2d object detector to 3d detection", "将任意二维检测器扩展为三维检测"),
    (r"(?i)recovering the visual space from any", "从任意视图恢复视觉空间几何"),
    (r"(?i)edge[- ]aware lift[- ]splat[- ]shot framework for 3d bev", "边缘感知的Lift-Splat-Shoot鸟瞰三维检测框架"),
    (r"(?i)visual geometry transformer for autonomous driving", "面向自动驾驶的视觉几何Transformer"),
    (r"(?i)leveraging modality[- ]specific object semantics", "利用模态特定语义增强多模态融合检测"),
    (r"(?i)extracting force-informed actions from kinesthetic demonstrations for dexterous manipulation",
     "从动觉演示中提取力感知动作用于灵巧操作"),
    (r"(?i)learning hybrid force[- ]position control policy under interaction frame",
     "在交互坐标系下学习力-位混合控制策略"),
    (r"(?i)unleashing hybrid force[- ]position control with force awareness",
     "将力-位混合控制与力感知结合"),
    (r"(?i)distributed real[- ]world evaluation of generalist robot policies",
     "跨机构分布式真实场景评估通才机器人策略"),
]

# 摘要领域关键主张（世界模型 / VLA / WAM）
_ABSTRACT_DOMAIN_CLAIMS: list[tuple[str, str]] = [
    (r"(?i)whether.*test[- ]time future imagination.*(?:necessary|need)", "探讨测试时未来想象对世界动作模型的必要性"),
    (r"(?i)we ask whether wams? need explicit test[- ]time", "质疑世界动作模型是否必须依赖测试时未来想象"),
    (r"(?i)imagine[- ]then[- ]execute.*(?:latency|substantial)", "指出想象-执行范式带来显著测试延迟"),
    (r"(?i)without.*iterative video denoising|bypass.*future imagination", "无需迭代视频去噪即可实现高效动作预测"),
    (r"(?i)unified latent action", "统一潜动作表征"),
    (r"(?i)world models? as (?:a )?data engine", "将世界模型作为数据引擎生成训练数据"),
    (r"(?i)action[- ]centered world[-–]action", "以动作为中心的世界-动作联合建模"),
    (r"(?i)push(?:es)? tactile[- ]reactive manipulation into", "将触觉反馈机制引入VLA灵巧操作"),
    (r"(?i)variable[- ]rate mix[- ]of[- ]transformer", "可变速率MoT架构处理触觉时序"),
    (r"(?i)temporal tactile vq[- ]vae", "时序触觉VQ-VAE编码高频信号"),
    (r"(?i)multi[- ]traversal.*(?:novel view|reconstruction|splatting)", "利用多趟次数据提升场景重建与新视角合成"),
    (r"(?i)inherent challenges in multi[- ]traversal", "解决多趟次数据外观变化导致的重建质量下降"),
]


def _is_generic_new_method(summary: str) -> bool:
    """空泛占位：「针对X提出新方法」类句式。"""
    return bool(re.search(r"针对.{2,48}提出新方法|提出新方法", summary or ""))


def _has_semantic_marker(summary: str) -> bool:
    return bool(_SEMANTIC_MARKERS.search(summary or ""))


def _is_title_echo_in_summary(summary: str, title: str = "") -> bool:
    """摘要是否大量复述未翻译的英文副标题。"""
    if not summary:
        return False
    s = summary.strip()
    if re.search(r"相关方法[。.]?$", s):
        return True
    if re.search(r"^提出[A-Z][A-Za-z0-9-]+:\s*[A-Za-z]", s):
        return True
    _, subtitle = _title_parts(title) if title else ("", "")
    if subtitle:
        sub_words = {w for w in re.findall(r"[A-Za-z]{4,}", subtitle.lower()) if w not in {"with", "from", "that", "this", "under", "over", "into", "learning", "control", "policy", "world", "model"}}
        sum_words = set(re.findall(r"[A-Za-z]{4,}", s.lower()))
        if len(sub_words & sum_words) >= 2:
            return True
        sub_key = re.sub(r"\s+", " ", subtitle.lower())[:35]
        if sub_key and sub_key in s.lower():
            return True
    # 方法段英文占比过高（忽略 SLAM/BEV 等常见缩写）
    head = s.split("，")[0].split("。")[0]
    zh_chars = sum(1 for c in head if "\u4e00" <= c <= "\u9fff")
    latin_chars = sum(
        1 for w in re.findall(r"[A-Za-z]{3,}", head)
        if w.upper() not in {"SLAM", "BEV", "VLA", "VLM", "LLM", "DETR", "NERF", "RGB", "LIDAR", "IMU", "SAM"}
        for _ in [0]
    )
    if zh_chars < 4 and re.search(r"[A-Z][A-Za-z0-9-]+", head):
        return True
    if zh_chars >= 4 and latin_chars >= 3 and _latin_ratio(head) > 0.5:
        return True
    return False


def _is_untranslated_phrase(text: str) -> bool:
    if not text:
        return True
    if _latin_ratio(text) > 0.38:
        return True
    if re.search(r"(?i)\b(?:the|with|for|and|from|under|learning|unleashing|distributed)\b", text):
        return True
    return False


def _named_paper_preset(main: str) -> str:
    if not main:
        return ""
    key = main.strip()
    if key in _NAMED_PAPER_PRESETS:
        return _NAMED_PAPER_PRESETS[key]
    for name, preset in _NAMED_PAPER_PRESETS.items():
        if key.upper() == name.upper():
            return preset
    return ""


def is_weak_summary(summary: str, *, title: str = "") -> bool:
    """检测空泛/仅方法名/占位符摘要。"""
    if not summary or len(summary.strip()) < 8:
        return True
    s = summary.strip()
    if len(s) < 22:
        return True
    if len(s) < 25:
        if _has_semantic_marker(s) and not _is_title_echo_in_summary(s, title):
            bad = False
            for pat, _ in _WEAK_SUMMARY_RES:
                if re.search(pat, s):
                    bad = True
                    break
            if not bad and not _is_generic_new_method(s):
                return False
        return True
    if not _has_semantic_marker(s):
        return True
    for pat, _ in _WEAK_SUMMARY_RES:
        if re.search(pat, s):
            return True
    if _is_bare_name_method(s):
        return True
    if _is_generic_new_method(s):
        return True
    if _is_title_echo_in_summary(s, title):
        return True
    # 方法段几乎无中文实质
    head = s.split("，")[0].split("。")[0]
    zh_chars = sum(1 for c in head if "\u4e00" <= c <= "\u9fff")
    if zh_chars < 4 and re.search(r"[A-Z][A-Za-z0-9-]+", head):
        return True
    # 「通过改进」后无实质内容
    if re.search(r"通过改进[。.]?$", s):
        return True
    m = re.search(r"通过改进([^。，]{0,8})[，。]", s)
    if m and not m.group(1).strip():
        return True
    return False


def _is_bare_name_method(method: str) -> bool:
    """方法段是否仅为缩写名（可带「面向XX」）。"""
    if not method:
        return False
    m = re.match(
        r"^(?:提出)?([A-Z][A-Za-z0-9-]+)(?:[：:]([^，。]+))?(.*)$",
        method.strip(),
    )
    if not m:
        return False
    desc = (m.group(2) or "").strip()
    tail = (m.group(3) or "").strip()
    if desc and len(desc) >= 6 and sum(1 for c in desc if "\u4e00" <= c <= "\u9fff") >= 3:
        return False
    if not desc and not tail:
        return True
    if not desc and re.match(r"^，?面向[^。]{2,20}。?$", tail):
        return True
    if desc and _latin_ratio(desc) > 0.55:
        return True
    return False


def _ensure_method_prefix(method: str) -> str:
    if not method:
        return ""
    if re.match(r"^(提出|采用|通过|用|基于|将|引入|构建|设计|桥接)", method):
        return method
    if "：" in method:
        head = method.split("：", 1)[0]
        if _is_method_name(head) or re.match(r"^[A-Z0-9-]+$", head):
            return method
    if method.startswith("桥接"):
        return f"提出{method}"
    if method.startswith(("用", "通过", "基于")):
        return method
    return f"提出{method}"


def _extract_insight(abstract: str, title: str) -> str:
    """从摘要提取核心 insight / 观点 / 发现。"""
    if not abstract:
        return ""
    blob = _normalize_text(abstract)
    low = blob.lower()

    patterns: list[tuple[str, int]] = [
        (r"(?i)our (?:key )?insight(?:s)? (?:is|are) that?\s+(.{12,90}?)(?:\.|$)", 1),
        (r"(?i)(?:the )?(?:key|main|central) (?:idea|insight|contribution|finding) (?:is|lies in|stems from)\s+(.{12,90}?)(?:\.|$)", 1),
        (r"(?i)we (?:hypothesize|argue|contend) that?\s+(.{12,85}?)(?:\.|$)", 1),
        (r"(?i)we (?:show|find|observe|demonstrate|reveal) that?\s+(.{12,85}?)(?:\.|,|;|$)", 1),
        (r"(?i)(?:this|our approach) (?:enables|allows|suggests|reveals)\s+(.{12,80}?)(?:\.|$)", 1),
        (r"(?i)unlike (?:prior|previous|existing|conventional)\s+[^,]{5,40},\s+(?:we|our method)\s+(.{12,80}?)(?:\.|$)", 1),
        (r"(?i)the (?:core|central) (?:hypothesis|claim|premise) is that?\s+(.{12,80}?)(?:\.|$)", 1),
        (r"(?i)crucially,?\s+(.{12,80}?)(?:\.|$)", 1),
        (r"(?i)notably,?\s+(.{12,80}?)(?:\.|$)", 1),
        (r"(?i)we (?:are the )?first to (?:show|demonstrate|prove|achieve)\s+(.{12,80}?)(?:\.|$)", 1),
    ]
    for pat, grp in patterns:
        m = re.search(pat, blob)
        if m:
            frag = _translate_phrase(m.group(grp), 55)
            if frag and _latin_ratio(frag) < 0.55 and len(frag) >= 8:
                return _polish_insight(frag)

    # 第二句常含动机/对比
    sents = _sentences(blob)
    for sent in sents[1:4]:
        sl = sent.lower()
        if any(k in sl for k in ("however", "yet", "while", "although", "unlike", "existing")):
            frag = _translate_phrase(sent, 60)
            if frag and _latin_ratio(frag) < 0.5:
                return _polish_insight(frag)

    # 标题副标题中的观点性短语
    _, sub = _title_parts(title)
    if sub and re.search(r"(?i)bridging|towards|rethinking|revisiting|beyond", sub):
        zh = _translate_phrase(sub, 45)
        if zh and _latin_ratio(zh) < 0.35:
            return f"核心思路是{zh}"

    return ""


def _polish_insight(text: str) -> str:
    text = text.strip(" ，。、；")
    if not text:
        return ""
    if re.match(r"^(关键|核心|认为|表明|发现|在于|显示|区别)", text):
        return text
    return f"核心观点认为{text}"


def _normalize_text(text: str) -> str:
    """修复 PDF 抽取中的断词连字符（如 physi- cal → physical）。"""
    if not text:
        return ""
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    text = re.sub(r"of-\s+ten", "often", text, flags=re.I)
    text = re.sub(r"^[\s:：—–\-]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _zh_tags(tags: list[str], n: int = 2) -> str:
    out = [TAG_ZH.get(t, t) for t in tags[:n] if t and t != "Uncategorized"]
    return "、".join(out)


def _title_parts(title: str) -> tuple[str, str]:
    title = re.sub(r"\s+", " ", title.strip())
    for sep in (":", " - ", " – ", " — "):
        if sep in title:
            a, b = title.split(sep, 1)
            return a.strip(), b.strip()
    return title, ""


def _protect_compounds(text: str) -> tuple[str, dict[str, str]]:
    """保护连字符专有词（In-the-Wild、UMI-FT 等），避免 in/with 误译。"""
    protected: dict[str, str] = {}
    counter = 0

    def _protect(m: re.Match[str]) -> str:
        nonlocal counter
        key = f"__CP{counter}__"
        counter += 1
        protected[key] = m.group(0)
        return key

    text = re.sub(r"\b[A-Za-z][A-Za-z0-9]*(?:[-–/][A-Za-z0-9]+)+\b", _protect, text)
    return text, protected


def _restore_compounds(text: str, protected: dict[str, str]) -> str:
    for key, val in protected.items():
        text = text.replace(key, val)
    return text


def _translate_phrase(text: str, max_len: int = 40) -> str:
    """将英文片段译为可读中文短语。"""
    if not text:
        return ""
    out = re.sub(r"\s+", " ", text.strip())
    out = re.sub(
        r"(?i)^(we|this paper|this work|they|it|these|existing|prevailing|current|a|an|the)\s+",
        "",
        out,
    )
    out = re.sub(r"(?i)^(often|typically|usually|still|novel|unified|scalable)\s+", "", out)
    # Phrase rules before compound protection (e.g. tactile-reactive in T-Rex subtitle).
    for pat, zh in sorted(_PHRASE_ZH, key=lambda x: -len(x[0])):
        out = re.sub(pat, zh, out, flags=re.I)
    out, compounds = _protect_compounds(out)
    out = re.sub(r"(?i)\bwith\b", "基于", out)
    out = re.sub(r"(?i)\bvia\b", "通过", out)
    out = re.sub(r"(?i)\bfor\b", "用于", out)
    out = re.sub(r"(?i)\band\b", "与", out)
    out = re.sub(r"(?i)\bof\b", "的", out)
    out = re.sub(r"(?i)\bin\b", "于", out)
    out = re.sub(r"(?i)\bto\b", "以", out)
    out = re.sub(r"(?i)\bthe\b", "", out)
    out = _restore_compounds(out, compounds)
    out = re.sub(r"\s+", " ", out).strip(" ,-–—.")
    if len(out) > max_len:
        out = out[: max_len - 1].rsplit(" ", 1)[0]
    return out


def _latin_ratio(text: str) -> float:
    if not text:
        return 0.0
    letters = sum(1 for c in text if c.isalpha() and ord(c) < 128)
    return letters / max(len(text), 1)


def _clean_zh(text: str) -> str:
    """去掉残留英文片段，保留常见缩写。"""
    if not text:
        return ""
    keep = {
        "DETR", "DINO", "3DGS", "SLAM", "VLA", "VLM", "LLM", "NeRF", "RGB", "IMU",
        "AP", "GPU", "CPU", "CATG", "BEV", "T-Rex", "Qwen", "EgoDex", "SayCan",
        "UMI-FT", "DexUMI", "DexForce", "TacForeSight", "UMI", "Transformer",
        "Force Policy", "ForceVLA2", "RoboArena",
    }
    protected: dict[str, str] = {}
    counter = 0

    def _protect(m: re.Match[str]) -> str:
        nonlocal counter
        key = f"__PH{counter}__"
        counter += 1
        protected[key] = m.group(0)
        return key

    text = re.sub(r"《[^》]+》", _protect, text)
    text = re.sub(r"\d+%", _protect, text)
    text = re.sub(r"[A-Za-z][A-Za-z0-9]*(?:[-–/][A-Za-z0-9]+)+", _protect, text)
    text = re.sub(r"[A-Z][a-z]+(?:[A-Z][a-z0-9]*)+", _protect, text)
    text = re.sub(r"^[A-Z][A-Za-z0-9-]+(?=：)", _protect, text)
    text = re.sub(r"^([A-Z][A-Za-z0-9]+(?:[ -][A-Za-z0-9]+)*)(?=：)", _protect, text)

    def _strip_latin(seg: str) -> str:
        def repl(m: re.Match[str]) -> str:
            w = m.group(0)
            return w if w.upper() in keep or w in keep else ""
        if re.search(r"[一-龥]", seg):
            return re.sub(r"[A-Za-z]{4,}", repl, seg)
        return re.sub(r"[A-Za-z]{3,}", repl, seg)

    parts = re.split(r"([，。、；：])", text)
    cleaned: list[str] = []
    for part in parts:
        if part in "，。、；：":
            cleaned.append(part)
            continue
        if part in protected:
            cleaned.append(protected[part])
            continue
        tokens = part.split()
        zh_tokens = []
        for tok in tokens:
            bare = re.sub(r"[^\w./-]", "", tok)
            if not bare:
                continue
            if bare.upper() in keep or bare in keep or re.match(r"^\d", bare):
                zh_tokens.append(bare)
            elif re.search(r"[一-龥]", bare):
                zh_tokens.append(bare)
            elif _latin_ratio(bare) > 0.8:
                continue
            else:
                zh_tokens.append(bare)
        seg = "".join(zh_tokens) if any(re.search(r"[一-龥]", t) for t in zh_tokens) else ""
        if not seg and zh_tokens and all(
            t.upper() in keep or t in keep for t in zh_tokens
        ):
            seg = "".join(zh_tokens)
        seg = _strip_latin(seg)
        seg = re.sub(r"\s+", "", seg)
        if seg:
            cleaned.append(seg)
    out = "".join(cleaned)
    out = re.sub(r"[，、]{2,}", "，", out)
    out = re.sub(r"，。", "。", out)
    for key, val in protected.items():
        out = out.replace(key, val)
    return out.strip("，、 ")


def _infer_context(abstract: str, title: str, tags: dict) -> str:
    blob = f"{title} {abstract}".lower()
    for pat, zh in _CONTEXT_HINTS:
        if re.search(pat, blob, re.I):
            return zh
    return _context_from_tags(tags)


def _context_from_tags(tags: dict) -> str:
    topics = tags.get("topic", [])
    tasks = tags.get("task", [])
    topic_set = {t.lower() for t in topics}
    task_set = {t.lower() for t in tasks}
    if "end-to-end driving" in topic_set and "imitation learning" in (topic_set | task_set):
        return "端到端自动驾驶"
    topic = _zh_tags(topics, 2)
    task = _zh_tags(tasks, 1)
    method = _zh_tags(tags.get("method", []), 1)
    if topic:
        return topic
    if task:
        return task
    if method:
        return method
    return ""


def _is_method_name(name: str) -> bool:
    """标题冒号前是否为方法/系统名（如 DexForce、UMI-FT）。"""
    if not name or len(name) > 40:
        return False
    return bool(re.match(r"^[A-Z][A-Za-z0-9]*(?:[-–/][A-Za-z0-9]+)*$", name.strip()))


def _method_from_subtitle(subtitle: str) -> str:
    """从标题副标题提取方法描述。"""
    sub = re.sub(r"(?i)\bfor\s+.+$", "", subtitle).strip()
    sub = re.sub(r"(?i)\ba\s+(?:novel|unified|scalable)\s+", "", sub).strip()
    # 副标题仅为方法/产品名缩写时，交给摘要处理
    if re.match(r"^[A-Z0-9-]+(?:\s+with\s+[A-Z][\w\s-]+)?$", sub):
        return ""
    low = sub.lower()

    if re.search(r"(?i)learning hybrid force[- ]position control policy under interaction frame", subtitle):
        task = _translate_phrase(
            re.sub(r"(?i)^learning hybrid force[- ]position control policy under interaction frame\s*(?:for\s+)?", "", subtitle),
            18,
        )
        base = "在交互坐标系下学习力-位混合控制策略"
        if task and _latin_ratio(task) < 0.45 and "接触" in task:
            return f"{base}，用于{task}"
        return base
    if re.search(r"(?i)unleashing hybrid force[- ]position control with force awareness", subtitle):
        task = _translate_phrase(
            re.sub(r"(?i)^unleashing hybrid force[- ]position control with force awareness\s*(?:for\s+)?", "", subtitle),
            18,
        )
        base = "将力-位混合控制与力感知结合"
        if task and _latin_ratio(task) < 0.45:
            return f"{base}，用于{task}"
        return base
    if re.search(r"(?i)distributed real[- ]world evaluation of generalist robot policies", subtitle):
        return "跨机构分布式真实场景评估通才机器人策略"

    # Extracting X from Y for Z
    if re.search(r"(?i)extracting force-informed actions from kinesthetic", subtitle):
        return "从动觉演示中提取力感知动作用于策略学习"
    m = re.search(r"(?i)extracting\s+(.+?)\s+from\s+(.+?)\s+for\s+(.+)", subtitle)
    if m:
        obj = _translate_phrase(m.group(1), 22)
        src = _translate_phrase(m.group(2), 18)
        task = _translate_phrase(m.group(3), 15)
        if obj and src:
            return f"从{src}提取{obj}" + (f"，用于{task}" if task and _latin_ratio(task) < 0.45 else "")

    # Using X as Y for Z
    if re.search(r"(?i)using human hand as the universal manipulation interface", subtitle):
        return "以人手作为通用操作接口，将灵巧操作技能迁移至多种机械手"
    m = re.search(r"(?i)using\s+(.+?)\s+as\s+(?:the\s+)?(.+?)\s+for\s+(.+)", subtitle)
    if m:
        tool = _translate_phrase(m.group(1), 15)
        role = _translate_phrase(m.group(2), 22)
        task = _translate_phrase(m.group(3), 15)
        if tool and role:
            return f"以{tool}作为{role}" + (f"，实现{task}" if task and _latin_ratio(task) < 0.45 else "")

    # Tactile-Reactive Dexterous Manipulation (T-Rex and similar)
    if re.search(r"(?i)tactile[- ]reactive", sub):
        rest = re.sub(r"(?i)^tactile[- ]reactive\s+", "", sub).strip()
        tail = _translate_phrase(rest, 28).strip() if rest else ""
        if tail:
            return f"触觉反馈驱动的{tail}"
        return "触觉反馈驱动的灵巧操作策略"

    # Force-Guided / X-Guided Y for Z
    if re.search(r"(?i)force-guided tactile world model", subtitle):
        return "力引导的触觉世界模型，用于接触丰富操作"
    m = re.search(r"(?i)([\w-]+[- ]guided)\s+(.+?)\s+for\s+(.+)", subtitle)
    if m:
        obj = _translate_phrase(m.group(2), 25)
        task = _translate_phrase(m.group(3), 18)
        guide = _translate_phrase(m.group(1), 12)
        if obj:
            prefix = f"{guide}的" if guide and _latin_ratio(guide) < 0.4 else "力引导的"
            return f"{prefix}{obj}" + (f"，用于{task}" if task and _latin_ratio(task) < 0.45 else "")

    # Bridging Reasoning and Action Prediction
    m = re.search(r"(?i)bridging\s+(.+?)\s+and\s+(.+)", sub)
    if m:
        left = _translate_phrase(m.group(1), 15)
        right = _translate_phrase(m.group(2), 15)
        if left and right:
            return f"桥接{left}与{right}"

    # Unifying Vision-Language-Action Modeling across Tasks, Environments, ...
    if re.search(r"(?i)unifying vision-language-action modeling across", sub):
        return "统一跨任务、环境与机器人本体的视觉-语言-动作建模"
    m = re.search(r"(?i)unifying\s+(.+?)\s+across\s+(.+)", sub)
    if m:
        obj = _translate_phrase(m.group(1), 30)
        scope = _translate_phrase(m.group(2), 30)
        if obj:
            return f"统一{obj}" + (f"，覆盖{scope}" if scope and _latin_ratio(scope) < 0.5 else "")

    # Grounding Language in Robotic Affordances
    if re.search(r"(?i)grounding language in robotic affordances", sub):
        return "将大型语言模型的语义规划与机器人物理示能结合"
    m = re.search(r"(?i)grounding\s+(.+?)\s+in\s+(.+)", sub)
    if m:
        left = _translate_phrase(m.group(1), 18)
        right = _translate_phrase(m.group(2), 18)
        if left and right:
            return f"将{left}与{right}结合"

    # Learning Bird Eye View Representations from Multi-Camera Images
    # Learning Dexterous Manipulation from Large-Scale Egocentric Video
    if re.search(r"(?i)learning dexterous manipulation from large-scale egocentric video", sub):
        return "从大规模第一人称视频学习灵巧操作"
    m = re.search(r"(?i)learning\s+(.+?)\s+from\s+(.+)", sub)
    if m:
        obj = _translate_phrase(m.group(1), 25)
        src_raw = re.sub(r"(?i)\s+via\s+.+$", "", m.group(2)).strip()
        src = _translate_phrase(src_raw, 20)
        if obj and src:
            return f"从{src}学习{obj}"

    # DETR with Improved DeNoising Anchor Boxes
    m = re.search(r"(?i)DETR with (.+)", sub)
    if m:
        detail = _translate_phrase(m.group(1), 30)
        if detail:
            return f"通过改进{detail}增强DETR检测器"

    # Constraint-Aware Trajectory Generation with Flow Matching
    m = re.search(
        r"(?i)(constraint[- ]aware)?\s*trajectory\s+generation\s+with\s+(.+)",
        sub,
    )
    if m:
        tech = _translate_phrase(m.group(2), 20)
        prefix = "约束感知的" if m.group(1) else ""
        return f"用{prefix}{tech}生成多样化轨迹"

    # X with Y (general)
    m = re.search(r"(?i)(.+?)\s+with\s+(.+)", sub)
    if m:
        left = _translate_phrase(m.group(1), 25)
        right = _translate_phrase(m.group(2), 20)
        if left and right and _latin_ratio(left) < 0.4 and _latin_ratio(right) < 0.4:
            if "生成" in left or "generation" in m.group(1).lower():
                return f"用{right}实现{left}"
            if len(left) >= 4 and len(right) >= 2:
                return f"通过{right}改进{left}"

    # Multi-view 3D Object Detection with Sparse Spatial-Temporal Fusion
    m = re.search(r"(?i)(multi[- ]view 3d object detection)\s+with\s+(.+)", sub)
    if m:
        fusion = _translate_phrase(m.group(2), 25)
        return f"采用稀疏{fusion}实现多视角三维检测"

    desc = _subtitle_to_method_desc(sub)
    if desc:
        return desc

    zh = _translate_phrase(sub, 45)
    if zh and _latin_ratio(zh) < 0.45 and len(zh) >= 4:
        if not re.search(r"(?i)(?:\bdo\b|\bneed\b|\bfor\b|\bwith\b|\bthe\b|\ban?\b|[A-Za-z]{3,})", zh):
            return zh
    return ""


def _method_from_title(title: str) -> str:
    """整标题即方法描述时（无副标题），或标题含 with METHOD 后缀。"""
    main, subtitle = _title_parts(title)
    if subtitle:
        return ""
    m = re.search(r"(?i)(.+?)\s+with\s+([A-Z][A-Za-z0-9-]+)$", title)
    if m:
        task = _translate_phrase(m.group(1), 30)
        method = m.group(2)
        if "compliant" in m.group(1).lower() and "wild" in m.group(1).lower():
            return f"{method}手持柔顺操作数据采集平台"
        if task and _latin_ratio(task) < 0.35:
            return f"{method}：面向{task}"
        return f"{method}数据采集与策略学习平台"
    zh = _translate_phrase(title, 50)
    if zh and _latin_ratio(zh) < 0.2 and len(zh) >= 6:
        if re.search(r"(?i)self[- ]supervised", title):
            return f"采用{zh}"
        return zh
    return ""


def _subtitle_to_method_desc(subtitle: str) -> str:
    """副标题 → 方法描述（含预设与结构化解析）。"""
    if not subtitle:
        return ""
    sub = subtitle.strip()
    for pat, zh in _SUBTITLE_PRESETS:
        if re.search(pat, sub):
            return zh

    # 疑问式副标题：Do X Need Y?
    m = re.search(r"(?i)^do\s+(.+?)\s+need\s+(.+?)\??$", sub)
    if m:
        topic = _translate_phrase(m.group(1), 28)
        need = _translate_phrase(m.group(2), 28)
        if topic and need and _latin_ratio(topic) < 0.5:
            return f"探讨{topic}是否需要{need}"

    # An Efficient X / A Unified X
    m = re.search(r"(?i)^an?\s+(?:efficient|unified|scalable|novel)\s+(.+)$", sub)
    if m:
        core = _translate_phrase(m.group(1), 40)
        if core and _latin_ratio(core) < 0.45 and len(core) >= 4:
            qual = "高效" if "efficient" in sub.lower() else ""
            return f"{qual}{core}" if qual else core

    # X as Y to/for Z
    m = re.search(r"(?i)^(.+?)\s+as\s+(?:a\s+)?(.+?)\s+(?:to|for)\s+(.+)$", sub)
    if m:
        left = _translate_phrase(m.group(1), 18)
        role = _translate_phrase(m.group(2), 18)
        goal = _translate_phrase(m.group(3), 18)
        if left and role and _latin_ratio(left) < 0.5:
            s = f"将{left}作为{role}"
            if goal and _latin_ratio(goal) < 0.5:
                s += f"以{goal}"
            return s

    # Lifting X to Y
    m = re.search(r"(?i)^lifting\s+(?:any\s+)?(.+?)\s+to\s+(.+)$", sub)
    if m:
        src = _translate_phrase(m.group(1), 22)
        dst = _translate_phrase(m.group(2), 22)
        if src and dst and _latin_ratio(src) < 0.5:
            return f"将{src}扩展至{dst}"

    # Leveraging X for Y
    m = re.search(r"(?i)^leveraging\s+(.+?)\s+for\s+(.+)$", sub)
    if m:
        src = _translate_phrase(m.group(1), 25)
        dst = _translate_phrase(m.group(2), 22)
        if src and dst and _latin_ratio(src) < 0.5:
            return f"利用{src}实现{dst}"

    # Recovering / Learning / Towards X
    m = re.search(r"(?i)^(recovering|learning|towards?)\s+(.+)$", sub)
    if m:
        verb = {"recovering": "恢复", "learning": "学习", "toward": "面向", "towards": "面向"}.get(
            m.group(1).lower(), m.group(1)
        )
        obj = _translate_phrase(m.group(2), 35)
        if obj and _latin_ratio(obj) < 0.5:
            return f"{verb}{obj}"

    # Framework / Model for X
    m = re.search(r"(?i)^(.+?)\s+(?:framework|model|approach|method)\s+for\s+(.+)$", sub)
    if m:
        core = _translate_phrase(m.group(1), 25)
        task = _translate_phrase(m.group(2), 22)
        if core and task and _latin_ratio(core) < 0.5:
            return f"{core}框架用于{task}"

    return ""


def _abstract_domain_claim(abstract: str, main: str = "") -> str:
    """从摘要提取世界模型/VLA/WAM等领域关键主张。"""
    if not abstract:
        return ""
    for pat, zh in _ABSTRACT_DOMAIN_CLAIMS:
        if re.search(pat, abstract):
            return zh
    # 首两句通用贡献句
    for sent in _sentences(abstract)[:2]:
        sl = sent.lower()
        if re.search(r"(?i)^(world action models|wams?|vision[- ]language[- ]action)", sl):
            frag = _translate_phrase(sent, 55)
            if frag and _latin_ratio(frag) < 0.5 and len(frag) >= 10:
                return frag
        m = re.search(
            rf"(?i)\b(?:we|this paper)\s+({_METHOD_VERBS})\s+(.{{8,80}}?)(?:\.|,|$)",
            sent,
        )
        if m:
            frag = _translate_phrase(m.group(2), 50)
            if frag and _latin_ratio(frag) < 0.5 and len(frag) >= 8:
                return frag
    return ""


def _method_from_named_title(main: str, subtitle: str, abstract: str = "") -> str:
    """标题为「方法名: 描述」时，组合方法名与副标题/摘要语义。绝不只返回方法名。"""
    if not _is_method_name(main) or not subtitle:
        return ""
    desc = _subtitle_to_method_desc(subtitle) or _method_from_subtitle(subtitle)
    if not desc and abstract:
        desc = _abstract_domain_claim(abstract, main)
    if desc:
        return f"{main}：{desc}"
    zh = _translate_phrase(subtitle, 45)
    if zh and _latin_ratio(zh) < 0.45 and len(zh) >= 6:
        return f"{main}：{zh}"
    if abstract:
        claim = _abstract_domain_claim(abstract, main)
        if claim:
            return f"{main}：{claim}"
    return ""


def _tactile_vla_abstract_stack(abstract: str) -> str:
    """从触觉反馈 VLA 摘要提取 MoT / VQ-VAE / 数据集等核心组件。"""
    if not abstract or not re.search(r"(?i)tactile", abstract):
        return ""
    parts: list[str] = []
    if re.search(r"(?i)100[- ]hour|large[- ]scale.*tactile|tactile[- ]rich dataset", abstract):
        parts.append("百小时触觉数据集")
    if re.search(r"(?i)egocentric|motor prim", abstract):
        parts.append("基础运动原语采集")
    if re.search(r"(?i)variable[- ]rate mix[- ]of[- ]transformer|mix[- ]of[- ]transformer", abstract):
        parts.append("可变速率MoT架构")
    if re.search(r"(?i)temporal tactile vq[- ]vae|tactile vq[- ]vae", abstract):
        parts.append("时序触觉VQ-VAE编码器")
    return "与".join(parts)


def _enrich_named_method(method: str, abstract: str) -> str:
    """将摘要中的架构/数据细节并入「方法名：描述」式提取结果。"""
    if not method or "：" not in method:
        return method
    name, desc = method.split("：", 1)
    stack = _tactile_vla_abstract_stack(abstract)
    if stack and stack not in method:
        return f"{name}：{stack}，实现{desc.rstrip('。')}"
    return method


def _extract_method(abstract: str, title: str) -> str:
    """提取核心方法/贡献。"""
    main, subtitle = _title_parts(title)
    if subtitle and _is_method_name(main):
        m = _method_from_named_title(main, subtitle, abstract)
        if m:
            return _enrich_named_method(m, abstract)
    if subtitle:
        m = _subtitle_to_method_desc(subtitle) or _method_from_subtitle(subtitle)
        if m:
            if _is_method_name(main):
                return _enrich_named_method(f"{main}：{m}", abstract)
            return m
    else:
        m = _method_from_title(title)
        if m:
            return m

    claim = _abstract_domain_claim(abstract, main if _is_method_name(main) else "")
    if claim:
        if _is_method_name(main):
            return _enrich_named_method(f"{main}：{claim}", abstract)
        return claim

    low_all = (abstract or "").lower()
    if re.search(r"(?i)tactile[- ]reactive", abstract or "") and re.search(
        r"(?i)mix[- ]of[- ]transformer|vq[- ]vae|variable[- ]rate", abstract or ""
    ):
        stack = _tactile_vla_abstract_stack(abstract)
        if stack:
            name = main if subtitle and _is_method_name(main) else "该方法"
            return f"{name}：{stack}"

    if "denois" in low_all and "contrastive" in low_all:
        return "对比去噪训练、混合查询选择与双向前向预测增强DETR检测器"

    for sent in _sentences(abstract):
        low = sent.lower()

        if "denois" in low and "contrastive" in low:
            return "对比去噪训练、混合查询选择与双向前向预测增强DETR检测器"

        # We propose / introduce NAME[, .] (a ...) ...
        m = re.search(
            r"(?i)\bwe\s+(?:propose|introduce|present)\s+([A-Za-z0-9-]+)"
            r"(?:,\s*(?:a|an)\s+(.+?)|\.\s*(?:\1\s+)?(.+?))(?:\.|,|$)",
            sent,
        )
        if m:
            name = m.group(1)
            desc = (m.group(2) or m.group(3) or "").strip()
            if desc:
                desc = re.sub(rf"(?i)^{re.escape(name)}\s+", "", desc)
                tech = _translate_phrase(desc.split(".")[0], 40)
                if tech and _latin_ratio(tech) < 0.55:
                    return f"{name}：{tech}"
            # 绝不单独返回方法名
            if _is_method_name(name) and subtitle:
                sub_desc = _method_from_subtitle(subtitle) or _subtitle_to_method_desc(subtitle)
                if sub_desc:
                    return f"{name}：{sub_desc}"
            continue

        m = re.search(r"(?i)\bwe propose\s+([A-Za-z0-9-]+),\s*(?:a|an)\s+(.+?)(?:\.|,|$)", sent)
        if m:
            tech = _translate_phrase(m.group(2), 35)
            if tech and _latin_ratio(tech) < 0.5:
                return f"{m.group(1)}：{tech}方法"

        # We present / introduce NAME, a ...
        m = re.search(
            rf"(?i)\b(?:we|this paper)\s+({_METHOD_VERBS})\s+(.{{5,70}}?)(?:\.|,|—|-)",
            sent,
        )
        if m:
            verb, rest = m.group(1).lower(), m.group(2)
            rest = re.sub(r"(?i),?\s*a (?:novel|unified|scalable|simple|efficient|lightweight)\s+", " ", rest)
            rest = re.sub(r"(?i)^(?:an?|the)\s+", "", rest)
            head = re.split(r"[,.]", rest)[0]
            zh = _translate_phrase(head, 50)
            if zh and _latin_ratio(zh) < 0.4 and len(zh) >= 6:
                if verb in ("introduce", "present", "propose"):
                    return zh
                if not _is_untranslated_phrase(zh):
                    return f"通过{zh}实现改进"

        if "sparse spatial" in low and "fusion" in low:
            return "稀疏时空融合的多视角三维检测框架"
        if not re.search(rf"(?i)\b(we|this paper|this work|improves?)\b", sent):
            continue
        if re.search(r"(?i)\bby using\b", sent):
            m2 = re.search(r"(?i)by using\s+(.+?)(?:\.|,|and achieves)", sent)
            if m2:
                zh = _translate_phrase(m2.group(1), 45)
                if zh and _latin_ratio(zh) < 0.35:
                    return f"基于{zh}的方法"
        sent_clean = re.sub(
            rf"(?i)^.*?\b({_METHOD_VERBS})\s+",
            "",
            sent,
        )
        sent_clean = re.sub(r"(?i), a (?:state-of-the-art|novel|unified|scalable)\s+", "，", sent_clean)
        sent_clean = re.sub(r"(?i)^(?:an?|the)\s+", "", sent_clean)
        head = re.split(r"[,.]", sent_clean)[0]
        zh = _translate_phrase(head, 50)
        if zh and _latin_ratio(zh) < 0.35:
            return zh

    return ""


def _extract_problems(abstract: str) -> list[str]:
    """从摘要提取问题/挑战列表。"""
    if not abstract:
        return []
    low = abstract.lower()
    found: list[str] = []

    checks: list[tuple[str, str]] = [
        (r"mode collapse", "模式坍塌"),
        (r"fail(?:ing)? to produce diverse", "轨迹多样性不足"),
        (r"struggle(?:s)? to incorporate.*(?:safety|physi[- ]?cal) constraint", "安全关键场景规划不足"),
        (r"ignore high[- ]frequency", "忽视高频触觉反馈"),
        (r"existing policies ignore", "现有策略忽视触觉信号"),
        (r"overlook the tactile modality|limited to encoders with static cues", "VLA忽视触觉模态或仅用静态触觉编码"),
        (r"scarcity of diverse training data|scarcity of.*training data", "缺乏多样化触觉训练数据"),
        (r"limitations of static tactile encoders?", "静态触觉编码器难以捕捉高频信号"),
        (r"tactile feedback is essential", "触觉反馈不可或缺"),
        (r"essential for in[- ]the[- ]wild", "对真实场景至关重要"),
        (r"necessitating an additional optimization", "需额外优化阶段"),
        (r"suffer(?:s)? from\s+(.{5,50}?)(?:\.|,|$)", ""),
        (r"remain(?:s)? brittle", "长尾场景下表现脆弱"),
        (r"supervision is sparse|sparse supervision", "监督信号稀疏"),
        (r"performance and efficiency", "精度与训练效率不足"),
        (r"complex dynamics|dynamic driving scenes", "动态场景实时重建困难"),
        (r"intercity highways|long[- ]distance highway", "城际高速远距感知不足"),
        (r"perception distances of at least", "远距感知距离不足"),
        (r"spatio[- ]temporal alignment", "时空对齐不一致"),
        (r"cross[- ]embodiment|different sensor", "跨传感器/具身数据迁移困难"),
        (r"robust training and validation.*require massive", "缺乏大规模多样化数据"),
        (r"real[- ]time.*(?:challenged|difficult)", "实时性与保真度难以兼顾"),
        (r"high[- ]quality demonstr", "缺乏高质量演示数据"),
        (r"lack of direct haptic feedback", "缺乏直接触觉反馈"),
        (r"unintuitive human[- ]to[- ]robot motion retargeting", "人机运动重定向不直观"),
        (r"force/torque \(F/T\) sensors have limited", "力/力矩传感器成本高且易损"),
        (r"commercial force/torque", "商用力矩传感器限制大规模力控学习"),
        (r"careful force modulation", "操作需精细力调节"),
        (r"rarely model the asymmetric", "未建模全局力与局部触觉的不对称作用"),
        (r"embodiment gap", "人机具身差异大"),
        (r"contact[- ]rich manipulation requires", "接触丰富操作需持续感知与调节交互力"),
    ]
    for pat, zh in checks:
        if re.search(pat, low, re.I):
            if zh:
                if zh not in found:
                    found.append(zh)
            else:
                m = re.search(pat, low, re.I)
                if m and m.lastindex:
                    frag = _translate_phrase(m.group(1), 25)
                    if frag and "模式坍塌" in found:
                        continue
                    if frag:
                        found.append(f"存在{frag}问题")

    # however / yet 从句
    if not found:
        for pat in (r"however,?\s+(.{12,70}?)(?:\.|,|$)", r"yet\s+(.{12,70}?)(?:\.|,|$)"):
            m = re.search(pat, low, re.I)
            if m:
                frag = _translate_phrase(m.group(1), 35)
                if frag and _latin_ratio(frag) < 0.5:
                    found.append(frag)
                    break

    if "necessitating an additional optimization" in low:
        found.append("需额外优化才能满足安全约束")

    return found[:3]


def _dedupe_problems(problems: list[str]) -> list[str]:
    """合并语义重复的问题描述。"""
    if "模式坍塌" in problems:
        problems = [p for p in problems if p not in ("轨迹多样性不足", "存在模式坍塌问题")]
    if "轨迹多样性不足" in problems and "模式坍塌" in problems:
        problems = [p for p in problems if p != "轨迹多样性不足"]
    # 去掉包含关系重复
    out: list[str] = []
    for p in problems:
        if any(p != q and p in q for q in problems):
            continue
        if p not in out:
            out.append(p)
    return out


def _extract_benefit(abstract: str) -> str:
    if not abstract:
        return ""
    patterns: list[str | tuple[str, str]] = [
        (r"(?i)achieving over (\d+)% higher (?:average )?success rate", "平均成功率较基线提升{}%以上"),
        (r"(?i)achiev(?:e|es|ing) over (\d+)% higher", "较基线提升{}%以上"),
        r"(?i)(?:achiev(?:e|es|ing)|enabl(?:e|es|ing)|improv(?:e|es|ing)|enhanc(?:e|es|ing)|"
        r"outperform(?:s|ing)?)\s+(.{8,55}?)(?:\.|,|$)",
        r"(?i)yield(?:s|ing)?\s+(?:a )?(?:significant )?(.{8,50}?)(?:\.|,|$)",
        r"(?i)result(?:s|ing)? in\s+(.{8,50}?)(?:\.|,|$)",
    ]
    for pat in patterns:
        if isinstance(pat, tuple):
            regex, template = pat
            m = re.search(regex, abstract)
            if m:
                return template.format(m.group(1))
            continue
        m = re.search(pat, abstract)
        if m:
            zh = _translate_phrase(m.group(1), 35)
            if zh and _latin_ratio(zh) < 0.4 and not re.search(r"(?i)^\d", zh):
                return zh
    return ""


def _extract_novelty(abstract: str) -> str:
    """提取与已有方法的不同之处。"""
    if not abstract:
        return ""
    m = re.search(
        r"(?i)(?:in contrast to|compared to|different from|unlike)\s+(.{8,45}?),\s+(.{15,70}?)(?:\.|$)",
        abstract,
    )
    if m:
        diff = _translate_phrase(m.group(2), 50)
        if diff and _latin_ratio(diff) < 0.45:
            return f"区别于既有方案，{diff}"
    return ""


def _sentences(text: str) -> list[str]:
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 8]


def _join_problems(problems: list[str]) -> str:
    if not problems:
        return ""
    deduped: list[str] = []
    for p in problems:
        if any(p in d or d in p for d in deduped):
            continue
        if p == "轨迹多样性不足" and any("模式坍塌" in d for d in deduped):
            continue
        if p == "安全关键场景规划不足" and any("长尾" in d for d in deduped):
            continue
        if p == "长尾场景下表现脆弱" and any("安全关键" in d for d in deduped):
            continue
        if p == "监督信号稀疏" and any("长尾" in d for d in deduped):
            continue
        deduped.append(p)
    if len(deduped) == 1:
        return deduped[0]
    return "与".join(deduped[:2]) + ("等问题" if len(deduped) > 2 else "")


def _compose(method: str, problems: list[str], insight: str, benefit: str, context: str) -> str:
    """组装：方法 + 问题 + insight（一句或分号连接的两句）。"""
    prob = _join_problems(problems)
    if method and _is_bare_name_method(method):
        method = ""
    method = _ensure_method_prefix(method) if method else ""
    if method and _is_bare_name_method(method):
        method = ""

    clauses: list[str] = []

    # 主句：方法 + 问题
    if method and prob:
        if context and context not in method:
            clauses.append(f"{method}，以解决{context}中{prob}。")
        else:
            clauses.append(f"{method}，以解决{prob}。")
    elif method and context and not _is_bare_name_method(method):
        clauses.append(f"{method}，面向{context}。")
    elif method:
        clauses.append(f"{method}。")
    elif prob:
        # 禁止空泛「针对X提出新方法」；交由 _title_fallback / _hard_fallback
        pass

    # insight / 观点
    ins = insight
    if not ins and prob and "需额外优化" in prob:
        ins = "仅靠模仿学习难以同时满足安全约束，需显式生成多样化轨迹"
    if not ins and benefit:
        ins = f"实验验证可{benefit}"

    if ins:
        ins = ins.rstrip("。")
        if not re.match(r"^(关键|核心|区别于|实验|主要)", ins):
            ins = f"核心观点：{ins}"
        # 去掉 insight 中重复的方法/问题措辞
        if method and method[:8] in ins:
            ins = re.sub(r"^核心观点：", "进一步认为：", ins)
        clauses.append(f"{ins}。")

    if not clauses:
        return ""

    text = "".join(clauses)
    if len(clauses) == 1 and benefit and benefit not in text and len(text) < 100:
        text = text.rstrip("。") + f"，{benefit}。"
    return text


def _survey_summary(title: str, abstract: str = "") -> str | None:
    m = re.search(r"(?i)methods for (.+) in (.+)", title)
    if m:
        topic = f"{_translate_phrase(m.group(2))}中的{_translate_phrase(m.group(1))}"
        scope = _survey_scope_from_abstract(abstract)
        if scope:
            return f"综述{topic}，涵盖{scope}。"
        return f"综述{topic}。"
    low = title.lower()
    if re.search(r"\b(survey|review|overview)\b", low):
        main, sub = _title_parts(title)
        if sub and re.search(r"(?i)(survey|review|overview)", sub):
            topic = _survey_topic_from_main(main)
        else:
            topic_raw = re.sub(r"(?i).*(survey|review|overview)\s*(of|on|about|for)?\s*", "", title)
            topic = _survey_topic_from_main(topic_raw or main)
        scope = _survey_scope_from_abstract(abstract)
        if scope:
            return f"综述{topic}，涵盖{scope}。"
        return f"综述{topic}。"
    if re.search(r"\b(benchmark|dataset)\b", low):
        return f"发布{_translate_phrase(title, 50)}基准或数据集。"
    if re.search(r"\b(challenge|workshop|competition)\b", low):
        return f"介绍{_translate_phrase(title, 50)}竞赛或挑战。"
    return None


def _survey_topic_from_main(main: str) -> str:
    if re.search(r"(?i)world model", main):
        if re.search(r"(?i)robot learning|robotic", main):
            return "机器人学习中的世界模型"
        if re.search(r"(?i)vision", main):
            return "视觉世界模型"
        return "世界模型"
    topic = _translate_phrase(main, 40)
    if topic and _latin_ratio(topic) < 0.35:
        return topic
    return main.strip() or "相关领域"


def _survey_scope_from_abstract(abstract: str) -> str:
    if not abstract:
        return ""
    sents = _sentences(_normalize_text(abstract))
    if not sents:
        return ""
    first = sents[0]
    # 去掉定义从句后的核心范围
    scope_bits: list[str] = []
    if re.search(r"(?i)world model", first):
        scope_bits.append("环境动力学的预测表征")
    if re.search(r"(?i)policy learning|planning|simulation|evaluation|data generation", abstract):
        scope_bits.extend(["策略学习", "规划", "仿真", "评估与数据生成"])
    if scope_bits:
        return "、".join(dict.fromkeys(scope_bits))
    scope = _translate_phrase(first, 55)
    if scope and _latin_ratio(scope) < 0.35 and len(scope) >= 8:
        return scope.rstrip("。")
    return ""


def _abstract_snippet_fallback(abstract: str, context: str) -> str:
    """从摘要首句提取可读内容，替代空泛 fallback。"""
    if not abstract:
        return ""
    sents = _sentences(_normalize_text(abstract))
    for sent in sents[:4]:
        sl = sent.lower()
        for pat in (
            r"(?i)\bwe propose\s+([A-Za-z0-9-]+),?\s*(?:a|an)\s+(.+?)(?:\.|,|$)",
            r"(?i)\bwe (?:present|introduce)\s+([A-Za-z0-9-]+),?\s*(?:a|an)?\s*(.+?)(?:\.|,|$)",
            r"(?i)\bwe (?:present|introduce)\s+([A-Za-z0-9-]+)(?:\.|,|$)",
        ):
            m = re.search(pat, sent)
            if m:
                name = m.group(1)
                desc = (m.group(2) if m.lastindex and m.lastindex >= 2 else "").strip()
                if desc:
                    frag = _translate_phrase(desc.split(".")[0], 50)
                    if frag and _latin_ratio(frag) < 0.5 and len(frag) >= 6:
                        return f"{name}：{frag}"
                preset = _named_paper_preset(name)
                if preset:
                    return preset
        if re.search(r"(?i)^(we|this paper|this work|in this)", sl):
            m = re.search(
                rf"(?i)\b(?:we|this paper)\s+({_METHOD_VERBS})\s+(.+)",
                sent,
            )
            if m:
                frag = _translate_phrase(m.group(2).split(".")[0], 55)
                if frag and _latin_ratio(frag) < 0.5 and len(frag) >= 8:
                    return _ensure_method_prefix(frag)
        frag = _translate_phrase(sent, 60)
        if frag and _latin_ratio(frag) < 0.45 and len(frag) >= 10:
            if context and context not in frag:
                return f"针对{context}，{frag}"
            return frag
    return ""


def _hard_fallback(title: str, abstract: str, tags: dict, context: str) -> str:
    """最终兜底：确保有标题时绝不返回空字符串或空泛占位。"""
    main, subtitle = _title_parts(title)
    preset = _named_paper_preset(main)
    if preset:
        return preset

    special = _survey_summary(title, abstract)
    if special and not is_weak_summary(special, title=title):
        return special

    snippet = _abstract_snippet_fallback(abstract, context)
    if snippet and not is_weak_summary(snippet, title=title):
        if _is_method_name(main) and "：" not in snippet and not snippet.startswith(main):
            return f"{main}：{snippet.lstrip('提出')}"
        return snippet if snippet.endswith("。") else f"{snippet.rstrip('。')}。"

    desc = ""
    if subtitle:
        desc = _subtitle_to_method_desc(subtitle) or _method_from_subtitle(subtitle)
    if not desc and abstract:
        desc = _abstract_domain_claim(abstract, main if _is_method_name(main) else "")
    if desc and not _is_untranslated_phrase(desc):
        if _is_method_name(main):
            body = f"{main}：{desc}"
        else:
            body = _ensure_method_prefix(desc)
        if context and context not in body:
            return f"{body}，面向{context}。"
        return f"{body}。"

    zh = _translate_phrase(subtitle or title, 55)
    if zh and not _is_untranslated_phrase(zh):
        body = f"{main}：{zh}" if _is_method_name(main) else _ensure_method_prefix(zh)
        if context and context not in body:
            return f"{body.rstrip('。')}，面向{context}。"
        return f"{body.rstrip('。')}。"

    ctx = context or _context_from_tags(tags) or "该领域"
    if abstract:
        for sent in _sentences(_normalize_text(abstract))[:2]:
            frag = _translate_phrase(sent, 72)
            if frag and len(frag) >= 10 and not _is_untranslated_phrase(frag):
                body = f"{main}：{frag}" if _is_method_name(main) else _ensure_method_prefix(frag)
                if ctx and ctx not in body:
                    body = f"{body.rstrip('。')}，面向{ctx}。"
                else:
                    body = f"{body.rstrip('。')}。"
                if not is_weak_summary(body, title=title):
                    return body

    if _is_method_name(main):
        sub_desc = (_subtitle_to_method_desc(subtitle) or _method_from_subtitle(subtitle)) if subtitle else ""
        if sub_desc and not _is_untranslated_phrase(sub_desc):
            return f"{main}：{sub_desc}，面向{ctx}。"
        return f"{main}：面向{ctx}场景的方法与系统研究工作。"

    focus = _translate_phrase(subtitle or title, 45)
    if focus and not _is_untranslated_phrase(focus):
        return f"面向{ctx}，提出{focus.rstrip('。')}。"
    return f"面向{ctx}，围绕{main or '该主题'}开展方法与系统研究。"


def _title_fallback(title: str, tags: dict, abstract: str) -> str:
    ctx = _infer_context(abstract, title, tags)
    main, subtitle = _title_parts(title)
    method = _extract_method(abstract, title)
    if not method and subtitle and _is_method_name(main):
        method = _method_from_named_title(main, subtitle, abstract)
    if not method and subtitle:
        method = _method_from_subtitle(subtitle) or _subtitle_to_method_desc(subtitle)
        if method and _is_method_name(main):
            method = f"{main}：{method}"
    if not method:
        method = _method_from_title(title)
    if not method:
        method = _abstract_domain_claim(abstract, main if _is_method_name(main) else "")
        if method and _is_method_name(main):
            method = f"{main}：{method}"
    insight = _extract_insight(abstract, title)
    problems = _dedupe_problems(_extract_problems(abstract))

    if method and not _is_bare_name_method(method):
        method = _ensure_method_prefix(method)
        if _is_bare_name_method(method):
            method = ""
    if method:
        prob = _join_problems(problems)
        parts = [f"{method}，以解决{prob}。" if prob else f"{method}。"]
        if insight:
            parts.append(f"{insight.rstrip('。')}。")
        out = "".join(parts)
        if not is_weak_summary(out, title=title):
            return out

    snippet = _abstract_snippet_fallback(abstract, ctx)
    if snippet and not is_weak_summary(snippet, title=title):
        ins = insight or _extract_benefit(abstract)
        if ins:
            return f"{snippet.rstrip('。')}。{ins.rstrip('。')}。"
        return f"{snippet.rstrip('。')}。"

    if ctx and insight:
        return f"针对{ctx}，{insight.rstrip('。')}。"
    if subtitle:
        desc = _subtitle_to_method_desc(subtitle) or _method_from_subtitle(subtitle)
        if desc:
            head = f"{main}：" if _is_method_name(main) else "提出"
            return f"{head}{desc}，面向{ctx}。" if ctx else f"{head}{desc}。"
    return ""


def summarize_zh(paper: dict) -> str:
    """生成中文总结：方法 + 问题 + insight。"""
    title = (paper.get("title") or paper.get("stem") or "").strip()
    abstract = _normalize_text((paper.get("abstract") or "").strip())
    tags = paper.get("tags") or {}

    special = _survey_summary(title, abstract)
    if special:
        s = _clean_zh(special[:160])
        if not is_weak_summary(s, title=title):
            return s

    main, _subtitle = _title_parts(title)
    preset = _named_paper_preset(main)
    if preset:
        s = _clean_zh(preset[:160])
        if not is_weak_summary(s, title=title):
            return s

    context = _infer_context(abstract, title, tags)
    method = _extract_method(abstract, title)
    if method and (_is_bare_name_method(method) or _is_untranslated_phrase(method.split("：", 1)[-1])):
        method = ""
    problems = _dedupe_problems(_extract_problems(abstract))
    insight = _extract_insight(abstract, title) or _extract_novelty(abstract)
    benefit = _extract_benefit(abstract)

    s = _compose(method, problems, insight, benefit, context)
    if not s or is_weak_summary(s, title=title):
        s = _title_fallback(title, tags, abstract)
    elif _latin_ratio(s) > 0.38 and is_weak_summary(s, title=title):
        s = _title_fallback(title, tags, abstract)

    raw = s
    s = _clean_zh(s)
    if s and is_weak_summary(s, title=title) and raw and not is_weak_summary(raw, title=title):
        s = raw

    if not s or is_weak_summary(s, title=title):
        ctx = context or _infer_context(abstract, title, tags)
        snippet = _abstract_snippet_fallback(abstract, ctx)
        if snippet and not is_weak_summary(snippet, title=title):
            s = snippet
        elif ctx:
            main, subtitle = _title_parts(title)
            desc = _subtitle_to_method_desc(subtitle) if subtitle else ""
            if desc and not _is_untranslated_phrase(desc):
                prefix = f"{main}：" if _is_method_name(main) else ""
                s = f"提出{prefix}{desc}，面向{ctx}。"
            elif insight:
                s = f"针对{ctx}，{insight.rstrip('。')}。"

    if s and is_weak_summary(s, title=title):
        alt = _title_fallback(title, tags, abstract)
        if alt and not is_weak_summary(alt, title=title):
            s = alt

    if not s or is_weak_summary(s, title=title):
        s = _hard_fallback(title, abstract, tags, context)

    cleaned = _clean_zh(s)
    if cleaned and not is_weak_summary(cleaned, title=title):
        s = cleaned
    elif s and is_weak_summary(_clean_zh(s), title=title) and not is_weak_summary(s, title=title):
        pass

    if len(s) > 160:
        s = s[:157] + "…。"
    return s or ""


def add_summaries(papers: list[dict]) -> None:
    """为每篇论文写入 summary_zh 字段。"""
    for p in papers:
        p["summary_zh"] = summarize_zh(p)
