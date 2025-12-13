#!/bin/bash
# Mac Mini 자동 배포 스크립트
# launchd로 1분마다 실행하여 GitHub 변경사항 확인 후 자동 배포

PROJECT_PATH="$HOME/projects/stock-volatility-alert"
LOG_FILE="$PROJECT_PATH/deploy.log"
LOCK_FILE="/tmp/stock_deploy.lock"

# 로그 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 중복 실행 방지
if [ -f "$LOCK_FILE" ]; then
    # Lock 파일이 10분(600초) 이상 됐으면 삭제 (비정상 종료 대비)
    if [ $(($(date +%s) - $(stat -f %m "$LOCK_FILE" 2>/dev/null || echo 0))) -gt 600 ]; then
        rm -f "$LOCK_FILE"
    else
        exit 0  # 이미 실행 중
    fi
fi

# Lock 파일 생성
touch "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

cd "$PROJECT_PATH" || { log "❌ 프로젝트 경로 없음: $PROJECT_PATH"; exit 1; }

# 변경사항 확인
git fetch origin 2>/dev/null

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    log "🔄 업데이트 발견! 배포 시작..."
    
    # 변경된 파일 목록
    CHANGED_FILES=$(git diff --name-only HEAD origin/main)
    CHANGED_COUNT=$(echo "$CHANGED_FILES" | wc -l | tr -d ' ')
    
    # Git Pull
    log "📥 Git Pull..."
    git pull origin main
    
    # 커밋 정보
    COMMIT_MSG=$(git log -1 --pretty=format:"%s")
    COMMIT_AUTHOR=$(git log -1 --pretty=format:"%an")
    
    log "   📦 변경 파일: ${CHANGED_COUNT}개"
    log "   💬 커밋: ${COMMIT_MSG}"
    log "   👤 작성자: ${COMMIT_AUTHOR}"
    
    # ============================================
    # 빌드 방식 결정 (파일 유형별 분기)
    # ============================================
    
    # 1️⃣ Dockerfile 또는 requirements.txt 변경 → 전체 빌드 (--no-cache)
    if echo "$CHANGED_FILES" | grep -qE "^(Dockerfile|requirements\.txt)$"; then
        BUILD_TYPE="🔴 전체 빌드 (--no-cache)"
        log "🐳 $BUILD_TYPE"
        log "   → Dockerfile/requirements.txt 변경 감지"
        docker-compose build --no-cache
        docker-compose up -d
    
    # 2️⃣ 소스 코드 변경 (.py, .html, .css, .js 등) → 빠른 빌드 (--build)
    elif echo "$CHANGED_FILES" | grep -qE "\.(py|html|css|js|json|sh)$"; then
        BUILD_TYPE="🟡 빠른 빌드 (--build)"
        log "🐳 $BUILD_TYPE"
        log "   → 소스 파일 변경 감지"
        docker-compose up -d --build
    
    # 3️⃣ docker-compose.yml 변경 → 빌드 없이 재시작
    elif echo "$CHANGED_FILES" | grep -qE "^docker-compose\.yml$"; then
        BUILD_TYPE="🟢 재시작 (빌드 없음)"
        log "🐳 $BUILD_TYPE"
        log "   → docker-compose.yml 변경 감지"
        docker-compose up -d
    
    # 4️⃣ 기타 파일 (README, .md 등) → 재시작만
    else
        BUILD_TYPE="⚪ 재시작만 (변경 없음)"
        log "🐳 $BUILD_TYPE"
        log "   → 빌드 불필요한 파일만 변경됨"
        docker-compose up -d
    fi
    
    log "✅ 배포 완료! ($BUILD_TYPE)"
    log ""
fi
