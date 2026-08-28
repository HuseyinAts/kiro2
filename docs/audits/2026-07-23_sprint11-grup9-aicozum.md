# KIRO2 — Faz 3 · SPRINT11 (Grup 9 · AI & Çözüm) — Grup 9 TAMAM

**2026-07-23** — 3 ekran ✅: **AI Sohbet · Sokratik AI · İnteraktif Çözüm** (paper). Çözüm Paylaş MVP-dışı. Keşif: `2026-07-23_sprint11-grup9-kesif.md`. **Grup 9 = Faz 3 son grubu.**

## Kullanıcı Kararları (uygulandı)
- **Streaming = ÇİFT-KOLLU** (Düello deseni): `streamSohbet` mock setTimeout token-sim (test/dev) + gerçek `/enhanced-chat/stream` fetch+ReadableStream (live). Sokratik = `teaching_mode='socratic'` (SOCRATIC_SYSTEM_PROMPT `:207`, Faz 0 doğrulandı).
- **İnteraktif Çözüm = DC birebir istemci manipülatif** (a/b/c kaydırıcı → canlı SVG parabol + içgörü; keşif-öğrenme). Backend/ChatBubble YOK; istemci-matematik = deterministik render (meşru manipülatif, cevap-uydurma değil).

## Infra (additive)
- types +8 (SohbetMesaj/SohbetOturum/SohbetTeachingMode/SohbetStreamArgs/SohbetStreamHandlers/SokratikSenaryo + 2 mock alan) · api-client +3 (`getSohbet`·`postSohbetMesaj`·**`streamSohbet` çift-kollu**) · msw +2 · kiro-data +2 (sohbet + **sokratik scripted diyalog** — mock LLM yerine cevabı-vermeyen yönlendirici sorular). `ui/ChatBubble` REUSE (ilk gerçek chat tüketicisi).

## Ekranlar
- **AI Sohbet:** SideNav + sohbet kolonu + composer; ChatBubble ai/ben; streamSohbet direct token akışı (pending→onToken append→onFinished); role=log+aria-live; Enter=gönder.
- **Sokratik AI:** 3-sütun (SideNav + merkez sohbet + sağ ray: Üzerinde çalışılan soru / İpucu merdiveni / Sokratik ilerleme); streamSohbet socratic (cevabı VERMEZ, yönlendirir); ≤1023 sağ ray → ana kola kompakt fallback.
- **İnteraktif Çözüm:** istemci manipülatif — a/b/c kaydırıcı + bespoke SVG parabol (tepe/diskriminant/kök) + canlı içgörü kartları; slider aria + aria-live; mesaj/backend yok.

## Adversarial (19 ajan, 4 boyut) — 13 doğrulandı / 10 unique / 2 phantom (0 P0)
- **1 major (a11y):** Sokratik giriş inline `outline:none` global `:focus-visible`'ı eziyor (WCAG 2.4.7) → `.k-sok-field` odak-halkası (AISohbet deseni). AISohbet textarea aynı sınıf → düzeltildi.
- **minör fix:** Sokratik "Çözümü göster"/ilerleme ≤1023 erişilemez → ana kola kompakt fallback; sayaç/adım hizası (3-basamak); "Tekrar dene" 44px; AI Sohbet **`onConnected` bağlandı** (canlı session_id, sunucu-otorite); AI Sohbet SR "yazıyor" duyurusu; İnteraktif eyebrow #3B82F6 3.68:1→ink.muted 5.65:1 AA.
- **nit fix:** ChatBubble uzun-token satır-kaydırma (overflowWrap/wordBreak/minWidth:0, paylaşılan).
- **phantom:** LockIcon faded3 grafik-kontrast (borderline); DC-atlama doğrulama kaydı.

## Kapı (otoriter, bağımsız)
kanon **0 ihlal** (15 uyarı pre-existing) · scoped tsc **0** · vitest **69 dosya / 472 test PASS** (423→472, +49) · **breakpoint 0 FAIL / 483** · axe temiz. (Rebuild turu: Sokratik giriş input hit-target 20→44 fix.) ChatBubble değişikliği tüketicileri (SeriDondurma) bozmadı.

**İlerleme: 41/42 ekran + QuestionCard + WeeklyActivityBars + VeliYonlendirmeKarti + ui/Switch + ayarStore. Grup 9 (AI & Çözüm) TAMAM (3/3).**
Sonraki: **Auth kalıntı** — İlk Hafta + route guard/rol yönlendirmesi → **Faz 3 KAPANIŞ (42/42)**. Sonra Ödev Atama↔Ödevlerim E2E + push + full build (roadmap C) + Faz 4 wiring.
