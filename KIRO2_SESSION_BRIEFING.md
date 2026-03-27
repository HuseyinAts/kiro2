# KIRO2 — Yeni Sohbet Bilgilendirme Notu
> Son güncelleme: 26 Mart 2026 — Büyük fix oturumu tamamlandı
> Bu dosyayı her yeni sohbette ilk olarak oku!

---

## 🎯 PROJE NEDİR?

**KIRO2** — Türkiye YKS (TYT/AYT) sınavına hazırlık platformu.
- **Hedef:** 100,000+ eş zamanlı kullanıcı
- **Teknik fark:** IRT (3PL) + FSRS + ZPD + DAG algoritma stack'i
- **Konum:** `C:\Users\husey\kiro2`
- **TÜBİTAK 1512 BİGG** başvurusu planlanıyor

---

## 🚀 SİSTEMLERİ BAŞLATMA

```powershell
# 1. Docker servislerini başlat
docker start kiro2-frontend kiro2_redis kiro-postgres

# 2. Backend başlat (BERTurk ~60-90 sn sürer)
cd C:\Users\husey\kiro2\backend
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

> ⚠️ **PORT 8001:** Port 8000 Docker Desktop tarafından tutulmaktadır.

| Servis | URL |
|--------|-----|
| Backend FastAPI | http://localhost:**8001** |
| Frontend React | http://localhost:3001 (Docker: kiro2-frontend) |
| Redis | localhost:6379 (Docker: kiro2_redis) |
| PostgreSQL | localhost:5434 (Docker: kiro-postgres) |

**Admin:** `admin@kiro2.com` / `Kiro2Beta2026@x`
**DB:** host=localhost port=5434 dbname=kiro2 user=postgres pass=changeme_strong_password_here
**Veli test:** `veli_test@kiro2.com` / `VeliTest2026!` (PARENT rolü)
**Öğrenci test:** `ogrenci_veli_test@kiro2.com` / `VeliTest2026!`

---

## 📊 VERİTABANI DURUMU (26 Mart 2026)

```
question_bank:              64,225  aktif soru
  is_calibrated=TRUE:          360  (3PL EM — sentetik veri bazlı)
kiro2_cat_sessions:              2  (completed)
kiro2_learning_events:     117,297  (22 gerçek + 117,179 sentetik)
user_theta:                    103  kayıt | 52 kullanıcı | 9 ders
users:                          56  (5 asıl + 50 beta + 1 register test)
yks_exam_goals:                 52
daily_plans:                    52  (bugün tarihli — Celery ile otomatik yenilenir)
topic_hierarchy (aktif):       105  konu — 12 ders
topic_prerequisites:            29
irt_calibration_history:     1,080
user_item_fsrs:                 22
parent_child:                    1  (veli_test → ogrenci_veli_test)
```

### Ders bazlı topic_hierarchy (12 ders, 26 Mart sonrası):
```
MATEMATIK(20) FIZIK(4) KIMYA(4) BIYOLOJI(2) TURKCE(3) TARIH(7)
COGRAFYA(7) EDEBIYAT(5) GEOMETRI(5) SOSYAL(5) GENEL(5) FEN(5)
```

---

## 🧠 MİMARİ (GÜNCEL)

```
Öğrenci CAT testi yapar
    ↓
kiro2_cat_sessions'a yazılır
    ↓
user_theta UPSERT — OTOMATİK ✅ (cat_session.py)
+ plan_refresh_needed: True response'a eklendi ✅
    ↓
Frontend cat-complete CustomEvent dispatch ✅
    ↓
LearningPathOrchestrator (ZPD + IRT + FSRS + DAG)
    ├── needs_cat=True  → mastery=0%, priority=100
    └── needs_cat=False → mastery=CDF((θ+1)/SE)
    ↓
generate_daily_plan() → daily_plans tablosu
    ↓ (Celery beat her gece 02:00'de yeniler)
/api/v1/learning-path/today → DailyPlanPage.tsx
```

---

## ✅ 26 MART OTURUMUNDA TAMAMLANAN İŞLER

### 1. Register API — in-memory → DB ✅
**Dosya:** `backend/api/auth.py`

**Bug:** `kullanici_servisi` tamamen in-memory dict kullanıyordu, PostgreSQL'e hiç yazmıyordu.
**Fix:** `/kayit` ve `/register` endpoint'leri artık direkt `INSERT INTO users` + `await db.commit()` yapıyor.
**Kritik detay:** `CAST(:role AS userrole)` — asyncpg `::` cast syntax'ını desteklemiyor.
**Test:** HTTP 201 + DB'de kayıt oluştu ✅

### 2. Frontend port 8001 ✅
**Dosya:** `frontend/.env`
```
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001
```
**Config:** `frontend/src/config/index.ts` → `VITE_API_URL ?? 'http://localhost:8000'`
Boşsa 8000'e fallback yapıyordu. Artık düzeltildi.
**Frontend rebuild + Docker deploy tamamlandı:**
```powershell
cd C:\Users\husey\kiro2\frontend
npm run build  # 2.5 dakika sürer
docker cp .\dist\. kiro2-frontend:/usr/share/nginx/html/
docker exec kiro2-frontend nginx -s reload
```

### 3. topic_hierarchy 35 yeni konu ✅
**Migration:** `backend/migrations/010_topic_hierarchy_v3.sql`
**Eklendi:** SOSYAL(5) + GENEL(5) + FEN(5) + GEOMETRI(5) + EDEBIYAT(5) + TARIH(+5) + COGRAFYA(+5)
**Toplam:** 12 ders, 105 aktif konu
**NOT NULL zorunlu kolonlar:** `osym_frequency`, `total_questions`, `average_difficulty` — migration'larda hepsini belirt!

### 4. Celery beat — daily_plans otomasyonu ✅
**Dosya:** `backend/tasks/daily_plan_tasks.py` (yeni oluşturuldu)
**Schedule:** `core/celery_app.py` → `refresh-daily-plans` her gece **02:00**
```python
"refresh-daily-plans": {
    "task": "tasks.refresh_daily_plans",
    "schedule": crontab(hour=2, minute=0),
}
```
**Çalıştırmak için:**
```powershell
cd C:\Users\husey\kiro2\backend
python -m celery -A core.celery_app worker --loglevel=warning
python -m celery -A core.celery_app beat --loglevel=warning
```

### 5. CAT → frontend sync ✅
**Backend:** `backend/app/services/cat_session.py`
CAT bitince response'a `"plan_refresh_needed": True` eklendi.
**Frontend:** `frontend/src/hooks/useCATSession.ts`
`plan_refresh_needed` görününce `cat-complete` CustomEvent dispatch edildi.
`CATSessionState`'e `subject_id?: string` eklendi.

### 6. mastery=97.7% bug fix ✅
CAT yapılmamış ders → mastery=0%, needs_cat=True, priority=100
**Dosya:** `backend/app/services/learning_path_orchestrator.py`

### 7. daily_plans yenilendi ✅
`python C:\Temp\fill_daily_plans.py` — 52 plan bugün tarihiyle üretildi.

---

## 🚨 KALAN TEK SORUN — Veli /cocuklar Endpoint (SONRAKI OTURUM)

### Mevcut durum
- Veli login: ✅ HTTP 200
- `/api/v1/veli/cocuklar`: ❌ HTTP 400 "Veli profili bulunamadı"
- `parent_child` tablosunda bağlantı var (veli_id → ogrenci_id)
- `parent_profiles` tablosunda profil var

### Root cause
`veli_servisi.veli_cocuklarini_getir()` → `kullanici_servisi.veli_profili_getir()` → in-memory dict → boş dönüyor.

### Yapılan fix'ler (kısmen uygulandı)
`backend/api/veli.py` içindeki `mevcut_veli_getir()`:
- ✅ `kullanici_servisi` → `get_current_user` (DB-backed JWT)
- ✅ `UserRole.PARENT.value` enum fix (`str(enum)` değil `.value` kullan)
- ✅ `SimpleNamespace` wrapper (frozen pydantic bypass)
- ❌ `veli_servisi.veli_cocuklarini_getir()` hâlâ in-memory

### Çözüm (uygulanacak)
`cocuk_listesi_getir` fonksiyonuna `db` parametresi ekle,
`parent_child` tablosunu direkt sorgula:

```python
# backend/api/veli.py → cocuk_listesi_getir fonksiyonu
@router.get("/cocuklar", ...)
async def cocuk_listesi_getir(
    mevcut_veli=Depends(mevcut_veli_getir),
    db: AsyncSession = Depends(get_db),      # ← EKLE
):
    from sqlalchemy import text
    veli_id = mevcut_veli.kullanici_id

    # parent_child tablosundan direkt oku
    result = await db.execute(text("""
        SELECT u.id, u.first_name, u.last_name, u.email
        FROM parent_child pc
        JOIN users u ON u.id = pc.child_id
        WHERE pc.parent_id = :veli_id
    """), {"veli_id": veli_id})
    rows = result.fetchall()

    cocuklar = [
        {"kullanici_id": str(r[0]), "ad_soyad": f"{r[1]} {r[2]}".strip(), "email": r[3]}
        for r in rows
    ]
    return {"success": True, "data": cocuklar, "message": f"{len(cocuklar)} çocuk bulundu"}
```

### Test
```powershell
python -c "
import urllib.request, json
def api(m,p,b=None,t=None):
    h={'Content-Type':'application/json'}
    if t: h['Authorization']=f'Bearer {t}'
    req=urllib.request.Request(f'http://localhost:8001{p}',method=m,data=json.dumps(b).encode() if b else None,headers=h)
    try: r=urllib.request.urlopen(req,timeout=10); return json.loads(r.read()),r.status
    except urllib.error.HTTPError as e: return json.loads(e.read()),e.code
r,s=api('POST','/api/v1/auth/login',{'email':'veli_test@kiro2.com','password':'VeliTest2026!'})
t=r.get('access_token','')
print('Login:',s)
r2,s2=api('GET','/api/v1/veli/cocuklar',t=t)
print('Cocuklar:',s2,r2)
"
```

---

## ⚠️ BİLİNEN AÇIK SORUNLAR

| # | Sorun | Etki | Çözüm |
|---|-------|------|-------|
| 1 | Veli /cocuklar (in-memory bypass) | Veli paneli çalışmıyor | Yukarıdaki DB-direct kod |
| 2 | IRT parametreleri sentetik (a≈1, b≈0, c≈0.25) | CAT soru seçimi optimal değil | 50+ gerçek yanıt birince `--force` kalibre et |
| 3 | DailyPlanPage `cat-complete` event listener | CAT bitince plan otomatik güncellenmez | `frontend/src/pages/DailyPlanPage.tsx`'e event listener ekle |

---

## 📋 SIRADAKI SPRINT ÖNERİLERİ

### 🔴 Acil (1-2 saat)
1. **Veli /cocuklar DB-direct fix** — yukarıdaki kodu uygula
2. **DailyPlanPage cat-complete listener** — CAT bitince plan yenile

### 🟡 Orta (yarım gün)
3. **IRT gerçek veri kalibrasyonu** — 50+ yanıt birikince:
   ```powershell
   cd C:\Users\husey\kiro2\backend
   python scripts\irt_calibration_runner.py --force --limit 360 --min-responses 50
   ```
4. **Celery başlatma** — Günlük plan otomasyonu için:
   ```powershell
   python -m celery -A core.celery_app worker --loglevel=warning --concurrency=2
   python -m celery -A core.celery_app beat --loglevel=warning
   ```

### 🟢 Sonraki sprint
5. **TÜBİTAK 1512 BİGG** başvuru belgesi
6. **KIRO Destanı** animasyonları (Three.js)
7. **OCR Pipeline** — Gemini API key gerekiyor (2594 PNG bekliyor)
8. **d-dataset YOLO cevap crop'ları** — 725 crop işlenmemiş

---

## 🔑 ÖNEMLİ DOSYA YOLLARI

```
# Backend — değiştirilen dosyalar
backend/api/auth.py                              ← Register DB-backed ✅
backend/api/veli.py                              ← mevcut_veli_getir fix ✅ | /cocuklar ❌
backend/app/services/cat_session.py              ← user_theta UPSERT + plan_refresh_needed ✅
backend/app/services/learning_path_orchestrator.py ← needs_cat fix ✅
backend/app/api/learning_path_daily.py           ← LP endpoints ✅
backend/tasks/daily_plan_tasks.py                ← Celery task (YENİ) ✅
backend/core/celery_app.py                       ← refresh-daily-plans schedule ✅
backend/migrations/010_topic_hierarchy_v3.sql    ← 35 yeni konu ✅

# Frontend — değiştirilen dosyalar
frontend/.env                                    ← VITE_API_URL=8001 ✅
frontend/src/hooks/useCATSession.ts              ← cat-complete event + subject_id ✅

# C:\Temp\ test scriptleri
C:\Temp\test_all_final.py    ← 9 testi birden çalıştırır (8/9 geçiyor)
C:\Temp\fill_daily_plans.py  ← daily_plans manuel yenile
C:\Temp\test_veli.py         ← veli endpoint testi
C:\Temp\db_full_status.py    ← DB tam durum raporu
C:\Temp\setup_veli.py        ← veli+öğrenci hesabı + parent_child bağlantısı kur
```

---

## 📡 ÇALIŞAN API ENDPOINT'LER (http://localhost:8001)

```
# Auth
POST /api/v1/auth/register   → {email, sifre, ad_soyad, rol} → DB'ye yazar ✅
POST /api/v1/auth/login       → {email, password} → JWT token ✅

# Learning Path
GET  /api/v1/learning-path/status   → 9 ders: θ, mastery, needs_cat, ZPD
GET  /api/v1/learning-path/today    → günlük plan (blok bazlı)
GET  /api/v1/learning-path/weekly   → 7 günlük takvim
GET  /api/v1/learning-path/next     → ?subject=MATEMATIK
POST /api/v1/learning-path/goal     → {exam_type, exam_date, daily_minutes}

# CAT
POST /api/v1/cat/sessions            → CAT başlat (plan_refresh_needed: True döner)
POST /api/v1/cat/sessions/{id}/answer

# FSRS
GET  /api/v1/fsrs/due
POST /api/v1/fsrs/review

# Veli (kısmen çalışıyor)
GET  /api/v1/veli/cocuklar          → ❌ 400 (DB-direct fix gerek)

# Diğerleri
GET  /api/v1/estimate/tyt
GET  /api/v1/estimate/full
GET  /api/v1/leagues/current
GET  /api/v1/duel/rating
POST /api/v1/placement/start
GET  /api/v1/calibration/status
```

---

## ⚡ HIZLI KONTROL KOMUTLARI

```powershell
# Tüm fix'leri test et (8/9 geçmeli)
python C:\Temp\test_all_final.py

# DB durumu
python C:\Temp\db_full_status.py

# daily_plans manuel yenile
cd C:\Users\husey\kiro2\backend
python C:\Temp\fill_daily_plans.py

# Frontend rebuild + deploy (port değişince)
cd C:\Users\husey\kiro2\frontend
npm run build
docker cp .\dist\. kiro2-frontend:/usr/share/nginx/html/
docker exec kiro2-frontend nginx -s reload

# IRT yeniden kalibre et (veri birikince)
cd C:\Users\husey\kiro2\backend
python scripts\irt_calibration_runner.py --force --limit 360 --min-responses 50
```

---

## 🌐 FRONTEND SAYFALARI (http://localhost:3001)

| URL | Açıklama | Durum |
|-----|---------|-------|
| `/dashboard` | Ana ekran | ✅ |
| `/cat` | Adaptif test | ✅ |
| `/assessment` | Placement Test | ✅ |
| `/fsrs-review` | Flashcard tekrar | ✅ |
| `/daily-plan` | Günlük plan (ZPD+IRT+FSRS) | ✅ |
| `/learning-path-map` | Konu haritası | ✅ |
| `/league` | Lig tablosu | ✅ |
| `/duel` | 1v1 düello | ✅ |
| `/estimate` | TYT/AYT puan tahmini | ✅ |
| `/parent-new` | Veli paneli | ⚠️ /cocuklar 400 |
| `/kiro-destan` | 12 Türk dönemi haritası | ✅ |
| `/admin/calibration` | IRT kalibrasyon dashboard | ✅ |
