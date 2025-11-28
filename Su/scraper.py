import sqlite3
import newspaper
from newspaper import Article
from urllib.parse import urlparse
import feedparser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def create_database():
    """데이터베이스와 테이블을 생성합니다."""
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    # User's request: title, text, link, company
    c.execute('DROP TABLE IF EXISTS articles')
    c.execute('''
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            text TEXT,
            url TEXT UNIQUE,
            company TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_company_from_url(url):
    """URL에서 도메인 이름을 추출하여 회사 이름으로 사용합니다."""
    try:
        parsed_url = urlparse(url)
        # 'www.example.com'에서 'example' 부분만 추출
        domain_parts = parsed_url.netloc.split('.')
        if len(domain_parts) > 2 and domain_parts[0] == 'www':
            return domain_parts[1]
        return domain_parts[0]
    except Exception as e:
        print(f"Could not parse company from URL {url}: {e}")
        return "Unknown"


def search_and_get_urls(query, max_urls=10):
    """Google News RSS 피드를 사용하여 뉴스 기사 URL을 가져옵니다."""
    print(f"Searching for '{query}' on Google News RSS feed...")
    
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    
    feed = feedparser.parse(rss_url)
    
    urls = []
    for entry in feed.entries:
        if len(urls) >= max_urls:
            break
        urls.append(entry.link)

    print(f"Extracted {len(urls)} unique URLs.")
    return urls


def scrape_and_save_articles(article_urls):
    """
    제공된 URL 목록에서 기사를 스크랩하고 데이터베이스에 저장합니다.
    """
    if not article_urls:
        print("No URLs provided to scrape.")
        return

    conn = sqlite3.connect('articles.db')
    c = conn.cursor()

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    
    try:
        service = Service(ChromeDriverManager().install())
    except Exception as e:
        print(f"Error setting up webdriver: {e}")
        return

    for url in article_urls:
        driver = None
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)
            time.sleep(2) # Allow for redirects
            final_url = driver.current_url
            driver.quit() # Close the driver after getting the URL
            
            article = Article(final_url, language='ko')
            article.download()
            article.parse()

            title = article.title
            text = article.text

            if not title or not text:
                print(f"Skipping article with no title or text: {final_url}")
                continue

            company = get_company_from_url(final_url)
            print(f"Scraping: '{title}' from {company}")

            # Insert into database, ignore if URL is already present
            c.execute('''
                INSERT OR IGNORE INTO articles (title, text, url, company)
                VALUES (?, ?, ?, ?)
            ''', (title, text, final_url, company))

        except Exception as e:
            print(f"Error scraping {url}: {e}")
        finally:
            if driver:
                driver.quit()

    conn.commit()
    conn.close()

def get_articles_from_db():
    """데이터베이스에서 모든 기사를 가져와 출력합니다."""
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    # Fetch the new columns
    c.execute("SELECT title, text, url, company FROM articles")
    articles = c.fetchall()
    conn.close()

    print("\n--- Stored Articles ---")
    if not articles:
        print("No articles found in the database.")
        return
        
    for article in articles:
        print(f"Title: {article[0]}")
        print(f"Company: {article[3]}")
        print(f"URL: {article[2]}")
        # Print only the first 150 characters of the text for brevity
        print(f"Text: {article[1][:150]}...")
        print("-" * 20)

if __name__ == '__main__':
    # 검색할 키워드
    SEARCH_KEYWORD = "반도체"
    
    # 1. 데이터베이스 설정
    create_database()

    # 2. RSS 피드로 "반도체" 검색 및 URL 수집
    urls_to_scrape = search_and_get_urls(SEARCH_KEYWORD, max_urls=5)

    # 3. Newspaper3k로 기사 스크랩 및 저장
    if urls_to_scrape:
        scrape_and_save_articles(urls_to_scrape)
        
        # 4. 저장된 데이터 확인
        get_articles_from_db()
    else:
        print("Could not retrieve any URLs. Halting execution.")