---
name: systematic-debugging
description: Sistematik hata ayiklama metodolojisi — phantom sorun ayiklama, kanit toplama, katmanli analiz
trigger: always
priority: high
---

# Systematic Debugging Methodology

## ALTIN KURAL: TAHMiN ETME, GOR

Her sorun icin: ONCE gercek kanit topla, SONRA yorum yap.
"Muhtemelen X'tir" YASAK — "X ciktisi Y gosteriyor" ZORUNLU.

---

## ADIM 1: Sorun Siniflandirma (30 saniye)

Gelen sorunu siniflandir:

| Sinif | Ornek | Ilk Aksiyon |
|-------|-------|-------------|
| **Infra** | 503, timeout, connection refused | `docker ps`, `pg_isready`, `redis-cli ping` |
| **Runtime** | 500, traceback, ImportError | Container log: `docker logs kiro2-backend --tail 50` |
| **Logic** | 200 + yanlis/bos data | DB sorgu + is_active kontrol |
| **Test** | pytest failure | Fail mesajini oku, assert'i anla |
| **Docker** | Container'da calismaz, local'de calisir | Image vs local fark kontrolu |
| **Phantom** | Raporda var ama gercekte yok | Grep + DB kontrol ile dogrula |

---

## ADIM 2: Phantom Sorun Filtresi (KRITIK)

Bir sorun raporlandiginda ONCE dogrula:

```
1. "Tablo X eksik" → SELECT * FROM information_schema.tables WHERE table_name = 'X'
2. "Kolon Y yok" → SELECT column_name FROM information_schema.columns WHERE table_name = 'X'
3. "Dosya Z kayitli degil" → grep -c 'Z' <kayit-dosyasi>
4. "Endpoint 404" → grep 'endpoint_pattern' routers/loader.py
5. "Modul import edilemiyor" → python -c "from X import Y; print('OK')"
```

### Phantom Sorun Kaliplari (Gercek ornekler, Session 121)

| Raporlanan | Gercek Durum | Nasil Yakalanir |
|-----------|-------------|-----------------|
| `cat_responses` tablo eksik | SQL alias, tablo degil | grep `CREATE TABLE cat_responses` = 0 |
| `irt_calibration_jobs` eksik | Gercek ad `irt_calibration_history` | grep codebase-wide |
| `subjects.slug` crash | Kod slug kullanmiyor, inline dict var | grep `s.slug` tum app/api/ = 0 |
| `dag_topics/dag_edges` eksik | `topic_hierarchy` + `topic_prerequisites` | Model dosyalari oku |
| loader.py'de entry yok | 6/6 entry mevcut | Dosyayi dogrudan oku |
| `emergency_content.sql` yok | Legacy, bos `questions`'a insert | Dosya icerigini oku |

**Kural:** 6 "kritik" sorundan 4'u phantom cikti (%67). Rapor GUVENMEDEN ONCE dogrula.

---

## ADIM 3: Docker vs Local Ayrimi

Container'da calismayan bir sey varsa:

```bash
# 1. Image ne zaman build edildi?
docker inspect kiro2-backend --format '{{.Created}}'

# 2. Container icindeki dosya local ile ayni mi?
docker exec kiro2-backend bash -c "grep -c 'PATTERN' /app/FILE"
# vs
grep -c 'PATTERN' backend/FILE

# 3. Container env dogru mu?
docker exec kiro2-backend env | grep KEY

# 4. Container icinden erisilebilirlik
docker exec kiro2-backend bash -c "python -c \"import redis; r=redis.from_url('REDIS_URL'); print(r.ping())\""
```

### Docker Sorunlarin %90'i 3 Sebep

1. **Eski image** — `docker compose build --no-cache backend` coz
2. **Yanlis env var** — `.env.mvp` kontrol (ozellikle hostname: `localhost` vs `host.docker.internal`)
3. **Network izolasyonu** — container icinden `localhost` = container kendisi, host'a `host.docker.internal` ile ulas

---

## ADIM 4: Katmanli Hata Ayiklama

Her katmani SIRASIYA kontrol et — atla:

```
Katman 1: ALTYAPI
  pg_isready -p 5434
  redis-cli ping
  docker ps (tum servisler healthy mi?)
  curl localhost:8000/health

Katman 2: IMPORT / MODUL
  python -c "from modül import sinif"
  Docker icinde ayni import calisiyor mu?

Katman 3: VERI
  SELECT COUNT(*) FROM tablo (bos mu?)
  Dogru tablo mu? (question_bank vs questions)
  is_active filtresi var mi?

Katman 4: LOGIC
  Endpoint'i curl ile cagir
  Response body'yi oku
  Log'lari kontrol et
```

**Kural:** Katman 1 basarisizsa Katman 2-4'e gecme. Altyapi sorunu iken kod debug etme.

---

## ADIM 5: Kanit Tablosu (Fix Oncesi ZORUNLU)

Fix yazmadan ONCE bu tabloyu doldur:

| Soru | Cevap (GERCEK OUTPUT ile) |
|------|---------------------------|
| Hata mesaji ne? | [pytest/curl/log ciktisi — kopyala-yapistir] |
| Hangi katmanda? | [Infra / Import / Veri / Logic / Docker] |
| Phantom mi? | [Evet: gercek ad X / Hayir: gercekte mevcut] |
| Root cause? | [dosya:satir veya config:key] |
| Docker'a ozgu mu? | [Evet: image/env/network / Hayir: local'de de olur] |
| Fix scope? | [dosya listesi, max 3] |
| Yan etki riski? | [Hangi baska servis/endpoint etkilenir] |

---

## ADIM 6: Fix Sonrasi Dogrulama

```bash
# 1. Ayni hata tekrarlanmadigini dogrula
pytest tests/SPECIFIC_TEST.py -v --tb=short

# 2. Yan etki kontrolu
pytest -x --tb=short -q  # veya etkilenen modulu calistir

# 3. Docker'da da calistigini dogrula (Docker sorunuysa)
docker compose build --no-cache backend && docker compose up -d
docker exec kiro2-backend bash -c "DOGRULAMA_KOMUTU"

# 4. Ruff
ruff check DEGISEN_DOSYALAR --select=E,F,W
```

---

## ANTI-PATTERN'LER

| Yapma | Yap |
|-------|-----|
| Rapordaki her sorunu gercek kabul et | Grep + DB ile dogrula |
| "Tablo yok" duyunca migration yaz | Farkli isimle var mi kontrol et |
| Container'da 404 gorunde kod degistir | Image rebuild dene ONCE |
| `localhost` kullanan env'i docker'da birak | `host.docker.internal` kullan |
| Birden fazla sorunu ayni anda fix et | Tek tek, dogrulayarak ilerle |
| Phantom soruna zaman harca | 30 saniye dogrulama ile ele |
| Log okumadan tahmin yap | `docker logs --tail 50` ile GERCEK hatayi gor |

---

## HIZLI REFERANS: Sik Karsilasilan Phantom'lar

| Semptom | Gercek Sebep |
|---------|-------------|
| "Tablo X yok" | Farkli isimle var (orn: `cat_responses` → `kiro2_learning_events` alias) |
| "Endpoint 404" | Docker image eski, loader.py guncellenmemis |
| "Kolon Y yok" | Inline dict/mapping var, kolon gerekmez |
| "Redis baglanamiyor" | `localhost` vs `host.docker.internal` |
| "Migration eksik" | Tablo zaten var, farkli migration'da olusturulmus |
| "Modul bulunamiyor" | `requirements-minimal.txt`'te yok (Docker'a ozgu) |
