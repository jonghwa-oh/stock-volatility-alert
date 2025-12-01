"""
스케줄러 설정
"""

# 스케줄 설정
SCHEDULE_CONFIG = {
    # 일일 분석 시간 (장 시작 전 매수 알림)
    'daily_analysis_time': '08:50',  # 오전 8시 50분 (장 시작 전)
    
    # 실시간 모니터링
    'realtime_check_interval': 5,  # 5분마다
    'realtime_enabled': True,
    
    # 운영 시간 (장이 열려있는 시간만 체크)
    'market_open_time': '09:00',
    'market_close_time': '15:30',
    
    # 요일 (0=월요일, 6=일요일)
    'trading_days': [0, 1, 2, 3, 4],  # 월-금
}

# 모니터링 종목 리스트 (최대 20개)
WATCH_LIST = {
    # 한국 지수
    'KS200': '코스피200',
    
    # 레버리지 ETF
    'TQQQ': 'ProShares UltraPro QQQ',
    'QLD': 'ProShares Ultra QQQ',
    'SOXL': 'Direxion Daily Semiconductor Bull 3X',
    'UPRO': 'ProShares UltraPro S&P500',
    'TECL': 'Direxion Daily Technology Bull 3X',
    
    # 일반 ETF
    'SPY': 'S&P 500 ETF',
    'QQQ': 'Invesco QQQ Trust',
    'IWM': 'Russell 2000 ETF',
    'DIA': 'Dow Jones ETF',
    'VOO': 'Vanguard S&P 500 ETF',
    'VTI': 'Vanguard Total Stock Market ETF',
    
    # 섹터 ETF
    'XLK': 'Technology Select Sector',
    'XLF': 'Financial Select Sector',
    'XLE': 'Energy Select Sector',
    'XLV': 'Health Care Select Sector',
    
    # 개별 종목 (원하면 추가)
    # 'AAPL': 'Apple',
    # 'MSFT': 'Microsoft',
    # 'NVDA': 'NVIDIA',
    # 'TSLA': 'Tesla',
}

# 알림 설정
ALERT_CONFIG = {
    # 1시그마 도달 시
    'alert_1sigma': True,
    'alert_1sigma_threshold': 0.95,  # 1시그마의 95% 도달 시 알림
    
    # 2시그마 도달 시
    'alert_2sigma': True,
    'alert_2sigma_threshold': 0.95,  # 2시그마의 95% 도달 시 알림
    
    # 중복 알림 방지 (같은 종목 재알림까지 최소 시간, 분)
    'alert_cooldown_minutes': 60,
}

