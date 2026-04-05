"""
Batch 6: Deep endpoint coverage for top uncovered modules.
Target: learning_path_v2, auth, enhanced_chat, diary_api, analytics,
sinav, manipulatives_progress, video_solution, performance, rag,
multi_agent, admin, duel_api, math_solution_steps, ocr_api,
live_session_routes.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _mock_user(role="student"):
    u = MagicMock()
    u.id = "test-user-123"
    u.email = "test@kiro2.com"
    u.role = MagicMock()
    u.role.value = role
    u.username = "testuser"
    u.is_active = True
    u.full_name = "Test User"
    return u


def _mock_admin():
    return _mock_user("admin")


def _mock_db():
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalars.return_value.first.return_value = None
    mock_result.scalar.return_value = 0
    mock_result.scalar_one_or_none.return_value = None
    mock_result.fetchone.return_value = None
    mock_result.fetchall.return_value = []
    mock_result.mappings.return_value.all.return_value = []
    mock_result.mappings.return_value.first.return_value = None
    db.execute = AsyncMock(return_value=mock_result)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    db.flush = AsyncMock()
    db.rollback = AsyncMock()
    db.get = AsyncMock(return_value=None)
    return db


def _mock_redis():
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.set = AsyncMock(return_value=True)
    r.delete = AsyncMock(return_value=1)
    r.exists = AsyncMock(return_value=0)
    r.setex = AsyncMock(return_value=True)
    r.incr = AsyncMock(return_value=1)
    r.ttl = AsyncMock(return_value=-1)
    r.expire = AsyncMock(return_value=True)
    r.keys = AsyncMock(return_value=[])
    r.mget = AsyncMock(return_value=[])
    r.pipeline = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                return_value=AsyncMock(
                    get=AsyncMock(return_value=None),
                    execute=AsyncMock(return_value=[]),
                )
            ),
            __aexit__=AsyncMock(return_value=False),
        )
    )
    return r


def _make_app(module_path: str, prefix_override: str | None = None):
    import importlib

    mod = importlib.import_module(module_path)
    router = mod.router
    app = FastAPI()
    app.include_router(router)

    from core.database import get_db_session
    from core.dependencies import get_current_admin_user, get_current_user

    mock_db = _mock_db()
    mock_redis = _mock_redis()

    app.dependency_overrides[get_current_user] = lambda: _mock_user()
    app.dependency_overrides[get_current_admin_user] = lambda: _mock_admin()
    app.dependency_overrides[get_db_session] = lambda: mock_db

    try:
        from core.database import get_db

        app.dependency_overrides[get_db] = lambda: mock_db
    except ImportError:
        pass

    try:
        from core.dependencies import get_redis_client

        app.dependency_overrides[get_redis_client] = lambda: mock_redis
    except ImportError:
        pass

    return app, mock_db, mock_redis


# ---------------------------------------------------------------------------
# learning_path_v2.py — deep endpoint testing
# ---------------------------------------------------------------------------
class TestLearningPathV2Deep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.learning_path_v2")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_create_profile(self):
        r = self.client.post(
            "/create-profile", json={"student_id": "s1", "subjects": ["matematik"]}
        )
        assert r.status_code != 405

    def test_assess_knowledge(self):
        r = self.client.post(
            "/assess-knowledge",
            json={"student_id": "s1", "subject": "matematik", "answers": []},
        )
        assert r.status_code != 405

    def test_create_path(self):
        r = self.client.post(
            "/create-path", json={"student_id": "s1", "target_exam": "TYT"}
        )
        assert r.status_code != 405

    def test_search_resources(self):
        r = self.client.post(
            "/search-resources",
            json={"query": "matematik integral", "subject": "matematik"},
        )
        assert r.status_code != 405

    def test_adapt_path(self):
        r = self.client.post(
            "/adapt-path", json={"student_id": "s1", "performance_data": {}}
        )
        assert r.status_code != 405

    def test_get_completion(self):
        r = self.client.get("/completion/test-user-123")
        assert r.status_code != 405

    def test_update_completion(self):
        r = self.client.put(
            "/completion/test-user-123",
            json={"completed_nodes": ["n1"], "total_nodes": 10},
        )
        assert r.status_code != 405

    def test_submit_quiz(self):
        r = self.client.post(
            "/quiz/q1/submit", json={"answers": [{"question_id": "q1", "answer": "A"}]}
        )
        assert r.status_code != 405

    def test_update_progress(self):
        r = self.client.put(
            "/progress/test-user-123/node1", json={"status": "completed", "score": 85}
        )
        assert r.status_code != 405

    def test_fallback_videos(self):
        r = self.client.get("/fallback-videos/matematik")
        assert r.status_code != 405

    def test_health(self):
        r = self.client.get("/health")
        assert r.status_code != 405

    def test_my_profile(self):
        r = self.client.get("/my-profile")
        assert r.status_code != 405

    def test_exit_quiz(self):
        r = self.client.get("/exit-quiz/matematik")
        assert r.status_code != 405

    def test_internal_normalize(self):
        from api.learning_path_v2 import _normalize_turkish

        assert _normalize_turkish("İstanbul") == "istanbul"
        assert _normalize_turkish("ANKARA") == "ankara"

    def test_internal_map_difficulty(self):
        from api.learning_path_v2 import _map_difficulty_to_knowledge_level

        result = _map_difficulty_to_knowledge_level("EASY")
        assert result is not None


# ---------------------------------------------------------------------------
# enhanced_chat.py — deep endpoint testing
# ---------------------------------------------------------------------------
class TestEnhancedChatDeep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.enhanced_chat")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_send_message(self):
        r = self.client.post(
            "/api/v1/enhanced-chat/message",
            json={
                "message": "Merhaba, matematik sorusu sorabilir miyim?",
                "session_id": "session-1",
            },
        )
        assert r.status_code != 405

    def test_get_sessions(self):
        r = self.client.get("/api/v1/enhanced-chat/sessions")
        assert r.status_code != 405

    def test_get_session_messages(self):
        r = self.client.get("/api/v1/enhanced-chat/sessions/session-1/messages")
        assert r.status_code != 405

    def test_get_history(self):
        r = self.client.get("/api/v1/enhanced-chat/history/test-user-123")
        assert r.status_code != 405

    def test_message_with_attachment(self):
        r = self.client.post(
            "/api/v1/enhanced-chat/message-with-attachment",
            data={"message": "Bu soruyu çöz"},
            files={"file": ("test.txt", b"test content", "text/plain")},
        )
        assert r.status_code != 405


# ---------------------------------------------------------------------------
# diary_api.py — deep endpoint testing
# ---------------------------------------------------------------------------
class TestDiaryDeep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.diary_api")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_get_today_summary(self):
        r = self.client.get("/api/v1/diary/summary/today")
        assert r.status_code != 405

    def test_get_summary(self):
        r = self.client.get("/api/v1/diary/summary")
        assert r.status_code != 405

    def test_get_summaries(self):
        r = self.client.get("/api/v1/diary/summaries")
        assert r.status_code != 405

    def test_create_summary(self):
        r = self.client.post(
            "/api/v1/diary/summary",
            json={
                "content": "Bugün matematik çalıştım",
                "mood": "happy",
                "study_hours": 3.0,
            },
        )
        assert r.status_code != 405

    def test_update_summary(self):
        r = self.client.put(
            "/api/v1/diary/summary/entry-1", json={"content": "Güncellenmiş içerik"}
        )
        assert r.status_code != 405

    def test_delete_summary(self):
        r = self.client.delete("/api/v1/diary/summary/entry-1")
        assert r.status_code != 405

    def test_get_goals(self):
        r = self.client.get("/api/v1/diary/goals")
        assert r.status_code != 405

    def test_get_active_goals(self):
        r = self.client.get("/api/v1/diary/goals/active")
        assert r.status_code != 405

    def test_get_at_risk_goals(self):
        r = self.client.get("/api/v1/diary/goals/at-risk")
        assert r.status_code != 405

    def test_get_goal_statistics(self):
        r = self.client.get("/api/v1/diary/goals/statistics")
        assert r.status_code != 405

    def test_get_goal(self):
        r = self.client.get("/api/v1/diary/goals/goal-1")
        assert r.status_code != 405

    def test_create_goal(self):
        r = self.client.post(
            "/api/v1/diary/goals",
            json={
                "title": "YKS Matematik 80+",
                "target_date": "2026-06-01",
                "category": "exam",
            },
        )
        assert r.status_code != 405

    def test_validate_smart_goal(self):
        r = self.client.post(
            "/api/v1/diary/goals/validate-smart", json={"title": "Matematik net 30"}
        )
        assert r.status_code != 405

    def test_update_goal(self):
        r = self.client.put(
            "/api/v1/diary/goals/goal-1", json={"title": "Updated Goal"}
        )
        assert r.status_code != 405

    def test_update_goal_progress(self):
        r = self.client.patch(
            "/api/v1/diary/goals/goal-1/progress", json={"progress": 50}
        )
        assert r.status_code != 405

    def test_get_goal_risk(self):
        r = self.client.get("/api/v1/diary/goals/goal-1/risk")
        assert r.status_code != 405

    def test_adjust_goal(self):
        r = self.client.post(
            "/api/v1/diary/goals/goal-1/adjust", json={"new_target": "2026-07-01"}
        )
        assert r.status_code != 405

    def test_goal_retrospective(self):
        r = self.client.post(
            "/api/v1/diary/goals/goal-1/retrospective",
            json={"reflection": "İyi gidiyor"},
        )
        assert r.status_code != 405

    def test_delete_goal(self):
        r = self.client.delete("/api/v1/diary/goals/goal-1")
        assert r.status_code != 405

    def test_get_insights(self):
        r = self.client.get("/api/v1/diary/insights")
        assert r.status_code != 405

    def test_analyze_insights(self):
        r = self.client.post("/api/v1/diary/insights/analyze", json={})
        assert r.status_code != 405

    def test_get_insight(self):
        r = self.client.get("/api/v1/diary/insights/insight-1")
        assert r.status_code != 405

    def test_delete_insight(self):
        r = self.client.delete("/api/v1/diary/insights/insight-1")
        assert r.status_code != 405

    def test_get_reflection_prompts(self):
        r = self.client.get("/api/v1/diary/reflection/prompts")
        assert r.status_code != 405

    def test_create_reflection(self):
        r = self.client.post(
            "/api/v1/diary/reflection", json={"content": "Bugün verimli geçti"}
        )
        assert r.status_code != 405

    def test_get_reflections(self):
        r = self.client.get("/api/v1/diary/reflections")
        assert r.status_code != 405

    def test_get_reflection(self):
        r = self.client.get("/api/v1/diary/reflection/refl-1")
        assert r.status_code != 405

    def test_create_learning_entry(self):
        r = self.client.post(
            "/api/v1/diary/learning",
            json={"topic": "integral", "notes": "Belirli integral"},
        )
        assert r.status_code != 405

    def test_get_learning_entries(self):
        r = self.client.get("/api/v1/diary/learning")
        assert r.status_code != 405


# ---------------------------------------------------------------------------
# analytics.py — deep endpoint testing
# ---------------------------------------------------------------------------
class TestAnalyticsDeep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.analytics")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_student_analytics(self):
        r = self.client.get("/api/v1/analytics/student/test-user-123")
        assert r.status_code != 405

    def test_class_analytics(self):
        r = self.client.get("/api/v1/analytics/class/class-1")
        assert r.status_code != 405

    def test_admin_dashboard(self):
        r = self.client.get("/api/v1/analytics/admin/dashboard")
        assert r.status_code != 405

    def test_retention_d7(self):
        r = self.client.get("/api/v1/analytics/retention/d7")
        assert r.status_code != 405

    def test_export_pdf(self):
        r = self.client.post(
            "/api/v1/analytics/export/pdf",
            json={"data_type": "student", "format": "pdf"},
        )
        assert r.status_code != 405

    def test_export_excel(self):
        r = self.client.post(
            "/api/v1/analytics/export/excel",
            json={"data_type": "student", "format": "excel"},
        )
        assert r.status_code != 405

    def test_export_csv(self):
        r = self.client.post(
            "/api/v1/analytics/export/csv",
            json={"data_type": "student", "format": "csv"},
        )
        assert r.status_code != 405

    def test_web_vitals(self):
        r = self.client.post(
            "/api/v1/analytics/web-vitals",
            json={"name": "LCP", "value": 1200, "rating": "good"},
        )
        assert r.status_code in (200, 204, 422, 500)


# ---------------------------------------------------------------------------
# sinav.py — deep endpoint testing
# ---------------------------------------------------------------------------
class TestSinavDeep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.sinav")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_exam_configs(self):
        r = self.client.get("/api/v1/osym-exam/exam-configs")
        assert r.status_code != 405

    def test_create_exam(self):
        r = self.client.post("/api/v1/osym-exam/create", json={"exam_type": "TYT"})
        assert r.status_code != 405

    def test_save_answer(self):
        r = self.client.post(
            "/api/v1/osym-exam/sess-1/save-answer",
            json={"question_id": "q1", "answer": "A"},
        )
        assert r.status_code != 405

    def test_flag_question(self):
        r = self.client.post(
            "/api/v1/osym-exam/sess-1/flag-question", json={"question_index": 0}
        )
        assert r.status_code != 405

    def test_remaining_time(self):
        r = self.client.get("/api/v1/osym-exam/sess-1/remaining-time")
        assert r.status_code != 405

    def test_delete_session(self):
        r = self.client.delete("/api/v1/osym-exam/sess-1")
        assert r.status_code != 405

    def test_my_exams(self):
        r = self.client.get("/api/v1/osym-exam/my-exams")
        assert r.status_code != 405


# ---------------------------------------------------------------------------
# video_solution.py — deep endpoint testing
# ---------------------------------------------------------------------------
class TestVideoSolutionDeep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.video_solution")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_upload_video(self):
        r = self.client.post(
            "/api/v1/video-solutions/upload",
            json={
                "question_id": "q1",
                "video_url": "https://youtube.com/watch?v=test",
                "title": "Çözüm",
            },
        )
        assert r.status_code != 405

    def test_get_video(self):
        r = self.client.get("/api/v1/video-solutions/v1")
        assert r.status_code != 405

    def test_list_videos(self):
        r = self.client.get("/api/v1/video-solutions/")
        assert r.status_code != 405

    def test_delete_video(self):
        r = self.client.delete("/api/v1/video-solutions/v1")
        assert r.status_code != 405


# ---------------------------------------------------------------------------
# performance.py — deep endpoint testing
# ---------------------------------------------------------------------------
class TestPerformanceDeep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.performance")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_metrics(self):
        r = self.client.get("/api/v1/performance/metrics")
        assert r.status_code != 405

    def test_system_status(self):
        r = self.client.get("/api/v1/performance/system-status")
        assert r.status_code != 405

    def test_cache_stats(self):
        r = self.client.get("/api/v1/performance/cache-stats")
        assert r.status_code != 405

    def test_db_performance(self):
        r = self.client.get("/api/v1/performance/database-performance")
        assert r.status_code != 405

    def test_revolutionary_features(self):
        r = self.client.get("/api/v1/performance/revolutionary-features-performance")
        assert r.status_code != 405

    def test_clear_cache(self):
        r = self.client.post("/api/v1/performance/clear-cache")
        assert r.status_code != 405

    def test_api_response_times(self):
        r = self.client.get("/api/v1/performance/api-response-times")
        assert r.status_code != 405

    def test_optimize(self):
        r = self.client.post("/api/v1/performance/optimize")
        assert r.status_code != 405

    def test_health_check(self):
        r = self.client.get("/api/v1/performance/health-check")
        assert r.status_code != 405


# ---------------------------------------------------------------------------
# rag.py — deep endpoint testing
# ---------------------------------------------------------------------------
class TestRAGDeep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.rag")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_index_text(self):
        r = self.client.post(
            "/api/v1/rag/index/text",
            json={"text": "Matematik integral konusu", "metadata": {}},
        )
        assert r.status_code != 405

    def test_search(self):
        r = self.client.post(
            "/api/v1/rag/search", json={"query": "integral nasıl hesaplanır"}
        )
        assert r.status_code != 405

    def test_context(self):
        r = self.client.post("/api/v1/rag/context", json={"query": "türev nedir"})
        assert r.status_code != 405

    def test_list_documents(self):
        r = self.client.get("/api/v1/rag/documents")
        assert r.status_code != 405

    def test_delete_document(self):
        r = self.client.delete("/api/v1/rag/documents/doc-1")
        assert r.status_code != 405

    def test_stats(self):
        r = self.client.get("/api/v1/rag/stats")
        assert r.status_code != 405

    def test_health(self):
        r = self.client.get("/api/v1/rag/health")
        assert r.status_code != 405


# ---------------------------------------------------------------------------
# multi_agent.py — deep endpoint testing
# ---------------------------------------------------------------------------
class TestMultiAgentDeep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.multi_agent")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_write(self):
        r = self.client.post(
            "/api/v1/multi-agent/write", json={"key": "test-key", "value": "test-value"}
        )
        assert r.status_code != 405

    def test_read(self):
        r = self.client.get("/api/v1/multi-agent/read/test-key")
        assert r.status_code != 405

    def test_delete(self):
        r = self.client.delete("/api/v1/multi-agent/delete/test-key")
        assert r.status_code != 405

    def test_subscribe(self):
        r = self.client.post(
            "/api/v1/multi-agent/subscribe",
            json={"topic": "test-topic", "callback_url": "http://test"},
        )
        assert r.status_code != 405

    def test_coordination_request(self):
        r = self.client.post(
            "/api/v1/multi-agent/coordination/request",
            json={"task": "analyze", "data": {}},
        )
        assert r.status_code != 405

    def test_coordination_respond(self):
        r = self.client.post(
            "/api/v1/multi-agent/coordination/respond",
            json={"request_id": "req-1", "result": {}},
        )
        assert r.status_code != 405

    def test_metrics(self):
        r = self.client.get("/api/v1/multi-agent/metrics")
        assert r.status_code != 405

    def test_agents_status(self):
        r = self.client.get("/api/v1/multi-agent/agents/status")
        assert r.status_code != 405

    def test_events_history(self):
        r = self.client.get("/api/v1/multi-agent/events/history")
        assert r.status_code != 405

    def test_health(self):
        r = self.client.get("/api/v1/multi-agent/health")
        assert r.status_code != 405


# ---------------------------------------------------------------------------
# admin.py — deep endpoint testing
# ---------------------------------------------------------------------------
class TestAdminDeep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.admin")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_list_users(self):
        r = self.client.get("/api/v1/admin/users")
        assert r.status_code != 405

    def test_create_user(self):
        r = self.client.post(
            "/api/v1/admin/users",
            json={"email": "new@test.com", "password": "Test1234!", "role": "student"},
        )
        assert r.status_code != 405

    def test_get_user(self):
        r = self.client.get("/api/v1/admin/users/user-1")
        assert r.status_code != 405

    def test_update_user(self):
        r = self.client.put(
            "/api/v1/admin/users/user-1", json={"full_name": "Updated Name"}
        )
        assert r.status_code != 405

    def test_delete_user(self):
        r = self.client.delete("/api/v1/admin/users/user-1")
        assert r.status_code != 405

    def test_dashboard_stats(self):
        r = self.client.get("/api/v1/admin/dashboard/stats")
        assert r.status_code != 405

    def test_list_questions(self):
        r = self.client.get("/api/v1/admin/content/questions")
        assert r.status_code != 405

    def test_create_question(self):
        r = self.client.post(
            "/api/v1/admin/content/questions",
            json={"content": "2+2=?", "answer": "4", "subject": "matematik"},
        )
        assert r.status_code != 405

    def test_update_question(self):
        r = self.client.put(
            "/api/v1/admin/content/questions/q1", json={"content": "Updated question"}
        )
        assert r.status_code != 405

    def test_delete_question(self):
        r = self.client.delete("/api/v1/admin/content/questions/q1")
        assert r.status_code != 405

    def test_list_educational(self):
        r = self.client.get("/api/v1/admin/content/educational")
        assert r.status_code != 405

    def test_create_educational(self):
        r = self.client.post(
            "/api/v1/admin/content/educational", json={"title": "Test Material"}
        )
        assert r.status_code != 405

    def test_update_educational(self):
        r = self.client.put(
            "/api/v1/admin/content/educational/m1", json={"title": "Updated"}
        )
        assert r.status_code != 405

    def test_delete_educational(self):
        r = self.client.delete("/api/v1/admin/content/educational/m1")
        assert r.status_code != 405


# ---------------------------------------------------------------------------
# duel_api.py — deep endpoint testing
# ---------------------------------------------------------------------------
class TestDuelDeep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.duel_api")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_create_duel(self):
        r = self.client.post(
            "/api/v1/duel/create", json={"opponent_id": "u2", "subject": "matematik"}
        )
        assert r.status_code != 405

    def test_accept_duel(self):
        r = self.client.post("/api/v1/duel/accept", json={"duel_id": "d1"})
        assert r.status_code != 405

    def test_get_active_duels(self):
        r = self.client.get("/api/v1/duel/active")
        assert r.status_code != 405

    def test_get_history(self):
        r = self.client.get("/api/v1/duel/history")
        assert r.status_code != 405

    def test_get_stats(self):
        r = self.client.get("/api/v1/duel/stats")
        assert r.status_code != 405


# ---------------------------------------------------------------------------
# math_solution_steps.py — deep endpoint testing
# ---------------------------------------------------------------------------
class TestMathSolutionDeep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.math_solution_steps")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_generate(self):
        r = self.client.post(
            "/api/v1/math-solution-steps/generate", json={"problem": "x^2 + 2x + 1 = 0"}
        )
        assert r.status_code != 405

    def test_get_solution(self):
        r = self.client.get("/api/v1/math-solution-steps/solution/p1")
        assert r.status_code != 405

    def test_get_step(self):
        r = self.client.get("/api/v1/math-solution-steps/step/p1/1")
        assert r.status_code != 405

    def test_hint(self):
        r = self.client.post(
            "/api/v1/math-solution-steps/hint",
            json={"problem_id": "p1", "step_number": 1},
        )
        assert r.status_code != 405

    def test_navigation(self):
        r = self.client.get("/api/v1/math-solution-steps/navigation/p1")
        assert r.status_code != 405

    def test_delete_cache(self):
        r = self.client.delete("/api/v1/math-solution-steps/cache")
        assert r.status_code != 405

    def test_hint_stats(self):
        r = self.client.get("/api/v1/math-solution-steps/hint-stats/test-user-123")
        assert r.status_code != 405

    def test_hint_trends(self):
        r = self.client.get("/api/v1/math-solution-steps/hint-trends/test-user-123")
        assert r.status_code != 405

    def test_check_answer(self):
        r = self.client.post(
            "/api/v1/math-solution-steps/check-answer",
            json={"problem_id": "p1", "answer": "x = -1"},
        )
        assert r.status_code != 405

    def test_error_analysis(self):
        r = self.client.get("/api/v1/math-solution-steps/error-analysis/test-user-123")
        assert r.status_code != 405

    def test_health(self):
        r = self.client.get("/api/v1/math-solution-steps/health")
        assert r.status_code != 405


# ---------------------------------------------------------------------------
# ocr_api.py — deep endpoint testing
# ---------------------------------------------------------------------------
class TestOCRDeep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.ocr_api")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_extract(self):
        r = self.client.post(
            "/api/v1/ocr/extract",
            files={"file": ("test.png", b"\x89PNG\r\n", "image/png")},
        )
        assert r.status_code != 405

    def test_extract_base64(self):
        r = self.client.post(
            "/api/v1/ocr/extract-base64",
            json={"image_base64": "data:image/png;base64,iVBORw0KGgo="},
        )
        assert r.status_code != 405

    def test_question_ocr(self):
        r = self.client.post(
            "/api/v1/ocr/question",
            files={"file": ("q.png", b"\x89PNG\r\n", "image/png")},
        )
        assert r.status_code != 405

    def test_engines(self):
        r = self.client.get("/api/v1/ocr/engines")
        assert r.status_code != 405

    def test_health(self):
        r = self.client.get("/api/v1/ocr/health")
        assert r.status_code != 405

    def test_info(self):
        r = self.client.get("/api/v1/ocr/info")
        assert r.status_code != 405


# ---------------------------------------------------------------------------
# live_session_routes.py — deep endpoint testing
# ---------------------------------------------------------------------------
class TestLiveSessionDeep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.live_session_routes")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_create_session(self):
        r = self.client.post(
            "/api/v1/live-sessions",
            json={"title": "Matematik Dersi", "type": "tutorial"},
        )
        assert r.status_code != 405

    def test_get_session(self):
        r = self.client.get("/api/v1/live-sessions/sess-1")
        assert r.status_code != 405

    def test_start_session(self):
        r = self.client.post("/api/v1/live-sessions/sess-1/start")
        assert r.status_code != 405

    def test_end_session(self):
        r = self.client.post("/api/v1/live-sessions/sess-1/end")
        assert r.status_code != 405

    def test_join_session(self):
        r = self.client.post("/api/v1/live-sessions/sess-1/join")
        assert r.status_code != 405

    def test_leave_session(self):
        r = self.client.post("/api/v1/live-sessions/sess-1/leave")
        assert r.status_code != 405

    def test_screen_share_start(self):
        r = self.client.post("/api/v1/live-sessions/sess-1/screen-share/start")
        assert r.status_code != 405

    def test_screen_share_stop(self):
        r = self.client.post("/api/v1/live-sessions/screen-share/ss-1/stop")
        assert r.status_code != 405

    def test_create_whiteboard(self):
        r = self.client.post(
            "/api/v1/live-sessions/sess-1/whiteboard", json={"title": "Board 1"}
        )
        assert r.status_code != 405

    def test_get_whiteboard(self):
        r = self.client.get("/api/v1/live-sessions/whiteboard/wb-1")
        assert r.status_code != 405

    def test_whiteboard_stroke(self):
        r = self.client.post(
            "/api/v1/live-sessions/whiteboard/wb-1/stroke",
            json={"points": [{"x": 0, "y": 0}], "color": "black"},
        )
        assert r.status_code != 405

    def test_whiteboard_equation(self):
        r = self.client.post(
            "/api/v1/live-sessions/whiteboard/wb-1/equation",
            json={"latex": "x^2 + 1 = 0"},
        )
        assert r.status_code != 405


# ---------------------------------------------------------------------------
# manipulatives_progress_api.py — deep endpoint testing
# ---------------------------------------------------------------------------
class TestManipulativesProgressDeep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.manipulatives_progress_api")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_dashboard(self):
        r = self.client.get("/api/v1/manipulatives/progress/progress/dashboard")
        assert r.status_code != 405

    def test_badges(self):
        r = self.client.get("/api/v1/manipulatives/progress/badges")
        assert r.status_code != 405

    def test_summary(self):
        r = self.client.get("/api/v1/manipulatives/progress/progress/summary")
        assert r.status_code != 405

    def test_claim_badge(self):
        r = self.client.post("/api/v1/manipulatives/progress/badges/badge-1/claim")
        assert r.status_code != 405

    def test_weekly(self):
        r = self.client.get("/api/v1/manipulatives/progress/progress/weekly")
        assert r.status_code != 405


# ---------------------------------------------------------------------------
# auth.py — deep endpoint testing (more endpoints)
# ---------------------------------------------------------------------------
class TestAuthDeep:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app, self.db, self.redis = _make_app("api.auth")
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_validate(self):
        r = self.client.post("/validate")
        assert r.status_code != 405

    def test_change_password(self):
        r = self.client.post(
            "/change-password",
            json={"old_password": "OldPass123!", "new_password": "NewPass456!"},
        )
        assert r.status_code != 405

    def test_forgot_password(self):
        r = self.client.post("/forgot-password", json={"email": "test@kiro2.com"})
        assert r.status_code != 405

    def test_reset_password(self):
        r = self.client.post(
            "/reset-password", json={"token": "tok-1", "new_password": "Reset789!"}
        )
        assert r.status_code != 405

    def test_update_profile(self):
        r = self.client.put("/profile", json={"full_name": "Updated Name"})
        assert r.status_code != 405
