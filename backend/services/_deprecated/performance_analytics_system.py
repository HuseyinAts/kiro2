"""
Performans Analitikleri Sistemi (Performance Analytics System)
Task 64: Performans Analitikleri
Requirements: REQ-49.85-49.100

Bu modül adaptif test sistemine performans analitikleri ekler:
- Learning curve analysis (Subtask 64.1)
- Predictive analytics (Subtask 64.2)
- Anomaly detection (Subtask 64.3)
- Cohort analysis (Subtask 64.4)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit

from services.adaptive_test_engine import TestSession

logger = logging.getLogger(__name__)


@dataclass
class LearningCurveData:
    """Öğrenme eğrisi verileri"""

    timestamps: List[datetime] = field(default_factory=list)
    theta_values: List[float] = field(default_factory=list)
    accuracy_values: List[float] = field(default_factory=list)
    growth_rate: float = 0.0
    plateau_detected: bool = False
    plateau_start_index: Optional[int] = None


@dataclass
class PredictionResult:
    """Tahmin sonucu"""

    predicted_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    confidence_level: float
    prediction_date: datetime
    model_type: str  # 'linear', 'exponential', 'logistic'
    r_squared: float  # Model uyum iyiliği


@dataclass
class AnomalyDetection:
    """Anomali tespiti"""

    is_anomaly: bool
    anomaly_type: str  # 'performance_drop', 'unusual_pattern', 'cheating_suspected'
    severity: float  # 0-1 arası
    description: str
    timestamp: datetime
    affected_questions: List[str] = field(default_factory=list)


class PerformanceAnalyticsSystem:
    """
    Performans Analitikleri Sistemi

    REQ-49.85-49.88: Learning curve analysis
    REQ-49.89-49.92: Predictive analytics
    REQ-49.93-49.96: Anomaly detection
    REQ-49.97-49.100: Cohort analysis
    """

    def __init__(self):
        """Performans analitikleri sistemini başlat"""
        # Learning curve parametreleri
        self.plateau_threshold = 0.05  # %5'ten az değişim = plateau
        self.plateau_window = 10  # Son 10 veri noktası

        # Prediction parametreleri
        self.confidence_level = 0.95  # %95 güven aralığı

        # Anomaly detection parametreleri
        self.z_score_threshold = 2.5  # Z-score > 2.5 = anomali
        self.cheating_threshold = 0.8  # Şüpheli davranış eşiği

        logger.info("Performance Analytics System başlatıldı")

    # ==================== SUBTASK 64.1: Learning Curve Analysis ====================

    def track_progress_over_time(
        self,
        session: TestSession,
        historical_sessions: Optional[List[TestSession]] = None,
    ) -> LearningCurveData:
        """
        Zaman içinde ilerlemeyi izle.

        REQ-49.85: Learning curve analysis - zaman içinde ilerlemeyi izleme
        REQ-49.86: Growth rate calculation - öğrenme hızını hesaplama
        REQ-49.87: Plateau detection - durağan dönemleri tespit etme
        REQ-49.88: Görsel grafik sunma

        Args:
            session: Mevcut test oturumu
            historical_sessions: Geçmiş oturumlar

        Returns:
            Öğrenme eğrisi verileri
        """
        curve_data = LearningCurveData()

        # Mevcut oturum verilerini ekle
        state = session.knowledge_state

        for i, theta in enumerate(state.theta_history):
            # Timestamp tahmin et (her soru için)
            timestamp = session.start_time + timedelta(
                minutes=i * 2
            )  # Her soru ~2 dakika
            curve_data.timestamps.append(timestamp)
            curve_data.theta_values.append(theta)

            # Accuracy hesapla
            if i < len(session.responses):
                responses_so_far = session.responses[: i + 1]
                correct_count = sum(
                    1 for r in responses_so_far if r.get("is_correct", False)
                )
                accuracy = (
                    correct_count / len(responses_so_far) if responses_so_far else 0.0
                )
                curve_data.accuracy_values.append(accuracy)

        # Geçmiş oturumları ekle
        if historical_sessions:
            for hist_session in historical_sessions:
                hist_state = hist_session.knowledge_state
                for i, theta in enumerate(hist_state.theta_history):
                    timestamp = hist_session.start_time + timedelta(minutes=i * 2)
                    curve_data.timestamps.append(timestamp)
                    curve_data.theta_values.append(theta)

        # Growth rate hesapla (REQ-49.86)
        if len(curve_data.theta_values) >= 2:
            curve_data.growth_rate = self.calculate_growth_rate(curve_data.theta_values)

        # Plateau detection (REQ-49.87)
        plateau_info = self.detect_plateau(curve_data.theta_values)
        curve_data.plateau_detected = plateau_info["detected"]
        curve_data.plateau_start_index = plateau_info.get("start_index")

        logger.info(
            f"Learning curve analizi - Session: {session.session_id}, "
            f"Data Points: {len(curve_data.theta_values)}, "
            f"Growth Rate: {curve_data.growth_rate:.4f}, "
            f"Plateau: {curve_data.plateau_detected}"
        )

        return curve_data

    def calculate_growth_rate(self, theta_values: List[float]) -> float:
        """
        Öğrenme hızını hesapla.

        REQ-49.86: Growth rate calculation

        Args:
            theta_values: Theta değerleri listesi

        Returns:
            Büyüme oranı (theta/zaman birimi)
        """
        if len(theta_values) < 2:
            return 0.0

        # Linear regression ile trend hesapla
        x = np.arange(len(theta_values))
        y = np.array(theta_values)

        # Slope = growth rate
        slope, intercept = np.polyfit(x, y, 1)

        return float(slope)

    def detect_plateau(
        self, theta_values: List[float], window_size: Optional[int] = None
    ) -> Dict:
        """
        Durağan dönemleri tespit et.

        REQ-49.87: Plateau detection - durağan dönemleri tespit etme

        Args:
            theta_values: Theta değerleri
            window_size: Analiz penceresi boyutu

        Returns:
            Plateau bilgileri
        """
        if window_size is None:
            window_size = self.plateau_window

        if len(theta_values) < window_size:
            return {"detected": False}

        # Son N değerin standart sapması
        recent_values = theta_values[-window_size:]
        std_dev = np.std(recent_values)

        # Plateau: std dev < threshold
        plateau_detected = std_dev < self.plateau_threshold

        if plateau_detected:
            # Plateau başlangıç noktasını bul
            for i in range(len(theta_values) - window_size, -1, -1):
                window = theta_values[i : i + window_size]
                if np.std(window) >= self.plateau_threshold:
                    start_index = i + 1
                    break
            else:
                start_index = 0

            logger.info(
                f"Plateau tespit edildi - Start Index: {start_index}, "
                f"STD: {std_dev:.4f}, Threshold: {self.plateau_threshold}"
            )

            return {
                "detected": True,
                "start_index": start_index,
                "std_dev": std_dev,
                "plateau_value": np.mean(recent_values),
            }

        return {"detected": False}

    def generate_learning_curve_visualization(
        self, curve_data: LearningCurveData
    ) -> Dict:
        """
        Öğrenme eğrisi görselleştirme verisi oluştur.

        REQ-49.88: Görsel grafik sunma

        Args:
            curve_data: Öğrenme eğrisi verileri

        Returns:
            Görselleştirme verisi (frontend için)
        """
        # Zaman serisi verisi
        time_series = [
            {
                "timestamp": ts.isoformat(),
                "theta": theta,
                "accuracy": acc if i < len(curve_data.accuracy_values) else None,
            }
            for i, (ts, theta, acc) in enumerate(
                zip(
                    curve_data.timestamps,
                    curve_data.theta_values,
                    curve_data.accuracy_values
                    + [None]
                    * (len(curve_data.theta_values) - len(curve_data.accuracy_values)),
                )
            )
        ]

        # Trend line
        if len(curve_data.theta_values) >= 2:
            x = np.arange(len(curve_data.theta_values))
            y = np.array(curve_data.theta_values)
            slope, intercept = np.polyfit(x, y, 1)
            trend_line = [float(slope * i + intercept) for i in x]
        else:
            trend_line = []

        # Plateau marker
        plateau_marker = None
        if curve_data.plateau_detected and curve_data.plateau_start_index is not None:
            plateau_marker = {
                "start_index": curve_data.plateau_start_index,
                "start_timestamp": curve_data.timestamps[
                    curve_data.plateau_start_index
                ].isoformat(),
                "message": "Öğrenme platosuna ulaşıldı",
            }

        return {
            "time_series": time_series,
            "trend_line": trend_line,
            "growth_rate": curve_data.growth_rate,
            "plateau_marker": plateau_marker,
            "chart_config": {
                "x_axis": "Zaman",
                "y_axis": "Yetenek Seviyesi (Theta)",
                "title": "Öğrenme Eğrisi",
                "show_trend": True,
                "show_plateau": curve_data.plateau_detected,
            },
        }

    # ==================== SUBTASK 64.2: Predictive Analytics ====================

    def predict_success_probability(
        self, session: TestSession, target_theta: float = 0.0
    ) -> PredictionResult:
        """
        Gelecek performansı tahmin et.

        REQ-49.89: Success probability prediction - gelecek performansı tahmin etme
        REQ-49.92: %95 güven aralığı ile tahmin verme

        Args:
            session: Test oturumu
            target_theta: Hedef yetenek seviyesi

        Returns:
            Tahmin sonucu
        """
        state = session.knowledge_state

        if len(state.theta_history) < 3:
            # Yeterli veri yok
            return PredictionResult(
                predicted_value=0.5,
                confidence_interval_lower=0.0,
                confidence_interval_upper=1.0,
                confidence_level=self.confidence_level,
                prediction_date=datetime.now(),
                model_type="insufficient_data",
                r_squared=0.0,
            )

        # Exponential growth model fit et
        x = np.arange(len(state.theta_history))
        y = np.array(state.theta_history)

        try:
            # Exponential model: y = a * exp(b * x) + c
            def exp_model(x, a, b, c):
                return a * np.exp(b * x) + c

            popt, pcov = curve_fit(exp_model, x, y, maxfev=5000)
            a, b, c = popt

            # Gelecek tahmin (10 adım sonra)
            future_x = len(state.theta_history) + 10
            predicted_theta = exp_model(future_x, a, b, c)

            # Güven aralığı hesapla (REQ-49.92)
            # Residual standard error
            y_pred = exp_model(x, a, b, c)
            residuals = y - y_pred
            rse = np.sqrt(np.sum(residuals**2) / (len(y) - 3))  # 3 parametre

            # t-distribution
            t_value = stats.t.ppf((1 + self.confidence_level) / 2, len(y) - 3)
            margin_of_error = t_value * rse

            ci_lower = predicted_theta - margin_of_error
            ci_upper = predicted_theta + margin_of_error

            # R-squared
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

            model_type = "exponential"

        except Exception as e:
            logger.warning(
                f"Exponential model fit başarısız: {e}, linear model kullanılıyor"
            )

            # Fallback: Linear model
            slope, intercept = np.polyfit(x, y, 1)
            future_x = len(state.theta_history) + 10
            predicted_theta = slope * future_x + intercept

            # Linear için güven aralığı
            y_pred = slope * x + intercept
            residuals = y - y_pred
            rse = np.sqrt(np.sum(residuals**2) / (len(y) - 2))
            t_value = stats.t.ppf((1 + self.confidence_level) / 2, len(y) - 2)
            margin_of_error = t_value * rse

            ci_lower = predicted_theta - margin_of_error
            ci_upper = predicted_theta + margin_of_error

            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

            model_type = "linear"

        # Başarı olasılığına çevir
        # Theta > target_theta ise başarılı
        success_prob = 1.0 / (1.0 + np.exp(-(predicted_theta - target_theta)))

        logger.info(
            f"Başarı tahmini - Session: {session.session_id}, "
            f"Predicted Theta: {predicted_theta:.3f}, "
            f"Success Prob: {success_prob:.3f}, "
            f"CI: [{ci_lower:.3f}, {ci_upper:.3f}], "
            f"Model: {model_type}, R²: {r_squared:.3f}"
        )

        return PredictionResult(
            predicted_value=success_prob,
            confidence_interval_lower=max(
                0.0, 1.0 / (1.0 + np.exp(-(ci_lower - target_theta)))
            ),
            confidence_interval_upper=min(
                1.0, 1.0 / (1.0 + np.exp(-(ci_upper - target_theta)))
            ),
            confidence_level=self.confidence_level,
            prediction_date=datetime.now() + timedelta(days=30),  # 30 gün sonrası
            model_type=model_type,
            r_squared=r_squared,
        )

    def predict_university_placement(
        self, session: TestSession, target_programs: List[Dict]
    ) -> List[Dict]:
        """
        Üniversite yerleşme olasılığı hesapla.

        REQ-49.90: University placement prediction - üniversite yerleşme olasılığı hesaplama
        REQ-49.92: %95 güven aralığı ile tahmin verme

        Args:
            session: Test oturumu
            target_programs: Hedef programlar [{'name': str, 'min_score': float}, ...]

        Returns:
            Program bazlı yerleşme tahminleri
        """
        state = session.knowledge_state

        # Mevcut theta'dan puan tahmini
        # Basitleştirilmiş: theta * 100 + 500 (TYT/AYT puan aralığı)
        current_score = state.theta * 100 + 500

        # Gelecek theta tahmini
        future_prediction = self.predict_success_probability(session, target_theta=0.0)

        # Gelecek puan tahmini
        # Predicted theta'yı puana çevir
        # Burada basitleştirilmiş bir yaklaşım kullanıyoruz
        # Gerçek implementasyonda ÖSYM puan hesaplama formülü kullanılır

        results = []

        for program in target_programs:
            program_name = program["name"]
            min_score = program["min_score"]

            # Mevcut puan ile karşılaştır
            score_gap = min_score - current_score

            # Yerleşme olasılığı
            if score_gap <= 0:
                # Zaten yeterli puan
                placement_prob = 0.95
            else:
                # Gelecek tahminine göre
                # Basitleştirilmiş: future_prediction.predicted_value'yu kullan
                placement_prob = future_prediction.predicted_value * (
                    1.0 - min(1.0, score_gap / 100.0)
                )

            # Güven aralığı
            ci_lower = max(0.0, placement_prob - 0.1)
            ci_upper = min(1.0, placement_prob + 0.1)

            results.append(
                {
                    "program_name": program_name,
                    "min_score_required": min_score,
                    "current_estimated_score": current_score,
                    "score_gap": score_gap,
                    "placement_probability": placement_prob,
                    "confidence_interval": [ci_lower, ci_upper],
                    "confidence_level": self.confidence_level,
                    "recommendation": self._get_placement_recommendation(
                        placement_prob, score_gap
                    ),
                }
            )

        logger.info(
            f"Üniversite yerleşme tahmini - Session: {session.session_id}, "
            f"Programs: {len(target_programs)}"
        )

        return results

    def _get_placement_recommendation(
        self, placement_prob: float, score_gap: float
    ) -> str:
        """Yerleşme önerisi oluştur"""
        if placement_prob >= 0.8:
            return "Yüksek yerleşme olasılığı! Bu program senin için uygun."
        elif placement_prob >= 0.5:
            return f"Orta yerleşme olasılığı. {abs(score_gap):.0f} puan daha çalışman gerekiyor."
        elif placement_prob >= 0.3:
            return f"Düşük yerleşme olasılığı. {abs(score_gap):.0f} puan fark var. Yoğun çalışma gerekli."
        else:
            return "Çok düşük yerleşme olasılığı. Alternatif programları değerlendir."

    def estimate_score_range(self, session: TestSession) -> Dict:
        """
        Puan aralığı tahmini yap.

        REQ-49.91: Score range estimation - puan aralığı tahmini sunma
        REQ-49.92: %95 güven aralığı ile tahmin verme

        Args:
            session: Test oturumu

        Returns:
            Puan aralığı tahmini
        """
        state = session.knowledge_state

        # Mevcut theta'dan puan hesapla
        # Basitleştirilmiş: theta * 100 + 500
        estimated_score = state.theta * 100 + 500

        # Güven aralığı (standard error'dan)
        # %95 güven aralığı için z = 1.96
        z_score = 1.96
        margin_of_error = z_score * state.standard_error * 100  # Puan cinsinden

        score_lower = estimated_score - margin_of_error
        score_upper = estimated_score + margin_of_error

        # Sınırla (0-600 arası TYT/AYT puanı)
        score_lower = max(0.0, score_lower)
        score_upper = min(600.0, score_upper)

        logger.info(
            f"Puan aralığı tahmini - Session: {session.session_id}, "
            f"Estimated: {estimated_score:.1f}, "
            f"Range: [{score_lower:.1f}, {score_upper:.1f}]"
        )

        return {
            "estimated_score": estimated_score,
            "score_range_lower": score_lower,
            "score_range_upper": score_upper,
            "confidence_level": self.confidence_level,
            "margin_of_error": margin_of_error,
            "theta": state.theta,
            "standard_error": state.standard_error,
        }

    # ==================== SUBTASK 64.3: Anomaly Detection ====================

    def detect_unusual_patterns(self, session: TestSession) -> List[AnomalyDetection]:
        """
        Olağandışı performans paternlerini tespit et.

        REQ-49.93: Unusual performance patterns - anormal davranışları işaretleme
        REQ-49.94: Cheating detection - şüpheli yanıt paternlerini tespit etme
        REQ-49.95: Data quality monitoring - veri tutarlılığını kontrol etme
        REQ-49.96: Yöneticiye bildirim gönderme

        Args:
            session: Test oturumu

        Returns:
            Tespit edilen anomaliler listesi
        """
        anomalies = []
        state = session.knowledge_state

        # 1. Ani performans düşüşü (REQ-49.93)
        if len(state.theta_history) >= 5:
            recent_thetas = state.theta_history[-5:]
            theta_drop = recent_thetas[0] - recent_thetas[-1]

            if theta_drop > 1.0:  # 1 puandan fazla düşüş
                anomalies.append(
                    AnomalyDetection(
                        is_anomaly=True,
                        anomaly_type="performance_drop",
                        severity=min(1.0, theta_drop / 2.0),
                        description=f"Ani performans düşüşü tespit edildi: {theta_drop:.2f} puan",
                        timestamp=datetime.now(),
                    )
                )

        # 2. Şüpheli yanıt paterni (REQ-49.94)
        cheating_score = self._calculate_cheating_score(session)

        if cheating_score > self.cheating_threshold:
            anomalies.append(
                AnomalyDetection(
                    is_anomaly=True,
                    anomaly_type="cheating_suspected",
                    severity=cheating_score,
                    description=f"Şüpheli yanıt paterni tespit edildi (skor: {cheating_score:.2f})",
                    timestamp=datetime.now(),
                )
            )

        # 3. Veri tutarlılığı kontrolü (REQ-49.95)
        data_quality_issues = self._check_data_quality(session)

        if data_quality_issues:
            anomalies.append(
                AnomalyDetection(
                    is_anomaly=True,
                    anomaly_type="data_quality_issue",
                    severity=0.5,
                    description=f'Veri tutarlılığı sorunu: {", ".join(data_quality_issues)}',
                    timestamp=datetime.now(),
                )
            )

        # 4. Z-score bazlı anomali tespiti
        if len(session.responses) >= 10:
            response_times = [r.get("response_time", 0) for r in session.responses]
            z_scores = stats.zscore(response_times)

            anomalous_indices = np.where(np.abs(z_scores) > self.z_score_threshold)[0]

            if len(anomalous_indices) > 0:
                anomalies.append(
                    AnomalyDetection(
                        is_anomaly=True,
                        anomaly_type="unusual_response_time",
                        severity=0.6,
                        description=f"{len(anomalous_indices)} soru olağandışı yanıt süresine sahip",
                        timestamp=datetime.now(),
                        affected_questions=[
                            session.questions_administered[i] for i in anomalous_indices
                        ],
                    )
                )

        # Yöneticiye bildirim (REQ-49.96)
        if anomalies:
            self._notify_admin(session, anomalies)

        logger.info(
            f"Anomali tespiti - Session: {session.session_id}, "
            f"Anomalies: {len(anomalies)}"
        )

        return anomalies

    def _calculate_cheating_score(self, session: TestSession) -> float:
        """
        Kopya çekme skorunu hesapla.

        REQ-49.94: Cheating detection

        Args:
            session: Test oturumu

        Returns:
            Kopya skoru (0-1 arası)
        """
        if len(session.responses) < 10:
            return 0.0

        cheating_indicators = []

        # 1. Çok hızlı yanıtlar (zor sorularda)
        for response in session.responses:
            response_time = response.get("response_time", 0)
            difficulty = (
                response.get("params", {}).b
                if hasattr(response.get("params", {}), "b")
                else 0.0
            )

            # Zor soru (b > 1.0) ama çok hızlı yanıt (< 10 saniye)
            if (
                difficulty > 1.0
                and response_time < 10.0
                and response.get("is_correct", False)
            ):
                cheating_indicators.append(0.3)

        # 2. Ani doğruluk artışı
        if len(session.responses) >= 20:
            first_half = session.responses[: len(session.responses) // 2]
            second_half = session.responses[len(session.responses) // 2 :]

            first_accuracy = sum(
                1 for r in first_half if r.get("is_correct", False)
            ) / len(first_half)
            second_accuracy = sum(
                1 for r in second_half if r.get("is_correct", False)
            ) / len(second_half)

            accuracy_jump = second_accuracy - first_accuracy

            if accuracy_jump > 0.4:  # %40'tan fazla artış
                cheating_indicators.append(0.5)

        # 3. Tutarsız performans (kolay sorularda yanlış, zor sorularda doğru)
        easy_correct = 0
        easy_total = 0
        hard_correct = 0
        hard_total = 0

        for response in session.responses:
            difficulty = (
                response.get("params", {}).b
                if hasattr(response.get("params", {}), "b")
                else 0.0
            )
            is_correct = response.get("is_correct", False)

            if difficulty < -0.5:  # Kolay soru
                easy_total += 1
                if is_correct:
                    easy_correct += 1
            elif difficulty > 1.0:  # Zor soru
                hard_total += 1
                if is_correct:
                    hard_correct += 1

        if easy_total > 0 and hard_total > 0:
            easy_accuracy = easy_correct / easy_total
            hard_accuracy = hard_correct / hard_total

            # Zor sorularda daha başarılı (şüpheli)
            if hard_accuracy > easy_accuracy + 0.3:
                cheating_indicators.append(0.4)

        # Toplam skor
        cheating_score = sum(cheating_indicators) / max(1, len(cheating_indicators))
        cheating_score = min(1.0, cheating_score)

        return cheating_score

    def _check_data_quality(self, session: TestSession) -> List[str]:
        """
        Veri kalitesini kontrol et.

        REQ-49.95: Data quality monitoring

        Args:
            session: Test oturumu

        Returns:
            Tespit edilen sorunlar listesi
        """
        issues = []

        # 1. Eksik veri kontrolü
        for i, response in enumerate(session.responses):
            if "response_time" not in response:
                issues.append(f"Soru {i+1}: Yanıt süresi eksik")

            if "is_correct" not in response:
                issues.append(f"Soru {i+1}: Doğruluk bilgisi eksik")

        # 2. Tutarsız theta geçmişi
        state = session.knowledge_state
        if (
            len(state.theta_history) != len(session.responses) + 1
        ):  # +1 for initial theta
            issues.append("Theta geçmişi tutarsız")

        # 3. Negatif yanıt süreleri
        negative_times = [
            i for i, r in enumerate(session.responses) if r.get("response_time", 0) < 0
        ]
        if negative_times:
            issues.append(f"{len(negative_times)} soru negatif yanıt süresine sahip")

        # 4. Aşırı uzun yanıt süreleri (> 10 dakika)
        long_times = [
            i
            for i, r in enumerate(session.responses)
            if r.get("response_time", 0) > 600
        ]
        if long_times:
            issues.append(f"{len(long_times)} soru aşırı uzun yanıt süresine sahip")

        return issues

    def _notify_admin(self, session: TestSession, anomalies: List[AnomalyDetection]):
        """
        Yöneticiye bildirim gönder.

        REQ-49.96: Yöneticiye bildirim gönderme

        Args:
            session: Test oturumu
            anomalies: Tespit edilen anomaliler
        """
        # Yüksek severity anomalileri filtrele
        high_severity = [a for a in anomalies if a.severity >= 0.7]

        if high_severity:
            notification = {
                "type": "anomaly_alert",
                "session_id": session.session_id,
                "student_id": session.student_id,
                "timestamp": datetime.now().isoformat(),
                "anomalies": [
                    {
                        "type": a.anomaly_type,
                        "severity": a.severity,
                        "description": a.description,
                    }
                    for a in high_severity
                ],
                "action_required": True,
            }

            # Burada gerçek bildirim sistemi entegre edilir
            # Örnek: email, SMS, push notification
            logger.warning(
                f"ADMIN ALERT - Session: {session.session_id}, "
                f"High Severity Anomalies: {len(high_severity)}"
            )

            # Notification queue'ya ekle (örnek)
            # notification_queue.put(notification)

    # ==================== SUBTASK 64.4: Cohort Analysis ====================

    def compare_group_performance(
        self, sessions: List[TestSession], group_by: str = "test_type"
    ) -> Dict:
        """
        Grup performanslarını karşılaştır.

        REQ-49.97: Group performance comparison - grup performanslarını karşılaştırma
        REQ-49.98: Demographic analysis - demografik faktörleri analiz etme
        REQ-49.99: Intervention effectiveness - müdahale etkisini değerlendirme
        REQ-49.100: Detaylı karşılaştırma raporu sunma

        Args:
            sessions: Test oturumları listesi
            group_by: Gruplama kriteri ('test_type', 'grade', 'school', etc.)

        Returns:
            Grup karşılaştırma raporu
        """
        if not sessions:
            return {}

        # Gruplara ayır
        groups = {}
        for session in sessions:
            if group_by == "test_type":
                group_key = session.test_type
            else:
                # Diğer gruplama kriterleri için session'dan al
                group_key = getattr(session, group_by, "unknown")

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(session)

        # Her grup için istatistikler hesapla
        group_stats = {}

        for group_name, group_sessions in groups.items():
            # Theta istatistikleri
            final_thetas = [s.knowledge_state.theta for s in group_sessions]

            # Accuracy istatistikleri
            accuracies = [
                s.knowledge_state.correct_count / s.knowledge_state.responses_count
                if s.knowledge_state.responses_count > 0
                else 0.0
                for s in group_sessions
            ]

            # Completion rate
            completed = sum(1 for s in group_sessions if s.is_complete)
            completion_rate = completed / len(group_sessions) if group_sessions else 0.0

            group_stats[group_name] = {
                "count": len(group_sessions),
                "theta_mean": np.mean(final_thetas),
                "theta_std": np.std(final_thetas),
                "theta_median": np.median(final_thetas),
                "accuracy_mean": np.mean(accuracies),
                "accuracy_std": np.std(accuracies),
                "completion_rate": completion_rate,
                "avg_questions": np.mean(
                    [len(s.questions_administered) for s in group_sessions]
                ),
            }

        # Gruplar arası karşılaştırma (ANOVA)
        if len(groups) >= 2:
            group_thetas = [
                [s.knowledge_state.theta for s in group_sessions]
                for group_sessions in groups.values()
            ]

            # One-way ANOVA
            f_stat, p_value = stats.f_oneway(*group_thetas)

            statistical_significance = {
                "f_statistic": f_stat,
                "p_value": p_value,
                "significant": p_value < 0.05,
                "interpretation": "Gruplar arası anlamlı fark var"
                if p_value < 0.05
                else "Gruplar arası anlamlı fark yok",
            }
        else:
            statistical_significance = None

        logger.info(
            f"Cohort analizi - Groups: {len(groups)}, "
            f"Total Sessions: {len(sessions)}"
        )

        return {
            "group_by": group_by,
            "groups": group_stats,
            "statistical_significance": statistical_significance,
            "total_sessions": len(sessions),
            "analysis_date": datetime.now().isoformat(),
        }

    def analyze_demographic_factors(
        self, sessions: List[TestSession], demographic_data: Dict[str, Dict]
    ) -> Dict:
        """
        Demografik faktörleri analiz et.

        REQ-49.98: Demographic analysis - demografik faktörleri analiz etme

        Args:
            sessions: Test oturumları
            demographic_data: Demografik veriler {student_id: {'grade': int, 'gender': str, ...}}

        Returns:
            Demografik analiz raporu
        """
        # Demografik gruplara göre performans
        demographic_groups = {}

        for session in sessions:
            student_id = session.student_id
            demo = demographic_data.get(student_id, {})

            # Her demografik faktör için gruplama
            for factor, value in demo.items():
                if factor not in demographic_groups:
                    demographic_groups[factor] = {}

                if value not in demographic_groups[factor]:
                    demographic_groups[factor][value] = []

                demographic_groups[factor][value].append(session)

        # Her faktör için istatistikler
        factor_analysis = {}

        for factor, groups in demographic_groups.items():
            factor_stats = {}

            for group_value, group_sessions in groups.items():
                thetas = [s.knowledge_state.theta for s in group_sessions]
                accuracies = [
                    s.knowledge_state.correct_count / s.knowledge_state.responses_count
                    if s.knowledge_state.responses_count > 0
                    else 0.0
                    for s in group_sessions
                ]

                factor_stats[str(group_value)] = {
                    "count": len(group_sessions),
                    "theta_mean": np.mean(thetas),
                    "accuracy_mean": np.mean(accuracies),
                }

            factor_analysis[factor] = factor_stats

        logger.info(
            f"Demografik analiz - Factors: {len(demographic_groups)}, "
            f"Sessions: {len(sessions)}"
        )

        return {
            "demographic_factors": factor_analysis,
            "total_sessions": len(sessions),
            "analysis_date": datetime.now().isoformat(),
        }

    def evaluate_intervention_effectiveness(
        self,
        pre_intervention_sessions: List[TestSession],
        post_intervention_sessions: List[TestSession],
    ) -> Dict:
        """
        Müdahale etkinliğini değerlendir.

        REQ-49.99: Intervention effectiveness - müdahale etkisini değerlendirme

        Args:
            pre_intervention_sessions: Müdahale öncesi oturumlar
            post_intervention_sessions: Müdahale sonrası oturumlar

        Returns:
            Müdahale etkinlik raporu
        """
        if not pre_intervention_sessions or not post_intervention_sessions:
            return {"error": "Insufficient data"}

        # Pre-intervention istatistikleri
        pre_thetas = [s.knowledge_state.theta for s in pre_intervention_sessions]
        pre_accuracies = [
            s.knowledge_state.correct_count / s.knowledge_state.responses_count
            if s.knowledge_state.responses_count > 0
            else 0.0
            for s in pre_intervention_sessions
        ]

        # Post-intervention istatistikleri
        post_thetas = [s.knowledge_state.theta for s in post_intervention_sessions]
        post_accuracies = [
            s.knowledge_state.correct_count / s.knowledge_state.responses_count
            if s.knowledge_state.responses_count > 0
            else 0.0
            for s in post_intervention_sessions
        ]

        # İstatistiksel karşılaştırma (paired t-test)
        theta_t_stat, theta_p_value = stats.ttest_ind(pre_thetas, post_thetas)
        accuracy_t_stat, accuracy_p_value = stats.ttest_ind(
            pre_accuracies, post_accuracies
        )

        # Effect size (Cohen's d)
        theta_effect_size = (np.mean(post_thetas) - np.mean(pre_thetas)) / np.sqrt(
            (np.std(pre_thetas) ** 2 + np.std(post_thetas) ** 2) / 2
        )

        accuracy_effect_size = (
            np.mean(post_accuracies) - np.mean(pre_accuracies)
        ) / np.sqrt((np.std(pre_accuracies) ** 2 + np.std(post_accuracies) ** 2) / 2)

        # Yorum
        if theta_p_value < 0.05 and theta_effect_size > 0.5:
            interpretation = "Müdahale etkili - Anlamlı ve büyük etki"
        elif theta_p_value < 0.05:
            interpretation = "Müdahale kısmen etkili - Anlamlı ama küçük etki"
        else:
            interpretation = "Müdahale etkisiz - Anlamlı fark yok"

        logger.info(
            f"Müdahale etkinliği - Pre: {len(pre_intervention_sessions)}, "
            f"Post: {len(post_intervention_sessions)}, "
            f"Effect Size: {theta_effect_size:.3f}, "
            f"P-value: {theta_p_value:.4f}"
        )

        return {
            "pre_intervention": {
                "count": len(pre_intervention_sessions),
                "theta_mean": np.mean(pre_thetas),
                "theta_std": np.std(pre_thetas),
                "accuracy_mean": np.mean(pre_accuracies),
            },
            "post_intervention": {
                "count": len(post_intervention_sessions),
                "theta_mean": np.mean(post_thetas),
                "theta_std": np.std(post_thetas),
                "accuracy_mean": np.mean(post_accuracies),
            },
            "statistical_tests": {
                "theta_t_statistic": theta_t_stat,
                "theta_p_value": theta_p_value,
                "theta_effect_size": theta_effect_size,
                "accuracy_t_statistic": accuracy_t_stat,
                "accuracy_p_value": accuracy_p_value,
                "accuracy_effect_size": accuracy_effect_size,
            },
            "interpretation": interpretation,
            "significant": theta_p_value < 0.05,
            "analysis_date": datetime.now().isoformat(),
        }

    def generate_cohort_report(
        self, sessions: List[TestSession], demographic_data: Optional[Dict] = None
    ) -> Dict:
        """
        Detaylı cohort raporu oluştur.

        REQ-49.100: Detaylı karşılaştırma raporu sunma

        Args:
            sessions: Test oturumları
            demographic_data: Demografik veriler (opsiyonel)

        Returns:
            Kapsamlı cohort raporu
        """
        report = {
            "report_date": datetime.now().isoformat(),
            "total_sessions": len(sessions),
            "summary": {},
        }

        # Genel istatistikler
        all_thetas = [s.knowledge_state.theta for s in sessions]
        all_accuracies = [
            s.knowledge_state.correct_count / s.knowledge_state.responses_count
            if s.knowledge_state.responses_count > 0
            else 0.0
            for s in sessions
        ]

        report["summary"] = {
            "theta_mean": np.mean(all_thetas),
            "theta_median": np.median(all_thetas),
            "theta_std": np.std(all_thetas),
            "accuracy_mean": np.mean(all_accuracies),
            "accuracy_std": np.std(all_accuracies),
            "completion_rate": sum(1 for s in sessions if s.is_complete)
            / len(sessions),
        }

        # Test tipi bazlı karşılaştırma
        report["by_test_type"] = self.compare_group_performance(sessions, "test_type")

        # Demografik analiz (varsa)
        if demographic_data:
            report["demographic_analysis"] = self.analyze_demographic_factors(
                sessions, demographic_data
            )

        # Performans dağılımı
        report["performance_distribution"] = {
            "low": sum(1 for t in all_thetas if t < -1.0),
            "medium": sum(1 for t in all_thetas if -1.0 <= t <= 1.0),
            "high": sum(1 for t in all_thetas if t > 1.0),
        }

        logger.info(f"Cohort raporu oluşturuldu - Sessions: {len(sessions)}")

        return report
