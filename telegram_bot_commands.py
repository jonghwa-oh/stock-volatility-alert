#!/usr/bin/env python3
"""
텔레그램 봇 커맨드 핸들러
사용자가 텔레그램에서 봇에게 명령을 보내면 처리하는 모듈
"""
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from database import StockDatabase
from daily_analysis import send_daily_alerts, analyze_all_stocks
from volatility_analysis import analyze_daily_volatility
from config import load_config
from kis_api import KISApi
import FinanceDataReader as fdr
from datetime import datetime


class TelegramBotCommandHandler:
    """텔레그램 봇 커맨드 핸들러"""
    
    def __init__(self):
        self.db = StockDatabase()
        config = load_config()
        self.bot_token = config['TELEGRAM_CONFIG']['BOT_TOKEN']
        self.kis_api = KISApi()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /start - 봇 시작 및 환영 메시지
        """
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # 사용자 확인
        users = self.db.get_all_users()
        is_registered = any(u['chat_id'] == str(chat_id) for u in users)
        
        message = f"👋 안녕하세요, {user.first_name}님!\n\n"
        message += "📊 주식 변동성 알림 봇입니다.\n\n"
        
        if is_registered:
            message += "✅ 등록된 사용자입니다!\n\n"
        else:
            message += "❌ 등록되지 않은 사용자입니다.\n"
            message += f"💡 관리자에게 Chat ID를 알려주세요: `{chat_id}`\n\n"
        
        message += "📝 사용 가능한 명령어:\n"
        message += "/help - 도움말\n"
        message += "/list - 내 종목 목록\n"
        message += "/add TICKER - 종목 추가\n"
        message += "/remove TICKER - 종목 삭제\n"
        message += "/morning - 아침 알림 받기\n"
        message += "/status - 실시간 현재가 확인"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /help - 도움말
        """
        message = "📖 명령어 도움말\n\n"
        
        message += "📝 종목 관리:\n"
        message += "/list - 내 관심 종목 목록 보기\n"
        message += "/add TICKER - 종목 추가\n"
        message += "   예) /add TQQQ\n"
        message += "   예) /add 122630\n"
        message += "/remove TICKER - 종목 삭제\n"
        message += "   예) /remove TQQQ\n\n"
        
        message += "📊 실시간 조회:\n"
        message += "/morning - 오늘의 매수 전략 받기\n"
        message += "/status - 현재가 및 목표가 확인\n"
        message += "   예) /status\n"
        message += "   예) /status TQQQ\n\n"
        
        message += "💡 Tips:\n"
        message += "• 한국 주식: 티커 번호 (예: 122630)\n"
        message += "• 미국 주식: 티커 심볼 (예: TQQQ)\n"
        message += "• 실시간 알림은 09:00~24:00에만 전송됩니다.\n"
        message += "• 밤 사이 놓친 알림은 08:00에 요약 전송됩니다."
        
        await update.message.reply_text(message)
    
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /list - 내 관심 종목 목록
        """
        chat_id = str(update.effective_chat.id)
        
        # 사용자 찾기
        users = self.db.get_all_users()
        user = next((u for u in users if u['chat_id'] == chat_id), None)
        
        if not user:
            await update.message.reply_text(
                "❌ 등록되지 않은 사용자입니다.\n"
                f"관리자에게 Chat ID를 알려주세요: `{chat_id}`",
                parse_mode='Markdown'
            )
            return
        
        # 관심 종목 가져오기
        watchlist = self.db.get_user_watchlist_with_names(user['name'])
        
        if not watchlist:
            await update.message.reply_text("📝 관심 종목이 없습니다.\n\n/add TICKER 로 종목을 추가하세요!")
            return
        
        message = f"📊 {user['name']}님의 관심 종목\n\n"
        message += f"투자금액: {int(user['investment_amount']):,}원\n\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"
        
        for idx, stock in enumerate(watchlist, 1):
            ticker = stock['ticker']
            name = stock['name']
            country = stock['country']
            flag = '🇰🇷' if country == 'KR' else '🇺🇸'
            
            if ticker.isdigit():
                message += f"{idx}. {flag} {name} ({ticker})\n"
            else:
                message += f"{idx}. {flag} {ticker} - {name}\n"
        
        message += f"\n━━━━━━━━━━━━━━━━━━\n"
        message += f"총 {len(watchlist)}개 종목"
        
        await update.message.reply_text(message)
    
    async def add_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /add TICKER - 종목 추가
        """
        chat_id = str(update.effective_chat.id)
        
        # 인자 확인
        if not context.args or len(context.args) < 1:
            await update.message.reply_text(
                "❌ 티커를 입력해주세요.\n\n"
                "사용법: /add TICKER\n"
                "예) /add TQQQ\n"
                "예) /add 122630"
            )
            return
        
        ticker = context.args[0].upper()
        
        # 사용자 찾기
        users = self.db.get_all_users()
        user = next((u for u in users if u['chat_id'] == chat_id), None)
        
        if not user:
            await update.message.reply_text(
                "❌ 등록되지 않은 사용자입니다.\n"
                f"관리자에게 Chat ID를 알려주세요: `{chat_id}`",
                parse_mode='Markdown'
            )
            return
        
        # 이미 있는지 확인
        watchlist = self.db.get_user_watchlist_with_names(user['name'])
        if any(stock['ticker'] == ticker for stock in watchlist):
            await update.message.reply_text(f"⚠️  {ticker}는 이미 관심 종목에 있습니다!")
            return
        
        # 종목 정보 가져오기
        await update.message.reply_text(f"🔍 {ticker} 정보를 확인 중...")
        
        try:
            # 한국 주식인지 미국 주식인지 판별
            is_korean = ticker.isdigit()
            country = 'KR' if is_korean else 'US'
            
            # 티커 이름 가져오기
            if is_korean:
                # KIS API로 한국 주식 조회
                price_data = self.kis_api.get_stock_price(ticker)
                if price_data and 'name' in price_data:
                    ticker_name = price_data['name']
                else:
                    # FDR로 백업
                    df = fdr.DataReader(ticker)
                    ticker_name = ticker
            else:
                # KIS API로 미국 주식 조회
                price_data = self.kis_api.get_overseas_stock_price(ticker)
                if price_data and 'name' in price_data:
                    ticker_name = price_data['name']
                else:
                    # FDR로 백업
                    df = fdr.DataReader(ticker)
                    ticker_name = ticker
            
            # DB에 추가
            conn = self.db.connect()
            cursor = conn.cursor()
            
            # 먼저 daily_prices에 추가 (없으면)
            cursor.execute('SELECT COUNT(*) FROM daily_prices WHERE ticker = ?', (ticker,))
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO daily_prices (ticker, ticker_name, country)
                    VALUES (?, ?, ?)
                ''', (ticker, ticker_name, country))
            
            # user_watchlist에 추가
            cursor.execute('''
                INSERT INTO user_watchlist (user_id, ticker, country, enabled)
                VALUES (?, ?, ?, 1)
            ''', (user['id'], ticker, country))
            
            conn.commit()
            self.db.close()
            
            flag = '🇰🇷' if is_korean else '🇺🇸'
            await update.message.reply_text(
                f"✅ {flag} {ticker_name} ({ticker}) 추가 완료!\n\n"
                "💡 내일 아침부터 알림을 받습니다."
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ 종목 추가 실패: {str(e)}\n\n"
                "티커가 올바른지 확인해주세요."
            )
    
    async def remove_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /remove TICKER - 종목 삭제
        """
        chat_id = str(update.effective_chat.id)
        
        # 인자 확인
        if not context.args or len(context.args) < 1:
            await update.message.reply_text(
                "❌ 티커를 입력해주세요.\n\n"
                "사용법: /remove TICKER\n"
                "예) /remove TQQQ"
            )
            return
        
        ticker = context.args[0].upper()
        
        # 사용자 찾기
        users = self.db.get_all_users()
        user = next((u for u in users if u['chat_id'] == chat_id), None)
        
        if not user:
            await update.message.reply_text(
                "❌ 등록되지 않은 사용자입니다.\n"
                f"관리자에게 Chat ID를 알려주세요: `{chat_id}`",
                parse_mode='Markdown'
            )
            return
        
        # 종목 삭제
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM user_watchlist
            WHERE user_id = ? AND ticker = ?
        ''', (user['id'], ticker))
        
        if cursor.rowcount > 0:
            conn.commit()
            await update.message.reply_text(f"✅ {ticker} 삭제 완료!")
        else:
            await update.message.reply_text(f"❌ {ticker}는 관심 종목에 없습니다.")
        
        self.db.close()
    
    async def morning_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /morning - 아침 알림 수동 받기
        """
        chat_id = str(update.effective_chat.id)
        
        # 사용자 찾기
        users = self.db.get_all_users()
        user = next((u for u in users if u['chat_id'] == chat_id), None)
        
        if not user:
            await update.message.reply_text(
                "❌ 등록되지 않은 사용자입니다.\n"
                f"관리자에게 Chat ID를 알려주세요: `{chat_id}`",
                parse_mode='Markdown'
            )
            return
        
        await update.message.reply_text("📊 분석 중... 잠시만 기다려주세요!")
        
        try:
            # 분석 실행
            analysis_results = analyze_all_stocks()
            
            # 알림 전송
            send_daily_alerts(analysis_results)
            
        except Exception as e:
            await update.message.reply_text(f"❌ 분석 실패: {str(e)}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /status [TICKER] - 현재가 및 목표가 확인
        """
        chat_id = str(update.effective_chat.id)
        
        # 사용자 찾기
        users = self.db.get_all_users()
        user = next((u for u in users if u['chat_id'] == chat_id), None)
        
        if not user:
            await update.message.reply_text(
                "❌ 등록되지 않은 사용자입니다.\n"
                f"관리자에게 Chat ID를 알려주세요: `{chat_id}`",
                parse_mode='Markdown'
            )
            return
        
        # 티커 지정 여부 확인
        if context.args and len(context.args) > 0:
            # 특정 티커만
            ticker = context.args[0].upper()
            watchlist = self.db.get_user_watchlist_with_names(user['name'])
            stocks_to_check = [s for s in watchlist if s['ticker'] == ticker]
            
            if not stocks_to_check:
                await update.message.reply_text(f"❌ {ticker}는 관심 종목에 없습니다.")
                return
        else:
            # 전체 종목
            watchlist = self.db.get_user_watchlist_with_names(user['name'])
            stocks_to_check = watchlist
        
        if not stocks_to_check:
            await update.message.reply_text("📝 관심 종목이 없습니다.")
            return
        
        await update.message.reply_text("🔍 현재가 조회 중...")
        
        message = f"📊 {user['name']}님의 실시간 현황\n\n"
        message += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"
        
        for stock in stocks_to_check:
            ticker = stock['ticker']
            name = stock['name']
            country = stock['country']
            flag = '🇰🇷' if country == 'KR' else '🇺🇸'
            
            try:
                # 현재가 가져오기
                if country == 'KR':
                    price_data = self.kis_api.get_stock_price(ticker)
                    if price_data:
                        current_price = price_data['price']
                    else:
                        current_price = None
                else:
                    price_data = self.kis_api.get_overseas_stock_price(ticker)
                    if price_data:
                        current_price = price_data['price']
                    else:
                        current_price = None
                
                if not current_price:
                    message += f"{flag} {name} ({ticker})\n"
                    message += "   ❌ 현재가 조회 실패\n\n"
                    continue
                
                # 목표가 계산
                data = analyze_daily_volatility(ticker, name, investment_amount=user['investment_amount'])
                
                if data:
                    if country == 'KR':
                        message += f"{flag} {name} ({ticker})\n"
                        message += f"💰 현재가: {current_price:,.0f}원\n\n"
                        message += f"🧪 테스트: {data['target_05x']:,.0f}원 ({data['drop_05x']:.2f}% 하락)\n"
                        message += f"1차 매수: {data['target_1x']:,.0f}원 ({data['drop_1x']:.2f}% 하락)\n"
                        message += f"2차 매수: {data['target_2x']:,.0f}원 ({data['drop_2x']:.2f}% 하락)\n\n"
                    else:
                        message += f"{flag} {ticker} - {name}\n"
                        message += f"💰 현재가: ${current_price:,.2f}\n\n"
                        message += f"🧪 테스트: ${data['target_05x']:,.2f} ({data['drop_05x']:.2f}% 하락)\n"
                        message += f"1차 매수: ${data['target_1x']:,.2f} ({data['drop_1x']:.2f}% 하락)\n"
                        message += f"2차 매수: ${data['target_2x']:,.2f} ({data['drop_2x']:.2f}% 하락)\n\n"
                else:
                    message += f"{flag} {name} ({ticker})\n"
                    message += f"💰 현재가: {current_price}\n"
                    message += "   ❌ 목표가 계산 실패\n\n"
                    
            except Exception as e:
                message += f"{flag} {name} ({ticker})\n"
                message += f"   ❌ 오류: {str(e)}\n\n"
        
        message += "━━━━━━━━━━━━━━━━━━"
        
        await update.message.reply_text(message)
    
    def run(self):
        """봇 실행"""
        print("\n" + "="*70)
        print("🤖 텔레그램 봇 커맨드 핸들러 시작")
        print("="*70)
        
        # Application 생성
        application = Application.builder().token(self.bot_token).build()
        
        # 커맨드 핸들러 등록
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("list", self.list_command))
        application.add_handler(CommandHandler("add", self.add_command))
        application.add_handler(CommandHandler("remove", self.remove_command))
        application.add_handler(CommandHandler("morning", self.morning_command))
        application.add_handler(CommandHandler("status", self.status_command))
        
        print("\n✅ 커맨드 핸들러 등록 완료:")
        print("   - /start: 봇 시작")
        print("   - /help: 도움말")
        print("   - /list: 종목 목록")
        print("   - /add: 종목 추가")
        print("   - /remove: 종목 삭제")
        print("   - /morning: 아침 알림")
        print("   - /status: 현재가 확인")
        
        print("\n🚀 봇 시작... (Ctrl+C로 종료)")
        print("="*70 + "\n")
        
        # 봇 실행
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    handler = TelegramBotCommandHandler()
    handler.run()

