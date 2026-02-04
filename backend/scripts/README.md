# Database Management Scripts

Bu klasör, Türkiye Üniversite Sınavları Hazırlık Platformu için database yönetim script'lerini içerir.

## 📁 Script'ler

### 1. `init_database.py` - Database Başlatma
Database'i başlatır, tabloları oluşturur ve sağlık kontrolü yapar.

```bash
# Database'i başlat
python scripts/init_database.py init

# Database durumunu kontrol et
python scripts/init_database.py status

# Database'i sıfırla (DİKKATLİ!)
python scripts/init_database.py reset --force
```

### 2. `seed_database.py` - Development Veri Seeding
Development ortamı için örnek veriler ekler.

```bash
# Development verilerini seed et
python scripts/seed_database.py
```

**Eklenen veriler:**
- 2 Admin kullanıcısı
- 3 Örnek öğretmen
- 3 Örnek öğrenci  
- 2 Örnek veli
- 7 Örnek soru (TYT/AYT)
- 4 Eğitim içeriği
- Sistem konfigürasyonları

### 3. `production_seed.py` - Production Veri Seeding
Production ortamı için kritik minimum veriler ekler.

```bash
# Production verilerini seed et (sadece production ortamında)
python scripts/production_seed.py
```

**Eklenen veriler:**
- Kritik sistem konfigürasyonları
- Admin kullanıcısı (güvenli şifre ile)
- Minimum soru bankası

### 4. `manage_db.py` - Database Yönetim CLI
Kapsamlı database yönetim aracı.

```bash
# Migration oluştur
python scripts/manage_db.py migration create "Migration mesajı"

# Migration'ları çalıştır
python scripts/manage_db.py migration run

# Migration'ı geri al
python scripts/manage_db.py migration rollback

# Mevcut revision'ı göster
python scripts/manage_db.py migration current

# Migration geçmişini göster
python scripts/manage_db.py migration history

# Development verilerini seed et
python scripts/manage_db.py seed dev

# Production verilerini seed et
python scripts/manage_db.py seed prod

# Database backup al
python scripts/manage_db.py backup --path backup.sql
```

### 5. `optimize_database.py` - Database Optimizasyon
Database performansını analiz eder ve optimizasyonlar uygular.

```bash
# Performans analizi yap
python scripts/optimize_database.py analyze

# Temel optimizasyonları uygula
python scripts/optimize_database.py optimize

# Database vacuum işlemi
python scripts/optimize_database.py vacuum
```

## 🚀 Hızlı Başlangıç

### Yeni Kurulum
```bash
# 1. Database'i başlat
python scripts/init_database.py init

# 2. Migration'ları çalıştır
python scripts/manage_db.py migration run

# 3. Development verilerini seed et
python scripts/manage_db.py seed dev

# 4. Database durumunu kontrol et
python scripts/init_database.py status
```

### Production Kurulum
```bash
# 1. Environment'ı production'a ayarla
export ENVIRONMENT=production

# 2. Database'i başlat
python scripts/init_database.py init

# 3. Migration'ları çalıştır
python scripts/manage_db.py migration run

# 4. Production verilerini seed et
python scripts/manage_db.py seed prod

# 5. Optimizasyonları uygula
python scripts/optimize_database.py optimize
```

## 📊 Database Schema

### Ana Tablolar
- **users**: Kullanıcı bilgileri (öğrenci, öğretmen, veli, admin)
- **student_profiles**: Öğrenci profil bilgileri
- **teacher_profiles**: Öğretmen profil bilgileri
- **parent_profiles**: Veli profil bilgileri
- **questions**: Soru bankası
- **exam_sessions**: Sınav oturumları
- **exam_questions**: Sınav-soru ilişkileri
- **student_answers**: Öğrenci cevapları
- **educational_contents**: Eğitim içerikleri
- **learning_analytics**: Öğrenme analitiği
- **classrooms**: Sınıf yönetimi
- **system_configurations**: Sistem ayarları
- **audit_logs**: Sistem audit logları

### Devrimsel Özellik Alanları
- **vark_profile**: VARK + Felder-Silverman hibrit profil (JSON)
- **zpd_range**: ZPD + Maarif aralığı (JSON)
- **irt_ability**: IRT yetenek parametresi
- **fsrs_parameters**: FSRS parametreleri (JSON)
- **morphology_complexity**: Türkçe morfolojik karmaşıklık

## 🔧 Konfigürasyon

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./turkiye_sinav.db
DATABASE_ECHO=false

# Environment
ENVIRONMENT=development
DEBUG=false

# Security
SECRET_KEY=your-secret-key-change-in-production
```

### Alembic Konfigürasyonu
- **alembic.ini**: Alembic ana konfigürasyonu
- **alembic/env.py**: Migration environment
- **alembic/versions/**: Migration dosyaları

## 🛡️ Güvenlik

### Production Güvenlik
- Admin şifreleri güvenli olarak oluşturulur
- Sensitive veriler environment variable'larda saklanır
- Production ortamında reset işlemleri engellenir
- Audit logging tüm kritik işlemler için aktif

### Backup Stratejisi
- Günlük otomatik backup'lar
- 30 gün backup retention
- Point-in-time recovery desteği

## 📈 Performans

### Index Stratejisi
- Email, username için unique index'ler
- Foreign key'ler için index'ler
- Sık sorgulanan alanlar için composite index'ler
- JSON alanları için functional index'ler

### Query Optimization
- Connection pooling
- Prepared statements
- Eager loading
- Pagination optimization

## 🔍 Monitoring

### Health Checks
- Database bağlantı durumu
- Pool utilization
- Query performance metrics
- Index usage statistics

### Logging
- Tüm database işlemleri loglanır
- Performance metrics kaydedilir
- Error tracking ve alerting

## 🆘 Troubleshooting

### Yaygın Sorunlar

**Migration Hatası:**
```bash
# Migration'ı geri al ve tekrar dene
python scripts/manage_db.py migration rollback
python scripts/manage_db.py migration run
```

**Database Lock:**
```bash
# Database connection'ları kontrol et
python scripts/init_database.py status
```

**Performance Sorunları:**
```bash
# Performans analizi yap
python scripts/optimize_database.py analyze
# Optimizasyonları uygula
python scripts/optimize_database.py optimize
```

**Veri Kaybı:**
```bash
# Backup'tan restore et
python scripts/manage_db.py backup --path restore_backup.sql
```

## 📞 Destek

Sorunlar için:
1. Log dosyalarını kontrol edin
2. Database durumunu kontrol edin: `python scripts/init_database.py status`
3. Performance analizi yapın: `python scripts/optimize_database.py analyze`
4. Gerekirse backup'tan restore edin

---

**Not:** Production ortamında script'leri çalıştırmadan önce mutlaka backup alın!