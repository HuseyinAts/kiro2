# KIRO2 Hızlı Başvuru Rehberi

## 🚀 Hızlı Başlangıç

```bash
# Backend
cd backend && uvicorn main:app --reload --port 8000

# Frontend  
cd frontend && npm run dev -- --port 3001

# Database
docker-compose up -d postgres redis
```

## ⚠️ KRİTİK KURALLAR

1. **ASLA** `useAuth.ts` kullanma → `authStore.ts` kullan
2. **ASLA** mock veri kullanma → Gerçek API çağrıları yap
3. Her değişiklikten önce **testleri çalıştır**
4. Commit öncesi **lint kontrol** yap

## 🔧 Aktif Sorunlar

| # | Sorun | Çözüm |
|---|-------|-------|
| 1 | emergency_content.sql yüklenmemiş | `psql -U postgres -d kiro2 -f emergency_content.sql` |
| 2 | WebSocket deprecated (L123-145) | `examService.ts`'den kaldır |
| 3 | Content %0.11 eşleşme | d-dataset pipeline çalıştır |

## 📊 Mevcut Durum

- **Soru sayısı:** 2,436 / 50,000 hedef
- **OCR işlenmiş:** 75,745 soru (eşleşme bekliyor)
- **Backend:** %95 tamamlandı
- **Frontend:** %95 tamamlandı

## 🎯 Öncelikler

1. `emergency_content.sql` yükle (30dk)
2. WebSocket kodunu kaldır (15dk)  
3. DB bağlantısını doğrula (20dk)
4. d-dataset cevap eşleştirme başlat

## 📁 Önemli Dosya Konumları

```
C:\Users\husey\kiro2\
├── backend/main.py          # FastAPI ana
├── frontend/src/stores/authStore.ts  # Auth store
├── emergency_content.sql    # 50 hazır soru
├── d-dataset/              # OCR pipeline
└── .claude/                # Claude yapılandırma
```

## 🔗 Servis URL'leri

- Backend API: http://localhost:8000
- Frontend: http://localhost:3001
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5434
- Redis: localhost:6379
