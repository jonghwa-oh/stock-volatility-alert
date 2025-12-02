#!/bin/bash

# 로컬에서 봇 테스트 실행 스크립트

cd /Users/jjongz/PycharmProjects/finacneFee

echo "======================================"
echo "🤖 로컬 텔레그램 봇 테스트 시작"
echo "======================================"
echo ""

# 가상환경 확인
if [ ! -d "venv" ]; then
    echo "❌ 가상환경이 없습니다!"
    echo "   python3 -m venv venv 실행 필요"
    exit 1
fi

# 가상환경 활성화
echo "🔧 가상환경 활성화..."
source venv/bin/activate

# 패키지 확인
echo "📦 필수 패키지 확인..."
pip list | grep -E "python-telegram-bot|requests" > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ 패키지가 없습니다!"
    echo "   pip install -r requirements.txt 실행 필요"
    exit 1
fi

# DB 확인
echo "💾 데이터베이스 확인..."
if [ ! -f "data/stock_data.db" ]; then
    echo "❌ DB가 없습니다!"
    echo "   python data_collector.py init 실행 필요"
    exit 1
fi

# Bot Token 확인
echo "🔑 Bot Token 확인..."
BOT_TOKEN=$(sqlite3 data/stock_data.db "SELECT value FROM settings WHERE key='telegram_bot_token';" 2>/dev/null)
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ Bot Token이 없습니다!"
    echo "   python init_settings.py 실행 필요"
    exit 1
fi

echo ""
echo "✅ 모든 준비 완료!"
echo ""
echo "======================================"
echo "🚀 텔레그램 봇 커맨드 핸들러 시작"
echo "======================================"
echo ""
echo "📱 텔레그램에서 테스트하세요:"
echo "   /list - 종목 목록"
echo "   /morning - 아침 알림"
echo "   /status - 현재가 확인"
echo ""
echo "⚠️  종료하려면 Ctrl+C를 누르세요"
echo ""

# 봇 실행
python telegram_bot_commands.py


