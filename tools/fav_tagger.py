"""
fav_tagger.py — LLM + rule-based tagging for Chrome/Zhihu favorites.

Tags are content-derived (not bookmark folders). Results cached in .fav_cache.json.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

CACHE_FILE = Path(__file__).parent / ".fav_cache.json"
PROMPT_VERSION = "v2"
DEFAULT_MODEL = os.environ.get("FAV_LLM_MODEL", os.environ.get("SUMMARY_LLM_MODEL", "gpt-4o-mini"))
BATCH_SIZE = 25

META_TAGS = frozenset({"Survey / Review", "Tutorial / Course", "Blog / Notes", "Paper / arXiv"})

# tag → regex patterns (title + url)
TAG_PATTERNS: dict[str, list[str]] = {
    "VLA": [
        r"\bvla\b",
        r"vision.language.action",
        r"openpi",
        r"galaxea",
        r"lingbot",
        r"unifolm",
        r"gr00t",
        r"视觉.?语言.?动作",
        r"opendrivevla",
        r"\borion\b",
    ],
    "Humanoid": [r"\bhumanoid\b", r"legged robot", r"whole.body", r"人形"],
    "World Model": [
        r"world model",
        r"\bwam\b",
        r"leworld",
        r"fast-wam",
        r"wan2",
        r"世界模型",
        r"\bepona\b",
    ],
    "Autonomous Driving": [
        r"\bad\b",
        r"autonomous driv",
        r"end.to.end driv",
        r"self.driv",
        r"自动驾驶",
        r"端到端",
        r"opendrive",
        r"bevfusion",
        r"sparsebev",
    ],
    "Motion Planning": [
        r"motion plan",
        r"trajectory plan",
        r"\bplanner\b",
        r"\bpnc\b",
        r"diffusiondrive",
        r"运动规划",
        r"轨迹规划",
    ],
    "Perception": [
        r"\bbev\b",
        r"3d detect",
        r"occupancy",
        r"sparse4d",
        r"perception",
        r"detr",
        r"3d目标检测",
        r"3d检测",
        r"测距",
        r"感知",
    ],
    "Reinforcement Learning": [
        r"\bgrpo\b",
        r"\bppo\b",
        r"reinforcement learn",
        r"\brl\b",
        r"verl",
        r"强化学习",
    ],
    "LLM / VLM": [
        r"\bllm\b",
        r"\bvlm\b",
        r"vision.language model",
        r"\bqwen\b",
        r"glm",
        r"flamingo",
        r"大模型",
        r"视觉.?语言",
    ],
    "NVIDIA / Isaac": [
        r"\bnvidia\b",
        r"\bisaaac\b",
        r"nvlabs",
        r"cosmos",
        r"jetson",
        r"英伟达",
        r"isaac lab",
        r"\bcuda\b",
        r"cudnn",
    ],
    "Imitation Learning": [
        r"imitation learn",
        r"lerobot",
        r"behavior clon",
        r"demonstration",
        r"模仿学习",
    ],
    "Simulation": [r"\bcarla\b", r"\bnuplan\b", r"isaac sim", r"closed.loop sim"],
    "Infrastructure": [r"\binfra\b", r"data (loop|engine|pipeline)", r"middleware", r"deployment"],
    "Robot Manipulation": [r"manipul", r"grasp", r"pick.and.place", r"dexterous", r"灵巧"],
    "Foundation Model": [r"foundation model", r"physical ai", r"github.com"],
    "Survey / Review": [r"\bsurvey\b", r"综述", r"\breview paper\b"],
    "Tutorial / Course": [
        r"\btutorial\b",
        r"教程",
        r"\bcourse\b",
        r"入门",
        r"路线图",
        r"getting started",
    ],
    "Blog / Notes": [r"笔记", r"解析", r"一文看懂", r"聊聊", r"分享", r"\bnote\b"],
}


def _cache_key(item: dict[str, Any]) -> str:
    url = re.sub(r"#.*", "", item["url"].rstrip("/")).lower()
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def load_cache() -> dict[str, Any]:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"entries": {}, "prompt_version": PROMPT_VERSION}


def save_cache(cache: dict[str, Any]) -> None:
    cache["prompt_version"] = PROMPT_VERSION
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def _match_text(text: str) -> list[str]:
    text = text.lower()
    hits: list[str] = []
    for tag, patterns in TAG_PATTERNS.items():
        if any(re.search(p, text, re.I) for p in patterns):
            hits.append(tag)
    return hits


def rule_tags(item: dict[str, Any]) -> list[str]:
    blob = " ".join(
        filter(None, [item.get("title", ""), item.get("url", ""), item.get("domain", "")])
    )
    tags = _match_text(blob)
    topic = [t for t in tags if t not in META_TAGS]
    meta = [t for t in tags if t in META_TAGS]
    if topic:
        out = topic[:3] + meta[:1]
    elif meta:
        out = meta[:2]
    else:
        domain = (item.get("domain") or "").lower()
        if "github.com" in domain:
            out = ["Foundation Model"]
        elif "arxiv" in domain:
            out = ["Paper / arXiv"]
        else:
            out = ["General Tech"]
    return out[:4]


def _llm_call(prompt: str, *, model: str, max_tokens: int = 2000) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.15,
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return (data["choices"][0]["message"]["content"] or "").strip()


def _parse_llm_json(raw: str) -> list[dict[str, Any]]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw)
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    if isinstance(data, list):
        return data
    raise ValueError("unexpected LLM JSON shape")


def _llm_batch_prompt(batch: list[dict[str, Any]]) -> str:
    lines = []
    for it in batch:
        lines.append(
            {
                "id": it["id"],
                "title": it["title"][:160],
                "url": it["url"][:200],
                "domain": it.get("domain", ""),
                "hints": rule_tags(it),
            }
        )
    return f"""你是技术收藏分类助手。为每条收藏分配 1-3 个英文研究标签（简短、可复用，跨条目一致）。

标签应描述「内容领域/技术方向」，例如：VLA, Humanoid, World Model, Autonomous Driving, Motion Planning, Perception, Reinforcement Learning, LLM / VLM, NVIDIA / Isaac, Simulation, Infrastructure, Robot Manipulation, Foundation Model, Survey / Review, Tutorial / Course, Blog / Notes, Paper / arXiv 等。
优先分配具体技术主题；仅当内容确实是综述/教程/笔记时再使用 Survey / Review、Tutorial / Course、Blog / Notes。
不要直接使用用户的文件夹名作为标签；根据标题与 URL 判断实质内容。

输入：
{json.dumps(lines, ensure_ascii=False)}

只输出 JSON 数组，每项格式：{{"id":"...", "tags":["...", "..."]}}
"""


def llm_tag_batch(batch: list[dict[str, Any]], *, model: str) -> dict[str, list[str]]:
    prompt = _llm_batch_prompt(batch)
    raw = _llm_call(prompt, model=model)
    parsed = _parse_llm_json(raw)
    out: dict[str, list[str]] = {}
    for row in parsed:
        iid = row.get("id")
        tags = row.get("tags") or []
        if not iid or not isinstance(tags, list):
            continue
        cleaned = [str(t).strip() for t in tags if str(t).strip()][:3]
        if cleaned:
            out[str(iid)] = cleaned
    return out


def tag_items(
    items: list[dict[str, Any]],
    *,
    use_llm: bool = True,
    model: str = DEFAULT_MODEL,
    llm_limit: int | None = None,
) -> list[dict[str, Any]]:
    cache = load_cache()
    entries: dict[str, Any] = cache.setdefault("entries", {})

    for item in items:
        key = _cache_key(item)
        cached = entries.get(key)
        if (
            cached
            and cached.get("prompt_version") == PROMPT_VERSION
            and cached.get("tags")
        ):
            item["tags"] = list(cached["tags"])
            item["primary_tag"] = item["tags"][0]
            continue
        tags = rule_tags(item)
        item["tags"] = tags
        item["primary_tag"] = tags[0]
        entries[key] = {"tags": tags, "prompt_version": PROMPT_VERSION, "source": "rule"}

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not use_llm or not api_key:
        save_cache(cache)
        return items

    pending = [
        it
        for it in items
        if entries.get(_cache_key(it), {}).get("source") != "llm"
    ]
    if llm_limit is not None:
        pending = pending[:llm_limit]

    print(f"[tags] LLM tagging {len(pending)} items (batch={BATCH_SIZE}) ...")
    tagged = 0
    for i in range(0, len(pending), BATCH_SIZE):
        batch = pending[i : i + BATCH_SIZE]
        try:
            result = llm_tag_batch(batch, model=model)
        except (RuntimeError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
            print(f"  WARNING: LLM batch failed: {exc}")
            break
        for it in batch:
            tags = result.get(it["id"])
            if not tags:
                continue
            it["tags"] = tags
            it["primary_tag"] = tags[0]
            key = _cache_key(it)
            entries[key] = {"tags": tags, "prompt_version": PROMPT_VERSION, "source": "llm"}
            tagged += 1
        save_cache(cache)
        time.sleep(0.3)

    print(f"  LLM tagged: {tagged}")
    save_cache(cache)
    return items


def tag_stats(items: list[dict[str, Any]]) -> dict[str, Any]:
    counter: Counter[str] = Counter()
    for item in items:
        for t in item.get("tags") or []:
            counter[t] += 1
    return {
        "tag_count": len(counter),
        "tags": [{"name": k, "count": v} for k, v in counter.most_common()],
    }
