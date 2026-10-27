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


def _bar(val: int, max_val: int, width: int = 10) -> str:
    if max_val == 0:
        return "○" * width
    filled = round(val / max_val * width)
    return "●" * filled + "○" * (width - filled)


def build_message(
    rows: list[dict],
    entries: list[dict],
    insight_list: list[dict],
    ai_text: str | None,
    today: str,
    site_url: str,
) -> str:
    lines: list[str] = []

    lines.append(f"<b>트렌드 리포트 · {today}</b>")
    lines.append(f"기사 {len(entries)}건 수집\n")

    # ── AI 인사이트 (있으면 최우선) ──────────────────────────────────
    if ai_text:
        lines.append("<b>AI 인사이트</b>")
        for ln in ai_text.strip().splitlines()[:6]:
            lines.append(ln)
        lines.append("")

    # ── 키워드별 인사이트 (헤드라인 근거) ────────────────────────────
    active = [ins for ins in insight_list if ins.get("headlines")]
    if active:
        lines.append("<b>키워드 인사이트</b>")
        for ins in active[:5]:
            lines.append(f"<b>{ins['keyword']}</b> — {ins.get('summary','')}")
            for h in ins["headlines"][:2]:
                lines.append(f"  · {h[:50]}")
        lines.append("")

    # ── 키워드 랭킹 ──────────────────────────────────────────────────
    max_rss = max((r["rss_mentions"] for r in rows), default=1) or 1
    ranked = sorted(rows, key=lambda r: r["rss_mentions"], reverse=True)
    lines.append("<b>키워드 순위</b>")
    lines.append("<code>")
    for i, r in enumerate(ranked[:8], 1):
        bar = _bar(r["rss_mentions"], max_rss, 8)
        lines.append(f"{i}. {r['keyword']:<6} {bar} {r['rss_mentions']}건")
    lines.append("</code>")
    lines.append("")

    # ── 주목 기사 3개 ────────────────────────────────────────────────
    lines.append("<b>주목 기사</b>")
    for e in entries[:3]:
        title = (e["title"] or "")[:48]
        src = e["source"]
        lines.append(f"· [{src}] {title}")
    lines.append("")

    lines.append(f'<a href="{site_url}">전체 리포트 보기</a>')
    return "\n".join(lines)


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    site_url = os.environ.get("SITE_URL", "https://trend-bot-ecru.vercel.app")

    if not token or not chat_id:
        print("[telegram] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 없음 — 건너뜀")
        return

    import config
    from sources import rss_feeds
    from pipeline import dedupe, score, insights
    from datetime import date

    today = date.today().isoformat()
    entries = rss_feeds.fetch_recent_entries(config.RSS_FEEDS, config.RSS_LOOKBACK_HOURS)
    entries = dedupe.dedupe_entries(entries)
    rss_mentions = rss_feeds.count_keyword_mentions(entries, config.KEYWORD_GROUPS)
    rows = score.build_scores(config.KEYWORD_GROUPS, {}, {}, rss_mentions, config.SCORE_WEIGHTS)
    rows.sort(key=lambda r: r["score"], reverse=True)

    kw_articles = insights.map_keyword_articles(entries, config.KEYWORD_GROUPS)
    insight_list = insights.rule_based_insights(rows, kw_articles)
    ai_text = insights.ai_insights(rows, kw_articles, config.DEFAULT_AI_MODEL)

    msg = build_message(rows, entries, insight_list, ai_text, today, site_url)
    send(token, chat_id, msg)
    print(f"[telegram] 발송 완료 → {chat_id}")


if __name__ == "__main__":
    main()
