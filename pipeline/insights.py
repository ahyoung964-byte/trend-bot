"""인사이트 추출 — 키워드별 근거 기사 매핑 + (선택) AI 해석."""
from __future__ import annotations

import os
import re


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def map_keyword_articles(
    entries: list[dict], keyword_groups: list[dict]
) -> dict[str, list[dict]]:
    """키워드별로 관련 기사를 모은다."""
    result: dict[str, list[dict]] = {}
    for g in keyword_groups:
        terms = [g["name"]] + g.get("keywords", [])
        matched = [
            e for e in entries
            if any(t in f"{e['title']} {e['summary']}" for t in terms)
        ]
        result[g["name"]] = matched
    return result


def rule_based_insights(
    rows: list[dict], kw_articles: dict[str, list[dict]]
) -> list[dict]:
    """규칙 기반 인사이트: 키워드별 헤드라인 근거 + 소스 분포."""
    insights = []
    for r in rows:
        name = r["keyword"]
        arts = kw_articles.get(name, [])
        if not arts:
            insights.append({"keyword": name, "summary": None, "headlines": [], "sources": []})
            continue

        headlines = [_clean(a["title"]) for a in arts[:3]]
        sources = list({a["source"] for a in arts})

        # 간단 규칙 요약: 몇 건, 어느 소스 주도
        lead_src = max(set(a["source"] for a in arts), key=lambda s: sum(1 for a in arts if a["source"] == s))
        summary = f"{lead_src} 등 {len(sources)}개 매체, {len(arts)}건"

        insights.append({
            "keyword": name,
            "rss_count": r["rss_mentions"],
            "score": r["score"],
            "summary": summary,
            "headlines": headlines,
            "sources": sources,
        })
    return insights


def ai_insights(
    rows: list[dict],
    kw_articles: dict[str, list[dict]],
    model: str,
) -> str | None:
    """AI 인사이트: 기사 헤드라인을 포함해 '왜 뜨는가' 해석."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None

    client = anthropic.Anthropic()
    model = os.getenv("AI_MODEL", model)

    blocks = []
    for r in sorted(rows, key=lambda x: x["rss_mentions"], reverse=True)[:6]:
        name = r["keyword"]
        arts = kw_articles.get(name, [])
        if not arts:
            continue
        headlines = " / ".join(_clean(a["title"]) for a in arts[:4])
        blocks.append(f"[{name}] RSS {r['rss_mentions']}건 — 헤드라인: {headlines}")

    if not blocks:
        return None

    prompt = (
        "아래는 오늘 수집된 트렌드 키워드별 뉴스 헤드라인입니다.\n"
        "각 키워드가 오늘 왜 뜨는지 한 줄씩, 마케터가 바로 활용할 수 있는 "
        "핵심 인사이트로 정리하세요.\n"
        "형식: 키워드 — 한 줄 해석 (구체적 근거 포함)\n"
        "해요체, 과장 금지, 이모지 금지.\n\n"
        + "\n".join(blocks)
    )

    try:
        resp = client.messages.create(
            model=model,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip() or None
    except Exception as exc:
        print(f"[ai] 인사이트 실패: {exc}")
        return None
