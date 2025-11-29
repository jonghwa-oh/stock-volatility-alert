"""
텔레그램 봇 알림 기능
"""

import asyncio
from telegram import Bot
from telegram.error import TelegramError
from pathlib import Path


class TelegramNotifier:
    """텔레그램 알림 클래스"""
    
    def __init__(self, bot_token, chat_id):
        """
        Args:
            bot_token: 봇 토큰
            chat_id: 채팅 ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = Bot(token=bot_token)
    
    async def send_message(self, message):
        """
        텍스트 메시지 전송
        
        Args:
            message: 전송할 메시지
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            print("✅ 텔레그램 메시지 전송 완료")
        except TelegramError as e:
            print(f"❌ 텔레그램 메시지 전송 실패: {e}")
    
    async def send_photo(self, photo_path, caption=None):
        """
        이미지 전송
        
        Args:
            photo_path: 이미지 파일 경로
            caption: 이미지 설명
        """
        try:
            with open(photo_path, 'rb') as photo:
                await self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode='HTML'
                )
            print(f"✅ 이미지 전송 완료: {photo_path}")
        except TelegramError as e:
            print(f"❌ 이미지 전송 실패: {e}")
        except FileNotFoundError:
            print(f"❌ 파일을 찾을 수 없습니다: {photo_path}")
    
    async def send_analysis_report(self, analysis_result, chart_path=None):
        """
        분석 리포트 전송
        
        Args:
            analysis_result: 분석 결과 딕셔너리
            chart_path: 차트 이미지 경로
        """
        # 메시지 작성
        message = self._format_analysis_message(analysis_result)
        
        # 메시지 전송
        await self.send_message(message)
        
        # 차트 전송 (있으면)
        if chart_path and Path(chart_path).exists():
            await self.send_photo(chart_path, caption=f"📊 {analysis_result['ticker_name']} 차트")
    
    def _format_analysis_message(self, result):
        """분석 결과를 메시지 형식으로 변환"""
        ticker_name = result['ticker_name']
        current = result['current_price']
        mean_ret = result['mean_return']
        std_ret = result['std_return']
        target_1x = result['target_1x']
        target_2x = result['target_2x']
        drop_1x = result['drop_1x']
        drop_2x = result['drop_2x']
        up_days = result['up_days']
        down_days = result['down_days']
        
        # 매수 상태 판단
        is_buy_signal = False
        status_icon = "📊"
        
        message = f"<b>📊 {ticker_name}</b>\n"
        message += f"{'='*30}\n\n"
        
        message += f"💰 <b>현재가:</b> {current:,.2f}\n"
        message += f"📈 <b>평균 일일 변동:</b> {mean_ret:+.2f}%\n"
        message += f"📊 <b>표준편차:</b> {std_ret:.2f}%\n"
        message += f"   (하루 평균 ±{std_ret:.2f}% 움직임)\n\n"
        
        message += f"📅 <b>1년간 거래일:</b>\n"
        message += f"   • 상승: {up_days}일\n"
        message += f"   • 하락: {down_days}일\n\n"
        
        message += f"🎯 <b>매수 목표가:</b>\n"
        message += f"   📍 1차: {target_1x:,.2f}\n"
        message += f"      (하루 {drop_1x:.2f}% 하락 시)\n"
        message += f"   📍 2차: {target_2x:,.2f}\n"
        message += f"      (하루 {drop_2x:.2f}% 하락 시)\n\n"
        
        # 최근 변동률 체크
        if 'latest_change' in result and result['latest_change'] is not None:
            latest = result['latest_change']
            message += f"📉 <b>최근 변동:</b> {latest:+.2f}%\n"
            
            if latest <= -drop_1x * 0.8:  # 1차 목표의 80% 이상 하락
                message += f"\n🔔 <b>주의!</b> 매수 기회가 가까워졌습니다!\n"
                is_buy_signal = True
        
        return message
    
    async def send_daily_summary(self, all_results):
        """
        전체 종목 요약 전송
        
        Args:
            all_results: 전체 분석 결과 리스트
        """
        message = "<b>📊 일일 변동성 분석 리포트</b>\n"
        message += f"{'='*35}\n\n"
        
        # 변동성 순위
        sorted_results = sorted(all_results, key=lambda x: x['std_return'], reverse=True)
        
        message += "<b>🎯 변동성 순위:</b>\n\n"
        for idx, result in enumerate(sorted_results, 1):
            name = result['ticker_name']
            std = result['std_return']
            current = result['current_price']
            
            message += f"{idx}. <b>{name}</b>\n"
            message += f"   • 표준편차: {std:.2f}%\n"
            message += f"   • 현재가: {current:,.2f}\n\n"
        
        await self.send_message(message)
    
    async def send_buy_alert(self, ticker_name, current_price, drop_pct, target_price, level):
        """
        매수 알림 전송
        
        Args:
            ticker_name: 종목명
            current_price: 현재가
            drop_pct: 하락률
            target_price: 목표가
            level: 1차/2차
        """
        message = "🔔 <b>매수 신호 발생!</b>\n"
        message += f"{'='*30}\n\n"
        message += f"📊 <b>{ticker_name}</b>\n\n"
        message += f"💰 현재가: {current_price:,.2f}\n"
        message += f"📉 하락률: {drop_pct:+.2f}%\n"
        message += f"🎯 목표가: {target_price:,.2f}\n"
        message += f"⭐ 상태: <b>{level}차 매수 시점!</b>\n\n"
        message += f"💡 지금이 매수 기회입니다!"
        
        await self.send_message(message)


def send_telegram_sync(bot_token, chat_id, message=None, photo_path=None):
    """
    동기 방식으로 텔레그램 전송 (기존 코드와 호환)
    
    Args:
        bot_token: 봇 토큰
        chat_id: 채팅 ID
        message: 메시지
        photo_path: 이미지 경로
    """
    notifier = TelegramNotifier(bot_token, chat_id)
    
    async def send():
        if message:
            await notifier.send_message(message)
        if photo_path:
            await notifier.send_photo(photo_path)
    
    asyncio.run(send())


# 테스트 함수
def test_telegram_bot(bot_token, chat_id):
    """텔레그램 봇 테스트"""
    print("텔레그램 봇 연결 테스트 중...")
    
    notifier = TelegramNotifier(bot_token, chat_id)
    
    async def test():
        await notifier.send_message(
            "✅ <b>텔레그램 봇 연결 성공!</b>\n\n"
            "주식 변동성 알림 시스템이 준비되었습니다. 🎉"
        )
    
    try:
        asyncio.run(test())
        print("✅ 테스트 성공!")
        return True
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    # config.py에서 설정 가져오기
    try:
        from config import TELEGRAM_CONFIG
        
        bot_token = TELEGRAM_CONFIG['BOT_TOKEN']
        chat_id = TELEGRAM_CONFIG['CHAT_ID']
        
        if bot_token == 'YOUR_BOT_TOKEN_HERE' or chat_id == 'YOUR_CHAT_ID_HERE':
            print("⚠️  config.py에서 BOT_TOKEN과 CHAT_ID를 설정해주세요!")
        else:
            test_telegram_bot(bot_token, chat_id)
    
    except ImportError:
        print("❌ config.py 파일을 찾을 수 없습니다.")

