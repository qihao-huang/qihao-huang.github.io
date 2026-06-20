#!/usr/bin/env python3
"""
fix_titles.py — 审计并修复缓存中的垃圾/误解析标题。

用法:
  python tools/fix_titles.py --audit
  python tools/fix_titles.py --apply [--online] [--limit N]
"""

from __future__ import annotations
import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from paper_filter import (
    is_junk_title,
    junk_title_reasons,
    should_exclude,
    title_from_stem,
)
from generate_papers import (
    CACHE_FILE,
    load_cache,
    save_cache,
    load_fitz,
    resolve_junk_title,
    _clear_summary_cache,
)

REPORT_FILE = SCRIPT_DIR / "title_fix_report.json"


def count_junk(cache: dict) -> int:
    return sum(
        1 for p in cache.get("papers", {}).values()
        if is_junk_title(p.get("title"), p)
    )


def _collect_junk(cache: dict) -> list[dict]:
    rows: list[dict] = []
    for ckey, paper in cache.get("papers", {}).items():
        title = paper.get("title") or ""
        reasons = junk_title_reasons(title, paper)
        if not reasons:
            continue
        ex, ex_reason = should_exclude(paper)
        rows.append({
            "ckey": ckey,
            "title": title,
            "stem": paper.get("stem", ""),
            "rel_path": paper.get("rel_path", ""),
            "library": paper.get("library", ""),
            "arxiv_id": paper.get("arxiv_id"),
            "reasons": reasons,
            "excluded": ex,
            "exclude_reason": ex_reason,
        })
    return rows


def audit(cache: dict) -> dict:
    junk = _collect_junk(cache)
    by_reason: Counter = Counter()
    for row in junk:
        for r in row["reasons"]:
            by_reason[r] += 1

    fixable = [r for r in junk if not r["excluded"]]
    unfixable = [r for r in junk if r["excluded"]]

    report = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "total_cache": len(cache.get("papers", {})),
        "junk_total": len(junk),
        "junk_count": len(junk),
        "fixable": len(fixable),
        "unfixable_excluded": len(unfixable),
        "by_reason": dict(by_reason.most_common()),
        "examples": junk[:40],
        "unfixable_examples": unfixable[:20],
    }
    return report


def fix_one(paper: dict, cache: dict, fitz, *, online: bool) -> dict:
    """Re-parse title for one paper. Returns {status, old_title, new_title, method}."""
    old_title = paper.get("title") or ""
    reasons = junk_title_reasons(old_title, paper)
    if not reasons:
        return {"status": "ok", "old_title": old_title, "new_title": old_title, "method": None}

    ex, ex_reason = should_exclude(paper)
    if ex:
        return {
            "status": "excluded",
            "old_title": old_title,
            "new_title": old_title,
            "method": ex_reason,
            "reasons": reasons,
        }

    path_str = paper.get("path")
    pdf_path = Path(path_str) if path_str and Path(path_str).exists() else None

    method: str | None = None
    if resolve_junk_title(paper, pdf_path, fitz, cache, online):
        new_title = paper.get("title") or ""
        if paper.get("arxiv_id") and online:
            method = "arxiv_api"
        elif pdf_path:
            method = "pdf_reextract"
        else:
            method = "stem"
        paper["needs_review"] = bool(paper.get("_title_is_filename"))
        return {
            "status": "fixed",
            "old_title": old_title,
            "new_title": new_title,
            "method": method,
            "reasons": reasons,
        }

    # Last resort: stem without online
    fallback = title_from_stem(paper.get("stem", ""))
    if fallback and not is_junk_title(fallback, paper):
        paper["title"] = fallback
        paper["_title_is_filename"] = True
        _clear_summary_cache(paper)
        paper["needs_review"] = True
        return {
            "status": "fixed",
            "old_title": old_title,
            "new_title": fallback,
            "method": "stem",
            "reasons": reasons,
        }

    return {
        "status": "still_junk",
        "old_title": old_title,
        "new_title": paper.get("title") or old_title,
        "method": method,
        "reasons": reasons,
    }


def apply_fixes(cache: dict, *, online: bool, limit: int | None) -> dict:
    fitz = load_fitz()
    before_count = count_junk(cache)
    junk = _collect_junk(cache)
    targets = [r for r in junk if not r["excluded"]]
    if limit:
        targets = targets[:limit]

    results: list[dict] = []
    fixed = still_junk = excluded = 0
    by_method: Counter = Counter()

    print(f"\n[Fix] Processing {len(targets)} fixable junk titles (online={online}) ...")
    for i, row in enumerate(targets):
        ckey = row["ckey"]
        paper = cache["papers"].get(ckey)
        if not paper:
            continue
        if i % 10 == 0 or i == len(targets) - 1:
            print(f"\r  {i+1}/{len(targets)} (fixed {fixed}) ...", end="", flush=True)

        outcome = fix_one(paper, cache, fitz, online=online)
        outcome["ckey"] = ckey
        outcome["stem"] = row["stem"]
        outcome["rel_path"] = row["rel_path"]
        results.append(outcome)

        if outcome["status"] == "fixed":
            fixed += 1
            by_method[outcome.get("method") or "unknown"] += 1
        elif outcome["status"] == "still_junk":
            still_junk += 1
        elif outcome["status"] == "excluded":
            excluded += 1

        if fixed % 25 == 0 and fixed:
            save_cache(cache)

    print(f"\r  Done: fixed {fixed}, still junk {still_junk}, excluded {excluded}       ")
    save_cache(cache)

    after_count = count_junk(cache)
    return {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "junk_before": before_count,
        "junk_after": after_count,
        "processed": len(targets),
        "fixed": fixed,
        "still_junk": still_junk,
        "excluded": excluded,
        "by_method": dict(by_method),
        "results": results,
    }


def print_audit_report(report: dict) -> None:
    print("=" * 60)
    print("Title Audit Report")
    print("=" * 60)
    print(f"Cache entries     : {report['total_cache']}")
    print(f"Junk titles       : {report['junk_total']}")
    print(f"  Fixable         : {report['fixable']}")
    print(f"  Unfixable (excl): {report['unfixable_excluded']}")
    print("\nBy reason:")
    for reason, cnt in report["by_reason"].items():
        print(f"  {reason:25s} {cnt}")
    print("\nTop examples:")
    for row in report["examples"][:20]:
        t = row["title"][:80]
        print(f"  [{','.join(row['reasons'])}] {t!r}")
        print(f"    stem={row['stem']!r} arxiv={row['arxiv_id']}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit and fix junk paper titles in cache")
    ap.add_argument("--audit", action="store_true", help="Scan and report junk titles")
    ap.add_argument("--apply", action="store_true", help="Re-parse and fix junk titles")
    ap.add_argument("--online", action="store_true", help="Use arXiv/S2/Crossref for fixes")
    ap.add_argument("--limit", type=int, default=None, help="Max papers to fix")
    args = ap.parse_args()

    if not args.audit and not args.apply:
        args.audit = True

    cache = load_cache()
    print(f"[Cache] Loaded {len(cache.get('papers', {}))} entries")

    if args.audit:
        report = audit(cache)
        REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print_audit_report(report)
        print(f"\nReport saved: {REPORT_FILE}")

    if args.apply:
        before = count_junk(cache)
        print(f"[Regression] Junk titles before fix: {before}")
        fix_report = apply_fixes(cache, online=args.online, limit=args.limit)
        after = count_junk(cache)
        fix_report_path = SCRIPT_DIR / "title_fix_apply_report.json"
        fix_report_path.write_text(
            json.dumps(fix_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\nApply report: fixed={fix_report['fixed']}, still_junk={fix_report['still_junk']}")
        print(f"[Regression] Junk titles after fix: {after} (before={before})")
        if after != 0:
            print(f"WARNING: {after} junk titles remain!", file=sys.stderr)
        else:
            print("[Regression] PASS: 0 junk titles")
        print(f"By method: {fix_report['by_method']}")
        print(f"Saved: {fix_report_path}")


if __name__ == "__main__":
    main()
