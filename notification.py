"""
통합 알림 모듈 (ntfy 전용)
사용자별 ntfy 토픽으로 알림 전송
"""
from database import StockDatabase
from ntfy_alert import NtfyAlert


def send_notification(user_id: int, message: str, title: str = None) -> bool:
    """
    사용자에게 ntfy 알림 전송
    
    Args:
        user_id: 사용자 ID
        message: 알림 메시지
        title: 알림 제목
    
    Returns:
        성공 여부
    """
    db = StockDatabase()
    
    # 사용자별 ntfy 토픽 조회
    topic = db.get_user_ntfy_topic(user_id)
    db.close()
    
    if not topic:
        print(f"❌ 사용자 {user_id}의 ntfy 토픽이 설정되지 않았습니다.")
        return False
    
    ntfy = NtfyAlert(topic)
    return ntfy.send(message, title=title, priority=4)


def send_stock_alert(user_id: int, ticker: str, name: str, current_price: float, 
                     target_price: float, signal_type: str = "매수", sigma: float = 1.0,
                     country: str = 'US') -> bool:
    """
    주식 알림 전송
    """
    db = StockDatabase()
    topic = db.get_user_ntfy_topic(user_id)
    db.close()
    
    if not topic:
        print(f"❌ 사용자 {user_id}의 ntfy 토픽이 설정되지 않았습니다.")
        return False
    
    ntfy = NtfyAlert(topic)
    
    # 통화 기호 결정
    currency = '₩' if country == 'KR' else '$'
    
    return ntfy.send_stock_alert(ticker, name, current_price, target_price, signal_type, sigma)


def send_morning_report(user_id: int, report: str) -> bool:
    """
    아침 리포트 전송
    """
    db = StockDatabase()
    topic = db.get_user_ntfy_topic(user_id)
    db.close()
    
    if not topic:
        print(f"❌ 사용자 {user_id}의 ntfy 토픽이 설정되지 않았습니다.")
        return False
    
    ntfy = NtfyAlert(topic)
    return ntfy.send_morning_report(report)


def notify_all_users(message: str, title: str = None) -> int:
    """
    모든 활성 사용자에게 알림 전송
    
    Returns:
        성공한 사용자 수
    """
    db = StockDatabase()
    
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, ntfy_topic FROM users 
        WHERE enabled = 1 AND notification_enabled = 1 AND ntfy_topic IS NOT NULL
    ''')
    users = cursor.fetchall()
    db.close()
    
    success_count = 0
    for user_id, topic in users:
        if topic:
            ntfy = NtfyAlert(topic)
            if ntfy.send(message, title=title, priority=4):
                success_count += 1
    
    return success_count


def send_stock_alert_to_all(ticker: str, name: str, current_price: float,
                            target_price: float, signal_type: str = "매수", 
                            sigma: float = 1.0, country: str = 'US') -> int:
    """
    모든 활성 사용자에게 주식 알림 전송
    (해당 종목을 관심 종목으로 등록한 사용자만)
    
    Returns:
        성공한 사용자 수
    """
    db = StockDatabase()
    
    conn = db.connect()
    cursor = conn.cursor()
    
    # 해당 종목을 관심 종목으로 등록하고, ntfy 토픽이 설정된 활성 사용자 조회
    cursor.execute('''
        SELECT DISTINCT u.id, u.ntfy_topic 
        FROM users u
        JOIN user_watchlist uw ON u.id = uw.user_id
        WHERE u.enabled = 1 
          AND u.notification_enabled = 1 
          AND u.ntfy_topic IS NOT NULL
          AND uw.ticker = ?
          AND uw.enabled = 1
    ''', (ticker,))
    
    users = cursor.fetchall()
    db.close()
    
    if not users:
        print(f"⚠️ {ticker} 종목을 관심 종목으로 등록한 활성 사용자가 없습니다.")
        return 0
    
    success_count = 0
    for user_id, topic in users:
        if topic:
            ntfy = NtfyAlert(topic)
            if ntfy.send_stock_alert(ticker, name, current_price, target_price, signal_type, sigma):
                success_count += 1
                print(f"✅ 사용자 {user_id}에게 {ticker} 알림 전송 완료")
    
    return success_count


# 테스트
if __name__ == "__main__":
    # 모든 사용자에게 테스트 알림
    count = notify_all_users("테스트 알림입니다! 🎉", "📊 주식 알림 테스트")
    print(f"✅ {count}명에게 알림 전송 완료")
