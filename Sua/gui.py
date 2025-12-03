"""
GUI 애플리케이션 모듈
tkinter 기반 사용자 인터페이스
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from database import DatabaseManager
from rss_parser import RSSParser, SAMPLE_RSS_FEEDS
from hybrid_crawler import HybridCrawler


class CrawlerGUI:
    """크롤러 GUI 메인 클래스"""
    
    def __init__(self, root):
        """GUI 초기화
        
        Args:
            root: tkinter 루트 윈도우
        """
        self.root = root
        self.root.title("RSS 기사 크롤러")
        self.root.geometry("1200x800")
        
        # 모듈 초기화
        self.db = DatabaseManager()
        self.rss_parser = RSSParser()
        self.crawler = None
        
        # 크롤링 진행 상태
        self.is_crawling = False
        
        # GUI 구성
        self.setup_ui()
        
        # 초기 데이터 로드
        self.load_articles()
    
    def setup_ui(self):
        """UI 구성"""
        # 탭 컨트롤 생성
        self.tab_control = ttk.Notebook(self.root)
        
        # 탭 1: 크롤링
        self.tab_crawl = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_crawl, text="크롤링")
        
        # 탭 2: 데이터 확인
        self.tab_view = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_view, text="데이터 확인")
        
        # 탭 3: 데이터 관리
        self.tab_manage = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_manage, text="데이터 관리")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # 각 탭 설정
        self.setup_crawl_tab()
        self.setup_view_tab()
        self.setup_manage_tab()
    
    def setup_crawl_tab(self):
        """크롤링 탭 구성"""
        # RSS 피드 섹션
        rss_frame = ttk.LabelFrame(self.tab_crawl, text="RSS 피드 설정", padding=10)
        rss_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(rss_frame, text="RSS URL:").pack(anchor="w")
        self.rss_url_entry = ttk.Entry(rss_frame, width=80)
        self.rss_url_entry.pack(fill="x", pady=5)
        self.rss_url_entry.insert(0, SAMPLE_RSS_FEEDS[0])
        
        rss_btn_frame = ttk.Frame(rss_frame)
        rss_btn_frame.pack(fill="x")
        
        ttk.Button(rss_btn_frame, text="RSS 파싱", command=self.parse_rss).pack(side="left", padx=5)
        ttk.Button(rss_btn_frame, text="샘플 피드 불러오기", command=self.load_sample_feeds).pack(side="left")
        
        # URL 리스트 섹션
        url_frame = ttk.LabelFrame(self.tab_crawl, text="크롤링 URL 목록", padding=10)
        url_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # URL 리스트박스와 스크롤바
        list_frame = ttk.Frame(url_frame)
        list_frame.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.url_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode="extended")
        self.url_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.url_listbox.yview)
        
        # URL 직접 추가
        add_frame = ttk.Frame(url_frame)
        add_frame.pack(fill="x", pady=5)
        
        self.manual_url_entry = ttk.Entry(add_frame)
        self.manual_url_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(add_frame, text="URL 추가", command=self.add_manual_url).pack(side="left", padx=2)
        ttk.Button(add_frame, text="선택 삭제", command=self.remove_selected_urls).pack(side="left", padx=2)
        ttk.Button(add_frame, text="전체 삭제", command=self.clear_urls).pack(side="left", padx=2)
        
        # 크롤링 실행 섹션
        crawl_frame = ttk.LabelFrame(self.tab_crawl, text="크롤링 실행", padding=10)
        crawl_frame.pack(fill="x", padx=10, pady=5)
        
        options_frame = ttk.Frame(crawl_frame)
        options_frame.pack(fill="x", pady=5)
        
        ttk.Label(options_frame, text="대기 시간(초):").pack(side="left")
        self.wait_time_var = tk.StringVar(value="1")
        ttk.Entry(options_frame, textvariable=self.wait_time_var, width=10).pack(side="left", padx=5)
        
        ttk.Label(options_frame, text="요청 간격(초):").pack(side="left", padx=(20, 0))
        self.delay_var = tk.StringVar(value="0")
        ttk.Entry(options_frame, textvariable=self.delay_var, width=10).pack(side="left", padx=5)
        
        self.crawl_btn = ttk.Button(crawl_frame, text="크롤링 시작", command=self.start_crawling)
        self.crawl_btn.pack(pady=5)
        
        # 진행 상황
        self.progress_label = ttk.Label(crawl_frame, text="대기 중...")
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(crawl_frame, mode="determinate")
        self.progress_bar.pack(fill="x", pady=5)
        
        # 로그
        log_frame = ttk.LabelFrame(self.tab_crawl, text="실행 로그", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8)
        self.log_text.pack(fill="both", expand=True)
    
    def setup_view_tab(self):
        """데이터 확인 탭 구성"""
        # 검색 섹션
        search_frame = ttk.Frame(self.tab_view, padding=10)
        search_frame.pack(fill="x")
        
        ttk.Label(search_frame, text="검색:").pack(side="left")
        self.search_entry = ttk.Entry(search_frame, width=50)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_articles())
        
        ttk.Button(search_frame, text="검색", command=self.search_articles).pack(side="left", padx=2)
        ttk.Button(search_frame, text="전체보기", command=self.load_articles).pack(side="left", padx=2)
        ttk.Button(search_frame, text="새로고침", command=self.load_articles).pack(side="left", padx=2)
        
        # 기사 목록 (Treeview)
        list_frame = ttk.Frame(self.tab_view)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Treeview 생성
        columns = ("ID", "제목", "출처", "수집일")
        self.article_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", selectmode="browse")
        
        # 컬럼 설정
        self.article_tree.column("#0", width=0, stretch=False)
        self.article_tree.column("ID", width=50, anchor="center")
        self.article_tree.column("제목", width=500)
        self.article_tree.column("출처", width=200)
        self.article_tree.column("수집일", width=150, anchor="center")
        
        # 헤더 설정
        for col in columns:
            self.article_tree.heading(col, text=col)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.article_tree.yview)
        self.article_tree.configure(yscrollcommand=scrollbar.set)
        
        self.article_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 더블클릭으로 상세보기
        self.article_tree.bind("<Double-1>", self.show_article_detail)
        
        # 통계 정보
        stats_frame = ttk.LabelFrame(self.tab_view, text="통계", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="총 기사 수: 0")
        self.stats_label.pack()
    
    def setup_manage_tab(self):
        """데이터 관리 탭 구성"""
        # 통계 정보
        stats_frame = ttk.LabelFrame(self.tab_manage, text="데이터베이스 통계", padding=10)
        stats_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=15)
        self.stats_text.pack(fill="both", expand=True)
        
        ttk.Button(stats_frame, text="통계 새로고침", command=self.update_statistics).pack(pady=5)
        
        # 데이터 관리
        manage_frame = ttk.LabelFrame(self.tab_manage, text="데이터 관리", padding=10)
        manage_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(manage_frame, text="기사 ID:").pack(side="left")
        self.delete_id_entry = ttk.Entry(manage_frame, width=20)
        self.delete_id_entry.pack(side="left", padx=5)
        
        ttk.Button(manage_frame, text="기사 삭제", command=self.delete_article).pack(side="left", padx=5)
        ttk.Button(manage_frame, text="전체 삭제", command=self.clear_all_data).pack(side="left", padx=5)
        
        # 초기 통계 로드
        self.update_statistics()
    
    # === 크롤링 탭 메서드 ===
    
    def parse_rss(self):
        """RSS 파싱"""
        rss_url = self.rss_url_entry.get().strip()
        if not rss_url:
            messagebox.showwarning("경고", "RSS URL을 입력하세요.")
            return
        
        self.log("RSS 파싱 시작...")
        
        def parse_thread():
            try:
                articles = self.rss_parser.parse_feed(rss_url)
                
                if articles:
                    for article in articles:
                        self.root.after(0, lambda url=article['url']: self.url_listbox.insert(tk.END, url))
                    self.root.after(0, lambda count=len(articles): self.log(f"RSS 파싱 완료: {count}개 URL 추가"))
                else:
                    self.root.after(0, lambda: self.log("RSS 파싱 실패 또는 기사 없음"))
            except Exception as e:
                self.root.after(0, lambda e=e: self.log(f"RSS 파싱 오류: {str(e)}"))
        
        threading.Thread(target=parse_thread, daemon=True).start()
    
    def load_sample_feeds(self):
        """샘플 RSS 피드 불러오기"""
        self.log("샘플 피드 파싱 시작...")
        
        def load_thread():
            try:
                all_articles = self.rss_parser.parse_multiple_feeds(SAMPLE_RSS_FEEDS)
                
                if all_articles:
                    for article in all_articles:
                        self.root.after(0, lambda url=article['url']: self.url_listbox.insert(tk.END, url))
                    self.root.after(0, lambda count=len(all_articles): self.log(f"샘플 피드 파싱 완료: {count}개 URL 추가"))
                else:
                    self.root.after(0, lambda: self.log("샘플 피드 파싱 실패: 유효한 기사가 없거나 모든 피드에 접근할 수 없음"))
            except Exception as e:
                self.root.after(0, lambda e=e: self.log(f"샘플 피드 파싱 오류: {str(e)}"))
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def add_manual_url(self):
        """수동으로 URL 추가"""
        url = self.manual_url_entry.get().strip()
        if url:
            self.url_listbox.insert(tk.END, url)
            self.manual_url_entry.delete(0, tk.END)
            self.log(f"URL 추가: {url}")
    
    def remove_selected_urls(self):
        """선택된 URL 삭제"""
        selected = self.url_listbox.curselection()
        for index in reversed(selected):
            self.url_listbox.delete(index)
        self.log(f"{len(selected)}개 URL 삭제")
    
    def clear_urls(self):
        """모든 URL 삭제"""
        count = self.url_listbox.size()
        self.url_listbox.delete(0, tk.END)
        self.log(f"전체 URL 삭제: {count}개")
    
    def start_crawling(self):
        """크롤링 시작"""
        if self.is_crawling:
            messagebox.showinfo("알림", "이미 크롤링이 진행 중입니다.")
            return
        
        url_count = self.url_listbox.size()
        if url_count == 0:
            messagebox.showwarning("경고", "크롤링할 URL이 없습니다.")
            return
        
        urls = [self.url_listbox.get(i) for i in range(url_count)]
        
        try:
            wait_time = int(self.wait_time_var.get())
            delay = float(self.delay_var.get())
        except ValueError:
            messagebox.showerror("오류", "대기 시간과 요청 간격은 정수여야 합니다.")
            return
        
        self.is_crawling = True
        self.crawl_btn.config(state="disabled")
        self.progress_bar["maximum"] = url_count
        self.progress_bar["value"] = 0
        
        def crawl_thread():
            success_count = 0
            successful_articles = []  # 배치 저장을 위한 리스트
            
            try:
                # 병렬 처리를 위한 함수
                def crawl_single(url_info):
                    index, url = url_info
                    result = HybridCrawler(headless=True).crawl_article(url, wait_time)
                    return index, result
                
                # URL을 인덱스와 함께 묶음
                url_with_index = [(i, url) for i, url in enumerate(urls, 1)]
                
                # ThreadPoolExecutor로 병렬 처리 (최대 4개 워커로 조정)
                with ThreadPoolExecutor(max_workers=4) as executor:
                    # 모든 작업 제출
                    future_to_index = {
                        executor.submit(crawl_single, url_info): url_info[0] 
                        for url_info in url_with_index
                    }
                    
                    # 완료된 작업 순서로 처리
                    for future in as_completed(future_to_index):
                        index, result = future.result()
                        
                        # GUI 업데이트 (배치 업데이트로 성능 향상)
                        if index % 5 == 0 or index == url_count:  # 5개마다 또는 마지막에 업데이트
                            self.root.after(0, lambda i=index: self.progress_label.config(text=f"진행 중: {i}/{url_count}"))
                            self.root.after(0, lambda i=index, u=result['url']: self.log(f"[{i}/{url_count}] 크롤링: {u}"))
                        
                        if result.get('success'):
                            # 배치 저장을 위해 리스트에 추가
                            successful_articles.append({
                                'url': result['url'],
                                'title': result.get('title', ''),
                                'content': result.get('content', ''),
                                'author': result.get('author', ''),
                                'published_date': result.get('published_date', ''),
                                'source': result.get('source', ''),
                                'rss_feed': '',
                                'tags': ''
                            })
                            
                            success_count += 1
                            method = result.get('method', 'unknown')
                            title = result.get('title', 'No title')[:50]
                            self.root.after(0, lambda t=title, m=method: self.log(f"✓ {m}: {t}"))
                        else:
                            error = result.get('error', 'Unknown error')
                            method = result.get('method', 'unknown')
                            self.root.after(0, lambda e=error, m=method: self.log(f"✗ {m} 실패: {e}"))
                        
                        self.root.after(0, lambda i=index: self.progress_bar.config(value=i))
                
            except Exception as e:
                self.root.after(0, lambda e=e: self.log(f"크롤링 중 오류 발생: {str(e)}"))
                
            except Exception as e:
                self.root.after(0, lambda e=e: self.log(f"크롤링 중 오류 발생: {str(e)}"))
                
            finally:
                self.is_crawling = False
                self.root.after(0, lambda: self.crawl_btn.config(state="normal"))
                
                # 배치 저장
                if successful_articles:
                    batch_saved = self.db.batch_insert_articles(successful_articles)
                    self.root.after(0, lambda b=batch_saved: self.log(f"배치 저장 완료: {b}개 기사"))
                
                self.root.after(0, lambda s=success_count: self.progress_label.config(text=f"완료: {s}/{url_count}개 크롤링"))
                self.root.after(0, lambda s=success_count: self.log(f"크롤링 완료: 총 {s}개 기사 수집"))
                
                # 데이터 확인 탭 새로고침
                self.root.after(0, self.load_articles)
        
        threading.Thread(target=crawl_thread, daemon=True).start()
    
    def log(self, message):
        """로그 메시지 출력"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
    
    # === 데이터 확인 탭 메서드 ===
    
    def load_articles(self):
        """기사 목록 로드"""
        # 기존 항목 삭제
        for item in self.article_tree.get_children():
            self.article_tree.delete(item)
        
        # 데이터베이스에서 로드
        articles = self.db.get_all_articles(limit=1000)
        
        for article in articles:
            self.article_tree.insert("", tk.END, values=(
                article['id'],
                article['title'] or '제목 없음',
                article['source'] or '출처 없음',
                article['collected_date']
            ))
        
        # 통계 업데이트
        self.stats_label.config(text=f"총 기사 수: {len(articles)}")
    
    def search_articles(self):
        """기사 검색"""
        keyword = self.search_entry.get().strip()
        
        if not keyword:
            self.load_articles()
            return
        
        # 기존 항목 삭제
        for item in self.article_tree.get_children():
            self.article_tree.delete(item)
        
        # 검색
        articles = self.db.search_articles(keyword, limit=1000)
        
        for article in articles:
            self.article_tree.insert("", tk.END, values=(
                article['id'],
                article['title'] or '제목 없음',
                article['source'] or '출처 없음',
                article['collected_date']
            ))
        
        # 통계 업데이트
        self.stats_label.config(text=f"검색 결과: {len(articles)}개")
    
    def show_article_detail(self, event):
        """기사 상세보기"""
        selection = self.article_tree.selection()
        if not selection:
            return
        
        item = self.article_tree.item(selection[0])
        article_id = item['values'][0]
        
        article = self.db.get_article_by_id(article_id)
        if not article:
            messagebox.showerror("오류", "기사를 찾을 수 없습니다.")
            return
        
        # 상세보기 윈도우
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"기사 상세 - ID: {article_id}")
        detail_window.geometry("900x700")
        
        # 내용 표시
        text_widget = scrolledtext.ScrolledText(detail_window, wrap=tk.WORD)
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        content = f"""
제목: {article['title'] or '제목 없음'}
URL: {article['url']}
출처: {article['source'] or '출처 없음'}
작성자: {article['author'] or '작성자 없음'}
게시일: {article['published_date'] or '게시일 없음'}
수집일: {article['collected_date']}
태그: {article['tags'] or '태그 없음'}

{'='*80}

{article['content'] or '본문 없음'}
"""
        text_widget.insert(tk.END, content)
        text_widget.config(state="disabled")
    
    # === 데이터 관리 탭 메서드 ===
    
    def update_statistics(self):
        """통계 정보 업데이트"""
        stats = self.db.get_statistics()
        
        self.stats_text.delete(1.0, tk.END)
        
        stats_text = f"""
=== 데이터베이스 통계 ===

총 기사 수: {stats['total_count']}
최근 수집일: {stats['last_collected'] or '없음'}

출처별 통계 (상위 10개):
"""
        for source, count in stats['top_sources']:
            stats_text += f"  - {source}: {count}개\n"
        
        self.stats_text.insert(tk.END, stats_text)
    
    def delete_article(self):
        """기사 삭제"""
        article_id = self.delete_id_entry.get().strip()
        
        if not article_id:
            messagebox.showwarning("경고", "삭제할 기사 ID를 입력하세요.")
            return
        
        try:
            article_id = int(article_id)
        except ValueError:
            messagebox.showerror("오류", "ID는 숫자여야 합니다.")
            return
        
        if messagebox.askyesno("확인", f"ID {article_id} 기사를 삭제하시겠습니까?"):
            if self.db.delete_article(article_id):
                messagebox.showinfo("완료", "기사가 삭제되었습니다.")
                self.delete_id_entry.delete(0, tk.END)
                self.update_statistics()
                self.load_articles()
            else:
                messagebox.showerror("오류", "기사를 찾을 수 없습니다.")
    
    def clear_all_data(self):
        """모든 데이터 삭제"""
        if messagebox.askyesno("경고", "모든 데이터를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."):
            if messagebox.askyesno("재확인", "정말로 모든 데이터를 삭제하시겠습니까?"):
                self.db.clear_all_articles()
                messagebox.showinfo("완료", "모든 데이터가 삭제되었습니다.")
                self.update_statistics()
                self.load_articles()


def main():
    """GUI 애플리케이션 실행"""
    root = tk.Tk()
    app = CrawlerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
