"""
데이터 수집 시스템
일봉 & 분봉 데이터 수집 및 DB 저장
"""

import FinanceDataReader as fdr
from datetime import datetime, timedelta
from database import StockDatabase
from scheduler_config import WATCH_LIST
import time


class DataCollector:
    """데이터 수집 관리"""
    
    def __init__(self):
        self.db = StockDatabase()
    
    def initialize_historical_data(self, years=1):
        """
        초기 히스토리 데이터 로드 (최초 1회만)
        """
        print("\n" + "="*60)
        print(f"📊 초기 데이터 로드 시작 ({years}년치)")
        print("="*60)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365 + 30)
        
        total_tickers = len(WATCH_LIST)
        success_count = 0
        total_rows = 0
        
        for idx, (ticker, name) in enumerate(WATCH_LIST.items(), 1):
            print(f"\n[{idx}/{total_tickers}] {name} ({ticker})")
            
            try:
                # 데이터 확인
                latest_date = self.db.get_latest_date(ticker)
                
                if latest_date:
                    # 이미 데이터가 있으면 마지막 날짜 이후만 가져오기
                    start = datetime.strptime(latest_date, '%Y-%m-%d') + timedelta(days=1)
                    print(f"  • 기존 데이터 발견: {latest_date}까지")
                    print(f"  • 추가 로드: {start.strftime('%Y-%m-%d')} 이후")
                else:
                    start = start_date
                    print(f"  • 신규 로드: {start.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
                
                # 데이터 가져오기
                df = fdr.DataReader(ticker, start, end_date)
                
                if df.empty:
                    print(f"  ❌ 데이터 없음")
                    continue
                
                # DB에 저장할 데이터 준비
                data_to_insert = []
                for date, row in df.iterrows():
                    data_to_insert.append((
                        ticker,
                        name,
                        date.strftime('%Y-%m-%d'),
                        float(row.get('Open', row['Close'])),
                        float(row.get('High', row['Close'])),
                        float(row.get('Low', row['Close'])),
                        float(row['Close']),
                        int(row.get('Volume', 0))
                    ))
                
                # 대량 삽입
                if self.db.insert_daily_prices_bulk(data_to_insert):
                    print(f"  ✅ {len(data_to_insert)}개 데이터 저장 완료")
                    success_count += 1
                    total_rows += len(data_to_insert)
                else:
                    print(f"  ❌ 저장 실패")
                
                # API 과부하 방지
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ❌ 오류: {e}")
        
        print("\n" + "="*60)
        print(f"✅ 초기 데이터 로드 완료")
        print(f"   • 성공: {success_count}/{total_tickers}개 종목")
        print(f"   • 총 {total_rows:,}개 데이터")
        print("="*60)
        
        return success_count
    
    def update_daily_data(self):
        """
        일일 데이터 업데이트 (월-금 실행)
        어제 데이터만 추가
        """
        print("\n" + "="*60)
        print(f"📊 일일 데이터 업데이트 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        print("="*60)
        
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        # 주말이면 금요일 데이터 가져오기
        if today.weekday() == 0:  # 월요일
            yesterday = today - timedelta(days=3)
        elif today.weekday() == 6:  # 일요일
            yesterday = today - timedelta(days=2)
        
        start_date = yesterday - timedelta(days=5)  # 여유있게
        end_date = today
        
        total_tickers = len(WATCH_LIST)
        success_count = 0
        new_data_count = 0
        
        for idx, (ticker, name) in enumerate(WATCH_LIST.items(), 1):
            try:
                print(f"[{idx}/{total_tickers}] {name} ({ticker})...", end=" ")
                
                # 최근 데이터 가져오기
                df = fdr.DataReader(ticker, start_date, end_date)
                
                if df.empty:
                    print("❌ 데이터 없음")
                    continue
                
                # DB에 있는 최신 날짜
                latest_date = self.db.get_latest_date(ticker)
                
                # 새 데이터만 필터링
                if latest_date:
                    df = df[df.index > latest_date]
                
                if df.empty:
                    print("✅ 최신 상태")
                    success_count += 1
                    continue
                
                # DB에 저장
                data_to_insert = []
                for date, row in df.iterrows():
                    data_to_insert.append((
                        ticker,
                        name,
                        date.strftime('%Y-%m-%d'),
                        float(row.get('Open', row['Close'])),
                        float(row.get('High', row['Close'])),
                        float(row.get('Low', row['Close'])),
                        float(row['Close']),
                        int(row.get('Volume', 0))
                    ))
                
                if self.db.insert_daily_prices_bulk(data_to_insert):
                    print(f"✅ {len(data_to_insert)}개 추가")
                    success_count += 1
                    new_data_count += len(data_to_insert)
                else:
                    print("❌ 저장 실패")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ {e}")
        
        print("\n" + "="*60)
        print(f"✅ 일일 업데이트 완료")
        print(f"   • 성공: {success_count}/{total_tickers}개 종목")
        print(f"   • 신규 데이터: {new_data_count}개")
        print("="*60)
        
        return success_count
    
    def collect_current_prices(self):
        """
        현재가 수집 (5분마다 실행)
        분봉 데이터로 저장
        """
        print(f"\n⏰ 현재가 수집 중... ({datetime.now().strftime('%H:%M:%S')})")
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:00')
        success_count = 0
        prices_data = []
        
        for ticker, name in WATCH_LIST.items():
            try:
                # 최근 5일 데이터에서 최신 가격 가져오기
                df = fdr.DataReader(ticker, datetime.now() - timedelta(days=5), datetime.now())
                
                if df.empty:
                    continue
                
                current_price = float(df['Close'].iloc[-1])
                volume = int(df.get('Volume', [0]).iloc[-1])
                
                # 분봉 데이터 저장
                prices_data.append((
                    ticker,
                    name,
                    current_time,
                    current_price,
                    volume
                ))
                
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ {ticker}: {e}")
        
        # 대량 저장
        if prices_data:
            if self.db.insert_minute_prices_bulk(prices_data):
                print(f"  ✅ {success_count}개 종목 현재가 저장")
            else:
                print(f"  ❌ 저장 실패")
        
        return success_count, prices_data
    
    def calculate_and_cache_statistics(self):
        """
        표준편차 등 통계 계산 및 캐싱
        월-금 8:50 또는 데이터 업데이트 후 실행
        """
        print("\n📊 통계 계산 중...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        success_count = 0
        
        for ticker, name in WATCH_LIST.items():
            try:
                # 1년치 데이터 가져오기
                df = self.db.get_daily_prices(ticker, days=252)
                
                if df.empty or len(df) < 30:
                    print(f"  ⚠️  {name}: 데이터 부족")
                    continue
                
                # 일일 수익률 계산
                returns = df['close'].pct_change() * 100
                returns = returns.dropna()
                
                # 통계 계산
                mean_return = returns.mean()
                std_dev = returns.std()
                current_price = df['close'].iloc[-1]
                
                # 목표가 계산
                target_1sigma = current_price * (1 - std_dev / 100)
                target_2sigma = current_price * (1 - 2 * std_dev / 100)
                
                # 캐시에 저장
                if self.db.update_statistics_cache(
                    ticker, today, mean_return, std_dev, 
                    current_price, target_1sigma, target_2sigma
                ):
                    success_count += 1
                
            except Exception as e:
                print(f"  ❌ {name}: {e}")
        
        print(f"  ✅ {success_count}개 종목 통계 캐싱 완료")
        return success_count
    
    def get_statistics_from_cache(self, ticker: str):
        """캐시에서 통계 조회 (초고속)"""
        return self.db.get_statistics_cache(ticker)
    
    def close(self):
        """DB 연결 종료"""
        self.db.close()


def initialize_database():
    """초기 데이터베이스 설정 (최초 1회)"""
    print("\n" + "="*60)
    print("🚀 데이터베이스 초기화")
    print("="*60)
    
    collector = DataCollector()
    
    # 1년치 히스토리 데이터 로드
    collector.initialize_historical_data(years=1)
    
    # 통계 계산 및 캐싱
    collector.calculate_and_cache_statistics()
    
    # 현황 출력
    status = collector.db.get_data_status()
    print("\n" + "="*60)
    print("📊 데이터베이스 현황:")
    print(f"   • 일봉 데이터: {status['daily']['total_rows']:,}개")
    print(f"   • 종목 수: {status['daily']['tickers']}개")
    if status['daily']['date_range'][0]:
        print(f"   • 기간: {status['daily']['date_range'][0]} ~ {status['daily']['date_range'][1]}")
    print("="*60)
    
    collector.close()


def daily_update():
    """월-금 실행할 업데이트"""
    collector = DataCollector()
    
    # 1. 어제 데이터 추가
    collector.update_daily_data()
    
    # 2. 통계 재계산
    collector.calculate_and_cache_statistics()
    
    collector.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'init':
            # 초기 설정
            initialize_database()
        elif sys.argv[1] == 'update':
            # 일일 업데이트
            daily_update()
        elif sys.argv[1] == 'status':
            # 현황 확인
            db = StockDatabase()
            status = db.get_data_status()
            print("\n📊 데이터베이스 현황:")
            print(f"일봉 데이터: {status['daily']['total_rows']:,}개 ({status['daily']['tickers']}개 종목)")
            print(f"분봉 데이터: {status['minute']['total_rows']:,}개 ({status['minute']['tickers']}개 종목)")
            if status['daily']['date_range'][0]:
                print(f"일봉 기간: {status['daily']['date_range'][0]} ~ {status['daily']['date_range'][1]}")
            if status['minute']['datetime_range'][0]:
                print(f"분봉 기간: {status['minute']['datetime_range'][0]} ~ {status['minute']['datetime_range'][1]}")
            db.close()
    else:
        print("\n사용법:")
        print("  python data_collector.py init     # 초기 데이터 로드")
        print("  python data_collector.py update   # 일일 업데이트")
        print("  python data_collector.py status   # 현황 확인")

