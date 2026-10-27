"""RSS 피드 수집 — 버티컬 미디어/브랜드 블로그 신규글.

키 불필요. dry-run 에서 이 모듈만으로 파이프라인을 검증할 수 있다.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import feedparser


def fetch_recent_entries(feeds: list[dict], lookback_hours: int) -> list[dict]:
    """최근 lookback_hours 내 발행된 글 목록.

    반환: [{"source", "title", "link", "published"(ISO), "summary"}]
    published 파싱 불가 항목은 최근글로 간주해 포함한다.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    entries: list[dict] = []

    for feed in feeds:
        url = feed["url"]
        source = feed.get("source", url)
        parsed = feedparser.parse(url)
        if parsed.bozo and not parsed.entries:
            print(f"[rss] 파싱 실패/빈 피드: {source} ({url})")
            continue

        for e in parsed.entries:
            published_dt = _entry_datetime(e)
            if published_dt is not None and published_dt < cutoff:
                continue
            entries.append(
                {
                    "source": source,
                    "title": (e.get("title") or "").strip(),
                    "link": e.get("link", ""),
                    "published": published_dt.isoformat() if published_dt else "",
                    "summary": _clean(e.get("summary", "")),
                }
            )
    return entries


def _entry_datetime(entry) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        struct = entry.get(field)
        if struct:
            return datetime.fromtimestamp(time.mktime(struct), tz=timezone.utc)
    return None


def _clean(text: str, limit: int = 200) -> str:
    import re

    text = re.sub(r"<[^>]+>", "", text or "").strip()
    return text[:limit]


def count_keyword_mentions(entries: list[dict], keyword_groups: list[dict]) -> dict[str, int]:
    """그룹명/유의어가 RSS 제목·요약에 몇 번 등장했는지."""
    counts: dict[str, int] = {}
    for g in keyword_groups:
        terms = [g["name"], *g.get("keywords", [])]
        hits = 0
        for e in entries:
            blob = f"{e['title']} {e['summary']}"
            if any(t in blob for t in terms):
                hits += 1
        counts[g["name"]] = hits
    return counts
