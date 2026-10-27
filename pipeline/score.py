"""규칙 기반 점수 계산 — 세 소스 신호를 0~100 점수로 합산.

정규화 후 가중합. 유튜브 velocity 는 소스 내 상대 순위로 정규화한다.
"""
from __future__ import annotations


def build_scores(
    keyword_groups: list[dict],
    naver: dict[str, dict],
    youtube: dict[str, dict],
    rss_mentions: dict[str, int],
    weights: dict[str, float],
) -> list[dict]:
    """키워드별 점수 리포트(내림차순) 반환."""
    # 유튜브 velocity 정규화용 최댓값
    max_velocity = max((v.get("velocity", 0.0) for v in youtube.values()), default=0.0)
    max_mentions = max(rss_mentions.values(), default=0)

    rows: list[dict] = []
    for g in keyword_groups:
        name = g["name"]
        n = naver.get(name, {})
        y = youtube.get(name, {})

        naver_ratio = float(n.get("ratio", 0.0))          # 이미 0~100
        naver_delta = float(n.get("delta_pct", 0.0))       # %p, 음수 가능
        yt_velocity = float(y.get("velocity", 0.0))
        mentions = int(rss_mentions.get(name, 0))

        yt_norm = (yt_velocity / max_velocity * 100.0) if max_velocity else 0.0
        mention_norm = (mentions / max_mentions * 100.0) if max_mentions else 0.0
        delta_clamped = max(min(naver_delta, 100.0), -100.0)

        score = (
            naver_ratio * weights["naver_ratio"]
            + delta_clamped * weights["naver_delta"]
            + yt_norm * weights["youtube_velocity"]
            + mention_norm * weights["rss_mentions"]
        )

        rows.append(
            {
                "keyword": name,
                "score": round(score, 1),
                "naver_ratio": round(naver_ratio, 1),
                "naver_delta_pct": round(naver_delta, 1),
                "youtube_velocity": round(yt_velocity, 1),
                "youtube_top_title": y.get("top_title", ""),
                "youtube_top_url": y.get("top_url", ""),
                "rss_mentions": mentions,
            }
        )

    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows
