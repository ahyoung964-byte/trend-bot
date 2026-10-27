"""수집 결과를 정적 HTML로 출력 — 발굴 트렌드 중심."""
from __future__ import annotations

import sys
from datetime import date

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import config
from sources import rss_feeds, naver_news, google_trends
from pipeline import dedupe, discover


_CAT_COLOR = {
    "라이프스타일": "#6366f1",
    "패션": "#ec4899",
    "음식": "#f97316",
    "테크": "#0ea5e9",
    "문화": "#8b5cf6",
    "기타": "#94a3b8",
}


def _cat_chip(cat: str) -> str:
    color = _CAT_COLOR.get(cat, "#94a3b8")
    return f'<span style="background:{color}1a;color:{color};border:1px solid {color}40;border-radius:20px;padding:2px 10px;font-size:.72rem;font-weight:600">{cat}</span>'


def _trend_cards(trends: list[dict]) -> str:
    if not trends:
        return '<p style="color:#94a3b8;padding:20px">발굴된 트렌드가 없습니다 (API 키 설정 시 활성화)</p>'
    cards = ""
    for t in trends:
        name = t.get("name", "")
        desc = t.get("desc", "")
        cat  = t.get("category", "기타")
        evs  = t.get("evidence", [])
        ev_html = "".join(f'<li>{e}</li>' for e in evs[:2])
        chip = _cat_chip(cat)
        cards += f"""
<div style="background:#fff;border-radius:14px;padding:18px 20px;box-shadow:0 1px 6px rgba(0,0,0,.07)">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
    <span style="font-size:1.15rem;font-weight:800;color:#1e293b">{name}</span>
    {chip}
  </div>
  <p style="font-size:.88rem;color:#475569;margin:0 0 10px">{desc}</p>
  {"<ul style='padding-left:16px;margin:0;font-size:.8rem;color:#94a3b8;line-height:1.8'>" + ev_html + "</ul>" if ev_html else ""}
</div>"""
    return cards


def _article_groups(entries: list[dict]) -> str:
    by_source: dict[str, list] = {}
    for e in entries:
        by_source.setdefault(e["source"], []).append(e)
    html = ""
    for src, arts in sorted(by_source.items(), key=lambda x: -len(x[1])):
        items = ""
        for e in arts[:20]:
            t = e.get("title") or ""
            link = e.get("link", "")
            pub  = (e.get("published") or "")[:10]
            items += f'<li><a href="{link}" target="_blank">{t}</a><span style="color:#cbd5e1;font-size:.75rem;margin-left:6px">{pub}</span></li>'
        html += f"""
<details open>
  <summary style="padding:12px 16px;font-weight:700;font-size:.9rem;cursor:pointer;list-style:none;display:flex;align-items:center;gap:8px;color:#334155">
    {src}
    <span style="background:#e0e7ff;color:#6366f1;border-radius:20px;padding:2px 10px;font-size:.75rem;font-weight:600;margin-left:auto">{len(arts)}건</span>
  </summary>
  <ul style="list-style:none;border-top:1px solid #f1f5f9;padding:0">{items}</ul>
</details>"""
    return html


def build_html(
    trends: list[dict],
    all_entries: list[dict],
    rss_entries: list[dict],
    today: str,
) -> str:
    trend_cards = _trend_cards(trends)
    article_groups = _article_groups(all_entries)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>트렌드 리포트 · {today}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',sans-serif;background:#f1f5f9;color:#1e293b;line-height:1.6}}
.hd{{background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;padding:28px 20px 24px}}
.hd h1{{font-size:1.3rem;font-weight:800}}
.hd .sub{{opacity:.7;font-size:.83rem;margin-top:3px}}
.stats{{display:flex;gap:14px;margin-top:16px;flex-wrap:wrap}}
.stat{{background:rgba(255,255,255,.15);border-radius:10px;padding:8px 16px;text-align:center}}
.stat .v{{font-size:1.35rem;font-weight:800}}
.stat .l{{font-size:.7rem;opacity:.8}}
.wrap{{max-width:920px;margin:0 auto;padding:20px 16px}}
.sec{{margin-bottom:28px}}
.sec-title{{font-size:.78rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.6px;margin-bottom:12px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}}
details{{background:#fff;border-radius:12px;margin-bottom:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.07)}}
details ul li{{padding:9px 16px;border-bottom:1px solid #f8fafc;font-size:.84rem}}
details ul li:last-child{{border-bottom:none}}
details ul li a{{color:#334155;text-decoration:none}}
details ul li a:hover{{color:#6366f1}}
details summary::-webkit-details-marker{{display:none}}
</style>
</head>
<body>
<div class="hd">
  <h1>트렌드 발굴 리포트</h1>
  <div class="sub">{today}</div>
  <div class="stats">
    <div class="stat"><div class="v">{len(trends)}</div><div class="l">발굴 트렌드</div></div>
    <div class="stat"><div class="v">{len(all_entries)}</div><div class="l">수집 기사</div></div>
    <div class="stat"><div class="v">{len(rss_entries)}</div><div class="l">RSS</div></div>
  </div>
</div>

<div class="wrap">
  <div class="sec">
    <div class="sec-title">오늘의 트렌드</div>
    <div class="grid">{trend_cards}</div>
  </div>

  <div class="sec">
    <div class="sec-title">수집 기사 ({len(all_entries)}건)</div>
    {article_groups}
  </div>
</div>
</body>
</html>"""


def main() -> None:
    today = date.today().isoformat()

    # 1. RSS
    rss_entries = rss_feeds.fetch_recent_entries(config.RSS_FEEDS, 48)
    rss_entries = dedupe.dedupe_entries(rss_entries)

    # 2. 네이버 뉴스 검색
    naver_entries = naver_news.fetch_trend_articles(config.NAVER_DISCOVERY_QUERIES, config.NAVER_DISCOVERY_DISPLAY)

    # 3. Google Trends 급상승어
    rising_map = google_trends.fetch_rising_queries(config.GOOGLE_TREND_SEEDS)

    # 합치기
    all_entries = dedupe.dedupe_entries(rss_entries + naver_entries)

    # 4. 트렌드 발굴
    trends = discover.discover(all_entries, rising_map, config.DEFAULT_AI_MODEL)

    html = build_html(trends, all_entries, rss_entries, today)
    out = f"report_{today}.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"저장: {out}  (트렌드 {len(trends)}개, 기사 {len(all_entries)}건)")


if __name__ == "__main__":
    main()
