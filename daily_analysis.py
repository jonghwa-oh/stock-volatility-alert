"""
일일 매수 알림 스크립트
매일 8:50 AM에 실행되어 매수 추천 종목을 분석하고 텔레그램으로 전송
"""

from datetime import datetime
from pathlib import Path
import os

from database import StockDatabase, User, UserStock
from volatility_analysis import analyze_daily_volatility, visualize_volatility
from telegram_bot import send_message, send_photo
from config import TELEGRAM_CONFIG


def get_unique_tickers():
    """모든 사용자의 종목을 중복 없이 가져오기"""
    db = StockDatabase()
    
    # 활성 사용자와 종목 가져오기
    users = db.get_all_users()
    
    unique_tickers = {}  # {ticker: name}
    for user in users:
        if not user['is_active']:
            continue
        
        stocks = db.get_user_stocks(user['id'])
        for stock in stocks:
            if stock['is_active']:
                unique_tickers[stock['ticker']] = stock['name']
    
    db.close()
    return unique_tickers


def analyze_and_generate_charts():
    """
    모든 종목 분석 및 차트 생성 (중복 제거)
    같은 날짜의 차트가 있으면 재사용
    """
    today = datetime.now().strftime('%Y-%m-%d')
    unique_tickers = get_unique_tickers()
    
    if not unique_tickers:
        print("⚠️  활성 종목이 없습니다.")
        return {}
    
    print("="*70)
    print(f"📊 일일 분석 시작 ({today})")
    print(f"📈 분석 종목: {len(unique_tickers)}개")
    print("="*70)
    
    results = {}
    
    for ticker, name in unique_tickers.items():
        print(f"\n📊 {ticker} ({name}) 분석 중...")
        
        # 차트 파일 경로
        chart_path = Path('charts') / ticker / f"{today}_{ticker}_{name.replace(' ', '_')}_volatility.png"
        
        # 이미 오늘 차트가 있으면 재사용
        if chart_path.exists():
            print(f"  ✅ 기존 차트 사용: {chart_path}")
            results[ticker] = {
                'name': name,
                'chart_path': str(chart_path),
                'data': None  # 이미 생성됨
            }
            continue
        
        # 분석 수행
        try:
            data = analyze_daily_volatility(ticker, name)
            if data:
                # 차트 생성
                chart_file = visualize_volatility(data)
                results[ticker] = {
                    'name': name,
                    'chart_path': chart_file,
                    'data': data
                }
                print(f"  ✅ 새 차트 생성: {chart_file}")
        except Exception as e:
            print(f"  ❌ 분석 실패: {e}")
            continue
    
    return results


def send_daily_alerts():
    """각 사용자에게 맞춤 알림 전송"""
    today = datetime.now().strftime('%Y-%m-%d')
    db = StockDatabase()
    
    # 활성 사용자 가져오기
    users = db.get_all_users()
    
    for user in users:
        if not user['is_active']:
            continue
        
        print(f"\n👤 {user['name']} 님에게 알림 전송 중...")
        
        # 사용자 종목 가져오기
        stocks = db.get_user_stocks(user['id'])
        active_stocks = [s for s in stocks if s['is_active']]
        
        if not active_stocks:
            print(f"  ⚠️  활성 종목이 없습니다.")
            continue
        
        # 요약 메시지
        message = f"🌅 {user['name']}님, 좋은 아침입니다!\n\n"
        message += f"📅 {today}\n"
        message += f"📊 오늘의 매수 전략 분석\n\n"
        message += f"관심 종목: {len(active_stocks)}개\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"
        
        # 종목별 알림
        sent_charts = 0
        for stock in active_stocks:
            ticker = stock['ticker']
            name = stock['name']
            
            # 차트 파일 찾기
            chart_path = Path('charts') / ticker / f"{today}_{ticker}_{name.replace(' ', '_')}_volatility.png"
            
            if not chart_path.exists():
                message += f"⚠️  {ticker} ({name}): 차트 없음\n"
                continue
            
            # 차트 전송
            stock_message = f"📊 {ticker} - {name}\n"
            stock_message += f"💰 투자금: {stock['investment_amount']:,}원\n"
            
            try:
                send_photo(
                    user['telegram_chat_id'],
                    str(chart_path),
                    stock_message
                )
                sent_charts += 1
                message += f"✅ {ticker}: 차트 전송 완료\n"
                print(f"  ✅ {ticker} 차트 전송 완료")
            except Exception as e:
                message += f"❌ {ticker}: 전송 실패\n"
                print(f"  ❌ {ticker} 차트 전송 실패: {e}")
        
        # 요약 메시지 전송
        message += f"\n━━━━━━━━━━━━━━━━━━\n"
        message += f"✅ 총 {sent_charts}개 종목 차트 전송\n\n"
        message += "💡 매수 시점:\n"
        message += "  • 1차: 표준편차 1배 하락 시\n"
        message += "  • 2차: 표준편차 2배 하락 시\n\n"
        message += "행운을 빕니다! 🍀"
        
        try:
            send_message(user['telegram_chat_id'], message)
            print(f"  ✅ 요약 메시지 전송 완료")
        except Exception as e:
            print(f"  ❌ 요약 메시지 전송 실패: {e}")
    
    db.close()


def main():
    """메인 실행"""
    print("\n" + "="*70)
    print("🌅 일일 매수 알림 시작")
    print(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 1단계: 모든 종목 분석 (중복 제거)
    print("\n[1/2] 종목 분석 및 차트 생성...")
    results = analyze_and_generate_charts()
    
    if not results:
        print("\n⚠️  분석 결과가 없습니다.")
        return
    
    print(f"\n✅ 총 {len(results)}개 종목 분석 완료")
    
    # 2단계: 사용자별 알림 전송
    print("\n[2/2] 사용자별 알림 전송...")
    send_daily_alerts()
    
    print("\n" + "="*70)
    print("✅ 일일 매수 알림 완료!")
    print("="*70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

