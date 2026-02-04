"""
Structured Learning Path Generation System
Teknofest 2025 - Eğitim Eylemci Projesi

Bu modül:
- Prerequisite dependency mapping system
- Milestone and checkpoint creation
- Time-based scheduling algorithms
- Learning objective tracking
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DependencyType(Enum):
    """Bağımlılık türleri"""

    PREREQUISITE = "prerequisite"  # Önkoşul
    COREQUISITE = "corequisite"  # Eş zamanlı
    RECOMMENDED = "recommended"  # Önerilen
    OPTIONAL = "optional"  # Opsiyonel


class MilestoneType(Enum):
    """Kilometre taşı türleri"""

    KNOWLEDGE_CHECK = "knowledge_check"  # Bilgi kontrolü
    SKILL_ASSESSMENT = "skill_assessment"  # Beceri değerlendirmesi
    PROJECT_COMPLETION = "project_completion"  # Proje tamamlama
    PHASE_COMPLETION = "phase_completion"  # Faz tamamlama
    FINAL_ASSESSMENT = "final_assessment"  # Final değerlendirmesi


class LearningObjectiveType(Enum):
    """Öğrenme hedefi türleri"""

    KNOWLEDGE = "knowledge"  # Bilgi
    COMPREHENSION = "comprehension"  # Anlama
    APPLICATION = "application"  # Uygulama
    ANALYSIS = "analysis"  # Analiz
    SYNTHESIS = "synthesis"  # Sentez
    EVALUATION = "evaluation"  # Değerlendirme


@dataclass
class LearningObjective:
    """Öğrenme hedefi"""

    objective_id: str
    title: str
    description: str
    objective_type: LearningObjectiveType
    bloom_level: int  # 1-6 Bloom taksonomisi seviyesi
    measurable_outcomes: list[str]  # Ölçülebilir çıktılar
    assessment_criteria: list[str]  # Değerlendirme kriterleri
    estimated_time_minutes: int
    difficulty_level: float  # 0-1 arası
    prerequisites: list[str]  # Önkoşul objective ID'leri
    tags: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Milestone:
    """Kilometre taşı"""

    milestone_id: str
    title: str
    description: str
    milestone_type: MilestoneType
    objectives: list[str]  # İlgili objective ID'leri
    completion_criteria: list[str]  # Tamamlama kriterleri
    estimated_time_minutes: int
    required_score: float  # Geçmek için gereken skor (0-1)
    resources: list[str]  # İlgili kaynak ID'leri
    position_in_path: int  # Yoldaki pozisyon
    dependencies: list[str]  # Bağımlı milestone ID'leri
    rewards: list[str]  # Tamamlama ödülleri
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningPhase:
    """Öğrenme fazı"""

    phase_id: str
    title: str
    description: str
    objectives: list[LearningObjective]
    milestones: list[Milestone]
    estimated_duration_days: int
    difficulty_progression: list[float]  # Fazın zorluk ilerlemesi
    prerequisites: list[str]  # Önkoşul faz ID'leri
    learning_activities: list[str]  # Öğrenme aktiviteleri
    assessment_methods: list[str]  # Değerlendirme yöntemleri
    success_criteria: list[str]  # Başarı kriterleri
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StructuredPath:
    """Yapılandırılmış öğrenme yolu"""

    path_id: str
    title: str
    description: str
    student_id: str
    learning_goal: str
    phases: list[LearningPhase]
    dependency_graph: dict[str, list[str]]  # Bağımlılık grafiği
    total_objectives: int
    total_milestones: int
    estimated_total_time_hours: float
    difficulty_curve: list[float]  # Zorluk eğrisi
    completion_percentage: float
    current_phase: str | None
    current_milestone: str | None
    adaptive_parameters: dict[str, Any]  # Adaptif parametreler
    created_at: datetime
    last_updated: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduleItem:
    """Zamanlama öğesi"""

    item_id: str
    item_type: str  # objective, milestone, resource
    title: str
    scheduled_date: datetime
    estimated_duration_minutes: int
    priority: int  # 1-5 arası
    dependencies: list[str]
    flexible: bool  # Esnek zamanlama
    metadata: dict[str, Any] = field(default_factory=dict)


class StructuredLearningPathGenerator:
    """Yapılandırılmış Öğrenme Yolu Oluşturucu"""

    def __init__(self):
        self.objective_templates = self._load_objective_templates()
        self.milestone_templates = self._load_milestone_templates()
        self.dependency_rules = self._load_dependency_rules()
        self.scheduling_algorithms = self._load_scheduling_algorithms()

    def _load_objective_templates(self) -> dict[str, list[dict[str, Any]]]:
        """Öğrenme hedefi şablonları"""
        return {
            "matematik": [
                {
                    "title": "Temel Sayı Kavramları",
                    "type": LearningObjectiveType.KNOWLEDGE,
                    "bloom_level": 1,
                    "outcomes": ["Doğal sayıları tanır", "Sayı doğrusunu kullanır"],
                    "time": 60,
                    "difficulty": 0.2,
                },
                {
                    "title": "Dört İşlem Uygulaması",
                    "type": LearningObjectiveType.APPLICATION,
                    "bloom_level": 3,
                    "outcomes": ["Toplama işlemi yapar", "Çıkarma işlemi yapar"],
                    "time": 90,
                    "difficulty": 0.4,
                    "prerequisites": ["Temel Sayı Kavramları"],
                },
                {
                    "title": "Problem Çözme Stratejileri",
                    "type": LearningObjectiveType.ANALYSIS,
                    "bloom_level": 4,
                    "outcomes": ["Problemi analiz eder", "Çözüm stratejisi geliştirir"],
                    "time": 120,
                    "difficulty": 0.7,
                    "prerequisites": ["Dört İşlem Uygulaması"],
                },
            ],
            "fen": [
                {
                    "title": "Madde ve Özellikleri",
                    "type": LearningObjectiveType.KNOWLEDGE,
                    "bloom_level": 1,
                    "outcomes": [
                        "Maddenin hallerini bilir",
                        "Fiziksel özellikleri tanır",
                    ],
                    "time": 75,
                    "difficulty": 0.3,
                },
                {
                    "title": "Deney Tasarlama",
                    "type": LearningObjectiveType.SYNTHESIS,
                    "bloom_level": 5,
                    "outcomes": ["Hipotez kurar", "Deney düzeneği tasarlar"],
                    "time": 150,
                    "difficulty": 0.8,
                    "prerequisites": ["Madde ve Özellikleri"],
                },
            ],
        }

    def _load_milestone_templates(self) -> dict[str, list[dict[str, Any]]]:
        """Kilometre taşı şablonları"""
        return {
            "knowledge_check": [
                {
                    "title": "Temel Kavramlar Testi",
                    "type": MilestoneType.KNOWLEDGE_CHECK,
                    "criteria": ["10 sorudan en az 7'sini doğru yanıtlar"],
                    "time": 30,
                    "required_score": 0.7,
                }
            ],
            "skill_assessment": [
                {
                    "title": "Uygulama Becerisi Değerlendirmesi",
                    "type": MilestoneType.SKILL_ASSESSMENT,
                    "criteria": ["Verilen problemi çözer", "Çözüm adımlarını açıklar"],
                    "time": 45,
                    "required_score": 0.8,
                }
            ],
            "project": [
                {
                    "title": "Mini Proje Tamamlama",
                    "type": MilestoneType.PROJECT_COMPLETION,
                    "criteria": ["Projeyi tamamlar", "Sonuçları sunar"],
                    "time": 120,
                    "required_score": 0.75,
                }
            ],
        }

    def _load_dependency_rules(self) -> dict[str, list[str]]:
        """Bağımlılık kuralları"""
        return {
            "matematik": [
                "Sayılar → Dört İşlem → Kesirler → Ondalık Sayılar",
                "Temel Geometri → Alan Hesaplama → Hacim Hesaplama",
                "Cebir Temelleri → Denklemler → Fonksiyonlar",
            ],
            "fen": [
                "Madde → Karışımlar → Kimyasal Değişim",
                "Kuvvet → Hareket → Enerji",
                "Hücre → Doku → Organ → Sistem",
            ],
        }

    def _load_scheduling_algorithms(self) -> dict[str, Any]:
        """Zamanlama algoritmaları"""
        return {
            "linear": {"name": "Doğrusal İlerleme", "flexibility": 0.1},
            "adaptive": {"name": "Adaptif Zamanlama", "flexibility": 0.3},
            "spiral": {"name": "Spiral Öğrenme", "flexibility": 0.2},
            "mastery": {"name": "Ustalık Tabanlı", "flexibility": 0.4},
        }

    async def generate_structured_path(
        self,
        student_id: str,
        learning_goal: str,
        subject: str,
        duration_weeks: int = 8,
        difficulty_preference: float = 0.5,
        learning_style: str = "mixed",
    ) -> StructuredPath:
        """
        Yapılandırılmış öğrenme yolu oluştur

        Args:
            student_id: Öğrenci ID
            learning_goal: Öğrenme hedefi
            subject: Konu alanı
            duration_weeks: Süre (hafta)
            difficulty_preference: Zorluk tercihi (0-1)
            learning_style: Öğrenme stili

        Returns:
            Yapılandırılmış öğrenme yolu
        """
        try:
            # 1. Öğrenme hedeflerini oluştur
            objectives = await self._generate_learning_objectives(
                subject, learning_goal, difficulty_preference
            )

            # 2. Bağımlılık grafiğini oluştur
            dependency_graph = self._build_dependency_graph(objectives)

            # 3. Kilometre taşlarını oluştur
            milestones = self._create_milestones(objectives, subject)

            # 4. Fazları organize et
            phases = self._organize_into_phases(objectives, milestones, duration_weeks)

            # 5. Zorluk eğrisini hesapla
            difficulty_curve = self._calculate_difficulty_curve(phases)

            # 6. Yapılandırılmış yolu oluştur
            structured_path = StructuredPath(
                path_id=f"structured_{student_id}_{datetime.now().timestamp()}",
                title=f"Yapılandırılmış {subject.title()} Öğrenme Yolu",
                description=f"{learning_goal} hedefi için {duration_weeks} haftalık yapılandırılmış program",
                student_id=student_id,
                learning_goal=learning_goal,
                phases=phases,
                dependency_graph=dependency_graph,
                total_objectives=len(objectives),
                total_milestones=len(milestones),
                estimated_total_time_hours=sum(
                    obj.estimated_time_minutes for obj in objectives
                )
                / 60,
                difficulty_curve=difficulty_curve,
                completion_percentage=0.0,
                current_phase=phases[0].phase_id if phases else None,
                current_milestone=None,
                adaptive_parameters={
                    "difficulty_preference": difficulty_preference,
                    "learning_style": learning_style,
                    "auto_adjust": True,
                    "flexibility_level": 0.3,
                },
                created_at=datetime.now(),
                last_updated=datetime.now(),
                metadata={
                    "subject": subject,
                    "duration_weeks": duration_weeks,
                    "generation_method": "structured_algorithm",
                },
            )

            logger.info(
                f"Generated structured learning path: {structured_path.path_id}"
            )
            return structured_path

        except Exception as e:
            logger.error(f"Error generating structured path: {e!s}")
            raise

    async def _generate_learning_objectives(
        self, subject: str, learning_goal: str, difficulty_preference: float
    ) -> list[LearningObjective]:
        """Öğrenme hedeflerini oluştur"""
        objectives = []
        templates = self.objective_templates.get(subject.lower(), [])

        # Template'lerden hedefler oluştur
        for i, template in enumerate(templates):
            if template["difficulty"] <= difficulty_preference + 0.3:  # Zorluk filtresi
                objective = LearningObjective(
                    objective_id=f"{subject}_obj_{i}",
                    title=template["title"],
                    description=f"{learning_goal} kapsamında {template['title']}",
                    objective_type=template["type"],
                    bloom_level=template["bloom_level"],
                    measurable_outcomes=template["outcomes"],
                    assessment_criteria=[
                        f"{outcome} kriterini karşılar"
                        for outcome in template["outcomes"]
                    ],
                    estimated_time_minutes=template["time"],
                    difficulty_level=template["difficulty"],
                    prerequisites=template.get("prerequisites", []),
                    tags=[subject, learning_goal.lower()],
                    metadata={"template_based": True},
                )
                objectives.append(objective)

        # Ek hedefler oluştur (LLM ile)
        if len(objectives) < 5:  # Minimum 5 hedef
            additional_objectives = await self._generate_additional_objectives(
                subject, learning_goal, 5 - len(objectives)
            )
            objectives.extend(additional_objectives)

        return objectives

    async def _generate_additional_objectives(
        self, subject: str, learning_goal: str, count: int
    ) -> list[LearningObjective]:
        """LLM ile ek hedefler oluştur"""
        # Basit implementasyon - gerçek uygulamada LLM kullanılacak
        additional = []

        for i in range(count):
            objective = LearningObjective(
                objective_id=f"{subject}_additional_{i}",
                title=f"{subject.title()} - Ek Hedef {i+1}",
                description=f"{learning_goal} için ek öğrenme hedefi",
                objective_type=LearningObjectiveType.APPLICATION,
                bloom_level=3,
                measurable_outcomes=[f"Hedef {i+1} çıktısını gerçekleştirir"],
                assessment_criteria=[f"Hedef {i+1} kriterini karşılar"],
                estimated_time_minutes=60,
                difficulty_level=0.5,
                prerequisites=[],
                tags=[subject, "additional"],
                metadata={"generated": True},
            )
            additional.append(objective)

        return additional

    def _build_dependency_graph(
        self, objectives: list[LearningObjective]
    ) -> dict[str, list[str]]:
        """Bağımlılık grafiğini oluştur"""
        graph = defaultdict(list)

        # Her hedef için önkoşulları grafiğe ekle
        for objective in objectives:
            for prereq in objective.prerequisites:
                # Önkoşul hedefini bul
                prereq_obj = next(
                    (obj for obj in objectives if obj.title == prereq), None
                )
                if prereq_obj:
                    graph[prereq_obj.objective_id].append(objective.objective_id)

        return dict(graph)

    def _create_milestones(
        self, objectives: list[LearningObjective], subject: str
    ) -> list[Milestone]:
        """Kilometre taşlarını oluştur"""
        milestones = []

        # Her 2-3 hedef için bir milestone oluştur
        for i in range(0, len(objectives), 3):
            batch_objectives = objectives[i : i + 3]

            # Milestone türünü belirle
            avg_bloom_level = sum(obj.bloom_level for obj in batch_objectives) / len(
                batch_objectives
            )

            if avg_bloom_level <= 2:
                milestone_type = MilestoneType.KNOWLEDGE_CHECK
                required_score = 0.7
            elif avg_bloom_level <= 4:
                milestone_type = MilestoneType.SKILL_ASSESSMENT
                required_score = 0.75
            else:
                milestone_type = MilestoneType.PROJECT_COMPLETION
                required_score = 0.8

            milestone = Milestone(
                milestone_id=f"{subject}_milestone_{i//3}",
                title=f"{subject.title()} - Kilometre Taşı {i//3 + 1}",
                description=f"{len(batch_objectives)} hedefin tamamlanması",
                milestone_type=milestone_type,
                objectives=[obj.objective_id for obj in batch_objectives],
                completion_criteria=[
                    f"{obj.title} hedefini tamamlar" for obj in batch_objectives
                ],
                estimated_time_minutes=sum(
                    obj.estimated_time_minutes for obj in batch_objectives
                )
                // 4,
                required_score=required_score,
                resources=[],
                position_in_path=i // 3,
                dependencies=[f"{subject}_milestone_{i//3 - 1}"] if i > 0 else [],
                rewards=[f"Seviye {i//3 + 1} tamamlandı", "Yeni içerikler açıldı"],
                metadata={"objective_count": len(batch_objectives)},
            )
            milestones.append(milestone)

        return milestones

    def _organize_into_phases(
        self,
        objectives: list[LearningObjective],
        milestones: list[Milestone],
        duration_weeks: int,
    ) -> list[LearningPhase]:
        """Hedefleri fazlara organize et"""
        phases = []

        # Fazları haftalara böl
        objectives_per_phase = max(len(objectives) // duration_weeks, 1)

        for week in range(duration_weeks):
            start_idx = week * objectives_per_phase
            end_idx = min(start_idx + objectives_per_phase, len(objectives))

            if start_idx >= len(objectives):
                break

            phase_objectives = objectives[start_idx:end_idx]
            phase_milestones = [
                m
                for m in milestones
                if any(
                    obj_id in [obj.objective_id for obj in phase_objectives]
                    for obj_id in m.objectives
                )
            ]

            # Zorluk ilerlemesini hesapla
            difficulty_progression = [obj.difficulty_level for obj in phase_objectives]
            difficulty_progression.sort()  # Kolay'dan zor'a

            phase = LearningPhase(
                phase_id=f"phase_{week + 1}",
                title=f"Hafta {week + 1}: {phase_objectives[0].title if phase_objectives else 'Genel'}",
                description=f"{len(phase_objectives)} hedef ve {len(phase_milestones)} kilometre taşı",
                objectives=phase_objectives,
                milestones=phase_milestones,
                estimated_duration_days=7,  # 1 hafta
                difficulty_progression=difficulty_progression,
                prerequisites=[f"phase_{week}"] if week > 0 else [],
                learning_activities=self._generate_learning_activities(
                    phase_objectives
                ),
                assessment_methods=self._generate_assessment_methods(phase_milestones),
                success_criteria=["Tüm hedefleri %75 başarı ile tamamlar"],
                metadata={
                    "week_number": week + 1,
                    "objective_count": len(phase_objectives),
                    "milestone_count": len(phase_milestones),
                },
            )
            phases.append(phase)

        return phases

    def _generate_learning_activities(
        self, objectives: list[LearningObjective]
    ) -> list[str]:
        """Öğrenme aktivitelerini oluştur"""
        activities = []

        for objective in objectives:
            if objective.objective_type == LearningObjectiveType.KNOWLEDGE:
                activities.extend(["Video izleme", "Okuma", "Not alma"])
            elif objective.objective_type == LearningObjectiveType.APPLICATION:
                activities.extend(["Alıştırma yapma", "Problem çözme", "Uygulama"])
            elif objective.objective_type == LearningObjectiveType.ANALYSIS:
                activities.extend(["Analiz yapma", "Karşılaştırma", "Değerlendirme"])
            else:
                activities.extend(["Araştırma", "Proje", "Sunum"])

        return list(set(activities))  # Tekrarları kaldır

    def _generate_assessment_methods(self, milestones: list[Milestone]) -> list[str]:
        """Değerlendirme yöntemlerini oluştur"""
        methods = []

        for milestone in milestones:
            if milestone.milestone_type == MilestoneType.KNOWLEDGE_CHECK:
                methods.append("Çoktan seçmeli test")
            elif milestone.milestone_type == MilestoneType.SKILL_ASSESSMENT:
                methods.append("Performans değerlendirmesi")
            elif milestone.milestone_type == MilestoneType.PROJECT_COMPLETION:
                methods.append("Proje sunumu")
            else:
                methods.append("Kapsamlı değerlendirme")

        return methods

    def _calculate_difficulty_curve(self, phases: list[LearningPhase]) -> list[float]:
        """Zorluk eğrisini hesapla"""
        curve = []

        for phase in phases:
            if phase.difficulty_progression:
                avg_difficulty = sum(phase.difficulty_progression) / len(
                    phase.difficulty_progression
                )
                curve.append(avg_difficulty)
            else:
                curve.append(0.5)  # Default orta zorluk

        return curve

    def create_milestone_checkpoints(
        self, structured_path: StructuredPath
    ) -> list[dict[str, Any]]:
        """Kilometre taşı kontrol noktaları oluştur"""
        checkpoints = []

        for phase in structured_path.phases:
            for milestone in phase.milestones:
                checkpoint = {
                    "checkpoint_id": f"checkpoint_{milestone.milestone_id}",
                    "milestone_id": milestone.milestone_id,
                    "title": milestone.title,
                    "description": milestone.description,
                    "position": milestone.position_in_path,
                    "requirements": {
                        "objectives_completed": milestone.objectives,
                        "minimum_score": milestone.required_score,
                        "time_limit_minutes": milestone.estimated_time_minutes,
                    },
                    "rewards": milestone.rewards,
                    "next_unlock": self._get_next_unlocked_content(
                        milestone, structured_path
                    ),
                    "assessment_type": milestone.milestone_type.value,
                    "created_at": datetime.now().isoformat(),
                }
                checkpoints.append(checkpoint)

        return checkpoints

    def _get_next_unlocked_content(
        self, milestone: Milestone, structured_path: StructuredPath
    ) -> list[str]:
        """Sonraki açılacak içerikleri belirle"""
        next_content = []

        # Sonraki fazı bul
        current_phase_idx = None
        for i, phase in enumerate(structured_path.phases):
            if milestone in phase.milestones:
                current_phase_idx = i
                break

        if current_phase_idx is not None and current_phase_idx + 1 < len(
            structured_path.phases
        ):
            next_phase = structured_path.phases[current_phase_idx + 1]
            next_content.extend(
                [obj.title for obj in next_phase.objectives[:2]]
            )  # İlk 2 hedef

        return next_content

    def generate_time_based_schedule(
        self,
        structured_path: StructuredPath,
        start_date: datetime,
        daily_study_minutes: int = 60,
        study_days_per_week: int = 5,
    ) -> list[ScheduleItem]:
        """Zaman tabanlı program oluştur"""
        schedule = []
        current_date = start_date

        for phase in structured_path.phases:
            # Faz için toplam süre
            total_phase_time = sum(
                obj.estimated_time_minutes for obj in phase.objectives
            )

            # Günlük çalışma süresine göre gün sayısını hesapla
            days_needed = max(1, total_phase_time // daily_study_minutes)

            # Haftalık çalışma günlerine göre ayarla
            weeks_needed = max(1, days_needed // study_days_per_week)

            for objective in phase.objectives:
                # Her hedef için zamanlama
                schedule_item = ScheduleItem(
                    item_id=f"schedule_{objective.objective_id}",
                    item_type="objective",
                    title=objective.title,
                    scheduled_date=current_date,
                    estimated_duration_minutes=objective.estimated_time_minutes,
                    priority=objective.bloom_level,  # Bloom seviyesi = öncelik
                    dependencies=objective.prerequisites,
                    flexible=True,
                    metadata={
                        "phase_id": phase.phase_id,
                        "difficulty": objective.difficulty_level,
                        "type": objective.objective_type.value,
                    },
                )
                schedule.append(schedule_item)

                # Sonraki çalışma gününe geç
                current_date = self._get_next_study_date(
                    current_date, study_days_per_week
                )

            # Milestone'lar için zamanlama
            for milestone in phase.milestones:
                schedule_item = ScheduleItem(
                    item_id=f"schedule_{milestone.milestone_id}",
                    item_type="milestone",
                    title=milestone.title,
                    scheduled_date=current_date,
                    estimated_duration_minutes=milestone.estimated_time_minutes,
                    priority=5,  # Milestone'lar yüksek öncelik
                    dependencies=milestone.dependencies,
                    flexible=False,  # Milestone'lar esnek değil
                    metadata={
                        "phase_id": phase.phase_id,
                        "type": milestone.milestone_type.value,
                        "required_score": milestone.required_score,
                    },
                )
                schedule.append(schedule_item)

                current_date = self._get_next_study_date(
                    current_date, study_days_per_week
                )

        return schedule

    def _get_next_study_date(
        self, current_date: datetime, study_days_per_week: int
    ) -> datetime:
        """Sonraki çalışma tarihini hesapla"""
        # Hafta içi çalışma varsayımı (Pazartesi-Cuma)
        next_date = current_date + timedelta(days=1)

        # Hafta sonu kontrolü
        while next_date.weekday() >= study_days_per_week:  # 5 = Cumartesi, 6 = Pazar
            next_date += timedelta(days=1)

        return next_date

    def optimize_learning_sequence(
        self, structured_path: StructuredPath, student_performance: dict[str, float]
    ) -> StructuredPath:
        """Öğrenme sırasını optimize et"""
        try:
            # Performans verilerine göre zorluk ayarlaması
            avg_performance = (
                sum(student_performance.values()) / len(student_performance)
                if student_performance
                else 0.5
            )

            # Düşük performans = daha kolay içerik öncelikle
            if avg_performance < 0.6:
                # Fazları zorluk seviyesine göre yeniden sırala
                for phase in structured_path.phases:
                    phase.objectives.sort(key=lambda obj: obj.difficulty_level)

            # Yüksek performans = daha zor içerik ekle
            elif avg_performance > 0.8:
                # Ek zorlayıcı hedefler ekle
                for phase in structured_path.phases:
                    if len(phase.objectives) < 5:  # Maksimum 5 hedef per faz
                        challenge_objective = self._create_challenge_objective(phase)
                        phase.objectives.append(challenge_objective)

            # Metadata güncelle
            structured_path.adaptive_parameters[
                "last_optimization"
            ] = datetime.now().isoformat()
            structured_path.adaptive_parameters[
                "optimization_reason"
            ] = f"Performance: {avg_performance:.2f}"
            structured_path.last_updated = datetime.now()

            return structured_path

        except Exception as e:
            logger.error(f"Error optimizing learning sequence: {e!s}")
            return structured_path

    def _create_challenge_objective(self, phase: LearningPhase) -> LearningObjective:
        """Zorlayıcı hedef oluştur"""
        return LearningObjective(
            objective_id=f"{phase.phase_id}_challenge",
            title=f"{phase.title} - Zorlayıcı Hedef",
            description="Performansınız yüksek olduğu için ek zorlayıcı hedef",
            objective_type=LearningObjectiveType.EVALUATION,
            bloom_level=6,
            measurable_outcomes=[
                "Karmaşık problemleri çözer",
                "Yaratıcı çözümler üretir",
            ],
            assessment_criteria=["Orijinal çözüm yaklaşımı sergiler"],
            estimated_time_minutes=90,
            difficulty_level=0.9,
            prerequisites=[obj.objective_id for obj in phase.objectives],
            tags=["challenge", "advanced"],
            metadata={"auto_generated": True, "challenge_level": "high"},
        )

    def track_learning_objectives(
        self,
        structured_path: StructuredPath,
        completed_objectives: list[str],
        objective_scores: dict[str, float],
    ) -> dict[str, Any]:
        """Öğrenme hedeflerini takip et"""
        try:
            tracking_data = {
                "path_id": structured_path.path_id,
                "total_objectives": structured_path.total_objectives,
                "completed_count": len(completed_objectives),
                "completion_percentage": len(completed_objectives)
                / structured_path.total_objectives
                * 100,
                "average_score": sum(objective_scores.values()) / len(objective_scores)
                if objective_scores
                else 0,
                "phase_progress": {},
                "milestone_status": {},
                "next_recommendations": [],
                "performance_analysis": {},
            }

            # Faz bazlı ilerleme
            for phase in structured_path.phases:
                phase_objectives = [obj.objective_id for obj in phase.objectives]
                completed_in_phase = [
                    obj_id
                    for obj_id in completed_objectives
                    if obj_id in phase_objectives
                ]

                tracking_data["phase_progress"][phase.phase_id] = {
                    "total": len(phase_objectives),
                    "completed": len(completed_in_phase),
                    "percentage": len(completed_in_phase) / len(phase_objectives) * 100
                    if phase_objectives
                    else 0,
                    "current": len(completed_in_phase) < len(phase_objectives),
                }

            # Milestone durumu
            for phase in structured_path.phases:
                for milestone in phase.milestones:
                    milestone_objectives = milestone.objectives
                    completed_milestone_objs = [
                        obj_id
                        for obj_id in completed_objectives
                        if obj_id in milestone_objectives
                    ]

                    is_completed = len(completed_milestone_objs) == len(
                        milestone_objectives
                    )
                    avg_score = (
                        sum(
                            objective_scores.get(obj_id, 0)
                            for obj_id in milestone_objectives
                        )
                        / len(milestone_objectives)
                        if milestone_objectives
                        else 0
                    )

                    tracking_data["milestone_status"][milestone.milestone_id] = {
                        "completed": is_completed,
                        "score": avg_score,
                        "passed": avg_score >= milestone.required_score,
                        "objectives_completed": len(completed_milestone_objs),
                        "objectives_total": len(milestone_objectives),
                    }

            # Sonraki öneriler
            tracking_data["next_recommendations"] = self._generate_next_recommendations(
                structured_path, completed_objectives, objective_scores
            )

            # Performans analizi
            tracking_data["performance_analysis"] = self._analyze_performance(
                structured_path, objective_scores
            )

            return tracking_data

        except Exception as e:
            logger.error(f"Error tracking learning objectives: {e!s}")
            return {"error": str(e)}

    def _generate_next_recommendations(
        self,
        structured_path: StructuredPath,
        completed_objectives: list[str],
        objective_scores: dict[str, float],
    ) -> list[str]:
        """Sonraki önerileri oluştur"""
        recommendations = []

        # Tamamlanmamış hedefleri bul
        all_objective_ids = []
        for phase in structured_path.phases:
            all_objective_ids.extend([obj.objective_id for obj in phase.objectives])

        remaining_objectives = [
            obj_id for obj_id in all_objective_ids if obj_id not in completed_objectives
        ]

        if remaining_objectives:
            # İlk tamamlanmamış hedefi öner
            next_obj_id = remaining_objectives[0]
            next_obj = None

            for phase in structured_path.phases:
                for obj in phase.objectives:
                    if obj.objective_id == next_obj_id:
                        next_obj = obj
                        break
                if next_obj:
                    break

            if next_obj:
                recommendations.append(f"Sonraki hedef: {next_obj.title}")
                recommendations.append(
                    f"Tahmini süre: {next_obj.estimated_time_minutes} dakika"
                )

                if next_obj.prerequisites:
                    missing_prereqs = [
                        prereq
                        for prereq in next_obj.prerequisites
                        if prereq not in completed_objectives
                    ]
                    if missing_prereqs:
                        recommendations.append(
                            f"Önce şu hedefleri tamamlayın: {', '.join(missing_prereqs)}"
                        )

        # Düşük skorlu hedefleri tekrar et
        low_score_objectives = [
            obj_id for obj_id, score in objective_scores.items() if score < 0.7
        ]
        if low_score_objectives:
            recommendations.append(
                f"Tekrar edilmesi önerilen hedefler: {len(low_score_objectives)} adet"
            )

        return recommendations

    def _analyze_performance(
        self, structured_path: StructuredPath, objective_scores: dict[str, float]
    ) -> dict[str, Any]:
        """Performans analizi"""
        if not objective_scores:
            return {"message": "Henüz performans verisi yok"}

        scores = list(objective_scores.values())

        return {
            "average_score": sum(scores) / len(scores),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "consistency": 1.0 - (max(scores) - min(scores)),  # Tutarlılık
            "trend": "improving"
            if len(scores) > 1 and scores[-1] > scores[0]
            else "stable",
            "strong_areas": [
                obj_id for obj_id, score in objective_scores.items() if score > 0.8
            ],
            "improvement_areas": [
                obj_id for obj_id, score in objective_scores.items() if score < 0.6
            ],
        }


# Singleton instance
structured_path_generator = StructuredLearningPathGenerator()
