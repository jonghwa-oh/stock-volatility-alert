"""
설정 파일
민감한 정보는 암호화된 DB에서 로드
"""

from secrets_manager import SecretsManager


def load_config():
    """암호화된 DB에서 설정 로드"""
    try:
        sm = SecretsManager()
        
        # 텔레그램 설정
        bot_token = sm.get_secret('BOT_TOKEN')
        chat_id = sm.get_secret('CHAT_ID')
        
        if not bot_token or not chat_id:
            raise ValueError(
                "텔레그램 설정이 없습니다!\n"
                "python setup_secrets.py를 먼저 실행하세요."
            )
        
        # 투자 설정
        default_amount = sm.get_secret('DEFAULT_AMOUNT', '1000000')
        
        return {
            'TELEGRAM_CONFIG': {
                'BOT_TOKEN': bot_token,
                'CHAT_ID': chat_id,
            },
            'INVESTMENT_CONFIG': {
                'default_amount': int(default_amount),
            }
        }
    except Exception as e:
        print(f"⚠️  설정 로드 실패: {e}")
        print("python setup_secrets.py를 실행하여 설정하세요.")
        raise


# 설정 로드
_config = load_config()
TELEGRAM_CONFIG = _config['TELEGRAM_CONFIG']
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

