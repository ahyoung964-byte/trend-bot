"""Notion DB 자동 기록.

키워드 1개당 1행(page)을 데이터베이스에 추가한다.
필요 키: NOTION_TOKEN(Integration), NOTION_DATABASE_ID
Notion 초당 3요청 제한 → 요청 간 0.4초 대기(가이드 6장 주의사항).

DB 속성(README 참고, 정확히 일치해야 함):
  키워드(제목) · 날짜(날짜) · 점수(숫자) · 검색량비율(숫자)
  · 전주대비(숫자) · 유튜브속도(숫자) · RSS언급(숫자) · 급상승영상(URL)
"""
from __future__ import annotations

import os
import time
from datetime import date

import requests

PAGES_URL = "https://api.notion.com/v1/pages"
NOTION_VERSION = "2022-06-28"
RATE_LIMIT_SLEEP = 0.4  # 초당 3요청 제한 대응


def write_report(rows: list[dict], report_date: str | None = None) -> int:
    """rows 를 Notion DB에 기록. 기록한 행 수 반환. 키 없으면 0."""
    token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")
    if not token or not database_id:
        print("[notion] NOTION_TOKEN/NOTION_DATABASE_ID 없음 — 기록 건너뜀")
        return 0

    report_date = report_date or date.today().isoformat()
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    written = 0
    for r in rows:
        payload = {
            "parent": {"database_id": database_id},
            "properties": _properties(r, report_date),
        }
        try:
            resp = requests.post(PAGES_URL, json=payload, headers=headers, timeout=15)
            if resp.status_code >= 400:
                print(f"[notion] '{r['keyword']}' 기록 실패 {resp.status_code}: {resp.text[:200]}")
            else:
                written += 1
        except requests.RequestException as exc:
            print(f"[notion] '{r['keyword']}' 요청 오류: {exc}")
        time.sleep(RATE_LIMIT_SLEEP)

    return written


def _properties(r: dict, report_date: str) -> dict:
    props = {
        "키워드": {"title": [{"text": {"content": r["keyword"]}}]},
        "날짜": {"date": {"start": report_date}},
        "점수": {"number": r["score"]},
        "검색량비율": {"number": r["naver_ratio"]},
        "전주대비": {"number": r["naver_delta_pct"]},
        "유튜브속도": {"number": r["youtube_velocity"]},
        "RSS언급": {"number": r["rss_mentions"]},
    }
    if r.get("youtube_top_url"):
        props["급상승영상"] = {"url": r["youtube_top_url"]}
    return props
