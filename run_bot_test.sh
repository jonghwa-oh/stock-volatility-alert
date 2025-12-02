#!/bin/bash
cd /Users/jjongz/PycharmProjects/finacneFee

echo "=================================="
echo "🤖 텔레그램 봇 시작"
echo "=================================="
echo ""
echo "📱 이제 텔레그램에서 다음을 테스트하세요:"
echo "   /morning"
echo ""
echo "⏸️  봇을 종료하려면 Ctrl+C를 누르세요"
echo "=================================="
echo ""

source venv/bin/activate
python telegram_bot_commands.py

