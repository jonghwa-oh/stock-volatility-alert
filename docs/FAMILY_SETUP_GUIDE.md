# 👨‍👩‍👦 가족용 멀티 유저 설정 가이드

**각 가족 구성원이 자신만의 종목을 모니터링하고 개별 알림을 받을 수 있습니다!**

---

## ✨ 가족용 시스템 특징

### 개인화된 투자
- ✅ **각자 다른 종목** 모니터링
- ✅ **각자 다른 텔레그램**으로 알림
- ✅ **개인별 투자 금액** 설정
- ✅ **DB로 관리** (간편한 추가/수정)

### 예시
```
👨 아빠
  • 종목: TQQQ, SOXL, QLD (레버리지)
  • 투자: 100만원
  • 알림: 아빠 텔레그램

👩 엄마  
  • 종목: SPY, QQQ, VOO (안정적)
  • 투자: 100만원
  • 알림: 엄마 텔레그램

👦 아들
  • 종목: XLK, TECL, QQQ (기술주)
  • 투자: 50만원
  • 알림: 아들 텔레그램
```

---

## 🚀 4단계 설정

### 1단계: 텔레그램 Chat ID 확인

각 가족 구성원이 자신의 Chat ID를 확인해야 합니다.

#### 방법 1: @userinfobot 사용 (권장)
1. 텔레그램에서 `@userinfobot` 검색
2. 봇과 대화 시작
3. Chat ID 확인 (숫자)

#### 방법 2: 우리 봇 사용
1. `@stock_alert_sigma_bot` 검색
2. `/start` 입력
3. `python check_chatid.py` 실행

**준비:**
```
아빠 Chat ID: 123456789 (예시)
엄마 Chat ID: 234567890 (각자 확인)
아들 Chat ID: 345678901 (각자 확인)
```

---

### 2단계: 가족 정보 등록

```bash
cd /Users/jjongz/PycharmProjects/finacneFee
source venv/bin/activate
python user_manager.py family
```

**대화형으로 입력:**
```
1️⃣ 첫 번째 사용자 (본인)
  텔레그램 Chat ID: 123456789
  
✅ 사용자 추가 완료!
   • 이름: 아빠
   • Chat ID: 123456789
   • 투자 금액: 1,000,000원

관심 종목 추가:
  추천: 레버리지 ETF (TQQQ, SOXL, QLD)
  종목 코드 (쉼표로 구분, 엔터=추천): [엔터]
  
✅ 아빠에게 3개 종목 추가

2️⃣ 두 번째 사용자 (배우자)
  텔레그램 Chat ID: 123456789
  
... (반복)
```

---

### 3단계: 실시간 모니터링 시작

```bash
python realtime_monitor_multiuser.py
```

**출력:**
```
👨‍👩‍👦 가족용 멀티 유저 모니터링 시스템
══════════════════════════════════════

👥 등록된 사용자: 3명
   • 아빠: 3개 종목
   • 엄마: 3개 종목
   • 아들: 3개 종목

📊 모니터링 중인 총 종목: 8개
✅ 3명 사용자 텔레그램 초기화

✅ 모니터링 시작!
```

---

### 4단계: 알림 받기

각 가족 구성원의 텔레그램으로 **개별 알림**이 갑니다!

#### 아빠 텔레그램:
```
📊 아빠님의 일일 분석
═══════════════════════
⏰ 2024-11-29 09:30
💰 투자 금액: 1,000,000원

🎯 관심 종목 (3개):
1. TQQQ (ProShares UltraPro QQQ)
   현재: $54.54
   변동성: 4.49%
   1차 목표: $52.09 → 1,000,000원
   2차 목표: $49.65 → 2,000,000원
...
```

#### 매수 신호 (개별 알림):
```
🔔 아빠님, 매수 신호!
══════════════════

📊 TQQQ
💰 현재가: $52.00
🎯 목표가: $52.09

⭐ 1차 매수 시점!
💵 권장 투자: 1,000,000원
💵 USD: $769

💡 지금 매수를 고려하세요!
```

---

## 🛠️ 사용자 관리

### 사용자 목록 확인
```bash
python user_manager.py list
```

**출력:**
```
👥 등록된 사용자
══════════════════════════════════════

📱 아빠
   • Chat ID: 123456789
   • 투자 금액: 1,000,000원
   • 관심 종목 (3개):
     - TQQQ: ProShares UltraPro QQQ
     - SOXL: Direxion Daily Semiconductor Bull 3X
     - QLD: ProShares Ultra QQQ

📱 엄마
   • Chat ID: 234567890
   • 투자 금액: 1,000,000원
   • 관심 종목 (3개):
     - SPY: S&P 500 ETF
     - QQQ: Invesco QQQ Trust
     - VOO: Vanguard S&P 500 ETF
...
```

---

### 종목 추가/제거

#### 대화형 모드
```bash
python user_manager.py setup
```

**메뉴:**
```
메뉴:
  1. 사용자 추가
  2. 관심 종목 추가
  3. 관심 종목 제거
  4. 사용자 목록
  5. 사용자 상세
  6. 종료

선택 (1-6): 2

사용 가능한 종목:
  1. KS200: 코스피200
  2. TQQQ: ProShares UltraPro QQQ
  3. QLD: ProShares Ultra QQQ
  ...

사용자 이름: 아빠
종목 코드 (쉼표로 구분): AAPL,MSFT

✅ 아빠에게 2개 종목 추가
```

---

### Python으로 직접 관리

```python
from database import StockDatabase

db = StockDatabase()

# 종목 추가
db.add_user_watchlist("아빠", "AAPL")
db.add_user_watchlist("아빠", "MSFT")

# 종목 제거
db.remove_user_watchlist("아빠", "AAPL")

# 투자 금액 변경
db.update_user_investment("아빠", 2000000)

# 관심 종목 확인
watchlist = db.get_user_watchlist("아빠")
print(watchlist)

db.close()
```

---

## 📊 DB 구조

### users 테이블
```sql
id              사용자 ID
name            이름 (아빠, 엄마, 아들)
chat_id         텔레그램 Chat ID
investment_amount  투자 금액
enabled         활성화 여부
```

### user_watchlist 테이블
```sql
id              ID
user_id         사용자 ID
ticker          종목 코드
enabled         활성화 여부
added_at        추가 날짜
```

---

## 💡 추천 종목 조합

### 👨 아빠 (공격적)
```
레버리지 ETF:
- TQQQ (나스닥 3배)
- SOXL (반도체 3배)  
- QLD (나스닥 2배)
- UPRO (S&P500 3배)
```

### 👩 엄마 (안정적)
```
일반 ETF:
- SPY (S&P 500)
- QQQ (나스닥 100)
- VOO (Vanguard S&P 500)
- VTI (Total Market)
```

### 👦 아들 (기술주)
```
기술 섹터:
- XLK (Technology)
- TECL (Tech 3배)
- QQQ (나스닥 100)
- SOXX (반도체)
```

---

## 🍓 라즈베리파이 성능

### 가족 3명 사용 시

| 항목 | 수량 | 성능 | 판정 |
|------|------|------|------|
| 사용자 | 3명 | - | ✅ |
| 총 종목 | 8-15개 | 2-3초 | ✅ |
| 일일 업데이트 | 3명 | 3-5초 | ✅ |
| 5분 체크 | 3명 | 2-3초 | ✅ |
| 메모리 | - | 350MB | ✅ |

**결론: 라즈베리파이5로 충분! ✅**

### 확장 가능성
```
최대 10명까지 가능!
각 10개 종목 = 총 100개
여전히 충분함 ✅
```

---

## 📱 알림 예시

### 매일 9:30 - 개인별 리포트

**아빠 텔레그램:**
```
📊 아빠님의 일일 분석
관심 종목: TQQQ, SOXL, QLD
```

**엄마 텔레그램:**
```
📊 엄마님의 일일 분석
관심 종목: SPY, QQQ, VOO
```

**아들 텔레그램:**
```
📊 아들님의 일일 분석
관심 종목: XLK, TECL, QQQ
```

### 5분마다 - 매수 신호 (개별)

**아빠만 TQQQ 알림 받음:**
```
🔔 아빠님, 매수 신호!
TQQQ - 1차 매수 시점
```

**엄마만 SPY 알림 받음:**
```
🔔 엄마님, 매수 신호!
SPY - 1차 매수 시점
```

---

## 🎯 장점

### 1. 개인화
- ✅ 각자 관심 종목
- ✅ 개별 투자 금액
- ✅ 자신의 텔레그램으로만 알림

### 2. 효율성
- ✅ 중복 종목은 1번만 조회
- ✅ DB에서 캐싱
- ✅ 초고속 (2-3초)

### 3. 관리 편의성
- ✅ 대화형 설정 도구
- ✅ 언제든 종목 변경
- ✅ DB로 영구 저장

---

## 🔧 고급 설정

### 투자 금액 개인별 설정

```python
from database import StockDatabase

db = StockDatabase()

# 아빠: 200만원
db.update_user_investment("아빠", 2000000)

# 엄마: 150만원
db.update_user_investment("엄마", 1500000)

# 아들: 50만원
db.update_user_investment("아들", 500000)

db.close()
```

### 일부 사용자 비활성화

```python
from database import StockDatabase

db = StockDatabase()
conn = db.connect()
cursor = conn.cursor()

# 아들 일시 비활성화
cursor.execute("UPDATE users SET enabled = 0 WHERE name = '아들'")
conn.commit()

db.close()
```

---

## ❓ FAQ

### Q1. 나중에 가족 구성원 추가 가능?
**A:** 언제든 가능합니다!
```bash
python user_manager.py setup
# → 1. 사용자 추가
```

### Q2. 종목 변경은?
**A:** 실시간 반영됩니다!
```bash
python user_manager.py setup
# → 2. 관심 종목 추가/제거
```

### Q3. 같은 종목을 여러 명이 관심 종목으로 하면?
**A:** 문제없습니다!
- 데이터는 1번만 조회 (효율적)
- 각자 개별 알림 (각자 텔레그램)

### Q4. 투자 금액 다르게?
**A:** 가능합니다!
```python
db.update_user_investment("아빠", 2000000)
db.update_user_investment("엄마", 1000000)
db.update_user_investment("아들", 500000)
```

---

## 🎉 완성 체크리스트

### 초기 설정
- [ ] DB 초기화 (`python data_collector.py init`)
- [ ] 가족 Chat ID 확인
- [ ] 사용자 등록 (`python user_manager.py family`)
- [ ] 종목 추가 확인 (`python user_manager.py list`)

### 실행
- [ ] 실시간 모니터링 시작 (`python realtime_monitor_multiuser.py`)
- [ ] 각자 텔레그램 알림 확인
- [ ] 매수 신호 테스트

### 라즈베리파이 (선택)
- [ ] 라즈베리파이 설정
- [ ] 자동 시작 설정
- [ ] 24시간 운영

---

## 🚀 빠른 시작 (완전 자동)

```bash
# 1. DB 초기화 (이미 했으면 생략)
python data_collector.py init

# 2. 가족 설정
python user_manager.py family
# → Chat ID 입력
# → 종목 선택

# 3. 모니터링 시작
python realtime_monitor_multiuser.py

# 끝! 각자 텔레그램으로 알림 받기 시작!
```

---

## 📊 DB 직접 확인

```bash
sqlite3 stock_data.db

# 사용자 목록
SELECT * FROM users;

# 사용자별 종목
SELECT u.name, uw.ticker, dp.ticker_name
FROM users u
JOIN user_watchlist uw ON u.id = uw.user_id
LEFT JOIN daily_prices dp ON uw.ticker = dp.ticker
WHERE uw.enabled = 1
GROUP BY u.name, uw.ticker;

.quit
```

---

## 💡 활용 팁

### 1. 가족 회의
- 매주 관심 종목 리뷰
- 수익률 비교
- 종목 추가/제거

### 2. 교육 목적
- 아이들에게 투자 교육
- 실시간 데이터로 학습
- 리스크 관리 연습

### 3. 포트폴리오 분산
- 가족 전체로 다양한 종목
- 리스크 분산
- 기회 극대화

---

## 🎉 완료!

### 구축한 시스템:

✅ **가족 멀티 유저 시스템**
- 각자 다른 종목
- 개별 텔레그램 알림
- 개인별 투자 금액

✅ **DB 기반 관리**
- 쉬운 추가/수정
- 영구 저장
- 빠른 조회

✅ **라즈베리파이 최적화**
- 3명 이상도 가능
- 저전력 운영
- 24시간 자동

---

**이제 온 가족이 함께 스마트한 투자를 시작하세요!** 👨‍👩‍👦📊🚀

