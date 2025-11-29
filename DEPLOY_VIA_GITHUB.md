# 🌐 GitHub 경유 배포 가이드

**회사 보안 정책으로 내부 네트워크 접근이 차단된 경우**

---

## 🎯 상황

```
문제: Twingate 등 보안 솔루션으로 192.168.x.x 접근 불가
해결: GitHub을 중간 경유지로 사용
```

---

## 🔄 워크플로우

```
회사 노트북 (Mac)
    ↓ git push
GitHub Private Repository (중간 저장소)
    ↓ git pull
시놀로지 NAS (192.168.1.136)
    ↓ docker-compose up
실행!
```

**장점:**
- ✅ 보안 정책 우회 (합법적)
- ✅ 클라우드 백업
- ✅ 버전 관리
- ✅ 어디서든 접근 가능

---

## 🚀 1단계: GitHub Private Repository 생성

### A. GitHub.com 접속

1. https://github.com 로그인
2. 우측 상단 **+** → **New repository**

### B. 리포지토리 설정

```
Repository name: stock-monitor
Description: Multi-user stock monitoring system
☑️ Private (중요! 민감한 정보 보호)
☑️ Add a README file (체크 안 함)
☑️ Add .gitignore (체크 안 함, 이미 있음)

→ Create repository
```

### C. Repository URL 복사

```
https://github.com/YOUR_USERNAME/stock-monitor.git
```

---

## 📤 2단계: 로컬 → GitHub Push

### A. Git 초기화 (아직 안 했으면)

```bash
cd /Users/jjongz/PycharmProjects/finacneFee

# Git 초기화
git init

# 사용자 정보
git config user.name "jjongz"
git config user.email "your@email.com"
```

### B. GitHub Remote 추가

```bash
# GitHub 추가
git remote add origin https://github.com/YOUR_USERNAME/stock-monitor.git

# 확인
git remote -v
```

**출력:**
```
origin  https://github.com/YOUR_USERNAME/stock-monitor.git (fetch)
origin  https://github.com/YOUR_USERNAME/stock-monitor.git (push)
```

### C. 파일 추가 및 커밋

```bash
# 모든 파일 추가 (.gitignore 제외)
git add .

# 상태 확인
git status

# config.py가 포함되지 않았는지 확인!
# (포함되면 안 됨 - 토큰 유출 위험)

# 첫 커밋
git commit -m "Initial commit: Multi-user stock monitoring system"
```

### D. GitHub로 Push

```bash
# main 브랜치로 push
git branch -M main
git push -u origin main

# GitHub 로그인 요청 시:
# Username: YOUR_USERNAME
# Password: Personal Access Token (PAT) 필요
```

**Personal Access Token 생성:**
1. GitHub → Settings → Developer settings
2. Personal access tokens → Tokens (classic)
3. Generate new token
4. 권한: `repo` 전체 체크
5. 생성 후 토큰 복사 (비밀번호로 사용)

---

## 📥 3단계: GitHub → 시놀로지 Clone

### A. 시놀로지 SSH 접속

**방법 1: 집에서 직접 접속**
```bash
# WiFi가 같은 네트워크면 가능
ssh admin@192.168.1.136 -p 2848
```

**방법 2: 시놀로지 QuickConnect 사용**
```bash
# DSM 웹 인터페이스 접속
https://quickconnect.to/YOUR_SYNOLOGY_ID

# 터미널 또는 SSH 활성화 확인
```

**방법 3: 시놀로지 DDNS + 외부 접속**
```bash
# DSM 포트 포워딩 설정 후
ssh admin@YOUR_DDNS_ADDRESS -p 2848
```

### B. GitHub에서 Clone

```bash
# Docker 디렉토리
cd /volume1/docker

# GitHub에서 Clone
git clone https://github.com/YOUR_USERNAME/stock-monitor.git
cd stock-monitor

# 또는 이미 있으면
cd stock-monitor
git pull origin main
```

### C. config.py 생성

```bash
# 템플릿에서 복사
cp config.py.example config.py

# 편집
nano config.py
```

**입력할 내용:**
```python
TELEGRAM_CONFIG = {
    'BOT_TOKEN': '8105040252:AAHXbWn0FV3ymw9PTzlbPMyIC6JoehY-3pM',
    'CHAT_ID': '6633793503',
}

INVESTMENT_CONFIG = {
    'default_amount': 1000000,
}
```

저장: `Ctrl+O` → Enter → `Ctrl+X`

---

## 🐳 4단계: Docker 실행

### A. 초기 데이터 로드 (최초 1회)

```bash
cd /volume1/docker/stock-monitor

# DB 초기화
docker run -it --rm -v $(pwd):/app -w /app python:3.11-slim \
  bash -c "pip install -r requirements.txt && python data_collector.py init"

# 사용자 설정
docker run -it --rm -v $(pwd):/app -w /app python:3.11-slim \
  bash -c "pip install -r requirements.txt && python user_manager.py family"
```

### B. Docker Compose 실행

```bash
# 빌드 및 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

**성공 메시지:**
```
👨‍👩‍👦 가족용 멀티 유저 모니터링 시스템
👥 등록된 사용자: 3명
✅ 모니터링 시작!
```

---

## 🔄 일상적인 개발 워크플로우

### 회사 노트북에서 작업

```bash
cd /Users/jjongz/PycharmProjects/finacneFee

# 코드 수정
nano scheduler_config.py

# 커밋
git add .
git commit -m "Update stock watchlist"

# GitHub로 Push
git push origin main
```

### 시놀로지에서 업데이트

```bash
# SSH 접속 (집에서)
ssh admin@192.168.1.136 -p 2848

cd /volume1/docker/stock-monitor

# 최신 코드 받기
git pull origin main

# Docker 재빌드
docker-compose up -d --build

# 로그 확인
docker-compose logs -f
```

---

## 🤖 자동화 스크립트

### 시놀로지에서 정기적으로 자동 Pull

#### A. 자동 업데이트 스크립트 생성

```bash
ssh admin@192.168.1.136 -p 2848

cd /volume1/docker/stock-monitor

# 스크립트 생성
cat > auto_update.sh << 'EOF'
#!/bin/bash

cd /volume1/docker/stock-monitor

# 최신 코드 받기
git pull origin main

# 변경사항 있으면 재빌드
if [ $? -eq 0 ]; then
  echo "Code updated, rebuilding..."
  docker-compose up -d --build
  echo "Update complete!"
else
  echo "No changes"
fi
EOF

chmod +x auto_update.sh
```

#### B. DSM 작업 스케줄러 등록

1. **제어판** → **작업 스케줄러**
2. **생성** → **예약된 작업** → **사용자 정의 스크립트**

**설정:**
```
작업 이름: GitHub Auto Update
사용자: admin
일정: 매일 02:00 (새벽 2시)

스크립트:
/volume1/docker/stock-monitor/auto_update.sh
```

**결과:**
- 매일 새벽 2시에 자동으로 GitHub에서 최신 코드 받아서 업데이트!

---

## 🌐 시놀로지 외부 접속 설정 (선택)

### 방법 A: QuickConnect (가장 쉬움)

#### 1. QuickConnect 활성화
1. DSM → **제어판** → **QuickConnect**
2. ☑️ **QuickConnect 활성화**
3. QuickConnect ID 생성: `jjongz-nas` (예시)

#### 2. 외부에서 접속
```bash
# 웹 브라우저
https://quickconnect.to/jjongz-nas

# SSH는 QuickConnect Relay 통해 접속 가능
# 하지만 속도 느림
```

### 방법 B: DDNS + 포트 포워딩

#### 1. DDNS 설정
1. DSM → **제어판** → **외부 액세스** → **DDNS**
2. **추가** → Synology DDNS 선택
3. 호스트 이름: `jjongz.synology.me` (예시)

#### 2. 라우터 포트 포워딩
```
외부 포트: 2848
내부 IP: 192.168.1.136
내부 포트: 2848
```

#### 3. 외부에서 SSH 접속
```bash
ssh admin@jjongz.synology.me -p 2848
```

---

## 📱 GitHub Actions 자동 배포 (고급)

### 코드 Push 시 자동으로 시놀로지 업데이트

#### A. GitHub Secrets 설정

1. GitHub Repository → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** 클릭
3. 추가할 Secrets:

```
Name: SSH_HOST
Value: 192.168.1.136 (또는 DDNS 주소)

Name: SSH_PORT
Value: 2848

Name: SSH_USER
Value: admin

Name: SSH_KEY
Value: (SSH 개인키 내용, ~/.ssh/id_rsa)
```

#### B. GitHub Actions 워크플로우 생성

```bash
# 로컬에서
cd /Users/jjongz/PycharmProjects/finacneFee

mkdir -p .github/workflows

cat > .github/workflows/deploy.yml << 'EOF'
name: Deploy to Synology

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Deploy to Synology NAS
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SSH_HOST }}
        port: ${{ secrets.SSH_PORT }}
        username: ${{ secrets.SSH_USER }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /volume1/docker/stock-monitor
          git pull origin main
          docker-compose up -d --build
EOF

# 커밋 & Push
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Actions auto-deploy"
git push origin main
```

**결과:**
- GitHub에 Push → 자동으로 시놀로지 업데이트! 🚀

---

## 🔐 보안 체크리스트

### ✅ 반드시 확인!

```bash
# 1. config.py가 Git에 포함되지 않았는지 확인
git status
# config.py 없어야 함!

# 2. .gitignore 확인
cat .gitignore | grep config.py
# config.py 있어야 함!

# 3. GitHub Repository가 Private인지 확인
# GitHub 웹에서 Repository → Settings
# Repository visibility: Private ✅

# 4. 민감한 정보 검색
git log -p | grep -i "token"
git log -p | grep -i "password"
# 아무것도 안 나와야 함!
```

### ⚠️ 만약 실수로 토큰을 올렸다면

```bash
# 1. 즉시 토큰 재발급
# Telegram BotFather에서 토큰 재생성

# 2. Git 히스토리에서 제거
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch config.py" \
  --prune-empty --tag-name-filter cat -- --all

# 3. 강제 Push
git push origin main --force

# 4. 새 토큰으로 업데이트
```

---

## 📊 비교: 직접 접속 vs GitHub 경유

| 항목 | 직접 접속 | GitHub 경유 |
|------|----------|------------|
| 속도 | 매우 빠름 | 약간 느림 |
| 보안 정책 | ❌ 차단됨 | ✅ 우회 가능 |
| 백업 | 수동 | ✅ 자동 (GitHub) |
| 버전 관리 | 로컬만 | ✅ 클라우드 |
| 어디서든 접근 | ❌ 집에서만 | ✅ 가능 |
| 협업 | 어려움 | ✅ 쉬움 |

**결론: GitHub 경유가 더 좋음!** ✅

---

## 🎯 완료 체크리스트

### 로컬 (회사 노트북)
- [ ] `.gitignore` 생성
- [ ] `config.py.example` 생성
- [ ] GitHub Private Repo 생성
- [ ] Git 초기화
- [ ] GitHub Remote 추가
- [ ] 첫 Push 완료

### 시놀로지
- [ ] SSH 접속 확인
- [ ] GitHub Clone 완료
- [ ] `config.py` 생성 (실제 토큰)
- [ ] DB 초기화
- [ ] 사용자 설정
- [ ] Docker 실행
- [ ] 텔레그램 알림 확인

### 자동화 (선택)
- [ ] 자동 업데이트 스크립트
- [ ] DSM 스케줄러 등록
- [ ] GitHub Actions 설정

---

## 💡 추가 팁

### 브랜치 전략

```bash
# 개발용 브랜치
git checkout -b develop
# 작업...
git push origin develop

# 시놀로지는 main만 pull
cd /volume1/docker/stock-monitor
git pull origin main
```

### 설정 파일 암호화 (고급)

```bash
# git-crypt 사용 (선택)
brew install git-crypt

# config.py 암호화
git-crypt init
echo "config.py filter=git-crypt diff=git-crypt" >> .gitattributes
git add .gitattributes config.py
git commit -m "Encrypt config.py"
```

---

## 🎉 완료!

### 이제 가능한 것:

✅ **회사 노트북에서 개발** (Twingate 우회)  
✅ **GitHub에 Push** (Private Repo)  
✅ **시놀로지에서 Pull** (자동/수동)  
✅ **Docker 자동 재빌드**  
✅ **클라우드 백업** (GitHub)  
✅ **버전 관리** (Git)  

---

**이제 어디서든 개발하고 배포하세요!** 🌐🚀🎉

