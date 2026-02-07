"""
50 Soru Üretimi ve ÖSYM Kalite Değerlendirmesi
Real OSYM Question Generator kullanarak 50 soru üretir ve kalitelerini değerlendirir
"""

import sys
import os
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any

# Import real OSYM generator (NO MOCK)
from services.osym_question_generator import OSYMQuestionGenerator
from services.llm.ensemble_manager import MultiLLMEnsembleManager
from services.batch_question_generator import BatchQuestionGenerator
from services.comprehensive_quality_evaluator import ComprehensiveQualityEvaluator

# ÖSYM standart konular
TOPICS_CONFIG = {
    "TYT": {
        "Matematik": ["Sayılar", "Denklemler", "Fonksiyonlar", "Geometri", "Olasılık"],
        "Fizik": ["Hareket", "Kuvvet", "Enerji", "Elektrik", "Manyetizma"],
        "Kimya": ["Atom", "Periyodik Sistem", "Kimyasal Bağlar", "Asit-Baz", "Reaksiyonlar"],
        "Biyoloji": ["Hücre", "Genetik", "Ekosistem", "Sindirim", "Dolaşım"]
    }
}


async def generate_questions_batch(
    batch_size: int = 50,
    exam_type: str = "TYT",
    subject: str = "Matematik"
) -> List[Dict[str, Any]]:
    """
    50 soru üret (REAL OSYM generator)
    """
    print(f"\n{'='*80}")
    print(f">>> REAL OSYM Soru Uretimi Basliyor...")
    print(f"{'='*80}")
    print(f"Batch Size: {batch_size}")
    print(f"Exam Type: {exam_type}")
    print(f"Subject: {subject}")
    print(f"Generator: REAL OSYMQuestionGenerator (NO MOCK)")
    print(f"{'='*80}\n")

    # Initialize REAL generator
    ensemble = MultiLLMEnsembleManager()
    generator = OSYMQuestionGenerator(ensemble)
    batch_gen = BatchQuestionGenerator()

    # Create batch configuration
    config = batch_gen.create_batch_config(
        batch_size=batch_size,
        exam_type=exam_type,
        subject=subject,
        topics=TOPICS_CONFIG[exam_type][subject],
        difficulty_range=(0.4, 0.8),  # Orta zorluk
        bloom_levels=[2, 3, 4]  # Kavrama, Uygulama, Analiz
    )

    print(f"📋 Batch Configuration Created:")
    print(f"   - Total tasks: {len(config['tasks'])}")
    print(f"   - Topics: {len(set(t['topic'] for t in config['tasks']))}")
    print(f"   - Difficulty range: 0.4 - 0.8")
    print(f"   - Bloom levels: Kavrama, Uygulama, Analiz\n")

    # Generate questions
    questions = []
    total = len(config['tasks'])

    for i, task_config in enumerate(config['tasks'], 1):
        try:
            print(f"[{i}/{total}] Generating: {task_config['topic']} / {task_config['subtopic']}...", end=" ")

            # CRITICAL: Use REAL OSYM generator - NO MOCK
            question = await generator.generate_question(
                topic=task_config['topic'],
                subtopic=task_config['subtopic'],
                exam_type=task_config['exam_type'],
                subject=task_config['subject'],
                difficulty=task_config['difficulty'],
                bloom_level=task_config['bloom_level'],
                generation_method='ensemble',  # Multi-LLM ensemble
                save_to_db=False  # Don't save during test
            )

            questions.append(question)
            print(f"[OK] Quality: {question.get('quality_score_total', 0):.2f}")

        except Exception as e:
            print(f"[ERROR] FAILED: {str(e)}")
            continue

    print(f"\n{'='*80}")
    print(f"[OK] Generation Complete: {len(questions)}/{total} questions generated")
    print(f"{'='*80}\n")

    return questions


def evaluate_questions_quality(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    ÖSYM standartlarına göre kalite değerlendirmesi
    """
    print(f"\n{'='*80}")
    print(f"[EVAL] OSYM Kalite Degerlendirmesi Basliyor...")
    print(f"{'='*80}\n")

    evaluator = ComprehensiveQualityEvaluator()

    # Evaluate each question
    evaluations = []
    for i, question in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] Evaluating question...", end=" ")

        try:
            evaluation = evaluator.evaluate_complete(question)
            evaluations.append(evaluation)

            overall_score = evaluation.get('overall_score', 0)
            osym_compliance = evaluation.get('osym_compliance_score', 0)

            print(f"Overall: {overall_score:.2f} | ÖSYM: {osym_compliance:.2f}")

        except Exception as e:
            print(f"[ERROR] FAILED: {str(e)}")
            continue

    # Calculate statistics
    if not evaluations:
        return {
            'error': 'No evaluations completed',
            'total_questions': len(questions),
            'evaluated_questions': 0
        }

    overall_scores = [e.get('overall_score', 0) for e in evaluations]
    osym_scores = [e.get('osym_compliance_score', 0) for e in evaluations]
    meb_scores = [e.get('meb_compliance_score', 0) for e in evaluations]

    # Quality classification
    excellent = sum(1 for s in overall_scores if s >= 0.9)
    good = sum(1 for s in overall_scores if 0.8 <= s < 0.9)
    acceptable = sum(1 for s in overall_scores if 0.7 <= s < 0.8)
    poor = sum(1 for s in overall_scores if s < 0.7)

    # ÖSYM compliance levels
    osym_excellent = sum(1 for s in osym_scores if s >= 0.9)
    osym_good = sum(1 for s in osym_scores if 0.8 <= s < 0.9)
    osym_acceptable = sum(1 for s in osym_scores if 0.7 <= s < 0.8)
    osym_poor = sum(1 for s in osym_scores if s < 0.7)

    results = {
        'total_questions': len(questions),
        'evaluated_questions': len(evaluations),
        'generation_timestamp': datetime.now().isoformat(),

        # Overall Quality
        'overall_quality': {
            'average_score': sum(overall_scores) / len(overall_scores),
            'min_score': min(overall_scores),
            'max_score': max(overall_scores),
            'excellent': excellent,
            'good': good,
            'acceptable': acceptable,
            'poor': poor
        },

        # ÖSYM Compliance
        'osym_compliance': {
            'average_score': sum(osym_scores) / len(osym_scores),
            'min_score': min(osym_scores),
            'max_score': max(osym_scores),
            'excellent': osym_excellent,
            'good': osym_good,
            'acceptable': osym_acceptable,
            'poor': osym_poor
        },

        # MEB Compliance
        'meb_compliance': {
            'average_score': sum(meb_scores) / len(meb_scores),
            'min_score': min(meb_scores),
            'max_score': max(meb_scores)
        },

        # Detailed evaluations
        'detailed_evaluations': evaluations,

        # Questions data
        'questions': questions
    }

    print(f"\n{'='*80}")
    print(f"[OK] Evaluation Complete")
    print(f"{'='*80}\n")

    return results


def generate_quality_report(results: Dict[str, Any]) -> str:
    """
    Detaylı kalite raporu oluştur
    """
    report = []
    report.append("=" * 100)
    report.append("🎯 50 SORU ÜRETİMİ ve ÖSYM KALİTE DEĞERLENDİRMESİ RAPORU")
    report.append("=" * 100)
    report.append("")

    # Header info
    report.append(f"📅 Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"📊 Toplam Soru: {results['total_questions']}")
    report.append(f"[OK] Değerlendirilen: {results['evaluated_questions']}")
    report.append(f"🤖 Generator: REAL OSYMQuestionGenerator (Multi-LLM Ensemble)")
    report.append("")

    # Overall Quality Summary
    overall = results['overall_quality']
    report.append("=" * 100)
    report.append("📈 GENEL KALİTE SKORU")
    report.append("=" * 100)
    report.append(f"Ortalama Skor: {overall['average_score']:.4f} / 1.0")
    report.append(f"En Düşük:      {overall['min_score']:.4f}")
    report.append(f"En Yüksek:     {overall['max_score']:.4f}")
    report.append("")
    report.append("Kalite Dağılımı:")
    report.append(f"  🌟 Mükemmel (0.9+):    {overall['excellent']:3d} soru ({overall['excellent']/results['evaluated_questions']*100:5.1f}%)")
    report.append(f"  [OK] İyi (0.8-0.9):      {overall['good']:3d} soru ({overall['good']/results['evaluated_questions']*100:5.1f}%)")
    report.append(f"  [WARN]  Kabul Edilebilir:  {overall['acceptable']:3d} soru ({overall['acceptable']/results['evaluated_questions']*100:5.1f}%)")
    report.append(f"  [ERROR] Zayıf (<0.7):       {overall['poor']:3d} soru ({overall['poor']/results['evaluated_questions']*100:5.1f}%)")
    report.append("")

    # ÖSYM Compliance
    osym = results['osym_compliance']
    report.append("=" * 100)
    report.append("🎓 ÖSYM UYUMLULUK SKORU")
    report.append("=" * 100)
    report.append(f"Ortalama Skor: {osym['average_score']:.4f} / 1.0")
    report.append(f"En Düşük:      {osym['min_score']:.4f}")
    report.append(f"En Yüksek:     {osym['max_score']:.4f}")
    report.append("")
    report.append("ÖSYM Standart Uygunluğu:")
    report.append(f"  🌟 Mükemmel (0.9+):    {osym['excellent']:3d} soru ({osym['excellent']/results['evaluated_questions']*100:5.1f}%)")
    report.append(f"  [OK] İyi (0.8-0.9):      {osym['good']:3d} soru ({osym['good']/results['evaluated_questions']*100:5.1f}%)")
    report.append(f"  [WARN]  Kabul Edilebilir:  {osym['acceptable']:3d} soru ({osym['acceptable']/results['evaluated_questions']*100:5.1f}%)")
    report.append(f"  [ERROR] Zayıf (<0.7):       {osym['poor']:3d} soru ({osym['poor']/results['evaluated_questions']*100:5.1f}%)")
    report.append("")

    # MEB Compliance
    meb = results['meb_compliance']
    report.append("=" * 100)
    report.append("📚 MEB UYUMLULUK SKORU")
    report.append("=" * 100)
    report.append(f"Ortalama Skor: {meb['average_score']:.4f} / 1.0")
    report.append(f"En Düşük:      {meb['min_score']:.4f}")
    report.append(f"En Yüksek:     {meb['max_score']:.4f}")
    report.append("")

    # Success Criteria
    report.append("=" * 100)
    report.append("[OK] BAŞARI KRİTERLERİ DEĞERLENDİRMESİ")
    report.append("=" * 100)

    # Criterion 1: Overall Quality >= 0.8
    avg_quality = overall['average_score']
    criterion1 = "[OK] BAŞARILI" if avg_quality >= 0.8 else "[ERROR] BAŞARISIZ"
    report.append(f"1. Ortalama Kalite >= 0.8:  {criterion1} ({avg_quality:.4f})")

    # Criterion 2: ÖSYM Compliance >= 0.85
    avg_osym = osym['average_score']
    criterion2 = "[OK] BAŞARILI" if avg_osym >= 0.85 else "[ERROR] BAŞARISIZ"
    report.append(f"2. ÖSYM Uyumluluk >= 0.85:  {criterion2} ({avg_osym:.4f})")

    # Criterion 3: At least 80% good or excellent
    good_or_better = overall['excellent'] + overall['good']
    good_percentage = good_or_better / results['evaluated_questions'] * 100
    criterion3 = "[OK] BAŞARILI" if good_percentage >= 80 else "[ERROR] BAŞARISIZ"
    report.append(f"3. İyi/Mükemmel >= 80%:     {criterion3} ({good_percentage:.1f}%)")

    # Criterion 4: No more than 5% poor quality
    poor_percentage = overall['poor'] / results['evaluated_questions'] * 100
    criterion4 = "[OK] BAŞARILI" if poor_percentage <= 5 else "[ERROR] BAŞARISIZ"
    report.append(f"4. Zayıf Soru <= 5%:        {criterion4} ({poor_percentage:.1f}%)")

    report.append("")

    # Overall assessment
    all_passed = all([
        avg_quality >= 0.8,
        avg_osym >= 0.85,
        good_percentage >= 80,
        poor_percentage <= 5
    ])

    report.append("=" * 100)
    if all_passed:
        report.append("🎉 SONUÇ: TÜM KRİTERLER SAĞLANDI - ÖSYM KALİTE STANDARTLARI KARŞILANDI!")
    else:
        report.append("[WARN] SONUÇ: BAZI KRİTERLER SAĞLANAMADI - İYİLEŞTİRME GEREKLİ")
    report.append("=" * 100)
    report.append("")

    # Top 5 Best Questions
    report.append("=" * 100)
    report.append("🏆 EN İYİ 5 SORU")
    report.append("=" * 100)

    evaluations = results['detailed_evaluations']
    questions = results['questions']

    # Sort by overall score
    sorted_evals = sorted(
        zip(evaluations, questions),
        key=lambda x: x[0].get('overall_score', 0),
        reverse=True
    )[:5]

    for i, (eval_data, question) in enumerate(sorted_evals, 1):
        report.append(f"\n{i}. Soru:")
        report.append(f"   Konu: {question.get('topic', 'N/A')} / {question.get('subtopic', 'N/A')}")
        report.append(f"   Genel Skor: {eval_data.get('overall_score', 0):.4f}")
        report.append(f"   ÖSYM Uyumluluk: {eval_data.get('osym_compliance_score', 0):.4f}")
        report.append(f"   Zorluk: {question.get('difficulty', 0):.2f}")
        report.append(f"   Bloom Seviyesi: {question.get('bloom_level', 'N/A')}")

    report.append("")
    report.append("=" * 100)
    report.append("📊 Detaylı veriler 'question_quality_results.json' dosyasına kaydedildi")
    report.append("=" * 100)

    return "\n".join(report)


async def main():
    """
    Ana çalıştırma fonksiyonu
    """
    print("\n>>> Starting 50 Question Generation and OSYM Quality Evaluation...\n")

    try:
        # Step 1: Generate 50 questions
        questions = await generate_questions_batch(
            batch_size=50,
            exam_type="TYT",
            subject="Matematik"
        )

        if len(questions) < 10:
            print(f"[ERROR] ERROR: Only {len(questions)} questions generated. Minimum 10 required.")
            return

        # Step 2: Evaluate quality
        results = evaluate_questions_quality(questions)

        # Step 3: Generate report
        report = generate_quality_report(results)

        # Print report
        print("\n" + report)

        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save JSON
        json_file = f'question_quality_results_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 JSON Results saved to: {json_file}")

        # Save report
        report_file = f'quality_evaluation_report_{timestamp}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"💾 Text Report saved to: {report_file}")

        print("\n[OK] Process completed successfully!")

    except Exception as e:
        print(f"\n[ERROR] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
