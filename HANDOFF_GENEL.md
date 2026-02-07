# KIRO2 - Genel Proje Durumu ve Devam Rehberi
**Tarih:** 2026-01-10
**Versiyon:** Comprehensive Handoff v2

---

## 🎯 PROJE ÖZETİ

**KIRO2** = Türkiye'deki lise öğrencileri için YKS/TYT/AYT sınavlarına hazırlık EdTech platformu.

| Özellik | Değer |
|---------|-------|
| **Konum** | `C:\Users\husey\kiro2` |
| **Stack** | FastAPI + React 18 + TypeScript + PostgreSQL + Redis |
| **AI/NLP** | BERTurk, Qwen3-8B (fine-tuned), Turkish embeddings |
| **Hedef Kullanıcı** | 100,000+ concurrent students |
| **İçerik Hedefi** | 2,500+ soru (şu an ~50 aktif) |

---

## 📊 MEVCUT DURUM

### Backend (95% Tamamlandı)
- 588 dosya, 50+ router, FastAPI
- PostgreSQL port 5434
- IRT/FSRS adaptive learning algoritmaları
- `backend/main.py` (810 satır)

### Frontend (95% Tamamlandı)
- 780+ dosya, React 18 + TypeScript
- Material-UI + Tailwind CSS
- Zustand state management (`authStore.ts` - production-ready)
- `examService.ts` (900 satır - WebSocket DEPRECATED L123-145)

### Orchestrator (100% Tamamlandı) ✅
- Claude Code + Codex CLI otomatik routing
- Konum: `C:\Users\husey\kiro2\kiro2-orchestrator\`
- Launcher: `C:\Users\husey\kiro2\kiro2.bat`

### D-Dataset (İçerik Pipeline - Devam Ediyor)
- Konum: `C:\Users\husey\d-dataset\`
- 75,745 OCR-processed soru (317 kitap)
- 88,711 cevap anahtarı
- Eşleşme oranı: %0.11 (2,436 match) - İYİLEŞTİRME GEREKİYOR
- 725 YOLO-detected "cevaplar" cropu İŞLENMEMİŞ

---

## 🔴 KRİTİK BEKLEYEN İŞLER (65 dakika toplam)

### 1. emergency_content.sql Yüklenmedi (30 dk)
```powershell
# PostgreSQL'e 50 soru yükle
psql -U postgres -d kiro2 -f C:\Users\husey\kiro2\emergency_content.sql
```

### 2. WebSocket Kodu Kaldırılmalı (15 dk)
- Dosya: `frontend/src/services/examService.ts`
- Satırlar: 123-145 (`createWebSocketConnection()`)
- SSE zaten mevcut: `streamExamExplanation()`, `streamChat()`

### 3. DB Bağlantı Doğrulama (20 dk)
```python
# backend/database/connection.py
# get_db() async generator test et
```

---

## ✅ ÇÖZÜLEN SORUNLAR

| Sorun | Çözüm | Tarih |
|-------|-------|-------|
| useAuth.ts import hataları | authStore.ts'e migrate edildi, 12 dosya güncellendi | 2026-01-09 |
| CORS 403 | Backend main.py CORS config düzeltildi | 2026-01-09 |
| Orchestrator kurulum | Windows path'ler ve encoding düzeltildi | 2026-01-10 |

---

## 🚀 ORCHESTRATOR KULLANIMI

```powershell
cd C:\Users\husey\kiro2

# Routing test (çalıştırmaz)
.\kiro2.bat --dry-run "React component yaz"

# Gerçek çalıştırma
.\kiro2.bat "FastAPI endpoint oluştur"

# Stats
.\kiro2.bat --stats
```

### Routing Özeti:
- **Turkish NLP** → Claude Opus
- **Security** → Claude Opus
- **YKS Content** → Claude Sonnet
- **Database** → Claude Sonnet
- **Frontend/React** → Codex
- **Backend/API** → Codex
- **Tests** → Codex

---

## 📁 ÖNEMLİ DOSYA KONUMLARI

```
C:\Users\husey\kiro2\
├── backend/
│   ├── main.py                    # 810 satır, ana FastAPI
│   ├── database/connection.py     # AsyncPG bağlantı
│   └── config/*.yaml              # Yapılandırma
├── frontend/
│   ├── src/services/examService.ts  # 900 satır, L123-145 WebSocket DEPRECATED
│   ├── src/stores/authStore.ts      # 320 satır, production-ready
│   └── src/hooks/useAuth.ts         # SİLİNDİ ✓
├── kiro2-orchestrator/              # Multi-agent orchestrator
│   └── kiro2-orchestrator/scripts/kiro2_orchestrator.py
├── kiro2.bat                        # Orchestrator launcher
├── emergency_content.sql            # 50 soru - YÜKLEME BEKLİYOR
├── HANDOFF_ORCHESTRATOR.md          # Orchestrator detay dokümantasyonu
└── HANDOFF_GENEL.md                 # Bu dosya

C:\Users\husey\d-dataset\
├── 317 kitap dizini (OCR processed)
├── answers_v9.db                    # Cevap veritabanı
├── CEVAP_ANAHTARI_STRATEJI_RAPORU.md
└── extract_answers_batch.py         # Batch OCR script
```

---

## 📚 PROJE DOSYALARI (Claude Projede)

Yeni sohbette bu dosyaları oku:
1. `/mnt/project/KIRO2_CLAUDE.md` - Ana proje talimatları
2. `/mnt/project/KIRO2_SETUP_GUIDE.md` - Orchestrator rehberi
3. `/mnt/project/Türkçe_YKS_Soru-Cevap_Eşleştirme_Pipeline_Rehberi.md` - NLP stratejileri
4. `/mnt/project/cevap_cikarma_raporu.md` - Manuel çıkarma raporu
5. `/mnt/project/en_az_cevapli_400_kitap.txt` - Eksik cevaplı kitaplar

---

## 💡 YENİ SOHBETE BAŞLAMA ŞABLONU

```
KIRO2 projesine devam ediyorum.

## Proje Bilgisi
- Konum: C:\Users\husey\kiro2
- Stack: FastAPI + React + PostgreSQL + Redis
- Amaç: YKS sınav hazırlık platformu

## Son Durum
- Orchestrator kuruldu ve çalışıyor (kiro2.bat)
- useAuth.ts sorunu çözüldü (authStore.ts'e migrate)
- CORS sorunu çözüldü

## Bekleyen İşler (65 dk)
1. emergency_content.sql yükle (30 dk)
2. WebSocket kodu kaldır - examService.ts L123-145 (15 dk)
3. DB bağlantı doğrula (20 dk)

## Şimdi Yapmak İstediğim
[BURAYI DOLDUR]

Proje dosyalarını oku:
- /mnt/project/KIRO2_CLAUDE.md
- /mnt/project/KIRO2_SETUP_GUIDE.md
```

---

## 🔧 ORTAM BİLGİLERİ

| Bileşen | Değer |
|---------|-------|
| OS | Windows 11 + WSL2 Ubuntu |
| Python | 3.11+ |
| Node.js | 22.x (NVM) |
| PostgreSQL | Port 5434 |
| IDE | VS Code + Kiro IDE |
| Claude CLI | Mevcut ✅ |
| Codex CLI | Mevcut ✅ |

---

## 📈 İÇERİK STRATEJİSİ (D-Dataset)

### Mevcut Durum
- 426 kitap tarandı
- 251 kitapta 0 cevap (%59)
- 36 kitapta >100 cevap
- En verimli: Sure TYT Türkçe (850 cevap)

### Çıkarma Stratejisi (4 Faz)
1. **Faz 1:** YOLO crop OCR (2 gün) - 725 işlenmemiş crop
2. **Faz 2:** Kitap sonu cevap anahtarları (3 gün)
3. **Faz 3:** Regex pattern matching (1 gün)
4. **Faz 4:** Soru-cevap eşleştirme optimizasyonu (2 gün)

### Format Tipleri
- `BOOK_END_TABLE`: Kitap sonunda tablo (en verimli - 200+ cevap/sayfa)
- `PAGE_BOTTOM`: Sayfa altı mini kutu (3-15 cevap/sayfa)
- `TEST_END_KONU_ANALIZI`: Test sonu analiz sayfası (30 cevap/sayfa)

---

## 🎯 ROADMAP

### Acil (Bu Hafta)
- [ ] emergency_content.sql yükle
- [ ] WebSocket kodu temizle
- [ ] DB bağlantı doğrula
- [ ] Production smoke test

### Kısa Vadeli (2 Hafta)
- [ ] 725 YOLO crop'u işle
- [ ] Eşleşme oranını %10'a çıkar
- [ ] 500+ aktif soru

### Orta Vadeli (1 Ay)
- [ ] AI soru üretimi (Claude + VBART)
- [ ] 2,500+ soru hedefi
- [ ] Beta kullanıcı testi

---

**Hazırlayan:** Claude Code Session
**Son Güncelleme:** 2026-01-10
**Durum:** Production'a 65 dakika uzaklıkta
