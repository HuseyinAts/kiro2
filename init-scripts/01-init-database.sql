-- Türkiye Üniversite Sınavları Hazırlık Platformu
-- PostgreSQL veritabanı başlangıç scripti
-- Türkçe karakter desteği ile

-- Veritabanı encoding kontrolü
SELECT current_setting('server_encoding');

-- Türkçe collation ayarları
CREATE COLLATION IF NOT EXISTS turkish (provider = icu, locale = 'tr-TR');

-- Extension'ları etkinleştir
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Türkçe metin arama için konfigürasyon
CREATE TEXT SEARCH CONFIGURATION turkish_config (COPY = simple);

-- Temel tablolar için schema oluştur
CREATE SCHEMA IF NOT EXISTS sinav_sistemi;
CREATE SCHEMA IF NOT EXISTS kullanici_yonetimi;
CREATE SCHEMA IF NOT EXISTS icerik_yonetimi;
CREATE SCHEMA IF NOT EXISTS analitik;

-- Türkçe karakter test tablosu
CREATE TABLE IF NOT EXISTS test_turkce (
    id SERIAL PRIMARY KEY,
    metin TEXT COLLATE turkish,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Test verisi ekle
INSERT INTO test_turkce (metin) VALUES 
('Türkçe karakterler: ç, ğ, ı, ö, ş, ü'),
('ÖSYM sınavları: TYT, AYT, YDT'),
('MEB müfredatı uyumluluğu');

-- Başarılı kurulum mesajı
DO $$
BEGIN
    RAISE NOTICE 'Türkiye Üniversite Sınavları Hazırlık Platformu veritabanı başarıyla kuruldu!';
END $$;