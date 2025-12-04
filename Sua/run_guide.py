"""
실행 가이드
"""

print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║         RSS 기사 크롤러 - 실행 가이드                     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

📦 프로젝트 위치
   /Users/su/Documents/selenium_project/Sua

✅ 환경 설정 완료
   - Python 가상환경: .venv/
   - 필수 패키지: 모두 설치됨
   - 데이터베이스: SQLite (자동 생성)

🚀 실행 방법

1. 환경 테스트 (선택사항)
   /Users/su/Documents/selenium_project/Sua/.venv/bin/python test_setup.py

2. 애플리케이션 실행
   /Users/su/Documents/selenium_project/Sua/.venv/bin/python main.py

3. 가상환경 활성화 후 실행
   cd /Users/su/Documents/selenium_project/Sua
   source .venv/bin/activate
   python main.py

📋 주요 기능

【크롤링 탭】
  • RSS 피드에서 URL 자동 수집
  • 샘플 피드 제공 (한겨레, 중앙일보, 매일경제)
  • URL 수동 추가 가능
  • 실시간 진행 상황 모니터링

【데이터 확인 탭】
  • 키워드 검색
  • 기사 목록 표시
  • 더블클릭으로 상세보기

【데이터 관리 탭】
  • 통계 정보 조회
  • 기사 삭제
  • 데이터베이스 관리

🔧 기술 스택
   - Python 3.14
   - Selenium (동적 페이지 렌더링)
   - trafilatura (본문 추출)
   - feedparser (RSS 파싱)
   - SQLite (데이터 저장)
   - tkinter (GUI)

📝 최근 개선사항
   ✓ 최신 Chrome 헤드리스 모드 적용
   ✓ 에러 핸들링 강화
   ✓ GUI 스레드 안전성 개선
   ✓ 페이지 로딩 재시도 로직
   ✓ 환경 테스트 스크립트 추가

💡 사용 팁
   - 크롤링 시작 전 URL 개수 확인
   - 대기 시간은 3초, 요청 간격은 2초 권장
   - 많은 URL을 크롤링할 때는 시간 여유를 두세요
   - 데이터는 자동으로 articles.db에 저장됩니다

⚠️  주의사항
   - Chrome 브라우저 필요
   - 인터넷 연결 필요
   - 과도한 크롤링은 서버 부하 유발 가능

═══════════════════════════════════════════════════════════

문제가 발생하면:
1. test_setup.py를 실행하여 환경 확인
2. Chrome 브라우저가 설치되어 있는지 확인
3. 가상환경이 활성화되어 있는지 확인

준비가 완료되었습니다! 애플리케이션을 실행해보세요.

""")
