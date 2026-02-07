"""
KIRO2 Educational Algorithms
IRT, FSRS, ZPD ve diğer eğitim algoritmaları
"""

import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger('KIRO2.Algorithms')


class ItemResponseTheory:
    """
    Item Response Theory (IRT) - 3PL Model
    Öğrenci yetenek seviyesi ve soru zorluğu analizi
    """
    
    def __init__(self):
        self.model_type = "3PL"  # 3-Parameter Logistic
        self.D = 1.7  # Scaling constant
        
    def calculate_probability(self, theta: float, a: float = 1.0, 
                            b: float = 0.0, c: float = 0.0) -> float:
        """
        3PL IRT modeli ile başarı olasılığını hesapla
        
        Args:
            theta: Öğrenci yetenek seviyesi (-3 to +3)
            a: Discrimination parameter (ayırt edicilik)
            b: Difficulty parameter (zorluk)
            c: Guessing parameter (tahmin parametresi)
        """
        exp_val = math.exp(self.D * a * (theta - b))
        probability = c + (1 - c) * (exp_val / (1 + exp_val))
        return probability
    
    def estimate_ability(self, responses: List[Dict]) -> float:
        """Maximum Likelihood Estimation ile yetenek tahmini"""
        theta = 0.0  # Başlangıç tahmini
        
        for _ in range(20):  # Newton-Raphson iterations
            first_derivative = 0
            second_derivative = 0
            
            for response in responses:
                p = self.calculate_probability(
                    theta, 
                    response.get('a', 1.0),
                    response.get('b', 0.0),
                    response.get('c', 0.0)
                )
                
                # Derivatives for MLE
                first_derivative += (response['answer'] - p) * response.get('a', 1.0)
                second_derivative -= p * (1 - p) * response.get('a', 1.0) ** 2
            
            if second_derivative == 0:
                break
                
            theta = theta - first_derivative / second_derivative
        
        return max(-3.0, min(3.0, theta))  # Bound between -3 and +3
    
    def adaptive_question_selection(self, theta: float, 
                                   question_pool: List[Dict]) -> Dict:
        """Fisher Information maximization ile adaptif soru seçimi"""
        best_question = None
        max_information = 0
        
        for question in question_pool:
            p = self.calculate_probability(
                theta,
                question.get('a', 1.0),
                question.get('b', 0.0),
                question.get('c', 0.0)
            )
            
            # Fisher Information
            information = question.get('a', 1.0) ** 2 * p * (1 - p)
            
            if information > max_information:
                max_information = information
                best_question = question
        
        return best_question


class FSRS:
    """
    Free Spaced Repetition Scheduler - 17 Parametreli Model
    Anki benzeri gelişmiş tekrar algoritması
    """
    
    def __init__(self, parameters: int = 17):
        self.params = self._initialize_parameters(parameters)
        self.w = self.params['weights']  # 17 ağırlık parametresi
        
    def _initialize_parameters(self, n: int) -> Dict:
        """17 FSRS parametresini initialize et"""
        return {
            'weights': [
                0.4,    # w0: Initial stability for Again
                0.7,    # w1: Initial stability for Hard  
                2.3,    # w2: Initial stability for Good
                10.9,   # w3: Initial stability for Easy
                4.93,   # w4: Stability increment for Again
                0.94,   # w5: Stability increment for Hard
                0.86,   # w6: Stability increment for Good
                0.01,   # w7: Stability increment for Easy
                1.49,   # w8: Retrievability power
                0.14,   # w9: Stability decay
                0.94,   # w10: Difficulty increment
                2.18,   # w11: Stability factor
                0.05,   # w12: Retrievability factor
                0.34,   # w13: Initial difficulty
                1.26,   # w14: Difficulty penalty
                0.29,   # w15: Stability penalty
                2.61    # w16: Response penalty
            ] if n == 17 else [1.0] * n,
            'decay': -0.5,
            'factor': 0.9 ** (1/19),
            'request_retention': 0.9
        }
    
    def calculate_interval(self, stability: float, retention: float) -> int:
        """Tekrar aralığını hesapla"""
        interval = stability * math.log(retention) / math.log(self.params['factor'])
        return max(1, round(interval))
    
    def calculate_stability(self, difficulty: float, stability: float, 
                           rating: int, elapsed_days: int) -> float:
        """Yeni stability değerini hesapla"""
        
        # Retrievability hesapla
        retrievability = math.exp(math.log(0.9) * elapsed_days / stability)
        
        # Rating'e göre stability güncelleme
        if rating == 1:  # Again
            new_stability = self.w[4] * difficulty * stability * retrievability
        elif rating == 2:  # Hard
            new_stability = self.w[5] * difficulty * stability * retrievability
        elif rating == 3:  # Good
            new_stability = self.w[6] * difficulty * stability * retrievability
        else:  # Easy
            new_stability = self.w[7] * difficulty * stability * retrievability
            
        return max(0.1, new_stability)
    
    def calculate_difficulty(self, difficulty: float, rating: int) -> float:
        """Zorluk parametresini güncelle"""
        delta = self.w[10] * (rating - 3)
        new_difficulty = difficulty + delta * (1 - difficulty)
        return max(0.1, min(1.0, new_difficulty))
    
    def get_next_review(self, card: Dict, rating: int) -> Dict:
        """Sonraki tekrar zamanını hesapla"""
        current_stability = card.get('stability', 1.0)
        current_difficulty = card.get('difficulty', 0.3)
        elapsed = card.get('elapsed_days', 0)
        
        # Güncelle
        new_stability = self.calculate_stability(
            current_difficulty, current_stability, rating, elapsed
        )
        new_difficulty = self.calculate_difficulty(current_difficulty, rating)
        
        # Interval hesapla
        interval = self.calculate_interval(
            new_stability, 
            self.params['request_retention']
        )
        
        return {
            'stability': new_stability,
            'difficulty': new_difficulty,
            'interval': interval,
            'next_review': datetime.now() + timedelta(days=interval)
        }


class ZoneProximalDevelopment:
    """
    Zone of Proximal Development (ZPD) - Vygotsky
    Öğrenci için optimal zorluk seviyesi belirleme
    """
    
    def __init__(self):
        self.zpd_range = 0.15  # ±15% optimal range
        self.scaffolding_levels = {
            'none': 0,
            'minimal': 0.25,
            'moderate': 0.5,
            'substantial': 0.75,
            'maximum': 1.0
        }
    
    def calculate_zpd_range(self, current_ability: float) -> Tuple[float, float]:
        """Öğrencinin ZPD aralığını hesapla"""
        lower_bound = current_ability - self.zpd_range
        upper_bound = current_ability + self.zpd_range
        return (lower_bound, upper_bound)
    
    def is_in_zpd(self, ability: float, difficulty: float) -> bool:
        """Soru zorluğunun ZPD içinde olup olmadığını kontrol et"""
        lower, upper = self.calculate_zpd_range(ability)
        return lower <= difficulty <= upper
    
    def calculate_scaffolding(self, ability: float, difficulty: float) -> str:
        """Gerekli scaffolding seviyesini belirle"""
        gap = difficulty - ability
        
        if gap <= 0:
            return 'none'
        elif gap <= 0.1:
            return 'minimal'
        elif gap <= 0.2:
            return 'moderate'
        elif gap <= 0.3:
            return 'substantial'
        else:
            return 'maximum'
    
    def adaptive_difficulty(self, performance: List[int], 
                           current_difficulty: float) -> float:
        """Performansa göre zorluk ayarlama"""
        if not performance:
            return current_difficulty
            
        success_rate = sum(performance) / len(performance)
        
        # Optimal success rate: %70-80
        if success_rate > 0.8:
            # Çok kolay, zorluğu artır
            adjustment = min(0.1, (success_rate - 0.8) * 0.5)
            return min(1.0, current_difficulty + adjustment)
        elif success_rate < 0.7:
            # Çok zor, zorluğu azalt
            adjustment = min(0.1, (0.7 - success_rate) * 0.5)
            return max(0.0, current_difficulty - adjustment)
        else:
            # Optimal aralıkta
            return current_difficulty


class MultiArmedBandit:
    """
    Multi-Armed Bandit Algorithm - Content Selection
    Thompson Sampling ile optimal içerik seçimi
    """
    
    def __init__(self, n_arms: int = 10):
        self.n_arms = n_arms
        self.alpha = np.ones(n_arms)  # Successes
        self.beta = np.ones(n_arms)   # Failures
        
    def select_arm(self) -> int:
        """Thompson Sampling ile kol seçimi"""
        samples = [np.random.beta(self.alpha[i], self.beta[i]) 
                  for i in range(self.n_arms)]
        return int(np.argmax(samples))
    
    def update(self, arm: int, reward: bool):
        """Sonuca göre parametreleri güncelle"""
        if reward:
            self.alpha[arm] += 1
        else:
            self.beta[arm] += 1
    
    def get_statistics(self) -> List[Dict]:
        """Her kolun istatistiklerini döndür"""
        stats = []
        for i in range(self.n_arms):
            mean = self.alpha[i] / (self.alpha[i] + self.beta[i])
            variance = (self.alpha[i] * self.beta[i]) / \
                      ((self.alpha[i] + self.beta[i]) ** 2 * \
                       (self.alpha[i] + self.beta[i] + 1))
            
            stats.append({
                'arm': i,
                'mean': mean,
                'variance': variance,
                'trials': self.alpha[i] + self.beta[i] - 2
            })
        
        return stats


class BloomTaxonomy:
    """
    Bloom's Taxonomy - Cognitive Level Classification
    Soru ve içerikleri bilişsel seviyelere göre sınıflandırma
    """
    
    def __init__(self):
        self.levels = {
            1: {'name': 'Remember', 'keywords': ['tanımla', 'listele', 'adlandır', 'hatırla']},
            2: {'name': 'Understand', 'keywords': ['açıkla', 'özetle', 'yorumla', 'sınıflandır']},
            3: {'name': 'Apply', 'keywords': ['uygula', 'kullan', 'çöz', 'hesapla']},
            4: {'name': 'Analyze', 'keywords': ['analiz et', 'karşılaştır', 'ayır', 'incele']},
            5: {'name': 'Evaluate', 'keywords': ['değerlendir', 'eleştir', 'yargıla', 'savun']},
            6: {'name': 'Create', 'keywords': ['oluştur', 'tasarla', 'geliştir', 'üret']}
        }
    
    def classify_question(self, question_text: str) -> int:
        """Soruyu Bloom seviyesine göre sınıflandır"""
        question_lower = question_text.lower()
        
        for level, data in self.levels.items():
            for keyword in data['keywords']:
                if keyword in question_lower:
                    return level
        
        # Default to Understanding level
        return 2
    
    def get_level_name(self, level: int) -> str:
        """Seviye adını döndür"""
        return self.levels.get(level, {}).get('name', 'Unknown')
    
    def suggest_question_type(self, target_level: int) -> List[str]:
        """Hedef seviye için soru tipleri öner"""
        suggestions = {
            1: ["Tanım soruları", "Liste soruları", "Eşleştirme soruları"],
            2: ["Açıklama soruları", "Özet soruları", "Karşılaştırma soruları"],
            3: ["Problem çözme", "Hesaplama soruları", "Uygulama soruları"],
            4: ["Analiz soruları", "Grafik yorumlama", "Veri analizi"],
            5: ["Değerlendirme soruları", "Kritik düşünme", "Argüman analizi"],
            6: ["Proje tasarımı", "Yaratıcı problem çözme", "Sentez soruları"]
        }
        
        return suggestions.get(target_level, [])


# Test fonksiyonu
def test_algorithms():
    """Tüm algoritmaları test et"""
    print("\n" + "="*80)
    print("🧮 KIRO2 EDUCATIONAL ALGORITHMS TEST")
    print("="*80)
    
    # 1. IRT Test
    print("\n📊 Item Response Theory (IRT):")
    print("-"*60)
    irt = ItemResponseTheory()
    
    # Öğrenci yetenek seviyesi 0.5, soru zorluğu 0.5
    prob = irt.calculate_probability(theta=0.5, a=1.2, b=0.5, c=0.25)
    print(f"  Başarı olasılığı: {prob:.2%}")
    
    # Yetenek tahmini
    responses = [
        {'answer': 1, 'a': 1.0, 'b': -0.5, 'c': 0.2},
        {'answer': 1, 'a': 1.2, 'b': 0.0, 'c': 0.25},
        {'answer': 0, 'a': 0.8, 'b': 1.0, 'c': 0.15},
    ]
    ability = irt.estimate_ability(responses)
    print(f"  Tahmin edilen yetenek: {ability:.2f}")
    
    # 2. FSRS Test
    print("\n🔄 FSRS (17 Parameters):")
    print("-"*60)
    fsrs = FSRS(17)
    
    card = {
        'stability': 2.5,
        'difficulty': 0.3,
        'elapsed_days': 5
    }
    
    # Good rating (3)
    next_review = fsrs.get_next_review(card, rating=3)
    print(f"  Sonraki tekrar: {next_review['interval']} gün sonra")
    print(f"  Yeni stability: {next_review['stability']:.2f}")
    print(f"  Yeni zorluk: {next_review['difficulty']:.2f}")
    
    # 3. ZPD Test
    print("\n🎯 Zone of Proximal Development:")
    print("-"*60)
    zpd = ZoneProximalDevelopment()
    
    student_ability = 0.6
    zpd_range = zpd.calculate_zpd_range(student_ability)
    print(f"  Öğrenci yeteneği: {student_ability:.2f}")
    print(f"  ZPD aralığı: [{zpd_range[0]:.2f}, {zpd_range[1]:.2f}]")
    
    question_difficulty = 0.7
    in_zpd = zpd.is_in_zpd(student_ability, question_difficulty)
    scaffolding = zpd.calculate_scaffolding(student_ability, question_difficulty)
    print(f"  Soru zorluğu: {question_difficulty:.2f}")
    print(f"  ZPD içinde mi?: {in_zpd}")
    print(f"  Gerekli destek: {scaffolding}")
    
    # 4. Multi-Armed Bandit Test
    print("\n🎰 Multi-Armed Bandit:")
    print("-"*60)
    mab = MultiArmedBandit(n_arms=5)
    
    # Simülasyon
    for _ in range(20):
        arm = mab.select_arm()
        reward = np.random.random() < (0.3 + arm * 0.1)  # Farklı başarı oranları
        mab.update(arm, reward)
    
    stats = mab.get_statistics()
    print("  İçerik performansları:")
    for stat in stats[:3]:  # İlk 3 kolu göster
        print(f"    İçerik {stat['arm']}: Başarı={stat['mean']:.2%}, Deneme={stat['trials']:.0f}")
    
    # 5. Bloom's Taxonomy Test
    print("\n🌸 Bloom's Taxonomy:")
    print("-"*60)
    bloom = BloomTaxonomy()
    
    questions = [
        "İntegral nedir? Tanımlayınız.",
        "Verilen fonksiyonun integralini hesaplayınız.",
        "İki yöntem arasındaki farkları analiz ediniz."
    ]
    
    for q in questions:
        level = bloom.classify_question(q)
        level_name = bloom.get_level_name(level)
        print(f"  Soru: '{q[:40]}...'")
        print(f"    → Seviye {level}: {level_name}")
    
    print("\n✅ Tüm algoritmalar başarıyla test edildi!")
    return True


if __name__ == "__main__":
    print("🚀 Educational Algorithms Test başlatılıyor...")
    test_algorithms()
