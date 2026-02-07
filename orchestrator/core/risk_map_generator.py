"""Risk Map Generator - Görev risk analizi.

Görevlerin risk seviyesini değerlendirip risk haritası üretir:
- Dosya complexity analizi
- Dependency risk skorlama
- Değişiklik büyüklüğü tahmini
- Önceki hata geçmişi
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class RiskLevel(Enum):
    """Risk seviyeleri."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(Enum):
    """Risk kategorileri."""

    COMPLEXITY = "complexity"
    DEPENDENCY = "dependency"
    SCOPE = "scope"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DATA_INTEGRITY = "data_integrity"


@dataclass
class RiskFactor:
    """Tek bir risk faktörü."""

    category: RiskCategory
    level: RiskLevel
    score: float  # 0.0 - 1.0
    description: str
    file_path: str | None = None
    mitigation: str = ""


@dataclass
class RiskMap:
    """Bir görevin risk haritası."""

    task_id: str
    overall_level: RiskLevel = RiskLevel.LOW
    overall_score: float = 0.0
    factors: list[RiskFactor] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def add_factor(self, factor: RiskFactor) -> None:
        """Risk faktörü ekle ve genel skoru güncelle."""
        self.factors.append(factor)
        self._recalculate()

    def _recalculate(self) -> None:
        """Genel risk skorunu ve seviyesini yeniden hesapla."""
        if not self.factors:
            self.overall_score = 0.0
            self.overall_level = RiskLevel.LOW
            return

        weights = {
            RiskCategory.SECURITY: 2.0,
            RiskCategory.DATA_INTEGRITY: 1.8,
            RiskCategory.DEPENDENCY: 1.5,
            RiskCategory.COMPLEXITY: 1.2,
            RiskCategory.SCOPE: 1.0,
            RiskCategory.PERFORMANCE: 0.8,
        }

        weighted_sum = sum(
            f.score * weights.get(f.category, 1.0) for f in self.factors
        )
        total_weight = sum(
            weights.get(f.category, 1.0) for f in self.factors
        )
        self.overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        if self.overall_score >= 0.8:
            self.overall_level = RiskLevel.CRITICAL
        elif self.overall_score >= 0.6:
            self.overall_level = RiskLevel.HIGH
        elif self.overall_score >= 0.3:
            self.overall_level = RiskLevel.MEDIUM
        else:
            self.overall_level = RiskLevel.LOW

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable dict."""
        return {
            "task_id": self.task_id,
            "overall_level": self.overall_level.value,
            "overall_score": round(self.overall_score, 3),
            "factors": [
                {
                    "category": f.category.value,
                    "level": f.level.value,
                    "score": round(f.score, 3),
                    "description": f.description,
                    "file_path": f.file_path,
                    "mitigation": f.mitigation,
                }
                for f in self.factors
            ],
            "recommendations": self.recommendations,
        }


@dataclass
class RiskMapGenerator:
    """Risk haritası üretici.

    Bir görevi analiz edip risk haritası oluşturur.

    Example:
        >>> generator = RiskMapGenerator(working_dir=Path("."))
        >>> risk_map = generator.analyze("task-001", files=["auth/login.py"])
    """

    working_dir: Path = field(default_factory=lambda: Path("."))

    # Yüksek riskli dosya pattern'ları
    HIGH_RISK_PATTERNS: list[str] = field(
        default_factory=lambda: [
            "auth", "login", "password", "token", "secret",
            "payment", "billing", "admin", "migration",
            "delete", "drop", "truncate",
        ]
    )

    # Güvenlik-kritik uzantılar
    SECURITY_EXTENSIONS: list[str] = field(
        default_factory=lambda: [".env", ".key", ".pem", ".crt"]
    )

    def analyze(
        self,
        task_id: str,
        *,
        description: str = "",
        files: list[str] | None = None,
    ) -> RiskMap:
        """Görev için risk haritası oluştur.

        Args:
            task_id: Görev ID'si.
            description: Görev açıklaması.
            files: Etkilenecek dosya listesi.

        Returns:
            RiskMap with all identified risk factors.
        """
        risk_map = RiskMap(task_id=task_id)

        if files:
            self._analyze_files(risk_map, files)

        if description:
            self._analyze_description(risk_map, description)

        self._generate_recommendations(risk_map)
        return risk_map

    def _analyze_files(self, risk_map: RiskMap, files: list[str]) -> None:
        """Dosya bazlı risk analizi."""
        # Scope riski
        if len(files) > 5:
            risk_map.add_factor(RiskFactor(
                category=RiskCategory.SCOPE,
                level=RiskLevel.HIGH,
                score=min(len(files) / 10.0, 1.0),
                description=f"{len(files)} dosya etkilenecek",
                mitigation="Değişiklikleri daha küçük PR'lara bölün",
            ))

        for file_path in files:
            path_lower = file_path.lower()

            # Güvenlik riski
            if any(p in path_lower for p in self.HIGH_RISK_PATTERNS):
                risk_map.add_factor(RiskFactor(
                    category=RiskCategory.SECURITY,
                    level=RiskLevel.HIGH,
                    score=0.8,
                    description=f"Güvenlik-kritik dosya: {file_path}",
                    file_path=file_path,
                    mitigation="Security review zorunlu",
                ))

            # Migration riski
            if "migration" in path_lower or "alembic" in path_lower:
                risk_map.add_factor(RiskFactor(
                    category=RiskCategory.DATA_INTEGRITY,
                    level=RiskLevel.CRITICAL,
                    score=0.9,
                    description=f"Database migration: {file_path}",
                    file_path=file_path,
                    mitigation="Rollback planı hazırla, staging'de test et",
                ))

            # Complexity - büyük dosya kontrolü
            full_path = self.working_dir / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                if size > 50_000:  # 50KB+
                    risk_map.add_factor(RiskFactor(
                        category=RiskCategory.COMPLEXITY,
                        level=RiskLevel.MEDIUM,
                        score=min(size / 100_000, 1.0),
                        description=f"Büyük dosya ({size // 1024}KB): {file_path}",
                        file_path=file_path,
                        mitigation="Değişiklikleri minimal tut",
                    ))

    def _analyze_description(self, risk_map: RiskMap, description: str) -> None:
        """Görev açıklamasından risk analizi."""
        desc_lower = description.lower()

        risky_keywords = {
            "refactor": (RiskCategory.COMPLEXITY, 0.5, "Refactoring geniş kapsamlı olabilir"),
            "migration": (RiskCategory.DATA_INTEGRITY, 0.8, "Veri bütünlüğü riski"),
            "delete": (RiskCategory.DATA_INTEGRITY, 0.6, "Veri kaybı riski"),
            "security": (RiskCategory.SECURITY, 0.7, "Güvenlik değişikliği"),
            "performance": (RiskCategory.PERFORMANCE, 0.4, "Performans etkisi olabilir"),
        }

        for keyword, (category, score, desc) in risky_keywords.items():
            if keyword in desc_lower:
                risk_map.add_factor(RiskFactor(
                    category=category,
                    level=RiskLevel.MEDIUM if score < 0.6 else RiskLevel.HIGH,
                    score=score,
                    description=desc,
                ))

    def _generate_recommendations(self, risk_map: RiskMap) -> None:
        """Risk seviyesine göre öneriler üret."""
        if risk_map.overall_level == RiskLevel.CRITICAL:
            risk_map.recommendations.extend([
                "Plan Mode kullanın (Shift+Tab x2)",
                "Security reviewer subagent çalıştırın",
                "Staging ortamında test edin",
                "Rollback planı hazırlayın",
            ])
        elif risk_map.overall_level == RiskLevel.HIGH:
            risk_map.recommendations.extend([
                "Plan Mode kullanın",
                "Code review zorunlu",
                "Tüm testleri çalıştırın",
            ])
        elif risk_map.overall_level == RiskLevel.MEDIUM:
            risk_map.recommendations.extend([
                "İlgili testleri çalıştırın",
                "Değişiklikleri gözden geçirin",
            ])
