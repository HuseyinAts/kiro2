-- ============================================================
-- Migration 010 v2: topic_hierarchy eksik dersler (osym_frequency dahil)
-- Tarih: 2026-03-26
-- ============================================================

INSERT INTO topic_hierarchy (id, level, code, name_tr, subject_area, difficulty_level, osym_relevance, osym_frequency, is_active, created_at, updated_at) VALUES
  -- SOSYAL
  (gen_random_uuid(),1,'SOC01','Vatandaşlık ve Demokrasi','SOSYAL',-1.0,0.80,3,TRUE,NOW(),NOW()),
  (gen_random_uuid(),2,'SOC02','Türk Tarihi Temel','SOSYAL',-0.5,0.75,2,TRUE,NOW(),NOW()),
  (gen_random_uuid(),3,'SOC03','Dünya Coğrafyasına Giriş','SOSYAL',0.0,0.70,2,TRUE,NOW(),NOW()),
  (gen_random_uuid(),4,'SOC04','Ekonomi ve Kalkınma','SOSYAL',0.5,0.65,2,TRUE,NOW(),NOW()),
  (gen_random_uuid(),5,'SOC05','Çağdaş Dünya Sorunları','SOSYAL',1.0,0.60,1,TRUE,NOW(),NOW()),
  -- GENEL
  (gen_random_uuid(),1,'GEN01','Temel Mantık ve Akıl Yürütme','GENEL',-1.2,0.85,4,TRUE,NOW(),NOW()),
  (gen_random_uuid(),2,'GEN02','Türkiye Coğrafyası Genel','GENEL',-0.6,0.80,3,TRUE,NOW(),NOW()),
  (gen_random_uuid(),3,'GEN03','Türk Kültür ve Medeniyeti','GENEL',0.0,0.75,3,TRUE,NOW(),NOW()),
  (gen_random_uuid(),4,'GEN04','Bilim ve Teknoloji Tarihi','GENEL',0.4,0.65,2,TRUE,NOW(),NOW()),
  (gen_random_uuid(),5,'GEN05','Güncel Olaylar ve Analiz','GENEL',0.9,0.55,1,TRUE,NOW(),NOW()),
  -- FEN
  (gen_random_uuid(),1,'FEN01','Madde ve Özellikleri','FEN',-1.3,0.90,4,TRUE,NOW(),NOW()),
  (gen_random_uuid(),2,'FEN02','Hücre ve Canlılar','FEN',-0.8,0.85,3,TRUE,NOW(),NOW()),
  (gen_random_uuid(),3,'FEN03','Kuvvet ve Hareket','FEN',-0.2,0.85,3,TRUE,NOW(),NOW()),
  (gen_random_uuid(),4,'FEN04','Enerji Dönüşümleri','FEN',0.4,0.80,3,TRUE,NOW(),NOW()),
  (gen_random_uuid(),5,'FEN05','Ekosistem ve Çevre','FEN',0.8,0.70,2,TRUE,NOW(),NOW()),
  -- GEOMETRI
  (gen_random_uuid(),1,'GEO01','Temel Geometri Kavramları','GEOMETRI',-1.5,0.90,5,TRUE,NOW(),NOW()),
  (gen_random_uuid(),2,'GEO02','Üçgenler','GEOMETRI',-0.8,0.90,5,TRUE,NOW(),NOW()),
  (gen_random_uuid(),3,'GEO03','Dörtgenler ve Çokgenler','GEOMETRI',-0.2,0.85,4,TRUE,NOW(),NOW()),
  (gen_random_uuid(),4,'GEO04','Çember ve Daire','GEOMETRI',0.5,0.85,4,TRUE,NOW(),NOW()),
  (gen_random_uuid(),5,'GEO05','Analitik Geometri','GEOMETRI',1.2,0.80,3,TRUE,NOW(),NOW()),
  -- EDEBIYAT
  (gen_random_uuid(),1,'EDU01','Divan Edebiyatı','EDEBIYAT',-1.0,0.85,3,TRUE,NOW(),NOW()),
  (gen_random_uuid(),2,'EDU02','Tanzimat ve Servet-i Fünun','EDEBIYAT',-0.4,0.85,3,TRUE,NOW(),NOW()),
  (gen_random_uuid(),3,'EDU03','Milli Edebiyat Dönemi','EDEBIYAT',0.1,0.80,3,TRUE,NOW(),NOW()),
  (gen_random_uuid(),4,'EDU04','Cumhuriyet Dönemi Edebiyatı','EDEBIYAT',0.6,0.80,3,TRUE,NOW(),NOW()),
  (gen_random_uuid(),5,'EDU05','Çağdaş Türk Edebiyatı','EDEBIYAT',1.0,0.75,2,TRUE,NOW(),NOW()),
  -- TARIH
  (gen_random_uuid(),1,'TAR01','İlk ve Orta Çağ Türk Tarihi','TARIH',-1.2,0.85,3,TRUE,NOW(),NOW()),
  (gen_random_uuid(),2,'TAR02','Osmanlı Devleti Kuruluş','TARIH',-0.6,0.85,4,TRUE,NOW(),NOW()),
  (gen_random_uuid(),3,'TAR03','Osmanlı Yükselme ve Duraklama','TARIH',0.0,0.80,4,TRUE,NOW(),NOW()),
  (gen_random_uuid(),4,'TAR04','Kurtuluş Savaşı ve Cumhuriyet','TARIH',0.5,0.90,5,TRUE,NOW(),NOW()),
  (gen_random_uuid(),5,'TAR05','Yakın Çağ ve Çağdaş Tarih','TARIH',1.0,0.80,3,TRUE,NOW(),NOW()),
  -- COGRAFYA
  (gen_random_uuid(),1,'COG01','Harita Bilgisi ve Koordinatlar','COGRAFYA',-1.3,0.85,3,TRUE,NOW(),NOW()),
  (gen_random_uuid(),2,'COG02','İklim ve Bitki Örtüsü','COGRAFYA',-0.5,0.85,4,TRUE,NOW(),NOW()),
  (gen_random_uuid(),3,'COG03','Nüfus ve Yerleşme','COGRAFYA',0.0,0.80,3,TRUE,NOW(),NOW()),
  (gen_random_uuid(),4,'COG04','Ekonomik Faaliyetler','COGRAFYA',0.5,0.80,3,TRUE,NOW(),NOW()),
  (gen_random_uuid(),5,'COG05','Bölgesel Coğrafya','COGRAFYA',1.0,0.75,2,TRUE,NOW(),NOW())
ON CONFLICT DO NOTHING;

-- Kontrol
SELECT subject_area, COUNT(*) as n FROM topic_hierarchy
WHERE is_active=TRUE AND subject_area IS NOT NULL
GROUP BY subject_area ORDER BY subject_area;
