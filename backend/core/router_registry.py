"""
Router Registry - Centralized API Router Management
Replaces 436 lines of repetitive router includes in main.py

API Versioning Standard:
- /api/v1/* - Existing stable endpoints
- /api/v2/* - New endpoints (after 2026-01-20)
- /admin/* - Admin-only endpoints
"""

import importlib
import logging
from dataclasses import dataclass

from fastapi import FastAPI

logger = logging.getLogger(__name__)

# API Version Constants
API_V1_PREFIX = "/api/v1"
API_V2_PREFIX = "/api/v2"
ADMIN_PREFIX = "/admin"


@dataclass
class RouterConfig:
    """Configuration for API router registration"""

    module_path: str  # e.g., "api.health"
    router_name: str  # e.g., "router"
    display_name: str  # e.g., "Health Check"
    category: str  # 'core', 'features', 'integrations', 'monitoring'
    priority: int  # Load order (lower = earlier)
    required: bool = True  # If False, failure won't stop app
    api_version: str | None = None  # 'v1', 'v2', or None for unversioned

    def get_expected_prefix(self) -> str | None:
        """Get expected API prefix based on version"""
        if self.api_version == "v1":
            return API_V1_PREFIX
        if self.api_version == "v2":
            return API_V2_PREFIX
        if self.category == "admin":
            return ADMIN_PREFIX
        return None


class RouterRegistry:
    """
    Centralized router registration system
    Manages loading and registration of all API routers
    """

    def __init__(self, app: FastAPI):
        self.app = app
        self.logger = logger
        self.routers = self._get_router_configs()
        self.loaded_routers = []
        self.failed_routers = []

    def _get_router_configs(self) -> list[RouterConfig]:
        """
        Define all router configurations
        Returns routers in priority order
        """
        return [
            # CORE ROUTERS (Priority 1-9)
            RouterConfig("api.health", "router", "Health Check", "core", 1, True, "v1"),
            RouterConfig("api.auth", "router", "Authentication", "core", 2, True, "v1"),
            # EXAM & ASSESSMENT (Priority 10-29)
            RouterConfig(
                "api.sinav", "router", "Sınav Motoru", "features", 10, True, "v1"
            ),
            RouterConfig(
                "api.exam_performance",
                "router",
                "Exam Performance",
                "features",
                11,
                True,
                "v1",
            ),
            RouterConfig(
                "api.exam", "router", "WebSocket Exam", "features", 13, False, "v1"
            ),
            # LEARNING & ANALYTICS (Priority 30-49)
            RouterConfig(
                "api.monitoring",
                "router",
                "Advanced Monitoring",
                "monitoring",
                30,
                True,
                "v1",
            ),
            RouterConfig(
                "api.analytics",
                "router",
                "Advanced Analytics",
                "features",
                31,
                True,
                "v1",
            ),
            # Learning Path router
            RouterConfig(
                "api.learning_path_v2",
                "router",
                "Learning Path v2",
                "features",
                30,
                True,
            ),
            RouterConfig(
                "api.learning_style",
                "router",
                "Learning Style Analysis",
                "features",
                32,
                True,
            ),
            RouterConfig(
                "api.zpd_maarif_api", "router", "ZPD Maarif API", "features", 33, True
            ),
            RouterConfig(
                "api.irt_morfoloji_api",
                "router",
                "IRT Morfoloji API",
                "features",
                34,
                True,
            ),
            RouterConfig(
                "api.student_dashboard",
                "router",
                "Student Dashboard",
                "features",
                35,
                True,
            ),
            RouterConfig("api.fsrs_api", "router", "FSRS API", "features", 36, False),
            # CONTENT & QUESTIONS (Priority 50-69)
            RouterConfig(
                "api.soru_bankasi_api",
                "router",
                "Soru Bankası API",
                "features",
                50,
                True,
            ),
            RouterConfig(
                "api.content_management_api",
                "router",
                "Content Management",
                "features",
                51,
                True,
            ),
            RouterConfig(
                "api.curriculum_compliance_api",
                "router",
                "Curriculum Compliance",
                "features",
                52,
                False,
            ),
            # USER MANAGEMENT (Priority 70-79)
            RouterConfig("api.admin_api", "router", "Admin API", "features", 70, True),
            RouterConfig(
                "api.ogretmen_api", "router", "Öğretmen API", "features", 71, True
            ),
            RouterConfig("api.veli_api", "router", "Veli API", "features", 72, True),
            RouterConfig(
                "api.parent_api", "router", "Parent API", "features", 73, True
            ),
            # AI & NLP FEATURES (Priority 80-99)
            RouterConfig(
                "api.agents_api", "router", "AI Agents API", "features", 80, False
            ),
            RouterConfig(
                "api.multi_agent_api",
                "router",
                "Multi-Agent System",
                "features",
                81,
                False,
            ),
            RouterConfig(
                "api.zemberek_morfoloji_api",
                "router",
                "Zemberek Morfoloji",
                "integrations",
                82,
                False,
            ),
            RouterConfig(
                "api.berturk_api", "router", "BERTurk API", "integrations", 83, False
            ),
            RouterConfig(
                "api.turkish_nlp_api",
                "router",
                "Turkish NLP API",
                "integrations",
                84,
                False,
            ),
            RouterConfig(
                "api.turkish_nlp_chat_api",
                "router",
                "Turkish NLP Chat",
                "integrations",
                85,
                False,
            ),
            RouterConfig(
                "api.rag_advanced_api", "router", "RAG Advanced", "features", 86, False
            ),
            RouterConfig(
                "api.enhanced_chat_api",
                "router",
                "Enhanced Chat",
                "features",
                87,
                False,
            ),
            RouterConfig(
                "api.streaming_chat", "router", "Streaming Chat", "features", 88, False
            ),
            # INTEGRATIONS (Priority 100-119)
            RouterConfig(
                "api.ebatv_api", "router", "EBA TV API", "integrations", 100, False
            ),
            RouterConfig(
                "api.youtube_api", "router", "YouTube API", "integrations", 101, False
            ),
            RouterConfig(
                "api.elasticsearch_api",
                "router",
                "Elasticsearch API",
                "integrations",
                102,
                False,
            ),
            # UTILITIES & TOOLS (Priority 120-139)
            RouterConfig(
                "api.cache", "router", "Cache Management", "monitoring", 120, True
            ),
            RouterConfig(
                "api.text_simplification_api",
                "router",
                "Text Simplification",
                "features",
                121,
                False,
            ),
            RouterConfig(
                "api.bionic_reading_api",
                "router",
                "Bionic Reading",
                "features",
                122,
                False,
            ),
            RouterConfig(
                "api.cultural_adaptation_api",
                "router",
                "Cultural Adaptation",
                "features",
                123,
                False,
            ),
            # MONITORING & PERFORMANCE (Priority 140+)
            RouterConfig(
                "api.performance", "router", "Performance API", "monitoring", 140, True
            ),
            RouterConfig(
                "api.advanced_reports",
                "router",
                "Advanced Reports",
                "monitoring",
                141,
                False,
            ),
            RouterConfig(
                "api.performance_monitoring_api",
                "router",
                "Performance Monitoring",
                "monitoring",
                142,
                False,
            ),
        ]

    def register_all_routers(self) -> None:
        """
        Register all routers in priority order
        Handles errors gracefully for optional routers
        """
        # Sort by priority
        sorted_routers = sorted(self.routers, key=lambda x: x.priority)

        for config in sorted_routers:
            self._register_router(config)

        # Log summary
        self.logger.info(
            f"[ROUTER REGISTRY] Loaded {len(self.loaded_routers)}/{len(self.routers)} routers"
        )
        if self.failed_routers:
            self.logger.warning(
                f"[ROUTER REGISTRY] Failed to load {len(self.failed_routers)} optional routers: {', '.join(self.failed_routers)}"
            )

    def _register_router(self, config: RouterConfig) -> None:
        """
        Register a single router with error handling
        """
        try:
            # Dynamically import module
            module = importlib.import_module(config.module_path)

            # Get router from module
            router = getattr(module, config.router_name)

            # Include router in app
            self.app.include_router(router)

            # Track success
            self.loaded_routers.append(config.display_name)
            self.logger.info(
                f"[OK] [{config.category.upper()}] {config.display_name} API loaded"
            )

        except ImportError as e:
            self._handle_router_error(config, f"Import failed: {e}")

        except AttributeError:
            self._handle_router_error(
                config, f"Router '{config.router_name}' not found in module"
            )

        except Exception as e:
            self._handle_router_error(config, f"Unexpected error: {e}")

    def _handle_router_error(self, config: RouterConfig, error_msg: str) -> None:
        """Handle router loading errors based on required status"""
        if config.required:
            self.logger.error(
                f"[ERROR] REQUIRED router failed: {config.display_name} - {error_msg}"
            )
            raise RuntimeError(f"Failed to load required router: {config.display_name}")
        self.failed_routers.append(config.display_name)
        self.logger.warning(
            f"[WARNING] Optional router not loaded: {config.display_name} - {error_msg}"
        )

    def get_router_summary(self) -> dict:
        """Get summary of router registration status"""
        return {
            "total_routers": len(self.routers),
            "loaded_routers": len(self.loaded_routers),
            "failed_routers": len(self.failed_routers),
            "loaded_router_names": self.loaded_routers,
            "failed_router_names": self.failed_routers,
            "success_rate": f"{len(self.loaded_routers) / len(self.routers) * 100:.1f}%",
        }

    def audit_api_versioning(self) -> dict:
        """
        Audit API versioning consistency across registered routers.
        Returns a report of version distribution and potential issues.
        """
        versioning_report = {
            "v1_routers": [],
            "v2_routers": [],
            "unversioned_routers": [],
            "admin_routers": [],
            "total_audited": 0,
            "recommendations": [],
        }

        for config in self.routers:
            versioning_report["total_audited"] += 1

            if config.api_version == "v1":
                versioning_report["v1_routers"].append(config.display_name)
            elif config.api_version == "v2":
                versioning_report["v2_routers"].append(config.display_name)
            elif config.category == "admin":
                versioning_report["admin_routers"].append(config.display_name)
            else:
                versioning_report["unversioned_routers"].append(config.display_name)

        # Add recommendations
        unversioned_count = len(versioning_report["unversioned_routers"])
        if unversioned_count > 0:
            versioning_report["recommendations"].append(
                f"Consider adding api_version to {unversioned_count} unversioned routers"
            )

        return versioning_report


def register_all_routers(app: FastAPI) -> RouterRegistry:
    """
    Convenience function to register all routers
    Usage in main.py:

    from core.router_registry import register_all_routers
    register_all_routers(app)
    """
    registry = RouterRegistry(app)
    registry.register_all_routers()
    return registry
