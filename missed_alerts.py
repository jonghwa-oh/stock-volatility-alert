"""
놓친 알림 요약 (밤 사이 00:00~06:00)
매일 08:00에 실행
"""
from datetime import datetime, timedelta
from database import StockDatabase
from notification import send_notification


def send_missed_alerts_summary():
    """
    밤 사이 놓친 알림 요약 전송 (00:00~06:00)
    """
    print("\n" + "="*70)
    print("🌙 밤 사이 놓친 알림 확인")
    print("="*70)
    
    db = StockDatabase()
    
    # 오늘 00:00 ~ 06:00 사이 놓친 알림 조회
    today = datetime.now()
    start_time = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = today.replace(hour=6, minute=0, second=0, microsecond=0)
    
    conn = db.connect()
    cursor = conn.cursor()
    
    # 전송되지 않은 알림 조회
    cursor.execute('''
        SELECT ticker, ticker_name, country, alert_level, 
               target_price, current_price, drop_rate, alert_time
        FROM alert_history
        WHERE alert_time >= ? AND alert_time < ?
          AND sent = 0
        ORDER BY alert_time DESC
    ''', (start_time.isoformat(), end_time.isoformat()))
    
    missed_alerts = cursor.fetchall()
    
    if not missed_alerts:
        print("✅ 놓친 알림 없음")
        db.close()
        return
    
    print(f"📊 놓친 알림: {len(missed_alerts)}개")
    
    # 사용자별로 알림 전송
    users = db.get_all_users()
    
    for user in users:
        if not user['enabled'] or not user.get('notification_enabled'):
            continue
        
        # 해당 사용자의 관심 종목만 필터링
        user_watchlist = db.get_user_watchlist_with_names(user['name'])
        user_tickers = [stock['ticker'] for stock in user_watchlist]
        
        user_missed = [alert for alert in missed_alerts if alert[0] in user_tickers]
        
        if not user_missed:
            continue
        
        # 메시지 구성
        message = f"🌙 {user['name']}님, 밤 사이 매수 기회가 있었습니다!\n\n"
        message += f"📅 {today.strftime('%Y-%m-%d')} 새벽 (00:00~06:00)\n"
        message += f"🔔 총 {len(user_missed)}건의 알림\n\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"
        
        for idx, alert in enumerate(user_missed, 1):
            ticker, name, country, level, target, current, drop, alert_time = alert
            
            flag = '🇰🇷' if country == 'KR' else '🇺🇸'
            level_text = "1차" if level == '1x' else "2차"
            currency = "원" if country == 'KR' else "$"
            
            alert_dt = datetime.fromisoformat(alert_time)
            
            if country == 'KR':
                price_format = f"{current:,.0f}{currency}"
                target_format = f"{target:,.0f}{currency}"
            else:
                price_format = f"{currency}{current:,.2f}"
                target_format = f"{currency}{target:,.2f}"
            
            message += f"{idx}. {flag} {name} ({ticker})\n"
            message += f"   {level_text} 매수 시점 도달!\n"
            message += f"   시각: {alert_dt.strftime('%H:%M:%S')}\n"
            message += f"   가격: {price_format}\n"
            message += f"   목표가: {target_format} ({drop:.2f}% 하락)\n\n"
        
        message += "━━━━━━━━━━━━━━━━━━\n\n"
        message += "💡 실시간 알림은 09:00~24:00만 전송됩니다.\n"
        message += "   밤 사이 매수 기회는 다음 날 아침에 요약해드립니다."
        
        # ntfy로 전송
        try:
            result = send_notification(user['id'], message, title="🌙 밤 사이 놓친 알림")
            if result:
                print(f"  ✅ {user['name']}님에게 전송: {len(user_missed)}건")
            else:
                print(f"  ⚠️ {user['name']}님 전송 실패 (ntfy 토픽 미설정?)")
        except Exception as e:
            print(f"  ❌ {user['name']}님 전송 실패: {e}")
    
    # 전송 완료 표시
    cursor.execute('''
        UPDATE alert_history
        SET sent = 1
        WHERE alert_time >= ? AND alert_time < ?
    ''', (start_time.isoformat(), end_time.isoformat()))
    
    conn.commit()
    db.close()
    
    print("\n✅ 놓친 알림 요약 전송 완료!")
    print("="*70)


if __name__ == "__main__":
    send_missed_alerts_summary()
