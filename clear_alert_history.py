#!/usr/bin/env python3
"""
알림 내역 초기화 스크립트
"""
from database import StockDatabase

def clear_alert_history():
    """alert_history 테이블 전체 삭제"""
    db = StockDatabase()
    conn = db.connect()
    cursor = conn.cursor()
    
    # 현재 개수 확인
    cursor.execute('SELECT COUNT(*) FROM alert_history')
    count = cursor.fetchone()[0]
    print(f"📊 현재 알림 내역: {count}건")
    
    # 전체 삭제
    cursor.execute('DELETE FROM alert_history')
    conn.commit()
    
    print(f"🗑️ {count}건 삭제 완료!")
    
    db.close()

if __name__ == '__main__':
    clear_alert_history()

