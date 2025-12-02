#!/bin/bash
# NAS 디버그 스크립트 - 복사해서 NAS에서 실행하세요

echo "========================================"
echo "🔍 Stock Monitor 상태 진단"
echo "========================================"
echo ""

cd /volume1/docker/stock-volatility-alert

echo "1️⃣ 컨테이너 상태"
echo "----------------------------------------"
sudo docker-compose ps
echo ""

echo "2️⃣ Git 상태 (최신 코드인가?)"
echo "----------------------------------------"
git log --oneline | head -3
echo ""

echo "3️⃣ 실행 중인 프로세스"
echo "----------------------------------------"
sudo docker exec stock_monitor ps aux | grep -E "python|PID" || echo "❌ 컨테이너 실행 안됨"
echo ""

echo "4️⃣ start.sh 버전 확인"
echo "----------------------------------------"
sudo docker exec stock_monitor head -20 start.sh | grep -E "telegram_bot|PID|로그" || echo "❌ 오래된 start.sh"
echo ""

echo "5️⃣ 컨테이너 로그 (최근 50줄)"
echo "----------------------------------------"
sudo docker-compose logs --tail=50 stock-monitor
echo ""

echo "========================================"
echo "✅ 진단 완료"
echo "========================================"

