# 🤖 AI 주식 변동성 알림 시스템

변동성 분석으로 최적의 매수 타이밍을 알려드립니다.

## ✨ 주요 기능

- 📊 **변동성 분석**: 1년 일봉 데이터로 **0.5x, 1x, 2x** 표준편차 매수 타이밍 분석
- ⚡ **WebSocket 실시간 알림**: 매수 타이밍 도달 즉시 알림 (지연 0초!)
- 🌙 **놓친 알림 요약**: 밤 사이 매수 기회를 아침 8시에 요약해서 전송
- 🤖 **텔레그램 봇 커맨드**: `/add`, `/remove`, `/status`, `/morning` 명령으로 편리한 관리
- 👨‍👩‍👦 **가족 멀티 유저**: 각자 다른 종목, 투자금액 설정 가능
- 📱 **텔레그램 연동**: 차트 이미지와 함께 매수 알림 전송
- 🏦 **한국투자증권 API**: REST + WebSocket 실시간 시세 (Fallback 지원)
- 🔐 **보안 강화**: 민감한 정보는 암호화하여 DB 저장
- 🐳 **Docker 지원**: 간편한 배포 및 실행
- 🍓 **경량 최적화**: 라즈베리파이 5 / 시놀로지 NAS 최적화

## 🔐 데이터 관리

**모든 설정을 하나의 DB로 통합 관리!**

```
stock_data.db (하나의 DB)
├── 주식 데이터 (일봉/분봉)
├── 사용자 정보
├── 종목 관심 목록
├── 설정 (봇 토큰, 투자 금액)
└── KIS API 인증 정보 (암호화)
```

- ✅ 설정 관리 간편
- ✅ DB 하나만 백업하면 끝
- ✅ 별도 파일 관리 불필요
- ✅ 암호화로 보안 강화

## 📊 데이터 소스

**자동 Fallback으로 안정성 극대화!**

| 종목 유형 | 1순위 | 2순위 (백업) |
|----------|------|-------------|
| 한국 주식 (122630, 498400 등) | 🏦 한국투자증권 API | 📈 FinanceDataReader |
| 미국 주식 (SOXL, TQQQ 등) | 🏦 한국투자증권 API | 📈 FinanceDataReader |

- ✅ **모든 주식 KIS API 통합** (한국 + 미국)
- ✅ 실시간 데이터 (한국 WebSocket, 미국 폴링)
- ✅ API 장애 시 자동 백업 (FinanceDataReader)
- ✅ 데이터 소실 없음

## 🚀 빠른 시작

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/stock-monitor.git
cd stock-monitor
```

### 2. 가상환경 및 패키지 설치

```bash
# Python 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 3. 한국투자증권 API 설정 (선택)

**한국 주식 실시간 데이터를 원하시면 설정하세요!**

```bash
python init_kis_settings.py
```

상세 가이드: [KIS API 설정 가이드](docs/KIS_API_GUIDE.md)

**설정하지 않으면?**
- 한국 주식도 FinanceDataReader로 수집됩니다.
- 기능은 모두 정상 작동합니다!

### 3. 초기 설정

```bash
python init_settings.py
```

**입력 예시:**
```
Bot Token: (BotFather에서 받은 토큰 입력)
기본 Chat ID (선택): (텔레그램 Chat ID 입력)
기본 투자 금액 (원): 1000000
```

이 명령어는:
- DB의 settings 테이블에 설정 저장
- 텔레그램 봇 토큰 등록
- 기본 투자 금액 설정

### 4. DB 초기화 및 데이터 수집

```bash
# 1년치 일봉 데이터 수집 (최초 1회)
python data_collector.py init

# 사용자 설정
python user_manager.py
```

### 5. 실행

```bash
# 실시간 모니터링 시작
python realtime_monitor_multiuser.py
```

---

## ⏰ 작동 방식

### 24시간 자동 운영

```
📅 매일 08:00 (아침)
├── 1단계: 일봉 데이터 자동 업데이트
└── 2단계: 밤 사이 놓친 알림 요약 전송
    └─ 00:00~06:00 사이 매수 기회 요약

📊 월-금 08:50 (아침)
└── 오늘의 매수 전략 분석
    ├─ 차트 이미지 생성
    └─ 사용자별 텔레그램 전송

⚡ 09:00~24:00 (활동 시간)
├── 한국 주식: WebSocket 실시간 모니터링
│   └─ 목표가 도달 즉시 알림 (지연 0초)
└── 미국 주식: 1분마다 폴링
    └─ 목표가 도달 시 즉시 알림

🌙 00:00~06:00 (수면 시간)
└── 목표가 도달 시 DB에만 기록
    └─ 다음 날 08:00에 요약 전송
```

### 놓친 알림 요약 예시

```
🌙 jjongz님, 밤 사이 매수 기회가 있었습니다!

📅 2025-12-01 새벽 (00:00~06:00)
🔔 총 2건의 알림

━━━━━━━━━━━━━━━━━━

1. 🇺🇸 SOXL - Direxion Daily Semiconductor Bull 3X
   2차 매수 시점 도달!
   시각: 02:45:23
   가격: $35.00
   목표가: $35.10 (-14.93% 하락)

2. 🇺🇸 TQQQ - ProShares UltraPro QQQ
   1차 매수 시점 도달!
   시각: 04:15:10
   가격: $52.00
   목표가: $52.09 (-4.49% 하락)

━━━━━━━━━━━━━━━━━━

💡 실시간 알림은 09:00~24:00만 전송됩니다.
   밤 사이 매수 기회는 다음 날 아침에 요약해드립니다.
```

**장점:**
- ✅ 수면 방해 없음 (밤 알림 차단)
- ✅ 기회 놓치지 않음 (아침 요약)
- ✅ 완전한 기록 (DB 저장)
- ✅ 사용자별 맞춤 (관심 종목만)

---

## 🤖 텔레그램 봇 커맨드

### 지원 명령어

```
/start - 봇 시작 및 환영 메시지
/help - 도움말 보기

📝 종목 관리:
/list - 내 관심 종목 목록
/add TICKER - 종목 추가
/remove TICKER - 종목 삭제

📊 실시간 조회:
/morning - 오늘의 매수 전략 받기
/status - 현재가 및 목표가 확인
/status TICKER - 특정 종목만 확인
```

### 사용 예시

#### 1. 종목 추가

```
/add TQQQ
→ ✅ 🇺🇸 ProShares UltraPro QQQ (TQQQ) 추가 완료!

/add 122630
→ ✅ 🇰🇷 KODEX 레버리지 (122630) 추가 완료!
```

#### 2. 종목 목록 확인

```
/list
→ 📊 jjongz님의 관심 종목
   투자금액: 1,000,000원
   
   1. 🇺🇸 SOXL - Direxion Daily Semiconductor Bull 3X
   2. 🇺🇸 TQQQ - ProShares UltraPro QQQ
   3. 🇰🇷 KODEX 레버리지 (122630)
   4. 🇰🇷 KODEX 200타겟위클리커버드콜 (498400)
   
   총 4개 종목
```

#### 3. 실시간 현재가 및 목표가 확인

```
/status SOXL
→ 📊 jjongz님의 실시간 현황
   ⏰ 2025-12-01 14:30:25
   
   🇺🇸 SOXL - Direxion Daily Semiconductor Bull 3X
   💰 현재가: $35.50
   
   🧪 테스트: $35.00 (-1.41% 하락)
   1차 매수: $34.50 (-2.82% 하락)
   2차 매수: $33.50 (-5.63% 하락)
```

#### 4. 아침 알림 수동 받기

```
/morning
→ 📊 분석 중... 잠시만 기다려주세요!
   (차트 이미지 + 매수 목표가 전송)
```

#### 5. 종목 삭제

```
/remove TQQQ
→ ✅ TQQQ 삭제 완료!
```

### 봇 커맨드 실행 방법

#### 로컬 테스트

```bash
python telegram_bot_commands.py
```

#### Docker에서 실행 (백그라운드)

```bash
# start.sh 수정하여 백그라운드 실행 추가
python telegram_bot_commands.py &
```

### 장점

- ✅ 웹/앱 접속 불필요
- ✅ 텔레그램만으로 완전한 관리
- ✅ 실시간 조회 가능
- ✅ 종목 추가/삭제 간편
- ✅ Chat ID 자동 인식

---

## 🧪 0.5 표준편차 (테스트용)

### 왜 추가했나요?

**기존 문제:**
- 1x, 2x 표준편차 알림은 드물게 발생
- 시스템이 정상 작동하는지 확인 어려움
- 테스트를 위해 오래 기다려야 함

**해결책:**
- **0.5x 표준편차 추가!**
- 약 -1.5~2% 하락 시 알림
- 더 자주 발생 → 테스트 용이

### 매수 시점 비교

| 레벨 | 하락폭 | 발생 빈도 | 투자금 |
|------|--------|----------|--------|
| 🧪 테스트 (0.5x) | 약 -1.5~2% | **자주** (주 1-2회) | 50% |
| 1차 (1x) | 약 -3~4% | 보통 (월 2-3회) | 100% |
| 2차 (2x) | 약 -6~8% | 드묾 (분기 1-2회) | 200% |

### 예시: SOXL (표준편차 3%)

```
현재가: $36.00

🧪 테스트 매수: $35.46 (-1.5% 하락)
   투자금: 500,000원
   
1차 매수: $34.92 (-3.0% 하락)
   투자금: 1,000,000원
   
2차 매수: $33.84 (-6.0% 하락)
   투자금: 2,000,000원
```

### 사용 방법

**테스트가 끝나면 0.5x 알림을 끄고 싶다면:**

1. `volatility_analysis.py`에서 `drop_05x` 계산 주석 처리
2. `realtime_monitor_hybrid.py`에서 0.5x 체크 주석 처리
3. `daily_analysis.py`에서 0.5x 표시 주석 처리

또는 그냥 **무시**하셔도 됩니다! 😊

---

## 🐳 Docker 사용 (권장)

### 1. 초기 설정

```bash
# 설정 파일 생성
python setup_secrets.py
```

### 2. Docker 빌드 및 실행

```bash
# 빌드
docker-compose build

# 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 3. 컨테이너 내에서 초기화

```bash
# 사용자 설정
docker-compose exec stock-monitor python user_manager.py

# 데이터 수집
docker-compose exec stock-monitor python data_collector.py init
```

---

## 📊 주요 모듈

| 파일 | 설명 |
|------|------|
| `init_settings.py` | 초기 설정 스크립트 |
| `config.py` | 설정 로더 (DB에서 읽기) |
| `database.py` | SQLite DB 관리 (설정 포함) |
| `data_collector.py` | 일봉/분봉 데이터 수집 |
| `user_manager.py` | 사용자 및 종목 관리 |
| `daily_analysis.py` | 일일 매수 알림 (8:50 AM) |
| `realtime_monitor_multiuser.py` | 실시간 모니터링 (5분마다) |
| `telegram_bot.py` | 텔레그램 알림 전송 |
| `volatility_analysis.py` | 변동성 분석 및 차트 생성 |
| `backtest_strategy.py` | 백테스트 분석 |

---

## 👨‍👩‍👦 가족 멀티 유저 설정

```bash
# 사용자 추가
python user_manager.py
```

**예시:**
```
1. 사용자 추가
이름: 아빠
텔레그램 Chat ID: 123456789
기본 투자금액: 1000000

종목 추가:
  - TQQQ
  - SOXL
  - QLD

2. 사용자 추가
이름: 와이프
텔레그램 Chat ID: 987654321
기본 투자금액: 500000

종목 추가:
  - SPY
  - QQQ
```

자세한 내용: [FAMILY_SETUP_GUIDE.md](FAMILY_SETUP_GUIDE.md)

---

## 🍓 라즈베리파이 배포

[RASPBERRY_PI_GUIDE.md](RASPBERRY_PI_GUIDE.md) 참조

---

## 💾 시놀로지 NAS 배포

### Docker 사용 (권장)

[DS218_DOCKER_GUIDE.md](DS218_DOCKER_GUIDE.md) 참조

### 직접 설치

[SYNOLOGY_SETUP_GUIDE.md](SYNOLOGY_SETUP_GUIDE.md) 참조

---

## 📈 백테스트

```bash
# QLD, TQQQ, SOXL 5년 백테스트
python backtest_strategy.py
```

**결과 예시:**
- 1-시그마: 1000달러 매수
- 2-시그마: 2000달러 매수
- 최종 수익률 비교

---

## 🔧 설정 파일

### scheduler_config.py

```python
# 모니터링 종목 설정
MONITORING_TICKERS = {
    'KS200': '코스피200',
    'TQQQ': 'ProShares UltraPro QQQ',
    'QLD': 'ProShares Ultra QQQ',
    'SOXL': 'Direxion Daily Semiconductor Bull 3X',
    'SPY': 'S&P 500 ETF',
    'QQQ': 'Invesco QQQ Trust',
}

# 스케줄링
SCHEDULE = {
    'daily_analysis_time': '08:50',     # 월-금 오전 8:50
    'realtime_interval': 5,             # 5분마다
    'data_update_time': '08:00',        # 데이터 업데이트
}
```

---

## 📁 파일 구조

```
stock-monitor/
├── 🐍 Python 소스코드
│   ├── init_settings.py            # 초기 설정 (Telegram)
│   ├── init_kis_settings.py        # KIS API 설정
│   ├── export_settings.py          # 설정 내보내기 ⭐ NEW
│   ├── import_settings.py          # 설정 가져오기 ⭐ NEW
│   ├── config.py                   # 설정 로더
│   ├── database.py                 # DB 관리
│   ├── data_collector.py           # 데이터 수집
│   ├── user_manager.py             # 유저 관리
│   ├── daily_analysis.py           # 일일 분석 (월-금 8:50)
│   ├── daily_updater.py            # 일일 업데이트 (매일 8:00) ⭐ NEW
│   ├── missed_alerts.py            # 놓친 알림 요약 ⭐ NEW
│   ├── realtime_monitor_hybrid.py  # 실시간 모니터링 (하이브리드)
│   ├── telegram_bot.py             # 텔레그램 봇
│   ├── volatility_analysis.py      # 변동성 분석
│   ├── kis_auth.py                 # KIS API 인증
│   ├── kis_api.py                  # KIS REST API
│   ├── kis_websocket.py            # KIS WebSocket
│   ├── kis_crypto.py               # KIS 암호화
│   ├── backtest_strategy.py        # 백테스트
│   └── scheduler_config.py         # 스케줄 설정
│
├── 📁 데이터 폴더
│   ├── data/                       # 데이터베이스 저장소
│   │   └── stock_data.db          # 통합 DB (주식 데이터 + 설정)
│   ├── charts/                     # 차트 이미지 (종목별 폴더)
│   │   ├── TQQQ/
│   │   │   └── 2024-11-30_TQQQ_...png
│   │   └── QLD/
│   │       └── 2024-11-30_QLD_...png
│   ├── logs/                       # 로그 파일
│   └── backup/                     # DB 백업
│
├── 📚 문서
│   ├── docs/                       # 가이드 문서
│   └── README.md                   # 이 파일
│
├── 🐳 Docker
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── 🔒 로컬 전용 (Git 제외)
│   ├── .env                        # 마스터 키
│   ├── data/*.db                   # DB 파일들
│   └── logs/*.log                  # 로그 파일들
│
└── requirements.txt                # 패키지 목록
```

---

## 🔒 보안 주의사항

### GitHub에 올라가는 파일 ✅
- 모든 `.py` 소스코드
- `README.md` 등 문서
- `requirements.txt`
- `Dockerfile`, `docker-compose.yml`

### GitHub에 올라가면 안 되는 파일 ❌
- `data/stock_data.db` (주식 데이터 + 설정)
- `logs/*.log` (로그 파일)
- `backup/*.db` (백업 파일)
- `charts/` (차트 이미지)

**.gitignore**에 모두 포함되어 있습니다!

---

## 🛠️ 개발 환경

- Python 3.11+
- SQLite3
- Docker (선택)

---

## 📚 문서

### 시작하기
- [빠른 시작 가이드](docs/QUICK_START.md)
- [다음 단계](docs/NEXT_STEPS.md)
- [GitHub Push 가이드](docs/GITHUB_PUSH_GUIDE.md)

### 설정
- [가족 멀티 유저 설정](docs/FAMILY_SETUP_GUIDE.md)
- [텔레그램 봇 설정](docs/봇_설치_가이드.md)

### 배포
- [시놀로지 NAS (Docker)](docs/deployment/DS218_DOCKER_GUIDE.md)
- [시놀로지 NAS (직접 설치)](docs/deployment/SYNOLOGY_SETUP_GUIDE.md)
- [라즈베리파이 5](docs/deployment/RASPBERRY_PI_GUIDE.md)
- [**NAS 설정 마이그레이션**](docs/deployment/NAS_MIGRATION_GUIDE.md) ⭐ 추천!

---

## 📄 라이선스

MIT License

---

## 🤝 기여

이슈나 PR은 언제나 환영합니다!

---

## 📧 문의

문제가 있으시면 이슈를 등록해주세요.

---

## 🎯 로드맵

- [ ] 웹 대시보드 추가
- [ ] 더 많은 거래소 지원 (바이낸스, 업비트 등)
- [ ] AI 기반 추가 분석 지표
- [ ] 백테스트 자동화 및 최적화
- [ ] 멀티 텔레그램 그룹 지원

---

**⭐ 도움이 되셨다면 Star를 눌러주세요!**
