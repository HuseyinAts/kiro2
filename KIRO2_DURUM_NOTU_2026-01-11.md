# 📋 KIRO2 PROJE DURUM NOTU
**Tarih:** 11 Ocak 2026  
**Son Güncelleme:** Bu oturum

---

## 🎯 PROJE AMACI
Türk öğrencileri YKS/TYT/AYT üniversite sınavlarına hazırlayan AI destekli eğitim platformu.
- 100,000+ eşzamanlı kullanıcı hedefi
- IRT (Item Response Theory) + FSRS (Spaced Repetition) + ZPD algoritmaları
- Türkçe NLP (BERTurk, Zemberek)
- ÖSYM standartlarında sınav deneyimi

---

## 📁 PROJE YAPISI

```
C:\Users\husey\kiro2\           # Ana proje
├── backend/                     # FastAPI (588 dosya, 50+ router)
│   ├── main.py (810 satır)     # CORS config L519-651
│   ├── models.py
│   └── database/connection.py
├── frontend/                    # React 18 + TypeScript (780+ dosya)
│   ├── src/hooks/authStore.ts  # (320L, ÇALIŞIYOR ✅)
│   └── src/services/examService.ts (900L, WebSocket DEPRECATED L123-145)
├── orchestrator/               # Otonom multi-agent sistemi (YENİ)
│   └── core/                   # 45 policy implementasyonu
└── emergency_content.sql       # 50 soru (YÜKLENMEDİ!)

C:\Users\husey\d-dataset\       # Veri pipeline
├── 75,745 OCR sorusu
├── 317 kitap
└── 725 YOLO cevap crop'u (İŞLENMEMİŞ!)
```

---

## ✅ TAMAMLANAN İŞLER

### 1. Frontend Auth Migrasyonu
- `useAuth.ts` → `authStore.ts` (Zustand) migrasyonu tamamlandı
- 12 bağımlı dosya güncellendi
- TypeScript ✅, Build ✅, Manual Test ✅

### 2. CORS 403 Hatası Çözüldü
- `backend/main.py` L519-651 CORS config düzeltildi
- `.env` dosyasına `ENVIRONMENT=development` eklendi
- Login endpoint: `POST /api/v1/auth/login`

### 3. Orchestrator Sistemi (%95 Tamamlandı)
**45 Otonom Policy (P1-P45) - 6 Kategori:**
- Routing Policies (P1-P8)
- Quality Gate Policies (P9-P18)
- Learning Policies (P19-P28)
- Resource Policies (P29-P36)
- Error Handling Policies (P37-P42)
- Meta Policies (P43-P45)

**Düzeltilen Import Hataları:**
- `routing.py`: `get_routing_engine()` factory eklendi (L403-413)
- `quality_gates.py`: `get_quality_pipeline()` factory eklendi (L445-470)
- `__init__.py`: LangGraph graph imports devre dışı (L68-74)
- `PostgresMemoryStore` import'u kaldırıldı
- `ImprovementAction` class adı düzeltildi

---

## ⚠️ BEKLEYEN İŞLER (ÖNCELİK SIRASINA GÖRE)

### 🔴 KRİTİK (Bugün)

| # | İş | Dosya/Konum | Süre |
|---|---|-------------|------|
| 1 | Orchestrator __all__ cleanup | `orchestrator/core/__init__.py` L165-167 | 5dk |
| 2 | Orchestrator test çalıştır | `test_complete_system.py` | 10dk |
| 3 | emergency_content.sql yükle | PostgreSQL'e 50 soru | 15dk |
| 4 | WebSocket kodu kaldır | `examService.ts` L123-145 | 10dk |

### 🟡 ORTA (Bu Hafta)

| # | İş | Detay |
|---|---|-------|
| 5 | DB bağlantı doğrulama | `database/connection.py` test |
| 6 | YOLO cevap crop'ları OCR | 725 görsel işlenmeli |
| 7 | Cevap eşleştirme pipeline | %0.11 → %66 hedef |

---

## 🚨 İÇERİK KRİZİ DETAYLARI

**d-dataset Durumu:**
- 75,745 OCR sorusu var
- Sadece 2,436 cevap eşleşmiş (%0.11)
- Hedef: %66 eşleşme oranı

**Kitap Analizi (426 kitap):**
- 251 kitapta 0 cevap (%59 YOK)
- 51 kitapta 1-10 cevap
- 67 kitapta 11-50 cevap
- Sadece 36 kitapta 100+ cevap

**Manuel Çıkarılan Cevaplar:** ~980
- Sure Tyt Türkçe: 850 ✅
- Diğer: 130

**En Kaliteli Yayıncılar:**
- ACİL ⭐⭐⭐⭐⭐
- CAP ⭐⭐⭐⭐⭐
- Bilgi Sarmalı ⭐⭐⭐⭐

**Cevap Çıkarma Stratejisi:**
1. Faz 1: YOLO crop OCR (2 gün)
2. Faz 2: Kitap sonu tablo tarama (3 gün)
3. Faz 3: Regex pattern matching (1 gün)
4. Faz 4: Soru-cevap eşleştirme (2 gün)

---

## 🔧 TEKNİK STACK

| Katman | Teknoloji |
|--------|-----------|
| Backend | FastAPI + Python 3.11+ |
| Frontend | React 18 + TypeScript |
| Database | PostgreSQL 15 (port 5434) |
| Cache | Redis 7 |
| NLP | BERTurk, Zemberek |
| Auth | JWT + OAuth2 |
| State | Zustand (authStore) |
| OCR | PaddleOCR, Gemini Vision |

---

## 📍 DOSYA REFERANSLARI

**Backend Kritik Dosyalar:**
- `main.py` (810L) - CORS: L519-651
- `database/connection.py` - AsyncPG
- `config/*.yaml`

**Frontend Kritik Dosyalar:**
- `authStore.ts` (320L) ✅ ÇALIŞIYOR
- `examService.ts` (900L) - WebSocket L123-145 KALDIRILACAK

**Orchestrator Dosyaları:**
- `orchestrator/core/routing.py` (413L)
- `orchestrator/core/quality_gates.py` (470L)
- `orchestrator/core/self_improvement.py`
- `orchestrator/core/__init__.py` - L68-74 disabled, L165-167 cleanup needed
- `test_complete_system.py` (287L)

---

## 🔑 ÖNEMLİ KOMUTLAR

```bash
# PostgreSQL emergency content yükleme
psql -U postgres -d kiro2 -f emergency_content.sql
SELECT COUNT(*) FROM questions;  # 50 bekleniyor

# Frontend test
cd frontend
npm run type-check
npm run build

# Backend test
cd backend
pytest tests/ -v

# Orchestrator test
cd orchestrator
python test_complete_system.py
```

---

## 📝 MEMORY KAYITLARI

Şu anda 19 aktif memory kaydı var:
- #1-6: Temel tech stack ve dosyalar
- #7: İçerik krizi detayları
- #8-11: Geliştirme stratejisi
- #12-15: Session referansları ve cevap stratejisi
- #16-19: Orchestrator sistemi

---

## 🎯 YENİ OTURUMDA YAPILACAKLAR

1. **Orchestrator'ı Bitir:**
   ```bash
   # __init__.py L165-167 graph referanslarını kaldır
   # test_complete_system.py çalıştır
   ```

2. **emergency_content.sql Yükle:**
   ```bash
   psql -U postgres -d kiro2 -f emergency_content.sql
   ```

3. **WebSocket Kodunu Kaldır:**
   - `examService.ts` L123-145 sil
   - SSE zaten var: `streamExamExplanation()`, `streamChat()`

4. **İçerik Pipeline'ını Başlat:**
   - YOLO crop'ları OCR
   - Cevap eşleştirme

---

## 📞 HIZLI REFERANS

**Proje Yolu:** `C:\Users\husey\kiro2`
**Dataset Yolu:** `C:\Users\husey\d-dataset`
**PostgreSQL Port:** 5434
**Frontend Port:** 3001
**Backend Port:** 8000

**Transcripts:** `/mnt/transcripts/journal.txt`

---

*Bu notu yeni oturumda Claude'a kopyalayarak devam edebilirsin.*
