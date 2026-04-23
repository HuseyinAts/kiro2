"""
Formatters Module
Teknofest 2025 - Eğitim Eylemci Projesi

Output formatting utilities for learning path agent
"""

from datetime import datetime, timedelta
from typing import Any

from ..models import (
    KnowledgeLevel,
    LearningPath,
    LearningPhase,
    LearningResource,
    LearningStyle,
    StudentProfile,
)


class StudentProfileFormatter:
    """Format student profile data for display"""

    @staticmethod
    def format_profile(profile: StudentProfile) -> dict[str, Any]:
        """
        Format student profile for API response

        Args:
            profile: StudentProfile object

        Returns:
            Formatted dictionary with Turkish labels
        """
        return {
            "student_id": profile.student_id,
            "name": profile.name,
            "grade": profile.grade,
            "exam_target": profile.exam_target,
            "learning_goal": profile.learning_goal,
            "profile_summary": {
                "learning_style": {
                    "value": profile.learning_style.value,
                    "label": StudentProfileFormatter._translate_learning_style(
                        profile.learning_style
                    ),
                },
                "knowledge_level": {
                    "value": profile.knowledge_level.value,
                    "label": StudentProfileFormatter._translate_knowledge_level(
                        profile.knowledge_level
                    ),
                },
                "interests": profile.interests,
                "available_time": {
                    "hours_per_week": profile.available_time,
                    "label": f"{profile.available_time} saat/hafta",
                },
            },
            "metadata": profile.metadata,
        }

    @staticmethod
    def _translate_learning_style(style: LearningStyle) -> str:
        """Translate learning style to Turkish"""
        translations = {
            LearningStyle.VISUAL: "Görsel Öğrenen",
            LearningStyle.AUDITORY: "İşitsel Öğrenen",
            LearningStyle.READING: "Okuyarak Öğrenen",
            LearningStyle.KINESTHETIC: "Yaparak Öğrenen",
            LearningStyle.MIXED: "Karma Öğrenen",
        }
        return translations.get(style, style.value)

    @staticmethod
    def _translate_knowledge_level(level: KnowledgeLevel) -> str:
        """Translate knowledge level to Turkish"""
        translations = {
            KnowledgeLevel.BEGINNER: "Başlangıç",
            KnowledgeLevel.ELEMENTARY: "Temel",
            KnowledgeLevel.INTERMEDIATE: "Orta",
            KnowledgeLevel.ADVANCED: "İleri",
            KnowledgeLevel.EXPERT: "Uzman",
        }
        return translations.get(level, level.value)

    @staticmethod
    def format_profile_summary(profile: StudentProfile) -> str:
        """
        Create human-readable profile summary

        Args:
            profile: StudentProfile object

        Returns:
            Turkish summary string
        """
        style_label = StudentProfileFormatter._translate_learning_style(
            profile.learning_style
        )
        level_label = StudentProfileFormatter._translate_knowledge_level(
            profile.knowledge_level
        )

        summary = f"""
{profile.name} - {profile.grade}. Sınıf

📚 Hedef: {profile.exam_target}
🎯 Öğrenme Hedefi: {profile.learning_goal}
🧠 Öğrenme Stili: {style_label}
📊 Seviye: {level_label}
⏰ Haftalık Süre: {profile.available_time} saat
        """.strip()

        if profile.interests:
            summary += f"\n💡 İlgi Alanları: {', '.join(profile.interests)}"

        return summary


class ResourceFormatter:
    """Format learning resource data for display"""

    @staticmethod
    def format_resource(resource: LearningResource) -> dict[str, Any]:
        """
        Format learning resource for API response

        Args:
            resource: LearningResource object

        Returns:
            Formatted dictionary
        """
        # Extract learning style tags from metadata if available
        learning_style_tags = []
        if resource.metadata and "learning_styles" in resource.metadata:
            learning_style_tags = resource.metadata["learning_styles"]

        return {
            "resource_id": resource.resource_id,
            "title": resource.title,
            "type": resource.resource_type,
            "platform": ResourceFormatter._translate_platform(resource.source),
            "url": resource.url,
            "duration": {
                "minutes": resource.estimated_time,
                "label": ResourceFormatter._format_duration(resource.estimated_time),
            },
            "difficulty": {
                "value": resource.difficulty_level.value,
                "label": StudentProfileFormatter._translate_knowledge_level(
                    resource.difficulty_level
                ),
            },
            "subjects": resource.tags,
            "learning_style_tags": [
                ResourceFormatter._translate_style_tag(tag)
                for tag in learning_style_tags
            ],
            "quality_score": resource.rating,
            "metadata": resource.metadata,
        }

    @staticmethod
    def format_resource_list(resources: list[LearningResource]) -> list[dict[str, Any]]:
        """Format list of resources"""
        return [ResourceFormatter.format_resource(r) for r in resources]

    @staticmethod
    def _translate_platform(platform: str) -> str:
        """Translate platform name to Turkish"""
        translations = {
            "youtube": "YouTube",
            "khan_academy": "Khan Academy",
            "oer": "Açık Eğitim Kaynakları",
            "custom": "Özel Kaynak",
        }
        return translations.get(platform, platform)

    @staticmethod
    def _translate_style_tag(tag: str) -> str:
        """Translate learning style tag"""
        translations = {
            "visual": "görsel",
            "auditory": "işitsel",
            "reading": "okuma",
            "kinesthetic": "yaparak",
        }
        return translations.get(tag, tag)

    @staticmethod
    def _format_duration(minutes: int) -> str:
        """Format duration in human-readable Turkish"""
        if minutes < 60:
            return f"{minutes} dakika"
        if minutes < 120:
            return "~1 saat"
        hours = minutes // 60
        return f"~{hours} saat"


class PathFormatter:
    """Format learning path data for display"""

    @staticmethod
    def format_path(path: LearningPath) -> dict[str, Any]:
        """
        Format learning path for API response

        Args:
            path: LearningPath object

        Returns:
            Formatted dictionary
        """
        total_duration = sum(r.estimated_time for r in path.resources)

        return {
            "path_id": path.path_id,
            "student_id": path.student_id,
            "goal": path.goal,
            "created_at": path.created_at.isoformat(),
            "summary": {
                "total_resources": len(path.resources),
                "total_phases": len(path.phases),
                "estimated_duration": {
                    "minutes": total_duration,
                    "label": ResourceFormatter._format_duration(total_duration),
                },
            },
            "phases": [PathFormatter.format_phase(phase) for phase in path.phases],
            "resources": ResourceFormatter.format_resource_list(path.resources),
            "reasoning": path.reasoning,
            "metadata": path.metadata,
        }

    @staticmethod
    def format_phase(phase: LearningPhase) -> dict[str, Any]:
        """Format learning phase"""
        phase_duration = sum(r.estimated_time for r in phase.resources)

        return {
            "phase_id": phase.phase_id,
            "name": phase.name,
            "description": phase.description,
            "order": phase.order,
            "resources": [r.resource_id for r in phase.resources],
            "duration": {
                "minutes": phase_duration,
                "label": ResourceFormatter._format_duration(phase_duration),
            },
            "learning_objectives": phase.learning_objectives,
        }

    @staticmethod
    def format_path_summary(path: LearningPath) -> str:
        """
        Create human-readable path summary

        Args:
            path: LearningPath object

        Returns:
            Turkish summary string
        """
        total_duration = sum(r.estimated_time for r in path.resources)
        duration_label = ResourceFormatter._format_duration(total_duration)

        summary = f"""
📚 Öğrenme Yolu: {path.goal}

📊 İstatistikler:
- Toplam Kaynak: {len(path.resources)}
- Aşama Sayısı: {len(path.phases)}
- Tahmini Süre: {duration_label}

🎯 Aşamalar:
        """.strip()

        for i, phase in enumerate(path.phases, 1):
            phase_duration = sum(r.estimated_time for r in phase.resources)
            summary += f"\n{i}. {phase.name} ({len(phase.resources)} kaynak, {ResourceFormatter._format_duration(phase_duration)})"

        return summary


class AssessmentFormatter:
    """Format assessment data for display"""

    @staticmethod
    def format_assessment(assessment: dict[str, Any]) -> dict[str, Any]:
        """Format assessment for API response"""
        return {
            "assessment_id": assessment.get("assessment_id", ""),
            "type": AssessmentFormatter._translate_assessment_type(
                assessment.get("type", "quick")
            ),
            "subject": assessment.get("subject", ""),
            "topic": assessment.get("topic"),
            "question_count": len(assessment.get("questions", [])),
            "questions": assessment.get("questions", []),
            "metadata": assessment.get("metadata", {}),
        }

    @staticmethod
    def _translate_assessment_type(type_val: str) -> str:
        """Translate assessment type"""
        translations = {
            "diagnostic": "Tanılama Testi",
            "quick": "Hızlı Test",
            "comprehensive": "Kapsamlı Test",
            "practice": "Pratik Testi",
        }
        return translations.get(type_val, type_val)

    @staticmethod
    def format_assessment_results(results: dict[str, Any]) -> dict[str, Any]:
        """Format assessment results for API response"""
        # Calculate statistics
        scores = results.get("scores", [])
        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            "student_id": results.get("student_id", ""),
            "assessment_id": results.get("assessment_id", ""),
            "statistics": {
                "total_questions": len(scores),
                "average_score": round(avg_score, 2),
                "label": AssessmentFormatter._get_performance_label(avg_score),
            },
            "topic_scores": results.get("topic_scores", {}),
            "weak_areas": AssessmentFormatter._identify_weak_areas(
                results.get("topic_scores", {})
            ),
            "recommendations": results.get("recommendations", []),
        }

    @staticmethod
    def _get_performance_label(score: float) -> str:
        """Get performance label based on score"""
        if score >= 85:
            return "Çok İyi"
        if score >= 70:
            return "İyi"
        if score >= 60:
            return "Orta"
        if score >= 50:
            return "Geliştirilmeli"
        return "Desteklenmeli"

    @staticmethod
    def _identify_weak_areas(topic_scores: dict[str, float]) -> list[str]:
        """Identify weak areas from topic scores"""
        return [topic for topic, score in topic_scores.items() if score < 60]


class ProgressFormatter:
    """Format progress data for display"""

    @staticmethod
    def format_progress(progress_data: dict[str, Any]) -> dict[str, Any]:
        """Format progress data for API response"""
        progress_percent = progress_data.get("progress_percent", 0)

        return {
            "student_id": progress_data.get("student_id", ""),
            "path_id": progress_data.get("path_id", ""),
            "progress": {
                "percent": round(progress_percent, 1),
                "completed": progress_data.get("completed_resources", 0),
                "total": progress_data.get("total_resources", 0),
                "label": ProgressFormatter._get_progress_label(progress_percent),
            },
            "recent_completions": progress_data.get("recent_completions", []),
            "next_recommendations": progress_data.get("next_recommendations", []),
            "estimated_completion": ProgressFormatter._estimate_completion_date(
                progress_data
            ),
        }

    @staticmethod
    def _get_progress_label(percent: float) -> str:
        """Get progress label"""
        if percent >= 100:
            return "Tamamlandı! 🎉"
        if percent >= 75:
            return "Neredeyse Bitti"
        if percent >= 50:
            return "Yarı Yolda"
        if percent >= 25:
            return "İyi Gidiyor"
        return "Yeni Başladı"

    @staticmethod
    def _estimate_completion_date(progress_data: dict[str, Any]) -> str | None:
        """Estimate completion date based on current progress"""
        # Simple estimation based on average pace
        completed = progress_data.get("completed_resources", 0)
        total = progress_data.get("total_resources", 0)

        if completed == 0 or total == 0:
            return None

        # Assume completion time from metadata if available
        days_spent = progress_data.get("metadata", {}).get("days_since_start", 7)
        resources_per_day = completed / days_spent if days_spent > 0 else 1

        remaining = total - completed
        estimated_days = (
            remaining / resources_per_day if resources_per_day > 0 else remaining
        )

        completion_date = datetime.now() + timedelta(days=estimated_days)
        return completion_date.strftime("%Y-%m-%d")


class ChatFormatter:
    """Format chat/conversation data for display"""

    @staticmethod
    def format_chat_response(response: dict[str, Any]) -> dict[str, Any]:
        """Format chat response for API"""
        return {
            "session_id": response.get("session_id", ""),
            "message": response.get("response", ""),
            "timestamp": datetime.now().isoformat(),
            "context": response.get("context", {}),
            "suggestions": response.get("suggestions", []),
        }

    @staticmethod
    def format_conversation_history(
        history: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Format conversation history"""
        return [
            {
                "role": msg.get("role", "user"),
                "message": msg.get("message", ""),
                "timestamp": msg.get("timestamp", datetime.now().isoformat()),
            }
            for msg in history
        ]


class ErrorFormatter:
    """Format error messages for API responses"""

    @staticmethod
    def format_error(
        error: Exception, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Format error for API response

        Args:
            error: Exception object
            context: Optional context information

        Returns:
            Formatted error dictionary
        """
        return {
            "success": False,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "timestamp": datetime.now().isoformat(),
            },
            "context": context or {},
        }

    @staticmethod
    def format_validation_error(field: str, message: str) -> dict[str, Any]:
        """Format validation error"""
        return {
            "success": False,
            "error": {
                "type": "ValidationError",
                "field": field,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            },
        }


def format_success_response(data: Any, message: str | None = None) -> dict[str, Any]:
    """
    Generic success response formatter

    Args:
        data: Response data
        message: Optional success message

    Returns:
        Formatted success response
    """
    response = {"success": True, "data": data, "timestamp": datetime.now().isoformat()}

    if message:
        response["message"] = message

    return response
