"""
ENHANCED OSYM QUESTION GENERATOR
Eksiklikleri giderilmiş gelişmiş versiyon
"""

import random
import json
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import io
import base64

class EnhancedOSYMGenerator:
    """Görsel destekli, adaptif, gerçek ÖSYM formatında soru üretici"""

    def __init__(self):
        # Bloom taksonomisi (mevcut)
        self.bloom_levels = {
            'Hatırlama': 0.2,
            'Anlama': 0.35,
            'Uygulama': 0.5,
            'Analiz': 0.65,
            'Değerlendirme': 0.75,
            'Yaratma': 0.85
        }

        # YENİ: Görsel template'ler
        self.visual_templates = {
            'grafik': self._generate_graph_template,
            'tablo': self._generate_table_template,
            'geometri': self._generate_geometry_template,
            'histogram': self._generate_histogram_template
        }

        # YENİ: Yaygın öğrenci hataları (distractor patterns)
        self.common_errors = {
            'matematik': {
                'işaret_hatası': lambda x: -x,
                'formül_karıştırma': lambda x: x * 2,
                'birim_hatası': lambda x: x / 10,
                'yuvarlama_hatası': lambda x: round(x),
                'ters_işlem': lambda x: 1/x if x != 0 else 0
            },
            'fizik': {
                'yön_hatası': lambda x: -x,
                'birim_dönüşüm': lambda x: x * 1000,
                'formül_seçimi': lambda x: x**2,
                'sürtünme_ihmal': lambda x: x * 1.2,
                'yerçekimi_hatası': lambda x: x * 9.8
            }
        }

        # YENİ: Zengin bağlamlar
        self.rich_contexts = {
            'günlük_hayat': {
                'market': ['indirim hesaplama', 'kdv', 'kâr-zarar', 'bütçe planlama'],
                'okul': ['not ortalaması', 'devamsızlık', 'başarı yüzdesi', 'sınıf mevcudu'],
                'hastane': ['doz hesabı', 'randevu planı', 'yatak kapasitesi', 'personel vardiya'],
                'trafik': ['hız hesabı', 'yakıt tüketimi', 'mesafe-zaman', 'trafik yoğunluğu']
            },
            'bilim': {
                'laboratuvar': ['deney tasarımı', 'ölçüm hatası', 'konsantrasyon', 'reaksiyon hızı'],
                'uzay': ['yörünge hesabı', 'yerçekimi', 'gezegen hareketleri', 'ışık hızı'],
                'teknoloji': ['veri aktarımı', 'işlemci hızı', 'bellek kapasitesi', 'algoritma karmaşıklığı'],
                'çevre': ['karbon ayak izi', 'geri dönüşüm', 'enerji tasarrufu', 'su tüketimi']
            },
            'ekonomi': {
                'borsa': ['hisse değeri', 'getiri oranı', 'risk analizi', 'portföy çeşitlendirme'],
                'enflasyon': ['alım gücü', 'fiyat artışı', 'maaş güncellemesi', 'faiz hesabı'],
                'yatırım': ['amortisman', 'kâr payı', 'vade hesabı', 'risk-getiri dengesi'],
                'vergi': ['gelir vergisi', 'kdv hesabı', 'stopaj', 'vergi iadesi']
            }
        }

        # YENİ: ÖSYM format şablonları
        self.osym_formats = {
            'paragraf_bazlı': self._generate_paragraph_question,
            'tablo_yorumlama': self._generate_table_interpretation,
            'grafik_analiz': self._generate_graph_analysis,
            'çoklu_bilgi': self._generate_multi_info_question,
            'ardışık_soru': self._generate_sequential_question
        }

    def generate_enhanced_question(self,
                                  exam_type: str = 'TYT',
                                  subject: str = 'Matematik',
                                  include_visual: bool = False,
                                  adaptive_difficulty: Optional[float] = None) -> Dict:
        """
        Geliştirilmiş soru üretimi

        Args:
            exam_type: TYT/AYT/YDT
            subject: Matematik/Fizik/Kimya vb.
            include_visual: Görsel içerik eklensin mi
            adaptive_difficulty: Öğrenci seviyesine göre zorluk (0-1)

        Returns:
            Zenginleştirilmiş soru objesi
        """

        # Bloom seviyesi seç
        bloom_level = random.choice(list(self.bloom_levels.keys()))
        base_difficulty = self.bloom_levels[bloom_level]

        # Adaptif zorluk ayarla
        if adaptive_difficulty is not None:
            difficulty = self._adjust_difficulty(base_difficulty, adaptive_difficulty)
        else:
            difficulty = base_difficulty

        # Bağlam seç
        context_category = random.choice(list(self.rich_contexts.keys()))
        context = random.choice(list(self.rich_contexts[context_category].keys()))
        context_detail = random.choice(self.rich_contexts[context_category][context])

        # Format seç
        format_type = random.choice(list(self.osym_formats.keys()))

        # Soru metni oluştur
        question_text = self.osym_formats[format_type](
            context, context_detail, difficulty, bloom_level
        )

        # Doğru cevap hesapla
        correct_answer = self._calculate_answer(difficulty)

        # YENİ: Akıllı distractor'lar oluştur
        distractors = self._generate_smart_distractors(correct_answer, subject)

        # Seçenekleri karıştır
        options = [correct_answer] + distractors
        random.shuffle(options)
        correct_index = options.index(correct_answer)

        # Soru objesi oluştur
        question = {
            'text': question_text,
            'options': options,
            'correct_answer': chr(65 + correct_index),  # A, B, C, D, E
            'difficulty': difficulty,
            'bloom_level': bloom_level,
            'exam_type': exam_type,
            'subject': subject,
            'context': f"{context_category}/{context}/{context_detail}",
            'format': format_type
        }

        # YENİ: Görsel ekle (opsiyonel)
        if include_visual:
            visual_type = random.choice(list(self.visual_templates.keys()))
            question['visual'] = self.visual_templates[visual_type](question_text)
            question['visual_type'] = visual_type

        # YENİ: Çözüm adımları ekle
        question['solution_steps'] = self._generate_solution_steps(
            question_text, correct_answer, difficulty
        )

        # YENİ: Öğrenme hedefleri
        question['learning_objectives'] = self._map_learning_objectives(
            bloom_level, subject, context_detail
        )

        return question

    def _generate_smart_distractors(self, correct_answer: float, subject: str) -> List[float]:
        """Akıllı yanlış seçenekler oluştur"""
        distractors = []

        if subject in self.common_errors:
            error_patterns = self.common_errors[subject]

            # Her hata tipinden bir distractor üret
            for error_name, error_func in list(error_patterns.items())[:4]:
                distractor = error_func(correct_answer)
                if distractor != correct_answer:
                    distractors.append(distractor)

        # Eksik varsa rastgele doldur
        while len(distractors) < 4:
            offset = random.uniform(-correct_answer*0.5, correct_answer*0.5)
            distractor = correct_answer + offset
            if distractor not in distractors and distractor != correct_answer:
                distractors.append(distractor)

        return distractors[:4]

    def _generate_paragraph_question(self, context: str, detail: str,
                                    difficulty: float, bloom: str) -> str:
        """ÖSYM tarzı paragraf bazlı soru"""

        values = {
            'initial': random.randint(100, 1000),
            'rate': random.randint(5, 25),
            'time': random.randint(2, 10),
            'extra': random.randint(50, 200)
        }

        text = f"""
{context.capitalize()} sektöründe faaliyet gösteren bir işletme, {detail} konusunda analiz yapmaktadır.

İşletmenin başlangıç değeri {values['initial']} birimdir. Her dönem %{values['rate']} oranında
bir değişim gözlenmektedir. {values['time']} dönem sonunda, ek olarak {values['extra']} birimlik
bir düzeltme faktörü uygulanmaktadır.

Bloom Seviyesi: {bloom}
Zorluk: {difficulty:.2f}

Bu bilgilere göre, nihai değer kaç birim olur?
        """

        return text.strip()

    def _generate_table_interpretation(self, context: str, detail: str,
                                      difficulty: float, bloom: str) -> str:
        """Tablo yorumlama sorusu"""

        text = f"""
Aşağıdaki tabloda {context} ile ilgili {detail} verileri gösterilmektedir:

| Dönem | Değer | Değişim (%) |
|-------|-------|-------------|
| Q1    | 100   | -           |
| Q2    | 115   | +15%        |
| Q3    | 138   | +20%        |
| Q4    | ?     | +25%        |

Tabloya göre Q4 dönemindeki değer kaçtır?
        """

        return text.strip()

    def _generate_graph_analysis(self, context: str, detail: str,
                                difficulty: float, bloom: str) -> str:
        """Grafik analiz sorusu"""

        text = f"""
[GÖRSEL: {context} konusunda {detail} grafiği]

Yukarıdaki grafikte gösterilen veriye göre, trend devam ederse
gelecek dönemdeki tahmini değer ne olur?

(Grafik: Doğrusal artış trendi göstermektedir)
        """

        return text.strip()

    def _generate_multi_info_question(self, context: str, detail: str,
                                     difficulty: float, bloom: str) -> str:
        """Çoklu bilgi sorusu"""

        text = f"""
{context.capitalize()} alanında {detail} hesabı için aşağıdaki bilgiler verilmiştir:

I. Başlangıç değeri: 500 birim
II. Artış oranı: %20
III. Süre: 3 dönem
IV. Düzeltme katsayısı: 0.9

Bu bilgiler kullanılarak hesaplanan sonuç aşağıdakilerden hangisidir?
        """

        return text.strip()

    def _generate_sequential_question(self, context: str, detail: str,
                                     difficulty: float, bloom: str) -> str:
        """Ardışık işlem sorusu"""

        text = f"""
Bir {context} probleminde şu işlemler sırayla uygulanıyor:

1. Başlangıç değeri 2 ile çarpılıyor
2. Sonuca 50 ekleniyor
3. Elde edilen değer 3'e bölünüyor
4. Son olarak 10 çıkarılıyor

Başlangıç değeri 30 ise, sonuç kaçtır?
        """

        return text.strip()

    def _generate_graph_template(self, question_text: str) -> str:
        """Grafik görseli oluştur"""
        plt.figure(figsize=(8, 6))

        # Örnek veri
        x = [1, 2, 3, 4, 5]
        y = [10, 25, 45, 70, 100]

        plt.plot(x, y, 'b-o', linewidth=2, markersize=8)
        plt.grid(True, alpha=0.3)
        plt.xlabel('Dönem')
        plt.ylabel('Değer')
        plt.title('Zaman-Değer Grafiği')

        # Base64 encoding
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()

        return f"data:image/png;base64,{image_base64}"

    def _generate_table_template(self, question_text: str) -> str:
        """Tablo HTML'i oluştur"""
        return """
        <table border='1'>
            <tr><th>Değişken</th><th>Değer</th></tr>
            <tr><td>X</td><td>100</td></tr>
            <tr><td>Y</td><td>200</td></tr>
            <tr><td>Z</td><td>?</td></tr>
        </table>
        """

    def _generate_geometry_template(self, question_text: str) -> str:
        """Geometrik şekil SVG'si"""
        return """
        <svg width="200" height="200">
            <rect x="50" y="50" width="100" height="100" fill="lightblue" stroke="black"/>
            <text x="100" y="100" text-anchor="middle">a=10</text>
        </svg>
        """

    def _generate_histogram_template(self, question_text: str) -> str:
        """Histogram oluştur"""
        plt.figure(figsize=(8, 6))

        data = [random.gauss(50, 15) for _ in range(1000)]
        plt.hist(data, bins=30, edgecolor='black', alpha=0.7)
        plt.xlabel('Değer')
        plt.ylabel('Frekans')
        plt.title('Dağılım Histogramı')

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()

        return f"data:image/png;base64,{image_base64}"

    def _calculate_answer(self, difficulty: float) -> float:
        """Zorluk seviyesine göre cevap hesapla"""
        base = random.randint(10, 100)
        multiplier = 1 + difficulty * 10
        return round(base * multiplier, 2)

    def _adjust_difficulty(self, base: float, target: float) -> float:
        """Adaptif zorluk ayarlama"""
        # Öğrenci seviyesine göre zorluğu ayarla
        adjustment = (target - base) * 0.5
        return max(0, min(1, base + adjustment))

    def _generate_solution_steps(self, question: str, answer: float, difficulty: float) -> List[str]:
        """Çözüm adımlarını oluştur"""
        steps = []

        if difficulty < 0.3:
            steps = [
                "1. Verilen değerleri belirle",
                f"2. İşlemi uygula",
                f"3. Sonuç: {answer}"
            ]
        elif difficulty < 0.6:
            steps = [
                "1. Problemi analiz et",
                "2. Gerekli formülü seç",
                "3. Değerleri yerine koy",
                f"4. Hesapla: {answer}"
            ]
        else:
            steps = [
                "1. Problemi parçalara ayır",
                "2. Alt problemleri çöz",
                "3. Ara sonuçları birleştir",
                "4. Doğrulamayı yap",
                f"5. Nihai sonuç: {answer}"
            ]

        return steps

    def _map_learning_objectives(self, bloom: str, subject: str, detail: str) -> List[str]:
        """Öğrenme hedeflerini eşleştir"""
        objectives = {
            'Hatırlama': [f"{subject} temel kavramlarını hatırlama"],
            'Anlama': [f"{detail} konusunu anlama ve açıklama"],
            'Uygulama': [f"{detail} ile ilgili problemleri çözme"],
            'Analiz': [f"{detail} verilerini analiz etme"],
            'Değerlendirme': [f"{subject} çözümlerini değerlendirme"],
            'Yaratma': [f"Yeni {detail} çözümleri üretme"]
        }

        return objectives.get(bloom, ["Genel problem çözme becerisi"])


# Kullanım örneği
if __name__ == "__main__":
    generator = EnhancedOSYMGenerator()

    # Normal soru
    question1 = generator.generate_enhanced_question(
        exam_type='TYT',
        subject='Matematik',
        include_visual=False
    )

    print("NORMAL SORU:")
    print(json.dumps(question1, indent=2, ensure_ascii=False))

    print("\n" + "="*80 + "\n")

    # Görsel destekli adaptif soru
    question2 = generator.generate_enhanced_question(
        exam_type='AYT',
        subject='Fizik',
        include_visual=True,
        adaptive_difficulty=0.7
    )

    print("GÖRSEL DESTEKLİ ADAPTİF SORU:")
    print(json.dumps({k:v for k,v in question2.items() if k != 'visual'},
                     indent=2, ensure_ascii=False))
    print(f"Görsel: {question2.get('visual_type', 'Yok')}")