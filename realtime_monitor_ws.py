"""
WebSocket 기반 실시간 매수 알림 시스템
1-sigma, 2-sigma 도달 시 즉시 텔레그램 알림
"""
import asyncio
from datetime import datetime
from pathlib import Path
from kis_websocket import KISWebSocket
from database import StockDatabase
from volatility_analysis import analyze_daily_volatility
from telegram_bot import send_telegram_sync
from config import load_config


class RealtimeMonitorWS:
    """WebSocket 기반 실시간 모니터링"""
    
    def __init__(self):
        self.db = StockDatabase()
        self.ws = KISWebSocket()
        self.config = load_config()
        self.telegram_config = self.config['TELEGRAM_CONFIG']
        
        # 종목별 매수 목표가 캐시
        self.target_prices = {}  # {ticker: {'1x': price, '2x': price, 'name': name}}
        
        # 알림 전송 이력 (중복 방지)
        self.alert_history = {}  # {ticker: {'1x': timestamp, '2x': timestamp}}
    
    def _is_korean_stock(self, ticker: str) -> bool:
        """한국 주식 여부 판단"""
        return ticker.isdigit() and len(ticker) == 6
    
    async def initialize(self):
        """초기화: 종목별 매수 목표가 계산"""
        print("\n" + "="*70)
        print("🚀 실시간 매수 알림 시스템 초기화 (WebSocket)")
        print("="*70)
        
        # 활성 사용자의 관심 종목 수집
        users = self.db.get_all_users()
        unique_tickers = {}
        
        for user in users:
            if not user['enabled']:
                continue
            
            watchlist = self.db.get_user_watchlist_with_names(user['name'])
            for stock in watchlist:
                unique_tickers[stock['ticker']] = stock['name']
        
        if not unique_tickers:
            print("⚠️  활성 종목이 없습니다.")
            return False
        
        print(f"\n📊 모니터링 종목: {len(unique_tickers)}개")
        
        # 한국 주식만 WebSocket으로 모니터링
        korean_stocks = {t: n for t, n in unique_tickers.items() if self._is_korean_stock(t)}
        
        if not korean_stocks:
            print("⚠️  한국 주식이 없습니다. (WebSocket은 한국 주식만 지원)")
            return False
        
        print(f"🇰🇷 한국 주식: {len(korean_stocks)}개 (WebSocket 모니터링)")
        
        # 매수 목표가 계산
        for ticker, name in korean_stocks.items():
            print(f"\n📊 {name} ({ticker}) 분석 중...")
            
            try:
                data = analyze_daily_volatility(ticker, name)
                
                if data:
                    self.target_prices[ticker] = {
                        '1x': data['target_1x'],
                        '2x': data['target_2x'],
                        'name': name,
                        'drop_1x': data['drop_1x'],
                        'drop_2x': data['drop_2x']
                    }
                    
                    print(f"  ✅ 1차 매수: {data['target_1x']:,.0f}원 ({data['drop_1x']:.2f}% 하락)")
                    print(f"  ✅ 2차 매수: {data['target_2x']:,.0f}원 ({data['drop_2x']:.2f}% 하락)")
                else:
                    print(f"  ❌ 분석 실패")
                    
            except Exception as e:
                print(f"  ❌ 오류: {e}")
        
        print(f"\n✅ 초기화 완료: {len(self.target_prices)}개 종목 모니터링 준비")
        return len(self.target_prices) > 0
    
    async def check_and_alert(self, price_info: dict):
        """
        가격 확인 및 알림 전송
        
        Args:
            price_info: WebSocket에서 수신한 가격 정보
        """
        ticker = price_info['ticker']
        current_price = price_info['current_price']
        
        if ticker not in self.target_prices:
            return
        
        targets = self.target_prices[ticker]
        name = targets['name']
        
        # 1차 매수 목표가 도달 확인
        if current_price <= targets['1x']:
            await self._send_buy_alert(ticker, name, current_price, '1x', targets)
        
        # 2차 매수 목표가 도달 확인
        if current_price <= targets['2x']:
            await self._send_buy_alert(ticker, name, current_price, '2x', targets)
    
    async def _send_buy_alert(self, ticker: str, name: str, current_price: float, level: str, targets: dict):
        """
        매수 알림 전송
        
        Args:
            ticker: 종목코드
            name: 종목명
            current_price: 현재가
            level: '1x' 또는 '2x'
            targets: 매수 목표가 정보
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
        
        message = f"🚨 매수 알림! {level_text} 매수 시점 도달\n\n"
        
        if ticker.isdigit():
            message += f"📊 {name} ({ticker})\n"
        else:
            message += f"📊 {ticker} - {name}\n"
        
        message += f"💰 현재가: {current_price:,.0f}원\n"
        message += f"🎯 목표가: {target_price:,.0f}원\n"
        message += f"📉 하락률: {drop_rate:.2f}%\n\n"
        message += f"⏰ {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if level == '1x':
            message += "💡 1차 매수 타이밍입니다!"
        else:
            message += "💡 2차 매수 타이밍입니다! (2배 투자)"
        
        # 차트 이미지 첨부
        today = now.strftime('%Y-%m-%d')
        chart_path = Path('charts') / ticker / f"{today}_{ticker}_{name.replace(' ', '_')}_volatility.png"
        
        # 모든 사용자에게 알림
        users = self.db.get_all_users()
        
        for user in users:
            if not user['enabled']:
                continue
            
            # 해당 사용자가 이 종목을 관심 종목으로 가지고 있는지 확인
            watchlist = self.db.get_user_watchlist_with_names(user['name'])
            if not any(s['ticker'] == ticker for s in watchlist):
                continue
            
            try:
                if chart_path.exists():
                    send_telegram_sync(
                        self.telegram_config['BOT_TOKEN'],
                        user['chat_id'],
                        photo_path=str(chart_path),
                        message=message
                    )
                else:
                    send_telegram_sync(
                        self.telegram_config['BOT_TOKEN'],
                        user['chat_id'],
                        message=message
                    )
                
                print(f"  ✅ {user['name']}님에게 {level_text} 매수 알림 전송")
                
            except Exception as e:
                print(f"  ❌ {user['name']}님 알림 전송 실패: {e}")
        
        # 알림 이력 기록
        if ticker not in self.alert_history:
            self.alert_history[ticker] = {}
        self.alert_history[ticker][level] = now
        
        print(f"🚨 {name} ({ticker}) {level_text} 매수 알림 전송: {current_price:,.0f}원")
    
    async def start_monitoring(self):
        """실시간 모니터링 시작"""
        try:
            # WebSocket 연결
            await self.ws.connect()
            
            # 종목별 구독
            for ticker in self.target_prices.keys():
                await self.ws.subscribe_price(ticker, self.check_and_alert)
            
            print("\n" + "="*70)
            print("👂 실시간 모니터링 시작!")
            print("="*70)
            print(f"📊 모니터링 종목: {len(self.target_prices)}개")
            print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("\n💡 Ctrl+C로 종료")
            print("="*70)
            
            # 실시간 데이터 수신
            await self.ws.listen()
            
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
    monitor = RealtimeMonitorWS()
    
    try:
        # 초기화
        if await monitor.initialize():
            # 모니터링 시작
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
    print("🚀 WebSocket 기반 실시간 매수 알림 시스템")
    print("="*70)
    print("\n실시간으로 가격을 모니터링하여")
    print("1-sigma, 2-sigma 매수 타이밍을 즉시 알려드립니다!\n")
    
    # 실행
    asyncio.run(main())

