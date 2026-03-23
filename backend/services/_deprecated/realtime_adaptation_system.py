"""
Gerçek Zamanlı Adaptasyon Sistemi (Real-Time Adaptation System)
Task 63: Gerçek Zamanlı Adaptasyon
Requirements: REQ-49.69-49.84

Bu modül adaptif test sistemine gerçek zamanlı adaptasyon özellikleri ekler:
- Real-time theta güncelleme (Subtask 63.1)
- Dinamik zorluk ayarlama (Subtask 63.2)
- Motivasyon desteği (Subtask 63.3)
- Yorgunluk tespiti (Subtask 63.4)
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.stats import norm

from services.adaptive_test_engine import (
    AdaptiveTestEngine,
    TestSession,
    IRTParameters,
)

logger = logging.getLogger(__name__)


@dataclass
class RealtimeMetrics:
    """Gerçek zamanlı metrikler"""

    response_times: List[float] = field(default_factory=list)
    accuracy_history: List[bool] = field(default_factory=list)
    difficulty_history: List[float] = field(default_factory=list)
    success_rate_window: float = 0.5
    avg_response_time: float = 0.0
    response_time_trend: float = 0.0  # Pozitif = yavaşlama
    accuracy_trend: float = 0.0  # Negatif = düşüş
    fatigue_score: float = 0.0  # 0-1 arası, 1 = çok yorgun
    motivation_level: float = 0.5  # 0-1 arası, 1 = çok motive
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class AdaptationDecision:
    """Adaptasyon kararı"""

    decision_type: str  # 'difficulty', 'motivation', 'break', 'continue'
    action: str  # Yapılacak aksiyon
    reason: str  # Karar nedeni
    parameters: Dict  # Ek parametreler
    timestamp: datetime = field(default_factory=datetime.now)


class RealtimeAdaptationSystem:
    """
    Gerçek Zamanlı Adaptasyon Sistemi

    REQ-49.69-49.72: Real-time theta güncelleme
    REQ-49.73-49.76: Dinamik zorluk ayarlama
    REQ-49.77-49.80: Motivasyon desteği
    REQ-49.81-49.84: Yorgunluk tespiti
    """

    def __init__(self, adaptive_engine: Optional[AdaptiveTestEngine] = None):
        """Gerçek zamanlı adaptasyon sistemini başlat"""
        self.adaptive_engine = adaptive_engine or AdaptiveTestEngine()
        self.session_metrics: Dict[str, RealtimeMetrics] = {}

        # Theta güncelleme parametreleri
        self.theta_update_threshold = 0.001  # Minimum değişim
        self.confidence_level = 0.95  # %95 güven aralığı

        # Zorluk ayarlama parametreleri
        self.target_success_rate_min = 0.4  # %40 minimum başarı
        self.target_success_rate_max = 0.8  # %80 maksimum başarı
        self.max_difficulty_change = 1.0  # Maksimum 1 seviye değişim

        # Motivasyon parametreleri
        self.low_motivation_threshold = 0.3
        self.high_motivation_threshold = 0.7

        # Yorgunluk parametreleri
        self.break_interval_minutes = 20  # 20 dakikada bir mola öner
        self.fatigue_threshold = 0.7  # Yorgunluk eşiği

        logger.info("Realtime Adaptation System başlatıldı")

    # ==================== SUBTASK 63.1: Real-time Theta Güncelleme ====================

    def update_theta_realtime(
        self,
        session: TestSession,
        question_params: IRTParameters,
        is_correct: bool,
        response_time: float,
    ) -> Tuple[float, float, float]:
        """
        Her yanıt sonrası theta'yı gerçek zamanlı güncelle.

        REQ-49.69: Real-time theta update - her yanıt sonrası theta güncellemek
        REQ-49.70: Incremental theta estimation - Bayesian update kullanmak
        REQ-49.71: Confidence interval tracking - %95 güven aralığı hesaplamak
        REQ-49.72: 100ms içinde sonuç döndürmek

        Args:
            session: Test oturumu
            question_params: Soru IRT parametreleri
            is_correct: Yanıt doğru mu?
            response_time: Yanıt süresi (saniye)

        Returns:
            (new_theta, standard_error, confidence_interval_width)
        """
        start_time = time.time()

        state = session.knowledge_state
        current_theta = state.theta

        # Incremental Bayesian update (REQ-49.70)
        # Prior: N(current_theta, current_se^2)
        prior_mean = current_theta
        prior_variance = state.standard_error**2

        # Likelihood: P(response | theta, question_params)
        # Fisher Information'dan likelihood variance hesapla
        information = self._calculate_fisher_information(current_theta, question_params)
        likelihood_variance = 1.0 / information if information > 0 else 1.0

        # Posterior: Bayesian update
        # Posterior variance = 1 / (1/prior_var + 1/likelihood_var)
        posterior_variance = 1.0 / (1.0 / prior_variance + 1.0 / likelihood_variance)

        # Posterior mean (ağırlıklı ortalama)
        # Yanıta göre theta shift hesapla
        expected_prob = self._calculate_response_probability(
            current_theta, question_params
        )

        if is_correct:
            # Doğru cevap: theta'yı yukarı çek
            theta_shift = (1.0 - expected_prob) * question_params.a * 0.5
        else:
            # Yanlış cevap: theta'yı aşağı çek
            theta_shift = -expected_prob * question_params.a * 0.5

        # Posterior mean
        posterior_mean = current_theta + theta_shift * posterior_variance

        # Sınırla (-3, +3) (REQ-49.72 ile uyumlu)
        new_theta = max(-3.0, min(3.0, posterior_mean))

        # Standard error
        new_se = np.sqrt(posterior_variance)

        # Confidence interval (%95) (REQ-49.71)
        z_score = norm.ppf((1 + self.confidence_level) / 2)  # 1.96 for 95%
        ci_width = 2 * z_score * new_se

        # Performans kontrolü (REQ-49.72)
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > 100:
            logger.warning(
                f"Theta güncelleme yavaş: {elapsed_ms:.1f}ms > 100ms - "
                f"Session: {session.session_id}"
            )

        logger.debug(
            f"Theta güncellendi - Session: {session.session_id}, "
            f"Old: {current_theta:.3f}, New: {new_theta:.3f}, "
            f"SE: {new_se:.3f}, CI: ±{ci_width/2:.3f}, "
            f"Time: {elapsed_ms:.1f}ms"
        )

        # State'i güncelle
        state.theta = new_theta
        state.standard_error = new_se
        state.theta_history.append(new_theta)

        return new_theta, new_se, ci_width

    def _calculate_fisher_information(
        self, theta: float, params: IRTParameters
    ) -> float:
        """
        Fisher Information hesapla.

        Args:
            theta: Yetenek seviyesi
            params: IRT parametreleri

        Returns:
            Fisher Information değeri
        """
        # 4PL IRT için Fisher Information
        a, b, c, d = params.a, params.b, params.c, params.d

        # P(theta)
        prob = self._calculate_response_probability(theta, params)

        # Q(theta) = 1 - P(theta)
        q_prob = 1.0 - prob

        # P'(theta) türevi
        exp_term = np.exp(-a * (theta - b))
        p_prime = a * (d - c) * exp_term / ((1 + exp_term) ** 2)

        # Fisher Information: I(theta) = [P'(theta)]^2 / [P(theta) * Q(theta)]
        if prob > 0.01 and q_prob > 0.01:  # Numerical stability
            information = (p_prime**2) / (prob * q_prob)
        else:
            information = 0.0

        return information

    def _calculate_response_probability(
        self, theta: float, params: IRTParameters
    ) -> float:
        """
        Yanıt olasılığını hesapla (4PL IRT).

        Args:
            theta: Yetenek seviyesi
            params: IRT parametreleri

        Returns:
            Yanıt olasılığı (0-1 arası)
        """
        a, b, c, d = params.a, params.b, params.c, params.d

        # 4PL IRT formülü
        exp_term = np.exp(-a * (theta - b))
        prob = c + (d - c) / (1 + exp_term)

        return prob

    def track_confidence_interval(self, session: TestSession) -> Dict[str, float]:
        """
        Güven aralığını takip et.

        REQ-49.71: Confidence interval tracking

        Args:
            session: Test oturumu

        Returns:
            Güven aralığı bilgileri
        """
        state = session.knowledge_state

        # %95 güven aralığı
        z_score = norm.ppf((1 + self.confidence_level) / 2)
        margin_of_error = z_score * state.standard_error

        ci_lower = state.theta - margin_of_error
        ci_upper = state.theta + margin_of_error
        ci_width = ci_upper - ci_lower

        return {
            "theta": state.theta,
            "standard_error": state.standard_error,
            "confidence_level": self.confidence_level,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "ci_width": ci_width,
            "margin_of_error": margin_of_error,
        }

    # ==================== SUBTASK 63.2: Zorluk Ayarlama ====================

    def adjust_difficulty_dynamically(
        self, session: TestSession, recent_window: int = 5
    ) -> AdaptationDecision:
        """
        Performansa göre zorluk seviyesini dinamik olarak ayarla.

        REQ-49.73: Dynamic difficulty adjustment - performansa göre zorluk ayarlama
        REQ-49.74: Performance-based scaling - başarı oranına göre ölçekleme
        REQ-49.75: Smooth difficulty transitions - ani zorluk değişimlerini önleme
        REQ-49.76: Maksimum 1 seviye değişim yapma

        Args:
            session: Test oturumu
            recent_window: Son N soruya bakılacak pencere

        Returns:
            Adaptasyon kararı
        """
        # Metrikleri al veya oluştur
        if session.session_id not in self.session_metrics:
            self.session_metrics[session.session_id] = RealtimeMetrics()

        metrics = self.session_metrics[session.session_id]

        # Son N sorunun başarı oranını hesapla (REQ-49.74)
        if len(metrics.accuracy_history) < recent_window:
            # Yeterli veri yok, değişiklik yapma
            return AdaptationDecision(
                decision_type="difficulty",
                action="maintain",
                reason="insufficient_data",
                parameters={"current_success_rate": metrics.success_rate_window},
            )

        recent_responses = metrics.accuracy_history[-recent_window:]
        success_rate = sum(recent_responses) / len(recent_responses)

        # Mevcut zorluk seviyesi
        if metrics.difficulty_history:
            current_difficulty = metrics.difficulty_history[-1]
        else:
            current_difficulty = session.knowledge_state.theta

        # Zorluk ayarlama kararı (REQ-49.73, REQ-49.74)
        if success_rate < self.target_success_rate_min:
            # Çok düşük başarı - zorluğu azalt
            difficulty_change = -0.5  # Orta seviye azaltma
            action = "decrease"
            reason = f"low_success_rate_{success_rate:.2f}"

        elif success_rate > self.target_success_rate_max:
            # Çok yüksek başarı - zorluğu artır
            difficulty_change = 0.5  # Orta seviye artırma
            action = "increase"
            reason = f"high_success_rate_{success_rate:.2f}"

        else:
            # Optimal aralıkta - değişiklik yapma
            difficulty_change = 0.0
            action = "maintain"
            reason = f"optimal_success_rate_{success_rate:.2f}"

        # Smooth transitions (REQ-49.75, REQ-49.76)
        # Maksimum 1 seviye değişim
        difficulty_change = max(
            -self.max_difficulty_change,
            min(self.max_difficulty_change, difficulty_change),
        )

        # Yeni zorluk seviyesi
        new_difficulty = current_difficulty + difficulty_change
        new_difficulty = max(-3.0, min(3.0, new_difficulty))  # Sınırla

        # Metrikleri güncelle
        metrics.difficulty_history.append(new_difficulty)
        metrics.success_rate_window = success_rate

        logger.info(
            f"Zorluk ayarlandı - Session: {session.session_id}, "
            f"Success Rate: {success_rate:.2f}, "
            f"Old Difficulty: {current_difficulty:.2f}, "
            f"New Difficulty: {new_difficulty:.2f}, "
            f"Change: {difficulty_change:+.2f}, "
            f"Action: {action}"
        )

        return AdaptationDecision(
            decision_type="difficulty",
            action=action,
            reason=reason,
            parameters={
                "old_difficulty": current_difficulty,
                "new_difficulty": new_difficulty,
                "difficulty_change": difficulty_change,
                "success_rate": success_rate,
                "target_min": self.target_success_rate_min,
                "target_max": self.target_success_rate_max,
            },
        )

    def scale_difficulty_by_performance(
        self, session: TestSession, target_difficulty: float
    ) -> float:
        """
        Performansa göre zorluk ölçekle.

        REQ-49.74: Performance-based scaling

        Args:
            session: Test oturumu
            target_difficulty: Hedef zorluk seviyesi

        Returns:
            Ölçeklenmiş zorluk seviyesi
        """
        state = session.knowledge_state

        # Öğrenci yetenek seviyesi ile hedef zorluk arasındaki fark
        difficulty_gap = target_difficulty - state.theta

        # Başarı oranına göre ölçekleme faktörü
        if state.responses_count > 0:
            success_rate = state.correct_count / state.responses_count

            if success_rate < 0.4:
                # Düşük başarı - zorluğu azalt
                scaling_factor = 0.7
            elif success_rate > 0.8:
                # Yüksek başarı - zorluğu artır
                scaling_factor = 1.3
            else:
                # Normal - değiştirme
                scaling_factor = 1.0
        else:
            scaling_factor = 1.0

        # Ölçeklenmiş zorluk
        scaled_difficulty = state.theta + (difficulty_gap * scaling_factor)
        scaled_difficulty = max(-3.0, min(3.0, scaled_difficulty))

        return scaled_difficulty

    def ensure_smooth_transitions(
        self,
        current_difficulty: float,
        target_difficulty: float,
        max_change: float = 1.0,
    ) -> float:
        """
        Ani zorluk değişimlerini önle.

        REQ-49.75: Smooth difficulty transitions
        REQ-49.76: Maksimum 1 seviye değişim

        Args:
            current_difficulty: Mevcut zorluk
            target_difficulty: Hedef zorluk
            max_change: Maksimum değişim miktarı

        Returns:
            Yumuşatılmış zorluk seviyesi
        """
        difficulty_change = target_difficulty - current_difficulty

        # Maksimum değişimi sınırla (REQ-49.76)
        if abs(difficulty_change) > max_change:
            if difficulty_change > 0:
                smoothed_difficulty = current_difficulty + max_change
            else:
                smoothed_difficulty = current_difficulty - max_change
        else:
            smoothed_difficulty = target_difficulty

        logger.debug(
            f"Zorluk yumuşatıldı - Current: {current_difficulty:.2f}, "
            f"Target: {target_difficulty:.2f}, "
            f"Smoothed: {smoothed_difficulty:.2f}, "
            f"Max Change: {max_change:.2f}"
        )

        return smoothed_difficulty

    # ==================== SUBTASK 63.3: Motivasyon Desteği ====================

    def monitor_success_rate(
        self, session: TestSession, window_size: int = 10
    ) -> Dict[str, float]:
        """
        Başarı oranını izle ve motivasyon seviyesini hesapla.

        REQ-49.77: Success rate monitoring - başarı oranını %40-80 aralığında tutma
        REQ-49.78: Encouragement messages - pozitif pekiştirme sunma
        REQ-49.79: Achievement celebrations - milestone'larda kutlama gösterme
        REQ-49.80: Destek mesajları gösterme

        Args:
            session: Test oturumu
            window_size: Başarı oranı penceresi

        Returns:
            Motivasyon metrikleri
        """
        # Metrikleri al
        if session.session_id not in self.session_metrics:
            self.session_metrics[session.session_id] = RealtimeMetrics()

        metrics = self.session_metrics[session.session_id]

        # Son N sorunun başarı oranı
        if len(metrics.accuracy_history) >= window_size:
            recent_responses = metrics.accuracy_history[-window_size:]
            success_rate = sum(recent_responses) / len(recent_responses)
        elif len(metrics.accuracy_history) > 0:
            success_rate = sum(metrics.accuracy_history) / len(metrics.accuracy_history)
        else:
            success_rate = 0.5  # Varsayılan

        # Motivasyon seviyesi hesapla
        # Optimal aralıkta (%40-80) ise yüksek motivasyon (REQ-49.77)
        if self.target_success_rate_min <= success_rate <= self.target_success_rate_max:
            motivation_level = 0.8  # Yüksek motivasyon
        elif success_rate < self.target_success_rate_min:
            # Düşük başarı - motivasyon düşebilir
            motivation_level = 0.3 + (success_rate / self.target_success_rate_min) * 0.3
        else:
            # Çok yüksek başarı - sıkılma riski
            motivation_level = 0.6

        metrics.motivation_level = motivation_level

        # Streak hesapla (ardışık doğru cevaplar)
        streak = 0
        for response in reversed(metrics.accuracy_history):
            if response:
                streak += 1
            else:
                break

        return {
            "success_rate": success_rate,
            "motivation_level": motivation_level,
            "streak": streak,
            "total_correct": sum(metrics.accuracy_history),
            "total_questions": len(metrics.accuracy_history),
            "target_min": self.target_success_rate_min,
            "target_max": self.target_success_rate_max,
        }

    def generate_encouragement_message(
        self, session: TestSession, motivation_metrics: Dict
    ) -> Optional[str]:
        """
        Pozitif pekiştirme mesajı oluştur.

        REQ-49.78: Encouragement messages - pozitif pekiştirme

        Args:
            session: Test oturumu
            motivation_metrics: Motivasyon metrikleri

        Returns:
            Teşvik mesajı veya None
        """
        success_rate = motivation_metrics["success_rate"]
        streak = motivation_metrics["streak"]
        motivation_level = motivation_metrics["motivation_level"]

        # Düşük motivasyon - destek mesajı (REQ-49.80)
        if motivation_level < self.low_motivation_threshold:
            messages = [
                "Devam et! Her soru seni hedefe yaklaştırıyor. 💪",
                "Zorlandığın konuları tespit ediyoruz. Birlikte başaracağız! 🎯",
                "Öğrenme bir süreç. Sen harika gidiyorsun! ⭐",
                "Hatalar öğrenmenin bir parçası. Devam et! 🚀",
            ]
            return np.random.choice(messages)

        # Streak kutlaması (REQ-49.79)
        if streak >= 5:
            messages = [
                f"Harika! {streak} ardışık doğru cevap! 🔥",
                f"Muhteşem bir seri: {streak} doğru! Devam et! 🌟",
                f"İnanılmaz! {streak} soru üst üste doğru! 🎉",
            ]
            return np.random.choice(messages)

        # Yüksek başarı oranı kutlaması (REQ-49.79)
        if success_rate >= 0.8:
            messages = [
                "Mükemmel performans! %{:.0f} başarı oranı! 🏆".format(
                    success_rate * 100
                ),
                "Harika gidiyorsun! Başarı oranın çok yüksek! ⭐",
                "Süpersin! Bu konuyu çok iyi kavramışsın! 🎯",
            ]
            return np.random.choice(messages)

        # Orta seviye teşvik (REQ-49.78)
        if success_rate >= 0.5:
            messages = [
                "İyi gidiyorsun! Devam et! 👍",
                "Güzel! Doğru yoldasın! 🎯",
                "Harika! İlerlemen çok iyi! ⭐",
            ]
            return np.random.choice(messages)

        return None

    def celebrate_achievement(
        self, session: TestSession, achievement_type: str
    ) -> Dict:
        """
        Başarı kutlaması oluştur.

        REQ-49.79: Achievement celebrations - milestone'larda kutlama

        Args:
            session: Test oturumu
            achievement_type: Başarı tipi (streak, milestone, mastery)

        Returns:
            Kutlama bilgileri
        """
        state = session.knowledge_state

        celebrations = {
            "streak_5": {
                "title": "5 Ardışık Doğru! 🔥",
                "message": "Harika bir seri yakaladın! Devam et!",
                "badge": "fire_streak",
                "points": 50,
            },
            "streak_10": {
                "title": "10 Ardışık Doğru! 🌟",
                "message": "İnanılmaz! Muhteşem bir performans!",
                "badge": "star_streak",
                "points": 100,
            },
            "milestone_10": {
                "title": "10 Soru Tamamlandı! 🎯",
                "message": "İlk 10 soruyu geride bıraktın!",
                "badge": "milestone_10",
                "points": 25,
            },
            "milestone_25": {
                "title": "25 Soru Tamamlandı! 🏆",
                "message": "Çeyrek yolu geçtin! Harikasın!",
                "badge": "milestone_25",
                "points": 50,
            },
            "milestone_50": {
                "title": "50 Soru Tamamlandı! 👑",
                "message": "Yarı yolu geçtin! Muhteşem bir çaba!",
                "badge": "milestone_50",
                "points": 100,
            },
            "mastery": {
                "title": "Konu Hakimiyeti! 🎓",
                "message": "Bu konuyu mükemmel şekilde kavradın!",
                "badge": "mastery",
                "points": 200,
            },
            "theta_improvement": {
                "title": "Seviye Atladın! 📈",
                "message": f"Yetenek seviyeni artırdın! Yeni seviye: {state.theta:.1f}",
                "badge": "level_up",
                "points": 75,
            },
        }

        celebration = celebrations.get(
            achievement_type,
            {
                "title": "Başarı! 🎉",
                "message": "Harika bir iş çıkardın!",
                "badge": "achievement",
                "points": 25,
            },
        )

        logger.info(
            f"Başarı kutlaması - Session: {session.session_id}, "
            f"Type: {achievement_type}, Points: {celebration['points']}"
        )

        return celebration

    def provide_support_message(
        self, session: TestSession, difficulty_level: str
    ) -> str:
        """
        Destek mesajı sağla.

        REQ-49.80: Destek mesajları gösterme

        Args:
            session: Test oturumu
            difficulty_level: Zorluk seviyesi (low, medium, high)

        Returns:
            Destek mesajı
        """
        support_messages = {
            "low": [
                "Zorlandığın konuları tespit ettik. Sana özel çalışma materyalleri hazırlıyoruz. 📚",
                "Endişelenme! Herkes farklı hızda öğrenir. Sen kendi hızında ilerliyorsun. 🌱",
                "Bu konuyu birlikte çalışalım. Adım adım ilerleyeceğiz. 🎯",
                "Hatalar öğrenmenin en önemli parçası. Devam et! 💪",
            ],
            "medium": [
                "İyi gidiyorsun! Biraz daha pratikle mükemmel olacaksın. 👍",
                "Doğru yoldasın! Devam et, başarıya çok yakınsın. ⭐",
                "Güzel ilerleme! Birkaç konu daha çalışalım. 📖",
            ],
            "high": [
                "Harika performans! Zorluğu artırıyoruz. 🚀",
                "Mükemmel! Daha zorlu sorulara hazır mısın? 🎯",
                "Süpersin! Seviyeni yükseltiyoruz. 🏆",
            ],
        }

        messages = support_messages.get(difficulty_level, support_messages["medium"])
        return np.random.choice(messages)

    # ==================== SUBTASK 63.4: Yorgunluk Tespiti ====================

    def analyze_response_time(
        self, session: TestSession, recent_window: int = 10
    ) -> Dict[str, float]:
        """
        Yanıt sürelerini analiz et ve yorgunluk tespiti yap.

        REQ-49.81: Response time analysis - yanıt sürelerini izleme
        REQ-49.82: Accuracy decline detection - doğruluk düşüşünü tespit etme
        REQ-49.83: Break recommendations - 20 dakikada bir mola önerme
        REQ-49.84: Yorgunluk tespit edildiğinde zorluk seviyesini geçici düşürme

        Args:
            session: Test oturumu
            recent_window: Analiz penceresi

        Returns:
            Yanıt süresi analizi
        """
        # Metrikleri al
        if session.session_id not in self.session_metrics:
            self.session_metrics[session.session_id] = RealtimeMetrics()

        metrics = self.session_metrics[session.session_id]

        if len(metrics.response_times) < 2:
            return {
                "avg_response_time": 0.0,
                "response_time_trend": 0.0,
                "fatigue_detected": False,
            }

        # Ortalama yanıt süresi (REQ-49.81)
        if len(metrics.response_times) >= recent_window:
            recent_times = metrics.response_times[-recent_window:]
        else:
            recent_times = metrics.response_times

        avg_response_time = np.mean(recent_times)

        # Yanıt süresi trendi (yavaşlama tespiti) (REQ-49.81)
        if len(recent_times) >= 5:
            # İlk yarı vs son yarı karşılaştırması
            mid_point = len(recent_times) // 2
            first_half_avg = np.mean(recent_times[:mid_point])
            second_half_avg = np.mean(recent_times[mid_point:])

            # Pozitif trend = yavaşlama
            response_time_trend = (
                (second_half_avg - first_half_avg) / first_half_avg
                if first_half_avg > 0
                else 0.0
            )
        else:
            response_time_trend = 0.0

        metrics.avg_response_time = avg_response_time
        metrics.response_time_trend = response_time_trend

        # Yorgunluk tespiti
        # Yavaşlama > %30 veya ortalama süre > 60 saniye
        fatigue_detected = response_time_trend > 0.3 or avg_response_time > 60.0

        return {
            "avg_response_time": avg_response_time,
            "response_time_trend": response_time_trend,
            "fatigue_detected": fatigue_detected,
            "recent_times": recent_times,
        }

    def detect_accuracy_decline(
        self, session: TestSession, window_size: int = 10
    ) -> Dict[str, any]:
        """
        Doğruluk düşüşünü tespit et.

        REQ-49.82: Accuracy decline detection - doğruluk düşüşünü tespit etme

        Args:
            session: Test oturumu
            window_size: Analiz penceresi

        Returns:
            Doğruluk analizi
        """
        # Metrikleri al
        if session.session_id not in self.session_metrics:
            self.session_metrics[session.session_id] = RealtimeMetrics()

        metrics = self.session_metrics[session.session_id]

        if len(metrics.accuracy_history) < window_size:
            return {
                "accuracy_trend": 0.0,
                "decline_detected": False,
                "current_accuracy": 0.5,
            }

        # Son N sorunun doğruluğu
        recent_accuracy = metrics.accuracy_history[-window_size:]

        # İlk yarı vs son yarı karşılaştırması
        mid_point = len(recent_accuracy) // 2
        first_half_accuracy = sum(recent_accuracy[:mid_point]) / mid_point
        second_half_accuracy = sum(recent_accuracy[mid_point:]) / (
            len(recent_accuracy) - mid_point
        )

        # Negatif trend = düşüş
        accuracy_trend = second_half_accuracy - first_half_accuracy

        metrics.accuracy_trend = accuracy_trend

        # Düşüş tespiti: %20'den fazla düşüş
        decline_detected = accuracy_trend < -0.2

        return {
            "accuracy_trend": accuracy_trend,
            "decline_detected": decline_detected,
            "current_accuracy": second_half_accuracy,
            "first_half_accuracy": first_half_accuracy,
            "second_half_accuracy": second_half_accuracy,
        }

    def recommend_break(self, session: TestSession) -> Optional[Dict]:
        """
        Mola önerisi yap.

        REQ-49.83: Break recommendations - 20 dakikada bir mola önerme

        Args:
            session: Test oturumu

        Returns:
            Mola önerisi veya None
        """
        # Metrikleri al
        if session.session_id not in self.session_metrics:
            return None

        metrics = self.session_metrics[session.session_id]

        # Son güncelleme zamanından bu yana geçen süre
        elapsed_time = (
            datetime.now() - session.start_time
        ).total_seconds() / 60.0  # dakika

        # 20 dakikada bir mola öner (REQ-49.83)
        if elapsed_time >= self.break_interval_minutes:
            # Yorgunluk skorunu hesapla
            response_analysis = self.analyze_response_time(session)
            accuracy_analysis = self.detect_accuracy_decline(session)

            # Yorgunluk skoru (0-1 arası)
            fatigue_score = 0.0

            # Yanıt süresi yavaşlaması
            if response_analysis["response_time_trend"] > 0:
                fatigue_score += min(0.5, response_analysis["response_time_trend"])

            # Doğruluk düşüşü
            if accuracy_analysis["accuracy_trend"] < 0:
                fatigue_score += min(0.5, abs(accuracy_analysis["accuracy_trend"]))

            metrics.fatigue_score = fatigue_score

            # Yorgunluk eşiğini aştı mı? (REQ-49.83)
            if fatigue_score >= self.fatigue_threshold:
                logger.info(
                    f"Mola önerisi - Session: {session.session_id}, "
                    f"Elapsed: {elapsed_time:.1f} min, "
                    f"Fatigue Score: {fatigue_score:.2f}"
                )

                return {
                    "recommendation": "break",
                    "reason": "fatigue_detected",
                    "elapsed_time_minutes": elapsed_time,
                    "fatigue_score": fatigue_score,
                    "message": "20 dakikadır çalışıyorsun. 5 dakika mola vermek ister misin? ☕",
                    "break_duration_minutes": 5,
                }

        return None

    def adjust_difficulty_for_fatigue(
        self, session: TestSession, current_difficulty: float
    ) -> float:
        """
        Yorgunluk tespit edildiğinde zorluğu geçici olarak düşür.

        REQ-49.84: Yorgunluk tespit edildiğinde zorluk seviyesini geçici düşürme

        Args:
            session: Test oturumu
            current_difficulty: Mevcut zorluk seviyesi

        Returns:
            Ayarlanmış zorluk seviyesi
        """
        # Metrikleri al
        if session.session_id not in self.session_metrics:
            return current_difficulty

        metrics = self.session_metrics[session.session_id]

        # Yorgunluk skoru yüksekse zorluğu düşür (REQ-49.84)
        if metrics.fatigue_score >= self.fatigue_threshold:
            # Yorgunluk seviyesine göre zorluk azaltma
            difficulty_reduction = metrics.fatigue_score * 0.5  # Maksimum 0.5 azaltma
            adjusted_difficulty = current_difficulty - difficulty_reduction

            # Sınırla
            adjusted_difficulty = max(-3.0, min(3.0, adjusted_difficulty))

            logger.info(
                f"Zorluk yorgunluk için azaltıldı - Session: {session.session_id}, "
                f"Original: {current_difficulty:.2f}, "
                f"Adjusted: {adjusted_difficulty:.2f}, "
                f"Fatigue Score: {metrics.fatigue_score:.2f}"
            )

            return adjusted_difficulty

        return current_difficulty

    def calculate_fatigue_score(self, session: TestSession) -> float:
        """
        Yorgunluk skorunu hesapla.

        Args:
            session: Test oturumu

        Returns:
            Yorgunluk skoru (0-1 arası)
        """
        # Yanıt süresi analizi
        response_analysis = self.analyze_response_time(session)

        # Doğruluk analizi
        accuracy_analysis = self.detect_accuracy_decline(session)

        # Yorgunluk skoru bileşenleri
        fatigue_components = []

        # 1. Yanıt süresi yavaşlaması (0-0.4 arası)
        if response_analysis["response_time_trend"] > 0:
            time_fatigue = min(0.4, response_analysis["response_time_trend"])
            fatigue_components.append(time_fatigue)

        # 2. Doğruluk düşüşü (0-0.4 arası)
        if accuracy_analysis["accuracy_trend"] < 0:
            accuracy_fatigue = min(0.4, abs(accuracy_analysis["accuracy_trend"]))
            fatigue_components.append(accuracy_fatigue)

        # 3. Süre faktörü (0-0.2 arası)
        elapsed_minutes = (datetime.now() - session.start_time).total_seconds() / 60.0
        if elapsed_minutes > self.break_interval_minutes:
            time_factor = min(
                0.2,
                (elapsed_minutes - self.break_interval_minutes)
                / self.break_interval_minutes
                * 0.2,
            )
            fatigue_components.append(time_factor)

        # Toplam yorgunluk skoru
        fatigue_score = sum(fatigue_components)
        fatigue_score = min(1.0, fatigue_score)  # Maksimum 1.0

        return fatigue_score

    # ==================== Yardımcı Metodlar ====================

    def update_session_metrics(
        self, session: TestSession, response_time: float, is_correct: bool
    ):
        """
        Oturum metriklerini güncelle.

        Args:
            session: Test oturumu
            response_time: Yanıt süresi (saniye)
            is_correct: Doğru mu?
        """
        if session.session_id not in self.session_metrics:
            self.session_metrics[session.session_id] = RealtimeMetrics()

        metrics = self.session_metrics[session.session_id]

        # Yanıt süresi ve doğruluğu kaydet
        metrics.response_times.append(response_time)
        metrics.accuracy_history.append(is_correct)

        # Son güncelleme zamanı
        metrics.last_update = datetime.now()

        logger.debug(
            f"Metrikler güncellendi - Session: {session.session_id}, "
            f"Response Time: {response_time:.1f}s, Correct: {is_correct}"
        )

    def get_adaptation_summary(self, session: TestSession) -> Dict:
        """
        Adaptasyon özetini al.

        Args:
            session: Test oturumu

        Returns:
            Adaptasyon özeti
        """
        if session.session_id not in self.session_metrics:
            return {}

        metrics = self.session_metrics[session.session_id]

        # Motivasyon metrikleri
        motivation_metrics = self.monitor_success_rate(session)

        # Yorgunluk analizi
        response_analysis = self.analyze_response_time(session)
        accuracy_analysis = self.detect_accuracy_decline(session)

        # Mola önerisi
        break_recommendation = self.recommend_break(session)

        return {
            "session_id": session.session_id,
            "theta": session.knowledge_state.theta,
            "standard_error": session.knowledge_state.standard_error,
            "success_rate": motivation_metrics["success_rate"],
            "motivation_level": metrics.motivation_level,
            "fatigue_score": metrics.fatigue_score,
            "avg_response_time": metrics.avg_response_time,
            "response_time_trend": metrics.response_time_trend,
            "accuracy_trend": metrics.accuracy_trend,
            "break_recommended": break_recommendation is not None,
            "break_recommendation": break_recommendation,
            "questions_count": len(session.questions_administered),
            "elapsed_time_minutes": (
                datetime.now() - session.start_time
            ).total_seconds()
            / 60.0,
        }
