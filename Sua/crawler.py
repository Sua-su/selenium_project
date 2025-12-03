"""
Selenium + trafilatura 크롤러 모듈
동적 웹페이지를 렌더링하고 본문을 추출합니다.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import trafilatura
import time
import platform
from typing import Optional, Dict


class WebCrawler:
    """Selenium + trafilatura 웹 크롤러 클래스"""
    
    def __init__(self, headless: bool = True):
        """크롤러 초기화
        
        Args:
            headless: 헤드리스 모드 사용 여부
        """
        self.headless = headless
        self.driver = None
    
    def init_driver(self):
        """Selenium 드라이버 초기화"""
        if self.driver is not None:
            return
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')  # 최신 헤드리스 모드
        
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
        
        # 플랫폼별 옵션
        system = platform.system().lower()
        if system == 'linux':
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
        elif system == 'darwin':  # macOS
            chrome_options.add_argument('--disable-web-security')
        elif system == 'windows':
            chrome_options.add_argument('--disable-web-security')
        
        # 자동화 탐지 회피
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 페이지 로딩 전략
        chrome_options.page_load_strategy = 'normal'
        
        try:
            # webdriver-manager로 자동 ChromeDriver 관리
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
            self.driver.set_page_load_timeout(30)
            
        except Exception as e:
            print(f"드라이버 초기화 오류: {str(e)}")
            print("Chrome 브라우저가 설치되어 있는지 확인하세요.")
            raise
    
    def close_driver(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def get_page_html(self, url: str, wait_time: int = 3) -> Optional[str]:
        """페이지 HTML 가져오기 (JavaScript 렌더링 포함)
        
        Args:
            url: 크롤링할 URL
            wait_time: 페이지 로딩 대기 시간 (초)
            
        Returns:
            렌더링된 HTML 또는 None
        """
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                if self.driver is None:
                    self.init_driver()
                
                self.driver.get(url)
                
                # 페이지가 완전히 로드될 때까지 대기
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 추가 대기 (동적 콘텐츠 로딩)
                time.sleep(wait_time)
                
                html = self.driver.page_source
                return html
            
            except Exception as e:
                print(f"페이지 로딩 오류 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # 재시도 전 대기
                    continue
                return None
    
    def extract_content(self, html: str, url: str = None) -> Dict:
        """trafilatura로 본문 추출
        
        Args:
            html: HTML 소스
            url: 원본 URL (선택)
            
        Returns:
            추출된 콘텐츠 딕셔너리
        """
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
    
    def crawl_article(self, url: str, wait_time: int = 3) -> Dict:
        """기사 크롤링 (Selenium + trafilatura)
        
        Args:
            url: 크롤링할 기사 URL
            wait_time: 페이지 로딩 대기 시간
            
        Returns:
            추출된 기사 정보
        """
        print(f"크롤링 중: {url}")
        
        # 1단계: Selenium으로 동적 페이지 렌더링
        html = self.get_page_html(url, wait_time)
        
        if not html:
            return {
                'url': url,
                'success': False,
                'error': '페이지 로딩 실패'
            }
        
        # 2단계: trafilatura로 본문 추출
        extracted = self.extract_content(html, url)
        
        # 콘텐츠 유효성 검사
        if not extracted['content'] or len(extracted['content'].strip()) < 50:
            return {
                'url': url,
                'success': False,
                'error': '본문 추출 실패 또는 콘텐츠 부족'
            }
        
        return {
            'url': url,
            'success': True,
            'title': extracted['title'],
            'content': extracted['content'],
            'author': extracted['author'],
            'published_date': extracted['date'],
            'source': extracted['sitename'],
            'description': extracted['description']
        }
    
    def crawl_multiple_articles(self, urls: list, wait_time: int = 3, delay: float = 2.0) -> list:
        """여러 기사 일괄 크롤링
        
        Args:
            urls: 크롤링할 URL 리스트
            wait_time: 각 페이지 로딩 대기 시간
            delay: 요청 간 지연 시간
            
        Returns:
            크롤링 결과 리스트
        """
        results = []
        
        try:
            self.init_driver()
            
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
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.init_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.close_driver()
