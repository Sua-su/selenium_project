"""
하이브리드 크롤러 모듈
requests + trafilatura (정적 페이지) + Selenium (동적 페이지)
"""

import sys
import requests
import trafilatura
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional, Dict, List
import time
import re
import platform
from urllib.parse import urlparse
from cache_manager import get_cache_manager, skip_if_crawled


class HybridCrawler:
    """하이브리드 크롤러: 정적 페이지는 requests, 동적 페이지는 Selenium"""
    
    def __init__(self, headless: bool = True):
        """크롤러 초기화"""
        self.headless = headless
        self.driver = None
        self.selenium_available = True  # Selenium 사용 가능 여부
        
        # requests 세션 설정
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        })
        
        # 정적 페이지로 판단할 도메인 패턴 (대부분의 한국 뉴스 사이트)
        self.static_patterns = [
            r'.*\.hani\.co\.kr',      # 한겨레
            r'.*\.mk\.co\.kr',        # 매일경제
            r'.*\.chosun\.com',       # 조선일보
            r'.*\.joongang\.co\.kr',  # 중앙일보
            r'.*\.hankyung\.com',     # 한국경제
            r'.*\.news1\.kr',         # 뉴스1
            r'.*\.yonhapnews\.com',   # 연합뉴스
            r'.*\.yna\.co\.kr',       # 연합뉴스
            r'.*news\.yna\.co\.kr',   # 연합뉴스 뉴스
            r'.*\.hankookilbo\.com',  # 한국일보
            r'.*\.kmib\.com',         # 국민일보
            r'.*\.seoul\.co\.kr',     # 서울신문
            r'.*\.kyunghyang\.com',   # 경향신문
            r'.*\.ohmynews\.com',     # 오마이뉴스
            r'.*\.newsis\.com',       # 뉴시스
            r'.*\.heraldcorp\.com',   # 헤럴드경제
            r'.*\.etnews\.com',       # 전자신문
            r'.*\.zdnet\.co\.kr',     # ZDNet Korea
            r'.*\.techholic\.co\.kr', # 테크홀릭
            r'.*\.inven\.co\.kr',     # 인벤
            r'.*\.gamechosun\.co\.kr', # 게임조선
            r'.*\.thisisgame\.com',   # 디스이즈게임
        ]
    
    def is_static_page(self, url: str) -> bool:
        """정적 페이지인지 확인"""
        domain = urlparse(url).netloc
        for pattern in self.static_patterns:
            if re.match(pattern, domain):
                return True
        return False
    
    def init_driver(self):
        """Selenium 드라이버 초기화 (동적 페이지용)"""
        if self.driver is not None:
            return
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # 공통 옵션 (모든 플랫폼)
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')
        
        # 플랫폼별 옵션
        system = platform.system().lower()
        if system == 'linux':
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
        elif system == 'darwin':  # macOS
            chrome_options.add_argument('--disable-web-security')
        elif system == 'windows':
            chrome_options.add_argument('--disable-web-security')
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.page_load_strategy = 'eager'  # interactive보다 빠름
        
        try:
            import sys
            import os
            
            # 번들 환경인지 확인
            if getattr(sys, 'frozen', False):
                # PyInstaller로 번들된 경우
                print("번들 환경에서 ChromeDriver 초기화 시도...")
                
                # 여러 드라이버 위치 시도
                driver_paths = []
                
                # 1. 실행 파일과 같은 디렉토리
                try:
                    meipass = getattr(sys, '_MEIPASS', None)
                    if meipass:
                        driver_dir = meipass
                    else:
                        driver_dir = os.path.dirname(sys.executable)
                except:
                    driver_dir = os.getcwd()
                
                driver_paths.extend([
                    os.path.join(driver_dir, 'chromedriver.exe'),
                    os.path.join(driver_dir, 'chromedriver'),
                    os.path.join(os.getcwd(), 'chromedriver.exe'),
                    os.path.join(os.getcwd(), 'chromedriver')
                ])
                
                # 2. webdriver_manager fallback
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    driver_paths.append(ChromeDriverManager().install())
                except:
                    pass
                
                # 3. 시스템 PATH에서 찾기
                driver_paths.append('chromedriver')
                
                # 가능한 드라이버 경로 시도
                driver_found = False
                for driver_path in driver_paths:
                    try:
                        if os.path.exists(driver_path) or driver_path == 'chromedriver':
                            print(f"ChromeDriver 경로 시도: {driver_path}")
                            service = Service(driver_path)
                            self.driver = webdriver.Chrome(service=service, options=chrome_options)
                            print(f"ChromeDriver 초기화 성공: {driver_path}")
                            driver_found = True
                            break
                    except Exception as path_e:
                        print(f"드라이버 경로 실패 {driver_path}: {str(path_e)}")
                        continue
                
                if not driver_found:
                    raise Exception("사용 가능한 ChromeDriver를 찾을 수 없음")
                    
            else:
                # 개발 환경
                print("개발 환경에서 ChromeDriver 초기화...")
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 자동화 탐지 우회 (드라이버가 성공적으로 초기화된 경우에만)
            if self.driver:
                try:
                    self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                        "userAgent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
                    })
                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                except Exception as e:
                    print(f"CDP 명령 실행 실패 (무시 가능): {str(e)}")
                
                # 타임아웃 설정
                self.driver.set_page_load_timeout(15)
            
        except Exception as e:
            print(f"드라이버 초기화 오류: {str(e)}")
            print("Selenium 모드 실패, requests-only 모드로 전환")
            self.selenium_available = False
            # 예외를 발생시키지 않고 계속 진행
    
    def close_driver(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def get_static_html(self, url: str, timeout: int = 10) -> Optional[str]:
        """requests로 정적 페이지 HTML 가져오기"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                # 번들 환경에서 SSL 인증서 문제 해결
                import certifi
                import os
                
                # 번들 환경인지 확인
                if getattr(sys, 'frozen', False):
                    # certifi 번들 경로 설정
                    ca_bundle = certifi.where()
                    if not os.path.exists(ca_bundle):
                        # fallback to system certs
                        response = self.session.get(url, timeout=timeout, allow_redirects=True, verify=False)
                    else:
                        response = self.session.get(url, timeout=timeout, allow_redirects=True, verify=ca_bundle)
                else:
                    response = self.session.get(url, timeout=timeout, allow_redirects=True)
                
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"HTTP 오류: {response.status_code} - {url}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return None
                    
            except Exception as e:
                print(f"정적 페이지 로딩 오류 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                print(f"  URL: {url}")
                print(f"  번들 환경: {getattr(sys, 'frozen', False)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return None
    
    def get_dynamic_html(self, url: str, wait_time: int = 1) -> Optional[str]:
        """Selenium으로 동적 페이지 HTML 가져오기"""
        # Selenium이 사용 불가능한 경우 즉시 None 반환
        if not self.selenium_available:
            return None
            
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                if self.driver is None:
                    self.init_driver()
                
                # 드라이버가 여전히 None인 경우
                if self.driver is None:
                    return None
                
                self.driver.get(url)
                
                # 페이지가 완전히 로드될 때까지 대기
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 적응적 대기: 페이지 로딩 상태 확인
                try:
                    WebDriverWait(self.driver, 5).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                except:
                    pass  # 타임아웃되어도 계속 진행
                
                # 최소 대기 시간
                time.sleep(wait_time)
                
                html = self.driver.page_source
                return html
            
            except Exception as e:
                print(f"동적 페이지 로딩 오류 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None
    
    def extract_content(self, html: str, url: str = '') -> Dict:
        """trafilatura로 본문 추출 (fallback 포함)"""
        try:
            # trafilatura로 본문 추출
            content = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                url=url if url else ''
            )
            
            # 메타데이터 추출
            metadata = trafilatura.extract_metadata(html)
            
            result = {
                'content': content or '',
                'title': metadata.title if metadata and metadata.title else '',
                'author': metadata.author if metadata and metadata.author else '',
                'date': metadata.date if metadata and metadata.date else '',
                'description': metadata.description if metadata and metadata.description else '',
                'sitename': metadata.sitename if metadata and metadata.sitename else '',
            }
            
            # 콘텐츠 유효성 검사 - 너무 짧으면 fallback 시도
            if not content or len(content.strip()) < 100:
                print(f"  trafilatura 추출 콘텐츠 부족 ({len(content or '')}자), BeautifulSoup fallback 시도...")
                return self._fallback_extract_content(html, url)
            
            return result
        
        except Exception as e:
            print(f"trafilatura 추출 오류: {str(e)}")
            print("  BeautifulSoup fallback 시도...")
            return self._fallback_extract_content(html, url)
    
    def _fallback_extract_content(self, html: str, url: str) -> Dict:
        """BeautifulSoup로 fallback 본문 추출"""
        try:
            from bs4 import BeautifulSoup
            import re
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 제목 추출 - 사이트별 특화 로직 추가
            title = ''
            
            # 1. meta 태그 우선 (og:title, twitter:title 등)
            meta_title = None
            for meta_attr in ['og:title', 'twitter:title', 'title']:
                meta_tag = soup.find('meta', {'property': meta_attr}) or soup.find('meta', {'name': meta_attr})
                if meta_tag:
                    content = meta_tag.get('content')
                    if content:
                        meta_title = content.strip()
                        if meta_title and len(meta_title) > 5:
                            break
            
            # 2. title 태그
            if not meta_title:
                title_tag = soup.find('title')
                if title_tag:
                    meta_title = title_tag.get_text().strip()
            
            # 3. h1, h2, h3 태그 (한겨레 특화)
            if not meta_title:
                for header_tag in ['h1', 'h2', 'h3']:
                    header = soup.find(header_tag)
                    if header:
                        header_text = header.get_text().strip()
                        # 한겨레 특유 패턴 필터링
                        if '젠슨' not in header_text and len(header_text) > 10:
                            meta_title = header_text
                            break
            
            title = meta_title or ''
            
            # 본문 추출 - 다양한 선택자 시도 (한겨레 특화 포함)
            content_selectors = [
                # 한겨레 특화 선택자 (실제 HTML 구조 기반)
                '.article-text',
                '.article-text p.text',
                '.article-body',
                '.text',
                '.news-text',
                '#articleText',
                '#articleBody',
                '.article-content',
                '.content-text',
                '.story-text',
                '.article-main',
                '.news-body',
                # 일반적인 선택자
                'article',
                '.article-content',
                '.content',
                '.post-content',
                '.entry-content',
                '.news-content',
                '.article-body',
                '.post-body',
                'main',
                '.main-content',
                '#article-content',
                '#content',
                '#main-content'
            ]
            
            content = ''
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    # 한겨레 특화: .article-text 안의 p.text 태그들만 추출
                    if selector == '.article-text':
                        p_texts = element.select('p.text')
                        if p_texts:
                            content = '\n'.join([p.get_text().strip() for p in p_texts])
                        else:
                            content = element.get_text().strip()
                    else:
                        content = element.get_text().strip()
                    
                    if len(content) > 100:  # 최소 길이 확인
                        break
            
            # 본문이 너무 짧으면 전체 텍스트에서 추출
            if len(content) < 100:
                # 불필요한 태그 제거
                for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'ad', 'iframe']):
                    tag.decompose()
                
                # body 텍스트 추출
                body = soup.find('body')
                if body:
                    content = body.get_text().strip()
            
            # 텍스트 정제 (강화)
            content = re.sub(r'\s+', ' ', content)  # 여러 공백을 하나로
            content = re.sub(r'\n\s*\n', '\n\n', content)  # 문단 구분
            content = re.sub(r'^\s+|\s+$', '', content)  # 앞뒤 공백 제거
            
            # 불필요한 패턴 제거
            content = re.sub(r'관련뉴스.*$', '', content, flags=re.MULTILINE)  # 관련뉴스 제거
            content = re.sub(r'기자\s*:\s*\w+\s*기자.*$', '', content, flags=re.MULTILINE)  # 기자 정보 제거
            content = re.sub(r'☞.*$', '', content, flags=re.MULTILINE)  # 링크 제거
            
            # 출처/사이트 정보 추출
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            
            # 저자 추출 시도 - 더 구체적인 선택자들
            author = ''
            author_selectors = [
                '.author',
                '.byline', 
                '.reporter',
                '.writer',
                '.journalist',
                '.by',
                '.article-author',
                '.news-author',
                '.post-author',
                '.entry-author',
                '[class*="author"]',
                '[class*="byline"]',
                '[class*="reporter"]',
                '[class*="writer"]',
                '[class*="journalist"]',
                '[rel="author"]',
                '.byline-name',
                '.author-name',
                'span[class*="by"]',
                'div[class*="author"]'
            ]
            
            for selector in author_selectors:
                element = soup.select_one(selector)
                if element:
                    author = element.get_text().strip()
                    if len(author) > 2:
                        break
            
            # 날짜 추출 시도
            date = ''
            date_selectors = [
                '.date',
                '.publish-date',
                '.article-date',
                '.news-date',
                'time',
                '[datetime]',
                '[class*="date"]',
                '[class*="time"]'
            ]
            
            for selector in date_selectors:
                element = soup.select_one(selector)
                if element:
                    date = element.get('datetime') or element.get_text().strip()
                    if date:
                        break
            
            # 사이트 이름 추출 - 한겨레 특화
            sitename = domain
            
            # 1. og:site_name meta 태그
            site_tag = soup.find('meta', {'property': 'og:site_name'})
            if site_tag:
                content = site_tag.get('content')
                if content:
                    sitename = content.strip()
                else:
                    sitename = ''
            
            # 2. 한겨레 특화 처리
            if not sitename and 'hani.co.kr' in domain:
                sitename = '한겨레'
            
            # 3. 일반적인 사이트 이름 선택자
            if not sitename:
                site_name_selectors = [
                    '.site-name',
                    '.brand',
                    '.logo',
                    '[class*="site"]',
                    '[class*="brand"]'
                ]
                
                for selector in site_name_selectors:
                    element = soup.select_one(selector)
                    if element:
                        sitename = element.get_text().strip()
                        if sitename:
                            break
            
            return {
                'content': content,
                'title': title,
                'author': author,
                'date': date,
                'description': '',
                'source': sitename or domain
            }
            
        except ImportError:
            print("  BeautifulSoup 없음, 기본 텍스트 추출 시도...")
            return self._basic_text_extract(html)
        except Exception as e:
            print(f"  fallback 추출 오류: {str(e)}")
            return self._basic_text_extract(html)
    
    def _basic_text_extract(self, html: str) -> Dict:
        """기본 텍스트 추출 (최후의 수단)"""
        try:
            import re
            
            # HTML 태그 제거
            text = re.sub(r'<[^>]+>', '', html)
            # HTML 엔티티 디코딩
            text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            # 여러 공백 정리
            text = re.sub(r'\s+', ' ', text).strip()
            
            return {
                'content': text,
                'title': '',
                'author': '',
                'date': '',
                'description': '',
                'sitename': ''
            }
        except Exception as e:
            print(f"  기본 텍스트 추출 오류: {str(e)}")
            return {
                'content': '',
                'title': '',
                'author': '',
                'date': '',
                'description': '',
                'sitename': ''
            }
    
    @skip_if_crawled
    def crawl_article(self, url: str, wait_time: int = 1) -> Dict:
        """하이브리드 기사 크롤링 (캐싱 적용)"""
        print(f"크롤링 중: {url}")
        
        # 캐시된 HTML 확인
        cache = get_cache_manager()
        cached_html = cache.get_cached_html(url)
        
        if cached_html:
            print("  캐시된 HTML 사용")
            html = cached_html
            method = "cached"
        else:
            # 임시로 모든 페이지를 정적으로 처리 (테스트용)
            is_static = True  # self.is_static_page(url)
            crawler_type = "정적(requests)"
            print(f"  {crawler_type} 페이지로 판단 (임시 강제)")
            
            # 1단계: HTML 가져오기
            if is_static:
                html = self.get_static_html(url)
                method = "requests"
            else:
                html = self.get_dynamic_html(url, wait_time)
                method = "selenium"
                
                # 동적 처리 실패 시 정적 fallback
                if not html:
                    print("  동적 처리 실패, 정적 fallback 시도...")
                    html = self.get_static_html(url)
                    if html:
                        method = "requests_fallback"
             
            # 성공한 경우 HTML 캐싱
            if html:
                cache.cache_html(url, html)
        
        if not html:
            return {
                'url': url,
                'success': False,
                'error': f'페이지 로딩 실패 ({method})',
                'method': method
            }
        
        # 2단계: trafilatura로 본문 추출
        extracted = self.extract_content(html, url)
        
        # 콘텐츠 유효성 검사
        if not extracted['content'] or len(extracted['content'].strip()) < 50:
            return {
                'url': url,
                'success': False,
                'error': '본문 추출 실패 또는 콘텐츠 부족',
                'method': method
            }
        
        return {
            'url': url,
            'success': True,
            'title': extracted['title'],
            'content': extracted['content'],
            'author': extracted['author'],
            'published_date': extracted['date'],
            'source': extracted['sitename'],
            'description': extracted['description'],
            'method': method
        }
    
    def crawl_multiple_articles(self, urls: List[str], wait_time: int = 1, delay: float = 0.5) -> List[Dict]:
        """여러 기사 일괄 크롤링 (순차적)"""
        results = []
        
        # 필요한 경우에만 드라이버 초기화
        has_dynamic = any(not self.is_static_page(url) for url in urls)
        if has_dynamic:
            self.init_driver()
        
        try:
            for i, url in enumerate(urls, 1):
                print(f"진행중: {i}/{len(urls)}")
                result = self.crawl_article(url, wait_time)
                results.append(result)
                
                # 서버 부하 방지를 위한 지연
                if i < len(urls):
                    time.sleep(delay)
        
        finally:
            self.close_driver()
        
        return results
    
    def close(self):
        """리소스 정리"""
        self.close_driver()
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.close()