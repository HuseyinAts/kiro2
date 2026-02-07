# Expert Agents API Documentation

Konu Bazli Subagent Sistemi - YKS Soruları İçin Uzman Yapay Zeka

## Overview

6 domain expert agent sistemi, Sid Bidasaria subagent mimarisine dayanır:
- Her agent 200K token izole context ile çalışır
- Blackboard pattern ile koordinasyon
- Sequential multi-domain işleme

## Base URL

```
/api/v1
```

## Endpoints

### 1. POST /ask-question

Soru sor ve cevap al.

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question_text` | string | Yes | Soru metni (10-5000 karakter) |
| `student_id` | string | No | Öğrenci ID (tracking için) |
| `preferred_domain` | enum | No | Tercih edilen domain |
| `include_visualizations` | bool | No | Görsel oluştur (default: true) |
| `include_step_by_step` | bool | No | Adım adım çözüm (default: true) |

#### Example Requests

**Matematik Sorusu:**
```json
{
  "question_text": "2x + 3 = 7 denklemini çözünüz.",
  "student_id": "student_001",
  "include_step_by_step": true
}
```

**Fizik Sorusu:**
```json
{
  "question_text": "2 kg kütleye 10 N kuvvet uygulanırsa ivme kaç m/s² olur?",
  "preferred_domain": "fizik"
}
```

**Türkçe Sorusu:**
```json
{
  "question_text": "Namık Kemal'in eserleri hangi edebi akıma aittir?",
  "student_id": "student_002"
}
```

**Multi-Domain Sorusu:**
```json
{
  "question_text": "Newton'un hareket yasaları ve türev ilişkisini açıklayınız."
}
```

#### Response

```json
{
  "success": true,
  "classification": {
    "primary_domain": "matematik",
    "primary_confidence": 0.95,
    "secondary_domain": null,
    "secondary_confidence": null,
    "is_multi_domain": false
  },
  "responses": [
    {
      "domain": "matematik",
      "content": "2x + 3 = 7 denklemini çözelim...",
      "confidence": 0.92,
      "tools_used": ["sympy"],
      "step_by_step_solution": [
        "Adım 1: Her iki taraftan 3 çıkar: 2x = 4",
        "Adım 2: Her iki tarafı 2'ye böl: x = 2"
      ],
      "latex_expressions": ["2x + 3 = 7", "x = 2"],
      "visualizations": [],
      "references": ["Cebir temel kuralları"],
      "response_time_ms": 1250.5,
      "tokens_used": 1500
    }
  ],
  "synthesized_response": "Denklemin çözümü x = 2'dir.",
  "specialization_score": 0.88,
  "total_response_time_ms": 1250.5,
  "metadata": {
    "agents_called": ["matematik"],
    "is_multi_domain": false,
    "student_id": "student_001"
  }
}
```

---

### 2. GET /agents/{agent_name}/performance

Agent performans metriklerini al.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_name` | string | Agent adı (matematik, fizik, turkce, sosyal, biyoloji, yabanci_dil) |

#### Response

```json
{
  "agent_id": "matematik_agent_001",
  "domain": "matematik",
  "specialization_areas": ["cebir", "geometri", "analiz", "olasilik"],
  "total_questions_answered": 150,
  "successful_answers": 145,
  "failed_answers": 5,
  "average_response_time_ms": 1200.5,
  "average_confidence": 0.89,
  "current_specialization_score": {
    "domain": "matematik",
    "domain_relevance": 0.92,
    "accuracy": 0.88,
    "completeness": 0.85,
    "user_satisfaction": 0.90,
    "total_score": 0.89,
    "calculated_at": "2026-01-16T12:00:00Z"
  },
  "context_usage": {
    "current_tokens": 15000,
    "max_tokens": 200000,
    "usage_percent": 7.5
  },
  "tools_available": ["sympy", "matplotlib", "latex"],
  "last_activity": "2026-01-16T12:00:00Z"
}
```

---

### 3. GET /agents/specialization-scores

Tüm agent'ların uzmanlik skorlarini al.

#### Response

```json
{
  "scores": [
    {
      "domain": "matematik",
      "domain_relevance": 0.92,
      "accuracy": 0.88,
      "completeness": 0.85,
      "user_satisfaction": 0.90,
      "total_score": 0.89,
      "calculated_at": "2026-01-16T12:00:00Z"
    },
    {
      "domain": "fizik",
      "total_score": 0.87,
      "..."
    }
  ],
  "average_score": 0.87,
  "best_performing_domain": "matematik",
  "needs_retraining": []
}
```

---

### 4. GET /agents/metrics

Sistem metriklerini al.

#### Response

```json
{
  "coordinator": {
    "total_questions_processed": 500,
    "multi_domain_questions": 45,
    "average_response_time_ms": 1500.0
  },
  "scorer": {
    "total_scores_calculated": 500,
    "domains_tracked": 6
  },
  "tracker": {
    "uptime_seconds": 86400,
    "requests_per_minute": 5.2
  }
}
```

---

## Agent Specialization Areas

### Matematik Agent (REQ-1)

| Alt Alan | Açıklama | Araçlar |
|----------|----------|---------|
| Cebir | Denklemler, polinomlar, fonksiyonlar | SymPy |
| Geometri | Üçgenler, çemberler, koordinat geometrisi | Matplotlib |
| Analiz | Türev, integral, limit | SymPy |
| Olasılık | Kombinatorik, olasılık dağılımları | NumPy |

### Fizik Agent (REQ-2)

| Alt Alan | Açıklama | Araçlar |
|----------|----------|---------|
| Mekanik | Newton yasaları, enerji, momentum | SymPy |
| Elektrik | Ohm yasası, devreler, elektromanyetizma | Matplotlib |
| Optik | Mercekler, aynalar, dalga optiği | Diagram gen |
| Termodinamik | Isı, sıcaklık, ideal gazlar | Formül |

### Türkçe Agent (REQ-3)

| Alt Alan | Açıklama | Araçlar |
|----------|----------|---------|
| Dilbilgisi | Ek fiil, sözcük türleri, cümle yapısı | Zemberek |
| Edebiyat | Dönemler, yazarlar, eserler | Veritabanı |
| Anlam Bilgisi | Mecaz, anlam genişlemesi, deyimler | NLP |

### Sosyal Bilimler Agent (REQ-4)

| Alt Alan | Açıklama | Araçlar |
|----------|----------|---------|
| Tarih | Osmanlı, Cumhuriyet, dünya tarihi | Kronoloji |
| Coğrafya | İklim, nüfus, ekonomik coğrafya | Harita ref |
| Felsefe | Epistemoloji, etik, mantık | Kaynak |

### Biyoloji Agent (REQ-5)

| Alt Alan | Açıklama | Araçlar |
|----------|----------|---------|
| Hücre | Organeller, metabolizma, bölünme | Diagram |
| Genetik | DNA, RNA, Mendel, Punnett | Punnett gen |
| Ekoloji | Ekosistem, besin zinciri, popülasyon | Şema |

### Yabancı Dil Agent (REQ-6)

| Alt Alan | Açıklama | Araçlar |
|----------|----------|---------|
| Grammar | Tenses, conditionals, passive | Kural tablosu |
| Vocabulary | Synonyms, antonyms, etymology | Sözlük |
| Reading | Main idea, inference, context clues | Strateji |

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Başarılı |
| 400 | Geçersiz istek (bad request) |
| 404 | Agent bulunamadı |
| 422 | Validation hatası |
| 500 | Sunucu hatası |
| 503 | Agent servisi kullanılamıyor |

---

## Specialization Score Formula

```
Score = 0.40 × Domain Relevance
      + 0.30 × Accuracy
      + 0.20 × Completeness
      + 0.10 × User Satisfaction
```

**Thresholds:**
- Optimal: >= 0.85
- Acceptable: 0.70 - 0.85
- Retraining needed: < 0.70

---

## Success Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Specialization Score | >= 0.85 | Weighted average of quality metrics |
| Cross-Domain Contamination | < 5% | Domain-specific content accuracy |
| Response Accuracy | >= 95% | Correct answer rate |
| Response Time | < 3 sec | Average response time |
| User Satisfaction | >= 4.5/5.0 | User feedback score |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| POST /ask-question | 60/minute |
| GET /agents/* | 120/minute |

---

## Authentication

Endpoints require valid JWT token in Authorization header:

```
Authorization: Bearer <token>
```

---

## Changelog

- **v1.0.0** (2026-01-16): Initial release with 6 domain experts
