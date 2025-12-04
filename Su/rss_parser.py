import feedparser
import requests
from typing import List, Dict
from datetime import datetime
import time


class RSSParser:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def parse_feed(self, rss_url: str) -> List[Dict]:
        try:
            response = requests.get(rss_url, headers=self.headers, timeout=10, allow_redirects=True)
            
            if response.status_code != 200:
                print(f"HTTP 오류: {response.status_code} - {rss_url}")
                return []
            
            content_type = response.headers.get('content-type', '').lower()
            if 'xml' not in content_type and 'rss' not in content_type:
                print(f"잘못된 Content-Type: {content_type} - {rss_url}")
                return []
            
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                print(f"RSS 파싱 오류: {feed.bozo_exception} - {rss_url}")
            
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
                
                if article['url']:
                    articles.append(article)
            
            return articles
        
        except requests.exceptions.RequestException as e:
            print(f"네트워크 오류: {str(e)} - {rss_url}")
            return []
        except Exception as e:
            print(f"RSS 파싱 오류: {str(e)} - {rss_url}")
            return []
    
    def parse_multiple_feeds(self, rss_urls: List[str]) -> List[Dict]:
        all_articles = []
        
        for rss_url in rss_urls:
            print(f"RSS 파싱 중: {rss_url}")
            articles = self.parse_feed(rss_url)
            if articles:
                all_articles.extend(articles)
                print(f"  ✓ {len(articles)}개 기사 수집")
            else:
                print(f"  ✗ 실패 또는 기사 없음")
            time.sleep(1)
        
        return all_articles
    
    def _parse_date(self, entry) -> str:
        date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
        
        for field in date_fields:
            if hasattr(entry, field):
                time_struct = getattr(entry, field)
                if time_struct:
                    try:
                        return time.strftime("%Y-%m-%d %H:%M:%S", time_struct)
                    except:
                        pass
        
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _extract_tags(self, entry) -> str:
        tags = []
        
        if hasattr(entry, 'tags'):
            for tag in entry.tags:
                if isinstance(tag, dict) and 'term' in tag:
                    tags.append(tag['term'])
                elif isinstance(tag, str):
                    tags.append(tag)
        
        return ', '.join(tags) if tags else ''
    
    def get_feed_info(self, rss_url: str) -> Dict:
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


SAMPLE_RSS_FEEDS = [
    "https://www.hani.co.kr/rss/",
    "https://www.mk.co.kr/rss/30000001/",
]
