"""
Enhanced Study Buddy Agent with All Improvements
Integrates context management, dynamic content, analytics, and plugin architecture
"""

import json
import logging
import os

# Import new core modules
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analytics_monitoring import EventType, MetricType, get_analytics_manager
from core.context_manager import ConversationTurn, StudentProfile, get_context_manager
from core.dynamic_content_generator import (
    ContentType,
    DifficultyLevel,
    get_content_generator,
)
from core.llm_service import llm_service
from core.plugin_architecture import AgentCapability, AgentManifest, BaseAgentPlugin

logger = logging.getLogger(__name__)


class EnhancedStudyBuddyAgent(BaseAgentPlugin):
    """Enhanced Study Buddy Agent with full feature integration"""

    def __init__(self):
        # Create manifest
        manifest = AgentManifest(
            name="EnhancedStudyBuddy",
            version="2.0.0",
            description="Advanced AI-powered study companion with personalization",
            author="Teknofest Team",
            capabilities=[
                AgentCapability.TEACHING,
                AgentCapability.ASSESSMENT,
                AgentCapability.TUTORING,
                AgentCapability.CONTENT_GENERATION,
                AgentCapability.PROBLEM_SOLVING,
            ],
            supported_languages=["tr", "en"],
            supported_subjects=["matematik", "fen", "türkçe", "sosyal", "ingilizce"],
            configuration={
                "max_session_duration": 120,  # minutes
                "adaptive_difficulty": True,
                "personalization": True,
                "analytics_enabled": True,
            },
        )

        super().__init__(manifest)

        # Core services (will be initialized)
        self.context_manager = None
        self.content_generator = None
        self.analytics = None

        # Agent-specific data
        self.active_sessions = {}
        self.performance_cache = {}

    async def initialize(self, context_manager, content_generator, analytics):
        """Initialize with core services"""
        await super().initialize(context_manager, content_generator, analytics)

        # Get singleton instances if not provided
        self.context_manager = context_manager or await get_context_manager()
        self.content_generator = content_generator or get_content_generator()
        self.analytics = analytics or get_analytics_manager()

        logger.info(
            f"Enhanced Study Buddy Agent initialized - Version {self.manifest.version}"
        )

    async def process_message(
        self, message: str, session_id: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process message with full context and personalization"""

        start_time = time.time()

        try:
            # 1. Get or create session
            session = await self._get_or_create_session(session_id, context)

            # 2. Get student profile
            student_profile = await self.context_manager.get_or_create_student_profile(
                session.student_id, **context if context else {}
            )

            # 3. Analyze message intent
            intent, entities = await self._analyze_intent(message, session)

            # 4. Generate personalized response
            response = await self._generate_personalized_response(
                message, intent, entities, session, student_profile
            )

            # 5. Update context with conversation turn
            turn = ConversationTurn(
                turn_id=f"turn_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                agent_name=self.manifest.name,
                user_message=message,
                agent_response=response,
                intent=intent,
                entities=entities,
                confidence=0.95,
                processing_time=(time.time() - start_time) * 1000,
            )

            await self.context_manager.update_session(
                session_id,
                turn=turn,
                variables={"last_intent": intent, "last_topic": entities.get("topic")},
            )

            # 6. Track analytics
            self._track_interaction(
                session.student_id,
                message,
                response,
                intent,
                (time.time() - start_time) * 1000,
            )

            # 7. Update progress if learning occurred
            if intent in ["learn", "practice", "quiz"]:
                await self._update_learning_progress(
                    session.student_id,
                    entities.get("topic"),
                    entities.get("success", True),
                )

            return response

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.analytics.error_tracker.record_error(
                "message_processing",
                str(e),
                {"session_id": session_id, "message": message[:100]},
            )
            return await self.handle_error(e)

    async def _get_or_create_session(
        self, session_id: str, context: Optional[Dict[str, Any]]
    ):
        """Get existing or create new session"""
        session = await self.context_manager.get_session(session_id)

        if not session:
            # Create new session
            student_id = (
                context.get("student_id") if context else f"student_{session_id[:8]}"
            )
            session = await self.context_manager.create_session(
                student_id, initial_context=context
            )

        return session

    async def _analyze_intent(
        self, message: str, session
    ) -> Tuple[str, Dict[str, Any]]:
        """Analyze message intent and extract entities"""

        # Get recent context
        recent_turns = session.get_context_window(3)
        context_summary = "\\n".join(
            [f"User: {turn.user_message[:50]}" for turn in recent_turns]
        )

        # Use LLM for intent analysis
        prompt = f"""
        Analyze the student's message and determine intent.
        
        Recent context:
        {context_summary}
        
        Current message: {message}
        
        Possible intents:
        - learn: Student wants to learn a new topic
        - practice: Student wants to practice exercises
        - quiz: Student wants to take a quiz
        - help: Student needs help or clarification
        - feedback: Student is providing feedback
        - social: Social conversation
        
        Extract entities:
        - topic: Subject or topic mentioned
        - difficulty: Easy, medium, hard
        - question_type: Type of question if applicable
        
        Return JSON:
        {{
            "intent": "intent_name",
            "entities": {{
                "topic": "topic_name",
                "difficulty": "level"
            }},
            "confidence": 0.95
        }}
        """

        try:
            result = await llm_service.generate(prompt=prompt, temperature=0.3)

            if result.get("success"):
                data = json.loads(result.get("text", "{}"))
                return data.get("intent", "help"), data.get("entities", {})
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.debug(f"Intent analysis failed, using fallback: {e}")
            pass

        # Fallback to simple keyword matching
        message_lower = message.lower()

        if any(word in message_lower for word in ["öğren", "anlat", "açıkla"]):
            intent = "learn"
        elif any(word in message_lower for word in ["alıştırma", "pratik", "çöz"]):
            intent = "practice"
        elif any(word in message_lower for word in ["sınav", "quiz", "test"]):
            intent = "quiz"
        elif any(word in message_lower for word in ["yardım", "anlamadım", "nasıl"]):
            intent = "help"
        else:
            intent = "social"

        # Extract topic
        topics = ["matematik", "fen", "türkçe", "sosyal", "ingilizce"]
        topic = None
        for t in topics:
            if t in message_lower:
                topic = t
                break

        return intent, {"topic": topic}

    async def _generate_personalized_response(
        self,
        message: str,
        intent: str,
        entities: Dict[str, Any],
        session,
        student_profile: StudentProfile,
    ) -> str:
        """Generate personalized response based on intent and profile"""

        # Get appropriate content type based on intent
        content_type_map = {
            "learn": ContentType.EXPLANATION,
            "practice": ContentType.PRACTICE,
            "quiz": ContentType.QUIZ,
            "help": ContentType.EXPLANATION,
            "feedback": ContentType.SUMMARY,
            "social": ContentType.EXPLANATION,
        }

        content_type = content_type_map.get(intent, ContentType.EXPLANATION)

        # Generate personalized content
        topic = entities.get("topic", "genel")

        profile_dict = {
            "student_id": student_profile.student_id,
            "learning_style": student_profile.learning_style,
            "difficulty_level": student_profile.difficulty_level,
            "subjects_of_interest": student_profile.subjects_of_interest,
        }

        content = await self.content_generator.generate_content(
            topic=topic,
            content_type=content_type,
            student_profile=profile_dict,
            context={
                "intent": intent,
                "message": message,
                "session_context": session.get_summary(),
            },
        )

        # Add interactive elements based on learning style
        response = content.body

        if student_profile.learning_style == "visual":
            response += "\\n\\n[CHART] Görsel öğrenme materyalleri eklendi."
        elif student_profile.learning_style == "kinesthetic":
            response += "\\n\\n[TARGET] Pratik aktiviteler eklendi."

        # Add progress tracking message
        progress = self.context_manager.progress_tracker.get_progress_report(
            student_profile.student_id
        )

        if progress and progress.get("statistics"):
            stats = progress["statistics"]
            if stats.get("current_streak", 0) > 0:
                response += (
                    f"\\n\\n[FIRE] Mevcut seri: {stats['current_streak']} doğru cevap!"
                )

        return response

    def _track_interaction(
        self,
        student_id: str,
        message: str,
        response: str,
        intent: str,
        processing_time_ms: float,
    ):
        """Track interaction for analytics"""

        # Record event
        self.analytics.metrics_collector.record_event(
            EventType.AGENT_INTERACTION,
            f"{self.manifest.name}_interaction",
            duration_ms=processing_time_ms,
            success=True,
            user_id=student_id,
            agent_name=self.manifest.name,
            metadata={
                "intent": intent,
                "message_length": len(message),
                "response_length": len(response),
            },
        )

        # Record metrics
        self.analytics.metrics_collector.record_metric(
            "agent_response_time",
            MetricType.HISTOGRAM,
            processing_time_ms,
            labels={"agent": self.manifest.name, "intent": intent},
        )

        # Track for learning analytics
        self.analytics.learning_analytics.record_interaction(
            student_id=student_id,
            agent_name=self.manifest.name,
            input_text=message,
            output_text=response,
            context={"intent": intent},
            response_time_ms=processing_time_ms,
        )

    async def _update_learning_progress(
        self, student_id: str, topic: Optional[str], success: bool
    ):
        """Update student learning progress"""

        # Update progress tracker
        self.context_manager.progress_tracker.update_progress(
            student_id, "question_answered", {"correct": success, "topic": topic}
        )

        if topic and success:
            # Mark topic as progressing
            self.context_manager.progress_tracker.update_progress(
                student_id, "topic_progress", topic
            )

        # Update student profile
        await self.context_manager.update_student_profile(
            student_id,
            {"last_active": datetime.now(), "total_study_time": 5},  # Add 5 minutes
        )

    async def get_capabilities(self) -> List[str]:
        """Return agent capabilities"""
        return [cap.value for cap in self.manifest.capabilities]

    async def create_adaptive_quiz(
        self, student_id: str, topic: str, session_id: str
    ) -> Dict[str, Any]:
        """Create adaptive quiz based on student performance"""

        # Get student profile
        profile = await self.context_manager.get_or_create_student_profile(student_id)

        # Get progress report
        progress = self.context_manager.progress_tracker.get_progress_report(student_id)

        # Determine appropriate difficulty
        accuracy = progress.get("statistics", {}).get("accuracy", 50)
        if accuracy < 40:
            difficulty = DifficultyLevel.BEGINNER
        elif accuracy < 60:
            difficulty = DifficultyLevel.ELEMENTARY
        elif accuracy < 80:
            difficulty = DifficultyLevel.INTERMEDIATE
        else:
            difficulty = DifficultyLevel.ADVANCED

        # Generate quiz content
        profile_dict = {
            "student_id": student_id,
            "learning_style": profile.learning_style,
            "difficulty_level": difficulty.name.lower(),
        }

        quiz_content = await self.content_generator.generate_content(
            topic=topic, content_type=ContentType.QUIZ, student_profile=profile_dict
        )

        # Create quiz structure
        quiz = {
            "quiz_id": f"quiz_{datetime.now().timestamp()}",
            "student_id": student_id,
            "topic": topic,
            "difficulty": difficulty.value,
            "questions": quiz_content.assessments,
            "adaptive": True,
            "created_at": datetime.now().isoformat(),
        }

        # Track quiz creation
        self.analytics.metrics_collector.record_event(
            EventType.CONTENT_GENERATION,
            "adaptive_quiz_created",
            user_id=student_id,
            metadata={"topic": topic, "difficulty": difficulty.value},
        )

        return quiz

    async def provide_real_time_feedback(
        self, student_id: str, question_id: str, answer: str
    ) -> Dict[str, Any]:
        """Provide real-time feedback on student answers"""

        start_time = time.time()

        # Generate feedback using LLM
        feedback_prompt = f"""
        Provide encouraging feedback for the student's answer.
        Question ID: {question_id}
        Student Answer: {answer}
        
        Include:
        1. Whether the answer is correct
        2. Explanation if wrong
        3. Encouragement
        4. Next steps
        
        Return in Turkish.
        """

        result = await llm_service.generate(prompt=feedback_prompt, temperature=0.7)

        feedback_text = result.get("text", "Good effort! Keep trying.")

        # Determine if correct (simplified)
        is_correct = (
            "doğru" in feedback_text.lower() or "correct" in feedback_text.lower()
        )

        # Update progress
        await self._update_learning_progress(
            student_id,
            question_id.split("_")[0] if "_" in question_id else None,
            is_correct,
        )

        # Track feedback generation
        processing_time = (time.time() - start_time) * 1000
        self.analytics.metrics_collector.record_metric(
            "feedback_generation_time", MetricType.HISTOGRAM, processing_time
        )

        return {
            "feedback": feedback_text,
            "is_correct": is_correct,
            "processing_time_ms": processing_time,
        }

    async def get_learning_insights(self, student_id: str) -> Dict[str, Any]:
        """Get personalized learning insights"""

        # Get progress report
        progress = self.context_manager.progress_tracker.get_progress_report(student_id)

        # Get student profile
        profile = await self.context_manager.get_or_create_student_profile(student_id)

        # Get recent session history
        history = await self.context_manager.get_student_history(student_id, limit=5)

        # Generate insights
        insights = {
            "student_id": student_id,
            "learning_style": profile.learning_style,
            "current_level": progress.get("gamification", {}).get("level", 1),
            "total_study_time": profile.total_study_time,
            "strengths": profile.strong_topics,
            "areas_for_improvement": profile.weak_topics,
            "recent_activity": [
                {
                    "session_id": session.session_id,
                    "date": session.created_at.isoformat(),
                    "duration": (
                        session.last_updated - session.created_at
                    ).total_seconds()
                    / 60,
                    "topic": session.current_topic,
                }
                for session in history
            ],
            "recommendations": progress.get("recommendations", []),
            "achievements": progress.get("gamification", {}).get("achievements", []),
        }

        return insights

    async def shutdown(self):
        """Clean up resources"""
        # Save any pending data
        if self.analytics:
            await self.analytics.shutdown()

        logger.info("Enhanced Study Buddy Agent shutdown complete")


# Create singleton instance
_enhanced_agent = None


async def get_enhanced_study_buddy() -> EnhancedStudyBuddyAgent:
    """Get or create enhanced study buddy agent"""
    global _enhanced_agent

    if _enhanced_agent is None:
        _enhanced_agent = EnhancedStudyBuddyAgent()

        # Initialize with core services
        context_manager = await get_context_manager()
        content_generator = get_content_generator()
        analytics = get_analytics_manager()

        await _enhanced_agent.initialize(context_manager, content_generator, analytics)

    return _enhanced_agent
