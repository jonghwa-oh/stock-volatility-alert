"""
SQLite 데이터베이스 관리
일봉 & 분봉 데이터 저장/조회
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd


class StockDatabase:
    """주식 데이터 관리"""
    
    def __init__(self, db_path='stock_data.db'):
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def connect(self):
        """DB 연결"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def close(self):
        """DB 연결 종료"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # 일봉 데이터 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                ticker_name TEXT NOT NULL,
                date DATE NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL NOT NULL,
                volume INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, date)
            )
        ''')
        
        # 분봉 데이터 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS minute_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                ticker_name TEXT NOT NULL,
                datetime TIMESTAMP NOT NULL,
                price REAL NOT NULL,
                volume INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, datetime)
            )
        ''')
        
        # 통계 캐시 테이블 (표준편차 등)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                date DATE NOT NULL,
                mean_return REAL,
                std_dev REAL,
                current_price REAL,
                target_1sigma REAL,
                target_2sigma REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, date)
            )
        ''')
        
        # 사용자 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                chat_id TEXT NOT NULL,
                investment_amount REAL DEFAULT 1000000,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 사용자별 관심 종목 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, ticker)
            )
        ''')
        
        # 인덱스 생성
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_ticker_date ON daily_prices(ticker, date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_minute_ticker_datetime ON minute_prices(ticker, datetime)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stats_ticker_date ON statistics_cache(ticker, date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_watchlist ON user_watchlist(user_id, ticker)')
        
        conn.commit()
        print("✅ 데이터베이스 초기화 완료")
    
    def insert_daily_price(self, ticker: str, ticker_name: str, date: str, 
                          open_price: float, high: float, low: float, 
                          close: float, volume: int):
        """일봉 데이터 저장"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO daily_prices 
                (ticker, ticker_name, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ticker, ticker_name, date, open_price, high, low, close, volume))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ 일봉 데이터 저장 실패 ({ticker}): {e}")
            return False
    
    def insert_daily_prices_bulk(self, data: List[Tuple]):
        """일봉 데이터 대량 저장"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.executemany('''
                INSERT OR REPLACE INTO daily_prices 
                (ticker, ticker_name, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ 일봉 데이터 대량 저장 실패: {e}")
            return False
    
    def insert_minute_price(self, ticker: str, ticker_name: str, 
                           datetime_str: str, price: float, volume: int = 0):
        """분봉 데이터 저장"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO minute_prices 
                (ticker, ticker_name, datetime, price, volume)
                VALUES (?, ?, ?, ?, ?)
            ''', (ticker, ticker_name, datetime_str, price, volume))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ 분봉 데이터 저장 실패 ({ticker}): {e}")
            return False
    
    def insert_minute_prices_bulk(self, data: List[Tuple]):
        """분봉 데이터 대량 저장"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.executemany('''
                INSERT OR REPLACE INTO minute_prices 
                (ticker, ticker_name, datetime, price, volume)
                VALUES (?, ?, ?, ?, ?)
            ''', data)
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ 분봉 데이터 대량 저장 실패: {e}")
            return False
    
    def get_daily_prices(self, ticker: str, days: int = 252) -> pd.DataFrame:
        """일봉 데이터 조회 (최근 N일)"""
        conn = self.connect()
        
        query = '''
            SELECT date, open, high, low, close, volume
            FROM daily_prices
            WHERE ticker = ?
            ORDER BY date DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(ticker, days))
        
        if not df.empty:
            df = df.sort_values('date').reset_index(drop=True)
            df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    def get_daily_prices_range(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """일봉 데이터 조회 (날짜 범위)"""
        conn = self.connect()
        
        query = '''
            SELECT date, open, high, low, close, volume
            FROM daily_prices
            WHERE ticker = ? AND date BETWEEN ? AND ?
            ORDER BY date
        '''
        
        df = pd.read_sql_query(query, conn, params=(ticker, start_date, end_date))
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    def get_latest_date(self, ticker: str) -> str:
        """해당 종목의 최신 데이터 날짜"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT MAX(date) FROM daily_prices WHERE ticker = ?
        ''', (ticker,))
        
        result = cursor.fetchone()
        return result[0] if result[0] else None
    
    def get_minute_prices(self, ticker: str, hours: int = 24) -> pd.DataFrame:
        """분봉 데이터 조회 (최근 N시간)"""
        conn = self.connect()
        
        cutoff_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        query = '''
            SELECT datetime, price, volume
            FROM minute_prices
            WHERE ticker = ? AND datetime >= ?
            ORDER BY datetime
        '''
        
        df = pd.read_sql_query(query, conn, params=(ticker, cutoff_time))
        
        if not df.empty:
            df['datetime'] = pd.to_datetime(df['datetime'])
        
        return df
    
    def update_statistics_cache(self, ticker: str, date: str, 
                                mean_return: float, std_dev: float,
                                current_price: float, target_1sigma: float, 
                                target_2sigma: float):
        """통계 캐시 업데이트"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO statistics_cache 
                (ticker, date, mean_return, std_dev, current_price, target_1sigma, target_2sigma)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ticker, date, mean_return, std_dev, current_price, target_1sigma, target_2sigma))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ 통계 캐시 업데이트 실패 ({ticker}): {e}")
            return False
    
    def get_statistics_cache(self, ticker: str, date: str = None) -> Dict:
        """통계 캐시 조회"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT mean_return, std_dev, current_price, target_1sigma, target_2sigma, updated_at
            FROM statistics_cache
            WHERE ticker = ? AND date = ?
        ''', (ticker, date))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'mean_return': result[0],
                'std_dev': result[1],
                'current_price': result[2],
                'target_1sigma': result[3],
                'target_2sigma': result[4],
                'updated_at': result[5]
            }
        return None
    
    def get_all_tickers(self) -> List[str]:
        """저장된 모든 종목 코드"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT ticker FROM daily_prices')
        return [row[0] for row in cursor.fetchall()]
    
    def get_data_status(self) -> Dict:
        """데이터 현황"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # 일봉 데이터 현황
        cursor.execute('SELECT COUNT(*) FROM daily_prices')
        daily_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT ticker) FROM daily_prices')
        daily_tickers = cursor.fetchone()[0]
        
        cursor.execute('SELECT MIN(date), MAX(date) FROM daily_prices')
        daily_range = cursor.fetchone()
        
        # 분봉 데이터 현황
        cursor.execute('SELECT COUNT(*) FROM minute_prices')
        minute_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT ticker) FROM minute_prices')
        minute_tickers = cursor.fetchone()[0]
        
        cursor.execute('SELECT MIN(datetime), MAX(datetime) FROM minute_prices')
        minute_range = cursor.fetchone()
        
        return {
            'daily': {
                'total_rows': daily_count,
                'tickers': daily_tickers,
                'date_range': daily_range
            },
            'minute': {
                'total_rows': minute_count,
                'tickers': minute_tickers,
                'datetime_range': minute_range
            }
        }
    
    def cleanup_old_minute_data(self, days: int = 30):
        """오래된 분봉 데이터 삭제 (선택)"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            DELETE FROM minute_prices WHERE datetime < ?
        ''', (cutoff_date,))
        
        deleted = cursor.rowcount
        conn.commit()
        
        # VACUUM으로 디스크 공간 회수
        cursor.execute('VACUUM')
        
        print(f"✅ {deleted}개 오래된 분봉 데이터 삭제 (30일 이전)")
        return deleted
    
    def backup_database(self, backup_path: str):
        """데이터베이스 백업"""
        import shutil
        try:
            shutil.copy2(self.db_path, backup_path)
            print(f"✅ 백업 완료: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ 백업 실패: {e}")
            return False
    
    # ========================================
    # 사용자 관리
    # ========================================
    
    def add_user(self, name: str, chat_id: str, investment_amount: float = 1000000):
        """사용자 추가"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (name, chat_id, investment_amount)
                VALUES (?, ?, ?)
            ''', (name, chat_id, investment_amount))
            conn.commit()
            print(f"✅ 사용자 추가: {name}")
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"⚠️  이미 존재하는 사용자: {name}")
            return None
        except Exception as e:
            print(f"❌ 사용자 추가 실패: {e}")
            return None
    
    def get_user(self, name: str) -> Dict:
        """사용자 정보 조회"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, chat_id, investment_amount, enabled
            FROM users WHERE name = ?
        ''', (name,))
        
        result = cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'chat_id': result[2],
                'investment_amount': result[3],
                'enabled': result[4]
            }
        return None
    
    def get_all_users(self) -> List[Dict]:
        """모든 활성 사용자 조회"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, chat_id, investment_amount, enabled
            FROM users WHERE enabled = 1
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'name': row[1],
                'chat_id': row[2],
                'investment_amount': row[3],
                'enabled': row[4]
            })
        return users
    
    def update_user_investment(self, name: str, amount: float):
        """사용자 투자 금액 변경"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users SET investment_amount = ? WHERE name = ?
            ''', (amount, name))
            conn.commit()
            print(f"✅ {name} 투자 금액 변경: {amount:,.0f}원")
            return True
        except Exception as e:
            print(f"❌ 투자 금액 변경 실패: {e}")
            return False
    
    def add_user_watchlist(self, user_name: str, ticker: str):
        """사용자 관심 종목 추가"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # 사용자 ID 가져오기
        user = self.get_user(user_name)
        if not user:
            print(f"❌ 사용자 없음: {user_name}")
            return False
        
        try:
            cursor.execute('''
                INSERT INTO user_watchlist (user_id, ticker)
                VALUES (?, ?)
            ''', (user['id'], ticker))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # 이미 있으면 활성화
            cursor.execute('''
                UPDATE user_watchlist SET enabled = 1
                WHERE user_id = ? AND ticker = ?
            ''', (user['id'], ticker))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ 관심 종목 추가 실패: {e}")
            return False
    
    def remove_user_watchlist(self, user_name: str, ticker: str):
        """사용자 관심 종목 제거"""
        conn = self.connect()
        cursor = conn.cursor()
        
        user = self.get_user(user_name)
        if not user:
            return False
        
        try:
            cursor.execute('''
                UPDATE user_watchlist SET enabled = 0
                WHERE user_id = ? AND ticker = ?
            ''', (user['id'], ticker))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ 관심 종목 제거 실패: {e}")
            return False
    
    def get_user_watchlist(self, user_name: str) -> List[str]:
        """사용자 관심 종목 목록"""
        conn = self.connect()
        cursor = conn.cursor()
        
        user = self.get_user(user_name)
        if not user:
            return []
        
        cursor.execute('''
            SELECT ticker FROM user_watchlist
            WHERE user_id = ? AND enabled = 1
        ''', (user['id'],))
        
        return [row[0] for row in cursor.fetchall()]
    
    def get_user_watchlist_with_names(self, user_name: str) -> List[Dict]:
        """사용자 관심 종목 목록 (종목명 포함)"""
        conn = self.connect()
        cursor = conn.cursor()
        
        user = self.get_user(user_name)
        if not user:
            return []
        
        cursor.execute('''
            SELECT DISTINCT uw.ticker, dp.ticker_name
            FROM user_watchlist uw
            LEFT JOIN daily_prices dp ON uw.ticker = dp.ticker
            WHERE uw.user_id = ? AND uw.enabled = 1
            GROUP BY uw.ticker
        ''', (user['id'],))
        
        watchlist = []
        for row in cursor.fetchall():
            watchlist.append({
                'ticker': row[0],
                'name': row[1] or row[0]
            })
        return watchlist


if __name__ == "__main__":
    # 테스트
    db = StockDatabase()
    
    print("\n📊 데이터베이스 현황:")
    status = db.get_data_status()
    print(f"일봉 데이터: {status['daily']['total_rows']:,}개 ({status['daily']['tickers']}개 종목)")
    print(f"분봉 데이터: {status['minute']['total_rows']:,}개 ({status['minute']['tickers']}개 종목)")
    
    if status['daily']['date_range'][0]:
        print(f"일봉 기간: {status['daily']['date_range'][0]} ~ {status['daily']['date_range'][1]}")
    
    if status['minute']['datetime_range'][0]:
        print(f"분봉 기간: {status['minute']['datetime_range'][0]} ~ {status['minute']['datetime_range'][1]}")
    
    db.close()

