"""트렌드 수집봇 설정."""

# ── RSS 피드 ──────────────────────────────────────────────────────────
RSS_FEEDS = [
    # IT·테크
    {"source": "ZDNet Korea",   "url": "https://feeds.feedburner.com/zdkorea"},
    {"source": "IT조선",         "url": "https://it.chosun.com/rss/allArticle.xml"},
    # 문화·라이프
    {"source": "한겨레 문화",    "url": "https://www.hani.co.kr/rss/culture/"},
    {"source": "한겨레 사회",    "url": "https://www.hani.co.kr/rss/society/"},
    {"source": "오마이뉴스 문화","url": "https://rss.ohmynews.com/rss/culture.xml"},
    {"source": "시사인",         "url": "https://www.sisain.co.kr/rss/allArticle.xml"},
    {"source": "헬스조선",       "url": "https://health.chosun.com/site/data/rss/rss.xml"},
    {"source": "세계일보 라이프","url": "https://www.segye.com/Articles/RSSList/segye_culture.xml"},
]

# ── 네이버 뉴스·블로그 검색 쿼리 (트렌드 발굴용) ──────────────────────
# NAVER_CLIENT_ID/SECRET 있을 때만 동작.
NAVER_DISCOVERY_QUERIES = [
    "MZ트렌드", "힙스터", "라이프스타일 유행",
    "요즘 유행", "신조어", "트렌드 2026",
    "MZ세대 소비", "바이럴 챌린지",
]
NAVER_DISCOVERY_DISPLAY = 15  # 쿼리당 기사 수

# ── Google Trends 급상승 씨앗 단어 ────────────────────────────────────
GOOGLE_TREND_SEEDS = ["힙", "유행", "트렌드", "MZ", "라이프"]

# ── 네이버 데이터랩 키워드 (검색량 추이 비교용, 보조 지표) ────────────
KEYWORD_GROUPS = [
    {"name": "AI",    "keywords": ["인공지능", "AI", "챗GPT", "클로드"]},
    {"name": "런닝",  "keywords": ["러닝", "달리기", "마라톤", "런닝크루"]},
    {"name": "다이어트","keywords": ["다이어트", "체중감량"]},
    {"name": "힙",    "keywords": ["힙스터", "텍스트힙", "불교힙", "힙합"]},
]

YOUTUBE_QUERIES = [g["name"] for g in KEYWORD_GROUPS]

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
