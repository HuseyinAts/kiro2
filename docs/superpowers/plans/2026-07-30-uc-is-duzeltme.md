# Üç İş Düzeltme Planı — 30 Temmuz 2026

**Kapsam:** (A) admin content POST/DELETE kusuru, (B) Elasticsearch ↔ PostgreSQL
senkron boşluğu, (C) ölü CI workflow YAML.

**Durum:** HEAD `8d8bdf31f`, dal `feature/self-evolution-optimization`,
`git status --short` BOŞ. Hiçbir fix henüz uygulanmadı.

**Bu plan yazılırken canlı doğrulananlar** (plan yazarının kendi ölçümü, teşhis
raporlarından bağımsız):

| Ölçüm | Komut | Sonuç |
|---|---|---|
| Workflow dosya sayısı | `glob('.github/workflows/*.yml')` | **11** (teşhisteki "12" yanlış — 12. giriş `desktop.ini`) |
| golden-flows YAML | `yaml.safe_load` | `FAIL … line 172, column 43` |
| quality-gate YAML (düz) | `yaml.safe_load` | **OK** ← düz yükleyici kusuru KAÇIRIYOR |
| quality-gate YAML (dup-key) | özel `SafeLoader` alt sınıfı | `FAIL: tekrarli anahtar: 'workflow_dispatch'` |
| golden-flows:172 ham içerik | `repr(satir)` | `'      - name: AST lint — Pydantic \`user_id: int\` type lie (rule-of-five)'` |
| quality-gate:17,18 | `repr` | ikisi de `'  workflow_dispatch:'` |
| `mv_safe_for_beta` | `psql SELECT count(*)` | **25 127** satır (matview MEVCUT) |
| ES index | `_cat/indices` | `turkiye_sinav_platform` → **64 270** doc, `docs.deleted=0`, `creation.date 2026-04-01T01:51:50Z` |
| `admin.py:425` | dosya okuma | `basarili = await admin_servisi.soru_sil(soru_id)` ✔ |
| `admin_service.py:31` | dosya okuma | `current_user = kwargs.get("current_user") or (args[0] if args else None)` ✔ |
| `admin_service.py:78-99` | dosya okuma | `hasattr(x,"rol")` + `x.aktif` bekliyor ✔ |
| `soru_bankasi_service.py:188` | dosya okuma | `async def soru_ekle(self, soru_data: dict)` ✔ |
| `elasticsearch.py:160-170` | dosya okuma | öğrenci-güvenli süzgeç **ZATEN VAR** (dict-comprehension) ✔ |
| `STUDENT_SAFE_QUESTION_FIELDS` | `elasticsearch_service.py:27-45` | **17 alan**, `correct_answer` YOK ✔ |
| `test_admin_api.py` fixture'ları | dosya okuma | `admin_app:80`, `admin_client:105`, override `115-116`, `clear():123` ✔ |
| celery beat deseni | `celery_app.py:112-131` | `refresh-safe-pool-nightly` = `crontab(hour=3, minute=30)` ✔ |

---

## ⚠️ SIFIRINCI ADIM — SIRALAMADAN BAĞIMSIZ, İLK YAPILACAK

**"Severity de bir ölçümdür"** (`.claude/rules/audit-methodology.md`). Bu plandaki
tek yüksek-severity iddia — *"ES 9200 kimliksiz ve 0.0.0.0'a bağlı, dolayısıyla
64 270 sorunun cevap anahtarı auth'suz okunabiliyor"* — **sınama turunda yeniden
ölçülmedi, teşhisten devralındı**. Aciliyeti bu ölçüm belirler; plan sırası da
ondan sonra kesinleşir.

```bash
# S0.1 — Port bağlaması gerçekten 0.0.0.0 mı?
docker port turkiye_sinav_elasticsearch

# S0.2 — Kimlik doğrulama var mı? (401 beklenirse güvenli, 200 gelirse değil)
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:9200/

# S0.3 — Doküman düzeyinde cevap anahtarı var mı? (ASIL SORU)
curl -s -X POST http://localhost:9200/turkiye_sinav_platform/_count \
     -H 'Content-Type: application/json' \
     -d '{"query":{"exists":{"field":"correct_answer"}}}'

# S0.4 — Makine LAN'dan erişilebilir mi? (0.0.0.0 tek başına yetmez)
netstat -ano | grep ':9200'
```

**Karar kuralı:**

| S0.2 | S0.3 count | Sonuç |
|---|---|---|
| `200` (auth yok) | `> 0` | **YÜKSEK** — İŞ B sıranın BAŞINA alınır, ağ kısıtlaması (bind → `127.0.0.1`) reindex'ten ÖNCE yapılır |
| `401` | herhangi | ORTA — plandaki sıra aynen geçerli |
| `200` | `0` | DÜŞÜK — İŞ B yalnız kapı bypass'ı sorunudur |

**Bu ölçüm yapılmadan İŞ B'ye başlanmaz.** Maliyeti 4 komut, ~2 dakika. Ölçüm
sonucu bu dosyanın en altındaki "Ölçüm Kaydı" bölümüne yazılır.

---

## İŞ A — Admin content POST/DELETE kusuru

### A.0 Sınama kök nedeni ÇÜRÜTTÜ MÜ?

**KISMEN ÇÜRÜTTÜ — iki yönde.** Aşağıda hem orijinal iddia hem düzeltilmiş hâli.

| # | Orijinal iddia | Sınama verdikti | Düzeltilmiş kök neden |
|---|---|---|---|
| 1 | "POST 200 diyor ama yazmıyor — kök neden: `soru_hash` çakışması sessizce başarı raporlanıyor" | **MEKANİZMA DOĞRU, TEK SEBEP DEĞİL** | İki seri bağlı sebep: (1) çakışma sessiz başarı, (2) çakışan satır DELETE 500 verdiği için SİLİNEMİYOR → semptom kendi kendini besleyen kapalı döngü |
| 2 | "Fix = `duplicate_ok=False`" | **REDDEDİLDİ (A1'in fix'i olarak)** | Bedeli ölçüldü: `test_golden_flows.py:795` `assert resp.status_code == 200` → GF6w KIRMIZI. Kazancı ölçüldü: semptom **AYNEN KALIR** (admin yine hiçbir soruyu silemez). Bu, #451'in birebir hesabı |
| 3 | "DELETE 500 kök neden: `@admin_required` `args[0]` tuzağı" | **DOĞRU AMA DAR** | `args[0]`ı düzeltmek YETMEZ: `_admin_yetkisi_kontrol` `.rol`/`.aktif` bekliyor, `AuthenticatedUser` `.role` taşıyor → geçerli admin objesi verilse **BİLE** `False` döner. Konteynerde ölçüldü. İKİNCİ seri bağlı bastırıcı |
| 4 | (yok) | **YENİ ÖLÇÜM** | Severity **DÜŞÜK**: `adminService.deleteQuestion` tanımlı ama `.tsx` çağıranı yok; 17 saatlik logdaki tüm trafik GF probu. Bu "admin paneli bozuk" DEĞİL, "ölü admin özelliği + log gürültüsü" |
| 5 | (yok) | **YENİ ÖLÇÜM** | DELETE düzelince POST'un "sahte sahiplik" zinciri gerçek bir veri kaybı yoluna dönüşür: POST **BAŞKASININ** satırının id'sini "yeni eklendi" diye verir, çağıran onu siler. Bu, `duplicate_ok` fix'inin ihmal edilemez gerekçesidir — ama AYRI commit'te ve GF6w güncellemesiyle BİRLİKTE |

**Sonuç:** İŞ A **iki commit**tir, sırası bağlayıcıdır. A-1 (DELETE) semptomu
kaldırır. A-2 (POST) A-1'in açtığı sahte-sahiplik yolunu kapatır. A-2'siz A-1
eksik, A-1'siz A-2 değersizdir.

### A.1 Root Cause Analysis — A-1 (DELETE 500)

| Soru | Cevap |
|------|-------|
| **Hata ne?** | Canlı konteyner logu, 3/3: `INFO: 172.25.0.1:53280 - "DELETE /api/v1/admin/content/questions/3faf4e57-1f38-4771-a209-30839101cd2c HTTP/1.1" 500 Internal Server Error` (satır 6146, 13561, 21073). Traceback **YOK** — handler'ın `except Exception` bloğu loglamıyor. Ayırt edici sayımlar: `grep -c 'Soru silme hatası'` → **0**, `grep -c 'Admin yetki kontrolü hatası'` → **0**, kıyas `grep -c 'Traceback'` → **832** |
| **Root cause?** | `backend/api/admin.py:425` — `basarili = await admin_servisi.soru_sil(soru_id)` POZİSYONEL. → `backend/services/admin_service.py:31` `current_user = kwargs.get("current_user") or (args[0] if args else None)` → `args[0]` = soru_id. → `backend/services/admin_service.py:78-99` `_admin_yetkisi_kontrol` bu string'i DEPRECATED in-memory `KullaniciServisi`'de arar (0 kayıt) → `None` → `False` → `AdminAuthorizationError` (gövde HİÇ çalışmadan) → `admin.py:433-437` çıplak `except Exception` → HTTP 500. **İKİNCİ BASTIRICI:** aynı fonksiyon `hasattr(x,"rol")` + `x.aktif` bekler; `AuthenticatedUser` `.role` taşır, `.rol`/`.aktif` YOK → geçerli admin verilse bile `else: return False` |
| **Doğru tablo mu?** | Evet. Yaprak `soru_bankasi_servisi.soru_sil` → `models.question_bank.QuestionBankItem` → `question_bank` (187 835 satır prod). `questions` legacy'ye dokunulmuyor. Hedef satır canlı: `SELECT id,is_active FROM question_bank WHERE id='3faf4e57-…'` → 1 satır, `is_active=t`. Yani 500 "satır yok"tan DEĞİL — kod satıra hiç BAKMADI |
| **Altyapı OK mu?** | Evet, elendi. `pg_isready -p 5434` OK; `mv_safe_for_beta` 25 127 satır okunabiliyor; backend `/health` 200; host↔konteyner `md5sum` 3/3 eşit (`admin.py` `468ebf22…`, `admin_service.py` `38710087…`, `user_service.py` `f1d78918…`); konteyner dosya `mtime` (2026-07-02 22:03Z / 2026-06-11 15:45Z) < süreç başlangıcı (2026-07-30T01:48:07Z) → **çalışan sürüm okuduğum sürüm**. `.pyc` bayatlığı bu yolla elendi (`inspect.getsource` diski okur, tek başına elemez) |
| **Fix scope?** | **1 dosya:** `backend/api/admin.py` (1 fonksiyonel satır). **+1 test dosyası:** `backend/tests/unit/test_admin_api.py` (2 mevcut testin patch hedefi güncellenir + 2 yeni test) |

### A.2 Root Cause Analysis — A-2 (POST sessiz no-op)

| Soru | Cevap |
|------|-------|
| **Hata ne?** | Canlı log, 3 kez (15:32:58 / 15:36:01 / 15:39:33): `WARNING - Duplicate question detected (IntegrityError on soru_hash). Returning existing question. Error: … duplicate key value violates unique constraint "uq_qb_soru_hash_active"` ve **HEMEN ARDINDAN** `INFO: "POST /api/v1/admin/content/questions HTTP/1.1" 200 OK`. DB tarafı: `SELECT count(*) FILTER (WHERE created_at::date='2026-07-30') FROM question_bank` → **0**; `max(created_at)` → **2026-06-22 23:55:40** |
| **Root cause?** | `backend/services/soru_bankasi_service.py:344` `except IntegrityError` → `:358-359` `if existing: return existing` — mevcut satırı döndürüyor. `backend/api/admin.py:355-375` bu satırı koşulsuz `{"success": true, "message": "Soru başarıyla eklendi"}` zarfına sarıyor. Yani kusur "yazma yolu bozuk" DEĞİL — **çakışma sessizce başarı olarak raporlanıyor**. Yazma yolu çalışıyor: 22 Haz'daki `3faf4e57` satırını tam olarak bu uç yarattı (`created_by=admin@kiro2.com`) |
| **Doğru tablo mu?** | Evet, `question_bank`. Kısıt: `CREATE UNIQUE INDEX uq_qb_soru_hash_active ON public.question_bank USING btree (soru_hash) WHERE (is_active = true)` — **kısmi** index, yalnız aktif satırları kapsar (A-1 fix'i sonrası davranışı bu belirler) |
| **Altyapı OK mu?** | Evet. Rakip hipotez elendi: `SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname='question_bank'` → `f | f`. `question_bank`'ta **RLS KAPALI** — "kiro2_app RLS yüzünden yazamıyor" hipotezi ölü. (Not: MEMORY.md'deki "79 tabloda FORCE RLS" bu tabloyu KAPSAMIYOR — drift) |
| **Fix scope?** | **3 dosya:** `backend/services/soru_bankasi_service.py` (imza + 1 guard), `backend/api/admin.py` (1 kwarg), `backend/tests/e2e/test_golden_flows.py` (GF6w yükü benzersizleştirilir — fix'in ZORUNLU parçası) |

### A.3 TDD — A-1 (DELETE)

#### Adım 1 — Fail eden testi yaz

**Tam dosya yolu:** `C:/Users/husey/kiro2/backend/tests/unit/test_admin_api.py`
(MEVCUT dosya, 1019 satır — `class TestDeleteQuestion` satır 782'de. Aşağıdaki
iki test bu sınıfın SONUNA, satır ~825 civarına eklenir.)

**Neden bu dosya:** `admin_app` (satır 80: `FastAPI()` + `include_router(admin_router)`)
ve `admin_client` (satır 105, `dependency_overrides[get_current_user]` + `[get_db]`,
`ASGITransport`) fixture'ları burada ZATEN var ve doğrulandı. `from main import app`
KULLANILMIYOR → aiosqlite motoru ayağa kalkmıyor → asılma sınıfı dışında (bkz. A.6).

```python
    @pytest.mark.asyncio
    async def test_delete_question_reaches_leaf_service(
        self, admin_client: AsyncClient
    ):
        """DELETE yaprak servise ULAŞMALI — araya giren katman 500 üretiyordu.

        Canlı ölçüm (30 Tem 2026, 3/3):
            DELETE /api/v1/admin/content/questions/3faf4e57-… -> 500

        Kök neden: api/admin.py:425 `admin_servisi.soru_sil(soru_id)` çağrısını
        POZİSYONEL yapıyordu; services/admin_service.py:31 `args[0]`ı
        `current_user` sanıp SORU ID'sini DEPRECATED in-memory
        KullaniciServisi'nde (0 kayıt) arıyor -> False ->
        AdminAuthorizationError -> admin.py:433 çıplak `except Exception` -> 500.
        Gövde hiç çalışmadığı için logda 'Soru silme hatası' da yok (0 satır).

        KRİTİK: bu test `api.admin.admin_servisi`'yi BİLEREK patch'lemez. Bu
        sınıfın mevcut iki testi (satır 786, 797) onu KOMPLE patch'liyor ve tam
        bu yüzden üretim 500 verirken yeşil kaldılar — vakum testi. Burada
        yalnız EN ALT katman (DB'ye dokunan yaprak) stub'lanır; router -> servis
        yolu bozulmadan koşar, yani kapının kendisi ölçülür.
        """
        from services.soru_bankasi_service import soru_bankasi_servisi

        qid = "3faf4e57-1f38-4771-a209-30839101cd2c"
        leaf = AsyncMock(return_value=True)

        # patch.object: `admin_service.soru_bankasi_servisi is
        # soru_bankasi_service.soru_bankasi_servisi` -> True (konteynerde
        # ölçüldü), dolayısıyla import yolundan bağımsız olarak her iki
        # çağrı yolunu da yakalar.
        with patch.object(soru_bankasi_servisi, "soru_sil", leaf):
            response = await admin_client.delete(
                f"/api/v1/admin/content/questions/{qid}"
            )

        assert response.status_code == 200, (
            f"DELETE {response.status_code} döndü (beklenen 200): "
            f"{response.text[:300]}"
        )
        assert response.json()["success"] is True
        # Sahte fix'e karşı çivi: yalnız 200 dönmek yetmez, silme gerçekten
        # yaprak servise ve DOĞRU id ile inmiş olmalı.
        leaf.assert_awaited_once_with(qid)

    @pytest.mark.asyncio
    async def test_delete_question_missing_returns_404_from_leaf(
        self, admin_client: AsyncClient
    ):
        """Yaprak False dönünce 404 gelmeli — 500 değil.

        İki invaryantı aynı anda çiviler:
          (1) araya giren kırık katman atlandı,
          (2) `except HTTPException: raise` koruması duruyor (404'ün 500'e
              yutulması regresyonu geri gelirse bu test kırılır).
        """
        from services.soru_bankasi_service import soru_bankasi_servisi

        leaf = AsyncMock(return_value=False)
        with patch.object(soru_bankasi_servisi, "soru_sil", leaf):
            response = await admin_client.delete(
                "/api/v1/admin/content/questions/yok-boyle-bir-soru"
            )

        assert response.status_code == 404, response.text[:300]
        leaf.assert_awaited_once_with("yok-boyle-bir-soru")
```

**Gerekli import'lar:** `AsyncMock`, `patch`, `pytest`, `AsyncClient` — dosyanın
başında (satır 31-32) ZATEN mevcut, ek import gerekmez.

#### Adım 2 — Testi koş, FAIL'i doğrula

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/unit/test_admin_api.py::TestDeleteQuestion -v --no-header -p no:cacheprovider
```

**Beklenen FAIL mesajı (iki test için):**

```
FAILED tests/unit/test_admin_api.py::TestDeleteQuestion::test_delete_question_reaches_leaf_service
AssertionError: DELETE 500 döndü (beklenen 200): {"detail":"Islem basarisiz. Lutfen tekrar deneyin."}
assert 500 == 200

FAILED tests/unit/test_admin_api.py::TestDeleteQuestion::test_delete_question_missing_returns_404_from_leaf
AssertionError: assert 500 == 404
```

> **DÜRÜSTLÜK NOTU — DOĞRULANMADI.** Bu FAIL çıktısı **pytest koşturularak
> gözlemlenmedi** (her iki teşhis turu da salt-okunur mandat altındaydı). Türetildiği
> ölçülmüş ara adımlar: (a) konteynerde `_admin_yetkisi_kontrol('3faf4e57-…') -> False`
> + `IN-MEMORY başlatıldı` uyarısı, (b) A/B kontrol kolu
> `soru_sil(..., current_user=<geçerli admin>)` → `AdminAuthorizationError`,
> (c) canlı HTTP 3/3 → 500. **Fix yazmadan ÖNCE bu adım fiilen koşulup RED
> görülmelidir** — atlanırsa vakum-test riski açık kalır (bu depoda 8 testin 6'sı
> bir kez fix'ten önce de geçti).

#### Adım 3 — Minimal fix

**Dosya:** `C:/Users/husey/kiro2/backend/api/admin.py` (satır 417-437)

**ÖNCESİ:**

```python
@router.delete("/content/questions/{soru_id}", summary="Soru Sil")
async def soru_sil(
    soru_id: str, _: Kullanici = Depends(admin_kullanici_getir)
) -> dict[str, Any]:
    """
    Soruyu sil (Admin yetkisi gerekli)
    """
    try:
        basarili = await admin_servisi.soru_sil(soru_id)

        if basarili:
            return {"success": True, "message": "Soru başarıyla silindi"}
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı"
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
```

**SONRASI:**

```python
@router.delete("/content/questions/{soru_id}", summary="Soru Sil")
async def soru_sil(
    soru_id: str, _: Kullanici = Depends(admin_kullanici_getir)
) -> dict[str, Any]:
    """
    Soruyu sil (Admin yetkisi gerekli)
    """
    try:
        # admin_kullanici_getir yetki doğrulamasını ZATEN yapıyor (403).
        # admin_service.soru_sil'deki @admin_required dekoratörü iki ayrı
        # sebeple geçilemiyor: (1) pozisyonel çağrıda args[0]=soru_id'yi
        # current_user sanıyor, (2) _admin_yetkisi_kontrol `.rol`/`.aktif`
        # bekliyor ama AuthenticatedUser `.role` taşıyor -> doğru current_user
        # verilse bile False. Sonuç: her çağrı AdminAuthorizationError -> 500.
        # POST /content/questions aynı sebeple 2 Tem'de bypass edilmişti
        # (bkz. bu dosyada satır 349-352 yorumu); DELETE geride kalmıştı.
        from services.soru_bankasi_service import soru_bankasi_servisi

        basarili = await soru_bankasi_servisi.soru_sil(soru_id)

        if basarili:
            return {"success": True, "message": "Soru başarıyla silindi"}
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı"
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("admin /content/questions DELETE hatasi")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
```

Fonksiyonel değişiklik: **1 satır** (`admin_servisi` → `soru_bankasi_servisi`)
+ yerel import + yorum. `logger.exception` ayrı ve küçük bir teşhis-edilebilirlik
düzeltmesidir (`logger` dosyada zaten tanımlı; POST handler'ı satır 383'te aynı
satırı taşıyor, DELETE ve PUT'ta yok — bu 3 adet 500'ün 17 saatlik logda hiç iz
bırakmamasının sebebi tam olarak budur).

**ZORUNLU EŞLİK EDEN DEĞİŞİKLİK** — `backend/tests/unit/test_admin_api.py`,
mevcut iki testin patch hedefi. Yapılmazsa testler GERÇEK DB'ye düşer:
`os.environ.setdefault("DATABASE_URL", ...)` kabukta tanımlı bir DSN'i **EZMEZ**,
yani prod DSN'li bir kabukta gerçek `question_bank` satırı soft-delete edilebilir.

```python
# satır 786-789, test_delete_question_success — ÖNCESİ:
        with patch("api.admin.admin_servisi") as mock_service:
            mock_service.soru_sil = AsyncMock(return_value=True)

            response = await admin_client.delete("/api/v1/admin/content/questions/q1")

# SONRASI:
        with patch(
            "services.soru_bankasi_service.soru_bankasi_servisi.soru_sil",
            new=AsyncMock(return_value=True),
        ):
            response = await admin_client.delete("/api/v1/admin/content/questions/q1")


# satır 808-813, test_delete_question_returns_500_when_not_found — ÖNCESİ:
        with patch("api.admin.admin_servisi") as mock_service:
            mock_service.soru_sil = AsyncMock(return_value=False)

            response = await admin_client.delete(
                "/api/v1/admin/content/questions/missing"
            )

# SONRASI:
        with patch(
            "services.soru_bankasi_service.soru_bankasi_servisi.soru_sil",
            new=AsyncMock(return_value=False),
        ):
            response = await admin_client.delete(
                "/api/v1/admin/content/questions/missing"
            )
```

Bu patch hedefi aynı dosyada POST testleri için (satır 701)
`patch("services.soru_bankasi_service.soru_bankasi_servisi.soru_ekle")` olarak
ZATEN kullanılıyor — çalıştığı kanıtlı desen.

#### Adım 4 — GREEN doğrulama

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/unit/test_admin_api.py -v --no-header -p no:cacheprovider
# Beklenen: 48 passed (46 mevcut + 2 yeni), 0 failed

# Kapsam = değişikliğin kapsamı (.claude/rules/verification.md):
grep -rl "api.admin\|admin_servisi" backend/ --include="*.py" | grep -v "^backend/api/admin.py"
# çıkan her dosyanın testi de koşulur

ruff check backend/api/admin.py backend/tests/unit/test_admin_api.py --select=E,F,W --ignore=E501
```

#### Adım 5 — MUTASYON (fix'i bozacak değişiklik + öldüğünün kanıtı)

> Mutasyondan **ÖNCE commit et.** Geri alım: `git checkout HEAD -- <yol> && git status --short`
> → çıktı **BOŞ** olmalı. `git stash pop` KULLANMA: index'e değil çalışma ağacına
> koyar, sonraki `git checkout --` staged fix'i siler (30 Tem'de iki kez veri kaybı).

| # | Mutasyon | Beklenen | Ne kanıtlar |
|---|---|---|---|
| **M1** | `admin.py`: `soru_bankasi_servisi.soru_sil` → `admin_servisi.soru_sil` (fix'i birebir geri al) | `test_delete_question_reaches_leaf_service` **FAIL** (500 alır) **VE** `test_delete_question_missing_returns_404_from_leaf` **FAIL** | Test doğrudan kırılan zincire bağlı |
| **M2** | `admin.py`: `basarili = await soru_bankasi_servisi.soru_sil(soru_id)` → `basarili = True` (sonucu yok say) | `..._missing_returns_404...` **FAIL** (200 alır, 404 bekliyor); ilki PASS kalır | Testin yalnız "çökmedi" demediğini, sonucu da denetlediğini gösterir |
| **M3** | `admin.py`: `soru_sil(soru_id)` → `soru_sil(soru_id.lower())` | `leaf.assert_awaited_once_with(qid)` **FAIL** | Sahte-fix çivisi: 200 dönmek yetmiyor, doğru id ile inmiş olmalı |
| **M4** | `admin.py`: `except HTTPException: raise` satırını sil | `..._missing_returns_404...` **FAIL** (404 → 500'e yutulur) | Eski çıplak-except bug'ının geri gelmesini yakalar |
| **M5** | `admin_service.py:31`: `or (args[0] if args else None)` fallback'ini kaldır (dar teşhis) | **HİÇBİR test değişmez** — M1 ile birlikte HÂLÂ 500 | **ÖLDÜRMEMELİ.** "Sebep yalnız `args[0]`" teşhisinin YETERSİZ olduğunu, ikinci bastırıcının (`.rol`/`.aktif`) da var olduğunu kanıtlar — kaldırma deneyinin test-içi karşılığı |
| **M6** (kontrol) | Handler docstring'ini veya `logger.exception` satırını değiştir | İki test de **PASS** kalmalı | Testin aşırı-bağlı olmadığını gösterir |

### A.4 TDD — A-2 (POST sessiz no-op)

#### Adım 1 — Fail eden testi yaz

**Tam dosya yolu:** `C:/Users/husey/kiro2/backend/tests/unit/test_soru_ingestion_upsert.py`
(MEVCUT dosya, 99 satır — SONUNA eklenir. Yeni conftest/fixture GEREKMİYOR.)

**Neden bu dosya:** `test_soru_ekle_upsert_fallback` (satır 50-98) aynı duplicate
yolunu ZATEN koşuyor ve geçiyor; seed/patch kalıbı oradan birebir alınır. Üst
import'lar (`hashlib`, `patch`, `pytest`, `AsyncSession`, `TopicHierarchy`,
`soru_bankasi_servisi`, `db_manager`, `SoruEkleRequest`) yeterli.

```python
@pytest.mark.asyncio
async def test_soru_ekle_duplicate_ok_false_raises(db_session: AsyncSession):
    """Admin yolu: soru_hash çakışması SESSİZCE 'mevcut olanı döndür' olamaz.

    Aynı testte İKİ sözleşme birden çivilenir:
      - varsayılan (ingestion/upsert) davranışı DEĞİŞMEZ  -> `again.id == first.id`
      - duplicate_ok=False verildiğinde ValueError yükselir -> admin ucu 400 döner

    İkincisi olmadan admin POST'u 'Soru başarıyla eklendi' diyerek BAŞKASININ
    satırının id'sini geri veriyor; çağıran onu silmeye kalkınca gerçek içerik
    kaybı yolu açılıyor (A-1 fix'i DELETE'i çalışır hâle getirdiği için bu
    artık teorik değil).
    """
    topic = TopicHierarchy(
        id="t-dup-guard",
        subject_area="MATEMATIK",
        name_tr="Matematik",
        name_en="Mathematics",
        code="MATDUP",
        level=1,
        is_active=True,
    )
    db_session.add(topic)
    await db_session.commit()

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_get_session():
        yield db_session

    with patch.object(db_manager, "get_session", side_effect=mock_get_session):
        payload = {
            "soru_metni": "Duplicate guard test question",
            "secenekler": ["Secenek A", "Secenek B", "Secenek C", "Secenek D"],
            "dogru_cevap": "A",
            "sinav_tipi": "TYT",
            "konu": "Matematik",
            "zorluk_seviyesi": "orta",
            "created_by": None,
        }
        req = SoruEkleRequest(**payload)
        soru_data = payload.copy()
        soru_data["soru_hash"] = req.soru_hash

        first = await soru_bankasi_servisi.soru_ekle(soru_data)
        assert first is not None

        # Ingestion sözleşmesi KORUNMALI — fix bunu bozmamalı.
        again = await soru_bankasi_servisi.soru_ekle(soru_data)
        assert again.id == first.id

        # Admin sözleşmesi: çakışma başarı sayılamaz.
        with pytest.raises(ValueError):
            await soru_bankasi_servisi.soru_ekle(soru_data, duplicate_ok=False)


@pytest.mark.asyncio
async def test_admin_soru_ekle_asks_service_to_reject_duplicates():
    """admin.py çakışmayı reddetmesini servise SÖYLEMELİ.

    HTTP client YOK: handler doğrudan çağrılıyor, servis AsyncMock ile
    değiştiriliyor. Kablonun bağlı olduğunu ölçer — servis tarafındaki guard'ın
    varlığı tek başına yetmez, uç onu ISTEMELIDIR.
    """
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from api.admin import soru_ekle as admin_soru_ekle

    fake = SimpleNamespace(
        id="q-1",
        question_text="Soru?",
        exam_type="TYT",
        subject_area="MATEMATIK",
        difficulty_level="MEDIUM",
        created_at=None,
    )
    admin = SimpleNamespace(id="admin-1")

    mocked = AsyncMock(return_value=fake)
    with patch(
        "services.soru_bankasi_service.soru_bankasi_servisi.soru_ekle", new=mocked
    ):
        body = await admin_soru_ekle({"soru_metni": "Soru?"}, admin=admin)

    assert body["success"] is True
    assert mocked.await_args.kwargs.get("duplicate_ok") is False, (
        "admin ucu servise duplicate_ok=False geçirmiyor -> soru_hash "
        "çakışması 200 OK + 'Soru başarıyla eklendi' olarak raporlanır"
    )
```

#### Adım 2 — Testi koş, FAIL'i doğrula

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/unit/test_soru_ingestion_upsert.py -v --no-header -p no:cacheprovider
```

**Beklenen FAIL mesajı:**

```
FAILED …::test_soru_ekle_duplicate_ok_false_raises
TypeError: soru_ekle() got an unexpected keyword argument 'duplicate_ok'
    (pytest.raises(ValueError) TypeError'ı yakalamaz)

FAILED …::test_admin_soru_ekle_asks_service_to_reject_duplicates
AssertionError: admin ucu servise duplicate_ok=False geçirmiyor -> soru_hash
çakışması 200 OK + 'Soru başarıyla eklendi' olarak raporlanır
assert None is False
```

> **DOĞRULANMADI:** pytest koşturulmadı. Türetme: `soru_bankasi_service.py:188`
> imzası ölçüldü (`async def soru_ekle(self, soru_data: dict)` — kwarg yok) ve
> `admin.py:355` çağrısı kwarg'sız. `db_session` fixture'ı ise DOĞRULANDI
> (`backend/tests/conftest.py:558`, `test_async_engine` → `backend/conftest.py:139`,
> varsayılan `sqlite+aiosqlite:///:memory:` → prod DB'ye yazmaz; sqlite'ta
> `postgresql_where` yok sayılır, `uq_qb_soru_hash_active` tam UNIQUE olarak
> yaratılır → `IntegrityError` yine tetiklenir; bunu **mevcut geçen test**
> `test_soru_ekle_upsert_fallback` zaten kanıtlıyor).

#### Adım 3 — Minimal fix

**Dosya 1:** `backend/services/soru_bankasi_service.py:188`

```python
# ÖNCESİ:
    async def soru_ekle(self, soru_data: dict) -> Question:

# SONRASI:
    async def soru_ekle(self, soru_data: dict, *, duplicate_ok: bool = True) -> Question:
```

**Dosya 1 (devam):** `soru_bankasi_service.py:344-352`, `except IntegrityError`
dalının BAŞI. Mevcut lookup mantığına DOKUNULMUYOR — araya guard ekleniyor.

```python
# ÖNCESİ:
                except IntegrityError as ie:
                    # Savepoint is rolled back automatically by context manager.
                    # Transaction is preserved and not poisoned.
                    logger.warning(
                        "Duplicate question detected (IntegrityError on soru_hash). "
                        "Returning existing question. Error: %s",
                        ie,
                    )
                    # Fetch and return the existing record by soru_hash

# SONRASI:
                except IntegrityError as ie:
                    # Savepoint is rolled back automatically by context manager.
                    # Transaction is preserved and not poisoned.
                    logger.warning(
                        "Duplicate question detected (IntegrityError on soru_hash). "
                        "Returning existing question. Error: %s",
                        ie,
                    )
                    if not duplicate_ok:
                        # Çağıran (admin paneli) 'oluşturuldu' cevabı bekliyor;
                        # mevcut satırı döndürmek 200 OK yalanı üretir ve
                        # çağırana BAŞKASININ satırının id'sini verir.
                        raise ValueError(
                            "Bu soru zaten mevcut (soru_hash çakışması); "
                            "yeni kayıt oluşturulmadı."
                        ) from ie
                    # Fetch and return the existing record by soru_hash
```

**Dosya 2:** `backend/api/admin.py:355-357`

```python
# ÖNCESİ:
        soru = await soru_bankasi_servisi.soru_ekle(
            {**soru_data, "created_by": admin.id}
        )

# SONRASI:
        soru = await soru_bankasi_servisi.soru_ekle(
            {**soru_data, "created_by": admin.id}, duplicate_ok=False
        )
```

Sonuç: çakışma → `ValueError` → `admin.py:376-380`'deki **MEVCUT** `except ValueError`
dalı → HTTP 400 + `detail="Bu soru zaten mevcut (soru_hash çakışması); yeni kayıt
oluşturulmadı."`. Yeni handler dalı, yeni exception sınıfı, yeni şema GEREKMEZ.

**Dosya 3 — ZORUNLU:** `backend/tests/e2e/test_golden_flows.py`, GF6w yükü
(satır 781-788). Fix uygulanınca `:795` `assert resp.status_code == 200` KIRILIR;
bu bir regresyon değil, testin **yanlış vaadi sözleşme gibi kilitlemesidir**.

```python
# ÖNCESİ (sabit yük — her koşuda aynı soru_hash):
    payload = {
        "soru_metni": "Golden Flow write test: 2+2 kaç eder?",
        ...
    }

# SONRASI (benzersiz yük — çakışma yapısal olarak imkânsız):
    import uuid

    payload = {
        "soru_metni": (
            f"Golden Flow write test: 2+2 kaç eder? [{uuid.uuid4().hex[:8]}]"
        ),
        ...
    }
```

**Neden benzersizleştirme, "400 bekle" değil:** GF6w'nin işi *yazma yolunun
çalıştığını* kanıtlamaktır. Sabit yükle test, ilk koşuda satırı yarattı ve sonraki
HER koşuda çakışma dalını test edip "geçti" dedi — yani paket tam da bu kusuru
ÖDÜLLENDİRİYORDU. Benzersiz yük GF6w'yi gerçekten yazma yolunu ölçen bir teste
çevirir ve `duplicate_ok` fix'inden bağımsız kılar.

#### Adım 4 — GREEN doğrulama

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/unit/test_soru_ingestion_upsert.py -v --no-header -p no:cacheprovider
# Beklenen: 3 passed (1 mevcut + 2 yeni)

# Ingestion sözleşmesinin bozulmadığını KANITLA (asıl risk burada):
grep -rn "soru_ekle" backend/api/ backend/services/ --include="*.py" | grep -v "def soru_ekle"
# Ölçülen çağıranlar: api/soru_bankasi.py:763 (ingestion), api/admin.py:355,
# services/admin_service.py:501 -> ilk ikisi kwarg'sız kalmalı (varsayılan True)
python -m pytest tests/unit/test_soru_ingestion_upsert.py tests/unit/test_admin_api.py -q

ruff check backend/services/soru_bankasi_service.py backend/api/admin.py --select=E,F,W --ignore=E501
```

#### Adım 5 — MUTASYON

| # | Mutasyon | Beklenen | Ne kanıtlar |
|---|---|---|---|
| **M1** | `soru_bankasi_service.py`: `if not duplicate_ok: raise ValueError(...)` bloğunu SİL (parametreyi bırak) | `test_soru_ekle_duplicate_ok_false_raises` **FAIL**; diğeri PASS kalır | Guard'ın yük taşıdığını gösterir |
| **M2** | `admin.py`: `, duplicate_ok=False` ifadesini SİL (kabloyu kes) | `test_admin_soru_ekle_asks_service_to_reject_duplicates` **FAIL**; diğeri PASS kalır | İki testin bağımsız olduğunu, servis-guard'ının uç-kablosunu ikame etmediğini gösterir |
| **M3** | `soru_bankasi_service.py`: guard'ı `duplicate_ok`'tan BAĞIMSIZ yap (her zaman `raise`) | `..._duplicate_ok_false_raises` içindeki `again.id == first.id` **FAIL** **VE** mevcut `test_soru_ekle_upsert_fallback` (satır 50) **FAIL** | Fix'in ingestion sözleşmesini kırması da yakalanır — `soru_bankasi.py:763` bu davranışa dayanıyor |
| **M4** | `test_golden_flows.py`: `uuid4` ekini geri al (sabit yük) | GF6w ikinci koşuda 400 alır → **FAIL** | Benzersizleştirmenin gerçekten gerekli olduğunu, kozmetik olmadığını gösterir |

### A.5 Riskler ve geri alım

| Risk | Ölçüm | Azaltma |
|---|---|---|
| DELETE artık gerçekten siliyor | `soru_bankasi_servisi.soru_sil` **soft-delete** (`is_active=False` + `updated_at`, `soru_bankasi_service.py:1265-1298`) — hard delete DEĞİL | Geri alım tek UPDATE. Ama bu bir **yetenek açılışıdır**, operatör bilerek deploy etmeli |
| Yetki kaybı | **YOK.** Router kapısı `Depends(admin_kullanici_getir)` (`admin.py:42-47`), mevcut `test_delete_question_returns_403_for_student` çiviliyor. Kaldırılan `@admin_required` katmanı ölçüldü: geçerli `AuthenticatedUser` ile bile `False` → hiçbir zaman geçilemiyordu | — |
| Mevcut 2 test gerçek DB'ye düşer | `os.environ.setdefault` kabuktaki DSN'i EZMEZ | Patch hedefi güncellemesi **ZORUNLU** (Adım 3'te dahil) |
| GF6w kırılır | `test_golden_flows.py:795` `== 200` | Aynı commit'te benzersiz yük (A-2 Adım 3, Dosya 3) |
| GF fix sonrası her koşuda satır bırakır | `uq_qb_soru_hash_active` yalnız `is_active=true` üzerinde → soft-delete sonrası yeni INSERT serbest. Bugün 45 GF satırı var (44 pasif + 1 aktif) | Kabul edilir (satırlar pasif + `quality_review_status='pending'`, kapı dışı). İzlenecek: `SELECT count(*) FROM question_bank WHERE question_text LIKE 'Golden Flow write test%'` |

**Geri alım (doğrulamalı):**

```bash
git checkout HEAD -- backend/api/admin.py \
                     backend/services/soru_bankasi_service.py \
                     backend/tests/unit/test_admin_api.py \
                     backend/tests/unit/test_soru_ingestion_upsert.py \
                     backend/tests/e2e/test_golden_flows.py && git status --short
# çıktı BOŞ olmalı — boş değilse geri alım YAPILMAMIŞTIR

# Konteynere alındıysa kanonik döngü:
docker cp backend/api/admin.py kiro2-backend:/app/api/admin.py
docker cp backend/services/soru_bankasi_service.py kiro2-backend:/app/services/soru_bankasi_service.py
docker exec kiro2-backend find /app -name "*.pyc" -delete
docker restart kiro2-backend && sleep 22
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/health

# Veri geri alımı (yanlışlıkla silinen soru):
# psql -p 5434 -U postgres -d kiro2 -c "SELECT id,is_active,updated_at FROM question_bank WHERE id='<id>'"  # ÖNCE yedekle
# psql ... -c "UPDATE question_bank SET is_active=true WHERE id='<id>' AND is_active=false"
```

### A.6 BU FIX YANLIŞSA NASIL ANLARIZ

| Sinyal | Nasıl ölçülür | Ne demek |
|---|---|---|
| **DELETE hâlâ 500** | Fix + deploy sonrası `docker logs kiro2-backend --since <T> \| grep 'DELETE /api/v1/admin/content/questions'` → hâlâ 500 | **ÜÇÜNCÜ bir bastırıcı var.** Artık `logger.exception` traceback basacağı için doğrudan görülür. Teşhis eksikti |
| **DELETE 200 ama satır aktif kalıyor** | `SELECT is_active FROM question_bank WHERE id='<silinen>'` → `t` | Yaprak servis çağrıldı ama soft-delete işlemedi — kusur `soru_bankasi_service.py:1265`'te, router'da değil. Fix yanlış katmana yapıldı |
| **POST hâlâ 200 + "eklendi"** | Aynı yükü iki kez POST et; ikincisi 400 dönmeli | `duplicate_ok` kablosu bağlanmamış (M2 mutasyonuyla aynı durum) veya çakışma `IntegrityError` yerine başka yoldan geliyor |
| **Ingestion kırıldı** | `api/soru_bankasi.py:763` ucuna aynı yükü iki kez gönder; ikincisi 200 + aynı id dönmeli | Varsayılan `duplicate_ok=True` korunmamış → M3 mutasyonunun canlı hâli. **Acil geri alım** |
| **Semptom kaybolmadı** | Fix sonrası `SELECT count(*) FILTER (WHERE created_at::date=CURRENT_DATE) FROM question_bank` yeni bir POST'tan sonra hâlâ 0 | Yazma yolu gerçekten bozukmuş; "22 Haz satırını bu uç yarattı" çıkarımı yanlıştı. Teşhisin temeli çöker |
| **PUT de 500 veriyor** | `admin.py:401` aynı kırık deseni taşıyor ama canlı logda **hiç PUT çağrısı yok** — ölçülmedi, ÇIKARIM | Fix kapsamına ALINMADI. PUT ölçülürse ve 500 verirse aynı 1-satırlık desen uygulanır (ayrı görev) |

**Karşı-kanıt deneyi (fix'i uygulamadan, isteğe bağlı):** `admin_service.py:562`'deki
`@admin_required` dekoratörünü yorum satırına al → `docker cp` → `.pyc` sil →
restart → `sleep 22` → aynı DELETE. 500 kaybolmuyorsa teşhis yanlıştır. **Kontrol
kolu ÖNCE:** değişiklikten önce aynı DELETE'i at ve 500 + log sessizliğini GÖR;
görülmüyorsa ölçüm aleti arızalıdır, deneye başlama.

### A.7 Test koşum uyarısı (İŞ A ve B için geçerli)

`backend/tests/` altındaki testler koşulmadan önce:

1. **`from main import app` KULLANMA.** Ölçüldü (py-spy, 3 süreç): `backend/tests/conftest.py:1106`
   `client` fixture'ı `from main import app` + `TestClient(app)` yapıyor;
   `setup_test_database` (`:261`, session+autouse) DSN'i `sqlite+aiosqlite:///./test_test_db.db`
   yapıyor; hiçbir yerde `engine.dispose()` YOK → non-daemon `aiosqlite._connection_worker_thread`
   sızıyor → pytest oturumu bittikten SONRA `threading._shutdown`'da SONSUZA KADAR
   asılı kalıyor. **`pytest-timeout` bu noktada ölüdür** (yalnız `pytest_runtest_protocol`
   içinde kurulur) — 300 s de 30 s de ateşlenmez.
2. **Operatör görevi:** şu an asılı 3 süreci sonlandır — `taskkill /PID 33384 /F`,
   `/PID 27336 /F`, `/PID 34840 /F` (en eskisi 5+ saat, `backend/test_test_db.db`
   üzerinde açık sqlite tutuyorlar).
3. **`backend/` dizininden koş.** `rootdir` argümandan türetilir; `backend/tests/...`
   yolu verildiği sürece `backend/pytest.ini` kazanır (timeout 300). Kökten
   ARGÜMANSIZ `pytest` koşulursa `pyproject.toml` (timeout 30, `func_only=True`)
   seçilir — CI zaten `cd backend && pytest tests/` yapıyor.
4. `backend/tests/` altında **herhangi bir** koşum, teardown'da `backend/test_test_db.db`
   dosyasını SİLER. Bu bir yazmadır, "salt okunur doğrulama" değildir.

---

## İŞ B — Elasticsearch ↔ PostgreSQL senkron boşluğu

### B.0 Sınama kök nedeni ÇÜRÜTTÜ MÜ?

**EVET — dört kanıt satırı geçersiz çıktı, bir de yeni ve daha ağır bulgu eklendi.**
Sonuç ("uygulama içinden soru index'i yeniden kurulamıyor, artımlı senkron yok")
ayakta kaldı, ama farklı gerekçelerle.

| # | Orijinal iddia | Sınama verdikti | Düzeltilmiş hâl |
|---|---|---|---|
| 1 | "Uygulamanın İÇİNDE çalışan bir indexleme yolu **HİÇ OLMADI**" | **ÇÜRÜTÜLDÜ** | `AnalyticsService.log_event` (`elasticsearch_service.py:466-495`) uygulama içinden ES'e YAZIYOR: `analytics-2026-07`'de 121 gerçek doküman, en yenisi bugün tarihli. Doğrusu: **"soru index'ine yazan yol yok"** |
| 2 | "`indexing.index_total=0` ⇒ oluşturulmasından beri tek yazma yok" | **KANIT GEÇERSİZ** | `index_total` düğüm ömrü boyunca tutulur, **yeniden başlatmada sıfırlanır**. Kanıt: `analytics-2026-04` → 53 doc ama `index_total=0`. Sonuç yine de ayakta ama farklı kanıtla: mapping parmak izi + `creation.date` 2026-04-01 değişmemiş + `docs.deleted=0` |
| 3 | "Üç seri bağlı kusur; üçüncüsü `bulk_index(id_field=...)`" | **ÇÜRÜTÜLDÜ** | `question_bank` dalı `bulk_index` KULLANMIYOR; `api/elasticsearch.py:442` `index_question` çağırıyor ve o imza UYUYOR. `bulk_index_questions` yalnız ÖSYM dalında. **Tek aktif bloklayıcı `initialize_index`** |
| 4 | "7 günlük canlı log" | **ÇÜRÜTÜLDÜ** | Konteyner `StartedAt=2026-07-30T01:48:07Z` → pencere **~17 saat**. "Kimse kullanmıyor" sonucunun asıl dayanağı log değil, frontend taraması |
| 5 | (yok) | **YENİ + EN AĞIR** | **Ölü indexleyici atıl değil, KURULU BİR SİLAH.** Dördüncü sözleşme kayması: `api/elasticsearch.py:442` `{"question_id":…,"stem":…}` gönderiyor, `index_question` `q.get("id")`/`q.get("text")` okuyor → `doc_id=""` → elasticsearch-py 8.11'de `"" in SKIP_IN_PATH` → `PUT` değil **`POST` (otomatik id)**. Yani "`mapping=` → `mappings=`" gibi makul görünen bir onarım canlı index'e **110 858** adet otomatik-id'li, `question_text`'i BOŞ, `explanation`'ı DOLU çöp doküman EKLER. Bugün bunu engelleyen TEK şey satır 367'deki 500 |
| 6 | "Seçenek A: index'i sil + arama yüzeyini kaldır" | **ÖLÇÜM EKSİĞİYLE ÖNERİLMİŞ** | Index'in **İKİ** canlı tüketicisi var; iddia birini saymış. İkincisi: `api/question_crud_api.py:777` `GET /api/v1/questions/search/elasticsearch` → `question_crud_service.py:877` → aynı index (probe: 401, rota var, auth kapılı). Silme kararı bu ölçülmeden verilemez |

**Düzeltilmiş kök neden:** Soru index'ini uygulama içinden yazabilecek TEK yol
(admin reindex) İLK satırında ölüyor — `services/elasticsearch_service.py:153`
`create_index`'i `mapping=` ile çağırıyor, gerçek parametre `mappings` → `TypeError`
→ geniş `except` → `return False` → `api/elasticsearch.py:367` `HTTPException(500)`.
Artımlı senkron ise gerçekten YOK: `celery_app.py` `beat_schedule`'da tek bir ES
görevi bulunmuyor (`grep -rn 'elasticsearch\|reindex' backend/tasks/ backend/core/celery_app.py`
→ BOŞ). Canlı index'i kuran, imajın DIŞINDAKİ `scripts/index_to_es.py`'dir
(`docker exec kiro2-backend ls /app/scripts/` → dizin yok).

### B.1 Root Cause Analysis

| Soru | Cevap |
|------|-------|
| **Hata ne?** | Doğrudan ölçüm (bu plan yazarı): `curl _cat/indices/turkiye_sinav_platform` → `64270 0 2026-04-01T01:51:50.358Z` (64 270 doc, `docs.deleted=0`, 1 Nis'tan beri değişmemiş). Buna karşılık `psql SELECT count(*) FROM mv_safe_for_beta` → **25 127**. Yani arama yüzeyi kalite kapısından **4 ay geride**. Ek: konteynerde `inspect.signature` ile — `create_index(self, index_name, mappings=None, settings=None)` vs çağrı `create_index(index_name=…, mapping=…)` → `TypeError: got an unexpected keyword argument 'mapping'`; `initialize_index() -> False` |
| **Root cause?** | `backend/services/elasticsearch_service.py:153` (`create_index(mapping=…)`, gerçek ad `mappings`) → `backend/core/elasticsearch_client.py:115-136` (`create_index`, ayrıca delete-if-exists YOK → kwarg düzeltilse bile `resource_already_exists` ile düşer) → `backend/api/elasticsearch.py:353-367` (`initialize_index` `False` → 500). Artımlı senkron yokluğu: `backend/core/celery_app.py:112-160` `beat_schedule`'da ES görevi yok. **Ayrıca `backend/api/elasticsearch.py:442`** dördüncü sözleşme kayması (`question_id`/`stem` vs `id`/`text` → `doc_id=""`) |
| **Doğru tablo mu?** | Kaynak `question_bank` **ama filtre `is_active` DEĞİL, kalite kapısıdır.** `scripts/index_to_es.py:100` `WHERE is_active = TRUE` diyor — kapı YOK. Doğrusu `JOIN mv_safe_for_beta` (kapı predikatlarını REPLİKE ETME kuralı, `core/quality_gate.py`). `mv_safe_for_beta` yalnız `id` (varchar) taşıdığı için JOIN şart |
| **Altyapı OK mu?** | ES ayakta: `_cat/indices` 200 döndü. PG ayakta: `mv_safe_for_beta` sorgulanabildi. **AMA ES'in kimlik doğrulama durumu ÖLÇÜLMEDİ** — bkz. SIFIRINCI ADIM. Bu, plandaki tek ölçülmemiş severity iddiasıdır |
| **Fix scope?** | **Yeni:** `backend/scripts/es_reindex.py` (~110 satır), `backend/tasks/es_sync_tasks.py` (~40 satır), `backend/tests/e2e/test_es_index_hygiene.py` (~90 satır). **Değişen:** `backend/core/celery_app.py` (+5 satır), `backend/tests/e2e/test_es_answer_leak.py` (−6 satır, `xfail` marker'ı kalkar), `backend/api/elasticsearch.py` (ölü + tehlikeli admin reindex handler'ı kaldırılır). **Silinen:** `scripts/index_to_es.py` |

### B.2 TASARIM — en basit çalışan çözüm (madde 4)

#### B.2.1 Alias switch GEREKLİ Mİ?

**GEREKLİ.** Ama "esneklik" için değil — **ölçülmüş bir gereksinim** için:

Bu değişiklik arama yüzeyini **64 270 → ~25 127**'ye indiriyor (%61 daralma).
Bu **outward-facing** bir değişikliktir. Geri alımın tek komut olması zorunludur.

Daha basit alternatifler değerlendirildi ve **elendi**:

| Alternatif | Neden yetmiyor |
|---|---|
| `_delete_by_query` ile kapı dışı 60K dokümanı sil | Kalan 25K dokümanda `correct_answer` **kalır** — mapping'den alan çıkarılamaz. Geri alım yine tam reindex ister. Asıl amacı (cevap anahtarını index'ten kaldırmak) karşılamıyor |
| Aynı ad altında `delete + create + doldur` | Doldurma süresince arama BOŞ döner (kesinti). Geri alım = yine tam reindex. Rollback maliyeti ~20 sn kesinti |
| **Alias + yeni somut index + atomik takas** | Kesinti YOK, geri alım **tek `_aliases` çağrısı**, eski index saklanır. Ek kod maliyeti: **bir POST** |

Alias'ın maliyeti gerçekten bir POST'tur ve env değişikliği GEREKTİRMEZ:
`ELASTICSEARCH_INDEX=turkiye_sinav_platform` aynen kalır, o ad artık bir alias olur.
ES 8.11 `remove_index` eylemiyle silme + alias ekleme TEK transaction:

```json
POST /_aliases
{"actions": [
  {"remove_index": {"index": "turkiye_sinav_platform"}},
  {"add": {"index": "questions_20260731", "alias": "turkiye_sinav_platform"}}
]}
```

İlk koşuda `remove_index` (somut index → alias'a dönüşüm), sonraki koşularda
`{"remove": {"index": "questions_<eski>", "alias": "turkiye_sinav_platform"}}`.

> **DOĞRULANMADI:** `remove_index` eyleminin bu kurulumda çalıştığı denenmedi
> (yazma gerektirir). ES 6.5+ sürüm bilgisidir. **Uygulayan kişi ÖNCE atılabilir
> bir index+alias çiftiyle prova etmelidir.** Kontrol kolu beklendiği gibi
> davranmıyorsa bulgu değil, alet arızası vardır.

#### B.2.2 Hangi alanlar indexlenmeli?

**Tam olarak `STUDENT_SAFE_QUESTION_FIELDS`.** Bu liste
`backend/services/elasticsearch_service.py:27-45`'te ZATEN var, 17 alan, ve
ölçüldü — `correct_answer` içinde YOK:

```
id, question_text, option_a, option_b, option_c, option_d, option_e,
subject_area, primary_topic_id, exam_type, difficulty_level, irt_difficulty,
grade_level, osym_year, source_book, bloom_level, word_count
```

Bu, **tek doğruluk noktası** kullanmak demektir: reindex script'i listeyi kendisi
yazmaz, o modülden import eder. İkinci bir alan listesi bakımı yaratmaz.

#### B.2.3 `correct_answer` indexlenmeli mi?

**HAYIR. Kesinlikle hayır.** Üç ölçülmüş gerekçe:

1. **Hiçbir tüketici istemiyor.** Her iki tüketici de ES'ten yalnız arama sonucu
   alıp içeriği PG'den yeniden çekiyor (`question_crud_service.py:946-960` bunu
   `is_active` + kapı filtresiyle yapıyor — mimari olarak doğru desen).
2. **API beyaz listesi durgun veriyi KORUMAZ.** `api/elasticsearch.py:160-170`'teki
   süzgeç (ölçüldü, ZATEN VAR) yalnız HTTP yanıtını kesiyor. Dokümanlar hâlâ
   `correct_answer` taşıyor.
3. **En basit koruma, korunacak veriyi oraya hiç koymamaktır.** Indexlenmeyen
   alan sızamaz. Bu, ES'in kimlik durumu ne çıkarsa çıksın (SIFIRINCI ADIM)
   geçerli olan tek savunmadır.

Aynı gerekçeyle `explanation`, `quality_score`, `is_calibrated`, `is_calib_pool`
de indexlenmez.

**`is_active` de indexlenmez** — ek fayda: bugünkü "ES'te 64 270/64 270 doküman
`is_active=true`" yalanı **yapısal olarak imkânsız** hâle gelir.

#### B.2.4 Artımlı senkron nasıl?

**`updated_at` watermark KULLANILMAZ. Gecelik TAM yeniden kurma yapılır.**

Gerekçe (bu, "daha karmaşık VE daha yanlış" olduğu için asıl karar noktasıdır):
kapı üyeliği `quality_review_status` + `pipeline_metadata` + `gate2c_demoted`
bileşimine bağlıdır. Bir soru **hiç değişmeden** `mv_safe_for_beta`'dan DÜŞEBİLİR
(matview yenilendiğinde). Watermark bu demote'u **yapısal olarak kaçırır** →
sessiz servis sızıntısı (`.claude/rules/testing.md` Ders #31'in zaman-penceresine
dönüşmüş hâli). 25 127 satırın tam kurulumu ~20 saniye; artımlı mantık ek durum
tutar, bakım ister ve yanlış cevap verir.

Uygulama: `backend/tasks/quality_gate_tasks.py`'nin **kanıtlı desenini** kopyalar
(advisory lock + fire-and-forget schedule). Zamanlama bilinçli:

```
03:30  refresh-safe-pool-nightly   (MEVCUT — mv_safe_for_beta yenilenir)
04:00  reindex-es-nightly          (YENİ  — yenilenmiş matview'den index kurulur)
```

Ters sıra sessizce bir gün eski havuzu indexler. Advisory lock anahtarı
`quality_gate_tasks`'ınkinden **FARKLI** olmalı — aynısı kullanılırsa iki görev
birbirini sessizce atlar.

#### B.2.5 Geri alım

| Katman | Yordam | Süre |
|---|---|---|
| **Veri** | Eski somut index SİLİNMEZ, saklanır. `POST /_aliases` ile tek çağrıda geri dön | ~1 sn, kesintisiz |
| **Zamanlama** | `celery_app.py` beat girdisini kaldır + `docker compose up -d --no-deps celery-beat` | ~30 sn |
| **Kod** | `git checkout HEAD -- backend/scripts/es_reindex.py backend/tasks/es_sync_tasks.py backend/core/celery_app.py && git status --short` → **BOŞ** olmalı | anında |

#### B.2.6 Reindex script'i (gerçek kod)

**Dosya:** `C:/Users/husey/kiro2/backend/scripts/es_reindex.py` (YENİ)

```python
"""Soru arama index'ini kalite kapısından yeniden kurar.

NEDEN VAR
---------
Canlı `turkiye_sinav_platform` index'i 2026-04-01'de `scripts/index_to_es.py`
(imaj dışı, tek atımlık) ile kuruldu ve o günden beri hiç güncellenmedi:
64.270 doküman, `docs.deleted=0`, `creation.date` değişmemiş. Buna karşılık
kalite kapısı `mv_safe_for_beta` bugün 25.127 satır. Yani arama, PG'nin dört ay
önceki hâlini servis ediyor ve kapı bu yola hiç değmiyor.

TASARIM KARARLARI
-----------------
1. KAYNAK = `mv_safe_for_beta` JOIN. Kapı predikatlarını REPLİKE ETMEYİZ
   (bkz. core/quality_gate.py); matview'e JOIN yaparız. `is_active` filtresi
   kapının YERİNE değil YANINA konur.
2. ALAN LİSTESİ = `STUDENT_SAFE_QUESTION_FIELDS` (tek doğruluk noktası,
   services/elasticsearch_service.py). `correct_answer`/`explanation`/
   `quality_score` ne SELECT'te ne mapping'de yer alır — indexlenmeyen alan
   sızamaz. API beyaz listesi yalnız HTTP yanıtını keser, DURGUN VERİYİ korumaz.
3. TAM YENİDEN KURMA, artımlı diff DEĞİL. Bir soru HİÇ DEĞİŞMEDEN kapıdan
   düşebilir (matview yenilenince); `updated_at` watermark bu demote'u yapısal
   olarak kaçırır -> sessiz sızıntı. 25K satır ~20 sn.
4. ATOMİK ALIAS TAKASI. Yüzey 64.270 -> ~25.127'ye iniyor; outward-facing bir
   değişikliğin geri alımı tek komut olmalı. Eski somut index SİLİNMEZ.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from elasticsearch import Elasticsearch, helpers

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.elasticsearch_service import (  # noqa: E402
    STUDENT_SAFE_QUESTION_FIELDS,
)

logger = logging.getLogger(__name__)

ES_URL = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
ALIAS = os.environ.get("ELASTICSEARCH_INDEX", "turkiye_sinav_platform")

# Turkish analyzer ayarları canlı index'ten birebir alındı (aramanın
# davranışı değişmesin diye) — yalnız alan listesi daraltıldı.
_SETTINGS = {
    "analysis": {
        "analyzer": {
            "turkish_analyzer": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "turkish_stop", "turkish_stemmer"],
            },
            "turkish_search_analyzer": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "turkish_stop"],
            },
        },
        "filter": {
            "turkish_stop": {"type": "stop", "stopwords": "_turkish_"},
            "turkish_stemmer": {"type": "stemmer", "language": "turkish"},
        },
    }
}

_TEXT_TR = {"type": "text", "analyzer": "turkish_analyzer"}
_PROPERTIES = {
    "id": {"type": "keyword"},
    "question_text": {
        "type": "text",
        "analyzer": "turkish_analyzer",
        "search_analyzer": "turkish_search_analyzer",
    },
    "option_a": _TEXT_TR,
    "option_b": _TEXT_TR,
    "option_c": _TEXT_TR,
    "option_d": _TEXT_TR,
    "option_e": _TEXT_TR,
    "subject_area": {"type": "keyword"},
    "primary_topic_id": {"type": "keyword"},
    "exam_type": {"type": "keyword"},
    "difficulty_level": {"type": "keyword"},
    "irt_difficulty": {"type": "float"},
    "grade_level": {"type": "integer"},
    "osym_year": {"type": "integer"},
    "source_book": {"type": "keyword"},
    "bloom_level": {"type": "integer"},
    "word_count": {"type": "integer"},
}

# Yapısal invaryant: mapping ile beyaz liste AYNI kümedir. Biri değişip diğeri
# unutulursa import anında patlar — sessiz kayma imkânsız.
assert set(_PROPERTIES) == set(STUDENT_SAFE_QUESTION_FIELDS), (
    f"mapping <-> beyaz liste kayması: "
    f"{set(_PROPERTIES) ^ set(STUDENT_SAFE_QUESTION_FIELDS)}"
)

_COLUMNS = ", ".join(f"q.{alan}" for alan in STUDENT_SAFE_QUESTION_FIELDS)
SQL = f"""
    SELECT {_COLUMNS}
    FROM question_bank q
    JOIN mv_safe_for_beta m ON m.id = q.id
    WHERE q.is_active = TRUE
    ORDER BY q.id
"""


def _dsn() -> str:
    dsn = os.environ.get("DATABASE_URL_SYNC") or os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL tanımlı değil")
    return dsn.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )


def _fetch() -> list[dict]:
    with psycopg2.connect(_dsn()) as conn, conn.cursor() as cur:
        cur.execute(SQL)
        return [
            dict(zip(STUDENT_SAFE_QUESTION_FIELDS, row, strict=True))
            for row in cur.fetchall()
        ]


def reindex(*, dry_run: bool = False) -> dict:
    """Yeni somut index kur, doldur, doğrula, alias'ı atomik takas et."""
    rows = _fetch()
    if not rows:
        raise RuntimeError("kapı 0 satır döndürdü — matview bayat olabilir, DURULDU")

    yeni = f"questions_{datetime.now(timezone.utc):%Y%m%d%H%M%S}"
    logger.info("es_reindex_basladi: kaynak=%s satır, hedef=%s", len(rows), yeni)
    if dry_run:
        return {"dry_run": True, "rows": len(rows), "target": yeni}

    es = Elasticsearch([ES_URL], request_timeout=120)
    es.indices.create(index=yeni, settings=_SETTINGS, mappings={"properties": _PROPERTIES})

    helpers.bulk(
        es,
        (
            {"_index": yeni, "_id": str(r["id"]), "_source": r}
            for r in rows
        ),
        chunk_size=1000,
        request_timeout=120,
    )
    es.indices.refresh(index=yeni)

    # DOĞRULAMA KAPISI: takas yalnız doküman sayısı tuttuğunda yapılır.
    # Boş/eksik index'i canlıya almak, kapı bypass'ından daha kötüdür.
    sayim = es.count(index=yeni)["count"]
    if sayim != len(rows):
        es.indices.delete(index=yeni)
        raise RuntimeError(f"doküman sayısı tutmadı: {sayim} != {len(rows)} — takas YOK")

    # ATOMİK TAKAS. Eski somut index SİLİNMEZ (alias'lıysa) -> tek çağrıyla geri dönüş.
    eskiler = list(es.indices.get_alias(name=ALIAS).keys()) if es.indices.exists_alias(name=ALIAS) else []
    actions: list[dict] = []
    if eskiler:
        for eski in eskiler:
            actions.append({"remove": {"index": eski, "alias": ALIAS}})
    elif es.indices.exists(index=ALIAS):
        # İlk koşu: ALIAS adı hâlâ SOMUT bir index. remove_index onu siler ve
        # aynı transaction'da alias'ı bağlar (ES 6.5+).
        actions.append({"remove_index": {"index": ALIAS}})
    actions.append({"add": {"index": yeni, "alias": ALIAS}})
    es.indices.update_aliases(actions=actions)

    logger.info("es_reindex_ok: %s doküman, alias %s -> %s", sayim, ALIAS, yeni)
    return {"indexed": sayim, "index": yeni, "retired": eskiler}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="sorguyu koş, ES'e YAZMA")
    print(reindex(dry_run=ap.parse_args().dry_run))
```

#### B.2.7 Celery görevi (gerçek kod)

**Dosya:** `C:/Users/husey/kiro2/backend/tasks/es_sync_tasks.py` (YENİ)

```python
"""ES soru index'i gecelik yeniden kurma.

`tasks/quality_gate_tasks.py` deseninin birebir ikizi. Sıra bilinçli:
03:30 matview yenilenir -> 04:00 index o matview'den kurulur. Ters sıra
sessizce bir gün eski havuzu indexler.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from core.celery_app import celery_app
except Exception:  # broker/celery yoksa modül yine import edilebilmeli
    celery_app = None  # type: ignore[assignment]


def schedule_es_reindex(*, countdown: int = 300) -> None:
    """Kalite yargısı değişince yeniden kurmayı kuyruğa al (fire-and-forget).

    Çağıran uçları ASLA kırmamalı: broker erişilemezse yalnız log düşer.
    Gecikirse en kötü ihtimalle gecelik beat yakalar. `countdown` bilinçli:
    küratörün ardışık yargıları tek pencerede toplanır.
    """
    if celery_app is None:
        return
    try:
        celery_app.send_task("tasks.es_sync_tasks.reindex_question_search", countdown=countdown)
    except Exception as exc:
        logger.warning("es_reindex_schedule_failed: %s", exc)


if celery_app is not None:

    @celery_app.task(
        name="tasks.es_sync_tasks.reindex_question_search",
        bind=True,
        max_retries=2,
    )
    def reindex_question_search(self) -> dict[str, Any]:
        from scripts.es_reindex import reindex

        try:
            return reindex()
        except Exception as exc:
            logger.error("es_reindex_failed: %s", exc)
            raise self.retry(exc=exc, countdown=600) from exc
```

**Dosya:** `backend/core/celery_app.py`, `beat_schedule` içine (satır ~131,
`refresh-safe-pool-nightly` girdisinin HEMEN ARDINA):

```python
        # ES soru arama index'i: matview yenilendikten SONRA yeniden kurulur.
        # 03:30 refresh-safe-pool-nightly -> 04:00 reindex. Ters sıra bir gün
        # eski havuzu indexler.
        "reindex-es-nightly": {
            "task": "tasks.es_sync_tasks.reindex_question_search",
            "schedule": crontab(hour=4, minute=0),
        },
```

### B.3 TDD

#### Adım 1 — RED test ZATEN VAR (yazmaya gerek yok)

**Tam dosya yolu:** `C:/Users/husey/kiro2/backend/tests/e2e/test_es_answer_leak.py:210-250`

Bu depoda `test_es_search_respects_quality_gate` adında bir test ZATEN var ve
**bilerek `xfail(strict=True)`** ile işaretli. Dosyanın kendi yorumu (doğrulandı,
okundu):

```python
# BEKLENEN KIRMIZI: kapı bypass'ı bilinçli olarak ertelendi (27 Tem kararı).
# …
# strict=True bilinçli: reindex yapıldığı anda bu test geçmeye başlayacak ve
# paket "unexpectedly passing" ile kırmızıya dönecek — marker'ı kaldırmak
# ZORUNLU olacak. Yeşil paketin içinde sessizce yaşayan bilinen-kırık test
# bırakmamak için.
@pytest.mark.xfail(
    reason="ES index'i kalite kapısından geçirilmedi — reindex v_safe_for_beta'dan "
    "yapılana kadar arama kapı dışı soru döndürüyor (ölçüm: 14/15)",
    strict=True,
)
```

Yani **RED durumu bu depoya çoktan çivilenmiş** ve marker'ın kaldırılması fix'in
zorunlu parçası. Bu, yeni bir test yazmaktan daha güçlüdür: ölü-adam anahtarı
hâlihazırda kurulu.

#### Adım 2 — Eksik olan: DOKÜMAN düzeyi test (YENİ)

Mevcut test **ucun döndürdüğünü** denetliyor. Ama `api/elasticsearch.py:160-170`'teki
beyaz liste (ölçüldü, ZATEN VAR) sayesinde cevap-sızıntısı testi **bugün de
GEÇİYOR** — yani API katmanında yazılacak bir "cevap sızmıyor" testi **vakumdur**.
Korunması gereken şey **durgun veridir**.

**Tam dosya yolu:** `C:/Users/husey/kiro2/backend/tests/e2e/test_es_index_hygiene.py` (YENİ)

```python
"""ES index'inin KENDİSİ kapılı ve cevapsız olmalı — API filtresi değil.

NEDEN AYRI DOSYA: test_es_answer_leak.py ucun DÖNDÜRDÜĞÜNÜ denetliyor ve API
beyaz listesi (STUDENT_SAFE_QUESTION_FIELDS, api/elasticsearch.py:160-170)
sayesinde bugün GEÇİYOR. Ama dokümanlar hâlâ correct_answer taşıyor. Beyaz liste
yalnız HTTP yanıtını keser; DURGUN VERİYİ korumaz. Bu dosya ES'i DOĞRUDAN
sorgular, API katmanı araya girmez.
"""

from __future__ import annotations

import os

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

pytestmark = [pytest.mark.golden_flow, pytest.mark.e2e]

# Konteyner içi ELASTICSEARCH_URL host'tan çözülmüyor -> ayrı değişken.
ES_URL = os.environ.get("ELASTICSEARCH_URL_HOST", "http://localhost:9200")
ES_INDEX = os.environ.get("ELASTICSEARCH_INDEX", "turkiye_sinav_platform")

BANNED_FIELDS = (
    "correct_answer",
    "explanation",
    "quality_score",
    "is_calib_pool",
    "is_calibrated",
)


@pytest.fixture(scope="module")
def es() -> httpx.Client:
    c = httpx.Client(base_url=ES_URL, timeout=30.0)
    try:
        r = c.get(f"/{ES_INDEX}/_count")
    except Exception as exc:
        c.close()
        pytest.skip(f"ES {ES_URL} ulaşılamıyor: {exc}")
    if r.status_code == 404:
        c.close()
        pytest.skip(f"index/alias '{ES_INDEX}' yok")
    try:
        yield c
    finally:
        c.close()


@pytest_asyncio.fixture
async def db_session():
    dsn = resolve_pg_dsn()
    if not dsn:
        pytest.skip(SKIP_REASON)
    engine = create_async_engine(dsn, poolclass=NullPool)
    try:
        conn = await engine.connect()
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"DB erişilemiyor: {type(exc).__name__}")
    maker = async_sessionmaker(bind=conn, class_=AsyncSession, expire_on_commit=False)
    session = maker()
    try:
        yield session
    finally:
        await session.close()
        await conn.close()
        await engine.dispose()


def _count(es: httpx.Client, query: dict) -> int:
    r = es.post(f"/{ES_INDEX}/_count", json={"query": query})
    assert r.status_code == 200, f"_count {r.status_code}: {r.text[:200]}"
    return r.json()["count"]


def _all_ids(es: httpx.Client) -> list[str]:
    ids: list[str] = []
    r = es.post(
        f"/{ES_INDEX}/_search",
        params={"scroll": "2m"},
        json={"size": 5000, "_source": False, "query": {"match_all": {}}},
    )
    assert r.status_code == 200, f"_search {r.status_code}: {r.text[:200]}"
    body = r.json()
    scroll_id = body.get("_scroll_id")
    while True:
        hits = body["hits"]["hits"]
        if not hits:
            break
        ids.extend(h["_id"] for h in hits)
        body = es.post("/_search/scroll", json={"scroll": "2m", "scroll_id": scroll_id}).json()
    return ids


def test_index_carries_no_answer_key(es: httpx.Client):
    """Hiçbir dokümanda cevap/kalite alanı BULUNMAMALI (durgun veri)."""
    total = _count(es, {"match_all": {}})
    if total == 0:
        pytest.skip("index boş — test anlamsız")

    kirli = {alan: _count(es, {"exists": {"field": alan}}) for alan in BANNED_FIELDS}
    kirli = {k: v for k, v in kirli.items() if v}
    assert not kirli, (
        f"{total} dokümanın içinde yasaklı alan var: {kirli}. "
        "Index kapısız/eski indexleyiciyle kurulmuş olabilir."
    )


@pytest.mark.asyncio
async def test_index_is_subset_of_safe_pool(es: httpx.Client, db_session: AsyncSession):
    """Index'teki HER id mv_safe_for_beta içinde olmalı (örnekleme değil, TAMAMI)."""
    ids = _all_ids(es)
    if not ids:
        pytest.skip("index boş — test anlamsız")

    rows = await db_session.execute(
        text(
            """
            SELECT x.id
            FROM unnest(CAST(:ids AS text[])) AS x(id)
            WHERE NOT EXISTS (SELECT 1 FROM mv_safe_for_beta m WHERE m.id = x.id)
            """
        ),
        {"ids": ids},
    )
    disarida = [r[0] for r in rows.fetchall()]
    oran = 100.0 * len(disarida) / len(ids)
    assert not disarida, (
        f"{len(disarida)}/{len(ids)} doküman (%{oran:.2f}) kalite kapısı DIŞINDA. "
        f"Örnek: {disarida[:3]}"
    )


@pytest.mark.asyncio
async def test_no_ghost_documents(es: httpx.Client, db_session: AsyncSession):
    """PG'de karşılığı olmayan hayalet doküman BULUNMAMALI.

    Ayrı test: bir doküman kapı dışında OLMADAN da hayalet olabilir
    (question_bank'tan tamamen silinmiş).
    """
    ids = _all_ids(es)
    if not ids:
        pytest.skip("index boş — test anlamsız")

    rows = await db_session.execute(
        text(
            """
            SELECT x.id
            FROM unnest(CAST(:ids AS text[])) AS x(id)
            WHERE NOT EXISTS (SELECT 1 FROM question_bank q WHERE q.id = x.id)
            """
        ),
        {"ids": ids},
    )
    hayaletler = [r[0] for r in rows.fetchall()]
    assert not hayaletler, (
        f"{len(hayaletler)} hayalet doküman (PG'de YOK ama servis ediliyor). "
        f"Örnek: {hayaletler[:3]}"
    )
```

**Altyapı doğrulaması (DOĞRULANDI, bu plan yazarı okudu):**
`backend/tests/e2e/pg_dsn.py` mevcut ve `SKIP_REASON` + `resolve_pg_dsn`
sağlıyor; `test_es_answer_leak.py:45` bugün kullanıyor. `db_session` fixture kalıbı
aynı dosyadan birebir. `pytestmark = [golden_flow, e2e]` aynı dosyada satır 47.
Yeni conftest GEREKMİYOR.

#### Adım 3 — Testleri koş, FAIL'i doğrula

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/e2e/test_es_index_hygiene.py -v --no-header -p no:cacheprovider
```

**Beklenen FAIL mesajları:**

```
FAILED …::test_index_carries_no_answer_key
AssertionError: 64270 dokümanın içinde yasaklı alan var:
{'correct_answer': 64270, 'explanation': 64270, 'quality_score': 64270,
 'is_calib_pool': 64270, 'is_calibrated': 64270}.
Index kapısız/eski indexleyiciyle kurulmuş olabilir.

FAILED …::test_index_is_subset_of_safe_pool
AssertionError: <N>/64270 doküman (%<oran>) kalite kapısı DIŞINDA. Örnek: [...]
```

> **DOĞRULANMADI (iki ayrı yerde):**
> 1. **pytest koşturulmadı.** İlk testin RED olacağı `_count(exists:correct_answer)`
>    → 64 270 ölçümünden türetildi (teşhis turu).
> 2. **"60 605 kapı dışı" sayısı doğrulanmadı.** Sınama turu bunu yeniden
>    üretemedi ve şunu ölçtü: üst sınır `64 270 − 25 127 = 39 143`, yani iddianın
>    sayısı ile **çelişiyor**. Gerçek sayı ancak ID kesişimi hesaplanınca bilinir
>    — bu testin kendisi onu ölçer. **Plan hiçbir yerde 60 605 rakamını
>    kullanmıyor.** `test_no_ghost_documents`'ın RED olup olmayacağı da BELİRSİZ
>    ("9 hayalet" iddiası hiç doğrulanmadı) — geçerse bu iyi haberdir, testin
>    değeri regresyon korumasıdır.

#### Adım 4 — Fix ve GREEN doğrulama

```bash
# 1) Kuru koşum — SQL'i ve alan listesini ES'e dokunmadan doğrula
cd C:/Users/husey/kiro2/backend
python scripts/es_reindex.py --dry-run
# Beklenen: {'dry_run': True, 'rows': 25127, 'target': 'questions_2026...'}
# rows != mv_safe_for_beta sayımı ise JOIN yanlış -> DUR

# 2) === ONAY ADIMI (bkz. B.4) — buradan sonrası CANLI ARAMA YÜZEYİNİ DEĞİŞTİRİR ===
python scripts/es_reindex.py

# 3) GREEN
python -m pytest tests/e2e/test_es_index_hygiene.py -v --no-header -p no:cacheprovider
# Beklenen: 3 passed

# 4) xfail marker'ı KALDIR (test_es_answer_leak.py:212-216) — sonra:
python -m pytest tests/e2e/test_es_answer_leak.py -v --no-header -p no:cacheprovider
# Marker kalmazsa: XPASS(strict) -> paket KIRMIZI. Kaldırma fix'in parçasıdır.

# 5) Kapsam = değişikliğin kapsamı
grep -rl "elasticsearch" backend/api/ backend/services/ --include="*.py"
# İKİNCİ tüketici de duman testinden geçmeli:
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/api/v1/questions/search/elasticsearch
# 401 beklenir (rota var, auth kapılı) — 404/500 gelirse index adı/alias kırılmış

ruff check backend/scripts/es_reindex.py backend/tasks/es_sync_tasks.py --select=E,F,W --ignore=E501
```

#### Adım 5 — MUTASYON

| # | Mutasyon | Beklenen | Ne kanıtlar |
|---|---|---|---|
| **M1** | `es_reindex.py`: `_PROPERTIES`'e ve SELECT'e `correct_answer` geri ekle, reindex et | `test_index_carries_no_answer_key` **KIRMIZI**; diğer ikisi yeşil | Cevap-anahtarı invaryantı bağımsız |
| **M2** | `es_reindex.py`: `JOIN mv_safe_for_beta m ON m.id = q.id` satırını sil (yalnız `is_active` bırak) | `test_index_is_subset_of_safe_pool` **KIRMIZI** (110 858 − 25 127 = 85 731 kapı dışı); `test_no_ghost_documents` **YEŞİL** kalır | İki testin bağımsız olduğunu kanıtlar — kapı dışı olmak ≠ hayalet olmak |
| **M3** | ES'e PG'de olmayan tek bir `_id` ile doküman yaz | Yalnız `test_no_ghost_documents` **KIRMIZI** | Üçüncü invaryantın ayrı yük taşıdığını gösterir |
| **M4** | Eski `scripts/index_to_es.py`'yi tekrar koştur (en gerçekçi regresyon) | **ÜÇÜ DE** aynı anda **KIRMIZI** | Korunmak istenen tam senaryo. Bu yüzden o script SİLİNİR |
| **M5** | `test_index_is_subset_of_safe_pool`: `assert not disarida` → `assert len(disarida) < len(ids)` | Bugünkü 64 270 dokümanla **YEŞİL** döner | **Testin kendisini zayıflatan mutasyon.** Orantısal eşiğin değersizliğini gösterir |
| **M6** | `es_reindex.py`: doküman-sayısı doğrulama kapısını (`if sayim != len(rows)`) kaldır ve `helpers.bulk`'u kısmi başarısız yap | Takas eksik index'le yapılır → `test_index_is_subset_of_safe_pool` geçer ama arama sonuç sayısı düşer | Doğrulama kapısının yük taşıdığını gösterir |
| **M7** | `es_reindex.py`: `assert set(_PROPERTIES) == set(STUDENT_SAFE_QUESTION_FIELDS)` satırını sil, sonra mapping'e bir alan ekle | Import anında patlamaz, sessiz kayma başlar | Tek-doğruluk-noktası invaryantının yük taşıdığını gösterir |

### B.4 🔴 ONAY ADIMI — OUTWARD-FACING DEĞİŞİKLİK

> **`python scripts/es_reindex.py` (kuru koşum DEĞİL, gerçek koşum) canlı arama
> yüzeyini değiştirir: 64 270 → ~25 127 doküman (%61 daralma). Bu adım SESSİZCE
> YAPILMAZ.**

**Onaydan önce sunulacaklar:**

1. `--dry-run` çıktısı (gerçek satır sayısı; `mv_safe_for_beta` sayımıyla eşleşmeli)
2. SIFIRINCI ADIM ölçüm sonuçları (ES kimlik/erişilebilirlik durumu)
3. `test_index_is_subset_of_safe_pool`'un RED çıktısındaki **gerçek** kapı-dışı sayısı
   (planın hiçbir yerinde tahmin sayı kullanılmadı)
4. Geri alım komutunun **prova edilmiş** olması (atılabilir index+alias çiftiyle)

**Onay verilmesi gereken üç ayrı karar:**

| Karar | Seçenekler | Not |
|---|---|---|
| **K1 — Arama havuzu daralması kabul mü?** | (a) Evet, kapı amacı bu (b) Hayır, önce kapı gevşetilsin | %61 daralma "kayıp" değil kapının AMACI; ama ürün tarafı bunu bilerek kabul etmeli |
| **K2 — Zamanlama** | (a) Hemen (b) Düşük trafik penceresi (c) Gecelik beat'in ilk koşumuyla | Kesinti yok (alias takası) ama gözlem penceresi istenebilir |
| **K3 — İkinci tüketici** | `GET /api/v1/questions/search/elasticsearch` de daralacak — kabul mü? | Bu uç ES'ten yalnız id alıp PG'den kapılı çekiyor, yani zaten kapılı; daralma yalnız aday havuzunu küçültür |

**Onay ALINMADAN yapılabilecekler (güvenli):** SIFIRINCI ADIM ölçümleri,
`--dry-run`, test dosyalarının yazılması, RED doğrulaması, script/görev kodunun
yazılması ve gözden geçirilmesi.

### B.5 Kapsamdan ÇIKARILANLAR (ve neden)

| Yapılmayacak | Ölçülmüş gerekçe |
|---|---|
| `initialize_index` / `bulk_index_questions` **onarımı** | Alan adları (`text`/`subject`/`options`-nested) canlı mapping'le hiç uyuşmuyor; onarmak kullanılmayan İKİNCİ bir indexleme yolu yaratır (bugünkü ikiliğin ta kendisi). Reindex artık script/celery yolundan |
| Admin reindex ucunun **korunması** | Ölü **VE** tehlikeli: naif onarım 110 858 çöp doküman yazar (B.0 #5). `api/elasticsearch.py:353-460` handler'ı KALDIRILIR. Regresyon testi: `POST .../admin/reindex/questions` → 404 (bugün 405/500, yani rota var) |
| ES'e **kimlik doğrulama** eklemek | Bu işin kapsamı değil; ama `correct_answer`'ı hiç indexlememek onu büyük ölçüde gereksiz kılar. Ağ kısıtlaması SIFIRINCI ADIM sonucuna göre AYRI görev |
| Ayrı bir "ES senkron servisi/soyutlaması" | `quality_gate_tasks.py` deseni aynı problemi çözmüş; kopyalanacak tek desen var, 3+ tekrar yok (CLAUDE.md abstraction kuralı) |
| Index'i **tamamen silmek** (teşhisin "Seçenek A"sı) | İKİ tüketici ölçüldü, iddia birini saymış. Silme kararı ürün teyidi ister — bu plan onu vermiyor |

### B.6 BU FIX YANLIŞSA NASIL ANLARIZ

| Sinyal | Nasıl ölçülür | Ne demek |
|---|---|---|
| **`--dry-run` 0 satır döndürüyor** | Script zaten `RuntimeError` ile duruyor | `mv_safe_for_beta` bayat/boş. Fix'e devam etmek yerine matview yenilenmeli. **Script bu durumda ES'e DOKUNMAZ** |
| **`--dry-run` satır sayısı ≠ `count(*) mv_safe_for_beta`** | `psql -c "SELECT count(*) FROM mv_safe_for_beta"` ile karşılaştır | JOIN veya `is_active` filtresi yanlış. `is_active` kapının YANINA konmuştu; fark varsa kapıda `is_active=false` satır var demektir → kapı tanımı gözden geçirilmeli |
| **Takas sonrası arama BOŞ dönüyor** | `curl "$ES/turkiye_sinav_platform/_count"` → 0 | Alias yanlış index'e bağlandı. **Tek komutla geri dön**: `POST /_aliases` ile eski somut index'i bağla |
| **`test_index_is_subset_of_safe_pool` fix sonrası hâlâ KIRMIZI** | Test çıktısındaki `disarida` listesi | Alias eski index'e bakıyor VEYA matview ile `question_bank` arasında tutarsızlık var. `es.indices.get_alias(name=ALIAS)` ile hangi somut index'e bağlı olduğunu göster |
| **`test_es_answer_leak.py` XPASS(strict) ile paketi kırmızıya çeviriyor** | pytest çıktısı `XPASS` | **BU BEKLENEN VE İYİ.** Marker kaldırılmalı — fix'in zorunlu parçası. Kaldırmayı unutmak paketi kırar, sessizce geçmez (ölü-adam anahtarı çalışıyor) |
| **Arama sonuçları alakasızlaştı** | Aynı sorgu için önce/sonra ilk 10 sonucu karşılaştır | Turkish analyzer ayarları taşınmamış. Script analyzer'ı canlı index'ten birebir alıyor; farklıysa `_settings` karşılaştır |
| **Gecelik görev hiç koşmuyor** | `docker logs kiro2-celery-beat \| grep reindex-es-nightly` | Beat girdisi yüklenmedi. `docker compose up -d --no-deps celery-beat` (restart yetmez) |
| **İki görev birbirini atlıyor** | `es_reindex_ok` logu hiç düşmüyor ama hata da yok | Advisory lock anahtarı `quality_gate_tasks` ile ÇAKIŞMIŞ. Farklı sabit kullanılmalı |
| **Semptom kaybolmadı: arama hâlâ kapı dışı soru veriyor** | `test_index_is_subset_of_safe_pool` yeşil ama canlı arama kapı dışı döndürüyor | Uç, alias'ı değil başka bir index adını okuyor. `ELASTICSEARCH_INDEX` env'ini konteynerde doğrula: `docker exec kiro2-backend env \| grep ELASTIC` |

---

## İŞ C — Ölü CI workflow YAML

### C.0 Sınama kök nedeni ÇÜRÜTTÜ MÜ?

**HAYIR — mekanizma doğrulandı. AMA anlatı iki yerde eksik/yanlış çıktı.**

| # | Orijinal iddia | Sınama verdikti | Düzeltilmiş hâl |
|---|---|---|---|
| 1 | "golden-flows.yml:172 + quality-gate.yml:17-18 → GitHub ayrıştıramıyor" | **DOĞRULANDI** (4 ayrıştırıcı + GitHub'ın kendi davranışı + iki doğal deney) | Aynen geçerli |
| 2 | "CI 3,5 aydır ölü **çünkü** YAML" | **TARİHÇE YANLIŞ** | **SERİ BAĞLI BİRİNCİ SEBEP:** YAML geçerliyken de tek iş koşmamış. 10-11 Nis'taki 24/24 koşum `failure`, 3-5 sn, 1 iş / **0 adım**. GitHub anotasyonu: *"The job was not started because recent account payments have failed or your spending limit needs to be increased."* = **FATURALAMA bloğu**. Bu BUGÜN çözülmüş (kontrol kolu: Health Checks bugün 4 iş, gerçek adımlar `success`) |
| 3 | (yok) | **ÜÇÜNCÜ SEBEP** | Kusur 3,5 ay bir bekçi olmadığı için değil, **bekçi HİÇ KOŞMADIĞI** için yaşadı. `.pre-commit-config.yaml:13` `check-yaml` ZATEN VAR ve bugün iki dosya için de `EXIT=1` veriyor; ama `~/.cache/pre-commit/` **27 Tem 2026 18:03**'te oluşmuş (kırılmadan 3,5 ay SONRA) ve `pre-commit.log` bandit ortamının kurulamadığını gösteriyor → pre-commit bir hook ortamı kuramayınca TÜM koşumu düşürür, `check-yaml` sıraya bile gelmez |
| 4 | ".github/workflows'ta 12 dosya" | **YANLIŞ** (bu plan yazarı bağımsız ölçtü) | `glob('*.yml')` = **11**, `glob('*.yaml')` = 0. 12. giriş `desktop.ini` |
| 5 | "Test: `yaml.safe_load` ile her dosyayı ayrıştır" | **YARIM-VAKUM** (bu plan yazarı bağımsız ölçtü) | Düz `safe_load` `quality-gate.yml`'i **OK** diyor (PyYAML mükerrer anahtarı sessizce yutar, son değer kazanır). **Dup-key farkındalı yükleyici ZORUNLU** — yoksa test 290 başarısız koşumluk ikinci kusuru hiç görmez |

**Düzeltilmiş kök neden:** Bugün aktif olan tek bloklayıcı YAML ayrıştırma
hatasıdır (iki dosya, iki bağımsız kusur). Tarihsel olarak faturalama bloğu daha
önce geldi ve zaten çözülmüş; hayatta kalma sebebi ise koşmayan pre-commit'tir.

### C.1 Root Cause Analysis

| Soru | Cevap |
|------|-------|
| **Hata ne?** | Bu plan yazarının kendi ölçümü: `yaml.safe_load` → `FAIL golden-flows.yml \| mapping values are not allowed here … line 172, column 43`; dup-key yükleyici → `FAIL quality-gate.yml \| tekrarli anahtar: 'workflow_dispatch'`. GitHub tarafı (teşhis turu): `GET /actions/workflows` → 13 workflow, 11'i beyan ettiği adı gösteriyor, **tam bu ikisi DOSYA YOLUNU ad olarak gösteriyor** (`name='.github/workflows/golden-flows.yml'`) — GitHub'ın `name:` okuyamadığında yaptığı geri-düşüş. En son koşum `30569194367`: `total_jobs=0`, süre 0.0 s. `?status=success` → golden-flows 447 koşumun **0**'ı, quality-gate 291 koşumun **0**'ı |
| **Root cause?** | `.github/workflows/golden-flows.yml:172` — tırnaksız düz skalar içinde `': '`: `      - name: AST lint — Pydantic \`user_id: int\` type lie (rule-of-five)` (sütun 43 = `user_id`den sonraki iki nokta). Kıran commit `d1506c22f`, 2026-04-12. `.github/workflows/quality-gate.yml:17-18` — `workflow_dispatch:` İKİ KEZ. Kıran commit `9eee80d71`, 2026-05-29 |
| **Doğru tablo mu?** | **İlgisiz** — DB'ye dokunmuyor. Yerine sorulacak eşdeğer: *doğru sürüm mü?* CI, GitHub'daki push'lanmış blob'u okur. `git status --short -- <iki dosya>` BOŞ, `git rev-list --left-right --count HEAD...origin/…` = `0 0`. **AYRICA `origin/master` DA BOZUK** (ayrı okundu) — feature dalındaki fix master'ı kendiliğinden düzeltmez |
| **Altyapı OK mu?** | Evet, kontrol koluyla: 30 Tem 17:44Z `Health Checks` koşumu `total_jobs=4`, `Set up job`/`Checkout`/`Set up Python`/`Install dependencies` hepsi `success`, 120 s. Yani runner ve Actions dakikaları BUGÜN çalışıyor; 0-iş yalnız bu iki dosyaya özgü. Faturalama bloğu (Nisan) kalkmış |
| **Fix scope?** | **2 dosya, 2 satır:** `.github/workflows/golden-flows.yml`, `.github/workflows/quality-gate.yml`. **+1 test:** `backend/tests/unit/test_workflow_yaml.py` (YENİ) |

### C.2 TDD

#### Adım 1 — Fail eden testi yaz

**Tam dosya yolu:** `C:/Users/husey/kiro2/backend/tests/unit/test_workflow_yaml.py` (YENİ)

**Neden `backend/tests/unit/`:** hiçbir fixture kullanmıyor, DB/ES/backend
gerektirmiyor, `from main import app` yapmıyor (A.7'deki asılma sınıfı dışında).
CI zaten `cd backend && pytest tests/` koşuyor → otomatik dahil olur.
`ruamel.yaml` **kullanılmıyor**: `backend/requirements*.txt` yalnız `PyYAML==6.0.3`
listeliyor, ruamel deklare edilmiş bağımlılık değil → yerelde yeşil, CI'da
`ImportError` olurdu.

```python
"""GitHub Actions workflow YAML geçerlilik bekçisi.

ÖLÇÜLEN KUSURLAR (30 Tem 2026):
  * golden-flows.yml:172 — tırnaksız skalar içinde ': '. Kıran commit
    d1506c22f (2026-04-12). GitHub audit: 447 koşum, 0 success.
  * quality-gate.yml:17-18 — 'workflow_dispatch:' İKİ KEZ. Kıran commit
    9eee80d71 (2026-05-29). GitHub audit: 291 koşum, 0 success.

Ayrıştırılamayan workflow için GitHub ne `name` ne `on:` filtresini okuyabilir;
her push'ta 0-işli / 0-saniyelik 'failure' üretir ve kapı FİİLEN ÖLÜR.

DUP-KEY YÜKLEYİCİ ZORUNLU: PyYAML `safe_load` mükerrer anahtarı SESSİZCE yutar
(son değer kazanır). Ölçüldü — düz safe_load ile bu paket 2 RED yerine yalnız
1 RED verir, yani 291 başarısız koşumluk ikinci kusuru hiç görmez.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# unit -> tests -> backend -> depo kökü
_KOK = Path(__file__).resolve().parents[3]
_WF = _KOK / ".github" / "workflows"
# rglob DEĞİL: `.archive/` altında 18 emekli dosya var (biri bozuk) ve GitHub
# .github/workflows'un ALT DİZİNLERİNİ okumaz.
_DOSYALAR = sorted(_WF.glob("*.yml"))


class _TekrarsizYukleyici(yaml.SafeLoader):
    """`safe_load`in yuttuğu tekrarlı anahtarı hata yapar (GitHub da yapar)."""


def _tekrarsiz_esleme(loader, node, deep=False):
    gorulen = set()
    for anahtar_dugum, _ in node.value:
        anahtar = loader.construct_object(anahtar_dugum, deep=True)
        if anahtar in gorulen:
            raise yaml.YAMLError(f"tekrarli anahtar: {anahtar!r}")
        gorulen.add(anahtar)
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


_TekrarsizYukleyici.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _tekrarsiz_esleme
)


def test_kontrol_kolu_workflow_dizini_bulundu():
    """ALET DOĞRULAMASI: yol türetmesi kırılırsa aşağısı 0 parametreyle
    sessizce YEŞİL yalan söyler. Bu depoda '0 satır tarayan bekçi' vakası
    yaşandı — invaryant spekülatif değil."""
    assert _WF.is_dir(), f"workflow dizini yok: {_WF}"
    assert len(_DOSYALAR) >= 10, (
        f"beklenen >=10 workflow, bulunan {len(_DOSYALAR)}: "
        f"{[p.name for p in _DOSYALAR]}"
    )


@pytest.mark.parametrize("yol", _DOSYALAR, ids=lambda p: p.name)
def test_workflow_gecerli_yaml_ve_is_tanimli(yol: Path):
    try:
        veri = yaml.load(yol.read_text(encoding="utf-8"), _TekrarsizYukleyici)
    except yaml.YAMLError as hata:
        pytest.fail(
            f"{yol.name} GitHub tarafından AYRIŞTIRILAMAZ -> her push'ta "
            f"0-işli 'failure' koşumu üretir:\n{hata}"
        )

    assert isinstance(veri, dict), f"{yol.name}: kök düğüm eşleme değil"
    # PyYAML `on:` anahtarını YAML 1.1 uyarınca bool True okur -> veri.get("on") YANLIŞ.
    assert True in veri or "on" in veri, f"{yol.name}: tetikleyici (`on:`) yok"
    assert veri.get("name"), (
        f"{yol.name}: `name` okunamıyor -> GitHub workflow adını dosya YOLU gösterir"
    )
    assert veri.get("jobs"), f"{yol.name}: `jobs` yok/boş"
    for is_adi, is_govde in veri["jobs"].items():
        assert isinstance(is_govde, dict), f"{yol.name}:{is_adi} gövde eşleme değil"
        assert "runs-on" in is_govde or "uses" in is_govde, (
            f"{yol.name}:{is_adi} ne `runs-on` ne `uses` içeriyor"
        )
```

#### Adım 2 — Testi koş, FAIL'i doğrula

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/unit/test_workflow_yaml.py -v --no-header -p no:cacheprovider
```

**Beklenen FAIL mesajı:**

```
PASSED …::test_kontrol_kolu_workflow_dizini_bulundu
FAILED …::test_workflow_gecerli_yaml_ve_is_tanimli[golden-flows.yml]
Failed: golden-flows.yml GitHub tarafından AYRIŞTIRILAMAZ -> her push'ta
0-işli 'failure' koşumu üretir:
mapping values are not allowed here
  in "<unicode string>", line 172, column 43

FAILED …::test_workflow_gecerli_yaml_ve_is_tanimli[quality-gate.yml]
Failed: quality-gate.yml GitHub tarafından AYRIŞTIRILAMAZ -> her push'ta
0-işli 'failure' koşumu üretir:
tekrarli anahtar: 'workflow_dispatch'

======= 2 failed, 10 passed =======
```

> **DOĞRULAMA DURUMU — bu plandaki EN GÜÇLÜ RED:** pytest'in kendisi
> koşturulmadı (dosya yazılmadı), **ama testin mantık gövdesi bu plan yazarı
> tarafından bellekte birebir koşturuldu** ve tam bu iki FAIL üretildi:
> `FAIL golden-flows.yml | mapping values are not allowed here … line 172, column 43`
> ve `FAIL quality-gate.yml | tekrarli anahtar: 'workflow_dispatch'`, kalan 9
> dosya OK. Dosya sayısı da doğrulandı (11). Yani RED **ölçüldü**, yalnız pytest
> sarmalayıcısı içinde değil.

#### Adım 3 — Minimal fix

**Dosya 1:** `.github/workflows/golden-flows.yml`, satır 172

```yaml
# ÖNCESİ (repr ile doğrulandı: 6 boşluk girinti, içinde ne ' ne " var, em-dash U+2014):
      - name: AST lint — Pydantic `user_id: int` type lie (rule-of-five)

# SONRASI:
      - name: "AST lint — Pydantic `user_id: int` type lie (rule-of-five)"
```

Çift tırnak seçildi: içerikte ne çift ne tek tırnak var (yalnız backtick ve
em-dash) → kaçış gerekmiyor; ayrıca aynı dosyadaki `python-version: "3.11"`
stiliyle tutarlı.

**Dosya 2:** `.github/workflows/quality-gate.yml`, satır 15-19

```yaml
# ÖNCESİ (repr ile doğrulandı):
  15|  pull_request:
  16|    branches: [main, master]
  17|  workflow_dispatch:
  18|  workflow_dispatch:
  19|

# SONRASI (18. satır SİLİNİR):
  15|  pull_request:
  16|    branches: [main, master]
  17|  workflow_dispatch:
  18|
```

**İKİ AYRI COMMIT.** İki kusur bağımsız; tek commit'te birleştirilirse hangi
değişikliğin hangi GitHub sonucunu ürettiği ölçülemez.

#### Adım 4 — GREEN doğrulama

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/unit/test_workflow_yaml.py -v --no-header -p no:cacheprovider
# Beklenen: 12 passed (1 kontrol kolu + 11 workflow)

# MEVCUT bekçiyi de bir kez tüm dosyalara koştur (yeni hook eklemeye gerek YOK):
cd C:/Users/husey/kiro2
pre-commit run check-yaml --all-files
# Beklenen: Passed

# GitHub tarafı doğrulama (push SONRASI — asıl kanıt):
curl -s https://api.github.com/repos/HuseyinAts/kiro2/actions/workflows \
  | python -c "import json,sys; [print(w['name'],'|',w['path']) for w in json.load(sys.stdin)['workflows']]"
# Beklenen: 'Golden Flows | .github/workflows/golden-flows.yml'
#           'Quality Gate (New-Endpoint Checklist) | .github/workflows/quality-gate.yml'
#   (dosya YOLU değil, beyan edilen AD görünmeli)
```

#### Adım 5 — MUTASYON

| # | Mutasyon | Beklenen | Ne kanıtlar |
|---|---|---|---|
| **M1** | `golden-flows.yml:172`'deki çift tırnakları kaldır | `[golden-flows.yml]` **FAIL** | Fix'in yük taşıdığı |
| **M2** | `quality-gate.yml`'e ikinci bir `  workflow_dispatch:` geri ekle | `[quality-gate.yml]` **FAIL** | — |
| **M3** | Testte `yaml.load(..., _TekrarsizYukleyici)` → `yaml.safe_load(...)` | **M2 artık ÖLDÜRÜLMEZ** (quality-gate yeşil geçer) | **Dup-key korumasının yük taşıdığını kanıtlar.** Bu plan yazarı bunu bellekte ölçtü: düz `safe_load` 2 RED yerine 1 RED verir. Teşhisin önerdiği test yarım-vakumdu |
| **M4** | `_KOK = parents[3]` → `parents[2]` | `test_kontrol_kolu_workflow_dizini_bulundu` **FAIL** | 0-parametre sessiz-yeşil senaryosunu yakalar |
| **M5** | `_WF.glob("*.yml")` → `_WF.rglob("*.yml")` | 11 → 29 dosya; `.archive/comprehensive-ci-cd.yml` **FAIL** eder | Aşırı-kapsamın gürültü ürettiğini gösterir — GitHub alt dizinleri okumaz |
| **M6** (kontrol) | Sağlam bir workflow'a (ör. `ci.yml`) dokunma | İlgili parametre **PASS** kalmalı | Testin her şeye kırmızı yanmadığını gösterir |

### C.3 Riskler

| Risk | Ölçüm | Not |
|---|---|---|
| **Kapılar KIRMIZI yanacak (yeşil değil)** | golden-flows'un 7 AST linter'ı yerelde koşuldu: `audit_missing_auth` **EXIT=1**, `audit_missing_is_active` **EXIT=1**, `audit_missing_rate_limit` **EXIT=1**, `audit_httpexception_guard` **EXIT=1**; temiz olan 3: `audit_db_dependency`, `audit_dual_table_trap`, `audit_pydantic_user_id`. quality-gate: `audit_path_drift --fail` **EXIT=1** (33 kalem), `ruff --select=E,F,W` **"Found 2231 errors"**, `audit_orm_schema_drift` **EXIT=1** | **BU BİR REGRESYON DEĞİL, DÜRÜSTLÜKTÜR.** Fix beklenen çıktısı "CI yeşil" DEĞİL, "CI dürüstçe kırmızı + fantom 0-iş koşumları bitti" |
| **Merge bloğu** | `.claude/rules/golden-flows.md` kural 1: GF fail = PR MERGE EDİLEMEZ | master'a açılacak ilk PR bloklanır. **Bu ordering'den bağımsızdır** — CI ne zaman düzeltilirse o zaman yüzeye çıkar. Erken çıkması geç çıkmasından iyidir (bkz. C.5 onay) |
| **Bu dalda hiçbir koşum görülmeyecek** | golden-flows `on:` = push/PR `[main, master, develop]`; quality-gate'te push tetikleyicisi **HİÇ YOK** | Çalışılan dal `feature/self-evolution-optimization` → fix sonrası bu dalda koşum **ÜRETİLMEZ**. "Fix'ledim ama koşmuyor" yanılgısına düşülmesin; doğrulama `workflow_dispatch` veya master'a PR ister |
| **`origin/master` da bozuk** | ayrı okundu, iki kusur da orada | Fix master'a da taşınmalı (merge/cherry-pick), yoksa master push'ları fantom kırmızı üretmeye devam eder |
| **Actions dakikası tüketimi artar** | `health-checks.yml` `on: schedule: '*/5 * * * *'` → 5 754 koşum birikmiş; Nisan'daki harcama-limiti bloğunun muhtemel sürücüsü | Gerçek koşumlar başlayınca tüketim sıçrar. Cron aralığı **ayrı bir karar** (bu fix'in kapsamı değil, ama izlenmeli) |
| **`.archive/comprehensive-ci-cd.yml` de bozuk** | ruamel: `could not find expected ':'`, satır 70 | **ATIL** — GitHub `.github/workflows` alt dizinlerini okumaz (kanıt: `GET /actions/workflows` 13 kayıt = 11 aktif + 2 dinamik dependabot; sayı birebir). Dokunulmaz |

**Geri alım:**

```bash
# Commit'liyse (tercih edilen):
git revert <fix_commit>

# Commit'siz denemede:
git checkout HEAD -- .github/workflows/golden-flows.yml .github/workflows/quality-gate.yml && git status --short
# çıktı BOŞ olmalı — boş değilse geri alım YAPILMAMIŞTIR (.claude/rules/verification.md)
```

### C.4 BU FIX YANLIŞSA NASIL ANLARIZ

| Sinyal | Nasıl ölçülür | Ne demek |
|---|---|---|
| **Workflow adı hâlâ dosya yolu** | Push sonrası `GET /actions/workflows` → `name` alanı hâlâ `.github/workflows/golden-flows.yml` | GitHub dosyayı hâlâ ayrıştıramıyor. Üçüncü bir YAML kusuru var VEYA push gitmemiş. Yerel test yeşil + GitHub kırmızı = **push doğrulanmamış** |
| **`workflow_dispatch` ile tetikledim, `total_jobs=0`** | `POST /actions/workflows/259116900/dispatches` sonra `GET /runs/<id>/jobs` | **YAML tek bloklayıcı değildi.** En olası ikinci bastırıcı: faturalama/harcama limiti geri geldi. Kontrol: `GET /check-runs/<id>/annotations` → *"The job was not started because recent account payments have failed…"* |
| **`total_jobs=1` ama `steps` listesi BOŞ, süre 2-4 sn** | Aynı `/jobs` çıktısı | **Tam olarak Nisan/Mayıs imzası.** İş yaratıldı ama başlatılmadı = hesap düzeyi Actions engeli. Kod tarafında yapılacak bir şey yok |
| **Yerel test yeşil ama GitHub kırmızı diyor** | `pre-commit run check-yaml --all-files` + `python -m pytest tests/unit/test_workflow_yaml.py` ikisi de yeşilse | GitHub'ın ayrıştırıcısı bizimkinden katı bir kural uyguluyor demektir. Anotasyon metni (`Invalid workflow file: … (Line: N, Col: M)`) kesin konumu verir — **kimlik doğrulamalı** API isteği gerekir (`gh` CLI bu makinede YOK) |
| **Kapı yeşil yandı** | golden-flows koşumu `success` | **ŞÜPHELEN.** Ölçüldü: 4/7 AST linter yerelde `EXIT=1`. Yeşilse ya linter'lar bu arada düzeltildi ya da iş adımlara ulaşmadan "başarılı" sayıldı. `/jobs` çıktısındaki adım listesini AÇ ve `AST lint` adımlarının gerçekten koştuğunu gör |
| **`test_kontrol_kolu_workflow_dizini_bulundu` FAIL** | pytest çıktısı | Yol türetmesi kırık (`parents[3]`). Diğer testler 0 parametreyle sessizce yeşil geçerdi — **kontrol kolu tam bunun için var** |

### C.5 🟡 ONAY GEREKTİREN KARAR — merge bloğu

CI düzeltilir düzeltilmez `.claude/rules/golden-flows.md` kural 1 ("GF fail =
PR MERGE EDİLEMEZ") **fiilen yürürlüğe girer**. Ölçülen borç:

| Kapı | Kırmızı yapan | Sayı |
|---|---|---|
| golden-flows | `audit_missing_auth --fail-on-high` | 33 bulgu / 31 HIGH |
| golden-flows | `audit_missing_is_active --fail-on-high` | 1 HIGH (`api/curator.py:522`) |
| golden-flows | `audit_missing_rate_limit --fail-on-high` | 1 HIGH (`api/enhanced_chat.py:1025`) |
| golden-flows | `audit_httpexception_guard --fail` | 12 riskli / 3 dosya |
| quality-gate | `audit_path_drift --fail` | 33 kalem |
| quality-gate | `ruff --select=E,F,W --ignore=E501` | 2 231 hata |
| quality-gate | `audit_orm_schema_drift --fail` | **CI'da YAPISAL OLARAK geçemez** — `psycopg2.connect(get_db_url())` ile `localhost:5434`'e bağlanıyor, o workflow'da postgres service YOK → `return 2` |

**Seçenekler (operatör kararı):**

1. **Kırmızıyı kabul et** — kapı dürüstçe kırmızı, borç ayrı bir backlog olarak
   işlenir. Merge'ler bu süre boyunca bloklanır.
2. **Backlog'u önce kapat** — CI fix'ini bu 7 kalem düzelene kadar beklet.
   (Ama o zaman gürültü koşumları da devam eder.)
3. **quality-gate Adım 4'ü (`audit_orm_schema_drift`) kaldır veya postgres service
   ekle** — bu adım *kod düzeltilse bile* geçemez, yani gerçek bir kapı değil,
   yapısal bir kırmızıdır. Ayrı ve küçük bir iş.

**Bu kararı almadan İŞ C'nin fix'i push EDİLMEZ.** (Yazılabilir, test edilebilir,
commit edilebilir — push kararı ayrıdır.)

---

## SIRALAMA VE GEREKÇE

### Kriter: risk × kazanç × bağımlılık

| Sıra | İş | Risk | Kazanç (ölçülmüş) | Bağımlılık | Maliyet |
|---|---|---|---|---|---|
| **0** | **SIFIRINCI ADIM** (ES severity ölçümü) | YOK (salt okuma) | Planın sırasını değiştirebilecek TEK bilgi | Yok | 4 komut, ~2 dk |
| **1** | **İŞ C** (CI YAML) | DÜŞÜK (kod değişmiyor) | ~740 fantom `failure` koşumu susar; kapı durumu dürüstleşir | Yok | 2 satır + 1 test |
| **2** | **İŞ A** (admin POST/DELETE) | DÜŞÜK-ORTA (yetenek açılışı, soft-delete) | Ölçülmüş 3/3 canlı 500 kapanır; sahte-sahiplik veri kaybı yolu kapanır | Yok | 2 commit, 5 dosya |
| **3** | **İŞ B** (ES) | ORTA (outward-facing) | Arama kalite kapısına hizalanır; cevap anahtarı index'ten kalkar | **ONAY** (B.4) | 3 yeni + 3 değişen dosya |

### Neden C önce? (ve neden bu "koruma" DEĞİL)

**Sorulan soru:** *CI fix'i önce yapılırsa diğer fix'ler CI korumasından
yararlanır mı, yoksa CI zaten başka sebeple mi çalışmıyor?*

**Ölçülmüş cevap: HAYIR, yararlanmazlar. Üç bağımsız sebeple:**

1. **`on:` filtresi kapsamıyor.** golden-flows `on:` = push/PR `[main, master,
   develop]`; çalışılan dal `feature/self-evolution-optimization`. quality-gate'te
   **push tetikleyicisi HİÇ YOK** (yalnız `pull_request [main, master]` +
   `workflow_dispatch` — 29 May commit'inin amacı Actions dakikası azaltmaktı).
   Yani YAML düzeltilse bile bu dalda **koşum üretilmez**.
2. **Koşsa bile e2e'ye ULAŞAMAZ.** golden-flows'un 17 adımının 5.'si
   `audit_missing_auth --fail-on-high` ve yerelde `EXIT=1`. İş orada ölür;
   migration / seed / `nohup uvicorn` / 30 sn health bekleme / GF6w e2e adımlarına
   **hiç sıra gelmez**. İŞ A'nın GF6w'yi kıracak olması bu yüzden CI'da bugün
   *görünmez* — koruma da yok, engel de yok.
3. **quality-gate Adım 2 zaten vakum.** `pytest tests/e2e/test_golden_flows.py -m golden_flow`
   koşuyor ama o workflow backend'i **ayağa kaldırmıyor**; fixture `/health`
   başarısızsa `pytest.skip` ediyor (`test_golden_flows.py:77-82`). Workflow'un
   kendi yorumu bunu itiraf ediyor (satır 57-61). Yani o adım her zaman "yeşil" —
   hiçbir şey ölçmüyor.

**O hâlde C neden yine de önce?** Koruma için değil, **üç ucuz sebep** için:

- **En düşük risk:** 2 satır YAML, uygulama kodu değişmiyor, geri alım `git revert`.
- **Gürültü susturma:** İki kapı her push'ta fantom kırmızı X üretiyor. Bu, A ve
  B'nin gerçek sonuçlarını okumayı zorlaştırır. Ölçüm ortamını önce temizle.
- **Merge bloğu erken yüzeye çıksın:** C ne zaman yapılırsa yapılsın master'a
  PR'ı bloklayacak (C.5). Bunu A ve B tamamlandıktan *sonra* keşfetmek, ikisini
  de merge kuyruğunda kilitler. Önce keşfet, kararı önce ver.

### Neden A, B'den önce?

- **A'nın bağımlılığı yok, B'nin ONAY bağımlılığı var.** B'nin gerçek reindex'i
  operatör onayı bekler; A o beklerken tamamlanabilir.
- **A daha ucuz:** 2 dosya + test. B: 3 yeni dosya + celery + alias provası.
- **Ama SIFIRINCI ADIM bu sırayı BOZABİLİR.** ES 9200 auth'suz ve
  `correct_answer` sayısı > 0 çıkarsa, B'nin *ağ kısıtlaması* kısmı (bind →
  `127.0.0.1`) A'dan da C'den de önce gelir. Reindex yine onay bekler ama
  erişimi kapatmak beklemez.

### Bağımlılık grafiği

```
SIFIRINCI ADIM (ölçüm)
   │
   ├── [S0 YÜKSEK çıkarsa] ──► B-ağ kısıtlaması (ACİL, onaysız yapılabilir)
   │
   ▼
İŞ C (2 satır YAML)  ──► C.5 ONAY (merge bloğu kararı) ──► push
   │
   ▼
İŞ A-1 (DELETE, 1 satır)  ──►  İŞ A-2 (POST + GF6w benzersizleştirme)
   │                              ▲
   │                              └── A-1 olmadan A-2 değersiz,
   │                                  A-2 olmadan A-1 eksik (sahte sahiplik)
   ▼
İŞ B-ölçüm (--dry-run)  ──►  B.4 ONAY  ──►  B-reindex  ──►  xfail marker kaldır
```

**İşler arası teknik bağımlılık YOK** — üçü farklı dosyalara dokunuyor, çakışma
yok. Bağımlılıklar yalnız iş İÇİNDE (A-1 → A-2) ve onay kapılarında.

---

## Ölçüm Kaydı (uygulama sırasında doldurulur)

| # | Ölçüm | Komut | Sonuç | Tarih |
|---|---|---|---|---|
| S0.1 | ES port bağlaması | `docker port turkiye_sinav_elasticsearch` | — | — |
| S0.2 | ES kimlik doğrulama | `curl -s -o /dev/null -w '%{http_code}' http://localhost:9200/` | — | — |
| S0.3 | Doküman düzeyi cevap anahtarı | `_count exists:correct_answer` | — | — |
| S0.4 | LAN erişimi | `netstat -ano \| grep ':9200'` | — | — |
| A-1 RED | DELETE testi kırmızı mı? | `pytest tests/unit/test_admin_api.py::TestDeleteQuestion` | — | — |
| A-2 RED | POST testi kırmızı mı? | `pytest tests/unit/test_soru_ingestion_upsert.py` | — | — |
| B RED | Index hijyen testi kırmızı mı? | `pytest tests/e2e/test_es_index_hygiene.py` | — | — |
| B kapı-dışı | **Gerçek** kapı dışı doküman sayısı | Yukarıdaki testin FAIL çıktısı | — | — |
| B dry-run | Kaynak satır sayısı | `python scripts/es_reindex.py --dry-run` | — | — |
| C RED | Workflow testi kırmızı mı? | `pytest tests/unit/test_workflow_yaml.py` | — | — |
| C GitHub | Workflow adları düzeldi mi? | `GET /actions/workflows` | — | — |

---

## Açık sorular (uygulamadan önce cevaplanmalı)

1. **ES 9200 ağdan erişilebilir mi ve kimliksiz mi?** → SIFIRINCI ADIM. Planın
   tek ölçülmemiş severity iddiası; sırayı değiştirebilir.
2. **`GET /api/v1/questions/search/elasticsearch` gerçek kullanıcı trafiği
   alıyor mu?** → 17 saatlik log penceresi bunu kesinleştiremez; frontend'de
   elle-yazılmış çağıranı yok. B'nin daralmasının kimi etkilediği buna bağlı.
3. **Merge bloğu kabul mü?** → C.5. Kabul edilmezse C'nin push'u beklemeli.
4. **Arama havuzu %61 daralması ürün tarafından onaylı mı?** → B.4 / K1.
5. **`PUT /content/questions/{id}` gerçekten 500 mü?** → Kod yolu DELETE ile
   birebir aynı, ama canlı logda hiç PUT çağrısı yok. **Ölçülmedi, çıkarım.**
   Ölçülürse aynı 1-satırlık desen uygulanır (ayrı görev).
6. **`test_no_ghost_documents` bugün kırmızı mı?** → "9 hayalet" iddiası hiç
   doğrulanmadı. Geçerse test regresyon koruması olarak kalır.
7. **`health-checks.yml` `*/5` cron'u kısılmalı mı?** → 5 754 koşum birikmiş;
   Nisan'daki harcama-limiti bloğunun muhtemel sürücüsü. Ayrı karar.

---

## Bilinen ölçüm boşlukları (bu plan bunları İDDİA ETMİYOR)

| Boşluk | Neden ölçülemedi | Etkisi |
|---|---|---|
| Hiçbir pytest FAIL'i **gözlemlenmedi** | Her iki teşhis turu salt-okunur mandat altındaydı; bu plan turu da yazma yapmadı | Tüm RED iddiaları **türetilmiş**. İSTİSNA: İŞ C'nin RED'i bellekte birebir koşturuldu. **Her fix'ten önce RED fiilen görülmelidir** |
| ES `remove_index` eylemi bu kurulumda denenmedi | Yazma gerektirir | Alias takası **prova edilmeli** (atılabilir index çiftiyle) |
| "60 605 kapı dışı" / "9 hayalet" | Sınama turu yeniden üretemedi; üst sınır (39 143) iddiayla çelişiyor | **Plan bu sayıları hiçbir yerde kullanmıyor.** Gerçek sayıyı testin kendisi ölçecek |
| A fix'i sonrası semptomun gerçekten kaybolduğu | Kaldırma deneyi yazma gerektirir | A.6'daki "semptom kaybolmadı" satırı bunun kontrolü |
| PUT 500 | Logda hiç PUT yok | Kapsam dışı, çıkarım olarak işaretli |
| GitHub koşum anotasyonlarının tam metni | `gh` CLI yok, anonim API kimlik doğrulaması gerektiriyor | C.4'te alternatif kanıt yolu (`name` geri-düşüşü + `total_jobs=0`) verildi |
| 1 Nis – 30 Tem arası uygulama davranışı | Konteyner logu yalnız 17 saat geriye gidiyor, merkezi log yok | "4 aydır hiç çağrılmadı" iddiaları koda + frontend'e dayanıyor, loga değil |

---

*Oluşturulma: 30 Temmuz 2026. HEAD `8d8bdf31f`. Bu plan yazılırken 16 canlı ölçüm
yapıldı (tablo en üstte); teşhis raporlarından devralınan ve yeniden
doğrulanmayan her iddia `DOĞRULANMADI` ile işaretlendi.*
