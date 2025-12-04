#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
빌드된 실행 파일 테스트 스크립트
"""

import sys
import os

def test_imports():
    """필수 모듈 임포트 테스트"""
    print("모듈 임포트 테스트 시작...")
    
    try:
        import tkinter as tk
        print("✓ tkinter")
    except Exception as e:
        print(f"✗ tkinter: {e}")
        
    try:
        import trafilatura
        print("✓ trafilatura")
    except Exception as e:
        print(f"✗ trafilatura: {e}")
        
    try:
        import feedparser
        print("✓ feedparser")
    except Exception as e:
        print(f"✗ feedparser: {e}")
        
    try:
        import requests
        print("✓ requests")
    except Exception as e:
        print(f"✗ requests: {e}")
        
    try:
        import bs4
        print("✓ bs4")
    except Exception as e:
        print(f"✗ bs4: {e}")
        
    try:
        import lxml
        print("✓ lxml")
    except Exception as e:
        print(f"✗ lxml: {e}")
        
    try:
        import sqlite3
        print("✓ sqlite3")
    except Exception as e:
        print(f"✗ sqlite3: {e}")
        
    try:
        import concurrent.futures
        print("✓ concurrent.futures")
    except Exception as e:
        print(f"✗ concurrent.futures: {e}")

def test_trafilatura():
    """trafilatura 기능 테스트"""
    print("\ntrafilatura 기능 테스트...")
    
    try:
        import trafilatura
        from trafilatura import fetch_url, extract
        
        # 간단한 테스트 URL
        test_url = "https://httpbin.org/html"
        print(f"테스트 URL: {test_url}")
        
        downloaded = fetch_url(test_url)
        if downloaded:
            result = extract(downloaded)
            if result:
                print("✓ trafilatura 추출 성공")
                print(f"추출된 텍스트 길이: {len(result)} 자")
            else:
                print("✗ trafilatura 추출 실패")
        else:
            print("✗ trafilatura 다운로드 실패")
            
    except Exception as e:
        print(f"✗ trafilatura 테스트 실패: {e}")

def main():
    """메인 함수"""
    print("=" * 50)
    print("RSS Crawler 빌드 테스트")
    print("=" * 50)
    
    # 현재 환경 정보
    print(f"Python 버전: {sys.version}")
    print(f"실행 파일: {sys.executable}")
    print(f"작업 디렉토리: {os.getcwd()}")
    print("=" * 50)
    
    # 모듈 임포트 테스트
    test_imports()
    
    # trafilatura 기능 테스트
    test_trafilatura()
    
    print("\n" + "=" * 50)
    print("테스트 완료")
    print("=" * 50)

if __name__ == "__main__":
    main()