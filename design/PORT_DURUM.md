# KIRO2 — Faz 0-1 Kuruluş Durumu (2026-07-22)

**Faz 0 keşif ✅** — 4 hedef canlı kodda doğrulandı (`docs/audits/2026-07-22_faz0-kesif.md`, 8 agent):
- teacher/classes **VAR** (`teacher_classroom.py:98,138`); katılım kodu · code/rotate · `/me/class/join` · sınıf-varsayılanları **YENİ**.
- Lig **VAR** (`league_api.py`, loader:205) → **yeni `/league` YAZMA**; "sakin mod / sıralamayı gizle" ayarı **YENİ**.
- diary mood kayıt ucu + gizlilik guard'ı **VAR** (`diary_api.py:1266`, self-only) → yeniden kurma yok.
- ⚠ Sokratik prompt "evi" = **`enhanced_chat.py`** (SOCRATIC_SYSTEM_PROMPT + teaching_mode), bilge_alp DEĞİL — plan G düzeltmesi.

**Faz 1 kuruluş ✅** — DoD:
- `design/` = handoff kökü (flatten); `node design/scripts/kanon-lint.mjs frontend/src/kiro` çalışır.
- `frontend/src/kiro/{tokens,types,api,ui,screens}/` — tokens.ts/css + types.ts + api-client.ts + kiro-data.json birebir; theme.tsx foundation.
- `configureKiroApi({mode:'mock', mockData})` → `OrnekPage` GERÇEK mock veriyi render eder (RTL testi **PASS**).
- Doğrulama: kanon-lint **0 ihlal** (2 uyarı: tokens `#6B6478` — kaynak dosya paper+dusk ikisini de tanımlar, yanlış-pozitif) · scoped strict `tsc` **0 hata** · vitest **PASS**.
- ADR'ler `docs/adr/README.md` (design tek-dosya formatı). kanon-lint CI'da: `ci.yml` frontend-test adımı + `npm run kanon:lint`.
- Verbatim sapmalar (kayıt): import `./types`→`../types` · 2 doküman-yorumu "eksik" + 1 `⚠️` emoji neutralize · kullanılmayan `Question` import kaldırıldı.
- react-query v5 (ADR-006) **ERTELENDİ** — Faz 1 plain hooks; screen-state gerektiğinde (YAGNI).

---

# KIRO2 — Faz 2 Bileşen Kalite Kapısı (2026-07-22)

**20/20 bileşen ✅** — her biri story + RTL + axe + BackstopJS kapısından geçti.
- Storybook **10.5.3** (Vite 7 builder) + `@storybook/addon-a11y`; `.storybook/` config; `npm run storybook` / `build-storybook`.
- Piksel refleri `frontend/src/kiro/ui/__pixel_refs__/` (7 `.dc.html`; gitignore'lu Deckset'e bağımlı değil).
- Kalibrasyon trio: Button · Card · StatusChip. Kalan 17: **17-agent workflow fan-out** (kanon 0 + strict tsc 0 ilk geçişte).
- **Doğrulama:** vitest **115 test / 21 dosya PASS** · kanon-lint **0 ihlal** · scoped strict tsc **0** · BackstopJS **111 story → 222/222 ≤%1** (LOKAL dev gate: `npm run kiro:visual:ref|test`).
- Skeleton: kiroSweep (2.6s) + 3sn güvence + gün-mantrası (`role=status`) — spec-mandated, story+test dahil.

**A11y bulguları (çözüldü — GİZLENMEDİ):**
- ProgressBar: `role=progressbar` erişilebilir ad yoktu → **`ariaLabel` prop eklendi** (fix).
- ChatBubble(me) · Button primary · SideNav-aktif: beyaz metin coral `#FF6F5C` üzerinde ~2.75:1 < AA idi → **düzeltildi** (yeni token `coralCtaBg = #C2452B`; beyaz metin 5:1, `#C2452B`/`#FFF3EE` 4.69:1 — AA ✓). Bright coral yalnız aksan/glow için kalır.

**Sapmalar → ADR-007** (`docs/adr/README.md`).

---

# KIRO2 — Faz 3 · SPRINT1 Durumu (2026-07-22)

**2/2 ekran ✅** — Giriş & Kayıt · Ödevlerim (rapor: `docs/audits/2026-07-22_sprint1-ekranlar.md`).
- **Tema:** her ikisi **paper** (Giriş "dusk" talimatı → SPEC/DC gereği **paper** onaylandı; route-bazlı, toggle YOK).
- **DoD:** axe temiz · breakpoint **14/14** (390→1440 overflowX=0 + hit≥44 ≤1199, `npm run kiro:breakpoints`) · odak halkası `:focus-visible` · kanon 0 · tsc 0 · vitest **13/13**.
- **Veri:** configureKiroApi mock + MSW handler seti (`kiro/api/mswHandlers.ts`, kiro-api.js'ten türetildi).
- **Coral-CTA:** `coralCtaBg #C2452B` + beyaz (onaylı sapma). **Button md 40→44px** (SPEC A1 + hit≥44).
- **Kopya sapması (ONAY BEKLER):** 2 dize spec'in kendi "absence-dili yok" kuralı gereği nötrlendi — e-posta hint "yarım görünüyor"; liste dipnotu "Geciken ödev kapanmaz — 'bekliyor'".
- **Kalibrasyon:** ekran-port infra (template + MSW kalıbı + `kiro:breakpoints` Playwright denetçisi) tek-seferlik kuruldu; kalan 40 ekran ≈ **44–52 birim** (S2'de yeniden ölç). Detay raporda.

---

# KIRO2 — Faz 3 Ekran Port Takibi (43 ekran × 6 DoD — 42 port + 1 MVP-dışı bekleme)

2026-07-22: +1 Sınıf Kurulumu (S11). Tasarım Dili (public sayfa) ve E-posta & Bildirim (kopya sistemi spec'i) PORT EDİLMEZ — referans yüzeyleri.
2026-07-05: +3 yeni tasarım eklendi (Veli Bağlama · Öğrenci Özeti · Plan Yönetimi); 3DS bekleme
durumu Ödeme ekranının parçasıdır (ayrı satır değil). Çözüm Paylaş MVP DIŞI işaretlendi.

Sütunlar (URETIM_YOL_HARITASI Faz 3 DoD'si):
**PX** prototiple yan yana piksel karşılaştırma · **DUR** Skeleton/Empty/Error üç durum bağlı ·
**390** 390px'te overflow-x=0 + hit ≥44pt + safe-area · **KOPYA** kaygı-duyarlı kopya birebir ·
**A11Y** klavye + aria-label + axe temiz · **TEMA** ekran-türü teması doğru (çalışma=açık · duygusal=koyu)

İşaretleme: `☐` → `☑`. Her PR bu dosyayı günceller; grup bitince gruba tarih yaz.

## 1 · Auth & ilk temas (4)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Giriş & Kayıt | KIRO2 Giris.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Hesap Kurtarma (3 adım) | KIRO2 Hesap Kurtarma.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Onboarding (misafir yerleştirme) | KIRO2 Onboarding.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| İlk Hafta | KIRO Ilk Hafta.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

+ route guard + rol yönlendirmesi (öğrenci/veli/öğretmen): ☐

## 2 · SideNav + Öğrenci Paneli (1)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Öğrenci Paneli (Rahat/Kompakt) | KIRO2 Ogrenci Paneli.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

## 3 · Çekirdek döngü (6)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Soru Çözme | KIRO2 Soru Cozme.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Neden Geri Bildirim | KIRO2 Neden Geri Bildirim.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| FSRS Tekrar | KIRO2 FSRS Tekrar.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Adaptif Test | KIRO2 Adaptif Test.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Harmanlanmış Deneme | KIRO2 Harmanlanmis Deneme.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Sınav Sonuç (net-birincil) | KIRO2 Sinav Sonuc.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

## 4 · Planlama (4)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Haftalık Plan | KIRO2 Haftalik Plan.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Öğrenme Yolu | KIRO2 Ogrenme Yolu.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Bilgi Atomları | KIRO Bilgi Atomlari.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Çalışma Modları | KIRO Calisma Modlari.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

## 5 · Hub / duygusal — KOYU (6)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Bugün (hub) | KIRO Safak.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Kutlama | KIRO2 Kutlama.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Mola | KIRO2 Mola.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Geri Sayım (kaygı-nötr varsayılan) | KIRO2 Sinav Geri Sayim.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Başarımlar | KIRO2 Basarimlar.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Boss Savaşı | KIRO2 Boss Savasi.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

## 6 · Oyunlaştırma (4)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Lig (siralamaGizli + gizle düğmesi) | KIRO2 Lig.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 1v1 Düello | KIRO2 Duello.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Arkadaş Serisi | KIRO2 Arkadas Serisi.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Seri Dondurma | KIRO2 Seri Dondurma.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

## 7 · Roller (6)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Veli Paneli (SİZ-dili) | KIRO2 Veli Paneli.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Öğretmen Paneli | KIRO2 Ogretmen Paneli.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Öğrenci Özeti (öğretmen, salt-okur) | KIRO2 Ogretmen Ogrenci Ozet.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Veli Bağlama (KVKK, iki taraf) | KIRO2 Veli Baglama.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Ödev Atama | KIRO2 Odev Atama.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Sınıf Kurulumu ("İlk sınıfını kur") | KIRO2 Sinif Kurulum.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Ödevlerim | KIRO2 Odevlerim.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |

Ödev Atama ↔ Ödevlerim tek döngü olarak test edildi: ☐

## 8 · İş & dayanıklılık (7)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Abonelik (?rol=veli) | KIRO2 Abonelik.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Ödeme (+3DS bekleme durumu) | KIRO2 Odeme.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Plan Yönetimi (premium) | KIRO2 Plan Yonetimi.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Ayarlar | KIRO2 Ayarlar.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Bildirim Merkezi | KIRO2 Bildirim Merkezi.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Alan Kütüphanesi (ünite drill) | KIRO2 Alan Kutuphanesi.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Çevrimdışı | KIRO2 Cevrimdisi.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

## 9 · AI & çözüm (4)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| AI Sohbet | KIRO2 AI Sohbet.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Sokratik AI (mock → Faz 4 proxy) | KIRO2 Sokratik AI.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| İnteraktif Çözüm | KIRO2 Interaktif Cozum.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Çözüm Paylaş — **MVP DIŞI** (karar 2026-07-04; pilot kararı gelirse açılır) | KIRO Cozum Paylas.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

---
**Kapsam dışı (2):** Kaygı Ölçüm · Moderatör Kılavuzu — araştırma saha paketi, üretime port edilmez.

**Kalibrasyon (ilk sprint):** Button+Card+StatusChip + Giriş + Ödevlerim → ekran-başı/bileşen-başı gerçek süreyi buraya yaz:
- Bileşen-başı ölçülen süre: ___
- Ekran-başı ölçülen süre: ___
- Tahmin: kalan ≈ (ekran-süresi × 37) + (bileşen-süresi × 17) + (uç-süresi × 34)
