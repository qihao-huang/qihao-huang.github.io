#!/usr/bin/env python3
"""
fetch_zhihu_stats.py — Fetch Zhihu profile stats and update index.html

Fetches voteup (赞同), thanked (喜欢), and favorited (收藏) counts from the
Zhihu member API and injects them into the homepage stats block.

Usage:
  python3 tools/fetch_zhihu_stats.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_DIR = SCRIPT_DIR.parent
INDEX_HTML = REPO_DIR / "index.html"
SNAPSHOT_JSON = SCRIPT_DIR / "snapshots" / "zhihu_stats.json"

ZHIHU_USER = "quiescencent"
ZHIHU_PROFILE = f"https://www.zhihu.com/people/{ZHIHU_USER}"
ZHIHU_API = (
    f"https://www.zhihu.com/api/v4/members/{ZHIHU_USER}"
    "?include=answer_count%2Carticles_count%2Cfollower_count%2Cfollowing_count"
    "%2Cvoteup_count%2Cthanked_count%2Cfavorited_count"
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

STATS_START = "<!-- ZHIHU_STATS_START -->"
STATS_END = "<!-- ZHIHU_STATS_END -->"


def api_get(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": ZHIHU_PROFILE,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def format_count(n: int) -> str:
    return f"{n:,}"


def load_cached_stats() -> dict[str, Any] | None:
    if not SNAPSHOT_JSON.exists():
        return None
    try:
        return json.loads(SNAPSHOT_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def fetch_stats() -> dict[str, Any]:
    data = api_get(ZHIHU_API)
    if data.get("error"):
        raise RuntimeError(f"Zhihu API error: {data['error']}")

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "profile_url": ZHIHU_PROFILE,
        "voteup_count": int(data.get("voteup_count") or 0),
        "thanked_count": int(data.get("thanked_count") or 0),
        "favorited_count": int(data.get("favorited_count") or 0),
    }


def render_stats_html(stats: dict[str, Any]) -> str:
    voteups = format_count(stats["voteup_count"])
    thanked = format_count(stats["thanked_count"])
    favorited = format_count(stats["favorited_count"])
    profile = stats.get("profile_url", ZHIHU_PROFILE)

    return (
        f'{STATS_START}\n'
        f'        <div class="zhihu-stats" aria-label="知乎互动数据">\n'
        f'          <a href="{profile}" target="_blank" rel="noopener noreferrer">\n'
        f'            <span><span class="zhihu-stat-val">{voteups}</span> 赞同</span>'
        f'<span class="zhihu-stat-sep">·</span>'
        f'<span><span class="zhihu-stat-val">{thanked}</span> 喜欢</span>'
        f'<span class="zhihu-stat-sep">·</span>'
        f'<span><span class="zhihu-stat-val">{favorited}</span> 收藏</span>\n'
        f"          </a>\n"
        f"        </div>\n"
        f"        {STATS_END}"
    )


def update_index_html(stats: dict[str, Any]) -> bool:
    html = INDEX_HTML.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(STATS_START) + r".*?" + re.escape(STATS_END),
        re.DOTALL,
    )
    replacement = render_stats_html(stats)
    if not pattern.search(html):
        print(f"ERROR: stats markers not found in {INDEX_HTML}", file=sys.stderr)
        return False

    new_html = pattern.sub(replacement, html, count=1)
    if new_html == html:
        print("No changes needed in index.html")
        return False

    INDEX_HTML.write_text(new_html, encoding="utf-8")
    return True


def save_snapshot(stats: dict[str, Any]) -> None:
    SNAPSHOT_JSON.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_JSON.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Zhihu stats for homepage")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and print stats without writing files",
    )
    args = parser.parse_args()

    try:
        stats = fetch_stats()
    except (urllib.error.URLError, RuntimeError, json.JSONDecodeError) as exc:
        cached = load_cached_stats()
        if cached:
            print(f"WARNING: fetch failed ({exc}), using cached snapshot", file=sys.stderr)
            stats = cached
        else:
            print(f"ERROR: fetch failed and no cache available: {exc}", file=sys.stderr)
            return 1

    print(
        f"赞同 {stats['voteup_count']:,} · "
        f"喜欢 {stats['thanked_count']:,} · "
        f"收藏 {stats['favorited_count']:,}"
    )

    if args.dry_run:
        print(render_stats_html(stats))
        return 0

    save_snapshot(stats)
    changed = update_index_html(stats)
    if changed:
        print(f"Updated {INDEX_HTML}")
    print(f"Snapshot saved to {SNAPSHOT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
