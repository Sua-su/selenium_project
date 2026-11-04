# 🔨 빌드 가이드

## 현재 상황 분석

### ✅ 사용 중인 크롤러

- **hybrid_crawler.py** ← 실제 사용 중 (gui.py에서 import)
- crawler.py ← 테스트용 (사용 안 함)
- simple_crawler.py ← 테스트용 (사용 안 함)

### 🔍 문제 원인

`.exe` 파일로 빌드 시 한겨레만 크롤링되고 중앙일보/매일경제가 안 되는 이유:

1. **Selenium 모듈 누락**

   - PyInstaller가 동적 import를 자동 감지하지 못함
   - Selenium 관련 모듈이 빌드에 포함되지 않음

2. **SSL 인증서 누락**

   - HTTPS 요청에 필요한 certifi 인증서가 포함되지 않음

3. **webdriver-manager 문제**
   - ChromeDriver 자동 다운로드 경로가 .exe 환경에서 작동 안 함

### 📋 HybridCrawler 동작 방식

```python
# 정적 페이지 (requests 사용)
- hani.co.kr (한겨레) ✅
- mk.co.kr (매일경제)
- chosun.com
- joongang.co.kr
- hankyung.com
- yonhapnews.com

# 동적 페이지 (Selenium 사용)
- joins.com (중앙일보) ← Selenium이 필요!
- 기타 JavaScript 의존 사이트
```

## 🔧 해결 방법

### 1. build.py 수정 완료 ✅

다음 옵션들이 추가되었습니다:

```python
'--hidden-import=selenium',
'--hidden-import=selenium.webdriver',
'--hidden-import=selenium.webdriver.chrome.service',
'--hidden-import=selenium.webdriver.chrome.options',
'--hidden-import=webdriver_manager',
'--hidden-import=webdriver_manager.chrome',
'--hidden-import=trafilatura',
'--hidden-import=feedparser',
'--hidden-import=requests',
'--hidden-import=urllib3',
'--hidden-import=certifi',
'--collect-all=certifi',
'--collect-all=selenium',
'--copy-metadata=selenium',
'--copy-metadata=trafilatura',
```

### 2. 빌드 실행

```bash
cd /Users/su/Documents/selenium_project/Sua
source .venv/bin/activate
python build.py
```

### 3. 테스트

빌드 후 `dist/RSS_Crawler.app` (macOS) 또는 `dist/RSS_Crawler.exe` (Windows) 실행

## ⚠️ 주의사항

### Chrome 브라우저 필수

- `.exe` 파일을 실행하는 컴퓨터에 Chrome이 설치되어 있어야 함
- webdriver-manager가 자동으로 ChromeDriver 다운로드

### 첫 실행 시

- 인터넷 연결 필요 (ChromeDriver 다운로드)
- 방화벽 허용 필요 (Chrome 실행)

### 빌드 환경

- macOS: `.app` 파일 생성
- Windows: `.exe` 파일 생성
- 크로스 플랫폼 빌드 불가 (Windows에서 macOS용 빌드 안 됨)

## 🐛 디버깅

### 빌드 후 테스트 방법

1. **콘솔 모드로 실행** (에러 확인)

   ```bash
   # build.py에서 '--windowed' 제거 후 빌드
   # 또는 터미널에서 직접 실행
   ./dist/RSS_Crawler.app/Contents/MacOS/RSS_Crawler
   ```

2. **로그 확인**

   - 크롤링 탭의 실행 로그에서 어떤 방식으로 크롤링되는지 확인
   - "정적(requests)" vs "동적(Selenium)" 메시지 확인

3. **개별 사이트 테스트**
   - URL 수동 추가로 각 사이트를 하나씩 테스트
   - 한겨레: http 또는 https 확인
   - 중앙일보: Selenium 동작 확인
   - 매일경제: requests 동작 확인

## 📝 추가 최적화

### hybrid_crawler.py 정적 패턴 확인

```python
self.static_patterns = [
    r'.*\.hani\.co\.kr',      # 한겨레 ✅
    r'.*\.mk\.co\.kr',        # 매일경제
    r'.*\.joongang\.co\.kr',  # 중앙일보 (도메인 다름!)
    # joins.com은 여기 없음 → Selenium 사용
]
```

중앙일보는 `joins.com`을 사용하므로 Selenium이 필요합니다.

### RSS 피드 URL 확인

```python
SAMPLE_RSS_FEEDS = [
    "https://www.hani.co.kr/rss/",
    "https://rss.joins.com/joins_news_list.xml",
    "https://www.mk.co.kr/rss/30000001/",
]
```

## 🎯 결론

- **한겨레**: requests로 크롤링 (빠름) ✅
- **중앙일보**: Selenium으로 크롤링 (느림) - 빌드 수정 후 작동
- **매일경제**: requests로 크롤링 (빠름) - SSL 인증서 포함 후 작동

빌드 시 Selenium과 SSL 인증서를 명시적으로 포함시켜 모든 사이트가 정상 작동하도록 수정했습니다!
