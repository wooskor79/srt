# 파이썬 공식 이미지 사용
FROM python:3.11-slim

# 도커 클라이언트 설치 (app.py에서 docker logs 명령어를 실행하기 위함)
RUN apt-get update && apt-get install -y docker.io && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치 (수정된 numpy 버전 반영)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

# 필요한 폴더 생성
RUN mkdir -p uploads /output 

# 실행
CMD ["python", "app.py"]