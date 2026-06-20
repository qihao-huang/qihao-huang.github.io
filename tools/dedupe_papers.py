"""
dedupe_papers.py — 论文库条目去重（生成 papers.html 时使用）

同一 PDF 出现在不同文件夹视为重复。主键优先级：
  1. 有效 arxiv_id
  2. 规范化标题
  3. 标题相似度 > 0.92（模糊匹配）
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from paper_filter import is_valid_arxiv_id, is_junk_title, recover_arxiv_from_stem

FUZZY_THRESHOLD = 0.92
_VERSION_SUFFIX = re.compile(r"\s*v\d+\s*$", re.I)

# 文件夹优先级（数值越小越优先）
_FOLDER_RANK: dict[str, int] = {
    "paper-HKU": 0,
}


def normalize_title(title: str | None) -> str:
    """小写、去标点、合并空白、去掉版本后缀。"""
    if not title:
        return ""
    t = title.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = _VERSION_SUFFIX.sub("", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def title_similarity(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    stop = {"the", "a", "an", "of", "in", "is", "for", "and", "with", "on", "via", "using", "from"}
    ta = set(re.findall(r"\w+", a.lower())) - stop
    tb = set(re.findall(r"\w+", b.lower())) - stop
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def _arxiv_from_pdf(paper: dict) -> bool:
    """arxiv_id 来自 PDF/文件名，而非在线猜测。"""
    aid = paper.get("arxiv_id")
    if not is_valid_arxiv_id(aid):
        return False
    stem = paper.get("stem") or ""
    if re.match(rf"^{re.escape(aid)}", stem):
        return True
    if recover_arxiv_from_stem(stem):
        return True
    src = paper.get("pub_date_source")
    if src in ("pdf", "arxiv_id", "filename"):
        return True
    return False


def _folder_rank(paper: dict) -> int:
    rel = (paper.get("rel_path") or "").replace("\\", "/")
    folder = paper.get("folder") or ""
    if folder in _FOLDER_RANK:
        return _FOLDER_RANK[folder]
    if rel.startswith("paper-HKU/"):
        return 0
    if folder.startswith("paper-"):
        return 1
    return 2


def _entry_score(paper: dict) -> tuple:
    """分数越高越应保留。"""
    abstract = paper.get("abstract") or ""
    return (
        1 if len(abstract) > 50 else 0,
        len(abstract),
        1 if _arxiv_from_pdf(paper) else 0,
        0 if is_junk_title(paper.get("title"), paper) else 1,
        -_folder_rank(paper),
        -len(paper.get("rel_path") or ""),
        paper.get("mtime") or 0,
        paper.get("size") or 0,
    )


def _merge_metadata(keeper: dict, other: dict) -> None:
    """将副本中有价值的字段合并到保留条目。"""
    if not keeper.get("abstract") and other.get("abstract"):
        keeper["abstract"] = other["abstract"]
    if not is_valid_arxiv_id(keeper.get("arxiv_id")) and is_valid_arxiv_id(other.get("arxiv_id")):
        keeper["arxiv_id"] = other["arxiv_id"]
        if other.get("pub_date_source"):
            keeper["pub_date_source"] = other["pub_date_source"]
    if not keeper.get("pub_year") and other.get("pub_year"):
        keeper["pub_year"] = other["pub_year"]
        keeper["pub_month"] = other.get("pub_month")
        if other.get("pub_date_source"):
            keeper["pub_date_source"] = other["pub_date_source"]
    if keeper.get("needs_review") and not other.get("needs_review"):
        keeper["needs_review"] = False


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def union(self, i: int, j: int) -> None:
        ri, rj = self.find(i), self.find(j)
        if ri != rj:
            self.parent[rj] = ri


def _arxiv_conflict(aid_i: str | None, aid_j: str | None) -> bool:
    return bool(aid_i and aid_j and aid_i != aid_j)


def _find_duplicate_groups(papers: list[dict]) -> list[list[int]]:
    n = len(papers)
    if n == 0:
        return []

    uf = _UnionFind(n)
    arxiv_ids = [
        p.get("arxiv_id") if is_valid_arxiv_id(p.get("arxiv_id")) else None
        for p in papers
    ]
    norm_titles = [normalize_title(p.get("title")) for p in papers]

    arxiv_map: dict[str, list[int]] = defaultdict(list)
    for i, aid in enumerate(arxiv_ids):
        if aid:
            arxiv_map[aid].append(i)
    for indices in arxiv_map.values():
        for j in indices[1:]:
            uf.union(indices[0], j)

    title_map: dict[str, list[int]] = defaultdict(list)
    for i, nt in enumerate(norm_titles):
        if nt and len(nt) > 10:
            title_map[nt].append(i)
    for indices in title_map.values():
        if len(indices) < 2:
            continue
        aids = {arxiv_ids[i] for i in indices if arxiv_ids[i]}
        if len(aids) <= 1:
            for j in indices[1:]:
                uf.union(indices[0], j)

    for i in range(n):
        for j in range(i + 1, n):
            if uf.find(i) == uf.find(j):
                continue
            if _arxiv_conflict(arxiv_ids[i], arxiv_ids[j]):
                continue
            if title_similarity(papers[i].get("title"), papers[j].get("title")) > FUZZY_THRESHOLD:
                uf.union(i, j)

    groups_map: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        groups_map[uf.find(i)].append(i)
    return list(groups_map.values())


def dedupe_papers(papers: list[dict]) -> list[dict]:
    """去重并返回保留条目；副本路径写入 alternate_paths。"""
    if not papers:
        return []

    groups = _find_duplicate_groups(papers)
    kept: list[dict] = []

    for indices in groups:
        members = [papers[i] for i in indices]
        if len(members) == 1:
            kept.append(members[0])
            continue

        best = max(members, key=_entry_score)
        keeper = dict(best)
        alternates: list[str] = []

        for m in members:
            if m is best:
                continue
            rel = m.get("rel_path") or m.get("path") or ""
            if rel and rel not in alternates:
                alternates.append(rel)
            _merge_metadata(keeper, m)

        if alternates:
            keeper["alternate_paths"] = alternates
        kept.append(keeper)

    return kept


def audit_duplicates(papers: list[dict]) -> dict[str, Any]:
    """统计重复组：按 arxiv_id、规范化标题，及合并后的去重组。"""
    arxiv_groups: dict[str, list[dict]] = defaultdict(list)
    title_groups: dict[str, list[dict]] = defaultdict(list)

    for p in papers:
        aid = p.get("arxiv_id")
        if is_valid_arxiv_id(aid):
            arxiv_groups[aid].append(p)
        nt = normalize_title(p.get("title"))
        if nt and len(nt) > 10:
            title_groups[nt].append(p)

    arxiv_dup = {k: v for k, v in arxiv_groups.items() if len(v) > 1}
    title_dup = {k: v for k, v in title_groups.items() if len(v) > 1}

    merge_groups = [g for g in _find_duplicate_groups(papers) if len(g) > 1]
    merge_groups.sort(key=len, reverse=True)

    def _group_info(indices: list[int]) -> dict:
        members = [papers[i] for i in indices]
        return {
            "size": len(members),
            "title": members[0].get("title") or members[0].get("stem", ""),
            "arxiv_id": next(
                (m.get("arxiv_id") for m in members if is_valid_arxiv_id(m.get("arxiv_id"))),
                None,
            ),
            "paths": [m.get("rel_path") or m.get("path", "") for m in members],
        }

    top20 = [_group_info(g) for g in merge_groups[:20]]

    return {
        "total": len(papers),
        "arxiv_dup_groups": len(arxiv_dup),
        "arxiv_dup_entries": sum(len(v) - 1 for v in arxiv_groups.values() if len(v) > 1),
        "title_dup_groups": len(title_dup),
        "title_dup_entries": sum(len(v) - 1 for v in title_groups.values() if len(v) > 1),
        "merged_dup_groups": len(merge_groups),
        "merged_dup_removable": sum(len(g) - 1 for g in merge_groups),
        "after_dedupe": len(papers) - sum(len(g) - 1 for g in merge_groups),
        "top20": top20,
    }


def print_audit_report(report: dict[str, Any]) -> None:
    print(f"总论文数: {report['total']}")
    print(f"按 arxiv_id 重复组: {report['arxiv_dup_groups']} 组 "
          f"({report['arxiv_dup_entries']} 条可移除)")
    print(f"按规范化标题重复组: {report['title_dup_groups']} 组 "
          f"({report['title_dup_entries']} 条可移除)")
    print(f"合并去重后重复组: {report['merged_dup_groups']} 组 "
          f"({report['merged_dup_removable']} 条可移除)")
    print(f"去重后预计总数: {report['after_dedupe']}")
    print("\n前 20 大重复组:")
    for i, g in enumerate(report["top20"], 1):
        print(f"\n  {i}. [{g['size']} 份] {g['title'][:80]}")
        if g["arxiv_id"]:
            print(f"     arxiv: {g['arxiv_id']}")
        for path in g["paths"][:5]:
            print(f"     - {path}")
        if len(g["paths"]) > 5:
            print(f"     ... 还有 {len(g['paths']) - 5} 份")


def _load_papers_for_audit(*, online: bool = False) -> list[dict]:
    from generate_papers import LIBRARIES, load_cache, load_fitz, scan_library

    fitz = load_fitz()
    cache = load_cache()
    all_papers: list[dict] = []
    for lib_name, lib_path in LIBRARIES.items():
        if not lib_path.exists():
            continue
        papers, _ = scan_library(lib_name, lib_path, cache, fitz, online)
        all_papers.extend(papers)
    return all_papers


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="论文库去重审计")
    ap.add_argument("--online", action="store_true", help="启用在线元数据补全")
    args = ap.parse_args()

    print("扫描论文库...")
    papers = _load_papers_for_audit(online=args.online)
    report = audit_duplicates(papers)
    print_audit_report(report)
