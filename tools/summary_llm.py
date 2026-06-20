"""
summary_llm.py — LLM 中文一句话摘要（离线批量 / 增量缓存）。

设计原则：
  - 构建 papers.html 时零 LLM 调用，只读 cache
  - --llm-summary 时才调用 API，结果写入 .papers_cache.json
  - 回退链：cache LLM → cache 规则 → 现场规则生成
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Callable

# 变更 prompt / 输出约束时递增，使旧缓存失效
PROMPT_VERSION = "v2"
DEFAULT_MODEL = os.environ.get("SUMMARY_LLM_MODEL", "gpt-4o-mini")
ABSTRACT_PREFIX_LEN = 300
INTRO_EXCERPT_MAX = 1500
SUMMARY_MAX_CHARS = 120
DEFAULT_CONCURRENCY = 10
LLM_YEAR_MIN = 2025
LLM_YEAR_MAX = 2026

PROMPT_TEMPLATE = """你是学术论文阅读助手。根据下列英文论文信息，写一句中文总结。

要求：
1. 仅一句，不超过{max_chars}个汉字（含标点）
2. 结构：提出什么方法/框架 → 解决什么问题 → 核心亮点（可省略第三段若超长）
3. 使用流畅中文，专有名词可保留英文缩写（如 DETR、BEV、VLA）
4. 不要编造未给出的实验数字；无摘要时根据标题合理概括
5. 只输出这一句总结，不要引号、编号或解释

标题：{title}
领域标签：{tags}
摘要节选：{abstract}
"""

PROMPT_TEMPLATE_RECENT = """你是学术论文阅读助手。根据下列英文论文的标题、摘要与 Introduction 节选，写一句中文总结。

要求：
1. 仅一句，不超过{max_chars}个汉字（含标点）
2. 结构：提出什么方法/框架 → 解决什么问题 → 核心洞见或亮点
3. 使用流畅中文，专有名词可保留英文缩写（如 DETR、BEV、VLA）
4. 不要编造未给出的实验数字；信息不足时根据已有文本合理概括
5. 只输出这一句总结，不要引号、编号或解释

标题：{title}
领域标签：{tags}
摘要：{abstract}
Introduction节选：{intro}
"""

# 规则摘要质量启发式（与 summary_zh._latin_ratio 阈值一致）
_LATIN_RATIO_BAD = 0.38


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    return re.sub(r"\s+", " ", text).strip()


def _latin_ratio(text: str) -> float:
    if not text:
        return 0.0
    letters = sum(1 for c in text if c.isalpha() and ord(c) < 128)
    return letters / max(len(text), 1)


def requires_llm_by_year(paper: dict) -> bool:
    """2025–2026 论文强制走 LLM，不用规则生成（LLM 失败时除外）。"""
    yr = paper.get("pub_year")
    if yr is None:
        return False
    try:
        y = int(yr)
    except (TypeError, ValueError):
        return False
    return LLM_YEAR_MIN <= y <= LLM_YEAR_MAX


def _abstract_for_llm(paper: dict) -> str:
    return _normalize_text((paper.get("abstract") or ""))


def _intro_for_llm(paper: dict) -> str:
    return _normalize_text((paper.get("intro_excerpt") or ""))[:INTRO_EXCERPT_MAX]


def _zh_tags(paper: dict, n: int = 3) -> str:
    tags = paper.get("tags") or {}
    parts: list[str] = []
    for key in ("topic", "task", "method"):
        for t in tags.get(key, [])[:2]:
            if t and t != "Uncategorized" and t not in parts:
                parts.append(t)
            if len(parts) >= n:
                break
        if len(parts) >= n:
            break
    return "、".join(parts) or "未分类"


def content_hash(paper: dict, *, model: str = DEFAULT_MODEL) -> str:
    """用于判断输入是否变化，决定是否重算 LLM 摘要。"""
    title = (paper.get("title") or paper.get("stem") or "").strip()
    tags = _zh_tags(paper)
    if requires_llm_by_year(paper):
        abstract = _abstract_for_llm(paper)
        intro = _intro_for_llm(paper)
        blob = f"{PROMPT_VERSION}|{model}|{title}|{abstract}|{intro}|{tags}"
    else:
        abstract = _abstract_for_llm(paper)[:ABSTRACT_PREFIX_LEN]
        blob = f"{PROMPT_VERSION}|{model}|{title}|{abstract}|{tags}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def build_prompt(paper: dict, *, max_chars: int = SUMMARY_MAX_CHARS) -> str:
    title = (paper.get("title") or paper.get("stem") or "未知标题").strip()
    tags = _zh_tags(paper)
    if requires_llm_by_year(paper):
        abstract = _abstract_for_llm(paper) or "（无摘要，请根据标题与 Introduction 推断）"
        intro = _intro_for_llm(paper) or "（无 Introduction 节选，请主要依据摘要）"
        return PROMPT_TEMPLATE_RECENT.format(
            max_chars=max_chars,
            title=title,
            tags=tags,
            abstract=abstract,
            intro=intro,
        )
    abstract = _abstract_for_llm(paper)[:ABSTRACT_PREFIX_LEN]
    if not abstract:
        abstract = "（无摘要，请根据标题推断）"
    return PROMPT_TEMPLATE.format(
        max_chars=max_chars,
        title=title,
        tags=tags,
        abstract=abstract,
    )


def _trim_summary(text: str, max_chars: int = SUMMARY_MAX_CHARS) -> str:
    text = re.sub(r"\s+", "", (text or "").strip().strip("「」『』\"'"))
    text = re.sub(r"^(总结[：:]|摘要[：:])", "", text)
    if len(text) > max_chars:
        text = text[: max_chars - 1] + "…"
    return text


def needs_llm(paper: dict, rule_summary: str | None = None) -> bool:
    """
    两档策略：2025–2026 强制 LLM；其余简单场景用规则，复杂走 LLM。
    返回 True 表示应调用 LLM（在 --llm-summary 或自动近年模式下）。
    """
    from summary_zh import is_weak_summary

    if requires_llm_by_year(paper):
        return True

    title = (paper.get("title") or "").lower()
    if paper.get("needs_review"):
        return True
    flags = paper.get("validation_flags") or []
    if flags:
        return True
    if re.search(r"\b(survey|review|benchmark|dataset|challenge|workshop)\b", title):
        return False
    if rule_summary:
        if is_weak_summary(rule_summary):
            return True
        if _latin_ratio(rule_summary) <= _LATIN_RATIO_BAD and len(rule_summary) >= 12:
            return False
    tags = paper.get("tags") or {}
    if not tags.get("topic") and not tags.get("task"):
        return True
    if not paper.get("abstract"):
        return True
    return False


def cache_llm_valid(paper: dict, *, model: str = DEFAULT_MODEL) -> bool:
    if not paper.get("summary_zh_llm"):
        return False
    if paper.get("summary_llm_model") != model:
        return False
    expected = content_hash(paper, model=model)
    return paper.get("summary_llm_input_hash") == expected


def apply_llm_result(
    paper: dict,
    summary: str,
    *,
    model: str = DEFAULT_MODEL,
) -> None:
    paper["summary_zh_llm"] = _trim_summary(summary)
    paper["summary_llm_model"] = model
    paper["summary_llm_at"] = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    paper["summary_llm_input_hash"] = content_hash(paper, model=model)
    paper["summary_zh"] = paper["summary_zh_llm"]


def _rule_summary_stale(summary: str, *, rule_version: str | None = None) -> bool:
    """旧版规则摘要或空泛 fallback，需重新生成。"""
    from summary_zh import RULE_VERSION, is_weak_summary

    if rule_version != RULE_VERSION:
        return True
    if not summary:
        return True
    if is_weak_summary(summary):
        return True
    bad_patterns = ("方法见标题", "建议阅读摘要", "聚焦", "《")
    return any(p in summary for p in bad_patterns)


def _rule_cache_valid(paper: dict) -> bool:
    from summary_zh import RULE_VERSION

    cached = (paper.get("summary_zh") or "").strip()
    if not cached:
        return False
    if paper.get("summary_rule_version") != RULE_VERSION:
        return False
    return not _rule_summary_stale(cached, rule_version=paper.get("summary_rule_version"))


def resolve_summary_zh(paper: dict, *, model: str = DEFAULT_MODEL) -> str:
    """回退链：cache LLM → 规则（现场或缓存）；2025–2026 跳过规则缓存。"""
    from summary_zh import RULE_VERSION, summarize_zh

    if cache_llm_valid(paper, model=model):
        return paper["summary_zh_llm"]
    if not requires_llm_by_year(paper) and _rule_cache_valid(paper):
        return paper.get("summary_zh") or ""
    s = summarize_zh(paper)
    paper["summary_zh"] = s
    paper["summary_rule_version"] = RULE_VERSION
    return s


def count_recent_missing_llm(papers: list[dict], *, model: str = DEFAULT_MODEL) -> int:
    """2025–2026 中尚无有效 LLM 缓存的论文数。"""
    return sum(
        1 for p in papers
        if requires_llm_by_year(p) and not cache_llm_valid(p, model=model)
    )


def _restore_cache_fields(paper: dict, cached: dict) -> None:
    for field in (
        "summary_zh_llm",
        "summary_llm_model",
        "summary_llm_at",
        "summary_llm_input_hash",
        "summary_zh",
        "summary_rule_version",
        "intro_excerpt",
    ):
        if cached.get(field) is not None:
            paper[field] = cached[field]


# ── LLM 客户端（按需实现；默认 urllib 兼容 OpenAI Chat Completions）──────────

def _default_llm_call(prompt: str, *, model: str) -> str:
    """同步单次调用。需环境变量 OPENAI_API_KEY 或兼容端点。"""
    import urllib.error
    import urllib.request

    api_key = os.environ.get("OPENAI_API_KEY", "")
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 120,
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return (data["choices"][0]["message"]["content"] or "").strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM API error {e.code}: {body[:300]}") from e


async def _async_llm_call(
    prompt: str,
    *,
    model: str,
    llm_call: Callable[[str], str],
    semaphore: asyncio.Semaphore,
) -> str:
    async with semaphore:
        return await asyncio.to_thread(llm_call, prompt)


async def summarize_batch_async(
    papers: list[dict],
    *,
    model: str = DEFAULT_MODEL,
    concurrency: int = DEFAULT_CONCURRENCY,
    llm_call: Callable[[str], str] | None = None,
    only_if_needed: bool = True,
) -> list[tuple[dict, str | None, str | None]]:
    """
    并发生成摘要。返回 [(paper, summary_or_none, error_or_none), ...]
    only_if_needed=True 时跳过 cache 有效且不需要 LLM 的条目。
    """
    from summary_zh import summarize_zh

    if llm_call is None:
        llm_call = lambda p, m=model: _default_llm_call(p, model=m)  # noqa: E731

    semaphore = asyncio.Semaphore(concurrency)
    tasks: list[tuple[dict, asyncio.Task[str]]] = []

    for paper in papers:
        if cache_llm_valid(paper, model=model):
            paper["summary_zh"] = paper["summary_zh_llm"]
            continue
        rule_summary = summarize_zh(paper)
        if only_if_needed and not needs_llm(paper, rule_summary):
            paper["summary_zh"] = rule_summary
            continue
        prompt = build_prompt(paper)
        task = asyncio.create_task(
            _async_llm_call(prompt, model=model, llm_call=llm_call, semaphore=semaphore)
        )
        tasks.append((paper, task))

    results: list[tuple[dict, str | None, str | None]] = []
    for paper, task in tasks:
        try:
            raw = await task
            summary = _trim_summary(raw)
            apply_llm_result(paper, summary, model=model)
            results.append((paper, summary, None))
        except Exception as e:
            results.append((paper, None, str(e)))
    return results


def add_llm_summaries(
    papers: list[dict],
    cache: dict,
    *,
    model: str = DEFAULT_MODEL,
    limit: int | None = None,
    concurrency: int = DEFAULT_CONCURRENCY,
    only_if_needed: bool = True,
    recent_years_only: bool = False,
    llm_call: Callable[[str], str] | None = None,
) -> dict[str, int]:
    """
    LLM 摘要入口：对缺摘要或需重算的论文调用 LLM，并写回 cache。

    recent_years_only=True 时仅处理 2025–2026（有 API key 时的默认自动模式）；
    其余论文走 cache/规则路径。

    返回统计：{"cached": n, "rule": n, "llm_ok": n, "llm_fail": n, "skipped_limit": n}
    """
    from summary_zh import RULE_VERSION, summarize_zh

    stats = {"cached": 0, "rule": 0, "llm_ok": 0, "llm_fail": 0, "skipped_limit": 0}
    pending: list[dict] = []

    def _apply_rule_summary(paper: dict, rule_summary: str) -> None:
        paper["summary_zh"] = rule_summary
        paper["summary_rule_version"] = RULE_VERSION
        ckey = paper.get("_ckey")
        if ckey and ckey in cache.get("papers", {}):
            entry = cache["papers"][ckey]
            entry["summary_zh"] = rule_summary
            entry["summary_rule_version"] = RULE_VERSION

    for paper in papers:
        ckey = paper.get("_ckey")
        if ckey and ckey in cache.get("papers", {}):
            _restore_cache_fields(paper, cache["papers"][ckey])

        if cache_llm_valid(paper, model=model):
            paper["summary_zh"] = paper["summary_zh_llm"]
            stats["cached"] += 1
            continue

        if recent_years_only and not requires_llm_by_year(paper):
            if _rule_cache_valid(paper):
                paper["summary_zh"] = paper.get("summary_zh") or ""
                stats["rule"] += 1
                continue
            rule_summary = summarize_zh(paper)
            _apply_rule_summary(paper, rule_summary)
            stats["rule"] += 1
            continue

        rule_summary = summarize_zh(paper)
        paper["summary_rule_version"] = RULE_VERSION
        if only_if_needed and not needs_llm(paper, rule_summary):
            paper["summary_zh"] = rule_summary
            stats["rule"] += 1
            if ckey and ckey in cache.get("papers", {}):
                entry = cache["papers"][ckey]
                entry["summary_zh"] = rule_summary
                entry["summary_rule_version"] = RULE_VERSION
            continue

        if limit is not None and stats["llm_ok"] + len(pending) >= limit:
            paper["summary_zh"] = rule_summary
            stats["skipped_limit"] += 1
            continue

        pending.append(paper)

    if not pending:
        return stats

    t0 = time.time()
    print(f"\n[LLM Summary] {len(pending)} papers (model={model}, workers={concurrency}) ...")

    if llm_call is None:
        llm_call = lambda p, m=model: _default_llm_call(p, model=m)  # noqa: E731

    async def _run() -> list[tuple[dict, str | None, str | None]]:
        semaphore = asyncio.Semaphore(concurrency)
        tasks = []
        for paper in pending:
            prompt = build_prompt(paper)
            tasks.append(
                (paper, asyncio.create_task(
                    _async_llm_call(prompt, model=model, llm_call=llm_call, semaphore=semaphore)
                ))
            )
        out = []
        for i, (paper, task) in enumerate(tasks):
            try:
                raw = await task
                summary = _trim_summary(raw)
                apply_llm_result(paper, summary, model=model)
                out.append((paper, summary, None))
            except Exception as e:
                from summary_zh import summarize_zh as _sz

                paper["summary_zh"] = _sz(paper)
                out.append((paper, None, str(e)))
            if (i + 1) % 20 == 0 or i + 1 == len(tasks):
                print(f"\r  {i+1}/{len(tasks)} ...", end="", flush=True)
        return out

    results = asyncio.run(_run())
    print(f"\r  Done in {time.time() - t0:.1f}s                    ")

    for paper, summary, err in results:
        ckey = paper.get("_ckey")
        if summary and ckey and ckey in cache.get("papers", {}):
            entry = cache["papers"][ckey]
            entry["summary_zh_llm"] = paper["summary_zh_llm"]
            entry["summary_llm_model"] = paper["summary_llm_model"]
            entry["summary_llm_at"] = paper["summary_llm_at"]
            entry["summary_llm_input_hash"] = paper["summary_llm_input_hash"]
            entry["summary_zh"] = paper["summary_zh"]
            if paper.get("intro_excerpt"):
                entry["intro_excerpt"] = paper["intro_excerpt"]
            stats["llm_ok"] += 1
        elif err:
            stats["llm_fail"] += 1
            if stats["llm_fail"] <= 3:
                print(f"  WARN: {paper.get('title', '')[:50]} — {err}")

    return stats


def _invalidate_stale_rule_summaries(cache: dict) -> int:
    """RULE_VERSION 变更或弱摘要时清除 cache 中的旧规则摘要。"""
    from summary_zh import RULE_VERSION, is_weak_summary

    cleared = 0
    for entry in cache.get("papers", {}).values():
        ver = entry.get("summary_rule_version")
        summary = (entry.get("summary_zh") or "").strip()
        if ver == RULE_VERSION and summary and not is_weak_summary(summary):
            continue
        if summary or ver:
            entry.pop("summary_zh", None)
            entry.pop("summary_rule_version", None)
            cleared += 1
    return cleared


def add_summaries_from_cache(papers: list[dict], cache: dict, *, model: str = DEFAULT_MODEL) -> None:
    """
    构建主路径（无 LLM 调用）：从 cache 恢复 LLM 摘要，否则规则生成。
    2025–2026 论文跳过规则缓存，无 LLM 缓存时用规则作 fallback 并告警。
    不发起任何网络请求。
    """
    from summary_zh import RULE_VERSION, summarize_zh

    _invalidate_stale_rule_summaries(cache)
    recent_rule_fallback = 0
    for paper in papers:
        ckey = paper.get("_ckey")
        if ckey and ckey in cache.get("papers", {}):
            _restore_cache_fields(paper, cache["papers"][ckey])

        if cache_llm_valid(paper, model=model):
            paper["summary_zh"] = paper["summary_zh_llm"]
            continue

        if requires_llm_by_year(paper):
            recent_rule_fallback += 1
            paper["summary_zh"] = summarize_zh(paper)
            paper["summary_rule_version"] = RULE_VERSION
            if ckey and ckey in cache.get("papers", {}):
                entry = cache["papers"][ckey]
                entry["summary_zh"] = paper["summary_zh"]
                entry["summary_rule_version"] = RULE_VERSION
            continue

        if _rule_cache_valid(paper):
            paper["summary_zh"] = paper.get("summary_zh") or ""
            continue

        paper["summary_zh"] = summarize_zh(paper)
        paper["summary_rule_version"] = RULE_VERSION
        if ckey and ckey in cache.get("papers", {}):
            entry = cache["papers"][ckey]
            entry["summary_zh"] = paper["summary_zh"]
            entry["summary_rule_version"] = RULE_VERSION

    missing = count_recent_missing_llm(papers, model=model)
    if missing:
        print(
            f"  WARN: {missing} 篇 2025–2026 论文尚无 LLM 摘要缓存，"
            f"当前使用规则 fallback（{recent_rule_fallback} 篇）。"
            f"设置 OPENAI_API_KEY 后重新运行以生成 LLM 摘要。"
        )
