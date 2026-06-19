# vp-unlock readability validation — RESULT (2026-06-19)

## Soru
2.107 verified_provisional + content-excluded soru fazla mı eleniyor? D9 view-unlock mümkün mü?

## Bulgu (CANLI DB ölçümü, ezber değil)
- v_safe=7.812, vp_flag_active=9.329, unfiltered=71.603, active=110.895 (handoff doğrulandı)
- **Readability validation: 60/60 SERVABLE (%100 precision)** — workflow wyvo30jwt, 6'lık dalga, schema yok.
  Stratified 60 (11 branş, seed42). Tek borderline: GENEL OCR-pürüz conf0.62 ama servable.
- **AMA mekanizma yanlış modellenmişti:** content-integrity filtresi v_safe_for_beta_unfiltered İÇİNDE.
  2.107 vp-excluded zaten unfiltered'da = content filtresini GEÇMİŞ. Asıl blokör D8 üst-kapıları.
- **Kapı kırılımı (2.107 vp-excluded):**
  - clause3 fallback (konu-etiketi güvensiz): **2.058**
  - clause1 status (unverified): 2.065
  - clause6 gate2c: 42 / clause2 demoted: 6
  - **Temiz açılabilir (yalnız status, fallback/demoted/gate2c temiz): 1**
  - fallback-olmayan toplam: 49

## Karar
- **D9 view-unlock ÖLÜ** — yalnız +1, view-edit'e değmez. UYGULANMADI (DB'ye yazım YOK).
- Okunabilirlik 60/60 doğru ama YANLIŞ EKSEN: fallback = topic-tag güvenilirliği, okunabilirlik değil.
- **Gerçek kaldıraç: fallback re-tag** — 2.058 soru 3-sinyal doğrulanmış (key+blind+readability),
  yalnız güvenilir subject_area/primary_topic eksik. Re-tag → fallback flag temizlenir + status promote → v_safe.
  Handoff "fallback 2.115 topic re-tag (kök-çözüm)" maddesiyle birebir.

## Karpathy dersi
"vp content-filtresine takılıyor" varsayımı yanlıştı; ölçünce gerçek kapı fallback çıktı.
Önce hangi kapının bloklandığını ÖLÇ, sonra çözüm tasarla.
