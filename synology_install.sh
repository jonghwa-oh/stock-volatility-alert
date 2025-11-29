#!/bin/bash

# 시놀로지 NAS 자동 설치 스크립트
# 사용법: bash synology_install.sh

echo ""
echo "============================================================"
echo "📦 시놀로지 NAS 주식 알림 시스템 설치"
echo "============================================================"
echo ""

# 현재 위치 확인
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt를 찾을 수 없습니다."
    echo "   이 스크립트는 프로젝트 디렉토리에서 실행해야 합니다."
    exit 1
fi

# Python3 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3이 설치되지 않았습니다!"
    echo ""
    echo "설치 방법:"
    echo "1. DSM 패키지 센터 열기"
    echo "2. 설정 → 패키지 소스 → 추가"
    echo "   이름: SynoCommunity"
    echo "   위치: https://packages.synocommunity.com/"
    echo "3. Python3 검색 → 설치"
    echo ""
    exit 1
fi

echo "✅ Python3 확인: $(python3 --version)"
echo ""

# 1. 가상환경 생성
echo "1️⃣ 가상환경 생성 중..."
if [ -d "venv" ]; then
    echo "   ⚠️  기존 가상환경 발견. 삭제 후 재생성..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate
echo "   ✅ 가상환경 생성 완료"
echo ""

# 2. pip 업그레이드
echo "2️⃣ pip 업그레이드 중..."
pip install --upgrade pip > /dev/null 2>&1
echo "   ✅ pip 업그레이드 완료"
echo ""

# 3. 패키지 설치
echo "3️⃣ 패키지 설치 중..."
echo "   (이 작업은 2-3분 소요됩니다)"
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "   ❌ 패키지 설치 실패"
    echo "   인터넷 연결을 확인하세요."
    exit 1
fi

echo "   ✅ 패키지 설치 완료"
echo ""

# 4. DB 초기화
echo "4️⃣ 데이터베이스 초기화..."
echo "   (1년치 데이터 로딩, 30초~1분 소요)"

python data_collector.py init

if [ $? -ne 0 ]; then
    echo "   ❌ DB 초기화 실패"
    exit 1
fi

echo "   ✅ DB 초기화 완료"
echo ""

# 5. 시작 스크립트 생성
echo "5️⃣ 시작 스크립트 생성 중..."

SCRIPT_DIR=$(pwd)

cat > start_monitor.sh << EOF
#!/bin/bash

# 작업 디렉토리
cd $SCRIPT_DIR

# 가상환경 활성화
source venv/bin/activate

# 모니터링 시작
python realtime_monitor_multiuser.py >> monitor.log 2>&1
EOF

chmod +x start_monitor.sh
echo "   ✅ 시작 스크립트 생성: start_monitor.sh"
echo ""

# 6. 백업 스크립트 생성
echo "6️⃣ 백업 스크립트 생성 중..."

mkdir -p backup

cat > backup_db.sh << EOF
#!/bin/bash

BACKUP_DIR="$SCRIPT_DIR/backup"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p \$BACKUP_DIR

# DB 백업
cp $SCRIPT_DIR/stock_data.db \\
   \$BACKUP_DIR/stock_data_\$DATE.db

# 30일 이전 백업 삭제
find \$BACKUP_DIR -name "stock_data_*.db" -mtime +30 -delete

echo "Backup completed: \$DATE"
EOF

chmod +x backup_db.sh
echo "   ✅ 백업 스크립트 생성: backup_db.sh"
echo ""

# 7. 로그 정리 스크립트 생성
echo "7️⃣ 로그 관리 스크립트 생성 중..."

cat > rotate_logs.sh << EOF
#!/bin/bash

cd $SCRIPT_DIR

# 7일 이전 로그 삭제
find . -name "*.log" -mtime +7 -delete

# 로그 파일 크기 제한 (10MB)
if [ -f monitor.log ]; then
  SIZE=\$(stat -f%z monitor.log 2>/dev/null || stat -c%s monitor.log 2>/dev/null)
  if [ \$SIZE -gt 10485760 ]; then
    mv monitor.log monitor.log.old
    echo "Log rotated: \$(date)"
  fi
fi
EOF

chmod +x rotate_logs.sh
echo "   ✅ 로그 관리 스크립트 생성: rotate_logs.sh"
echo ""

# 8. 정리
deactivate

# 완료 메시지
echo "============================================================"
echo "✅ 설치 완료!"
echo "============================================================"
echo ""
echo "📊 설치 내용:"
echo "   • Python 가상환경: venv/"
echo "   • 데이터베이스: stock_data.db ($(du -h stock_data.db 2>/dev/null | cut -f1))"
echo "   • 시작 스크립트: start_monitor.sh"
echo "   • 백업 스크립트: backup_db.sh"
echo "   • 로그 관리: rotate_logs.sh"
echo ""
echo "📱 다음 단계:"
echo ""
echo "1️⃣ 가족 설정"
echo "   source venv/bin/activate"
echo "   python user_manager.py family"
echo ""
echo "2️⃣ 테스트 실행"
echo "   ./start_monitor.sh"
echo ""
echo "3️⃣ DSM 작업 스케줄러 등록"
echo "   - 제어판 → 작업 스케줄러"
echo "   - 생성 → 사용자 정의 스크립트"
echo "   - 부팅 시 실행: $SCRIPT_DIR/start_monitor.sh"
echo ""
echo "4️⃣ 백업 스케줄 등록 (선택)"
echo "   - 매일 자정 실행: $SCRIPT_DIR/backup_db.sh"
echo "   - 매일 자정 실행: $SCRIPT_DIR/rotate_logs.sh"
echo ""
echo "============================================================"
echo "📚 가이드: SYNOLOGY_SETUP_GUIDE.md"
echo "============================================================"
echo ""

