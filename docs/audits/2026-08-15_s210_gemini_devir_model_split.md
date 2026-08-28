# S210 — Gemini turunun devralınması + `question_bank` model split (P0-B kapandı)

**Tarih:** 14-15 Ağustos 2026
**Branch:** `feature/self-evolution-optimization`
**Commit'ler:** `dbf06794c` → `99cda20a4` → `0fd9b8413`
**Önceki durum:** `015e11123` (S209 handoff, P0-B açık)

---

## 0. Bağlam

Kullanıcı bu aralıkta Gemini ile çalıştı ve uyardı: *"çok şey farklı gelebilir."*
Devralma bir denetimle başladı; çıkan tablo, ilk görünenden üç kat daha iyi huyluydu.

---

## 1. Gemini turunun gerçek şekli (ölçüm)

`git status`: **3522 kirli dosya**. Ölçünce üç ayrı şeye ayrıldı:

| Görünen | Gerçek | Nasıl ölçüldü |
|---|---|---|
| 2020 dosya değişmiş (`M`) | **1345'i yalnız CRLF** — içerik farkı yok | `git diff --name-only` vs `--ignore-cr-at-eol` farkı |
| 142 `.py` silinmiş | **75'i taşınmış** (birebir), 7'si taşınmış+düzenlenmiş, 60'ı gerçek silme | basename eşleşmesi + satır-sonu normalize edilmiş içerik karşılaştırması |
| 334 frontend dosyası silinmiş | **120'si yük taşıyordu**, 219'u ölü kod | iki derleyicinin sabit-nokta döngüsü (aşağıda) |

**`script_mezarligi/`**: Gemini `backend/` kökündeki tek-kullanımlık script'leri
(`demo_*.py`, `analyze_cov*.py`, `insert_345_*.py`) buraya taşımış. Git bunu
`D` + `??` çifti olarak gösteriyor. → **`git status`'ta `D` görmek "silinmiş"
demek değil.**

Gerçekten silinen 60 `.py`'nin **hiçbiri import edilmiyor** (`backend/tasks/social_tasks.py`,
`backend/utils/zemberek_integration.py` dahil — ikisi de ölü).

---

## 2. Frontend kurtarma (`dbf06794c`)

**Bulgu:** `package.json`, `index.html`, `vite.config.ts`, `tailwind.config.js`,
`package-lock.json` diskte **yoktu**. Frontend kaynağı build edilemez durumdaydı.
(`node_modules` duruyordu — 919 paket.)

**Yöntem:** derleyiciye sor, tahmin etme. Silinen dosyayı geri yüklemek hiçbir
commit'siz işi ezemez (diskte yok), bu yüzden güvenli.

```
tsc döngüsü:   366 TS2307 → 78 restore → 21 → 17 → 9 → 4 → sabit nokta
vite döngüsü:  5 CSS daha (styles.css, tokens.css, accessibility.css,
               touch-optimized.css, DyscalculiaSupportPage.css)
ambient:       vite-env.d.ts — tek başına 19 hata (ImportMeta.env)
```

**Sonuç:** 120 dosya geri yüklendi (HEAD ile birebir → git diff üretmez).
Kalan **219 silinmiş dosyayı iki derleyici de istemedi** = ölü kod, silinmiş kalıyor.

**Ölçüm:** `tsc --noEmit` 17 → **0** hata · `npm run build` **exit 0** · `dist/` (128 precache).

### Sınav UI'ı → backend sözleşmesi

Gemini **iki ayrı sınav API'si** bırakmış: yeni `api/v1/exams.py` ve mevcut
`examService.ts` → `/api/v1/osym-exam/*`. Yeni UI yeniyi çağırıyordu, servis
katmanı yoktu.

`getExamSession` / `submitExam` **ad çatışması** vardı (aynı ad, farklı API,
farklı dönüş tipi). Karar: ayrı `mockExamService.ts` — `examService.ts`'e
**hiç dokunulmadı**, mevcut `/osym-exam` çağıranları etkilenmedi.

Ayrıca `DiagnosticTestInterface.tsx`'te 4 çağrı-yeri hatası (servis eksiği değil):
eksik `sessionId`, `navigateQuestion`→`navigateToQuestion` ×2, `ModernLoader text`→`message`.

---

## 3. Backend modüller (`99cda20a4`)

`leaderboard_service.py` `dict[str, any]` yazmış — builtin `any` fonksiyonunu tip
sanmış, **modül hiç import edilemiyordu** (`NameError: name 'Any' is not defined`).
+ `test_assembly.py` tekrar-giderme/`ClassVar`, `bionic_reading.py`.

---

## 4. P0-B: `question_bank` model split (`0fd9b8413`) — **KAPANDI**

### Teşhis

| | HEAD | Disk (commit'siz) | Canlı DB |
|---|---|---|---|
| `QuestionBankItem` | **84 kolon**, tek parça | **12 kolon** | **12 kolon** |
| Yan tablolar | yok | `QuestionContent`/`Metadata`/`Statistics` | `question_content`/`_metadata`/`_statistics` |

→ **HEAD modeli bu DB'ye karşı zaten çalışmıyordu.** Tam-varlık sorgusu
`column question_bank.question_text does not exist` verir. Split'i commit'lemek
regresyon değil, ORM'i dürüst yapmak.

### Göç hacmi — asıl karar noktası

**69 alan taşınmış, 0 kayıp.** (grep'le değil, HEAD ve disk AST'lerinin farkıyla.)

| Ölçüm | Değer |
|---|---|
| Toplam nokta-erişimi (üst sınır) | 2542 / 340 dosya |
| **Sınıf düzeyi** `QuestionBankItem.<alan>` (SQL ifadesi, gerçek kolon şart) | **108 / 17 dosya** |

Bu ayrım stratejiyi değiştirdi: **sert çekirdek 340 değil 17 dosya.** Strangler
uygulanabilir hale geldi.

### Uygulama

`models/question_bank.py::_install_compat_delegates()`:

- Alan listesi **elle tutulmuyor** — hedef sınıfların kolonlarından türetiliyor,
  split ilerledikçe kendini günceller.
- Örnek düzeyi **okuma + yazma** ilişkiye devreder; ilişkili kayıt yoksa okuma
  `None` (çökmez), yazma yol gösteren `AttributeError`.
- **Sınıf düzeyi erişim kasıtlı olarak açık hata verir.** Sessiz `None`, JOIN'e
  çevrilmesi gereken 108 yeri görünmez kılardı → borç ölçülemez olurdu.
- Kaynaklar arası tekrar **açık kümeyle** önleniyor: kurulmuş devredici sınıf
  düzeyinde hata fırlattığı için `hasattr()` onu göremez; tek başına `hasattr`
  guard'ı sessiz "son kazanır" bırakırdı (71 alanda çakışma yok — ölçüldü).

`should_update_difficulty` artık `.statistics` üzerinden okuyor (dolaylı
devrediciye güvenmiyor).

### `api/v1/exams.py` — aynı commit'te indi

Şema göçü: `zorluk` → `QuestionStatistics.difficulty_level` (LEFT JOIN, DB enum'ı
İngilizce ↔ assembler Türkçe eşlemesi), `content` bir **ilişki** →
`content.question_text`, options `option_a..e`'den, `correct_answer` yoksa soru
**boş** sayılır (yanlış değil — veri eksiği öğrencinin hatası değil).

Yol boyunca **3 gizli kusur**:

1. `avg_time` yalnız `if` gövdesinde atanıp dışarıda koşulsuz okunuyordu →
   `time_spent_seconds=0` (varsayılan) + ≥%80 skorda **UnboundLocalError → 500**
2. `SubjectArea["MAT"]` **KeyError** (enum üyeleri Türkçe: `MATEMATIK`) — üstelik
   `except KeyError: SubjectArea.MAT` fallback'i de var olmayan üyeye bakıyordu →
   her yanlış soruda 500
3. `and_(..., True)` çıplak Python bool → `true()`

Ayrıca prefix `/exams` → `/api/v1/exams`: nginx yalnız `/api/*` proxy'liyor,
önceki hâli **üretimde 404** olurdu.

---

## 5. Doğrulama zinciri

| Kapı | Sonuç |
|---|---|
| pytest (compat + exams + bionic + assembly) | **27/27 PASS** |
| pre-commit (ruff + mypy + bandit + import smoke 154 modül) | **0 failed hook** |
| Uygulama açılışı | **1224 yol**, `/api/v1/exams/*` ×4 |
| frontend | `tsc` 0 hata, `npm run build` exit 0 |
| **Mutasyon** | **4/4 öldürdü** |

Mutasyonlar (hepsi `failed`, `error` değil — geçerli):
- **M1** `_BRANCH_RANGES` ilk aralığı boz → 2 test
- **M2** `content.question_text` → yok olan alan → 1 test
- **M3** compat sınıf-düzeyi korumasını kaldır (sessiz `None`) → 4 test
- **M4** compat setter'ı etkisizleştir → 1 test

---

## 6. Bu turda öğrenilen alet dersleri

Defterde: `L-alet-tip-vs-paketleyici`, `L-alet-mypy-bailout`,
`L-alet-mypy-anotasyonsuz-kor`, `L-alet-read-son-satir`, `L-alet-crlf-pathspec`,
`L-alet-hasattr-descriptor`, `L-olcum-tasima-silme-degil`, `L-olcum-sert-cekirdek`,
`L-sema-shim-sessiz-none-yasak` (`.claude/lessons/ders_kaydi.yaml`, 9 satır, hepsi `aktif`).
Prose: `.claude/rules/audit-methodology.md` — "Grafiği, sorduğun derleyici kadar
görürsün" + "Uyumluluk katmanı yardım edemediği yerde sessiz kalmamalı" + tabloya 4 satır.

En pahalıları:

1. **Tip grafiği ≠ paketleyici grafiği.** `tsc` "0 eksik modül" dedikten sonra
   `vite` 5 CSS daha istedi; en pahalı bulgu (19 hata) hiçbir import grafiğinde
   görünmeyen `vite-env.d.ts`'ti. "Eksik dosya" sorusu **her derleyiciye ayrı** sorulur.
2. **mypy iki ayrı sebeple 0 verir.** (a) `errors prevented further checking` ile
   bail-out (numpy stub) — 1363 satırlık koşum bunu ortaya çıkardı; (b) anotasyonsuz
   kodda `Any` → hiçbir attr kontrolü yok. Pozitif kontrol olmadan mypy'ın 0'ı
   ölçüm değildir.
3. **Göçün boyutu toplam kullanım değil, karşılanamayan alt küme.** 2542/340
   "repo-geneli göç" dedirtiyordu; 108/17 ayrımı işi çözülebilir kıldı.

---

## 7. Açık kalanlar

| # | İş | Not |
|---|---|---|
| **#485** | 108 sınıf-düzeyi sorguyu JOIN'e çevir (17 dosya) | Bloke etmiyor, açık hata veriyor. En yoğun: `question_crud_service.py` (42), `question_bank_service.py` (13), `duel_api.py` (12), `curator.py` (10), `productive_failure_service.py` (9) |
| **#444** | Öğretmen Öğrenciler sayfası UI | roster backend hazır |
| — | `core/rag_service.py:682` `search_with_mmr` O(k²) embed | S207'den devir |
| — | Kirli ağaç ~3280 dosya | Gemini'nin kasıtlı commit'siz işi; ayrı triyaj |

**Ortam notu:** bu makine taze — `question_bank` **0 satır**, 246 tablo, DB 32 MB.
DB'ye dayanan her ölçümden önce satır sayısına bak.

**MEMORY.md düzeltmesi:** `DISABLED_ROUTERS` artık **boş**; 154 router yükleniyor.
Eski "110 router kapalı → 167 yol 404" tablosu bu ağaçta geçersiz.
