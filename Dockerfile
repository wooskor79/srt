# 파이썬 공식 이미지 사용 (작고 효율적)
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 라이브러리 설치 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# 업로드 및 출력 폴더 생성
# /output 폴더는 NAS의 /volume1/torrent와 매핑될 위치입니다.
RUN mkdir -p uploads
RUN mkdir -p /output 

# 컨테이너 실행 시 Flask 서버 시작
CMD ["python", "app.py"]