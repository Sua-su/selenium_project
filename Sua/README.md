# RSS + Selenium + Trafilatura 크롤러

## 프로젝트 개요

RSS 피드를 통해 URL을 수집하고, Selenium으로 동적 웹페이지를 렌더링한 후, trafilatura로 본문을 추출하여 SQLite에 저장하는 크롤링 애플리케이션입니다.

## 주요 기능

- **RSS 파싱**: RSS 피드에서 URL 목록 수집
- **동적 렌더링**: Selenium으로 JavaScript 기반 페이지 로딩
- **본문 추출**: trafilatura로 깨끗한 텍스트 콘텐츠 추출
- **AI 요약**: 크롤링 직후 로컬 LLM(llama-cpp-python)으로 기사 요약 자동 생성
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

### 3. 요약용 로컬 LLM 모델 다운로드

`summary` 기능은 Qwen2.5-3B-Instruct GGUF 모델을 로컬에서 실행합니다. 용량(약 2GB)이 커서 저장소에는 포함되어 있지 않으니 최초 1회 아래처럼 받아두세요.

```bash
mkdir -p models
curl -L -o models/qwen2.5-3b-instruct-q4_k_m.gguf \
  "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"
```

모델 파일이 없으면 크롤링/요약 자체는 실패하지 않고 `summary` 값만 비어 있게 됩니다.

## EXE 파일 빌드

```bash
python build.py
```

## 프로젝트 구조

```
Sua/
├── main.py              # GUI 애플리케이션 진입점
├── database.py          # SQLite 데이터베이스 관리
├── rss_parser.py        # RSS 피드 파싱
├── crawler.py           # Selenium + trafilatura 크롤러
├── summarizer.py        # 로컬 LLM(GGUF) 기반 기사 요약
├── models/               # 요약용 GGUF 모델 파일 (git 미포함)
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
- **llama-cpp-python** - 로컬 LLM(GGUF) 추론, 기사 요약
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
- `summary` - 로컬 LLM이 생성한 요약

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
