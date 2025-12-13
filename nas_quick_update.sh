#!/bin/bash
# NAS 빠른 업데이트 스크립트 (캐시 사용)
# 일반 코드 변경 시 사용 (Dockerfile, requirements.txt 변경 없을 때)

# 로그 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "======================================================================="
log "⚡ Stock Monitor 빠른 업데이트 (캐시 사용)"
log "======================================================================="

# 1. Git Pull
log "📥 최신 코드 받기..."
git pull || { log "❌ git pull 실패!"; exit 1; }
log "✅ 최근 커밋: $(git log --oneline -1)"
log ""

# 2. 변경된 파일 확인
CHANGED_FILES=$(git diff --name-only HEAD~1 2>/dev/null || echo "")
log "📝 변경된 파일:"
echo "$CHANGED_FILES" | head -10
log ""

# 3. Dockerfile 또는 requirements.txt 변경 확인
if echo "$CHANGED_FILES" | grep -qE "(Dockerfile|requirements.txt)"; then
    log "⚠️  Dockerfile 또는 requirements.txt 변경 감지!"
    log "   전체 빌드가 필요합니다. nas_update.sh를 사용하세요."
    read -p "   그래도 캐시 빌드를 진행할까요? (y/N): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        log "취소됨"
        exit 0
    fi
fi

# 4. 컨테이너 중지
log "🛑 컨테이너 중지..."
sudo docker-compose down || { log "❌ 실패!"; exit 1; }

# 5. 빠른 빌드 (캐시 사용)
log "🔨 이미지 빌드 (캐시 사용)..."
sudo docker-compose build || { log "❌ 빌드 실패!"; exit 1; }
log "✅ 빌드 완료!"
log ""

# 6. 컨테이너 시작
log "🚀 컨테이너 시작..."
sudo docker-compose up -d || { log "❌ 시작 실패!"; exit 1; }

# 7. 상태 확인
sleep 3
log ""
log "📊 컨테이너 상태:"
sudo docker-compose ps
log ""

# 8. 웹 서버 로그 확인
log "📋 stock-web 로그 (최근 15줄):"
sudo docker logs stock_web --tail 15 2>&1
log ""

log "======================================================================="
log "✅ 빠른 업데이트 완료!"
log "======================================================================="
log ""
log "📌 접속: http://$(tailscale ip -4 2>/dev/null || echo 'NAS-IP'):8080"
log "📌 로그: sudo docker logs stock_web -f"
log ""





