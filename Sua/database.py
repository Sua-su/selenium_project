"""
SQLite 데이터베이스 관리 모듈
크롤링된 기사 데이터를 저장하고 관리합니다.
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import os


class DatabaseManager:
    """SQLite 데이터베이스 관리 클래스"""
    
    def __init__(self, db_name: str = "articles.db"):
        """데이터베이스 초기화
        
        Args:
            db_name: 데이터베이스 파일명
        """
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """데이터베이스 테이블 초기화"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                content TEXT,
                author TEXT,
                published_date TEXT,
                collected_date TEXT NOT NULL,
                source TEXT,
                rss_feed TEXT,
                tags TEXT,
                UNIQUE(url)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_article(self, url: str, title: str = None, content: str = None,
                      author: str = None, published_date: str = None,
                      source: str = None, rss_feed: str = None, tags: str = None) -> bool:
        """새로운 기사 저장
        
        Args:
            url: 기사 URL (필수)
            title: 기사 제목
            content: 기사 본문
            author: 작성자
            published_date: 게시일
            source: 출처
            rss_feed: RSS 피드 URL
            tags: 태그 (쉼표로 구분)
            
        Returns:
            저장 성공 여부
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        collected_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            cursor.execute('''
                INSERT INTO articles 
                (url, title, content, author, published_date, collected_date, source, rss_feed, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (url, title, content, author, published_date, collected_date, source, rss_feed, tags))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # URL이 이미 존재하는 경우
            conn.close()
            return False
    
    def get_all_articles(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """모든 기사 조회
        
        Args:
            limit: 조회할 최대 개수
            offset: 시작 위치
            
        Returns:
            기사 리스트
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, url, title, content, author, published_date, 
                   collected_date, source, rss_feed, tags
            FROM articles
            ORDER BY collected_date DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        columns = [description[0] for description in cursor.description]
        articles = []
        
        for row in cursor.fetchall():
            article = dict(zip(columns, row))
            articles.append(article)
        
        conn.close()
        return articles
    
    def search_articles(self, keyword: str, limit: int = 100) -> List[Dict]:
        """키워드로 기사 검색
        
        Args:
            keyword: 검색 키워드
            limit: 조회할 최대 개수
            
        Returns:
            검색 결과 리스트
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        search_pattern = f"%{keyword}%"
        
        cursor.execute('''
            SELECT id, url, title, content, author, published_date, 
                   collected_date, source, rss_feed, tags
            FROM articles
            WHERE title LIKE ? OR content LIKE ? OR source LIKE ? OR tags LIKE ?
            ORDER BY collected_date DESC
            LIMIT ?
        ''', (search_pattern, search_pattern, search_pattern, search_pattern, limit))
        
        columns = [description[0] for description in cursor.description]
        articles = []
        
        for row in cursor.fetchall():
            article = dict(zip(columns, row))
            articles.append(article)
        
        conn.close()
        return articles
    
    def get_article_by_id(self, article_id: int) -> Optional[Dict]:
        """ID로 특정 기사 조회
        
        Args:
            article_id: 기사 ID
            
        Returns:
            기사 정보 또는 None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, url, title, content, author, published_date, 
                   collected_date, source, rss_feed, tags
            FROM articles
            WHERE id = ?
        ''', (article_id,))
        
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            article = dict(zip(columns, row))
            conn.close()
            return article
        
        conn.close()
        return None
    
    def delete_article(self, article_id: int) -> bool:
        """기사 삭제
        
        Args:
            article_id: 삭제할 기사 ID
            
        Returns:
            삭제 성공 여부
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM articles WHERE id = ?', (article_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def update_article(self, article_id: int, **kwargs) -> bool:
        """기사 정보 업데이트
        
        Args:
            article_id: 업데이트할 기사 ID
            **kwargs: 업데이트할 필드들
            
        Returns:
            업데이트 성공 여부
        """
        if not kwargs:
            return False
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        values.append(article_id)
        
        cursor.execute(f'''
            UPDATE articles
            SET {set_clause}
            WHERE id = ?
        ''', values)
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return updated
    
    def get_statistics(self) -> Dict:
        """데이터베이스 통계 정보
        
        Returns:
            통계 정보 딕셔너리
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 총 기사 수
        cursor.execute('SELECT COUNT(*) FROM articles')
        total_count = cursor.fetchone()[0]
        
        # 출처별 통계
        cursor.execute('''
            SELECT source, COUNT(*) as count
            FROM articles
            WHERE source IS NOT NULL
            GROUP BY source
            ORDER BY count DESC
            LIMIT 10
        ''')
        sources = cursor.fetchall()
        
        # 최근 수집일
        cursor.execute('SELECT MAX(collected_date) FROM articles')
        last_collected = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_count': total_count,
            'top_sources': sources,
            'last_collected': last_collected
        }
    
    def clear_all_articles(self) -> bool:
        """모든 기사 삭제
        
        Returns:
            삭제 성공 여부
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM articles')
        
        conn.commit()
        conn.close()
        
        return True
