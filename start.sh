#!/bin/bash
# Docker 컨테이너 시작 스크립트

# 로그 함수 (타임스탬프 포함)
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "=================================="
log "🚀 Stock Monitor 시작"
log "=================================="
log "🔧 DEBUG_MODE: ${DEBUG_MODE:-false}"
log "=================================="

# 1. DB 데이터 확인
log "📊 데이터 확인 중..."
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

log "   현재 데이터: ${DATA_COUNT}개"

# 2. 데이터가 없으면 수집
if [ "$DATA_COUNT" -lt 100 ]; then
    log ""
    log "📥 초기 데이터 수집 중..."
    log "   (최초 1회만, 5-10분 소요)"
    python -c "
from data_collector import DataCollector
dc = DataCollector()
dc.initialize_historical_data(years=1)
"
    log "✅ 데이터 수집 완료!"
else
    log "✅ 데이터 있음 (수집 건너뛰기)"
fi

# 3. 일일 업데이트 스케줄러 백그라운드 실행
log ""
log "=================================="
log "📅 일일 데이터 업데이트 스케줄러 시작"
log "=================================="
python daily_updater.py > /app/logs/daily_updater.log 2>&1 &
UPDATER_PID=$!
log "✅ 스케줄러 시작 완료!"
log "   PID: $UPDATER_PID"
log "   로그: /app/logs/daily_updater.log"
sleep 2

# 프로세스 확인 (kill -0은 ps 명령어가 없어도 작동)
if kill -0 $UPDATER_PID 2>/dev/null; then
    log "✅ 스케줄러 정상 실행 중"
else
    log "❌ 스케줄러 시작 실패!"
    cat /app/logs/daily_updater.log
    exit 1
fi

# 4. 텔레그램 봇 커맨드 핸들러 백그라운드 실행
log ""
log "=================================="
log "🤖 텔레그램 봇 커맨드 핸들러 시작"
log "=================================="
python telegram_bot_commands.py > /app/logs/telegram_bot.log 2>&1 &
BOT_PID=$!
log "✅ 봇 시작 완료!"
log "   PID: $BOT_PID"
log "   로그: /app/logs/telegram_bot.log"
sleep 3

# 프로세스 확인 (kill -0은 ps 명령어가 없어도 작동)
if kill -0 $BOT_PID 2>/dev/null; then
    log "✅ 텔레그램 봇 정상 실행 중"
    log ""
    log "📋 봇 초기화 로그:"
    tail -20 /app/logs/telegram_bot.log
else
    log "❌ 텔레그램 봇 시작 실패!"
    cat /app/logs/telegram_bot.log
    exit 1
fi

# 5. 실시간 모니터링 시작
log ""
log "=================================="
log "🎯 실시간 모니터링 시작"
log "=================================="
log ""

# 실시간 모니터링 시작 (포그라운드)
python realtime_monitor_hybrid.py

# 종료 시 백그라운드 프로세스도 종료
log ""
log "=================================="
log "⚠️  종료 중..."
log "=================================="
kill $UPDATER_PID 2>/dev/null && log "✅ 스케줄러 종료"
kill $BOT_PID 2>/dev/null && log "✅ 봇 종료"
log "👋 정상 종료되었습니다."

