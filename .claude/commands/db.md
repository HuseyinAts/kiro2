---
allowed-tools: Bash(alembic:*), Bash(python:*), Read
argument-hint: [migrate|rollback|status|create <name>]
description: Veritabanı migration işlemleri
---

## Task
Veritabanı migration işlemi: $ARGUMENTS

## Komutlar

### Status - Mevcut durumu göster
```bash
cd backend && alembic current
cd backend && alembic history --verbose | head -20
```

### Migrate - Migration uygula
```bash
cd backend && alembic upgrade head
```

### Rollback - Son migration'ı geri al
```bash
cd backend && alembic downgrade -1
```

### Create - Yeni migration oluştur
```bash
cd backend && alembic revision --autogenerate -m "<name>"
```

## Önemli Notlar

### ⚠️ Migration Oluşturmadan Önce
1. Model değişikliklerini kontrol et
2. İlişkileri doğrula (ForeignKey, relationship)
3. Index'leri kontrol et

### Migration Best Practices (KIRO2)
- Her migration tek bir değişiklik içermeli
- Rollback script'i test edilmeli
- Production'da migration öncesi backup alınmalı

### Kritik Tablolar
- `users` - Kullanıcı verileri
- `questions` - Soru bankası (100K+ kayıt)
- `exam_sessions` - Sınav oturumları
- `user_progress` - Öğrenme ilerlemesi

## Örnek Migration İsimleri
```
add_2fa_columns_to_users
create_exam_analytics_table
add_index_to_questions_topic
rename_user_settings_column
```
