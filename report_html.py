"""수집 결과를 정적 HTML로 출력."""
from __future__ import annotations

import sys
from datetime import date

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import config
from sources import rss_feeds
from pipeline import dedupe, score, insights


def _score_color(s: float) -> str:
    if s >= 10:
        return "#ef4444"
    if s >= 3:
        return "#f97316"
    if s > 0:
        return "#eab308"
    return "#94a3b8"


def _bar(val: int, max_val: int, width: int = 120) -> str:
    if max_val == 0:
        return ""
    pct = min(val / max_val * 100, 100)
    return (
        f'<div style="background:#e0e7ff;border-radius:4px;height:8px;width:{width}px;display:inline-block;vertical-align:middle">'
        f'<div style="background:#6366f1;border-radius:4px;height:8px;width:{pct*width/100:.0f}px"></div></div>'
    )


def build_html(
    rows: list[dict],
    entries: list[dict],
    insight_list: list[dict],
    ai_text: str | None,
    today: str,
) -> str:
    max_rss = max((r["rss_mentions"] for r in rows), default=1) or 1

    # ── 인사이트 섹션 ─────────────────────────────────────────────────
    insight_items = ""
    for ins in insight_list:
        if not ins.get("headlines"):
            continue
        color = _score_color(ins["score"])
        heads = "".join(f'<li>{h}</li>' for h in ins["headlines"])
        insight_items += f"""
        <div class="ins-card">
          <div class="ins-kw" style="color:{color}">{ins['keyword']}</div>
          <div class="ins-meta">{ins.get('summary','')}</div>
          <ul class="ins-heads">{heads}</ul>
        </div>"""

    ai_block = ""
    if ai_text:
        ai_block = f'<div class="ai-box"><div class="ai-label">AI 인사이트</div><pre class="ai-pre">{ai_text}</pre></div>'

    # ── 키워드 랭킹 테이블 ────────────────────────────────────────────
    rows_html = ""
    for i, r in enumerate(rows, 1):
        color = _score_color(r["score"])
        bar = _bar(r["rss_mentions"], max_rss)
        rows_html += f"""
        <tr>
          <td class="rank">#{i}</td>
          <td class="kw" style="color:{color}">{r['keyword']}</td>
          <td class="num score" style="color:{color}">{r['score']:.1f}</td>
          <td>{bar} <span class="num">{r['rss_mentions']}</span></td>
          <td class="num">{r['naver_ratio']:.1f}</td>
          <td class="num delta {'up' if r['naver_delta_pct']>0 else 'dn' if r['naver_delta_pct']<0 else ''}">{r['naver_delta_pct']:+.1f}%</td>
        </tr>"""

    # ── 기사 목록 (소스별 그룹) ───────────────────────────────────────
    by_source: dict[str, list[dict]] = {}
    for e in entries:
        by_source.setdefault(e["source"], []).append(e)

    articles_html = ""
    for src, arts in sorted(by_source.items(), key=lambda x: -len(x[1])):
        items = ""
        for e in arts[:20]:
            title = (e["title"] or "")
            link = e["link"]
            pub = e["published"][:10] if e["published"] else ""
            items += f'<li><a href="{link}" target="_blank">{title}</a><span class="adate">{pub}</span></li>\n'
        articles_html += f"""
        <details open>
          <summary class="src-summary">{src} <span class="cnt">{len(arts)}건</span></summary>
          <ul class="art-list">{items}</ul>
        </details>"""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>트렌드 리포트 · {today}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',sans-serif;background:#f1f5f9;color:#1e293b;line-height:1.6}}
.header{{background:linear-gradient(135deg,#4f46e5 0%,#7c3aed 100%);color:#fff;padding:28px 24px 24px}}
.header h1{{font-size:1.3rem;font-weight:700;letter-spacing:-.3px}}
.header .sub{{opacity:.75;font-size:.85rem;margin-top:4px}}
.stats{{display:flex;gap:20px;margin-top:16px}}
.stat{{background:rgba(255,255,255,.15);border-radius:8px;padding:8px 16px;text-align:center}}
.stat .val{{font-size:1.4rem;font-weight:700}}
.stat .lbl{{font-size:.72rem;opacity:.8}}
.container{{max-width:900px;margin:0 auto;padding:20px 16px}}
section{{margin-bottom:28px}}
h2{{font-size:1rem;font-weight:700;color:#475569;margin-bottom:12px;text-transform:uppercase;letter-spacing:.5px}}

/* 인사이트 카드 */
.ins-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}}
.ins-card{{background:#fff;border-radius:12px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.07)}}
.ins-kw{{font-size:1.05rem;font-weight:700;margin-bottom:4px}}
.ins-meta{{font-size:.78rem;color:#94a3b8;margin-bottom:8px}}
.ins-heads{{padding-left:16px;font-size:.82rem;color:#475569;line-height:1.8}}
.ins-heads li{{margin-bottom:2px}}

/* AI 인사이트 */
.ai-box{{background:#fdf4ff;border:1px solid #e9d5ff;border-radius:12px;padding:18px;margin-bottom:20px}}
.ai-label{{font-size:.78rem;font-weight:700;color:#7c3aed;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px}}
.ai-pre{{font-family:inherit;font-size:.88rem;white-space:pre-wrap;color:#3b0764;line-height:1.8}}

/* 랭킹 테이블 */
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.07)}}
th{{background:#f8fafc;color:#64748b;padding:10px 14px;font-size:.78rem;font-weight:600;text-align:left;border-bottom:1px solid #e2e8f0;text-transform:uppercase;letter-spacing:.4px}}
td{{padding:11px 14px;border-bottom:1px solid #f1f5f9;font-size:.9rem}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:#fafbff}}
.rank{{color:#94a3b8;font-size:.8rem;width:36px}}
.kw{{font-weight:700}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.score{{font-weight:700;font-size:1rem}}
.up{{color:#22c55e}}.dn{{color:#ef4444}}

/* 기사 목록 */
details{{background:#fff;border-radius:12px;margin-bottom:10px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.07)}}
.src-summary{{padding:12px 16px;font-weight:700;font-size:.9rem;cursor:pointer;display:flex;align-items:center;gap:8px;list-style:none;color:#334155}}
.src-summary::-webkit-details-marker{{display:none}}
.src-summary::before{{content:'▶';font-size:.65rem;color:#94a3b8;transition:.2s}}
details[open] .src-summary::before{{content:'▼'}}
.cnt{{background:#e0e7ff;color:#6366f1;border-radius:20px;padding:2px 10px;font-size:.75rem;font-weight:600;margin-left:auto}}
.art-list{{list-style:none;border-top:1px solid #f1f5f9}}
.art-list li{{padding:9px 16px;border-bottom:1px solid #f8fafc;font-size:.85rem;display:flex;align-items:baseline;gap:8px}}
.art-list li:last-child{{border-bottom:none}}
.art-list a{{color:#334155;text-decoration:none;flex:1}}
.art-list a:hover{{color:#6366f1}}
.adate{{flex-shrink:0;color:#cbd5e1;font-size:.75rem}}
</style>
</head>
<body>
<div class="header">
  <h1>트렌드 수집봇 리포트</h1>
  <div class="sub">{today}</div>
  <div class="stats">
    <div class="stat"><div class="val">{len(entries)}</div><div class="lbl">수집 기사</div></div>
    <div class="stat"><div class="val">{len(rows)}</div><div class="lbl">추적 키워드</div></div>
    <div class="stat"><div class="val">{sum(r['rss_mentions'] for r in rows)}</div><div class="lbl">키워드 언급</div></div>
  </div>
</div>

<div class="container">

{"<section>" + '<h2>AI 인사이트</h2>' + ai_block + "</section>" if ai_block else ""}

<section>
  <h2>키워드별 인사이트</h2>
  <div class="ins-grid">{insight_items}</div>
</section>

<section>
  <h2>키워드 랭킹</h2>
  <table>
    <tr><th>#</th><th>키워드</th><th style="text-align:right">점수</th><th>RSS 언급</th><th style="text-align:right">네이버</th><th style="text-align:right">전주대비</th></tr>
    {rows_html}
  </table>
</section>

<section>
  <h2>수집 기사 ({len(entries)}건)</h2>
  {articles_html}
</section>

</div>
</body>
</html>"""


def main() -> None:
    today = date.today().isoformat()
    entries = rss_feeds.fetch_recent_entries(config.RSS_FEEDS, config.RSS_LOOKBACK_HOURS)
    entries = dedupe.dedupe_entries(entries)
    rss_mentions = rss_feeds.count_keyword_mentions(entries, config.KEYWORD_GROUPS)
    rows = score.build_scores(config.KEYWORD_GROUPS, {}, {}, rss_mentions, config.SCORE_WEIGHTS)
    rows.sort(key=lambda r: r["score"], reverse=True)

    kw_articles = insights.map_keyword_articles(entries, config.KEYWORD_GROUPS)
    insight_list = insights.rule_based_insights(rows, kw_articles)
    ai_text = insights.ai_insights(rows, kw_articles, config.DEFAULT_AI_MODEL)

    html = build_html(rows, entries, insight_list, ai_text, today)
    out = f"report_{today}.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"저장: {out}  ({len(entries)}건, {len(rows)}개 키워드)")


if __name__ == "__main__":
    main()
