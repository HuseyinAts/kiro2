---
name: db-query
description: PostgreSQL sorgularini guvenli calistir (port 5434, kiro2 DB)
user-invocable: true
---

# DB Query Skill

PostgreSQL veritabaninda sorgu calistir. Production veritabani: `kiro2`, port `5434`.

## Kullanim

```
/db-query SELECT COUNT(*) FROM question_bank WHERE is_active = true
/db-query \dt question_*
/db-query SELECT subject_area, COUNT(*) FROM question_bank WHERE is_active = true GROUP BY subject_area
```

## Kurallar

1. Sadece **SELECT** ve meta-komutlar (\dt, \d, \di) calistir
2. **INSERT/UPDATE/DELETE/DROP/TRUNCATE YASAK** — kullanicidan onay al
3. Production tablosu: `question_bank` (77,336 soru). `questions` tablosu BOS legacy — KULLANMA
4. `is_active = true` filtresini unutma (13,055 cop soru devre disi)
5. Buyuk sonuc setlerinde `LIMIT 20` ekle

## Calistirma

```bash
PGPASSWORD=$KIRO2_DB_PASSWORD psql -h localhost -p 5434 -U postgres -d kiro2 -c "$ARGUMENTS"
```

Eger `KIRO2_DB_PASSWORD` tanimli degilse:
```bash
psql -h localhost -p 5434 -U postgres -d kiro2 -c "$ARGUMENTS"
```

## Ornek Sorgular

- Toplam aktif soru: `SELECT COUNT(*) FROM question_bank WHERE is_active = true`
- Konu dagilimi: `SELECT subject_area, COUNT(*) FROM question_bank WHERE is_active = true GROUP BY subject_area ORDER BY count DESC`
- Son migration: `SELECT version_num FROM alembic_version`
- Tablo listesi: `\dt`
