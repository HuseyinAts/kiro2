"""
Adaptif Test Motoru (Adaptive Test Engine)
Task 60: Adaptif Test Motoru
Requirements: REQ-49.17-49.32

Bu modül adaptif test sisteminin çekirdeğini oluşturur:
- Maximum Information Criterion ile soru seçimi
- Bayesian Knowledge Tracing
- EAP/MLE theta estimation
- Stopping rules (fixed-length, precision-based, classification-based)
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import norm

from services.irt_psychometric_analysis import IRTParameters, IRTPsychometricAnalysis

logger = logging.getLogger(__name__)


@dataclass
class QuestionCandidate:
    """Soru adayı bilgileri"""

    question_id: str
    irt_params: IRTParameters
    subject: str
    topic: str
    difficulty_level: str
    exposure_count: int
    last_used: datetime | None
    information_value: float = 0.0
    content_balance_score: float = 0.0
    total_score: float = 0.0


@dataclass
class StudentKnowledgeState:
    """Öğrenci bilgi durumu (Bayesian Knowledge Tracing)"""

    student_id: str
    theta: float  # Mevcut yetenek tahmini
    theta_history: list[float]  # Theta geçmişi
    standard_error: float  # Tahmin hatası
    knowledge_probability: float  # Bilgi olasılığı (0-1)
    learning_rate: float  # Öğrenme hızı
    guess_probability: float  # Tahmin olasılığı
    slip_probability: float  # Hata yapma olasılığı
    responses_count: int  # Toplam yanıt sayısı
    correct_count: int  # Doğru yanıt sayısı


@dataclass
class TestSession:
    """Test oturumu bilgileri"""

    session_id: str
    student_id: str
    test_type: str  # diagnostic, formative, summative, benchmark, mock
    start_time: datetime
    current_question_index: int
    questions_administered: list[str]
    responses: list[dict]
    knowledge_state: StudentKnowledgeState
    content_coverage: dict[str, int]  # Konu bazlı soru sayısı
    is_complete: bool = False
    completion_reason: str | None = None


class AdaptiveTestEngine:
    """
    Adaptif Test Motoru

    REQ-49.17-49.20: Maximum Information Criterion
    REQ-49.21-49.24: Bayesian Knowledge Tracing
    REQ-49.25-49.28: EAP/MLE theta estimation
    REQ-49.29-49.32: Stopping rules
    """

    def __init__(self):
        """Adaptif Test Motoru başlat"""
        self.irt_service = IRTPsychometricAnalysis()
        self.active_sessions: dict[str, TestSession] = {}

        # Stopping rule parametreleri
        self.fixed_length_min = 10  # Minimum soru sayısı
        self.fixed_length_max = 50  # Maksimum soru sayısı (REQ-49.32)
        self.precision_threshold = 0.3  # SE < 0.3 (REQ-49.30)

        # Content balancing parametreleri
        self.content_balance_weight = 0.3  # İçerik dengesi ağırlığı
        self.information_weight = 0.7  # Bilgi değeri ağırlığı

        # Exposure control parametreleri
        self.max_exposure_rate = 0.2  # Maksimum %20 maruz kalma

        logger.info("Adaptive Test Engine başlatıldı")

    # ==================== SUBTASK 60.1: Maximum Information Criterion ====================

    def select_next_question(
        self,
        session: TestSession,
        question_pool: list[QuestionCandidate],
        content_constraints: dict[str, int] | None = None,
    ) -> QuestionCandidate | None:
        """
        Maximum Information Criterion ile bir sonraki soruyu seç.

        REQ-49.17: Maximum Information Criterion - en bilgilendirici soruyu seçme
        REQ-49.18: Information maximization - mevcut theta tahminine göre optimize etme
        REQ-49.19: Content balancing constraints - konu dağılımını dengeleme
        REQ-49.20: 500ms içinde karar verme

        Args:
            session: Test oturumu
            question_pool: Soru havuzu
            content_constraints: Konu bazlı minimum soru sayıları

        Returns:
            Seçilen soru veya None
        """
        start_time = datetime.now()

        if not question_pool:
            logger.warning(f"Boş soru havuzu - Session: {session.session_id}")
            return None

        # Mevcut theta tahmini
        current_theta = session.knowledge_state.theta

        # Her soru için information value hesapla (REQ-49.17, REQ-49.18)
        for candidate in question_pool:
            # Fisher Information hesapla
            candidate.information_value = self.irt_service.calculate_information(
                theta=current_theta, params=candidate.irt_params
            )

            # Content balance score hesapla (REQ-49.19)
            candidate.content_balance_score = self._calculate_content_balance_score(
                candidate, session, content_constraints
            )

            # Exposure penalty uygula
            exposure_penalty = self._calculate_exposure_penalty(candidate)

            # Toplam skor
            candidate.total_score = (
                self.information_weight * candidate.information_value
                + self.content_balance_weight * candidate.content_balance_score
            ) * exposure_penalty

        # En yüksek skora sahip soruyu seç
        selected = max(question_pool, key=lambda q: q.total_score)

        # Performans kontrolü (REQ-49.20)
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        if elapsed_ms > 500:
            logger.warning(
                f"Soru seçimi yavaş: {elapsed_ms:.1f}ms > 500ms - "
                f"Session: {session.session_id}"
            )

        logger.info(
            f"Soru seçildi - ID: {selected.question_id}, "
            f"Info: {selected.information_value:.3f}, "
            f"Content: {selected.content_balance_score:.3f}, "
            f"Total: {selected.total_score:.3f}, "
            f"Time: {elapsed_ms:.1f}ms"
        )

        return selected

    def _calculate_content_balance_score(
        self,
        candidate: QuestionCandidate,
        session: TestSession,
        content_constraints: dict[str, int] | None,
    ) -> float:
        """
        İçerik dengesi skorunu hesapla.

        REQ-49.19: Content balancing constraints

        Args:
            candidate: Soru adayı
            session: Test oturumu
            content_constraints: Konu bazlı minimum soru sayıları

        Returns:
            Content balance skoru (0-1 arası)
        """
        if not content_constraints:
            return 1.0  # Kısıt yoksa tam skor

        topic = candidate.topic
        current_count = session.content_coverage.get(topic, 0)
        required_count = content_constraints.get(topic, 0)

        # Eksik olan konulara öncelik ver
        if current_count < required_count:
            # Eksiklik oranına göre skor
            deficit = required_count - current_count
            return 1.0 + (deficit / required_count)  # Bonus skor
        # Yeterli kapsama varsa düşük skor
        return 0.5

    def _calculate_exposure_penalty(self, candidate: QuestionCandidate) -> float:
        """
        Exposure penalty hesapla (sık kullanılan soruları cezalandır).

        Args:
            candidate: Soru adayı

        Returns:
            Penalty çarpanı (0-1 arası)
        """
        # Basitleştirilmiş exposure control
        # Gerçek implementasyonda Sympson-Hetter metodu kullanılır
        if candidate.exposure_count == 0:
            return 1.0

        # Exposure rate hesapla
        # Burada toplam test sayısını bilmediğimiz için basit bir yaklaşım
        exposure_rate = min(1.0, candidate.exposure_count / 100.0)

        if exposure_rate > self.max_exposure_rate:
            # Aşırı maruz kalmış sorular için ceza
            penalty = 1.0 - (exposure_rate - self.max_exposure_rate)
            return max(0.1, penalty)  # Minimum %10 şans ver

        return 1.0

    # ==================== SUBTASK 60.2: Bayesian Knowledge Tracing ====================

    def initialize_knowledge_state(
        self,
        student_id: str,
        prior_theta: float = 0.0,
        prior_knowledge_prob: float = 0.5,
    ) -> StudentKnowledgeState:
        """
        Öğrenci bilgi durumunu başlat.

        REQ-49.21: Prior knowledge estimation

        Args:
            student_id: Öğrenci ID'si
            prior_theta: Önceki theta tahmini (varsayılan 0.0 - orta seviye)
            prior_knowledge_prob: Önceki bilgi olasılığı

        Returns:
            Başlangıç bilgi durumu
        """
        return StudentKnowledgeState(
            student_id=student_id,
            theta=prior_theta,
            theta_history=[prior_theta],
            standard_error=1.0,  # Yüksek belirsizlik
            knowledge_probability=prior_knowledge_prob,
            learning_rate=0.1,  # Varsayılan öğrenme hızı
            guess_probability=0.25,  # 4 seçenekli soru için
            slip_probability=0.1,  # Hata yapma olasılığı
            responses_count=0,
            correct_count=0,
        )

    def update_knowledge_state(
        self,
        state: StudentKnowledgeState,
        question_params: IRTParameters,
        is_correct: bool,
    ) -> StudentKnowledgeState:
        """
        Yanıta göre bilgi durumunu güncelle (Bayesian Knowledge Tracing).

        REQ-49.22: Posterior update algorithm - her yanıt sonrası güncelleme
        REQ-49.23: Knowledge state tracking - öğrenme, unutma, tahmin ve hata parametreleri
        REQ-49.24: Hidden Markov Model kullanımı

        Args:
            state: Mevcut bilgi durumu
            question_params: Soru IRT parametreleri
            is_correct: Yanıt doğru mu?

        Returns:
            Güncellenmiş bilgi durumu
        """
        # BKT parametreleri (REQ-49.23)
        P_L = state.knowledge_probability  # Bilme olasılığı
        P_T = state.learning_rate  # Öğrenme (transition) olasılığı
        P_G = state.guess_probability  # Tahmin olasılığı
        P_S = state.slip_probability  # Hata (slip) olasılığı

        # Posterior update (REQ-49.22, REQ-49.24)
        if is_correct:
            # Doğru cevap verildi
            # P(L|correct) = P(L) * (1 - P_S) / [P(L) * (1 - P_S) + (1 - P(L)) * P_G]
            numerator = P_L * (1 - P_S)
            denominator = P_L * (1 - P_S) + (1 - P_L) * P_G
        else:
            # Yanlış cevap verildi
            # P(L|incorrect) = P(L) * P_S / [P(L) * P_S + (1 - P(L)) * (1 - P_G)]
            numerator = P_L * P_S
            denominator = P_L * P_S + (1 - P_L) * (1 - P_G)

        if denominator > 0:
            P_L_updated = numerator / denominator
        else:
            P_L_updated = P_L

        # Öğrenme ile güncelleme (transition)
        # P(L_new) = P(L_updated) + (1 - P(L_updated)) * P_T
        P_L_new = P_L_updated + (1 - P_L_updated) * P_T

        # Theta güncelleme (IRT tabanlı)
        state.responses_count += 1
        if is_correct:
            state.correct_count += 1

        # EAP/MLE ile theta güncelle (sonraki subtask'ta detaylı)
        new_theta = self._update_theta_simple(state, question_params, is_correct)

        # Güncellenen state
        state.knowledge_probability = P_L_new
        state.theta = new_theta
        state.theta_history.append(new_theta)

        logger.debug(
            f"Knowledge state güncellendi - Student: {state.student_id}, "
            f"P(L): {P_L:.3f} -> {P_L_new:.3f}, "
            f"Theta: {state.theta_history[-2]:.3f} -> {new_theta:.3f}"
        )

        return state

    def _update_theta_simple(
        self,
        state: StudentKnowledgeState,
        question_params: IRTParameters,
        is_correct: bool,
    ) -> float:
        """
        Basit theta güncelleme (EAP/MLE detayları subtask 60.3'te).

        Args:
            state: Bilgi durumu
            question_params: Soru parametreleri
            is_correct: Doğru mu?

        Returns:
            Güncellenmiş theta
        """
        # Basit güncelleme: doğru cevap theta'yı artırır, yanlış azaltır
        current_theta = state.theta
        difficulty = question_params.b

        # Adaptasyon miktarı (öğrenme hızına bağlı)
        adaptation = state.learning_rate * (difficulty - current_theta)

        if is_correct:
            new_theta = current_theta + abs(adaptation) * 0.5
        else:
            new_theta = current_theta - abs(adaptation) * 0.5

        # Sınırla
        new_theta = max(-3.0, min(3.0, new_theta))

        return new_theta

    # ==================== SUBTASK 60.3: EAP/MLE Theta Estimation ====================

    def estimate_theta_eap(
        self, responses: list[dict], prior_mean: float = 0.0, prior_sd: float = 1.0
    ) -> tuple[float, float]:
        """
        Expected A Posteriori (EAP) metodu ile theta tahmini.

        REQ-49.25: Expected A Posteriori (EAP) method
        REQ-49.27: Standard error < 0.3 hedefleme
        REQ-49.28: -3 ile +3 arası değer üretme

        Args:
            responses: Yanıt listesi [{'params': IRTParameters, 'is_correct': bool}, ...]
            prior_mean: Prior dağılım ortalaması
            prior_sd: Prior dağılım standart sapması

        Returns:
            (theta_estimate, standard_error)
        """
        if not responses:
            return prior_mean, prior_sd

        # Theta grid oluştur (-3 ile +3 arası) (REQ-49.28)
        theta_grid = np.linspace(-3.0, 3.0, 61)

        # Prior dağılım
        prior_probs = norm.pdf(theta_grid, loc=prior_mean, scale=prior_sd)

        # Likelihood hesapla
        likelihood = np.ones_like(theta_grid)

        for response in responses:
            params = response["params"]
            is_correct = response["is_correct"]

            # Her theta değeri için olasılık
            for i, theta in enumerate(theta_grid):
                prob = self.irt_service.calculate_probability(theta, params)

                if is_correct:
                    likelihood[i] *= prob
                else:
                    likelihood[i] *= 1 - prob

        # Posterior dağılım
        posterior = prior_probs * likelihood
        posterior = posterior / np.sum(posterior)  # Normalize

        # EAP estimate (posterior'un beklenen değeri)
        theta_eap = np.sum(theta_grid * posterior)

        # Standard error (posterior'un standart sapması) (REQ-49.27)
        variance = np.sum(((theta_grid - theta_eap) ** 2) * posterior)
        standard_error = np.sqrt(variance)

        logger.debug(
            f"EAP estimation - Theta: {theta_eap:.3f}, SE: {standard_error:.3f}"
        )

        return float(theta_eap), float(standard_error)

    def estimate_theta_mle(
        self, responses: list[dict], initial_theta: float = 0.0
    ) -> tuple[float, float]:
        """
        Maximum Likelihood Estimation (MLE) metodu ile theta tahmini.

        REQ-49.26: Maximum Likelihood Estimation (MLE)
        REQ-49.27: Standard error < 0.3 hedefleme
        REQ-49.28: -3 ile +3 arası değer üretme

        Args:
            responses: Yanıt listesi
            initial_theta: Başlangıç theta değeri

        Returns:
            (theta_estimate, standard_error)
        """
        if not responses:
            return initial_theta, 1.0

        # Negatif log-likelihood fonksiyonu
        def neg_log_likelihood(theta):
            ll = 0.0
            for response in responses:
                params = response["params"]
                is_correct = response["is_correct"]

                prob = self.irt_service.calculate_probability(theta, params)
                prob = max(1e-10, min(1 - 1e-10, prob))  # Numerical stability

                if is_correct:
                    ll += math.log(prob)
                else:
                    ll += math.log(1 - prob)

            return -ll

        # Optimize et (REQ-49.28: -3 ile +3 arası)
        result = minimize_scalar(
            neg_log_likelihood, bounds=(-3.0, 3.0), method="bounded"
        )

        theta_mle = result.x

        # Standard error hesapla (Fisher Information'dan) (REQ-49.27)
        total_information = 0.0
        for response in responses:
            params = response["params"]
            info = self.irt_service.calculate_information(theta_mle, params)
            total_information += info

        if total_information > 0:
            standard_error = 1.0 / math.sqrt(total_information)
        else:
            standard_error = 1.0

        logger.debug(
            f"MLE estimation - Theta: {theta_mle:.3f}, SE: {standard_error:.3f}"
        )

        return float(theta_mle), float(standard_error)

    def monitor_theta_convergence(
        self, state: StudentKnowledgeState, convergence_window: int = 5
    ) -> bool:
        """
        Theta yakınsamasını izle.

        REQ-49.27: Theta convergence monitoring

        Args:
            state: Bilgi durumu
            convergence_window: Yakınsama penceresi (son N theta)

        Returns:
            Yakınsama sağlandı mı?
        """
        if len(state.theta_history) < convergence_window:
            return False

        # Son N theta değerinin standart sapması
        recent_thetas = state.theta_history[-convergence_window:]
        theta_std = np.std(recent_thetas)

        # Yakınsama kriteri: std < 0.1
        converged = theta_std < 0.1

        if converged:
            logger.info(
                f"Theta yakınsadı - Student: {state.student_id}, "
                f"Theta: {state.theta:.3f}, STD: {theta_std:.4f}"
            )

        return converged

    # ==================== SUBTASK 60.4: Stopping Rules ====================

    def check_stopping_rules(
        self, session: TestSession, test_config: dict
    ) -> tuple[bool, str | None]:
        """
        Test sonlandırma kurallarını kontrol et.

        REQ-49.29: Fixed-length stopping - belirlenen soru sayısında durma
        REQ-49.30: Precision-based stopping - SE < 0.3 olduğunda durma
        REQ-49.31: Classification-based stopping - yeterlik seviyesi belirlendiğinde durma
        REQ-49.32: Minimum 10, maksimum 50 soru sınırı

        Args:
            session: Test oturumu
            test_config: Test konfigürasyonu

        Returns:
            (should_stop, reason)
        """
        questions_count = len(session.questions_administered)
        state = session.knowledge_state

        # Minimum soru kontrolü (REQ-49.32)
        if questions_count < self.fixed_length_min:
            return False, None

        # Maksimum soru kontrolü (REQ-49.32)
        if questions_count >= self.fixed_length_max:
            return True, "maximum_length_reached"

        # Fixed-length stopping (REQ-49.29)
        target_length = test_config.get("target_length")
        if target_length and questions_count >= target_length:
            return True, "target_length_reached"

        # Precision-based stopping (REQ-49.30)
        if state.standard_error < self.precision_threshold:
            logger.info(
                f"Precision threshold reached - SE: {state.standard_error:.3f} < {self.precision_threshold}"
            )
            return True, "precision_threshold_reached"

        # Classification-based stopping (REQ-49.31)
        classification_threshold = test_config.get("classification_threshold")
        if classification_threshold:
            classification_confidence = self._calculate_classification_confidence(state)

            if classification_confidence > classification_threshold:
                logger.info(
                    f"Classification confidence reached - "
                    f"Confidence: {classification_confidence:.3f} > {classification_threshold}"
                )
                return True, "classification_confidence_reached"

        # Devam et
        return False, None

    def _calculate_classification_confidence(
        self, state: StudentKnowledgeState
    ) -> float:
        """
        Sınıflandırma güvenini hesapla.

        REQ-49.31: Classification-based stopping

        Args:
            state: Bilgi durumu

        Returns:
            Sınıflandırma güveni (0-1 arası)
        """
        # Basit yaklaşım: knowledge probability ve theta stability'ye göre
        knowledge_confidence = state.knowledge_probability

        # Theta stability (son 5 theta'nın varyansı)
        if len(state.theta_history) >= 5:
            recent_thetas = state.theta_history[-5:]
            theta_variance = np.var(recent_thetas)
            theta_stability = 1.0 / (
                1.0 + theta_variance
            )  # Düşük varyans = yüksek stability
        else:
            theta_stability = 0.5

        # Kombine güven
        classification_confidence = (knowledge_confidence + theta_stability) / 2.0

        return classification_confidence

    def apply_fixed_length_stopping(
        self, session: TestSession, target_length: int
    ) -> bool:
        """
        Fixed-length stopping rule uygula.

        REQ-49.29: Fixed-length stopping

        Args:
            session: Test oturumu
            target_length: Hedef soru sayısı

        Returns:
            Durmalı mı?
        """
        return len(session.questions_administered) >= target_length

    def apply_precision_stopping(
        self, session: TestSession, precision_threshold: float = 0.3
    ) -> bool:
        """
        Precision-based stopping rule uygula.

        REQ-49.30: Precision-based stopping - SE < 0.3

        Args:
            session: Test oturumu
            precision_threshold: Precision eşiği

        Returns:
            Durmalı mı?
        """
        return session.knowledge_state.standard_error < precision_threshold

    def apply_classification_stopping(
        self, session: TestSession, classification_threshold: float = 0.9
    ) -> bool:
        """
        Classification-based stopping rule uygula.

        REQ-49.31: Classification-based stopping

        Args:
            session: Test oturumu
            classification_threshold: Sınıflandırma güven eşiği

        Returns:
            Durmalı mı?
        """
        confidence = self._calculate_classification_confidence(session.knowledge_state)
        return confidence > classification_threshold

    # ==================== Helper Methods ====================

    def create_test_session(
        self, session_id: str, student_id: str, test_type: str, prior_theta: float = 0.0
    ) -> TestSession:
        """
        Yeni test oturumu oluştur.

        Args:
            session_id: Oturum ID'si
            student_id: Öğrenci ID'si
            test_type: Test tipi
            prior_theta: Önceki theta tahmini

        Returns:
            Test oturumu
        """
        knowledge_state = self.initialize_knowledge_state(student_id, prior_theta)

        session = TestSession(
            session_id=session_id,
            student_id=student_id,
            test_type=test_type,
            start_time=datetime.now(),
            current_question_index=0,
            questions_administered=[],
            responses=[],
            knowledge_state=knowledge_state,
            content_coverage={},
        )

        self.active_sessions[session_id] = session

        logger.info(
            f"Test oturumu oluşturuldu - Session: {session_id}, "
            f"Student: {student_id}, Type: {test_type}"
        )

        return session

    def record_response(
        self,
        session: TestSession,
        question_id: str,
        question_params: IRTParameters,
        is_correct: bool,
        response_time: float,
    ) -> TestSession:
        """
        Öğrenci yanıtını kaydet ve bilgi durumunu güncelle.

        Args:
            session: Test oturumu
            question_id: Soru ID'si
            question_params: Soru IRT parametreleri
            is_correct: Doğru mu?
            response_time: Yanıt süresi (saniye)

        Returns:
            Güncellenmiş oturum
        """
        # Yanıtı kaydet
        response = {
            "question_id": question_id,
            "params": question_params,
            "is_correct": is_correct,
            "response_time": response_time,
            "timestamp": datetime.now(),
        }

        session.responses.append(response)
        session.questions_administered.append(question_id)

        # Bilgi durumunu güncelle
        session.knowledge_state = self.update_knowledge_state(
            session.knowledge_state, question_params, is_correct
        )

        # Theta'yı EAP/MLE ile yeniden hesapla (daha doğru tahmin)
        theta_eap, se_eap = self.estimate_theta_eap(session.responses)
        session.knowledge_state.theta = theta_eap
        session.knowledge_state.standard_error = se_eap

        logger.info(
            f"Yanıt kaydedildi - Session: {session.session_id}, "
            f"Question: {question_id}, Correct: {is_correct}, "
            f"New Theta: {theta_eap:.3f}, SE: {se_eap:.3f}"
        )

        return session

    def complete_session(
        self, session: TestSession, completion_reason: str
    ) -> TestSession:
        """
        Test oturumunu tamamla.

        Args:
            session: Test oturumu
            completion_reason: Tamamlanma nedeni

        Returns:
            Tamamlanmış oturum
        """
        session.is_complete = True
        session.completion_reason = completion_reason

        # Final theta estimation
        if session.responses:
            final_theta, final_se = self.estimate_theta_mle(session.responses)
            session.knowledge_state.theta = final_theta
            session.knowledge_state.standard_error = final_se

        logger.info(
            f"Test oturumu tamamlandı - Session: {session.session_id}, "
            f"Reason: {completion_reason}, "
            f"Questions: {len(session.questions_administered)}, "
            f"Final Theta: {session.knowledge_state.theta:.3f}, "
            f"SE: {session.knowledge_state.standard_error:.3f}"
        )

        return session

    def get_session_summary(self, session: TestSession) -> dict:
        """
        Oturum özetini al.

        Args:
            session: Test oturumu

        Returns:
            Oturum özeti
        """
        state = session.knowledge_state

        return {
            "session_id": session.session_id,
            "student_id": session.student_id,
            "test_type": session.test_type,
            "is_complete": session.is_complete,
            "completion_reason": session.completion_reason,
            "questions_count": len(session.questions_administered),
            "correct_count": state.correct_count,
            "accuracy": state.correct_count / state.responses_count
            if state.responses_count > 0
            else 0.0,
            "final_theta": state.theta,
            "standard_error": state.standard_error,
            "knowledge_probability": state.knowledge_probability,
            "theta_history": state.theta_history,
            "content_coverage": session.content_coverage,
        }
