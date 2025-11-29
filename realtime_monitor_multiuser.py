"""
멀티 유저 실시간 모니터링 시스템
가족 구성원별로 다른 종목 모니터링 및 알림
"""

import asyncio
import schedule
import time
from datetime import datetime, timedelta
from telegram_bot import TelegramNotifier
from scheduler_config import SCHEDULE_CONFIG, ALERT_CONFIG
from data_collector import DataCollector
from database import StockDatabase


class MultiUserMonitor:
    """멀티 유저 실시간 모니터링"""
    
    def __init__(self):
        self.db = StockDatabase()
        self.collector = DataCollector()
        self.notifiers = {}  # user_id: TelegramNotifier
        self.last_alerts = {}  # (user_id, ticker): datetime
    
    def init_notifiers(self):
        """각 사용자별 텔레그램 봇 초기화"""
        users = self.db.get_all_users()
        
        for user in users:
            # 각 사용자마다 별도의 notifier 생성
            from config import TELEGRAM_CONFIG
            notifier = TelegramNotifier(
                TELEGRAM_CONFIG['BOT_TOKEN'],
                user['chat_id']
            )
            self.notifiers[user['id']] = notifier
        
        print(f"✅ {len(self.notifiers)}명 사용자 텔레그램 초기화")
    
    async def daily_analysis(self):
        """월-금 오전 8:50 - 전체 분석 및 개인별 알림"""
        print("\n" + "="*60)
        print("🌅 일일 분석 시작 (멀티 유저)")
        print("="*60)
        
        # 1. 데이터 업데이트 (전체 종목)
        all_tickers = self.get_all_unique_tickers()
        print(f"\n모니터링 중인 총 종목: {len(all_tickers)}개")
        
        self.collector.update_daily_data()
        self.collector.calculate_and_cache_statistics()
        
        # 2. 각 사용자별 요약 전송
        users = self.db.get_all_users()
        for user in users:
            await self.send_user_daily_summary(user)
        
        print("✅ 일일 분석 완료\n")
    
    def get_all_unique_tickers(self):
        """모든 사용자의 관심 종목 (중복 제거)"""
        tickers = set()
        users = self.db.get_all_users()
        
        for user in users:
            user_tickers = self.db.get_user_watchlist(user['name'])
            tickers.update(user_tickers)
        
        return list(tickers)
    
    async def send_user_daily_summary(self, user: dict):
        """사용자별 일일 요약 전송"""
        notifier = self.notifiers.get(user['id'])
        if not notifier:
            return
        
        # 사용자 관심 종목
        watchlist = self.db.get_user_watchlist_with_names(user['name'])
        
        if not watchlist:
            await notifier.send_message(
                f"<b>📊 {user['name']}님의 일일 분석</b>\n\n"
                f"⚠️ 관심 종목이 없습니다.\n"
                f"user_manager.py로 종목을 추가하세요."
            )
            return
        
        message = f"<b>📊 {user['name']}님의 일일 분석</b>\n"
        message += f"{'='*35}\n"
        message += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        message += f"💰 투자 금액: {user['investment_amount']:,.0f}원\n\n"
        
        # 관심 종목별 통계
        stats_list = []
        for item in watchlist:
            ticker = item['ticker']
            stats = self.collector.get_statistics_from_cache(ticker)
            if stats:
                stats['ticker'] = ticker
                stats['name'] = item['name']
                stats_list.append(stats)
        
        if not stats_list:
            await notifier.send_message(message + "⚠️ 통계 데이터를 불러올 수 없습니다.")
            return
        
        # 변동성 순위
        stats_list.sort(key=lambda x: x['std_dev'], reverse=True)
        
        message += f"<b>🎯 관심 종목 ({len(stats_list)}개):</b>\n\n"
        
        for idx, stats in enumerate(stats_list, 1):
            name = stats['name']
            ticker = stats['ticker']
            std = stats['std_dev']
            current = stats['current_price']
            t1 = stats['target_1sigma']
            t2 = stats['target_2sigma']
            
            # 1차 투자금 계산
            amount_1 = user['investment_amount']
            amount_2 = user['investment_amount'] * 2
            
            message += f"{idx}. <b>{name}</b> ({ticker})\n"
            message += f"   현재: ${current:,.2f}\n"
            message += f"   변동성: {std:.2f}%\n"
            message += f"   1차 목표: ${t1:,.2f} → {amount_1:,.0f}원\n"
            message += f"   2차 목표: ${t2:,.2f} → {amount_2:,.0f}원\n\n"
        
        message += f"🔔 <b>실시간 모니터링 활성화</b>\n"
        message += f"{SCHEDULE_CONFIG['realtime_check_interval']}분마다 체크 중..."
        
        await notifier.send_message(message)
        print(f"  ✅ {user['name']}님 일일 리포트 전송")
    
    async def realtime_check(self):
        """5분마다 실행 - 각 사용자별 실시간 가격 체크"""
        print(f"\n⏰ 가격 체크 중... ({datetime.now().strftime('%H:%M:%S')})")
        
        # 전체 종목 현재가 수집
        success_count, prices_data = self.collector.collect_current_prices()
        
        if not prices_data:
            print("  ❌ 가격 데이터 없음")
            return
        
        # 가격 데이터를 딕셔너리로 변환
        current_prices = {ticker: (price, volume) for ticker, _, _, price, volume in prices_data}
        
        # 각 사용자별 체크
        users = self.db.get_all_users()
        total_alerts = 0
        
        for user in users:
            alerts_sent = await self.check_user_signals(user, current_prices)
            total_alerts += alerts_sent
        
        if total_alerts > 0:
            print(f"  🔔 총 {total_alerts}개 알림 전송")
        else:
            print(f"  ✅ 매수 신호 없음 ({len(current_prices)}개 종목 체크)")
    
    async def check_user_signals(self, user: dict, current_prices: dict):
        """사용자별 매수 신호 체크"""
        notifier = self.notifiers.get(user['id'])
        if not notifier:
            return 0
        
        # 사용자 관심 종목
        watchlist = self.db.get_user_watchlist(user['name'])
        alerts_sent = 0
        
        for ticker in watchlist:
            if ticker not in current_prices:
                continue
            
            current_price, volume = current_prices[ticker]
            
            # 통계 조회
            stats = self.collector.get_statistics_from_cache(ticker)
            if not stats:
                continue
            
            baseline_price = stats['current_price']
            target_1sigma = stats['target_1sigma']
            target_2sigma = stats['target_2sigma']
            std_dev = stats['std_dev']
            
            # 하락률 계산
            drop_pct = ((current_price - baseline_price) / baseline_price) * 100
            
            # 쿨다운 체크
            cooldown_key = (user['id'], ticker)
            cooldown_minutes = ALERT_CONFIG['alert_cooldown_minutes']
            
            if cooldown_key in self.last_alerts:
                time_since_last = (datetime.now() - self.last_alerts[cooldown_key]).total_seconds() / 60
                if time_since_last < cooldown_minutes:
                    continue
            
            # 종목명 가져오기
            ticker_info = self.db.get_user_watchlist_with_names(user['name'])
            ticker_name = ticker
            for item in ticker_info:
                if item['ticker'] == ticker:
                    ticker_name = item['name']
                    break
            
            # 2시그마 체크 (우선)
            if ALERT_CONFIG['alert_2sigma']:
                threshold = target_2sigma * (1 + (1 - ALERT_CONFIG['alert_2sigma_threshold']))
                if current_price <= threshold:
                    await self.send_user_buy_alert(
                        user, notifier, ticker, ticker_name, current_price,
                        target_2sigma, std_dev * 2, drop_pct, 2
                    )
                    self.last_alerts[cooldown_key] = datetime.now()
                    alerts_sent += 1
                    continue
            
            # 1시그마 체크
            if ALERT_CONFIG['alert_1sigma']:
                threshold = target_1sigma * (1 + (1 - ALERT_CONFIG['alert_1sigma_threshold']))
                if current_price <= threshold:
                    await self.send_user_buy_alert(
                        user, notifier, ticker, ticker_name, current_price,
                        target_1sigma, std_dev, drop_pct, 1
                    )
                    self.last_alerts[cooldown_key] = datetime.now()
                    alerts_sent += 1
        
        return alerts_sent
    
    async def send_user_buy_alert(self, user: dict, notifier, ticker, ticker_name,
                                  current_price, target_price, std_dev, drop_pct, level):
        """사용자별 매수 알림 전송"""
        message = f"🔔 <b>{user['name']}님, 매수 신호!</b>\n"
        message += f"{'='*30}\n\n"
        message += f"📊 <b>{ticker_name}</b> ({ticker})\n\n"
        message += f"💰 <b>현재가:</b> ${current_price:,.2f}\n"
        message += f"🎯 <b>목표가:</b> ${target_price:,.2f}\n"
        message += f"📉 <b>변동:</b> {drop_pct:+.2f}%\n"
        message += f"📊 <b>표준편차:</b> {std_dev:.2f}%\n\n"
        
        if level == 1:
            amount = user['investment_amount']
            message += f"⭐ <b>1차 매수 시점!</b>\n"
            message += f"💵 권장 투자: {amount:,.0f}원\n"
            message += f"💵 USD: ${amount/1300:.0f}\n\n"
        else:
            amount = user['investment_amount'] * 2
            message += f"⭐⭐ <b>2차 매수 시점!</b>\n"
            message += f"💵 권장 투자: {amount:,.0f}원\n"
            message += f"💵 USD: ${amount/1300:.0f}\n\n"
        
        message += f"💡 <b>지금 매수를 고려하세요!</b>"
        
        await notifier.send_message(message)
        print(f"  🔔 알림: {user['name']} - {ticker_name} {level}차 매수")
    
    def close(self):
        """리소스 정리"""
        self.collector.close()
        self.db.close()


def is_market_open():
    """장이 열려있는 시간인지 체크"""
    now = datetime.now()
    
    # 요일 체크 (월-금)
    if now.weekday() not in SCHEDULE_CONFIG['trading_days']:
        return False
    
    # 시간 체크
    current_time = now.strftime('%H:%M')
    open_time = SCHEDULE_CONFIG['market_open_time']
    close_time = SCHEDULE_CONFIG['market_close_time']
    
    return open_time <= current_time <= close_time


monitor = MultiUserMonitor()


async def scheduled_daily_analysis():
    """스케줄된 일일 분석"""
    await monitor.daily_analysis()


async def scheduled_realtime_check():
    """스케줄된 실시간 체크 (장 시간만)"""
    if is_market_open():
        await monitor.realtime_check()
    else:
        print(f"⏸️  장 마감 시간 ({datetime.now().strftime('%H:%M')})")


def run_scheduler():
    """스케줄러 실행 (메인 루프)"""
    print("\n" + "="*60)
    print("👨‍👩‍👦 가족용 멀티 유저 모니터링 시스템")
    print("="*60)
    
    # 사용자 확인
    users = monitor.db.get_all_users()
    
    if not users:
        print("\n❌ 등록된 사용자가 없습니다!")
        print("먼저 사용자를 등록하세요:")
        print("  python user_manager.py family")
        return
    
    print(f"\n👥 등록된 사용자: {len(users)}명")
    for user in users:
        watchlist = monitor.db.get_user_watchlist(user['name'])
        print(f"   • {user['name']}: {len(watchlist)}개 종목")
    
    # 전체 종목 수
    all_tickers = monitor.get_all_unique_tickers()
    print(f"\n📊 모니터링 중인 총 종목: {len(all_tickers)}개")
    
    # 텔레그램 초기화
    monitor.init_notifiers()
    
    # 스케줄 등록
    print(f"\n📅 일일 분석: 월-금 {SCHEDULE_CONFIG['daily_analysis_time']}")
    print(f"⏰ 실시간 체크: {SCHEDULE_CONFIG['realtime_check_interval']}분마다")
    print(f"💾 DB 사용: SQLite (초고속)")
    print("="*60)
    
    schedule.every().day.at(SCHEDULE_CONFIG['daily_analysis_time']).do(
        lambda: asyncio.run(scheduled_daily_analysis())
    )
    
    schedule.every(SCHEDULE_CONFIG['realtime_check_interval']).minutes.do(
        lambda: asyncio.run(scheduled_realtime_check())
    )
    
    # DB 상태 확인
    status = monitor.db.get_data_status()
    
    if status['daily']['total_rows'] == 0:
        print("\n⚠️  데이터베이스가 비어있습니다!")
        print("먼저 초기 데이터를 로드하세요:")
        print("  python data_collector.py init")
        return
    
    print(f"\n📊 DB 현황:")
    print(f"   • 일봉 데이터: {status['daily']['total_rows']:,}개")
    
    # 통계 캐시 확인
    print("\n🔄 통계 캐시 확인 중...")
    cached_count = 0
    for ticker in all_tickers:
        if monitor.collector.get_statistics_from_cache(ticker):
            cached_count += 1
    
    if cached_count < len(all_tickers):
        print(f"⚠️  일부 통계 캐시 없음. 계산 중...")
        monitor.collector.calculate_and_cache_statistics()
    else:
        print(f"✅ {cached_count}개 종목 통계 캐시 확인")
    
    print("\n✅ 모니터링 시작! (Ctrl+C로 종료)\n")
    
    # 메인 루프
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 모니터링 종료")
        monitor.close()


if __name__ == "__main__":
    run_scheduler()

