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
        '--windowed',  
        '--clean',
        '--noconfirm',
        f'--distpath={os.path.join(current_dir, "dist")}',
        f'--workpath={os.path.join(current_dir, "build")}',
        f'--specpath={current_dir}',
        # 필수 모듈 명시적 포함
        '--hidden-import=selenium',
        '--hidden-import=selenium.webdriver',
        '--hidden-import=selenium.webdriver.chrome.service',
        '--hidden-import=selenium.webdriver.chrome.options',
        '--hidden-import=webdriver_manager',
        '--hidden-import=webdriver_manager.chrome',
        '--hidden-import=trafilatura',
        '--hidden-import=feedparser',
        '--hidden-import=requests',
        '--hidden-import=urllib3',
        '--hidden-import=certifi',
        '--hidden-import=llama_cpp',
        # SSL 인증서 파일 포함
        '--collect-all=certifi',
        '--collect-all=selenium',
        '--collect-all=llama_cpp',
        # 데이터 파일 수집
        '--copy-metadata=selenium',
        '--copy-metadata=trafilatura',
        # 요약 모델 파일(GGUF) 포함
        f'--add-data={os.path.join(current_dir, "models")}{os.pathsep}models',
    ]
    
    
    # macOS용
    if sys.platform == 'darwin':
        pass
    
    # Windows용
    elif sys.platform == 'win32':
        pass
    
    print("=" * 60)
    print("RSS Crawler 빌드 시작...")
    print("=" * 60)
    print(f"플랫폼: {sys.platform}")
    print(f"메인 스크립트: {main_script}")
    print("=" * 60)
    
    try:
        # PyInstaller
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
