"""
설정 파일
설정은 stock_data.db의 settings 테이블에서 로드
"""

from database import StockDatabase


def load_config():
    """DB에서 설정 로드"""
    try:
        db = StockDatabase()
        
        # 텔레그램 설정
        bot_token = db.get_setting('bot_token')
        default_chat_id = db.get_setting('default_chat_id')
        
        db.close()
        
        return {
            'TELEGRAM_CONFIG': {
                'BOT_TOKEN': bot_token,
                'CHAT_ID': default_chat_id,
            }
        }
    except Exception as e:
        print(f"⚠️  설정 로드 실패: {e}")
        print("user_manager.py를 실행하여 봇 설정을 입력하세요.")
        # 기본값 반환
        return {
            'TELEGRAM_CONFIG': {
                'BOT_TOKEN': None,
                'CHAT_ID': None,
            }
        }


# 설정 로드
_config = load_config()
TELEGRAM_CONFIG = _config['TELEGRAM_CONFIG']


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

