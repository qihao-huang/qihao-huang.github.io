"""
paper_filter.py — 识别非论文/不合理条目（课件、slides、空文件、教程等）。
"""

from __future__ import annotations
import re
import unicodedata
from datetime import datetime
from pathlib import Path

MAX_PUB_YEAR = datetime.now().year  # 发表年份上限（不含未来年份）

# 路径中含这些目录 → 非论文收藏
EXCLUDED_DIR_PARTS: tuple[str, ...] = (
    "course_slides/",
    "e2e-tutorial/",
    "SLAM_summer/",
    "_excluded/",
)

# 文件名/标题命中 → 排除
STEM_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"(?i)^\d+-slides$", "numbered_slides"),
    (r"(?i)tutorialslides", "tutorial_slides"),
    (r"(?i)^slides of ", "slides_prefix"),
    (r"(?i)\s+slides$", "slides_suffix"),
    (r"(?i)^final_presentation", "presentation_deck"),
    (r"(?i)^wayve_tutorial", "tutorial_deck"),
    (r"(?i)^cmu_stereo_lecture", "lecture_deck"),
    (r"(?i)_slides$", "slides_deck"),
    (r"(?i)^lecture\d+", "lecture_deck"),
    (r"(?i)^simclr slides$", "slides_deck"),
    (r"(?i)^netwarp\.pdf$", "slides_deck"),  # 常为 slide 配套
    (r"(?i)^valse-", "valse_talk"),
    (r"(?i)^arun_mallya-intro", "intro_slides"),
    (r"(?i)^intro\.pdf$", "intro_slides"),
)

CN_JUNK_KEYWORDS: tuple[str, ...] = (
    "课件", "公开课", "暑期学校", "模型实现讲解", "讲解与实践", "合辑",
    "开课仪式", "实践作业", "问题汇总", "环境配置与实践", "泰坦公开课",
    "嵌入式AI合辑", "CV前沿讲座", "CV研究合辑", "自动驾驶概述与挑战",
    "自动驾驶决策规划", "端到端模型的训练与闭环评测", "预测规划的联合方法",
    "单目深度估计公开课", "从BEV到End to End", "从BEV到Occupancy",
    "基于征程芯片的BEV算法部署", "自动驾驶中的4D Label概述",
    "时序特征融合的视频实例分割", "计算机如何理解视频动作", "视觉SLAM",
    "相机模型与投影变换", "章国锋-",
)

# 无摘要 + 中文文件名 → 课件/笔记（非 arXiv 论文）
CN_NO_ABS_PATTERN = re.compile(r"[\u4e00-\u9fff]")

# 误解析标题特征
_JUNK_RESEARCHGATE = re.compile(r"See discussions, stats", re.I)
_JUNK_AFFILIATION = re.compile(r"(?:^|\d)Affiliation not available", re.I)
_JUNK_CN_MULTI_SECTION = re.compile(r"基于.*[（(].*[)）].*[：:].*基于")
_JUNK_CN_BASED_SECTION = re.compile(r"基于[^:：]{2,50}[（(][^)）]+[)）][：:]")
_JUNK_CVPR_WATERMARK = re.compile(
    r"This (?:CVPR|ICCV|WACV) (?:workshop )?paper is the Open Access version", re.I
)
_JUNK_ACCEPTED_ARTICLE = re.compile(
    r"This article has been accepted for publication in a future issue", re.I
)
_JUNK_TO_APPEAR = re.compile(r"To appear in:", re.I)
_JUNK_ACCEPTED_VERSION = re.compile(r"accepted version of the following article", re.I)
_JUNK_JOURNAL_BOILERPLATE = re.compile(r"Reprints and permission:\s*sagepub", re.I)
_JUNK_ARXIV_QUERY = re.compile(r"^arXiv Query:", re.I)
_JUNK_NUMBERED_OUTLINE = re.compile(r"^\d+\.\s+.{10,}")
_JUNK_UNDER_REVIEW = re.compile(
    r"(?:^under review(?: as a conference paper)?(?: at \w+ \d{4})?$"
    r"|^preprint\.?\s*under review\.?$"
    r"|submitted to .+ under review)",
    re.I,
)
_JUNK_LATEX_TEMPLATE = re.compile(r"^JOURNAL OF LATEX CLASS FILES", re.I)
_JUNK_IEEE_HEADER = re.compile(
    r"^(?:SUBMITTED TO )?IEEE TRANSACTIONS ON .+(?:\d+\s*)?$", re.I
)
_JUNK_PROCEEDINGS = re.compile(
    r"^Proceedings of (?:the )?(?:\d+(?:st|nd|rd|th) )?(?:International )?(?:Conference|Workshop|Symposium)",
    re.I,
)
_JUNK_PREPRINT_HEADER = re.compile(r"^Preprint\.?\s*$", re.I)
_JUNK_DOWNLOAD_PDF = re.compile(r"^Download PDF", re.I)
_JUNK_SUPPLEMENTARY = re.compile(r"^Supplementary Material:\s*", re.I)
_JUNK_ICLR_FOOTER = re.compile(
    r"^(?:Published|Under review) as a conference paper at ICLR \d{4}\.?$", re.I
)
_JUNK_CONF_PAPER = re.compile(
    r"(?i)^Published as a conference paper at\b", re.I
)
_JUNK_UNDER_REVIEW_CONF = re.compile(
    r"(?i)^Under review as a conference paper at\b", re.I
)
# 中文 PDF 批注/读书笔记段落标题（非论文正式标题）
_JUNK_CN_ANNOTATION_PREFIX = re.compile(
    r"^(?:动机|观察|提出|背景|方法|结论|贡献|问题|创新点|亮点|总结|概述|"
    r"核心思想|主要贡献|实验结果|局限性)[：:\s]",
    re.I,
)
_JUNK_CN_OBSERVATION = re.compile(r"^观察[：:\s]", re.I)
_JUNK_CN_MOTIVATION = re.compile(r"^动机[：:\s]", re.I)
_JUNK_CN_PROPOSE = re.compile(r"^提出[：:\s]", re.I)
_JUNK_CN_CONTRIBUTION = re.compile(r"该论.{0,2}核心贡献", re.I)
_JUNK_CN_CLASSIC_EXAMPLE = re.compile(r"^经典例.{0,2}[：:]", re.I)
_JUNK_CN_METHOD_PLACEHOLDER = re.compile(r"^聚焦.{2,20}[，,]方法见标题", re.I)
_JUNK_CN_SEE_ABSTRACT = re.compile(r"详见摘要")
_JUNK_CN_READER_COMMENTARY = re.compile(
    r"(?:^|[：:]\s*)(?:作者试图|本文试图|该文试图|论文试图|作者希望|作者旨在)",
    re.I,
)
_JUNK_CN_PAPER_REF = re.compile(r"^该论文[：:\s]", re.I)

# 标题长度上限（超过视为摘要/批注误解析）
_MAX_TITLE_LEN = 200


def arxiv_id_to_pub_date(arxiv_id: str) -> tuple[int, int] | None:
    """arXiv 新编号 YYMM.NNNNN → (year, month)；无效则 None。"""
    if not is_valid_arxiv_id(arxiv_id):
        return None
    yy, mm = int(arxiv_id[:2]), int(arxiv_id[2:4])
    year = 1900 + yy if yy >= 91 else 2000 + yy
    return year, mm


def is_valid_arxiv_id(arxiv_id: str | None) -> bool:
    """校验 arXiv 新编号格式 YYMM.NNNNN（2007 年后主流格式）。"""
    if not arxiv_id:
        return False
    m = re.match(r"^(\d{4})\.(\d{4,5})(?:v\d+)?$", arxiv_id.strip())
    if not m:
        return False
    yymm = m.group(1)
    suffix = m.group(2)
    yy, mm = int(yymm[:2]), int(yymm[2:4])
    if mm < 1 or mm > 12:
        return False
    if suffix == "00000" or yymm.startswith("0001"):
        return False
    year = 1900 + yy if yy >= 91 else 2000 + yy
    if year < 1991 or year > MAX_PUB_YEAR:
        return False
    # 0704 起新编号；更早的 9912.xxxx 等仍可能出现
    if int(yymm) < 704 and year >= 2000:
        return False
    return True


def is_invalid_arxiv_id(arxiv_id: str | None) -> bool:
    """PDF 首页误解析的假 arXiv ID（空 ID 不算 invalid）。"""
    if not arxiv_id:
        return False
    return not is_valid_arxiv_id(arxiv_id)


def is_plausible_pub_year(year: int | None) -> bool:
    return year is not None and 1990 <= year <= MAX_PUB_YEAR


def junk_title_reasons(title: str | None, paper: dict | None = None) -> list[str]:
    """返回标题被判为垃圾的原因列表；空则正常。"""
    if not title or not title.strip():
        return []
    t = unicodedata.normalize("NFKC", title.strip())
    reasons: list[str] = []

    if len(t) > _MAX_TITLE_LEN:
        reasons.append("too_long")
    if _JUNK_RESEARCHGATE.search(t):
        reasons.append("researchgate")
    if _JUNK_AFFILIATION.search(t):
        reasons.append("affiliation")
    if _JUNK_CN_MULTI_SECTION.search(t):
        reasons.append("cn_multi_section")
    if len(_JUNK_CN_BASED_SECTION.findall(t)) >= 2:
        reasons.append("cn_section_summary")
    if t.count(":") >= 3 or t.count("：") >= 3:
        reasons.append("many_colons")
    parts = [p.strip() for p in re.split(r"[：:] |\n", t) if p.strip()]
    if len(parts) >= 3:
        reasons.append("multi_parts")
    if _JUNK_CVPR_WATERMARK.search(t):
        reasons.append("cvpr_watermark")
    if _JUNK_ACCEPTED_ARTICLE.search(t):
        reasons.append("accepted_article")
    if _JUNK_TO_APPEAR.search(t):
        reasons.append("to_appear")
    if _JUNK_ACCEPTED_VERSION.search(t):
        reasons.append("accepted_version")
    if _JUNK_JOURNAL_BOILERPLATE.search(t):
        reasons.append("journal_boilerplate")
    if _JUNK_ARXIV_QUERY.search(t):
        reasons.append("arxiv_query")
    if _JUNK_NUMBERED_OUTLINE.match(t):
        reasons.append("numbered_outline")
    if _JUNK_UNDER_REVIEW.search(t):
        reasons.append("under_review")
    if _JUNK_LATEX_TEMPLATE.search(t):
        reasons.append("latex_template")
    if _JUNK_IEEE_HEADER.search(t):
        reasons.append("ieee_header")
    if _JUNK_PROCEEDINGS.search(t):
        reasons.append("proceedings")
    if _JUNK_PREPRINT_HEADER.match(t):
        reasons.append("preprint_header")
    if _JUNK_DOWNLOAD_PDF.search(t):
        reasons.append("download_pdf")
    if _JUNK_SUPPLEMENTARY.search(t):
        reasons.append("supplementary")
    if _JUNK_ICLR_FOOTER.match(t):
        reasons.append("iclr_footer")
    if _JUNK_CONF_PAPER.search(t):
        reasons.append("conf_paper_boilerplate")
    if _JUNK_UNDER_REVIEW_CONF.search(t):
        reasons.append("under_review_conf")
    if _JUNK_CN_ANNOTATION_PREFIX.search(t):
        reasons.append("cn_annotation_prefix")
    if _JUNK_CN_OBSERVATION.search(t):
        reasons.append("cn_observation")
    if _JUNK_CN_MOTIVATION.search(t):
        reasons.append("cn_motivation")
    if _JUNK_CN_PROPOSE.search(t):
        reasons.append("cn_propose")
    if _JUNK_CN_CONTRIBUTION.search(t):
        reasons.append("cn_contribution")
    if _JUNK_CN_CLASSIC_EXAMPLE.search(t):
        reasons.append("cn_classic_example")
    if _JUNK_CN_METHOD_PLACEHOLDER.search(t):
        reasons.append("cn_method_placeholder")
    if _JUNK_CN_SEE_ABSTRACT.search(t):
        reasons.append("cn_see_abstract")
    if _JUNK_CN_READER_COMMENTARY.search(t):
        reasons.append("cn_reader_commentary")
    if _JUNK_CN_PAPER_REF.search(t):
        reasons.append("cn_paper_ref")

    if paper:
        if paper.get("_title_is_filename"):
            stem = paper.get("stem") or ""
            if any(kw in stem for kw in ("实践", "讲解", "概述", "公开课", "课件", "教程", "作业", "仪式", "配置", "合辑")):
                reasons.append("filename_course_stem")

    return reasons


def is_junk_title(title: str | None, paper: dict | None = None) -> bool:
    """标题是否为误解析的摘要/水印/课件大纲等。"""
    return bool(junk_title_reasons(title, paper))


def title_from_stem(stem: str) -> str | None:
    """从文件名 stem 生成可读标题（去掉 arXiv 编号前缀）。"""
    if not stem:
        return None
    s = re.sub(r"^\d{4}\.\d{4,5}(?:v\d+)?[_\-]*", "", stem)
    s = re.sub(r"[_\-]+", " ", s).strip()
    if len(s) >= 3 and not re.match(r"^[\d\s.\-]+$", s):
        return s
    return None


def should_exclude(paper: dict, pdf_path: Path | None = None) -> tuple[bool, str]:
    """
    判断是否应从论文库排除。
    返回 (exclude, reason)。
    """
    rel = (paper.get("rel_path") or "").replace("\\", "/")
    if not rel and pdf_path:
        rel = str(pdf_path)
    rel_lower = rel.lower()
    stem = paper.get("stem") or (pdf_path.stem if pdf_path else "")
    title = paper.get("title") or stem
    abstract = paper.get("abstract") or ""

    if paper.get("size", 1) == 0:
        return True, "empty_file"

    for part in EXCLUDED_DIR_PARTS:
        if part.lower() in rel_lower:
            return True, f"dir:{part.strip('/')}"

    for pat, reason in STEM_PATTERNS:
        if re.search(pat, stem):
            return True, reason

    for kw in CN_JUNK_KEYWORDS:
        if kw in stem or kw in title:
            return True, "course_material"

    # 重解析后仍为垃圾标题 + 无摘要 → 课件/笔记
    if is_junk_title(title, paper) and not abstract:
        if CN_NO_ABS_PATTERN.search(stem) or CN_NO_ABS_PATTERN.search(title):
            return True, "junk_title_course_notes"

    if "智东西" in stem or "智东西" in title:
        return True, "course_material"

    # BEV 课程目录下无摘要的中文/课程设置类 PDF
    if "course_slides" in rel_lower and not abstract:
        return True, "course_slides_no_abstract"

    # 明确是教程讲义：无摘要 + 全中文文件名 + 非 arXiv 文件名
    if (
        not abstract
        and CN_NO_ABS_PATTERN.search(stem)
        and not re.match(r"^\d{4}\.\d{4,5}", stem)
        and paper.get("_title_is_filename")
    ):
        # 保留看起来像正式论文中文标题的（较长且含「论文」等）— 极少
        if not re.search(r"(?i)paper|arxiv|proceedings", stem):
            if any(x in stem for x in ("实践", "讲解", "概述", "公开课", "课件", "教程", "作业", "仪式", "配置")):
                return True, "cn_tutorial_no_abstract"

    return False, ""


def fix_bogus_arxiv(paper: dict) -> None:
    """清除误解析的 arXiv ID；仅移除由该 ID 推导的错误日期。"""
    aid = paper.get("arxiv_id")
    if is_valid_arxiv_id(aid):
        dt = arxiv_id_to_pub_date(aid)
        if dt and paper.get("pub_date_source") in ("arxiv_id", None):
            paper["pub_year"], paper["pub_month"] = dt
        return

    bogus_dt: tuple[int, int] | None = None
    if aid and re.match(r"^\d{4}\.", aid):
        yy, mm = int(aid[:2]), int(aid[2:4])
        bogus_dt = (2000 + yy, mm)

    if aid:
        paper.pop("arxiv_id", None)

    src = paper.get("pub_date_source")
    py, pm = paper.get("pub_year"), paper.get("pub_month")

    if src in ("arxiv_id", "arxiv_api"):
        paper.pop("pub_year", None)
        paper.pop("pub_month", None)
        paper.pop("pub_date_source", None)
    elif src == "pdf":
        pass  # 保留 PDF 首页提取的年份
    elif bogus_dt and py == bogus_dt[0] and (pm in (None, bogus_dt[1])):
        # 无来源标记，但年份/月份与误解析 arXiv 一致 → 清除
        paper.pop("pub_year", None)
        paper.pop("pub_month", None)
        paper.pop("pub_date_source", None)

    if not is_plausible_pub_year(paper.get("pub_year")):
        paper.pop("pub_year", None)
        paper.pop("pub_month", None)
        if paper.get("pub_date_source") in ("arxiv_id", "arxiv_api", None):
            paper.pop("pub_date_source", None)


def recover_arxiv_from_stem(stem: str) -> dict:
    """从文件名恢复合法 arXiv ID（PDF 正文误匹配时）。"""
    m = re.match(r"^(\d{4}\.\d{4,5})(?:v\d+)?$", stem)
    if not m:
        return {}
    aid = m.group(1)
    dt = arxiv_id_to_pub_date(aid)
    if not dt:
        return {}
    y, mo = dt
    return {"arxiv_id": aid, "pub_year": y, "pub_month": mo, "pub_date_source": "arxiv_id"}


def recover_year_from_stem(stem: str) -> dict:
    """从文件名后缀恢复发表年份（如 DeepMimic_2018、*_CVPR_2019_paper）。"""
    m = re.search(r"(?:^|[_\-.])(20\d{2})(?:[_\-.]|$)", stem)
    if not m:
        return {}
    year = int(m.group(1))
    if not is_plausible_pub_year(year):
        return {}
    return {"pub_year": year, "pub_date_source": "filename"}
