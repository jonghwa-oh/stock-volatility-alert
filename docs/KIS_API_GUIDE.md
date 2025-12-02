# 한국투자증권 Open Trading API 통합 가이드

## 📋 목차

1. [개요](#개요)
2. [주요 기능](#주요-기능)
3. [설정 방법](#설정-방법)
4. [데이터 수집 방식](#데이터-수집-방식)
5. [API 사용법](#api-사용법)
6. [문제 해결](#문제-해결)

---

## 개요

### 🎯 목적

한국투자증권 Open Trading API를 통합하여:
- **실시간 한국 주식 데이터** 수집
- **REST API** 및 **WebSocket** 지원
- **안정적인 Fallback 시스템** (FinanceDataReader 백업)

### 📊 데이터 소스 우선순위

```
한국 주식 (122630, 498400 등):
  1순위: 한국투자증권 API ✅
  2순위: FinanceDataReader (백업)

미국 주식 (SOXL, TQQQ 등):
  - FinanceDataReader만 사용
```

### 🔒 보안

- **App Key**와 **App Secret**은 **암호화**되어 저장
- 암호화 키는 `data/.kis_key`에 저장 (Git에서 제외)
- DB에는 암호화된 데이터만 저장

---

## 주요 기능

### 1. 암호화 시스템 (`kis_crypto.py`)

```python
from kis_crypto import KISCrypto

crypto = KISCrypto()

# 암호화
encrypted = crypto.encrypt("민감한 정보")

# 복호화
decrypted = crypto.decrypt(encrypted)

# KIS 인증 정보 저장
crypto.save_kis_credentials(
    app_key="PS3dFQ9T...",
    app_secret="qEtP1Qwu...",
    account_no="12345678",
    account_code="01"
)

# KIS 인증 정보 로드
credentials = crypto.load_kis_credentials()
```

### 2. API 인증 (`kis_auth.py`)

```python
from kis_auth import KISAuth

auth = KISAuth()

# 접근 토큰 발급
token = auth.get_access_token()

# API 헤더 생성
headers = auth.get_headers(tr_id="FHKST01010100")
```

**토큰 관리:**
- 자동 캐싱 (DB 저장)
- 만료 5분 전 자동 갱신
- 토큰 유효 기간: 24시간

### 3. API 클라이언트 (`kis_api.py`)

```python
from kis_api import KISApi

api = KISApi()

# 현재가 조회
price = api.get_stock_price("122630")
print(f"{price['name']}: {price['current_price']:,}원")

# 일봉 데이터 조회 (1년)
df = api.get_daily_price_history("498400")
print(df.tail())
```

### 4. 데이터 수집 통합 (`data_collector.py`)

```python
from data_collector import DataCollector

collector = DataCollector()

# 초기 데이터 로드 (KIS API 우선, 실패 시 FDR)
collector.initialize_historical_data(years=1)
```

**수집 로직:**
1. 한국 주식 감지 (숫자 6자리)
2. KIS API 시도
3. 실패 시 FinanceDataReader로 fallback
4. 둘 다 실패 시 에러 로그

---

## 설정 방법

### 1. 패키지 설치

```bash
# requirements.txt 업데이트됨
pip install -r requirements.txt
```

새로 추가된 패키지:
- `cryptography>=41.0.0`
- `requests>=2.31.0`

### 2. 한국투자증권 API 키 발급

#### 📱 절차

1. **한국투자증권 계좌 개설**
2. **홈페이지 또는 앱에서 Open API 신청**
   - [한국투자증권 Open API 포털](https://apiportal.koreainvestment.com)
3. **App Key 및 App Secret 발급**

#### 🔑 발급 정보 예시

```
App Key: PS3dFQ9TYaOGhO3MBABLt9JtUTivW1ihOJrt
App Secret: qEtP1QwuheXZvouP/tjPPYMiyDRJ5S...
```

### 3. 초기 설정 실행

```bash
python init_kis_settings.py
```

#### 입력 항목

```
🏦 한국투자증권 Open Trading API 설정
======================================================================

📝 API 인증 정보를 입력해주세요:

  App Key: PS3dFQ9TYaOGhO3MBABLt9JtUTivW1ihOJrt
  App Secret: qEtP1QwuheXZvouP/tjPPYMiyDRJ5S...

📝 계좌 정보를 입력해주세요:
   (선택 사항, 나중에 추가 가능)

  계좌번호 앞 8자리 (선택): 12345678
  
  계좌번호 뒤 2자리 선택:
    01: 종합계좌 (기본)
    03: 국내선물옵션
    08: 해외선물옵션
    22: 연금저축
    29: 퇴직연금

  선택 (기본 01): 01
```

### 4. 인증 테스트

```bash
python kis_auth.py
```

**예상 출력:**
```
🧪 한국투자증권 API 인증 테스트
======================================================================
🔑 한국투자증권 접근 토큰 발급 중...
✅ 토큰 발급 성공! (만료: 2025-12-01 14:30:00)

✅ 인증 성공!
  토큰: eyJ0eXAiOiJKV1QiLCJ...
  만료: 2025-12-01 14:30:00
```

### 5. API 테스트

```bash
python kis_api.py
```

**예상 출력:**
```
🧪 한국투자증권 API 테스트
======================================================================

[테스트 1] 삼성전자 (005930) 현재가 조회
----------------------------------------------------------------------
✅ 종목명: 삼성전자
   현재가: 71,000원
   전일대비: +1,000원 (+1.43%)
   거래량: 15,234,567주

[테스트 2] KODEX 레버리지 (122630) 현재가 조회
----------------------------------------------------------------------
✅ 종목명: KODEX 레버리지
   현재가: 72,500원
   전일대비: -500원 (-0.68%)

[테스트 3] KODEX 200타겟위클리커버드콜 (498400) 일봉 조회
----------------------------------------------------------------------
✅ 일봉 데이터 수집: 240개
✅ 데이터 기간: 2024-12-01 ~ 2025-11-30
   데이터 수: 240개
```

---

## 데이터 수집 방식

### 자동 Fallback 시스템

```python
# 한국 주식 (122630)
📊 KODEX 레버리지 (122630)
  🇰🇷 한국 주식 - KIS API 시도...
  ✅ KIS API: 240개 데이터
  ✅ 240개 데이터 저장 완료

# 만약 KIS API 실패 시
📊 KODEX 레버리지 (122630)
  🇰🇷 한국 주식 - KIS API 시도...
  ⚠️  KIS API 오류: Connection timeout
  🔄 Fallback - FDR 사용...
  ✅ FDR: 240개 데이터
  ✅ 240개 데이터 저장 완료

# 미국 주식 (SOXL)
📊 SOXL - Direxion Daily Semiconductor Bull 3X
  🇺🇸 미국 주식 - FDR 사용...
  ✅ FDR: 250개 데이터
  ✅ 250개 데이터 저장 완료
```

### 데이터 수집 실행

```bash
python data_collector.py
```

**또는 대화형 모드:**
```python
from data_collector import DataCollector

collector = DataCollector()

# 1년치 데이터 수집
collector.initialize_historical_data(years=1)
```

---

## API 사용법

### 현재가 조회

```python
from kis_api import KISApi

api = KISApi()

# 삼성전자 현재가
price = api.get_stock_price("005930")
print(f"현재가: {price['current_price']:,}원")
print(f"전일대비: {price['change_price']:+,}원")
print(f"등락률: {price['change_rate']:+.2f}%")

api.close()
```

### 일봉 데이터 조회

```python
from kis_api import KISApi
from datetime import datetime, timedelta

api = KISApi()

# 최근 1년 데이터
df = api.get_daily_price_history("122630")

# 특정 기간 데이터
start = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
end = datetime.now().strftime('%Y%m%d')
df = api.get_daily_price_history("122630", start, end)

print(df.head())
api.close()
```

### 데이터 수집기에서 사용

```python
from data_collector import DataCollector

collector = DataCollector()

# KIS API 사용 가능 여부 확인
if collector.kis_api:
    print("✅ KIS API 활성화")
else:
    print("⚠️  KIS API 비활성화")

# 데이터 수집 (자동 fallback)
collector.initialize_historical_data(years=1)

collector.close()
```

---

## 문제 해결

### 1. 암호화 키 오류

**증상:**
```
FileNotFoundError: data/.kis_key
```

**해결:**
```bash
python init_kis_settings.py
```

### 2. 토큰 발급 실패

**증상:**
```
❌ API 요청 오류: 401 Unauthorized
```

**해결:**
1. App Key와 App Secret 확인
2. 한국투자증권 API 신청 상태 확인
3. 토큰 재발급:
```bash
python kis_auth.py
```

### 3. 데이터 조회 실패

**증상:**
```
⚠️  122630 시세 조회 실패: Invalid ticker
```

**해결:**
1. 종목코드 형식 확인 (6자리 숫자)
2. 시장 시간 확인 (장 마감 후에는 전일 데이터)
3. Fallback 확인:
```python
collector = DataCollector()
# FDR로 자동 fallback됨
```

### 4. API 장애 상황

**증상:**
```
⚠️  KIS API 오류: Service unavailable
```

**자동 대응:**
- 시스템이 자동으로 FinanceDataReader로 전환
- 로그에 fallback 메시지 출력
- 데이터 수집 정상 진행

### 5. 인증 정보 재설정

```bash
# 기존 설정 삭제
python -c "from database import StockDatabase; db = StockDatabase(); db.delete_setting('kis_app_key'); db.delete_setting('kis_app_secret'); db.close()"

# 새로 설정
python init_kis_settings.py
```

---

## 파일 구조

```
finacneFee/
├── kis_crypto.py          # 암호화/복호화 모듈
├── kis_auth.py            # API 인증 관리
├── kis_api.py             # API 클라이언트
├── init_kis_settings.py   # 초기 설정 스크립트
├── data_collector.py      # 데이터 수집 (KIS + FDR)
├── data/
│   ├── .kis_key          # 암호화 키 (Git 제외)
│   └── stock_data.db     # 설정 및 데이터
└── docs/
    └── KIS_API_GUIDE.md  # 이 문서
```

---

## 참고 자료

- [한국투자증권 Open API 포털](https://apiportal.koreainvestment.com)
- [한국투자증권 GitHub](https://github.com/koreainvestment/open-trading-api)
- [API 문서](https://apiportal.koreainvestment.com/apiservice)

---

## 다음 단계

✅ **완료:**
1. 암호화 시스템 구축
2. API 인증 관리
3. 데이터 수집 통합
4. Fallback 시스템

🔜 **향후 계획:**
1. WebSocket 실시간 시세 연동
2. 주문 API 통합 (매수/매도)
3. 실시간 알림 강화

---

**📧 문의:** 한국투자증권 Open API 챗봇
**🔗 GitHub:** https://github.com/koreainvestment/open-trading-api



