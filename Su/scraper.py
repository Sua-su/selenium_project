import sqlite3
import newspaper
from newspaper import Article

def create_database():
    """데이터베이스와 테이블을 생성합니다."""
    conn = sqlite3.connect('Su/articles.db')
    c = conn.cursor()
    # 기존 테이블이 있으면 삭제하여 스키마를 변경합니다.
    c.execute('DROP TABLE IF EXISTS articles')
    c.execute('''
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            authors TEXT,
            publish_date TEXT,
            text TEXT,
            url TEXT,
            keywords TEXT,
            summary TEXT
        )
    ''')
    conn.commit()
    conn.close()

def scrape_and_save_articles():
    """
    뉴스 소스에서 기사를 스크랩하고 데이터베이스에 저장합니다.
    """
    print("Building news source...")
    paper = newspaper.build('http://www.cnn.com', memoize_articles=False, language='en')
    
    conn = sqlite3.connect('Su/articles.db')
    c = conn.cursor()

    article_count = 0
    for article_url in paper.article_urls():
        if article_count >= 3:
            break
        
        try:
            article = Article(article_url)
            article.download()
            article.parse()
            article.nlp()

            title = article.title
            authors = ', '.join(article.authors)
            publish_date = str(article.publish_date)
            text = article.text
            keywords = ', '.join(article.keywords)
            summary = article.summary

            if not title or not text:
                print(f"Skipping article with no title or text: {article_url}")
                continue

            print(f"Scraping: {title}")

            c.execute('''
                INSERT INTO articles (title, authors, publish_date, text, url, keywords, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, authors, publish_date, text, article_url, keywords, summary))
            
            article_count += 1

        except Exception as e:
            print(f"Error scraping {article_url}: {e}")

    conn.commit()
    conn.close()

def get_articles_from_db():
    """데이터베이스에서 모든 기사를 가져와 출력합니다."""
    conn = sqlite3.connect('Su/articles.db')
    c = conn.cursor()
    c.execute("SELECT title, authors, publish_date, keywords, summary FROM articles")
    articles = c.fetchall()
    conn.close()

    print("\n--- Stored Articles ---")
    for article in articles:
        print(f"Title: {article[0]}")
        print(f"Authors: {article[1]}")
        print(f"Publish Date: {article[2]}")
        print(f"Keywords: {article[3]}")
        print(f"Summary: {article[4]}")
        print("-" * 20)

if __name__ == '__main__':
    # 데이터베이스 설정
    create_database()

    # 스크랩 및 저장 실행
    scrape_and_save_articles()

    # 저장된 데이터 확인
    get_articles_from_db()