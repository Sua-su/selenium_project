import sys
import tkinter as tk
from gui import CrawlerGUI


def main():
    try:
        root = tk.Tk()
        app = CrawlerGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"애플리케이션 실행 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
    