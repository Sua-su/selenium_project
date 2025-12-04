"""
메인 실행 파일
GUI 애플리케이션을 시작합니다.
"""

import sys
import tkinter as tk
from gui import CrawlerGUI


def main():
    """메인 함수"""
    try:
        # Tkinter 루트 윈도우 생성
        root = tk.Tk()
        
        # GUI 애플리케이션 초기화
        app = CrawlerGUI(root)
        
        # 이벤트 루프 시작
        root.mainloop()
        
    except Exception as e:
        print(f"애플리케이션 실행 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
    