# 🔧 시놀로지 Git Server 설정 가이드

**로컬 프로젝트를 시놀로지 NAS Git Server로 관리하기**

---

## 📋 환경 정보

```
시놀로지 NAS IP: 192.168.1.136
SSH 포트: 2848
사용자: admin (DSM 관리자)
```

---

## 🚀 1단계: 시놀로지 Git Server 설정

### A. DSM에서 Git Server 폴더 생성

#### 방법 1: DSM File Station (권장)
1. **File Station** 열기
2. `/volume1/` 이동
3. **새 폴더** → 이름: `git`
4. `git` 폴더 안에 **새 폴더** → 이름: `stock_monitor.git`

#### 방법 2: SSH로 생성
```bash
ssh admin@192.168.1.136 -p 2848

# Git 저장소 디렉토리 생성
sudo mkdir -p /volume1/git/stock_monitor.git
cd /volume1/git/stock_monitor.git

# Bare 리포지토리 초기화
sudo git init --bare

# 권한 설정
sudo chown -R admin:users /volume1/git/stock_monitor.git
```

---

## 📤 2단계: 로컬 프로젝트 Git 설정

### A. Git 초기화 (로컬)

```bash
cd /Users/jjongz/PycharmProjects/finacneFee

# Git 저장소 초기화 (아직 안 했으면)
git init

# 사용자 정보 설정
git config user.name "jjongz"
git config user.email "your@email.com"
```

### B. .gitignore 생성

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# DB (로컬 개발용)
stock_data.db

# 로그
*.log
monitor.log*

# 백업
backup/

# 이미지 (차트는 제외, 생성되는 파일)
*_volatility.png
*_backtest.png

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# 테스트
test_*.py

# 터미널
terminals/

# 개인 설정 (중요!)
config.py
EOF
```

**중요!** `config.py`는 텔레그램 토큰이 있으므로 Git에 올리지 않습니다!

### C. config.py.example 생성

```bash
# config.py 템플릿 생성
cat > config.py.example << 'EOF'
"""
설정 파일 템플릿
config.py로 복사 후 실제 값으로 변경하세요
"""

TELEGRAM_CONFIG = {
    'BOT_TOKEN': 'YOUR_BOT_TOKEN_HERE',
    'CHAT_ID': 'YOUR_CHAT_ID_HERE',
}

INVESTMENT_CONFIG = {
    'default_amount': 1000000,  # 기본 투자 금액 (원)
}
EOF
```

---

## 🔗 3단계: 시놀로지 Git Server 연결

### A. Remote 추가

```bash
cd /Users/jjongz/PycharmProjects/finacneFee

# 시놀로지 Git Server를 remote로 추가
git remote add synology ssh://admin@192.168.1.136:2848/volume1/git/stock_monitor.git

# 확인
git remote -v
```

**출력:**
```
synology    ssh://admin@192.168.1.136:2848/volume1/git/stock_monitor.git (fetch)
synology    ssh://admin@192.168.1.136:2848/volume1/git/stock_monitor.git (push)
```

### B. SSH 키 설정 (비밀번호 없이 접속)

```bash
# SSH 키 생성 (없으면)
ssh-keygen -t rsa -b 4096 -C "your@email.com"
# Enter 3번 (기본값 사용)

# 공개키 복사
cat ~/.ssh/id_rsa.pub
```

**시놀로지에 공개키 등록:**
```bash
# SSH로 시놀로지 접속
ssh admin@192.168.1.136 -p 2848

# .ssh 디렉토리 생성 (없으면)
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# authorized_keys 파일에 공개키 추가
nano ~/.ssh/authorized_keys
# 위에서 복사한 공개키 붙여넣기
# Ctrl+O, Enter, Ctrl+X

# 권한 설정
chmod 600 ~/.ssh/authorized_keys
```

**테스트:**
```bash
# 비밀번호 없이 접속되면 성공!
ssh admin@192.168.1.136 -p 2848
```

---

## 📦 4단계: 첫 Push

### A. 파일 추가 및 커밋

```bash
cd /Users/jjongz/PycharmProjects/finacneFee

# 모든 파일 추가 (.gitignore 제외)
git add .

# 상태 확인
git status

# 커밋
git commit -m "Initial commit: Stock monitoring system with multi-user support"
```

### B. Push to Synology

```bash
# main 브랜치로 push
git push -u synology main

# 또는 master 브랜치
git push -u synology master
```

**출력:**
```
Enumerating objects: 50, done.
Counting objects: 100% (50/50), done.
Delta compression using up to 8 threads
Compressing objects: 100% (45/45), done.
Writing objects: 100% (50/50), 150.00 KiB | 5.00 MiB/s, done.
Total 50 (delta 10), reused 0 (delta 0)
To ssh://192.168.1.136:2848/volume1/git/stock_monitor.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'synology'.
```

---

## 🐳 5단계: 시놀로지에서 Clone 및 Docker 실행

### A. SSH 접속

```bash
ssh admin@192.168.1.136 -p 2848
```

### B. Docker 디렉토리에 Clone

```bash
# Docker 작업 디렉토리
cd /volume1/docker

# Git에서 Clone
git clone /volume1/git/stock_monitor.git
cd stock_monitor

# config.py 생성 (템플릿에서)
cp config.py.example config.py
nano config.py
# 실제 토큰과 Chat ID 입력
```

### C. 초기 데이터 로드

```bash
# 임시 컨테이너로 DB 초기화
docker run -it --rm \
  -v $(pwd):/app \
  -w /app \
  python:3.11-slim \
  bash -c "pip install -r requirements.txt && python data_collector.py init"

# 사용자 설정
docker run -it --rm \
  -v $(pwd):/app \
  -w /app \
  python:3.11-slim \
  bash -c "pip install -r requirements.txt && python user_manager.py family"
```

### D. Docker 실행

```bash
# Docker 이미지 빌드 및 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

---

## 🔄 6단계: 개발 워크플로우

### 로컬에서 개발

```bash
cd /Users/jjongz/PycharmProjects/finacneFee

# 코드 수정
nano scheduler_config.py

# 변경사항 확인
git status
git diff

# 커밋
git add scheduler_config.py
git commit -m "Update watchlist configuration"

# 시놀로지로 Push
git push synology main
```

### 시놀로지에서 업데이트

```bash
ssh admin@192.168.1.136 -p 2848
cd /volume1/docker/stock_monitor

# 최신 코드 받기
git pull origin main

# Docker 재빌드
docker-compose up -d --build

# 로그 확인
docker-compose logs -f
```

---

## 🌐 7단계: GitHub 연동 (선택사항)

### 백업 및 공유를 위해 GitHub도 추가

```bash
cd /Users/jjongz/PycharmProjects/finacneFee

# GitHub private repository 생성 후
git remote add github https://github.com/YOUR_USERNAME/stock-monitor.git

# 두 곳에 모두 push
git push synology main
git push github main

# 확인
git remote -v
```

**출력:**
```
synology    ssh://admin@192.168.1.136:2848/volume1/git/stock_monitor.git (fetch)
synology    ssh://admin@192.168.1.136:2848/volume1/git/stock_monitor.git (push)
github      https://github.com/YOUR_USERNAME/stock-monitor.git (fetch)
github      https://github.com/YOUR_USERNAME/stock-monitor.git (push)
```

---

## 🔧 유용한 Git 명령어

### 일상적인 작업

```bash
# 상태 확인
git status

# 변경사항 확인
git diff

# 커밋 이력
git log --oneline

# 특정 파일만 커밋
git add config.py.example
git commit -m "Update config template"
git push synology main

# 모든 변경사항 커밋
git add .
git commit -m "Update multiple files"
git push synology main
```

### 브랜치 작업

```bash
# 새 기능 개발
git checkout -b feature/new-stock-alert
# 작업...
git commit -am "Add new stock alert feature"
git push synology feature/new-stock-alert

# main 브랜치로 돌아가기
git checkout main

# 브랜치 병합
git merge feature/new-stock-alert
git push synology main
```

### 롤백

```bash
# 마지막 커밋 취소 (변경사항 유지)
git reset --soft HEAD~1

# 특정 파일 이전 버전으로
git checkout HEAD~1 -- scheduler_config.py

# 특정 커밋으로 되돌리기
git log --oneline  # 커밋 ID 확인
git reset --hard COMMIT_ID
git push synology main -f  # 강제 push (주의!)
```

---

## 📊 시놀로지 Git Server 장점

### vs GitHub

| 항목 | GitHub | 시놀로지 Git |
|------|--------|-------------|
| 속도 | 인터넷 의존 | **로컬 네트워크 (초고속)** ✅ |
| 프라이버시 | Public/Private | **완전 프라이빗** ✅ |
| 용량 제한 | 100MB/file | **무제한** ✅ |
| 비용 | Private는 유료 | **무료** ✅ |
| 백업 | GitHub 서버 | **내 NAS** ✅ |
| 접근 | 인터넷 필요 | 집에서만 |

**결론: 둘 다 사용! (시놀로지: 메인, GitHub: 백업)**

---

## 🔐 보안 팁

### 1. config.py 관리

```bash
# config.py는 절대 Git에 올리지 않기!
# .gitignore에 이미 포함됨

# 대신 config.py.example 사용
cp config.py.example config.py
nano config.py  # 실제 값 입력
```

### 2. .env 파일 사용 (선택)

```bash
# .env 파일로 민감한 정보 관리
cat > .env << 'EOF'
BOT_TOKEN=8105040252:AAHXbWn0FV3ymw9PTzlbPMyIC6JoehY-3pM
CHAT_ID=6633793503
EOF

# .gitignore에 추가
echo ".env" >> .gitignore
```

### 3. Git Hooks (선택)

```bash
# .git/hooks/pre-commit 생성
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# config.py가 커밋되려고 하면 차단
if git diff --cached --name-only | grep -q "^config.py$"; then
    echo "Error: config.py should not be committed!"
    exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

---

## 🎯 자동화 스크립트

### 빠른 배포 스크립트

```bash
# deploy.sh 생성
cat > deploy.sh << 'EOF'
#!/bin/bash

echo "🚀 Deploying to Synology..."

# 1. 로컬 커밋
git add .
git commit -m "Auto deploy: $(date '+%Y-%m-%d %H:%M:%S')"

# 2. Push
git push synology main

# 3. 시놀로지에서 업데이트
ssh admin@192.168.1.136 -p 2848 << 'ENDSSH'
cd /volume1/docker/stock_monitor
git pull origin main
docker-compose up -d --build
ENDSSH

echo "✅ Deployment complete!"
EOF

chmod +x deploy.sh

# 사용
./deploy.sh
```

---

## 🐛 문제 해결

### Q1. Permission denied (publickey)
```bash
# SSH 키가 제대로 등록되지 않음
# 시놀로지에 공개키 다시 등록
cat ~/.ssh/id_rsa.pub
# 복사 후 시놀로지 ~/.ssh/authorized_keys에 추가
```

### Q2. fatal: Could not read from remote repository
```bash
# Git 저장소 경로 확인
ssh admin@192.168.1.136 -p 2848
ls -la /volume1/git/stock_monitor.git

# 권한 확인
sudo chown -R admin:users /volume1/git/stock_monitor.git
```

### Q3. Push rejected
```bash
# 강제 push (주의!)
git push synology main -f

# 또는 pull 후 merge
git pull synology main
git push synology main
```

---

## 📚 추가 리소스

### Git 학습
- [Pro Git Book (한글)](https://git-scm.com/book/ko/v2)
- [Git 치트시트](https://education.github.com/git-cheat-sheet-education.pdf)

### 시놀로지 Git Server
- [시놀로지 Git Server 가이드](https://www.synology.com/en-global/knowledgebase/DSM/help/Git)

---

## 🎉 완료!

### 이제 가능한 것:

✅ **로컬 개발** - Mac에서 코드 작성  
✅ **버전 관리** - Git으로 추적  
✅ **시놀로지 백업** - NAS에 자동 저장  
✅ **자동 배포** - Push → Docker 재빌드  
✅ **GitHub 백업** - 클라우드 백업 (선택)  

---

**이제 전문가처럼 개발하세요!** 🚀💻🎉

