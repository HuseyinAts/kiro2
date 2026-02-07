"""
Deneme Sınavı Tipleri (Test Types)
Task 61: Deneme Sınavı Tipleri
Requirements: REQ-49.33-49.52

Bu modül 5 farklı test tipini implement eder:
1. Diagnostic Test - Zayıf alanları tespit etme
2. Formative Test - Öğrenme ilerlemesi değerlendirme  
3. Summative Test - Final değerlendirme
4. Benchmark Test - Ulusal ortalama ile karşılaştırma
5. Mock Exam - Tam ÖSYM simülasyonu
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TestConfiguration:
    """Test konfigürasyonu"""

    test_type: str
    target_length: Optional[int] = None
    min_length: int = 10
    max_length: int = 50
    precision_threshold: float = 0.3
    content_constraints: Optional[Dict[str, int]] = None
    time_limit_minutes: Optional[int] = None
    immediate_feedback: bool = False
    adaptive_difficulty: bool = True
    osym_format_compliance: bool = False


class BaseTestType(ABC):
    """Test tipi için temel sınıf"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def get_configuration(self) -> TestConfiguration:
        """Test konfigürasyonunu döndür"""
        pass

    @abstractmethod
    def generate_feedback(self, session_data: Dict) -> Dict:
        """Test için geri bildirim oluştur"""
        pass

    @abstractmethod
    def calculate_recommendations(self, session_data: Dict) -> List[str]:
        """Öneriler oluştur"""
        pass
