"""
paper_tagger.py — Multi-dimensional automatic tagging from title + abstract.

Tag layers:
  topic    — research area (BEV, VLA, Planning, …)
  method   — algorithm / architecture (Transformer, Diffusion, RL, …)
  task     — what the paper does (Detection, Segmentation, Manipulation, …)
  modality — sensor / input type (LiDAR, Camera, Language, …)
  keyword  — corpus-distinctive TF-IDF terms (auto-extracted)
  folder   — user's manual folder classification (always included)
  arxiv    — arXiv primary category when available
"""

from __future__ import annotations
import re, math
from collections import Counter, defaultdict
from typing import Any

# ── Stopwords ──────────────────────────────────────────────────────────────────
_STOP = {
    "the", "a", "an", "and", "or", "of", "in", "is", "are", "to", "for", "with",
    "on", "at", "by", "from", "as", "this", "that", "we", "our", "their", "have",
    "has", "be", "been", "not", "can", "also", "it", "its", "which", "both", "such",
    "when", "using", "used", "based", "show", "shown", "propose", "proposed", "paper",
    "work", "method", "approach", "model", "models", "learn", "learning", "training",
    "train", "data", "results", "performance", "tasks", "task", "improve", "novel",
    "new", "large", "deep", "neural", "network", "networks", "via", "while", "however",
    "than", "more", "most", "well", "two", "one", "three", "first", "second", "each",
    "all", "many", "several", "different", "various", "across", "within", "between",
    "into", "over", "under", "during", "after", "before", "through", "without",
    "present", "demonstrate", "achieve", "state", "art", "significantly", "effective",
    "efficient", "framework", "system", "systems", "problem", "challenges", "challenge",
    "real", "world", "high", "low", "set", "use", "used", "using", "make", "made",
}

# ── Layered taxonomy: layer → tag → [regex patterns] ─────────────────────────
TAXONOMY: dict[str, dict[str, list[str]]] = {
    "topic": {
        # Autonomous Driving
        "BEV Perception":        [r"bird.?s.?eye.?view", r"\bbev\b", r"bevformer", r"bevdet"],
        "Occupancy Prediction":  [r"\boccupancy\b", r"occupancy grid", r"\bocc\b prediction", r"semantic scene completion"],
        "3D Detection":          [r"3d object detection", r"3d detection", r"multi.view 3d", r"monocular 3d"],
        "End-to-End Driving":    [r"end.to.end (driv|plan|percep|autonom)", r"\be2e\b (driv|plan|ad)", r"drive.*end.to.end"],
        "Motion Planning":       [r"motion plan", r"trajectory plan", r"path plan", r"\bplanner\b", r"planning and control"],
        "Motion Prediction":     [r"motion (forecast|predict)", r"trajectory (forecast|predict)", r"behavior predict"],
        "World Model":           [r"world model", r"driving world model", r"4d.*model"],
        "Simulation":            [r"\bcarla\b", r"\bnuplan\b", r"\bwaymax\b", r"closed.loop sim", r"driving simul"],
        "HD Mapping":            [r"\bhd map", r"high.definition map", r"online mapping", r"vectorized map"],
        "Tracking":              [r"multi.object track", r"\bmot\b", r"3d track", r"object track"],
        "SLAM / Localization":   [r"\bslam\b", r"visual odometry", r"\blocalization\b", r"simultaneous local"],
        # Embodied AI
        "VLA":                   [r"\bvla\b", r"\bvlas\b", r"vision.language.action", r"vision.language model.*(robot|action|manipul)"],
        "Robot Manipulation":    [r"robot manipul", r"robotic manipul", r"pick.and.place", r"mobile manipul"],
        "Humanoid Robot":        [r"\bhumanoid\b", r"whole.body (control|motion|manipul)", r"bipedal", r"legged robot"],
        "Dexterous Manipulation":[r"dexterous", r"dexterity", r"in.hand manipul", r"multi.finger"],
        "Force / Compliance":    [r"\bcompliance\b", r"\bimpedance\b", r"force control", r"contact.rich", r"force/torque", r"\bforces\b"],
        "Teleoperation":         [r"\bteleoperation\b", r"\bteleop\b", r"human.in.the.loop", r"remote operat"],
        "Imitation Learning":    [r"imitation learn", r"behavior clon", r"demonstration learn", r"learning from demonstr"],
        "Data Collection":       [r"data collection (system|pipeline|framework)", r"collect.*demonstration"],
    },
    "method": {
        "Transformer":           [r"\btransformer\b", r"\bdetr\b", r"attention mechanism", r"cross.attention"],
        "Diffusion Model":       [r"diffusion (model|policy|plan)", r"denoising diffusion", r"score.based"],
        "Reinforcement Learning":[r"reinforcement learn", r"\bppo\b", r"\bsac\b", r"policy gradient", r"\brl\b"],
        "Generative Model":      [r"generative (model|adversarial)", r"\bgan\b", r"\bvae\b", r"variational auto"],
        "NeRF / 3DGS":           [r"\bnerf\b", r"neural radiance", r"gaussian splat", r"\b3dgs\b"],
        "Graph Neural Network":  [r"graph neural", r"\bgnn\b", r"message passing"],
        "Foundation Model":      [r"foundation model", r"large.pretrain", r"pre.train.*model"],
        "LLM / VLM":             [r"large language model", r"\bllm\b", r"vision.language model", r"\bvlm\b", r"multimodal.*(llm|language)"],
        "Self-Supervised":       [r"self.supervised", r"contrastive learn", r"masked autoencoder", r"\bmae\b"],
        "Distillation":          [r"knowledge distil", r"teacher.student", r"model distil"],
        "Optimization":          [r"convex optim", r"nonlinear optim", r"trajectory optim", r"mixed.integer"],
    },
    "task": {
        "Object Detection":      [r"object detection", r"2d detection", r"open.vocabulary detect"],
        "Segmentation":          [r"\bsegmentation\b", r"semantic segment", r"instance segment", r"panoptic"],
        "Classification":        [r"\bclassification\b", r"image classif"],
        "Tracking":              [r"\btracking\b", r"track.let", r"multi.object track"],
        "Depth Estimation":      [r"depth estim", r"depth predict", r"stereo depth", r"monocular depth"],
        "Pose Estimation":       [r"pose estim", r"6d pose", r"articulated pose"],
        "Grasping":              [r"\bgrasping\b", r"grasp (plan|detect|generat)", r"grasp pose"],
        "Navigation":            [r"\bnavigation\b", r"visual navig", r"goal.directed navig"],
        "Control":               [r"(robot )?control\b", r"model predictive control", r"\bmpc\b"],
        "Forecasting":           [r"\bforecast", r"future (state|frame|trajectory)"],
        "Reconstruction":        [r"3d reconstruct", r"scene reconstruct", r"surface reconstruct"],
        "Generation":            [r"(image|video|scene|trajectory) generat", r"text.to.image"],
        "Benchmark / Dataset":   [r"\bwe (introduce|present|release|propose).{0,40}\b(dataset|benchmark)\b",
                                   r"^(a )?(new |large.?scale )?(dataset|benchmark)\b",
                                   r"\bsurvey (of|on)\b", r"comprehensive survey"],
        "Evaluation":            [r"\bevaluation\b", r"we evaluate", r"experimental (results|evaluation)"],
    },
    "modality": {
        "LiDAR":                 [r"\blidar\b", r"point cloud", r"\bpts\b"],
        "Camera / Vision":         [r"\bcamera\b", r"visual (input|perception|feature)", r"rgb.d", r"monocular", r"multi.view"],
        "Radar":                 [r"\bradar\b", r"4d radar"],
        "Language":              [r"natural language", r"text (input|prompt|condition)", r"language instruct"],
        "Tactile":               [r"\btactile\b", r"\bhaptic\b", r"touch sensor"],
        "IMU / Proprioception":  [r"\bimu\b", r"propriocept", r"joint (angle|position|torque)"],
        "Multi-Modal Fusion":    [r"multi.modal", r"sensor fusion", r"cross.modal", r"vision.lidar"],
    },
}

# Folder → topic tag mapping (fallback when text match is weak)
FOLDER_TAGS: dict[str, list[str]] = {
    "BEV": ["BEV Perception"],
    "3d-perception": ["3D Detection"],
    "planner-paper": ["Motion Planning"],
    "WM": ["World Model"],
    "diffusion": ["Diffusion Model"],
    "RL": ["Reinforcement Learning"],
    "LLM_AD": ["LLM / VLM"],
    "VLA_E2E": ["VLA", "End-to-End Driving"],
    "loop-sim": ["Simulation"],
    "sim": ["Simulation"],
    "survey": ["Benchmark / Dataset"],
    "dataset": ["Benchmark / Dataset"],
    "competition": ["Benchmark / Dataset"],
    "VLA": ["VLA"],
    "humanoid": ["Humanoid Robot"],
    "force": ["Force / Compliance"],
    "exoskeleton": ["Teleoperation", "Data Collection"],
    "data-collection": ["Data Collection"],
    "WM-WAM": ["World Model"],
    "V-agent": ["Robot Manipulation"],
    "V-LLM": ["LLM / VLM"],
    "bench": ["Benchmark / Dataset"],
    "base-paper": ["Robot Manipulation"],
}

_ARXIV_CAT_MAP: dict[str, str] = {
    "cs.RO": "Robotics",
    "cs.CV": "Computer Vision",
    "cs.LG": "Machine Learning",
    "cs.AI": "Artificial Intelligence",
    "cs.CL": "NLP",
    "cs.SY": "Control Systems",
    "eess.IV": "Image/Video",
    "eess.SP": "Signal Processing",
    "stat.ML": "Machine Learning",
}

# Lowercase alias → canonical tag (Title Case topic/modality/method names).
# Used to merge keyword variants with structured tags and dedupe display/stats.
TAG_ALIASES: dict[str, str] = {
    # Modality
    "tactile": "Tactile",
    "haptic": "Tactile",
    # Topic — VLA
    "vla": "VLA",
    "vlas": "VLA",
    # Topic — force / compliance
    "force": "Force / Compliance",
    "forces": "Force / Compliance",
    "compliance": "Force / Compliance",
    "impedance": "Force / Compliance",
}

_STRUCTURAL_LAYERS = ("topic", "method", "task", "modality", "folder", "arxiv")

_compiled: dict[str, list[tuple[str, list[re.Pattern]]]] = {}


def _get_compiled(layer: str) -> list[tuple[str, list[re.Pattern]]]:
    if layer not in _compiled:
        _compiled[layer] = [
            (tag, [re.compile(p, re.IGNORECASE) for p in patterns])
            for tag, patterns in TAXONOMY.get(layer, {}).items()
        ]
    return _compiled[layer]


def _match_layer(text: str, layer: str) -> list[str]:
    return [
        tag for tag, patterns in _get_compiled(layer)
        if any(p.search(text) for p in patterns)
    ]


def _canonical_tag(tag: str) -> str:
    """Map alias / case variant to canonical display name."""
    return TAG_ALIASES.get(tag.lower(), tag)


def _dedup_key(tag: str) -> str:
    """Case-insensitive semantic key for cross-layer deduplication."""
    return _canonical_tag(tag).lower()


def _filter_redundant_keywords(
    keywords: list[str], result: dict[str, list[str]]
) -> list[str]:
    """Drop TF-IDF keywords already covered by a structured tag (incl. aliases)."""
    structural_keys = {
        _dedup_key(t)
        for layer in _STRUCTURAL_LAYERS
        for t in result.get(layer, [])
    }
    seen_kw: set[str] = set()
    filtered: list[str] = []
    for kw in keywords:
        key = _dedup_key(kw)
        if key in structural_keys or key in seen_kw:
            continue
        seen_kw.add(key)
        filtered.append(kw)
    return filtered


def _build_all_tags(result: dict[str, list[str]]) -> list[str]:
    """Flat display list: structural layers first, semantic dedup across layers."""
    seen: set[str] = set()
    all_tags: list[str] = []
    for layer in (*_STRUCTURAL_LAYERS, "keyword"):
        for t in result.get(layer, []):
            key = _dedup_key(t)
            if key in seen:
                continue
            seen.add(key)
            all_tags.append(_canonical_tag(t))
    return all_tags


def _tokenize(text: str) -> list[str]:
    # Normalize unicode ligatures (PDF extraction artifact)
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl").replace("\u2019", "'")
    text = re.sub(r"[^\w\s\-]", " ", text.lower())
    tokens = []
    for t in text.split():
        if len(t) > 2 and t not in _STOP and not t.isdigit():
            tokens.append(t)
    return tokens


def build_keyword_vocabulary(
    papers: list[dict], min_df: int = 12, max_df_ratio: float = 0.25
) -> dict[str, float]:
    """Return {term: idf} for corpus-distinctive terms."""
    n = len(papers)
    if n == 0:
        return {}
    df: Counter = Counter()
    for p in papers:
        text = f"{p.get('title') or ''} {p.get('abstract') or ''}"
        df.update(set(_tokenize(text)))

    idf = {}
    for term, count in df.items():
        if count >= min_df and count <= n * max_df_ratio:
            idf[term] = math.log((n + 1) / (count + 1))
    return idf


def extract_keyword_tags(
    paper: dict, idf_vocab: dict[str, float], top_n: int = 4
) -> list[str]:
    text = f"{paper.get('title') or ''} {paper.get('abstract') or ''}"
    tf = Counter(_tokenize(text))
    scores = {t: (1 + math.log(tf[t])) * idf_vocab[t] for t in tf if t in idf_vocab}
    top = sorted(scores, key=scores.get, reverse=True)[:top_n]  # type: ignore
    return [f"kw:{t}" for t in top if scores[t] > 0.5]


def tag_paper(paper: dict, idf_vocab: dict[str, float] | None = None) -> dict[str, list[str]]:
    """
    Return structured tags:
      {layer: [tag, ...], "all": [flat list with layer prefix stripped for display]}
    """
    text = f"{paper.get('title') or ''} {paper.get('abstract') or ''}".lower()

    result: dict[str, list[str]] = {
        "topic": _match_layer(text, "topic"),
        "method": _match_layer(text, "method"),
        "task": _match_layer(text, "task"),
        "modality": _match_layer(text, "modality"),
        "keyword": [],
        "folder": [],
        "arxiv": [],
    }

    # Folder fallback tags
    folder = paper.get("folder", "")
    if folder in FOLDER_TAGS:
        for t in FOLDER_TAGS[folder]:
            if t not in result["topic"]:
                result["folder"].append(t)

    # arXiv category
    cat = paper.get("arxiv_cat")
    if cat and cat in _ARXIV_CAT_MAP:
        result["arxiv"].append(_ARXIV_CAT_MAP[cat])

    # TF-IDF keyword tags
    if idf_vocab:
        text_full = f"{paper.get('title') or ''} {paper.get('abstract') or ''}"
        tf = Counter(_tokenize(text_full))
        scores = {t: (1 + math.log(tf[t])) * idf_vocab[t] for t in tf if t in idf_vocab}
        top = sorted(scores, key=scores.get, reverse=True)[:3]  # type: ignore
        result["keyword"] = _filter_redundant_keywords(
            [t for t in top if scores[t] > 0.8], result
        )

    result["all"] = _build_all_tags(result)
    return result


def tag_all_papers(papers: list[dict]) -> tuple[list[dict], dict[str, Any]]:
    """
    Tag every paper in-place (adds paper["tags"] dict).
    Returns (papers, tag_stats) where tag_stats has counts, co-occurrence, by-layer.
    """
    idf_vocab = build_keyword_vocabulary(papers)

    layer_counts: dict[str, Counter] = {layer: Counter() for layer in TAXONOMY}
    layer_counts["folder"] = Counter()
    layer_counts["keyword"] = Counter()
    layer_counts["arxiv"] = Counter()
    all_tag_counts: Counter = Counter()
    cooccur: dict[str, Counter] = defaultdict(Counter)
    uncat = 0

    for p in papers:
        tags = tag_paper(p, idf_vocab)
        p["tags"] = tags
        if not tags["all"]:
            uncat += 1
            tags["all"] = ["Uncategorized"]
            tags["topic"] = ["Uncategorized"]

        for t in tags["all"]:
            all_tag_counts[t] += 1

        for layer, tag_list in tags.items():
            if layer == "all":
                continue
            for t in tag_list:
                layer_counts.setdefault(layer, Counter())[t] += 1

        # Co-occurrence (topic + method tags only, for cleaner graph)
        structural = tags["topic"] + tags["method"] + tags["task"]
        for i, t1 in enumerate(structural):
            for t2 in structural[i + 1:]:
                cooccur[t1][t2] += 1
                cooccur[t2][t1] += 1

    stats = {
        "total": len(papers),
        "uncategorized": uncat,
        "unique_tags": len(all_tag_counts),
        "by_tag": dict(all_tag_counts.most_common(200)),
        "by_layer": {
            layer: dict(
                (t, c) for t, c in c.most_common()
                if layer != "keyword" or c >= 10  # sidebar: only frequent keywords
            )
            for layer, c in layer_counts.items()
        },
        "cooccur": {
            t1: dict(sorted(c.items(), key=lambda x: -x[1])[:20])
            for t1, c in sorted(cooccur.items(), key=lambda x: -sum(x[1].values()))[:60]
        },
        "layers": list(TAXONOMY.keys()) + ["folder", "keyword", "arxiv"],
    }
    return papers, stats
