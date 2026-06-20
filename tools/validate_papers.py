#!/usr/bin/env python3
"""
validate_papers.py — CLI for secondary paper metadata & tag validation.

Usage:
  tools/.venv/bin/python tools/validate_papers.py              # offline, fast
  tools/.venv/bin/python tools/validate_papers.py --online     # + online verify
  tools/.venv/bin/python tools/validate_papers.py --online --limit 50
  tools/.venv/bin/python tools/validate_papers.py --sample 100
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from paper_validator import (
    CACHE_FILE,
    load_papers_from_cache,
    validate_all_papers,
    write_validation_summary,
)

REPORT_JSON = SCRIPT_DIR / "validation_report.json"
REPORT_MD = SCRIPT_DIR / "validation_summary.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate paper metadata and tags")
    parser.add_argument("--online", action="store_true", help="Online verify ambiguous papers")
    parser.add_argument("--limit", type=int, default=None, help="Max papers for online verify")
    parser.add_argument("--sample", type=int, default=None, help="Random sample size")
    parser.add_argument("--cache", type=Path, default=CACHE_FILE, help="Cache JSON path")
    args = parser.parse_args()

    if not args.cache.exists():
        print(f"ERROR: cache not found: {args.cache}", file=sys.stderr)
        print("Run tools/generate_papers.py first.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading papers from {args.cache} ...")
    papers = load_papers_from_cache(args.cache)
    print(f"  {len(papers)} papers (after exclusion filter)")

    mode = "offline + online" if args.online else "offline only"
    print(f"Running validation ({mode}) ...")
    report = validate_all_papers(
        papers,
        online=args.online,
        limit=args.limit,
        sample=args.sample,
    )

    # Write structured report (trim online_results in per-paper for size)
    report_out = dict(report)
    report_out["papers"] = [
        {k: v for k, v in p.items() if k != "online_verify"}
        for p in report["papers"]
    ]
    REPORT_JSON.write_text(
        json.dumps(report_out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_validation_summary(report, REPORT_MD)

    print(f"\nDone.")
    print(f"  Papers validated : {report['total_papers']}")
    print(f"  Avg confidence   : {report['avg_confidence']}")
    print(f"  Need review      : {report['papers_needing_review']}")
    print(f"  Online verified  : {report['online_verified']}")
    print(f"  Report JSON      : {REPORT_JSON}")
    print(f"  Summary MD       : {REPORT_MD}")

    ic = report.get("issue_counts", {})
    if ic:
        print("\n  Top issues:")
        for t, c in sorted(ic.items(), key=lambda x: -x[1])[:8]:
            print(f"    {t}: {c}")


if __name__ == "__main__":
    main()
