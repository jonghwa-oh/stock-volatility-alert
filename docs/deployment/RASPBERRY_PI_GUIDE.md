# 🍓 라즈베리파이5 설정 가이드

24시간 실시간 주식 모니터링 시스템 구축

---

## 🖥️ 하드웨어 요구사항

### 권장 스펙
- **라즈베리파이5** 4GB 이상 (8GB 권장)
- **microSD 카드** 32GB 이상 (Class 10)
- **전원 어댑터** 5V/3A USB-C
- **인터넷 연결** (유선 또는 WiFi)

### ✅ 성능 분석
```
작업                  부하         라즈베리파이5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
20개 종목 데이터 로드   낮음         ✅ 문제없음
표준편차 계산          매우 낮음      ✅ 즉각
차트 생성 20개         중간         ✅ 2-3분
5분마다 가격 체크      매우 낮음      ✅ 즉각
텔레그램 전송          낮음         ✅ 문제없음
```

**결론:** 라즈베리파이5로 충분히 가능합니다! 💪

---

## 📋 1단계: 라즈베리파이 OS 설치

### A. OS 다운로드 및 설치
1. [Raspberry Pi Imager](https://www.raspberrypi.com/software/) 다운로드
2. microSD 카드를 PC에 삽입
3. Raspberry Pi Imager 실행
4. **Raspberry Pi OS (64-bit)** 선택
5. **고급 설정**에서:
   - ✅ SSH 활성화
   - ✅ WiFi 설정
   - ✅ 사용자명/비밀번호 설정
6. 쓰기 시작

### B. 라즈베리파이 부팅
1. microSD 카드를 라즈베리파이에 삽입
2. 전원 연결
3. 부팅 대기 (1-2분)

---

## 🔧 2단계: 초기 설정

### SSH로 접속 (맥/리눅스)
```bash
ssh pi@raspberrypi.local
# 비밀번호 입력
```

### 시스템 업데이트
```bash
sudo apt update
sudo apt upgrade -y
```

### Python 및 필수 도구 설치
```bash
# Python 3 확인 (보통 이미 설치됨)
python3 --version

# pip 설치
sudo apt install python3-pip python3-venv -y

# Git 설치
sudo apt install git -y
```

---

## 📦 3단계: 프로젝트 설치

### A. 프로젝트 복사
```bash
# 홈 디렉토리로 이동
cd ~

# 프로젝트 폴더 생성
mkdir stock_monitor
cd stock_monitor

# 파일들을 여기에 복사 (방법은 아래 참조)
```

### 파일 전송 방법:

**방법 1: SCP 사용 (맥/리눅스에서)**
```bash
# 로컬 컴퓨터에서 실행
scp -r /Users/jjongz/PycharmProjects/finacneFee/* pi@raspberrypi.local:~/stock_monitor/
```

**방법 2: Git 사용**
```bash
# GitHub에 올린 후
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git stock_monitor
cd stock_monitor
```

**방법 3: 수동 복사**
- FileZilla 같은 FTP 프로그램 사용
- 또는 USB 메모리 사용

### B. 가상환경 생성 및 패키지 설치
```bash
cd ~/stock_monitor

# 가상환경 생성
python3 -m venv venv

# 활성화
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

---

## ⚙️ 4단계: 설정

### config.py 수정
```bash
nano config.py
```

다음 내용 확인 및 수정:
```python
TELEGRAM_CONFIG = {
    'BOT_TOKEN': '8105040252:AAHXbWn0FV3ymw9PTzlbPMyIC6JoehY-3pM',
    'CHAT_ID': '6633793503',
}
```

저장: `Ctrl+O` → Enter → `Ctrl+X`

---

## 🤖 5단계: 실시간 모니터링 시작

### 수동 실행 (테스트)
```bash
cd ~/stock_monitor
source venv/bin/activate
python realtime_monitor.py
```

→ 5분마다 가격 체크, 매일 9:30에 전체 분석!

### 백그라운드 실행
```bash
# nohup으로 실행 (터미널 종료해도 계속 실행)
nohup python realtime_monitor.py > monitor.log 2>&1 &

# 프로세스 확인
ps aux | grep realtime_monitor

# 종료하려면
pkill -f realtime_monitor
```

---

## 🔄 6단계: 자동 시작 설정 (부팅 시)

### systemd 서비스 생성
```bash
sudo nano /etc/systemd/system/stock-monitor.service
```

다음 내용 입력:
```ini
[Unit]
Description=Stock Volatility Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/stock_monitor
Environment="PATH=/home/pi/stock_monitor/venv/bin"
ExecStart=/home/pi/stock_monitor/venv/bin/python realtime_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

저장 후 활성화:
```bash
# 서비스 활성화
sudo systemctl enable stock-monitor

# 서비스 시작
sudo systemctl start stock-monitor

# 상태 확인
sudo systemctl status stock-monitor

# 로그 확인
sudo journalctl -u stock-monitor -f
```

---

## 📱 7단계: 알림 받기

### 받게 될 알림:

**1. 매일 오전 9:30**
```
📊 일일 변동성 분석
══════════════════
⏰ 2024-11-29 09:30

🎯 고변동성 종목 TOP 5:
1. SOXL - 7.46%
   현재: $41.26
   1차 목표: $38.18
   2차 목표: $35.10
...
```

**2. 5분마다 (매수 기회 발생 시)**
```
🔔 매수 신호 발생!
══════════════════

📊 TQQQ (ProShares UltraPro QQQ)

💰 현재가: $52.00
🎯 목표가: $52.09
📉 변동: -0.99%
📊 표준편차: 4.49%

⭐ 1차 매수 시점!
💵 권장 투자: $1,000

💡 지금 매수를 고려하세요!
```

---

## 🔍 모니터링 & 관리

### 로그 확인
```bash
# 실시간 로그
tail -f ~/stock_monitor/monitor.log

# 서비스 로그
sudo journalctl -u stock-monitor -f
```

### 재시작
```bash
sudo systemctl restart stock-monitor
```

### 종료
```bash
sudo systemctl stop stock-monitor
```

### 설정 변경 후
```bash
# 설정 변경 (scheduler_config.py 등)
nano ~/stock_monitor/scheduler_config.py

# 서비스 재시작
sudo systemctl restart stock-monitor
```

---

## ⚙️ 커스터마이징

### 종목 추가/변경
`scheduler_config.py` 편집:
```python
WATCH_LIST = {
    'AAPL': 'Apple',      # 추가
    'MSFT': 'Microsoft',  # 추가
    'NVDA': 'NVIDIA',     # 추가
    # ... 최대 20개까지
}
```

### 체크 간격 변경
```python
SCHEDULE_CONFIG = {
    'realtime_check_interval': 10,  # 10분으로 변경
}
```

### 투자 금액 변경
`config.py`:
```python
INVESTMENT_CONFIG = {
    'default_amount': 2000000,  # 변경
}
```

---

## 💡 성능 최적화 팁

### 1. 차트 생성 최소화
- 매일 모든 차트를 보내면 부하 증가
- 상위 5개만 차트 생성하도록 수정 가능

### 2. 메모리 절약
```bash
# 스왑 메모리 증가 (4GB 라즈베리파이인 경우)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=2048로 변경
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 3. API 호출 제한
- FinanceDataReader: 제한 거의 없음
- 텔레그램: 분당 30개까지 가능
- 20개 종목 × 5분 간격 = 문제없음 ✅

---

## 🔋 전력 소비

- 라즈베리파이5: 약 3-5W
- 24시간 운영: 월 전기료 약 500원
- **매우 경제적!**

---

## 📊 예상 시나리오

### 평일 (거래일)
```
09:30 - 📊 일일 분석 실행 (3-5분)
09:35 - 📱 텔레그램 요약 전송
09:35 - 🔄 실시간 모니터링 시작
09:40 - ✅ 가격 체크 (5분마다)
...
16:00 - 장 마감
16:05 - ⏸️  실시간 체크 중단
```

### 주말
```
모니터링 일시 중단
```

---

## 🆘 문제 해결

### Q1. 서비스가 시작 안 됨
```bash
# 로그 확인
sudo journalctl -u stock-monitor -n 50

# 경로 확인
cd ~/stock_monitor && source venv/bin/activate && python realtime_monitor.py
```

### Q2. 메모리 부족
```bash
# 메모리 확인
free -h

# 불필요한 프로세스 종료
# 스왑 메모리 증가 (위 참조)
```

### Q3. 알림이 안 옴
```bash
# 네트워크 확인
ping google.com

# 텔레그램 연결 테스트
python telegram_alert.py test
```

---

## 📈 성능 벤치마크

### 라즈베리파이5에서 예상 성능:

| 작업 | 예상 시간 | 실제 부하 |
|------|----------|---------|
| 1개 종목 1년 데이터 | < 1초 | 낮음 |
| 20개 종목 분석 | 10-20초 | 낮음 |
| 차트 1개 생성 | 5-10초 | 중간 |
| 차트 20개 생성 | 2-3분 | 중간 |
| 실시간 가격 체크 | < 5초 | 낮음 |

**결론:** 여유있게 작동 가능! ✅

---

## 🎯 실전 운영 팁

### 1. 단계별 접근
**1주차:** 수동 실행으로 테스트
```bash
python realtime_monitor.py
```

**2주차:** 백그라운드 실행
```bash
nohup python realtime_monitor.py &
```

**3주차:** 자동 시작 설정
```bash
sudo systemctl enable stock-monitor
```

### 2. 로그 관리
```bash
# 로그 파일이 너무 커지면
# logrotate 설정 추가
sudo nano /etc/logrotate.d/stock-monitor
```

### 3. 원격 접속
```bash
# SSH 키 설정 (비밀번호 없이 접속)
ssh-copy-id pi@raspberrypi.local

# 또는 공유기에서 포트포워딩 설정
```

---

## 💰 비용 계산

### 초기 비용
- 라즈베리파이5 (8GB): ~$80
- microSD 32GB: ~$10
- 케이스 + 쿨러: ~$15
- **총**: ~$105

### 운영 비용
- 전기료: 월 ~500원
- API: 무료 (FinanceDataReader)
- 텔레그램: 무료
- **총**: 월 ~500원

**vs 클라우드 (AWS EC2 t3.micro):**
- 월 비용: ~$10 (약 13,000원)
- 라즈베리파이: 1년 후 본전!

---

## 🚀 빠른 설치 스크립트

라즈베리파이에서 한번에 설치:

```bash
#!/bin/bash
# setup.sh

# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install python3-pip python3-venv git -y

# 프로젝트 디렉토리 생성
mkdir -p ~/stock_monitor
cd ~/stock_monitor

# 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install finance-datareader pandas numpy matplotlib python-telegram-bot schedule

echo "✅ 설치 완료!"
echo "다음 단계: config.py 설정 후 python realtime_monitor.py 실행"
```

실행:
```bash
chmod +x setup.sh
./setup.sh
```

---

## 📱 알림 예시

### 오전 9:30 - 일일 리포트
- 20개 종목 변동성 순위
- 각 종목 매수 목표가
- 상위 5개 종목 상세 정보

### 실시간 (5분마다 체크)
- 1시그마 도달 → 즉시 알림
- 2시그마 도달 → 즉시 알림 (강조)
- 중복 알림 방지 (1시간 쿨다운)

---

## ⚠️ 주의사항

### 1. 인터넷 연결
- 안정적인 연결 필수
- WiFi보다 유선 권장

### 2. 전원 관리
- UPS 사용 권장 (정전 대비)
- 갑작스런 전원 차단 시 SD 카드 손상 가능

### 3. API 제한
- FinanceDataReader: 제한 거의 없음
- 과도한 호출 자제

### 4. 시간대 설정
```bash
# 타임존 설정 (한국)
sudo timedatectl set-timezone Asia/Seoul

# 확인
date
```

---

## 🎯 체크리스트

설치 전:
- [ ] 라즈베리파이5 준비
- [ ] microSD 카드 준비
- [ ] 안정적인 인터넷 연결
- [ ] 텔레그램 봇 설정 완료

설치 후:
- [ ] Python 설치 확인
- [ ] 프로젝트 파일 복사
- [ ] 가상환경 생성
- [ ] 패키지 설치
- [ ] config.py 설정
- [ ] 테스트 실행
- [ ] 자동 시작 설정

---

## 📞 지원

문제 발생 시:
1. 로그 확인: `tail -f monitor.log`
2. 서비스 상태: `sudo systemctl status stock-monitor`
3. 수동 실행 테스트: `python realtime_monitor.py`

---

## 🎉 완료!

이제 라즈베리파이가 24시간 자동으로:
- 📊 매일 아침 분석 리포트
- 🔔 5분마다 매수 기회 감시
- 📱 즉시 텔레그램 알림

**완전 자동화된 주식 모니터링 시스템 완성!** 🎉

