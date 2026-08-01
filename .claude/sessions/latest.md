## Session Handoff — 2026-08-01 (S200 · doğrulama + 7 görev kapatma)

**Branch:** feature/self-evolution-optimization
**Son commit:** `ef6bafe47` · origin ile **senkron** · çalışma ağacı **temiz**

---

## ⚠️ SONRAKI OTURUM BURADAN BAŞLAR

**`docs/audits/2026-07-31_eksiklik_durum_dogrulamasi.md`** — 30-31 Tem denetiminin
113 bulgusu + 29 Tem'in 12 kalemi, hepsi canlı kodda doğrulanmış durum tablosu.
**Bu belge, kalemler kapanana kadar TEK REFERANSTIR.**

**§3.0-SONRAKI** bölümünde sıra yazılı. Aç, ilk açık kalemi al, kapat,
kutucuğu işaretle + **ankraj yaz** (commit + `dosya:satır`). Ankrajsız kapanış yok.

**Durum: 21 kutucuk kapalı · 51 açık · Açık P0 = 2**

### Sıra

| # | Görev | Neden |
|---|---|---|
| **1** | **#467** ES `Y3` | `api/elasticsearch.py:353-491` **canlı alias'a `correct_answer` yazıyor**; onu bugün kapatan tek şey bir kwarg hatası (`mapping=` vs `mappings=`). Biri "düzeltirse" cevap anahtarı canlı indekse döner. + `Y1`/`Y2`/`Y4`/`YENI-10` |
| **2** | **#468** CI tetikleme | `F8-b`: kapı **aktif dalda hiç tetiklenmiyor** (`[main,master,develop]`, dal 318 commit önde). #462'de kapıyı gerçek yaptım ama koşmuyor → değeri sıfır. + `T1`/`T2`/`T3` |
| **3** | **#470** Sınav oturumu | `F17` üç katmanda yok + `F17b` **ölü bekçiyi 3 test yeşil doğruluyor** |
| **4** | **#469** Kiro yüzey | `K3` 70 yoldan ~43'ü backend'de yok · `K4.6` tek satırlık takas |
| **5** | **#471** P2/P3 hijyen | P0/P1 bitmeden geçme |

---

## Bu oturumda kapananlar (7 görev)

| Görev | Sonuç | Commit |
|---|---|---|
| **#460** canlı ölçüm turu | 5 komut, hepsi kontrol kollu | — |
| **#463** hızlı kazanç (9 kalem + Y6) | doküman sayıları canlı ölçümle senkron | `962f7d4c9` |
| **#461** K1 `user_item_fsrs` **P0** | tablo restore + GRANT + sınıf bekçisi (5/5) | `3773b3d42` |
| **#462** Golden Flow kapısı **P0** | 178 login→4, 429→FAIL, CI eşiği; 2 mutasyon çivili | `c5a4f2c98` |
| **#465** Admin uçları **P0** | **3.** bastırıcı bulundu; 5 bayat test (1 vakum) onarıldı | `b93cfcd3c`, `0d0dfd069` |
| **#464** RLS | 🟡 kapatılmadı, **ölçülebilir** yapıldı; tuzak dedektörü çivili | `64d6452be` |
| **#466** SMTP zinciri | F20+F21+F21-yeni; 3 mutasyon çivili | `4ddd74383`, `ef6bafe47` |

**Açık P0: 7 → 2** — `#441` SMTP (operatör) · `B5` RLS (mimari sprint)

---

## Fail Eden Testler

**YOK.** Bu oturumda koşulanlar: FSRS şema sözleşmesi 5/5 · GF login kapısı 6/6 ·
workflow YAML 12/12 · admin paketi 56/56 · RLS bekçisi 6/6 · SMTP zinciri 6/6 ·
email_util tüketicileri 23/23 · `tests/performance/` 20 test temiz toplanıyor.

**Önceden var, değişmedi:** TAM backend paketi koşamıyor (`pytest_asyncio` teardown
deadlock, `T1`). Bu #468'in kapsamında.

---

## Engelleyiciler

- **SMTP** 6/6 env UNSET (canlı ölçüldü). **Kod tarafında yapılacak şey KALMADI.**
  Operatör: `.env.mvp`'ye `SMTP_HOST`+`SMTP_USERNAME`+`SMTP_PASSWORD`+`EMAIL_FROM`,
  sonra `docker compose up -d --no-deps backend` (**restart YETMEZ**).
  Not: `.env.mvp.example`'da şablon **yok** ve CLAUDE.md `.env*`'ı salt-okunur
  ilan ettiği için **kod tarafından eklenemez** (`YENI-9`).
- `gh` CLI yok → CI koşum durumu doğrulanamıyor (#390/#436).

---

## Kararlar (gelecek oturum tekrar tartışmasın)

- **`alembic/env.py` exclude listesine `user_item_fsrs` EKLENMEDİ.** `include_object()`
  doğrudan çağrılarak ölçüldü: `env.py:117-118` yapısal kapısı zaten koruyor
  (kontrol kolları: `question_bank`→DAHİL, yeni tablo→DAHİL). +0 değer → #451 gereği.
- **`@admin_required` dekoratörü DÜZELTİLMEDİ.** 17 metot korumalı ama üretimden
  çağrılan **tek** metot vardı (düzeltildi); kalan 16 ölü kod → +0 değer.
- **İki paralel FSRS implementasyonu var** (`user_item_fsrs` vs `fsrs_cards`).
  Restore ikisini de çalışır yaptı; **kanonik seçimi ürün kararı**, yapılmadı.
- **RLS politikaları fail-closed YAPILMADI.** 163 router'ı ilgilendiren mimari iş.
  Bunun yerine tuzak dedektörü kondu: 2. org eklendiği an CI kırmızıya döner.
- **`soru_bankasi_servisi.soru_guncelle` DEĞİŞTİRİLMEDİ** (`YENI-8`): "bulunamadı"
  ve "istisna" için aynı `None`'ı dönüyor, ama ikinci üretim çağıranı var
  (`api/soru_bankasi.py:845`) — cerrahi müdahale kuralı.
- **Fantom listesi (§5) 8 kalem — uğraşılmaz.** Özellikle `#458a-2` (kasıtlı fixture)
  ve `#447-schema` (`backend/schemas/persona.py` hiç olmadı).

---

## Bu oturumun ALET DERSLERİ (tekrarlanmasın)

1. **`cd` kalıcı → geri alım sessizce başarısız oluyor.** 3 kez oldu.
   `git checkout HEAD -- <yol>` yanlış dizinden koşunca "pathspec did not match"
   verip **hiçbir şey yapmıyor**, ve `git status` da yanlış dizinden koşulunca
   "boş" görünüyor. **Her geri alımı repo kökünden ölç.**
2. **`git checkout -- X` YETMEZ** — index'ten geri yükler. `git add` yapıldıysa
   `git checkout HEAD -- X` gerekir.
3. **Biçimlendirici `# pragma`/`# noqa` yorumlarını satırdan kaydırıyor.**
   detect-secrets/ruff **satır bazlı** bakıyor. Pragma değerin kendi satırında olmalı.
4. **Biçimlendirici kullanılmayan import'u siliyor** (F401 autofix) → `NameError`.
   Kullanımı ÖNCE yaz, import'u SONRA.
5. **`pytest.fail`/`skip` `BaseException` türetir** — `pytest.raises(Exception)`
   onları yakalamaz; test kendisi "skipped" olur ve hiçbir şey ölçmez.
   `_pytest.outcomes.{Failed,Skipped}` kullan.
6. **detect-secrets sadece DEĞİŞEN dosyaları tarar.** Bir dosyaya dokununca
   tamamı denetime girer ve **önceden var olan** satırlar commit'i bloklar.
7. **`git check-ignore` TAKİPLİ dosyayı raporlamaz** — boş çıktı "ignore edilmiyor"
   demek değil, "zaten takipli" de olabilir. (Bu yüzden yanlış alarm verdim.)
8. **reward-hacking bekçisi boş gövdeli test double'ı reddediyor** (exit 2, push
   bloklanır). Susturma — gövde ver, kayıt tut; test de güçlenir.
9. Git Bash'te **`git grep` deseni `/` içerirse** MSYS yol dönüşümüne takılıp
   var olan metne **0 isabet** döner. Kontrol kolu koymadan olumsuz bulgu raporlama.
10. **`.env*` salt-okunurdur** (CLAUDE.md). İzin sistemi haklı olarak bloklar.
