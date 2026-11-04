"""
캐싱 시스템 모듈
URL 중복 확인 및 HTML 캐싱으로 성능 최적화
"""

import hashlib
import os
import pickle
import sqlite3
from functools import lru_cache
from typing import Set, Optional
import time


class CacheManager:
    """캐시 관리자: URL 중복 확인 및 HTML 캐싱"""
    
    def __init__(self, cache_dir: str = "cache", db_path: str = "cache.db"):
        """캐시 관리자 초기화"""
        self.cache_dir = cache_dir
        self.db_path = db_path
        
        # 캐시 디렉토리 생성
        os.makedirs(cache_dir, exist_ok=True)
        
        # 캐시 데이터베이스 초기화
        self.init_cache_db()
        
        # 메모리 캐시 (URL 중복 확인용)
        self._url_cache: Set[str] = set()
        self._load_url_cache()
    
    def init_cache_db(self):
        """캐시 데이터베이스 초기화"""
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
        
        # 오래된 캐시 정리 (7일 이상)
        week_ago = time.time() - (7 * 24 * 3600)
        cursor.execute("DELETE FROM url_cache WHERE timestamp < ?", (week_ago,))
        cursor.execute("DELETE FROM html_cache WHERE timestamp < ?", (week_ago,))
        
        conn.commit()
        conn.close()
    
    def _load_url_cache(self):
        """URL 캐시를 메모리로 로드"""
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
        """URL 해시 생성"""
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def is_url_crawled(self, url: str) -> bool:
        """URL이 이미 크롤링되었는지 확인 (메모리 캐시 사용)"""
        return url in self._url_cache
    
    def mark_url_crawled(self, url: str, success: bool = True):
        """URL을 크롤링된 것으로 표시"""
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
        
        # 메모리 캐시 업데이트
        if success:
            self._url_cache.add(url)
    
    def get_cached_html(self, url: str, max_age_hours: int = 48) -> Optional[str]:
        """캐시된 HTML 가져오기"""
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
        """HTML 캐싱"""
        if not html or len(html) < 100:  # 너무 짧은 HTML은 캐시하지 않음
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
        """캐시 통계 정보"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # URL 캐시 통계
        cursor.execute("SELECT COUNT(*) FROM url_cache WHERE success = 1")
        successful_urls = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM url_cache WHERE success = 0")
        failed_urls = cursor.fetchone()[0]
        
        # HTML 캐시 통계
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
        """캐시 정리"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if older_than_hours:
            # 특정 시간보다 오래된 캐시만 정리
            cutoff_time = time.time() - (older_than_hours * 3600)
            cursor.execute("DELETE FROM url_cache WHERE timestamp < ?", (cutoff_time,))
            cursor.execute("DELETE FROM html_cache WHERE timestamp < ?", (cutoff_time,))
            print(f"{older_than_hours}시간 이상 된 캐시 정리됨")
        else:
            # 모든 캐시 정리
            cursor.execute("DELETE FROM url_cache")
            cursor.execute("DELETE FROM html_cache")
            print("모든 캐시 정리됨")
        
        conn.commit()
        conn.close()
        
        # 메모리 캐시도 정리
        self._url_cache.clear()
        self._load_url_cache()


# 전역 캐시 관리자 인스턴스
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """전역 캐시 관리자 인스턴스 가져오기"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

# 데코이터: URL 중복 확인
def skip_if_crawled(func):
    """이미 크롤링된 URL이면 건너뛰는 데코이터"""
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
        
        # 성공한 경우에만 캐시에 표시
        if result.get('success'):
            cache.mark_url_crawled(url, True)
        else:
            cache.mark_url_crawled(url, False)
        
        return result
    
    return wrapper

# LRU 캐시: 자주 사용하는 HTML 캐싱
@lru_cache(maxsize=2000)
def get_cached_content(url_hash: str) -> Optional[str]:
    """LRU 캐시에서 HTML 가져오기"""
    cache = get_cache_manager()
    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT html FROM html_cache WHERE url_hash = ?", (url_hash,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None