#!/usr/bin/env python3
"""
users 테이블 마이그레이션 스크립트
- investment_amount 컬럼 제거
- chat_id 컬럼 제거
"""

import sqlite3
import sys
from pathlib import Path


def migrate_users_table(db_path='data/stock_data.db'):
    """users 테이블에서 불필요한 컬럼 제거"""
    
    if not Path(db_path).exists():
        print(f"❌ DB 파일을 찾을 수 없습니다: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 현재 테이블 구조 확인
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"현재 users 테이블 컬럼: {columns}")
        
        # 이미 마이그레이션 되었는지 확인
        if 'chat_id' not in columns and 'investment_amount' not in columns:
            print("✅ 이미 마이그레이션 완료된 상태입니다.")
            return True
        
        print("\n🔄 마이그레이션 시작...")
        
        # 새 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                enabled BOOLEAN DEFAULT 1,
                notification_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 데이터 복사
        cursor.execute('''
            INSERT INTO users_new (id, name, enabled, notification_enabled, created_at)
            SELECT id, name, enabled, notification_enabled, created_at FROM users
        ''')
        
        # 기존 테이블 삭제
        cursor.execute('DROP TABLE users')
        
        # 새 테이블 이름 변경
        cursor.execute('ALTER TABLE users_new RENAME TO users')
        
        conn.commit()
        
        # 결과 확인
        cursor.execute("PRAGMA table_info(users)")
        new_columns = [col[1] for col in cursor.fetchall()]
        print(f"변경 후 users 테이블 컬럼: {new_columns}")
        
        # 사용자 데이터 확인
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        print(f"\n📊 사용자 데이터 ({len(users)}명):")
        for user in users:
            print(f"  - {user}")
        
        print("\n✅ 마이그레이션 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/stock_data.db'
    print(f"📁 DB 경로: {db_path}\n")
    migrate_users_table(db_path)

