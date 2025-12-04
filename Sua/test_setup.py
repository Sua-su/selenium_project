"""
환경 설정 테스트 스크립트
모든 패키지가 제대로 설치되었는지 확인합니다.
"""

import sys

def test_imports():
    """패키지 import 테스트"""
    print("=" * 60)
    print("패키지 import 테스트 시작...")
    print("=" * 60)
    
    packages = {
        'trafilatura': 'trafilatura',
        'selenium': 'selenium',
        'feedparser': 'feedparser',
        'webdriver_manager': 'webdriver-manager',
    }
    
    success_count = 0
    
    for module_name, package_name in packages.items():
        try:
            __import__(module_name)
            print(f"✓ {package_name}: 정상")
            success_count += 1
        except ImportError as e:
            print(f"✗ {package_name}: 실패 - {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"결과: {success_count}/{len(packages)} 패키지 정상")
    print("=" * 60)
    
    return success_count == len(packages)


def test_database():
    """데이터베이스 모듈 테스트"""
    print("\n데이터베이스 모듈 테스트...")
    
    try:
        from database import DatabaseManager
        db = DatabaseManager("test.db")
        print("✓ 데이터베이스 초기화 성공")
        
        # 테스트 데이터 삽입
        result = db.insert_article(
            url="http://test.example.com",
            title="테스트 기사",
            content="테스트 내용입니다."
        )
        
        if result:
            print("✓ 데이터 삽입 성공")
        
        # 데이터 조회
        articles = db.get_all_articles()
        print(f"✓ 데이터 조회 성공: {len(articles)}개 기사")
        
        # 테스트 DB 삭제
        import os
        if os.path.exists("test.db"):
            os.remove("test.db")
            print("✓ 테스트 데이터베이스 정리 완료")
        
        return True
        
    except Exception as e:
        print(f"✗ 데이터베이스 테스트 실패: {str(e)}")
        return False


def test_rss_parser():
    """RSS 파서 테스트"""
    print("\nRSS 파서 모듈 테스트...")
    
    try:
        from rss_parser import RSSParser
        parser = RSSParser()
        print("✓ RSS 파서 초기화 성공")
        
        # 간단한 RSS 테스트 (실제 요청 없이 모듈만 확인)
        print("✓ RSS 파서 모듈 정상")
        return True
        
    except Exception as e:
        print(f"✗ RSS 파서 테스트 실패: {str(e)}")
        return False


def test_crawler():
    """크롤러 모듈 테스트"""
    print("\n크롤러 모듈 테스트...")
    
    try:
        from crawler import WebCrawler
        print("✓ 크롤러 모듈 import 성공")
        
        # 드라이버 초기화는 Chrome이 필요하므로 스킵
        print("  (드라이버 초기화는 실제 실행 시 테스트)")
        
        return True
        
    except Exception as e:
        print(f"✗ 크롤러 테스트 실패: {str(e)}")
        return False


def main():
    """메인 테스트 함수"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "환경 설정 테스트" + " " * 27 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    # 패키지 import 테스트
    results.append(("패키지 Import", test_imports()))
    
    # 데이터베이스 테스트
    results.append(("데이터베이스", test_database()))
    
    # RSS 파서 테스트
    results.append(("RSS 파서", test_rss_parser()))
    
    # 크롤러 테스트
    results.append(("크롤러", test_crawler()))
    
    # 최종 결과
    print("\n" + "=" * 60)
    print("최종 테스트 결과")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ 통과" if result else "✗ 실패"
        print(f"{name:20s}: {status}")
    
    print("=" * 60)
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"\n🎉 모든 테스트 통과! ({success_count}/{total_count})")
        print("\n애플리케이션을 실행할 준비가 되었습니다:")
        print("  python main.py")
        return 0
    else:
        print(f"\n⚠️  일부 테스트 실패 ({success_count}/{total_count})")
        print("\n실패한 항목을 확인하고 패키지를 재설치해주세요:")
        print("  pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
