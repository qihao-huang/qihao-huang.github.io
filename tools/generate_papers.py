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
  --no-online     Skip network enrichment (faster, unknowns marked needs_review)
  --public        Strip personal reading timestamps (mtime/birthtime) from HTML
  --llm-summary   Generate Chinese summaries via LLM (offline batch; writes cache)
  --llm-limit N   Max LLM calls per run (default: unlimited)
  --llm-model X   LLM model id (default: gpt-4o-mini or SUMMARY_LLM_MODEL env)

2025–2026 papers always use LLM (abstract + Introduction excerpt) when OPENAI_API_KEY
is set, even without --llm-summary. Without the key, a warning is printed and rule
summaries are used as fallback.
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
from summary_llm import (
    add_llm_summaries,
    add_summaries_from_cache,
    count_recent_missing_llm,
    DEFAULT_MODEL as LLM_DEFAULT_MODEL,
)
from paper_filter import (
    should_exclude, fix_bogus_arxiv, is_invalid_arxiv_id,
    is_valid_arxiv_id, arxiv_id_to_pub_date, recover_arxiv_from_stem,
    recover_year_from_stem, is_plausible_pub_year,
    is_junk_title, title_from_stem, junk_title_reasons,
)
from dedupe_papers import dedupe_papers

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

def _title_block_score(txt: str, block: tuple, page_w: float, page_h: float) -> float:
    """Heuristic: title blocks are short, centered, near top of page."""
    x0, y0, x1, y1 = block[0], block[1], block[2], block[3]
    cx = (x0 + x1) / 2
    width = max(x1 - x0, 1)
    score = 0.0
    # Prefer upper half
    score += max(0, 1.0 - y0 / max(page_h * 0.45, 1))
    # Prefer horizontally centered
    score += max(0, 1.0 - abs(cx - page_w / 2) / max(page_w / 2, 1)) * 0.5
    # Prefer moderate length (typical paper titles)
    if 15 <= len(txt) <= 120:
        score += 1.0
    elif len(txt) <= 150:
        score += 0.4
    else:
        score -= 0.5
    # Penalize author-list patterns
    if txt.count(",") > 4 or "et al" in txt.lower():
        score -= 0.8
    if is_junk_title(txt):
        score -= 5.0
    return score


def _extract_title(blocks: list, *, stem: str = "") -> str | None:
    if not blocks:
        return None
    text_blocks = [b for b in blocks if b[6] == 0]
    if not text_blocks:
        return None
    page_w = max(b[2] for b in text_blocks)
    page_h = max(b[3] for b in text_blocks) if text_blocks else 800
    top = sorted([b for b in text_blocks if b[1] < page_h * 0.55], key=lambda b: b[1])
    if not top:
        top = sorted(text_blocks, key=lambda b: b[1])

    def _clean(txt: str) -> str:
        return re.sub(r"\s+", " ", txt).strip()

    raw_candidates: list[tuple[str, tuple, float]] = []
    for b in top[:12]:
        txt = _clean(b[4])
        if len(txt) <= 10 or re.match(r"^[\d\s.\-]+$", txt) or "@" in txt:
            continue
        if len(txt) > 200:
            continue
        raw_candidates.append((txt, b, _title_block_score(txt, b, page_w, page_h)))

    if not raw_candidates:
        fallback = title_from_stem(stem)
        if fallback and not is_junk_title(fallback):
            return fallback
        return None

    # Skip junk blocks; rank remaining by score (prefer short centered title-like text)
    ranked = sorted(raw_candidates, key=lambda x: -x[2])
    seen: set[str] = set()
    candidates: list[str] = []
    for txt, _, score in ranked:
        if txt in seen or score < -2:
            continue
        seen.add(txt)
        if is_junk_title(txt):
            continue
        candidates.append(txt)
        if len(candidates) >= 5:
            break

    # 中文 PDF：优先短标题块；长块多为章节摘要
    has_cjk = any(re.search(r"[\u4e00-\u9fff]", c) for c in candidates)
    if has_cjk:
        short = [c for c in candidates if len(c) < 120 and not is_junk_title(c)]
        if short:
            candidates = short + [c for c in candidates if c not in short]

    for title in candidates:
        if (title.count(",") > 4 or "et al" in title.lower()) and len(candidates) > 1:
            continue
        if len(title) > 5 and not is_junk_title(title):
            return title

    fallback = title_from_stem(stem)
    if fallback and not is_junk_title(fallback):
        return fallback
    return None

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

INTRO_EXCERPT_MAX = 1500
_INTRO_NEXT_SECTION_RE = re.compile(
    r'\n\s*(?:'
    r'\d+\.?\s*(?:Related\s+Work|Background|Preliminaries|Method|Methods|Problem|Overview|Approach|Preliminary)|'
    r'2\.?\s+[A-Z]|'
    r'II\.|'
    r'\bReferences\b|'
    r'\bConclusion\b|'
    r'\bExperiments\b|'
    r'\bImplementation\b'
    r')',
    re.IGNORECASE,
)

def _extract_introduction(text: str) -> str | None:
    """从 PDF 前几页文本中提取 Introduction 章节（最多 INTRO_EXCERPT_MAX 字符）。"""
    if not text:
        return None
    text = text.replace("\r\n", "\n")
    patterns = [
        r'\b(?:1\.?\s*)?Introduction\b[.\s:—–-]*\n?\s*(.{100,8000})',
        r'\bINTRODUCTION\b[.\s:—–-]*\n?\s*(.{100,8000})',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
        if not m:
            continue
        body = m.group(1)
        nxt = _INTRO_NEXT_SECTION_RE.search(body)
        if nxt:
            body = body[: nxt.start()]
        intro = re.sub(r"(\w)-\s+(\w)", r"\1\2", body)
        intro = re.sub(r"\s+", " ", intro).strip()
        if len(intro) >= 80:
            return intro[:INTRO_EXCERPT_MAX]
    return None

def extract_intro_from_pdf(pdf_path: Path, fitz, *, max_pages: int = 3) -> str | None:
    """读取 PDF 前 max_pages 页，提取 Introduction 节选。"""
    try:
        doc = fitz.open(str(pdf_path))
        if not doc.page_count:
            doc.close()
            return None
        chunks: list[str] = []
        for i in range(min(max_pages, doc.page_count)):
            chunks.append(doc[i].get_text("text"))
        doc.close()
        return _extract_introduction("\n".join(chunks))
    except Exception:
        return None

def ensure_intro_excerpt(paper: dict, pdf_path: Path, fitz) -> None:
    """为论文填充 intro_excerpt（已有则跳过）。"""
    if paper.get("intro_excerpt"):
        return
    intro = extract_intro_from_pdf(pdf_path, fitz)
    if intro:
        paper["intro_excerpt"] = intro

_AUTHOR_SKIP_RE = re.compile(
    r'^(arXiv|doi:|https?://|www\.|Keywords|Index Terms|Preprint|Submitted|Accepted|Proceedings)',
    re.I,
)
_AUTHOR_AFFIL_HINT_RE = re.compile(
    r'university|institute|department|laboratory|\blab\b|school of|college of|'
    r'horizon|google|meta|microsoft|nvidia|amazon|facebook|openai',
    re.I,
)
_AUTHOR_JUNK_PHRASE_RE = re.compile(
    r'equal\s+contrib|correspond(?:ing|ence)\s+auth|project\s+lead(?:er)?|'
    r'human\s+egocentric|post[\s-]?training|pre[\s-]?training|'
    r'worldbench\s+team|contact[\s-]?rich|zero[\s-]?shot|'
    r'mixture[\s-]of[\s-]|figure\s*\d|tactile[\s-]?reactive|in[\s-]?the[\s-]?wild',
    re.I,
)
_AUTHOR_JUNK_WORDS = frozenset({
    "equal", "contribution", "contributions", "corresponding", "correspondence",
    "author", "authors", "project", "leader", "lead", "human", "egocentric",
    "post", "pre", "training", "tasks", "task", "model", "models", "dataset",
    "encoder", "backbone", "expert", "experts", "latent", "action", "tactile",
    "spatial", "temporal", "contact", "rich", "skills", "team", "worldbench",
    "university", "institute", "inc", "laboratory", "lab", "school", "college",
    "department", "figure", "abstract", "arxiv", "preprint", "submitted",
    "accepted", "proceedings", "berkeley", "nvidia", "stanford", "google", "meta",
    "microsoft", "amazon", "openai", "alibaba", "singapore", "china", "email",
    "contact", "overview", "following", "grounding", "efficient", "diverse",
    "objects", "videos", "trajectories", "primitives", "teleoperation", "motor",
    "language", "image", "images", "signals", "wrist", "view", "head", "slow",
    "fast", "future", "visual", "prediction", "refinement", "denosing", "toothpaste",
    "apply", "pour", "drill", "dumpling", "rollup", "wrap", "fold", "peel", "close",
    "wipe", "squeeze", "insert", "extract", "cube", "make", "roll",
    "wipe", "squeeze", "insert", "extract", "natural", "daily", "interactions",
    "manipulation", "reactive", "world", "rl", "posttraining", "pretraining",
})
_NAME_LIKE_RE = re.compile(
    r'(?:[A-Z][a-z]+(?:[-\'][A-Z][a-z]+)?|[A-Z]{2,})(?:\s+(?:[A-Z]\.?|[A-Z][a-z]+(?:[-\'][A-Z][a-z]+)?|[A-Z]{2,}))+'
    r'|[\u4e00-\u9fff]{2,4}(?:\s*[\u4e00-\u9fff]{1,3})?'
)
_MAX_AUTHOR_LINE_SHORT = 250
_MAX_AUTHOR_LINE_LONG  = 900

def _name_like_tokens(txt: str) -> list[str]:
    return [m.group(0).strip() for m in _NAME_LIKE_RE.finditer(txt)]

def _line_looks_like_author_list(txt: str) -> bool:
    if txt.count(",") < 1 and not re.search(r'\band\b', txt, re.I):
        return False
    names = _name_like_tokens(txt)
    good = [n for n in names if is_valid_author_name(n)]
    return len(good) >= 2

def is_valid_author_name(name: str) -> bool:
    name = re.sub(r'[\d\*†‡§∗\[\]（）()]+', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip(' ,;.')
    if not name or len(name) < 3 or len(name) > 60:
        return False
    if _AUTHOR_JUNK_PHRASE_RE.search(name):
        return False
    if _AUTHOR_SKIP_RE.match(name) or re.match(r'^Abstract\b', name, re.I):
        return False
    if re.match(r'^https?://', name, re.I):
        return False
    if re.search(r'[\u4e00-\u9fff]', name):
        han = re.findall(r'[\u4e00-\u9fff]+', name)
        return bool(han) and all(2 <= len(h) <= 4 for h in han)
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", name)
    if len(words) < 2:
        return False
    if any(len(w) == 1 and not re.match(r'^[A-Z]\.?$', w) for w in words):
        return False
    lower_words = [w.lower() for w in words]
    if all(w in _AUTHOR_JUNK_WORDS for w in lower_words):
        return False
    if _AUTHOR_AFFIL_HINT_RE.search(name) and sum(
        1 for w in lower_words if w not in _AUTHOR_JUNK_WORDS
    ) < 2:
        return False
    name_like = sum(
        1 for w in words
        if (len(w) >= 2 and w[0].isupper() and w.lower() not in _AUTHOR_JUNK_WORDS)
    )
    return name_like >= 2

def is_valid_author_line(txt: str) -> bool:
    if len(txt) < 6 or len(txt) > _MAX_AUTHOR_LINE_LONG:
        return False
    if re.match(r'^[\d\s.\-]+$', txt):
        return False
    if _AUTHOR_SKIP_RE.match(txt) or re.match(r'^Abstract\b', txt, re.I):
        return False
    if _AUTHOR_JUNK_PHRASE_RE.search(txt):
        return False
    if re.match(r'^https?://', txt, re.I):
        return False
    if any(c in txt for c in '{}$\\'):
        return False
    if '@' in txt:
        return False
    lines = [ln.strip() for ln in txt.split('\n') if ln.strip()]
    if len(lines) >= 2:
        valid_lines = [ln for ln in lines if is_valid_author_name(ln)]
        if len(valid_lines) >= 2:
            return True
    if _line_looks_like_author_list(txt):
        return True
    names = _parse_author_names(txt, validate=False)
    valid = [n for n in names if is_valid_author_name(n)]
    if valid:
        return True
    if 2 <= len(txt.split()) <= 12 and is_valid_author_name(txt):
        return True
    return False

def clean_authors(authors: list[str] | str | None) -> list[str]:
    if not authors:
        return []
    if isinstance(authors, str):
        authors = [authors]
    out: list[str] = []
    seen: set[str] = set()
    for raw in authors:
        for name in _parse_author_names(str(raw)):
            if not is_valid_author_name(name):
                continue
            key = name.lower()
            if key not in seen:
                seen.add(key)
                out.append(name)
    return out[:20]

def authors_look_invalid(authors: list[str] | str | None) -> bool:
    if not authors:
        return False
    if isinstance(authors, str):
        authors = [authors]
    joined = ", ".join(str(a) for a in authors)
    if any(c in joined for c in '{}$\\'):
        return True
    if _AUTHOR_JUNK_PHRASE_RE.search(joined):
        return True
    cleaned = clean_authors(authors)
    if not cleaned:
        return True
    if len(cleaned) < max(1, len(authors) // 2):
        return True
    invalid = sum(1 for a in authors if not is_valid_author_name(str(a).strip()))
    return invalid > len(authors) // 2

def _looks_like_author_line(txt: str) -> bool:
    return is_valid_author_line(txt)

def _parse_author_names(txt: str, *, validate: bool = True) -> list[str]:
    txt = re.sub(r'[{}$\\]', '', txt)
    txt = re.sub(r'[\d\*†‡§∗]+', '', txt)
    txt = re.sub(r'\S+@\S+', '', txt)
    txt = re.sub(r'[ \t]+', ' ', txt).strip(' ,;')
    if not txt:
        return []
    parts = re.split(r',|\band\b|、|·|\n', txt, flags=re.I)
    names: list[str] = []
    for part in parts:
        name = re.sub(r'\s+', ' ', part).strip(' ,;')
        if not name or len(name) < 2 or len(name) > 60:
            continue
        if validate and not is_valid_author_name(name):
            continue
        if re.search(r'[A-Za-z\u4e00-\u9fff]', name):
            names.append(name)
    if not names and _line_looks_like_author_list(txt):
        for name in _name_like_tokens(txt):
            name = re.sub(r'\s+', ' ', name).strip(' ,;')
            if validate and not is_valid_author_name(name):
                continue
            if name:
                names.append(name)
    return names

def _extract_authors(blocks: list, *, title: str | None = None) -> list[str]:
    if not blocks:
        return []
    text_blocks = [b for b in blocks if b[6] == 0]
    if not text_blocks:
        return []
    page_h = max(b[3] for b in text_blocks) if text_blocks else 800
    sorted_blocks = sorted(text_blocks, key=lambda b: b[1])

    abstract_y = page_h
    for b in sorted_blocks:
        txt = re.sub(r'\s+', ' ', b[4]).strip()
        if re.match(r'^Abstract\b', txt, re.I):
            abstract_y = b[1]
            break

    title_bottom = 0.0
    if title:
        needle = title[:50].lower()
        for b in sorted_blocks:
            txt = re.sub(r'\s+', ' ', b[4]).strip()
            if needle and (needle in txt.lower() or txt.lower()[:50] in needle):
                title_bottom = b[3]
                break

    author_lines: list[str] = []
    for b in sorted_blocks:
        if b[1] <= title_bottom + 2:
            continue
        if b[1] >= abstract_y - 2:
            break
        txt = b[4].strip()
        if not txt:
            continue
        if len(txt) > _MAX_AUTHOR_LINE_LONG:
            if author_lines:
                break
            continue
        if len(txt) > _MAX_AUTHOR_LINE_SHORT and not _line_looks_like_author_list(txt):
            if author_lines:
                break
            continue
        if _looks_like_author_line(txt):
            author_lines.append(txt)
            if _line_looks_like_author_list(txt) or len(clean_authors(_parse_author_names(txt))) >= 3:
                break
        elif author_lines:
            break
        elif _AUTHOR_AFFIL_HINT_RE.search(txt):
            continue

    authors: list[str] = []
    for line in author_lines[:3]:
        authors.extend(_parse_author_names(line))

    return clean_authors(authors)[:15]

def extract_pdf_metadata(pdf_path: Path, fitz) -> dict:
    result: dict[str, Any] = {
        "title": None, "abstract": None, "authors": None,
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

        result["title"]    = _extract_title(blocks, stem=pdf_path.stem)
        result["abstract"] = _extract_abstract(text)
        authors = _extract_authors(blocks, title=result["title"])
        if authors and not authors_look_invalid(authors):
            result["authors"] = authors

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

def _parse_arxiv_xml(xml: str) -> dict | None:
    """从 arXiv Atom API 响应解析第一篇 entry 的元数据。"""
    entries = re.findall(r"<entry>(.*?)</entry>", xml, re.DOTALL)
    if not entries:
        return None
    entry = entries[0]
    titles = [
        re.sub(r"\s+", " ", t).strip()
        for t in re.findall(r"<title[^>]*>(.*?)</title>", entry, re.DOTALL)
        if t.strip()
    ]
    abstracts = re.findall(r"<summary[^>]*>(.*?)</summary>", entry, re.DOTALL)
    ids = re.findall(r"<id[^>]*>.*?(\d{4}\.\d{4,5})(?:v\d+)?</id>", entry)
    dates = re.findall(r"<published>(.*?)</published>", entry)
    cats = re.findall(r'<arxiv:primary_category[^/]* term="([^"]+)"', entry)
    if not titles:
        return None
    title = titles[0]
    if is_junk_title(title):
        return None
    author_names = [
        re.sub(r"\s+", " ", n).strip()
        for n in re.findall(r"<name>(.*?)</name>", entry)
        if n.strip()
    ]
    year = month = None
    if dates:
        m = re.match(r"(\d{4})-(\d{2})", dates[0])
        if m:
            year, month = int(m.group(1)), int(m.group(2))
    aid = ids[0] if ids else None
    if not year and aid:
        year, month = _parse_arxiv_id(aid)
    return {
        "title": title,
        "abstract": abstracts[0].strip() if abstracts else None,
        "authors": author_names or None,
        "arxiv_id": aid,
        "arxiv_cat": cats[0] if cats else None,
        "pub_year": year,
        "pub_month": month,
    }

def _apply_online(paper: dict, result: dict, source: str = "online") -> None:
    for f in ("title", "abstract", "authors", "arxiv_id", "arxiv_cat", "pub_year", "pub_month"):
        if not result.get(f):
            continue
        if f == "title":
            cur = paper.get("title")
            if (
                not cur
                or paper.get("_title_is_filename")
                or is_junk_title(cur, paper)
            ) and not is_junk_title(result[f]):
                paper[f] = result[f]
                paper.pop("_title_is_filename", None)
        elif f == "authors":
            new_authors = clean_authors(result[f])
            if not new_authors:
                continue
            cur = paper.get("authors")
            if not cur or authors_look_invalid(cur):
                paper[f] = new_authors
        elif not paper.get(f):
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

        parsed = _parse_arxiv_xml(xml)
        if parsed and (arxiv_id or _title_sim(paper.get("title"), parsed["title"]) > 0.45):
            result = parsed
            if arxiv_id:
                result["arxiv_id"] = arxiv_id
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
        parsed = _parse_arxiv_xml(xml)
        if parsed:
            result = parsed
            result["arxiv_id"] = arxiv_id
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
           f"?fields=title,year,publicationDate,abstract,authors")
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
        s2_authors = [a.get("name") for a in (data.get("authors") or []) if a.get("name")]
        result = {
            "title": data.get("title"), "abstract": data.get("abstract"),
            "authors": s2_authors or None,
            "arxiv_id": arxiv_id, "arxiv_cat": None,
            "pub_year": year, "pub_month": month,
        }

    cache["online"][key] = result
    if result:
        _apply_online(paper, result, "semanticscholar")
        return True
    return False

def _enrich_s2_authors_only(paper: dict, cache: dict) -> bool:
    """Semantic Scholar lookup focused on author names (no year required)."""
    arxiv_id = paper.get("arxiv_id")
    if not arxiv_id:
        return False
    key = f"s2authors:{arxiv_id}"
    if key in cache["online"]:
        cached = cache["online"][key]
        if cached and cached.get("authors"):
            _apply_online(paper, cached, "semanticscholar")
        return bool(cached and cached.get("authors"))

    url = (f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}"
           f"?fields=title,authors")
    time.sleep(ONLINE_DELAY)
    data = _fetch_json(url)
    result = None
    if data:
        s2_authors = clean_authors(
            [a.get("name") for a in (data.get("authors") or []) if a.get("name")]
        )
        if s2_authors:
            result = {
                "title": data.get("title"),
                "authors": s2_authors,
                "arxiv_id": arxiv_id,
            }

    cache["online"][key] = result
    if result:
        _apply_online(paper, result, "semanticscholar")
        return True
    return False

def resolve_paper_authors(
    paper: dict,
    pdf_path: Path,
    fitz,
    cache: dict,
    online: bool,
) -> None:
    """Sanitize, re-extract, or online-fetch authors; hide garbage when still invalid."""
    authors = paper.get("authors")
    if authors and not authors_look_invalid(authors):
        cleaned = clean_authors(authors)
        if cleaned:
            paper["authors"] = cleaned
            return
        paper.pop("authors", None)

    if authors and authors_look_invalid(authors):
        paper.pop("authors", None)

    meta = extract_pdf_metadata(pdf_path, fitz)
    if meta.get("authors") and not authors_look_invalid(meta["authors"]):
        paper["authors"] = meta["authors"]
        return

    if online and paper.get("arxiv_id"):
        _enrich_arxiv_by_id(paper, cache)
        if paper.get("authors") and not authors_look_invalid(paper["authors"]):
            paper["authors"] = clean_authors(paper["authors"])
            return
        paper.pop("authors", None)
        _enrich_s2_authors_only(paper, cache)
        if paper.get("authors") and not authors_look_invalid(paper["authors"]):
            paper["authors"] = clean_authors(paper["authors"])
            return

    paper.pop("authors", None)

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
           f"?query={q}&limit=3&fields=title,year,publicationDate,externalIds,abstract,authors")
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
                s2_authors = [a.get("name") for a in (item.get("authors") or []) if a.get("name")]
                result = {
                    "title": item.get("title"), "abstract": item.get("abstract"),
                    "authors": s2_authors or None,
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
            or authors_look_invalid(paper.get("authors"))
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
                for f in ("pub_year", "pub_month", "pub_date_source", "title", "abstract", "authors", "arxiv_id", "arxiv_cat"):
                    if paper.get(f) is not None:
                        cache["papers"][ckey][f] = paper[f]
                cache["papers"][ckey]["needs_review"] = bool(
                    paper.get("_title_is_filename")
                    or not paper.get("pub_year")
                    or is_junk_title(paper.get("title"), paper)
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
            paper.get("_title_is_filename")
            or not paper.get("pub_year")
            or is_junk_title(paper.get("title"), paper)
        )


def sanitize_authors_cache(cache: dict) -> int:
    """清除缓存中明显错误的作者列表，便于重新提取或在线补全。"""
    fixed = 0
    for paper in cache.get("papers", {}).values():
        authors = paper.get("authors")
        if not authors:
            continue
        joined = ", ".join(str(a) for a in (authors if isinstance(authors, list) else [authors]))
        if any(c in joined for c in '{}$\\') or authors_look_invalid(authors):
            paper.pop("authors", None)
            fixed += 1
            continue
        cleaned = clean_authors(authors)
        if cleaned != authors:
            paper["authors"] = cleaned or None
            if not paper.get("authors"):
                paper.pop("authors", None)
            fixed += 1
    return fixed

_SUMMARY_FIELDS_TO_CLEAR = (
    "summary_zh", "summary_zh_llm", "summary_llm_model", "summary_llm_at",
    "summary_llm_input_hash", "summary_rule_version",
)


def _clear_summary_cache(paper: dict) -> None:
    for f in _SUMMARY_FIELDS_TO_CLEAR:
        paper.pop(f, None)


def resolve_junk_title(
    paper: dict,
    pdf_path: Path | None,
    fitz,
    cache: dict,
    online: bool,
) -> bool:
    """
    修复垃圾标题：有 arXiv ID 时优先 API → PDF 重提取 → 文件名 stem → needs_review。
    返回 True 表示已得到非垃圾标题。
    """
    if not is_junk_title(paper.get("title"), paper):
        return False

    old_title = paper.get("title")
    arxiv_id = paper.get("arxiv_id")

    if arxiv_id and online:
        paper.pop("title", None)
        _enrich_arxiv_by_id(paper, cache)
        if paper.get("title") and not is_junk_title(paper.get("title"), paper):
            paper.pop("_title_is_filename", None)
            _clear_summary_cache(paper)
            return True

    if pdf_path and pdf_path.exists() and fitz:
        meta = extract_pdf_metadata(pdf_path, fitz)
        candidate = meta.get("title")
        if candidate and not is_junk_title(candidate, paper):
            paper["title"] = candidate
            paper.pop("_title_is_filename", None)
            _clear_summary_cache(paper)
            return True

    if arxiv_id and online:
        _enrich_arxiv_by_id(paper, cache)
        if paper.get("title") and not is_junk_title(paper.get("title"), paper):
            paper.pop("_title_is_filename", None)
            _clear_summary_cache(paper)
            return True

    stem = paper.get("stem") or (pdf_path.stem if pdf_path else "")
    fallback = title_from_stem(stem)
    if fallback and not is_junk_title(fallback, paper):
        paper["title"] = fallback
        paper["_title_is_filename"] = True
        _clear_summary_cache(paper)
        return True

    if old_title and not paper.get("title"):
        paper["title"] = old_title
    paper["needs_review"] = True
    return False


def sanitize_junk_titles_cache(cache: dict) -> int:
    """清除缓存中的垃圾标题并标记待重 enrichment（含摘要缓存）。"""
    cleared = 0
    for paper in cache.get("papers", {}).values():
        if not is_junk_title(paper.get("title"), paper):
            continue
        _clear_summary_cache(paper)
        paper["needs_review"] = True
        if paper.get("arxiv_id"):
            paper.pop("title", None)
            paper["_title_is_filename"] = True
        cleared += 1
    return cleared


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
) -> tuple[list[dict], list[dict]]:
    pdf_files = sorted(lib_path.rglob("*.pdf"))
    total     = len(pdf_files)
    print(f"\n[{lib_name}] Found {total} PDFs")

    papers: list[dict] = []
    excluded: list[dict] = []
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
            rel = pdf_path.relative_to(lib_path)
            excluded.append({
                "stem": pdf_path.stem,
                "path": str(pdf_path),
                "rel_path": str(rel),
                "folder": rel.parts[0] if len(rel.parts) > 1 else "_root",
                "library": lib_name,
                "_exclude_reason": "read_error",
            })
            skipped += 1
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
            resolve_paper_authors(paper, pdf_path, fitz, cache, online)
            ensure_intro_excerpt(paper, pdf_path, fitz)
            if paper.get("pub_year") and not paper.get("pub_date_source"):
                paper["pub_date_source"] = "arxiv_id" if paper.get("arxiv_id") else "pdf"
            if is_junk_title(paper.get("title"), paper):
                resolve_junk_title(paper, pdf_path, fitz, cache, online)
                if is_junk_title(paper.get("title"), paper):
                    paper["needs_review"] = True
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

            if not paper.get("title") or is_junk_title(paper.get("title"), paper):
                stem_title = title_from_stem(stem)
                if stem_title and not is_junk_title(stem_title):
                    paper["title"] = stem_title
                    paper["_title_is_filename"] = True
                else:
                    paper["title"] = re.sub(r"[_\-]+", " ", stem).strip()
                    paper["_title_is_filename"] = True

            if is_junk_title(paper.get("title"), paper):
                resolve_junk_title(paper, pdf_path, fitz, cache, online)

            if paper.get("pub_year") and not paper.get("pub_date_source"):
                paper["pub_date_source"] = "pdf" if meta.get("pub_year") else "arxiv_id"

            enrich_paper(paper, cache, online)

            if is_junk_title(paper.get("title"), paper):
                paper.pop("title", None)
                paper["_title_is_filename"] = True

            paper["needs_review"] = bool(
                paper.get("_title_is_filename")
                or not paper.get("pub_year")
                or is_junk_title(paper.get("title"), paper)
            )
            paper["_ckey"] = ckey
            ensure_intro_excerpt(paper, pdf_path, fitz)

        sanitize_pub_date(paper, pdf_path=pdf_path, fitz=fitz)

        cacheable = {k: v for k, v in paper.items() if k not in ("mtime", "birthtime")}
        cache["papers"][ckey] = cacheable

        ex, reason = should_exclude(paper)
        if ex:
            skipped += 1
            fail = dict(paper)
            fail["_exclude_reason"] = reason
            excluded.append(fail)
            continue

        papers.append(paper)

    print(f"\r  Done: {len(papers)} papers ({skipped} excluded)             ")
    return papers, excluded

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

# ── Unparsed / failed entries ──────────────────────────────────────────────────

def _unparsed_entry(paper: dict, reason: str, public: bool) -> dict[str, Any]:
    """Serialize one file that did not make it into the main paper list."""
    obj: dict[str, Any] = {
        "path":       paper.get("path", ""),
        "rel_path":   paper.get("rel_path", ""),
        "stem":       paper.get("stem", ""),
        "filename":   Path(paper.get("path", "")).name,
        "folder":     paper.get("folder", ""),
        "library":    paper.get("library", ""),
        "reason":     reason,
        "title":      paper.get("title"),
        "arxiv_id":   paper.get("arxiv_id"),
        "pub_year":   paper.get("pub_year"),
        "needs_review": bool(paper.get("needs_review")),
        "size":       paper.get("size"),
    }
    junk = junk_title_reasons(paper.get("title"), paper)
    if junk:
        obj["junk_reasons"] = junk
    if paper.get("_title_is_filename"):
        obj["title_from_filename"] = True
    if not public:
        if paper.get("mtime") is not None:
            obj["mtime"] = paper["mtime"]
        if paper.get("birthtime") is not None:
            obj["birthtime"] = paper["birthtime"]
    return obj


def build_unparsed_list(
    excluded: list[dict],
    pre_dedupe: list[dict],
    deduped: list[dict],
    no_date: list[dict],
    public: bool,
) -> list[dict]:
    """
    All scanned PDFs not in the final papers.html list.
    Reasons: exclude filter, duplicate copy, or missing publication year.
    """
    keeper_paths = {p["path"] for p in deduped}
    dedupe_removed = [p for p in pre_dedupe if p["path"] not in keeper_paths]

    seen: set[str] = set()
    out: list[dict] = []

    def add(paper: dict, reason: str) -> None:
        path = paper.get("path")
        if not path or path in seen:
            return
        seen.add(path)
        out.append(_unparsed_entry(paper, reason, public))

    for p in excluded:
        add(p, p.get("_exclude_reason") or "excluded")
    for p in dedupe_removed:
        add(p, "duplicate")
    for p in no_date:
        add(p, "no_pub_date")

    out.sort(key=lambda x: (x.get("library", ""), x.get("folder", ""), x.get("stem", "")))
    return out


def _unparsed_to_json(unparsed: list[dict]) -> str:
    return json.dumps(unparsed, ensure_ascii=False, separators=(",", ":"))


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
        authors = clean_authors(p.get("authors"))
        if authors and not authors_look_invalid(authors):
            obj["authors"] = authors
        alts = p.get("alternate_paths")
        if alts:
            obj["alternate_paths"] = alts
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
    unparsed: list[dict],
    public: bool,
) -> str:
    papers_json    = _papers_to_json(papers, public)
    unparsed_json  = _unparsed_to_json(unparsed)
    tag_stats_json = json.dumps(tag_stats, ensure_ascii=False, separators=(",", ":"))
    pub_stats_json = json.dumps(pub_stats, ensure_ascii=False, separators=(",", ":"))
    evolution_json = json.dumps(evolution, ensure_ascii=False, separators=(",", ":"))

    total           = len(papers)
    unparsed_cnt    = sum(1 for u in unparsed if u.get("reason") != "duplicate")
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
        ("__UNPARSED_JSON__",  unparsed_json),
        ("__UNPARSED_CNT__",   str(unparsed_cnt)),
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
        ("__HAS_READING__",    "false" if public else "true"),
    ]:
        html = html.replace(token, value)
    return html

# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Personal Paper Library — generate papers.html")
    ap.add_argument("--no-online", action="store_true", help="Skip online enrichment")
    ap.add_argument("--public",    action="store_true", help="Strip reading timestamps from HTML")
    ap.add_argument("--llm-summary", action="store_true",
                    help="Batch LLM Chinese summaries into cache (default: cache/rules only)")
    ap.add_argument("--llm-limit", type=int, default=None, metavar="N",
                    help="Cap LLM API calls per run")
    ap.add_argument("--llm-model", default=None, metavar="X",
                    help=f"LLM model (default: {LLM_DEFAULT_MODEL})")
    args = ap.parse_args()
    online = not args.no_online
    public = args.public
    llm_model = args.llm_model or LLM_DEFAULT_MODEL

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
    authors_fixed = sanitize_authors_cache(cache)
    if authors_fixed:
        print(f"[Cache] Cleared/fixed {authors_fixed} entries with invalid authors ...")
    junk_cleared = sanitize_junk_titles_cache(cache)
    if junk_cleared:
        print(f"[Cache] Cleared {junk_cleared} junk titles for re-enrichment ...")
        save_cache(cache)

    all_papers: list[dict] = []
    all_excluded: list[dict] = []
    for lib_name, lib_path in LIBRARIES.items():
        if not lib_path.exists():
            print(f"WARNING: not found: {lib_path}", file=sys.stderr)
            continue
        papers, excluded = scan_library(lib_name, lib_path, cache, fitz, online)
        all_papers.extend(papers)
        all_excluded.extend(excluded)

    print(f"\n[Cache] Saving {len(cache['papers'])} entries ...")
    save_cache(cache)

    pre_dedupe = all_papers
    before_dedupe = len(pre_dedupe)
    deduped_all = dedupe_papers(pre_dedupe)
    all_papers = deduped_all
    print(f"Deduped: {before_dedupe} -> {len(all_papers)} ({before_dedupe - len(all_papers)} removed)")

    filled = enrich_missing_dates(all_papers, cache, online)
    if filled:
        print(f"[Cache] Updating cache after online date enrichment ...")
        save_cache(cache)

    no_date_papers = [p for p in all_papers if not p.get("pub_year")]
    all_papers = [p for p in all_papers if p.get("pub_year")]
    skipped_no_date = len(no_date_papers)
    if skipped_no_date:
        print(f"Skipped {skipped_no_date} papers without publication date")

    unparsed = build_unparsed_list(
        all_excluded, pre_dedupe, deduped_all, no_date_papers, public
    )
    print(f"Unparsed/failed: {len(unparsed)} entries for HTML tab")

    print(f"\n[Tagging] {len(all_papers)} papers ...")
    all_papers, tag_stats = tag_all_papers(all_papers)
    print(f"  {tag_stats['unique_tags']} unique tags, {tag_stats['uncategorized']} uncategorized")

    n_flagged = attach_validation_flags(all_papers)
    print(f"  {n_flagged} papers with validation flags")
    for p in all_papers:
        ckey = p.get("_ckey")
        if ckey and ckey in cache["papers"]:
            cache["papers"][ckey]["validation_flags"] = p.get("validation_flags", [])

    if args.llm_summary:
        print(f"\n[Summary] LLM Chinese one-liners (all eligible, model={llm_model}) ...")
        llm_stats = add_llm_summaries(
            all_papers, cache,
            model=llm_model,
            limit=args.llm_limit,
        )
        print(f"  cached={llm_stats['cached']} rule={llm_stats['rule']} "
              f"llm_ok={llm_stats['llm_ok']} llm_fail={llm_stats['llm_fail']} "
              f"skipped_limit={llm_stats['skipped_limit']}")
        save_cache(cache)
    elif os.environ.get("OPENAI_API_KEY"):
        recent_missing = count_recent_missing_llm(all_papers, model=llm_model)
        print(
            f"\n[Summary] Auto LLM for 2025–2026 papers "
            f"({recent_missing} pending, model={llm_model}) ..."
        )
        llm_stats = add_llm_summaries(
            all_papers, cache,
            model=llm_model,
            limit=args.llm_limit,
            recent_years_only=True,
        )
        print(f"  cached={llm_stats['cached']} rule={llm_stats['rule']} "
              f"llm_ok={llm_stats['llm_ok']} llm_fail={llm_stats['llm_fail']} "
              f"skipped_limit={llm_stats['skipped_limit']}")
        save_cache(cache)
    else:
        print(f"\n[Summary] Chinese one-liners (cache + rules, no LLM) ...")
        add_summaries_from_cache(all_papers, cache, model=llm_model)
        save_cache(cache)

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

    html = render_html(all_papers, tag_stats, pub_stats, evolution, unparsed, public)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    size_mb = OUTPUT_HTML.stat().st_size / 1_048_576

    needs_review = sum(1 for p in all_papers if p.get("needs_review"))
    junk_titles = sum(1 for p in all_papers if is_junk_title(p.get("title"), p))
    if not public:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("sync_papers", SCRIPT_DIR / "sync_papers.py")
        _sp = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_sp)
        rs = _sp.reading_stats()
        print(f"Recent reading: {rs['week']} (7d) / {rs['month']} (30d)")
    print(f"\n{'='*50}")
    print(f"Total papers  : {len(all_papers)}")
    print(f"With pub date : {pub_stats['with_date']} ({pub_stats['coverage_pct']}%)")
    print(f"  sources     : {pub_stats['by_source']}")
    print(f"Unique tags   : {tag_stats['unique_tags']}")
    print(f"Uncategorized : {tag_stats['uncategorized']}")
    print(f"Needs review  : {needs_review}")
    print(f"Junk titles   : {junk_titles}")
    if junk_titles:
        print(f"WARNING: {junk_titles} papers still have junk titles!", file=sys.stderr)
    print(f"Unparsed tab  : {len(unparsed)}")
    print(f"Output        : {OUTPUT_HTML}  ({size_mb:.1f} MB)")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
