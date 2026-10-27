"""AI 요약 (선택) — 점수 리포트를 사람이 읽는 브리핑으로.

ANTHROPIC_API_KEY 가 있을 때만 동작. 없으면 None 반환(요약 없이 진행).
Anthropic 공식 파이썬 SDK 사용.
"""
from __future__ import annotations

import os

MAX_KEYWORDS_IN_PROMPT = 15


def summarize(rows: list[dict], model: str) -> str | None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("[ai] ANTHROPIC_API_KEY 없음 — AI 요약 건너뜀")
        return None

    try:
        import anthropic
    except ImportError:
        print("[ai] anthropic 패키지 미설치 — AI 요약 건너뜀 (pip install anthropic)")
        return None

    client = anthropic.Anthropic()
    model = os.getenv("AI_MODEL", model)

    top = rows[:MAX_KEYWORDS_IN_PROMPT]
    lines = []
    for r in top:
        line = (
            f"- {r['keyword']}: 점수 {r['score']}, "
            f"검색량 {r['naver_ratio']}(전주대비 {r['naver_delta_pct']:+}%), "
            f"유튜브속도 {r['youtube_velocity']}, RSS언급 {r['rss_mentions']}"
        )
        if r.get("youtube_top_title"):
            line += f" / 급상승영상: {r['youtube_top_title']}"
        lines.append(line)
    data_block = "\n".join(lines)

    prompt = (
        "아래는 오늘의 국내 트렌드 신호 데이터입니다. 마케터가 오전에 훑어볼 "
        "간결한 한국어 브리핑으로 정리해 주세요.\n\n"
        "요구사항:\n"
        "- 급상승 키워드 3개를 우선순위로 뽑고, 각각 왜 뜨는지 한 줄 해석\n"
        "- 그중 오늘 바로 콘텐츠로 엮을 만한 것 1개를 '추천 액션'으로\n"
        "- 과장·추측 금지. 데이터에 있는 것만. 이모지 금지, 해요체.\n\n"
        f"[데이터]\n{data_block}"
    )

    try:
        resp = client.messages.create(
            model=model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:  # noqa: BLE001 - 요약 실패는 치명적이지 않음
        print(f"[ai] 요약 실패: {exc}")
        return None

    return "".join(b.text for b in resp.content if b.type == "text").strip() or None
