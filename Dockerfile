# 시놀로지 NAS용 주식 알림 시스템 Docker 이미지

FROM python:3.11-slim

# 작업 디렉토리
WORKDIR /app

# 시스템 패키지 업데이트
RUN apt-get update && apt-get install -y \
    git \
    sqlite3 \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사
COPY . .

# 한글 폰트 설정을 위한 환경 변수
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 데이터 볼륨
VOLUME ["/app/data", "/app/backup"]

# 헬스체크
HEALTHCHECK --interval=5m --timeout=3s \
  CMD python -c "import sqlite3; sqlite3.connect('/app/data/stock_data.db').close()" || exit 1

# 시작 스크립트 복사 및 실행 권한
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 실행 (시작 스크립트)
CMD ["/app/start.sh"]

