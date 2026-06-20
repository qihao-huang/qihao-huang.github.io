#!/usr/bin/env python3
"""
generate_fav.py — Chrome bookmarks + Zhihu favorites → fav.html dashboard

Reads Chrome Profile 1 bookmarks (topics/ only, excluding SANY), fetches Zhihu
favlists, assigns content tags (rule-based + optional LLM), renders fav.html.

Usage:
  python3 tools/generate_fav.py [--no-zhihu] [--llm-tags] [--llm-limit N]
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_DIR = SCRIPT_DIR.parent
OUTPUT_HTML = REPO_DIR / "fav.html"

sys.path.insert(0, str(SCRIPT_DIR))
from fav_tagger import tag_items, tag_stats

CHROME_BOOKMARKS = (
    Path.home()
    / "Library/Application Support/Google/Chrome/Profile 1/Bookmarks"
)

ZHIHU_USER = "quiescencent"
ZHIHU_FAVLISTS = f"https://www.zhihu.com/api/v4/members/{ZHIHU_USER}/favlists"
ZHIHU_CONTENTS = "https://www.zhihu.com/api/v4/collections/{id}/contents"

USER_AGENT = "PersonalFavDashboard/1.0 (research tool)"
CHROME_EPOCH_OFFSET = 11644473600
API_DELAY = 0.4


def detect_source(url: str, platform: str) -> str:
    if platform == "zhihu":
        return "Zhihu"
    lower = url.lower()
    if "github.com" in lower:
        return "GitHub"
    if "huggingface.co" in lower:
        return "HuggingFace"
    if "zhuanlan.zhihu.com" in lower or "zhihu.com" in lower:
        return "Zhihu"
    if "arxiv.org" in lower:
        return "arXiv"
    if "mp.weixin.qq.com" in lower:
        return "WeChat"
    if "nvidia" in lower or "nvlabs" in lower:
        return "NVIDIA"
    if "deepmind" in lower:
        return "DeepMind"
    if "apollo.baidu.com" in lower:
        return "Apollo"
    return "Other"


def chrome_ts(micro: int | str | None) -> int:
    if not micro:
        return 0
    try:
        return int(int(micro) / 1_000_000 - CHROME_EPOCH_OFFSET)
    except (TypeError, ValueError):
        return 0


def normalize_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host or "unknown"
    except Exception:
        return "unknown"


def is_sany_path(path: tuple[str, ...]) -> bool:
    return any("SANY" in p.upper() for p in path)


def is_topics_path(path: tuple[str, ...]) -> bool:
    return "topics" in path


def extract_topic(path: tuple[str, ...]) -> str:
    parts = [p for p in path if p and p not in ("书签栏", "other", "mobile", "synced")]
    if "topics" in parts:
        idx = parts.index("topics")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return parts[-1] if parts else "other"


def folder_label(path: tuple[str, ...]) -> str:
    parts = [p for p in path if p and p not in ("书签栏", "other", "mobile", "synced")]
    if "topics" in parts:
        idx = parts.index("topics")
        return "/".join(parts[idx:])
    return "/".join(parts) if parts else "other"


def api_get(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def paginate(url_template: str, **fmt: Any) -> list[dict[str, Any]]:
    offset = 0
    items: list[dict[str, Any]] = []
    while True:
        url = url_template.format(offset=offset, **fmt)
        data = api_get(url)
        items.extend(data.get("data") or [])
        paging = data.get("paging") or {}
        if paging.get("is_end", True):
            break
        offset += int(paging.get("limit") or 20)
        time.sleep(API_DELAY)
    return items


def zhihu_title(item: dict[str, Any]) -> str:
    if item.get("title"):
        return str(item["title"]).strip()
    q = item.get("question") or {}
    if isinstance(q, dict) and q.get("title"):
        return str(q["title"]).strip()
    excerpt = (item.get("excerpt") or "").strip()
    if excerpt:
        return excerpt[:120]
    return item.get("type") or "知乎收藏"


def load_chrome_bookmarks() -> list[dict[str, Any]]:
    if not CHROME_BOOKMARKS.exists():
        print(f"WARNING: Chrome bookmarks not found: {CHROME_BOOKMARKS}", file=sys.stderr)
        return []

    raw = json.loads(CHROME_BOOKMARKS.read_text(encoding="utf-8"))
    out: list[dict[str, Any]] = []

    def walk(node: dict[str, Any], path: tuple[str, ...] = ()) -> None:
        if is_sany_path(path):
            return
        ntype = node.get("type")
        if ntype == "url":
            if not is_topics_path(path):
                return
            url = (node.get("url") or "").strip()
            if not url or url.startswith("javascript:"):
                return
            title = (node.get("name") or url).strip()
            out.append(
                {
                    "id": f"chrome-{hash(url) & 0xFFFFFFFF:08x}",
                    "title": title,
                    "url": url,
                    "platform": "chrome",
                    "folder": folder_label(path),
                    "folder_topic": extract_topic(path),
                    "domain": normalize_domain(url),
                    "date": chrome_ts(node.get("date_added")),
                    "source": detect_source(url, "chrome"),
                }
            )
        elif ntype == "folder":
            name = node.get("name") or ""
            child_path = path + (name,) if name else path
            if is_sany_path(child_path):
                return
            for child in node.get("children") or []:
                walk(child, child_path)

    for root in raw.get("roots", {}).values():
        if isinstance(root, dict):
            walk(root, (root.get("name") or "",))

    return out


def load_zhihu_favorites() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        lists = paginate(ZHIHU_FAVLISTS + "?offset={offset}&limit=20")
    except urllib.error.URLError as exc:
        print(f"WARNING: Zhihu favlists fetch failed: {exc}", file=sys.stderr)
        return out

    for lst in lists:
        list_id = lst.get("id")
        list_title = (lst.get("title") or "未命名").strip()
        if not list_id:
            continue
        try:
            contents = paginate(
                ZHIHU_CONTENTS + "?offset={offset}&limit=20", id=list_id
            )
        except urllib.error.URLError as exc:
            print(f"WARNING: Zhihu contents for {list_title} failed: {exc}", file=sys.stderr)
            continue

        for item in contents:
            url = (item.get("url") or "").strip()
            if not url:
                continue
            title = zhihu_title(item)
            out.append(
                {
                    "id": f"zhihu-{item.get('id', hash(url) & 0xFFFFFFFF)}",
                    "title": title,
                    "url": url,
                    "platform": "zhihu",
                    "folder": f"zhihu/{list_title}",
                    "folder_topic": list_title,
                    "domain": normalize_domain(url),
                    "date": int(item.get("collect_time") or item.get("created_time") or 0),
                    "source": "Zhihu",
                }
            )
        time.sleep(API_DELAY)

    return out


def dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for item in items:
        key = re.sub(r"#.*", "", item["url"].rstrip("/")).lower()
        prev = seen.get(key)
        if prev is None:
            seen[key] = item
            continue
        if item.get("date", 0) > prev.get("date", 0):
            seen[key] = item
        elif item.get("date", 0) == prev.get("date", 0) and len(item.get("title", "")) > len(
            prev.get("title", "")
        ):
            seen[key] = item
    return list(seen.values())


def item_for_html(item: dict[str, Any]) -> dict[str, Any]:
    url = item["url"]
    stable_id = hashlib.sha256(
        re.sub(r"#.*", "", url.rstrip("/")).lower().encode()
    ).hexdigest()[:16]
    out: dict[str, Any] = {
        "id": stable_id,
        "title": item["title"],
        "url": url,
        "domain": item.get("domain", ""),
        "date": item.get("date") or 0,
        "tags": item.get("tags") or [],
    }
    if item.get("primary_tag"):
        out["primary_tag"] = item["primary_tag"]
    return out


def compute_payload(items: list[dict[str, Any]], *, tagging_mode: str = "rule") -> dict[str, Any]:
    stats = tag_stats(items)

    by_month: dict[str, int] = defaultdict(int)
    tag_by_month: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for item in items:
        ts = item.get("date") or 0
        if ts <= 0:
            continue
        month = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m")
        by_month[month] += 1
        for tag in item.get("tags") or []:
            tag_by_month[month][tag] += 1

    months = sorted(by_month.keys())
    timeline = [{"month": m, "count": by_month[m]} for m in months]

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "tagging": tagging_mode,
        "total": len(items),
        "tags": stats["tags"],
        "tag_count": stats["tag_count"],
        "timeline": timeline,
        "tag_timeline": {m: dict(tag_by_month[m]) for m in months},
        "items": sorted(
            (item_for_html(i) for i in items),
            key=lambda x: (-(x.get("date") or 0), x["title"]),
        ),
    }


def load_template() -> str:
    spec = importlib.util.spec_from_file_location(
        "_fav_html_template", SCRIPT_DIR / "_fav_html_template.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_fav_html_template"] = mod
    spec.loader.exec_module(mod)
    return mod.HTML_TEMPLATE


def render_html(payload: dict[str, Any]) -> str:
    template = load_template()
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    html = template.replace("__TOTAL__", str(payload["total"]))
    html = html.replace("__GENERATED_AT__", payload["generated_at"])
    html = html.replace("__TAGGING__", payload.get("tagging", "rule"))
    html = html.replace("__DATA_JSON__", data_json)
    return html


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate fav.html from bookmarks + Zhihu")
    parser.add_argument("--no-zhihu", action="store_true", help="Skip Zhihu API fetch")
    parser.add_argument("--llm-tags", action="store_true", help="Use LLM to refine tags (needs OPENAI_API_KEY)")
    parser.add_argument("--llm-limit", type=int, default=None, help="Max items to LLM-tag this run")
    args = parser.parse_args()

    print("[chrome] Reading bookmarks (topics/ only, SANY excluded) ...")
    chrome_items = load_chrome_bookmarks()
    print(f"  {len(chrome_items)} links")

    zhihu_items: list[dict[str, Any]] = []
    if not args.no_zhihu:
        print("[zhihu] Fetching favlists ...")
        zhihu_items = load_zhihu_favorites()
        print(f"  {len(zhihu_items)} items")

    merged = dedupe_items(chrome_items + zhihu_items)
    use_llm = args.llm_tags or bool(os.environ.get("OPENAI_API_KEY"))
    if use_llm and not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: --llm-tags set but OPENAI_API_KEY missing; using rules only", file=sys.stderr)
        use_llm = False

    merged = tag_items(merged, use_llm=use_llm, llm_limit=args.llm_limit)
    tagging_mode = "llm+rule" if use_llm and os.environ.get("OPENAI_API_KEY") else "rule"
    payload = compute_payload(merged, tagging_mode=tagging_mode)

    print(f"[html] Rendering fav.html ({payload['total']} items, {payload['tag_count']} tags) ...")
    html = render_html(payload)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    size_kb = OUTPUT_HTML.stat().st_size / 1024

    print(f"\n{'='*50}")
    print(f"Total items   : {payload['total']}")
    print(f"Tags          : {payload['tag_count']}  (mode: {payload['tagging']})")
    print(f"Output        : {OUTPUT_HTML}  ({size_kb:.0f} KB)")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
