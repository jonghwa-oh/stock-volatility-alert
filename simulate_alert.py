#!/usr/bin/env python3
"""
과거 분봉 데이터 기반 알림 시뮬레이션
- 특정 날짜의 분봉 데이터를 순회하며 알림 발생 시점 확인
- 실제 알림 발송 테스트 가능
"""

import argparse
import numpy as np
from datetime import datetime, date
from database import StockDatabase
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
    
    # 1. 전일 종가 및 변동성 계산
    print("[1] 📈 전일 종가 기준 분석...")
    
    conn = db.connect()
    cursor = conn.cursor()
    
    # 종목 정보 가져오기
    cursor.execute('''
        SELECT DISTINCT ticker_name FROM minute_prices WHERE ticker = ?
    ''', (ticker,))
    row = cursor.fetchone()
    name = row[0] if row else ticker
    
    # 국가 판별
    country = 'KR' if ticker.isdigit() or (len(ticker) == 6 and ticker[0].isdigit()) else 'US'
    
    # 전일 종가 가져오기 (시뮬레이션 날짜 직전 거래일)
    from kis_api import KISApi
    kis = KISApi()
    
    if country == 'US':
        exchange = kis.get_exchange_code(ticker)
        df = kis.get_overseas_daily_price_history(ticker, exchange)
    else:
        df = kis.get_daily_price_history(ticker)
    
    kis.close()
    
    if df is None or df.empty:
        print(f"❌ {ticker} 일봉 데이터 없음")
        db.close()
        return
    
    # 시뮬레이션 날짜의 전일 종가 찾기
    target_dt = datetime.strptime(target_date, '%Y-%m-%d').date()
    
    # 날짜 인덱스 처리
    df_dates = df.index.date if hasattr(df.index, 'date') else df.index
    prev_close = None
    prev_date = None
    
    for i, d in enumerate(df_dates):
        if d >= target_dt and i > 0:
            prev_close = float(df['Close'].iloc[i-1])
            prev_date = df_dates[i-1]
            break
    
    if prev_close is None:
        # 마지막 날짜 이전 데이터 사용
        if len(df) >= 2:
            prev_close = float(df['Close'].iloc[-2])
            prev_date = df_dates[-2]
        else:
            print(f"❌ 전일 종가를 찾을 수 없습니다")
            db.close()
            return
    
    # 변동성 계산 (최근 20일 기준)
    returns = df['Close'].pct_change().dropna() * 100
    std_return = float(returns.tail(20).std())
    
    # 목표가 계산
    target_05x = prev_close * (1 - std_return * 0.5 / 100)
    target_1x = prev_close * (1 - std_return / 100)
    target_2x = prev_close * (1 - std_return * 2 / 100)
    
    drop_05x = std_return * 0.5
    drop_1x = std_return
    drop_2x = std_return * 2
    
    analysis = {
        'current_price': prev_close,
        'std_return': std_return,
        'target_05x': target_05x,
        'target_1x': target_1x,
        'target_2x': target_2x,
        'drop_05x': drop_05x,
        'drop_1x': drop_1x,
        'drop_2x': drop_2x
    }
    
    print(f"   종목: {name} ({ticker})")
    print(f"   국가: {country}")
    print(f"   기준일: {prev_date} (전일)")
    print(f"   전일종가: ${prev_close:.2f}" if country == 'US' else f"   전일종가: {prev_close:,.0f}원")
    print(f"   일일 변동성: {std_return:.2f}%")
    print(f"\n   🎯 {target_date} 목표가 (전일종가 기준):")
    if country == 'US':
        print(f"      0.5σ: ${target_05x:.2f} ({drop_05x:.2f}% 하락)")
        print(f"      1σ:   ${target_1x:.2f} ({drop_1x:.2f}% 하락)")
        print(f"      2σ:   ${target_2x:.2f} ({drop_2x:.2f}% 하락)")
    else:
        print(f"      0.5σ: {target_05x:,.0f}원 ({drop_05x:.2f}% 하락)")
        print(f"      1σ:   {target_1x:,.0f}원 ({drop_1x:.2f}% 하락)")
        print(f"      2σ:   {target_2x:,.0f}원 ({drop_2x:.2f}% 하락)")
    
    # 2. 해당 날짜 분봉 데이터 가져오기
    print(f"\n[2] 📊 {target_date} 분봉 데이터 조회...")
    
    # 미국 주식은 market_date (미국 거래일) 기준, 한국 주식은 datetime 기준
    if country == 'US':
        # market_date 컬럼이 있으면 사용 (yfinance로 수집된 데이터)
        cursor.execute('''
            SELECT datetime, price, volume 
            FROM minute_prices 
            WHERE ticker = ? AND market_date = ?
            ORDER BY datetime ASC
        ''', (ticker, target_date))
        
        minute_data = cursor.fetchall()
        
        # market_date가 없으면 기존 방식으로 fallback
        if not minute_data:
            print(f"   ⚠️ market_date 데이터 없음, datetime 기준으로 조회...")
            cursor.execute('''
                SELECT datetime, price, volume 
                FROM minute_prices 
                WHERE ticker = ? AND date(datetime) = ?
                ORDER BY datetime ASC
            ''', (ticker, target_date))
            minute_data = cursor.fetchall()
    else:
        # 한국 주식은 datetime 기준
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
    
    # 5. 실제 알림 발송 (옵션) - 중복 체크 후 발송
    if send_alert and alert_count > 0:
        print(f"\n[5] 📤 실제 알림 발송 (중복 체크 적용)...")
        
        from notification import send_stock_alert_to_all_with_check
        
        # 발생한 모든 알림 발송 (중복 체크 포함)
        for level in ['05x', '1x', '2x']:
            alert = alerts_triggered[level]
            if alert:
                level_name = {'05x': '테스트', '1x': '1차', '2x': '2차'}[level]
                sigma = {'05x': 0.5, '1x': 1.0, '2x': 2.0}[level]
                
                print(f"\n   📤 {level_name} 매수 알림 발송 중...")
                
                # 중복 체크 + DB 저장 + 알림 발송 (일괄 처리)
                success_count, skip_count = send_stock_alert_to_all_with_check(
                    ticker=ticker,
                    name=name,
                    current_price=alert['price'],
                    target_price=alert['target'],
                    signal_type=f"{level_name} 매수",
                    sigma=sigma,
                    country=country,
                    prev_close=prev_close,
                    alert_level=level,
                    drop_rate=alert['drop']
                )
                
                if success_count > 0:
                    print(f"   ✅ {success_count}명에게 알림 발송 완료!")
                if skip_count > 0:
                    print(f"   ⏭️ {skip_count}명 중복으로 스킵")
                if success_count == 0 and skip_count == 0:
                    print(f"   ⚠️ 알림 대상자 없음 ({ticker} 관심 종목 등록 필요)")
    
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

