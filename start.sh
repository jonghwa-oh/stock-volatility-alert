#!/bin/bash
# Docker 컨테이너 시작 스크립트

echo "=================================="
echo "🚀 Stock Monitor 시작"
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

# 3. 실시간 모니터링 시작
echo ""
echo "=================================="
echo "🎯 실시간 모니터링 시작"
echo "=================================="
python realtime_monitor_hybrid.py

