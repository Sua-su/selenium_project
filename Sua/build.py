# -*- coding: utf-8 -*-
"""
PyInstaller 빌드 스크립트
실행 파일(.exe 또는 .app)을 생성합니다.
"""

import PyInstaller.__main__
import os
import sys


def build_executable():
    """실행 파일 빌드"""
    
    # 현재 스크립트 디렉토리
    current_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(current_dir, 'main.py')
    
    # PyInstaller 옵션
    options = [
        main_script,
        '--name=RSS_Crawler',
        '--onefile',  # 단일 실행 파일
        '--windowed' if sys.platform != 'linux' else '--console',  # GUI 모드 (Linux는 콘솔)
        '--log-level=INFO',  # 간단한 빌드 로그
        '--clean',
        '--noconfirm',
        '--optimize=2',  # 최적화 레벨
        f'--distpath={os.path.join(current_dir, "dist")}',
        f'--workpath={os.path.join(current_dir, "build")}',
        f'--specpath={current_dir}',
        # GUI 관련 hidden imports
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.scrolledtext',
        # 필수 라이브러리 hidden imports
        '--hidden-import=trafilatura',
        '--hidden-import=trafilatura.core',
        '--hidden-import=trafilatura.utils',
        '--hidden-import=trafilatura.metadata',
        '--hidden-import=trafilatura.settings',
        '--hidden-import=feedparser',
        '--hidden-import=selenium',
        '--hidden-import=selenium.webdriver',
        '--hidden-import=selenium.webdriver.chrome',
        '--hidden-import=selenium.webdriver.chrome.service',
        '--hidden-import=selenium.webdriver.chrome.options',
        '--hidden-import=selenium.webdriver.common.by',
        '--hidden-import=selenium.webdriver.support.ui',
        '--hidden-import=selenium.webdriver.support.expected_conditions',
        '--hidden-import=webdriver_manager',
        '--hidden-import=webdriver_manager.chrome',
        '--hidden-import=webdriver_manager.core',
        '--hidden-import=requests',
        '--hidden-import=bs4',
        '--hidden-import=lxml',
        '--hidden-import=lxml.etree',
        '--hidden-import=lxml.html',
        '--hidden-import=sqlite3',
        '--hidden-import=concurrent.futures',
        '--hidden-import=threading',
        '--hidden-import=queue',
        # 데이터 파일 포함
        '--collect-data=certifi',
        '--collect-data=trafilatura',
        '--collect-data=charset_normalizer',
        '--collect-data=urllib3',
        '--collect-data=requests',
        '--collect-data=selenium',
        '--collect-all=webdriver_manager',
        # 모듈 전체 수집
        '--collect-submodules=selenium',
        '--collect-submodules=webdriver_manager',
        '--exclude-module=matplotlib',  # 불필요한 모듈 제외
        '--exclude-module=PIL',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
    ]
    
    # 플랫폼별 추가 옵션
    if sys.platform == 'linux':
        options.append('--strip')  # Linux에서만 strip 사용
    
    
    # macOS용 추가 옵션
    if sys.platform == 'darwin':
        pass

    # Windows용 추가 옵션
    elif sys.platform == 'win32':
        options.append('--noupx')  # UPX 압축 사용 안함 (안정성 증가)
        
        # ChromeDriver 번들링을 위한 추가 옵션 (파일이 있는 경우에만)
        chromedriver_path = os.path.join(current_dir, 'chromedriver.exe')
        if os.path.exists(chromedriver_path):
            options.append(f'--add-binary={chromedriver_path};.')  # chromedriver.exe를 같은 디렉토리에 포함
            print(f"ChromeDriver 번들링: {chromedriver_path}")
        else:
            print("ChromeDriver 파일을 찾을 수 없습니다. webdriver_manager가 자동으로 다운로드합니다.")
        
        # Chrome 설치 경로 추가
        chrome_path = 'C:\\Program Files\\Google\\Chrome\\Application'
        if os.path.exists(chrome_path):
            options.append(f'--paths={chrome_path}')
            print(f"Chrome 경로 추가: {chrome_path}")
        
        # 아이콘 파일이 있으면 추가
        icon_path = os.path.join(current_dir, 'icon.ico')
        if os.path.exists(icon_path):
            options.append(f'--icon={icon_path}')
    
    print("=" * 60)
    print("RSS Crawler 빌드 시작...")
    print("=" * 60)
    print(f"플랫폼: {sys.platform}")
    print(f"메인 스크립트: {main_script}")
    print("=" * 60)
    
    # 빌드 전 정리
    try:
        import shutil
        import subprocess
        
        # 프로세스 종료
        try:
            subprocess.run(['taskkill', '/f', '/im', 'RSS_Crawler.exe'], 
                         capture_output=True, text=True, check=False)
        except:
            pass
            
        # 폴더 정리
        for folder in ['dist', 'build']:
            folder_path = os.path.join(current_dir, folder)
            if os.path.exists(folder_path):
                print(f"기존 {folder} 폴더 정리...")
                shutil.rmtree(folder_path, ignore_errors=True)
                
    except Exception as e:
        print(f"정리 중 경고: {str(e)}")
    
    try:
        # PyInstaller 실행
        PyInstaller.__main__.run(options)
        
        print("\n" + "=" * 60)
        print("빌드 완료!")
        print(f"실행 파일 위치: {os.path.join(current_dir, 'dist')}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n빌드 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    build_executable()
