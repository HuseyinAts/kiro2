## Session Handoff — 2026-08-01 (S200 · doğrulama + P0 kapatma)

**Branch:** feature/self-evolution-optimization
**Son commit:** `3773b3d42` (push edildi, origin senkron)

### ⚠️ ÖNCE BUNU OKU

**`docs/audits/2026-07-31_eksiklik_durum_dogrulamasi.md`** — 30-31 Tem denetiminin
113 bulgusunun + 29 Tem'in 12 kaleminin doğrulanmış durum tablosu ve kontrol listesi.
**Kalemler kapanana kadar tek referans.** §0.5 ilerleme kaydı, §3.0 görev eşlemesi
(#460-#471), §5 fantom listesi (uğraşma), §4 kapananlar (yeniden açma).

### Bu oturumda kapananlar

| Görev | Sonuç | Commit |
|---|---|---|
| **#460** canlı ölçüm turu | 5/6 komut koşuldu; sonuçlar belgede §3.2-SONUÇ | — |
| **#463** hızlı kazanç (9 kalem + Y6) | doküman sayıları canlı ölçümle senkron | `962f7d4c9` |
| **#461** K1 `user_item_fsrs` **P0** | tablo restore + GRANT + sınıf bekçisi | `3773b3d42` |

Ölçümle kapanan bulgular: **B1-canlı** (ES alias 25.127, `correct_answer`=0),
**DEPLOY** + **B6-be** + **#447** (imaj taze, `/api/v1/me`→401).

**Açık P0: 7 → 4** — `B4`+`B4-x` (#462), `B5` (#464), `F1` (#465), `B2/#441` (operatör).

### Fail Eden Testler

- YOK. Koşulanlar: `test_fsrs_schema_contract.py` 5/5,
  `tests/performance/` 20 test temiz toplanıyor.
- TAM backend paketi HÂLÂ KOŞULAMIYOR (önceden var, T1): `pytest_asyncio` teardown deadlock.

### Engelleyiciler

- SMTP 6/6 env UNSET — canlı ölçüldü (#441, operatör)
- `gh` CLI yok → CI koşum durumu doğrulanamıyor (#390/#436, operatör)

### Sonraki Adımlar (maks 5)

1. **#462** Golden Flow merge kapısı (P0): `test_golden_flows.py:88-97` 429'u
   `pytest.skip`'e çeviriyor; `golden-flows.yml:196` seed hatasını `|| echo` ile yutuyor.
2. **#464** B5/RLS (P0): GUC 163 router'ın 2'sinde. `organizations`=1 ölçüldü →
   bugün sızıntı imkânsız, ama ikinci kiracıda 79 tablo birden açılır.
3. **#465** Admin uçları (P0/P1): `F1` okuma-yazma testi + `YENI-1` PUT hâlâ 500.
4. **#467-Y3** ES admin reindex ucu: canlı alias'a `correct_answer` yazıyor,
   bugün onu kapatan tek şey bir kwarg hatası (`mapping=` vs `mappings=`).
5. ES yedek indeksi (`turkiye_sinav_platform_yedek_20260731`, 64.270 dok, hepsi
   cevap anahtarlı) — sızıntı riski YOK ölçüldü, ama retention da yok → silinebilir.

### Kararlar (gelecek session tekrar tartışmasın)

- **`alembic/env.py` exclude listesine `user_item_fsrs` EKLENMEDİ.** `include_object()`
  doğrudan çağrılarak ölçüldü: `env.py:117-118` yapısal kapısı zaten koruyor
  (kontrol kolları: `question_bank`→DAHİL, yeni tablo→DAHİL). +0 değer → #451 gereği yapılmadı.
- **İki paralel FSRS implementasyonu var** (`user_item_fsrs` vs `fsrs_cards`). Restore
  ikisini de çalışır yaptı, **kanonik seçimi yapılmadı** — ürün kararı.
- **Kök `performance/` "kayıp" DEĞİL** — takipli. `git check-ignore` takipli dosyayı
  raporlamaz; ilk alarmım bu yüzden yanlıştı. Gerçek kayıp 3 dosyaydı, geri alındı.
- **Fantom listesi (§5) 8 kalem — uğraşılmaz.** Özellikle `#458a-2` (kasıtlı fixture)
  ve `#447-schema` (`backend/schemas/persona.py` hiç olmadı).
- `test_elk_performance.py`'deki `"secret_password"` **kasıtlı fixture** —
  `censor_sensitive_data`'nın sansürleyeceği veri. Silinmedi, işaretlendi.
- Git Bash'te `git grep` deseni `/` içerirse MSYS'e takılıp **var olan metne 0 isabet**
  döner. Kontrol kolu koymadan olumsuz bulgu raporlama.
