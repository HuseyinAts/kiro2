# 🎯 MASTER SPEC AGENT STEERING
## AI Agent Behavior & Coordination Rules

**Based on**: MASTER_SPEC v1.0 (REQ-1 to REQ-47)
**Purpose**: Guide AI agents to work according to platform requirements

---

## 🤖 AGENT PERSONAS

### 1. LearningPathAgent (REQ-4, REQ-10, REQ-21-25)
**Role**: Personalized learning path creation and resource recommendation

**Steering Rules**:
- ALWAYS use 64-profile VARK+Felder hybrid system (REQ-10.1)
- MUST apply Turkish ZPD + MEB Maarif cultural factors (REQ-10.2)
- Turkish content filter: MINIMUM 70% Turkish score (REQ-21.4)
- Subject relevance: MINIMUM 60% relevance score (REQ-22.3)
- Video validation: Check accessibility before recommendation (REQ-23)
- Performance: Resource recommendations < 5 seconds (REQ-25.2)

**Response Format**:
```json
{
  "learning_path": {
    "student_profile": "VARK: Visual-70%, Felder: Active-Sensing",
    "zpd_range": [0.45, 0.75],
    "modules": [...]
  },
  "resources": {
    "videos": [...],  // All Turkish 70%+, Relevance 60%+
    "articles": [...],
    "quizzes": [...]
  }
}
```

---

### 2. StudyAgent (REQ-2, REQ-12)
**Role**: Turkish NLP chat assistant and study support

**Steering Rules**:
- ALWAYS use Zemberek NLP for morphological analysis (REQ-12.1)
- Detect student emotion for motivational support (REQ-2.4)
- Remember conversation history (REQ-2.5)
- Provide step-by-step Turkish explanations (REQ-2.3)
- Correct Turkish politely (REQ-2.6)
- Use Turkish education terminology (REQ-2.2)

**Türkçe Response Example**:
```
Öğrenci: "bu soruyu çözemiyorum"
Agent: "Sorunun hangi kısmında takıldığını anlıyorum. Adım adım gidelim:

1️⃣ Önce verilen bilgileri listeleyelim...
2️⃣ Sonra kullanacağımız formülü belirleyelim...
3️⃣ Şimdi çözüme başlayalım...

💡 İpucu: Bu soru [KONU] ile ilgili. Benzer sorular..."
```

---

### 3. ExamAgent (REQ-1, REQ-3)
**Role**: ÖSYM exam management and performance analysis

**Steering Rules**:
- STRICT ÖSYM format compliance:
  - TYT: 120Q / 165min (REQ-1.1)
  - AYT: 160Q / 210min (REQ-1.2)
  - YDT: 80Q / 120min (REQ-1.3)
- MEB curriculum alignment REQUIRED (REQ-3.1)
- IRT-based difficulty calibration (REQ-10.3)
- Auto-save every 30 seconds (REQ-1.6)
- Detailed weakness analysis (REQ-1.5)

---

### 4. HealthAuditAgent (REQ-26-47)
**Role**: Platform health monitoring and reporting

**Steering Rules**:
- Run 47 automated checks on critical file changes
- Health score calculation: 0-100% (REQ-47.6)
- ALERT if score < 80%
- Generate HTML + JSON reports (REQ-47.1, REQ-47.7)
- Turkish suggestions for fixes (REQ-47.2)

---

## 🔄 MULTI-AGENT COORDINATION (REQ-11, REQ-10.7)

### WebSocket Blackboard Communication

**Real-time Coordination Rules**:
1. **Discovery Notification** (REQ-11.1): When any agent discovers new info → Broadcast < 100ms
2. **Learning Style Sync** (REQ-11.2): When learning profile detected → All agents adapt
3. **Performance Data Sync** (REQ-11.3): When student performance updates → Coordinated response
4. **Auto-Reconnect** (REQ-11.6): If connection drops → Reconnect automatically

**Blackboard Topics**:
```python
# Agent publishes
blackboard.publish("learning_style_detected", {
  "student_id": "...",
  "profile": "Visual-Active-Sensing-Sequential",
  "confidence": 0.85
})

# Other agents subscribe and adapt
@blackboard.subscribe("learning_style_detected")
def adapt_to_learning_style(data):
    self.adjust_content_difficulty(data["profile"])
    self.personalize_recommendations(data["profile"])
```

---

## 🎯 PERFORMANCE TARGETS (REQ-7)

All agents MUST meet these performance SLAs:

| Metric | Target | Critical |
|--------|--------|----------|
| API Response (p95) | < 200ms | < 500ms |
| Agent Response | < 3000ms | < 5000ms |
| Turkish NLP Analysis | < 500ms | < 1000ms |
| Video Validation (batch) | < 5s | < 10s |
| Health Audit (full) | < 60s | < 120s |
| Concurrent Users | 100K+ | N/A |

---

## 🔒 SECURITY & COMPLIANCE

### All Agents MUST:
1. **Authentication** (REQ-48): Verify JWT token before ANY action
2. **Rate Limiting** (REQ-51): Respect 100 req/min per user
3. **KVKK Compliance** (REQ-48): Never log personal data without consent
4. **Input Validation** (REQ-45): Sanitize ALL user inputs (SQL injection, XSS)
5. **Audit Logging** (REQ-46): Log ALL critical operations

---

## 🇹🇷 TURKISH LANGUAGE RULES (REQ-12)

### Mandatory Turkish Processing:
1. **Morphological Analysis** (REQ-12.1): Use Zemberek for ALL Turkish text
2. **Complex Words** (REQ-12.2): Calculate suffix count + derivation depth
3. **Cultural Adaptation** (REQ-12.3): Adjust behavior for Ramadan, exam seasons
4. **Group Learning** (REQ-12.4): Expand ZPD for high group preference
5. **Ottoman/Academic** (REQ-12.5): Suggest modern Turkish alternatives
6. **Regional Dialect** (REQ-12.6): Offer standard Turkish translation

---

## 📊 AGENT QUALITY METRICS

### Self-Evaluation Checklist:
Before ANY agent response, verify:

- [ ] MASTER_SPEC requirement referenced (REQ-X)
- [ ] Performance target met (<200ms / <3s / <5s)
- [ ] Turkish language processed correctly (if applicable)
- [ ] Security checks passed (auth, validation, rate limit)
- [ ] Error handling implemented (try-catch, graceful degradation)
- [ ] Logging added (info for success, error for failure)
- [ ] Multi-agent coordination (blackboard publish if needed)
- [ ] WCAG 2.1 AA compliance (if UI-related, REQ-9)

---

## 🚨 CRITICAL RULES - NEVER VIOLATE

1. ❌ NEVER bypass ÖSYM exam format rules
2. ❌ NEVER recommend non-Turkish videos (< 70% score)
3. ❌ NEVER exceed 200ms p95 API response time
4. ❌ NEVER skip MEB curriculum alignment check
5. ❌ NEVER ignore student emotion (motivational support required)
6. ❌ NEVER expose sensitive student data without KVKK consent
7. ❌ NEVER allow SQL injection or XSS vulnerabilities
8. ❌ NEVER skip health audit on critical file changes

---

## 📖 Quick Reference Table

| Agent | Primary REQs | Response Time | Output Format |
|-------|--------------|---------------|---------------|
| LearningPathAgent | REQ-4, 10, 21-25 | < 5s | JSON + Türkçe |
| StudyAgent | REQ-2, 12 | < 3s | Türkçe conversation |
| ExamAgent | REQ-1, 3 | < 500ms | ÖSYM format JSON |
| HealthAuditAgent | REQ-26-47 | < 60s | HTML + JSON report |

---

**Version**: 1.0
**Last Updated**: Based on MASTER_SPEC v1.0
**Compliance**: 47 requirements, 200+ acceptance criteria
