"""
RSS 피드 파싱 모듈
RSS 피드에서 기사 URL과 메타데이터를 추출합니다.
"""

import feedparser
import requests
from typing import List, Dict
from datetime import datetime
import time


class RSSParser:
    """RSS 피드 파서 클래스"""
    
    def __init__(self):
        """RSS 파서 초기화"""
        # User-Agent 설정
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def parse_feed(self, rss_url: str) -> List[Dict]:
        """RSS 피드 파싱
        
        Args:
            rss_url: RSS 피드 URL
            
        Returns:
            파싱된 기사 목록
        """
        try:
            # 먼저 requests로 HTTP 상태 확인
            response = requests.get(rss_url, headers=self.headers, timeout=10, allow_redirects=True)
            
            if response.status_code != 200:
                print(f"HTTP 오류: {response.status_code} - {rss_url}")
                return []
            
            # Content-Type 확인
            content_type = response.headers.get('content-type', '').lower()
            if 'xml' not in content_type and 'rss' not in content_type:
                print(f"잘못된 Content-Type: {content_type} - {rss_url}")
                return []
            
            # feedparser로 파싱
            feed = feedparser.parse(response.content)
            
            # Bozo flag 확인 (파싱 오류)
            if feed.bozo:
                print(f"RSS 파싱 오류: {feed.bozo_exception} - {rss_url}")
                # 계속 진행하지만 경고 표시
            
            # entries가 없는 경우
            if not hasattr(feed, 'entries') or len(feed.entries) == 0:
                print(f"기사가 없음: {rss_url}")
                return []
            
            articles = []
            for entry in feed.entries:
                article = {
                    'url': entry.get('link', ''),
                    'title': entry.get('title', ''),
                    'author': entry.get('author', ''),
                    'published_date': self._parse_date(entry),
                    'source': feed.feed.get('title', ''),
                    'rss_feed': rss_url,
                    'summary': entry.get('summary', ''),
                    'tags': self._extract_tags(entry)
                }
                
                if article['url']:  # URL이 있는 경우만 추가
                    articles.append(article)
            
            return articles
        
        except requests.exceptions.RequestException as e:
            print(f"네트워크 오류: {str(e)} - {rss_url}")
            return []
        except Exception as e:
            print(f"RSS 파싱 오류: {str(e)} - {rss_url}")
            return []
    
    def parse_multiple_feeds(self, rss_urls: List[str]) -> List[Dict]:
        """여러 RSS 피드 일괄 파싱
        
        Args:
            rss_urls: RSS 피드 URL 리스트
            
        Returns:
            모든 피드의 기사 목록
        """
        all_articles = []
        
        for rss_url in rss_urls:
            print(f"RSS 파싱 중: {rss_url}")
            articles = self.parse_feed(rss_url)
            if articles:
                all_articles.extend(articles)
                print(f"  ✓ {len(articles)}개 기사 수집")
            else:
                print(f"  ✗ 실패 또는 기사 없음")
            time.sleep(1)  # 서버 부하 방지
        
        return all_articles
    
    def _parse_date(self, entry) -> str:
        """게시일 파싱
        
        Args:
            entry: RSS 엔트리
            
        Returns:
            날짜 문자열 (YYYY-MM-DD HH:MM:SS)
        """
        date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
        
        for field in date_fields:
            if hasattr(entry, field):
                time_struct = getattr(entry, field)
                if time_struct:
                    try:
                        return time.strftime("%Y-%m-%d %H:%M:%S", time_struct)
                    except:
                        pass
        
        # 날짜를 찾을 수 없는 경우 현재 시간
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _extract_tags(self, entry) -> str:
        """태그 추출
        
        Args:
            entry: RSS 엔트리
            
        Returns:
            쉼표로 구분된 태그 문자열
        """
        tags = []
        
        if hasattr(entry, 'tags'):
            for tag in entry.tags:
                if isinstance(tag, dict) and 'term' in tag:
                    tags.append(tag['term'])
                elif isinstance(tag, str):
                    tags.append(tag)
        
        return ', '.join(tags) if tags else ''
    
    def get_feed_info(self, rss_url: str) -> Dict:
        """RSS 피드 정보 조회
        
        Args:
            rss_url: RSS 피드 URL
            
        Returns:
            피드 정보 딕셔너리
        """
        try:
            feed = feedparser.parse(rss_url)
            
            return {
                'title': feed.feed.get('title', ''),
                'link': feed.feed.get('link', ''),
                'description': feed.feed.get('description', ''),
                'language': feed.feed.get('language', ''),
                'updated': feed.feed.get('updated', ''),
                'entry_count': len(feed.entries)
            }
        
        except Exception as e:
            print(f"피드 정보 조회 오류: {str(e)}")
            return {}


# 주요 한국 뉴스 RSS 피드 예시
SAMPLE_RSS_FEEDS = [
    "https://www.hani.co.kr/rss/",  # 한겨레
    "https://www.mk.co.kr/rss/30000001/",  # 매일경제
]
