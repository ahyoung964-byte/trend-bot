"""유튜브 데이터 API v3 — 특정 키워드 급상승 영상 감지.

키워드별 최근 업로드 영상을 조회수순으로 조회해 '조회수 속도'를 낸다.
필요 키: YOUTUBE_API_KEY (Google Cloud, 기본 할당량 무료)
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import requests

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


def fetch_trending(queries: list[str], published_hours: int, max_results: int) -> dict[str, dict]:
    """{키워드: {"velocity": float, "top_title": str, "top_url": str}} 반환.

    velocity = 상위 영상의 (조회수 / 업로드 후 경과시간h). 키 없으면 빈 dict.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("[youtube] YOUTUBE_API_KEY 없음 — 급상승 감지 건너뜀")
        return {}

    published_after = (
        datetime.now(timezone.utc) - timedelta(hours=published_hours)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    out: dict[str, dict] = {}
    for q in queries:
        try:
            video_ids = _search_video_ids(q, published_after, max_results, api_key)
            if not video_ids:
                out[q] = {"velocity": 0.0, "top_title": "", "top_url": ""}
                continue
            best = _best_by_velocity(video_ids, api_key)
            out[q] = best
        except requests.RequestException as exc:
            print(f"[youtube] '{q}' 조회 실패: {exc}")
            out[q] = {"velocity": 0.0, "top_title": "", "top_url": ""}
    return out


def _search_video_ids(query: str, published_after: str, max_results: int, api_key: str) -> list[str]:
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": "viewCount",
        "publishedAfter": published_after,
        "maxResults": max_results,
        "regionCode": "KR",
        "relevanceLanguage": "ko",
        "key": api_key,
    }
    resp = requests.get(SEARCH_URL, params=params, timeout=15)
    resp.raise_for_status()
    return [item["id"]["videoId"] for item in resp.json().get("items", []) if item.get("id", {}).get("videoId")]


def _best_by_velocity(video_ids: list[str], api_key: str) -> dict:
    params = {
        "part": "snippet,statistics",
        "id": ",".join(video_ids),
        "key": api_key,
    }
    resp = requests.get(VIDEOS_URL, params=params, timeout=15)
    resp.raise_for_status()

    best = {"velocity": 0.0, "top_title": "", "top_url": ""}
    now = datetime.now(timezone.utc)
    for item in resp.json().get("items", []):
        views = int(item.get("statistics", {}).get("viewCount", 0))
        published = item["snippet"].get("publishedAt")
        try:
            pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        hours = max((now - pub_dt).total_seconds() / 3600.0, 1.0)
        velocity = views / hours
        if velocity > best["velocity"]:
            best = {
                "velocity": round(velocity, 1),
                "top_title": item["snippet"].get("title", ""),
                "top_url": f"https://youtu.be/{item['id']}",
            }
    return best
