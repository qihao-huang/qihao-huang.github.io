#!/usr/bin/env python3
"""
clean_library.py — 分析并移除非论文/不合理条目到各库的 _excluded/ 目录。

用法:
  python tools/clean_library.py          # 预览（不移动）
  python tools/clean_library.py --apply  # 执行移动 + 清理缓存
"""

from __future__ import annotations
import json, sys, argparse, shutil
from pathlib import Path
from datetime import datetime, timezone

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from generate_papers import LIBRARIES, CACHE_FILE, load_cache, save_cache, paper_cache_key
from paper_filter import should_exclude, fix_bogus_arxiv, is_invalid_arxiv_id

MANIFEST = SCRIPT_DIR / "excluded_manifest.json"


def collect_all_pdfs() -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for lib_name, lib_path in LIBRARIES.items():
        if not lib_path.exists():
            continue
        for pdf in sorted(lib_path.rglob("*.pdf")):
            if "/_excluded/" in str(pdf).replace("\\", "/"):
                continue
            out.append((lib_name, pdf))
    return out


def paper_dict_from_path(lib_name: str, pdf_path: Path, cache: dict) -> dict:
    rel = pdf_path.relative_to(LIBRARIES[lib_name])
    stat = pdf_path.stat()
    stem = pdf_path.stem
    entry = {
        "stem": stem,
        "path": str(pdf_path),
        "rel_path": str(rel),
        "folder": rel.parts[0] if len(rel.parts) > 1 else "_root",
        "library": lib_name,
        "size": stat.st_size,
        "title": stem.replace("_", " ").replace("-", " "),
        "_title_is_filename": True,
        "abstract": None,
    }
    # 合并缓存中已有 metadata
    ckey = paper_cache_key(pdf_path, stat)
    if ckey in cache.get("papers", {}):
        cached = cache["papers"][ckey]
        entry.update({k: v for k, v in cached.items() if k not in ("mtime", "birthtime")})
        entry["path"] = str(pdf_path)
        entry["rel_path"] = str(rel)
    return entry


def analyze() -> tuple[list[dict], list[dict]]:
    exclude_list: list[dict] = []
    fix_arxiv_list: list[dict] = []
    cache = load_cache()

    for lib_name, pdf_path in collect_all_pdfs():
        paper = paper_dict_from_path(lib_name, pdf_path, cache)
        ex, reason = should_exclude(paper, pdf_path)
        if ex:
            exclude_list.append({
                "library": lib_name,
                "rel_path": paper["rel_path"],
                "path": str(pdf_path),
                "title": paper.get("title") or paper["stem"],
                "reason": reason,
                "size": paper.get("size", 0),
            })
        if is_invalid_arxiv_id(paper.get("arxiv_id")):
            fix_arxiv_list.append({
                "library": lib_name,
                "rel_path": paper["rel_path"],
                "title": paper.get("title", "")[:60],
                "bad_arxiv": paper.get("arxiv_id"),
            })
    return exclude_list, fix_arxiv_list


def apply_exclusions(exclude_list: list[dict]) -> None:
    cache = load_cache()
    moved: list[dict] = []

    for item in exclude_list:
        src = Path(item["path"])
        if not src.exists():
            continue
        lib_path = LIBRARIES[item["library"]]
        dst = lib_path / "_excluded" / item["rel_path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            dst = dst.with_stem(dst.stem + "_dup")
        shutil.move(str(src), str(dst))
        item["moved_to"] = str(dst)
        moved.append(item)

        # 从缓存删除所有指向该路径的条目
        to_del = [k for k, v in cache.get("papers", {}).items() if v.get("path") == str(src)]
        for k in to_del:
            del cache["papers"][k]

    # 修复缓存中 bogus arxiv
    fixed = 0
    for k, paper in list(cache.get("papers", {}).items()):
        if is_invalid_arxiv_id(paper.get("arxiv_id")):
            fix_bogus_arxiv(paper)
            paper["needs_review"] = not paper.get("pub_year") or paper.get("_title_is_filename")
            fixed += 1

    save_cache(cache)

    manifest = {
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
        "moved_count": len(moved),
        "arxiv_fixed": fixed,
        "entries": moved,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Clean non-paper entries from libraries")
    ap.add_argument("--apply", action="store_true", help="Move files to _excluded/ and update cache")
    args = ap.parse_args()

    exclude_list, fix_arxiv = analyze()

    print(f"扫描 PDF 总数: {len(collect_all_pdfs())}")
    print(f"建议排除: {len(exclude_list)} 篇")
    print(f"需修复假 arXiv ID: {len(fix_arxiv)} 篇")

    from collections import Counter
    reasons = Counter(x["reason"] for x in exclude_list)
    print("\n排除原因分布:")
    for r, c in reasons.most_common():
        print(f"  {r}: {c}")

    print("\n--- 将排除的条目（前 40）---")
    for item in exclude_list[:40]:
        print(f"  [{item['reason']}] {item['library']}/{item['rel_path']}")
    if len(exclude_list) > 40:
        print(f"  ... 还有 {len(exclude_list) - 40} 条")

    if fix_arxiv:
        print("\n--- 假 arXiv（将修复 metadata，不移动）---")
        for x in fix_arxiv:
            print(f"  {x['bad_arxiv']} | {x['rel_path'][:55]}")

    if not args.apply:
        print("\n预览模式。确认后运行: python tools/clean_library.py --apply")
        return

    apply_exclusions(exclude_list)
    print(f"\n已移动 {len(exclude_list)} 个文件到各库 _excluded/ 目录")
    print(f"清单: {MANIFEST}")


if __name__ == "__main__":
    main()
