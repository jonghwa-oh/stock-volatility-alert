#!/usr/bin/env python3
"""
텔레그램 봇 커맨드 핸들러
사용자가 텔레그램에서 봇에게 명령을 보내면 처리하는 모듈
"""
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from database import StockDatabase
from daily_analysis import send_daily_alerts, analyze_and_generate_charts
from volatility_analysis import analyze_daily_volatility
from config import load_config
from kis_api import KISApi
import FinanceDataReader as fdr
from datetime import datetime
import traceback
from log_utils import log, log_section, log_success, log_error, log_debug, log_warning
from telegram_bot import send_telegram_sync


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
        log(f"📥 /start 명령 수신 - User: {update.effective_user.first_name}, Chat ID: {update.effective_chat.id}")
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
        message += "/status - 실시간 현재가 확인\n"
        message += "/alarm_on - 알림 켜기\n"
        message += "/alarm_off - 알림 끄기\n"
        message += "/alarm_status - 알림 상태"
        
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
        
        message += "🔔 알림 설정:\n"
        message += "/alarm_on - 알림 켜기\n"
        message += "/alarm_off - 알림 끄기\n"
        message += "/alarm_status - 알림 상태 확인\n\n"
        
        message += "💡 Tips:\n"
        message += "• 한국 주식: 티커 번호 (예: 122630)\n"
        message += "• 미국 주식: 티커 심볼 (예: TQQQ)\n"
        message += "• 실시간 알림은 09:00~24:00에만 전송됩니다.\n"
        message += "• 밤 사이 놓친 알림은 08:00에 요약 전송됩니다.\n"
        message += "• 잠잘 때는 /alarm_off로 알림을 끌 수 있습니다."
        
        await update.message.reply_text(message)
    
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /list - 내 관심 종목 목록
        """
        try:
            log(f"📥 /list 명령 수신 - Chat ID: {update.effective_chat.id}")
            chat_id = str(update.effective_chat.id)
            
            # 사용자 찾기
            users = self.db.get_all_users()
            log_debug(f"전체 사용자 수: {len(users)}")
            
            user = next((u for u in users if u['chat_id'] == chat_id), None)
            
            if not user:
                log_error(f"미등록 사용자: {chat_id}")
                await update.message.reply_text(
                    "❌ 등록되지 않은 사용자입니다.\n"
                    f"관리자에게 Chat ID를 알려주세요: `{chat_id}`",
                    parse_mode='Markdown'
                )
                return
            
            log_debug(f"사용자 찾음: {user['name']}")
            
            # 관심 종목 가져오기
            watchlist = self.db.get_user_watchlist_with_names(user['name'])
            log_debug(f"관심 종목 수: {len(watchlist)}")
            
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
            
            log_debug(f"메시지 전송: {len(message)} bytes")
            await update.message.reply_text(message)
            log_success(f"/list 명령 완료 - {user['name']}")
            
        except Exception as e:
            log_error(f"/list 명령 실패: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(f"❌ 오류 발생: {str(e)}")
    
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
        log(f"📥 /morning 명령 수신 - Chat ID: {update.effective_chat.id}")
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
            analysis_results = analyze_and_generate_charts()
            
            if not analysis_results:
                await update.message.reply_text("⚠️ 분석 결과가 없습니다.")
                return
            
            # 사용자 관심 종목 가져오기
            watchlist = self.db.get_user_watchlist_with_names(user['name'])
            
            if not watchlist:
                await update.message.reply_text("⚠️ 관심 종목이 없습니다.")
                return
            
            today = datetime.now().strftime('%Y-%m-%d')
            sent_count = 0
            
            # 각 관심 종목별로 차트 전송
            for stock in watchlist:
                ticker = stock['ticker']
                name = stock['name']
                
                # 분석 결과 가져오기 (analysis_results는 딕셔너리)
                result = analysis_results.get(ticker)
                
                if not result:
                    log_warning(f"  ⚠️  {ticker} 분석 결과 없음")
                    continue
                
                # 차트 파일 경로
                chart_path = Path(result['chart_path'])
                
                if not chart_path.exists():
                    log_warning(f"  ⚠️  {ticker} 차트 파일 없음: {chart_path}")
                    continue
                
                # 통화 단위 결정
                is_korean = ticker.isdigit()
                invest_str = f"{int(user['investment_amount']):,}원"
                
                # 분석 데이터가 있으면 메시지 생성
                if result.get('data'):
                    data = result['data']
                    
                    if is_korean:
                        message = f"📊 {name} ({ticker})\n"
                        message += f"💰 투자금: {invest_str}\n\n"
                        message += f"🧪 테스트 매수: {data['target_05x']:,.0f}원 ({data['drop_05x']:.2f}% 하락)\n"
                        message += f"1차 매수 목표: {data['target_1x']:,.0f}원 ({data['drop_1x']:.2f}% 하락)\n"
                        message += f"2차 매수 목표: {data['target_2x']:,.0f}원 ({data['drop_2x']:.2f}% 하락)\n"
                    else:
                        message = f"📊 {ticker} - {name}\n"
                        message += f"💰 투자금: {invest_str}\n\n"
                        message += f"🧪 테스트 매수: ${data['target_05x']:,.2f} ({data['drop_05x']:.2f}% 하락)\n"
                        message += f"1차 매수 목표: ${data['target_1x']:,.2f} ({data['drop_1x']:.2f}% 하락)\n"
                        message += f"2차 매수 목표: ${data['target_2x']:,.2f} ({data['drop_2x']:.2f}% 하락)\n"
                else:
                    # data가 없으면 간단한 메시지
                    if is_korean:
                        message = f"📊 {name} ({ticker})\n"
                    else:
                        message = f"📊 {ticker} - {name}\n"
                    message += f"💰 투자금: {invest_str}\n"
                
                # 차트와 함께 전송
                try:
                    send_telegram_sync(self.bot_token, user['chat_id'], message, str(chart_path))
                    sent_count += 1
                    log_success(f"  ✅ {ticker} 차트 전송 완료")
                except Exception as e:
                    log_error(f"  ❌ {ticker} 전송 실패: {e}")
            
            if sent_count > 0:
                await update.message.reply_text(f"✅ 분석 완료! {sent_count}개 종목 차트를 전송했습니다.")
            else:
                await update.message.reply_text("⚠️ 전송할 차트가 없습니다.")
            
        except Exception as e:
            error_msg = f"❌ 분석 실패: {str(e)}"
            await update.message.reply_text(error_msg)
            log_error(f"분석 실패: {e}")
            traceback.print_exc()
    
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
    
    async def alarm_on_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /alarm_on - 알림 켜기
        """
        log(f"📥 /alarm_on 명령 수신 - Chat ID: {update.effective_chat.id}")
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
        
        # 알림 활성화
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET notification_enabled = 1 
            WHERE id = ?
        ''', (user['id'],))
        conn.commit()
        self.db.close()
        
        await update.message.reply_text(
            "🔔 알림이 활성화되었습니다!\n\n"
            "실시간 매수 타이밍 알림을 받습니다."
        )
        log_success(f"사용자 {user['name']} 알림 활성화")
    
    async def alarm_off_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /alarm_off - 알림 끄기
        """
        log(f"📥 /alarm_off 명령 수신 - Chat ID: {update.effective_chat.id}")
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
        
        # 알림 비활성화
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET notification_enabled = 0 
            WHERE id = ?
        ''', (user['id'],))
        conn.commit()
        self.db.close()
        
        await update.message.reply_text(
            "🔕 알림이 비활성화되었습니다.\n\n"
            "실시간 매수 타이밍 알림을 받지 않습니다.\n"
            "다시 켜려면 /alarm_on 을 입력하세요."
        )
        log_success(f"사용자 {user['name']} 알림 비활성화")
    
    async def alarm_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /alarm_status - 알림 상태 확인
        """
        log(f"📥 /alarm_status 명령 수신 - Chat ID: {update.effective_chat.id}")
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
        
        # 알림 상태 확인
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT notification_enabled 
            FROM users 
            WHERE id = ?
        ''', (user['id'],))
        result = cursor.fetchone()
        self.db.close()
        
        notification_enabled = result[0] if result else 1
        
        if notification_enabled:
            status_icon = "🔔"
            status_text = "활성화"
            action_text = "끄려면 /alarm_off 를 입력하세요."
        else:
            status_icon = "🔕"
            status_text = "비활성화"
            action_text = "켜려면 /alarm_on 을 입력하세요."
        
        message = f"{status_icon} 알림 상태: **{status_text}**\n\n"
        message += f"📊 관심 종목: {len(self.db.get_user_watchlist_with_names(user['name']))}개\n"
        message += f"💰 투자금액: {int(user['investment_amount']):,}원\n\n"
        message += action_text
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    def run(self):
        """봇 실행"""
        log_section("🤖 텔레그램 봇 커맨드 핸들러 시작")
        log_success(f"Bot Token: {self.bot_token[:20]}...{self.bot_token[-10:]}")
        
        # Application 생성
        log("🔧 Telegram Application 생성 중...")
        application = Application.builder().token(self.bot_token).build()
        log_success("Application 생성 완료!")
        
        # 커맨드 핸들러 등록
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("list", self.list_command))
        application.add_handler(CommandHandler("add", self.add_command))
        application.add_handler(CommandHandler("remove", self.remove_command))
        application.add_handler(CommandHandler("morning", self.morning_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(CommandHandler("alarm_on", self.alarm_on_command))
        application.add_handler(CommandHandler("alarm_off", self.alarm_off_command))
        application.add_handler(CommandHandler("alarm_status", self.alarm_status_command))
        
        log("")
        log_success("커맨드 핸들러 등록 완료:")
        log("   - /start: 봇 시작")
        log("   - /help: 도움말")
        log("   - /list: 종목 목록")
        log("   - /add: 종목 추가")
        log("   - /remove: 종목 삭제")
        log("   - /morning: 아침 알림")
        log("   - /status: 현재가 확인")
        log("   - /alarm_on: 알림 켜기")
        log("   - /alarm_off: 알림 끄기")
        log("   - /alarm_status: 알림 상태")
        
        log("")
        log("🚀 봇 시작... (Ctrl+C로 종료)")
        log("="*70)
        log("")
        
        # 봇 실행
        log("🔄 Polling 시작...")
        try:
            application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            log_error(f"봇 실행 오류: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    handler = TelegramBotCommandHandler()
    handler.run()

