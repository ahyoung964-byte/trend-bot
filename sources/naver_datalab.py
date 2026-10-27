"""네이버 데이터랩 통합검색어 트렌드 API.

키워드 그룹별 최근 검색량 비율(0~100)과 전주 대비 증감을 반환.
필요 키: NAVER_CLIENT_ID, NAVER_CLIENT_SECRET (네이버 개발자센터, 무료)
"""
from __future__ import annotations

import os
from datetime import date, timedelta

import requests

ENDPOINT = "https://openapi.naver.com/v1/datalab/search"


def _credentials() -> tuple[str, str] | None:
    cid = os.getenv("NAVER_CLIENT_ID")
    secret = os.getenv("NAVER_CLIENT_SECRET")
    if not cid or not secret:
        return None
    return cid, secret


def fetch_search_trends(keyword_groups: list[dict]) -> dict[str, dict]:
    """{그룹명: {"ratio": float, "delta_pct": float}} 반환.

    ratio    = 기간 내 마지막 데이터 포인트(최근) 검색량 비율(0~100)
    delta_pct = 직전 대비 증감률(%). 데이터 부족 시 0.
    키가 없으면 빈 dict.
    """
    creds = _credentials()
    if creds is None:
        print("[naver] NAVER_CLIENT_ID/SECRET 없음 — 검색량 트렌드 건너뜀")
        return {}

    cid, secret = creds
    end = date.today()
    start = end - timedelta(days=30)
    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "timeUnit": "week",
        "keywordGroups": [
            {"groupName": g["name"], "keywords": g["keywords"]} for g in keyword_groups
        ],
    }
    headers = {
        "X-Naver-Client-Id": cid,
        "X-Naver-Client-Secret": secret,
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(ENDPOINT, json=body, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[naver] 요청 실패: {exc}")
        return {}

    out: dict[str, dict] = {}
    for series in resp.json().get("results", []):
        name = series["title"]
        points = series.get("data", [])
        if not points:
            out[name] = {"ratio": 0.0, "delta_pct": 0.0}
            continue
        latest = float(points[-1]["ratio"])
        prev = float(points[-2]["ratio"]) if len(points) >= 2 else latest
        delta = ((latest - prev) / prev * 100.0) if prev else 0.0
        out[name] = {"ratio": round(latest, 1), "delta_pct": round(delta, 1)}
    return out
