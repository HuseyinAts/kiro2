# KIRO2 — Faz 3 · SPRINT9-B Roller kalanı (Grup 7 · B) — RAPOR

**Tarih:** 2026-07-23
**Branch:** feature/self-evolution-optimization (push YOK)
**Kapsam:** Grup 7'nin ağır ikilisi — Veli Bağlama (KVKK) + Ödev Atama. **Grup 7 (Roller) TAMAM (6/6).**
**Sonuç:** 2/2 ✅. İlerleme **31/42 ekran + 1 composite (QuestionCard) + `ui/WeeklyActivityBars`**.

---

## Ekranlar (ikisi de PAPER)

| Ekran | Rota | Not |
|---|---|---|
| **Veli Bağlama** | `/veli-baglama` (+`?rol=ogrenci`) | KVKK iki-taraf onam; SideNav YOK merkezi kart-akışı; **veli SİZ 4-adım + öğrenci SEN 2-durum** |
| **Ödev Atama** | `/ogretmen/odev/yeni` (+`?ogrenci=id`) | öğretmen "sana" meslektaş; konu radiogroup + öğrenci checkbox + θ switch; Ödevlerim döngüsü |

---

## Kararlar & backend

- **Veli Bağlama = DC 6-haneli kod-akışı + mock** (kullanıcı kararı; IDOR-güvenli, çocuk-başlatımlı). Gerçek `/parent` **email-tabanlı** iki-taraf onay MEVCUT → Faz 4 wiring. KVKK uçları (`/kvkk/notice`, `/kvkk/consent/give`, `/parent/approval`) MEVCUT.
- **Ödev Atama** backend-gap: mevcut `POST /teacher/assignments` yalnız {baslik,aciklama,sinif,teslim,durum} — konu/adet/kişi YOK → mock zengin sözleşme. Öğrenci "Ödevlerim" GET de backend'de YOK (mock).
- **Metod-collision çözümü:** `getTopics`/`getClassRoster`/`postAssignment` + `SinifOgrenci` SPRINT4'ten farklı imzayla ZATEN VAR → yeni adlar `getAtamaKonular`/`getAtamaRoster`/`postAtama` + `AtamaOgrenci` (extends). **SPRINT4 bozulmadı** (additive).
- **Sunucu-otorite:** kod-doğrulama + KVKK rıza + bağlantı-durumu (Veli Bağlama) ve θ-tabanlı set-kurulumu (Ödev Atama) SUNUCUDA; istemci mock'ta bile bu türevleri üretmez/hesaplamaz.
- **Ödevlerim döngüsü:** AtamaForm shape'i Ödevlerim (SPRINT1) tüketimiyle hizalı; OgrenciOzeti "ödev ata" CTA rotası `/ogretmen/odev/yeni?ogrenci=` olacak şekilde hizalandı. Not: tam runtime-döngü (atama→Ödevlerim'de görünme) ortak-mock-store gerektirir — **Faz 4** (contract hizalı, E2E ertelendi).

---

## Adversarial review — P0 0 · major 0 · minor 2 · phantom 0

- **VeliBaglama: 0 bulgu** (KVKK/server-otorite + iç-içe checkbox-link fix + consent-gate + SEN/SİZ iki-dil hepsi tuttu — en hassas ekran tertemiz).
- **[minor] OdevAtama:352** — "Sınıfının" → "Sınıfın" (DC-birebir). **Fix.**
- **[minor] OdevAtama:460** — kaygı-kartı 2. maddesi DC'den sapmış. DC `Geciken teslim "eksik" değil "bekliyor"…` ama **kanon-lint `eksik` yasağı** (`/\beksik\b/i`) DC metnini engelliyor → DC'ye körlemesine dönmek gate'i kırardı. **Fix (kanon-güvenli):** `Geciken teslim kapanmaz; "bekliyor" olarak etiketlenir.` (kaygı-duyarlı anlam + DC-yapısına yakın, "eksik" yok).

---

## Kapı sonuçları (fix sonrası, canlı doğrulandı)

- kanon-lint **0 ihlal** (14 uyarı, pre-existing/kutlama; "eksik" 0)
- type-check **0 hata**
- vitest src/kiro **54 dosya / 308 test PASS**
- **breakpoint 0 FAIL / 329 kontrol** (2 yeni ekran 49/49 OK; kök box-sizing dersi tuttu)
- axe temiz

---

## ONAY BEKLER (inferred kopya)

- Veli Bağlama: Empty (bekleyen istek yok) / Error (kod doğrulanamadı amber) / kart-çöküşü.
- Ödev Atama: roster-boş → Sınıf Kurulumu / konu-havuzu-boş / Error (form-state korunur).

## Faz 4 / kalan

1. **Backend wiring:** Veli Bağlama gerçek `/parent` (email→kod-akışı sözleşmesi); Ödev Atama zengin `/teacher/assignments` + öğrenci Ödevlerim GET + teslim; katılım-kodu YOK.
2. **Ödev Atama ↔ Ödevlerim tam döngü:** ortak-mock-store veya gerçek backend ile E2E (şu an contract hizalı).
3. **KVKK:** kod-akışı ucu + rıza purpose slug (`veli_baglama_calisma_verisi`) + notice_version pinleme; öğrenci-yönlü "bekleyen veli isteği" GET ucu backend'de YOK.
4. Rota wiring: ekranlar App router'a bağlanmadı (ayrı backlog).

## Kararlar (gelecek session)

- Veli Bağlama = **DC kod-akışı + mock**; veli **SİZ** / öğrenci **SEN** iki-dil; kod/consent/durum **sunucu-otorite**.
- Ödev Atama θ-set **sunucuda**; öğretmen "sana" dili; risk=amber.
- **kanon-lint > DC-birebir** çakışmada (DC "eksik" → kanon yasak → kanon-güvenli reword). Metod-collision → yeni-ad (mevcut imzayı bozma).
