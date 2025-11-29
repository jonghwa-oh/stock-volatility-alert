# ⚡ 시놀로지 NAS 빠른 시작

**DS216+에서 5분 안에 설치하기**

---

## 🎯 시놀로지 DS216+ 사양

- **CPU**: Intel Celeron N3050 (듀얼코어 1.6GHz)
- **RAM**: 1GB
- **판정**: ✅ **충분히 작동!**

**예상 성능:**
- 가족 3명
- 10-15개 종목
- 일일 분석: 3-5초
- 5분 체크: 2-3초

---

## 🚀 5단계 설치

### 1단계: SSH 활성화 (2분)

1. DSM 로그인 (브라우저에서 시놀로지IP 접속)
2. **제어판** → **터미널 및 SNMP**
3. ☑️ **SSH 서비스 활성화**
4. **적용**

---

### 2단계: Python3 설치 (3분)

#### A. 패키지 소스 추가
1. **패키지 센터** 열기
2. **설정** (우측 상단 ⚙️)
3. **패키지 소스** 탭
4. **추가** 버튼

```
이름: SynoCommunity
위치: https://packages.synocommunity.com/
```

5. **확인**

#### B. Python3 설치
1. 패키지 센터에서 **"Python3"** 검색
2. **설치** 클릭
3. 완료 대기 (1-2분)

---

### 3단계: 파일 전송 (5분)

#### 방법 A: File Station (가장 쉬움!)

1. DSM에서 **File Station** 앱 실행
2. 좌측에서 **volume1** 클릭
3. **새 폴더** → 이름: `stock_monitor`
4. `stock_monitor` 폴더 열기
5. 로컬 컴퓨터에서 프로젝트 파일 **드래그 앤 드롭**

**전송할 파일:**
```
모든 .py 파일
requirements.txt
config.py
scheduler_config.py
stock_data.db (이미 생성했으면)
```

#### 방법 B: SCP (Mac/Linux)

```bash
# 로컬 컴퓨터에서 실행
cd /Users/jjongz/PycharmProjects/finacneFee
scp -r * admin@시놀로지IP:/volume1/stock_monitor/
```

---

### 4단계: 설치 실행 (5분)

#### SSH 접속

```bash
# Mac/Linux 터미널에서
ssh admin@시놀로지IP주소

# 비밀번호 입력 (DSM 비밀번호)
```

#### 자동 설치 실행

```bash
cd /volume1/stock_monitor

# 실행 권한 부여
chmod +x synology_install.sh

# 설치 시작!
bash synology_install.sh
```

**출력:**
```
============================================================
📦 시놀로지 NAS 주식 알림 시스템 설치
============================================================

✅ Python3 확인: Python 3.8.x
1️⃣ 가상환경 생성 중...
   ✅ 가상환경 생성 완료
2️⃣ pip 업그레이드 중...
   ✅ pip 업그레이드 완료
3️⃣ 패키지 설치 중...
   (2-3분 소요)
   ✅ 패키지 설치 완료
4️⃣ 데이터베이스 초기화...
   (30초~1분 소요)
   ✅ DB 초기화 완료

✅ 설치 완료!
```

---

### 5단계: 가족 설정 & 시작 (3분)

#### A. 사용자 설정

```bash
cd /volume1/stock_monitor
source venv/bin/activate

# 가족 설정
python user_manager.py family
```

**입력 예시:**
```
1️⃣ 첫 번째 사용자 (본인)
  텔레그램 Chat ID: 6633793503
  종목 (엔터=추천): [엔터]
  ✅ 3개 종목 추가

2️⃣ 두 번째 사용자 (배우자)
  텔레그램 Chat ID: 123456789
  종목 (엔터=추천): [엔터]
  ✅ 3개 종목 추가

3️⃣ 세 번째 사용자 (자녀)
  텔레그램 Chat ID: 987654321
  종목 (엔터=추천): [엔터]
  ✅ 3개 종목 추가
```

#### B. 테스트 실행

```bash
# 백그라운드 실행
nohup ./start_monitor.sh &

# 로그 확인
tail -f monitor.log
```

**출력:**
```
👨‍👩‍👦 가족용 멀티 유저 모니터링 시스템
══════════════════════════════════════

👥 등록된 사용자: 3명
   • 아빠: 3개 종목
   • 엄마: 3개 종목
   • 아들: 3개 종목

✅ 모니터링 시작!
```

#### C. 텔레그램 확인

각자 텔레그램으로 알림이 와야 합니다! 📱

---

## 🔄 자동 시작 설정 (DSM)

### 작업 스케줄러 등록

1. DSM **제어판** → **작업 스케줄러**
2. **생성** → **예약된 작업** → **사용자 정의 스크립트**

**설정:**
```
작업 이름: Stock Monitor
사용자: admin
일정: 부팅 시

작업 설정 탭:
  사용자 정의 스크립트:
  /volume1/stock_monitor/start_monitor.sh
```

3. **확인**

### 백업 스케줄 (선택)

**작업 1: DB 백업 (매일 자정)**
```
작업 이름: Stock DB Backup
사용자: admin
일정: 매일 00:00

스크립트:
  /volume1/stock_monitor/backup_db.sh
```

**작업 2: 로그 정리 (매일 자정)**
```
작업 이름: Log Rotation
사용자: admin
일정: 매일 00:00

스크립트:
  /volume1/stock_monitor/rotate_logs.sh
```

---

## 🔧 관리 명령어

### SSH 접속 후

```bash
cd /volume1/stock_monitor
source venv/bin/activate

# 사용자 목록
python user_manager.py list

# 종목 추가/제거
python user_manager.py setup

# DB 현황
python data_collector.py status

# 수동 업데이트
python data_collector.py update

# 로그 확인
tail -f monitor.log

# 프로세스 확인
ps aux | grep realtime_monitor

# 종료
pkill -f realtime_monitor

# 재시작
./start_monitor.sh
```

---

## 📊 DSM에서 모니터링

### 리소스 모니터

1. **제어판** → **리소스 모니터**
2. **성능** 탭 확인

**정상 범위:**
- CPU: 5-20%
- 메모리: 400-500MB
- 네트워크: 낮음

---

## 💾 Hyper Backup 설정 (권장!)

### 자동 백업 설정

1. **Hyper Backup** 앱 설치
2. **데이터 백업 작업 생성**
3. 백업 대상: `/volume1/stock_monitor`
4. 백업 목적지: 
   - 외장 HDD
   - 또는 클라우드 (Google Drive, Dropbox 등)
5. 스케줄: 매일 자동

---

## ⚠️ 문제 해결

### Q1. "Python3을 찾을 수 없습니다"
**A:** SynoCommunity 패키지 소스 추가 후 Python3 설치

### Q2. "pip 설치 실패"
**A:** 인터넷 연결 확인
```bash
ping 8.8.8.8
```

### Q3. "메모리 부족"
**A:** 종목 수 줄이기
```python
# scheduler_config.py
WATCH_LIST = {
    # 10개 이하로 제한
}
```

### Q4. "재부팅 후 작동 안 함"
**A:** 작업 스케줄러 "부팅 시" 설정 확인

### Q5. "텔레그램 알림 안 옴"
**A:** 
```bash
# config.py 확인
python telegram_alert.py test
```

---

## 📱 원격 관리 (모바일)

### DS file 앱 (iOS/Android)

1. **DS file** 앱 설치
2. NAS 연결
3. `/stock_monitor` 폴더
4. `monitor.log` 파일로 상태 확인

### SSH 앱

**iOS:**
- Termius
- Prompt

**Android:**
- JuiceSSH
- Termux

---

## 🎯 성능 최적화 (1GB RAM)

### 권장 설정

```python
# scheduler_config.py

# 가족 3명
# 각 5개씩 = 총 10-15개 종목 (중복 제거)

WATCH_LIST = {
    # 10개 정도가 최적
    'TQQQ': 'ProShares UltraPro QQQ',
    'SOXL': 'Semiconductor 3X',
    'QLD': 'ProShares Ultra QQQ',
    'SPY': 'S&P 500',
    'QQQ': 'Nasdaq 100',
    'VOO': 'Vanguard S&P 500',
    'XLK': 'Technology',
    'TECL': 'Tech 3X',
    'KS200': '코스피200',
    'IWM': 'Russell 2000',
}
```

### 메모리 사용량 줄이기

```python
# data_collector.py에서

# 30일마다 분봉 데이터 정리
def cleanup_old_data():
    db = StockDatabase()
    db.cleanup_old_minute_data(days=30)
    db.close()
```

---

## 📊 예상 비용

### 전력 소비

```
DS216+: 15-20W
24시간 운영: 월 0.36 ~ 0.48 kWh
월 전기료: 약 50-70원

vs 라즈베리파이: 월 15-20원
차이: 월 30-50원 (미미함)
```

### 총 비용

```
라즈베리파이5 신규 구매: $100 + 액세서리
시놀로지 DS216+: 이미 보유 ✅

→ 시놀로지가 더 경제적!
```

---

## 🎉 완료!

### 시놀로지 NAS 장점

✅ **이미 보유** - 추가 비용 $0  
✅ **안정적** - 24시간 운영  
✅ **백업 자동** - Hyper Backup  
✅ **Web 관리** - 편리함  
✅ **충분한 성능** - 10-15개 종목 OK  
✅ **원격 관리** - 모바일 앱  

---

## 📚 추가 문서

- **SYNOLOGY_SETUP_GUIDE.md** - 상세 설치 가이드
- **FAMILY_SETUP_GUIDE.md** - 가족 설정 가이드
- **README_FINAL.md** - 전체 시스템 설명

---

**시놀로지 NAS로 스마트한 투자를 시작하세요!** 📦📊🚀

