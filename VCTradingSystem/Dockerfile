FROM python:3.10.11

# 필수 시스템 패키지 설치
RUN apt-get update && apt-get install -y pkg-config default-libmysqlclient-dev gcc && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Django 정적 파일 수집
RUN python manage.py collectstatic --noinput

# Expose port and run the app
EXPOSE 8080
CMD ["gunicorn", "VCTradingSystem.wsgi:application", "--bind", "0.0.0.0:8080"]
