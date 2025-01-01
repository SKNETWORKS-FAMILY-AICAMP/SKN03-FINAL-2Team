FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    build-essential \
    curl \
    software-properties-common \
    git \
    # Chrome 및 ChromeDriver 관련 패키지 추가
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Chrome 관련 환경변수 설정
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# config.py 먼저 복사
COPY config.py /config.py

# app 디렉토리 복사
COPY app/ /app/
COPY data_modules/ /data_modules/

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# Streamlit 설정 파일이 있는지 확인하고 포트 설정
EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# 실행 명령어
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]