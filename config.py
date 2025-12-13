"""
설정 파일
설정은 stock_data.db의 settings 테이블에서 로드
"""

from database import StockDatabase


def load_config():
    """DB에서 설정 로드"""
    try:
        db = StockDatabase()
        
        # ntfy 설정 (전역 기본값, 실제로는 사용자별 토픽 사용)
        ntfy_server = db.get_setting('ntfy_server', 'https://ntfy.sh')
        
        # 투자 설정
        default_amount = db.get_setting('default_investment_amount', '1000000')
        
        db.close()
        
        return {
            'NTFY_CONFIG': {
                'SERVER': ntfy_server,
            },
            'INVESTMENT_CONFIG': {
                'default_amount': int(default_amount),
            }
        }
    except Exception as e:
        print(f"⚠️  설정 로드 실패: {e}")
        # 기본값 반환
        return {
            'NTFY_CONFIG': {
                'SERVER': 'https://ntfy.sh',
            },
            'INVESTMENT_CONFIG': {
                'default_amount': 1000000,
            }
        }


# 설정 로드
_config = load_config()
NTFY_CONFIG = _config['NTFY_CONFIG']
INVESTMENT_CONFIG = _config['INVESTMENT_CONFIG']


# 분석 종목 (여기는 민감한 정보 아니므로 그대로)
STOCKS = {
    'KS200': '코스피200',
    'TQQQ': 'ProShares UltraPro QQQ',
    'QLD': 'ProShares Ultra QQQ',
    'SOXL': 'Direxion Daily Semiconductor Bull 3X',
    'SPY': 'S&P 500 ETF',
    'QQQ': 'Invesco QQQ Trust',
}

# 알림 설정
ALERT_CONFIG = {
    'send_daily_report': True,      # 일일 리포트 전송 (월-금)
    'send_buy_signals': True,       # 매수 신호 전송
    'alert_threshold': 0.8,         # 표준편차의 80% 이상 하락 시 알림
}
