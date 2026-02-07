# KIRO2 Veritabanı Analiz Raporu
*Tarih: 2026-01-13*

## 1. Veritabanı Genel Bilgileri

### PostgreSQL Kurulumu
- **Versiyon**: PostgreSQL 18.1 (x86_64-windows, msvc-19.44.35219, 64-bit)
- **Veritabanı Adı**: kiro2
- **Port**: 5434
- **Boyut**: 11 MB
- **Kullanıcı**: postgres

## 2. Tablo Yapısı (41 Tablo)

### 2.1 Kullanıcı Yönetimi Tabloları
#### users (Ana kullanıcı tablosu)
- **Alanlar**: 22 alan (id, email, username, password_hash, 2FA alanları, premium durumu, kişisel bilgiler, rol, XP/level, timestamps)
- **İndeksler**: 7 adet (primary key, email, username, role, created_at)
- **İlişkiler**: 33 farklı tablo bu tabloya referans veriyor (en kritik tablo)
- **Özellikler**:
  - 2FA desteği (secret_2fa, is_2fa_enabled, backup_codes_hashed)
  - Premium kullanıcı desteği (is_premium, premium_expires_at)
  - Gamification (total_xp, level, last_level_up_at)
  - Rol bazlı yetkilendirme (role: userrole enum)

#### Profil Tabloları
- student_profiles: Öğrenci profil bilgileri
- teacher_profiles: Öğretmen profil bilgileri
- parent_profiles: Veli profil bilgileri

### 2.2 Soru Bankası Tabloları
#### questions (Soru deposu)
- **Alanlar**: 28 alan
- **Kritik Alanlar**:
  - Soru içeriği: question_text, question_image_url, option_a-e, correct_answer, explanation
  - Sınav bilgileri: exam_type (TYT/AYT/YDT), subject_area, topic, subtopic
  - IRT parametreleri: irt_difficulty (-3 ile 3 arası), irt_discrimination (0.1-3), irt_guessing (0-1)
  - NLP metrikleri: morphology_complexity, readability_score
  - İstatistikler: times_asked, times_correct, average_response_time
  - Visual content: JSON formatında görsel içerik desteği
- **İndeksler**: 6 adet (difficulty, exam_type, irt_difficulty, subject_area, topic)
- **Check Constraints**: 4 adet (correct_answer, IRT değer aralıkları)

### 2.3 Sınav Yönetimi
- exam_sessions: Sınav oturumları
- exam_questions: Sınav-soru ilişkileri
- student_answers: Öğrenci cevapları

### 2.4 Öğrenme Analitikleri
- learning_analytics: Öğrenme verilerinin analizi
- fsrs_cards: FSRS algoritması kartları
- fsrs_reviews: FSRS tekrar kayıtları
- fsrs_schedules: FSRS zamanlama
- fsrs_student_profiles: FSRS öğrenci profilleri
- fsrs_study_sessions: FSRS çalışma oturumları
- fsrs_subject_stats: FSRS konu istatistikleri

### 2.5 EBA İçerik Entegrasyonu
- eba_videos: EBA video içerikleri
- eba_video_usage: Video kullanım istatistikleri
- eba_video_recommendations: Video önerileri
- eba_content_collections: İçerik koleksiyonları
- eba_content_analytics: İçerik analitikleri

### 2.6 Gamification & Motivasyon
- user_achievements: Başarılar
- user_badges: Rozetler
- point_transactions: Puan işlemleri
- weekly_progress: Haftalık ilerleme
- student_goals: Öğrenci hedefleri

### 2.7 Eğitim Araçları
- manipulative_activities: Manipülatif aktiviteler
- manipulative_progress: Manipülatif ilerleme
- educational_contents: Eğitim içerikleri
- classrooms: Sınıf yönetimi

### 2.8 Sistem & Güvenlik
- sessions: Oturum yönetimi
- refresh_tokens: JWT refresh tokenlar
- api_keys: API anahtarları
- audit_logs: Denetim kayıtları
- system_configurations: Sistem konfigürasyonları

### 2.9 Bildirim & Raporlama
- notifications: Bildirimler
- parent_reports: Veli raporları
- parent_approvals: Veli onayları
- class_reports: Sınıf raporları
- student_grades: Öğrenci notları

### 2.10 Metadata
- alembic_version: Migration versiyonu

## 3. API Endpoint Analizi

### 3.1 Router Yapısı (139 Router)
Backend modüler bir yapıda organize edilmiş. Router'lar kategorilere ayrılmış:

#### Kategoriler ve Sayılar:
- **Security (11)**: Auth, 2FA, KVKK, DDOS koruması, rate limiting
- **Exam (3)**: Sınav yönetimi, performans takibi, cevap takibi
- **Learning (7)**: Öğrenme stilleri, öğrenme yolları, ZPD/Maarif, IRT/Morfoloji, FSRS, müfredat uyumu
- **Content (21)**: Soru bankası, ÖSYM soruları, hibrit soru üretimi, PDF işleme, batch üretim
- **AI/NLP (10)**: Agent'lar, çoklu agent, chat, RAG, Türkçe NLP, BERTurk, Zemberek
- **Integrations (5)**: YouTube, Khan Academy, EBA, gamification
- **Admin (15)**: Yönetim paneli, öğretmen/veli yönetimi, cache, kullanıcı yönetimi
- **Analytics (9)**: Analitikler, monitoring, performans, Elasticsearch, Sentry, video analitikleri
- **Accessibility (18)**: ADHD desteği, OSB desteği, metin sadeleştirme, TTS, biyonik okuma
- **University (6)**: Üniversite danışmanlığı, tercih simülasyonu, bölüm bilgileri

### 3.2 Özel Endpoint'ler
- Wave2B Quality Routes: Yeni nesil soru kalite kontrolü
- FERPA/COPPA Compliance: Uluslararası veri koruma standartları
- YOLO Detection API: Görüntü işleme ve nesne tespiti
- OCR API: Optik karakter tanıma

## 4. Model Yapısı Analizi

### 4.1 Domain Modelleri (60+ Model Dosyası)
Modeller domain bazlı ayrıştırılmış:
- **User Domain**: user_models.py (User, StudentProfile, TeacherProfile, ParentProfile)
- **Content Domain**: content_db.py (Question, EducationalContent, ClassRoom)
- **Exam Domain**: exam_db.py (ExamSession, ExamQuestion, StudentAnswer)
- **Analytics Domain**: analytics_db.py (LearningAnalytics)
- **FSRS Domain**: fsrs_models.py (6 farklı FSRS modeli)
- **EBA Domain**: eba_models.py (5 farklı EBA modeli)
- **Gamification Domain**: gamification_db.py (Badges, Achievements, Points)
- **System Domain**: system_models.py (RefreshToken, APIKey, AuditLog)

### 4.2 Enum Tanımları
- UserRole: student, teacher, parent, admin
- ExamType: TYT, AYT, YDT, YKS, ALES, YÖKDİL
- QuestionDifficulty: çok_kolay, kolay, orta, zor, çok_zor, uzman
- LearningStyle: visual, auditory, kinesthetic, reading_writing
- SubjectArea: matematik, türkçe, fizik, kimya, biyoloji, tarih, coğrafya, felsefe, din

## 5. Teknik Özellikler

### 5.1 Güvenlik
- **Bcrypt** ile şifre hashleme
- **JWT** tabanlı kimlik doğrulama (Access + Refresh Token)
- **2FA** desteği (TOTP + Backup codes)
- **API Key** yönetimi
- **Audit Log** sistemi (tüm kritik işlemler kaydediliyor)
- **DDOS koruması** ve **Rate Limiting**
- **KVKK/GDPR** uyumlu veri yönetimi
- **FERPA/COPPA** eğitim verisi koruma standartları

### 5.2 Performans Optimizasyonları
- **İndeksleme**: Her tabloda kritik alanlarda indeksler
- **Foreign Key Cascade**: Veri bütünlüğü için cascade delete
- **Check Constraints**: Veri kalitesi için kontroller
- **JSON alanları**: Esnek veri saklama (visual_content, backup_codes)
- **Timestamp with timezone**: Tüm zaman damgaları timezone aware

### 5.3 AI/ML Entegrasyonu
- **IRT Parametreleri**: Item Response Theory ile soru zorluğu analizi
- **Morfoloji Kompleksligi**: Türkçe dil işleme
- **Okunabilirlik Skoru**: Metin zorluğu analizi
- **BERTurk Entegrasyonu**: Türkçe NLP modeli
- **Zemberek**: Türkçe morfolojik analiz
- **FSRS Algoritması**: Spaced repetition sistemi

### 5.4 Modüler Mimari
- **Application Factory Pattern**: core/application.py
- **Dynamic Router Loading**: routers/loader.py
- **Domain-Driven Design**: Model ve servisler domain bazlı organize
- **Repository Pattern**: Veritabanı işlemleri için repository katmanı

## 6. Kritik Gözlemler

### 6.1 Güçlü Yönler
✅ Kapsamlı tablo yapısı (41 tablo)
✅ İyi tasarlanmış ilişkisel model
✅ Güçlü güvenlik altyapısı (2FA, JWT, Audit)
✅ AI/ML entegrasyonu (IRT, FSRS, NLP)
✅ Modüler ve ölçeklenebilir mimari
✅ Türkçe eğitim sistemine özel tasarım
✅ Uluslararası standartlara uyum (FERPA/COPPA)

### 6.2 Dikkat Edilmesi Gerekenler
⚠️ Veritabanında sadece test verisi var (her tabloda 1 kayıt)
⚠️ 139 router çok fazla - gruplandırma düşünülebilir
⚠️ Model dosyalarının sayısı yüksek (60+)
⚠️ Bazı legacy alias'lar mevcut (EgitimIcerigi)

### 6.3 Öneriler
1. **Veri Yükleme**: Acil olarak gerçek soru ve içerik verisi yüklenmeli
2. **Router Konsolidasyonu**: Benzer router'lar birleştirilebilir
3. **Model Organizasyonu**: Domain modelleri daha da sadeleştirilebilir
4. **Cache Stratejisi**: Redis entegrasyonu görünmüyor, eklenebilir
5. **Test Coverage**: Test veritabanı ve test senaryoları hazırlanmalı

## 7. Sonuç
KIRO2, Türkiye'nin YKS/TYT/AYT sınav sistemine özel geliştirilmiş, modern teknolojilerle donatılmış kapsamlı bir eğitim platformu. Veritabanı yapısı iyi tasarlanmış, güvenlik önlemleri alınmış ve AI/ML yetenekleri entegre edilmiş durumda. Platform production'a hazır ancak gerçek veri yüklenmesi kritik öneme sahip.

**Platform Durumu**: ✅ Teknik altyapı hazır | ⚠️ Veri yükleme bekliyor