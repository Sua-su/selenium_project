# RSS 뉴스 크롤러 + 로컬 LLM 요약기 (selenium_project)

한국 주요 언론사의 **RSS 피드**에서 기사 URL을 수집하고, **requests / Selenium 하이브리드 방식**으로 기사 본문을 크롤링한 뒤,
**로컬 LLM(Qwen2.5-3B-Instruct, llama.cpp)** 으로 3문장 이내 한국어 요약을 생성하여 **SQLite**에 저장하는 **데스크톱 GUI(tkinter) 애플리케이션**입니다.

외부 API 키나 서버 없이 **완전히 로컬에서 동작**하며, PyInstaller로 macOS `.app` / Windows `.exe` 단일 실행 파일로 배포할 수 있습니다.

---

## 목차

1. [주요 기능](#-주요-기능)
2. [동작 흐름](#-동작-흐름)
3. [폴더 구조](#-폴더-구조)
4. [모듈 상세 설명](#-모듈-상세-설명)
5. [지원 언론사](#-지원-언론사)
6. [기술 스택](#-기술-스택)
7. [설치 및 실행](#-설치-및-실행)
8. [실행 파일 빌드](#-실행-파일-빌드)
9. [데이터 저장 구조](#-데이터-저장-구조)
10. [GUI 사용법](#-gui-사용법)
11. [개발 이력](#-개발-이력)
12. [알려진 이슈 및 개선 과제](#-알려진-이슈-및-개선-과제)
13. [트러블슈팅](#-트러블슈팅)

---

## 주요 기능

| 기능                  | 설명                                                                                 |
| --------------------- | ------------------------------------------------------------------------------------ |
| **언론사 선택**       | 미리 검증된 10개 언론사 RSS 중 하나를 콤보박스에서 선택해 바로 등록·파싱             |
| **RSS 파싱**          | 임의의 RSS URL 입력 → 기사 URL 목록 자동 수집 (`feedparser`)                         |
| **수동 URL 관리**     | 기사 URL 직접 추가 / 선택 삭제 / 전체 삭제                                           |
| **하이브리드 크롤링** | 정적 페이지는 `requests`, 동적 페이지는 헤드리스 Chrome(Selenium)으로 자동 분기      |
| **병렬 처리**         | `ThreadPoolExecutor(max_workers=4)`로 4개 기사 동시 크롤링                           |
| **본문 추출**         | `trafilatura`로 광고·메뉴를 제거한 본문과 메타데이터(제목, 작성자, 날짜, 출처) 추출  |
| **AI 요약**           | 로컬 LLM(Qwen2.5-3B-Instruct Q4_K_M)으로 기사당 3문장 이내 요약 자동 생성            |
| **요약 재생성**       | 기사 상세 창에서 버튼 한 번으로 요약 생성/재생성                                     |
| **캐싱**              | 이미 수집한 URL은 건너뛰고, HTML은 48시간 캐시 (`cache.db`, 7일 지난 항목 자동 정리) |
| **데이터 조회**       | 제목/본문 검색, 목록(최대 1000건), 더블클릭 상세 보기                                |
| **데이터 관리**       | 통계(총 기사 수, 최근 수집일, 출처별 상위 10개), ID별 삭제, 전체 삭제                |
| **배포**              | PyInstaller로 macOS `.app` / Windows `.exe` 빌드 (모델 포함)                         |

---

## 동작 흐름

```
main.py
  └─ CrawlerGUI (gui.py)
       │
       ├─ [언론사 선택 / RSS URL 입력]
       │     └─ RSSParser.parse_feed()  ── feedparser ──▶  기사 URL 목록 (Listbox)
       │
       └─ [크롤링 시작]  ThreadPoolExecutor(max_workers=4)
             └─ URL마다 HybridCrawler(headless=True).crawl_article(url, wait_time)
                   │
                   ├─ ① @skip_if_crawled ─ cache.db(url_cache)에 성공 기록 있으면 건너뜀
                   ├─ ② CacheManager.get_cached_html() ─ 48시간 이내 HTML 캐시 확인
                   │      └─ 없으면 is_static_page(url)?
                   │            ├─ YES → get_static_html()   (requests)
                   │            └─ NO  → get_dynamic_html()  (Selenium 헤드리스 Chrome)
                   │      └─ cache_html() 로 HTML 캐시 저장
                   ├─ ③ extract_content()  ── trafilatura ──▶ 본문 + 메타데이터
                   └─ ④ summarizer.summarize(title, content) ── llama.cpp ──▶ AI 요약
             │
             └─ DatabaseManager.batch_insert_articles() ──▶ articles.db
                   └─ "데이터 확인" 탭 자동 새로고침
```

---

## 폴더 구조

저장소에는 같은 애플리케이션의 **두 가지 버전**이 있습니다.

- **`Sua/`** — ✅ **최신 버전** (로컬 LLM 요약 + 언론사 선택 기능 포함)
- **`Su/`** — 이전 버전 (LLM 요약·언론사 선택 없음, 실행 파일 경로 처리 포함)

```
selenium_project/
├── README.md                  # 이 문서
├── Sua/                       # ★ 최신 버전
│   ├── main.py                # 진입점 (tkinter 실행)
│   ├── gui.py                 # CrawlerGUI — 3개 탭 GUI
│   ├── rss_parser.py          # RSSParser, SAMPLE_RSS_FEEDS, KNOWN_RSS_FEEDS
│   ├── hybrid_crawler.py      # HybridCrawler — 실제 사용되는 크롤러
│   ├── summarizer.py          # 로컬 LLM 요약 (llama-cpp-python)
│   ├── cache_manager.py       # CacheManager, skip_if_crawled 데코레이터
│   ├── database.py            # DatabaseManager (articles.db)
│   ├── crawler.py             # (레거시) Selenium 전용 WebCrawler
│   ├── simple_crawler.py      # (레거시) requests 전용 SimpleCrawler
│   ├── test_setup.py          # 환경 점검 스크립트
│   ├── run_guide.py           # 실행 가이드 출력
│   ├── build.py               # PyInstaller 빌드 스크립트
│   ├── requirements.txt
│   ├── README.md              # 버전별 README (일부 내용 오래됨)
│   ├── BUILD_GUIDE.md         # 빌드 문제 해결 가이드
│   └── models/
│       └── qwen2.5-3b-instruct-q4_k_m.gguf   # 약 2.1GB, git 제외 (직접 다운로드)
└── Su/                        # 이전 버전
    ├── main.py, gui.py, rss_parser.py, hybrid_crawler.py,
    ├── cache_manager.py, database.py, build.py
    ├── requirements.txt
    └── 아카이브1.zip           # 소스/DB 백업 압축본
```

> `articles.db`, `cache.db`, `cache/`, `build/`, `dist/`, `*.spec`, `models/*.gguf`는 `.gitignore`로 제외됩니다.

---

## 모듈 상세 설명

### `main.py`

- `tk.Tk()` 생성 → `CrawlerGUI(root)` → `mainloop()`
- 예외 발생 시 traceback 출력 후 `sys.exit(1)`

### `gui.py` — `CrawlerGUI`

창 제목 **"RSS 기사 크롤러"**, 크기 1200×800, 3개의 탭으로 구성됩니다.

| 탭              | 주요 메서드                                                                                                                                                      | 기능                                                                                                     |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **크롤링**      | `setup_crawl_tab`, `register_selected_outlet`, `parse_rss`, `load_sample_feeds`, `add_manual_url`, `remove_selected_urls`, `clear_urls`, `start_crawling`, `log` | 언론사 선택, RSS 파싱, URL 목록 관리, 옵션(대기 시간·요청 간격), 진행률 바, 로그                         |
| **데이터 확인** | `load_articles`, `search_articles`, `show_article_detail`                                                                                                        | 기사 목록(ID/제목/출처/수집일), 검색, 상세 창(메타데이터·`[AI 요약]`·본문, **AI 요약 생성/재생성** 버튼) |
| **데이터 관리** | `update_statistics`, `delete_article`, `clear_all_data`                                                                                                          | 통계, ID별 삭제, 전체 삭제(2회 확인)                                                                     |

- 무거운 작업은 `threading`으로 백그라운드 실행하고, UI 갱신은 `root.after()`로 메인 스레드에서 처리합니다.

### `rss_parser.py` — `RSSParser`

- `parse_feed(rss_url)`: `requests`(timeout 10초, 브라우저 User-Agent)로 받아 HTTP 200 및 XML/RSS Content-Type 확인 후 `feedparser.parse`
  - 반환 필드: `url`, `title`, `author`, `published_date`, `source`, `rss_feed`, `summary`, `tags`
- `parse_multiple_feeds()`: 피드 사이 1초 대기
- 보조 메서드: `_parse_date`, `_extract_tags`, `get_feed_info`
- 상수
  - `SAMPLE_RSS_FEEDS`: 한겨레, 매일경제 ("샘플 피드 불러오기"에서 사용)
  - `KNOWN_RSS_FEEDS`: 언론사 선택용 10개 프리셋 ([지원 언론사](#-지원-언론사) 참고)

### `hybrid_crawler.py` — `HybridCrawler`

- **정적/동적 판별** `is_static_page()` — 도메인이 `static_patterns`에 매칭되면 requests 사용
  ```
  .*\.hani\.co\.kr   .*\.mk\.co\.kr      .*\.chosun\.com
  .*\.joongang\.co\.kr .*\.hankyung\.com .*\.news1\.kr
  .*\.yonhapnews\.com  .*\.yna\.co\.kr   .*news\.yna\.co\.kr
  ```
- **`init_driver()`** — Selenium Chrome 설정
  - `ChromeDriverManager().install()`로 ChromeDriver 자동 설치
  - 옵션: `--headless=new`, `--disable-gpu`, `--disable-blink-features=AutomationControlled`, Chrome 142 User-Agent, `page_load_strategy='eager'`, (Linux) `--no-sandbox`, `--disable-dev-shm-usage`
  - CDP로 User-Agent 덮어쓰기 및 `navigator.webdriver` 숨김, 페이지 로드 타임아웃 15초
  - 드라이버 초기화 실패 시 `selenium_available=False` → **requests 전용 모드로 계속 동작**
- `get_static_html()` / `get_dynamic_html()` — 각각 최대 2회 재시도. 동적 모드는 `body` 로드 및 `document.readyState == complete` 대기 후 `wait_time`초 추가 대기
- `extract_content()` — `trafilatura.extract(include_comments=False, include_tables=True, no_fallback=False)` + `extract_metadata`(title, author, date, description, sitename)
- `crawl_article()` — 본문 50자 미만이면 실패 처리. 성공 시 반환:
  `url, success, title, content, author, published_date, source(=sitename), description, summary, method("requests"|"selenium"|"cached")`
- `crawl_multiple_articles()`(순차 처리), `close()`, 컨텍스트 매니저(`__enter__`/`__exit__`) 제공

### `summarizer.py` — 로컬 LLM 요약

| 항목          | 값                                                                                                         |
| ------------- | ---------------------------------------------------------------------------------------------------------- |
| 런타임        | `llama-cpp-python` (프로세스 내 실행, 서버/포트 없음)                                                      |
| 모델          | `models/qwen2.5-3b-instruct-q4_k_m.gguf` (Qwen2.5-3B-Instruct, Q4_K_M 양자화)                              |
| 로드          | `Llama(model_path, n_ctx=4096, n_threads=CPU코어수-1, verbose=False)` — 최초 호출 시 1회 로드(지연 싱글턴) |
| 입력 제한     | 본문 최대 `MAX_CONTENT_CHARS = 4000`자                                                                     |
| 생성 파라미터 | `max_tokens=300`, `temperature=0.3`                                                                        |
| 동시성        | `threading.Lock`으로 LLM 호출 직렬화                                                                       |
| 실패 처리     | 모델 파일 없음/로드 실패 시 `_load_failed=True`로 재시도하지 않고 `None` 반환 (크롤링은 정상 진행)         |

- 주요 함수: `_get_llm()`, `is_available()`, `summarize(title, content, sentences=3)`
- 프롬프트
  - System: _"너는 뉴스 기사를 간결하고 정확하게 요약하는 어시스턴트야. 과장이나 추측 없이 기사에 있는 사실만 요약해."_
  - User: _"다음 뉴스 기사를 한국어로 {sentences}문장 이내로 요약해줘. 핵심 사실 위주로 작성하고 요약 외의 다른 말은 하지 마."_ + 제목 + 본문

### `cache_manager.py` — `CacheManager`

- `CacheManager(cache_dir="cache", db_path="cache.db")`
- 테이블: `url_cache`(URL MD5 해시, 성공 여부), `html_cache`(HTML 원문, 길이)
- 시작 시 7일 지난 캐시 자동 삭제, `get_cached_html(max_age_hours=48)`, 100자 미만 HTML은 캐시하지 않음
- `get_cache_manager()`(전역 싱글턴), `@skip_if_crawled` 데코레이터, `get_cache_stats()`, `clear_cache()`

### `database.py` — `DatabaseManager`

- `DatabaseManager(db_path="articles.db")`
- `init_database()`: 테이블 및 인덱스(`idx_url`, `idx_source`, `idx_collected_date`) 생성, `summary` 컬럼이 없으면 `ALTER TABLE`로 자동 마이그레이션
- 메서드: `insert_article`, `batch_insert_articles`(`INSERT OR IGNORE` — 중복 URL 무시), `get_all_articles`, `get_article_by_id`, `search_articles`, `get_statistics`, `update_summary`, `delete_article`, `clear_all_articles`, `get_articles_by_source`, `get_articles_by_date_range`

### 보조 / 레거시 파일

| 파일                | 설명                                                                                   |
| ------------------- | -------------------------------------------------------------------------------------- |
| `crawler.py`        | Selenium 전용 `WebCrawler` (현재 GUI에서 미사용, `test_setup.py`에서만 import)         |
| `simple_crawler.py` | requests 전용 `SimpleCrawler` (미사용)                                                 |
| `test_setup.py`     | 라이브러리 import, SQLite, RSSParser, WebCrawler 동작 확인 (llama_cpp는 확인하지 않음) |
| `run_guide.py`      | 실행 가이드 텍스트 출력                                                                |
| `build.py`          | PyInstaller 빌드 스크립트                                                              |

---

## 지원 언론사

`Sua/rss_parser.py`의 `KNOWN_RSS_FEEDS` (실제 접속 및 XML 응답 확인 후 등록된 목록)

| 언론사     | RSS URL                                                                      | 수집 방식       |
| ---------- | ---------------------------------------------------------------------------- | --------------- |
| 한겨레     | `https://www.hani.co.kr/rss/`                                                | requests (정적) |
| 매일경제   | `https://www.mk.co.kr/rss/30000001/`                                         | requests (정적) |
| 동아일보   | `https://rss.donga.com/total.xml`                                            | Selenium (동적) |
| 한국경제   | `https://www.hankyung.com/feed/all-news`                                     | requests (정적) |
| 경향신문   | `https://www.khan.co.kr/rss/rssdata/total_news.xml`                          | Selenium (동적) |
| 조선일보   | `https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml`               | requests (정적) |
| 연합뉴스   | `https://www.yna.co.kr/rss/news.xml`                                         | requests (정적) |
| SBS        | `https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER` | Selenium (동적) |
| 국민일보   | `https://www.kmib.co.kr/rss/data/kmibRssAll.xml`                             | Selenium (동적) |
| 머니투데이 | `https://rss.mt.co.kr/mt_news.xml`                                           | Selenium (동적) |

> 목록에 없는 언론사도 RSS URL을 직접 입력하거나 기사 URL을 수동으로 추가해 수집할 수 있습니다. `static_patterns`에 없는 도메인은 모두 Selenium으로 처리됩니다.

**언론사 선택 동작 방식**

1. 콤보박스(readonly)에서 언론사 선택
2. **"선택 언론사 등록"** 클릭 → `register_selected_outlet()`이 `KNOWN_RSS_FEEDS`에서 URL을 찾아 RSS URL 입력란에 채움
3. 자동으로 `parse_rss()` 실행 → 기사 URL이 목록에 추가

---

## 기술 스택

| 분류      | 사용 기술                                             |
| --------- | ----------------------------------------------------- |
| 언어      | Python 3 (개발 환경: Python 3.14)                     |
| GUI       | tkinter / ttk                                         |
| RSS       | feedparser, requests                                  |
| 크롤링    | requests, Selenium, webdriver-manager                 |
| 본문 추출 | trafilatura                                           |
| AI 요약   | llama-cpp-python + Qwen2.5-3B-Instruct (GGUF, Q4_K_M) |
| 저장소    | SQLite (sqlite3)                                      |
| 동시성    | threading, concurrent.futures                         |
| 빌드      | PyInstaller                                           |

**`Sua/requirements.txt`**

```
trafilatura>=1.6.0
selenium>=4.15.0
feedparser>=6.0.10
webdriver-manager>=4.0.1
pyinstaller>=6.0.0
requests>=2.31.0
llama-cpp-python>=0.3.0
```

**사전 요구 사항**

- **Google Chrome** 설치 (ChromeDriver는 `webdriver-manager`가 자동 다운로드 — 최초 실행 시 인터넷 필요)
- LLM 모델 파일 약 **2.1GB** 디스크 공간
- `llama-cpp-python` 설치 시 C/C++ 빌드 도구가 필요할 수 있음 (macOS: Xcode Command Line Tools)

---

## 설치 및 실행

```bash
# 1. 저장소 클론 후 최신 버전 폴더로 이동
cd selenium_project/Sua

# 2. 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 로컬 LLM 모델 다운로드 (약 2.1GB)
mkdir -p models
curl -L -o models/qwen2.5-3b-instruct-q4_k_m.gguf \
  "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"

# 5. (선택) 환경 점검
python test_setup.py

# 6. 실행
python main.py
```

> - 별도의 CLI 인자, 환경 변수, 설정 파일은 없습니다. 모든 설정은 GUI 입력 또는 코드 상수로 관리됩니다.
> - 모델 파일이 없어도 앱은 실행되며, 요약 없이 기사만 저장됩니다.
> - `articles.db`, `cache.db`, `cache/`는 **실행한 현재 디렉터리**에 생성됩니다.

---

## 실행 파일 빌드

```bash
cd Sua
python build.py
```

- 주요 PyInstaller 옵션: `--name=RSS_Crawler --windowed --clean --noconfirm`
  - `--hidden-import`: selenium, webdriver_manager, trafilatura, feedparser, requests, urllib3, certifi, llama_cpp 등
  - `--collect-all`: certifi, selenium, llama_cpp
  - `--copy-metadata`: selenium, trafilatura
  - `--add-data=models:models` → **LLM 모델이 실행 파일에 포함**됨 (결과물 약 2GB 이상)
- 결과물
  - macOS: `dist/RSS_Crawler.app`
  - Windows: `dist/RSS_Crawler/RSS_Crawler.exe`
- ⚠️ 크로스 컴파일은 불가하므로 대상 OS에서 직접 빌드해야 합니다.
- 빌드 관련 문제 해결은 [`Sua/BUILD_GUIDE.md`](Sua/BUILD_GUIDE.md)를 참고하세요.

---

## 데이터 저장 구조

### `articles.db` — `articles` 테이블

| 컬럼             | 타입                     | 설명                                        |
| ---------------- | ------------------------ | ------------------------------------------- |
| `id`             | INTEGER PK AUTOINCREMENT | 기사 ID                                     |
| `url`            | TEXT UNIQUE NOT NULL     | 기사 URL (중복 방지)                        |
| `title`          | TEXT                     | 제목                                        |
| `content`        | TEXT                     | 본문                                        |
| `author`         | TEXT                     | 작성자                                      |
| `published_date` | TEXT                     | 발행일                                      |
| `collected_date` | TEXT NOT NULL            | 수집 일시 (`%Y-%m-%d %H:%M:%S`)             |
| `source`         | TEXT                     | 출처 (trafilatura `sitename`)               |
| `rss_feed`       | TEXT                     | RSS 피드 URL (현재 GUI에서는 빈 값 저장)    |
| `tags`           | TEXT                     | 태그 (현재 GUI에서는 빈 값 저장)            |
| `created_at`     | TIMESTAMP                | 기본값 `CURRENT_TIMESTAMP`                  |
| `summary`        | TEXT                     | **AI 요약** (구버전 DB는 자동 마이그레이션) |

인덱스: `idx_url`, `idx_source`, `idx_collected_date`

### `cache.db`

| 테이블       | 컬럼                                                  | 용도                                 |
| ------------ | ----------------------------------------------------- | ------------------------------------ |
| `url_cache`  | `url_hash`(PK, MD5), `url`, `timestamp`, `success`    | 크롤링 완료 URL 기록 → 재크롤링 방지 |
| `html_cache` | `url_hash`(PK), `html`, `timestamp`, `content_length` | HTML 원문 캐시 (48시간 유효)         |

> CSV/JSON 내보내기 기능은 현재 없습니다. 필요 시 SQLite 도구(`sqlite3`, DB Browser for SQLite 등)로 직접 조회·내보내기 하세요.

---

## GUI 사용법

### 1) 크롤링 탭

1. **언론사 선택** 콤보박스에서 언론사 선택 → **"선택 언론사 등록"**
   (또는 RSS URL 직접 입력 후 **"RSS 파싱"**, 또는 **"샘플 피드 불러오기"**)
2. URL 목록 확인 — 필요 시 **URL 추가 / 선택 삭제 / 전체 삭제**
3. 옵션 설정 — **대기 시간(초)**(기본 1, Selenium 페이지 로드 후 대기), 요청 간격(초)(기본 0)
4. **"크롤링 시작"** → 진행률 바와 로그로 상태 확인
5. 완료되면 수집된 기사가 DB에 저장되고 데이터 확인 탭이 갱신됨

### 2) 데이터 확인 탭

- 검색창에 키워드 입력 → 제목/본문 LIKE 검색
- 목록 더블클릭 → 상세 창 (메타데이터, `[AI 요약]`, 본문)
- **"AI 요약 생성/재생성"** 버튼으로 요약 생성 후 DB 업데이트 (최대 1분 정도 소요 가능)

### 3) 데이터 관리 탭

- 통계: 총 기사 수, 최근 수집일, 출처별 상위 10개
- ID 입력 후 개별 삭제 / 전체 삭제 (2단계 확인)

---

## 📜 개발 이력

| 커밋      | 내용                                                                                                                                    |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `64fa08d` | **local-llm 추가로 요약 기능 추가** — `summarizer.py` 도입, `summary` 컬럼 추가 및 마이그레이션, 상세 창 AI 요약 버튼, 빌드에 모델 포함 |
| `baa4afa` | **언론사 선택 기능 추가** — `KNOWN_RSS_FEEDS` 10개 언론사 프리셋, 콤보박스 + "선택 언론사 등록" UI                                      |
| `8a0f387` | Merge pull request #2 from `Sua-su/Su`                                                                                                  |

브랜치: `main`(기본), `Su`, `2025-12-02`, `2025-12-04`

---

## ⚠️ 알려진 이슈 및 개선 과제

- **요청 간격(초) 미적용**: `start_crawling`에서 값을 읽지만 병렬 크롤링에는 사용되지 않습니다. 또한 오류 메시지는 "정수"를 요구하지만 실제로는 실수(float)로 파싱됩니다.
- **이미 크롤링된 URL이 실패로 표시**: `@skip_if_crawled`가 `{'success': False, 'error': '이미 크롤링된 URL', 'cached': True}`를 반환해 로그상 실패로 집계됩니다.
- **요약 속도**: LLM 호출이 전역 락으로 직렬화되어 있어, 4개 워커로 병렬 크롤링해도 요약 단계에서 병목이 발생합니다.
- **`rss_feed`, `tags` 미저장**: GUI 저장 경로에서 항상 빈 문자열로 저장됩니다.
- **DB 경로가 실행 위치에 의존**: `articles.db`/`cache.db`는 현재 작업 디렉터리 기준으로 생성됩니다 (구버전 `Su/`는 `sys.frozen` 처리 포함).
- **내보내기 기능 없음**: CSV/JSON export 미지원.
- **저장소 정리**: `Su/아카이브1.zip`(DB 포함)이 git에 추적되고 있으며, `Sua/README.md`·`BUILD_GUIDE.md` 일부 내용(샘플 피드, 파일 구조)이 최신 코드와 다릅니다.
- `test_setup.py`가 `llama_cpp` 설치 여부를 확인하지 않습니다.

---

## 트러블슈팅

| 증상                           | 원인 / 해결                                                                                                |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| 요약이 생성되지 않음           | `Sua/models/qwen2.5-3b-instruct-q4_k_m.gguf` 존재 여부 확인. 로드 실패 시 앱 재시작 전까지 재시도하지 않음 |
| `llama-cpp-python` 설치 실패   | C/C++ 컴파일러 설치 필요 (macOS: `xcode-select --install`)                                                 |
| Selenium/ChromeDriver 오류     | Chrome 설치 및 버전 확인, 최초 실행 시 인터넷 연결 필요. 실패 시 자동으로 requests 전용 모드로 동작        |
| 일부 기사 수집 실패            | 본문이 50자 미만이거나 동적 로딩이 느린 경우 → "대기 시간(초)" 증가                                        |
| 같은 기사가 다시 수집되지 않음 | `cache.db`의 `url_cache`에 기록됨 → `cache.db` 삭제 시 재수집 가능                                         |
| RSS 파싱 실패                  | HTTP 200 및 XML/RSS Content-Type 응답인지 확인 (일부 사이트는 차단 또는 HTML 반환)                         |
| 빌드 후 SSL/모듈 오류          | [`Sua/BUILD_GUIDE.md`](Sua/BUILD_GUIDE.md) 참고                                                            |
