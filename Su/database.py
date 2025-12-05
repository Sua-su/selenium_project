import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import sys
import os


class DatabaseManager:

    
    def __init__(self, db_path: str = "articles.db"):
        

        if getattr(sys, 'frozen', False): #했는데 exe오류남 데이터베이스 캐시는 정상작동
            base_path = os.path.dirname(sys.executable)
            self.db_path = os.path.join(base_path, db_path)
        else:
            self.db_path = db_path
        
        print(f"데이터베이스 경로: {self.db_path}")
        self.init_database()
    
    def init_database(self):
        """데이터베이스 테이블 초기화 및 인덱스 생성"""
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_url ON articles(url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON articles(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_collected_date ON articles(collected_date)')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def insert_article(self, url: str, title: str = None, content: str = None,
                      author: str = None, published_date: str = None,
                      source: str = None, rss_feed: str = None, tags: str = None) -> bool:
        """
        단일 기사 데이터 삽입
        
        참고용 
            url: 기사 URL (필수)
            title: 기사 제목
            content: 기사 본문
            author: 작성자
            published_date: 발행일
            source: 출처
            rss_feed: RSS URL
            tags: 태그
            bool: 삽입 성공 여부
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
            return True
            
        except sqlite3.IntegrityError:
            return False #추가해서 실패시 다운 막음;
        except Exception as e:
            print(f"데이터 삽입 오류: {str(e)}")
            return False
        finally:
            conn.close()
    
    def batch_insert_articles(self, articles: list) -> int:
        """
        여러 기사 한번에 삽입
        """
        if not articles:
            return 0
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        collected_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        data_to_insert = []
        for article in articles:
            data_to_insert.append((
                article.get('url', ''),
                article.get('title', ''),
                article.get('content', ''),
                article.get('author', ''),
                article.get('published_date', ''),
                collected_date,
                article.get('source', ''),
                article.get('rss_feed', ''),
                article.get('tags', '')
            ))
        
        try:#중복무시 하고 대량 
            cursor.executemany('''
                INSERT OR IGNORE INTO articles 
                (url, title, content, author, published_date, collected_date, source, rss_feed, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', data_to_insert)
            
            conn.commit()
            return cursor.rowcount
            
        except Exception as e:
            print(f"배치 데이터 삽입 오류: {str(e)}")
            return 0
        finally:
            conn.close()
    
    def get_all_articles(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        모든 기사 조회
        
        Args:
            limit: 최대 조회 개수
            offset: 시작 위치
            
        Returns:
            List[Dict]: 기사 리스트
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
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'content': row[3],
                'author': row[4],
                'published_date': row[5],
                'collected_date': row[6],
                'source': row[7],
                'rss_feed': row[8],
                'tags': row[9]
            })
        
        conn.close()
        return articles
    
    def get_article_by_id(self, article_id: int) -> Optional[Dict]:
        """
        ID로 특정 기사 조회
        
        Args:
            article_id: 기사 ID
            
        Returns:
            Optional[Dict]: 기사 데이터 또는 None
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
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'content': row[3],
                'author': row[4],
                'published_date': row[5],
                'collected_date': row[6],
                'source': row[7],
                'rss_feed': row[8],
                'tags': row[9]
            }
        
        return None
    
    def search_articles(self, keyword: str, limit: int = 100) -> List[Dict]:
        """
        키워드로 기사 검색 (제목 및 본문)
        
        Args:
            keyword: 검색 키워드
            limit: 최대 결과 개수
            
        Returns:
            List[Dict]: 검색된 기사 리스트
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        search_pattern = f"%{keyword}%"
        cursor.execute('''
            SELECT id, url, title, content, author, published_date, 
                   collected_date, source, rss_feed, tags
            FROM articles 
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY collected_date DESC
            LIMIT ?
        ''', (search_pattern, search_pattern, limit))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'content': row[3],
                'author': row[4],
                'published_date': row[5],
                'collected_date': row[6],
                'source': row[7],
                'rss_feed': row[8],
                'tags': row[9]
            })
        
        conn.close()
        return articles
    
    def get_statistics(self) -> Dict:
        """
        데이터베이스 통계 정보 조회
        
        Returns:
            Dict: 총 개수, 최근 수집일, 상위 출처 등
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(collected_date) FROM articles")
        last_collected = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT source, COUNT(*) as count
            FROM articles 
            WHERE source IS NOT NULL AND source != ''
            GROUP BY source
            ORDER BY count DESC     
            LIMIT 10
        ''')
        top_sources = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_count': total_count,
            'last_collected': last_collected,
            'top_sources': top_sources
        }
    
    def delete_article(self, article_id: int) -> bool:
        """
        특정 기사 삭제
        
        Args:
            article_id: 삭제할 기사 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"기사 삭제 오류: {str(e)}")
            return False
        finally:
            conn.close()
    
    def clear_all_articles(self):
        """모든 기사 데이터 삭제"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM articles")
            conn.commit()
        except Exception as e:
            print(f"전체 삭제 오류: {str(e)}")
        finally:
            conn.close()
    
    def get_articles_by_source(self, source: str, limit: int = 50) -> List[Dict]:
        """
        특정 출처의 기사 조회
        
        Args:
            source: 출처명
            limit: 최대 개수
            
        Returns:
            List[Dict]: 기사 리스트
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, url, title, content, author, published_date, 
                   collected_date, source, rss_feed, tags
            FROM articles 
            WHERE source = ?
            ORDER BY collected_date DESC
            LIMIT ?
        ''', (source, limit))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'content': row[3],
                'author': row[4],
                'published_date': row[5],
                'collected_date': row[6],
                'source': row[7],
                'rss_feed': row[8],
                'tags': row[9]
            })
        
        conn.close()
        return articles
    
    def get_articles_by_date_range(self, start_date: str, end_date: str, limit: int = 100) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, url, title, content, author, published_date, 
                   collected_date, source, rss_feed, tags
            FROM articles 
            WHERE DATE(collected_date) BETWEEN ? AND ?
            ORDER BY collected_date DESC
            LIMIT ?
        ''', (start_date, end_date, limit))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'content': row[3],
                'author': row[4],
                'published_date': row[5],
                'collected_date': row[6],
                'source': row[7],
                'rss_feed': row[8],
                'tags': row[9]
            })
        
        conn.close()
        return articles