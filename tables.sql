-- =====================================================
-- 주식 알림 시스템 데이터베이스 스키마
-- SQLite3
-- =====================================================

-- 일봉 데이터 테이블
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
);

-- 분봉 데이터 테이블
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
);

-- 통계 캐시 테이블 (표준편차 등)
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
);

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    password_hash TEXT,
    ntfy_topic TEXT,
    enabled BOOLEAN DEFAULT 1,
    notification_enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 사용자별 관심 종목 테이블
CREATE TABLE IF NOT EXISTS user_watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    name TEXT,
    country TEXT DEFAULT 'US',
    investment_amount REAL,
    enabled BOOLEAN DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, ticker)
);

-- 설정 테이블 (봇 토큰, 기본값 등)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 알림 이력 테이블 (놓친 알림 추적 + 중복 방지)
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
);

-- =====================================================
-- 인덱스
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_daily_ticker_date ON daily_prices(ticker, date);
CREATE INDEX IF NOT EXISTS idx_minute_ticker_datetime ON minute_prices(ticker, datetime);
CREATE INDEX IF NOT EXISTS idx_stats_ticker_date ON statistics_cache(ticker, date);
CREATE INDEX IF NOT EXISTS idx_user_watchlist ON user_watchlist(user_id, ticker);
CREATE INDEX IF NOT EXISTS idx_alert_history_user ON alert_history(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_history_ticker ON alert_history(ticker);

