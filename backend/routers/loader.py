"""
Dynamic Router Loader

Router'ları dinamik olarak yükleyen ve kaydeden sistem.
Updated: 2026-01-10 - Dosya adları düzeltildi
"""

from fastapi import FastAPI
import logging
import importlib

from routers import router_registry

logger = logging.getLogger(__name__)

# Router mapping - gerçek dosya adlarıyla eşleştirildi
ROUTER_MAPPING = {
    # Health & Monitoring
    "api.health": ("health", "api.health"),

    # Telemetry (frontend web-vitals + error report stubs)
    "api.telemetry": ("health", "api.telemetry"),

    # Authentication & Security
    "api.auth": ("auth", "api.auth"),
    "api.enhanced_auth_api": ("auth", "api.enhanced_auth_api"),
    "api.two_factor_auth_api": ("auth", "api.two_factor_auth_api"),
    "api.kvkk_consent_api": ("security", "api.kvkk_consent_api"),
    "api.kvkk_privacy_api": ("security", "api.kvkk_privacy_api"),
    "api.rate_limit_api": ("security", "api.rate_limit_api"),
    "api.ddos_management_api": ("security", "api.ddos_management_api"),
    "api.audit_api": ("security", "api.audit_api"),
    "api.audit_logs_api": ("security", "api.audit_logs_api"),
    "api.encryption_management": ("security", "api.encryption_management"),
    "api.api_key_api": ("security", "api.api_key_api"),

    # Exam & Assessment
    "api.sinav": ("exam", "api.sinav"),
    "api.exam_performance": ("exam", "api.exam_performance"),
    "api.exam_answer_tracking": ("exam", "api.exam_answer_tracking"),

    # Learning & Education
    "api.learning_style": ("learning", "api.learning_style"),
    "api.learning_path_v2": ("learning", "api.learning_path_v2"),
    "api.zpd_maarif": ("learning", "api.zpd_maarif"),
    "api.irt_morfoloji": ("learning", "api.irt_morfoloji"),
    "api.fsrs": ("learning", "api.fsrs"),
    "api.curriculum_compliance": ("learning", "api.curriculum_compliance"),

    # Content & Questions
    "api.soru_bankasi": ("content", "api.soru_bankasi"),
    "api.question_crud_api": ("content", "api.question_crud_api"),
    # "api.questions_api": ("content", "api.questions_api"),  # REMOVED - deprecated/non-existent
    "api.content_management": ("content", "api.content_management"),
    "api.content_api": ("content", "api.content_api"),
    "api.osym_questions_api": ("content", "api.osym_questions_api"),
    "api.osym_routes": ("content", "api.osym_routes"),
    "api.osym_inspired_routes": ("content", "api.osym_inspired_routes"),
    "api.hybrid_question_generation": ("content", "api.hybrid_question_generation"),
    "api.question_bank_v2_routes": ("content", "api.question_bank_v2_routes"),
    "api.pdf_processing_api": ("content", "api.pdf_processing_api"),
    "api.batch_generation_api": ("content", "api.batch_generation_api"),
    "api.wave2b_quality_routes": ("content", "api.wave2b_quality_routes"),
    "api.difficulty_classification_api": ("content", "api.difficulty_classification_api"),

    # AI & NLP Services
    "api.v1.expert_agents_api": ("ai", "api.v1.expert_agents_api"),
    "api.agents": ("ai", "api.agents"),
    "api.multi_agent": ("ai", "api.multi_agent"),
    "api.ai_chat_routes": ("ai", "api.ai_chat_routes"),
    "api.rag": ("ai", "api.rag"),
    "api.turkish_nlp_chat": ("ai", "api.turkish_nlp_chat"),
    "api.berturk_api": ("ai", "api.berturk_api"),
    "api.zemberek": ("ai", "api.zemberek"),
    "api.turkish_nlp": ("ai", "api.turkish_nlp"),
    "api.cultural_adaptation_api": ("ai", "api.cultural_adaptation_api"),
    "api.sequential_reasoning_api": ("ai", "api.sequential_reasoning_api"),
    "api.litellm_chat": ("ai", "api.litellm_chat"),
    "api.enhanced_chat": ("ai", "api.enhanced_chat"),

    # Integrations
    "api.youtube_routes": ("integrations", "api.youtube_routes"),
    "api.khan_routes": ("integrations", "api.khan_routes"),
    "api.eba_routes": ("integrations", "api.eba_routes"),
    "api.ebatv": ("integrations", "api.ebatv"),
    "api.gamification_api": ("integrations", "api.gamification_api"),

    # Admin & Management
    "api.admin": ("admin", "api.admin"),
    "api.teacher_routes": ("admin", "api.teacher_routes"),
    "api.ogretmen": ("admin", "api.ogretmen"),
    "api.veli": ("admin", "api.veli"),
    "api.parent": ("admin", "api.parent"),
    "api.student_dashboard": ("admin", "api.student_dashboard"),
    "api.advanced_reports": ("admin", "api.advanced_reports"),
    "api.cache": ("admin", "api.cache"),
    "api.cache_metrics": ("admin", "api.cache_metrics"),
    "api.celery_tasks_api": ("admin", "api.celery_tasks_api"),
    "api.config_routes": ("admin", "api.config_routes"),
    "api.enhanced_user_management_api": ("admin", "api.enhanced_user_management_api"),

    # Quality Gates & DevOps
    "api.quality_gates_api": ("devops", "api.quality_gates_api"),

    # Analytics & Monitoring
    "api.analytics": ("analytics", "api.analytics"),
    "api.monitoring": ("analytics", "api.monitoring"),
    "api.production_monitoring": ("analytics", "api.production_monitoring"),
    "api.performance_monitoring": ("analytics", "api.performance_monitoring"),
    "api.performance": ("analytics", "api.performance"),
    "api.elasticsearch": ("analytics", "api.elasticsearch"),
    "api.tracing_example": ("analytics", "api.tracing_example"),
    "api.sentry_demo": ("analytics", "api.sentry_demo"),
    "api.video_analytics_routes": ("analytics", "api.video_analytics_routes"),

    # Accessibility
    "api.adhd_task_management_api": ("accessibility", "api.adhd_task_management_api"),
    "api.adhd_focus_mode_api": ("accessibility", "api.adhd_focus_mode_api"),
    "api.adhd_support_api": ("accessibility", "api.adhd_support_api"),
    "api.osb_settings_api": ("accessibility", "api.osb_settings_api"),
    "api.instant_feedback_api": ("accessibility", "api.instant_feedback_api"),
    "api.text_simplification": ("accessibility", "api.text_simplification"),
    "api.tts_api": ("accessibility", "api.tts_api"),
    "api.bionic_reading": ("accessibility", "api.bionic_reading"),
    "api.math_solution_steps": ("accessibility", "api.math_solution_steps"),
    "api.video_solution": ("accessibility", "api.video_solution"),
    "api.alternative_solutions_api": ("accessibility", "api.alternative_solutions_api"),
    "api.manipulatives_api": ("accessibility", "api.manipulatives_api"),
    "api.manipulatives_progress_api": ("accessibility", "api.manipulatives_progress_api"),
    "api.visual_supports_api": ("accessibility", "api.visual_supports_api"),
    "api.multisensory_learning_api": ("accessibility", "api.multisensory_learning_api"),

    # University & Career
    "api.university_advisory_routes": ("university", "api.university_advisory_routes"),
    "api.preference_simulation_routes": ("university", "api.preference_simulation_routes"),
    "api.department_info_routes": ("university", "api.department_info_routes"),
    "api.university_info_routes": ("university", "api.university_info_routes"),
    "api.student_review_routes": ("university", "api.student_review_routes"),

    # Other Features
    "api.live_session_routes": ("learning", "api.live_session_routes"),
    "api.team_challenges_api": ("integrations", "api.team_challenges_api"),
    "api.revolutionary_features": ("ai", "api.revolutionary_features"),
    "api.ocr_api": ("content", "api.ocr_api"),
    "api.yolo_detection_api": ("content", "api.yolo_detection_api"),
    "api.vision_api": ("ai", "api.vision_api"),
    "api.ferpa_coppa_compliance_api": ("security", "api.ferpa_coppa_compliance_api"),
    "api.validation": ("admin", "api.validation"),

    # Batch & Optimization (API Response Time Optimization)
    "api.v1.batch": ("optimization", "api.v1.batch"),

    # Semantic Search (ChromaDB Entegrasyon - Spec)
    "api.v1.semantic_search": ("search", "api.v1.semantic_search"),

    # Clustering (ChromaDB Entegrasyon - Spec REQ-6)
    "api.clustering_api": ("search", "api.clustering_api"),

    # Content Recommendation (ChromaDB Entegrasyon - Spec REQ-4)
    "api.v1.content_recommendation": ("search", "api.v1.content_recommendation"),

    # Duplicate Detection (ChromaDB Entegrasyon - Spec REQ-5)
    "api.v1.duplicate_detection": ("search", "api.v1.duplicate_detection"),

    # Diary Plugin (claude-diary-plugin Spec)
    "api.diary_api": ("learning", "api.diary_api"),

    # Faz 2: Study Planner, Leagues, Coaching (Mega Feature Plan)
    "api.study_planner_api": ("learning", "api.study_planner_api"),
    "api.league_api": ("integrations", "api.league_api"),
    "api.coaching_api": ("learning", "api.coaching_api"),

    # Faz 3: Duel, Photo Ask, Placement Assessment (Mega Feature Plan)
    "api.duel_api": ("integrations", "api.duel_api"),
    "api.photo_ask_api": ("content", "api.photo_ask_api"),
    "api.placement_assessment_api": ("exam", "api.placement_assessment_api"),

    # Faz 4: Knowledge Map
    "api.knowledge_graph_api": ("learning", "api.knowledge_graph_api"),

    # F13: Mastery Confidence Indicator
    "api.mastery_confidence_api": ("learning", "api.mastery_confidence_api"),

    # Faz 4-5: DINA, Productive Failure, Error Clusters, Mnemonics
    "api.dina_api": ("learning", "api.dina_api"),
    "api.productive_failure_api": ("learning", "api.productive_failure_api"),
    "api.error_cluster_api": ("analytics", "api.error_cluster_api"),
    "api.mnemonic_api": ("content", "api.mnemonic_api"),

    # Faz 6: PWA Offline Sync
    "api.offline_sync_api": ("learning", "api.offline_sync_api"),
}

class RouterLoader:
    """Dynamic router loader."""

    def __init__(self, app: FastAPI):
        self.app = app
        self.loaded_count = 0
        self.failed_count = 0

    def load_all_routers(self):
        """Tüm router'ları yükle."""
        logger.info("=" * 60)
        logger.info("Starting router loading...")

        # Mapping'deki router'ları yükle
        for old_module, (category, new_module) in ROUTER_MAPPING.items():
            self._load_router(new_module, category)

        # Özet bilgi
        summary = router_registry.get_summary()
        logger.info("=" * 60)
        logger.info("Router Loading Complete!")
        logger.info(f"  Loaded: {summary['total']}")
        logger.info(f"  Failed: {summary['failed']}")
        logger.info(f"  Categories: {summary['categories']}")

        # Kategori detayları
        for category in router_registry.routers:
            count = len(router_registry.routers[category])
            if count > 0:
                logger.info(f"    {category}: {count} routers")

        # Tüm router'ları app'e ekle
        self._register_to_app()

    def _load_router(self, module_path: str, category: str):
        """Tek bir router'ı yükle."""
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, 'router'):
                router = module.router
                name = module_path.split('.')[-1]

                # Prefix'i belirle - boş string ise default kullan
                prefix = getattr(router, 'prefix', None) or f"/api/{name.replace('_', '-')}"

                router_registry.register(category, name, router, prefix)
                self.loaded_count += 1
            else:
                logger.warning(f"No router found in {module_path}")
                self.failed_count += 1
        except ImportError as e:
            logger.warning(f"Failed to import {module_path}: {e}")
            router_registry.register_failed(module_path, str(e))
            self.failed_count += 1
        except Exception as e:
            logger.warning(f"Unexpected error loading {module_path}: {e}")
            router_registry.register_failed(module_path, f"Unexpected error: {e}")
            self.failed_count += 1

    def _register_to_app(self):
        """Tüm router'ları FastAPI app'e kaydet."""
        for name, router, prefix in router_registry.get_all_routers():
            try:
                # P0 FIX: Don't strip /api prefix - routes need to be accessible at /api/...
                # The router already defines its full prefix (e.g., /api/learning-path)
                # So we should NOT add another prefix when including.
                # Include with empty prefix to use router's own prefix.
                self.app.include_router(router)
                logger.debug(f"Registered router {name} with prefix: {router.prefix}")
            except Exception as e:
                logger.error(f"Failed to register {name} to app: {e}")

def setup_routers(app: FastAPI):
    """Router'ları kur (public API)."""
    loader = RouterLoader(app)
    loader.load_all_routers()
    return loader
