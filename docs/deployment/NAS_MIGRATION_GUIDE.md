# NAS 배포 및 설정 마이그레이션 가이드

## 📋 개요

기존 개발 환경에서 Synology NAS로 설정 데이터를 쉽게 이동하는 방법입니다.

민감한 데이터(Telegram Bot Token, KIS API 키 등)를 안전하게 백업하고 복원할 수 있습니다.

---

## 🎯 포함되는 데이터

### 1. Settings (8개)
- `bot_token`: Telegram Bot Token
- `default_chat_id`: 기본 Chat ID
- `default_investment_amount`: 기본 투자 금액
- `kis_app_key`: KIS API App Key (암호화됨)
- `kis_app_secret`: KIS API App Secret (암호화됨)
- `kis_account_code`: KIS 계좌 코드
- `kis_access_token`: KIS Access Token (캐시)
- `kis_token_expired`: Token 만료 시간

### 2. Users (2명)
- `jjongz`: 활성화
- `bluejm`: 비활성화

### 3. User Watchlist (5개)
- 사용자별 관심 종목 목록
- 국가 정보 (KR/US)
- 활성화 상태

---

## 📤 1단계: 개발 환경에서 내보내기

### 1.1 설정 데이터 내보내기

```bash
cd /path/to/finacneFee
source venv/bin/activate
python export_settings.py
```

**결과:**
- `settings_backup.json` 파일 생성
- 모든 설정, 사용자, 관심 종목 포함

### 1.2 암호화 키 확인

```bash
ls -la data/.kis_key
```

**중요:** KIS API를 사용하는 경우 이 파일도 함께 복사해야 합니다!

---

## 📦 2단계: NAS로 파일 복사

### 2.1 방법 1: SCP 사용 (추천)

```bash
# Settings 백업 파일 복사
scp settings_backup.json admin@192.168.1.136:~/finacneFee/

# KIS 암호화 키 복사 (KIS API 사용 시)
scp data/.kis_key admin@192.168.1.136:~/finacneFee/data/
```

### 2.2 방법 2: GUI (Synology File Station)

1. File Station 웹 인터페이스 접속
2. `finacneFee/` 폴더로 이동
3. `settings_backup.json` 업로드
4. `data/.kis_key` 파일을 `data/` 폴더에 업로드

### 2.3 방법 3: SMB/CIFS 공유

1. NAS 공유 폴더 마운트
2. 파일 드래그 앤 드롭

---

## 📥 3단계: NAS에서 가져오기

### 3.1 NAS SSH 접속

```bash
ssh admin@192.168.1.136 -p 2848
cd /volume1/docker/finacneFee
```

### 3.2 설정 데이터 가져오기

```bash
# Docker 컨테이너 내에서 실행
docker exec -it finacnefee python import_settings.py

# 또는 호스트에서 직접 실행
python import_settings.py
```

**확인 프롬프트:**
```
⚠️  계속하시겠습니까? (yes/no): yes
```

**결과:**
```
✅ 가져오기 완료!

📊 저장된 데이터:
  • Settings: 8개 (KIS: 5개 포함)
  • Users: 2명
  • Watchlist: 5개
```

### 3.3 KIS 암호화 키 권한 설정

```bash
chmod 600 data/.kis_key
```

---

## ✅ 4단계: 확인

### 4.1 데이터 확인

```bash
python -c "
from database import StockDatabase
db = StockDatabase()

# 사용자 확인
users = db.get_all_users()
print('Users:', users)

# 설정 확인
print('Bot Token:', db.get_setting('bot_token')[:20] + '...')
print('Chat ID:', db.get_setting('default_chat_id'))

db.close()
"
```

### 4.2 KIS API 확인 (선택사항)

```bash
python -c "
from kis_crypto import KISCrypto

crypto = KISCrypto()
creds = crypto.load_kis_credentials()

print('✅ KIS API 인증 정보 로드 성공!')
print('App Key:', creds['app_key'][:10] + '...')
"
```

---

## 🔒 보안

### 백업 파일 삭제

```bash
# 개발 환경에서
rm settings_backup.json

# NAS에서
rm settings_backup.json
```

### 또는 안전한 곳에 백업

```bash
# 암호화하여 백업 (선택사항)
tar czf settings_backup.tar.gz settings_backup.json data/.kis_key
gpg -c settings_backup.tar.gz
rm settings_backup.tar.gz settings_backup.json
```

---

## 🚀 5단계: Docker 실행

### 5.1 Docker Compose로 실행

```bash
cd /volume1/docker/finacneFee
docker-compose up -d
```

### 5.2 로그 확인

```bash
docker-compose logs -f
```

---

## 🔄 업데이트 시 (기존 → NAS)

기존 설정을 유지하면서 코드만 업데이트:

```bash
# 1. 기존 환경에서 최신 설정 백업
python export_settings.py

# 2. Git에서 최신 코드 Pull
git pull origin main

# 3. NAS로 백업 파일만 복사
scp settings_backup.json admin@192.168.1.136:~/finacneFee/

# 4. NAS에서 설정 가져오기
docker exec -it finacnefee python import_settings.py

# 5. 컨테이너 재시작
docker-compose restart
```

---

## 🛠️ 트러블슈팅

### 1. `kis_key` 파일 없음

```
⚠️  키 파일 없음: data/.kis_key
```

**해결:**
- 기존 환경에서 `data/.kis_key` 복사
- 또는 `python init_kis_settings.py`로 새로 생성

### 2. 파일 권한 오류

```bash
chmod 600 data/.kis_key
chmod 644 settings_backup.json
```

### 3. DB 충돌

기존 데이터를 덮어쓰고 싶은 경우:

```bash
# 백업
cp data/stock_data.db data/stock_data.db.backup

# 강제 가져오기
python import_settings.py --force
```

---

## 📊 마이그레이션 체크리스트

- [ ] `python export_settings.py` 실행
- [ ] `settings_backup.json` 생성 확인
- [ ] `data/.kis_key` 파일 확인 (KIS 사용 시)
- [ ] NAS로 파일 복사
- [ ] `python import_settings.py` 실행
- [ ] 데이터 확인
- [ ] KIS API 테스트 (선택)
- [ ] Docker 컨테이너 실행
- [ ] 아침 알림 테스트
- [ ] 실시간 모니터링 테스트
- [ ] 백업 파일 삭제 또는 안전 보관

---

## 💡 추천 워크플로우

### 정기적인 백업

```bash
# 매월 1일 자동 백업 (cron)
0 0 1 * * cd /volume1/docker/finacneFee && python export_settings.py && mv settings_backup.json backup/settings_$(date +\%Y\%m\%d).json
```

### Git에서 코드 업데이트 + 설정 유지

```bash
#!/bin/bash
# update_nas.sh

echo "📥 최신 코드 가져오기..."
git pull origin main

echo "📦 의존성 업데이트..."
pip install -r requirements.txt

echo "🔄 Docker 재시작..."
docker-compose restart

echo "✅ 업데이트 완료!"
```

---

## ⚠️ 중요 주의사항

1. **민감한 정보 보호**
   - `settings_backup.json`에는 Telegram Bot Token, KIS API 키가 포함됩니다
   - Git에 커밋하지 마세요 (`.gitignore`에 추가됨)
   - 전송 시 HTTPS/SSH 사용

2. **암호화 키 관리**
   - `data/.kis_key`는 KIS 설정 복호화에 필수
   - 분실 시 KIS 설정을 다시 입력해야 함
   - 권한: `chmod 600`

3. **백업 주기**
   - 중요한 변경 후 즉시 백업
   - 정기적인 자동 백업 설정 권장

---

**끝! NAS 배포 준비 완료** 🎉



