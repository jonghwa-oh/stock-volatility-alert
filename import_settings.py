"""
DB 설정 데이터 가져오기 스크립트
NAS 배포 시 설정을 쉽게 복원하기 위한 도구
"""
import json
from pathlib import Path
from database import StockDatabase
import sys


def import_settings(input_file='settings_backup.json', force=False):
    """
    JSON 파일에서 DB로 설정 데이터 가져오기
    
    Args:
        input_file: 가져올 JSON 파일 경로
        force: 기존 데이터 덮어쓰기 여부
    """
    print("="*70)
    print("📥 DB 설정 데이터 가져오기")
    print("="*70)
    
    # 파일 존재 확인
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"\n❌ 파일을 찾을 수 없습니다: {input_path}")
        print("\n💡 사용 방법:")
        print(f"   1. 기존 서버에서 export_settings.py 실행")
        print(f"   2. {input_file}을 이 서버로 복사")
        print(f"   3. 다시 실행")
        return False
    
    # JSON 파일 읽기
    print(f"\n📂 파일 읽는 중: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        import_data = json.load(f)
    
    print(f"  ✅ 내보낸 날짜: {import_data['export_date']}")
    print(f"  ✅ 버전: {import_data['version']}")
    
    # 데이터 확인
    kis_count = sum(1 for s in import_data['settings'] if s['key'].startswith('kis_'))
    print(f"\n📦 가져올 데이터:")
    print(f"  • Settings: {len(import_data['settings'])}개 (KIS: {kis_count}개 포함)")
    print(f"  • Users: {len(import_data['users'])}명")
    print(f"  • Watchlist: {len(import_data['user_watchlist'])}개")
    
    # 확인
    if not force:
        response = input("\n⚠️  계속하시겠습니까? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ 취소되었습니다.")
            return False
    
    # DB 연결
    db = StockDatabase()
    conn = db.connect()
    cursor = conn.cursor()
    
    try:
        # 1. settings 테이블 (KIS 설정 포함)
        print("\n📋 settings 테이블 가져오기...")
        kis_count = 0
        for item in import_data['settings']:
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            ''', (item['key'], item['value']))
            if item['key'].startswith('kis_'):
                kis_count += 1
        print(f"  ✅ {len(import_data['settings'])}개 설정 항목 저장")
        print(f"     (KIS API 설정: {kis_count}개 포함)")
        
        # 2. users 테이블
        print("\n👤 users 테이블 가져오기...")
        for user in import_data['users']:
            # notification_enabled는 기본값 True (이전 버전 호환)
            notification_enabled = user.get('notification_enabled', True)
            cursor.execute('''
                INSERT OR REPLACE INTO users (name, chat_id, investment_amount, enabled, notification_enabled)
                VALUES (?, ?, ?, ?, ?)
            ''', (user['name'], user['chat_id'], user['investment_amount'], user['enabled'], notification_enabled))
            print(f"    - {user['name']}: chat_id={user['chat_id']}, enabled={user['enabled']}")
        print(f"  ✅ {len(import_data['users'])}명 사용자 저장")
        
        # 3. user_watchlist 테이블
        print("\n📊 user_watchlist 테이블 가져오기...")
        for item in import_data['user_watchlist']:
            # 사용자 ID 조회
            cursor.execute('SELECT id FROM users WHERE name = ?', (item['user_name'],))
            user_row = cursor.fetchone()
            
            if user_row:
                user_id = user_row[0]
                cursor.execute('''
                    INSERT OR REPLACE INTO user_watchlist (user_id, ticker, enabled, country)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, item['ticker'], item['enabled'], item['country']))
        print(f"  ✅ {len(import_data['user_watchlist'])}개 관심 종목 저장")
        
        # 커밋
        conn.commit()
        
        # 저장된 KIS 설정 카운트
        kis_count = sum(1 for s in import_data['settings'] if s['key'].startswith('kis_'))
        
        print("\n" + "="*70)
        print("✅ 가져오기 완료!")
        print("="*70)
        print(f"""
📊 저장된 데이터:
  • Settings: {len(import_data['settings'])}개 (KIS: {kis_count}개 포함)
  • Users: {len(import_data['users'])}명
  • Watchlist: {len(import_data['user_watchlist'])}개

⚠️  다음 단계:
  1. KIS API 사용 시: data/.kis_key 파일 복사 확인
  2. 데이터 확인: python -c "from database import StockDatabase; db = StockDatabase(); print(db.get_all_users())"
  3. 보안: {input_file} 삭제 또는 안전한 곳에 백업
""")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def check_kis_key():
    """
    KIS API 암호화 키 파일 확인
    """
    key_file = Path('data/.kis_key')
    
    print("\n" + "="*70)
    print("🔑 KIS API 암호화 키 확인")
    print("="*70)
    
    if key_file.exists():
        print(f"✅ 키 파일 존재: {key_file}")
        print("   KIS Settings를 복호화할 수 있습니다.")
    else:
        print(f"⚠️  키 파일 없음: {key_file}")
        print("""
⚠️  KIS API를 사용하는 경우:
  1. 기존 서버에서 data/.kis_key 파일 복사
  2. 이 서버의 data/ 폴더에 저장
  3. 권한 설정: chmod 600 data/.kis_key

💡 KIS API를 사용하지 않는 경우 무시하세요.
""")


if __name__ == "__main__":
    # 명령줄 인자 처리
    input_file = 'settings_backup.json'
    force = False
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    
    if '--force' in sys.argv:
        force = True
    
    try:
        # 설정 데이터 가져오기
        success = import_settings(input_file, force)
        
        if success:
            # KIS 키 파일 확인
            check_kis_key()
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

