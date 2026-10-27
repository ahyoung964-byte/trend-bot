"""트렌드 수집 결과를 텔레그램으로 발송."""
from __future__ import annotations

import os
import sys
import urllib.request
import json

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def send(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        resp = json.loads(r.read())
    if not resp.get("ok"):
        raise RuntimeError(f"Telegram error: {resp}")


def build_message(rows: list[dict], entries: list[dict], today: str, site_url: str) -> str:
    lines = [f"<b>트렌드 리포트 · {today}</b>"]
    lines.append("")

    # 상위 10줄 요약
    top = [r for r in rows if r["score"] > 0][:5]
    zero = [r for r in rows if r["score"] == 0]

    if top:
        lines.append("<b>급상승 키워드</b>")
        for r in top:
            bar = "▪" * min(int(r["score"]), 10)
            lines.append(f"{bar} {r['keyword']}  ({r['score']:.1f}점 / RSS {r['rss_mentions']}건)")
    else:
        # RSS만 있는 경우 언급수 기준
        by_rss = sorted(rows, key=lambda r: r["rss_mentions"], reverse=True)[:5]
        lines.append("<b>RSS 언급 TOP 키워드</b>")
        for r in by_rss:
            if r["rss_mentions"] > 0:
                lines.append(f"• {r['keyword']}  — {r['rss_mentions']}건")

    lines.append("")
    lines.append(f"<b>수집 기사</b> {len(entries)}건")

    # 최신 기사 3개
    for e in entries[:3]:
        title = (e["title"] or "")[:40]
        lines.append(f"• {title}")

    lines.append("")
    lines.append(f'<a href="{site_url}">전체 리포트 보기</a>')
    return "\n".join(lines)


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    site_url = os.environ.get("SITE_URL", "https://trend-bot.vercel.app")

    if not token or not chat_id:
        print("[telegram] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 없음 — 건너뜀")
        return

    import config
    from sources import rss_feeds
    from pipeline import dedupe, score

    from datetime import date
    today = date.today().isoformat()

    entries = rss_feeds.fetch_recent_entries(config.RSS_FEEDS, config.RSS_LOOKBACK_HOURS)
    entries = dedupe.dedupe_entries(entries)
    rss_mentions = rss_feeds.count_keyword_mentions(entries, config.KEYWORD_GROUPS)
    rows = score.build_scores(config.KEYWORD_GROUPS, {}, {}, rss_mentions, config.SCORE_WEIGHTS)
    rows.sort(key=lambda r: r["score"], reverse=True)

    msg = build_message(rows, entries, today, site_url)
    send(token, chat_id, msg)
    print(f"[telegram] 발송 완료 → {chat_id}")


if __name__ == "__main__":
    main()
