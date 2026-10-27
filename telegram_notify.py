"""트렌드 발굴 결과를 텔레그램으로 발송."""
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
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        resp = json.loads(r.read())
    if not resp.get("ok"):
        raise RuntimeError(f"Telegram error: {resp}")


_CAT_ICON = {
    "라이프스타일": "🛋",
    "패션": "👗",
    "음식": "🍽",
    "테크": "💻",
    "문화": "🎭",
    "기타": "📌",
}


def build_message(
    trends: list[dict],
    all_entries: list[dict],
    today: str,
    site_url: str,
) -> str:
    lines: list[str] = []
    lines.append(f"<b>트렌드 리포트 · {today}</b>")
    lines.append(f"기사 {len(all_entries)}건 분석\n")

    ai_trends = [t for t in trends if t.get("evidence")]
    fallback   = [t for t in trends if not t.get("evidence")]

    if ai_trends:
        lines.append("<b>오늘의 트렌드 TOP</b>")
        for i, t in enumerate(ai_trends[:10], 1):
            cat  = t.get("category", "기타")
            icon = _CAT_ICON.get(cat, "📌")
            name = t.get("name", "")
            desc = t.get("desc", "")
            evs  = t.get("evidence", [])
            lines.append(f"{i}. {icon} <b>{name}</b> — {desc}")
            for ev in evs[:1]:
                lines.append(f"   · {ev[:50]}")
    elif fallback:
        lines.append("<b>자주 언급된 키워드</b>")
        lines.append("<code>")
        for t in fallback[:10]:
            lines.append(f"• {t['name']:<8} {t.get('desc','')}")
        lines.append("</code>")
        lines.append("\n<i>* API 키 설정 시 트렌드 이름으로 발굴됩니다</i>")

    lines.append("")
    lines.append("<b>주목 기사</b>")
    for e in all_entries[:3]:
        title = (e.get("title") or "")[:50]
        src   = e.get("source", "")
        lines.append(f"· [{src}] {title}")

    lines.append("")
    lines.append(f'<a href="{site_url}">전체 리포트 보기</a>')
    return "\n".join(lines)


def main() -> None:
    token    = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id  = os.environ.get("TELEGRAM_CHAT_ID", "")
    site_url = os.environ.get("SITE_URL", "https://trend-bot-ecru.vercel.app")

    if not token or not chat_id:
        print("[telegram] 환경변수 없음 — 건너뜀")
        return

    import config
    from sources import rss_feeds, naver_news, google_trends
    from pipeline import dedupe, discover
    from datetime import date

    today = date.today().isoformat()

    rss_entries   = rss_feeds.fetch_recent_entries(config.RSS_FEEDS, 48)
    rss_entries   = dedupe.dedupe_entries(rss_entries)
    naver_entries = naver_news.fetch_trend_articles(config.NAVER_DISCOVERY_QUERIES, config.NAVER_DISCOVERY_DISPLAY)
    rising_map    = google_trends.fetch_rising_queries(config.GOOGLE_TREND_SEEDS)
    all_entries   = dedupe.dedupe_entries(rss_entries + naver_entries)
    trends        = discover.discover(all_entries, rising_map, config.DEFAULT_AI_MODEL)

    msg = build_message(trends, all_entries, today, site_url)
    send(token, chat_id, msg)
    print(f"[telegram] 발송 완료 → {chat_id}")


if __name__ == "__main__":
    main()
