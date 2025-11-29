# 📤 GitHub Push 가이드

## 🔐 안전하게 Public으로 Push!

이제 프로젝트가 **암호화 시스템**으로 완전히 보호됩니다!

### ✅ 보안 확인

```bash
# Git에 추가되지 않은 민감한 파일들 확인
git status --ignored
```

**제외된 파일:**
- ✅ `.env` (마스터 키)
- ✅ `secrets.db` (암호화된 설정)
- ✅ `stock_data.db` (주식 데이터)
- ✅ `*.png` (차트 이미지)

---

## 🚀 GitHub에 Push하기

### 1. GitHub 저장소 생성

1. https://github.com 접속
2. 우측 상단 `+` → `New repository` 클릭
3. 저장소 정보 입력:
   - **Repository name**: `stock-monitor` (또는 원하는 이름)
   - **Description**: `AI 기반 주식 변동성 알림 시스템`
   - **Visibility**: **Public** ✅ (안전합니다!)
   - ⚠️ **초기화 옵션 체크하지 마세요** (README, .gitignore 등)
4. `Create repository` 클릭

### 2. 원격 저장소 연결

```bash
cd /Users/jjongz/PycharmProjects/finacneFee

# 원격 저장소 추가 (YOUR_USERNAME을 실제 GitHub 사용자명으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/stock-monitor.git

# 원격 저장소 확인
git remote -v
```

### 3. Push!

```bash
# main 브랜치로 push
git push -u origin main
```

**인증 방법:**
- **Personal Access Token 사용** (권장)
  1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  2. `Generate new token (classic)` 클릭
  3. `repo` 권한 체크
  4. 생성된 토큰을 비밀번호로 사용

---

## 🏠 시놀로지 NAS에서 Clone

```bash
# SSH 접속
ssh -p 2848 jjongz@192.168.1.136

# 프로젝트 디렉토리로 이동
cd /volume1/docker

# GitHub에서 Clone
git clone https://github.com/YOUR_USERNAME/stock-monitor.git
cd stock-monitor

# 초기 설정
python3 setup_secrets.py

# Docker 실행
docker-compose up -d
```

---

## 🔄 이후 업데이트 방법

### 회사 노트북에서 수정 후 Push

```bash
cd /Users/jjongz/PycharmProjects/finacneFee

# 변경사항 확인
git status

# 변경사항 추가 및 커밋
git add .
git commit -m "feat: 새로운 기능 추가"

# Push
git push origin main
```

### 시놀로지에서 Pull

```bash
ssh -p 2848 jjongz@192.168.1.136

cd /volume1/docker/stock-monitor

# 최신 코드 받기
git pull origin main

# Docker 재시작
docker-compose restart
```

---

## 📊 프로젝트 상태

### 커밋 내역 확인

```bash
git log --oneline --graph
```

### 브랜치 확인

```bash
git branch -a
```

### 변경사항 확인

```bash
git diff
```

---

## ⚠️ 주의사항

### 절대 Push하면 안 되는 파일

이미 `.gitignore`에 포함되어 있지만, 혹시 모르니 확인:

```bash
# 민감한 파일 확인
ls -la | grep -E '(\.env|secrets\.db)'
```

만약 실수로 추가되었다면:

```bash
# Git에서 제거 (파일은 유지)
git rm --cached .env
git rm --cached secrets.db

# 커밋 및 Push
git commit -m "remove sensitive files"
git push origin main
```

### GitHub Public 장점

✅ **포트폴리오로 활용**
- 다른 사람에게 보여줄 수 있음
- 취업/이직 시 활용

✅ **협업 가능**
- 가족/친구와 함께 사용
- 이슈/PR로 기능 개선

✅ **백업**
- 코드가 GitHub에 안전하게 보관
- 언제 어디서나 Clone 가능

✅ **버전 관리**
- 코드 변경 이력 추적
- 문제 발생 시 이전 버전으로 되돌리기

---

## 🎯 다음 단계

1. ✅ **GitHub에 Push 완료**
2. 📱 **README.md에 GitHub 주소 추가**
3. 🏠 **시놀로지 NAS에 Clone**
4. 🔐 **시놀로지에서 setup_secrets.py 실행**
5. 🚀 **Docker로 실행**

---

## 📝 README 업데이트 예시

GitHub 저장소가 생성되면 `README.md`에 다음 추가:

```markdown
## 📦 설치

git clone https://github.com/YOUR_USERNAME/stock-monitor.git
cd stock-monitor
python setup_secrets.py
```

---

## 🆘 문제 해결

### Push 권한 오류

```bash
# Personal Access Token 재생성
# GitHub → Settings → Developer settings → Personal access tokens
```

### Twingate로 인한 접근 불가

- ✅ GitHub를 사용하면 해결!
- 회사 노트북 → GitHub (O)
- GitHub → 시놀로지 (O)

---

**🎉 축하합니다! 이제 어디서든 안전하게 개발할 수 있습니다!**

