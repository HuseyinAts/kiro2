"""
NLP Training Pipeline - Example Usage
Tüm servislerin kullanım örnekleri.
"""

import os
import torch
from services.nlp_training import (
    GPT4FineTuningService,
    BERTurkEmbeddingService,
    T5BARTGenerationService,
    RLHFTrainingService,
)
from services.nlp_training.rlhf_training import FeedbackType


def example_gpt4_finetuning():
    """GPT-4 Fine-tuning örneği"""
    print("\n=== GPT-4 Fine-tuning Example ===\n")

    # API key (environment variable'dan al)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return

    service = GPT4FineTuningService(api_key=api_key)

    # Örnek sorular
    questions = [
        {
            "subject": "Matematik",
            "topic": "Türev",
            "difficulty": "orta",
            "bloom_level": "uygulama",
            "stem": "f(x) = x² + 3x fonksiyonunun türevi nedir?",
            "options": ["2x + 3", "x + 3", "2x", "3x"],
            "correct_answer": 0,
            "explanation": "Türev kurallarına göre, x²'nin türevi 2x, 3x'in türevi 3'tür.",
        },
        {
            "subject": "Fizik",
            "topic": "Hareket",
            "difficulty": "kolay",
            "bloom_level": "bilgi",
            "stem": "Hız nedir?",
            "options": ["Yol/Zaman", "Zaman/Yol", "Yol*Zaman", "Yol-Zaman"],
            "correct_answer": 0,
            "explanation": "Hız, birim zamanda alınan yoldur.",
        },
    ]

    # Training data hazırla
    print("📝 Preparing training data...")
    file_path = service.prepare_training_data(questions, "training_data.jsonl")
    print(f"✓ Training data saved: {file_path}")

    # Dosyayı yükle
    print("\n📤 Uploading training file...")
    file_id = service.upload_training_file(file_path)
    print(f"✓ File uploaded: {file_id}")

    # Fine-tuning başlat
    print("\n🚀 Starting fine-tuning...")
    job_id = service.start_fine_tuning(file_id, suffix="osym-demo")
    print(f"✓ Fine-tuning job started: {job_id}")

    # Durum kontrolü
    print("\n📊 Checking status...")
    status = service.check_training_status(job_id)
    print(f"Status: {status['status']}")

    print("\n✓ GPT-4 fine-tuning example completed")


def example_berturk_embedding():
    """BERTurk Embedding örneği"""
    print("\n=== BERTurk Embedding Example ===\n")

    service = BERTurkEmbeddingService()

    # Tek embedding
    print("📝 Generating single embedding...")
    result = service.generate_embedding("Bu bir Türkçe test cümlesidir.")
    print(f"✓ Embedding dimension: {result.dimension}")
    print(f"✓ Model: {result.model_name}")

    # Semantic similarity
    print("\n🔍 Calculating semantic similarity...")
    text1 = "Matematik türev sorusu"
    text2 = "Fizik hareket sorusu"
    text3 = "Matematik türev uygulaması"

    sim12 = service.calculate_similarity(text1, text2)
    sim13 = service.calculate_similarity(text1, text3)

    print(f"'{text1}' vs '{text2}': {sim12:.4f}")
    print(f"'{text1}' vs '{text3}': {sim13:.4f}")

    # Batch similarity
    print("\n📊 Batch similarity calculation...")
    query = "Türev sorusu"
    candidates = [
        "İntegral sorusu",
        "Limit sorusu",
        "Türev uygulaması",
        "Fizik hareket",
        "Türev hesaplama",
    ]

    similarities = service.calculate_batch_similarities(query, candidates, top_k=3)
    print(f"\nTop 3 similar to '{query}':")
    for text, score in similarities:
        print(f"  {text}: {score:.4f}")

    # Clustering
    print("\n🎯 Text clustering...")
    texts = [
        "Matematik türev",
        "Matematik integral",
        "Fizik hareket",
        "Fizik kuvvet",
        "Kimya reaksiyon",
        "Kimya element",
    ]

    clusters = service.cluster_texts(texts, n_clusters=3)
    print("\nClusters:")
    for cluster_id, cluster_texts in clusters.items():
        print(f"  Cluster {cluster_id}: {cluster_texts}")

    print("\n✓ BERTurk embedding example completed")


def example_t5_bart_generation():
    """T5/BART Generation örneği"""
    print("\n=== T5/BART Generation Example ===\n")

    service = T5BARTGenerationService()

    # T5 soru üretimi
    print("📝 Generating question with T5...")
    questions = service.generate_question_t5(
        topic="Türev",
        subject="Matematik",
        difficulty="orta",
        num_beams=5,
        num_return_sequences=2,
    )

    print(f"\nGenerated {len(questions)} questions:")
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. {q.generated_text[:100]}...")
        print(f"   ÖSYM Compliance: {q.score:.2%}")

    # Seçenekli soru
    print("\n📋 Generating question with options...")
    question_with_options = service.generate_question_with_options(
        topic="Türev", subject="Matematik", difficulty="orta", num_options=4
    )

    print(f"\nSoru: {question_with_options['question'][:100]}...")
    print("Seçenekler:")
    for i, option in enumerate(question_with_options["options"]):
        marker = "✓" if i == question_with_options["correct_answer"] else " "
        print(f"  {marker} {chr(65+i)}) {option[:50]}...")
    print(f"ÖSYM Compliance: {question_with_options['osym_compliance']:.2%}")

    # BART paraphrasing
    print("\n🔄 Paraphrasing with BART...")
    text = "Bu soru çok zor ve karmaşık."
    paraphrases = service.paraphrase_bart(text, num_return_sequences=3)

    print(f"\nOriginal: {text}")
    print("Paraphrases:")
    for i, p in enumerate(paraphrases, 1):
        print(f"  {i}. {p.generated_text}")

    # Beam search optimization
    print("\n⚙️  Optimizing beam search...")
    optimal_beams, results = service.optimize_beam_search(
        text="Test cümlesi", num_beams_list=[3, 5, 7]
    )
    print(f"Optimal beam count: {optimal_beams}")

    print("\n✓ T5/BART generation example completed")


def example_rlhf_training():
    """RLHF Training örneği"""
    print("\n=== RLHF Training Example ===\n")

    service = RLHFTrainingService()

    # İnsan geri bildirimi topla
    print("📝 Collecting human feedback...")
    feedbacks = [
        {
            "question_id": "q1",
            "question_text": "f(x) = x² türevi nedir?",
            "quality_score": 85.0,
            "feedback_type": FeedbackType.POSITIVE,
            "comments": "İyi soru, açık ve net",
        },
        {
            "question_id": "q2",
            "question_text": "Hız nedir?",
            "quality_score": 70.0,
            "feedback_type": FeedbackType.NEUTRAL,
            "comments": "Basit ama yeterli",
        },
        {
            "question_id": "q3",
            "question_text": "Karmaşık soru...",
            "quality_score": 40.0,
            "feedback_type": FeedbackType.NEGATIVE,
            "comments": "Çok karmaşık ve anlaşılmaz",
        },
    ]

    for fb in feedbacks:
        service.collect_human_feedback(
            question_id=fb["question_id"],
            question_text=fb["question_text"],
            quality_score=fb["quality_score"],
            feedback_type=fb["feedback_type"],
            comments=fb["comments"],
            reviewer_id="demo_reviewer",
        )

    print(f"✓ Collected {len(feedbacks)} feedback items")

    # Reward model eğit
    print("\n🎓 Training reward model...")
    embeddings = torch.randn(50, 768)  # 50 soru embedding
    scores = torch.rand(50) * 100  # Kalite skorları

    metrics = service.train_reward_model(embeddings, scores, epochs=5)
    print("✓ Training completed")
    print(f"  Final Loss: {metrics['final_loss']:.4f}")
    print(f"  Avg Loss: {metrics['avg_loss']:.4f}")

    # Kalite tahmini
    print("\n🔮 Predicting quality...")
    test_embeddings = [torch.randn(768) for _ in range(3)]

    for i, emb in enumerate(test_embeddings, 1):
        quality = service.predict_quality(emb)
        print(f"  Question {i}: {quality:.2f}/100")

    # RLHF loop
    print("\n🔄 Running RLHF loop...")
    initial_questions = [{"quality_score": 50.0} for _ in range(20)]
    metrics_list = service.run_rlhf_loop(
        initial_questions=initial_questions,
        num_iterations=5,
        questions_per_iteration=10,
    )

    print(f"\n✓ RLHF loop completed ({len(metrics_list)} iterations)")

    # Performance improvement
    final_improvement = metrics_list[-1].performance_improvement
    print(f"\n📈 Performance Improvement: {final_improvement:.2f}%")

    if final_improvement >= 20.0:
        print("✓ REQ-48.32 satisfied (20%+ improvement)")
    else:
        print("⚠️  REQ-48.32 not satisfied yet")

    # Feedback istatistikleri
    print("\n📊 Feedback Statistics:")
    stats = service.get_feedback_statistics()
    print(f"  Total Feedback: {stats['total_feedback']}")
    print(f"  Avg Quality: {stats['avg_quality_score']:.2f}/100")
    print(f"  Min Quality: {stats['min_quality_score']:.2f}")
    print(f"  Max Quality: {stats['max_quality_score']:.2f}")
    print("  Feedback by Type:")
    for fb_type, count in stats["feedback_by_type"].items():
        print(f"    {fb_type}: {count}")

    print("\n✓ RLHF training example completed")


def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("NLP Training Pipeline - Example Usage")
    print("=" * 60)

    # BERTurk (GPU gerektirmez, hızlı)
    example_berturk_embedding()

    # T5/BART (GPU önerilir)
    if torch.cuda.is_available():
        example_t5_bart_generation()
    else:
        print("\n⚠️  Skipping T5/BART example (GPU not available)")

    # RLHF (GPU önerilir)
    if torch.cuda.is_available():
        example_rlhf_training()
    else:
        print("\n⚠️  Skipping RLHF example (GPU not available)")

    # GPT-4 (API key gerekli)
    if os.getenv("OPENAI_API_KEY"):
        example_gpt4_finetuning()
    else:
        print("\n⚠️  Skipping GPT-4 example (OPENAI_API_KEY not set)")

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
