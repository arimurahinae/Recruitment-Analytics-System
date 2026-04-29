import csv
import json
import random
import time
from typing import Any, Dict, List, Optional

import requests


HOT_CITIES = [
    {"code": "010", "name": "北京"},
    {"code": "020", "name": "上海"},
    {"code": "030", "name": "天津"},
    {"code": "040", "name": "重庆"},
    {"code": "050020", "name": "广州"},
    {"code": "050090", "name": "深圳"},
    {"code": "060080", "name": "苏州"},
    {"code": "060020", "name": "南京"},
    {"code": "070020", "name": "杭州"},
    {"code": "210040", "name": "大连"},
    {"code": "280020", "name": "成都"},
    {"code": "170020", "name": "武汉"},
    {"code": "270020", "name": "西安"},
]

CITY_CODE = "030"
CITY_DQ_CODE = "030" 
PAGE_SIZE = 40
OUTPUT_CSV = "liepin_jobs.csv"

MAX_PAGES: Optional[int] = None

FALLBACK_MAX_PAGES = 50

SLEEP_BASE_SECONDS = 1.2   
SLEEP_JITTER_SECONDS = 0.8  
SLEEP_BETWEEN_CITIES_SECONDS = 2.0  

MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 2.0 

headers = {
    "cookies": '''XSRF-TOKEN=95B7WW33RFOYUpddd4uotQ; __gc_id=d3eccfc8dd14450cabf112647e262439; _ga=GA1.1.1762655016.1774252534; __uuid=1774252535080.43; __sessionId=1774252535086.29; Hm_lvt_a2647413544f5a04f00da7eee0d5e200=1774252536; HMACCOUNT=C50316BEA88F7E95; _uetsid=c0cf1ab0269911f18c1aa971292bb1cc; _uetvid=c0cf2760269911f1924217c70843c106; _uetmsclkid=_uet89c76a11247e138b378f03d022787f38; _clck=19hwt7x%5E2%5Eg4l%5E0%5E2273; _clsk=1nsuug1%5E1774257731721%5E1%5E1%5Ev.clarity.ms%2Fcollect; _ga_54YTJKWN86=GS2.1.s1774257725$o2$g1$t1774257795$j59$l0$h0; Hm_lpvt_a2647413544f5a04f00da7eee0d5e200=1774257797; __session_seq=16; __tlg_event_seq=64''',
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://www.liepin.com",
    "Pragma": "no-cache",
    "Referer": "https://www.liepin.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
    "X-Client-Type": "web",
    "X-Fscp-Bi-Stat": "",  
    "X-Fscp-Fe-Version;": "",
    "X-Fscp-Std-Info": "{\"client_id\": \"40108\"}",
    "X-Fscp-Trace-Id": "fdf3634b-b0a3-46ab-9677-35e57d4ada3f",
    "X-Fscp-Version": "1.1",
    "X-Requested-With": "XMLHttpRequest",
    "X-XSRF-TOKEN": "95B7WW33RFOYUpddd4uotQ",
    "sec-ch-ua": "\"Chromium\";v=\"146\", \"Not-A.Brand\";v=\"24\", \"Microsoft Edge\";v=\"146\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
}

API_URL = "https://api-c.liepin.com/api/com.liepin.searchfront4c.pc-search-job"

CK_ID = "fhl7bqfpaxqkzjyfey5k87urdxl9eeeb"
SK_ID = "7d1ac0kz4gzedcwlx1mvvph18mskw1wa"
FK_ID = "7d1ac0kz4gzedcwlx1mvvph18mskw1wa"


def build_bi_stat(
    city_code: str,
    dq_code: str,
    current_page: int,
    page_size: int,
) -> str:
    location = (
        "https://www.liepin.com/zhaopin/?"
        f"city={city_code}&dq={dq_code}&pubTime=&currentPage={current_page}&pageSize={page_size}"
        "&key=&suggestTag=&workYearCode=0&compId=&compName=&compTag=&industry=&salaryCode="
        "&jobKind=&compScale=&compKind=&compStage=&eduLevel=&otherCity=&"
        f"ckId={CK_ID}&scene=condition&skId={SK_ID}&fkId={FK_ID}&sfrom=search_job_pc&suggestId="
    )
    return json.dumps({"location": location}, ensure_ascii=False)


def fetch_page(current_page: int, city_code: str, dq_code: str) -> Dict[str, Any]:
    payload = {
        "data": {
            "mainSearchPcConditionForm": {
                "city": city_code,
                "dq": dq_code,
                "currentPage": current_page,
                "pageSize": PAGE_SIZE,
                "key": "",
                "suggestTag": "",
                "workYearCode": "0",
                "compId": "",
                "compName": "",
                "compTag": "",
                "industry": "",
                "salaryCode": "",
                "jobKind": "",
                "compScale": "",
                "compKind": "",
                "compStage": "",
                "eduLevel": "",
                "otherCity": "",
                "salaryLow": "",
                "salaryHigh": "",
                "hrActiveTimeCode": "",
            },
            "passThroughForm": {
                "ckId": CK_ID,
                "scene": "condition",
                "skId": SK_ID,
                "fkId": FK_ID,
                "sfrom": "search_job_pc",
            },
        }
    }

    headers_local = headers.copy()
    headers_local["X-Fscp-Bi-Stat"] = build_bi_stat(
        city_code=city_code, dq_code=dq_code, current_page=current_page, page_size=PAGE_SIZE
    )

    last_err: Optional[Exception] = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(
                API_URL,
                headers=headers_local,
                data=json.dumps(payload, separators=(",", ":")),
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_err = e
            sleep_s = RETRY_BACKOFF_BASE * (2 ** attempt) + random.random() * 0.5
            print(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}. Sleep {sleep_s:.2f}s")
            time.sleep(sleep_s)
    # 把最后一次错误抛出，方便定位是否被长期封禁
    assert last_err is not None
    raise last_err


def find_first_list_by_key(obj: Any, target_key: str) -> List[Any]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == target_key and isinstance(v, list):
                return v
        for v in obj.values():
            got = find_first_list_by_key(v, target_key)
            if got:
                return got
    elif isinstance(obj, list):
        for item in obj:
            got = find_first_list_by_key(item, target_key)
            if got:
                return got
    return []


def find_first_dict_by_key(obj: Any, target_key: str) -> Optional[Dict[str, Any]]:
    if isinstance(obj, dict):
        if target_key in obj and isinstance(obj[target_key], dict):
            return obj[target_key]
        for v in obj.values():
            got = find_first_dict_by_key(v, target_key)
            if got is not None:
                return got
    elif isinstance(obj, list):
        for item in obj:
            got = find_first_dict_by_key(item, target_key)
            if got is not None:
                return got
    return None


def flatten_job_fields(job: Dict[str, Any], sep: str = "_") -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    def rec(value: Any, prefix: str) -> None:
        if isinstance(value, dict):
            for k, v in value.items():
                next_prefix = f"{prefix}{sep}{k}" if prefix else str(k)
                rec(v, next_prefix)
            return

        if isinstance(value, list):
            out[prefix] = json.dumps(value, ensure_ascii=False)
            return

        out[prefix] = "" if value is None else str(value)

    rec(job, "")
    return out


def main() -> None:
    all_rows: List[Dict[str, Any]] = []

    cities = HOT_CITIES if HOT_CITIES else [{"code": CITY_CODE, "dq_code": CITY_DQ_CODE, "name": CITY_CODE}]

    for city in cities:
        city_code = str(city.get("code"))
        city_name = str(city.get("name", city_code))
        dq_code = str(city.get("dq_code", city_code))  # 默认 dq_code = city_code

        current_page = 0
        total_page: Optional[int] = None

        while True:
            if MAX_PAGES is not None and current_page >= MAX_PAGES:
                break
            if total_page is None and current_page >= FALLBACK_MAX_PAGES:
                break

            print(f"Fetching city={city_name} page={current_page} ...")
            data = fetch_page(
                current_page=current_page,
                city_code=city_code,
                dq_code=dq_code,
            )

            job_cards = find_first_list_by_key(data, "jobCardList")
            if not job_cards:
                print(f"No jobCardList found for city={city_name}; stop city.")
                break

            pagination = find_first_dict_by_key(data, "pagination") or {}
            if total_page is None:
                total_page = pagination.get("totalPage") or pagination.get("totalPages")

            for job in job_cards:
                if isinstance(job, dict):
                    row = flatten_job_fields(job)
                    row["query_city_code"] = city_code
                    row["query_city_dq_code"] = dq_code
                    row["query_city_name"] = city_name
                    all_rows.append(row)

            if total_page is not None and current_page >= int(total_page) - 1:
                break

            current_page += 1

            time.sleep(SLEEP_BASE_SECONDS + random.random() * SLEEP_JITTER_SECONDS)

        # 每个城市抓完后，额外等待，降低切城市造成的突刺
        time.sleep(SLEEP_BETWEEN_CITIES_SECONDS)

    if not all_rows:
        print("No rows collected; nothing to write.")
        return

    all_fields = set()
    for row in all_rows:
        all_fields.update(row.keys())

    fieldnames = sorted(all_fields)

    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in all_rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    print(f"Saved {len(all_rows)} jobs to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
