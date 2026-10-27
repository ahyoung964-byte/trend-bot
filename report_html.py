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
from sources import rss_feeds, naver_datalab, youtube_trends
from pipeline import dedupe, score


def build_html(rows: list[dict], entries: list[dict], today: str) -> str:
    rows_html = ""
    for r in rows:
        rows_html += f"""
        <tr>
          <td class="kw">{r['keyword']}</td>
          <td class="num">{r['score']:.1f}</td>
          <td class="num">{r['naver_ratio']:.1f}</td>
          <td class="num">{r['naver_delta_pct']:+.1f}%</td>
          <td class="num">{r['youtube_velocity']:.0f}</td>
          <td class="num">{r['rss_mentions']}</td>
        </tr>"""

    articles_html = ""
    for e in entries[:50]:
        title = e['title'] or '(제목없음)'
        link = e['link']
        pub = e['published'][:10] if e['published'] else ''
        source = e['source']
        articles_html += f'<li><span class="src">[{source}]</span> <a href="{link}" target="_blank">{title}</a> <span class="date">{pub}</span></li>\n'

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>트렌드 리포트 · {today}</title>
<style>
  body{{font-family:'Apple SD Gothic Neo','Noto Sans KR',sans-serif;max-width:860px;margin:0 auto;padding:24px;color:#1a1a2e;background:#f8f9fa}}
  h1{{font-size:1.4rem;margin-bottom:4px}}
  .date{{color:#888;font-size:.85rem}}
  table{{width:100%;border-collapse:collapse;margin:20px 0;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,.08)}}
  th{{background:#4f46e5;color:#fff;padding:10px 14px;text-align:left;font-size:.85rem}}
  td{{padding:9px 14px;border-bottom:1px solid #f0f0f0;font-size:.9rem}}
  tr:last-child td{{border-bottom:none}}
  tr:hover td{{background:#f5f3ff}}
  .kw{{font-weight:600;color:#4f46e5}}
  .num{{text-align:right;font-variant-numeric:tabular-nums}}
  h2{{margin-top:32px;font-size:1.1rem}}
  ul{{padding-left:18px;line-height:1.9}}
  li{{font-size:.88rem}}
  .src{{color:#6366f1;font-weight:600}}
  a{{color:#1a1a2e;text-decoration:none}}
  a:hover{{text-decoration:underline;color:#4f46e5}}
  .date{{margin-left:6px;color:#aaa;font-size:.78rem}}
</style>
</head>
<body>
<h1>트렌드 수집봇 리포트</h1>
<p class="date">{today} · RSS {len(entries)}건 수집</p>

<h2>키워드 점수</h2>
<table>
<tr><th>키워드</th><th>점수</th><th>네이버검색량</th><th>전주대비</th><th>유튜브속도</th><th>RSS언급</th></tr>
{rows_html}
</table>

<h2>수집 기사 (최근 50건)</h2>
<ul>
{articles_html}
</ul>
</body>
</html>"""


def main() -> None:
    today = date.today().isoformat()
    entries = rss_feeds.fetch_recent_entries(config.RSS_FEEDS, config.RSS_LOOKBACK_HOURS)
    entries = dedupe.dedupe_entries(entries)
    rss_mentions = rss_feeds.count_keyword_mentions(entries, config.KEYWORD_GROUPS)
    rows = score.build_scores(config.KEYWORD_GROUPS, {}, {}, rss_mentions, config.SCORE_WEIGHTS)
    rows.sort(key=lambda r: r['score'], reverse=True)

    html = build_html(rows, entries, today)
    out = f"report_{today}.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"저장: {out}  ({len(entries)}건, {len(rows)}개 키워드)")


if __name__ == "__main__":
    main()
