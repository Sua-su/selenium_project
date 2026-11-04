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
from html.parser import HTMLParser

class HybridCrawler:
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.selenium_available = True
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        })
        
        # 정적 크롤링으로 처리할 도메인
        self.static_patterns = [
            r'.*\.hani\.co\.kr',
            r'.*\.mk\.co\.kr',
            r'.*\.chosun\.com',
            r'.*\.joongang\.co\.kr',
            r'.*\.hankyung\.com',
            r'.*\.news1\.kr',
            r'.*\.yonhapnews\.com',
            r'.*\.yna\.co\.kr',
            r'.*news\.yna\.co\.kr'
        ]
    
    def is_static_page(self, url: str) -> bool:
        """
        정적 판단
        """
        domain = urlparse(url).netloc
        for pattern in self.static_patterns:
            if re.match(pattern, domain):
                return True
        return False
    


    
    def init_driver(self):
        """Selenium WebDriver 초기화"""
        if self.driver is not None:
            return
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
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
        
        system = platform.system().lower()
        if system == 'linux':
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
        elif system == 'darwin':
            chrome_options.add_argument('--disable-web-security')
        elif system == 'windows':
            chrome_options.add_argument('--disable-web-security')
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.page_load_strategy = 'eager'
        


        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            try:
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
                })
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except Exception as e:
                print(f"CDP 명령 실행 실패 (무시 가능): {str(e)}")
            
            self.driver.set_page_load_timeout(15)
            
        except Exception as e:
            print(f"드라이버 초기화 오류: {str(e)}")
            print("Selenium 모드 실패, requests-only 모드로 전환")
            self.selenium_available = False
    
    def close_driver(self):
        """WebDriver 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    




    def get_static_html(self, url: str, timeout: int = 10) -> Optional[str]:
        """
        requests를 사용한 정적 페이지
        """
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
        """
        Selenium을 사용한 동적 페이지 HTML 가져오기
        """
        if not self.selenium_available:
            return None
            
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                if self.driver is None:
                    self.init_driver()
                
                if self.driver is None:
                    return None
                
                self.driver.get(url)
                
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                try:
                    WebDriverWait(self.driver, 5).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                except:
                    pass
                
                time.sleep(wait_time)
                
                html = self.driver.page_source
                return html
            
            except Exception as e:
                print(f"동적 페이지 로딩 오류 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None
    


    def extract_content_fallback(self, html: str) -> Dict:
        """
        trafilatura 실패 시 기본 HTML 파싱
        HTMLParser를 사용하여 텍스트 추출
        """
    
        class SimpleTextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text_parts = []
                self.title = ''
                self.in_title = False
                self.skip_tags = ['script', 'style', 'nav', 'header', 'footer', 'aside']
                self.current_skip = None
                
            def handle_starttag(self, tag, attrs):
                if tag == 'title':
                    self.in_title = True
                elif tag in self.skip_tags:
                    self.current_skip = tag
                    
            def handle_endtag(self, tag):
                if tag == 'title':
                    self.in_title = False
                elif tag == self.current_skip:
                    self.current_skip = None
                    
            def handle_data(self, data):
                if self.in_title:
                    self.title = data.strip()
                elif not self.current_skip:
                    text = data.strip()
                    if text and len(text) > 10:  # 5정도로 바꿀까 고민중
                        self.text_parts.append(text)


        
        try:
            extractor = SimpleTextExtractor()
            extractor.feed(html)
            
            content = '\n'.join(extractor.text_parts)
            
            return {
                'content': content,
                'title': extractor.title,
                'author': '',
                'date': '',
                'description': '',
                'sitename': ''
            }
        except Exception as e:
            print(f"Fallback 추출 오류: {str(e)}")
            return {
                'content': '',
                'title': '',
                'author': '',
                'date': '',
                'description': '',
                'sitename': ''
            }
        
    
    def extract_content(self, html: str, url: str = None) -> Dict:
        """
        fallback
        """
        try:
            # 1단계: 기본
            content = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                favor_precision=False,
                favor_recall=True,
                url=url
            )
            
            # 2단계: 30자 
            if not content or len(content.strip()) < 30:
                print("  1단계 실패, 2단계 시도...")
                content = trafilatura.extract(
                    html,
                    include_comments=False,
                    include_tables=True,
                    no_fallback=False,
                    favor_precision=False,
                    favor_recall=True,
                    include_links=False,
                    deduplicate=True,
                    url=url
                )
            
            metadata = trafilatura.extract_metadata(html)
            
            result = {
                'content': content or '',
                'title': metadata.title if metadata and metadata.title else '',
                'author': metadata.author if metadata and metadata.author else '',
                'date': metadata.date if metadata and metadata.date else '',
                'description': metadata.description if metadata and metadata.description else '',
                'sitename': metadata.sitename if metadata and metadata.sitename else '',
            }
            
            # 3단계:fallback 사용
            if not result['content'] or len(result['content'].strip()) < 30:
                print("  2단계 실패, 3단계 fallback 시도...")
                fallback_result = self.extract_content_fallback(html)
                if fallback_result['content'] and len(fallback_result['content'].strip()) >= 30:
                    print(" fallback으로 추출 성공")
                    return fallback_result
            
            return result
        
        except Exception as e:
            print(f"콘텐츠 추출 오류: {str(e)}, fallback 시도")
            return self.extract_content_fallback(html)
    



    @skip_if_crawled #데코 캐싱에서 사용할거
    def crawl_article(self, url: str, wait_time: int = 1) -> Dict:
        """
        단일 기사 크롤링 (자동으로 정적/동적 방식 선택)
        """
        print(f"크롤링 중: {url}")
        
        cache = get_cache_manager()
        cached_html = cache.get_cached_html(url)  #캐싱 .exe 오류 유력
        
        if cached_html:
            print("  캐시된 HTML 사용")
            html = cached_html
            method = "cached"
        else:
            is_static = self.is_static_page(url)
            crawler_type = "정적(requests)" if is_static else "동적(Selenium)"
            print(f"  {crawler_type} 페이지로 판단")
            
            if is_static:
                html = self.get_static_html(url)
                method = "requests"
            else:
                html = self.get_dynamic_html(url, wait_time)
                method = "selenium"
            
            #url저장
            if html:
                cache.cache_html(url, html)
        
        if not html:
            return {
                'url': url,
                'success': False,
                'error': f'페이지 로딩 실패 ({method})',
                'method': method
            }
        
        #추출
        extracted = self.extract_content(html, url)
        
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
        """
        여러 기사 일괄 크롤링
        """
        results = []
        
        has_dynamic = any(not self.is_static_page(url) for url in urls)
        if has_dynamic:
            self.init_driver()
            #최적화 먼저 셀레니움 키기!
        
        try:
            for i, url in enumerate(urls, 1):
                print(f"진행중: {i}/{len(urls)}")
                result = self.crawl_article(url, wait_time)
                results.append(result)
                
                if i < len(urls):
                    time.sleep(delay)
        
        finally:
            self.close_driver() #장단이 있어서 일단은 최적화
        
        return results
    


    
    def close(self):
        """모든 리소스 정리"""
        self.close_driver()
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """종료 시 자동 정리"""
        self.close()
