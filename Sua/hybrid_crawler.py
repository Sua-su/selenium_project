"""
하이브리드 크롤러 모듈
requests + trafilatura (정적 페이지) + Selenium (동적 페이지)
"""

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
        
        # 정적 페이지로 판단할 도메인 패턴
        self.static_patterns = [
            r'.*\.hani\.co\.kr',
            r'.*\.mk\.co\.kr',
            r'.*\.chosun\.com',
            r'.*\.joongang\.co\.kr',
            r'.*\.hankyung\.com',
            r'.*\.news1\.kr',
            r'.*\.yonhapnews\.com',
            r'.*\.yna\.co\.kr',  # 연합뉴스
            r'.*news\.yna\.co\.kr'  # 연합뉴스 뉴스 도메인
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
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 자동화 탐지 우회
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
    
    def extract_content(self, html: str, url: str = None) -> Dict:
        """trafilatura로 본문 추출"""
        try:
            # trafilatura로 본문 추출
            content = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                url=url
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
            
            return result
        
        except Exception as e:
            print(f"콘텐츠 추출 오류: {str(e)}")
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
            # 정적/동적 페이지 판단
            is_static = self.is_static_page(url)
            crawler_type = "정적(requests)" if is_static else "동적(Selenium)"
            print(f"  {crawler_type} 페이지로 판단")
            
            # 1단계: HTML 가져오기
            if is_static:
                html = self.get_static_html(url)
                method = "requests"
            else:
                html = self.get_dynamic_html(url, wait_time)
                method = "selenium"
            
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