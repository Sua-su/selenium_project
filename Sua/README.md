# RSS + Selenium + Trafilatura 크롤러

## 프로젝트 개요

RSS 피드를 통해 URL을 수집하고, Selenium으로 동적 웹페이지를 렌더링한 후, trafilatura로 본문을 추출하여 SQLite에 저장하는 크롤링 애플리케이션입니다.

## 주요 기능

- **RSS 파싱**: RSS 피드에서 URL 목록 수집
- **동적 렌더링**: Selenium으로 JavaScript 기반 페이지 로딩
- **본문 추출**: trafilatura로 깨끗한 텍스트 콘텐츠 추출
- **데이터 저장**: SQLite 데이터베이스에 체계적 저장
- **GUI**: 검색, 데이터 확인, 관리 기능이 있는 사용자 인터페이스

## 설치 및 실행 방법

### 1. 환경 설정 테스트

```bash
cd /Users/su/Documents/selenium_project/Sua
/Users/su/Documents/selenium_project/Sua/.venv/bin/python test_setup.py
```

### 2. 애플리케이션 실행

```bash
/Users/su/Documents/selenium_project/Sua/.venv/bin/python main.py
```

또는 가상환경 활성화 후:

```bash
source .venv/bin/activate
python main.py
```

## EXE 파일 빌드

```bash
python build.py
```

### Windows 환경에서의 문제 해결

Windows 환경에서 PyInstaller로 빌드된 exe 파일 실행 시 본문 추출이 실패하는 문제가 있을 수 있습니다. 이는 trafilatura 라이브러리의 설정 파일 누락 때문입니다.

#### 해결 방법:

1. **빌드 옵션 강화**: `build.py`에 trafilatura 관련 옵션 추가
   - `--collect-datas=trafilatura`: 설정 파일 포함
   - `--hidden-import`: 필수 모듈 명시적 포함

2. **Fallback 메커니즘**: trafilatura 실패 시 BeautifulSoup로 대체 추출
   - 한글 페이지 특화 추출 로직
   - 다양한 CSS 선택자 시도
   - 최후의 수단으로 기본 텍스트 추출

3. **의존성 추가**: `requirements.txt`에 필요한 패키지 추가
   - `beautifulsoup4>=4.12.0`: Fallback 추출기
   - `lxml>=4.9.0`: HTML 파싱 성능 향상

#### 테스트 방법:

```bash
# 1. 개발 환경 테스트
python main.py

# 2. 빌드 테스트
python build.py

# 3. exe 실행 테스트 (Windows)
cd dist/RSS_Crawler
RSS_Crawler.exe
```

#### Windows 환경 실행 가이드

1. **빌드 실행**
   ```bash
   python build.py
   ```

2. **exe 실행**
   ```bash
   cd dist/RSS_Crawler
   RSS_Crawler.exe
   ```

3. **문제 해결 방법**

   **A. trafilatura 관련 오류**
   - 증상: "trafilatura 추출 오류", "본문 추출 실패"
   - 해결: 자동으로 BeautifulSoup fallback 작동
   - 확인: "BeautifulSoup fallback 시도..." 메시지 출력

   **B. 데이터베이스/�시 경로 문제**
   - 증상: DB 파일 생성 실패, 캐시 파일 접근 오류
   - 해결: Windows 환경에서 자동으로 exe 위치에 파일 생성
   - 확인: "Windows 환경: DB 경로를..." 메시지 출력

   **C. 제목/출처 추출 문제**
   - 증상: 제목이 없거나 출처가 "domain"으로 표시
   - 해결: 사이트별 특화 처리 (한겨레 → "한겨레")
   - 확인: 정상적인 제목과 출처 출력

   **D. 일부 기사만 성공**
   - 증상: 일부는 성공, 일부는 실패
   - 원인: 사이트별 HTML 구조 차이, 네트워크 문제
   - 해결: 콘솔 로그로 원인 확인 후 재시도

4. **디버깅 팁**
   - 콘솔 창이 열리므로 상세한 로그 확인 가능
   - `--log-level=DEBUG` 옵션으로 빌드 시 상세한 정보 확인
   - 실패 시 URL과 오류 메시지 기록

5. **권장 사양**
   - Windows 10 이상
   - 4GB 이상 RAM
   - 안정적인 네트워크 연결

## 프로젝트 구조

```
Sua/
├── main.py              # GUI 애플리케이션 진입점
├── database.py          # SQLite 데이터베이스 관리
├── rss_parser.py        # RSS 피드 파싱
├── crawler.py           # Selenium + trafilatura 크롤러
├── gui.py               # tkinter GUI 인터페이스
├── test_setup.py        # 환경 설정 테스트
├── requirements.txt     # 패키지 의존성
├── build.py             # PyInstaller 빌드 스크립트
├── .venv/               # Python 가상환경
└── README.md            # 프로젝트 문서
```

## 기술 스택

- **Python 3.14** - 프로그래밍 언어
- **trafilatura** - 웹페이지 본문 추출
- **Selenium** - 동적 웹페이지 렌더링
- **feedparser** - RSS 피드 파싱
- **webdriver-manager** - ChromeDriver 자동 관리
- **SQLite** - 로컬 데이터베이스
- **tkinter** - GUI 프레임워크

## 데이터베이스 스키마

**articles** 테이블:

- `id` - 고유 ID (자동 증가)
- `url` - 기사 URL (중복 방지)
- `title` - 기사 제목
- `content` - 본문 내용
- `author` - 작성자
- `published_date` - 게시일
- `collected_date` - 수집일
- `source` - 출처
- `rss_feed` - RSS 피드 URL
- `tags` - 태그

## GUI 기능

### 1. 크롤링 탭

- RSS URL 입력 및 파싱
- 샘플 RSS 피드 불러오기 (한겨레, 중앙일보, 매일경제)
- URL 수동 추가/삭제
- 크롤링 옵션 설정 (대기 시간, 요청 간격)
- 실시간 진행 상황 및 로그 표시

### 2. 데이터 확인 탭

- 키워드 검색 기능
- 기사 목록 표시 (ID, 제목, 출처, 수집일)
- 더블클릭으로 기사 상세보기
- 통계 정보 표시

### 3. 데이터 관리 탭

- 데이터베이스 통계 조회
- 출처별 기사 수 확인
- 개별 기사 삭제
- 전체 데이터 삭제

## 개선 사항

### v1.1 업데이트

- ✅ 최신 Chrome 헤드리스 모드 (`--headless=new`) 적용
- ✅ Selenium 드라이버 초기화 안정성 향상
- ✅ 페이지 로딩 재시도 로직 추가
- ✅ GUI 스레드 안전성 개선 (tkinter `after` 사용)
- ✅ 에러 핸들링 강화
- ✅ RSS 피드 URL 업데이트 (안정적인 소스)
- ✅ 환경 설정 테스트 스크립트 추가
- ✅ Python 가상환경 자동 설정

## 문제 해결

### Chrome 드라이버 오류

```bash
# Chrome 브라우저가 설치되어 있는지 확인
# webdriver-manager가 자동으로 ChromeDriver를 설치합니다
```

### 패키지 import 오류

```bash
# 가상환경이 활성화되어 있는지 확인
source .venv/bin/activate

# 패키지 재설치
pip install -r requirements.txt
```

### GUI가 실행되지 않음

```bash
# 테스트 스크립트로 환경 확인
python test_setup.py
```

## 라이선스

MIT
