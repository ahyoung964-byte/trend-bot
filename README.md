# 트렌드 수집봇

자는 동안 AI가 매일 아침 국내 트렌드를 노션에 쌓아두는 봇.
소스 3종(네이버 데이터랩·RSS·유튜브) → 중복제거 → 규칙 기반 점수 → (선택)AI 요약 → Notion DB 기록.
GitHub Actions 로 매일 자동 실행(월 2,000분 무료 안에서 사실상 무료).

> 출처: @kelseygraphy_ 인스타 가이드(7장)를 그대로 구현.

## 지금 바로 확인 (키 없이)

```bash
pip install -r requirements.txt
python main.py --dry-run
```

RSS만 수집해 파이프라인이 도는지 보여줍니다. (네이버·유튜브·Notion은 건너뜀)

## 전체 실행에 필요한 것

| 준비물 | 용도 | 비용 | 환경변수 |
|---|---|---|---|
| 네이버 개발자 계정 | 데이터랩 API(검색량) | 무료 | `NAVER_CLIENT_ID` `NAVER_CLIENT_SECRET` |
| Google Cloud 계정 | YouTube Data API v3 | 기본 할당량 무료 | `YOUTUBE_API_KEY` |
| Notion 계정 | 결과 저장 | 무료 | `NOTION_TOKEN` `NOTION_DATABASE_ID` |
| Anthropic 키(선택) | AI 요약 | 사용량 과금 | `ANTHROPIC_API_KEY` |
| GitHub 계정 | 코드 저장·자동 실행 | 무료 | — |

### 1) 네이버 데이터랩 키
- developers.naver.com → 애플리케이션 등록 → **데이터랩(검색어트렌드)** API 추가
- Client ID / Secret 발급

### 2) 유튜브 API 키
- console.cloud.google.com → 프로젝트 생성 → **YouTube Data API v3** 사용 설정 → 사용자 인증정보 → API 키

### 3) Notion 셋업 (2단계)
1. **Integration 토큰**: notion.so/my-integrations → 새 Integration → 토큰 복사 (`NOTION_TOKEN`)
2. **데이터베이스 생성**: 아래 8개 속성으로 DB(표) 하나 생성 후, DB 우측 상단 `...` → **연결(Connections)** 에서 위 Integration 추가. DB URL의 `notion.so/xxxx?v=...` 에서 `xxxx`(32자)가 `NOTION_DATABASE_ID`.

   | 속성명 | 타입 |
   |---|---|
   | 키워드 | 제목(Title) |
   | 날짜 | 날짜(Date) |
   | 점수 | 숫자(Number) |
   | 검색량비율 | 숫자 |
   | 전주대비 | 숫자 |
   | 유튜브속도 | 숫자 |
   | RSS언급 | 숫자 |
   | 급상승영상 | URL |

   ⚠️ 속성명이 정확히 일치해야 기록됩니다(`notion_writer.py` 참조).

### 4) 로컬 전체 실행
```bash
cp .env.example .env   # 값 채우기
# (.env 로드가 필요하면: pip install python-dotenv 후 main 상단에 로드 추가)
python main.py
```

### 5) GitHub Actions 자동화
1. 이 폴더를 GitHub 저장소로 push
2. 저장소 → Settings → Secrets and variables → Actions → 위 환경변수들을 **Secrets** 로 등록(코드에 키 하드코딩 금지)
3. Actions 탭에서 `daily-trend` 활성화. 매일 KST 07시 전후 자동 실행 + 수동 실행 버튼(`Run workflow`)
4. **실패 알림**: GitHub → Settings → Notifications 에서 Actions 실패 이메일 알림 켜두기(봇이 조용히 멈추는 것 방지)

## 내 니치로 바꾸기
`config.py` 의 `KEYWORD_GROUPS` 와 `RSS_FEEDS` 만 고치면 됩니다. 점수 가중치도 `SCORE_WEIGHTS` 에서 조절.

## 구조
```
config.py                # ★키워드·피드·가중치 (여기만 고치면 됨)
sources/
  naver_datalab.py       # 검색량 트렌드
  rss_feeds.py           # 신규글 수집 (키 불필요)
  youtube_trends.py      # 급상승 영상
pipeline/
  dedupe.py  score.py  summarize.py(Claude)
notion_writer.py         # Notion DB 기록 (초당 3요청 → sleep 0.4)
main.py                  # 오케스트레이터 (--dry-run 지원)
.github/workflows/daily-trend.yml
```

## 운영 주의(가이드 6장)
- **API 호출 한도**: 키워드 수를 과하게 늘리지 말 것
- **Notion 초당 3요청**: `notion_writer.py` 가 요청 간 0.4초 대기
- **RSS 주소 변경**: 미디어사가 피드 URL을 바꾸면 수집 중단 → 월 1회 URL 점검
- **실패 알림**: Actions 실패 이메일 알림 필수
