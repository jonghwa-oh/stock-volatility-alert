#!/usr/bin/env python3
"""
분봉 데이터 수집 스크립트
- yfinance를 사용해 미국 주식 정규장 과거 분봉 데이터 수집
- KIS API를 사용해 한국 주식 분봉 데이터 수집
"""

import argparse
from datetime import datetime, timedelta
from database import StockDatabase
from kis_api import KISApi
import time

# yfinance 임포트 (미국 주식 분봉용)
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️ yfinance 미설치: pip install yfinance")


def collect_minute_data(ticker: str, name: str, country: str, 
                        start_date: str, end_date: str, 
                        interval: int = 1, source: str = 'auto'):
    """
    분봉 데이터 수집
    
    Args:
        ticker: 종목 코드
        name: 종목명
        country: 국가 (KR/US)
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        interval: 분봉 간격 (1, 5, 15, 30, 60)
        source: 데이터 소스 (auto, yfinance, kis)
    """
    db = StockDatabase()
    kis = KISApi()
    
    print(f"\n{'='*60}")
    print(f"📊 분봉 데이터 수집: {name} ({ticker})")
    print(f"   기간: {start_date} ~ {end_date}")
    print(f"   간격: {interval}분봉")
    print(f"   국가: {country}")
    print(f"   소스: {source}")
    print(f"{'='*60}\n")
    
    total_count = 0
    
    if country == 'KR':
        # 한국 주식 분봉 조회 (KIS API만 사용)
        total_count = collect_kr_minute_data(kis, db, ticker, name, start_date, end_date, interval)
    else:
        # 미국 주식 분봉 조회
        if source == 'yfinance' or (source == 'auto' and YFINANCE_AVAILABLE):
            # yfinance 사용 (정규장 데이터)
            total_count = collect_us_minute_data_yfinance(db, ticker, name, start_date, end_date, interval)
        else:
            # KIS API 사용 (시간외 데이터만 가능)
            total_count = collect_us_minute_data_kis(kis, db, ticker, name, start_date, end_date, interval)
    
    print(f"\n✅ 수집 완료! 총 {total_count}건 저장됨")
    db.close()
    return total_count


def collect_kr_minute_data(kis: KISApi, db: StockDatabase, 
                           ticker: str, name: str,
                           start_date: str, end_date: str, 
                           interval: int) -> int:
    """한국 주식 분봉 데이터 수집 (KIS API)"""
    
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


def collect_us_minute_data_yfinance(db: StockDatabase,
                                     ticker: str, name: str,
                                     start_date: str, end_date: str,
                                     interval: int) -> int:
    """
    미국 주식 분봉 데이터 수집 (yfinance - 정규장 데이터)
    
    yfinance 제한:
    - 1분봉: 최근 7일
    - 5분봉: 최근 60일
    - 1시간봉: 최근 730일
    """
    
    if not YFINANCE_AVAILABLE:
        print("❌ yfinance가 설치되지 않았습니다. pip install yfinance")
        return 0
    
    total_count = 0
    
    # interval 문자열 변환
    interval_map = {
        1: '1m',
        5: '5m',
        15: '15m',
        30: '30m',
        60: '1h'
    }
    yf_interval = interval_map.get(interval, '1m')
    
    # 기간 제한 확인
    days_limit = {
        '1m': 7,
        '5m': 60,
        '15m': 60,
        '30m': 60,
        '1h': 730
    }
    max_days = days_limit.get(yf_interval, 7)
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    today = datetime.now()
    
    # yfinance 제한 체크
    days_ago = (today - start_dt).days
    if days_ago > max_days:
        print(f"⚠️ yfinance {yf_interval} 제한: 최근 {max_days}일만 가능")
        print(f"   요청: {days_ago}일 전 데이터")
        # 시작일을 제한 내로 조정
        start_dt = today - timedelta(days=max_days - 1)
        start_date = start_dt.strftime('%Y-%m-%d')
        print(f"   조정된 시작일: {start_date}")
    
    try:
        print(f"  📡 yfinance에서 {ticker} 분봉 데이터 조회 중...")
        
        # yfinance로 데이터 조회
        stock = yf.Ticker(ticker)
        
        # end_date는 다음날로 설정 (yfinance는 end를 제외함)
        end_dt_next = end_dt + timedelta(days=1)
        
        df = stock.history(
            start=start_date,
            end=end_dt_next.strftime('%Y-%m-%d'),
            interval=yf_interval
        )
        
        if df.empty:
            print(f"  ❌ {ticker} 데이터 없음")
            return 0
        
        print(f"  ✅ {len(df)}건 조회됨")
        print(f"     시작: {df.index[0]}")
        print(f"     종료: {df.index[-1]}")
        
        # 정규장 시간만 필터링 (미국 동부 9:30 AM ~ 4:00 PM)
        # yfinance는 이미 정규장 시간만 반환함
        
        # 데이터 저장
        for idx, row in df.iterrows():
            try:
                # 타임존 처리 (yfinance는 미국 시간 반환, UTC로 변환 후 한국시간으로)
                if idx.tzinfo is not None:
                    # 한국 시간으로 변환
                    dt_utc = idx.tz_convert('UTC')
                    dt_kst = dt_utc.tz_convert('Asia/Seoul')
                    dt_str = dt_kst.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    dt_str = idx.strftime('%Y-%m-%d %H:%M:%S')
                
                price = float(row['Close'])
                volume = int(row['Volume'])
                
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
        
        # 날짜별 통계 출력
        if not df.empty:
            dates = df.index.date
            unique_dates = sorted(set(dates))
            for d in unique_dates:
                count = sum(1 for x in dates if x == d)
                print(f"  📅 {d}: {count}건 (정규장)")
                
    except Exception as e:
        print(f"  ❌ yfinance 조회 오류: {e}")
        import traceback
        traceback.print_exc()
    
    return total_count


def collect_us_minute_data_kis(kis: KISApi, db: StockDatabase,
                                ticker: str, name: str,
                                start_date: str, end_date: str,
                                interval: int) -> int:
    """미국 주식 분봉 데이터 수집 (KIS API - 시간외 데이터만)"""
    
    print("⚠️ KIS API는 미국 주식 시간외 데이터만 제공합니다.")
    print("   정규장 데이터를 원하시면 --source yfinance 옵션을 사용하세요.")
    
    total_count = 0
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 거래소 자동 감지
    price_info = kis.get_overseas_stock_price_auto(ticker)
    if price_info:
        exchange = price_info.get('exchange', 'NAS')
        print(f"  📍 거래소 자동 감지: {exchange}")
    else:
        exchange = kis.get_exchange_code(ticker)
        print(f"  📍 거래소 기본값: {exchange}")
    
    while current_date <= end_dt:
        date_str = current_date.strftime('%Y%m%d')
        
        try:
            # KIS API 미국 주식 분봉 조회
            minute_data = kis.get_us_minute_price(ticker, exchange, date_str, interval)
            
            if minute_data:
                for item in minute_data:
                    try:
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
                
                print(f"  📅 {date_str}: {len(minute_data)}건 수집 (시간외)")
            else:
                print(f"  📅 {date_str}: 데이터 없음")
        
        except Exception as e:
            print(f"  ❌ {date_str} 조회 오류: {e}")
        
        current_date += timedelta(days=1)
        time.sleep(0.5)  # API 호출 간격
    
    return total_count


def collect_all_watchlist(start_date: str, end_date: str, interval: int = 1, source: str = 'auto'):
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
    print(f"   간격: {interval}분봉")
    print(f"   소스: {source}\n")
    
    for ticker, info in all_tickers.items():
        collect_minute_data(
            ticker=ticker,
            name=info['name'],
            country=info['country'],
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            source=source
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
    parser.add_argument('--source', choices=['auto', 'yfinance', 'kis'], default='auto',
                        help='데이터 소스 (기본: auto = 미국은 yfinance, 한국은 KIS)')
    parser.add_argument('--all', '-a', action='store_true', 
                        help='관심 종목 전체 수집')
    
    args = parser.parse_args()
    
    # 종료일 기본값: 오늘
    end_date = args.end or datetime.now().strftime('%Y-%m-%d')
    
    if args.all:
        # 관심 종목 전체 수집
        collect_all_watchlist(args.start, end_date, args.interval, args.source)
    elif args.ticker:
        # 특정 종목 수집
        if not args.name or not args.country:
            print("❌ --name과 --country를 지정하세요.")
            print("   예: python collect_minute_data.py -t SOXL -n 'Direxion SOXL' -c US -s 2024-12-01")
            print("\n💡 yfinance 분봉 제한:")
            print("   - 1분봉: 최근 7일")
            print("   - 5분봉: 최근 60일")
            print("   - 1시간봉: 최근 730일")
            return
        
        collect_minute_data(
            ticker=args.ticker,
            name=args.name,
            country=args.country,
            start_date=args.start,
            end_date=end_date,
            interval=args.interval,
            source=args.source
        )
    else:
        parser.print_help()
        print("\n📌 사용 예시:")
        print("  # SOXL 최근 7일 1분봉 수집 (yfinance)")
        print("  python collect_minute_data.py -t SOXL -n 'Direxion SOXL' -c US -s 2024-12-07")
        print("")
        print("  # SOXL 5분봉 수집 (최근 60일 가능)")
        print("  python collect_minute_data.py -t SOXL -n 'Direxion SOXL' -c US -s 2024-11-01 -i 5")
        print("")
        print("  # 관심 종목 전체 수집")
        print("  python collect_minute_data.py --all -s 2024-12-10")


if __name__ == "__main__":
    main()
