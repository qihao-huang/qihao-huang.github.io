"""
paper_validator.py — Secondary validation of paper metadata and tags.

Checks metadata sanity, tag consistency vs title+abstract, folder alignment,
and optionally verifies ambiguous cases via arXiv / Semantic Scholar / Crossref.
"""

from __future__ import annotations

import json
import math
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from paper_filter import (
    is_invalid_arxiv_id,
    is_plausible_pub_year,
    is_valid_arxiv_id,
    should_exclude,
    MAX_PUB_YEAR,
)
from paper_tagger import (
    FOLDER_TAGS,
    TAXONOMY,
    _tokenize,
    tag_all_papers,
)

SCRIPT_DIR = Path(__file__).parent.resolve()
CACHE_FILE = SCRIPT_DIR / ".papers_cache.json"

ONLINE_DELAY = 0.3
USER_AGENT = "PersonalPaperLibrary/1.0 (validation tool; qihao.huang@example.com)"
MIN_ABSTRACT_LEN = 80
CONFIDENCE_THRESHOLD = 0.55
TITLE_MATCH_THRESHOLD = 0.7

JUNK_TITLE_PATTERNS: list[tuple[str, str]] = [
    (r"(?i)^researchgate", "researchgate_header"),
    (r"(?i)affiliation not available", "affiliation_unavailable"),
    (r"(?i)^see discussions?", "see_discussions"),
    (r"(?i)^download pdf", "download_pdf"),
    (r"(?i)^preprint", "preprint_header"),
    (r"(?i)^abstract\s*$", "abstract_only_title"),
]

# Folder segment → expected topic tags or content keywords
FOLDER_CONTENT_HINTS: dict[str, dict[str, Any]] = {
    "BEV": {"topics": ["BEV Perception"], "keywords": {"bev", "bird", "eye", "view"}},
    "3d-perception": {"topics": ["3D Detection"], "keywords": {"3d", "detection", "lidar", "point"}},
    "planner-paper": {"topics": ["Motion Planning"], "keywords": {"plan", "trajectory", "motion"}},
    "WM": {"topics": ["World Model"], "keywords": {"world", "model"}},
    "WM-WAM": {"topics": ["World Model"], "keywords": {"world", "model"}},
    "diffusion": {"topics": ["Diffusion Model"], "keywords": {"diffusion", "denois"}},
    "RL": {"topics": ["Reinforcement Learning"], "keywords": {"reinforcement", "policy", "reward"}},
    "LLM_AD": {"topics": ["LLM / VLM"], "keywords": {"language", "llm", "vlm", "multimodal"}},
    "VLA_E2E": {"topics": ["VLA", "End-to-End Driving"], "keywords": {"vla", "end", "end-to-end", "driving"}},
    "VLA": {"topics": ["VLA"], "keywords": {"vla", "vision", "language", "action"}},
    "loop-sim": {"topics": ["Simulation"], "keywords": {"simul", "carla", "closed", "loop"}},
    "sim": {"topics": ["Simulation"], "keywords": {"simul", "simulator"}},
    "humanoid": {"topics": ["Humanoid Robot"], "keywords": {"humanoid", "biped", "legged"}},
    "force": {"topics": ["Force / Compliance"], "keywords": {"force", "compliance", "impedance", "tactile"}},
    "exoskeleton": {"topics": ["Teleoperation"], "keywords": {"exoskeleton", "teleop", "wearable"}},
    "data-collection": {"topics": ["Data Collection"], "keywords": {"data", "collection", "demonstration"}},
    "V-agent": {"topics": ["Robot Manipulation"], "keywords": {"robot", "manipul", "agent"}},
    "V-LLM": {"topics": ["LLM / VLM"], "keywords": {"llm", "vlm", "language", "vision"}},
    "paper-video": {"topics": [], "keywords": {"video", "temporal", "tracking", "motion", "frame"}},
    "video": {"topics": [], "keywords": {"video", "temporal", "tracking"}},
    "paper-dynamic-geometry": {"topics": [], "keywords": {"geometry", "dynamic", "3d", "reconstruct", "deform"}},
    "base-paper": {"topics": ["Robot Manipulation"], "keywords": {"robot", "manipul"}},
    "survey": {"topics": ["Benchmark / Dataset"], "keywords": {"survey", "review"}},
    "dataset": {"topics": ["Benchmark / Dataset"], "keywords": {"dataset", "benchmark"}},
    "competition": {"topics": ["Benchmark / Dataset"], "keywords": {"challenge", "competition", "benchmark"}},
    "bench": {"topics": ["Benchmark / Dataset"], "keywords": {"benchmark", "evaluation"}},
}

# Broad catch-all folders — skip strict folder-content checks
FOLDER_CATCHALL = {"paper-HKU", "paper-general", "paper-topics", "others", "_root", "AR", "iRL"}

# Tag pairs that should not co-occur without supporting text
CONTRADICTION_RULES: list[dict[str, Any]] = [
    {
        "tags": {"LLM / VLM"},
        "layers": ("method", "topic"),
        "require_any": {"language", "llm", "vlm", "multimodal", "text", "prompt", "instruction"},
        "reason": "llm_tag_without_language",
    },
    {
        "tags": {"Reinforcement Learning"},
        "layers": ("method",),
        "require_any": {"reinforcement", "reward", "policy", "rl", "ppo", "sac", "q-learning"},
        "reason": "rl_tag_without_rl_keywords",
    },
    {
        "tags": {"LiDAR"},
        "layers": ("modality",),
        "require_any": {"lidar", "point", "cloud", "laser", "pts"},
        "reason": "lidar_tag_without_lidar",
    },
]

_BROAD_ARXIV_TAGS = {"Computer Vision", "Machine Learning", "Artificial Intelligence", "Robotics", "NLP"}


def _extract_keywords_from_patterns(patterns: list[str]) -> set[str]:
    words: set[str] = set()
    for pat in patterns:
        cleaned = re.sub(r"\\b|\\s|[\[\](){}^$|?*+.\-]", " ", pat.lower())
        for w in cleaned.split():
            w = w.strip("-")
            if len(w) > 2 and w not in {"the", "and", "for", "with", "end", "to"}:
                words.add(w)
    return words


def build_tag_keywords() -> dict[str, dict[str, set[str]]]:
    """Map layer → tag → keyword set for overlap scoring."""
    result: dict[str, dict[str, set[str]]] = {}
    for layer, tags in TAXONOMY.items():
        result[layer] = {}
        for tag, patterns in tags.items():
            kws = _extract_keywords_from_patterns(patterns)
            for part in re.split(r"[/\s]+", tag.lower()):
                if len(part) > 2:
                    kws.add(part)
            result[layer][tag] = kws
    # folder / arxiv layers
    folder_tag_names = {tag for tags in FOLDER_TAGS.values() for tag in tags}
    result["folder"] = {
        t: set(re.split(r"[/\s]+", t.lower()))
        for t in folder_tag_names
    }
    result["arxiv"] = {t: set(t.lower().split()) for t in _BROAD_ARXIV_TAGS}
    return result


TAG_KEYWORDS = build_tag_keywords()


def _title_sim(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    stop = {"the", "a", "an", "of", "in", "is", "for", "and", "with", "on", "via", "using", "from"}
    ta = set(re.findall(r"\w+", a.lower())) - stop
    tb = set(re.findall(r"\w+", b.lower())) - stop
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def _fetch_json(url: str, timeout: int = 12) -> Any:
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _text_tokens(paper: dict) -> set[str]:
    text = f"{paper.get('title') or ''} {paper.get('abstract') or ''}"
    return set(_tokenize(text))


def validate_metadata(paper: dict) -> list[dict]:
    issues: list[dict] = []
    path = paper.get("path")
    if path and not Path(path).exists():
        issues.append({"type": "path_missing", "severity": "error", "detail": path})

    title = paper.get("title") or ""
    abstract = paper.get("abstract") or ""

    if paper.get("_title_is_filename") and not abstract:
        issues.append({
            "type": "title_is_filename",
            "severity": "warning",
            "detail": title[:120],
        })

    for pat, reason in JUNK_TITLE_PATTERNS:
        if re.search(pat, title):
            issues.append({"type": "junk_title", "severity": "warning", "detail": reason})

    if not abstract:
        issues.append({"type": "missing_abstract", "severity": "warning"})
    elif len(abstract) < MIN_ABSTRACT_LEN:
        issues.append({
            "type": "short_abstract",
            "severity": "info",
            "detail": f"len={len(abstract)}",
        })

    pub_year = paper.get("pub_year")
    pub_month = paper.get("pub_month")
    if pub_year is None:
        issues.append({"type": "missing_pub_year", "severity": "warning"})
    elif not is_plausible_pub_year(pub_year):
        issues.append({
            "type": "implausible_pub_year",
            "severity": "warning",
            "detail": str(pub_year),
        })
    if pub_month is not None and not (1 <= pub_month <= 12):
        issues.append({
            "type": "implausible_pub_month",
            "severity": "warning",
            "detail": str(pub_month),
        })

    arxiv_id = paper.get("arxiv_id")
    if arxiv_id and is_invalid_arxiv_id(arxiv_id):
        issues.append({
            "type": "invalid_arxiv_id",
            "severity": "error",
            "detail": arxiv_id,
        })

    return issues


def validate_tag_overlap(paper: dict, tags: dict[str, list[str]]) -> list[dict]:
    issues: list[dict] = []
    tokens = _text_tokens(paper)
    if not tokens:
        return issues

    for layer in ("topic", "method", "task", "modality", "keyword"):
        for tag in tags.get(layer, []):
            if tag == "Uncategorized":
                continue
            kws = TAG_KEYWORDS.get(layer, {}).get(tag, set())
            if not kws:
                kws = set(re.split(r"[/\s]+", tag.lower())) - {"", "kw"}
            overlap = kws & tokens
            score = len(overlap) / len(kws) if kws else 0.0
            if score == 0.0 and layer != "keyword":
                issues.append({
                    "type": "suspicious_tag",
                    "severity": "warning",
                    "layer": layer,
                    "tag": tag,
                    "overlap_score": 0.0,
                })

    # Missing topic when clear domain signals exist but no topic assigned
    assigned_topics = set(tags.get("topic", []))
    has_real_topic = assigned_topics and "Uncategorized" not in assigned_topics
    if not has_real_topic:
        for topic, _patterns in TAXONOMY["topic"].items():
            kws = TAG_KEYWORDS["topic"].get(topic, set())
            hits = kws & tokens
            if len(hits) >= 2:
                issues.append({
                    "type": "missing_topic",
                    "severity": "info",
                    "suggested_topic": topic,
                    "matched_keywords": sorted(hits)[:5],
                })
                break  # one suggestion per paper

    # Contradictory tags
    for rule in CONTRADICTION_RULES:
        for layer in rule["layers"]:
            for tag in tags.get(layer, []):
                if tag in rule["tags"] and not (rule["require_any"] & tokens):
                    issues.append({
                        "type": "contradictory_tag",
                        "severity": "warning",
                        "layer": layer,
                        "tag": tag,
                        "reason": rule["reason"],
                    })

    return issues


def validate_folder(paper: dict, tags: dict[str, list[str]]) -> list[dict]:
    issues: list[dict] = []
    folder = paper.get("folder", "")
    if folder in FOLDER_CATCHALL or not folder:
        return issues

    hints = FOLDER_CONTENT_HINTS.get(folder)
    if not hints:
        return issues

    all_tags = set(tags.get("topic", []) + tags.get("folder", []) + tags.get("method", []))
    expected_topics = hints.get("topics", [])
    if expected_topics and not any(t in all_tags for t in expected_topics):
        issues.append({
            "type": "folder_topic_mismatch",
            "severity": "warning",
            "folder": folder,
            "expected_topics": expected_topics,
            "actual_topics": list(tags.get("topic", [])),
        })

    content_kws = hints.get("keywords", set())
    tokens = _text_tokens(paper)
    if content_kws and tokens and not (content_kws & tokens):
        # Only flag if folder-specific and no keyword overlap at all
        if folder.startswith("paper-") or folder in FOLDER_TAGS:
            issues.append({
                "type": "folder_content_mismatch",
                "severity": "info",
                "folder": folder,
                "expected_keywords": sorted(content_kws)[:6],
            })

    return issues


def _compute_confidence(paper: dict, issues: list[dict]) -> float:
    score = 1.0
    for iss in issues:
        sev = iss.get("severity", "info")
        itype = iss.get("type", "")
        if sev == "error":
            score -= 0.25
        elif sev == "warning":
            score -= 0.08 if itype != "suspicious_tag" else 0.05
        elif itype == "missing_topic":
            score -= 0.02
    if paper.get("_title_is_filename"):
        score -= 0.15
    if not paper.get("abstract"):
        score -= 0.1
    if not paper.get("pub_year"):
        score -= 0.08
    return max(0.0, min(1.0, score))


def _needs_online_verify(paper: dict, issues: list[dict], confidence: float) -> bool:
    if confidence < CONFIDENCE_THRESHOLD:
        return True
    trigger_types = {
        "title_is_filename", "junk_title", "suspicious_tag",
        "missing_pub_year", "invalid_arxiv_id", "contradictory_tag",
        "folder_topic_mismatch",
    }
    return any(i["type"] in trigger_types for i in issues)


def _online_lookup_arxiv(arxiv_id: str) -> dict | None:
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}&max_results=1"
    time.sleep(ONLINE_DELAY)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml = resp.read().decode("utf-8")
        titles = [
            re.sub(r"\s+", " ", t).strip()
            for t in re.findall(r"<title[^>]*>(.*?)</title>", xml, re.DOTALL)
            if t.strip() and "ArXiv" not in t
        ]
        abstracts = re.findall(r"<summary[^>]*>(.*?)</summary>", xml, re.DOTALL)
        cats = re.findall(r'<arxiv:primary_category[^/]* term="([^"]+)"', xml)
        if not titles:
            return None
        return {
            "source": "arxiv",
            "title": titles[0],
            "abstract": abstracts[0].strip() if abstracts else None,
            "arxiv_cat": cats[0] if cats else None,
        }
    except Exception:
        return None


def _online_lookup_s2(title: str, arxiv_id: str | None = None) -> dict | None:
    time.sleep(ONLINE_DELAY)
    if arxiv_id:
        url = (
            f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}"
            f"?fields=title,abstract,fieldsOfStudy,s2FieldsOfStudy"
        )
        data = _fetch_json(url)
        if data and data.get("title"):
            return {
                "source": "semanticscholar",
                "title": data.get("title"),
                "abstract": data.get("abstract"),
                "fields": [f.get("category") for f in (data.get("s2FieldsOfStudy") or []) if f.get("category")],
            }

    q = urllib.parse.quote(title[:100])
    url = (
        f"https://api.semanticscholar.org/graph/v1/paper/search"
        f"?query={q}&limit=3&fields=title,abstract,fieldsOfStudy,s2FieldsOfStudy"
    )
    data = _fetch_json(url)
    if data and data.get("data"):
        for item in data["data"]:
            if _title_sim(title, item.get("title", "")) > 0.55:
                return {
                    "source": "semanticscholar",
                    "title": item.get("title"),
                    "abstract": item.get("abstract"),
                    "fields": [
                        f.get("category")
                        for f in (item.get("s2FieldsOfStudy") or [])
                        if f.get("category")
                    ],
                }
    return None


def _online_lookup_crossref(title: str) -> dict | None:
    q = urllib.parse.quote(title[:100])
    url = (
        f"https://api.crossref.org/works?query.bibliographic={q}"
        f"&rows=3&select=title&mailto=qihao.huang@example.com"
    )
    time.sleep(ONLINE_DELAY)
    data = _fetch_json(url)
    if data and "message" in data:
        for item in data["message"].get("items", []):
            cr_titles = item.get("title", [])
            if cr_titles and _title_sim(title, cr_titles[0]) > 0.55:
                return {"source": "crossref", "title": cr_titles[0]}
    return None


def online_verify_paper(paper: dict) -> dict:
    """Query online sources; return verification result without mutating paper."""
    local_title = paper.get("title") or paper.get("stem", "")
    result: dict[str, Any] = {"verified": False, "sources_tried": []}

    online: dict | None = None
    arxiv_id = paper.get("arxiv_id")
    if arxiv_id and is_valid_arxiv_id(arxiv_id):
        result["sources_tried"].append("arxiv")
        online = _online_lookup_arxiv(arxiv_id)

    if not online and local_title:
        result["sources_tried"].append("semanticscholar")
        online = _online_lookup_s2(local_title, arxiv_id if is_valid_arxiv_id(arxiv_id) else None)

    if not online and local_title:
        result["sources_tried"].append("crossref")
        online = _online_lookup_crossref(local_title)

    if not online:
        result["status"] = "not_found"
        return result

    result["verified"] = True
    result["online_title"] = online.get("title")
    result["online_source"] = online.get("source")
    sim = _title_sim(local_title, online.get("title"))
    result["title_similarity"] = round(sim, 3)

    if sim < TITLE_MATCH_THRESHOLD:
        result["title_mismatch"] = {
            "local": local_title[:200],
            "online": (online.get("title") or "")[:200],
            "similarity": round(sim, 3),
        }

    # Tag suggestions from online abstract/fields
    suggestions: list[str] = []
    online_text = f"{online.get('title') or ''} {online.get('abstract') or ''}".lower()
    online_tokens = set(_tokenize(online_text))
    local_tags = set(paper.get("tags", {}).get("all", []))
    for layer, tag_map in TAXONOMY.items():
        for topic, patterns in tag_map.items():
            if topic in local_tags:
                continue
            kws = TAG_KEYWORDS[layer].get(topic, set())
            if len(kws & online_tokens) >= 2:
                suggestions.append(topic)
    if online.get("fields"):
        result["online_fields"] = online["fields"][:5]
    if suggestions:
        result["tag_suggestions"] = suggestions[:5]

    return result


def validate_paper(
    paper: dict,
    *,
    duplicate_titles: set[str] | None = None,
) -> dict:
    tags = paper.get("tags") or {}
    issues: list[dict] = []
    issues.extend(validate_metadata(paper))
    issues.extend(validate_tag_overlap(paper, tags))
    issues.extend(validate_folder(paper, tags))

    title_norm = (paper.get("title") or "").strip().lower()
    if duplicate_titles and title_norm and title_norm in duplicate_titles:
        issues.append({"type": "duplicate_title", "severity": "warning"})

    confidence = _compute_confidence(paper, issues)
    needs_online = _needs_online_verify(paper, issues, confidence)

    return {
        "path": paper.get("path"),
        "rel_path": paper.get("rel_path"),
        "title": (paper.get("title") or "")[:200],
        "folder": paper.get("folder"),
        "library": paper.get("library"),
        "confidence": round(confidence, 3),
        "needs_online_verify": needs_online,
        "issues": issues,
        "issue_count": len(issues),
        "tags_summary": {
            layer: tags.get(layer, [])
            for layer in ("topic", "method", "task", "modality", "keyword", "folder", "arxiv")
        },
    }


def load_papers_from_cache(cache_path: Path | None = None) -> list[dict]:
    path = cache_path or CACHE_FILE
    cache = json.loads(path.read_text(encoding="utf-8"))
    papers = list(cache.get("papers", {}).values())
    included: list[dict] = []
    for p in papers:
        ex, _ = should_exclude(p)
        if not ex:
            included.append(p)
    return included


def validate_all_papers(
    papers: list[dict],
    *,
    online: bool = False,
    limit: int | None = None,
    sample: int | None = None,
) -> dict:
    """Run validation on all papers; optionally online-verify ambiguous ones."""
    papers, tag_stats = tag_all_papers(list(papers))

    # Duplicate title detection
    title_groups: dict[str, list[dict]] = defaultdict(list)
    for p in papers:
        t = (p.get("title") or "").strip().lower()
        if t and len(t) > 10:
            title_groups[t].append(p)
    dup_titles: set[str] = set()
    for t, group in title_groups.items():
        arxiv_ids = {p.get("arxiv_id") for p in group if p.get("arxiv_id")}
        if len(group) > 1 and len(arxiv_ids) > 1:
            dup_titles.add(t)

    if sample and sample < len(papers):
        rng = random.Random(42)
        papers = rng.sample(papers, sample)

    results: list[dict] = []
    for p in papers:
        r = validate_paper(p, duplicate_titles=dup_titles)
        results.append(r)

    # Online verification for ambiguous cases
    online_candidates = [r for r in results if r["needs_online_verify"]]
    online_candidates.sort(key=lambda x: x["confidence"])
    if limit:
        online_candidates = online_candidates[:limit]

    online_results: list[dict] = []
    if online:
        for i, r in enumerate(online_candidates):
            paper = next(p for p in papers if p.get("path") == r["path"])
            vr = online_verify_paper(paper)
            entry = {"path": r["path"], "title": r["title"], **vr}
            online_results.append(entry)
            r["online_verify"] = vr

    category_analysis = analyze_categories(papers, results, tag_stats)

    issue_counts: Counter = Counter()
    for r in results:
        for iss in r["issues"]:
            issue_counts[iss["type"]] += 1

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_papers": len(results),
        "online_verified": len(online_results),
        "issue_counts": dict(issue_counts.most_common()),
        "papers_needing_review": sum(1 for r in results if r["needs_online_verify"]),
        "avg_confidence": round(
            sum(r["confidence"] for r in results) / max(len(results), 1), 3
        ),
        "category_analysis": category_analysis,
        "online_results": online_results,
        "papers": results,
        "tag_stats": tag_stats,
    }


def analyze_categories(
    papers: list[dict],
    results: list[dict],
    tag_stats: dict,
) -> dict:
    """Analyze tag layer reasonableness across the corpus."""
    by_layer = tag_stats.get("by_layer", {})
    topic_counts = by_layer.get("topic", {})
    method_counts = by_layer.get("method", {})
    keyword_counts = by_layer.get("keyword", {})

    # Papers with no topic (excluding Uncategorized assignment)
    no_topic = sum(
        1 for p in papers
        if not p.get("tags", {}).get("topic")
        or p["tags"]["topic"] == ["Uncategorized"]
    )

    # Folder-tag redundancy: folder tag also appears in topic
    folder_redundant = 0
    for p in papers:
        tags = p.get("tags", {})
        folder_tags = set(tags.get("folder", []))
        topic_tags = set(tags.get("topic", []))
        if folder_tags & topic_tags:
            folder_redundant += 1

    # Near-duplicate keywords (case variants)
    kw_norm: dict[str, list[str]] = defaultdict(list)
    for kw, cnt in keyword_counts.items():
        kw_norm[kw.lower()].append(kw)
    near_dup_keywords = {
        norm: variants
        for norm, variants in kw_norm.items()
        if len(set(variants)) > 1
    }

    # Suspicious tag examples
    suspicious_examples: list[dict] = []
    for r in results:
        for iss in r["issues"]:
            if iss["type"] == "suspicious_tag":
                suspicious_examples.append({
                    "title": r["title"][:80],
                    "folder": r["folder"],
                    "layer": iss["layer"],
                    "tag": iss["tag"],
                    "path": r["rel_path"],
                })
    suspicious_examples.sort(key=lambda x: (x["layer"], x["tag"]))
    suspicious_by_tag: Counter = Counter(
        (e["layer"], e["tag"]) for e in suspicious_examples
    )

    # Folder mismatch stats
    folder_mismatches: Counter = Counter()
    for r in results:
        for iss in r["issues"]:
            if iss["type"] in ("folder_topic_mismatch", "folder_content_mismatch"):
                folder_mismatches[iss.get("folder", "?")] += 1

    # Coverage: % papers with each layer non-empty
    layer_coverage: dict[str, float] = {}
    n = len(papers)
    for layer in ("topic", "method", "task", "modality", "keyword"):
        has = sum(1 for p in papers if p.get("tags", {}).get(layer))
        layer_coverage[layer] = round(has / max(n, 1) * 100, 1)

    # Top broad topics
    broad_topics = sorted(topic_counts.items(), key=lambda x: -x[1])[:15]

    return {
        "uncategorized": tag_stats.get("uncategorized", 0),
        "no_topic_pct": round(no_topic / max(len(papers), 1) * 100, 1),
        "layer_coverage_pct": layer_coverage,
        "top_topics": broad_topics,
        "top_methods": sorted(method_counts.items(), key=lambda x: -x[1])[:10],
        "folder_redundant_count": folder_redundant,
        "folder_redundant_pct": round(folder_redundant / max(len(papers), 1) * 100, 1),
        "near_duplicate_keywords": dict(list(near_dup_keywords.items())[:20]),
        "suspicious_tag_count": len(suspicious_examples),
        "suspicious_by_tag": {
            f"{layer}/{tag}": cnt
            for (layer, tag), cnt in suspicious_by_tag.most_common(20)
        },
        "suspicious_examples": suspicious_examples[:30],
        "folder_mismatch_counts": dict(folder_mismatches.most_common(20)),
    }


def write_validation_summary(report: dict, out_path: Path) -> None:
    """Write human-readable Chinese summary markdown."""
    ca = report.get("category_analysis", {})
    issue_counts = report.get("issue_counts", {})
    lines: list[str] = [
        "# 论文元数据与标签校验报告",
        "",
        f"生成时间：{report.get('generated_at', '')}",
        f"校验论文数：{report.get('total_papers', 0)}",
        f"平均置信度：{report.get('avg_confidence', 0)}",
        f"需人工复核：{report.get('papers_needing_review', 0)} 篇",
        "",
        "## 1. 各类问题数量统计",
        "",
        "| 问题类型 | 数量 |",
        "|---------|------|",
    ]
    type_labels = {
        "path_missing": "文件路径不存在",
        "title_is_filename": "标题为文件名回退",
        "junk_title": "垃圾标题模式",
        "missing_abstract": "缺少摘要",
        "short_abstract": "摘要过短",
        "missing_pub_year": "缺少年份",
        "implausible_pub_year": "年份不合理",
        "implausible_pub_month": "月份不合理",
        "invalid_arxiv_id": "无效 arXiv ID",
        "suspicious_tag": "疑似误标（零重叠）",
        "missing_topic": "可能遗漏主题",
        "contradictory_tag": "矛盾标签",
        "folder_topic_mismatch": "文件夹与主题不匹配",
        "folder_content_mismatch": "文件夹与内容不匹配",
        "duplicate_title": "重复标题不同 arXiv",
    }
    for itype, cnt in sorted(issue_counts.items(), key=lambda x: -x[1]):
        label = type_labels.get(itype, itype)
        lines.append(f"| {label} | {cnt} |")

    lines.extend([
        "",
        "## 2. 标签层级合理性分析",
        "",
        "### 各层覆盖率",
        "",
    ])
    for layer, pct in ca.get("layer_coverage_pct", {}).items():
        lines.append(f"- **{layer}**：{pct}% 论文有标签")

    lines.extend([
        "",
        "### 热门 topic 分布",
        "",
    ])
    for topic, cnt in ca.get("top_topics", [])[:10]:
        lines.append(f"- {topic}：{cnt} 篇")

    lines.extend([
        "",
        f"- 未分类（Uncategorized）：{ca.get('uncategorized', 0)} 篇（{ca.get('no_topic_pct', 0)}% 无有效 topic）",
        f"- folder 与 topic 冗余：{ca.get('folder_redundant_count', 0)} 篇（{ca.get('folder_redundant_pct', 0)}%）",
        f"- 疑似误标总数：{ca.get('suspicious_tag_count', 0)}",
        "",
        "### 疑似误标 Top 标签",
        "",
    ])
    for key, cnt in list(ca.get("suspicious_by_tag", {}).items())[:15]:
        lines.append(f"- `{key}`：{cnt} 次")

    lines.extend(["", "### 疑似误标示例", ""])
    for ex in ca.get("suspicious_examples", [])[:15]:
        lines.append(
            f"- [{ex['layer']}] `{ex['tag']}` — {ex['title']}（{ex['folder']}/）"
        )

    lines.extend([
        "",
        "## 3. 文件夹分类 vs 内容一致性",
        "",
    ])
    for folder, cnt in list(ca.get("folder_mismatch_counts", {}).items())[:15]:
        lines.append(f"- `{folder}`：{cnt} 处不一致")

    lines.extend([
        "",
        "## 4. 需人工复核清单（Top 50）",
        "",
    ])
    review_list = sorted(
        report.get("papers", []),
        key=lambda x: (x["confidence"], -x["issue_count"]),
    )[:50]
    for i, r in enumerate(review_list, 1):
        issue_types = Counter(iss["type"] for iss in r["issues"])
        top_issues = ", ".join(t for t, _ in issue_types.most_common(3))
        lines.append(
            f"{i}. **{r['title'][:70]}** — 置信度 {r['confidence']}，"
            f"文件夹 `{r['folder']}`，问题：{top_issues or '无'}"
        )

    if report.get("online_results"):
        lines.extend(["", "## 5. 联网校验样本", ""])
        for vr in report["online_results"][:20]:
            status = "✓ 匹配" if vr.get("verified") and not vr.get("title_mismatch") else "⚠ 需关注"
            lines.append(f"- {status} **{vr.get('title', '')[:60]}**")
            lines.append(f"  - 来源：{', '.join(vr.get('sources_tried', []))}")
            if vr.get("title_similarity") is not None:
                lines.append(f"  - 标题相似度：{vr['title_similarity']}")
            if vr.get("title_mismatch"):
                tm = vr["title_mismatch"]
                lines.append(f"  - 本地：{tm.get('local', '')[:80]}")
                lines.append(f"  - 在线：{tm.get('online', '')[:80]}")
            if vr.get("tag_suggestions"):
                lines.append(f"  - 标签建议：{', '.join(vr['tag_suggestions'])}")

    lines.extend([
        "",
        "## 6. 整体结论与改进建议",
        "",
        "### 合理的类别设计",
        "- **topic / method / task / modality 四层分离**清晰，覆盖率较高，适合驾驶/具身 AI 领域。",
        "- **folder 层**作为用户手动分类的补充合理，与 FOLDER_TAGS 映射有效。",
        "- **keyword 层**（TF-IDF）能捕捉语料 distinctive 术语，但需归一化大小写。",
        "",
        "### 需改进的规则（paper_tagger.py）",
        "",
        "1. **收窄过宽 topic**：`Tracking`、`Simulation` 等模式过于宽泛，建议要求更多上下文词（如 multi-object tracking vs generic tracking）。",
        "2. **folder 回退逻辑**：当 folder 已指定 topic 但文本匹配到其他 topic 时，应保留文本匹配结果而非仅追加 folder tag（减少 folder_topic_mismatch）。",
        "3. **keyword 归一化**：合并大小写变体（如 Self-Supervised vs self-supervised），统一为小写或 canonical form。",
        "4. **增加 paper-video / paper-dynamic-geometry 到 FOLDER_TAGS**：目前大量论文在这些 catch-all 文件夹中，缺少 topic 回退。",
        "5. **矛盾检测前置**：对 LLM/VLM、RL 等标签要求最低关键词命中数，避免 regex 误匹配（如单独 `rl\\b` 匹配到其他词）。",
        "",
    ])

    near_dup = ca.get("near_duplicate_keywords", {})
    if near_dup:
        lines.extend(["### 近重复关键词", ""])
        for norm, variants in list(near_dup.items())[:10]:
            lines.append(f"- `{norm}`：{variants}")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def attach_validation_flags(papers: list[dict]) -> int:
    """Attach compact validation_flags[] to each paper. Returns count with warnings/errors."""
    title_groups: dict[str, list[dict]] = defaultdict(list)
    for p in papers:
        t = (p.get("title") or "").strip().lower()
        if t and len(t) > 10:
            title_groups[t].append(p)
    dup_titles: set[str] = set()
    for t, group in title_groups.items():
        arxiv_ids = {p.get("arxiv_id") for p in group if p.get("arxiv_id")}
        if len(group) > 1 and len(arxiv_ids) > 1:
            dup_titles.add(t)

    flagged = 0
    for p in papers:
        r = validate_paper(p, duplicate_titles=dup_titles)
        flags = sorted({
            i["type"] for i in r["issues"]
            if i.get("severity") in ("error", "warning")
        })
        p["validation_flags"] = flags
        if flags:
            flagged += 1
    return flagged
