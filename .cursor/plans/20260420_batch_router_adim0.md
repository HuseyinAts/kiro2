# Batch ADIM 0 — Kalan 12 Disabled Router Durum Tespiti

**Tarih:** 2026-04-20
**Pilot referansı:** `.cursor/plans/20260420_diary_api_activation.md` (tamamlandı)
**Prior knowledge:** `backend/_pilots/20260420_diary_api_state.md` (okunmalı, soruları tekrarlama)
**Yürütücü:** Composer 2 (terminal sorguları, pattern matching)
**Süre tahmini:** 30-45 dakika

---

## Hedef

`KIRO2_SESSION_BRIEFING.md`'nin "DISABLED ROUTERLAR (13 adet, 06.04.2026)" listesinde **diary_api hariç** kalan 12 router için toplu **ADIM 0 durum tespiti** yap. Çıktı: matrix rapor, aşama sınıflandırması, sonraki pilot önerisi.

**KOD DEĞİŞTİRME. MIGRATION ÇALIŞTIRMA. COMMIT YAPMA.** Sadece tespit.

---

## Prior Knowledge (Önce Oku)

`backend/_pilots/20260420_diary_api_state.md` — diary pilot ADIM 0 çıktısı. Şunları zaten biliyorsun:

- `users.id` = `character varying` (VARCHAR, UUID değil)
- `DISABLED_ROUTERS = {}` (en az bu branch/ortamda, briefing çelişiyor)
- Alembic head şu an `student_review_drift_001`
- `loader.py` diary'i `learning` kategorisinde `/api/v1/diary` prefix'i ile kayıt eder
- Tablolar DB'de var ama Alembic grafiğinde olmayabilir (drift pattern'i)

Bu bilgileri her router için tekrar sorgulamanaya gerek yok.

---

## 12 Router Listesi (Briefing'den)

| # | Router | Briefing kategorisi | Not |
|---|---|---|---|
| 1 | `api.v1.semantic_search` | ChromaDB bağımlı | ES alternatifi P2 |
| 2 | `api.clustering_api` | ChromaDB bağımlı | ES alternatifi P2 |
| 3 | `api.v1.content_recommendation` | ChromaDB bağımlı | ES alternatifi P2 |
| 4 | `api.v1.duplicate_detection` | ChromaDB bağımlı | ES alternatifi P2 |
| 5 | `api.productive_failure_api` | Eksik tablo | `sub_problems` var, `solution_steps` belirsiz |
| 6 | `api.live_session_routes` | Eksik tablo | En büyük — 11 alt tablo |
| 7 | `api.v1.expert_agents_api` | Eksik servis | Expert agent framework deploy edilmemiş |
| 8 | `api.vision_api` | Eksik entegrasyon | YOLO + Gemini pipeline |
| 9 | `api.offline_sync_api` | PWA/Offline | |
| 10 | `api.pwa_sync_api` | PWA/Offline | |
| 11 | `api.revolutionary_features` | Çoğu mock | |
| 12 | `api.team_challenges_api` | Çoğu mock | |

---

## Her Router İçin 5 Kontrol

### K1 — Router `DISABLED_ROUTERS`'de mi?

```powershell
Select-String -Path "C:\Users\husey\kiro2\backend\routers\loader.py" -Pattern "<router_name>" -Context 2
```

### K2 — Router `ROUTER_MAPPING`'de mi?

Aynı dosyada ROUTER_MAPPING sözlüğünde string olarak var mı? Varsa kategori ve modül yolu ne?

### K3 — Canlı log'da yükleme durumu

```powershell
docker logs kiro2-backend --tail 500 2>&1 | Select-String "<router_kısa_adı>"
```

Ara: "Registered" (başarılı), "Failed to import" (hata), veya hiç satır yok (henüz denenmemiş).

### K4 — Beklenen tablolar DB'de var mı?

İlk önce model dosyasını bul:

```powershell
Get-ChildItem -Path "C:\Users\husey\kiro2\backend\models" -Filter "*<alan>*.py"
docker exec kiro2-backend bash -c "grep -h '__tablename__' /app/models/<model>.py"
```

Sonra PostgreSQL'de sorgula:

```powershell
$env:PGPASSWORD='postgres'
$tables = "'tbl1','tbl2','tbl3'"
$q = "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ($tables) ORDER BY table_name;"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -c $q
```

### K5 — FK tipleri uyumlu mu?

Eğer K4'te tablolar varsa:

```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name IN (...)
  AND column_name IN ('id','user_id')
ORDER BY table_name;
```

Beklenen: `id` ve `user_id` → `character varying`. UUID çıkarsa **Aşama C** (tip uyumsuz).

---

## Çıktı Şeması

`backend/_pilots/20260420_batch_router_state.md` dosyasına yaz.

### Bölüm 1: Özet Matrix

| # | Router | K1 Disabled? | K2 Mapping? | K3 Log | K4 Tablolar | K5 Tip | **Aşama** |
|---|---|---|---|---|---|---|---|
| 1 | semantic_search | ? | ? | ? | ? | ? | ? |
| 2 | clustering_api | ? | ? | ? | ? | ? | ? |
| ... |

### Bölüm 2: Aşama Sınıflandırması

```markdown
## Aşama A — Tablo yok, migration lazım
- [router listesi]

## Aşama B — Tablolar var, Alembic drift var (diary gibi)
- [router listesi]
  - en olası çoğunluk: briefing 06.04'te "58 eksik tablo oluşturuldu" diyor
  - Aşama B olanlar için tek ortak karar: Alembic drift stratejisi (A/B/C seçeneği)

## Aşama C — Tablolar var, tip uyumsuz (UUID)
- [router listesi]

## Aşama D — Dış bağımlılık (ChromaDB yok, YOLO yok)
- [router listesi]
  - Bu grup: ADIM 0 yetmiyor, ayrı altyapı kararı

## Aşama E — Belirsiz / manuel inceleme
- [router listesi]
```

### Bölüm 3: Sonraki Pilot Önerisi

Hangisi bir sonraki pilot için en uygun? Kriterler:
- Aşama A veya B (net yol var)
- Dış bağımlılık yok
- Briefing'de risk uyarısı yok
- Tablo sayısı orta (diary 8 tablo başardı, 11+ için daha dikkat)

**Öneri formatı:**
```markdown
## Sonraki pilot önerisi

**En uygun:** <router_name>
**Neden:** <1-2 cümle>
**Aşama:** B
**Tablo sayısı:** X
**Bilinmeyenler:** <varsa>
```

### Bölüm 4: Briefing Düzeltme Notları

Pilot sırasında fark edilen briefing-kod çelişkilerini listele (diary pilotunda `.token` vs `.access_token` gibi). Sonra `KIRO2_SESSION_BRIEFING.md` güncellenebilir.

### Bölüm 5: Ham komut çıktıları özeti

Her router için 2-3 satır — tam log/sql output'u değil, özet.

---

## Yasaklar

- ❌ Kod değişikliği (loader.py, migration dosyası, model dosyası — hiçbiri)
- ❌ `alembic upgrade/downgrade` çalıştırma
- ❌ `docker restart kiro2-backend` (lüzumsuz yan etki)
- ❌ `git add/commit` — rapor dosyasını yaz, commit insana bırak
- ❌ Tablo oluşturma / drop / ALTER
- ❌ Production/staging'e bağlanma — sadece `localhost:5434` kiro2 DB

---

## Durma Noktaları — "Bana Sor, Sonra Devam Et"

Aşağıdaki durumlarda **raporu çıkartma, dur ve kullanıcıya bildir**:

1. **Beklenmedik tablolar** (`backend/models/<alan>.py`'da olmayan tablolar var DB'de)
2. **UUID FK bulursan** (Aşama C — tip migrasyonu ciddi risk)
3. **Docker container durmuşsa** (`docker ps` kontrolü başarısız)
4. **Alembic heads birden fazla** (çift head → merge gerek)
5. **Kullanıcılar tablosunda veri tipi VARCHAR değilse** (briefing kuralı bozulmuş)
6. **`loader.py`'da `DISABLED_ROUTERS` boş değilse** (briefing haklı çıktı, durum değişti)

---

## Başarı Ölçütleri

- [ ] `backend/_pilots/20260420_batch_router_state.md` yazıldı
- [ ] 12 router için 5 kontrolün de matrisi dolu (? bırakılmadı)
- [ ] Aşama sınıflandırması yapıldı (her router A/B/C/D/E'de)
- [ ] Sonraki pilot önerisi gerekçeli
- [ ] Hiç kod değiştirilmedi (`git status` sadece yeni `_pilots/` dosyasını göstermeli)
- [ ] Brifing düzeltme notları toplandı

---

## Referanslar

- **Pilot pattern:** `.cursor/plans/20260420_diary_api_activation.md`
- **Prior state:** `backend/_pilots/20260420_diary_api_state.md`
- **Briefing:** `KIRO2_SESSION_BRIEFING.md` → "DISABLED ROUTERLAR (13 adet, 06.04.2026)" bölümü
- **Loader:** `backend/routers/loader.py`
- **Artifact yazım kuralı:** `backend/_pilots/README.md`
