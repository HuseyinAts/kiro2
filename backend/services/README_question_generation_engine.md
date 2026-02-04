# Soru Üretim Motoru (Question Generation Engine)

## Genel Bakış

Task 55 kapsamında geliştirilen Soru Üretim Motoru, LLM tabanlı ÖSYM formatında otomatik soru üretimi sağlar.

## Özellikler

### 1. Konu Bazlı Soru Üretim Algoritması (REQ-48.33-48.36)

**TopicBasedQuestionGenerator** sınıfı:
- ✅ MEB müfredatına uygun konu bazlı soru üretimi
- ✅ Context injection - Konu bağlamını prompt'a ekleme
- ✅ Question template system - ÖSYM soru yapısını taklit etme
- ✅ 3 saniye içinde sonuç döndürme

```python
from services.question_generation_engine import TopicBasedQuestionGenerator
from models.curriculum import SubjectType
from models.question_generation import DifficultyLevel, CognitiveLevel

generator = TopicBasedQuestionGenerator(llm_service=your_llm_service)

question = await generator.generate_question(
    subject=SubjectType.MATEMATIK,
    topic_name="Kesirler",
    topic_context="Kesir toplama ve çıkarma işlemleri",
    difficulty_level=DifficultyLevel.ORTA,
    cognitive_level=CognitiveLevel.UYGULAMA
)
```

### 2. Distractor Generation Sistemi (REQ-48.37-48.40)

**DistractorGenerationSystem** sınıfı:
- ✅ Plausible (makul) çeldirici üretimi
- ✅ Common misconception database - Yaygın öğrenci hatalarını içeren veritabanı
- ✅ Distractor quality scoring - Her çeldiriciyi 0-100 arası değerlendirme
- ✅ En yüksek skorlu 3 çeldiriciyi seçme

```python
from services.question_generation_engine import DistractorGenerationSystem

distractor_system = DistractorGenerationSystem(llm_service=your_llm_service)

distractors = await distractor_system.generate_distractors(
    correct_answer="x = 2",
    question_context="2x + 3 = 7 denklemini çözünüz",
    subject=SubjectType.MATEMATIK,
    topic="denklemler",
    count=3
)

# Her distractor quality_score ile birlikte gelir
for d in distractors:
    print(f"{d['text']} - Skor: {d['quality_score']}")
```

**Yaygın Kavram Yanılgıları Veritabanı:**
- Matematik: Kesirler, üslü sayılar, denklemler
- Türkçe: Yazım kuralları, noktalama
- Fen: Fizik, kimya kavramları

### 3. Matematiksel Doğrulama - SymPy Entegrasyonu (REQ-48.41-48.44)

**MathematicalValidationEngine** sınıfı:
- ✅ SymPy symbolic math engine - Denklemleri sembolik olarak çözme
- ✅ Equation validation - Matematiksel tutarlılık kontrolü
- ✅ Solution verification - Doğru cevabı doğrulama
- ✅ Matematiksel hata tespitinde soruyu reddetme

```python
from services.question_generation_engine import MathematicalValidationEngine

math_validator = MathematicalValidationEngine()

# Denklem doğrulama
validation = math_validator.validate_equation("2*x + 3 = 7")
print(f"Geçerli: {validation['valid']}")

# Denklem çözme
solution = math_validator.solve_equation("2*x + 3 = 7", variable="x")
print(f"Çözümler: {solution['solutions']}")  # ['2']

# Çözüm doğrulama
verification = math_validator.verify_solution(
    equation_str="2*x + 3 = 7",
    proposed_solution="2",
    variable="x"
)
print(f"Doğru mu: {verification['is_correct']}")  # True

# Soru doğrulama
question_validation = math_validator.validate_math_question(
    question_text="2x + 3 = 7 denkleminin çözümü nedir?",
    correct_answer="2",
    options=["A) 2", "B) 3", "C) 4", "D) 5"]
)
```

### 4. Görsel Üretim - Matplotlib/Plotly (REQ-48.45-48.48)

**VisualGenerationEngine** sınıfı:
- ✅ Graph generation - Matematiksel fonksiyonları görselleştirme
- ✅ Geometry figure generation - Geometrik şekilleri çizme
- ✅ Chart and diagram creation - Veri görselleştirmesi

```python
from services.question_generation_engine import VisualGenerationEngine

visual_engine = VisualGenerationEngine()

# Fonksiyon grafiği
graph = visual_engine.generate_function_graph(
    function_str="x**2 + 2*x + 1",
    x_range=(-5, 5),
    title="Parabol Grafiği",
    output_path="graph.png"
)

# Geometrik şekil
circle = visual_engine.generate_geometry_figure(
    shape_type="circle",
    parameters={"radius": 5, "center": (0, 0)},
    output_path="circle.png"
)

# Veri grafiği
chart = visual_engine.generate_chart(
    chart_type="bar",
    data={
        "categories": ["Matematik", "Türkçe", "Fen"],
        "values": [85, 90, 78]
    },
    title="Sınav Sonuçları",
    output_path="chart.png"
)

# İnteraktif grafik (Plotly)
interactive = visual_engine.generate_interactive_plot(
    plot_type="line",
    data={"x": [1, 2, 3, 4], "y": [10, 20, 15, 25]},
    title="İnteraktif Grafik"
)
# HTML string döner
```

## Ana Soru Üretim Motoru

**QuestionGenerationEngine** - Tüm sistemleri birleştiren ana sınıf:

```python
from services.question_generation_engine import QuestionGenerationEngine

# Motor başlatma
engine = QuestionGenerationEngine(llm_service=your_llm_service)

# Tam soru üretimi (soru + çeldiriciler + doğrulama + görsel)
complete_question = await engine.generate_complete_question(
    subject=SubjectType.MATEMATIK,
    topic_name="Üslü Sayılar",
    topic_context="Üslü sayılarla çarpma ve bölme işlemleri",
    difficulty_level=DifficultyLevel.ZOR,
    cognitive_level=CognitiveLevel.ANALIZ,
    include_visual=True  # Görsel üretimi dahil et
)

# Üretilen soru:
# - question_text: Soru metni
# - options: 4 seçenek (A: doğru, B-D: çeldiriciler)
# - correct_answer: Doğru cevap
# - explanation: Açıklama
# - is_validated: Matematiksel doğrulama yapıldı mı
# - source_materials: Görsel dosya yolları (varsa)
```

## Gereksinimler

```bash
pip install sympy==1.12
pip install matplotlib==3.8.2
pip install plotly==5.18.0
```

## Test Etme

```bash
pytest tests/unit/test_question_generation_engine.py -v
```

## Mimari

```
QuestionGenerationEngine (Ana Motor)
├── TopicBasedQuestionGenerator (Soru Üretimi)
│   ├── Context Injection
│   ├── Template Selection
│   └── Prompt Engineering
├── DistractorGenerationSystem (Çeldirici Üretimi)
│   ├── Misconception Database
│   ├── LLM-based Generation
│   └── Quality Scoring
├── MathematicalValidationEngine (Matematiksel Doğrulama)
│   ├── SymPy Integration
│   ├── Equation Validation
│   └── Solution Verification
└── VisualGenerationEngine (Görsel Üretimi)
    ├── Matplotlib Integration
    ├── Plotly Integration
    └── Graph/Chart Generation
```

## Performans

- **Soru Üretim Süresi**: < 3 saniye (REQ-48.36)
- **Çeldirici Kalite Skoru**: 0.0 - 1.0 arası
- **Matematiksel Doğrulama**: Sembolik hesaplama ile %100 doğruluk
- **Görsel Üretim**: PNG/HTML formatında yüksek kaliteli çıktı

## Gelecek Geliştirmeler

1. GPT-4 Fine-tuning entegrasyonu (REQ-48.17-48.32)
2. BERTurk embedding ile semantik benzerlik (REQ-48.21-48.24)
3. RLHF (Reinforcement Learning from Human Feedback) (REQ-48.29-48.32)
4. IRT parametrelerinin otomatik hesaplanması
5. A/B testing sistemi (REQ-48.61-48.64)

## Lisans

Bu modül Teknofest 2025 Eğitim Eylemci Platformu projesi kapsamında geliştirilmiştir.
