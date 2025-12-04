#!/usr/bin/env python3
"""
한국 주식 종목명 업데이트 스크립트
DB에 저장된 한국 주식의 ticker_name을 KIS API에서 조회하여 업데이트합니다.
"""
from database import StockDatabase
from kis_api import KISApi

def update_korean_stock_names():
    """한국 주식 종목명 업데이트"""
    print("="*60)
    print("🇰🇷 한국 주식 종목명 업데이트")
    print("="*60)
    
    db = StockDatabase()
    kis = KISApi()
    
    conn = db.connect()
    cursor = conn.cursor()
    
    # 1. 한국 주식 조회 (country='KR' 또는 숫자 티커)
    cursor.execute('''
        SELECT DISTINCT ticker, ticker_name 
        FROM daily_prices 
        WHERE country = 'KR' OR (ticker GLOB '[0-9]*' AND length(ticker) = 6)
    ''')
    kr_stocks = cursor.fetchall()
    
    print(f"\n📊 발견된 한국 주식: {len(kr_stocks)}개\n")
    
    updated_count = 0
    failed_count = 0
    
    for ticker, current_name in kr_stocks:
        print(f"  {ticker}: {current_name}", end=" → ")
        
        # 이미 종목명이 있고 티커와 다르면 스킵
        if current_name and current_name != ticker:
            print(f"(유지)")
            continue
        
        # KIS API에서 종목명 조회
        try:
            price_data = kis.get_stock_price(ticker)
            if price_data and 'name' in price_data and price_data['name']:
                new_name = price_data['name']
                
                # DB 업데이트
                cursor.execute('''
                    UPDATE daily_prices 
                    SET ticker_name = ? 
                    WHERE ticker = ?
                ''', (new_name, ticker))
                
                print(f"✅ {new_name}")
                updated_count += 1
            else:
                print(f"❌ API 응답 없음")
                failed_count += 1
        except Exception as e:
            print(f"❌ 오류: {e}")
            failed_count += 1
    
    conn.commit()
    
    # 2. user_watchlist의 country도 확인/업데이트
    print("\n" + "="*60)
    print("📋 user_watchlist country 확인")
    print("="*60)
    
    cursor.execute('''
        SELECT DISTINCT ticker, country 
        FROM user_watchlist 
        WHERE ticker GLOB '[0-9]*' AND length(ticker) = 6 AND country != 'KR'
    ''')
    wrong_country = cursor.fetchall()
    
    if wrong_country:
        print(f"\n⚠️  잘못된 country 발견: {len(wrong_country)}개")
        for ticker, country in wrong_country:
            print(f"  {ticker}: {country} → KR")
            cursor.execute('''
                UPDATE user_watchlist SET country = 'KR' WHERE ticker = ?
            ''', (ticker,))
        conn.commit()
        print(f"✅ country 수정 완료")
    else:
        print("\n✅ 모든 country가 정상입니다.")
    
    db.close()
    
    print("\n" + "="*60)
    print(f"📊 결과 요약")
    print(f"  • 업데이트 성공: {updated_count}개")
    print(f"  • 업데이트 실패: {failed_count}개")
    print("="*60)


def show_current_data():
    """현재 DB 데이터 확인"""
    print("\n" + "="*60)
    print("📋 현재 DB 데이터")
    print("="*60)
    
    db = StockDatabase()
    conn = db.connect()
    cursor = conn.cursor()
    
    # daily_prices
    print("\n📊 daily_prices (한국 주식):")
    cursor.execute('''
        SELECT DISTINCT ticker, ticker_name, country 
        FROM daily_prices 
        WHERE country = 'KR' OR ticker GLOB '[0-9]*'
        LIMIT 20
    ''')
    for row in cursor.fetchall():
        ticker, name, country = row
        status = "✅" if name and name != ticker else "❌"
        print(f"  {status} {ticker}: {name} [{country}]")
    
    # user_watchlist
    print("\n📋 user_watchlist:")
    cursor.execute('''
        SELECT uw.ticker, uw.country, dp.ticker_name
        FROM user_watchlist uw
        LEFT JOIN (
            SELECT ticker, MAX(ticker_name) as ticker_name 
            FROM daily_prices 
            GROUP BY ticker
        ) dp ON uw.ticker = dp.ticker
    ''')
    for row in cursor.fetchall():
        ticker, country, name = row
        flag = "🇰🇷" if country == 'KR' else "🇺🇸"
        print(f"  {flag} {ticker}: {name}")
    
    db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        show_current_data()
    else:
        show_current_data()
        print("\n")
        update_korean_stock_names()
        print("\n")
        show_current_data()

