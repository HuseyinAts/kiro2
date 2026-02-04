# NLP Model Training Pipeline

Türkiye Üniversite Sınavları Hazırlık Platformu için NLP model eğitim altyapısı.

## Modüller

### 1. GPT-4 Fine-tuning Service
OpenAI GPT-4 fine-tuning altyapısı - ÖSYM soru üretimi için.

**Requirements**: REQ-48.17-48.20

**Özellikler**:
- OpenAI fine-tuning API entegrasyonu
- Training data preparation (ÖSYM formatı)
- Hyperparameter tuning
- Model evaluation metrics (BLEU, ROUGE, BERTScore)

**Kullanım**:
```python
from services.nlp_training import GPT4FineTuningService

# Service başlat
service = GPT4FineTuningService(api_key="your-api-key")

# Training data hazırla
questions = [
    {
        "subject": "Matematik",
        "topic": "Türev",
        "difficulty": "orta",
        "bloom_level": "uygulama",
        "stem": "f(x) = x² + 3x fonksiyonunun türevi nedir?",
        "options": ["2x + 3", "x + 3", "2x", "3x"],
        "correct_answer": 0,
        "explanation": "Türev kurallarına göre..."
    }
]

file_path = service.prepare_training_data(questions)

# Dosyayı yükle
file_id = service.upload_training_file(file_path)

# Fine-tuning başlat
job_id = service.start_fine_tuning(file_id)

# Tamamlanmasını bekle
model_id = service.wait_for_completion(job_id)

# Model değerlendir
metrics = service.evaluate_model(model_id, test_questions)
print(f"BLEU: {metrics.bleu_score:.4f}, ROUGE: {metrics.rouge_score:.4f}")
```

### 2. BERTurk Embedding Service
Türkçe pre-trained BERT modeli ile sentence embedding ve semantic similarity.

**Requirements**: REQ-48.21-48.24

**Özellikler**:
- BERTurk model loading
- Sentence embedding generation (768 boyutlu)
- Semantic similarity calculation (cosine similarity)
- Similarity score (0-1 arası)

**Kullanım**:
```python
from services.nlp_training import BERTurkEmbeddingService

# Service başlat
service = BERTurkEmbeddingService()

# Embedding oluştur
result = service.generate_embedding("Bu bir test cümlesidir.")
print(f"Dimension: {result.dimension}")  # 768

# Semantic similarity hesapla
similarity = service.calculate_similarity(
    "Matematik sorusu",
    "Fizik sorusu"
)
print(f"Similarity: {similarity:.4f}")  # 0-1 arası

# Batch similarity
similarities = service.calculate_batch_similarities(
    query_text="Türev sorusu",
    candidate_texts=["İntegral sorusu", "Limit sorusu", "Türev uygulaması"],
    top_k=2
)
for text, score in similarities:
    print(f"{text}: {score:.4f}")
```

### 3. T5/BART Generation Service
Türkçe soru üretimi ve paraphrasing için T5 ve BART modelleri.

**Requirements**: REQ-48.25-48.28

**Özellikler**:
- T5 model for Turkish question generation
- BART model for paraphrasing
- Beam search optimization (5 beam)
- ÖSYM format compliance (95%+)

**Kullanım**:
```python
from services.nlp_training import T5BARTGenerationService

# Service başlat
service = T5BARTGenerationService()

# Soru üret
questions = service.generate_question_t5(
    topic="Türev",
    subject="Matematik",
    difficulty="orta",
    num_beams=5
)

for q in questions:
    print(f"Soru: {q.generated_text}")
    print(f"ÖSYM Compliance: {q.score:.2%}")

# Seçenekli soru üret
question_with_options = service.generate_question_with_options(
    topic="Türev",
    subject="Matematik",
    num_options=4
)

print(f"Soru: {question_with_options['question']}")
print(f"Seçenekler: {question_with_options['options']}")
print(f"Doğru Cevap: {question_with_options['correct_answer']}")

# Paraphrasing
paraphrases = service.paraphrase_bart(
    text="Bu soru çok zor.",
    num_return_sequences=3
)

for p in paraphrases:
    print(f"Paraphrase: {p.generated_text}")
```

### 4. RLHF Training Service
Reinforcement Learning from Human Feedback - Soru kalitesi iyileştirme.

**Requirements**: REQ-48.29-48.32

**Özellikler**:
- RLHF training loop with human feedback
- Reward model training (0-100 scoring)
- PPO algorithm implementation
- Model performance improvement (20%+)

**Kullanım**:
```python
from services.nlp_training import RLHFTrainingService
from services.nlp_training.rlhf_training import FeedbackType

# Service başlat
service = RLHFTrainingService()

# İnsan geri bildirimi topla
feedback = service.collect_human_feedback(
    question_id="q123",
    question_text="f(x) = x² türevi nedir?",
    quality_score=85.0,
    feedback_type=FeedbackType.POSITIVE,
    comments="İyi soru, açık ve net",
    reviewer_id="reviewer_1"
)

# Reward model eğit
import torch
embeddings = torch.randn(100, 768)  # 100 soru embedding
scores = torch.rand(100) * 100  # Kalite skorları

metrics = service.train_reward_model(embeddings, scores, epochs=10)
print(f"Training Loss: {metrics['final_loss']:.4f}")

# Kalite tahmini
test_embedding = torch.randn(768)
predicted_quality = service.predict_quality(test_embedding)
print(f"Predicted Quality: {predicted_quality:.2f}/100")

# RLHF loop çalıştır
initial_questions = [{"quality_score": 50.0} for _ in range(100)]
metrics_list = service.run_rlhf_loop(
    initial_questions=initial_questions,
    num_iterations=10
)

# Performance improvement kontrolü
final_improvement = metrics_list[-1].performance_improvement
print(f"Performance Improvement: {final_improvement:.2f}%")

# Feedback istatistikleri
stats = service.get_feedback_statistics()
print(f"Total Feedback: {stats['total_feedback']}")
print(f"Avg Quality: {stats['avg_quality_score']:.2f}")
```

## Gereksinimler

```bash
pip install openai transformers torch numpy scikit-learn nltk rouge-score
```

## Mimari

```
nlp_training/
├── __init__.py
├── gpt4_finetuning.py      # GPT-4 fine-tuning
├── berturk_embedding.py    # BERTurk embeddings
├── t5_bart_generation.py   # T5/BART generation
├── rlhf_training.py         # RLHF training
└── README.md
```

## Test

```bash
# Unit tests
pytest tests/unit/test_nlp_training.py

# Integration tests
pytest tests/integration/test_nlp_training_integration.py
```

## Performans

- **GPT-4 Fine-tuning**: ~3-5 saat (1000 örnek)
- **BERTurk Embedding**: ~10ms per sentence (CPU), ~2ms (GPU)
- **T5/BART Generation**: ~500ms per question (beam=5)
- **RLHF Training**: ~1-2 saat (10 iteration)

## Notlar

- GPU kullanımı önerilir (CUDA)
- OpenAI API key gereklidir (GPT-4 fine-tuning için)
- Minimum 8GB RAM önerilir
- BERTurk model ~500MB disk alanı
- T5/BART modeller ~2GB disk alanı

## Lisans

MIT License
