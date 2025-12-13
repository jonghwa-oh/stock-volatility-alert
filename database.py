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
    
    def __init__(self, db_path='data/stock_data.db'):
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
                datetime_utc TIMESTAMP,
                market_date DATE,
                price REAL NOT NULL,
                volume INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, datetime)
            )
        ''')
        
        # minute_prices에 market_date 컬럼 추가 (기존 테이블)
        try:
            cursor.execute("ALTER TABLE minute_prices ADD COLUMN datetime_utc TIMESTAMP")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE minute_prices ADD COLUMN market_date DATE")
        except:
            pass
        
        # 통계 캐시 테이블 (표준편차 등)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics_cache (
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
        
        # statistics_cache 컬럼 추가 (기존 테이블)
        for col, col_type in [
            ('ticker_name', 'TEXT'),
            ('country', 'TEXT DEFAULT "US"'),
            ('data_date', 'DATE'),
            ('target_05sigma', 'REAL'),
            ('drop_05x', 'REAL'),
            ('drop_1x', 'REAL'),
            ('drop_2x', 'REAL')
        ]:
            try:
                cursor.execute(f"ALTER TABLE statistics_cache ADD COLUMN {col} {col_type}")
            except:
                pass
        
        # 사용자 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                password_hash TEXT,
                ntfy_topic TEXT,
                enabled BOOLEAN DEFAULT 1,
                notification_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # notification_enabled 컬럼 추가 (기존 테이블 업데이트)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN notification_enabled BOOLEAN DEFAULT 1")
        except sqlite3.OperationalError:
            # 이미 컬럼이 존재하면 무시
            pass
        
        # password_hash 컬럼 추가 (웹 로그인용)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        except sqlite3.OperationalError:
            # 이미 컬럼이 존재하면 무시
            pass
        
        # ntfy_topic 컬럼 추가 (사용자별 ntfy 토픽)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN ntfy_topic TEXT")
        except sqlite3.OperationalError:
            # 이미 컬럼이 존재하면 무시
            pass
        
        # 사용자별 관심 종목 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                name TEXT,
                country TEXT DEFAULT 'US',
                enabled BOOLEAN DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, ticker)
            )
        ''')
        
        # country 컬럼 추가 (기존 테이블 업데이트)
        try:
            cursor.execute("ALTER TABLE user_watchlist ADD COLUMN country TEXT DEFAULT 'US'")
            # 기존 데이터에 country 값 설정 (숫자면 KR, 알파벳이면 US)
            cursor.execute('''
                UPDATE user_watchlist 
                SET country = CASE 
                    WHEN ticker GLOB '[0-9]*' THEN 'KR' 
                    ELSE 'US' 
                END
                WHERE country IS NULL OR country = ''
            ''')
            conn.commit()
        except sqlite3.OperationalError:
            # 이미 컬럼이 존재하면 무시
            pass
        
        # name 컬럼 추가 (기존 테이블 업데이트)
        try:
            cursor.execute("ALTER TABLE user_watchlist ADD COLUMN name TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            # 이미 컬럼이 존재하면 무시
            pass
        
        # investment_amount 컬럼 추가 (종목별 투자금액)
        try:
            cursor.execute("ALTER TABLE user_watchlist ADD COLUMN investment_amount REAL")
            conn.commit()
        except sqlite3.OperationalError:
            # 이미 컬럼이 존재하면 무시
            pass
        
        # 설정 테이블 (봇 토큰, 기본값 등)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 알림 이력 테이블 (놓친 알림 추적 + 중복 방지)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
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
        
        # alert_history에 user_id, alert_date 컬럼 추가 (기존 테이블 업데이트)
        try:
            cursor.execute("ALTER TABLE alert_history ADD COLUMN user_id INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE alert_history ADD COLUMN alert_date TEXT")
        except sqlite3.OperationalError:
            pass
        
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
                           datetime_str: str, price: float, volume: int = 0,
                           datetime_utc: str = None, market_date: str = None):
        """
        분봉 데이터 저장
        
        Args:
            datetime_str: 로컬 시간 (호환성 유지)
            datetime_utc: UTC 시간 (선택)
            market_date: 시장 거래일 (선택, 예: 미국 주식은 미국 날짜)
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO minute_prices 
                (ticker, ticker_name, datetime, datetime_utc, market_date, price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ticker, ticker_name, datetime_str, datetime_utc, market_date, price, volume))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ 분봉 데이터 저장 실패 ({ticker}): {e}")
            return False
    
    def insert_minute_prices_bulk(self, data: List[Tuple]):
        """
        분봉 데이터 대량 저장
        
        data 형식: [(ticker, ticker_name, datetime, datetime_utc, market_date, price, volume), ...]
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.executemany('''
                INSERT OR REPLACE INTO minute_prices 
                (ticker, ticker_name, datetime, datetime_utc, market_date, price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
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
                                target_2sigma: float, ticker_name: str = None,
                                country: str = 'US', data_date: str = None,
                                target_05sigma: float = None, drop_05x: float = None,
                                drop_1x: float = None, drop_2x: float = None):
        """통계 캐시 업데이트 (확장)"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # 모든 숫자값을 float로 강제 변환 (BLOB 저장 방지)
        def to_float(val):
            if val is None:
                return None
            try:
                return float(val)
            except:
                return None
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO statistics_cache 
                (ticker, ticker_name, country, date, data_date, mean_return, std_dev, 
                 current_price, target_05sigma, target_1sigma, target_2sigma,
                 drop_05x, drop_1x, drop_2x)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ticker, ticker_name, country, date, data_date, 
                  to_float(mean_return), to_float(std_dev), 
                  to_float(current_price), to_float(target_05sigma), 
                  to_float(target_1sigma), to_float(target_2sigma),
                  to_float(drop_05x), to_float(drop_1x), to_float(drop_2x)))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ 통계 캐시 업데이트 실패 ({ticker}): {e}")
            return False
    
    def get_statistics_cache(self, ticker: str, date: str = None) -> Dict:
        """통계 캐시 조회 (확장)"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT ticker_name, country, data_date, mean_return, std_dev, current_price, 
                   target_05sigma, target_1sigma, target_2sigma,
                   drop_05x, drop_1x, drop_2x, updated_at
            FROM statistics_cache
            WHERE ticker = ? AND date = ?
        ''', (ticker, date))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'ticker_name': result[0],
                'country': result[1],
                'data_date': result[2],
                'mean_return': result[3],
                'std_dev': result[4],
                'std_return': result[4],  # 호환성
                'current_price': result[5],
                'target_05x': result[6],
                'target_1x': result[7],
                'target_2x': result[8],
                'drop_05x': result[9],
                'drop_1x': result[10],
                'drop_2x': result[11],
                'updated_at': result[12],
                'from_cache': True
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
    
    def add_user(self, name: str, ntfy_topic: str = None):
        """사용자 추가"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (name, ntfy_topic)
                VALUES (?, ?)
            ''', (name, ntfy_topic))
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
            SELECT id, name, enabled, ntfy_topic
            FROM users WHERE name = ?
        ''', (name,))
        
        result = cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'enabled': result[3],
                'ntfy_topic': result[4]
            }
        return None
    
    def get_all_users(self, include_disabled: bool = False) -> List[Dict]:
        """모든 사용자 조회"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if include_disabled:
            cursor.execute('''
                SELECT id, name, enabled, notification_enabled, password_hash, ntfy_topic
                FROM users
            ''')
        else:
            cursor.execute('''
                SELECT id, name, enabled, notification_enabled, password_hash, ntfy_topic
                FROM users WHERE enabled = 1
            ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'name': row[1],
                'enabled': row[3],
                'notification_enabled': row[4] if row[4] is not None else 1,
                'password_hash': row[5],
                'ntfy_topic': row[6]
            })
        return users
    

    
    def add_user_watchlist(self, user_name: str, ticker: str, name: str = None, country: str = 'US', investment_amount: float = None):
        """사용자 관심 종목 추가
        
        Args:
            user_name: 사용자 이름
            ticker: 종목 코드
            name: 종목명 (없으면 ticker 사용)
            country: 국가 코드 ('KR' 또는 'US')
            investment_amount: 투자금액 (KR: 원, US: 달러)
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # 사용자 ID 가져오기
        user = self.get_user(user_name)
        if not user:
            print(f"❌ 사용자 없음: {user_name}")
            return False
        
        # 이름이 없으면 티커 사용
        if not name:
            name = ticker
        
        try:
            cursor.execute('''
                INSERT INTO user_watchlist (user_id, ticker, name, country, investment_amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (user['id'], ticker, name, country, investment_amount))
            conn.commit()
            print(f"✅ 관심 종목 추가: {name}({ticker}) [{country}] 투자금액: {investment_amount}")
            return True
        except sqlite3.IntegrityError:
            # 이미 있으면 활성화 + 이름/국가/투자금액 업데이트
            cursor.execute('''
                UPDATE user_watchlist SET enabled = 1, name = ?, country = ?, investment_amount = ?
                WHERE user_id = ? AND ticker = ?
            ''', (name, country, investment_amount, user['id'], ticker))
            conn.commit()
            print(f"✅ 관심 종목 재활성화: {name}({ticker}) [{country}] 투자금액: {investment_amount}")
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
    
    def update_watchlist_investment(self, user_name: str, ticker: str, investment_amount: float) -> bool:
        """종목별 투자금액 업데이트
        
        Args:
            user_name: 사용자 이름
            ticker: 종목 코드
            investment_amount: 투자금액 (KR: 원, US: 달러)
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        user = self.get_user(user_name)
        if not user:
            return False
        
        try:
            cursor.execute('''
                UPDATE user_watchlist SET investment_amount = ?
                WHERE user_id = ? AND ticker = ?
            ''', (investment_amount, user['id'], ticker))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ 투자금액 업데이트 실패: {e}")
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
        """사용자 관심 종목 목록 (종목명 + 국가 + 투자금액 정보 포함)
        
        우선순위: user_watchlist.name > daily_prices.ticker_name > ticker
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        user = self.get_user(user_name)
        if not user:
            return []
        
        cursor.execute('''
            SELECT uw.ticker, uw.name, MAX(dp.ticker_name) as dp_name, uw.country, uw.investment_amount
            FROM user_watchlist uw
            LEFT JOIN daily_prices dp ON uw.ticker = dp.ticker
            WHERE uw.user_id = ? AND uw.enabled = 1
            GROUP BY uw.ticker, uw.name, uw.country, uw.investment_amount
        ''', (user['id'],))
        
        watchlist = []
        for row in cursor.fetchall():
            ticker = row[0]
            uw_name = row[1]  # user_watchlist.name
            dp_name = row[2]  # daily_prices.ticker_name
            country = row[3] or 'US'
            investment_amount = row[4]
            
            # 우선순위: uw_name > dp_name > ticker
            name = uw_name or dp_name or ticker
            
            watchlist.append({
                'ticker': ticker,
                'name': name,
                'country': country,
                'investment_amount': investment_amount
            })
        return watchlist
    
    def get_user_watchlist_with_country(self, user_name: str) -> List[Dict]:
        """사용자 관심 종목 목록 (종목명 + 국가 정보 포함)"""
        conn = self.connect()
        cursor = conn.cursor()
        
        user = self.get_user(user_name)
        if not user:
            return []
        
        cursor.execute('''
            SELECT uw.ticker, MAX(dp.ticker_name) as ticker_name, uw.country
            FROM user_watchlist uw
            LEFT JOIN daily_prices dp ON uw.ticker = dp.ticker
            WHERE uw.user_id = ? AND uw.enabled = 1
            GROUP BY uw.ticker
        ''', (user['id'],))
        
        watchlist = []
        for row in cursor.fetchall():
            watchlist.append({
                'ticker': row[0],
                'name': row[1] or row[0],
                'country': row[2] or 'US'
            })
        return watchlist
    
    # ============ 웹 인증 관리 ============
    
    def set_user_password(self, name: str, password_hash: str) -> bool:
        """사용자 비밀번호 설정"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users SET password_hash = ? WHERE name = ?
            ''', (password_hash, name))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ 비밀번호 설정 실패: {e}")
            return False
    
    def get_user_by_name(self, name: str) -> Dict:
        """사용자 정보 조회 (웹 로그인용, 비밀번호 해시 포함)"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, enabled, notification_enabled, password_hash, ntfy_topic
            FROM users WHERE name = ?
        ''', (name,))
        
        result = cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'enabled': result[3],
                'notification_enabled': result[4] if result[4] is not None else 1,
                'password_hash': result[5],
                'ntfy_topic': result[6]
            }
        return None
    
    def set_user_ntfy_topic(self, name: str, ntfy_topic: str) -> bool:
        """사용자 ntfy 토픽 설정"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users SET ntfy_topic = ? WHERE name = ?
            ''', (ntfy_topic, name))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ ntfy 토픽 설정 실패: {e}")
            return False
    
    def get_user_ntfy_topic(self, user_id: int) -> str:
        """사용자 ntfy 토픽 조회"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('SELECT ntfy_topic FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        
        return result[0] if result and result[0] else None
    
    def verify_user_password(self, name: str, password_hash: str) -> bool:
        """사용자 비밀번호 확인"""
        user = self.get_user_by_name(name)
        if user and user['password_hash']:
            return user['password_hash'] == password_hash
        return False
    
    # ============ 설정 관리 ============
    
    def save_setting(self, key: str, value: str, description: str = None):
        """설정 저장"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, description, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (key, value, description))
        
        conn.commit()
        print(f"✅ 설정 저장: {key}")
    
    def get_setting(self, key: str, default=None):
        """설정 조회"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        
        return result[0] if result else default
    
    def list_settings(self):
        """모든 설정 조회"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('SELECT key, value, description FROM settings ORDER BY key')
        
        settings = []
        for row in cursor.fetchall():
            settings.append({
                'key': row[0],
                'value': row[1],
                'description': row[2]
            })
        return settings
    
    def delete_setting(self, key: str):
        """설정 삭제"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM settings WHERE key = ?', (key,))
        conn.commit()
        print(f"✅ 설정 삭제: {key}")
    
    # ==================== 알림 관련 ====================
    
    def check_alert_sent_today(self, user_id: int, ticker: str, alert_level: str) -> bool:
        """오늘 해당 종목/레벨의 알림이 이미 발송되었는지 확인
        
        Args:
            user_id: 사용자 ID
            ticker: 종목 코드
            alert_level: 알림 레벨 ('0.5x', '1x', '2x' 등)
        
        Returns:
            True: 이미 발송됨 (중복), False: 발송 안됨
        """
        from datetime import date
        
        conn = self.connect()
        cursor = conn.cursor()
        
        today = date.today().isoformat()
        
        cursor.execute('''
            SELECT id FROM alert_history 
            WHERE user_id = ? AND ticker = ? AND alert_date = ? AND alert_level = ?
        ''', (user_id, ticker, today, alert_level))
        
        return cursor.fetchone() is not None
    
    def record_alert(self, user_id: int, ticker: str, ticker_name: str, country: str,
                     alert_level: str, target_price: float, current_price: float, 
                     drop_rate: float, sent: bool = True, alert_date: str = None) -> bool:
        """알림 기록 저장 (중복 시 무시)
        
        Args:
            user_id: 사용자 ID
            ticker: 종목 코드
            ticker_name: 종목명
            country: 국가 (KR/US)
            alert_level: 알림 레벨 ('0.5x', '1x', '2x' 등)
            target_price: 목표가
            current_price: 현재가
            drop_rate: 하락률
            sent: 발송 여부
            alert_date: 알림 날짜 (None이면 오늘)
        
        Returns:
            True: 저장 성공 (새로운 알림), False: 중복으로 스킵
        """
        from datetime import date, datetime
        
        conn = self.connect()
        cursor = conn.cursor()
        
        today = alert_date or date.today().isoformat()
        now = datetime.now().isoformat()
        
        # 먼저 중복 체크 (UNIQUE 제약이 없는 기존 테이블 호환)
        cursor.execute('''
            SELECT id FROM alert_history 
            WHERE user_id = ? AND ticker = ? AND alert_date = ? AND alert_level = ?
        ''', (user_id, ticker, today, alert_level))
        
        if cursor.fetchone() is not None:
            # 이미 존재하면 스킵
            return False
        
        try:
            cursor.execute('''
                INSERT INTO alert_history 
                (user_id, ticker, ticker_name, country, alert_level, alert_date, 
                 target_price, current_price, drop_rate, alert_time, sent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, ticker, ticker_name, country, alert_level, today,
                  target_price, current_price, drop_rate, now, sent))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # 중복 (UNIQUE 제약 위반)
            return False
    
    def get_user_alerts(self, user_id: int, ticker: str = None, limit: int = 50) -> List[Dict]:
        """사용자 알림 내역 조회
        
        Args:
            user_id: 사용자 ID
            ticker: 종목 코드 (None이면 전체)
            limit: 최대 개수
        
        Returns:
            알림 내역 리스트 (최신순, 투자금액 포함)
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # 투자금액도 함께 조회 (user_watchlist 조인)
        if ticker:
            cursor.execute('''
                SELECT ah.id, ah.ticker, ah.ticker_name, ah.country, ah.alert_level, ah.alert_date,
                       ah.target_price, ah.current_price, ah.drop_rate, ah.alert_time, ah.sent,
                       uw.investment_amount
                FROM alert_history ah
                LEFT JOIN user_watchlist uw ON ah.user_id = uw.user_id AND ah.ticker = uw.ticker
                WHERE ah.user_id = ? AND ah.ticker = ?
                ORDER BY ah.alert_time DESC
                LIMIT ?
            ''', (user_id, ticker, limit))
        else:
            cursor.execute('''
                SELECT ah.id, ah.ticker, ah.ticker_name, ah.country, ah.alert_level, ah.alert_date,
                       ah.target_price, ah.current_price, ah.drop_rate, ah.alert_time, ah.sent,
                       uw.investment_amount
                FROM alert_history ah
                LEFT JOIN user_watchlist uw ON ah.user_id = uw.user_id AND ah.ticker = uw.ticker
                WHERE ah.user_id = ?
                ORDER BY ah.alert_time DESC
                LIMIT ?
            ''', (user_id, limit))
        
        alerts = []
        for row in cursor.fetchall():
            current_price = row[7]
            investment_amount = row[11]
            
            # 매수 수량 계산
            shares = 0
            if investment_amount and investment_amount > 0 and current_price and current_price > 0:
                shares = int(investment_amount / current_price)
            
            alerts.append({
                'id': row[0],
                'ticker': row[1],
                'ticker_name': row[2],
                'country': row[3],
                'alert_level': row[4],
                'alert_date': row[5],
                'target_price': row[6],
                'current_price': current_price,
                'drop_rate': row[8],
                'alert_time': row[9],
                'sent': row[10],
                'investment_amount': investment_amount,
                'shares': shares
            })
        return alerts
    
    def get_alerts_by_ticker(self, user_id: int) -> Dict[str, List[Dict]]:
        """종목별로 그룹화된 알림 내역 조회
        
        Returns:
            {ticker: [alerts...], ...} 형태
        """
        alerts = self.get_user_alerts(user_id, limit=200)
        
        by_ticker = {}
        for alert in alerts:
            ticker = alert['ticker']
            if ticker not in by_ticker:
                by_ticker[ticker] = []
            by_ticker[ticker].append(alert)
        
        return by_ticker


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

