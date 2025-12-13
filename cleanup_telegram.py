"""
텔레그램 관련 DB 데이터 정리 스크립트
- settings 테이블에서 텔레그램 관련 설정 삭제
- users 테이블에서 chat_id 컬럼 삭제
"""
import sqlite3
import shutil
from datetime import datetime


def cleanup_telegram_data(db_path='data/stock_data.db'):
    """텔레그램 관련 데이터 정리"""
    
    print("=" * 60)
    print("🧹 텔레그램 관련 DB 데이터 정리")
    print("=" * 60)
    
    # 백업 먼저
    backup_path = f"data/stock_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    print(f"\n📦 백업 생성: {backup_path}")
    shutil.copy2(db_path, backup_path)
    print("✅ 백업 완료!")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # SQLite 버전 확인
    cursor.execute("SELECT sqlite_version()")
    version = cursor.fetchone()[0]
    print(f"\n📊 SQLite 버전: {version}")
    
    # 1. settings 테이블에서 텔레그램 관련 삭제
    print("\n[1/2] settings 테이블 정리...")
    cursor.execute("""
        DELETE FROM settings 
        WHERE key IN ('bot_token', 'default_chat_id', 'notification_method', 'telegram_bot_token')
    """)
    deleted_settings = cursor.rowcount
    print(f"  ✅ 삭제된 설정: {deleted_settings}개")
    
    # 2. users 테이블에서 chat_id 컬럼 삭제
    print("\n[2/2] users 테이블에서 chat_id 컬럼 삭제...")
    
    # SQLite 3.35.0 이상에서만 DROP COLUMN 지원
    version_parts = [int(x) for x in version.split('.')]
    if version_parts[0] > 3 or (version_parts[0] == 3 and version_parts[1] >= 35):
        # 직접 컬럼 삭제 가능
        try:
            cursor.execute("ALTER TABLE users DROP COLUMN chat_id")
            print("  ✅ chat_id 컬럼 삭제 완료!")
        except sqlite3.OperationalError as e:
            print(f"  ⚠️ 컬럼 삭제 실패 (이미 없거나 오류): {e}")
    else:
        # 테이블 재생성 필요
        print(f"  📌 SQLite {version}은 DROP COLUMN 미지원, 테이블 재생성...")
        
        # 새 테이블 생성 (chat_id 제외)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                password_hash TEXT,
                ntfy_topic TEXT,
                investment_amount REAL DEFAULT 1000000,
                enabled BOOLEAN DEFAULT 1,
                notification_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 기존 데이터 복사
        cursor.execute("""
            INSERT INTO users_new (id, name, password_hash, ntfy_topic, investment_amount, enabled, notification_enabled, created_at)
            SELECT id, name, password_hash, ntfy_topic, investment_amount, enabled, notification_enabled, created_at
            FROM users
        """)
        
        # 기존 테이블 삭제 및 이름 변경
        cursor.execute("DROP TABLE users")
        cursor.execute("ALTER TABLE users_new RENAME TO users")
        
        print("  ✅ users 테이블 재생성 완료! (chat_id 컬럼 제거됨)")
    
    conn.commit()
    
    # 결과 확인
    print("\n" + "=" * 60)
    print("📊 정리 결과")
    print("=" * 60)
    
    # users 테이블 구조 확인
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print("\n👥 users 테이블 컬럼:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # settings 테이블 확인
    cursor.execute("SELECT key FROM settings")
    settings = cursor.fetchall()
    print("\n⚙️ settings 테이블 키:")
    for s in settings:
        print(f"  - {s[0]}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ 정리 완료!")
    print(f"📦 백업 파일: {backup_path}")
    print("=" * 60)


if __name__ == "__main__":
    cleanup_telegram_data()


