"""AI 트렌드 발굴 — 수집된 기사/검색어에서 유행 이름을 뽑아낸다.

'텍스트힙', '불교힙', '런닝크루' 같은 형태의 트렌드를 자동으로 발굴.
ANTHROPIC_API_KEY 가 있을 때만 작동. 없으면 빈도 기반 키워드 반환.
"""
from __future__ import annotations

import os
import re
import json
from collections import Counter


# ── 규칙 기반 폴백 ───────────────────────────────────────────────────

_STOP = {
    "이", "가", "을", "를", "의", "은", "는", "에", "서", "로", "와", "과",
    "도", "만", "도", "에서", "으로", "하는", "있는", "없는", "위한",
    "대한", "통해", "위해", "하고", "하며", "하여", "한다", "했다",
    "된다", "된", "할", "있다", "없다", "기자", "뉴스", "기사",
}


def _extract_nouns(text: str) -> list[str]:
    words = re.findall(r"[가-힣]{2,6}", text)
    return [w for w in words if w not in _STOP]


def rule_based_keywords(all_entries: list[dict], top_n: int = 10) -> list[dict]:
    """기사 제목·요약에서 자주 등장하는 명사 추출 (AI 없을 때 폴백)."""
    counter: Counter = Counter()
    for e in all_entries:
        words = _extract_nouns(f"{e.get('title','')} {e.get('summary','')}")
        counter.update(words)
    return [
        {"name": w, "count": c, "desc": f"{c}건 언급", "evidence": []}
        for w, c in counter.most_common(top_n)
    ]


# ── AI 발굴 ──────────────────────────────────────────────────────────

def _build_prompt(
    all_entries: list[dict],
    rising_map: dict[str, list[str]],
) -> str:
    titles = [e["title"] for e in all_entries if e.get("title")][:120]
    titles_block = "\n".join(f"- {t}" for t in titles)

    rising_block = ""
    for seed, terms in rising_map.items():
        if terms:
            rising_block += f"[{seed}] " + ", ".join(terms[:8]) + "\n"

    sections = []
    if rising_block:
        sections.append(f"【Google 급상승 연관검색어】\n{rising_block}")
    if titles_block:
        sections.append(f"【오늘 수집된 기사 제목】\n{titles_block}")

    data = "\n\n".join(sections) if sections else "(데이터 없음)"

    return f"""아래는 오늘 수집한 국내 트렌드 신호 데이터입니다.

{data}

---
이 데이터를 바탕으로, 지금 한국에서 뜨고 있는 라이프스타일·문화·소비 트렌드를 발굴해 주세요.
"텍스트힙", "불교힙", "런닝크루", "그레이징룩", "고프코어" 같은 구체적인 이름으로.

조건:
- 데이터에 실제 근거가 있는 것만 (만들어내지 마세요)
- 트렌드명: 실제로 쓰이는 2~8자 명칭
- 각 트렌드마다 한 줄 설명과 근거 기사/검색어 1~2개
- 없으면 솔직히 "해당 데이터에서 뚜렷한 라이프스타일 트렌드를 찾기 어려움"이라고

다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
[
  {{
    "name": "트렌드명",
    "desc": "한줄 설명 (20자 이내)",
    "evidence": ["근거1", "근거2"],
    "category": "라이프스타일|패션|음식|테크|문화|기타"
  }}
]"""


def ai_discover(
    all_entries: list[dict],
    rising_map: dict[str, list[str]],
    model: str,
) -> list[dict] | None:
    """AI로 트렌드를 발굴. 실패 시 None."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("[discover] ANTHROPIC_API_KEY 없음 — 규칙 기반으로 대체")
        return None

    try:
        import anthropic
    except ImportError:
        return None

    client = anthropic.Anthropic()
    model = os.getenv("AI_MODEL", model)
    prompt = _build_prompt(all_entries, rising_map)

    try:
        resp = client.messages.create(
            model=model,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = "".join(b.text for b in resp.content if b.type == "text").strip()
        # JSON만 추출
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if not m:
            return None
        return json.loads(m.group())
    except Exception as exc:
        print(f"[discover] AI 발굴 실패: {exc}")
        return None


def discover(
    all_entries: list[dict],
    rising_map: dict[str, list[str]],
    model: str,
) -> list[dict]:
    """메인 진입점. AI → 규칙 기반 순서로 시도."""
    result = ai_discover(all_entries, rising_map, model)
    if result is not None:
        print(f"[discover] AI 발굴 {len(result)}개 트렌드")
        return result
    print("[discover] 규칙 기반 키워드 추출")
    return rule_based_keywords(all_entries, top_n=10)
