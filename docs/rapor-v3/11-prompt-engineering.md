# BÖLÜM 11: Prompt Engineering

## 11.1 Alex Albert Hakkında

### Pozisyon ve Geçmiş

**Unvan:** Head of Claude Relations, Anthropic

**Önemli:** 2023'te Anthropic'e "ilk prompt engineer" olarak katıldı

**Katkılar:**
- Claude'un official prompting guide'ının yazarı
- Developer experience ve best practices
- Anthropic documentation lead

### Kaynaklar

- Anthropic Prompt Engineering Guide
- Anthropic Developer Documentation
- Claude Best Practices Blog

---

## 11.2 XML Tag Kullanımı

### Neden XML?

Claude, XML tag'lerini diğer formatlardan (JSON, YAML, Markdown) daha iyi parse ediyor:
- Yapısal ayrım net
- Nested content destekli
- Tag referansı kolay
- Output'ta da kullanılabilir

### Temel Tag'ler

| Tag | Kullanım | Örnek |
|-----|----------|-------|
| `<instructions>` | Talimatlar | `<instructions>Kodu incele</instructions>` |
| `<context>` | Bağlam bilgisi | `<context>Bu bir YKS projesi</context>` |
| `<example>` | Örnekler | `<example>Input: X, Output: Y</example>` |
| `<document>` | Belgeler | `<document>Spesifikasyon...</document>` |
| `<thinking>` | Düşünme süreci | `<thinking>Önce analiz...</thinking>` |
| `<answer>` | Final cevap | `<answer>Sonuç...</answer>` |
| `<constraints>` | Kısıtlamalar | `<constraints>Max 100 satır</constraints>` |
| `<format>` | Çıktı formatı | `<format>JSON olarak döndür</format>` |
| `<persona>` | Rol tanımı | `<persona>Senior Python developer</persona>` |

### Kullanım Prensipleri

**Prensip 1: Tutarlılık**
```xml
<!-- DOĞRU: Tutarlı tag isimleri -->
<task>
  <description>Soru üret</description>
  <requirements>UTF-8 encoding</requirements>
</task>

<!-- YANLIŞ: Tutarsız -->
<Task>
  <desc>Soru üret</desc>
  <requirement>UTF-8</requirement>
</Task>
```

**Prensip 2: Hiyerarşi**
```xml
<task>
  <context>
    <project>KIRO2</project>
    <module>Question Generator</module>
  </context>
  <instructions>
    <step>1. Konuyu analiz et</step>
    <step>2. Soru oluştur</step>
    <step>3. Doğrula</step>
  </instructions>
  <constraints>
    <rule>Zorluk 1-5 arası</rule>
    <rule>UTF-8 encoding</rule>
  </constraints>
</task>
```

**Prensip 3: Referans**
```xml
<context>
  YKS matematik soruları için şu kurallar geçerli:
  ...
</context>

<instructions>
  <context> tag'indeki kurallara göre bir limit sorusu üret.
</instructions>
```

**Prensip 4: Output Structure**
```xml
<instructions>
  Analiz sonucunu şu formatta döndür:
</instructions>

<output_format>
  <analysis>Analiz metni</analysis>
  <issues>Bulunan sorunlar</issues>
  <recommendations>Öneriler</recommendations>
</output_format>
```

---

## 11.3 Few-Shot Examples

### Optimal Sayı

**Genel kural:** 3-5 diverse örnek optimal

| Görev Karmaşıklığı | Örnek Sayısı |
|-------------------|--------------|
| Basit (format dönüşümü) | 1-2 |
| Orta (analiz, sınıflandırma) | 3-4 |
| Karmaşık (yaratıcı, çok adımlı) | 5-7 |

### Örnek Yapısı

```xml
<examples>
  <example id="1">
    <input>
      Konu: Limit
      Zorluk: 3
      Tip: Hesaplama
    </input>
    <output>
      {
        "question_text": "$$\\lim_{x \\to 0} \\frac{\\sin x}{x}$$ limitinin değeri nedir?",
        "options": {
          "A": "0",
          "B": "1",
          "C": "∞",
          "D": "-1",
          "E": "Tanımsız"
        },
        "correct_answer": "B",
        "difficulty_level": 3
      }
    </output>
    <reasoning>
      Bu klasik bir limit sorusu. L'Hôpital veya özel limit bilgisi gerektirir.
      Zorluk 3 çünkü formül bilgisi yeterli.
    </reasoning>
  </example>
  
  <example id="2">
    <input>
      Konu: Türev
      Zorluk: 4
      Tip: Uygulama
    </input>
    <output>
      {
        "question_text": "f(x) = x³ - 3x² + 2x fonksiyonunun yerel maksimum noktası kaçtır?",
        ...
      }
    </output>
    <reasoning>
      Türev alıp sıfıra eşitleme ve ikinci türev testi gerektirir.
      Çok adımlı olduğu için zorluk 4.
    </reasoning>
  </example>
</examples>
```

### Örnek Seçimi Best Practices

1. **Diversity:** Farklı senaryoları kapsa
2. **Edge cases:** Sınır durumları dahil et
3. **Common errors:** Yaygın hataları göster
4. **Gradual complexity:** Basitten karmaşığa

```xml
<!-- DOĞRU: Diverse örnekler -->
<examples>
  <example>Basit hesaplama</example>
  <example>Karmaşık problem</example>
  <example>Edge case (sıfıra bölme)</example>
  <example>Yaygın hata senaryosu</example>
</examples>

<!-- YANLIŞ: Benzer örnekler -->
<examples>
  <example>Limit hesapla 1</example>
  <example>Limit hesapla 2</example>
  <example>Limit hesapla 3</example>
</examples>
```

---

## 11.4 Chain-of-Thought (CoT)

### Ne Zaman Kullanılmalı?

| Görev Tipi | CoT Gerekli? |
|------------|--------------|
| Basit fact retrieval | ❌ |
| Format dönüşümü | ❌ |
| Matematik problemi | ✅ |
| Mantıksal analiz | ✅ |
| Çok adımlı planlama | ✅ |
| Debugging | ✅ |
| Karmaşık karar verme | ✅ |

### CoT Prompt Yapısı

```xml
<instructions>
  Bu problemi adım adım çöz.
  
  Düşünme sürecini <thinking> tag'inde göster.
  Final cevabı <answer> tag'inde ver.
</instructions>

<problem>
  f(x) = x² - 4x + 3 fonksiyonunun kökleri toplamı kaçtır?
</problem>

<expected_output>
  <thinking>
    1. Bu bir ikinci derece denklem: ax² + bx + c formunda
    2. a = 1, b = -4, c = 3
    3. Vieta formüllerine göre köklerin toplamı = -b/a
    4. Toplam = -(-4)/1 = 4
  </thinking>
  
  <answer>4</answer>
</expected_output>
```

### KIRO2 İçin CoT Uygulaması

```xml
<instructions>
  Matematik sorusu üretirken şu adımları izle:
</instructions>

<thinking_process>
  1. Konu analizi: Hangi kavramlar gerekli?
  2. Zorluk belirleme: Kaç adım, hangi beceriler?
  3. Soru tasarımı: Net, anlaşılır metin
  4. Seçenek oluşturma: Mantıklı çeldiriciler
  5. Doğrulama: Çözümün doğruluğu
</thinking_process>

<example>
  <input>Konu: İntegral, Zorluk: 4</input>
  
  <thinking>
    1. Konu analizi: Belirli integral hesaplama gerekiyor.
    2. Zorluk 4: Değişken dönüşümü veya parçalı integral gereksin.
    3. Soru: ∫₀¹ x·eˣ dx hesaplat - parçalı integral gerektirir.
    4. Çeldiriciler: Yaygın hatalardan türet:
       - Parçalı integral yanlış uygulama
       - Sınır değerleri unutma
       - İşaret hatası
    5. Doğrulama: Parçalı integral ile çözüm = 1
  </thinking>
  
  <answer>
    {
      "question_text": "$$\\int_0^1 x \\cdot e^x \\, dx$$ integralinin değeri kaçtır?",
      "options": {"A": "1", "B": "e-1", "C": "e", "D": "2", "E": "e-2"},
      "correct_answer": "A"
    }
  </answer>
</example>
```

---

## 11.5 Prefill Tekniği

### Tanım

Assistant mesajının başına metin ekleyerek Claude'u belirli bir formatta yanıtlamaya zorlamak.

### API Kullanımı

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Analyze this code for bugs."
        },
        {
            "role": "assistant",
            "content": "<analysis>"  # Prefill
        }
    ]
)

# Claude <analysis> ile başlayarak devam eder
```

### Claude Code'da Kullanım

Claude Code'da prefill doğrudan desteklenmez, ama prompt'ta isteyebilirsiniz:

```
Respond starting with <analysis> tag. Do not include any text before it.

<analysis>
```

### Prefill Kullanım Senaryoları

| Senaryo | Prefill |
|---------|---------|
| JSON output | `{` |
| XML output | `<response>` |
| Code output | `\`\`\`python` |
| List output | `1.` |
| Structured | `## Analysis` |

### KIRO2 Örneği

```python
# Soru üretimi için prefill
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    system="You are a YKS question generator.",
    messages=[
        {
            "role": "user",
            "content": "Generate a calculus question about limits."
        },
        {
            "role": "assistant",
            "content": '{"question_id": "MAT-'  # JSON prefill
        }
    ]
)
```

---

## 11.6 System Prompt Best Practices

### Yapı

```xml
<system_prompt>
  <role>
    You are a [specific role] with expertise in [domain].
  </role>
  
  <context>
    You are working on [project/task].
    The user is [user description].
  </context>
  
  <guidelines>
    <guideline>Always [behavior]</guideline>
    <guideline>Never [behavior]</guideline>
  </guidelines>
  
  <output_format>
    Respond in [format] with [structure].
  </output_format>
</system_prompt>
```

### KIRO2 System Prompt

```
You are an expert educational content creator specializing in Turkish university entrance exam (YKS) preparation.

CONTEXT:
- Project: KIRO2 - AI-powered YKS preparation platform
- Target: Turkish high school students preparing for TYT and AYT exams
- Language: Turkish (questions), English (code/technical)

EXPERTISE AREAS:
- Mathematics: Calculus, algebra, geometry, trigonometry
- Physics: Mechanics, electricity, optics, modern physics
- Turkish: Grammar, literature, comprehension

GUIDELINES:
- Generate questions aligned with MEB (Ministry of Education) curriculum
- Use LaTeX for mathematical notation: $...$ for inline, $$...$$ for display
- Ensure UTF-8 encoding for Turkish characters (ğ, ü, ş, ı, ö, ç)
- Include detailed solution steps
- Create plausible distractors based on common student errors

OUTPUT FORMAT:
- JSON format for questions
- Include all required fields: question_id, question_text, options, correct_answer, difficulty_level, topic_tags, explanation
- Validate against schema before returning

QUALITY STANDARDS:
- Difficulty level 1-5 must match content complexity
- No duplicate or near-duplicate questions
- No answer hints in question text
- Balanced option lengths
```

---

## 11.7 Claude-Specific Techniques

### Claude'un Güçlü Yönleri

| Özellik | Optimizasyon |
|---------|--------------|
| XML parsing | Yapılandırılmış prompt'lar için XML kullan |
| Long context | 200K token'ı verimli kullan |
| Instruction following | Açık, spesifik talimatlar ver |
| Multilingual | Türkçe ve İngilizce karıştır |
| Code understanding | Kod örnekleri ile açıkla |

### Kaçınılması Gerekenler

**❌ Gereksiz hatırlatmalar:**
```
Remember, you are an AI assistant created by Anthropic...
```

**❌ Aşırı kibar dil:**
```
Please, if you would be so kind, could you perhaps consider...
```

**❌ Negatif talimatlar (mümkünse):**
```
Don't use bullet points.  <!-- Daha zor takip edilir -->
Use paragraphs.           <!-- Daha kolay takip edilir -->
```

**❌ Belirsiz talimatlar:**
```
Write good code.          <!-- Belirsiz -->
Write Python code with type hints, docstrings, and error handling.  <!-- Spesifik -->
```

### Pozitif vs Negatif Talimatlar

| Negatif (Kaçın) | Pozitif (Tercih Et) |
|-----------------|---------------------|
| Don't be verbose | Be concise |
| Don't use jargon | Use simple language |
| Don't forget X | Always include X |
| Avoid errors | Ensure accuracy |

---

## 11.8 Prompt Templates

### KIRO2 Soru Üretimi Template

```xml
<system>
You are KIRO2 Question Generator, an expert in creating YKS exam questions.
</system>

<task>
Generate a {subject} question for {exam_type} exam.
</task>

<parameters>
  <topic>{topic}</topic>
  <subtopic>{subtopic}</subtopic>
  <difficulty>{difficulty}</difficulty>
  <question_type>{question_type}</question_type>
</parameters>

<constraints>
  - Difficulty must match complexity (see scale below)
  - Use LaTeX for math: $inline$ or $$display$$
  - UTF-8 encoding for Turkish characters
  - 5 options (A-E), exactly one correct
  - Include detailed solution steps
</constraints>

<difficulty_scale>
  1: Very Easy - Direct formula application
  2: Easy - Single-step problem
  3: Medium - Multi-step, standard approach
  4: Hard - Requires insight or multiple concepts
  5: Very Hard - Competition level, creative solution needed
</difficulty_scale>

<output_format>
Return a JSON object with these fields:
{
  "question_id": "string",
  "question_text": "string (LaTeX allowed)",
  "options": {"A": "", "B": "", "C": "", "D": "", "E": ""},
  "correct_answer": "A|B|C|D|E",
  "difficulty_level": 1-5,
  "topic_tags": ["string"],
  "subtopic": "string",
  "explanation": "string",
  "solution_steps": ["string"],
  "estimated_time_seconds": number,
  "bloom_level": 1-6
}
</output_format>

<examples>
  <!-- 2-3 relevant examples here -->
</examples>
```

### KIRO2 Code Review Template

```xml
<system>
You are KIRO2 Code Reviewer, specialized in Python and educational technology.
</system>

<task>
Review the following code for quality, security, and best practices.
</task>

<code>
{code_content}
</code>

<review_criteria>
  <category name="code_quality">
    - Type hints present and correct
    - Docstrings (Google style)
    - Error handling
    - Code organization
  </category>
  
  <category name="security">
    - Input validation
    - SQL injection prevention
    - Sensitive data handling
  </category>
  
  <category name="performance">
    - Algorithm efficiency
    - Database query optimization
    - Memory usage
  </category>
  
  <category name="maintainability">
    - Naming conventions
    - Single responsibility
    - DRY principle
  </category>
</review_criteria>

<output_format>
{
  "summary": "Overall assessment",
  "score": 0-100,
  "categories": {
    "code_quality": {"score": 0-25, "issues": []},
    "security": {"score": 0-25, "issues": []},
    "performance": {"score": 0-25, "issues": []},
    "maintainability": {"score": 0-25, "issues": []}
  },
  "critical_issues": [],
  "recommendations": []
}
</output_format>
```

---

## 11.9 Özet

### Checklist

- [ ] XML tag'ler tutarlı kullanılıyor
- [ ] 3-5 diverse few-shot örnek var
- [ ] Karmaşık görevlerde CoT kullanılıyor
- [ ] Prefill ile output format zorlanıyor
- [ ] System prompt yapılandırılmış
- [ ] Pozitif talimatlar tercih ediliyor

### Quick Reference

| Teknik | Ne Zaman |
|--------|----------|
| XML tags | Yapılandırılmış input/output |
| Few-shot | Yeni format öğretme |
| CoT | Karmaşık reasoning |
| Prefill | Output format zorlama |
| System prompt | Global davranış |

### Metrikler

| Metrik | Hedef |
|--------|-------|
| Instruction following rate | > 95% |
| Output format compliance | > 98% |
| First-attempt success | > 85% |

---

**Önceki Bölüm:** [10 - Reward Hacking ve Güvenlik](./10-reward-hacking-guvenlik.md)  
**Sonraki Bölüm:** [12 - MCP Entegrasyonları](./12-mcp-entegrasyonlari.md)
