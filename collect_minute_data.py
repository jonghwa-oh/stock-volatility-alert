#!/usr/bin/env python3
"""
분봉 데이터 수집 스크립트
- KIS API를 사용해 과거 분봉 데이터 수집
- 한국/미국 주식 모두 지원
"""

import argparse
from datetime import datetime, timedelta
from database import StockDatabase
from kis_api import KISApi
import time

def collect_minute_data(ticker: str, name: str, country: str, 
                        start_date: str, end_date: str, 
                        interval: int = 1):
    """
    분봉 데이터 수집
    
    Args:
        ticker: 종목 코드
        name: 종목명
        country: 국가 (KR/US)
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        interval: 분봉 간격 (1, 5, 15, 30, 60)
    """
    db = StockDatabase()
    kis = KISApi()
    
    print(f"\n{'='*60}")
    print(f"📊 분봉 데이터 수집: {name} ({ticker})")
    print(f"   기간: {start_date} ~ {end_date}")
    print(f"   간격: {interval}분봉")
    print(f"   국가: {country}")
    print(f"{'='*60}\n")
    
    total_count = 0
    
    if country == 'KR':
        # 한국 주식 분봉 조회
        total_count = collect_kr_minute_data(kis, db, ticker, name, start_date, end_date, interval)
    else:
        # 미국 주식 분봉 조회
        total_count = collect_us_minute_data(kis, db, ticker, name, start_date, end_date, interval)
    
    print(f"\n✅ 수집 완료! 총 {total_count}건 저장됨")
    db.close()
    return total_count


def collect_kr_minute_data(kis: KISApi, db: StockDatabase, 
                           ticker: str, name: str,
                           start_date: str, end_date: str, 
                           interval: int) -> int:
    """한국 주식 분봉 데이터 수집"""
    
    # KIS API 분봉 조회 (FHKST03010200)
    # 한 번에 최대 30건, 날짜별로 반복 조회 필요
    
    total_count = 0
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    while current_date <= end_dt:
        date_str = current_date.strftime('%Y%m%d')
        
        try:
            # KIS API 분봉 조회
            minute_data = kis.get_kr_minute_price(ticker, date_str, interval)
            
            if minute_data:
                for item in minute_data:
                    try:
                        dt_str = f"{item['stck_bsop_date'][:4]}-{item['stck_bsop_date'][4:6]}-{item['stck_bsop_date'][6:8]} {item['stck_cntg_hour'][:2]}:{item['stck_cntg_hour'][2:4]}:00"
                        price = float(item.get('stck_prpr', 0))
                        volume = int(item.get('cntg_vol', 0))
                        
                        if price > 0:
                            db.insert_minute_price(
                                ticker=ticker,
                                ticker_name=name,
                                datetime_str=dt_str,
                                price=price,
                                volume=volume
                            )
                            total_count += 1
                    except Exception as e:
                        print(f"  ⚠️ 데이터 파싱 오류: {e}")
                
                print(f"  📅 {date_str}: {len(minute_data)}건 수집")
            else:
                print(f"  📅 {date_str}: 데이터 없음")
        
        except Exception as e:
            print(f"  ❌ {date_str} 조회 오류: {e}")
        
        current_date += timedelta(days=1)
        time.sleep(0.5)  # API 호출 간격
    
    return total_count


def collect_us_minute_data(kis: KISApi, db: StockDatabase,
                           ticker: str, name: str,
                           start_date: str, end_date: str,
                           interval: int) -> int:
    """미국 주식 분봉 데이터 수집"""
    
    total_count = 0
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    exchange = kis.get_exchange_code(ticker)
    
    while current_date <= end_dt:
        date_str = current_date.strftime('%Y%m%d')
        
        try:
            # KIS API 미국 주식 분봉 조회
            minute_data = kis.get_us_minute_price(ticker, exchange, date_str, interval)
            
            if minute_data:
                for item in minute_data:
                    try:
                        # 날짜/시간 파싱
                        dt_str = f"{item['xymd'][:4]}-{item['xymd'][4:6]}-{item['xymd'][6:8]} {item['xhms'][:2]}:{item['xhms'][2:4]}:00"
                        price = float(item.get('last', 0))
                        volume = int(item.get('evol', 0))
                        
                        if price > 0:
                            db.insert_minute_price(
                                ticker=ticker,
                                ticker_name=name,
                                datetime_str=dt_str,
                                price=price,
                                volume=volume
                            )
                            total_count += 1
                    except Exception as e:
                        print(f"  ⚠️ 데이터 파싱 오류: {e}")
                
                print(f"  📅 {date_str}: {len(minute_data)}건 수집")
            else:
                print(f"  📅 {date_str}: 데이터 없음")
        
        except Exception as e:
            print(f"  ❌ {date_str} 조회 오류: {e}")
        
        current_date += timedelta(days=1)
        time.sleep(0.5)  # API 호출 간격
    
    return total_count


def collect_all_watchlist(start_date: str, end_date: str, interval: int = 1):
    """관심 종목 전체 분봉 데이터 수집"""
    
    db = StockDatabase()
    users = db.get_all_users()
    
    if not users:
        print("❌ 등록된 사용자가 없습니다.")
        return
    
    # 모든 사용자의 관심 종목 합치기
    all_tickers = {}
    for user in users:
        watchlist = db.get_user_watchlist_with_names(user['name'])
        for stock in watchlist:
            if stock['ticker'] not in all_tickers:
                all_tickers[stock['ticker']] = {
                    'name': stock['name'],
                    'country': stock['country']
                }
    
    db.close()
    
    print(f"\n📋 총 {len(all_tickers)}개 종목 분봉 데이터 수집")
    print(f"   기간: {start_date} ~ {end_date}")
    print(f"   간격: {interval}분봉\n")
    
    for ticker, info in all_tickers.items():
        collect_minute_data(
            ticker=ticker,
            name=info['name'],
            country=info['country'],
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        time.sleep(1)  # 종목 간 간격


def main():
    parser = argparse.ArgumentParser(description='분봉 데이터 수집')
    parser.add_argument('--ticker', '-t', help='종목 코드 (예: SOXL, 005930)')
    parser.add_argument('--name', '-n', help='종목명')
    parser.add_argument('--country', '-c', choices=['KR', 'US'], help='국가 (KR/US)')
    parser.add_argument('--start', '-s', required=True, help='시작일 (YYYY-MM-DD)')
    parser.add_argument('--end', '-e', help='종료일 (YYYY-MM-DD), 기본값: 오늘')
    parser.add_argument('--interval', '-i', type=int, default=1, 
                        choices=[1, 5, 15, 30, 60], help='분봉 간격 (기본: 1분)')
    parser.add_argument('--all', '-a', action='store_true', 
                        help='관심 종목 전체 수집')
    
    args = parser.parse_args()
    
    # 종료일 기본값: 오늘
    end_date = args.end or datetime.now().strftime('%Y-%m-%d')
    
    if args.all:
        # 관심 종목 전체 수집
        collect_all_watchlist(args.start, end_date, args.interval)
    elif args.ticker:
        # 특정 종목 수집
        if not args.name or not args.country:
            print("❌ --name과 --country를 지정하세요.")
            print("   예: python collect_minute_data.py -t SOXL -n 'Direxion SOXL' -c US -s 2024-12-01")
            return
        
        collect_minute_data(
            ticker=args.ticker,
            name=args.name,
            country=args.country,
            start_date=args.start,
            end_date=end_date,
            interval=args.interval
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

