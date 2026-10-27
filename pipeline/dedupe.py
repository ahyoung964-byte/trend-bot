"""RSS 신규글 중복 제거 — 같은 링크/제목 반복 수집 방지."""
from __future__ import annotations


def dedupe_entries(entries: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for e in entries:
        key = (e.get("link") or e.get("title") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out
