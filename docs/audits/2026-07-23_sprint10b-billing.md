# KIRO2 — Faz 3 · SPRINT10-B (Grup 8 · İş & Dayanıklılık — billing zinciri)

**2026-07-23** — 3 ekran ✅: **Abonelik · Ödeme(+3DS mock) · Plan Yönetimi** (paper) + paylaşılan **VeliYonlendirmeKarti** (KVKK). Keşif: `2026-07-23_sprint10-grup8-kesif.md`. Grup 8 → 6/7.

## Kullanıcı Kararları (uygulandı)
- **Ödeme/PSP = Faz 3 saf-mock:** gerçek iyzico/PayTR/Stripe yok; 3DS = timer-sim (`getOdeme3dsSonuc`, istemci sonuç üretmez); kart alanları PCI **UI-only** (backend'e gitmez).
- **Öğrenci fiyat GİZLİ:** Abonelik+Plan Yönetimi (+Ödeme guard) öğrenci rolünde fiyat/plan/CTA/ödeme göstermez → paylaşılan `VeliYonlendirmeKarti` (satın-alma yalnız veli).
- **İsim ayrımı:** `Plan*`/`PlanWeek`/`getPlanWeek` (çalışma planı) dokunulmadı; abonelik "Plan"ı = `AbonelikPlan`/`AbonelikYonetim`/`getAbonelikYonetim`. Fiyat/ROI modeli `veliDashboard.premium`+`roi` ile hizalı (çelişen 2. model yok).
- **Zincir:** Abonelik CTA → `/odeme?rol=veli&fatura={donem}` → Plan Yönetimi (route guard Faz 4; port CTA-link).

## Infra (additive)
- **types.ts (+11):** PlanTier · FaturaDonem · AbonelikPlan · AbonelikData · OdemeFaz · OdemeOzeti · KartFormState(UI-only) · ThreeDSDurum · OdemeYontem · Fatura · AbonelikYonetim.
- **api-client.ts (+8):** getAbonelik(rol) · getOdemeOzeti · postOdemeDeneme · getOdeme3dsSonuc(timer-sim) · getAbonelikYonetim(rol) · postAbonelikIptal · postAbonelikGeriAc · getFaturaMakbuz. REUSE getEngine/getVeliDashboard/getMe.
- **mswHandlers +8 route · kiro-data +2 anahtar** (abonelik/abonelikYonetim). **Paylaşılan:** `screens/billing/VeliYonlendirmeKarti.tsx` (KVKK, fiyat göstermez).

## Ekranlar
- **Abonelik:** rol-uyarlanır (veli SİZ / öğrenci SEN→VeliYonlendirme); veli: hero + kanıt şeridi (roi) + fatura toggle + 2-plan grid + güven çipleri; CTA → /odeme.
- **Ödeme (composite, 3-fazlı state machine):** form (2-sütun kart PCI-UI-only + özet) → 3ds (spinner RM-guard + bespoke stepper, `getOdeme3dsSonuc`) → tamam. banka-decline = AMBER (kırmızı değil).
- **Plan Yönetimi:** varyant matrisi (durum×fatura×rol); iptal-bandı amber + geri-aç; iptal düğmesi coral-METİN (kırmızı değil); Empty (fatura yok); öğrenci→VeliYonlendirme.

## Adversarial (23 ajan, 4 boyut) — 16 doğrulandı / 13 unique / 3 phantom
- **major (AA):** AbonelikPage:491 veli dipnotu `ink.faded2` (2.08:1) → `ink.muted` (S10-A Alan ile aynı sınıf; Plan doğru yapmıştı, Abonelik atlamıştı). **FIX.**
- **major (Ödeme a11y):** kart inputları `outline:none` → görünür odak (WCAG 2.4.7); 3DS decline `role=alert`+aria-invalid (4.1.3). **FIX.**
- **minör/nit fix:** Abonelik CTA veli-variant kopya (DC) + seri çipi amber→coral + hero dik serif; Ödeme validation aria-describedby always-render + geri-link 44px + **öğrenci guard→VeliYonlendirme (KVKK defense-in-depth)** + stepper role=list/aria-current + 3ds/tamam/decline axe testleri; Plan öğrenci MarkaBar 'Premium' kaldır (KVKK sızıntı) + geri-aç refetch (sunucu-otorite).
- **Phantom (Faz 4 notu):** getAbonelik('ogrenci') payload'ında fiyat (sunucu-strip Faz 4; ekran-gating yeterli) · 3DS 'bekliyor' re-poll (live Faz 4).

## Kapı (otoriter, bağımsız)
kanon **0 ihlal** (14 uyarı pre-existing) · scoped tsc **0** · vitest **61 dosya / 383 test PASS** (340→383, +43) · **breakpoint 0 FAIL / 455** · axe temiz.

**İlerleme: 37/42 ekran + QuestionCard + WeeklyActivityBars + VeliYonlendirmeKarti. Grup 8 kısmi (6/7).**
Sonraki: **S10-C Ayarlar** (composite + yeni `ui/Switch`; `KullaniciAyar` tek-kaynak + tam davranış; abonelik-banner gömülü dusk aksan) → Grup 8 TAMAM.
