"""트렌드 수집봇 설정.

여기만 고치면 됩니다. 키워드/피드를 감독님 니치로 바꾸세요.
(기본값은 가이드 예시인 한국 마케팅·트렌드 니치로 세팅해 두었습니다.)
"""

# 네이버 데이터랩으로 검색량 추이를 볼 키워드.
# 그룹당 여러 유의어를 묶으면 합산 추세로 잡힌다.
KEYWORD_GROUPS = [
    # 라이프스타일
    {"name": "다이어트", "keywords": ["다이어트", "체중감량", "살빼기"]},
    {"name": "홈트", "keywords": ["홈트", "홈트레이닝"]},
    {"name": "런닝", "keywords": ["러닝", "달리기", "마라톤"]},
    {"name": "탕후루", "keywords": ["탕후루"]},
    {"name": "제로음료", "keywords": ["제로콜라", "제로음료", "제로칼로리"]},
    # IT·테크
    {"name": "AI", "keywords": ["인공지능", "AI", "ChatGPT", "챗GPT", "클로드", "제미나이"]},
    {"name": "아이폰", "keywords": ["아이폰", "iPhone", "애플"]},
    {"name": "스타트업", "keywords": ["스타트업", "창업", "유니콘"]},
]

# 유튜브 급상승 감지에 쓸 검색 키워드(데이터랩 그룹명 재사용).
YOUTUBE_QUERIES = [g["name"] for g in KEYWORD_GROUPS]

# RSS 피드 — 버티컬 미디어/브랜드 블로그 신규글.
# ⚠️ 미디어사가 주소를 바꾸면 수집이 끊긴다. 월 1회 URL 점검 권장(가이드 6장).
RSS_FEEDS = [
    # IT·테크
    {"source": "ZDNet Korea", "url": "https://feeds.feedburner.com/zdkorea"},
    {"source": "IT조선", "url": "https://it.chosun.com/rss/allArticle.xml"},
    # 라이프스타일·트렌드
    {"source": "한겨레 문화", "url": "https://www.hani.co.kr/rss/culture/"},
    {"source": "헬스조선", "url": "https://health.chosun.com/site/data/rss/rss.xml"},
    {"source": "세계일보 라이프", "url": "https://www.segye.com/Articles/RSSList/segye_culture.xml"},
    {"source": "경향 라이프", "url": "https://www.khan.co.kr/rss/rssdata/kh_life.xml"},
]

# --- 점수 가중치 (규칙 기반) ---
# 최종점수 = 네이버추세*W_NAVER + 유튜브속도*W_YT + RSS언급*W_RSS
SCORE_WEIGHTS = {
    "naver_ratio": 0.5,      # 데이터랩 최근 검색량 비율(0~100)
    "naver_delta": 0.3,      # 전주 대비 증감(%p)
    "youtube_velocity": 0.15,  # 48h 이내 조회수 급상승
    "rss_mentions": 0.05,    # RSS 신규글 언급 수
}

# --- 수집 범위 ---
RSS_LOOKBACK_HOURS = 48       # 최근 N시간 내 신규글만
YOUTUBE_PUBLISHED_HOURS = 48  # 최근 N시간 내 업로드 영상만
YOUTUBE_MAX_RESULTS = 5       # 키워드당 상위 N개

# --- AI 요약 (선택) ---
# ANTHROPIC_API_KEY 가 있을 때만 동작. 없으면 요약 없이 리포트만 생성.
# 스킬 지침에 따라 기본 모델은 claude-opus-4-8. 비용 조절 시 AI_MODEL 환경변수로 교체.
AI_SUMMARY_ENABLED = True
DEFAULT_AI_MODEL = "claude-opus-4-8"
