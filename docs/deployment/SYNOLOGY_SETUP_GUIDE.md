# 📦 시놀로지 NAS 설치 가이드

**DS216+ 및 모든 시놀로지 NAS에서 주식 알림 시스템 실행하기**

---

## 🎯 시놀로지 NAS 장점

### 라즈베리파이 vs 시놀로지 NAS

| 항목 | 라즈베리파이5 | 시놀로지 DS216+ |
|------|--------------|----------------|
| CPU | 2.4GHz 쿼드코어 | 1.6GHz 듀얼코어 |
| RAM | 4/8GB | 1GB |
| 전력 | 3-5W | 15-20W |
| 가격 | ~$100 | **이미 보유!** ✅ |
| 안정성 | 좋음 | **매우 좋음** ✅ |
| 관리 | CLI | **Web UI** ✅ |
| 백업 | 수동 | **자동** ✅ |

**결론: 이미 NAS가 있다면 최고의 선택!** ✅

---

## 🚀 방법 1: Python3 직접 설치 (권장!)

### 1단계: Python3 설치

#### A. SSH 접속 활성화
1. DSM 로그인
2. **제어판** → **터미널 및 SNMP**
3. **SSH 서비스 활성화** 체크
4. 포트: 22 (기본값)
5. **적용**

#### B. SSH로 접속
```bash
# Mac/Linux
ssh admin@시놀로지IP주소

# Windows (PowerShell)
ssh admin@시놀로지IP주소

# 비밀번호 입력
```

#### C. Python3 설치
```bash
# 1. Community Package Center 추가 (최초 1회)
# DSM Web UI에서:
# 패키지 센터 → 설정 → 패키지 소스 → 추가

# 이름: SynoCommunity
# 위치: https://packages.synocommunity.com/

# 2. Python3 설치
# 패키지 센터에서 "Python3" 검색 → 설치

# 3. SSH에서 확인
python3 --version
# Python 3.8.x 또는 3.9.x
```

---

### 2단계: 프로젝트 설정

#### A. 작업 디렉토리 생성
```bash
# SSH 접속 후
cd /volume1  # 또는 /volume2 (설치된 볼륨)

# 프로젝트 디렉토리 생성
sudo mkdir -p /volume1/stock_monitor
sudo chown admin:users /volume1/stock_monitor
cd /volume1/stock_monitor
```

#### B. 파일 전송

**방법 1: SCP 사용 (Mac/Linux)**
```bash
# 로컬 컴퓨터에서 실행
cd /Users/jjongz/PycharmProjects/finacneFee

# 파일 전송
scp -r * admin@시놀로지IP:/volume1/stock_monitor/
```

**방법 2: DSM File Station 사용**
1. DSM 로그인
2. **File Station** 앱 실행
3. `/volume1` 폴더 이동
4. `stock_monitor` 폴더 생성
5. 파일 드래그 앤 드롭으로 업로드

**방법 3: SMB/CIFS 공유**
```bash
# Mac Finder에서
# 이동 → 서버에 연결
# smb://시놀로지IP
# stock_monitor 폴더로 파일 복사
```

---

### 3단계: Python 패키지 설치

#### A. pip 설치
```bash
cd /volume1/stock_monitor

# pip 설치 확인
python3 -m pip --version

# 없으면 설치
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py --user

# PATH 추가
export PATH="/volume1/homes/admin/.local/bin:$PATH"
```

#### B. 가상환경 생성
```bash
cd /volume1/stock_monitor

# 가상환경 생성
python3 -m venv venv

# 활성화
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

**참고:** 시놀로지 NAS는 ARM이 아닌 Intel CPU라서 대부분 패키지 문제없음 ✅

---

### 4단계: 초기 데이터 로드

```bash
cd /volume1/stock_monitor
source venv/bin/activate

# DB 초기화 (1년치 데이터)
python data_collector.py init

# 사용자 설정
python test_family_setup.py

# 또는
python user_manager.py family
```

---

### 5단계: 자동 실행 설정

#### A. 시작 스크립트 생성

```bash
cd /volume1/stock_monitor

# 시작 스크립트 생성
cat > start_monitor.sh << 'EOF'
#!/bin/bash

# 작업 디렉토리
cd /volume1/stock_monitor

# 가상환경 활성화
source venv/bin/activate

# 모니터링 시작
python realtime_monitor_multiuser.py >> monitor.log 2>&1
EOF

# 실행 권한
chmod +x start_monitor.sh
```

#### B. DSM 작업 스케줄러 설정

1. **DSM 제어판** → **작업 스케줄러**
2. **생성** → **예약된 작업** → **사용자 정의 스크립트**

**설정:**
```
작업 이름: Stock Monitor
사용자: admin
일정: 부팅 시
작업 설정:
  사용자 정의 스크립트:
  /volume1/stock_monitor/start_monitor.sh
```

3. **확인** → **실행** (테스트)

---

## 📊 방법 2: Docker 사용 (고급)

**참고:** DS216+는 Docker 공식 지원 안 되지만, 수동 설치 가능

### Docker 수동 설치 (선택사항)

```bash
# SSH 접속 후
sudo -i

# Docker 설치 (비공식)
wget https://github.com/SynoCommunity/spksrc/releases/download/docker-20.10.3-41/docker-x64-6.2_20.10.3-41.spk

# 패키지 센터에서 수동 설치
```

**권장:** DS216+는 Docker 대신 Python 직접 설치 사용 ⭐

---

## 🔧 시놀로지 최적화 설정

### 1. 메모리 관리

DS216+는 1GB RAM이므로 최적화 필요:

```python
# scheduler_config.py 수정
WATCH_LIST = {
    # 종목 수를 10개 이하로 제한 (권장)
    'TQQQ': 'ProShares UltraPro QQQ',
    'SOXL': 'Semiconductor 3X',
    'SPY': 'S&P 500',
    # ... 최대 10개
}
```

### 2. 로그 관리

```bash
# 로그 로테이션 설정
cd /volume1/stock_monitor

cat > rotate_logs.sh << 'EOF'
#!/bin/bash
cd /volume1/stock_monitor

# 7일 이전 로그 삭제
find . -name "*.log" -mtime +7 -delete

# 로그 파일 크기 제한 (10MB)
if [ -f monitor.log ]; then
  if [ $(stat -f%z monitor.log) -gt 10485760 ]; then
    mv monitor.log monitor.log.old
  fi
fi
EOF

chmod +x rotate_logs.sh
```

**작업 스케줄러:**
- 매일 자정 실행
- `rotate_logs.sh` 실행

### 3. 네트워크 설정

```bash
# config.py에서 timeout 설정 추가 (선택)
import socket
socket.setdefaulttimeout(10)
```

---

## 📱 DB 백업 (시놀로지 강점!)

### 자동 백업 설정

#### A. 스크립트 생성
```bash
cd /volume1/stock_monitor

cat > backup_db.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/volume1/backup/stock_monitor"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# DB 백업
cp /volume1/stock_monitor/stock_data.db \
   $BACKUP_DIR/stock_data_$DATE.db

# 30일 이전 백업 삭제
find $BACKUP_DIR -name "stock_data_*.db" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x backup_db.sh
```

#### B. 작업 스케줄러 등록
- 매일 자정 실행
- `/volume1/stock_monitor/backup_db.sh`

#### C. Hyper Backup 사용 (더 좋음!)
1. **Hyper Backup** 앱 설치
2. `/volume1/stock_monitor` 폴더 백업
3. 클라우드 또는 외장 HDD로 자동 백업

---

## 🔍 모니터링 & 관리

### 1. 로그 확인

```bash
# SSH 접속
cd /volume1/stock_monitor

# 실시간 로그
tail -f monitor.log

# 최근 100줄
tail -100 monitor.log

# 에러만 확인
grep ERROR monitor.log
```

### 2. 프로세스 확인

```bash
# 실행 중인지 확인
ps aux | grep realtime_monitor

# 종료
pkill -f realtime_monitor

# 재시작
/volume1/stock_monitor/start_monitor.sh
```

### 3. Web UI로 확인

**DSM 리소스 모니터:**
- 제어판 → 리소스 모니터
- CPU, 메모리 사용량 확인

---

## 💡 성능 최적화

### DS216+ 메모리 1GB 최적화

#### 1. 종목 수 제한
```python
# 최대 10-15개 종목 권장
# 가족 3명 × 5개 = 15개 OK
```

#### 2. 분봉 데이터 정리
```python
# 30일마다 자동 정리
from database import StockDatabase

db = StockDatabase()
db.cleanup_old_minute_data(days=30)
db.close()
```

#### 3. 스왑 메모리 확인
```bash
# 스왑 상태 확인
free -h

# 스왑 사용 중이면 OK
```

---

## 🔥 빠른 시작 스크립트

### 올인원 설치 스크립트

```bash
#!/bin/bash

echo "시놀로지 NAS 주식 알림 시스템 설치"
echo "=================================="

# 1. 디렉토리 생성
sudo mkdir -p /volume1/stock_monitor
sudo chown admin:users /volume1/stock_monitor
cd /volume1/stock_monitor

# 2. 파일 전송 확인
if [ ! -f "requirements.txt" ]; then
  echo "❌ 파일이 없습니다. 먼저 파일을 전송하세요."
  exit 1
fi

# 3. 가상환경 생성
echo "가상환경 생성 중..."
python3 -m venv venv
source venv/bin/activate

# 4. 패키지 설치
echo "패키지 설치 중..."
pip install -r requirements.txt

# 5. DB 초기화
echo "DB 초기화 중..."
python data_collector.py init

# 6. 시작 스크립트 생성
cat > start_monitor.sh << 'EOF'
#!/bin/bash
cd /volume1/stock_monitor
source venv/bin/activate
python realtime_monitor_multiuser.py >> monitor.log 2>&1
EOF

chmod +x start_monitor.sh

echo ""
echo "✅ 설치 완료!"
echo ""
echo "다음 단계:"
echo "1. python user_manager.py family  # 사용자 설정"
echo "2. ./start_monitor.sh             # 모니터링 시작"
echo "3. DSM 작업 스케줄러에 등록       # 자동 시작"
```

---

## 📊 성능 예측 (DS216+)

### 실제 예상 성능

| 작업 | 시간 | 메모리 | CPU | 판정 |
|------|------|--------|-----|------|
| 일일 업데이트 (10개) | 3-5초 | 400MB | 20% | ✅ |
| 5분 체크 (10개) | 2-3초 | 400MB | 10% | ✅ |
| 가족 3명 알림 | < 1초 | 400MB | 5% | ✅ |

**결론: DS216+로 완벽하게 작동! ✅**

### 권장 설정
```
사용자: 3-5명 ✅
종목: 10-15개 ✅
체크 간격: 5분 ✅
```

---

## ⚠️ 주의사항

### 1. 메모리 부족 시
```bash
# 다른 패키지 중지
# DSM 패키지 센터에서 불필요한 앱 중지
```

### 2. 시놀로지 재부팅 시
- 작업 스케줄러 "부팅 시 실행" 설정 확인
- 자동으로 재시작됨 ✅

### 3. DSM 업데이트 시
- Python3 패키지 재설치 필요할 수 있음
- 가상환경은 유지됨 ✅

---

## 🎯 체크리스트

### 설치 전
- [ ] SSH 활성화
- [ ] Python3 설치 (SynoCommunity)
- [ ] 파일 전송 준비

### 설치
- [ ] `/volume1/stock_monitor` 생성
- [ ] 파일 전송
- [ ] 가상환경 생성
- [ ] 패키지 설치
- [ ] DB 초기화

### 설정
- [ ] 사용자 등록 (`user_manager.py`)
- [ ] 테스트 실행
- [ ] 작업 스케줄러 등록
- [ ] 백업 설정

---

## 🆚 비교표

### 시놀로지 vs 라즈베리파이

| 항목 | 시놀로지 DS216+ | 라즈베리파이5 |
|------|----------------|--------------|
| 성능 | ✅ 충분 (듀얼코어) | ✅✅ 여유 (쿼드코어) |
| 메모리 | ⚠️ 1GB (제한적) | ✅ 4/8GB |
| 안정성 | ✅✅ 매우 좋음 | ✅ 좋음 |
| 백업 | ✅✅ 자동 (Hyper Backup) | ⚠️ 수동 |
| 관리 | ✅✅ Web UI | ⚠️ CLI |
| 가격 | ✅✅ 이미 보유 | ⚠️ $100 |
| 전력 | ⚠️ 15-20W | ✅ 3-5W |
| 확장성 | ⚠️ 10-15개 종목 | ✅ 100개 종목 |

**결론:** 
- 이미 NAS 보유 → **시놀로지 사용** ✅
- 새로 구매 → 라즈베리파이5 고려

---

## 📞 문제 해결

### Q1. Python3가 안 보여요
**A:** SynoCommunity 패키지 소스 추가 필요
```
https://packages.synocommunity.com/
```

### Q2. pip 설치 실패
**A:** 인터넷 연결 및 방화벽 확인
```bash
curl -I https://pypi.org
```

### Q3. 메모리 부족
**A:** 종목 수 줄이기
```python
# 10개 이하로 제한
WATCH_LIST = { ... }  # 10개
```

### Q4. 재부팅 후 작동 안 함
**A:** 작업 스케줄러 "부팅 시" 설정 확인

---

## 🎉 완료!

### 시놀로지 NAS 장점

✅ **이미 보유** - 추가 비용 없음  
✅ **안정적** - 24시간 운영  
✅ **백업 자동화** - Hyper Backup  
✅ **관리 편함** - Web UI  
✅ **충분한 성능** - 10-15개 종목 OK  

---

**시놀로지 NAS로 스마트한 투자를 시작하세요!** 📦📊🚀

