"""
RSS 피드 파싱 모듈
RSS 피드에서 기사 URL과 메타데이터를 추출합니다.
"""

import feedparser
from typing import List, Dict
from datetime import datetime
import time


class RSSParser:
    """RSS 피드 파서 클래스"""
    
    def __init__(self):
        """RSS 파서 초기화"""
        pass
    
    def parse_feed(self, rss_url: str) -> List[Dict]:
        """RSS 피드 파싱
        
        Args:
            rss_url: RSS 피드 URL
            
        Returns:
            파싱된 기사 목록
        """
        try:
            feed = feedparser.parse(rss_url)
            
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
        
        except Exception as e:
            print(f"RSS 파싱 오류: {str(e)}")
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
            all_articles.extend(articles)
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
    "https://rss.joins.com/joins_news_list.xml",  # 중앙일보
    "https://www.mk.co.kr/rss/30000001/",  # 매일경제
]
