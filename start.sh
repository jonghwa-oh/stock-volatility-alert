#!/bin/bash
# Docker 컨테이너 시작 스크립트

echo "=================================="
echo "🚀 Stock Monitor 시작"
echo "=================================="
echo "📅 시작 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo "🔧 DEBUG_MODE: ${DEBUG_MODE:-false}"
echo "=================================="

# 1. DB 데이터 확인
echo "📊 데이터 확인 중..."
DATA_COUNT=$(python -c "
from database import StockDatabase
db = StockDatabase()
conn = db.connect()
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM daily_prices')
count = cursor.fetchone()[0]
db.close()
print(count)
")

echo "   현재 데이터: ${DATA_COUNT}개"

# 2. 데이터가 없으면 수집
if [ "$DATA_COUNT" -lt 100 ]; then
    echo ""
    echo "📥 초기 데이터 수집 중..."
    echo "   (최초 1회만, 5-10분 소요)"
    python -c "
from data_collector import DataCollector
dc = DataCollector()
dc.initialize_historical_data(years=1)
"
    echo "✅ 데이터 수집 완료!"
else
    echo "✅ 데이터 있음 (수집 건너뛰기)"
fi

# 3. 일일 업데이트 스케줄러 백그라운드 실행
echo ""
echo "=================================="
echo "📅 일일 데이터 업데이트 스케줄러 시작"
echo "=================================="
python daily_updater.py > /tmp/daily_updater.log 2>&1 &
UPDATER_PID=$!
echo "✅ 스케줄러 시작 완료!"
echo "   PID: $UPDATER_PID"
echo "   로그: /tmp/daily_updater.log"
sleep 2

# 프로세스 확인
if ps -p $UPDATER_PID > /dev/null; then
    echo "✅ 스케줄러 정상 실행 중"
else
    echo "❌ 스케줄러 시작 실패!"
    cat /tmp/daily_updater.log
    exit 1
fi

# 4. 텔레그램 봇 커맨드 핸들러 백그라운드 실행
echo ""
echo "=================================="
echo "🤖 텔레그램 봇 커맨드 핸들러 시작"
echo "=================================="
python telegram_bot_commands.py > /tmp/telegram_bot.log 2>&1 &
BOT_PID=$!
echo "✅ 봇 시작 완료!"
echo "   PID: $BOT_PID"
echo "   로그: /tmp/telegram_bot.log"
sleep 3

# 프로세스 확인
if ps -p $BOT_PID > /dev/null; then
    echo "✅ 텔레그램 봇 정상 실행 중"
    echo ""
    echo "📋 봇 초기화 로그:"
    tail -20 /tmp/telegram_bot.log
else
    echo "❌ 텔레그램 봇 시작 실패!"
    cat /tmp/telegram_bot.log
    exit 1
fi

# 5. 실시간 모니터링 시작
echo ""
echo "=================================="
echo "🎯 실시간 모니터링 시작"
echo "=================================="
echo "⏰ 현재 시간: $(date '+%H:%M:%S')"
echo ""

# 실시간 모니터링 시작 (포그라운드)
python realtime_monitor_hybrid.py

# 종료 시 백그라운드 프로세스도 종료
echo ""
echo "=================================="
echo "⚠️  종료 중..."
echo "=================================="
kill $UPDATER_PID 2>/dev/null && echo "✅ 스케줄러 종료"
kill $BOT_PID 2>/dev/null && echo "✅ 봇 종료"
echo "👋 정상 종료되었습니다."

