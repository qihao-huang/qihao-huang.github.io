"""
summary_zh.py — 为每篇论文生成一句中文总结（离线，基于标题+摘要+标签）。
聚焦「解决什么问题」与「核心方法/想法」，避免机械复述标题。
"""

from __future__ import annotations
import re

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
    (r"denoising training", "去噪训练"),
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
    (r"imitation learning.*autonomous driving|autonomous driving.*imitation learning", "端到端模仿学习"),
    (r"end[- ]to[- ]end autonomous driving", "端到端自动驾驶"),
    (r"end[- ]to[- ]end (?:driving|perception|planning|architectures)", "端到端自动驾驶"),
    (r"imitation learning", "模仿学习"),
    (r"autonomous driving|autonomous cars|self[- ]driving", "自动驾驶"),
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

_METHOD_VERBS = r"(?:propose|introduce|present|develop|design|leverage|incorporate|build|train)"


def _normalize_text(text: str) -> str:
    """修复 PDF 抽取中的断词连字符（如 physi- cal → physical）。"""
    if not text:
        return ""
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    text = re.sub(r"of-\s+ten", "often", text, flags=re.I)
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
    for pat, zh in sorted(_PHRASE_ZH, key=lambda x: -len(x[0])):
        out = re.sub(pat, zh, out, flags=re.I)
    out = re.sub(r"(?i)\bwith\b", "基于", out)
    out = re.sub(r"(?i)\bvia\b", "通过", out)
    out = re.sub(r"(?i)\bfor\b", "用于", out)
    out = re.sub(r"(?i)\band\b", "与", out)
    out = re.sub(r"(?i)\bof\b", "的", out)
    out = re.sub(r"(?i)\bin\b", "于", out)
    out = re.sub(r"(?i)\bto\b", "以", out)
    out = re.sub(r"(?i)\bthe\b", "", out)
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
    keep = {"DETR", "3DGS", "SLAM", "VLA", "VLM", "LLM", "NeRF", "RGB", "IMU", "AP", "GPU", "CPU", "CATG", "BEV"}

    def _strip_latin(seg: str) -> str:
        def repl(m: re.Match[str]) -> str:
            w = m.group(0)
            return w if w.upper() in keep else ""
        if re.search(r"[一-龥]", seg):
            return re.sub(r"[A-Za-z]{4,}", repl, seg)
        return re.sub(r"[A-Za-z]{3,}", repl, seg)

    parts = re.split(r"([，。、；：])", text)
    cleaned: list[str] = []
    for part in parts:
        if part in "，。、；：":
            cleaned.append(part)
            continue
        tokens = part.split()
        zh_tokens = []
        for tok in tokens:
            bare = re.sub(r"[^\w./-]", "", tok)
            if not bare:
                continue
            if bare.upper() in keep or re.match(r"^\d", bare):
                zh_tokens.append(bare)
            elif re.search(r"[一-龥]", bare):
                zh_tokens.append(bare)
            elif _latin_ratio(bare) > 0.8:
                continue
            else:
                zh_tokens.append(bare)
        seg = "".join(zh_tokens) if any(re.search(r"[一-龥]", t) for t in zh_tokens) else ""
        seg = _strip_latin(seg)
        seg = re.sub(r"\s+", "", seg)
        if seg:
            cleaned.append(seg)
    out = "".join(cleaned)
    out = re.sub(r"[，、]{2,}", "，", out)
    out = re.sub(r"，。", "。", out)
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
        return "端到端模仿学习"
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


def _method_from_subtitle(subtitle: str) -> str:
    """从标题副标题提取方法描述。"""
    sub = re.sub(r"(?i)\bfor\s+.+$", "", subtitle).strip()
    sub = re.sub(r"(?i)\ba\s+(?:novel|unified|scalable)\s+", "", sub).strip()
    # 副标题仅为方法/产品名缩写时，交给摘要处理
    if re.match(r"^[A-Z0-9-]+(?:\s+with\s+[A-Z][\w\s-]+)?$", sub):
        return ""
    low = sub.lower()

    # Bridging Reasoning and Action Prediction
    m = re.search(r"(?i)bridging\s+(.+?)\s+and\s+(.+)", sub)
    if m:
        left = _translate_phrase(m.group(1), 15)
        right = _translate_phrase(m.group(2), 15)
        if left and right:
            return f"桥接{left}与{right}"

    # Learning Bird Eye View Representations from Multi-Camera Images
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
        if left and right:
            if "生成" in left or "generation" in m.group(1).lower():
                return f"用{right}实现{left}"
            return f"通过{right}改进{left}"

    # Multi-view 3D Object Detection with Sparse Spatial-Temporal Fusion
    m = re.search(r"(?i)(multi[- ]view 3d object detection)\s+with\s+(.+)", sub)
    if m:
        fusion = _translate_phrase(m.group(2), 25)
        return f"采用稀疏{fusion}实现多视角三维检测"

    zh = _translate_phrase(sub, 45)
    if zh and _latin_ratio(zh) < 0.35:
        return zh
    return ""


def _method_from_title(title: str) -> str:
    """整标题即方法描述时（无副标题）。"""
    _, subtitle = _title_parts(title)
    if subtitle:
        return ""
    zh = _translate_phrase(title, 50)
    if zh and _latin_ratio(zh) < 0.2 and len(zh) >= 6:
        if re.search(r"(?i)self[- ]supervised", title):
            return f"采用{zh}"
        return zh
    return ""


def _extract_method(abstract: str, title: str) -> str:
    """提取核心方法/贡献。"""
    _, subtitle = _title_parts(title)
    if subtitle:
        m = _method_from_subtitle(subtitle)
        if m:
            return m
    else:
        m = _method_from_title(title)
        if m:
            return m

    for sent in _sentences(abstract):
        low = sent.lower()
        if "denois" in low and "contrastive" in low:
            return "通过对比去噪训练与混合查询选择改进DETR检测器"
        if "sparse spatial" in low and "fusion" in low:
            return "采用稀疏时空融合实现多视角三维检测"
        if not re.search(rf"(?i)\b(we|this paper|this work|improves?)\b", sent):
            continue
        if re.search(r"(?i)\bby using\b", sent):
            m = re.search(r"(?i)by using\s+(.+?)(?:\.|,|and achieves)", sent)
            if m:
                zh = _translate_phrase(m.group(1), 45)
                if zh and _latin_ratio(zh) < 0.35:
                    return f"通过{zh}提升模型性能"
        sent_clean = re.sub(
            rf"(?i)^.*?\b({_METHOD_VERBS})\s+",
            "",
            sent,
        )
        sent_clean = re.sub(r"(?i), a (?:state-of-the-art|novel|unified|scalable)\s+", "，", sent_clean)
        sent_clean = re.sub(r"(?i)^(?:an?|the)\s+", "", sent_clean)
        head = re.split(r"[,.]", sent_clean)[0]
        zh = _translate_phrase(head, 45)
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
        (r"necessitating an additional optimization", "需额外优化阶段才能满足约束"),
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
    patterns = [
        r"(?i)(?:achiev(?:e|es|ing)|enabl(?:e|es|ing)|improv(?:e|es|ing)|enhanc(?:e|es|ing)|"
        r"outperform(?:s|ing)?)\s+(.{8,45}?)(?:\.|,|$)",
        r"(?i)yield(?:s|ing)?\s+(?:a )?(?:significant )?(.{8,40}?)(?:\.|,|$)",
    ]
    for pat in patterns:
        m = re.search(pat, abstract)
        if m:
            zh = _translate_phrase(m.group(1), 28)
            if zh and _latin_ratio(zh) < 0.4 and not re.search(r"(?i)^\d", zh):
                return zh
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


def _compose(method: str, problems: list[str], benefit: str, context: str) -> str:
    """组装一句自然中文：方法 + 问题/收益。"""
    prob = _join_problems(problems)
    ctx = context

    if method and prob:
        if ctx:
            if method.startswith("桥接"):
                s = f"通过{method}，提升{ctx}在长尾安全场景下的泛化能力，缓解{prob}。"
            elif method.startswith("用") or method.startswith("通过"):
                s = f"{method}，缓解{ctx}中的{prob}。"
            else:
                s = f"针对{ctx}中的{prob}，采用{method}。"
        else:
            if method.startswith("用") or method.startswith("通过"):
                s = f"{method}，缓解{prob}。"
            else:
                s = f"针对{prob}，采用{method}。"
        if benefit and len(s) < 95:
            s = s.rstrip("。") + f"，{benefit}。"
        return s

    if method and benefit:
        return f"{method}，{benefit}。"

    if method:
        if ctx:
            return f"{method}，改进{ctx}中的关键能力。"
        return f"{method}。"

    if prob:
        if ctx:
            return f"针对{ctx}中的{prob}，提出相应改进方法。"
        return f"针对{prob}，提出相应改进方法。"

    if ctx:
        return f"探索{ctx}中的关键问题与可行方法。"

    return ""


def _survey_summary(title: str) -> str | None:
    m = re.search(r"(?i)methods for (.+) in (.+)", title)
    if m:
        return f"综述{_translate_phrase(m.group(2))}中的{_translate_phrase(m.group(1))}。"
    low = title.lower()
    if re.search(r"\b(survey|review|overview)\b", low):
        topic = _translate_phrase(
            re.sub(r"(?i).*(survey|review|overview)\s*(of|on|about)?\s*", "", title), 40
        )
        return f"综述{topic or _translate_phrase(title, 40)}。"
    if re.search(r"\b(benchmark|dataset)\b", low):
        return f"发布{_translate_phrase(title, 50)}基准或数据集。"
    if re.search(r"\b(challenge|workshop|competition)\b", low):
        return f"介绍{_translate_phrase(title, 50)}竞赛或挑战。"
    return None


def _title_fallback(title: str, tags: dict, abstract: str) -> str:
    ctx = _infer_context(abstract, title, tags)
    _, subtitle = _title_parts(title)
    if subtitle:
        method = _method_from_subtitle(subtitle)
        if method:
            if ctx:
                return f"{method}，改进{ctx}中的关键能力。"
            return f"{method}。"
        zh = _translate_phrase(subtitle, 45)
        if zh and _latin_ratio(zh) < 0.35:
            if ctx:
                return f"面向{ctx}，探索{zh}。"
            return f"探索{zh}。"
    if ctx:
        return f"探索{ctx}中的关键问题与可行方法。"
    return ""


def summarize_zh(paper: dict) -> str:
    """生成一句中文总结。"""
    title = (paper.get("title") or paper.get("stem") or "").strip()
    abstract = _normalize_text((paper.get("abstract") or "").strip())
    tags = paper.get("tags") or {}

    special = _survey_summary(title)
    if special:
        return _clean_zh(special[:120])

    context = _infer_context(abstract, title, tags)
    method = _extract_method(abstract, title)
    problems = _dedupe_problems(_extract_problems(abstract))
    benefit = _extract_benefit(abstract)

    s = _compose(method, problems, benefit, context)
    if not s or _latin_ratio(s) > 0.25:
        s = _title_fallback(title, tags, abstract)

    s = _clean_zh(s)
    if not s:
        ctx = _infer_context(abstract, title, tags)
        s = f"探索{ctx}相关方向的关键问题。" if ctx else "探索该方向的关键问题与可行方法。"

    if len(s) > 120:
        s = s[:117] + "…。"
    return s


def add_summaries(papers: list[dict]) -> None:
    """为每篇论文写入 summary_zh 字段。"""
    for p in papers:
        p["summary_zh"] = summarize_zh(p)
