# A1 Altın Yol — dört ayağın uçtan uca ölçümü

**Tarih:** 20 Ağustos 2026 · **Oturum:** S241 · **Taban commit:** `0973e5495`
**Tasarım:** `docs/superpowers/specs/2026-08-20-a1-altin-yol-e2e-design.md`
**Plan:** `docs/superpowers/plans/2026-08-20-a1-altin-yol-olcum.md`

---

## Tek cümle

Öğrenci kayıt olabiliyor ve kapıda 353 gerçek TYT Matematik sorusu var, ama
**hiçbir öğrenci bugüne kadar tek bir sınav başlatamadı** — `exam_sessions`
tablosunda **sıfır satır** var ve sebebi tek bir kusur: RLS politikası
fail-closed, GUC ise sınav motorunun kullandığı bağlantıda hiç set edilmiyor.

---

## Methodology

| | |
|---|---|
| Yöntem | 5 bağımsız ölçücü (canlı stack, salt-okunur) → 5 bağımsız şüpheci (çürütme görevli) → 1 eksiklik eleştirmeni |
| Ajan | 11, hepsi tamamlandı (0 hata, 0 boş dönüş) · 523 araç çağrısı · ~50 dk |
| Özne | Tek test öğrencisi `a1e2e+s241@kiro2-e2e.dev` (`001f4676-…`), FAZ 0'da elle açıldı |
| Ortam | backend `localhost:8000` (kiro2-backend) · frontend `:3000` · PostgreSQL 18.1 `:5434` db `kiro2` |
| Kanıt standardı | Ham `curl` gövdesi / container log / `psql` çıktısı. Özet kanıt sayılmadı |
| Yazma | FAZ 0'daki tek test hesabı dışında **sıfır** yazma. `question_bank` okundu, yazılmadı |
| Yeniden üretilebilir | Evet — her bulgu `olcum_komutu` alanı taşıyor, şüpheci komutu **kendi** koştu |
| Ham kayıt | `…/workflows/wf_94cb8737-152/journal.jsonl` (262 KB, 22 satır, 11 ajan sonucu) |

**Çürütme sonucu: 45 bulgu → 44 ayakta / 1 düştü.** Düşen tek bulgu bir
**alet arızasıydı**: "kayıt ucu pratikte rate-limitsiz, 8 ardışık POST'ta 429
yok" iddiası; gerçek eşik 10/60 sn, ölçen 8 istek attığı için eşiğin **bir
altında** kalmıştı — klasik örneklem-eşik-altı hatası.

**Ölçenin kendi aleti bu turda 3 kez yanıldı** (dürüst kayıt, hepsi ana oturumda):

| # | Yanlış ölçüm | Neden yanlış | Doğrusu |
|---|---|---|---|
| 1 | `WHERE primary_topic_id LIKE 'MAT%'` → **0** | kolon UUID; `MAT.*` kodu başka tabloda | `topic_hierarchy.code` ile JOIN |
| 2 | `information_schema.columns … 'mv_safe_for_beta'` → **boş** | matview orada yok | `pg_attribute` |
| 3 | `GET /api/v1/sorular` → **404** | uç kök yolda, prefix'siz | `GET /sorular` |

Üçü de "0/boş/yok" görünümündeydi. Bu yüzden bu raporda hiçbir sıfır iddiası
kontrol kolu koşulmadan kabul edilmedi.

---

## Dört ayağın yargısı

| Ayak | Yargı | Kök neden ankrajı |
|---|---|---|
| **L1 Kayıt** | 🟡 **ÇALIŞIYOR** (mutlu yol) — ama bir kullanıcı alt kümesine kapalı | `application/commands/auth.py:100` |
| **L2 Doğrulama** | 🔴 **YOK** — kod yolu hiç yok | `application/commands/auth.py:86` |
| **L3 Sınav üretimi** | 🔴 **KIRIK** — seçim çalışıyor, teslim çalışmıyor | `core/osym_exam_engine.py:441` |
| **L4 Puanlama** | 🔴 **KIRIK** — tamamı erişilemez + kırılım yanlış katmanda | `core/osym_exam_engine.py:1364` |
| **L5 Yüzey** | 🔴 **KIRIK** — sayfa sağlam, ilk yazma adımı 500 | `core/dependencies.py:455` |

---

## Doğrulanmış engelleyiciler (ağırdan hafife)

### B1 — 🔴 P0 · `exam_sessions` RLS her sınav oluşturmayı reddediyor

**A1'in tek ve asıl engeli.** Üç ayağı (L3 teslim, L4 tamamı, L5 yüzey) aynı anda öldürüyor.

Zincir, dört ayrı ölçümle çivilendi:

1. `exam_sessions` üzerinde `tenant_isolation` politikası var ve **fail-closed**:
   `WITH CHECK ((organization_id)::text = current_setting('app.current_org_id', true))`
2. Backend `kiro2_app` rolüyle bağlı → `rolsuper=f`, `rolbypassrls=f` → **RLS uygulanıyor**
3. GUC'u set eden **tek** yer `core/dependencies.py:455-462` ve `is_local=true`
   (transaction-local, istek kapsamlı oturuma bağlı)
4. Motor o oturumu **kullanmıyor**: `core/osym_exam_engine.py:437-463`
   `async with get_db_session_context() as db_session:` ile **ayrı bağlantı** açıyor.
   Ayrıca `api/sinav.py`'nin **27 ucunun 0'ı** `get_current_tenant`'a bağımlı değil.

```
$ curl -X POST .../api/v1/osym-exam/beta-practice?num_questions=40   -> HTTP 500
$ curl -X POST .../api/v1/osym-exam/create   (MATEMATIK/40)          -> HTTP 500
docker logs kiro2-backend:
  asyncpg.exceptions.InsufficientPrivilegeError
  [SQL: INSERT INTO exam_sessions (id, student_id, exam_type, …)]
$ psql -c "SELECT count(*) FROM exam_sessions;"                      -> 0
```

`dependencies.py:456-457`'deki yorum bu kusurun **belgelenmiş sebebidir** ve
canlıda geçersizdir:

> `# RLS aktivasyon prerequisite: transaction-local GUC. App superuser (postgres)`
> `# olduğundan RLS şu an bypass edilir (no-op);`

Uygulama artık `postgres` değil `kiro2_app` ile bağlanıyor. Varsayım bayatladı,
yorum kaldı, kapı sessizce kapandı.

**Yan ölçüm — MEMORY.md düzeltmesi.** Kayıtlı bilgi *"politika kalıbı … GUC set
edilmezse tüm satırlar geçer"* diyordu. Ölçüldü: **73 politika FAIL_CLOSED /
6 permissive_when_unset**. `polqual` ve `polwithcheck` üzerinden çapraz kontrol
edildi, iki hesap da aynı sonucu verdi. Kayıtlı bilgi politikaların **%92'si
için yanlış** ve tam da bu yanlışlık B1'in görülmesini geciktirmiş olabilir.

---

### B2 — 🔴 P0 · Düz öğrenci token'ı cevap anahtarını okuyabiliyor

**Beş ayağın hiçbiri bulmadı** — eksiklik eleştirmeni buldu, ana oturum doğruladı.
L3 "cevap sızıntısı YOK" demişti; doğruydu **ama yalnız sınav ucu için**, ve o uç
zaten B1 yüzünden açılamıyor. Sızıntı başka yerde:

```
$ TOKEN=<duz ogrenci JWT>
$ curl -H "Authorization: Bearer $TOKEN" 'localhost:8000/sorular?limit=3'
  -> HTTP 200 · alanlar: correct_answer, explanation, times_correct
     f98e4492-… -> 'B'      88e7c33b-… -> 'B'      0d7a5b2a-… -> 'A'
     explanation: "A marka sünger ıslatıldığında $36 \cdot (1 + \frac{1}{3}) = …"

$ psql -c "SELECT id, correct_answer, (id IN (SELECT id FROM mv_safe_for_beta)) FROM question_content WHERE id IN (…)"
  0d7a5b2a-…|A|t      88e7c33b-…|B|t      f98e4492-…|B|t
```

**3/3 birebir tuttu ve üçü de kapıda.** Yani sızan şey rastgele bir alan değil,
öğrenciye servis edilecek soruların **doğru cevabı ve tam çözümü**.

Aynı sınıf iki uçta daha ölçüldü: `GET /api/v1/osym/questions` ve
`GET /api/v1/osym/random-questions` — ikisi de `correct_answer` taşıyor.

Bu, B1'den bağımsız ve ondan **daha temel**: sınav motoru onarılsa bile,
öğrenci cevap anahtarını okuyabildiği sürece platformun ölçtüğü şey geçersizdir.

---

### B3 — 🔴 P0 · "Konu kırılımı" aslında **ders** kırılımı

A1'in dördüncü ayağı — *"konu kırılımını görür"* — B1 onarılsa bile karşılanmıyor.

```
Motor 40 TYT MATEMATIK sorusu seciyor  ->  12-13 farkli GERCEK konu kodu
                                            (MAT.PRM, MAT.USL, MAT.FON, MAT.PRB…)
Donen kirilim                          ->  {'MATEMATIK': 40}     TEK KOVA
```

Ankraj `core/osym_exam_engine.py:1364` (`subject_area` ile gruplanıyor).
Şüpheci bağımsız koştu: 40 soru / 12 konu kodu / 1 kova. Seçim rastgele olduğu
için ölçümden ölçüme 12-13 arası oynuyor; sapma kusur değil, kova sayısı kusur.

Ayrıca `QuestionResponse.topic` ham UUID dönüyor (`3726ee2d-…`), konu kodu
(`MAT.USL`) değil — yüzeyin konu adını göstermesi için gereken veri **var**
(`topic_hierarchy.code` ve `name_tr` mevcut) ama taşınmıyor.

---

### B4 — 🔴 P0 · E-posta doğrulama yolu **hiç yok**

1.119 canlı yolda kullanıcı e-posta doğrulaması yok. 14 "verify/onay" eşleşmesinin
hiçbiri bu değil (2FA, veli-onay, öğretmen sertifikası, COPPA).
`api/` ve `services/` katmanlarında `users.is_verified`'ı `TRUE` yapan **tek satır yok**.
`commands/auth.py:95` INSERT'i sabit `FALSE` yazıyor. Kapı da yok:
`commands/auth.py:195` yalnız `is_active` kontrol ediyor, `is_verified` okunmuyor.

Çalışan magic-link zinciri (HTTP 200) bile `is_verified`'ı değiştirmiyor:
8/8 kullanıcı hâlâ `false`. `is_verified`'ı `TRUE` yapan tek kullanıcıya-açık yol
OAuth2 ve o uç ölü (`GET /auth/oauth2/google` → 500, `GOOGLE_CLIENT_ID` yok).

**Not:** bu ayağın "YOK" olması SMTP eksikliğinden değil. SMTP verilse bile
gönderilecek jeton üreten kod yok.

---

### B5 — 🟠 P1 · `username` çarpışması kurtarılamaz HTTP 500

`username` e-postanın yerel parçasından türetiliyor (`commands/auth.py:100`) ve
`ix_users_username` UNIQUE. Çarpışmada `UniqueViolationError` dışarı sızıp
`{"detail":"Dahili sunucu hatasi"}` + HTTP 500 oluyor (409/422 olmalı).

```
$ curl -X POST .../auth/kayit -d '{"email":"test@kiro2-l1probe2.dev", …}'  -> HTTP 500
docker log: duplicate key value violates unique constraint "ix_users_username"
            DETAIL:  Key (username)=(test) already exists.
$ psql -c "SELECT count(*) FROM users;"  -> 8 (istekten once de 8; rollback temiz)
```

Etki: `ahmet@gmail.com` kayıtlıysa `ahmet@hotmail.com` **asla** kayıt olamaz.
İstemciye eyleme dönüştürülebilir hiçbir bilgi dönmüyor; kullanıcının username
seçme imkânı da yok. Şüpheci sınıflandırmayı ENGELLEYICI'den KUSUR'a indirdi
(mutlu yol açık, yalnız 8 rezerve yerel parçayla çarpışanlar kapalı) — ama
B2C ölçeğinde çarpışma kesin.

---

### B6 — 🟠 P1 · Kayıt hatasında bcrypt hash + PII düz metin ERROR log'una düşüyor

`core/cqrs/bus.py:52` başarısız komutu `exc_info=True` ile logluyor ve kaydın
**gövdesi** SQL parametrelerini taşıyor: bcrypt hash, e-posta, ad, soyad,
doğum tarihi. Yukarıdaki B5 log çıktısında birebir görülüyor.

---

### B7 — 🟠 P1 · Aynı sınav için canlıda **iki farklı net formülü**

`osym_exam_engine.py:1903` ve `:1183` ile `api/sinav.py:785` → `net = D` (yanlış
götürmüyor). Başka bir yol → `net = D − Y/4`. ÖSYM kuralı `D − Y/4`. Hangi ucun
çağrıldığına göre öğrenci farklı net görüyor. (B1 yüzünden şu an ikisi de
tetiklenemiyor; onarılınca ilk çıkacak çelişki bu.)

---

## Çürütülen / indirgenen iddialar (sessiz silme yok)

| İddia | Sonuç |
|---|---|
| "Kayıt ucu pratikte rate-limitsiz (8 POST, 0×429)" | **DÜŞTÜ — alet arızası.** Gerçek eşik 10/60 sn; örneklem eşiğin altında kaldı |
| "Sayfalar mount edilmemiş `/api/v1/exams/*` ucuna konuşuyor" | **ÇÜRÜTÜLDÜ** (L5 kendi ön-yargısını ölçüp düşürdü): 29 URL'in 25'i canlı yollara gidiyor |
| "L1'de 2 ENGELLEYICI var" | **İNDİRGENDİ** — ikisi de A1 zincirini kesmiyor; mutlu yol açık |
| "L3'te 4 ENGELLEYICI var" | **İNDİRGENDİ 1'e** — B2/B3/B4 ya B1'in mekanizması ya da `beta-practice` ucunun ayrı kusuru |
| "L4'te 3 ENGELLEYICI var" | **İNDİRGENDİ 2'ye** — ikisi aynı kusurun iki yüzü (tek fix ikisini kapatır) |
| "Magic-link token'ı log'da → hesap ele geçirme" | **OLGU AYAKTA, ETKİ ÇÜRÜDÜ** — dönen jeton JWT değil, hiçbir uca geçmiyor (401) |
| "`QuestionBankItem.subject_area` yok" (ölçücünün kendi hipotezi) | **ÖLÇÜCÜ KENDİ HİPOTEZİNİ ÇÜRÜTTÜ** — sınıf düzeyinde yok, çalışma anında var |
| MEMORY.md: "GUC set edilmezse tüm satırlar geçer" | **ÇÜRÜTÜLDÜ** — 73 fail-closed / 6 permissive |

---

## Ölçülmemiş kalanlar (eksiklik eleştirmeni, 13 boşluk)

**Yüksek öncelik:**

1. **Çevrimdışı senkron paketi tasarım gereği `correct_answer` taşıyor** —
   `GET /api/v1/offline/sync-package` şu an 500 döndüğü için sızmıyor;
   **onarılırsa sızacak.** Beş ayağın hiçbiri bakmadı.
2. **Sınav süresi zorlanmıyor** — `ExamStatus.EXPIRED` tanımlı ama depoda
   hiçbir yerde **atanmıyor**; süre yalnız süreç-içi `asyncio.sleep` ile bekletiliyor.
3. **Cevap kalıcılığı ateşle-unut** — `save-answer` başarı dönüyor, DB yazımı sonra
   (`osym_exam_engine.py:641-645`). İdempotens ve eşzamanlılık hiç ölçülmedi.
4. **Hız sınırı / patlama** — tek öğrenci token'ıyla 40 ardışık `GET /soru/{id}`
   sonrası backend `HTTP 000` (bağlantı kurulamıyor) dönmeye başladı.

**Orta:** boş küme sessizce geçiyor (`practice-exam` 120 istenip 40 dönerken
`success:true`) · sınav kaynaklarında IDOR ölçülemedi · `/soru/{id}` kararsız 500
(`DetachedInstanceError`) · giriş ucunda kaba kuvvet/kilitleme ölçülmedi ·
boş cevap iki kaynakta farklı sayılıyor · **beş ayağın hiçbiri kendi aletinin
kontrol kolunu raporlamadı.**

**Düşük:** Türkçe bozulması yalnız soru metninde ölçüldü (500/500 temiz, md5
karşılaştırmalı); ad/konu adı ve yazma yolu açık · `POST /api/v1/search/questions`
sessizce 0 sonuç dönüyor.

---

## Çalışan kısımlar (pozitif bulgu da bir iddiadır, ayrıca ölçüldü)

- Kayıt mutlu yolu: tek transaction, `users` + `student_profiles` birlikte
- Rol yükseltme **bloklu**: `rol:"admin"` → 403 (mükerrer-e-posta kontrolünden **önce**)
- Parola politikası işliyor: `123456` → 422 (min uzunluk), `Parola12` → 422 (özel karakter)
- KVKK kapısı işliyor: `birth_date:"2012-01-01"` → 422; `veli_email` verilince geçiyor
- **Soru seçimi doğru**: 40 istendi → 40 seçildi, **40/40 kapıda**, 11-13 farklı MAT.* konu kodu, 0 boş şık
- Giriş ve `/exam/start` yüzeyi sağlam render ediyor; varsayılanlar A1 ile birebir
- Kimlik kapısı gerçek: tokenli 200 / tokensiz 401

---

## Sonuç

A1'in **içerik** engeli kalktı (S238-S240'ın kazanımı gerçek: kapıda 353 doğrulanmış
TYT Matematik sorusu var ve motor onları doğru seçiyor). Kalan engel **teslim
katmanında** ve büyük ölçüde **tek bir kusur**: B1.

Ama B1 onarılsa bile A1 tamamlanmaz — B2 (cevap anahtarı sızıntısı) ölçümü geçersiz
kılar, B3 (konu değil ders kırılımı) kriterin dördüncü ayağını karşılamaz,
B4 (doğrulama yolu yok) ikinci ayağını.
