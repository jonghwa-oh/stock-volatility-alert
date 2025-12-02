# 🐛 디버그 가이드

문제가 발생할 때 확인하는 방법입니다.

---

## 📋 목차

1. [로컬에서 테스트](#로컬에서-테스트)
2. [NAS Docker 로그 확인](#nas-docker-로그-확인)
3. [텔레그램 봇 응답 없음](#텔레그램-봇-응답-없음)
4. [8:50 알림이 안옴](#850-알림이-안옴)
5. [시간 제한 임시 해제](#시간-제한-임시-해제)

---

## 🏠 로컬에서 테스트

### 1. 봇 직접 실행

```bash
cd /Users/jjongz/PycharmProjects/finacneFee
source venv/bin/activate
python telegram_bot_commands.py
```

**예상 출력:**
```
======================================================================
🤖 텔레그램 봇 커맨드 핸들러 시작
======================================================================
✅ Bot Token: 1234567890:ABCDE...xyz

🔧 Telegram Application 생성 중...
✅ Application 생성 완료!

✅ 커맨드 핸들러 등록 완료:
   - /start: 봇 시작
   - /help: 도움말
   - /list: 종목 목록
   ...

🚀 봇 시작... (Ctrl+C로 종료)
======================================================================

🔄 Polling 시작...
```

**이 상태에서 텔레그램으로 `/list` 전송:**
```
📥 /list 명령 수신 - Chat ID: 6633793503
```

**응답이 없으면:**
- Bot Token이 올바른지 확인
- Chat ID가 DB에 등록되어 있는지 확인

### 2. 스케줄러 직접 실행

```bash
cd /Users/jjongz/PycharmProjects/finacneFee
source venv/bin/activate
python daily_updater.py
```

**예상 출력:**
```
======================================================================
📅 일일 스케줄러 시작
======================================================================
⏰ 스케줄:
   - 매일 08:00: 일봉 업데이트 + 놓친 알림
   - 매일 08:50: 매수 전략 분석 (월-금)
💡 Ctrl+C로 종료
======================================================================

🔧 스케줄 등록 중...
✅ 스케줄 등록 완료:
   - 다음 08:00 실행: 2025-12-03 08:00:00

🔍 시작 시 데이터 확인...
======================================================================
⏰ 아침 업데이트 시작: 2025-12-02 14:30:00
======================================================================
...

⏰ [14:30:00] 스케줄 대기 중... 다음 실행: 2025-12-03 08:00:00
⏰ [14:40:00] 스케줄 대기 중... 다음 실행: 2025-12-03 08:00:00
```

---

## 🐳 NAS Docker 로그 확인

### 1. SSH 접속

```bash
ssh admin@192.168.1.136 -p 2848
```

### 2. 프로젝트 디렉토리 이동

```bash
cd /volume1/docker/stock-volatility-alert
```

### 3. 컨테이너 상태 확인

```bash
sudo docker-compose ps
```

**예상 출력 (정상):**
```
NAME                IMAGE                                      STATUS
stock-monitor       stock-volatility-alert_stock-monitor       Up 2 hours
```

**예상 출력 (오류):**
```
NAME                IMAGE                                      STATUS
stock-monitor       stock-volatility-alert_stock-monitor       Exited (1) 2 minutes ago
```

### 4. 실시간 로그 확인

```bash
sudo docker-compose logs -f stock-monitor
```

**Ctrl+C로 중지**

### 5. 최근 로그만 확인

```bash
sudo docker-compose logs --tail=100 stock-monitor
```

### 6. 특정 컴포넌트 로그 확인

```bash
# 스케줄러 로그
sudo docker exec stock_monitor cat /tmp/daily_updater.log

# 텔레그램 봇 로그
sudo docker exec stock_monitor cat /tmp/telegram_bot.log
```

---

## 🤖 텔레그램 봇 응답 없음

### 체크리스트

#### 1. 봇이 실행 중인가?

**로컬:**
```bash
ps aux | grep telegram_bot_commands
```

**NAS:**
```bash
sudo docker exec stock_monitor ps aux | grep telegram_bot_commands
```

**없으면:**
```bash
# 로컬
cd /Users/jjongz/PycharmProjects/finacneFee
source venv/bin/activate
python telegram_bot_commands.py

# NAS
sudo docker-compose restart
```

#### 2. Bot Token이 올바른가?

```bash
# DB에서 확인
sqlite3 data/stock_data.db "SELECT substr(value, 1, 20) FROM settings WHERE key='telegram_bot_token';"
```

**출력이 없거나 짧으면:**
```bash
python init_settings.py
```

#### 3. Chat ID가 등록되어 있는가?

```bash
sqlite3 data/stock_data.db "SELECT name, chat_id FROM users WHERE enabled=1;"
```

**출력:**
```
jjongz|6633793503
```

**없으면:**
```bash
sqlite3 data/stock_data.db "INSERT INTO users (name, chat_id, investment_amount, enabled) VALUES ('jjongz', '6633793503', 5000000, 1);"
```

#### 4. 로그에 오류가 있는가?

**NAS:**
```bash
sudo docker exec stock_monitor tail -50 /tmp/telegram_bot.log
```

**찾을 메시지:**
```
✅ 커맨드 핸들러 등록 완료
🔄 Polling 시작...
```

**오류가 있으면:**
```bash
sudo docker-compose down
sudo docker-compose build --no-cache
sudo docker-compose up -d
```

---

## ⏰ 8:50 알림이 안옴

### 체크리스트

#### 1. 스케줄러가 실행 중인가?

**로컬:**
```bash
ps aux | grep daily_updater
```

**NAS:**
```bash
sudo docker exec stock_monitor ps aux | grep daily_updater
```

**없으면 재시작**

#### 2. 스케줄이 등록되어 있는가?

**NAS 로그 확인:**
```bash
sudo docker exec stock_monitor tail -100 /tmp/daily_updater.log
```

**찾을 메시지:**
```
✅ 스케줄 등록 완료:
   - 다음 08:00 실행: 2025-12-03 08:00:00
```

**없으면:** 스케줄러가 시작되지 않은 것

#### 3. 현재 시간이 맞는가?

**NAS 시간 확인:**
```bash
sudo docker exec stock_monitor date
```

**출력:**
```
Tue Dec  2 14:30:00 KST 2025
```

**시간이 틀리면:**
```yaml
# docker-compose.yml
environment:
  - TZ=Asia/Seoul
```

#### 4. 사용자가 활성화되어 있는가?

```bash
sqlite3 data/stock_data.db "SELECT name, enabled FROM users;"
```

**enabled=0이면:**
```bash
sqlite3 data/stock_data.db "UPDATE users SET enabled=1 WHERE name='jjongz';"
```

#### 5. 수동으로 테스트

**텔레그램에서:**
```
/morning
```

**로그 확인:**
```bash
sudo docker exec stock_monitor tail -f /tmp/telegram_bot.log
```

**예상 출력:**
```
📥 /morning 명령 수신 - Chat ID: 6633793503
📊 분석 중... 잠시만 기다려주세요!
...
✅ 분석 완료! 차트를 확인하세요.
```

---

## 🔧 시간 제한 임시 해제

알림이 08:00~24:00에만 전송되는데, 테스트를 위해 **24시간 활성화**할 수 있습니다.

### 로컬

```bash
export DEBUG_MODE=true
python realtime_monitor_hybrid.py
```

**출력:**
```
🔧 DEBUG MODE: 24시간 알림 활성화
...
⏰ 알림 시간: 24시간 (DEBUG_MODE)
```

### NAS Docker

#### 1. docker-compose.yml 수정

```bash
cd /volume1/docker/stock-volatility-alert
nano docker-compose.yml
```

#### 2. 환경 변수 변경

```yaml
environment:
  - TZ=Asia/Seoul
  - PYTHONUNBUFFERED=1
  - DEBUG_MODE=true  # false → true로 변경
```

#### 3. 재시작

```bash
sudo docker-compose down
sudo docker-compose up -d
```

#### 4. 로그 확인

```bash
sudo docker-compose logs stock-monitor | grep DEBUG
```

**출력:**
```
🔧 DEBUG_MODE: true
🔧 DEBUG MODE: 24시간 알림 활성화
```

---

## 🔍 빠른 문제 진단

### 1분 진단 스크립트

**NAS에서 실행:**
```bash
#!/bin/bash
cd /volume1/docker/stock-volatility-alert

echo "=== 컨테이너 상태 ==="
sudo docker-compose ps

echo ""
echo "=== 실행 중인 프로세스 ==="
sudo docker exec stock_monitor ps aux | grep -E "python|PID"

echo ""
echo "=== 스케줄러 로그 (최근 10줄) ==="
sudo docker exec stock_monitor tail -10 /tmp/daily_updater.log 2>/dev/null || echo "로그 없음"

echo ""
echo "=== 봇 로그 (최근 10줄) ==="
sudo docker exec stock_monitor tail -10 /tmp/telegram_bot.log 2>/dev/null || echo "로그 없음"

echo ""
echo "=== 사용자 상태 ==="
sudo docker exec stock_monitor sqlite3 data/stock_data.db "SELECT name, chat_id, enabled FROM users;"

echo ""
echo "=== Bot Token 확인 ==="
sudo docker exec stock_monitor sqlite3 data/stock_data.db "SELECT substr(value, 1, 20) || '...' FROM settings WHERE key='telegram_bot_token';"
```

---

## 🆘 그래도 안되면

### 완전 초기화

```bash
cd /volume1/docker/stock-volatility-alert

# 1. 컨테이너 중지 및 삭제
sudo docker-compose down

# 2. 최신 코드 받기
git pull

# 3. 이미지 완전 재빌드
sudo docker-compose build --no-cache

# 4. 재시작
sudo docker-compose up -d

# 5. 로그 확인
sudo docker-compose logs -f stock-monitor
```

### 로그 전체 보기

```bash
sudo docker-compose logs --tail=500 stock-monitor > debug.log
cat debug.log
```

---

## 📞 추가 도움

문제가 계속되면 다음 정보를 함께 공유해주세요:

1. **컨테이너 상태:**
   ```bash
   sudo docker-compose ps
   ```

2. **전체 로그:**
   ```bash
   sudo docker-compose logs --tail=100 stock-monitor
   ```

3. **DB 상태:**
   ```bash
   sudo docker exec stock_monitor sqlite3 data/stock_data.db "
   SELECT 'users:', COUNT(*) FROM users;
   SELECT 'stocks:', COUNT(*) FROM daily_prices;
   SELECT 'watchlist:', COUNT(*) FROM user_watchlist;
   "
   ```

4. **현재 시간:**
   ```bash
   sudo docker exec stock_monitor date
   ```

