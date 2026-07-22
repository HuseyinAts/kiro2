# KIRO2 — Faz 3 · SPRINT9-A Roller (Grup 7 · A: 4 panel) — RAPOR

**Tarih:** 2026-07-23
**Branch:** feature/self-evolution-optimization (push YOK)
**Kapsam:** Grup 7 Roller'ın hafif 4 paneli → `frontend/src/kiro/`. Veli Bağlama (KVKK) + Ödev Atama **ayrı tur** (kullanıcı "ağırları ayır").
**Sonuç:** 4/4 ✅. İlerleme **29/42 ekran + 1 composite (QuestionCard) + `ui/WeeklyActivityBars`**.

---

## Ekranlar (hepsi PAPER)

| Ekran | Rota | Rol/dil | Not |
|---|---|---|---|
| Veli Paneli | `/veli` | veli **SİZ** | çocuk **salt-okur** (sohbet/AI/mood gizli); ChildSwitcher tablist; Premium ROI (Grup 8 link ertelendi) |
| Öğretmen Paneli | `/ogretmen` | öğretmen **SİZ** | sınıf/roster `<table>`; risk=amber; dikkat-kartları |
| Öğrenci Özeti | `/ogretmen/ogrenci/:id` | öğretmen, **salt-okur** | tek yazma = "ödev ata" link |
| Sınıf Kurulumu | `/ogretmen/sinif/yeni` | öğretmen | 3-adım sihirbaz + katılım kodu (mock); **DC SEN korundu** (DC>spec) |

**Paylaşımlı:** `ui/WeeklyActivityBars` (Veli+Öğretmen+ÖğrenciÖzeti) — `transform:scaleY` (layout-anim değil), RM-guard, per-bar görünmez SR metni.

---

## Backend gerçeği (Grup 7)

- **`/api/v1/teacher`** (teacher_classroom) — classes/students/reports/assignments **MEVCUT** (DB-backed).
- **`/api/v1/parent`** (parent.py) — children + **email-tabanlı iki-taraf onay** + performance/weekly-report/dashboard **MEVCUT** (Pydantic).
- **YOK → mock:** katılım-kodu üret/rotate + öğrenci-katıl; öğrenci "Ödevlerim" GET + teslim; zengin-atama alanları (konu/adet/öğrenci-seç).
- **Karar (kullanıcı):** Veli Bağlama → **DC 6-haneli kod-akışı + mock** (IDOR-güvenli; gerçek /parent email-onay Faz 4).
- Kanon-net: TR/EN router canonical = `/teacher` + `/parent` (EN tekil, `/teachers` marketplace ≠); infra live-map best-effort snake→camel.

Faz 3 kuralı: ekranlar **mock server-sim api-client**; sunucu-otorite (net/hâkimiyet/risk/theta) mock'ta bile izole (kiro-data'dan okunur, ekranda hesaplanmaz).

---

## Süreç (pipeline)

keşif (7 ajan: 6 ekran + backend) → build (infra + WeeklyActivityBars → 4 ekran paralel → gate) → **adversarial review (11 ajan, rol-gizlilik odaklı)** → fix → breakpoint gate.

**Not (SPEC drift):** rol ekranları SPRINT9_SPEC'te değil SPRINT10/11'e dağılmış; DC birebir kaynak olduğundan build-spec sağlam. Adlandırma kullanıcının "SPRINT9/Grup 7" çerçevesiyle tutuldu (S8/Grup6 ile tutarlı).

---

## Adversarial review — P0 0 · major 2 · minor 2 · phantom 0

Her bulgu bağımsız skeptik doğrulamadan geçti. **Hepsi düzeltildi:**
- **[major] VeliPaneli:366** — Premium ROI "net artışı" sayısı `color.semantic.success` (#1FB683 **dolgu**-token) METİN olarak → 2.60:1 (<3:1 AA büyük-metin) + DC-regresyon. Fix → `successTextOnLight` (#047857).
- **[major] OgrenciOzeti:163** — başlık hiyerarşisi h3'ten başlıyordu (sayfa başlığı span, öğrenci adı div); SR başlık-nav sayfa başlığını/özneyi atlıyor. Fix → h1 (sayfa) + h2 (öğrenci adı) + h3 (kart); kardeş OgretmenPaneli deseniyle hizalı.
- **[minor] VeliPaneli:358** — "Yöntem işe yarıyor" rozeti #17936B 11px → 3.87:1 (<4.5 küçük-metin, DC-kalıtımı). Fix → `successTextOnLight`.
- **[minor] OgretmenPaneli:338** — "Sınıf ort. net" delta koşulsuz `success` (yeşil); negatif düşüş yeşil-iyileşme gibi. Fix → `ortNetDelta<0 ? 'attention'(amber) : 'success'` (kaygı-duyarlı, alarm-kırmızı değil).

SinifKurulumu adversarial'da **tertemiz** çıktı; ama mekanik breakpoint gate onu yakaladı (aşağıda).

---

## Breakpoint gate (hit≥44 + overflow)

İlk run: **21 FAIL** — hepsi **SinifKurulumu**, `overflowX=12` her genişlikte (3 story × 7). Adversarial review + build gate kaçırdı (SPRINT8 dersi tekrar). **Deterministik teşhis** (tek-seferlik Playwright script, parent-zincir): tek taşan öğe = kök `.k-paper` div, `boxSizing: content-box` + `padding: 0 20px 60px` (build ajanı çocuklara box-sizing ekleyip **kökü atladı**). Fix → kök div `boxSizing:'border-box'`. Re-run: **0 FAIL / 280**.

---

## Kapı sonuçları (fix sonrası, canlı doğrulandı)

- kanon-lint **0 ihlal** (12 uyarı, pre-existing/kutlama)
- type-check (tsc) **0 hata**
- vitest src/kiro **52 dosya / 294 test PASS** (0 fail)
- **breakpoint 0 FAIL / 280 kontrol** (rebuild + Playwright)
- axe temiz

---

## ONAY BEKLER (inferred kopya — DC'de olmayan)

- Veli Paneli: ErrorState/EmptyState (SİZ-dili), çocuk-yok → Veli Bağlama CTA.
- Öğretmen Paneli: Empty ("İlk sınıfını kur") / Error.
- Öğrenci Özeti: nötr-durum ("ne risk ne belirgin sağlıklı") + Empty/Error.
- Sınıf Kurulumu: POST hata / roster-boş / kod-üretilemedi.

## Faz 4 / kalan

1. **Grup 7 kalanı (ayrı tur):** Veli Bağlama (KVKK kod-akışı) + Ödev Atama (Ödevlerim döngüsü).
2. **Backend wiring (Faz 4):** `/teacher`+`/parent` gerçek uçlar; katılım-kodu/rotate/join + öğrenci Ödevlerim + zengin-atama backend'de YOK.
3. **Premium/monetization:** Veli Paneli Premium ROI CTA → Grup 8 Abonelik ekranı (link ertelendi).
4. **KVKK (Veli):** çocuk günlük-durum/XP görünürlüğü karşılıklı-onay + opt-in.
5. Rota wiring: ekranlar App router'a bağlanmadı (route guard ile ayrı backlog).

## Kararlar (gelecek session)

- 4 rol-paneli **paper**; Veli/Öğretmen **SİZ-dili**, çocuk/öğrenci verisi **salt-okur**.
- Sınıf Kurulumu **DC SEN** (DC>spec tiebreaker).
- Veli Bağlama = **DC kod-akışı + mock** (Faz 4 gerçek /parent).
- **Deterministik overflow teşhisi:** breakpoint fail'de tahmin etme → Playwright parent-zincir ile taşan öğeyi bul (bu turda kök box-sizing yakalandı).
