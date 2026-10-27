"""트렌드 수집봇 오케스트레이터.

세 소스 순찰 → 중복제거 → 점수 계산 → (선택)AI 요약 → Notion 기록.

실행:
  python main.py            # 전체 (키 필요)
  python main.py --dry-run  # RSS만, 키 없이 파이프라인 검증 (Notion 기록 안 함)
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

# Windows 콘솔(cp949)에서도 한글/기호 출력이 깨지거나 죽지 않도록 UTF-8 강제.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

import config
from sources import naver_datalab, rss_feeds, youtube_trends
from pipeline import dedupe, score, summarize
import notion_writer


def run(dry_run: bool = False) -> None:
    today = date.today().isoformat()
    print(f"=== 트렌드 수집봇 · {today}{' · DRY-RUN' if dry_run else ''} ===\n")

    # 1. RSS (키 불필요)
    entries = rss_feeds.fetch_recent_entries(config.RSS_FEEDS, config.RSS_LOOKBACK_HOURS)
    entries = dedupe.dedupe_entries(entries)
    rss_mentions = rss_feeds.count_keyword_mentions(entries, config.KEYWORD_GROUPS)
    print(f"[rss] 신규글 {len(entries)}건 수집 (중복제거 후)")

    if dry_run:
        # 키 없이도 파이프라인이 도는지 확인. 네이버/유튜브는 빈 값으로.
        naver = {}
        youtube = {}
    else:
        # 2. 네이버 데이터랩
        naver = naver_datalab.fetch_search_trends(config.KEYWORD_GROUPS)
        print(f"[naver] 검색량 트렌드 {len(naver)}개 그룹")
        # 3. 유튜브 급상승
        youtube = youtube_trends.fetch_trending(
            config.YOUTUBE_QUERIES,
            config.YOUTUBE_PUBLISHED_HOURS,
            config.YOUTUBE_MAX_RESULTS,
        )
        print(f"[youtube] 급상승 감지 {len(youtube)}개 키워드")

    # 4. 점수
    rows = score.build_scores(
        config.KEYWORD_GROUPS, naver, youtube, rss_mentions, config.SCORE_WEIGHTS
    )

    print("\n--- 오늘의 트렌드 점수 ---")
    for r in rows:
        print(
            f"  {r['keyword']:<8} 점수 {r['score']:>6}  "
            f"검색량 {r['naver_ratio']:>5}(전주 {r['naver_delta_pct']:+}%)  "
            f"유튜브 {r['youtube_velocity']:>8}  RSS {r['rss_mentions']}"
        )

    # 5. AI 요약 (선택)
    briefing = None
    if config.AI_SUMMARY_ENABLED:
        briefing = summarize.summarize(rows, config.DEFAULT_AI_MODEL)
    if briefing:
        print("\n--- AI 브리핑 ---")
        print(briefing)

    # 6. Notion 기록
    if dry_run:
        print("\n[dry-run] Notion 기록 생략.")
    else:
        written = notion_writer.write_report(rows, today)
        print(f"\n[notion] {written}개 행 기록 완료.")

    print("\n=== 완료 ===")


def main() -> None:
    parser = argparse.ArgumentParser(description="트렌드 수집봇")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="RSS만 수집하고 Notion 기록 없이 파이프라인만 검증",
    )
    args = parser.parse_args()
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
