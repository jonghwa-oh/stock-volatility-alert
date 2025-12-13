#!/usr/bin/env python3
"""
과거 분봉 데이터 기반 알림 시뮬레이션
- 특정 날짜의 분봉 데이터를 순회하며 알림 발생 시점 확인
- 실제 알림 발송 테스트 가능
"""

import argparse
from datetime import datetime, date
from database import StockDatabase
from volatility_analysis import analyze_daily_volatility
from ntfy_alert import NtfyAlert

def simulate_alerts(ticker: str, target_date: str, send_alert: bool = False):
    """
    과거 분봉 데이터로 알림 시뮬레이션
    
    Args:
        ticker: 종목 코드
        target_date: 시뮬레이션 날짜 (YYYY-MM-DD)
        send_alert: True면 실제 알림 발송
    """
    db = StockDatabase()
    
    print(f"\n{'='*60}")
    print(f"📊 알림 시뮬레이션: {ticker}")
    print(f"📅 날짜: {target_date}")
    print(f"🔔 알림 발송: {'예' if send_alert else '아니오 (테스트만)'}")
    print(f"{'='*60}\n")
    
    # 1. 종목 분석 데이터 가져오기
    print("[1] 📈 종목 분석...")
    
    # 종목 정보 가져오기
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT ticker_name FROM minute_prices WHERE ticker = ?
    ''', (ticker,))
    row = cursor.fetchone()
    name = row[0] if row else ticker
    
    # 국가 판별
    country = 'KR' if ticker.isdigit() or (len(ticker) == 6 and ticker[0].isdigit()) else 'US'
    
    # 분석 실행 (목표가 계산)
    analysis = analyze_daily_volatility(ticker, name, country=country, create_chart=False)
    
    if not analysis:
        print(f"❌ {ticker} 분석 실패")
        db.close()
        return
    
    print(f"   종목: {name} ({ticker})")
    print(f"   국가: {country}")
    print(f"   기준가: ${analysis['base_price']:.2f}" if country == 'US' else f"   기준가: {analysis['base_price']:,.0f}원")
    print(f"   일일 변동성: {analysis['std_return']:.2f}%")
    print(f"\n   🎯 목표가:")
    if country == 'US':
        print(f"      0.5σ: ${analysis['target_05x']:.2f} ({analysis['drop_05x']:.2f}% 하락)")
        print(f"      1σ:   ${analysis['target_1x']:.2f} ({analysis['drop_1x']:.2f}% 하락)")
        print(f"      2σ:   ${analysis['target_2x']:.2f} ({analysis['drop_2x']:.2f}% 하락)")
    else:
        print(f"      0.5σ: {analysis['target_05x']:,.0f}원 ({analysis['drop_05x']:.2f}% 하락)")
        print(f"      1σ:   {analysis['target_1x']:,.0f}원 ({analysis['drop_1x']:.2f}% 하락)")
        print(f"      2σ:   {analysis['target_2x']:,.0f}원 ({analysis['drop_2x']:.2f}% 하락)")
    
    # 2. 해당 날짜 분봉 데이터 가져오기
    print(f"\n[2] 📊 {target_date} 분봉 데이터 조회...")
    
    cursor.execute('''
        SELECT datetime, price, volume 
        FROM minute_prices 
        WHERE ticker = ? AND date(datetime) = ?
        ORDER BY datetime ASC
    ''', (ticker, target_date))
    
    minute_data = cursor.fetchall()
    
    if not minute_data:
        print(f"❌ {target_date} 분봉 데이터 없음")
        db.close()
        return
    
    print(f"   분봉 데이터: {len(minute_data)}건")
    print(f"   시작: {minute_data[0][0]}")
    print(f"   종료: {minute_data[-1][0]}")
    
    # 3. 분봉 순회하며 알림 시점 찾기
    print(f"\n[3] 🔍 알림 시점 분석...")
    
    alerts_triggered = {
        '05x': None,
        '1x': None,
        '2x': None
    }
    
    open_price = minute_data[0][1]
    high_price = minute_data[0][1]
    low_price = minute_data[0][1]
    
    for dt_str, price, volume in minute_data:
        high_price = max(high_price, price)
        low_price = min(low_price, price)
        
        # 0.5σ 목표가 도달
        if alerts_triggered['05x'] is None and price <= analysis['target_05x']:
            alerts_triggered['05x'] = {
                'time': dt_str,
                'price': price,
                'target': analysis['target_05x'],
                'drop': analysis['drop_05x']
            }
        
        # 1σ 목표가 도달
        if alerts_triggered['1x'] is None and price <= analysis['target_1x']:
            alerts_triggered['1x'] = {
                'time': dt_str,
                'price': price,
                'target': analysis['target_1x'],
                'drop': analysis['drop_1x']
            }
        
        # 2σ 목표가 도달
        if alerts_triggered['2x'] is None and price <= analysis['target_2x']:
            alerts_triggered['2x'] = {
                'time': dt_str,
                'price': price,
                'target': analysis['target_2x'],
                'drop': analysis['drop_2x']
            }
    
    close_price = minute_data[-1][1]
    day_change = ((close_price - open_price) / open_price) * 100
    
    print(f"\n   📈 당일 요약:")
    print(f"      시가: ${open_price:.2f}" if country == 'US' else f"      시가: {open_price:,.0f}원")
    print(f"      고가: ${high_price:.2f}" if country == 'US' else f"      고가: {high_price:,.0f}원")
    print(f"      저가: ${low_price:.2f}" if country == 'US' else f"      저가: {low_price:,.0f}원")
    print(f"      종가: ${close_price:.2f}" if country == 'US' else f"      종가: {close_price:,.0f}원")
    print(f"      등락: {day_change:+.2f}%")
    
    # 4. 알림 결과 출력
    print(f"\n[4] 🔔 알림 발생 결과:")
    
    alert_count = 0
    for level, alert in alerts_triggered.items():
        level_name = {'05x': '🧪 테스트(0.5σ)', '1x': '1차(1σ)', '2x': '2차(2σ)'}[level]
        
        if alert:
            alert_count += 1
            print(f"\n   ✅ {level_name} 알림 발생!")
            print(f"      시간: {alert['time']}")
            if country == 'US':
                print(f"      가격: ${alert['price']:.2f} (목표: ${alert['target']:.2f})")
            else:
                print(f"      가격: {alert['price']:,.0f}원 (목표: {alert['target']:,.0f}원)")
            print(f"      하락률: {alert['drop']:.2f}%")
        else:
            print(f"\n   ❌ {level_name} 알림 미발생 (목표가 미도달)")
    
    # 5. 실제 알림 발송 (옵션)
    if send_alert and alert_count > 0:
        print(f"\n[5] 📤 실제 알림 발송...")
        
        users = db.get_all_users()
        for user in users:
            ntfy_topic = user.get('ntfy_topic')
            if not ntfy_topic:
                continue
            
            ntfy = NtfyAlert(ntfy_topic)
            
            # 시뮬레이션 결과 알림
            message = f"📊 {target_date} 알림 시뮬레이션 결과\n\n"
            message += f"종목: {name} ({ticker})\n"
            message += f"당일 등락: {day_change:+.2f}%\n\n"
            
            for level, alert in alerts_triggered.items():
                level_name = {'05x': '0.5σ', '1x': '1σ', '2x': '2σ'}[level]
                if alert:
                    message += f"✅ {level_name}: {alert['time'][11:16]} @ ${alert['price']:.2f}\n"
                else:
                    message += f"❌ {level_name}: 미도달\n"
            
            result = ntfy.send(message, title=f"📈 {ticker} 시뮬레이션")
            print(f"   {user['name']}: {'✅ 발송 성공' if result else '❌ 발송 실패'}")
    
    print(f"\n{'='*60}")
    print(f"✅ 시뮬레이션 완료! 총 {alert_count}건 알림 발생")
    print(f"{'='*60}\n")
    
    db.close()


def main():
    parser = argparse.ArgumentParser(description='과거 분봉 데이터 알림 시뮬레이션')
    parser.add_argument('--ticker', '-t', required=True, help='종목 코드')
    parser.add_argument('--date', '-d', required=True, help='시뮬레이션 날짜 (YYYY-MM-DD)')
    parser.add_argument('--send', '-s', action='store_true', help='실제 알림 발송')
    
    args = parser.parse_args()
    
    simulate_alerts(args.ticker, args.date, args.send)


if __name__ == "__main__":
    main()

