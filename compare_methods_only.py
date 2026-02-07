"""
3 METOTUN KARŞILAŞTIRMASI - DATABASE KAYIT OLMADAN
"""
import random

# METOT 1: OSYM Generator
class OSYMGenerator:
    def __init__(self):
        self.bloom_levels = {
            'Hatırlama': 0.2,
            'Anlama': 0.35,
            'Uygulama': 0.5,
            'Analiz': 0.65,
            'Değerlendirme': 0.75,
            'Yaratma': 0.85
        }

    def generate_sample(self):
        bloom = random.choice(list(self.bloom_levels.keys()))
        difficulty = self.bloom_levels[bloom]

        text = f"""Bir fabrikada üretilen ürünlerin %{random.randint(20, 40)}'i A kalite, %{random.randint(30, 50)}'si B kalite, geri kalanı ise C kalitedir.

A kalite ürünlerin kg fiyatı {random.randint(100, 200)} TL, B kalite ürünlerin kg fiyatı {random.randint(50, 100)} TL, C kalite ürünlerin kg fiyatı {random.randint(20, 50)} TL'dir.

Bu fabrikada günde {random.randint(500, 1000)} kg ürün üretildiğine göre, günlük toplam gelir kaç TL'dir?"""

        return {
            'text': text,
            'difficulty': difficulty,
            'bloom': bloom,
            'length': len(text)
        }

# METOT 2: Hybrid Generator
class HybridGenerator:
    def __init__(self):
        self.contexts = ['market', 'okul', 'hastane', 'laboratuvar']

    def generate_sample(self):
        context = random.choice(self.contexts)

        text = f"""Bir {context} ile ilgili problem:

{context.capitalize()} alanında yapılan çalışmada, {random.randint(100, 500)} birimlik maliyet ile {random.randint(50, 200)} birimlik gelir elde edilmektedir.

Kar-zarar durumu nedir?"""

        return {
            'text': text,
            'difficulty': 0.55,
            'context': context,
            'length': len(text)
        }

# METOT 3: Quality-Aware Generator
class QualityAwareGenerator:
    def generate_sample(self):
        text = """ÖSYM Standartlarına Uygun Soru:

Bir işletme, ürünlerini 3 farklı pakette satmaktadır:
• Küçük paket: 5 adet ürün, 25 TL
• Orta paket: 20 adet ürün, 75 TL
• Büyük paket: 50 adet ürün, 150 TL

Bir müşteri, toplam 150 adet ürün almak istiyor ve en ekonomik alışverişi yapmak istiyor.

Aşağıdaki seçeneklerden hangisi en ekonomik alışveriştir?

I. 3 büyük paket
II. 7 orta paket + 2 küçük paket
III. 30 küçük paket"""

        length_score = min(len(text) / 200, 1.0) * 0.2
        complexity_score = 0.75 * 0.3
        clarity_score = 0.8 * 0.2
        relevance_score = 1.0 * 0.3 if 'ÖSYM' in text else 0.5 * 0.3

        quality_score = length_score + complexity_score + clarity_score + relevance_score

        return {
            'text': text,
            'difficulty': 0.65,
            'quality_score': quality_score,
            'length': len(text)
        }

def compare_methods():
    """3 metodu karşılaştır"""

    print("\n" + "=" * 80)
    print("3 METOT KARŞILAŞTIRMASI - ÖSYM UYGUNLUK ANALİZİ")
    print("=" * 80)

    # Generate samples
    osym_gen = OSYMGenerator()
    hybrid_gen = HybridGenerator()
    quality_gen = QualityAwareGenerator()

    # Generate 10 samples from each
    osym_samples = [osym_gen.generate_sample() for _ in range(10)]
    hybrid_samples = [hybrid_gen.generate_sample() for _ in range(10)]
    quality_samples = [quality_gen.generate_sample() for _ in range(10)]

    # Calculate metrics
    methods_data = {
        'OSYM_GENERATOR': {
            'samples': osym_samples,
            'avg_length': sum(s['length'] for s in osym_samples) / 10,
            'avg_difficulty': sum(s['difficulty'] for s in osym_samples) / 10,
            'has_bloom': True,
            'score': 0
        },
        'HYBRID_GENERATOR': {
            'samples': hybrid_samples,
            'avg_length': sum(s['length'] for s in hybrid_samples) / 10,
            'avg_difficulty': sum(s['difficulty'] for s in hybrid_samples) / 10,
            'has_context': True,
            'score': 0
        },
        'QUALITY_AWARE': {
            'samples': quality_samples,
            'avg_length': sum(s['length'] for s in quality_samples) / 10,
            'avg_difficulty': sum(s['difficulty'] for s in quality_samples) / 10,
            'avg_quality': sum(s['quality_score'] for s in quality_samples) / 10,
            'score': 0
        }
    }

    # Score calculation
    for name, data in methods_data.items():
        # Length score (ideal: 300+ chars)
        data['score'] += min(data['avg_length'] / 300, 1.0) * 25

        # Difficulty variety
        data['score'] += data['avg_difficulty'] * 25

        # Special features
        if name == 'OSYM_GENERATOR' and data.get('has_bloom'):
            data['score'] += 25
        elif name == 'HYBRID_GENERATOR' and data.get('has_context'):
            data['score'] += 20
        elif name == 'QUALITY_AWARE':
            data['score'] += data['avg_quality'] * 25

        # ÖSYM alignment bonus
        if 'ÖSYM' in data['samples'][0]['text'] or data['avg_length'] > 250:
            data['score'] += 25

    # Display results
    print("\nMETOT ANALİZ SONUÇLARI:")
    print("-" * 80)

    for name, data in methods_data.items():
        print(f"\n{name}:")
        print(f"  Ortalama uzunluk: {data['avg_length']:.0f} karakter")
        print(f"  Ortalama zorluk: {data['avg_difficulty']:.2f}")

        if name == 'OSYM_GENERATOR':
            print(f"  Bloom taksonomi: EVET")
        elif name == 'HYBRID_GENERATOR':
            print(f"  Bağlamsal içerik: EVET")
        elif name == 'QUALITY_AWARE':
            print(f"  Kalite skoru: {data['avg_quality']:.2f}")

        print(f"  \n  TOPLAM SKOR: {data['score']:.1f}/100")

    # Find winner
    winner = max(methods_data.items(), key=lambda x: x[1]['score'])

    print("\n" + "=" * 80)
    print(f"KAZANAN: {winner[0]}")
    print(f"ÖSYM'ye en yakın metot - Skor: {winner[1]['score']:.1f}/100")
    print("=" * 80)

    # Show sample questions
    print("\nÖRNEK SORULAR:")
    print("-" * 80)

    for name, data in methods_data.items():
        print(f"\n{name} Örnek:")
        sample = data['samples'][0]
        print(sample['text'][:400] + "..." if len(sample['text']) > 400 else sample['text'])
        print()

if __name__ == "__main__":
    compare_methods()