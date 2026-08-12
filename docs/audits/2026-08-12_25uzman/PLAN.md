# 25 Uzman Denetimi — İcra Planı

**Tarih:** 12 Ağustos 2026
**Metodoloji:** `docs/research/2026-08-12_claude_code_opus5_arastirma_raporu.md`
§C.2.8 (Anthropic kod-migrasyon 6 adımı) + §C.1.13 (döngü mühendisliği) + §D.1/#13-16
**Kütük:** `iddialar.yaml` · **Bekçi:** `backend/tests/audit/test_iddia_kutugu.py`

---

## 0. Neden bu plan böyle

Kullanıcı 25 uzman bulgusu verdi ve "hepsini çöz" dedi. Naif cevap: 25 görevi
sırayla uygulamak. **Bu yanlış olurdu** ve nedeni ölçülmüştür:

| Kanıt | Kaynak |
|---|---|
| Bu depoda 18 P0'ın **%87'si fantom** çıktı | 23 May 2026 meta-denetimi |
| 6 "kritik" sorundan **4'ü fantom** | Session 121 |
| Raporlanan P0'ların **%30-70'i** fantom olabilir | `systematic-debugging.md` |
| **12 Ağu 2026:** raporun kendi §E'sinde **3 bulgu fantom/bayat** çıktı | bu oturum |

Son satır belirleyici: 25 iddiayı değerlendirmek için yazdığım raporun **kendi
bulguları** ölçülünce çöktü (E2 kısmen fantom, E12 fantom, E14 bayat). Aynı
disiplinsizlikle 25 iddiaya girmek, aynı sonucu 25 kat büyütürdü.

**Bu yüzden sıra şudur:** önce **kural ve kuyruk**, sonra ölçüm, en son uygulama.
§C.2.8'in birinci cümlesi: *"Rulebook önce gelir."*

---

## 1. FAZ 0 — Ölçüm makinesi ✅ **UYGULANDI (12 Ağu 2026)**

§C.2.8 Adım 1-2. Bu fazın çıktısı kod düzeltmesi değil, **düzeltmeyi güvenilir
kılan alet**.

| # | Artefakt | Ne yapar | Durum |
|---|---|---|---|
| 0.1 | `iddialar.yaml` | 25 iddia + 6 ölçülmüş ek → **mekanik, devam ettirilebilir kuyruk**. "Bitti" = diskteki alan dolu | ✅ |
| 0.2 | `.claude/agents/iddia-dogrulayici.md` | Adversarial **çürütücü** (sonnet, salt-okunur). Doğrulamaya değil çürütmeye programlı | ✅ |
| 0.3 | `.claude/agents/kanit-hakemi.md` | İki çürütücü anlaşamazsa **3. hakem** (opus) | ✅ |
| 0.4 | `.claude/skills/iddia-dogrula/SKILL.md` | `context: fork` — tek iddia doğrular, **ana bağlamı kirletmez** | ✅ |
| 0.5 | `.claude/workflows/iddia-dogrulama.js` | `pipeline()` bariyersiz: çürüt-A → çürüt-B → (anlaşmazlıkta) hakem → sentez | ✅ |
| 0.6 | `backend/tests/audit/test_iddia_kutugu.py` | **Bekçi**: kanıtsız durum değişikliği merge edilemez. 10/10 geçiyor | ✅ |
| 0.7 | `scripts/mutate_iddia_kutugu.py` | Bekçiyi **mutasyonla çivileme** — 6/6 mutasyon FAIL ürettiriyor | ✅ |

**Tasarım kararlarının kaynağı:**
- İki bağımsız çürütücü + 3. hakem → §C.2.8 *"adversarial review, ayrı bağlamlar"*
- Çürütücü sonnet, hakem opus → §D.1/#15 *"küçük model uygular, büyük model hakemlik eder"*
- Stakes dili **sabit ve testle çivili** → §C.6.1 (aynı transkript, yalnız sonuç dili değişince **%85,6 ↔ %16,7**)
- `pipeline()` (bariyer değil) → §D.1/#7
- Bekçi testi → §D.1/#4 *"CLAUDE.md tavsiyedir; test zorlamadır"*

### FAZ 0'da ortaya çıkan iki alet arızası (kayda geçti)

1. **Binary string grep ile ayar anahtarı ölçümü GEÇERSİZ.** `excludePatterns=0`
   çıktı ama **belgelenmiş** `advisorModel` de `0` çıktı → kontrol kolu tutmadı.
   Karar: **silme yok** (X05 `beklemede`). Rapor §D.1/#16.
2. **Mutasyon ilk turda `error` verdi, `failed` değil.** Sebep: `backend/pytest.ini`
   `addopts` içinde `-n --dist=loadscope` var; xdist kapatılınca usage-error.
   Düzeltildi → 6/6 `failed`. 1 Ağu 2026 dersinin birebir tekrarı.

---

## 2. FAZ 1 — Zorlayıcı katman ✅ **UYGULANDI**

Rapor §D.2: *"CLAUDE.md'ye yasak yaz, engellenir"* → **çürütüldü**. Zorlama
`permissions.deny` + hook + sandbox ister.

| # | Değişiklik | Ölçüm | Durum |
|---|---|---|---|
| 1.1 | `.claude/settings.json` → 13 adet `Read(...)` deny | Ripgrep/tarama kuralı artık **tavsiye değil, kural** | ✅ |
| 1.2 | `model: claude-sonnet-4-6` → `claude-sonnet-5` | Bayat ID; yeni model 1M bağlam + **$2/$10 vs $3/$15** | ✅ |
| 1.3 | 5 rule dosyasına `paths:` | Kapsamsız yük **2.045 → 584 satır (−%71)** | ✅ |
| 1.4 | Çift frontmatter onarımı (`scripts/fix_rule_frontmatter.py`) | 3 dosyada `paths:` gövdeye düşmüştü → **sessiz no-op**, düzeltildi | ✅ |

**Kapsamsız bırakılanlar — bilinçli karar:** `debugging-first.md` (26),
`plan-before-execute.md` (23), `verification.md` (247), `audit-methodology.md` (288).
Bunlar **konuşma-seviyesi kapılardır**; `paths:` verilirse ancak bir dosya
okunduktan sonra yüklenirler — yani kapı, kapatması gereken andan **sonra** açılır.

---

## 3. FAZ 2 — 25 iddianın ölçümü 🔄 **SÜRÜYOR (2/26 bitti)**

**Koşturma:** Claude'a `use a workflow: iddia-dogrulama` de.
Alt küme: `args: {ids: ["U04","U13"]}`.

**Beklenen çıktı:** her iddia için `dogrulandi | fantom | abartili | olculemedi`
+ kanıt + `severity_olculen` + `fix_degeri`.

**Kapı:** Fantom oranı raporlanacak. Bu depoda tarihsel bant **%30-70**. Oran
%10'un altındaysa **çürütücüler yeterince agresif değil** demektir — prompt
kalibre edilir, tur tekrarlanır (§C.1.5 *"evaluator ayarlaması gerekir"*).

### 3.0 Tur 1 sonucu ✅ (12 Ağu, `wf_afc7dcf4-cf3`, commit `ff592f15f`)

4 ajan · 0 hata · **fantom oranı %50** → bant içinde, kalibrasyon **sağlıklı**.
İki çürütücü ikisinde de mutabık → hakem gerekmedi.

| ID | Yargı | Ölçülen | Belirleyici kanıt |
|---|---|---|---|
| **U04** | 🔴 `dogrulandi` | **P0** | **Canlı tetiklendi.** Gerçek `qwen3:8b` + gerçek system prompt, 3 turlu diyalog: T2 → `"C) 4"`, T3 → `"C"`. İddia *"ısrar edince"* diyordu; **tek ısrar yetti** |
| **U13** | ⚪ `fantom` | **yok** | **Atlatma denendi.** 4 admin ucu token'sız + geçersiz token → hepsi **401**. Kontrol kolu `/health` → 200. 17/17 uç aynı kapı altında; `test_admin_api.py` 46 passed |

**Kalibrasyonun asıl kanıtı U13'tür:** çürütücü bir P0'ı gerçekten çürüttü, yani
onaylamaya değil çürütmeye çalıştığı **ölçüldü**. Dört çürütme yolunun dördü de
her iki iddiada sonuçlu raporlandı.

**U04'ün kök nedeni tek değil, üç katmanlı ve seri bağlı:**
1. Guardrail **yalnız system prompt**'ta (`enhanced_chat.py:213-231`) — çıktı-tarafı zorlama yok
2. Frontend'in çağırdığı gerçek uç `/enhanced-chat/stream` guardrail servisini **hiç çağırmıyor**
3. `direct_answer_detected` hesaplanıyor ama **mesajı değiştirmiyor** (sadece metadata)

Bu, `audit-methodology.md`'nin *"seri bağlı filtre bu depoda gerçek bir desen"*
uyarısının bir örneği daha: yalnız (1)'i düzeltmek yetmez.

**Turda kendi ön bulgum çürütüldü:** U04 için *"ASLA metni yok"* demiştim; metin
**var**, başka dosyada. Kusur metnin yokluğu değil **tek katman olması**. Ön bulgu
bir hipotezdir — kütükte `on_bulgu` alanı bu yüzden `kanit`'ten ayrı tutuluyor.

### 3.0.1 Turdan çıkan iki yeni kalem

U04'ün doğrulaması **ayrılabilir** iki kusur ortaya çıkardı. Ayrı kalem açıldı,
çünkü U04 `uygulandi` işaretlenince bunlar kaybolurdu:

| ID | Kusur | Neden ayrı |
|---|---|---|
| **X07** | `SocraticGuard` `guard_mapping`'e kayıtlı değil, çağıran yok → **ölü kod**. Kayıtlı olsa bile `WARNING`/`should_stop=False` | **Silinerek de kapanabilir** — U04'ten farklı bir karar |
| **X08** | Dedektör regex'i *"cevap/doğru"* kelimesine bağımlı: `'Cevap C'`→True ama `'C) 4'`→**False**, `'C'`→**False** | Kapanmazsa "düzeltilmiş" dedektör **gerçek** sızıntı biçimini yine kaçırır |

**X08'e fix yazarken:** tek harf `"C"` meşru metinde de geçer (*"C vitamini"*,
*"C dili"*). Türkçe bağlam guard'ı + bilinen-iyi kümede yanlış-pozitif ölçümü
**zorunlu** — `audit-methodology.md` "Ucuz Filtre Tuzağı" (3 ucuz filtre geçerli
Türkçe STEM'i çöpe attı).

### 3.0.2 X06 güncellendi

U13 fantom çıkınca, parçalı auth'un (5+ rol-kontrol implementasyonu) **admin
yüzeyinde zarar üretmediği** ölçüldü. Bulgu ayakta ama severity düşürülmeli.
Kalan ölçüm: diğer 5 implementasyonu **kim çağırıyor** ve o uçlar atlatılabiliyor mu.

### Ölçüm sırası (P0 → P1 → P2)

| Sıra | ID | Durum | Neden bu sırada |
|---|---|---|---|
| 1 | **U04** Sokratik guardrail | ✅ `dogrulandi` P0 | P0. Canlı tetiklendi |
| 2 | **U13** admin RBAC | ✅ `fantom` | P0. Atlatma denendi → 401 |
| 3 | **U25** migration reversibility | 🔄 tur 2 | P1 ama **en yüksek kaldıraç**: tek bug değil, bir **doğrulama döngüsü** (§D.1/#14). Diğer 24'ün regresyonunu da yakalar |
| 4 | **U18** frontend test durumu | 🔄 tur 2 | P1. MEMORY: "111 frontend testi kırık" — flakiness değil düz kırık olabilir. **FAZ 3'ün hakemi buna bağlı** |
| 5 | **U01** IRT cache invalidation | 🔄 tur 2 | P1. Bayat kalibrasyon öğrenciye servis ediliyorsa doğruluk kusuru |
| 6 | **U03** BKT `subject_area` NULL | 🔄 tur 2 | P1. Tek SQL ile kesin cevap; ucuz ve kesin |
| 7-9 | U07, U08, U14 | ⏳ tur 3 | P1 grubu |
| 10-25 | kalanlar | ⏳ | P2/P3 |

**Tur 2 (`wf_285d1d38-c12`):** U25, U18, U01, U03 — 8 ajan + en fazla 4 hakem.
Parti büyüklüğü 2'den 4'e çıkarıldı çünkü tur 1 kalibrasyonu sağlıklı çıktı.
Üst sınır: `medium` workflow kılavuzu (<15 ajan) → tur başına **maks 6 iddia**.

### Ön ölçümde şimdiden şüpheli olanlar (çürütücü buraya bakacak)

| ID | Şüphe |
|---|---|
| U07 | `REFRESH ... CONCURRENTLY` yazıcıyı **bloklamaz** — "lock contention" PostgreSQL semantiğiyle çelişiyor. Ayrıca #428 zaten zamanlama eklemiş |
| U10 | `position:fixed` tek başına re-render **tetiklemez** (CSS'tir). Profiler kanıtı yoksa yanlış teşhis |
| U17 | Proje **KaTeX** kullanıyor olabilir; MathJax hiç yoksa iddia fantom |
| U21 | Vektör arama **zaten 21ms** (hedef <100ms). %79 marj varken tuning'in **değeri** yok |
| U11 | #415 (a11y aria-label) **tamamlanmış** — iddia ondan önce mi ölçüldü |
| U14 | Vector clock **çok yazarlı** sistemler içindir; burada tek yazar var → idempotency key yeter (KISS) |
| U08 | Modernizasyon, kusur değil → P1 değil P3 |
| U24 | Faz 3 tasarım-portu **42/42 tamam**; yeni tasarım dili tamamlanmış portu bozabilir |

---

## 4. FAZ 3 — Uygulama ⏳ **FAZ 2'YE BAĞLI**

**Ön koşul:** FAZ 2 bitmeden **tek satır fix yazılmaz.**

### 3.1 Mekanik hakem önce onarılır

§C.2.8 Adım 6 *"davranışı doğrula"* **hakemin gerçekten hakemlik ettiğini** varsayar.
U18 ölçümü "111 frontend testi kırık" derse, 25 fix'i o hakeme karşı koşturmak
**sahte yeşile** karşı koşturmaktır. Sıra: hakem → fix.

### 3.2 Fix döngüsü (her doğrulanmış iddia için)

```
1. RED    — kusuru gösteren fail eden test yaz, FAIL ettiğini gör
2. FIX    — minimum değişiklik (§D.1/#6: en basit harness)
3. GREEN  — test PASS
4. MUTASYON — testi boz, FAIL ürettiğini doğrula (vakum test değil)
5. KÜTÜK  — durum=uygulandi + commit + zorlayici_test  (bekçi bunu ZORLAR)
```

Adım 5 atlanırsa `test_uygulandi_commit_ve_test_ister` **düşer** — merge edilemez.

### 3.3 Paralellik

- **Aynı dosyaya dokunanlar seri** (§C.2.12: "aynı dosyaya çoklu düzenleme → çakışma")
- **Farklı dosyaya dokunanlar** `isolation: worktree` subagent ile paralel
- Frontend (U05, U09, U10, U11, U12, U16, U17, U19, U20, U22, U24) ile
  backend (U01, U03, U06, U07, U08, U14, U15, U21, U25) **birbirinden bağımsız** → iki koldan

### 3.4 Desen görülürse dosyayı değil kuralı düzelt

§D.1/#13. Örnek: U13 (admin RBAC) tek tek router yamalanarak çözülmez —
**X06** (5+ parçalı auth implementasyonu) çözülür. Fixer ajan tek tek bug'ları
halleder; kararı veren kişi **sistemik desene** bakar.

---

## 5. Ölçülen durum tablosu (12 Ağu 2026)

| Ölçüm | Önce | Sonra |
|---|---:|---:|
| Kapsamsız rule yükü | 2.045 satır | **584 satır** |
| `Read()` deny kuralı | 0 | **13** |
| Ayar `model` | `claude-sonnet-4-6` (bayat) | `claude-sonnet-5` |
| İddia kütüğü | yok | **31 kayıt** (25 panel + 6 ölçülmüş) |
| Kütük bekçisi | yok | **10 test, 6/6 mutasyonla çivili** |
| Adversarial doğrulama makinesi | yok | 2 subagent + 1 skill + 1 workflow |
| `CLAUDE.md` | 883 satır | 883 (**FAZ 4**) |
| **Ölçülen iddia** | 0/26 | **2/26** (tur 2'de +4) |
| **Ölçülen fantom oranı** | — | **%50** (bant %30-70 ✓) |
| **Canlı tetiklenmiş P0** | — | **1** (U04) |
| **Sıfır-değerli görev elendi** | — | **1** (U13, fix değeri 0) |

---

## 6. FAZ 4 — Kalan bağlam borcu ⏳

| # | İş | Neden ertelendi |
|---|---|---|
| 4.1 | `CLAUDE.md` 883 → ~200 satır | Yüksek riskli; kullanıcının çekirdek talimatları. FAZ 2 ölçümü hangi kuralların **gerçekten** kullanıldığını gösterecek — ondan sonra kes |
| 4.2 | X05: `excludePatterns`/`contextManagement` ölü mü | Alet arızası (§1). Doğru alet: canlı `claude doctor` |
| 4.3 | `verification.md` + `audit-methodology.md` (535 satır) sadeleştirme | Kapsamsız kalmaları **zorunlu**; küçültmek tek yol |
| 4.4 | `worktree.sparsePaths` | 15GB depo için değerli ama yanlış yol listesi worktree'yi bozar → FAZ 3.3'te gerçek worktree kullanımıyla birlikte |
| 4.5 | LSP plugin (`pyright-lsp`, `typescript-lsp`) | Rapor §E8. Binary kurulumu operatör işi |

---

## 7. Bu planın kendi çürütme sorusu

> **"Bu makine kurulmasaydı ne olurdu?"**

25 iddia doğrudan uygulanırdı. Tarihsel orana göre **7-17'si fantom** olurdu ve
her biri bir sprint yerdi. Ayrıca U07/U10/U21 gibi teknik olarak tutarsız veya
değeri ölçülmemiş işler yapılırdı.

> **"Peki makine yanlışsa?"**

O da ölçülür: FAZ 2 fantom oranı **%10'un altında** çıkarsa çürütücüler kör
demektir; **%70'in üstünde** çıkarsa çürütücüler aşırı agresif. İki durumda da
prompt kalibre edilir — makine de bir hipotezdir.

---

*Kaynak metodoloji: `docs/research/2026-08-12_claude_code_opus5_arastirma_raporu.md`
(1.792 satır, 12 Ağu 2026). Bu plandaki her sayı ölçülmüştür; ölçülemeyen her
şey `beklemede` işaretlidir.*
