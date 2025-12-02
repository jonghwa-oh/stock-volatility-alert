# 🔒 Git 히스토리에서 민감한 정보 완전 삭제 가이드

## ⚠️ 주의사항

**이 작업은 Git 히스토리를 다시 작성합니다!**
- 이미 Push한 경우, force push가 필요합니다.
- 다른 사람이 clone한 경우, 재clone이 필요합니다.

---

## 🛠️ 방법 1: BFG Repo-Cleaner (권장)

### 1. BFG 다운로드

```bash
# Homebrew로 설치
brew install bfg

# 또는 직접 다운로드
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar
```

### 2. 민감한 정보 리스트 작성

```bash
cd /Users/jjongz/PycharmProjects/finacneFee

# secrets.txt 파일 생성
cat > secrets.txt <<EOF
8105040252:AAHXbWn0FV3ymw9PTzlbPMyIC6JoehY-3pM
6633793503
798920
EOF
```

### 3. BFG 실행

```bash
# Homebrew 설치한 경우
bfg --replace-text secrets.txt

# JAR 파일 사용하는 경우
java -jar bfg-1.14.0.jar --replace-text secrets.txt
```

### 4. Git 히스토리 정리

```bash
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### 5. GitHub에 Force Push

```bash
git push --force origin main
```

---

## 🛠️ 방법 2: git filter-branch (수동)

### 1. 특정 파일 완전 삭제

```bash
cd /Users/jjongz/PycharmProjects/finacneFee

# docs/NEXT_STEPS.md의 모든 히스토리 삭제
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch docs/NEXT_STEPS.md" \
  --prune-empty --tag-name-filter cat -- --all
```

### 2. 특정 텍스트 치환

```bash
# Bot Token 치환
git filter-branch --force --tree-filter \
  'find . -type f -exec sed -i "" "s/8105040252:AAHXbWn0FV3ymw9PTzlbPMyIC6JoehY-3pM/[REDACTED_BOT_TOKEN]/g" {} \;' \
  HEAD
```

### 3. 정리

```bash
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### 4. Force Push

```bash
git push --force origin main
```

---

## 🛠️ 방법 3: 완전 초기화 (간단하지만 히스토리 손실)

### 히스토리를 포기하고 새로 시작

```bash
cd /Users/jjongz/PycharmProjects/finacneFee

# 1. 기존 Git 디렉토리 삭제
rm -rf .git

# 2. 새로 초기화
git init
git add .
git commit -m "🎉 Initial commit (clean)"

# 3. GitHub에 Force Push
git remote add origin https://github.com/jonghwa-oh/stock-volatility-alert.git
git branch -M main
git push -u --force origin main
```

**장점:**
- ✅ 가장 간단함
- ✅ 확실하게 모든 민감 정보 제거

**단점:**
- ❌ 모든 commit 히스토리 손실
- ❌ 기여자 정보 손실

---

## 📋 삭제해야 할 민감한 정보 목록

### 봇 토큰
```
8105040252:AAHXbWn0FV3ymw9PTzlbPMyIC6JoehY-3pM
```

### Chat ID
```
6633793503
798920
```

### KIS API 키 (코드에 노출된 경우)
```
PS3dFQ9TYaOGhO3MBABLt9JtUTivW1ihOJrt
qEtP1QwuheXZvouP/tjPPYMiyDRJ5S7YpWwFaCs+SIZQB7G5MlfVZ6+im/2u4xbbiamTQ0HXD4UFy3WT7242FKdHBLNVWzfHOhs8JLlBb3lGzuEuUMLsrf0rPYFFQXuMEfh7f1rr9oQAyYQXq70eJfJ5/ggn6kGEFqV7I3pRPzeBSTf6kQk=
```

---

## ✅ 실행 후 확인

### 1. 로컬에서 검색

```bash
# Bot Token 검색
git log -S"8105040252" --all

# Chat ID 검색
git log -S"6633793503" --all
```

**출력이 없으면 성공!**

### 2. GitHub에서 검색

1. GitHub 저장소 접속
2. 우측 상단 검색창에 `8105040252` 입력
3. **"Code" 탭에서 검색**

**결과가 없으면 성공!**

### 3. 전체 파일 검색

```bash
cd /Users/jjongz/PycharmProjects/finacneFee

# 모든 파일에서 민감한 정보 검색
grep -r "8105040252" .
grep -r "6633793503" .
grep -r "798920" .
```

**출력이 없으면 성공!**

---

## 🔐 예방 조치

### 1. Pre-commit Hook 설정

```bash
# .git/hooks/pre-commit 파일 생성
cat > .git/hooks/pre-commit <<'EOF'
#!/bin/bash

# 민감한 정보 검사
if git diff --cached | grep -E "8105[0-9]{6}|663[0-9]{7}"; then
  echo "❌ 민감한 정보가 포함되어 있습니다!"
  echo "   Commit을 중단합니다."
  exit 1
fi

echo "✅ 민감한 정보 없음 - Commit 진행"
EOF

# 실행 권한 부여
chmod +x .git/hooks/pre-commit
```

### 2. .gitignore 강화

```bash
cat >> .gitignore <<EOF

# 민감한 정보가 포함될 수 있는 파일
**/secrets.txt
**/credentials.txt
**/*_backup*.json
**/*.env.local
EOF
```

### 3. 환경 변수 사용

민감한 정보는 **절대 코드에 직접 입력하지 않기!**

```python
# ❌ 나쁜 예
BOT_TOKEN = "8105040252:AAH..."

# ✅ 좋은 예
import os
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
```

---

## 🆘 이미 GitHub에 노출되었다면?

### 1. 즉시 토큰 갱신

#### 텔레그램 Bot Token

1. BotFather와 대화 (`@BotFather`)
2. `/mybots` 선택
3. 봇 선택
4. `API Token` → `Revoke current token`
5. 새 토큰 생성
6. `init_settings.py` 재실행

#### KIS API 키

1. 한국투자증권 OpenAPI 사이트 접속
2. 기존 키 삭제
3. 새 키 발급
4. `init_kis_settings.py` 재실행

### 2. Git 히스토리 정리

위의 방법 1~3 중 선택하여 실행

### 3. Force Push

```bash
git push --force origin main
```

### 4. 다른 사람에게 알림

협업자가 있다면:
```
⚠️ Git 히스토리를 재작성했습니다!
로컬 저장소를 삭제하고 다시 clone해주세요:

git clone https://github.com/jonghwa-oh/stock-volatility-alert.git
```

---

## 📚 참고 자료

- [BFG Repo-Cleaner 공식 문서](https://rtyley.github.io/bfg-repo-cleaner/)
- [GitHub - 민감한 데이터 제거](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [Git filter-branch 문서](https://git-scm.com/docs/git-filter-branch)

---

## 💡 권장 방법

**프로젝트가 이미 Public이고 협업자가 없다면:**
→ **방법 3 (완전 초기화)** 추천!

**이유:**
- 가장 간단하고 확실함
- 히스토리가 짧아서 손실이 크지 않음
- 100% 민감 정보 제거 보장

**명령어:**
```bash
cd /Users/jjongz/PycharmProjects/finacneFee
rm -rf .git
git init
git add .
git commit -m "🎉 Initial commit (secrets removed)"
git remote add origin https://github.com/jonghwa-oh/stock-volatility-alert.git
git branch -M main
git push -u --force origin main
```

**완료 후:**
1. 텔레그램 Bot Token 재발급
2. KIS API 키 재발급
3. `init_settings.py` 재실행
4. 정상 작동 확인

---

**🔒 앞으로는 민감한 정보를 코드나 문서에 절대 넣지 마세요!**

