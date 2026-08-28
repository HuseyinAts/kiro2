\encoding UTF8
-- ADIM 1 yetki testi. Canli kiro2'de kosulur. ISLEM GERI SARILIR — kalici yazim YOK.
-- NOT: Turkce karakter iceriyor; bu yuzden -c DEGIL -f ile kosulmali
-- (kendi kayitli kuralimiz: inline -c Turkce'yi bozar, 0x97 hatasi).
BEGIN;

INSERT INTO topic_hierarchy (id, code, name_tr, level, is_active)
VALUES ('_y11_yetki_testi', '_TEST', 'yetki testi — çğıöşü', 1, false);

SELECT 'INSERT yetkisi VAR — eklenen satir: ' || count(*)
  FROM topic_hierarchy WHERE id = '_y11_yetki_testi';

ROLLBACK;

SELECT 'ROLLBACK sonrasi test satiri: ' || count(*) || '  (0 olmali)'
  FROM topic_hierarchy WHERE id = '_y11_yetki_testi';
SELECT 'toplam konu: ' || count(*) || '  (12 olmali)' FROM topic_hierarchy;
