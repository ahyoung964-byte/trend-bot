"""Google Trends 급상승 연관검색어 — 씨앗 단어로 rising 키워드 수집.

pytrends 사용. API 키 불필요.
"""
from __future__ import annotations


def fetch_rising_queries(seeds: list[str], geo: str = "KR") -> dict[str, list[str]]:
    """씨앗 단어별 급상승(rising) 연관검색어 반환.

    반환: {"힙": ["텍스트힙", "불교힙", ...], ...}
    실패한 씨앗은 빈 리스트.
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("[google_trends] pytrends 미설치 — 건너뜀")
        return {}

    pt = TrendReq(hl="ko", tz=540)
    result: dict[str, list[str]] = {}

    for seed in seeds:
        try:
            pt.build_payload([seed], geo=geo, timeframe="now 7-d")
            rq = pt.related_queries()
            rising_df = rq.get(seed, {}).get("rising")
            if rising_df is not None and not rising_df.empty:
                result[seed] = rising_df["query"].tolist()[:10]
            else:
                result[seed] = []
        except Exception as exc:
            print(f"[google_trends] 실패 ({seed}): {exc}")
            result[seed] = []

    total = sum(len(v) for v in result.values())
    print(f"[google_trends] 급상승 연관어 {total}개 수집")
    return result
