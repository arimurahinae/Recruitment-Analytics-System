from __future__ import annotations

import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _THIS_DIR.parent


def _looks_like_django_root(p: Path) -> bool:
    return (p / "manage.py").is_file() and (p / "config" / "settings.py").is_file()


def _detect_django_root() -> Path:
    env_root = (os.environ.get("DJANGO_ROOT") or "").strip()
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.append(Path("/app"))
    candidates.append(_PROJECT_DIR / "django_recruit")
    candidates.append(Path("/django_recruit"))
    for c in candidates:
        try:
            if _looks_like_django_root(c):
                return c
        except OSError:
            continue
    return _PROJECT_DIR / "django_recruit"


_DJANGO_ROOT = _detect_django_root()
if str(_DJANGO_ROOT) not in sys.path:
    sys.path.insert(0, str(_DJANGO_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings"))

import django

django.setup()

from django.db import transaction 

from job.models import Company, Job, Recruiter  

_LIEPIN_IMG_BASE = "https://image0.liepin.com/"

_CSV_NAME = "liepin_jobs.csv"
_CSV_PATH = _THIS_DIR / _CSV_NAME

_SALARY_K_PATTERN = re.compile(
    r"(?P<low>\d+(?:\.\d+)?)\s*[-~～至]\s*(?P<high>\d+(?:\.\d+)?)\s*[kKＫ]",
    re.UNICODE,
)
_SINGLE_K_PATTERN = re.compile(r"(?P<num>\d+(?:\.\d+)?)\s*[kKＫ](?:以上|起)?", re.UNICODE)

_MAX_SALARY_K = 500


def _debug(msg: str) -> None:
    print(f"[import_data] {msg}", flush=True)


def _strip_cell(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if s.lower() in ("", "nan", "none", "null", "undefined"):
        return ""
    return s


def _parse_bool(value: Any) -> Optional[bool]:
    s = _strip_cell(value)
    if s == "":
        return None
    low = s.lower()
    if low in ("true", "1", "yes", "y"):
        return True
    if low in ("false", "0", "no", "n"):
        return False
    return None


def _parse_int(value: Any) -> Optional[int]:
    if value is None or value is False:
        return None
    if isinstance(value, bool):
        return int(value)
    s = _strip_cell(value)
    if s == "":
        return None
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return None


def _parse_json_obj(value: Any) -> Optional[Dict[str, Any]]:
    s = _strip_cell(value)
    if not s:
        return None
    try:
        data = json.loads(s)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _parse_json_any(value: Any) -> Any:
    s = _strip_cell(value)
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


def _parse_data_info(value: Any) -> Optional[Dict[str, Any]]:
    s = _strip_cell(value)
    if not s:
        return None
    try:
        decoded = unquote(s)
        data = json.loads(decoded)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _normalize_labels(value: Any) -> str:
    raw = _strip_cell(value)
    if not raw:
        return ""
    parsed = _parse_json_any(raw)
    if isinstance(parsed, list):
        parts = [str(x).strip() for x in parsed if str(x).strip()]
        return "、".join(parts)
    return raw[:20000]


def _ensure_http_url(url: str, *, max_length: int = 500) -> str:
    u = _strip_cell(url)
    if not u:
        return ""
    if not urlparse(u).scheme:
        u = f"{_LIEPIN_IMG_BASE.rstrip('/')}/{u.lstrip('/')}"
    if len(u) > max_length:
        u = u[:max_length]
    return u


def _parse_refresh_time(value: Any) -> Optional[datetime]:
    s = _strip_cell(value)
    if not s or not s.isdigit():
        return None
    if len(s) == 14:
        try:
            return datetime.strptime(s, "%Y%m%d%H%M%S")
        except ValueError:
            return None
    # 兼容 8 位日期
    if len(s) == 8:
        try:
            return datetime.strptime(s, "%Y%m%d")
        except ValueError:
            return None
    return None


def _parse_salary_k_range(salary_text: str) -> Tuple[Optional[int], Optional[int]]:
    t = _strip_cell(salary_text)
    if not t:
        return None, None
    if "面议" in t or "negotiat" in t.lower():
        return None, None
    if "元/天" in t or "元／天" in t or "/天" in t:
        return None, None
    if "元/月" in t and "k" not in t.lower() and "K" not in t:
        return None, None

    m = _SALARY_K_PATTERN.search(t)
    if m:
        low = float(m.group("low"))
        high = float(m.group("high"))
        lo, hi = int(round(low)), int(round(high))
        if lo > hi:
            lo, hi = hi, lo
        return _clip_salary_pair(lo, hi)

    m2 = _SINGLE_K_PATTERN.search(t)
    if m2:
        v = int(round(float(m2.group("num"))))
        return _clip_salary_pair(v, v)

    return None, None


def _clip_salary_pair(lo: int, hi: int) -> Tuple[Optional[int], Optional[int]]:
    if lo < 0 or hi < 0:
        return None, None
    if lo > _MAX_SALARY_K or hi > _MAX_SALARY_K:
        _debug(f"薪资异常已忽略 K 区间: min={lo}, max={hi}")
        return None, None
    return lo, hi


def _dedupe_rows(rows: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], int]:
    seen: set[str] = set()
    out: List[Dict[str, str]] = []
    dup = 0
    for row in rows:
        jid = _strip_cell(row.get("job_jobId"))
        if not jid:
            continue
        if jid in seen:
            dup += 1
            continue
        seen.add(jid)
        out.append(row)
    return out, dup


def _row_to_company_defaults(row: Dict[str, str]) -> Dict[str, Any]:
    logo = _ensure_http_url(row.get("comp_compLogo", ""))
    link = _strip_cell(row.get("comp_link", ""))
    if link and not urlparse(link).scheme:
        link = ""
    return {
        "comp_compIndustry": _strip_cell(row.get("comp_compIndustry", ""))[:255],
        "comp_compLogo": logo[:500],
        "comp_compName": _strip_cell(row.get("comp_compName", ""))[:255] or "未知公司",
        "comp_compScale": _strip_cell(row.get("comp_compScale", ""))[:100],
        "comp_compStage": _strip_cell(row.get("comp_compStage", ""))[:100],
        "comp_link": link[:500],
    }


def _row_to_recruiter_defaults(row: Dict[str, str]) -> Dict[str, Any]:
    photo = _ensure_http_url(row.get("recruiter_recruiterPhoto", ""))
    im_status = _parse_int(row.get("recruiter_imStatus"))
    in_day = _parse_int(row.get("recruiter_inDay"))
    chatted = _parse_bool(row.get("recruiter_chatted"))
    return {
        "recruiter_chatted": bool(chatted) if chatted is not None else False,
        "recruiter_imId": _strip_cell(row.get("recruiter_imId", ""))[:64],
        "recruiter_imShowText": _strip_cell(row.get("recruiter_imShowText", ""))[:255],
        "recruiter_imStatus": im_status,
        "recruiter_imUserType": _strip_cell(row.get("recruiter_imUserType", ""))[:50],
        "recruiter_inDay": in_day,
        "recruiter_recruiterName": _strip_cell(row.get("recruiter_recruiterName", ""))[:100],
        "recruiter_recruiterPhoto": photo[:500],
        "recruiter_recruiterTitle": _strip_cell(row.get("recruiter_recruiterTitle", ""))[:255],
    }


def _row_to_job_fields(
    row: Dict[str, str],
    company: Optional[Company],
    recruiter: Optional[Recruiter],
) -> Dict[str, Any]:
    salary_raw = _strip_cell(row.get("job_salary", ""))[:100]
    smin, smax = _parse_salary_k_range(salary_raw)

    data_info = _parse_data_info(row.get("dataInfo", ""))
    data_params = _parse_json_obj(row.get("dataParams", ""))
    labels = _normalize_labels(row.get("job_labels", ""))

    adv = _parse_bool(row.get("job_advViewFlag"))
    job_adv_view = 1 if adv is True else (0 if adv is False else None)

    top = _parse_bool(row.get("job_topJob"))
    job_top = bool(top) if top is not None else False

    refresh = _parse_refresh_time(row.get("job_refreshTime", ""))

    title = _strip_cell(row.get("job_title", ""))[:255] or "未命名岗位"

    job_link = _strip_cell(row.get("job_link", ""))[:500]
    pc_link = _strip_cell(row.get("job_pcOuterLink", ""))[:500]
    h5_link = _strip_cell(row.get("job_h5OuterLink", ""))[:500]

    return {
        "company": company,
        "recruiter": recruiter,
        "dataInfo": data_info,
        "dataParams": data_params,
        "job_advViewFlag": job_adv_view,
        "job_campusJobKind": _strip_cell(row.get("job_campusJobKind", ""))[:100],
        "job_dataPromId": _strip_cell(row.get("job_dataPromId", ""))[:100],
        "job_dq": _strip_cell(row.get("job_dq", ""))[:100],
        "job_g": _strip_cell(row.get("job_g", ""))[:255],
        "job_h5OuterLink": h5_link,
        "job_j": _strip_cell(row.get("job_j", "")),
        "job_jobKind": _strip_cell(row.get("job_jobKind", ""))[:100],
        "job_labels": labels,
        "job_link": job_link,
        "job_pcOuterLink": pc_link,
        "job_refreshTime": refresh,
        "job_requireEduLevel": _strip_cell(row.get("job_requireEduLevel", ""))[:100],
        "job_requireWorkYears": _strip_cell(row.get("job_requireWorkYears", ""))[:100],
        "job_salary": salary_raw,
        "salary_min": smin,
        "salary_max": smax,
        "job_title": title,
        "job_topJob": job_top,
        "query_city_code": _strip_cell(row.get("query_city_code", ""))[:32],
        "query_city_dq_code": _strip_cell(row.get("query_city_dq_code", ""))[:32],
        "query_city_name": _strip_cell(row.get("query_city_name", ""))[:100],
    }


def _load_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"未找到 CSV：{path}")
    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            if not any(_strip_cell(v) for v in row.values()):
                continue
            rows.append(row)
    _debug(f"读取 CSV 行数（含空行跳过后）：{len(rows)}")
    return rows


def import_jobs(
    csv_path: Optional[Path] = None,
    *,
    dry_run: bool = False,
) -> None:
    path = csv_path or _CSV_PATH
    rows = _load_csv_rows(path)
    rows, dup_count = _dedupe_rows(rows)
    _debug(f"按 job_jobId 去重：移除重复 {dup_count} 条，剩余 {len(rows)} 条")

    skipped = 0
    created_jobs = 0
    updated_jobs = 0
    created_companies = 0
    created_recruiters = 0

    company_cache: Dict[str, Company] = {}
    recruiter_cache: Dict[str, Recruiter] = {}

    def get_company(row: Dict[str, str]) -> Optional[Company]:
        cid = _strip_cell(row.get("comp_compId", ""))
        if not cid:
            return None
        if cid in company_cache:
            return company_cache[cid]
        defaults = _row_to_company_defaults(row)
        if dry_run:
            c = Company(comp_compId=cid, **defaults)
            company_cache[cid] = c
            return c
        obj, created = Company.objects.update_or_create(
            comp_compId=cid,
            defaults=defaults,
        )
        company_cache[cid] = obj
        nonlocal created_companies
        if created:
            created_companies += 1
        return obj

    def get_recruiter(row: Dict[str, str]) -> Optional[Recruiter]:
        rid = _strip_cell(row.get("recruiter_recruiterId", ""))
        if not rid:
            return None
        if rid in recruiter_cache:
            return recruiter_cache[rid]
        defaults = _row_to_recruiter_defaults(row)
        if dry_run:
            r = Recruiter(recruiter_recruiterId=rid, **defaults)
            recruiter_cache[rid] = r
            return r
        obj, created = Recruiter.objects.update_or_create(
            recruiter_recruiterId=rid,
            defaults=defaults,
        )
        recruiter_cache[rid] = obj
        nonlocal created_recruiters
        if created:
            created_recruiters += 1
        return obj

    def process_one(row: Dict[str, str]) -> None:
        nonlocal skipped, created_jobs, updated_jobs
        jid = _strip_cell(row.get("job_jobId", ""))
        if not jid:
            skipped += 1
            return
        company = get_company(row)
        recruiter = get_recruiter(row)
        payload = _row_to_job_fields(row, company, recruiter)
        if dry_run:
            created_jobs += 1
            return
        _obj, created = Job.objects.update_or_create(
            job_jobId=jid,
            defaults=payload,
        )
        if created:
            created_jobs += 1
        else:
            updated_jobs += 1

    if dry_run:
        for row in rows:
            process_one(row)
    else:
        with transaction.atomic():
            for row in rows:
                process_one(row)

    _debug(
        "完成。"
        f" dry_run={dry_run} | 跳过无 jobId：{skipped} | "
        f"Job 新建 {created_jobs} | Job 更新 {updated_jobs} | "
        f"Company 新建 {created_companies} | Recruiter 新建 {created_recruiters}"
    )


def main(argv: Optional[List[str]] = None) -> None:
    argv = argv or sys.argv[1:]
    dry = "--dry-run" in argv
    csv_override = None
    for a in argv:
        if a.startswith("--csv="):
            csv_override = Path(a.split("=", 1)[1].strip())
    import_jobs(csv_override, dry_run=dry)


if __name__ == "__main__":
    main()
