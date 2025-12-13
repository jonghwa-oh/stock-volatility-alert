#!/usr/bin/env python3
"""캐시 테이블 재생성 스크립트"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'stock_data.db')

def reset_cache_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 기존 테이블 삭제
    cursor.execute('DROP TABLE IF EXISTS statistics_cache')
    print("✅ 기존 캐시 테이블 삭제")
    
    # 새 테이블 생성
    cursor.execute('''
        CREATE TABLE statistics_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            ticker_name TEXT,
            country TEXT DEFAULT 'US',
            date DATE NOT NULL,
            data_date DATE,
            mean_return REAL,
            std_dev REAL,
            current_price REAL,
            target_05sigma REAL,
            target_1sigma REAL,
            target_2sigma REAL,
            drop_05x REAL,
            drop_1x REAL,
            drop_2x REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker, date)
        )
    ''')
    
    # 인덱스 생성
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stats_ticker_date ON statistics_cache(ticker, date)')
    
    conn.commit()
    conn.close()
    print("✅ 캐시 테이블 재생성 완료")

if __name__ == '__main__':
    reset_cache_table()


