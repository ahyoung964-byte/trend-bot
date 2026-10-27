"""네이버 뉴스/블로그 검색 API — 트렌드 발굴용.

DataLab 과 동일한 키 사용.
NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 필요.
"""
from __future__ import annotations

import os
import re
import urllib.request
import urllib.parse
import json


SEARCH_ENDPOINT = "https://openapi.naver.com/v1/search/news.json"
BLOG_ENDPOINT   = "https://openapi.naver.com/v1/search/blog.json"


def _creds() -> tuple[str, str] | None:
    cid    = os.getenv("NAVER_CLIENT_ID")
    secret = os.getenv("NAVER_CLIENT_SECRET")
    return (cid, secret) if (cid and secret) else None


def _clean(html: str) -> str:
    return re.sub(r"<[^>]+>", "", (html or "")).replace("&quot;", '"').replace("&amp;", "&").strip()


def _search(endpoint: str, query: str, display: int = 20) -> list[dict]:
    creds = _creds()
    if not creds:
        return []
    cid, secret = creds
    params = urllib.parse.urlencode({"query": query, "display": display, "sort": "date"})
    req = urllib.request.Request(
        f"{endpoint}?{params}",
        headers={"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": secret},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            items = json.loads(r.read()).get("items", [])
    except Exception as exc:
        print(f"[naver_news] 검색 실패 ({query}): {exc}")
        return []
    return [
        {
            "source": "네이버뉴스",
            "title": _clean(i.get("title", "")),
            "link": i.get("originallink") or i.get("link", ""),
            "published": i.get("pubDate", ""),
            "summary": _clean(i.get("description", ""))[:200],
        }
        for i in items
    ]


def fetch_trend_articles(discovery_queries: list[str], display: int = 15) -> list[dict]:
    """discovery_queries 각각을 검색해 기사 목록으로 합쳐 반환."""
    seen: set[str] = set()
    result: list[dict] = []
    for q in discovery_queries:
        for item in _search(SEARCH_ENDPOINT, q, display):
            key = item["link"] or item["title"]
            if key not in seen:
                seen.add(key)
                item["query"] = q
                result.append(item)
    print(f"[naver_news] {len(result)}건 수집 ({len(discovery_queries)}개 쿼리)")
    return result


def fetch_blog_articles(discovery_queries: list[str], display: int = 10) -> list[dict]:
    """블로그 포스트 — 커뮤니티 감성 트렌드 잡기."""
    seen: set[str] = set()
    result: list[dict] = []
    for q in discovery_queries:
        for item in _search(BLOG_ENDPOINT, q, display):
            key = item["link"] or item["title"]
            if key not in seen:
                seen.add(key)
                item["source"] = "네이버블로그"
                item["query"] = q
                result.append(item)
    print(f"[naver_blog] {len(result)}건 수집")
    return result
