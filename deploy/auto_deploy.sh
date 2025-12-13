#!/bin/bash
# deploy/auto_deploy.sh - Git으로 관리되는 자동 배포 스크립트
# NAS 작업 스케줄러에서 1분마다 실행

PROJECT_PATH="/volume1/homes/jjongz/docker/financeFree/stock-volatility-alert"
LOG_FILE="/volume1/homes/jjongz/docker/financeFree/deploy.log"
LOCK_FILE="/volume1/homes/jjongz/docker/financeFree/deploy.lock"

# 중복 실행 방지
if [ -f "$LOCK_FILE" ]; then
    # Lock 파일이 10분(600초) 이상 됐으면 삭제 (비정상 종료 대비)
    if [ $(($(date +%s) - $(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo 0))) -gt 600 ]; then
        rm -f "$LOCK_FILE"
    else
        exit 0  # 이미 실행 중 - 조용히 종료
    fi
fi

# Lock 파일 생성
touch "$LOCK_FILE"

# 종료 시 Lock 파일 삭제 (정상/비정상 모두)
trap "rm -f $LOCK_FILE" EXIT

cd "$PROJECT_PATH" || { rm -f "$LOCK_FILE"; exit 1; }

# config.py에서 텔레그램 설정 추출
BOT_TOKEN=$(grep -oP "BOT_TOKEN.*?['\"]([^'\"]+)['\"]" config.py | grep -oP "['\"][^'\"]+['\"]$" | tr -d "\"'")
CHAT_ID=$(grep -oP "CHAT_ID.*?['\"]([^'\"]+)['\"]" config.py | grep -oP "['\"][^'\"]+['\"]$" | tr -d "\"'")

# 로그 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 텔레그램 메시지 전송
send_telegram() {
    local message="$1"
    if [ -n "$BOT_TOKEN" ] && [ -n "$CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
            -d "chat_id=${CHAT_ID}" \
            -d "text=${message}" \
            -d "parse_mode=HTML" > /dev/null 2>&1
    fi
}

# 변경사항 확인
git fetch origin

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    log "🔄 업데이트 발견! 배포 시작..."
    
    # 변경된 파일 목록
    CHANGED_FILES=$(git diff --name-only HEAD origin/main)
    CHANGED_COUNT=$(echo "$CHANGED_FILES" | wc -l)
    
    # Git Pull
    log "📥 Git Pull..."
    git pull origin main
    
    # 빌드 방식 결정
    if echo "$CHANGED_FILES" | grep -qE "(Dockerfile|requirements.txt)"; then
        BUILD_TYPE="전체 빌드 (Dockerfile/requirements 변경)"
        log "🐳 $BUILD_TYPE"
        docker-compose down
        docker-compose build --no-cache
    else
        BUILD_TYPE="빠른 빌드"
        log "🐳 $BUILD_TYPE"
        docker-compose down
        docker-compose build
    fi
    
    docker-compose up -d
    
    # 기존 차트 삭제
    rm -rf charts/*
    
    log "✅ 배포 완료!"
    
    # 텔레그램 알림 전송
    COMMIT_MSG=$(git log -1 --pretty=format:"%s")
    COMMIT_AUTHOR=$(git log -1 --pretty=format:"%an")
    
    send_telegram "🚀 <b>배포 완료!</b>

📦 변경된 파일: ${CHANGED_COUNT}개
🔧 빌드: ${BUILD_TYPE}
💬 커밋: ${COMMIT_MSG}
👤 작성자: ${COMMIT_AUTHOR}
⏰ 시간: $(date '+%Y-%m-%d %H:%M:%S')"

fi

# Lock 파일은 trap에 의해 자동 삭제됨






