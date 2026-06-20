#!/usr/bin/env python3
"""Regression tests for is_junk_title() — Chinese annotation & boilerplate patterns."""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from paper_filter import is_junk_title, junk_title_reasons

CASES: list[tuple[str, bool, str]] = [
    ("动机：作者试图探究，能否单靠开源机器人数据", True, "cn_motivation"),
    ("观察：该方法在仿真中表现良好", True, "cn_observation"),
    ("提出：一种新的 VLA 框架", True, "cn_propose"),
    ("该论文的核心贡献在于...", True, "cn_contribution"),
    ("Published as a conference paper at RLC 2024", True, "conf_paper_boilerplate"),
    ("详见摘要", True, "cn_see_abstract"),
    ("Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks", False, ""),
    ("DINO: DETR with Improved DeNoising Anchor Boxes for End-to-End Object Detection", False, ""),
    ("Under review as a conference paper at NeurIPS 2025", True, "under_review_conf"),
]


def main() -> int:
    failed = 0
    for title, expect_junk, expect_reason in CASES:
        got = is_junk_title(title)
        reasons = junk_title_reasons(title)
        if got != expect_junk:
            print(f"FAIL is_junk: {title[:60]!r} expect={expect_junk} got={got}")
            failed += 1
        elif expect_junk and expect_reason and expect_reason not in reasons:
            print(f"FAIL reason: {title[:60]!r} expect {expect_reason} in {reasons}")
            failed += 1
        else:
            print(f"OK  {title[:55]!r}")
    if failed:
        print(f"\n{failed} test(s) failed")
        return 1
    print(f"\nAll {len(CASES)} tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
