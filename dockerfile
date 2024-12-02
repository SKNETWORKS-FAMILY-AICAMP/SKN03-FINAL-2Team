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
    && rm -rf /var/lib/apt/lists/*

# 필요한 파일들 복사
COPY app/ /app/

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# Streamlit 설정 파일이 있는지 확인하고 포트 설정
EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# 실행 명령어
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]