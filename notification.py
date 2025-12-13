"""
통합 알림 모듈
설정에 따라 Telegram 또는 ntfy로 알림 전송
"""
from database import StockDatabase


def send_notification(user_id: int, message: str, title: str = None, photo_path: str = None) -> bool:
    """
    사용자에게 알림 전송 (설정에 따라 telegram 또는 ntfy)
    
    Args:
        user_id: 사용자 ID
        message: 알림 메시지
        title: 알림 제목 (ntfy용)
        photo_path: 이미지 경로 (telegram용)
    
    Returns:
        성공 여부
    """
    db = StockDatabase()
    
    # 알림 방식 확인
    notification_method = db.get_setting('notification_method', 'telegram')
    
    if notification_method == 'ntfy':
        return _send_ntfy(db, message, title)
    else:
        return _send_telegram(db, user_id, message, photo_path)


def _send_telegram(db: StockDatabase, user_id: int, message: str, photo_path: str = None) -> bool:
    """텔레그램으로 알림 전송"""
    try:
        from telegram_bot import send_telegram_sync
        
        bot_token = db.get_setting('bot_token')
        
        # 사용자 chat_id 조회
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        
        if not row:
            print(f"❌ 사용자 {user_id}를 찾을 수 없습니다.")
            db.close()
            return False
        
        chat_id = row[0]
        db.close()
        
        if not bot_token or not chat_id:
            print("❌ 텔레그램 설정이 없습니다.")
            return False
        
        send_telegram_sync(bot_token, chat_id, message=message, photo_path=photo_path)
        return True
        
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")
        db.close()
        return False


def _send_ntfy(db: StockDatabase, message: str, title: str = None) -> bool:
    """ntfy로 알림 전송"""
    try:
        from ntfy_alert import NtfyAlert
        
        topic = db.get_setting('ntfy_topic')
        server = db.get_setting('ntfy_server', 'https://ntfy.sh')
        db.close()
        
        if not topic:
            print("❌ ntfy 토픽이 설정되지 않았습니다.")
            return False
        
        ntfy = NtfyAlert(topic, server)
        return ntfy.send(message, title=title, priority=4)
        
    except Exception as e:
        print(f"❌ ntfy 전송 실패: {e}")
        db.close()
        return False


def send_stock_alert(user_id: int, ticker: str, name: str, current_price: float, 
                     target_price: float, signal_type: str = "매수", sigma: float = 1.0) -> bool:
    """
    주식 알림 전송
    """
    db = StockDatabase()
    notification_method = db.get_setting('notification_method', 'telegram')
    
    if notification_method == 'ntfy':
        try:
            from ntfy_alert import NtfyAlert
            
            topic = db.get_setting('ntfy_topic')
            server = db.get_setting('ntfy_server', 'https://ntfy.sh')
            db.close()
            
            if not topic:
                print("❌ ntfy 토픽이 설정되지 않았습니다.")
                return False
            
            ntfy = NtfyAlert(topic, server)
            return ntfy.send_stock_alert(ticker, name, current_price, target_price, signal_type, sigma)
            
        except Exception as e:
            print(f"❌ ntfy 주식 알림 실패: {e}")
            db.close()
            return False
    else:
        # 텔레그램 메시지 포맷
        message = f"""🚨 {signal_type} 신호!

📊 {name} ({ticker})
💰 현재가: ${current_price:,.2f}
🎯 목표가: ${target_price:,.2f} ({sigma}σ)
📈 신호: {signal_type}"""
        
        return _send_telegram(db, user_id, message)


def send_morning_report(user_id: int, report: str, photo_path: str = None) -> bool:
    """
    아침 리포트 전송
    """
    db = StockDatabase()
    notification_method = db.get_setting('notification_method', 'telegram')
    
    if notification_method == 'ntfy':
        try:
            from ntfy_alert import NtfyAlert
            
            topic = db.get_setting('ntfy_topic')
            server = db.get_setting('ntfy_server', 'https://ntfy.sh')
            db.close()
            
            if not topic:
                return False
            
            ntfy = NtfyAlert(topic, server)
            return ntfy.send_morning_report(report)
            
        except Exception as e:
            print(f"❌ ntfy 리포트 실패: {e}")
            db.close()
            return False
    else:
        return _send_telegram(db, user_id, report, photo_path)


# 간편 함수
def notify(message: str, title: str = None) -> bool:
    """
    기본 사용자에게 알림 전송 (user_id 1번)
    """
    return send_notification(1, message, title)


def notify_all_users(message: str, title: str = None) -> int:
    """
    모든 활성 사용자에게 알림 전송
    
    Returns:
        성공한 사용자 수
    """
    db = StockDatabase()
    
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE enabled = 1 AND notification_enabled = 1')
    users = cursor.fetchall()
    db.close()
    
    success_count = 0
    for (user_id,) in users:
        if send_notification(user_id, message, title):
            success_count += 1
    
    return success_count

