"""
LearningPathAgent Yanıt Doğrulayıcı

Bu modül, LearningPathAgent'ın ürettiği öğrenme yollarını doğrular.

Doğrulamalar:
1. Müfredat uyumu (MEB kazanımları)
2. Ön koşul sıralaması
3. Zorluk seviyesi uygunluğu
4. Tahmini süre gerçekçiliği
5. Kaynak erişilebilirliği

Requirements: REQ-1.1 - REQ-1.6
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from backend.validators.base_response_validator import (
    AgentResponse,
    BaseResponseValidator,
    ValidationResult,
)

logger = logging.getLogger(__name__)


# Zorluk seviyesi eşleştirmeleri
DIFFICULTY_LEVELS = {
    "çok_kolay": 1,
    "kolay": 2,
    "orta": 3,
    "zor": 4,
    "çok_zor": 5,
}

STUDENT_LEVELS = {
    "başlangıç": 2,
    "orta": 3,
    "ileri": 4,
}


class LearningPathValidator(BaseResponseValidator):
    """
    LearningPathAgent yanıtlarını doğrulayan validator.

    Öğrenme yollarının:
    - MEB müfredatına uygunluğunu
    - Konu sıralamasının doğruluğunu
    - Zorluk seviyesinin öğrenciye uygunluğunu
    - Süre tahminlerinin gerçekçiliğini
    - Kaynakların erişilebilirliğini

    kontrol eder.
    """

    # Minimum/maksimum saat tahminleri (konu başına)
    MIN_HOURS_PER_TOPIC = 2
    MAX_HOURS_PER_TOPIC = 10

    def __init__(
        self,
        weight: float = 0.30,
        meb_api_url: Optional[str] = None,
        resource_check_timeout: float = 5.0,
    ):
        """
        Args:
            weight: Validator ağırlığı (default: 0.30)
            meb_api_url: MEB API URL'i (opsiyonel)
            resource_check_timeout: Kaynak erişilebilirlik kontrolü timeout'u
        """
        super().__init__(weight)
        self.meb_api_url = meb_api_url
        self.resource_check_timeout = resource_check_timeout

        # MEB müfredat cache (basit in-memory)
        self._curriculum_cache: Dict[str, List[str]] = {}

    def get_validator_name(self) -> str:
        return "LearningPathValidator"

    async def validate(self, response: AgentResponse) -> ValidationResult:
        """
        LearningPathAgent yanıtını doğrula.

        Args:
            response: Doğrulanacak agent yanıtı

        Returns:
            ValidationResult: Doğrulama sonucu
        """
        errors: List[str] = []
        warnings: List[str] = []
        suggestions: List[str] = []
        score = 1.0

        # Learning path verilerini çıkar
        learning_path = response.response_data.get("learning_path", {})

        if not learning_path:
            # response_text'ten çıkarmaya çalış
            learning_path = self._extract_learning_path_from_text(
                response.response_text
            )

        topics = learning_path.get("topics", [])
        prerequisites = learning_path.get("prerequisites", {})
        difficulty = learning_path.get("difficulty", "orta")
        estimated_hours = learning_path.get("estimated_hours", 0)
        resources = learning_path.get("resources", [])

        # Context bilgilerini al
        context = response.context or {}
        grade_level = context.get("grade_level", 9)
        student_level = context.get("student_level", "orta")

        # 1. Müfredat uyumu kontrolü (REQ-1.1)
        curriculum_result = await self._validate_curriculum_compliance(
            topics, grade_level
        )
        if curriculum_result["invalid_topics"]:
            for topic in curriculum_result["invalid_topics"]:
                errors.append(f"Konu müfredatta yok: {topic}")
            score -= 0.2 * len(curriculum_result["invalid_topics"])
            suggestions.append(
                "Müfredatta olmayan konuları çıkarın veya uygun sınıf seviyesi belirleyin"
            )

        # 2. Ön koşul sıralaması kontrolü (REQ-1.2)
        prereq_result = self._validate_prerequisite_order(
            topics, prerequisites
        )
        if prereq_result["errors"]:
            for error in prereq_result["errors"]:
                errors.append(f"Ön koşul sıralaması hatalı: {error}")
            score -= 0.15 * len(prereq_result["errors"])
            suggestions.append(
                "Ön koşul konularını, bağımlı konulardan önce sıralayın"
            )

        # 3. Zorluk seviyesi kontrolü (REQ-1.3)
        difficulty_result = self._validate_difficulty_level(
            difficulty, student_level
        )
        if not difficulty_result["is_appropriate"]:
            warnings.append(difficulty_result["message"])
            score -= 0.1
            suggestions.append(difficulty_result["suggestion"])

        # 4. Tahmini süre kontrolü (REQ-1.4)
        time_result = self._validate_estimated_time(
            estimated_hours, len(topics)
        )
        if time_result["status"] == "too_short":
            warnings.append("Tahmini süre çok kısa görünüyor")
            score -= 0.05
            suggestions.append(
                f"Tahmini süreyi en az {time_result['min_expected']} saat olarak güncelleyin"
            )
        elif time_result["status"] == "too_long":
            warnings.append("Tahmini süre çok uzun görünüyor")
            score -= 0.05
            suggestions.append(
                f"Tahmini süreyi en fazla {time_result['max_expected']} saat olarak güncelleyin"
            )

        # 5. Kaynak erişilebilirliği kontrolü (REQ-1.5)
        if resources:
            resource_result = await self._validate_resource_accessibility(
                resources
            )
            for inaccessible in resource_result["inaccessible"]:
                warnings.append(
                    f"Kaynak erişilebilir değil: {inaccessible['title']}"
                )
                score -= 0.05
            if resource_result["inaccessible"]:
                suggestions.append(
                    "Erişilemeyen kaynakları alternatiflerle değiştirin"
                )

        # Skoru sınırla
        score = max(0.0, min(1.0, score))

        # Metadata oluştur
        metadata = {
            "validator": self.get_validator_name(),
            "topic_count": len(topics),
            "grade_level": grade_level,
            "student_level": student_level,
            "difficulty": difficulty,
            "estimated_hours": estimated_hours,
            "resource_count": len(resources),
        }

        return ValidationResult(
            is_valid=len(errors) == 0,
            score=score,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metadata=metadata,
        )

    def _extract_learning_path_from_text(
        self, text: str
    ) -> Dict[str, Any]:
        """
        Metin yanıtından öğrenme yolu bilgilerini çıkar.

        Args:
            text: Agent yanıt metni

        Returns:
            Dict: Çıkarılan öğrenme yolu verileri
        """
        # Basit extraction - daha gelişmiş NLP ile iyileştirilebilir
        topics = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            # Numaralı liste formatı: "1. Konu adı"
            if line and line[0].isdigit() and '.' in line:
                topic = line.split('.', 1)[1].strip()
                if topic and len(topic) > 2:
                    topics.append(topic)
            # Bullet point formatı: "- Konu adı"
            elif line.startswith('-') or line.startswith('•'):
                topic = line[1:].strip()
                if topic and len(topic) > 2:
                    topics.append(topic)

        return {
            "topics": topics[:20],  # Max 20 konu
            "prerequisites": {},
            "difficulty": "orta",
            "estimated_hours": len(topics) * 4,  # Varsayılan tahmin
            "resources": [],
        }

    async def _validate_curriculum_compliance(
        self, topics: List[str], grade_level: int
    ) -> Dict[str, Any]:
        """
        Konuların MEB müfredatına uygunluğunu kontrol et.

        Args:
            topics: Konu listesi
            grade_level: Sınıf seviyesi

        Returns:
            Dict: Geçerli ve geçersiz konular
        """
        # Cache kontrol
        cache_key = f"grade_{grade_level}"
        if cache_key not in self._curriculum_cache:
            self._curriculum_cache[cache_key] = await self._fetch_curriculum(
                grade_level
            )

        valid_topics = self._curriculum_cache[cache_key]
        invalid_topics = []

        for topic in topics:
            topic_lower = topic.lower()
            # Basit eşleşme - fuzzy matching iyileştirilebilir
            is_valid = any(
                topic_lower in valid.lower() or valid.lower() in topic_lower
                for valid in valid_topics
            )
            if not is_valid:
                invalid_topics.append(topic)

        return {
            "valid_topics": [t for t in topics if t not in invalid_topics],
            "invalid_topics": invalid_topics,
        }

    async def _fetch_curriculum(self, grade_level: int) -> List[str]:
        """
        MEB müfredatını getir (API veya fallback).

        Args:
            grade_level: Sınıf seviyesi

        Returns:
            List[str]: Müfredat konuları
        """
        if self.meb_api_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.meb_api_url}/curriculum/{grade_level}",
                        timeout=aiohttp.ClientTimeout(total=5.0),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return data.get("topics", [])
            except Exception as e:
                logger.warning(f"MEB API error: {e}")

        # Fallback: Temel müfredat konuları
        return self._get_fallback_curriculum(grade_level)

    def _get_fallback_curriculum(self, grade_level: int) -> List[str]:
        """
        Varsayılan müfredat konuları (fallback).

        Args:
            grade_level: Sınıf seviyesi

        Returns:
            List[str]: Temel konular
        """
        # Matematik konuları (sınıf seviyesine göre genişletilebilir)
        base_topics = [
            "sayılar", "işlemler", "denklemler", "eşitsizlikler",
            "fonksiyonlar", "geometri", "üçgenler", "dörtgenler",
            "çember", "analitik geometri", "trigonometri",
            "türev", "integral", "olasılık", "istatistik",
            "polinomlar", "permütasyon", "kombinasyon",
            "logaritma", "üstel fonksiyonlar", "limit",
            "matrisler", "determinant", "vektörler",
        ]

        # Fen konuları
        science_topics = [
            "fizik", "kimya", "biyoloji",
            "hareket", "kuvvet", "enerji", "ısı", "elektrik",
            "atom", "periyodik tablo", "kimyasal bağlar",
            "hücre", "kalıtım", "evrim", "ekosistem",
        ]

        # Türkçe/Edebiyat konuları
        turkish_topics = [
            "paragraf", "sözcük türleri", "cümle bilgisi",
            "anlatım bozuklukları", "yazım kuralları",
            "edebi sanatlar", "şiir", "roman", "öykü",
        ]

        return base_topics + science_topics + turkish_topics

    def _validate_prerequisite_order(
        self,
        topics: List[str],
        prerequisites: Dict[str, List[str]],
    ) -> Dict[str, Any]:
        """
        Ön koşul sıralamasını doğrula.

        Args:
            topics: Konu listesi (sıralı)
            prerequisites: Konu -> ön koşullar mapping

        Returns:
            Dict: Doğrulama sonucu
        """
        errors = []

        for topic, prereqs in prerequisites.items():
            if topic not in topics:
                continue

            topic_index = topics.index(topic)

            for prereq in prereqs:
                if prereq in topics:
                    prereq_index = topics.index(prereq)
                    if prereq_index >= topic_index:
                        errors.append(
                            f"'{prereq}' konusu '{topic}' konusundan önce gelmeli"
                        )

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
        }

    def _validate_difficulty_level(
        self, difficulty: str, student_level: str
    ) -> Dict[str, Any]:
        """
        Zorluk seviyesinin öğrenci seviyesine uygunluğunu kontrol et.

        Args:
            difficulty: Öğrenme yolu zorluğu
            student_level: Öğrenci seviyesi

        Returns:
            Dict: Uygunluk sonucu
        """
        diff_value = DIFFICULTY_LEVELS.get(difficulty.lower(), 3)
        student_value = STUDENT_LEVELS.get(student_level.lower(), 3)

        # Zorluk, öğrenci seviyesinin ±1 aralığında olmalı
        diff = abs(diff_value - student_value)

        if diff <= 1:
            return {
                "is_appropriate": True,
                "message": "",
                "suggestion": "",
            }
        elif diff_value > student_value:
            return {
                "is_appropriate": False,
                "message": f"Zorluk seviyesi ({difficulty}) öğrenci seviyesi ({student_level}) için çok yüksek",
                "suggestion": "Daha kolay bir zorluk seviyesi seçin veya ön hazırlık konuları ekleyin",
            }
        else:
            return {
                "is_appropriate": False,
                "message": f"Zorluk seviyesi ({difficulty}) öğrenci seviyesi ({student_level}) için çok düşük",
                "suggestion": "Daha zor bir zorluk seviyesi seçin veya ileri konular ekleyin",
            }

    def _validate_estimated_time(
        self, estimated_hours: float, topic_count: int
    ) -> Dict[str, Any]:
        """
        Tahmini sürenin gerçekçiliğini kontrol et.

        Args:
            estimated_hours: Tahmini süre (saat)
            topic_count: Konu sayısı

        Returns:
            Dict: Süre kontrolü sonucu
        """
        if topic_count == 0:
            return {"status": "ok", "min_expected": 0, "max_expected": 0}

        min_expected = topic_count * self.MIN_HOURS_PER_TOPIC
        max_expected = topic_count * self.MAX_HOURS_PER_TOPIC

        if estimated_hours < min_expected:
            return {
                "status": "too_short",
                "min_expected": min_expected,
                "max_expected": max_expected,
            }
        elif estimated_hours > max_expected:
            return {
                "status": "too_long",
                "min_expected": min_expected,
                "max_expected": max_expected,
            }
        else:
            return {
                "status": "ok",
                "min_expected": min_expected,
                "max_expected": max_expected,
            }

    async def _validate_resource_accessibility(
        self, resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Kaynakların erişilebilirliğini kontrol et.

        Args:
            resources: Kaynak listesi

        Returns:
            Dict: Erişilebilirlik sonucu
        """
        accessible = []
        inaccessible = []

        async def check_resource(resource: Dict[str, Any]) -> Tuple[bool, Dict]:
            url = resource.get("url")
            if not url:
                return True, resource

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.head(
                        url,
                        timeout=aiohttp.ClientTimeout(
                            total=self.resource_check_timeout
                        ),
                        allow_redirects=True,
                    ) as resp:
                        return resp.status == 200, resource
            except Exception:
                return False, resource

        # Paralel kontrol
        tasks = [check_resource(r) for r in resources[:10]]  # Max 10 kaynak
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                continue
            is_accessible, resource = result
            if is_accessible:
                accessible.append(resource)
            else:
                inaccessible.append(resource)

        return {
            "accessible": accessible,
            "inaccessible": inaccessible,
        }
