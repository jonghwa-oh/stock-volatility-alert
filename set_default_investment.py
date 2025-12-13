"""
기존 종목에 기본 투자금액 설정
- 한국 주식: 1,000,000원
- 미국 주식: $1,000
"""
import sqlite3


def set_default_investment(db_path='data/stock_data.db'):
    """기존 종목에 기본 투자금액 설정"""
    
    print("=" * 60)
    print("💰 기존 종목 기본 투자금액 설정")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 한국 주식: 1,000,000원
    cursor.execute('''
        UPDATE user_watchlist 
        SET investment_amount = 1000000 
        WHERE country = 'KR' AND (investment_amount IS NULL OR investment_amount = 0)
    ''')
    kr_count = cursor.rowcount
    print(f"🇰🇷 한국 주식 {kr_count}개 → 1,000,000원")
    
    # 미국 주식: $1,000
    cursor.execute('''
        UPDATE user_watchlist 
        SET investment_amount = 1000 
        WHERE country = 'US' AND (investment_amount IS NULL OR investment_amount = 0)
    ''')
    us_count = cursor.rowcount
    print(f"🇺🇸 미국 주식 {us_count}개 → $1,000")
    
    conn.commit()
    
    # 결과 확인
    cursor.execute('''
        SELECT uw.ticker, uw.name, uw.country, uw.investment_amount
        FROM user_watchlist uw
        WHERE uw.enabled = 1
        ORDER BY uw.country, uw.ticker
    ''')
    
    print("\n📋 현재 종목 목록:")
    for row in cursor.fetchall():
        ticker, name, country, amount = row
        flag = '🇰🇷' if country == 'KR' else '🇺🇸'
        currency = '원' if country == 'KR' else '$'
        amount_str = f"{amount:,.0f}{currency}" if amount else '미설정'
        print(f"  {flag} {name}({ticker}): {amount_str}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ 완료!")
    print("=" * 60)


if __name__ == "__main__":
    set_default_investment()

