"""
DB 설정 데이터 내보내기 스크립트
NAS 배포 시 설정을 쉽게 이동하기 위한 도구
"""
import json
from pathlib import Path
from database import StockDatabase
from datetime import datetime


def export_settings(output_file='settings_backup.json'):
    """
    DB의 모든 설정 데이터를 JSON 파일로 내보내기
    
    포함 항목:
    - settings: Telegram Bot Token, Chat ID, 투자금
    - kis_settings: KIS API 암호화된 키들
    - users: 사용자 정보
    - user_watchlist: 사용자별 관심 종목
    """
    print("="*70)
    print("📤 DB 설정 데이터 내보내기")
    print("="*70)
    
    db = StockDatabase()
    conn = db.connect()
    cursor = conn.cursor()
    
    export_data = {
        'export_date': datetime.now().isoformat(),
        'version': '1.0',
        'settings': [],
        'users': [],
        'user_watchlist': []
    }
    
    # 1. settings 테이블 (모든 설정, KIS 포함)
    print("\n📋 settings 테이블 내보내기...")
    cursor.execute('SELECT key, value FROM settings')
    kis_count = 0
    for row in cursor.fetchall():
        export_data['settings'].append({
            'key': row[0],
            'value': row[1]
        })
        if row[0].startswith('kis_'):
            kis_count += 1
    print(f"  ✅ {len(export_data['settings'])}개 설정 항목")
    print(f"     (KIS API 설정: {kis_count}개 포함)")
    
    # 3. users 테이블
    print("\n👤 users 테이블 내보내기...")
    cursor.execute('SELECT name, chat_id, investment_amount, enabled, notification_enabled FROM users')
    for row in cursor.fetchall():
        export_data['users'].append({
            'name': row[0],
            'chat_id': row[1],
            'investment_amount': row[2],
            'enabled': bool(row[3]),
            'notification_enabled': bool(row[4]) if row[4] is not None else True
        })
    print(f"  ✅ {len(export_data['users'])}명 사용자")
    
    # 4. user_watchlist 테이블
    print("\n📊 user_watchlist 테이블 내보내기...")
    cursor.execute('''
        SELECT u.name, uw.ticker, uw.enabled, uw.country
        FROM user_watchlist uw
        JOIN users u ON uw.user_id = u.id
    ''')
    for row in cursor.fetchall():
        export_data['user_watchlist'].append({
            'user_name': row[0],
            'ticker': row[1],
            'enabled': bool(row[2]),
            'country': row[3]
        })
    print(f"  ✅ {len(export_data['user_watchlist'])}개 관심 종목")
    
    # JSON 파일로 저장
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    # KIS 설정 카운트
    kis_count = sum(1 for s in export_data['settings'] if s['key'].startswith('kis_'))
    
    print("\n" + "="*70)
    print(f"✅ 내보내기 완료: {output_path}")
    print("="*70)
    print(f"""
📦 내보낸 데이터:
  • Settings: {len(export_data['settings'])}개 (KIS: {kis_count}개 포함)
  • Users: {len(export_data['users'])}명
  • Watchlist: {len(export_data['user_watchlist'])}개

⚠️  중요:
  • 이 파일에는 민감한 정보가 포함되어 있습니다!
  • Git에 커밋하지 마세요 (.gitignore에 추가됨)
  • NAS로 안전하게 복사하세요

📂 다음 단계:
  1. {output_file}을 NAS로 복사
  2. NAS에서 import_settings.py 실행
  3. 설정 파일 삭제 또는 안전한 곳에 백업
""")
    
    db.close()
    return str(output_path)


def export_kis_key():
    """
    KIS API 암호화 키 파일도 함께 복사 안내
    """
    key_file = Path('data/.kis_key')
    
    if key_file.exists():
        print("\n" + "="*70)
        print("🔑 KIS API 암호화 키 파일 확인")
        print("="*70)
        print(f"""
✅ 암호화 키 파일 존재: {key_file}

⚠️  중요:
  • KIS Settings를 복호화하려면 이 키 파일도 필요합니다!
  • NAS로 복사 시 이 파일도 함께 복사하세요
  
📂 복사 방법:
  1. {key_file}을 NAS의 data/ 폴더로 복사
  2. 권한 설정: chmod 600 data/.kis_key
""")
    else:
        print("\n⚠️  암호화 키 파일이 없습니다. KIS API를 사용하지 않는 경우 무시하세요.")


if __name__ == "__main__":
    try:
        # 설정 데이터 내보내기
        output_file = export_settings()
        
        # KIS 키 파일 안내
        export_kis_key()
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

