# Plan: Sokratik AI Sohbet & LLM Guardrails / RAG Katmanı Geliştirmeleri

## Kapsam ve Amaç
Qwen3 / LiteLLM destekli Sokratik AI Sohbet motorunun MEB YKS/TYT/AYT müfredatına %100 uyumlu, halüsinasyonsuz ve pedogojik soru-cevap mantığı ile çalışmasını garanti altına alan RAG (Retrieval-Augmented Generation) katmanı ve LLM Guardrail mimarisinin geliştirilmesi.

## Değiştirilecek / Oluşturulacak Bileşenler

1. **`backend/services/socratic_rag_guardrail_service.py` (Yeni Servis):**
   - **Müfredat Doğrulama (Curriculum Retrieval):** MEB YKS ders ve konu kazanımları ile RAG bağlamı oluşturma.
   - **Sokratik Uyumluluk Skoru (Socratic Compliance Check):** Cevabın direkt yanıt verme oranını (Direct Answer Leakage) tespit edip yonlendirici soruya çevirme.
   - **LaTeX / Formül Bütünlüğü:** `$`/`$$` LaTeX ifadelerinin doğru kapatıldığını doğrulama.

2. **`backend/app/guardrails/guards/socratic_guard.py` (Yeni Guardrail Bileşeni):**
   - Direct Answer Detector (Örn: "Doğru cevap C şıkkıdır", "x = 12 bulunur" kalıplarını yakalayıp Sokratik dönüşüm sağlama).
   - Prompt Injection & Scope Guardrail (Müfredat dışı veya zararlı komutları engelleme).

3. **`backend/api/enhanced_chat.py` Entegrasyonu:**
   - Sokratik sohbet endpoint'lerine (`/api/v1/enhanced-chat/message`, `/socratic-dialogue`) RAG bağlamı ve Guardrail denetim süreçlerini dahil etme.

4. **Kapsamlı Test Suite (`backend/tests/unit/test_socratic_rag_guardrails.py`):**
   - Direct answer leakage engelleme testleri.
   - Prompt injection ve müfredat dışı soru engelleme testleri.
   - RAG bağlamı ile halüsinasyonsuz yanıt üretimi testleri.
   - %80+ kapsama ve 0 ruff / mypy hatası.
