from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

from django.conf import settings
from django.core.cache import cache
from django.db.models import Avg, Count, IntegerField, Q, Value
from django.db.models.functions import Coalesce, TruncMonth
from django.http import HttpRequest, JsonResponse
from django.utils import timezone as dj_tz
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from user.views import _error, _ok, _parse_bearer_token, _user_from_token, json_api

from .city_province import city_to_province_map_name
from .models import Company, Job


def _require_user(request: HttpRequest):
    token = _parse_bearer_token(request)
    if not token:
        return None, _error("未登录", status=401)
    user = _user_from_token(token)
    if user is None or not user.is_active:
        return None, _error("登录已失效", status=401)
    return user, None


def _to_int(value: Any, default: int, min_value: int | None = None, max_value: int | None = None) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = default
    if min_value is not None:
        n = max(min_value, n)
    if max_value is not None:
        n = min(max_value, n)
    return n


def _job_list_cache_key(request: HttpRequest) -> str:
    items = sorted((k, v) for k, v in request.GET.items())
    joined = "&".join([f"{k}={v}" for k, v in items])
    return f"job:list:{joined}"


def _bucket_salary_min(qs):
    """按月薪 K 区间统计"""
    labels = ["0-10K", "10-20K", "20-30K", "30-50K", "50K+"]
    buckets = {k: 0 for k in labels}
    for row in qs.filter(salary_min__isnull=False).values_list("salary_min", flat=True).iterator(chunk_size=2000):
        try:
            v = int(row)
        except (TypeError, ValueError):
            continue
        if v < 10:
            buckets["0-10K"] += 1
        elif v < 20:
            buckets["10-20K"] += 1
        elif v < 30:
            buckets["20-30K"] += 1
        elif v < 50:
            buckets["30-50K"] += 1
        else:
            buckets["50K+"] += 1
    return [{"name": k, "value": v} for k, v in buckets.items()]


def _wordcloud_from_labels(qs, limit: int = 80) -> List[Dict[str, Any]]:
    counter: Counter[str] = Counter()
    for text in qs.exclude(job_labels="").values_list("job_labels", flat=True).iterator(chunk_size=500):
        if not text:
            continue
        for part in re.split(r"[、,，;\s]+", text):
            p = part.strip().strip("[]\"'")
            if len(p) >= 2 and len(p) <= 20:
                counter[p] += 1
    return [{"name": n, "value": c} for n, c in counter.most_common(limit)]


@csrf_exempt
@require_GET
@json_api
def job_list(request: HttpRequest) -> JsonResponse:
    _, err = _require_user(request)
    if err is not None:
        return err

    ttl = int(getattr(settings, "JOB_LIST_CACHE_TTL_SECONDS", 0) or 0)
    key = _job_list_cache_key(request) if ttl > 0 else ""
    if ttl > 0:
        cached = cache.get(key)
        if isinstance(cached, dict):
            return JsonResponse(cached, status=200)

    q = request.GET
    keyword = (q.get("keyword") or "").strip()
    city = (q.get("city") or "").strip()
    industry = (q.get("industry") or "").strip()
    edu = (q.get("edu") or "").strip()
    work_years = (q.get("work_years") or "").strip()
    company_scale = (q.get("company_scale") or "").strip()
    min_salary = _to_int(q.get("min_salary"), 0, min_value=0)
    max_salary = _to_int(q.get("max_salary"), 0, min_value=0)
    page = _to_int(q.get("page"), 1, min_value=1)
    page_size = _to_int(q.get("page_size"), 10, min_value=5, max_value=100)

    qs = Job.objects.select_related("company").all()

    if keyword:
        qs = qs.filter(Q(job_title__icontains=keyword) | Q(company__comp_compName__icontains=keyword))
    if city:
        qs = qs.filter(query_city_name__icontains=city)
    if industry:
        qs = qs.filter(company__comp_compIndustry__icontains=industry)
    if edu:
        qs = qs.filter(job_requireEduLevel__icontains=edu)
    if work_years:
        qs = qs.filter(job_requireWorkYears__icontains=work_years)
    if company_scale:
        qs = qs.filter(company__comp_compScale__icontains=company_scale)
    if min_salary > 0:
        qs = qs.filter(Q(salary_max__gte=min_salary) | Q(salary_min__gte=min_salary))
    if max_salary > 0:
        qs = qs.filter(Q(salary_min__lte=max_salary) | Q(salary_max__lte=max_salary))

    qs = qs.order_by("-updated_at", "-id")
    total = qs.count()
    start = (page - 1) * page_size
    end = start + page_size
    rows = []
    for j in qs[start:end]:
        co = j.company
        rows.append(
            {
                "job_jobId": j.job_jobId,
                "job_title": j.job_title or "",
                "job_salary": j.job_salary or "",
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
                "job_requireEduLevel": j.job_requireEduLevel or "",
                "job_requireWorkYears": j.job_requireWorkYears or "",
                "job_jobKind": j.job_jobKind or "",
                "query_city_name": j.query_city_name or "",
                "job_link": j.job_link or "",
                "company_name": co.comp_compName if co else "",
                "company_industry": co.comp_compIndustry if co else "",
                "company_scale": co.comp_compScale if co else "",
                "company_logo": (co.comp_compLogo or "").strip() if co else "",
                "updated_at": j.updated_at.isoformat() if j.updated_at else "",
            }
        )

    payload = {"ok": True, "items": rows, "total": total, "page": page, "page_size": page_size}
    if ttl > 0:
        cache.set(key, payload, ttl)
    return JsonResponse(payload, status=200)


@csrf_exempt
@require_GET
@json_api
def job_detail(request: HttpRequest, job_id: str) -> JsonResponse:
    """岗位详情接口"""
    _, err = _require_user(request)
    if err is not None:
        return err

    j = Job.objects.select_related("company", "recruiter").filter(job_jobId=job_id).first()
    if j is None:
        return _error("岗位不存在", status=404)

    co = j.company
    rc = j.recruiter
    return _ok(
        {
            "item": {
                "job_jobId": j.job_jobId,
                "job_title": j.job_title or "",
                "job_salary": j.job_salary or "",
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
                "job_requireEduLevel": j.job_requireEduLevel or "",
                "job_requireWorkYears": j.job_requireWorkYears or "",
                "job_jobKind": j.job_jobKind or "",
                "job_labels": j.job_labels or "",
                "job_j": j.job_j or "",
                "job_dq": j.job_dq or "",
                "query_city_name": j.query_city_name or "",
                "job_link": j.job_link or "",
                "job_pcOuterLink": j.job_pcOuterLink or "",
                "job_h5OuterLink": j.job_h5OuterLink or "",
                "job_refreshTime": j.job_refreshTime.isoformat() if j.job_refreshTime else "",
                "updated_at": j.updated_at.isoformat() if j.updated_at else "",
                "company_name": co.comp_compName if co else "",
                "company_logo": (co.comp_compLogo or "").strip() if co else "",
                "company_industry": co.comp_compIndustry if co else "",
                "company_scale": co.comp_compScale if co else "",
                "company_stage": co.comp_compStage if co else "",
                "company_link": co.comp_link if co else "",
                "recruiter_name": rc.recruiter_recruiterName if rc else "",
                "recruiter_title": rc.recruiter_recruiterTitle if rc else "",
                "recruiter_photo": rc.recruiter_recruiterPhoto if rc else "",
                "recruiter_in_day": rc.recruiter_inDay if rc else None,
            }
        }
    )


@csrf_exempt
@require_GET
@json_api
def job_dashboard_stats(request: HttpRequest) -> JsonResponse:
    _, err = _require_user(request)
    if err is not None:
        return err

    qs = Job.objects.select_related("company")
    total_jobs = qs.count()
    company_ids = qs.exclude(company_id__isnull=True).values("company_id").distinct().count()
    total_companies_db = Company.objects.count()

    salary_agg = qs.aggregate(
        avg_min=Avg("salary_min"),
        avg_max=Avg("salary_max"),
        with_salary=Count("id", filter=Q(salary_min__isnull=False)),
    )

    city_agg = list(
        qs.exclude(query_city_name="")
        .values("query_city_name")
        .annotate(value=Count("id"))
        .order_by("-value")
    )

    by_city = [{"name": r["query_city_name"], "value": r["value"]} for r in city_agg[:16]]

    prov_counter: Counter[str] = Counter()
    for r in city_agg:
        p = city_to_province_map_name(r["query_city_name"])
        if p:
            prov_counter[p] += r["value"]
    by_province = [{"name": n, "value": c} for n, c in prov_counter.most_common()]

    by_education = [
        {"name": r["job_requireEduLevel"], "value": r["value"]}
        for r in qs.exclude(job_requireEduLevel="")
        .values("job_requireEduLevel")
        .annotate(value=Count("id"))
        .order_by("-value")[:10]
    ]

    by_work_years = [
        {"name": r["job_requireWorkYears"], "value": r["value"]}
        for r in qs.exclude(job_requireWorkYears="")
        .values("job_requireWorkYears")
        .annotate(value=Count("id"))
        .order_by("-value")[:10]
    ]

    by_industry = [
        {"name": r["company__comp_compIndustry"], "value": r["value"]}
        for r in qs.exclude(company__isnull=True)
        .exclude(company__comp_compIndustry="")
        .values("company__comp_compIndustry")
        .annotate(value=Count("id"))
        .order_by("-value")[:12]
    ]

    by_month_qs = (
        qs.exclude(job_refreshTime__isnull=True)
        .annotate(m=TruncMonth("job_refreshTime"))
        .values("m")
        .annotate(value=Count("id"))
        .order_by("m")
    )
    by_month: List[Dict[str, Any]] = []
    for row in by_month_qs[:36]:
        m = row["m"]
        if isinstance(m, datetime):
            key = m.strftime("%Y-%m")
        else:
            key = str(m)[:7] if m else ""
        by_month.append({"month": key, "value": row["value"]})

    top_titles = [
        {"name": r["job_title"], "value": r["value"]}
        for r in qs.exclude(job_title="")
        .values("job_title")
        .annotate(value=Count("id"))
        .order_by("-value")[:12]
    ]

    top_companies = [
        {"name": r["company__comp_compName"] or "—", "value": r["value"]}
        for r in qs.exclude(company__isnull=True)
        .exclude(company__comp_compName="")
        .values("company__comp_compName")
        .annotate(value=Count("id"))
        .order_by("-value")[:12]
    ]

    by_dq = [
        {"name": r["job_dq"], "value": r["value"]}
        for r in qs.exclude(job_dq="")
        .values("job_dq")
        .annotate(value=Count("id"))
        .order_by("-value")[:14]
    ]

    by_job_kind = [
        {"name": r["job_jobKind"], "value": r["value"]}
        for r in qs.exclude(job_jobKind="")
        .values("job_jobKind")
        .annotate(value=Count("id"))
        .order_by("-value")[:8]
    ]

    top_job = qs.filter(job_topJob=True).count()
    salary_buckets = _bucket_salary_min(qs)
    wordcloud = _wordcloud_from_labels(qs)

    distinct_cities = qs.exclude(query_city_name="").values("query_city_name").distinct().count()

    top_salary_qs = (
        qs.annotate(
            _salary_sort=Coalesce("salary_max", "salary_min", Value(0), output_field=IntegerField()),
        )
        .filter(_salary_sort__gt=0)
        .order_by("-_salary_sort", "-salary_max", "-salary_min")[:5]
    )
    top_salary_jobs: List[Dict[str, Any]] = []
    for j in top_salary_qs:
        co = j.company
        top_salary_jobs.append(
            {
                "job_jobId": j.job_jobId,
                "job_title": j.job_title or "",
                "job_salary": j.job_salary or "",
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
                "company_name": co.comp_compName if co else "",
                "company_logo": (co.comp_compLogo or "").strip() if co else "",
                "query_city_name": j.query_city_name or "",
            }
        )

    summary = {
        "total_jobs": total_jobs,
        "companies_in_jobs": company_ids,
        "companies_total": total_companies_db,
        "avg_salary_min_k": round(salary_agg["avg_min"] or 0, 2),
        "avg_salary_max_k": round(salary_agg["avg_max"] or 0, 2),
        "jobs_with_salary": salary_agg["with_salary"] or 0,
        "top_job_count": top_job,
        "city_count": distinct_cities,
    }

    return _ok(
        {
            "summary": summary,
            "by_city": by_city,
            "by_province": by_province,
            "by_education": by_education,
            "by_work_years": by_work_years,
            "by_industry": by_industry,
            "by_month": by_month,
            "top_titles": top_titles,
            "top_companies": top_companies,
            "by_dq": by_dq,
            "by_job_kind": by_job_kind,
            "salary_buckets": salary_buckets,
            "wordcloud": wordcloud,
            "top_salary_jobs": top_salary_jobs,
            "updated_at": dj_tz.now().isoformat(),
        }
    )
