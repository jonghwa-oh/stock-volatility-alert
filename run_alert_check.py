#!/usr/bin/env python3
"""
실시간 알림 테스트 스크립트
- 특정 종목의 목표가를 현재가보다 높게 설정해서 알림 발생 유도
"""

import asyncio
from database import StockDatabase
from realtime_monitor_hybrid import HybridMonitor

async def test_alert():
    """알림 테스트 - 목표가를 현재가보다 높게 설정"""
    
    db = StockDatabase()
    monitor = HybridMonitor()
    
    # 사용자 정보 확인
    users = db.get_all_users()
    print("\n👥 등록된 사용자:")
    for user in users:
        ntfy_topic = user.get('ntfy_topic', '미설정')
        print(f"  - {user['name']} (ID: {user['id']}, ntfy: {ntfy_topic})")
    
    # 관심 종목 확인
    if users:
        user = users[0]
        watchlist = db.get_user_watchlist_with_names(user['name'])
        print(f"\n📋 {user['name']}님의 관심 종목:")
        for stock in watchlist:
            print(f"  - {stock['name']} ({stock['ticker']}) - {stock['country']}")
    
    # 모니터 초기화 (목표가 계산)
    print("\n📊 모니터 초기화 중...")
    await monitor.initialize()
    
    if not monitor.target_prices:
        print("❌ 목표가가 설정된 종목이 없습니다.")
        db.close()
        return
    
    # 첫 번째 종목으로 테스트
    test_ticker = list(monitor.target_prices.keys())[0]
    targets = monitor.target_prices[test_ticker]
    
    print(f"\n🧪 테스트 종목: {targets['name']} ({test_ticker})")
    print(f"   국가: {targets['country']}")
    print(f"   0.5σ 목표가: {targets['05x']}")
    print(f"   1σ 목표가: {targets['1x']}")
    print(f"   2σ 목표가: {targets['2x']}")
    
    # 테스트: 목표가보다 낮은 가격으로 알림 트리거
    # 0.5σ 목표가보다 약간 낮은 가격 사용
    test_price = targets['05x'] * 0.99  # 목표가의 99%
    
    print(f"\n🚀 테스트 알림 발송 (가격: {test_price:.2f})")
    print("="*50)
    
    await monitor.check_and_alert(test_ticker, test_price)
    
    print("="*50)
    print("✅ 테스트 완료! ntfy 앱에서 알림을 확인하세요.")
    
    # 알림 내역 확인
    if users:
        alerts = db.get_user_alerts(users[0]['id'], limit=5)
        if alerts:
            print(f"\n📜 최근 알림 내역:")
            for alert in alerts[:3]:
                print(f"  - {alert['ticker_name']} ({alert['ticker']}) {alert['alert_level']} @ {alert['alert_time']}")
    
    db.close()

if __name__ == "__main__":
    print("="*50)
    print("🔔 실시간 알림 테스트")
    print("="*50)
    
    asyncio.run(test_alert())

