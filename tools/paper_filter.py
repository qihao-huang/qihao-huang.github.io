"""
paper_filter.py — 识别非论文/不合理条目（课件、slides、空文件、教程等）。
"""

from __future__ import annotations
import re
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
