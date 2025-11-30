"""
하이브리드 실시간 매수 알림 시스템
- 한국 주식: WebSocket 실시간 모니터링
- 미국 주식: 분봉 데이터 모니터링
- 알림 시간: 09:00~24:00
"""
import asyncio
from datetime import datetime, time
from pathlib import Path
from kis_websocket import KISWebSocket
from database import StockDatabase
from volatility_analysis import analyze_daily_volatility
from telegram_bot import send_telegram_sync
from config import load_config
import FinanceDataReader as fdr


class HybridRealtimeMonitor:
    """하이브리드 실시간 모니터링"""
    
    def __init__(self):
        self.db = StockDatabase()
        self.ws = None  # WebSocket (한국 주식용)
        self.config = load_config()
        self.telegram_config = self.config['TELEGRAM_CONFIG']
        
        # 종목별 매수 목표가 캐시
        self.target_prices = {}  # {ticker: {'1x': price, '2x': price, 'name': name, 'country': country}}
        
        # 알림 전송 이력 (중복 방지)
        self.alert_history = {}  # {ticker: {'1x': timestamp, '2x': timestamp}}
        
        # 알림 시간 설정
        self.alert_start_time = time(9, 0)   # 09:00
        self.alert_end_time = time(23, 59)   # 24:00
    
    def _is_alert_time(self) -> bool:
        """알림 가능 시간 확인 (09:00~24:00)"""
        now = datetime.now().time()
        return self.alert_start_time <= now <= self.alert_end_time
    
    async def initialize(self):
        """초기화: 종목별 매수 목표가 계산 및 국가 구분"""
        print("\n" + "="*70)
        print("🚀 하이브리드 실시간 매수 알림 시스템 초기화")
        print("="*70)
        
        # 활성 사용자의 관심 종목 수집 (국가 정보 포함)
        users = self.db.get_all_users()
        
        conn = self.db.connect()
        cursor = conn.cursor()
        
        unique_stocks = {}  # {ticker: {'name': name, 'country': country}}
        
        for user in users:
            if not user['enabled']:
                continue
            
            cursor.execute('''
                SELECT uw.ticker, dp.ticker_name, uw.country
                FROM user_watchlist uw
                LEFT JOIN daily_prices dp ON uw.ticker = dp.ticker
                WHERE uw.user_id = ? AND uw.enabled = 1
                GROUP BY uw.ticker
            ''', (user['id'],))
            
            for row in cursor.fetchall():
                ticker, name, country = row
                if ticker not in unique_stocks:
                    unique_stocks[ticker] = {
                        'name': name or ticker,
                        'country': country or 'US'
                    }
        
        if not unique_stocks:
            print("⚠️  활성 종목이 없습니다.")
            return False
        
        print(f"\n📊 모니터링 종목: {len(unique_stocks)}개")
        
        # 국가별 구분
        korean_stocks = {t: s for t, s in unique_stocks.items() if s['country'] == 'KR'}
        us_stocks = {t: s for t, s in unique_stocks.items() if s['country'] == 'US'}
        
        print(f"🇰🇷 한국 주식: {len(korean_stocks)}개 (WebSocket)")
        print(f"🇺🇸 미국 주식: {len(us_stocks)}개 (분봉 모니터링)")
        
        # 매수 목표가 계산
        for ticker, info in unique_stocks.items():
            name = info['name']
            country = info['country']
            
            print(f"\n📊 {name} ({ticker}) 분석 중...")
            
            try:
                data = analyze_daily_volatility(ticker, name)
                
                if data:
                    self.target_prices[ticker] = {
                        '1x': data['target_1x'],
                        '2x': data['target_2x'],
                        'name': name,
                        'country': country,
                        'drop_1x': data['drop_1x'],
                        'drop_2x': data['drop_2x']
                    }
                    
                    flag = '🇰🇷' if country == 'KR' else '🇺🇸'
                    if country == 'KR':
                        print(f"  {flag} 1차 매수: {data['target_1x']:,.0f}원 ({data['drop_1x']:.2f}% 하락)")
                        print(f"  {flag} 2차 매수: {data['target_2x']:,.0f}원 ({data['drop_2x']:.2f}% 하락)")
                    else:
                        print(f"  {flag} 1차 매수: ${data['target_1x']:,.2f} ({data['drop_1x']:.2f}% 하락)")
                        print(f"  {flag} 2차 매수: ${data['target_2x']:,.2f} ({data['drop_2x']:.2f}% 하락)")
                else:
                    print(f"  ❌ 분석 실패")
                    
            except Exception as e:
                print(f"  ❌ 오류: {e}")
        
        # WebSocket 초기화 (한국 주식용)
        if korean_stocks:
            try:
                from kis_websocket import KISWebSocket
                self.ws = KISWebSocket()
                print(f"\n✅ WebSocket 클라이언트 준비 완료")
            except Exception as e:
                print(f"\n⚠️  WebSocket 초기화 실패: {e}")
                print("   한국 주식도 분봉으로 모니터링합니다.")
                self.ws = None
        
        print(f"\n✅ 초기화 완료: {len(self.target_prices)}개 종목 모니터링 준비")
        return len(self.target_prices) > 0
    
    async def check_and_alert(self, ticker: str, current_price: float):
        """
        가격 확인 및 알림 전송 (알림 시간 외에는 DB에만 기록)
        
        Args:
            ticker: 종목코드
            current_price: 현재가
        """
        if ticker not in self.target_prices:
            return
        
        targets = self.target_prices[ticker]
        name = targets['name']
        
        # 알림 시간 체크
        is_alert_time = self._is_alert_time()
        
        # 1차 매수 목표가 도달 확인
        if current_price <= targets['1x']:
            await self._send_buy_alert(ticker, name, current_price, '1x', targets, send_now=is_alert_time)
        
        # 2차 매수 목표가 도달 확인
        if current_price <= targets['2x']:
            await self._send_buy_alert(ticker, name, current_price, '2x', targets, send_now=is_alert_time)
    
    async def _send_buy_alert(self, ticker: str, name: str, current_price: float, level: str, targets: dict, send_now: bool = True):
        """
        매수 알림 전송 또는 DB 기록
        
        Args:
            send_now: True면 즉시 전송, False면 DB에만 기록
        """
        # 중복 알림 방지 (5분 내 동일 레벨 알림 방지)
        now = datetime.now()
        if ticker in self.alert_history:
            last_alert = self.alert_history[ticker].get(level)
            if last_alert and (now - last_alert).seconds < 300:  # 5분
                return
        
        # 알림 메시지 구성
        level_text = "1차" if level == '1x' else "2차"
        target_price = targets[level]
        drop_rate = targets[f'drop_{level}']
        country = targets['country']
        flag = '🇰🇷' if country == 'KR' else '🇺🇸'
        
        # 통화 단위 결정
        if country == 'KR':
            price_format = f"{current_price:,.0f}원"
            target_format = f"{target_price:,.0f}원"
        else:
            price_format = f"${current_price:,.2f}"
            target_format = f"${target_price:,.2f}"
        
        message = f"🚨 실시간 매수 알림! {level_text} 매수 시점 도달\n\n"
        message += f"{flag} {name} ({ticker})\n"
        message += f"💰 현재가: {price_format}\n"
        message += f"🎯 목표가: {target_format}\n"
        message += f"📉 하락률: {drop_rate:.2f}%\n\n"
        message += f"⏰ {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if level == '1x':
            message += "💡 1차 매수 타이밍입니다!\n"
        else:
            message += "💡 2차 매수 타이밍입니다! (2배 투자)\n"
        
        message += "\n📊 차트는 오늘 아침 알림을 확인하세요"
        
        # DB에 기록 (알림 시간 여부와 상관없이 항상)
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO alert_history 
            (ticker, ticker_name, country, alert_level, target_price, current_price, drop_rate, alert_time, sent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ticker, name, country, level, target_price, current_price, drop_rate, now.isoformat(), 1 if send_now else 0))
        conn.commit()
        
        # 알림 전송 (알림 시간일 때만)
        if send_now:
            users = self.db.get_all_users()
            
            for user in users:
                if not user['enabled']:
                    continue
                
                # 해당 사용자가 이 종목을 관심 종목으로 가지고 있는지 확인
                cursor.execute('''
                    SELECT COUNT(*) FROM user_watchlist 
                    WHERE user_id = ? AND ticker = ? AND enabled = 1
                ''', (user['id'], ticker))
                
                if cursor.fetchone()[0] == 0:
                    continue
                
                try:
                    send_telegram_sync(
                        self.telegram_config['BOT_TOKEN'],
                        user['chat_id'],
                        message=message
                    )
                    print(f"  ✅ {user['name']}님에게 {level_text} 매수 알림 전송")
                    
                except Exception as e:
                    print(f"  ❌ {user['name']}님 알림 전송 실패: {e}")
            
            print(f"🚨 {name} ({ticker}) {level_text} 매수 알림 전송")
        else:
            # 알림 시간 외에는 DB에만 기록
            print(f"💾 {name} ({ticker}) {level_text} 매수 시점 기록 (알림 시간 외: {now.strftime('%H:%M:%S')})")
        
        # 알림 이력 기록 (중복 방지용)
        if ticker not in self.alert_history:
            self.alert_history[ticker] = {}
        self.alert_history[ticker][level] = now
    
    async def monitor_korean_stocks_ws(self):
        """한국 주식 WebSocket 모니터링"""
        if not self.ws:
            return
        
        korean_stocks = {t: p for t, p in self.target_prices.items() if p['country'] == 'KR'}
        
        if not korean_stocks:
            return
        
        print("\n🇰🇷 한국 주식 WebSocket 모니터링 시작...")
        
        try:
            await self.ws.connect()
            
            # WebSocket 콜백
            async def price_callback(price_info):
                ticker = price_info['ticker']
                current_price = price_info['current_price']
                await self.check_and_alert(ticker, current_price)
            
            # 종목별 구독
            for ticker in korean_stocks.keys():
                await self.ws.subscribe_price(ticker, price_callback)
            
            # 실시간 데이터 수신
            await self.ws.listen()
            
        except Exception as e:
            print(f"⚠️  WebSocket 오류: {e}")
    
    async def monitor_us_stocks_poll(self):
        """미국 주식 폴링 모니터링 (1분 간격) - KIS API 우선"""
        us_stocks = {t: p for t, p in self.target_prices.items() if p['country'] == 'US'}
        
        if not us_stocks:
            return
        
        print(f"\n🇺🇸 미국 주식 폴링 모니터링 시작... ({len(us_stocks)}개)")
        
        # KIS API 초기화
        kis_api = None
        try:
            from kis_api import KISApi
            kis_api = KISApi()
            print(f"  ✅ KIS API 활성화 (미국 주식)")
        except Exception as e:
            print(f"  ⚠️  KIS API 비활성화: {e}")
            print(f"     FinanceDataReader로 대체합니다.")
        
        while True:
            # 알림 시간 체크
            if not self._is_alert_time():
                print(f"⏸️  알림 시간 외 (09:00~24:00만 알림)")
                await asyncio.sleep(60)
                continue
            
            for ticker, targets in us_stocks.items():
                try:
                    current_price = None
                    
                    # 1순위: KIS API
                    if kis_api:
                        try:
                            exchange = kis_api.get_exchange_code(ticker)
                            price_info = kis_api.get_overseas_stock_price(ticker, exchange)
                            if price_info:
                                current_price = price_info['current_price']
                        except Exception as e:
                            print(f"  ⚠️  KIS API 오류 ({ticker}): {e}")
                    
                    # 2순위: FDR (Fallback)
                    if current_price is None:
                        df = fdr.DataReader(ticker, datetime.now().date(), datetime.now())
                        if df is not None and not df.empty:
                            current_price = float(df['Close'].iloc[-1])
                    
                    # 알림 확인
                    if current_price:
                        await self.check_and_alert(ticker, current_price)
                
                except Exception as e:
                    print(f"⚠️  {ticker} 조회 오류: {e}")
            
            # 1분 대기
            await asyncio.sleep(60)
    
    async def start_monitoring(self):
        """모니터링 시작"""
        print("\n" + "="*70)
        print("👂 하이브리드 실시간 모니터링 시작!")
        print("="*70)
        print(f"📊 모니터링 종목: {len(self.target_prices)}개")
        print(f"⏰ 알림 시간: {self.alert_start_time.strftime('%H:%M')} ~ {self.alert_end_time.strftime('%H:%M')}")
        print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n💡 Ctrl+C로 종료")
        print("="*70)
        
        try:
            # 한국/미국 주식 동시 모니터링
            await asyncio.gather(
                self.monitor_korean_stocks_ws(),
                self.monitor_us_stocks_poll()
            )
        
        except KeyboardInterrupt:
            print("\n\n⏸️  사용자가 종료했습니다.")
        except Exception as e:
            print(f"\n❌ 모니터링 오류: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """리소스 정리"""
        print("\n🧹 리소스 정리 중...")
        
        if self.ws:
            await self.ws.disconnect()
            self.ws.close()
        
        if self.db:
            self.db.close()
        
        print("✅ 정리 완료")


async def main():
    """메인 실행 함수"""
    monitor = HybridRealtimeMonitor()
    
    try:
        if await monitor.initialize():
            await monitor.start_monitoring()
        else:
            print("\n⚠️  모니터링할 종목이 없습니다.")
    
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await monitor.cleanup()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 하이브리드 실시간 매수 알림 시스템")
    print("="*70)
    print("""
🇰🇷 한국 주식: WebSocket 실시간 모니터링
🇺🇸 미국 주식: 1분 간격 폴링 모니터링
⏰ 알림 시간: 09:00~24:00

실시간으로 가격을 모니터링하여
1-sigma, 2-sigma 매수 타이밍을 즉시 알려드립니다!
""")
    
    # 실행
    asyncio.run(main())

