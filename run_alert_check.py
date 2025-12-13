#!/usr/bin/env python3
"""
실시간 알림 테스트 스크립트
- DB 기록 테스트
- ntfy 알림 전송 테스트
"""

from database import StockDatabase
from ntfy_alert import NtfyAlert
from datetime import datetime

def test_all():
    """전체 테스트"""
    
    db = StockDatabase()
    
    print("="*60)
    print("🔔 실시간 알림 테스트")
    print("="*60)
    
    # 1. 사용자 정보 확인
    print("\n[1] 👥 등록된 사용자 확인")
    users = db.get_all_users()
    
    if not users:
        print("❌ 등록된 사용자가 없습니다!")
        db.close()
        return
    
    for user in users:
        ntfy_topic = user.get('ntfy_topic', '미설정')
        print(f"  - {user['name']} (ID: {user['id']})")
        print(f"    ntfy_topic: {ntfy_topic}")
        print(f"    enabled: {user.get('enabled', False)}")
        print(f"    notification_enabled: {user.get('notification_enabled', False)}")
    
    # 2. 관심 종목 확인
    print("\n[2] 📋 관심 종목 확인")
    user = users[0]
    watchlist = db.get_user_watchlist_with_names(user['name'])
    
    if not watchlist:
        print(f"❌ {user['name']}님의 관심 종목이 없습니다!")
        db.close()
        return
    
    for stock in watchlist:
        print(f"  - {stock['name']} ({stock['ticker']}) - {stock['country']}")
    
    test_stock = watchlist[0]
    
    # 3. DB 기록 테스트
    print("\n[3] 💾 DB 알림 기록 테스트")
    
    test_data = {
        'user_id': user['id'],
        'ticker': test_stock['ticker'],
        'ticker_name': test_stock['name'],
        'country': test_stock['country'],
        'alert_level': '05x',
        'target_price': 100.0,
        'current_price': 99.0,
        'drop_rate': 1.0
    }
    
    # 오늘 중복 체크
    already_sent = db.check_alert_sent_today(
        user['id'], test_stock['ticker'], '05x'
    )
    print(f"  오늘 이미 발송됨: {already_sent}")
    
    if already_sent:
        print("  ⚠️ 오늘 이미 해당 알림이 발송되어 건너뜁니다.")
        print("  → 다른 alert_level ('1x', '2x')로 테스트하거나 내일 다시 시도하세요.")
    else:
        # DB에 기록
        result = db.record_alert(**test_data)
        print(f"  DB 기록 결과: {'✅ 성공' if result else '❌ 실패 (중복)'}")
    
    # 최근 알림 확인
    alerts = db.get_user_alerts(user['id'], limit=5)
    print(f"\n  📜 최근 알림 내역 ({len(alerts)}건):")
    for alert in alerts[:3]:
        print(f"    - {alert['ticker']} {alert['alert_level']} @ {alert['alert_date']}")
    
    # 4. ntfy 알림 테스트
    print("\n[4] 📤 ntfy 알림 전송 테스트")
    
    ntfy_topic = user.get('ntfy_topic')
    if not ntfy_topic:
        print(f"  ❌ {user['name']}님의 ntfy_topic이 설정되지 않았습니다!")
        print("  → 웹 설정에서 ntfy 토픽을 설정하세요.")
        db.close()
        return
    
    print(f"  ntfy 토픽: {ntfy_topic}")
    
    ntfy = NtfyAlert(ntfy_topic)
    
    # 단순 메시지 테스트
    print("\n  [4-1] 단순 메시지 테스트...")
    result1 = ntfy.send(
        message=f"🧪 테스트 알림 - 시간: {datetime.now().strftime('%H:%M:%S')}",
        title="알림 테스트"
    )
    print(f"  결과: {'✅ 성공' if result1 else '❌ 실패'}")
    
    # 주식 알림 테스트
    print("\n  [4-2] 주식 알림 테스트...")
    result2 = ntfy.send_stock_alert(
        ticker=test_stock['ticker'],
        name=test_stock['name'],
        current_price=99.0,
        target_price=100.0,
        signal_type="매수",
        sigma=0.5
    )
    print(f"  결과: {'✅ 성공' if result2 else '❌ 실패'}")
    
    print("\n" + "="*60)
    if result1 and result2:
        print("✅ 모든 테스트 완료! ntfy 앱에서 알림을 확인하세요.")
    else:
        print("⚠️ 일부 테스트 실패. 위 로그를 확인하세요.")
    print("="*60)
    
    db.close()

if __name__ == "__main__":
    test_all()
