# Türkiye Üniversite Sınavları Hazırlık Platformu - Backend Dockerfile
FROM python:3.11-slim

# Türkçe karakter desteği için locale ayarları
ENV LANG=tr_TR.UTF-8
ENV LANGUAGE=tr_TR:tr
ENV LC_ALL=tr_TR.UTF-8
ENV PYTHONIOENCODING=utf-8

# Sistem paketlerini güncelle ve gerekli paketleri yükle
RUN apt-get update && apt-get install -y \
    locales \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Türkçe locale oluştur
RUN sed -i '/tr_TR.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen

# Çalışma dizini oluştur
WORKDIR /app

# Python bağımlılıklarını kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# Port açık
EXPOSE 8000

# Uygulama başlat
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]