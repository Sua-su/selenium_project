"""
간단한 HTTP 크롤러 모듈
requests + trafilatura로 가볍게 본문을 추출합니다.
"""

import requests
from typing import Optional, Dict
import time


class SimpleCrawler:
    """requests + trafilatura 간단한 크롤러 클래스"""
    
    def __init__(self):
        """크롤러 초기화"""
        # User-Agent 설정
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_page_html(self, url: str, timeout: int = 10) -> Optional[str]:
        """페이지 HTML 가져오기
        
        Args:
            url: 크롤링할 URL
            timeout: 요청 타임아웃 (초)
            
        Returns:
            HTML 또는 None
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
                        time.sleep(2)
                        continue
                    return None
                    
            except Exception as e:
                print(f"페이지 로딩 오류 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
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
        """기사 크롤링 (requests + trafilatura)
        
        Args:
            url: 크롤링할 기사 URL
            wait_time: 대기 시간 (requests에서는 무시됨)
            
        Returns:
            추출된 기사 정보
        """
        print(f"크롤링 중: {url}")
        
        # 1단계: requests로 HTML 가져오기
        html = self.get_page_html(url)
        
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
            wait_time: 각 페이지 로딩 대기 시간 (무시됨)
            delay: 요청 간 지연 시간
            
        Returns:
            크롤링 결과 리스트
        """
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"진행중: {i}/{len(urls)}")
            result = self.crawl_article(url, wait_time)
            results.append(result)
            
            # 서버 부하 방지를 위한 지연
            if i < len(urls):
                time.sleep(delay)
        
        return results
    
    def close(self):
        """세션 종료"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.close()