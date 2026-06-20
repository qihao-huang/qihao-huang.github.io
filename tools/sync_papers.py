#!/usr/bin/env python3
"""Pre-flight detection and post-generation sanity checks for paper sync."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_DIR = SCRIPT_DIR.parent
CACHE_FILE = SCRIPT_DIR / ".papers_cache.json"
OUTPUT_HTML = REPO_DIR / "papers.html"

LIBRARIES: dict[str, Path] = {
    "auto_ai": Path.home()
    / "Library/Mobile Documents/com~apple~CloudDocs/docs/papers/auto_ai",
    "physical_ai": Path.home()
    / "Library/Mobile Documents/com~apple~CloudDocs/docs/papers/physical_ai",
}


def paper_cache_key(pdf_path: Path, stat) -> str:
    return f"{pdf_path}|{stat.st_mtime:.0f}|{stat.st_size}"


def path_from_cache_key(ckey: str) -> str:
    return ckey.rsplit("|", 2)[0]


def detect_changes() -> dict[str, int]:
    cache: dict = {"papers": {}}
    if CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass

    cached_keys: set[str] = set(cache.get("papers", {}).keys())
    paths_in_cache: dict[str, str] = {}
    for ckey in cached_keys:
        paths_in_cache[path_from_cache_key(ckey)] = ckey

    new = updated = total = 0
    for lib_path in LIBRARIES.values():
        if not lib_path.exists():
            continue
        for pdf in sorted(lib_path.rglob("*.pdf")):
            if "/_excluded/" in str(pdf) or "\\_excluded\\" in str(pdf):
                continue
            try:
                stat = pdf.stat()
            except OSError:
                continue
            total += 1
            ckey = paper_cache_key(pdf, stat)
            path_str = str(pdf)
            if ckey in cached_keys:
                continue
            if path_str in paths_in_cache:
                updated += 1
            else:
                new += 1

    return {"new": new, "updated": updated, "total": total}


def sanity_check_html(max_year: int = 2026) -> tuple[int, list[int]]:
    if not OUTPUT_HTML.exists():
        raise FileNotFoundError(f"Missing output: {OUTPUT_HTML}")
    html = OUTPUT_HTML.read_text(encoding="utf-8")
    years = [int(y) for y in re.findall(r'"pub_year"\s*:\s*(\d{4})', html)]
    bad = sorted({y for y in years if y > max_year})
    return len(years), bad


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--detect-only":
        stats = detect_changes()
        print(
            f"NEW={stats['new']} UPDATED={stats['updated']} TOTAL={stats['total']}",
            flush=True,
        )
        return 0

    if len(sys.argv) > 1 and sys.argv[1] == "--sanity-check":
        count, bad = sanity_check_html()
        if bad:
            print(f"FAIL: {len(bad)} papers with pub_year > 2026: {bad[:10]}", file=sys.stderr)
            return 1
        print(f"OK: {count} pub_year entries checked")
        return 0

    print("Usage: sync_papers.py --detect-only | --sanity-check", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
