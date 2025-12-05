import hashlib
import os
import sqlite3
from functools import lru_cache, wraps
from typing import Set, Optional
import time
import sys


class CacheManager:
    """URL 캐시 및 HTML 캐시 관리 클래스"""
    
    def __init__(self, cache_dir: str = "cache", db_path: str = "cache.db"):

        # PyInstaller로 빌드 실행 경로 조정
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
            self.cache_dir = os.path.join(base_path, cache_dir)
            self.db_path = os.path.join(base_path, db_path)
            #이 두줄 때문에 경로 문제 떄문에 오류 나는 것일 수도 .. 절대 경로 박아놔서
        else:
            self.cache_dir = cache_dir
            self.db_path = db_path
        self.cache_dir = cache_dir
        self.db_path = db_path

        os.makedirs(cache_dir, exist_ok=True)
        self.init_cache_db()
        self._url_cache: Set[str] = set()
        self._load_url_cache()
    
    def init_cache_db(self):
        """캐시; 데이터베이스 초기화"""
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
        #일단 일주일
        week_ago = time.time() - (7 * 24 * 3600)
        cursor.execute("DELETE FROM url_cache WHERE timestamp < ?", (week_ago,))
        cursor.execute("DELETE FROM html_cache WHERE timestamp < ?", (week_ago,))
        
        conn.commit()
        conn.close()
    

    def _load_url_cache(self):
        """URL을 메모리에 로드"""
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
        """
        URL을 MD5 해시로 변환
        """
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    


    def is_url_crawled(self, url: str) -> bool:
        return url in self._url_cache
    

    
    def mark_url_crawled(self, url: str, success: bool = True):
        """
        URL을 크롤링 완료로 표시
        """
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

    
    #일단 이틀 저장
    def get_cached_html(self, url: str, max_age_hours: int = 48) -> Optional[str]:
        """
        캐시된 HTML 조회
        """
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
        """
        HTML 캐싱
        """
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
        """
        캐시 통계 정보 조회
        """
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
        """
        캐시 정리
        """
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
    """
    싱글톤 패턴으로 인스턴스 반환
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager






def skip_if_crawled(func):
    """
    이미 크롤링된 URL을 건너뛰는 데코
    """
    @wraps(func) 
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
    """
    램 캐시를 사용한 내용 조회
    """
    cache = get_cache_manager()
    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT html FROM html_cache WHERE url_hash = ?", (url_hash,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None
