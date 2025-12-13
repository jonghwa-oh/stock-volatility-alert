#!/usr/bin/env python3
"""
알림 내역 테이블 재생성 (UNIQUE 제약 추가)
기존 데이터는 모두 삭제됨
"""
import sqlite3

def reset_alert_history(db_path='data/stock_data.db'):
    """alert_history 테이블 재생성"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 현재 데이터 개수 확인
    try:
        cursor.execute('SELECT COUNT(*) FROM alert_history')
        count = cursor.fetchone()[0]
        print(f"📊 현재 알림 내역: {count}건")
    except:
        count = 0
        print("📊 alert_history 테이블 없음")
    
    # 테이블 삭제
    cursor.execute('DROP TABLE IF EXISTS alert_history')
    print("🗑️ 기존 테이블 삭제")
    
    # 새 테이블 생성 (UNIQUE 제약 포함)
    cursor.execute('''
        CREATE TABLE alert_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            ticker_name TEXT NOT NULL,
            country TEXT NOT NULL,
            alert_level TEXT NOT NULL,
            alert_date TEXT NOT NULL,
            target_price REAL NOT NULL,
            current_price REAL NOT NULL,
            drop_rate REAL NOT NULL,
            alert_time TIMESTAMP NOT NULL,
            sent BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, ticker, alert_date, alert_level)
        )
    ''')
    
    # 인덱스 생성
    cursor.execute('CREATE INDEX idx_alert_user_date ON alert_history(user_id, alert_date)')
    cursor.execute('CREATE INDEX idx_alert_ticker ON alert_history(ticker)')
    
    conn.commit()
    conn.close()
    
    print("✅ alert_history 테이블 재생성 완료!")
    print("   - UNIQUE(user_id, ticker, alert_date, alert_level) 제약 추가됨")

if __name__ == '__main__':
    reset_alert_history()


