"""
일일 매수 알림 스크립트
월-금 8:50 AM에 실행되어 매수 추천 종목을 분석하고 ntfy로 전송
"""

from datetime import datetime
from pathlib import Path
import os

from database import StockDatabase
from volatility_analysis import analyze_daily_volatility, visualize_volatility
from ntfy_alert import NtfyAlert
from scheduler_config import SCHEDULE_CONFIG
from kis_api import KISApi


def send_ntfy_message(ntfy_topic: str, message: str, title: str = None) -> bool:
    """ntfy 메시지 전송 wrapper"""
    if not ntfy_topic:
        return False
    ntfy = NtfyAlert(ntfy_topic)
    return ntfy.send(message, title=title)


def get_stock_name(ticker: str, fallback_name: str) -> str:
    """
    종목명 가져오기 (티커와 이름이 같으면 KIS API에서 조회)
    
    Args:
        ticker: 종목 코드
        fallback_name: 기본 이름 (DB에서 가져온 값)
    
    Returns:
        종목명
    """
    # 이름이 티커와 다르면 그대로 반환
    if fallback_name and fallback_name != ticker:
        return fallback_name
    
    # 한국 주식인 경우 KIS API에서 종목명 조회
    if ticker.isdigit():
        try:
            kis = KISApi()
            price_data = kis.get_stock_price(ticker)
            if price_data and 'name' in price_data and price_data['name']:
                return price_data['name']
        except Exception as e:
            print(f"  ⚠️ KIS API 종목명 조회 실패 ({ticker}): {e}")
    else:
        # 미국 주식인 경우 KIS API에서 종목명 조회
        try:
            kis = KISApi()
            price_data = kis.get_overseas_stock_price(ticker)
            if price_data and 'name' in price_data and price_data['name']:
                return price_data['name']
        except Exception as e:
            print(f"  ⚠️ KIS API 종목명 조회 실패 ({ticker}): {e}")
    
    return fallback_name or ticker


def get_unique_tickers():
    """모든 사용자의 종목을 중복 없이 가져오기"""
    db = StockDatabase()
    
    # 활성 사용자와 종목 가져오기
    users = db.get_all_users()
    
    unique_tickers = {}  # {ticker: name}
    for user in users:
        if not user['enabled']:
            continue
        
        # 사용자의 관심 종목 조회
        watchlist = db.get_user_watchlist_with_names(user['name'])
        for stock in watchlist:
            ticker = stock['ticker']
            # 종목명이 없거나 티커와 같으면 KIS API에서 가져오기
            name = get_stock_name(ticker, stock['name'])
            unique_tickers[ticker] = name
    
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
        
        # 분석 수행 (매수 목표가 계산 위해 항상 수행)
        try:
            data = analyze_daily_volatility(ticker, name)
            if not data:
                print(f"  ❌ 분석 실패")
                continue
            
            # 차트가 없으면 생성
            if chart_path.exists():
                print(f"  ✅ 기존 차트 사용: {chart_path}")
                chart_file = str(chart_path)
            else:
                chart_file = visualize_volatility(data)
                print(f"  ✅ 새 차트 생성: {chart_file}")
            
            results[ticker] = {
                'name': name,
                'chart_path': chart_file,
                'data': data  # 매수 목표가 계산을 위해 항상 저장
            }
        except Exception as e:
            print(f"  ❌ 분석 실패: {e}")
            continue
    
    return results


def send_daily_alerts(analysis_results):
    """각 사용자에게 맞춤 ntfy 알림 전송"""
    today = datetime.now().strftime('%Y-%m-%d')
    db = StockDatabase()
    
    # 활성 사용자 가져오기
    users = db.get_all_users()
    
    for user in users:
        # 사용자 활성화 체크
        if not user['enabled']:
            continue
        
        # 알림 활성화 체크
        notification_enabled = user.get('notification_enabled', 1)
        if not notification_enabled:
            print(f"  ⏸️  {user['name']} - 알림 비활성화 상태 (건너뜀)")
            continue
        
        # ntfy 토픽 확인
        ntfy_topic = user.get('ntfy_topic')
        if not ntfy_topic:
            print(f"  ⚠️  {user['name']} - ntfy 토픽 미설정 (건너뜀)")
            continue
        
        print(f"\n👤 {user['name']} 님에게 ntfy 알림 전송 중...")
        
        # 사용자 관심 종목 가져오기
        watchlist = db.get_user_watchlist_with_names(user['name'])
        
        if not watchlist:
            print(f"  ⚠️  관심 종목이 없습니다.")
            continue
        
        # 요약 메시지 생성
        message = f"좋은 아침입니다! 📅 {today}\n\n"
        message += f"📊 관심 종목 {len(watchlist)}개 분석\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"
        
        # 종목별 분석 결과
        for stock in watchlist:
            ticker = stock['ticker']
            name = stock['name']
            
            # 분석 데이터 가져오기
            result = analysis_results.get(ticker)
            
            # 통화 단위 결정
            is_korean = ticker.isdigit()
            
            if not result or not result['data']:
                if is_korean:
                    message += f"📊 {name}\n"
                else:
                    message += f"📊 {ticker}\n"
                message += "   분석 데이터 없음\n\n"
            else:
                data = result['data']
                if is_korean:
                    message += f"📊 {name}\n"
                    message += f"   🧪 {data['target_05x']:,.0f}원\n"
                    message += f"   1σ {data['target_1x']:,.0f}원\n"
                    message += f"   2σ {data['target_2x']:,.0f}원\n\n"
                else:
                    message += f"📊 {ticker}\n"
                    message += f"   🧪 ${data['target_05x']:,.2f}\n"
                    message += f"   1σ ${data['target_1x']:,.2f}\n"
                    message += f"   2σ ${data['target_2x']:,.2f}\n\n"
        
        message += "━━━━━━━━━━━━━━━━━━\n"
        message += "💡 🧪=테스트, 1σ/2σ=매수목표\n"
        message += "📱 상세 차트는 웹에서 확인!"
        
        # ntfy로 전송
        try:
            success = send_ntfy_message(
                ntfy_topic,
                message,
                title=f"📈 오늘의 투자 분석 ({len(watchlist)}종목)"
            )
            if success:
                print(f"  ✅ ntfy 알림 전송 완료")
            else:
                print(f"  ❌ ntfy 알림 전송 실패")
        except Exception as e:
            print(f"  ❌ ntfy 알림 전송 실패: {e}")
    
    db.close()


def main():
    """메인 실행"""
    now = datetime.now()
    weekday = now.weekday()  # 0=월요일, 6=일요일
    
    print("\n" + "="*70)
    print("🌅 일일 매수 알림 시작")
    print(f"⏰ 실행 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 요일: {['월', '화', '수', '목', '금', '토', '일'][weekday]}요일")
    print("="*70)
    
    # 거래일 체크 (월-금만 실행)
    trading_days = SCHEDULE_CONFIG.get('trading_days', [0, 1, 2, 3, 4])
    if weekday not in trading_days:
        print(f"\n⚠️  오늘은 거래일이 아닙니다. (주말/공휴일)")
        print(f"📊 테스트 모드로 실행합니다...")
    else:
        print(f"✅ 오늘은 거래일입니다. 분석을 시작합니다.")
    
    # 1단계: 모든 종목 분석 (중복 제거)
    print("\n[1/2] 종목 분석 및 차트 생성...")
    results = analyze_and_generate_charts()
    
    if not results:
        print("\n⚠️  분석 결과가 없습니다.")
        return
    
    print(f"\n✅ 총 {len(results)}개 종목 분석 완료")
    
    # 2단계: 사용자별 알림 전송
    print("\n[2/2] 사용자별 알림 전송...")
    send_daily_alerts(results)
    
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

