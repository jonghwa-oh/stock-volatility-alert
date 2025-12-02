# 🐳 NAS Docker 완전 재빌드 가이드

## 문제 상황
`/test`는 응답하지만 `/morning`은 응답 없음
→ **오래된 test_bot.py가 실행 중**

## 해결 방법: 완전 재빌드

### 1. SSH 접속
```bash
ssh admin@192.168.1.136 -p 2848
```

### 2. 프로젝트 디렉토리로 이동
```bash
cd /volume1/docker/stock-volatility-alert
```

### 3. 컨테이너 완전 중지 및 삭제
```bash
sudo docker-compose down
```

### 4. 오래된 이미지 삭제
```bash
sudo docker images | grep stock
```

**출력 예시:**
```
stock-volatility-alert_stock-monitor   latest   abc123def456   2 hours ago   500MB
```

**이미지 ID를 복사한 후 삭제:**
```bash
sudo docker rmi abc123def456
```

또는 강제 삭제:
```bash
sudo docker rmi -f abc123def456
```

### 5. 최신 코드 받기
```bash
git fetch --all
git reset --hard origin/main
git pull
```

**확인:**
```bash
ls -la test_bot.py
```

**출력:**
```
ls: cannot access 'test_bot.py': No such file or directory  ← 이게 정상!
```

**telegram_bot_commands.py 확인:**
```bash
ls -la telegram_bot_commands.py
```

**출력:**
```
-rw-r--r-- 1 admin users 12345 Dec  1 12:00 telegram_bot_commands.py  ← 있어야 함!
```

### 6. start.sh 내용 확인
```bash
grep "telegram_bot_commands.py" start.sh
```

**출력:**
```
python telegram_bot_commands.py &  ← 이 줄이 있어야 함!
```

### 7. Docker 이미지 새로 빌드
```bash
sudo docker-compose build --no-cache
```

**`--no-cache`**: 캐시 없이 완전히 새로 빌드

**예상 시간:** 5~10분

### 8. 컨테이너 시작
```bash
sudo docker-compose up -d
```

### 9. 로그 실시간 확인
```bash
sudo docker-compose logs -f stock-monitor
```

**확인할 내용:**
```
🤖 텔레그램 봇 커맨드 핸들러 시작...  ← 이 메시지가 보여야 함!
   PID: 124

✅ Bot Token: ************
✅ 커맨드 핸들러 등록 완료:
   - /start: 봇 시작
   - /help: 도움말
   - /list: 종목 목록
   - /add: 종목 추가
   - /remove: 종목 삭제
   - /morning: 아침 알림       ← 이게 보여야 함!
   - /status: 현재가 확인

🚀 봇 시작... (Ctrl+C로 종료)
```

**Ctrl+C**를 눌러 로그 확인 종료

### 10. 텔레그램에서 테스트

#### A. /test 명령어 (없어야 정상!)
```
/test
```

**예상 응답:**
```
죄송합니다. 알 수 없는 명령어입니다.
/help를 입력하여 사용 가능한 명령어를 확인하세요.
```

또는 **아무 응답 없음** (이게 정상!)

#### B. /morning 명령어 (작동해야 함!)
```
/morning
```

**예상 응답:**
```
📊 분석 중... 잠시만 기다려주세요!

(10초~1분 후)

📊 SOXL - Direxion...
(차트 이미지)

✅ 분석 완료! 차트를 확인하세요.
```

#### C. /list 명령어
```
/list
```

**예상 응답:**
```
📊 jjongz님의 관심 종목

투자금액: 1,000,000원
...
```

---

## 🔍 여전히 안 되면?

### 프로세스 확인
```bash
sudo docker-compose exec stock-monitor ps aux | grep python
```

**정상 출력:**
```
root  123  python daily_updater.py
root  124  python telegram_bot_commands.py    ← 이게 있어야 함!
root  125  python realtime_monitor_hybrid.py
```

**test_bot.py가 보이면 안됨!**

### 컨테이너 내부 확인
```bash
sudo docker-compose exec stock-monitor ls -la *.py | grep bot
```

**출력:**
```
-rw-r--r-- 1 root root 12345 Dec  1 12:00 telegram_bot_commands.py
```

**test_bot.py가 보이면 안됨!**

### 완전 초기화 (최후의 수단)
```bash
# 모든 컨테이너 중지
sudo docker-compose down

# 볼륨까지 모두 삭제 (주의: 데이터 손실!)
sudo docker-compose down -v

# 이미지 삭제
sudo docker rmi -f $(sudo docker images -q stock-volatility-alert*)

# 완전 재빌드
sudo docker-compose build --no-cache
sudo docker-compose up -d
```

---

## ✅ 성공 확인 체크리스트

- [ ] `test_bot.py` 파일이 없음
- [ ] `telegram_bot_commands.py` 파일이 있음
- [ ] Docker 로그에 "🤖 텔레그램 봇 커맨드 핸들러 시작..." 메시지 보임
- [ ] `/test` 명령어에 응답 없음 또는 "알 수 없는 명령어"
- [ ] `/morning` 명령어에 정상 응답
- [ ] `/list` 명령어에 정상 응답

---

## 📝 요약

**문제:**
- 오래된 `test_bot.py`가 Docker 이미지에 포함되어 실행 중
- Git에서는 삭제되었지만, Docker 이미지는 업데이트 안됨

**해결:**
1. 컨테이너 완전 중지 (`docker-compose down`)
2. 이미지 삭제 (`docker rmi`)
3. 코드 강제 업데이트 (`git reset --hard`)
4. 캐시 없이 재빌드 (`docker-compose build --no-cache`)
5. 재시작 및 확인

**핵심:**
- `--no-cache`를 사용해서 완전히 새로 빌드!
- `test_bot.py`가 없어야 함!
- `telegram_bot_commands.py`가 실행되어야 함!

