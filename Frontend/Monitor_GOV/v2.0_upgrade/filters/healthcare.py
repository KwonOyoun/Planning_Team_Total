import re
import logging

logger = logging.getLogger(__name__)

# Defaults (can be overridden by init_config)
PRIMARY_AGENCIES = [
    "보건복지부", "질병관리청", "식품의약품안전처",
    "한국보건산업진흥원", "건강보험심사평가원",
    "국립중앙의료원", "한국보건의료연구원",
]
SECONDARY_AGENCIES = [
    "과학기술정보통신부", "산업통상자원부",
    "정보통신산업진흥원", "정보통신기획평가원",
    "한국지능정보사회진흥원", "한국연구재단",
    "한국산업기술진흥원", "한국산업기술기획평가원",
    "한국에너지기술평가원"
]

INCLUDE_PATTERNS = ["의료기기", "헬스케어"]
EXCLUDE_PATTERNS = ["토목", "건설"]

inc_regex = re.compile("|".join(INCLUDE_PATTERNS), re.IGNORECASE)
exc_regex = re.compile("|".join(EXCLUDE_PATTERNS), re.IGNORECASE)

THRESHOLD = 5

def init_config(conf: dict):
    global PRIMARY_AGENCIES, SECONDARY_AGENCIES, INCLUDE_PATTERNS, EXCLUDE_PATTERNS, THRESHOLD
    global inc_regex, exc_regex
    
    if not conf:
        return

    if "primary_agencies" in conf:
        PRIMARY_AGENCIES = conf["primary_agencies"]
    if "secondary_agencies" in conf:
        SECONDARY_AGENCIES = conf["secondary_agencies"]
    if "include_patterns" in conf:
        INCLUDE_PATTERNS = conf["include_patterns"]
    if "exclude_patterns" in conf:
        EXCLUDE_PATTERNS = conf["exclude_patterns"]
    if "threshold" in conf:
        THRESHOLD = conf["threshold"]

    # Re-compile regex
    try:
        inc_regex = re.compile("|".join(INCLUDE_PATTERNS), re.IGNORECASE)
        exc_regex = re.compile("|".join(EXCLUDE_PATTERNS), re.IGNORECASE)
    except Exception as e:
        logger.error(f"Failed to compile regex matches: {e}")

def _text(*parts):
    return " ".join([str(p) for p in parts if p]).lower()

def score_notice(meta: dict, extra_text: str = "") -> tuple[int, list[str]]:
    reasons = []
    score = 0

    # 1) Agency Scoring
    src_agencies = " ".join([meta.get("소관부처",""), meta.get("전문기관","")])
    is_primary = any(ag in src_agencies for ag in PRIMARY_AGENCIES)
    is_secondary = any(ag in src_agencies for ag in SECONDARY_AGENCIES)

    if is_primary:
        score += 3
        reasons.append("1순위 보건/의료 기관(+3)")
    elif is_secondary:
        score += 1
        reasons.append("2순위 R&D/ICT 기관(+1)")

    # 2) Keyword Matching
    title = meta.get("공고명") or meta.get("title") or ""
    hay = _text(title, extra_text)

    inc = [m.group(0) for m in inc_regex.finditer(hay)]
    exc = [m.group(0) for m in exc_regex.finditer(hay)]

    if inc:
        inc_uniq = {s.lower() for s in inc if s}
        inc_pts = min(4, len(inc_uniq))
        score += inc_pts
        reasons.append(f"헬스 키워드 {inc_uniq}(+{inc_pts})")
    
    if exc:
        exc_uniq = {s.lower() for s in exc if s}
        exc_pts = min(4, len(exc_uniq))
        score -= exc_pts
        reasons.append(f"비헬스 키워드 {exc_uniq}(-{exc_pts})")

    # 3) Context Bonus
    if re.search(r"R&D|연구개발|플랫폼|데이터|AI|인공지능", hay, re.IGNORECASE):
        score += 1
        reasons.append("디지털/R&D 맥락(+1)")

    # 4) Penalty for secondary agencies without health keywords
    if is_secondary and not inc:
        score -= 1
        reasons.append("2순위 기관인데 헬스 키워드 없음(-1)")

    return score, reasons

def is_interesting_for_association(meta: dict, extra_text: str = "", threshold: int = None) -> tuple[bool, int, list[str]]:
    if threshold is None:
        threshold = THRESHOLD
    score, reasons = score_notice(meta, extra_text)
    return (score >= threshold), score, reasons
