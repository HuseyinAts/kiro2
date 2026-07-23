# KIRO2 — Faz 3 · SPRINT11 (Grup 9 · AI & Çözüm) Keşif

**2026-07-23** — 3 ekran: AI Sohbet · Sokratik AI · İnteraktif Çözüm (Çözüm Paylaş MVP-dışı). Keşif workflow (5 ajan + sentez; sentez ağ-hatası düştü → elle sentezlendi). **Grup 9 = Faz 3 son grubu.**

## Tema (3/3 PAPER, DC-kanıtlı)
Üçü de `body{background:#F7F4EF}` + `#2A2433` — dusk yok.

## Backend Gerçeği (mock-vs-gerçek)
| Ekran | Durum | Gerçek Uç | Not |
|---|---|---|---|
| **AI Sohbet** | GERÇEK | `POST /api/v1/enhanced-chat/message` + **SSE `/stream`** (`enhanced_chat.py:422/538`) | LLM: LiteLLM→Ollama qwen3:8b→statik fallback; `chat_sessions/messages` DB; IDOR guard. |
| **Sokratik AI** | GERÇEK | Aynı uçlar + `teaching_mode='socratic'` | **SOCRATIC_SYSTEM_PROMPT `:207` DOĞRULANDI** (Faz 0), bilge_alp DEĞİL; ayrı uç yok, flag. Cevabı vermeme kuralları prompt'ta. |
| **İnteraktif Çözüm** | — (istemci) | YOK gerekmiyor | **DC = istemci manipülatif** (a/b/c kaydırıcı → canlı SVG parabol + içgörü); chat/AI/adım-çözücü DEĞİL. İstemci matematik = deterministik render (meşru manipülatif). |

**Not (ölü/mock kalıntı):** `ai_chat_service.py:348` generate_ai_response = placeholder string (v1/chat); `litellm_chat.py` 0-byte (loader'da kayıtlı, ölü); `turkish-nlp-chat` + `math-solution-steps` şablon-tabanlı (LLM değil). Bunlar Grup 9 DC'lerinin evi DEĞİL — kullanılmayacak.

## Infra & Çakışma (çakışma YOK)
- `ui/ChatBubble` MEVCUT (props `role:'ai'|'me'`/children/tag/tagBg/tagFg/pending) — Grup 9 ilk gerçek tüketici (şimdiye SeriDondurma). REUSE, ikinci balon YAPMA.
- api-client'ta chat/sohbet/sokratik metod YOK — tüm adlar serbest.
- **Streaming:** `duelStream` (api-client.ts:824-891) çift-kollu deseni — mock setTimeout token-sim + canlı SSE. NOT: `/enhanced-chat/stream` **POST**'tur → EventSource (GET) değil, **fetch + ReadableStream** okuma; mock dalı setTimeout scripted token.
- İnteraktif Çözüm: yeni uç gerekmez (istemci); yeni ui primitive gerekmez (ekran-yerel SVG).

## Kullanıcı Kararları
- **Streaming = ÇİFT-KOLLU** (Düello deseni): mock setTimeout token-sim (test/dev varsayılan) + gerçek `/enhanced-chat/stream` fetch-stream (live). Sokratik = `teaching_mode='socratic'`.
- **İnteraktif Çözüm = DC BİREBİR istemci manipülatif** (kaydırıcı + canlı SVG parabol + içgörü kartları; keşif-öğrenme). Backend/ChatBubble/QuestionCard yok.

## Build Sırası
0. **Infra (chat):** types (SohbetMesaj/SohbetOturum/SohbetTeachingMode/StreamHandlers) + api (getSohbet · postSohbetMesaj · **streamSohbet çift-kollu**) + msw (sessions/message mock) + kiro-data (sohbet açılış + **sokratik scripted diyalog** — mock LLM yerine, cevabı-vermeyen yönlendirici sorular). ChatBubble REUSE.
1. **AI Sohbet** (SideNav + sohbet kolonu + composer; ChatBubble; streamSohbet direct).
2. **Sokratik AI** (3-sütun: SideNav + merkez sohbet + sağ ray "Üzerinde çalışılan soru / İpucu merdiveni / Sokratik ilerleme"; streamSohbet socratic).
3. **İnteraktif Çözüm** (istemci manipülatif; a/b/c kaydırıcı + bespoke SVG parabol + içgörü kartları; infra yok).

## Riskler / Kanon-watch
- Streaming-motion (typing/token) → RM-guard + calmMode (.k-calm) saygı; layout-anim yok.
- **faded/faded2 okunur-metin taraması** (3 sprint üst üste çıktı → ink.muted).
- Sokratik: istemci CEVAP UYDURMAZ; mock scripted diyalog cevabı vermez (yönlendirir). Sunucu-otorite.
- ChatBubble `role='me'` coral #C2452B — coral CTA/metin kanonu.
- İnteraktif SVG: kaydırıcı hit-target ≥44; slider aria (role=slider/aria-valuenow); canlı-bölge içgörü (aria-live polite).
- Kalibrasyon: AI Sohbet ~1.7 · Sokratik ~2.0 (3-sütun+streaming) · İnteraktif ~2.0 (bespoke SVG+etkileşim). Toplam ~5.7.

*Kaynak: keşif workflow `wf_1c79b681-7e4` (5/6 ajan; sentez ağ-hatası, elle sentez).*
