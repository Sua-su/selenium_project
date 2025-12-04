import hashlib
import os
import sqlite3
from functools import lru_cache
from typing import Set, Optional
import time


class CacheManager:
    def __init__(self, cache_dir: str = "cache", db_path: str = "cache.db"):
        self.cache_dir = cache_dir
        self.db_path = db_path
        os.makedirs(cache_dir, exist_ok=True)
        self.init_cache_db()
        self._url_cache: Set[str] = set()
        self._load_url_cache()
    
    def init_cache_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS url_cache (
                url_hash TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                timestamp REAL NOT NULL,
                success INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS html_cache (
                url_hash TEXT PRIMARY KEY,
                html TEXT NOT NULL,
                timestamp REAL NOT NULL,
                content_length INTEGER DEFAULT 0
            )
        ''')
        
        week_ago = time.time() - (7 * 24 * 3600)
        cursor.execute("DELETE FROM url_cache WHERE timestamp < ?", (week_ago,))
        cursor.execute("DELETE FROM html_cache WHERE timestamp < ?", (week_ago,))
        
        conn.commit()
        conn.close()
    
    def _load_url_cache(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT url FROM url_cache WHERE success = 1")
            self._url_cache = {row[0] for row in cursor.fetchall()}
            conn.close()
            print(f"캐시된 URL {len(self._url_cache)}개 로드됨")
        except Exception as e:
            print(f"URL 캐시 로드 실패: {str(e)}")
            self._url_cache = set()
    
    def _get_url_hash(self, url: str) -> str:
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def is_url_crawled(self, url: str) -> bool:
        return url in self._url_cache
    
    def mark_url_crawled(self, url: str, success: bool = True):
        url_hash = self._get_url_hash(url)
        timestamp = time.time()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO url_cache (url_hash, url, timestamp, success)
            VALUES (?, ?, ?, ?)
        ''', (url_hash, url, timestamp, int(success)))
        
        conn.commit()
        conn.close()
        
        if success:
            self._url_cache.add(url)
    
    def get_cached_html(self, url: str, max_age_hours: int = 48) -> Optional[str]:
        url_hash = self._get_url_hash(url)
        max_age = time.time() - (max_age_hours * 3600)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT html FROM html_cache 
            WHERE url_hash = ? AND timestamp > ?
        ''', (url_hash, max_age))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            print(f"캐시된 HTML 사용: {url}")
            return result[0]
        
        return None
    
    def cache_html(self, url: str, html: str):
        if not html or len(html) < 100:
            return
        
        url_hash = self._get_url_hash(url)
        timestamp = time.time()
        content_length = len(html)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO html_cache (url_hash, html, timestamp, content_length)
            VALUES (?, ?, ?, ?)
        ''', (url_hash, html, timestamp, content_length))
        
        conn.commit()
        conn.close()
        
        print(f"HTML 캐시됨: {url} ({content_length} bytes)")
    
    def get_cache_stats(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM url_cache WHERE success = 1")
        successful_urls = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM url_cache WHERE success = 0")
        failed_urls = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*), SUM(content_length) FROM html_cache")
        html_count, total_size = cursor.fetchone()
        
        conn.close()
        
        return {
            'successful_urls': successful_urls,
            'failed_urls': failed_urls,
            'html_cache_count': html_count or 0,
            'total_html_size_mb': round((total_size or 0) / (1024 * 1024), 2),
            'memory_cache_urls': len(self._url_cache)
        }
    
    def clear_cache(self, older_than_hours: int = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if older_than_hours:
            cutoff_time = time.time() - (older_than_hours * 3600)
            cursor.execute("DELETE FROM url_cache WHERE timestamp < ?", (cutoff_time,))
            cursor.execute("DELETE FROM html_cache WHERE timestamp < ?", (cutoff_time,))
            print(f"{older_than_hours}시간 이상 된 캐시 정리됨")
        else:
            cursor.execute("DELETE FROM url_cache")
            cursor.execute("DELETE FROM html_cache")
            print("모든 캐시 정리됨")
        
        conn.commit()
        conn.close()
        
        self._url_cache.clear()
        self._load_url_cache()


_cache_manager = None

def get_cache_manager() -> CacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

def skip_if_crawled(func):
    def wrapper(self, url: str, *args, **kwargs):
        cache = get_cache_manager()
        if cache.is_url_crawled(url):
            print(f"이미 크롤링된 URL 건너뛰기: {url}")
            return {
                'url': url,
                'success': False,
                'error': '이미 크롤링된 URL',
                'cached': True
            }
        
        result = func(self, url, *args, **kwargs)
        
        if result.get('success'):
            cache.mark_url_crawled(url, True)
        else:
            cache.mark_url_crawled(url, False)
        
        return result
    
    return wrapper

@lru_cache(maxsize=2000)
def get_cached_content(url_hash: str) -> Optional[str]:
    cache = get_cache_manager()
    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT html FROM html_cache WHERE url_hash = ?", (url_hash,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None
