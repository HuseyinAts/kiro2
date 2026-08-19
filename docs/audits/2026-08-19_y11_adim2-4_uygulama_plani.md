# Y11 ADIM 2-4 — Uygulama Planı (ölçüme dayalı, 19 Ağu 2026)

**Kapsam kararı (kullanıcı):** yalnız KIMYA · **Kapı politikası (kullanıcı):** `pending` yaz → ayrı onayla terfi
**Geri alma yordamı (kullanıcı):** `DELETE` + "bağlı cevap sayısı = 0" ön kapısı
**Girdi:** S232-H handoff · 8 ajanlı salt-okunur ölçüm turu (1,41M token) · ders defteri 143 ders

---

## 0. Bu plan neyi düzeltiyor

S232-H handoff'u "ADIM 2 için gereken her şey hazır" diyordu. Ölçüm bunu çürüttü:
**göçü koruyacak dört güvenlik ağının dördü de ölü**, ve göç commit'i kendi
pre-push kapısını kıracak.

| # | Ölçülen gerçek | Kanıt | Etki |
|---|---|---|---|
| P0-1 | `soru_hash` canlıda **%100 UUID4** | `_soru_hash_uret()` taklidi 5 satırda 0/5 | `uq_qb_soru_hash_active` **yapısal olarak ölü** |
| P0-2 | Kapı `v_safe_for_beta` **`is_active` filtrelemiyor** | viewdef WHERE'de 0 kez | `is_active=false` geri alması **NO-OP** |
| P0-3 | `question_bank(id)`'ye **11 FK, 11'i CASCADE** | `pg_constraint confrelid` | `DELETE` öğrenci cevabını **sessizce siler** |
| P0-4 | Yedek **bayat**: dump içinde `topic_hierarchy` 12, canlı 26 | `pg_restore --data-only` sayımı | Restore **ADIM 1'i geri alır** |
| P0-5 | Invaryant bekçisi pre-push'ta **3/3 SKIP** | `sss / EXIT=0`; DSN'le `2 passed, 1 xfailed` | "19 bekçi" bir **dosya** sayımı |
| P0-6 | Y12'nin 8 xfail'inden **4'ü INSERT anında XPASS** | `--runxfail`: `1>1`, `0>0` | **Göç commit'i kendi kapısını kırar** |
| P0-7 | `REFRESH` `kiro2_app` ile **çalışmaz** | `matviewowner=postgres`, `pg_has_role=f` | Celery matview görevi (#428) muhtemelen hiç koşmadı |
| P0-8 | `embedding` **768 ↔ 1536** | `format_type` (`udt_name` **0 fark** dedi) | Kolonu taşıyan INSERT patlar |

**Kapsam düzeltmesi:** handoff'un ders rakamları **kapı alt kümesi**, korpus değil
(MATEMATIK kapıda 14.119 / tabloda **65.341**). Kalan iş kapı düzeyinde **120,9M**,
tam korpus **743,1M** token. Tam korpus göçünde satırların **%94,07'si** bugün FK ihlali verir.

---

## 1. Planın dayandığı dersler (defterden, ankrajlı)

Her kapı bir derse bağlı. Ders yoksa kapı yoktur.

| Kapı | Zorlayan ders |
|---|---|
| Yedek "var" değil **geri yüklenebilir** olmalı | `L-s232-kurtarma-kaynagi-da-olculur` · `verification.md#GERI-ALIM-BIR-IDDIADIR` |
| Her yazım **iki turlu** (ROLLBACK provası → COMMIT) | S232-G kararı · `L-test-04` |
| Mutasyon `error` verirse ölçüm **geçersiz** | `L-s202-mutasyon-error-gecersiz` |
| Mutasyon **hiç uygulanmamış** olabilir | `L-s229-mutasyon-reddedilmis-olabilir` |
| Hayatta kalan mutasyon **testi değil aleti** ölçebilir | `L-s230-hayatta-kalan-mutasyon-gecersiz-olabilir` |
| Test paketi **bir dilim ölçer** — parametrize et | `L-s219-test-paketi-dilim-olcer` |
| "Göç ettin mi" ≠ "koruduğun mu" — **sayı** assert et | `L-s219-goc-ettin-mi-vs-korudun-mu` |
| Bekçi **bilinen-İYİ kolda yeşil** vermeli | `L-s232-kontrol-kolu-bekciyi-DUZELTIR` |
| Yanlış-**sıfır** tek kabul edilemez hata türü | `L-s219-yanlis-sifir-tek-kabul-edilemez-hata` |
| Hacim/bayrak **vekil ölçümdür** — örneklemi OKU | `L-s231-hacim-vekil-olcum-icerik-degil` · `L-s231-bayrak-tasidigi-iddiayi-kanitlamaz` |
| `correct_answer` **şık listesi olmadan anlamsız** | `L-s232-cevap-harfi-sik-listesi-olmadan-anlamsizdir` |
| Çarpıcı bulguda **önce aleti sına** | `L-s232-bulguyu-degil-aleti-sina` |
| Commit **yarım gidebilir** → `git show --stat` | `L-s229-commit-yarim-gidebilir` |
| Kapının ruff'ı **0.7.1**, kabuğunki 0.14.13 | `L-s224-arac-surumu-giris-noktasina-bagli` |
| Takipli-kirli filtresi `grep -v '^??'` | `L-s231-porcelain-bas-harfi-staged-sutunudur` |
| Türkçe SQL/metin **inline `-c`/heredoc'a girmez** | `L-s231-ters-tirnak-...` · S232-G alet hatası |
| `komut \| tail; $?` → **son halkayı** ölçer | `L-s232-boru-hattinda-exit-kodu-SON-komutundur` |
| Fix'in değerini ölçen sayıyı **önceden ilan et** | `L-s229-maskenin-altinda-maske` |
| Bekçi kırmızıysa: **bulgu benim satırımda mı?** | `L-s229-bekci-hakli-olabilir` |
| SKIP bir muafiyet değil, **üç ölçümlü erteleme** | `L-s229-kapi-borcu-karari-uc-olcum-ister` |
| Beklenmedik "0" → önce **`pwd`** | `L-s229-cd-kalici-sifir-collected` |
| `pre-commit run` **salt-okunur değil** | `L-s228-precommit-run-yazma-yapar` |
| Bilgi: mesaj→kaybolur, yorum→silinir, **test düşer** | `L-s219-yorum-cida-dusmez` |

---

## 2. Adım adım plan

Her adım = **ayrı turn + commit** (CLAUDE.md subagent disiplini).

### FAZ 0 — postgres erişimi (KARAR, kod yok)

Üç P0'ı birden açar. **İki dal planlandı**, iş hiçbirinde durmuyor.

| Dal | Sonuç |
|---|---|
| **postgres VAR** | A1 gerçek restore provası yapılabilir · FAZ E'de `REFRESH` çalışır · #428 celery görevi ölçülebilir |
| **postgres YOK** | A1 dosya-yedeği + damga-tabanlı `DELETE` tek geri alma · FAZ E **askıya alınır** (satırlar `pending` kalır, kapı değişmez) · #428 ayrı P1 açık iş |

**Kritik:** `pending` politikası sayesinde **FAZ D postgres'siz de yürür.** Bloke olan
yalnız FAZ E (terfi). Yani postgres kararı işi durdurmuyor, **son adımı** erteliyor.

### FAZ A — Güvenlik ağı (yazma: yalnız dosya/kod)

**A1. Yedeği yenile.**
`backups/kiro2_20260819_y11_oncesi.dump` ADIM 1 **öncesi** alınmış (içinde `topic_hierarchy`=12).
Yeni dump: `backups/kiro2_<tarih>_y11_adim2_oncesi.dump`.
**Kapı:** dump içinde `topic_hierarchy` **26** sayılır (`pg_restore --data-only | awk` ile satır sayımı) · 4 soru tablosu **36.967** · toplam **147.894**.
*Ders:* yedek bir iddiadır — dosyanın var olması kanıt değil.

**A2. Geri alma yordamını yaz + kanıtla.**
Yordam üç parçalı ve **sırası zorunlu**:
1. **Damga:** göçle yazılan her satır `pipeline_metadata->>'y11_batch'` taşır (ör. `'y11-kimya-2026-08'`). Geri alma kümesi **yalnız damgadan** türetilir — tarih penceresinden değil.
2. **Ön kapı (P0-3):** 11 CASCADE tablosunda o id'lere bağlı satır sayısı **= 0**. ≠0 ise geri alma **DURUR** ve insana döner.
3. **`DELETE FROM question_bank WHERE id IN (damgalı küme)`** — yavrular CASCADE ile gider.
**Kapı:** yordam bir script + testi olur; mutasyon: ön kapıyı kaldır → sahte bir `student_answers` satırıyla test kırmızı olmalı.
*Ders:* `L-s229-mutasyon-reddedilmis-olabilir` — mutasyonun uygulandığı bağımsız ölçülür.

**A3. Invaryant bekçisinin SKIP'ini kapat (P0-5).**
`backend/tests/db/test_question_bank_invariants.py` pre-push'ta `sss` veriyor; DSN yok.
`ders_zorlayici_kos.py` kancasına DSN geçir (env veya `.env` okuması).
**Kapı:** `pytest ... -rs` çıktısında **`sss` yok** · mutasyon: DSN'i boşalt → **skip'e döner** (yani ölçüm gerçekten DSN'e bağlıymış).
**Beklenen:** `2 passed, 1 xfailed` (hacim testi doğru alarm, `xfail(strict=True)`).
*Ders:* `L-s232-bayat-esik-mi-yoksa-susturulmus-gercek-alarm-mi` — eşiğe dokunma.

**A4. 4-tablo parity bekçisi yaz (bugün YOK, grep 0).**
Kısmi INSERT sessiz kalıyor: `question_bank`'a yazılıp yavruya yazılmayan satır
kapıda görünmez (`LEFT JOIN` → `quality_review_status` NULL), `question_bank`'ta durur, **hiçbir test görmez**.
**Kapı:** 6 yönlü yetim assert (her yavru için iki yön) · mutasyon: tek tabloya sahte INSERT → kırmızı.
*Ders:* `L-s230-yavru-tablonun-pk-si-id` — JOIN anahtarı `qc.id = qb.id`, **`question_id` kolonu YOKTUR**.

**A5. Y12 xfail sırasını çöz (P0-6).**
Ölçülen marjlar (`--runxfail`, 19 Ağu):

| test | bugünkü assert | göç sonrası | karar |
|---|---|---|---|
| i1 `pipeline_metadata` | `1 > 1` | **XPASS** | xfail **kaldırılacak** |
| i3 `primary_topic_id` | `1 > 1` | **XPASS** (16 konu gelir) | xfail **kaldırılacak** |
| i4 `reviewed_at` | `1 != 1` | **XPASS** | xfail **kaldırılacak** |
| i5 zorluk/IRT | `1 > 1` | **XPASS** (5 seviye gelir) | xfail **kaldırılacak** |
| i6 kapı lastik damga | `0 > 0` | **`pending` ile 0 kalır → xfail SÜRER** ⚠️ ÖLÇÜLECEK | dokunma |
| i2 `source_book` | `0.0 >= 0.5` | 3.306/40.521 ≈ **%8,2** → xfail sürer | dokunma |
| k2 mekanik çöp | `0,2075 <= 0,05` | xfail sürer | dokunma |
| k2 geçersiz anahtar | `105 == 0` | xfail sürer | dokunma |

⚠️ **i6 hakkındaki not bir ÖLÇÜM değil çıkarımdır.** Eleştirmen `auto_judged_high`
varsayımıyla "INSERT anında kırılır" dedi; `pending` yazınca satırlar
`quality_review_status`'e göre **kapıya hak kazanmaz**, dolayısıyla i6 muhtemelen 0'da
kalır. **FAZ D'den önce `--runxfail` ile bu tek test ölçülecek** (`L-s232-bulguyu-degil-aleti-sina`).

**✅ A5 ÖLÇÜLDÜ (20 Ağu) — P0-6 ÇÜRÜDÜ, bu tablo GEÇERSİZ.**

Yukarıdaki tablo eleştirmenin çıkarımıydı ve testlerin `question_bank`'ı ölçtüğünü
varsayıyordu. Kaynak okundu: **7 sorgu `FROM mv_safe_for_beta`**, yalnız 1'i
`FROM question_bank` (o da i6'nın ikinci ayağı). Ölçüm:

    i6 bugun (ajh/hv)                     : 0       -> assert 0 > 0 duser (xfail DOGRU)
    i6 + 'pending' IN listesine eklenirse : 9.894   <- DOGAL DENEY
    status: auto_judged_high 27.073 (kapida 27.073) | pending 9.894 (kapida 0)

Canlıda **zaten 9.894 `pending` satır var ve hiçbiri kapıda değil** — FAZ D'nin
yazacağı satırların davranışı için hazır bir doğal deney. Sonuç:

| Test | Ölçtüğü popülasyon | FAZ D sonrası |
|---|---|---|
| i1 · i2 · i3 · i4 · i5 · k2×2 | `mv_safe_for_beta` | **değişmez** (pending matview'e girmez, REFRESH de yok) |
| i6 | status'e göre hak eden ama mv'de olmayan | **0'da kalır** (`pending` hak etmiyor) |

→ **8 xfail'in 8'i de FAZ D'yi sağ atlatır.** "Göç commit'i kendi kapısını kırar"
`auto_judged_high` varsayımına dayanıyordu; `pending` politikasıyla geçersiz.

→ **FAZ D'den "xfail'leri kaldır" adımı DÜŞÜYOR.** O iş ve aşağıdaki sıra kısıtı
tamamen **FAZ E'ye** (terfi) kayıyor.

**Sıra kısıtı (FAZ E için geçerli):** pre-push **push anında** koşar, `UPDATE` ise
DB işlemidir. Doğru sıra → **(1) `pending → auto_judged_high` + REFRESH →
(2) xfail işaretlerini kaldır → (3) commit + push.** Ters sırada testler FAIL verir.

*Ders: adversarial ajanın bulgusu da bir İDDİADIR. Eleştirmen 8 P0'ın 7'sinde
haklıydı; P0-6'da testin hangi tabloya JOIN'lediğini okumadan çıkarım yaptı.*

### FAZ B — Göç script'i (TDD, yazma yok)

**B1.** `backend/scripts/quality/y11_goc.py` — **saf dönüşüm fonksiyonu**:
kaynak satır (78 kolon) → 4 hedef satır. DB'siz test edilebilir olmalı.
*Ders:* `L-s202-vakum-saf-fonksiyon` — canlıda üretilemeyen durum saf fonksiyona ayrılır.

**B2. RED testleri ÖNCE** (9 test, hepsi fix'ten önce **doğru sebeple** düşmeli):

| # | İddia | Neden (ölçülen) |
|---|---|---|
| 1 | `embedding` çıktıya **HİÇ konmaz** | 768 ≠ 1536 (P0-8) |
| 2 | topic remap **`code` ile** yapılır, id ile değil | canlı KIM `72e79276…` ≠ kaynak `dcd3211c…`; 306 satır |
| 3 | Eksik konu **kopyalanmaz** | `topic_hierarchy_code_key UNIQUE(code)` ihlali verir |
| 4 | `created_by` **NULL** basılır + `pipeline_metadata`'ya not | 65 satır yetim FK |
| 5 | `is_public` **açıkça** verilir | NOT NULL + default'suz |
| 6 | `quality_review_status='pending'` | kullanıcı kararı |
| 7 | Dedup **metin normalizasyonuyla** (hash ile DEĞİL) | P0-1: hash rastgele UUID |
| 8 | Dedup **şıkları da** hesaba katar | `L-s232-cevap-harfi-sik-listesi-olmadan-anlamsizdir` (516 meşru soru yanlışlıkla silinecekti) |
| 9 | Her satır `y11_batch` damgası taşır | geri alma kümesinin tek kaynağı |

**B3. Mutasyon bataryası** — her kapı için bir mutasyon; hepsi `failed`, hiçbiri `error`,
her geri alım `git status --short` **boş** ile doğrulanır (`read_bytes/write_bytes`, CRLF tuzağı).

### FAZ C — ADIM 2 pilot: 50 satır, `BEGIN … ROLLBACK`

**Örneklem seçimi kör nokta bırakmaz** (`L-s219-test-paketi-dilim-olcer`):
≥5 **remap gerektiren** (KIM/FIZ kök konulu) · ≥3 **kapıdan elenecek** (`match_tier=page_inline`) ·
≥2 **mükerrer grubundan** · ≥1 **çapraz-DB mükerreri** · ≥1 `created_by` yetimi.

**Kapılar:** 50 → 4×50 · yetim **0** (A4 bekçisi) · JOIN'le geri okuma **birebir** ·
5/5 nokta-kontrol (metin + 5 şık + anahtar) · `ROLLBACK` sonrası `question_bank`=**36.967**.

### FAZ D — ADIM 3: kalıcı yazım, `pending`, 1000'lik parti

**Beklenen son sayı ÖNCEDEN ilan edilir** (`L-s229-maskenin-altinda-maske`):

```
3.666 KABUL
 − 78 set-ici mukerrer (siki normalizasyon, 73 grup)
 − 34 capraz-DB mukerrer (canlida metni zaten var; 20'si kapida)
 + ortusme duzeltmesi (78 ile 34 kesisebilir)
= 3.554 ± ~10   -> question_bank 36.967 -> ~40.521
```

Her parti sonrası: satır invaryantı · yetim 0 · damga sayımı · `git`/DB durumu.
`REFRESH` yapılmaz → **`mv_safe_for_beta` 27.073'te KALIR** (beklenen, kusur değil).

### FAZ E — Terfi kapısı (AYRI ONAY, postgres'e bağlı)

1. `REFRESH` yetkisi çözülür (postgres) · #428 celery görevinin bugüne kadar koşup koşmadığı ölçülür
2. `pending → auto_judged_high` (damgalı küme, tek UPDATE, geri alınabilir)
3. `REFRESH MATERIALIZED VIEW mv_safe_for_beta` → beklenen **27.073 → ~30.300**
   (3.554'ün ~%90'ı kapıyı geçer; 330/3.666 oranı elenir)
4. Y12 bekçisi koşulur · hacim bekçisinin `MIN_SATIR` eşiği **yeniden ölçülür**
5. ES yeniden index (#433) — yoksa arama eski kümeyi döndürür

### FAZ F — Kapanış

Ders defterine ~8 yeni ders (aşağıdaki adaylar) · cırcır `ZORLAYICI_TABANI` yükseltilir ·
handoff + MEMORY güncellenir · takipli-kirli **0** (`grep -v '^??'`).

**Ders adayları:** hash-UUID4 körlüğü · kapı `is_active` filtrelemez · CASCADE geri alma tuzağı ·
bayat yedek · SKIP eden bekçi "19 dosya" sayılır · xfail sırası · `udt_name` typmod körlüğü ·
sentezciye giden paketi kesmek (bu turdaki kendi hatam).

---

## 3. Tahmini ilerleme (varsayımsal)

Tahmindir, ölçüm değildir. Bu depoda ölçülen tempo: TDD+mutasyonlu bir kapı ≈ 1 oturum.

| Oturum | Faz | Çıktı | question_bank | mv_safe_for_beta | Güven |
|---|---|---|---|---|---|
| S233 | 0 + A1 + A2 | postgres kararı · taze yedek (147.894 doğrulanmış) · geri alma script+testi | 36.967 | 27.073 | yüksek |
| S234 | A3 + A4 | 2 bekçi canlıya · SKIP kapandı · parity assert'i var | 36.967 | 27.073 | yüksek |
| S235 | A5 + B1 + B2 | i6 ölçüldü · saf dönüşüm + 9 RED test | 36.967 | 27.073 | orta |
| S236 | B3 + C | mutasyon 9/9 · **pilot 50 satır yazıldı ve geri alındı** | 36.967 | 27.073 | orta |
| S237 | D | **3.554 satır kalıcı (`pending`)** · 4 parti · xfail ×4 kaldırıldı | **~40.521** | 27.073 | orta |
| S238 | E | terfi + `REFRESH` + ES | ~40.521 | **~30.300** | **düşük** (postgres'e bağlı) |
| S239 | F | defter + handoff + kapanış | ~40.521 | ~30.300 | yüksek |

**Toplam ≈ 7 oturum.** Kritik yol: FAZ 0 → A5 → B → C → D. FAZ E dallanabilir.

**Sonrasında (bu planın DIŞI, ayrı karar):**

| Ders | Kapı alt kümesi | Tam tablo | Tahmini token (3.956/yargı) |
|---|---|---|---|
| MATEMATIK | 14.119 | 65.341 | 55,9M / 258,5M |
| FIZIK | 3.468 | — | 13,7M |
| GEOMETRI | 2.948 | 31.140 | 11,7M / 123,2M |
| **Kapı düzeyi kalan** | **30.563** | — | **120,9M** |
| **Tüm korpus** | — | **187.835** | **743,1M** |

⚠️ Tam korpus göçü için **topic FK bir ön koşuldur, opsiyonel değil**: 187.835'in
**%94,07'si** (176.688) bugün FK ihlali verir; yalnız 11.147'si INSERT edilebilir.

---

## 4. Bu planın bilinçli kapsam dışı bıraktıkları

- Kalan sayısal dersler (kullanıcı kararı)
- `#485` kalan: **SINIF=45 koşulsuz çalışma-anı kırığı** (`question_repository.py` 16 · `exam_performance_service.py` 11) + `irt_daemon.py:195` KWARG=6 → her IRT kalibrasyon yazımı `CompileError`
- Y3 (28× GF HTTP 500 — **doğrulanmadı**, `latest.md:1291`'den alındı) · Y9 (seed: `seed_mvp_data.py` 4 rolü de üretiyor, sadece bu DB'ye koşulmamış — **ucuz**) · Y10 (mypy yapısal kör) · Y2-kalan
- **Y8 severity ÇÜRÜDÜ:** kapı `pyproject.toml:195` `select` listesinde **`PL` yok** → 202 `PLW0603` kalemi hiçbir commit'i bloklamıyor. **P1 değil P3.**

---

## 4b. YÜRÜTME KAYDI — FAZ 0 + A1 + A2 (19 Ağu 2026, KAPANDI)

### FAZ 0 → **Dal A**. Engelleyici ÇÜRÜDÜ.

S232-G'den beri taşınan *"`kiro2_app` CREATE TABLE yetkisiz, DDL için `postgres` lazım,
**parolası elimde yok**"* engelleyicisi **hiç ölçülmemiş bir varsayımmış**.

    C:/Program Files/PostgreSQL/18/data/pg_hba.conf:
      local   all  all                    trust
      host    all  all  127.0.0.1/32      trust
      host    all  all  172.17.0.0/16     trust     <- docker
      host    all  all  192.168.65.0/24   trust     <- LAN

**Parola gerekmiyor.** Kanıt: `psql -U postgres -d kiro2 -c "SELECT current_user, usesuper"`
→ `postgres|t` (EXIT=0). Kontrol kolu: aynı komut `kiro2_app` ile → `kiro2_app` (ayrım yapıyor).

→ **P0-4 · P0-7 · backup-tablo engeli KALKTI.** FAZ E artık planlanabilir.

⚠️ **Yan bulgu (kapsam dışı, P1 güvenlik):** `trust` yalnız localhost değil **docker ağı
(172.17/172.18) ve LAN (192.168.65.0/24)** için de açık → o ağlardaki herhangi bir host
parolasız `postgres` süper kullanıcısı olabilir. Ayrı açık iş.

### A1 — Taze yedek ALINDI ve DOĞRULANDI

    backups/kiro2_20260819_y11_adim2_oncesi.dump          6,63 MB
    backups/kiro2_20260819_y11_adim2_oncesi.prereq.sql    299 B   (gitignore'da!)

Dump **içi** sayıldı (dosyanın varlığı kanıt değil):

| tablo | YENİ dump | ESKİ dump (kontrol kolu) |
|---|---|---|
| question_bank | 36.967 | 36.967 |
| question_content | 36.967 | 36.967 |
| question_metadata | 36.967 | 36.967 |
| question_statistics | 36.967 | 36.967 |
| **topic_hierarchy** | **26** ✅ | **12** ❌ |
| **TOPLAM** | **147.894** | 147.880 |

→ **P0-4 bağımsız olarak doğrulandı**: eski dump gerçekten ADIM 1 öncesiydi.
Kontrol kolu (26 ≠ 12) sayım aletinin ayırt ettiğini kanıtlıyor.

### A2 — Restore GERÇEKTEN denendi → **YENİ P0 bulundu**

Atılabilir `kiro2_restore_probe` DB'sine gerçek `pg_restore`. İlk deneme **düştü**:

    pg_restore: hata: ERROR: type "public.questiondifficultylevel" does not exist
    -> question_statistics TABLOSU HIC OLUSMADI -> 36.967 satir HIC YUKLENMEDI
    (4/5 tablo yuklendi, biri tamamen kayip)

**P0-9 — `pg_dump -t <tablo>` yedeği KENDİ KENDİNE YETERLİ DEĞİLDİR.**
`-t` ile alınan dump **enum tiplerini ve uzantı tiplerini taşımaz**. S232-G'nin
"147.880 satır doğrulandı" ölçümü dump'ın **içeriğini** kanıtlıyordu,
**geri yüklenebilirliğini değil** — ve o dump da aynı kusuru taşıyor.
(`L-s202-drop-table-enum-birakir`'ın yedek ayağı.)

İkinci katman: tip eklenince `public.vector` çıktı (`L-s202-katmanli-hata-sistemik-tara` —
tek tek keşif kaybeden strateji). **Sistemik tarandı**, bağımlılıkların tamamı **iki tane**:

    questiondifficultylevel | e | (kullanici enum)
    vector                  | b | vector uzantisi

### 🔁 KURTARMA RUNBOOK (prereq.sql gitignore'da — içeriği burada)

```sql
-- backups/kiro2_<tarih>_y11_adim2_oncesi.prereq.sql  (pg_catalog'dan URETILDI, elle yazilmadi)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TYPE public.questiondifficultylevel AS ENUM ('VERY_EASY','EASY','MEDIUM','HARD','VERY_HARD');
```

```bash
BIN="C:/Program Files/PostgreSQL/18/bin"
# 1) ONKOSULLAR (hedef DB'de tipler yoksa)
"$BIN/psql.exe" -h localhost -p 5434 -U postgres -d <HEDEF> -v ON_ERROR_STOP=1 -f backups/<...>.prereq.sql
# 2) VERI
"$BIN/pg_restore.exe" -h localhost -p 5434 -U postgres -d <HEDEF> --no-owner --no-privileges backups/<...>.dump
# 3) KAPI — satir sayilari 147.894 olmali
```

**Prova sonucu (ölçüldü):** `TOPLAM 147.894` · 5/5 tablo · `question_statistics` **36.967**.
Kalan tek hata sınıfı `relation "public.users" does not exist` — kapsam dışı tabloya FK;
gerçek kurtarma hedefi `kiro2`'de `users` var, veri yüklemesini etkilemedi.

**Temizlik:** `kiro2_restore_probe` **DROP edildi** (kontrol kolu: `kiro2`/`kiro2_temp`/`kiro2_test` duruyor).
**Canlı dokunulmadı:** `question_bank 36.967` · `mv_safe_for_beta 27.073` · `topic_hierarchy 26`.

### Bu turda çürüyen iki devir iddiası

| Devir iddiası | Ölçüm |
|---|---|
| "`postgres` parolası elimde yok → DDL bloke" (S232-G/H) | `pg_hba.conf` **trust** — parola gerekmiyor |
| "Yedek doğrulandı (147.880 satır)" (S232-G) | Doğru ama **eksik**: dump geri yüklenemiyordu (P0-9) |

---

## 5. Ölçülmemiş, bu planın varsaydığı şeyler (dürüst sınır)

1. **Hiçbir satır INSERT denenmedi.** "3.666 göç edilebilir" bir **kısıt analizinden çıkarımdır**, çalıştırılmış ölçüm değil. FAZ C bunu ilk kez sınayacak.
2. **%83 KABUL oranı yargı kalitesini yansıtıyor** — TSV iç tutarlılığı ölçüldü, **yargının doğruluğu ölçülmedi**.
3. **i6'nın `pending` ile 0'da kalacağı** — çıkarım, FAZ A5'te ölçülecek.
4. ~~**Dump'ın gerçekten restore edilebilirliği**~~ → ✅ **ÖLÇÜLDÜ (4b)**: denendi, **düştü**, kök neden bulundu (P0-9), önkoşul dosyası üretildi, ikinci prova **147.894/147.894** ile geçti.
5. **kiro2_temp'in 4 trigger'ı** (`trg_update_qb_stats` vb.) canlıda yok → göçle gelen istatistik alanları **donuk** kalır; kimse fark etmez.
6. **`irt_based_difficulty` / `bloom_category` varchar sürüklemesi** (medium/MEDIUM/kolay/orta; 17 farklı bloom) — DB reddetmez, uygulama kırılabilir. Karar: normalize et **veya** bilinerek ertelendiğini kayda geç.
