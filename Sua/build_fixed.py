# -*- coding: utf-8 -*-
"""
PyInstaller 빌드 스크립트 (수정版)
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
        '--name=RSS_Crawler_Fixed',
        '--onefile',  # 단일 실행 파일
        '--windowed' if sys.platform != 'linux' else '--console',  # GUI 모드 (Linux는 콘솔)
        '--log-level=DEBUG',  # 상세한 빌드 로그
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
        
        # 필수 라이브러리 hidden imports (추가)
        '--hidden-import=trafilatura',
        '--hidden-import=trafilatura.core',
        '--hidden-import=trafilatura.utils',
        '--hidden-import=trafilatura.metadata',
        '--hidden-import=trafilatura.settings',
        '--hidden-import=trafilatura.xpaths',
        '--hidden-import=feedparser',
        '--hidden-import=selenium',
        '--hidden-import=webdriver_manager',
        '--hidden-import=requests',
        '--hidden-import=bs4',
        '--hidden-import=lxml',
        '--hidden-import=lxml.etree',
        '--hidden-import=lxml.html',
        '--hidden-import=lxml.cssselect',
        '--hidden-import=sqlite3',
        '--hidden-import=concurrent.futures',
        '--hidden-import=threading',
        '--hidden-import=queue',
        '--hidden-import=urllib3',
        '--hidden-import=certifi',
        '--hidden-import=charset_normalizer',
        '--hidden-import=cchardet',
        '--hidden-import=html5lib',
        
        # 데이터 파일 포함 (전부)
        '--collect-data=certifi',
        '--collect-data=trafilatura',
        '--collect-data=charset_normalizer',
        '--collect-data=lxml',
        '--collect-all=certifi',
        
        # 모듈 수집
        '--collect-submodules=trafilatura',
        '--collect-submodules=feedparser',
        '--collect-submodules=requests',
        
        # 불필요한 모듈 제외
        '--exclude-module=matplotlib',
        '--exclude-module=PIL',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=jupyter',
        '--exclude-module=IPython',
    ]
    
    # 플랫폼별 추가 옵션
    if sys.platform == 'linux':
        options.append('--strip')  # Linux에서만 strip 사용
    
    # Windows용 추가 옵션
    elif sys.platform == 'win32':
        options.append('--noupx')  # UPX 압축 사용 안함 (안정성 증가)
        
        # 아이콘 파일이 있으면 추가
        icon_path = os.path.join(current_dir, 'icon.ico')
        if os.path.exists(icon_path):
            options.append(f'--icon={icon_path}')
    
    print("=" * 60)
    print("RSS Crawler 빌드 시작 (수정版)...")
    print("=" * 60)
    print(f"플랫폼: {sys.platform}")
    print(f"메인 스크립트: {main_script}")
    print("=" * 60)
    
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