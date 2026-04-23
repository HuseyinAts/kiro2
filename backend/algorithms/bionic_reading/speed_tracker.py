"""
Reading Speed Tracker - Okuma Hızı Takibi
REQ-3: Reading Speed Optimization

Features:
- WPM (Words Per Minute) calculation
- Before/after comparison
- Saccade reduction metrics
- Reading flow analysis
"""

import logging
import statistics
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import uuid4

logger = logging.getLogger(__name__)


class ReadingMode(Enum):
    """Okuma modu tipleri"""
    NORMAL = "normal"  # Bionic olmadan
    BIONIC = "bionic"  # Bionic ile


@dataclass
class ReadingSession:
    """Okuma oturumu verisi"""
    session_id: str
    user_id: str
    text_id: str
    mode: ReadingMode
    word_count: int
    start_time: datetime
    end_time: datetime | None = None
    wpm: float = 0.0
    completed: bool = False
    pause_duration_ms: int = 0
    regression_count: int = 0  # Geri dönüş sayısı


@dataclass
class SpeedComparison:
    """Hız karşılaştırma sonucu"""
    normal_wpm: float
    bionic_wpm: float
    improvement_percentage: float
    improvement_absolute: float
    target_met: bool  # >= %20 improvement
    sample_size: int
    confidence_level: float


@dataclass
class ReadingMetrics:
    """Okuma metrikleri"""
    average_wpm: float
    median_wpm: float
    max_wpm: float
    min_wpm: float
    total_words_read: int
    total_sessions: int
    total_reading_time_minutes: float
    saccade_estimate: float  # Tahmini saccade sayısı
    regression_rate: float  # Geri dönüş oranı


class ReadingSpeedTracker:
    """
    Reading Speed Tracker

    Okuma hızını takip eder ve bionic reading'in etkisini ölçer:
    - Baseline WPM ölçümü
    - Bionic WPM ölçümü
    - %20+ improvement hedefi (REQ-3.2)
    - Saccade reduction analizi (REQ-3.3)
    """

    # REQ-3.2: Hedef improvement oranı
    TARGET_IMPROVEMENT_PERCENTAGE = 20.0

    def __init__(self, user_id: str):
        """
        Args:
            user_id: Kullanıcı ID
        """
        self.user_id = user_id
        self.sessions: list[ReadingSession] = []
        self._active_session: ReadingSession | None = None

        # Geçmiş veriler için (DB'den yüklenebilir)
        self.historical_normal_wpm: list[float] = []
        self.historical_bionic_wpm: list[float] = []

    def start_session(
        self,
        text_id: str,
        word_count: int,
        mode: ReadingMode = ReadingMode.BIONIC
    ) -> ReadingSession:
        """
        Okuma oturumu başlat

        Args:
            text_id: Metin ID
            word_count: Kelime sayısı
            mode: Okuma modu

        Returns:
            ReadingSession: Başlatılan oturum
        """
        if self._active_session:
            # Önceki oturumu kapat
            self.end_session()

        session = ReadingSession(
            session_id=str(uuid4()),
            user_id=self.user_id,
            text_id=text_id,
            mode=mode,
            word_count=word_count,
            start_time=datetime.now()
        )

        self._active_session = session
        logger.info(f"Reading session started: {session.session_id} ({mode.value})")

        return session

    def end_session(self, regression_count: int = 0) -> ReadingSession | None:
        """
        Okuma oturumunu bitir

        Args:
            regression_count: Geri dönüş sayısı (eye tracking'den)

        Returns:
            ReadingSession: Tamamlanan oturum
        """
        if not self._active_session:
            return None

        session = self._active_session
        session.end_time = datetime.now()
        session.completed = True
        session.regression_count = regression_count

        # WPM hesapla
        session.wpm = self._calculate_wpm(session)

        # Geçmişe ekle
        if session.mode == ReadingMode.NORMAL:
            self.historical_normal_wpm.append(session.wpm)
        else:
            self.historical_bionic_wpm.append(session.wpm)

        self.sessions.append(session)
        self._active_session = None

        logger.info(f"Reading session ended: {session.session_id}, WPM: {session.wpm:.1f}")

        return session

    def pause_session(self):
        """Oturumu duraklat"""
        if self._active_session:
            # Pause süresini başlat
            self._pause_start = datetime.now()

    def resume_session(self):
        """Oturumu devam ettir"""
        if self._active_session and hasattr(self, '_pause_start'):
            pause_duration = (datetime.now() - self._pause_start).total_seconds() * 1000
            self._active_session.pause_duration_ms += int(pause_duration)
            delattr(self, '_pause_start')

    def _calculate_wpm(self, session: ReadingSession) -> float:
        """WPM (Words Per Minute) hesapla"""
        if not session.end_time or not session.start_time:
            return 0.0

        total_duration = (session.end_time - session.start_time).total_seconds()

        # Pause süresini çıkar
        net_duration = total_duration - (session.pause_duration_ms / 1000)
        net_duration = max(1.0, net_duration)  # En az 1 saniye

        # WPM hesapla
        minutes = net_duration / 60
        wpm = session.word_count / minutes

        return round(wpm, 1)

    def get_comparison(self) -> SpeedComparison | None:
        """
        Normal vs Bionic hız karşılaştırması

        Returns:
            SpeedComparison: Karşılaştırma sonucu
        """
        if not self.historical_normal_wpm or not self.historical_bionic_wpm:
            return None

        normal_avg = statistics.mean(self.historical_normal_wpm)
        bionic_avg = statistics.mean(self.historical_bionic_wpm)

        improvement_absolute = bionic_avg - normal_avg
        improvement_percentage = (improvement_absolute / normal_avg) * 100 if normal_avg > 0 else 0

        # Confidence level hesapla (sample size'a göre)
        sample_size = min(len(self.historical_normal_wpm), len(self.historical_bionic_wpm))
        confidence = min(0.95, 0.5 + (sample_size * 0.05))  # Max %95

        return SpeedComparison(
            normal_wpm=round(normal_avg, 1),
            bionic_wpm=round(bionic_avg, 1),
            improvement_percentage=round(improvement_percentage, 1),
            improvement_absolute=round(improvement_absolute, 1),
            target_met=improvement_percentage >= self.TARGET_IMPROVEMENT_PERCENTAGE,
            sample_size=sample_size,
            confidence_level=confidence
        )

    def get_metrics(self, mode: ReadingMode | None = None) -> ReadingMetrics:
        """
        Okuma metriklerini hesapla

        Args:
            mode: Filtrelenecek mod (None ise tümü)

        Returns:
            ReadingMetrics: Hesaplanan metrikler
        """
        sessions = self.sessions

        if mode:
            sessions = [s for s in sessions if s.mode == mode]

        if not sessions:
            return ReadingMetrics(
                average_wpm=0.0,
                median_wpm=0.0,
                max_wpm=0.0,
                min_wpm=0.0,
                total_words_read=0,
                total_sessions=0,
                total_reading_time_minutes=0.0,
                saccade_estimate=0.0,
                regression_rate=0.0
            )

        wpm_values = [s.wpm for s in sessions if s.wpm > 0]
        total_words = sum(s.word_count for s in sessions)
        total_regressions = sum(s.regression_count for s in sessions)

        # Toplam okuma süresi
        total_time_seconds = sum(
            (s.end_time - s.start_time).total_seconds()
            for s in sessions if s.end_time
        )

        # Saccade tahmini (ortalama her 7-8 karakterde bir saccade)
        avg_chars_per_word = 6  # Türkçe için ortalama
        total_chars = total_words * avg_chars_per_word
        saccade_estimate = total_chars / 7.5

        return ReadingMetrics(
            average_wpm=round(statistics.mean(wpm_values), 1) if wpm_values else 0.0,
            median_wpm=round(statistics.median(wpm_values), 1) if wpm_values else 0.0,
            max_wpm=round(max(wpm_values), 1) if wpm_values else 0.0,
            min_wpm=round(min(wpm_values), 1) if wpm_values else 0.0,
            total_words_read=total_words,
            total_sessions=len(sessions),
            total_reading_time_minutes=round(total_time_seconds / 60, 1),
            saccade_estimate=round(saccade_estimate, 0),
            regression_rate=round(total_regressions / max(total_words, 1) * 100, 2)
        )

    def get_progress_report(self) -> dict:
        """Detaylı ilerleme raporu"""
        comparison = self.get_comparison()
        normal_metrics = self.get_metrics(ReadingMode.NORMAL)
        bionic_metrics = self.get_metrics(ReadingMode.BIONIC)

        return {
            "user_id": self.user_id,
            "comparison": {
                "normal_wpm": comparison.normal_wpm if comparison else None,
                "bionic_wpm": comparison.bionic_wpm if comparison else None,
                "improvement_percentage": comparison.improvement_percentage if comparison else None,
                "target_met": comparison.target_met if comparison else None,
                "sample_size": comparison.sample_size if comparison else 0
            } if comparison else None,
            "normal_reading": {
                "average_wpm": normal_metrics.average_wpm,
                "total_sessions": normal_metrics.total_sessions,
                "total_words": normal_metrics.total_words_read
            },
            "bionic_reading": {
                "average_wpm": bionic_metrics.average_wpm,
                "total_sessions": bionic_metrics.total_sessions,
                "total_words": bionic_metrics.total_words_read,
                "regression_rate": bionic_metrics.regression_rate
            },
            "recommendation": self._get_recommendation()
        }

    def _get_recommendation(self) -> str:
        """Kullanıcıya öneri"""
        comparison = self.get_comparison()

        if not comparison:
            return "Karşılaştırma için daha fazla okuma oturumu gerekli."

        if comparison.target_met:
            return f"Harika! Bionic Reading ile okuma hızınız %{comparison.improvement_percentage:.0f} arttı!"

        if comparison.improvement_percentage > 10:
            return f"İyi gidiyorsunuz! %{comparison.improvement_percentage:.0f} iyileşme var. Hedef: %20+"

        if comparison.improvement_percentage > 0:
            return "Bionic Reading'e alışmak zaman alabilir. Düzenli kullanmaya devam edin."

        return "Bionic Reading ayarlarınızı optimize etmeyi deneyin."

    def estimate_time_saved(self, total_words: int) -> dict:
        """Tahminî zaman tasarrufu hesapla"""
        comparison = self.get_comparison()

        if not comparison or comparison.normal_wpm == 0:
            return {
                "normal_time_minutes": 0,
                "bionic_time_minutes": 0,
                "time_saved_minutes": 0,
                "time_saved_percentage": 0
            }

        normal_time = total_words / comparison.normal_wpm
        bionic_time = total_words / comparison.bionic_wpm
        time_saved = normal_time - bionic_time

        return {
            "normal_time_minutes": round(normal_time, 1),
            "bionic_time_minutes": round(bionic_time, 1),
            "time_saved_minutes": round(time_saved, 1),
            "time_saved_percentage": round((time_saved / normal_time) * 100, 1) if normal_time > 0 else 0
        }

    def add_historical_data(self, mode: ReadingMode, wpm_values: list[float]):
        """Geçmiş verileri ekle (DB'den yükleme için)"""
        if mode == ReadingMode.NORMAL:
            self.historical_normal_wpm.extend(wpm_values)
        else:
            self.historical_bionic_wpm.extend(wpm_values)

    def reset(self):
        """Tüm verileri sıfırla"""
        self.sessions.clear()
        self.historical_normal_wpm.clear()
        self.historical_bionic_wpm.clear()
        self._active_session = None
