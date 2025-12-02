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
        '--windowed',  # 콘솔 창 숨김 (GUI 애플리케이션)
        '--clean',
        '--noconfirm',
        f'--distpath={os.path.join(current_dir, "dist")}',
        f'--workpath={os.path.join(current_dir, "build")}',
        f'--specpath={current_dir}',
        # 데이터 파일 포함 (필요한 경우)
        # '--add-data=data;data',  # Windows
        # '--add-data=data:data',  # macOS/Linux
    ]
    
    # macOS용 추가 옵션
    if sys.platform == 'darwin':
        options.extend([
            '--icon=NONE',  # 아이콘 파일이 있다면 경로 지정
        ])
    
    # Windows용 추가 옵션
    elif sys.platform == 'win32':
        options.extend([
            '--icon=NONE',  # 아이콘 파일이 있다면 경로 지정
        ])
    
    print("=" * 60)
    print("RSS Crawler 빌드 시작...")
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
