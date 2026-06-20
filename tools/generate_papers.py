#!/usr/bin/env python3
"""
generate_papers.py — Personal Paper Library Tool (Phase 1: Read-only visualization)

Scans auto_ai / physical_ai PDF libraries, extracts metadata via PyMuPDF,
optionally enriches missing fields via arXiv / Crossref / Semantic Scholar APIs
(all free, no API key, pure urllib), classifies research directions offline
using keyword taxonomy, computes a content-similarity graph (TF-IDF + bonuses),
tracks interest evolution over time, and renders a self-contained papers.html.

Usage:
  python tools/generate_papers.py [--no-online] [--public]

Options:
  --no-online   Skip network enrichment (faster, unknowns marked needs_review)
  --public      Strip personal reading timestamps (mtime/birthtime) from HTML
"""

from __future__ import annotations
import os, sys, re, json, math, time, argparse, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict, Counter
from typing import Any

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent.resolve()
REPO_DIR     = SCRIPT_DIR.parent
CACHE_FILE   = SCRIPT_DIR / ".papers_cache.json"
SNAPSHOT_DIR = SCRIPT_DIR / "snapshots"
SNAPSHOT_FILE = SNAPSHOT_DIR / "history.json"
OUTPUT_HTML  = REPO_DIR / "papers.html"

LIBRARIES: dict[str, Path] = {
    "auto_ai":     Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/docs/papers/auto_ai",
    "physical_ai": Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/docs/papers/physical_ai",
}

TOP_K_NEIGHBORS = 15
ONLINE_DELAY    = 0.35   # seconds between API requests (be polite)
USER_AGENT      = "PersonalPaperLibrary/1.0 (research tool; qihao.huang@example.com)"

sys.path.insert(0, str(SCRIPT_DIR))
from paper_tagger import tag_all_papers
from paper_validator import attach_validation_flags
from summary_zh import add_summaries
from paper_filter import (
    should_exclude, fix_bogus_arxiv, is_invalid_arxiv_id,
    is_valid_arxiv_id, arxiv_id_to_pub_date, recover_arxiv_from_stem,
    recover_year_from_stem, is_plausible_pub_year,
)

# ── Cache ──────────────────────────────────────────────────────────────────────

def load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"papers": {}, "online": {}}

def save_cache(cache: dict) -> None:
    CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

def paper_cache_key(pdf_path: Path, stat: os.stat_result) -> str:
    return f"{pdf_path}|{stat.st_mtime:.0f}|{stat.st_size}"

# ── PyMuPDF import ─────────────────────────────────────────────────────────────

def load_fitz():
    try:
        import fitz
        return fitz
    except ImportError:
        print(
            "ERROR: PyMuPDF not installed.\n"
            "  Run: tools/.venv/bin/pip install pymupdf",
            file=sys.stderr,
        )
        sys.exit(1)

# ── PDF Extraction ─────────────────────────────────────────────────────────────

_ARXIV_ID_RE  = re.compile(r'(?:arXiv[:\s])?(\d{4}\.\d{4,5})(?:v\d+)?', re.IGNORECASE)
_ARXIV_CAT_RE = re.compile(r'\[([a-z]{2,4}\.[A-Z]{2,4})\]')
_YEAR_RE      = re.compile(r'\b(20\d{2})\b')

def _parse_arxiv_id(arxiv_id: str) -> tuple[int, int]:
    dt = arxiv_id_to_pub_date(arxiv_id)
    if dt:
        return dt
    yy, mm = int(arxiv_id[:2]), int(arxiv_id[2:4])
    return 2000 + yy, mm

def _normalize_arxiv_id(arxiv_id: str) -> str | None:
    """过滤 PDF 误解析的假 arXiv ID。"""
    return arxiv_id if is_valid_arxiv_id(arxiv_id) else None

def extract_from_filename(path: Path) -> dict:
    m = _ARXIV_ID_RE.search(path.stem)
    if m:
        aid = _normalize_arxiv_id(m.group(1))
        if aid:
            year, month = _parse_arxiv_id(aid)
            return {"arxiv_id": aid, "pub_year": year, "pub_month": month}
    return {}

def _extract_title(blocks: list) -> str | None:
    if not blocks:
        return None
    text_blocks = [b for b in blocks if b[6] == 0]
    if not text_blocks:
        return None
    page_h = max(b[3] for b in text_blocks) if text_blocks else 800
    top = sorted([b for b in text_blocks if b[1] < page_h * 0.5], key=lambda b: b[1])
    if not top:
        top = sorted(text_blocks, key=lambda b: b[1])
    candidates = []
    for b in top:
        txt = b[4].strip()
        if len(txt) > 10 and not re.match(r'^[\d\s\.\-]+$', txt) and '@' not in txt:
            candidates.append(re.sub(r'\s+', ' ', txt).strip())
        if len(candidates) >= 3:
            break
    if not candidates:
        return None
    title = candidates[0]
    # If it looks like author line (lots of commas / et al), try next
    if (title.count(',') > 4 or 'et al' in title.lower()) and len(candidates) > 1:
        title = candidates[1]
    return title if len(title) > 5 else None

def _extract_abstract(text: str) -> str | None:
    m = re.search(
        r'\bAbstract\b[.\s]*(.{100,2000}?)(?:\n\s*(?:1\.?\s*Introduction|Keywords|Index Terms))',
        text, re.DOTALL | re.IGNORECASE
    )
    if m:
        return re.sub(r'\s+', ' ', m.group(1)).strip()[:1500]
    m = re.search(r'\bAbstract\b[.\s]*(.{100,800})', text, re.DOTALL | re.IGNORECASE)
    if m:
        return re.sub(r'\s+', ' ', m.group(1)).strip()[:1500]
    return None

def extract_pdf_metadata(pdf_path: Path, fitz) -> dict:
    result: dict[str, Any] = {
        "title": None, "abstract": None,
        "arxiv_id": None, "arxiv_cat": None,
        "pub_year": None, "pub_month": None,
    }
    try:
        doc = fitz.open(str(pdf_path))
        if not doc.page_count:
            doc.close(); return result
        page   = doc[0]
        text   = page.get_text("text")
        blocks = page.get_text("blocks")
        doc.close()

        m = _ARXIV_ID_RE.search(text)
        if m:
            for raw in _ARXIV_ID_RE.findall(text):
                aid = _normalize_arxiv_id(raw)
                if aid:
                    result["arxiv_id"] = aid
                    result["pub_year"], result["pub_month"] = _parse_arxiv_id(aid)
                    break

        m = _ARXIV_CAT_RE.search(text)
        if m:
            result["arxiv_cat"] = m.group(1)

        result["title"]    = _extract_title(blocks)
        result["abstract"] = _extract_abstract(text)

        if not result["pub_year"]:
            years = [int(y) for y in _YEAR_RE.findall(text[:3000]) if is_plausible_pub_year(int(y))]
            if years:
                result["pub_year"] = Counter(years).most_common(1)[0][0]
    except Exception:
        pass
    return result

# ── Online Enrichment ──────────────────────────────────────────────────────────

def _fetch_json(url: str, timeout: int = 12) -> Any:
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

def _title_sim(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    stop = {'the','a','an','of','in','is','for','and','with','on','via','using','from'}
    ta = set(re.findall(r'\w+', a.lower())) - stop
    tb = set(re.findall(r'\w+', b.lower())) - stop
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))

def _apply_online(paper: dict, result: dict, source: str = "online") -> None:
    for f in ("title", "abstract", "arxiv_id", "arxiv_cat", "pub_year", "pub_month"):
        if not paper.get(f) and result.get(f):
            paper[f] = result[f]
    if result.get("pub_year") and not paper.get("pub_date_source"):
        paper["pub_date_source"] = source

def _enrich_arxiv(paper: dict, cache: dict) -> bool:
    arxiv_id = paper.get("arxiv_id")
    key = f"arxiv:{arxiv_id or paper.get('stem','')[:60]}"
    if key in cache["online"]:
        if cache["online"][key]:
            _apply_online(paper, cache["online"][key], "arxiv_api")
        return bool(cache["online"][key])

    result = None
    if arxiv_id:
        url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}&max_results=1"
    else:
        q = urllib.parse.quote(re.sub(r'[_\-]', ' ', paper.get("stem",""))[:80])
        url = f"http://export.arxiv.org/api/query?search_query=ti:{q}&max_results=3"

    time.sleep(ONLINE_DELAY)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml = resp.read().decode("utf-8")

        titles    = re.findall(r'<title[^>]*>(.*?)</title>', xml, re.DOTALL)
        abstracts = re.findall(r'<summary[^>]*>(.*?)</summary>', xml, re.DOTALL)
        ids       = re.findall(r'<id[^>]*>.*?(\d{4}\.\d{4,5})(?:v\d+)?</id>', xml)
        dates     = re.findall(r'<published>(.*?)</published>', xml)
        cats      = re.findall(r'<arxiv:primary_category[^/]* term="([^"]+)"', xml)
        titles    = [re.sub(r'\s+', ' ', t).strip() for t in titles
                     if t.strip() and 'ArXiv' not in t]

        if titles and (arxiv_id or _title_sim(paper.get("title"), titles[0]) > 0.45):
            year = month = None
            if dates:
                m = re.match(r'(\d{4})-(\d{2})', dates[0])
                if m:
                    year, month = int(m.group(1)), int(m.group(2))
            aid = ids[0] if ids else arxiv_id
            if not year and aid:
                year, month = _parse_arxiv_id(aid)
            result = {
                "title": titles[0], "abstract": abstracts[0].strip() if abstracts else None,
                "arxiv_id": aid, "arxiv_cat": cats[0] if cats else None,
                "pub_year": year, "pub_month": month,
            }
    except Exception:
        pass

    cache["online"][key] = result
    if result:
        _apply_online(paper, result, "arxiv_api")
        return True
    return False

def _enrich_arxiv_by_id(paper: dict, cache: dict) -> bool:
    """Direct arXiv API lookup when we already have an arXiv ID."""
    arxiv_id = paper.get("arxiv_id")
    if not arxiv_id:
        return False
    key = f"arxiv_id:{arxiv_id}"
    if key in cache["online"]:
        if cache["online"][key]:
            _apply_online(paper, cache["online"][key], "arxiv_api")
        return bool(cache["online"][key])

    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}&max_results=1"
    time.sleep(ONLINE_DELAY)
    result = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml = resp.read().decode("utf-8")
        titles    = [re.sub(r'\s+', ' ', t).strip() for t in re.findall(r'<title[^>]*>(.*?)</title>', xml, re.DOTALL)
                     if t.strip() and 'ArXiv' not in t]
        abstracts = re.findall(r'<summary[^>]*>(.*?)</summary>', xml, re.DOTALL)
        dates     = re.findall(r'<published>(.*?)</published>', xml)
        cats      = re.findall(r'<arxiv:primary_category[^/]* term="([^"]+)"', xml)
        year = month = None
        if dates:
            m = re.match(r'(\d{4})-(\d{2})', dates[0])
            if m:
                year, month = int(m.group(1)), int(m.group(2))
        if not year:
            year, month = _parse_arxiv_id(arxiv_id)
        if titles or year:
            result = {
                "title": titles[0] if titles else None,
                "abstract": abstracts[0].strip() if abstracts else None,
                "arxiv_id": arxiv_id,
                "arxiv_cat": cats[0] if cats else None,
                "pub_year": year, "pub_month": month,
            }
    except Exception:
        pass

    cache["online"][key] = result
    if result:
        _apply_online(paper, result, "arxiv_api")
        return True
    return False

def _enrich_s2_by_arxiv(paper: dict, cache: dict) -> bool:
    """Semantic Scholar by arXiv ID — often has publicationDate."""
    arxiv_id = paper.get("arxiv_id")
    if not arxiv_id:
        return False
    key = f"s2arxiv:{arxiv_id}"
    if key in cache["online"]:
        if cache["online"][key]:
            _apply_online(paper, cache["online"][key], "semanticscholar")
        return bool(cache["online"][key])

    url = (f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}"
           f"?fields=title,year,publicationDate,abstract")
    time.sleep(ONLINE_DELAY)
    data = _fetch_json(url)
    result = None
    if data and data.get("year"):
        pub_date = data.get("publicationDate") or ""
        month = None
        year = data.get("year")
        if pub_date:
            m = re.match(r'(\d{4})-(\d{2})', pub_date)
            if m:
                year, month = int(m.group(1)), int(m.group(2))
        result = {
            "title": data.get("title"), "abstract": data.get("abstract"),
            "arxiv_id": arxiv_id, "arxiv_cat": None,
            "pub_year": year, "pub_month": month,
        }

    cache["online"][key] = result
    if result:
        _apply_online(paper, result, "semanticscholar")
        return True
    return False

def _enrich_crossref(paper: dict, cache: dict) -> bool:
    title = paper.get("title") or paper.get("stem", "")
    if not title or paper.get("_title_is_filename"):
        title = re.sub(r'[_\-]+', ' ', paper.get("stem", "")).strip() or title
    key = f"cr:{title[:70]}"
    if key in cache["online"]:
        if cache["online"][key]:
            _apply_online(paper, cache["online"][key], "crossref")
        return bool(cache["online"][key])

    q   = urllib.parse.quote(title[:100])
    url = (f"https://api.crossref.org/works?query.bibliographic={q}"
           f"&rows=3&select=title,published,DOI&mailto=qihao.huang@example.com")
    time.sleep(ONLINE_DELAY)
    data   = _fetch_json(url)
    result = None
    if data and "message" in data:
        for item in data["message"].get("items", []):
            cr_titles = item.get("title", [])
            if cr_titles and _title_sim(paper.get("title") or title, cr_titles[0]) > 0.55:
                pub_parts = (item.get("published") or {}).get("date-parts", [[]])[0]
                result = {
                    "title": cr_titles[0], "abstract": None,
                    "arxiv_id": None, "arxiv_cat": None,
                    "pub_year": pub_parts[0] if pub_parts else None,
                    "pub_month": pub_parts[1] if len(pub_parts) > 1 else None,
                }
                break

    cache["online"][key] = result
    if result:
        _apply_online(paper, result, "crossref")
        return True
    return False

def _enrich_s2(paper: dict, cache: dict) -> bool:
    title = paper.get("title") or paper.get("stem", "")
    if not title:
        return False
    key = f"s2:{title[:70]}"
    if key in cache["online"]:
        if cache["online"][key]:
            _apply_online(paper, cache["online"][key], "semanticscholar")
        return bool(cache["online"][key])

    q   = urllib.parse.quote(title[:100])
    url = (f"https://api.semanticscholar.org/graph/v1/paper/search"
           f"?query={q}&limit=3&fields=title,year,publicationDate,externalIds,abstract")
    time.sleep(ONLINE_DELAY)
    data   = _fetch_json(url)
    result = None
    if data and "data" in data:
        for item in data["data"]:
            if _title_sim(title, item.get("title", "")) > 0.55:
                pub_date = item.get("publicationDate") or ""
                month = None
                year = item.get("year")
                if pub_date:
                    m = re.match(r'(\d{4})-(\d{2})', pub_date)
                    if m:
                        year, month = int(m.group(1)), int(m.group(2))
                result = {
                    "title": item.get("title"), "abstract": item.get("abstract"),
                    "arxiv_id": (item.get("externalIds") or {}).get("ArXiv"),
                    "arxiv_cat": None,
                    "pub_year": year, "pub_month": month,
                }
                break

    cache["online"][key] = result
    if result:
        _apply_online(paper, result, "semanticscholar")
        return True
    return False

def enrich_paper_online(paper: dict, cache: dict, *, dates_only: bool = False) -> bool:
    """
    Online enrichment: arXiv(by ID) → arXiv(search) → S2(by arXiv) → Crossref → S2(search).
    Returns True if pub_year was newly obtained.
    """
    had_date = bool(paper.get("pub_year"))
    need_date = not had_date
    need_meta = (
        not dates_only
        and (
            not paper.get("title")
            or paper.get("_title_is_filename")
            or not paper.get("abstract")
        )
    )
    if not need_date and not need_meta:
        return False

    if paper.get("arxiv_id"):
        _enrich_arxiv_by_id(paper, cache)
    if need_date and not paper.get("pub_year"):
        _enrich_arxiv(paper, cache)
    if need_date and not paper.get("pub_year") and paper.get("arxiv_id"):
        _enrich_s2_by_arxiv(paper, cache)
    if need_date and not paper.get("pub_year"):
        _enrich_crossref(paper, cache)
    if (need_date and not paper.get("pub_year")) or need_meta:
        _enrich_s2(paper, cache)

    return bool(paper.get("pub_year")) and not had_date

def enrich_missing_dates(papers: list[dict], cache: dict, online: bool) -> int:
    """Second pass: online-fetch dates for ALL papers still missing pub_year (incl. cached)."""
    if not online:
        return 0
    missing = [p for p in papers if not p.get("pub_year")]
    if not missing:
        return 0
    print(f"\n[Online] Fetching publication dates for {len(missing)} papers ...")
    filled = 0
    for i, paper in enumerate(missing):
        if i % 10 == 0 or i == len(missing) - 1:
            print(f"\r  {i+1}/{len(missing)} (filled {filled}) ...", end="", flush=True)
        if enrich_paper_online(paper, cache, dates_only=True):
            filled += 1
            # Persist back to cache
            ckey = paper.get("_ckey")
            if ckey and ckey in cache["papers"]:
                for f in ("pub_year", "pub_month", "pub_date_source", "title", "abstract", "arxiv_id", "arxiv_cat"):
                    if paper.get(f) is not None:
                        cache["papers"][ckey][f] = paper[f]
                cache["papers"][ckey]["needs_review"] = bool(
                    paper.get("_title_is_filename") or not paper.get("pub_year")
                )
            if filled % 25 == 0:
                save_cache(cache)
    print(f"\r  Done: filled {filled}/{len(missing)} missing dates       ")
    return filled

def enrich_paper(paper: dict, cache: dict, online: bool) -> None:
    """Fill missing fields on first scan."""
    if not online:
        return
    enrich_paper_online(paper, cache, dates_only=False)


def sanitize_pub_date(
    paper: dict,
    pdf_path: Path | None = None,
    fitz=None,
) -> None:
    """修复误解析 arXiv/发表日期；bogus arxiv 清除后尝试从文件名恢复。"""
    fix_bogus_arxiv(paper)
    stem = paper.get("stem") or (pdf_path.stem if pdf_path else Path(paper.get("path", "")).stem)
    if not paper.get("arxiv_id"):
        recovered = recover_arxiv_from_stem(stem)
        if recovered:
            paper.update(recovered)
        elif pdf_path:
            for k, v in extract_from_filename(pdf_path).items():
                if v is not None and not paper.get(k):
                    paper[k] = v
    if not paper.get("pub_year"):
        recovered_year = recover_year_from_stem(stem)
        if recovered_year:
            paper.update(recovered_year)
    if pdf_path and fitz and not paper.get("pub_year"):
        meta = extract_pdf_metadata(pdf_path, fitz)
        if meta.get("arxiv_id") and is_valid_arxiv_id(meta["arxiv_id"]):
            paper["arxiv_id"] = meta["arxiv_id"]
            dt = arxiv_id_to_pub_date(meta["arxiv_id"])
            if dt:
                paper["pub_year"], paper["pub_month"] = dt
                paper["pub_date_source"] = "arxiv_id"
        elif meta.get("pub_year") and is_plausible_pub_year(meta["pub_year"]):
            paper["pub_year"] = meta["pub_year"]
            paper["pub_month"] = meta.get("pub_month")
            paper["pub_date_source"] = "pdf"
    if not is_plausible_pub_year(paper.get("pub_year")):
        paper.pop("pub_year", None)
        paper.pop("pub_month", None)
        if paper.get("pub_date_source") in ("pdf", "arxiv_id", "arxiv_api", None):
            paper.pop("pub_date_source", None)
        paper["needs_review"] = True
    else:
        paper["needs_review"] = bool(
            paper.get("_title_is_filename") or not paper.get("pub_year")
        )


def sanitize_cache(cache: dict) -> int:
    """修复缓存中误解析的 arXiv ID 与不合理发表年份。"""
    fixed = 0
    for paper in cache.get("papers", {}).values():
        before = (paper.get("arxiv_id"), paper.get("pub_year"), paper.get("pub_month"))
        sanitize_pub_date(paper)
        after = (paper.get("arxiv_id"), paper.get("pub_year"), paper.get("pub_month"))
        if before != after:
            fixed += 1
    return fixed

# ── Tagging (see paper_tagger.py) ─────────────────────────────────────────────

# ── File Scanning + Timestamps ─────────────────────────────────────────────────

def scan_library(
    lib_name: str, lib_path: Path, cache: dict, fitz, online: bool
) -> list[dict]:
    pdf_files = sorted(lib_path.rglob("*.pdf"))
    total     = len(pdf_files)
    print(f"\n[{lib_name}] Found {total} PDFs")

    papers: list[dict] = []
    skipped = 0
    for i, pdf_path in enumerate(pdf_files):
        if "/_excluded/" in str(pdf_path) or "\\_excluded\\" in str(pdf_path):
            skipped += 1
            continue
        if i % 50 == 0 or i == total - 1:
            print(f"\r  {i+1}/{total} ...", end="", flush=True)
        try:
            stat = pdf_path.stat()
        except OSError:
            continue

        rel    = pdf_path.relative_to(lib_path)
        folder = rel.parts[0] if len(rel.parts) > 1 else "_root"
        stem   = pdf_path.stem
        ckey   = paper_cache_key(pdf_path, stat)

        mtime     = int(stat.st_mtime)
        birthtime = int(getattr(stat, "st_birthtime", stat.st_ctime))

        if ckey in cache["papers"]:
            paper = dict(cache["papers"][ckey])
            paper["mtime"]     = mtime
            paper["birthtime"] = birthtime
            paper["_ckey"]     = ckey
            if paper.get("pub_year") and not paper.get("pub_date_source"):
                paper["pub_date_source"] = "arxiv_id" if paper.get("arxiv_id") else "pdf"
        else:
            meta = extract_pdf_metadata(pdf_path, fitz)
            if not meta.get("arxiv_id"):
                for k, v in extract_from_filename(pdf_path).items():
                    if v is not None and not meta.get(k):
                        meta[k] = v

            paper: dict = {
                "stem": stem, "path": str(pdf_path), "rel_path": str(rel),
                "folder": folder, "library": lib_name,
                "size": stat.st_size, "mtime": mtime, "birthtime": birthtime,
                **meta,
            }

            if not paper.get("title"):
                paper["title"]              = re.sub(r'[_\-]+', ' ', stem).strip()
                paper["_title_is_filename"] = True

            if paper.get("pub_year") and not paper.get("pub_date_source"):
                paper["pub_date_source"] = "pdf" if meta.get("pub_year") else "arxiv_id"

            enrich_paper(paper, cache, online)

            paper["needs_review"] = bool(
                paper.get("_title_is_filename") or not paper.get("pub_year")
            )
            paper["_ckey"] = ckey

        sanitize_pub_date(paper, pdf_path=pdf_path, fitz=fitz)

        cacheable = {k: v for k, v in paper.items() if k not in ("mtime", "birthtime")}
        cache["papers"][ckey] = cacheable

        ex, reason = should_exclude(paper)
        if ex:
            skipped += 1
            continue

        papers.append(paper)

    print(f"\r  Done: {len(papers)} papers ({skipped} excluded)             ")
    return papers

# ── Similarity Graph ───────────────────────────────────────────────────────────

_STOPWORDS = {
    'the','a','an','and','or','of','in','is','are','to','for','with','on','at',
    'by','from','as','this','that','we','our','their','have','has','be','been',
    'not','can','also','it','its','which','both','such','when','using','used',
    'based','show','shown','propose','proposed','paper','work','method','approach',
    'model','models','learn','learning','training','train','data','results',
    'performance','tasks','task','improve','improvement','novel','new','large',
    'deep','neural','network','networks',
}

def _tokenize(text: str) -> list[str]:
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    return [t for t in text.split()
            if len(t) > 2 and t not in _STOPWORDS and not t.isdigit()]

def compute_similarity_graph(
    papers: list[dict], top_k: int = TOP_K_NEIGHBORS
) -> list[list[tuple[int, float]]]:
    n = len(papers)
    if n == 0:
        return []
    print(f"\n[Graph] TF-IDF similarity for {n} papers ...")

    doc_tokens = [
        _tokenize(f"{p.get('title') or ''} {p.get('title') or ''} {p.get('abstract') or ''}")
        for p in papers
    ]

    df: Counter = Counter()
    for tokens in doc_tokens:
        df.update(set(tokens))

    idf = {t: math.log((n + 1) / (df[t] + 1)) for t in df}

    vectors: list[dict[str, float]] = []
    for tokens in doc_tokens:
        tf  = Counter(tokens)
        vec: dict[str, float] = {}
        norm = 0.0
        for term, freq in tf.items():
            if 2 <= df[term] <= n * 0.65:
                v = (1 + math.log(freq)) * idf[term]
                vec[term] = v
                norm += v * v
        norm = math.sqrt(norm) if norm > 0 else 1.0
        vectors.append({t: v / norm for t, v in vec.items()})

    inv_idx: dict[str, list[int]] = defaultdict(list)
    for i, vec in enumerate(vectors):
        for term in vec:
            inv_idx[term].append(i)

    all_neighbors: list[list[tuple[int, float]]] = []
    for i, vec_i in enumerate(vectors):
        if i % 200 == 0:
            print(f"\r  {i}/{n} ...", end="", flush=True)
        cands: Counter = Counter()
        for term in vec_i:
            for j in inv_idx[term]:
                if j != i:
                    cands[j] += 1

        scores: dict[int, float] = {}
        for j, _ in cands.most_common(300):
            sim = sum(vec_i[t] * vectors[j].get(t, 0.0) for t in vec_i if t in vectors[j])
            # Direction bonus
            di = set(papers[i].get("tags", {}).get("all", [])) - {"Uncategorized"}
            dj = set(papers[j].get("tags", {}).get("all", [])) - {"Uncategorized"}
            if di & dj:
                sim += 0.08
            # Folder bonus
            if papers[i].get("folder") == papers[j].get("folder"):
                sim += 0.04
            # Year proximity
            yi, yj = papers[i].get("pub_year"), papers[j].get("pub_year")
            if yi and yj:
                sim += max(0.0, 0.04 - 0.01 * abs(yi - yj))
            scores[j] = sim

        top = sorted(scores.items(), key=lambda x: -x[1])[:top_k]
        all_neighbors.append([(j, round(s, 4)) for j, s in top])

    print(f"\r  Done.                  ")
    return all_neighbors

# ── Publication date statistics ───────────────────────────────────────────────

def compute_pub_stats(papers: list[dict]) -> dict[str, Any]:
    by_year: Counter = Counter()
    by_month: Counter = Counter()
    by_library_year: dict[str, Counter] = defaultdict(Counter)
    by_source: Counter = Counter()
    no_date: list[dict] = []

    for p in papers:
        yr = p.get("pub_year")
        if yr and is_plausible_pub_year(yr):
            by_year[yr] += 1
            mo = p.get("pub_month") or 0
            by_month[f"{yr}-{mo:02d}" if mo else str(yr)] += 1
            by_library_year[p.get("library", "?")][yr] += 1
            by_source[p.get("pub_date_source") or "unknown"] += 1
        else:
            no_date.append({
                "title": p.get("title") or p.get("stem", ""),
                "folder": p.get("folder", ""),
                "library": p.get("library", ""),
                "arxiv_id": p.get("arxiv_id"),
            })

    years = sorted(by_year.keys())
    return {
        "total": len(papers),
        "with_date": sum(by_year.values()),
        "missing_date": len(no_date),
        "coverage_pct": round(100 * sum(by_year.values()) / max(len(papers), 1), 1),
        "year_min": years[0] if years else None,
        "year_max": years[-1] if years else None,
        "by_year": dict(sorted(by_year.items())),
        "by_month": dict(sorted(by_month.items())),
        "by_library_year": {k: dict(sorted(v.items())) for k, v in by_library_year.items()},
        "by_source": dict(by_source.most_common()),
        "no_date_sample": no_date[:100],
    }

# ── Evolution & Snapshots ──────────────────────────────────────────────────────

def compute_evolution_instant(papers: list[dict]) -> dict[str, dict[str, int]]:
    slices: dict[str, Counter] = defaultdict(Counter)
    for p in papers:
        yr = p.get("pub_year")
        mo = p.get("pub_month") or 1
        if not yr:
            yr = datetime.fromtimestamp(p.get("birthtime", 0), tz=timezone.utc).year
        q  = f"{yr}-Q{(mo - 1) // 3 + 1}"
        for d in p.get("tags", {}).get("topic", ["Uncategorized"]):
            slices[q][d] += 1
    return {q: dict(c) for q, c in sorted(slices.items())}

def load_snapshots() -> list[dict]:
    if SNAPSHOT_FILE.exists():
        try:
            return json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []

def save_snapshot(papers: list[dict]) -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    dir_counts: Counter = Counter()
    lib_counts: Counter = Counter()
    for p in papers:
        lib_counts[p.get("library", "unknown")] += 1
        for d in p.get("tags", {}).get("all", []):
            dir_counts[d] += 1

    snap = {
        "date":        today,
        "total":       len(papers),
        "libraries":   dict(lib_counts),
        "directions":  dict(dir_counts.most_common()),
        "needs_review": sum(1 for p in papers if p.get("needs_review")),
        "with_date":   sum(1 for p in papers if p.get("pub_year")),
    }
    snaps = [s for s in load_snapshots() if s.get("date") != today]
    snaps.append(snap)
    snaps.sort(key=lambda s: s["date"])
    SNAPSHOT_FILE.write_text(json.dumps(snaps, ensure_ascii=False, indent=2), encoding="utf-8")

# ── HTML Rendering ─────────────────────────────────────────────────────────────

def _papers_to_json(
    papers: list[dict],
    public: bool,
) -> str:
    out = []
    for i, p in enumerate(papers):
        tags = p.get("tags", {})
        obj: dict[str, Any] = {
            "id":          i,
            "title":       p.get("title") or p.get("stem", ""),
            "folder":      p.get("folder", ""),
            "library":     p.get("library", ""),
            "arxiv_id":    p.get("arxiv_id"),
            "pub_year":    p.get("pub_year"),
            "pub_month":   p.get("pub_month"),
            "pub_date_source": p.get("pub_date_source"),
            "tags":        tags,
            "needs_review": p.get("needs_review", False),
            "abstract":    (p.get("abstract") or "")[:400],
            "summary_zh":  p.get("summary_zh", ""),
        }
        if not public:
            obj["mtime"]     = p.get("mtime")
            obj["birthtime"] = p.get("birthtime")
        out.append(obj)
    return json.dumps(out, ensure_ascii=False, separators=(",", ":"))

def render_html(
    papers: list[dict],
    tag_stats: dict,
    pub_stats: dict,
    evolution: dict[str, dict[str, int]],
    public: bool,
) -> str:
    papers_json    = _papers_to_json(papers, public)
    tag_stats_json = json.dumps(tag_stats, ensure_ascii=False, separators=(",", ":"))
    pub_stats_json = json.dumps(pub_stats, ensure_ascii=False, separators=(",", ":"))
    evolution_json = json.dumps(evolution, ensure_ascii=False, separators=(",", ":"))

    total           = len(papers)
    auto_cnt        = sum(1 for p in papers if p.get("library") == "auto_ai")
    phys_cnt        = sum(1 for p in papers if p.get("library") == "physical_ai")
    unique_tags     = tag_stats.get("unique_tags", 0)
    uncat           = tag_stats.get("uncategorized", 0)
    with_date       = pub_stats.get("with_date", 0)
    coverage        = pub_stats.get("coverage_pct", 0)
    generated_at    = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = HTML_TEMPLATE
    for token, value in [
        ("__PAPERS_JSON__",    papers_json),
        ("__TAG_STATS_JSON__", tag_stats_json),
        ("__PUB_STATS_JSON__", pub_stats_json),
        ("__EVOLUTION_JSON__", evolution_json),
        ("__TOTAL__",          str(total)),
        ("__AUTO_CNT__",       str(auto_cnt)),
        ("__PHYS_CNT__",       str(phys_cnt)),
        ("__UNIQUE_TAGS__",    str(unique_tags)),
        ("__UNCAT__",          str(uncat)),
        ("__WITH_DATE__",      str(with_date)),
        ("__COVERAGE__",       str(coverage)),
        ("__GENERATED_AT__",   generated_at),
        ("__PUBLIC__",         "true" if public else "false"),
    ]:
        html = html.replace(token, value)
    return html

# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Personal Paper Library — generate papers.html")
    ap.add_argument("--no-online", action="store_true", help="Skip online enrichment")
    ap.add_argument("--public",    action="store_true", help="Strip reading timestamps from HTML")
    args = ap.parse_args()
    online = not args.no_online
    public = args.public

    print("=" * 50)
    print("Personal Paper Library Generator")
    print(f"Mode : {'offline' if not online else 'online enrichment'}")
    print(f"HTML : {'public (no timestamps)' if public else 'full (with timestamps)'}")
    print("=" * 50)

    fitz  = load_fitz()
    cache = load_cache()
    cache_fixed = sanitize_cache(cache)
    if cache_fixed:
        print(f"[Cache] Fixed {cache_fixed} entries with invalid arXiv/date ...")

    all_papers: list[dict] = []
    for lib_name, lib_path in LIBRARIES.items():
        if not lib_path.exists():
            print(f"WARNING: not found: {lib_path}", file=sys.stderr)
            continue
        all_papers.extend(scan_library(lib_name, lib_path, cache, fitz, online))

    print(f"\n[Cache] Saving {len(cache['papers'])} entries ...")
    save_cache(cache)

    filled = enrich_missing_dates(all_papers, cache, online)
    if filled:
        print(f"[Cache] Updating cache after online date enrichment ...")
        save_cache(cache)

    before_date_filter = len(all_papers)
    all_papers = [p for p in all_papers if p.get("pub_year")]
    skipped_no_date = before_date_filter - len(all_papers)
    if skipped_no_date:
        print(f"Skipped {skipped_no_date} papers without publication date")

    print(f"\n[Tagging] {len(all_papers)} papers ...")
    all_papers, tag_stats = tag_all_papers(all_papers)
    print(f"  {tag_stats['unique_tags']} unique tags, {tag_stats['uncategorized']} uncategorized")

    n_flagged = attach_validation_flags(all_papers)
    print(f"  {n_flagged} papers with validation flags")
    for p in all_papers:
        ckey = p.get("_ckey")
        if ckey and ckey in cache["papers"]:
            cache["papers"][ckey]["validation_flags"] = p.get("validation_flags", [])

    print(f"\n[Summary] Generating Chinese one-liners ...")
    add_summaries(all_papers)

    evolution = compute_evolution_instant(all_papers)
    pub_stats = compute_pub_stats(all_papers)
    save_snapshot(all_papers)

    print(f"\n[HTML] Rendering ...")
    import importlib.util, sys as _sys
    spec = importlib.util.spec_from_file_location(
        "_html_template", SCRIPT_DIR / "_html_template.py"
    )
    mod = importlib.util.module_from_spec(spec)
    _sys.modules["_html_template"] = mod
    spec.loader.exec_module(mod)
    global HTML_TEMPLATE
    HTML_TEMPLATE = mod.HTML_TEMPLATE

    html = render_html(all_papers, tag_stats, pub_stats, evolution, public)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    size_mb = OUTPUT_HTML.stat().st_size / 1_048_576

    needs_review = sum(1 for p in all_papers if p.get("needs_review"))
    print(f"\n{'='*50}")
    print(f"Total papers  : {len(all_papers)}")
    print(f"With pub date : {pub_stats['with_date']} ({pub_stats['coverage_pct']}%)")
    print(f"  sources     : {pub_stats['by_source']}")
    print(f"Unique tags   : {tag_stats['unique_tags']}")
    print(f"Uncategorized : {tag_stats['uncategorized']}")
    print(f"Needs review  : {needs_review}")
    print(f"Output        : {OUTPUT_HTML}  ({size_mb:.1f} MB)")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
