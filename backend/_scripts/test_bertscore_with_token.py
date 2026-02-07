"""
BERTScore Test with HuggingFace Token
Wave 2B İyileştirme - BERTScore Aktivasyonu
"""

import sys
import io
from pathlib import Path

# UTF-8 kodlama
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Backend'i path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

# .env dosyasını yükle
from dotenv import load_dotenv

load_dotenv()

from services.bertscore_evaluator import BERTScoreEvaluator


def test_bertscore():
    """BERTScore'u HF token ile test et"""
    print("\n" + "=" * 80)
    print(" " * 20 + "BERTSCORE TEST - HF TOKEN İLE")
    print("=" * 80)

    # Evaluator başlat
    print("\n🔧 BERTScore evaluator başlatılıyor...")
    evaluator = BERTScoreEvaluator()

    if not evaluator.is_available():
        print("❌ BERTScore mevcut değil")
        return False

    print("✓ BERTScore paketi yüklü")

    # Test soruları
    candidate = "Bir sayının 3 katının 5 fazlası 26 ise, bu sayı kaçtır?"
    reference = "Bir sayının 2 katının 7 fazlası 23 ise, bu sayı kaçtır?"

    print(f"\n📝 Test Soruları:")
    print(f"   Aday: {candidate}")
    print(f"   Referans: {reference}")

    # BERTScore hesapla
    print(f"\n🔍 BERTScore hesaplanıyor...")
    try:
        result = evaluator.evaluate_single(candidate, reference)

        if result:
            print(f"\n✅ BERTSCORE BAŞARILI!")
            print(f"\n📊 Sonuçlar:")
            print(f"   Precision: {result['precision']:.3f}")
            print(f"   Recall: {result['recall']:.3f}")
            print(f"   F1: {result['f1']:.3f}")
            print(f"   Yorum: {result.get('interpretation', 'N/A')}")
            print(f"\n🎉 BERTScore artık aktif ve çalışıyor!")
            return True
        else:
            print(f"\n⚠️  BERTScore sonuç döndürmedi")
            return False

    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_bertscore()
    print("\n" + "=" * 80)
    if success:
        print("\n✅ TEST BAŞARILI - BERTScore HF token ile çalışıyor!")
        exit(0)
    else:
        print("\n❌ TEST BAŞARISIZ - BERTScore aktif edilemedi")
        exit(1)
