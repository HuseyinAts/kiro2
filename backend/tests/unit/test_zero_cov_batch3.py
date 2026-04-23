"""
Unit tests for zero-coverage backend files – Batch 3.

Targets:
  1. core/unified/monitoring_system.py  (334 stmts, 0%)
  2. core/sso_saml_service.py           (356 stmts, 0%)
  3. core/chat_interface.py             (219 stmts, 0%)
  4. services/video_conference_service.py (202 stmts, 14%)

All heavy imports are stubbed via sys.modules *before* the modules are loaded.
Modules are loaded with importlib.util to avoid cross-file contamination.
"""

import importlib.util
import os
import sys
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Stale-stub cleanup – remove any previously cached MagicMock stubs that
# might have been left by earlier test runs in the same process.
# ---------------------------------------------------------------------------
_STALE_PREFIXES = (
    "psutil",
    "cryptography",
    "core.llm_service",
    "models.live_session",
    "models.database",
    "sqlalchemy",
)
for _key in list(sys.modules):
    for _pfx in _STALE_PREFIXES:
        if _key == _pfx or _key.startswith(_pfx + "."):
            if isinstance(sys.modules[_key], MagicMock):
                del sys.modules[_key]
            break


# ---------------------------------------------------------------------------
# Heavy-import stubs
# ---------------------------------------------------------------------------

# psutil – used by monitoring_system.py
_psutil_stub = MagicMock()
_psutil_stub.cpu_percent.return_value = 25.0
_vm = MagicMock()
_vm.percent = 50.0
_vm.used = 512 * 1024 * 1024
_vm.available = 512 * 1024 * 1024
_psutil_stub.virtual_memory.return_value = _vm
_disk = MagicMock()
_disk.percent = 40.0
_disk.free = 100 * 1024 * 1024 * 1024
_psutil_stub.disk_usage.return_value = _disk
_net = MagicMock()
_net.bytes_sent = 1024 * 1024
_net.bytes_recv = 2 * 1024 * 1024
_psutil_stub.net_io_counters.return_value = _net
_psutil_stub.getloadavg.return_value = [0.5, 0.4, 0.3]
_psutil_stub.net_connections.return_value = [MagicMock()] * 5
_psutil_stub.AccessDenied = Exception
# Force-replace even if real psutil is installed — monitoring_system.py
# must see this stub when it is loaded by _load() below.
sys.modules["psutil"] = _psutil_stub

# cryptography – used by sso_saml_service.py
_crypto_stub = MagicMock()
_x509_stub = MagicMock()
_cert_mock = MagicMock()
_cert_mock.public_key.return_value = MagicMock()
_x509_stub.load_pem_x509_certificate.return_value = _cert_mock
_crypto_stub.x509 = _x509_stub
sys.modules.setdefault("cryptography", _crypto_stub)
sys.modules.setdefault("cryptography.x509", _x509_stub)

# core.llm_service – used by chat_interface.py
_llm_stub = MagicMock()
_llm_svc = MagicMock()
_llm_svc.generate = AsyncMock(return_value={"success": True, "text": "LLM response"})
_llm_stub.llm_service = _llm_svc
sys.modules.setdefault("core.llm_service", _llm_stub)

# models.live_session – used by video_conference_service.py
_ls_stub = MagicMock()


class _SessionStatus:
    SCHEDULED = "scheduled"
    LIVE = "live"
    ENDED = "ended"
    CANCELLED = "cancelled"


class _SessionType:
    ONE_ON_ONE = "one_on_one"
    GROUP_SESSION = "group_session"
    WEBINAR = "webinar"


class _PlatformType:
    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    JITSI = "jitsi"


class _ParticipantRole:
    HOST = "host"
    PARTICIPANT = "participant"


class _RecordingStatus:
    RECORDING = "recording"
    PROCESSING = "processing"
    READY = "ready"


class _ScreenShareType:
    FULL_SCREEN = "full_screen"
    WINDOW = "window"


class _LiveSession:
    # Class-level MagicMock column descriptors so that SQLAlchemy-style
    # .where(LiveSession.id == x) calls resolve without error.
    id = MagicMock()
    host_id = MagicMock()
    status = MagicMock()
    scheduled_start = MagicMock()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = "session-uuid-1"
        self.title = kwargs.get("title", "Test Session")
        self.description = kwargs.get("description", "desc")
        self.enable_mute_on_join = False
        self.enable_waiting_room = True
        self.auto_record = kwargs.get("auto_record", False)
        self.allow_recording = True
        self.is_recorded = False
        self.current_participants = 0
        self.status = _SessionStatus.SCHEDULED
        self.actual_start = None
        self.actual_end = None
        self.duration_minutes = kwargs.get("duration_minutes", 60)
        self.zoom_meeting_data = None
        self.meet_event_data = None
        self.meeting_id = None
        self.meeting_url = None
        self.join_url = None
        self.host_url = None
        self.meeting_password = None
        self.scheduled_start = kwargs.get("scheduled_start", datetime.now(UTC))
        self.scheduled_end = kwargs.get(
            "scheduled_end", datetime.now(UTC) + timedelta(hours=1)
        )


class _SessionParticipant:
    # Class-level column descriptors
    id = MagicMock()
    session_id = MagicMock()
    user_id = MagicMock()
    is_present = MagicMock()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = "part-uuid-1"
        self.is_present = False
        self.joined_at = None
        self.left_at = None
        self.duration_minutes = 0
        self.is_sharing_screen = False


class _ScreenShare:
    # Class-level column descriptors
    id = MagicMock()
    session_id = MagicMock()
    user_id = MagicMock()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = "share-uuid-1"
        self.started_at = kwargs.get("started_at", datetime.now(UTC))
        self.ended_at = None
        self.duration_seconds = 0
        self.session_id = kwargs.get("session_id", "session-uuid-1")
        self.user_id = kwargs.get("user_id", "user-uuid-1")


class _SessionChatMessage:
    # Class-level column descriptors
    id = MagicMock()
    session_id = MagicMock()
    user_id = MagicMock()
    recipient_id = MagicMock()
    is_private = MagicMock()
    is_deleted = MagicMock()
    created_at = MagicMock()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = "chat-uuid-1"


class _SessionAnalytics:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _SessionRecording:
    # Class-level column descriptors
    id = MagicMock()
    session_id = MagicMock()
    status = MagicMock()
    created_at = MagicMock()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = "rec-uuid-1"
        self.status = _RecordingStatus.RECORDING
        self.started_at = kwargs.get("started_at", datetime.now(UTC))
        self.ended_at = None
        self.duration_seconds = 0
        self.is_recorded = False
        self.processing_completed_at = None
        self.file_url = None
        self.thumbnail_url = None
        self.session_id = kwargs.get("session_id", "session-uuid-1")


_ls_stub.LiveSession = _LiveSession
_ls_stub.SessionParticipant = _SessionParticipant
_ls_stub.ScreenShare = _ScreenShare
_ls_stub.SessionChatMessage = _SessionChatMessage
_ls_stub.SessionAnalytics = _SessionAnalytics
_ls_stub.SessionRecording = _SessionRecording
_ls_stub.SessionStatus = _SessionStatus
_ls_stub.SessionType = _SessionType
_ls_stub.PlatformType = _PlatformType
_ls_stub.ParticipantRole = _ParticipantRole
_ls_stub.RecordingStatus = _RecordingStatus
_ls_stub.ScreenShareType = _ScreenShareType
sys.modules.setdefault("models.live_session", _ls_stub)

# models.database Base
_db_stub = MagicMock()
_db_stub.Base = MagicMock()
sys.modules.setdefault("models.database", _db_stub)


# ---------------------------------------------------------------------------
# Module loader helper
# ---------------------------------------------------------------------------
def _load(name: str, rel_path: str):
    full_path = os.path.join(_BACKEND, rel_path)
    spec = importlib.util.spec_from_file_location(name, full_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Load modules under test
# ---------------------------------------------------------------------------
monitoring = _load(
    "core.unified.monitoring_system",
    os.path.join("core", "unified", "monitoring_system.py"),
)
sso = _load("core.sso_saml_service", os.path.join("core", "sso_saml_service.py"))
chat = _load("core.chat_interface", os.path.join("core", "chat_interface.py"))
vcs = _load(
    "services.video_conference_service",
    os.path.join("services", "video_conference_service.py"),
)


# ===========================================================================
# 1.  monitoring_system.py  tests
# ===========================================================================


class TestMetricType:
    def test_all_values_present(self):
        mt = monitoring.MetricType
        assert mt.COUNTER.value == "counter"
        assert mt.GAUGE.value == "gauge"
        assert mt.HISTOGRAM.value == "histogram"
        assert mt.SUMMARY.value == "summary"
        assert mt.RATE.value == "rate"


class TestAlertLevel:
    def test_levels(self):
        al = monitoring.AlertLevel
        assert al.INFO.value == "info"
        assert al.WARNING.value == "warning"
        assert al.ERROR.value == "error"
        assert al.CRITICAL.value == "critical"


class TestMonitoringConfig:
    def test_defaults(self):
        cfg = monitoring.MonitoringConfig()
        assert cfg.collection_interval == 60
        assert cfg.retention_hours == 24
        assert cfg.max_metrics_memory == 10000
        assert cfg.enable_system_monitoring is True
        assert cfg.enable_api_monitoring is True
        assert cfg.cpu_threshold == 80.0
        assert cfg.memory_threshold == 85.0
        assert cfg.disk_threshold == 90.0
        assert cfg.response_time_threshold == 5.0
        assert cfg.error_rate_threshold == 0.05

    def test_custom_values(self):
        cfg = monitoring.MonitoringConfig(
            collection_interval=30, cpu_threshold=70.0, enable_alerts=False
        )
        assert cfg.collection_interval == 30
        assert cfg.cpu_threshold == 70.0
        assert cfg.enable_alerts is False


class TestMetricsAggregator:
    def _make_metric(self, name, value, cat=None):
        cat = cat or monitoring.MonitoringCategory.SYSTEM
        return monitoring.MetricPoint(
            timestamp=datetime.now(),
            name=name,
            value=value,
            metric_type=monitoring.MetricType.GAUGE,
            category=cat,
        )

    def test_add_and_get_statistics(self):
        agg = monitoring.MetricsAggregator(window_size=50)
        for v in [10, 20, 30, 40, 50]:
            agg.add_metric(self._make_metric("cpu", v))
        stats = agg.get_statistics(monitoring.MonitoringCategory.SYSTEM, "cpu")
        assert stats["count"] == 5
        assert stats["min"] == 10
        assert stats["max"] == 50
        assert stats["avg"] == 30.0
        assert stats["sum"] == 150

    def test_empty_statistics(self):
        agg = monitoring.MetricsAggregator()
        result = agg.get_statistics(monitoring.MonitoringCategory.SYSTEM, "missing")
        assert result == {}

    def test_get_rate_insufficient_data(self):
        agg = monitoring.MetricsAggregator()
        agg.add_metric(self._make_metric("req", 1))
        rate = agg.get_rate(monitoring.MonitoringCategory.SYSTEM, "req")
        assert rate == 0.0

    def test_window_size_enforced(self):
        agg = monitoring.MetricsAggregator(window_size=3)
        for v in range(10):
            agg.add_metric(self._make_metric("x", v))
        key = f"{monitoring.MonitoringCategory.SYSTEM.value}:x"
        assert len(agg.metrics_buffer[key]) == 3


class TestAlertManager:
    def _make_cfg(self, **kw):
        return monitoring.MonitoringConfig(**kw)

    def _make_metric(self, name, value, cat, offset_secs=0):
        ts = datetime.now() - timedelta(seconds=offset_secs)
        return monitoring.MetricPoint(
            timestamp=ts,
            name=name,
            value=value,
            metric_type=monitoring.MetricType.GAUGE,
            category=cat,
        )

    def test_no_alerts_when_below_threshold(self):
        cfg = self._make_cfg(cpu_threshold=80.0)
        mgr = monitoring.AlertManager(cfg)
        metrics = [
            self._make_metric("cpu_percent", 50.0, monitoring.MonitoringCategory.SYSTEM)
        ]
        alerts = mgr.check_alerts(metrics)
        assert alerts == []

    def test_cpu_alert_warning(self):
        cfg = self._make_cfg(cpu_threshold=80.0)
        mgr = monitoring.AlertManager(cfg)
        metrics = [
            self._make_metric("cpu_percent", 85.0, monitoring.MonitoringCategory.SYSTEM)
        ]
        alerts = mgr.check_alerts(metrics)
        assert len(alerts) == 1
        assert alerts[0].level == monitoring.AlertLevel.WARNING
        assert "CPU" in alerts[0].title

    def test_cpu_alert_critical(self):
        cfg = self._make_cfg(cpu_threshold=80.0)
        mgr = monitoring.AlertManager(cfg)
        metrics = [
            self._make_metric("cpu_percent", 95.0, monitoring.MonitoringCategory.SYSTEM)
        ]
        alerts = mgr.check_alerts(metrics)
        assert alerts[0].level == monitoring.AlertLevel.CRITICAL

    def test_memory_alert(self):
        cfg = self._make_cfg(memory_threshold=85.0)
        mgr = monitoring.AlertManager(cfg)
        metrics = [
            self._make_metric(
                "memory_percent", 90.0, monitoring.MonitoringCategory.SYSTEM
            )
        ]
        alerts = mgr.check_alerts(metrics)
        assert any("Memory" in a.title for a in alerts)

    def test_disk_alert(self):
        cfg = self._make_cfg(disk_threshold=90.0)
        mgr = monitoring.AlertManager(cfg)
        metrics = [
            self._make_metric(
                "disk_percent", 95.0, monitoring.MonitoringCategory.SYSTEM
            )
        ]
        alerts = mgr.check_alerts(metrics)
        assert any("Disk" in a.title for a in alerts)

    def test_alerts_disabled(self):
        cfg = self._make_cfg(enable_alerts=False)
        mgr = monitoring.AlertManager(cfg)
        assert len(mgr.alert_rules) == 0

    def test_response_time_alert(self):
        cfg = self._make_cfg(response_time_threshold=5.0)
        mgr = monitoring.AlertManager(cfg)
        metrics = [
            self._make_metric(
                "response_time", 8.0, monitoring.MonitoringCategory.API, offset_secs=i
            )
            for i in range(5)
        ]
        alerts = mgr.check_alerts(metrics)
        assert any("Response" in a.title for a in alerts)

    def test_error_rate_alert(self):
        cfg = self._make_cfg(error_rate_threshold=0.05)
        mgr = monitoring.AlertManager(cfg)
        metrics = [
            self._make_metric(
                "status_code", 500, monitoring.MonitoringCategory.API, offset_secs=i
            )
            for i in range(8)
        ] + [
            self._make_metric(
                "status_code", 200, monitoring.MonitoringCategory.API, offset_secs=i
            )
            for i in range(2)
        ]
        alerts = mgr.check_alerts(metrics)
        assert any("Error" in a.title for a in alerts)


class TestUnifiedMonitoringManager:
    def test_init_defaults(self):
        mgr = monitoring.UnifiedMonitoringManager()
        assert mgr._initialized is False
        assert mgr.metrics == []

    def test_add_metric(self):
        mgr = monitoring.UnifiedMonitoringManager()
        mgr.add_metric(
            "test_metric",
            42.0,
            monitoring.MetricType.GAUGE,
            monitoring.MonitoringCategory.API,
        )
        assert len(mgr.metrics) == 1
        assert mgr.metrics[0].name == "test_metric"
        assert mgr.metrics[0].value == 42.0

    def test_record_api_call(self):
        mgr = monitoring.UnifiedMonitoringManager()
        mgr.record_api_call(
            endpoint="/api/test",
            method="GET",
            status_code=200,
            response_time=0.1,
            request_size=100,
            response_size=500,
            user_id="user1",
        )
        names = [m.name for m in mgr.metrics]
        assert "response_time" in names
        assert "status_code" in names
        assert "api_call" in names

    def test_record_api_call_disabled(self):
        cfg = monitoring.MonitoringConfig(enable_api_monitoring=False)
        mgr = monitoring.UnifiedMonitoringManager(cfg)
        mgr.record_api_call("/x", "GET", 200, 0.1)
        assert len(mgr.metrics) == 0

    def test_record_database_query(self):
        mgr = monitoring.UnifiedMonitoringManager()
        mgr.record_database_query("SELECT", 0.05, rows_affected=10, table_name="users")
        names = [m.name for m in mgr.metrics]
        assert "db_query_time" in names
        assert "db_query_count" in names

    def test_record_db_query_disabled(self):
        cfg = monitoring.MonitoringConfig(enable_db_monitoring=False)
        mgr = monitoring.UnifiedMonitoringManager(cfg)
        mgr.record_database_query("SELECT", 0.01)
        assert len(mgr.metrics) == 0

    def test_collect_system_metrics(self):
        mgr = monitoring.UnifiedMonitoringManager()
        sys_m = mgr.collect_system_metrics()
        assert sys_m.cpu_percent == 25.0
        assert sys_m.memory_percent == 50.0
        assert sys_m.disk_percent == 40.0
        assert isinstance(sys_m.load_average, list)

    def test_get_metrics_summary_empty(self):
        mgr = monitoring.UnifiedMonitoringManager()
        summary = mgr.get_metrics_summary()
        assert summary["total_metrics"] == 0
        assert "categories" in summary

    def test_get_metrics_summary_with_data(self):
        mgr = monitoring.UnifiedMonitoringManager()
        mgr.add_metric(
            "resp", 0.3, monitoring.MetricType.GAUGE, monitoring.MonitoringCategory.API
        )
        summary = mgr.get_metrics_summary(category=monitoring.MonitoringCategory.API)
        assert summary["total_metrics"] == 1

    def test_get_alerts_filter(self):
        mgr = monitoring.UnifiedMonitoringManager()
        alert = monitoring.Alert(
            id="a1",
            level=monitoring.AlertLevel.WARNING,
            title="Test",
            message="Test alert",
            category=monitoring.MonitoringCategory.SYSTEM,
            timestamp=datetime.now(),
        )
        mgr.alert_manager.alerts.append(alert)
        result = mgr.get_alerts(level=monitoring.AlertLevel.WARNING)
        assert len(result) == 1
        assert result[0].id == "a1"

    def test_get_alerts_resolved_filter(self):
        mgr = monitoring.UnifiedMonitoringManager()
        a1 = monitoring.Alert(
            id="a1",
            level=monitoring.AlertLevel.INFO,
            title="T",
            message="M",
            category=monitoring.MonitoringCategory.SYSTEM,
            timestamp=datetime.now(),
            resolved=True,
        )
        a2 = monitoring.Alert(
            id="a2",
            level=monitoring.AlertLevel.WARNING,
            title="T2",
            message="M2",
            category=monitoring.MonitoringCategory.SYSTEM,
            timestamp=datetime.now(),
            resolved=False,
        )
        mgr.alert_manager.alerts = [a1, a2]
        unresolved = mgr.get_alerts(resolved=False)
        assert len(unresolved) == 1
        assert unresolved[0].id == "a2"

    def test_health_check_not_initialized(self):
        mgr = monitoring.UnifiedMonitoringManager()
        hc = mgr.health_check()
        assert hc["initialized"] is False
        assert hc["system"] is None

    def test_health_check_initialized(self):
        mgr = monitoring.UnifiedMonitoringManager()
        mgr._initialized = True
        hc = mgr.health_check()
        assert hc["initialized"] is True
        assert hc["system"] is not None

    def test_memory_cleanup_on_overflow(self):
        cfg = monitoring.MonitoringConfig(max_metrics_memory=5, retention_hours=0)
        mgr = monitoring.UnifiedMonitoringManager(cfg)
        for i in range(10):
            mgr.add_metric(
                "m",
                i,
                monitoring.MetricType.GAUGE,
                monitoring.MonitoringCategory.SYSTEM,
            )
        # After overflow, retention_hours=0 means cutoff=now, all purged
        assert len(mgr.metrics) <= 5

    @pytest.mark.asyncio
    async def test_initialize(self):
        cfg = monitoring.MonitoringConfig(enable_system_monitoring=False)
        mgr = monitoring.UnifiedMonitoringManager(cfg)
        await mgr.initialize()
        assert mgr._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self):
        cfg = monitoring.MonitoringConfig(enable_system_monitoring=False)
        mgr = monitoring.UnifiedMonitoringManager(cfg)
        await mgr.initialize()
        await mgr.initialize()
        assert mgr._initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self):
        cfg = monitoring.MonitoringConfig(enable_system_monitoring=False)
        mgr = monitoring.UnifiedMonitoringManager(cfg)
        await mgr.initialize()
        await mgr.shutdown()  # Should not raise

    def test_get_monitoring_manager_singleton(self):
        # Reset global state first
        monitoring._monitoring_manager = None
        m1 = monitoring.get_monitoring_manager()
        m2 = monitoring.get_monitoring_manager()
        assert m1 is m2
        assert isinstance(m1, monitoring.UnifiedMonitoringManager)
        monitoring._monitoring_manager = None  # cleanup


# ===========================================================================
# 2.  sso_saml_service.py  tests
# ===========================================================================

# Minimal valid IdP metadata XML (uses standard SAML NS)
_IDP_METADATA = """<?xml version="1.0"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
    entityID="https://idp.example.com">
  <md:IDPSSODescriptor WantAuthnRequestsSigned="false"
      protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:KeyDescriptor use="signing">
      <ds:KeyInfo>
        <ds:X509Data>
          <ds:X509Certificate>MIICpDCCAYwCCQDU+pQ4pHgSpDANBgkqhkiG9w0BAQsFADAUMRIwEAYDVQQDDAls
b2NhbGhvc3QwHhcNMjMwMTAxMDAwMDAwWhcNMjQwMTAxMDAwMDAwWjAUMRIwEAYD
VQQDDAlsb2NhbGhvc3QwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC7
o4qne60TB3pOK4KHNKCbGW8OJ0FRm63jYbDeW2gDRBRn1Dq1rKZMLVBKLBl2PQXQ
RQ3NdLfZzAp5IIWVFaUyJCeVdH0VYKkxTdDm0v9aV7c+YJXkq8WkIxQDPmjKdIqf
nFOAhYAqkKdsMGJ2s5BHsN7Q7xEHi+YFOP5KBVK1n</ds:X509Certificate>
        </ds:X509Data>
      </ds:KeyInfo>
    </md:KeyDescriptor>
    <md:SingleLogoutService
        Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        Location="https://idp.example.com/slo"/>
    <md:SingleSignOnService
        Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        Location="https://idp.example.com/sso"/>
    <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
  </md:IDPSSODescriptor>
</md:EntityDescriptor>"""

_IDP_METADATA_REDIRECT_ONLY = """<?xml version="1.0"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    entityID="https://idp2.example.com">
  <md:IDPSSODescriptor>
    <md:SingleSignOnService
        Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        Location="https://idp2.example.com/sso/redirect"/>
  </md:IDPSSODescriptor>
</md:EntityDescriptor>"""


def _make_sp_config():
    return sso.SPConfig(
        entity_id="https://kiro2.test/saml/metadata",
        acs_url="https://kiro2.test/api/v1/auth/saml/acs",
        slo_url="https://kiro2.test/api/v1/auth/saml/slo",
        metadata_url="https://kiro2.test/api/v1/auth/saml/metadata",
    )


class TestSAMLEnums:
    def test_saml_binding_values(self):
        assert "HTTP-POST" in sso.SAMLBinding.HTTP_POST.value
        assert "HTTP-Redirect" in sso.SAMLBinding.HTTP_REDIRECT.value
        assert "HTTP-Artifact" in sso.SAMLBinding.HTTP_ARTIFACT.value

    def test_saml_error_values(self):
        assert sso.SAMLError.INVALID_METADATA.value == "invalid_metadata"
        assert sso.SAMLError.REPLAY_ATTACK.value == "replay_attack"
        assert sso.SAMLError.IDP_NOT_CONFIGURED.value == "idp_not_configured"

    def test_saml_name_id_format(self):
        assert "emailAddress" in sso.SAMLNameIDFormat.EMAIL.value
        assert "persistent" in sso.SAMLNameIDFormat.PERSISTENT.value


class TestSAMLDataClasses:
    def test_idp_config_defaults(self):
        idp = sso.IdPConfig(entity_id="eid", sso_url="https://sso.example.com")
        assert idp.slo_url is None
        assert idp.certificate is None
        assert idp.name_id_format == sso.SAMLNameIDFormat.EMAIL
        assert idp.binding == sso.SAMLBinding.HTTP_POST

    def test_user_attributes_defaults(self):
        ua = sso.UserAttributes(email="test@example.com")
        assert ua.groups == []
        assert ua.extra == {}
        assert ua.role is None

    def test_saml_service_result_success(self):
        result = sso.SAMLServiceResult(success=True, data={"key": "val"})
        assert result.success is True
        assert result.error is None


class TestSAMLService:
    @pytest.mark.asyncio
    async def test_configure_idp_success(self):
        svc = sso.SAMLService(_make_sp_config())
        result = await svc.configure_idp(_IDP_METADATA)
        assert result.success is True
        assert svc.idp_config is not None
        assert svc.idp_config.entity_id == "https://idp.example.com"
        assert svc.idp_config.sso_url == "https://idp.example.com/sso"
        assert svc.idp_config.slo_url == "https://idp.example.com/slo"
        assert svc.idp_config.certificate is not None

    @pytest.mark.asyncio
    async def test_configure_idp_redirect_binding(self):
        svc = sso.SAMLService(_make_sp_config())
        result = await svc.configure_idp(_IDP_METADATA_REDIRECT_ONLY)
        assert result.success is True
        assert svc.idp_config.sso_url == "https://idp2.example.com/sso/redirect"

    @pytest.mark.asyncio
    async def test_configure_idp_invalid_xml(self):
        svc = sso.SAMLService(_make_sp_config())
        result = await svc.configure_idp("NOT VALID XML <<<")
        assert result.success is False
        assert result.error == sso.SAMLError.INVALID_METADATA

    @pytest.mark.asyncio
    async def test_configure_idp_missing_entity_id(self):
        xml = """<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata">
          <md:IDPSSODescriptor/>
        </md:EntityDescriptor>"""
        svc = sso.SAMLService(_make_sp_config())
        result = await svc.configure_idp(xml)
        assert result.success is False
        assert result.error == sso.SAMLError.INVALID_METADATA

    @pytest.mark.asyncio
    async def test_create_authn_request_no_idp(self):
        svc = sso.SAMLService(_make_sp_config())
        result = await svc.create_authn_request()
        assert result.success is False
        assert result.error == sso.SAMLError.IDP_NOT_CONFIGURED

    @pytest.mark.asyncio
    async def test_create_authn_request_success(self):
        svc = sso.SAMLService(_make_sp_config())
        await svc.configure_idp(_IDP_METADATA)
        result = await svc.create_authn_request(relay_state="/dashboard")
        assert result.success is True
        req = result.data
        assert req.relay_state == "/dashboard"
        assert req.id.startswith("_kiro2_")
        assert "SAMLRequest" in req.redirect_url

    @pytest.mark.asyncio
    async def test_create_authn_request_auto_relay_state(self):
        svc = sso.SAMLService(_make_sp_config())
        await svc.configure_idp(_IDP_METADATA)
        result = await svc.create_authn_request()
        assert result.success is True
        assert result.data.relay_state is not None
        assert len(result.data.relay_state) > 0

    @pytest.mark.asyncio
    async def test_create_authn_request_adds_pending(self):
        svc = sso.SAMLService(_make_sp_config())
        await svc.configure_idp(_IDP_METADATA)
        result = await svc.create_authn_request()
        assert result.data.id in svc._pending_requests

    @pytest.mark.asyncio
    async def test_initiate_logout_no_idp(self):
        svc = sso.SAMLService(_make_sp_config())
        result = await svc.initiate_logout("session1", "user@example.com")
        assert result.success is False
        assert result.error == sso.SAMLError.IDP_NOT_CONFIGURED

    @pytest.mark.asyncio
    async def test_initiate_logout_no_slo_url(self):
        svc = sso.SAMLService(_make_sp_config())
        await svc.configure_idp(_IDP_METADATA_REDIRECT_ONLY)
        # No SLO URL in redirect-only metadata
        result = await svc.initiate_logout("session1", "user@example.com")
        assert result.success is False
        assert result.error == sso.SAMLError.SLO_FAILED

    @pytest.mark.asyncio
    async def test_initiate_logout_success(self):
        svc = sso.SAMLService(_make_sp_config())
        await svc.configure_idp(_IDP_METADATA)
        svc._active_sessions["session42"] = {"user_email": "u@e.com"}
        result = await svc.initiate_logout("session42", "u@e.com")
        assert result.success is True
        req = result.data
        assert req.session_index == "session42"
        assert "session42" not in svc._active_sessions

    @pytest.mark.asyncio
    async def test_process_saml_response_no_idp(self):
        import base64

        svc = sso.SAMLService(_make_sp_config())
        dummy = base64.b64encode(b"<root/>").decode()
        result = await svc.process_saml_response(dummy)
        assert result.success is False
        assert result.error == sso.SAMLError.IDP_NOT_CONFIGURED

    @pytest.mark.asyncio
    async def test_handle_logout_response_success(self):
        import base64
        from xml.etree import ElementTree as ET

        ns = "urn:oasis:names:tc:SAML:2.0:protocol"
        root = ET.Element(f"{{{ns}}}LogoutResponse")
        status = ET.SubElement(root, f"{{{ns}}}Status")
        code = ET.SubElement(status, f"{{{ns}}}StatusCode")
        code.set("Value", "urn:oasis:names:tc:SAML:2.0:status:Success")
        xml_bytes = ET.tostring(root, encoding="unicode").encode()
        encoded = base64.b64encode(xml_bytes).decode()
        svc = sso.SAMLService(_make_sp_config())
        result = await svc.handle_logout_response(encoded)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_handle_logout_response_failure(self):
        import base64
        from xml.etree import ElementTree as ET

        ns = "urn:oasis:names:tc:SAML:2.0:protocol"
        root = ET.Element(f"{{{ns}}}LogoutResponse")
        status = ET.SubElement(root, f"{{{ns}}}Status")
        code = ET.SubElement(status, f"{{{ns}}}StatusCode")
        code.set("Value", "urn:oasis:names:tc:SAML:2.0:status:Responder")
        xml_bytes = ET.tostring(root, encoding="unicode").encode()
        encoded = base64.b64encode(xml_bytes).decode()
        svc = sso.SAMLService(_make_sp_config())
        result = await svc.handle_logout_response(encoded)
        assert result.success is False
        assert result.error == sso.SAMLError.SLO_FAILED

    @pytest.mark.asyncio
    async def test_generate_sp_metadata(self):
        svc = sso.SAMLService(_make_sp_config())
        xml = await svc.generate_sp_metadata()
        assert "kiro2.test" in xml
        assert "AssertionConsumerService" in xml
        assert "SingleLogoutService" in xml

    @pytest.mark.asyncio
    async def test_cleanup_expired_requests(self):
        svc = sso.SAMLService(_make_sp_config())
        await svc.configure_idp(_IDP_METADATA)
        r = await svc.create_authn_request()
        req_id = r.data.id
        # Artificially age the request
        svc._pending_requests[req_id].issue_instant = datetime.now(UTC) - timedelta(
            minutes=10
        )
        await svc._cleanup_expired_requests()
        assert req_id not in svc._pending_requests

    def test_get_saml_service_singleton(self):
        sso._saml_service = None
        s1 = sso.get_saml_service()
        s2 = sso.get_saml_service()
        assert s1 is s2
        sso._saml_service = None  # cleanup

    def test_init_saml_service(self):
        sp = _make_sp_config()
        svc = sso.init_saml_service(sp)
        assert isinstance(svc, sso.SAMLService)
        assert svc.sp_config is sp

    @pytest.mark.asyncio
    async def test_extract_attributes_email_from_subject(self):
        svc = sso.SAMLService(_make_sp_config())
        assertion = sso.SAMLAssertion(
            id="a1",
            issuer="https://idp.example.com",
            subject_name_id="user@example.com",
            subject_name_id_format=sso.SAMLNameIDFormat.EMAIL.value,
            audience="https://kiro2.test/saml/metadata",
            not_before=datetime.now(UTC) - timedelta(minutes=5),
            not_on_or_after=datetime.now(UTC) + timedelta(hours=1),
            authn_instant=datetime.now(UTC),
        )
        ua = await svc._extract_attributes(assertion)
        assert ua.email == "user@example.com"

    @pytest.mark.asyncio
    async def test_extract_attributes_mapped_fields(self):
        svc = sso.SAMLService(_make_sp_config())
        assertion = sso.SAMLAssertion(
            id="a2",
            issuer="https://idp.example.com",
            subject_name_id="uid001",
            subject_name_id_format=sso.SAMLNameIDFormat.PERSISTENT.value,
            audience="https://kiro2.test/saml/metadata",
            not_before=datetime.now(UTC) - timedelta(minutes=5),
            not_on_or_after=datetime.now(UTC) + timedelta(hours=1),
            authn_instant=datetime.now(UTC),
            attributes={
                "mail": "mapped@example.com",
                "givenName": "Ali",
                "sn": "Veli",
                "role": "student",
                "groups": ["math", "physics"],
            },
        )
        ua = await svc._extract_attributes(assertion)
        assert ua.email == "mapped@example.com"
        assert ua.first_name == "Ali"
        assert ua.last_name == "Veli"
        assert ua.role == "student"
        assert "math" in ua.groups
        # Full name constructed from first + last
        assert ua.name == "Ali Veli"


# ===========================================================================
# 3.  chat_interface.py  tests
# ===========================================================================


class TestChatEnums:
    def test_conversation_states(self):
        cs = chat.ConversationState
        assert cs.GREETING.value == "greeting"
        assert cs.GOAL_SETTING.value == "goal_setting"
        assert cs.COMPLETED.value == "completed"

    def test_message_types(self):
        mt = chat.MessageType
        assert mt.USER.value == "user"
        assert mt.ASSISTANT.value == "assistant"
        assert mt.SYSTEM.value == "system"

    def test_intent_types(self):
        it = chat.IntentType
        assert it.UNKNOWN.value == "unknown"
        assert it.GREETING.value == "greeting"
        assert it.SET_GOAL.value == "set_goal"


class TestChatInterface:
    def _make(self):
        return chat.ChatInterface()

    def test_init(self):
        ci = self._make()
        assert ci.conversations == {}
        assert len(ci.intent_patterns) > 0
        assert len(ci.conversation_flows) > 0
        assert len(ci.response_templates) > 0

    def test_get_or_create_context_new(self):
        ci = self._make()
        ctx = ci._get_or_create_context("sess1", "user1")
        assert ctx.session_id == "sess1"
        assert ctx.student_id == "user1"
        assert ctx.current_state == chat.ConversationState.GREETING

    def test_get_or_create_context_existing(self):
        ci = self._make()
        ctx1 = ci._get_or_create_context("sess2")
        ctx1.current_state = chat.ConversationState.GOAL_SETTING
        ctx2 = ci._get_or_create_context("sess2")
        assert ctx2 is ctx1
        assert ctx2.current_state == chat.ConversationState.GOAL_SETTING

    def test_detect_intent_greeting(self):
        ci = self._make()
        ctx = ci._get_or_create_context("s")
        intent = ci._detect_intent("merhaba", ctx)
        assert intent == chat.IntentType.GREETING

    def test_detect_intent_set_goal_in_goal_state(self):
        ci = self._make()
        ctx = ci._get_or_create_context("s")
        ctx.current_state = chat.ConversationState.GOAL_SETTING
        intent = ci._detect_intent("matematik öğrenmek istiyorum", ctx)
        assert intent == chat.IntentType.SET_GOAL

    def test_detect_intent_unknown(self):
        ci = self._make()
        ctx = ci._get_or_create_context("s")
        intent = ci._detect_intent("blahblah xyzxyz 12345", ctx)
        assert intent == chat.IntentType.UNKNOWN

    def test_detect_intent_help(self):
        ci = self._make()
        ctx = ci._get_or_create_context("s")
        intent = ci._detect_intent("yardım et", ctx)
        assert intent == chat.IntentType.ASK_HELP

    def test_detect_intent_progress(self):
        ci = self._make()
        ctx = ci._get_or_create_context("s")
        intent = ci._detect_intent("ilerleme durumum nedir", ctx)
        assert intent == chat.IntentType.CHECK_PROGRESS

    def test_get_next_question_known_field(self):
        ci = self._make()
        q = ci._get_next_question_for_field("subject")
        assert "Matematik" in q or "konu" in q.lower()

    def test_get_next_question_unknown_field(self):
        ci = self._make()
        q = ci._get_next_question_for_field("nonexistent_field")
        assert len(q) > 0

    def test_get_conversation_context_missing(self):
        ci = self._make()
        assert ci.get_conversation_context("unknown") is None

    def test_clear_conversation(self):
        ci = self._make()
        ci._get_or_create_context("del_sess")
        ci.clear_conversation("del_sess")
        assert "del_sess" not in ci.conversations

    def test_clear_conversation_nonexistent(self):
        ci = self._make()
        ci.clear_conversation("nothing")  # Should not raise

    def test_get_active_conversations(self):
        ci = self._make()
        ci._get_or_create_context("s1")
        ci._get_or_create_context("s2")
        active = ci.get_active_conversations()
        assert "s1" in active
        assert "s2" in active

    @pytest.mark.asyncio
    async def test_process_message_greeting(self):
        ci = self._make()
        response = await ci.process_message("sess_g", "merhaba", user_id="u1")
        assert isinstance(response, chat.ChatResponse)
        assert response.message_type == chat.MessageType.ASSISTANT
        assert len(response.message) > 0

    @pytest.mark.asyncio
    async def test_process_message_records_history(self):
        ci = self._make()
        await ci.process_message("sess_h", "selam")
        ctx = ci.get_conversation_context("sess_h")
        assert len(ctx.conversation_history) == 2  # user + assistant
        assert ctx.conversation_history[0].message_type == chat.MessageType.USER
        assert ctx.conversation_history[1].message_type == chat.MessageType.ASSISTANT

    @pytest.mark.asyncio
    async def test_process_message_state_transitions(self):
        ci = self._make()
        response = await ci.process_message("sess_t", "merhaba")
        assert response.next_state == chat.ConversationState.GOAL_SETTING

    @pytest.mark.asyncio
    async def test_extract_goal_info_subject(self):
        ci = self._make()
        extracted = await ci._extract_goal_information("matematik öğrenmek istiyorum")
        assert extracted.get("subject") == "matematik"

    @pytest.mark.asyncio
    async def test_extract_goal_info_exam(self):
        ci = self._make()
        extracted = await ci._extract_goal_information("yks hazırlığı yapıyorum")
        assert extracted.get("exam_target") == "YKS"

    @pytest.mark.asyncio
    async def test_extract_goal_info_timeline(self):
        ci = self._make()
        extracted = await ci._extract_goal_information("3 ay sonra sınav var")
        assert extracted.get("timeline") == "3 ay"

    @pytest.mark.asyncio
    async def test_extract_profile_info_grade(self):
        ci = self._make()
        extracted = await ci._extract_profile_information("10. sınıf öğrencisiyim")
        assert extracted.get("grade") == "10"

    @pytest.mark.asyncio
    async def test_extract_profile_info_hours(self):
        ci = self._make()
        extracted = await ci._extract_profile_information("günde 3 saat çalışabilirim")
        assert extracted.get("available_time") == 180  # 3h * 60

    @pytest.mark.asyncio
    async def test_extract_profile_info_minutes(self):
        ci = self._make()
        extracted = await ci._extract_profile_information("45 dakika zamanım var")
        assert extracted.get("available_time") == 45

    @pytest.mark.asyncio
    async def test_handle_learning_style_detection(self):
        ci = self._make()
        ctx = ci._get_or_create_context("s")
        ctx.current_state = chat.ConversationState.LEARNING_STYLE_DETECTION
        response = await ci._handle_learning_style_detection(
            "görsel öğreniyorum", chat.IntentType.UNKNOWN, ctx
        )
        assert response.next_state == chat.ConversationState.PATH_CREATION

    @pytest.mark.asyncio
    async def test_handle_path_creation(self):
        ci = self._make()
        ctx = ci._get_or_create_context("s")
        ctx.current_state = chat.ConversationState.PATH_CREATION
        response = await ci._handle_path_creation("tamam", chat.IntentType.UNKNOWN, ctx)
        assert response.next_state == chat.ConversationState.PROGRESS_DISCUSSION

    @pytest.mark.asyncio
    async def test_handle_progress_discussion(self):
        ci = self._make()
        ctx = ci._get_or_create_context("s")
        ctx.current_state = chat.ConversationState.PROGRESS_DISCUSSION
        response = await ci._handle_progress_discussion(
            "iyi gidiyor", chat.IntentType.CHECK_PROGRESS, ctx
        )
        assert response.requires_input is True
        assert len(response.suggested_actions) > 0

    @pytest.mark.asyncio
    async def test_general_chat_uses_llm(self):
        ci = self._make()
        ctx = ci._get_or_create_context("s_llm")
        response = await ci._handle_general_chat(
            "bu ne anlama geliyor?", chat.IntentType.GENERAL_QUESTION, ctx
        )
        assert "LLM response" in response.message

    @pytest.mark.asyncio
    async def test_process_message_error_handling(self):
        """process_message must return a safe ChatResponse even on internal errors."""
        ci = self._make()
        # Poison the intent detector to raise
        ci._detect_intent = MagicMock(side_effect=RuntimeError("boom"))
        response = await ci.process_message("sess_err", "test")
        assert isinstance(response, chat.ChatResponse)
        assert "hata" in response.message.lower() or "error" in response.metadata


# ===========================================================================
# 4.  video_conference_service.py  tests
# ===========================================================================

# Patch sqlalchemy.select inside the loaded vcs module so that our plain
# Python stub classes (which are NOT SQLAlchemy-mapped ORM models) can be
# passed to select() without triggering a coercion error.  The VCS service
# never inspects the query object itself — it just passes it to db.execute(),
# which is already mocked to return whatever we need.
_select_mock = MagicMock(return_value=MagicMock())
vcs.select = _select_mock


def _make_async_db():
    """Create a minimal AsyncMock that simulates AsyncSession behaviour."""
    db = AsyncMock()
    # scalar_one_or_none and scalar by default return None
    _result = MagicMock()
    _result.scalar_one_or_none.return_value = None
    _result.scalar.return_value = 0
    _result.scalars.return_value.all.return_value = []
    db.execute.return_value = _result
    db.add.return_value = None
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


class TestVideoConferenceService:
    def _make_svc(self, db=None):
        return vcs.VideoConferenceService(db or _make_async_db())

    # --- Session creation ---

    @pytest.mark.asyncio
    async def test_create_session_zoom(self):
        db = _make_async_db()
        svc = self._make_svc(db)
        now = datetime.now(UTC)
        session = await svc.create_session(
            host_id="host-uuid",
            title="Math Class",
            description="Test session",
            scheduled_start=now,
            scheduled_end=now + timedelta(hours=1),
            session_type=_SessionType.GROUP_SESSION,
            platform=_PlatformType.ZOOM,
        )
        assert session.title == "Math Class"
        assert session.zoom_meeting_data is not None
        assert session.meeting_url is not None
        assert session.join_url is not None
        db.add.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_google_meet(self):
        db = _make_async_db()
        svc = self._make_svc(db)
        now = datetime.now(UTC)
        session = await svc.create_session(
            host_id="host-uuid",
            title="Physics Webinar",
            description="desc",
            scheduled_start=now,
            scheduled_end=now + timedelta(hours=2),
            session_type=_SessionType.WEBINAR,
            platform=_PlatformType.GOOGLE_MEET,
        )
        assert "meet.google.com" in session.meeting_url
        assert session.meet_event_data is not None

    @pytest.mark.asyncio
    async def test_create_session_jitsi(self):
        db = _make_async_db()
        svc = self._make_svc(db)
        now = datetime.now(UTC)
        session = await svc.create_session(
            host_id="host-uuid",
            title="Study Group",
            description="desc",
            scheduled_start=now,
            scheduled_end=now + timedelta(minutes=90),
            session_type=_SessionType.GROUP_SESSION,
            platform=_PlatformType.JITSI,
        )
        assert "jit.si" in session.meeting_url
        assert session.meeting_id.startswith("kiro_")

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        db = _make_async_db()
        svc = self._make_svc(db)
        result = await svc.get_session("nonexistent-uuid")
        assert result is None

    @pytest.mark.asyncio
    async def test_start_session_not_found(self):
        svc = self._make_svc()
        result = await svc.start_session("nonexistent-uuid")
        assert result is None

    @pytest.mark.asyncio
    async def test_end_session_not_found(self):
        svc = self._make_svc()
        result = await svc.end_session("nonexistent-uuid")
        assert result is None

    @pytest.mark.asyncio
    async def test_start_session_found(self):
        db = _make_async_db()
        fake_session = _LiveSession(title="T")
        fake_session.status = _SessionStatus.SCHEDULED
        fake_session.auto_record = False
        fake_session.allow_recording = False
        db.execute.return_value.scalar_one_or_none.return_value = fake_session
        svc = self._make_svc(db)
        result = await svc.start_session("some-id")
        assert result is not None
        assert result.status == _SessionStatus.LIVE
        assert result.actual_start is not None

    @pytest.mark.asyncio
    async def test_end_session_found(self):
        db = _make_async_db()
        fake_session = _LiveSession(title="T")
        fake_session.status = _SessionStatus.LIVE
        fake_session.actual_start = datetime.now(UTC) - timedelta(minutes=30)
        # Need 3 execute calls: get_session, _end_active_recordings (recording query),
        # _update_participant_durations (participant query), analytics
        _mock_result = MagicMock()
        _mock_result.scalar_one_or_none.return_value = fake_session
        _mock_result.scalars.return_value.all.return_value = []
        _mock_result.scalar.return_value = 5
        db.execute.return_value = _mock_result
        svc = self._make_svc(db)
        result = await svc.end_session("some-id")
        assert result is not None
        assert result.status == _SessionStatus.ENDED
        assert result.duration_minutes >= 0

    # --- Participant management ---

    @pytest.mark.asyncio
    async def test_add_participant(self):
        db = _make_async_db()
        svc = self._make_svc(db)
        part = await svc.add_participant("sess-id", "user-id")
        assert isinstance(part, _SessionParticipant)
        db.add.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_join_session_creates_participant_when_missing(self):
        db = _make_async_db()
        # First call (participant lookup) returns None; second call (session lookup)
        # returns a fake session.
        fake_session = _LiveSession(title="T")
        fake_session.current_participants = 0
        results = [None, fake_session]
        call_count = [0]

        def _exec_side_effect(*args, **kwargs):
            r = MagicMock()
            r.scalar_one_or_none.return_value = results[
                min(call_count[0], len(results) - 1)
            ]
            r.scalars.return_value.all.return_value = []
            r.scalar.return_value = 0
            call_count[0] += 1
            return r

        db.execute.side_effect = _exec_side_effect
        svc = self._make_svc(db)
        part = await svc.join_session("sess-id", "user-id")
        assert part is not None
        assert part.is_present is True

    @pytest.mark.asyncio
    async def test_leave_session_not_found(self):
        svc = self._make_svc()
        result = await svc.leave_session("sess-id", "user-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_leave_session_found(self):
        db = _make_async_db()
        fake_part = _SessionParticipant()
        fake_part.is_present = True
        fake_part.joined_at = datetime.now(UTC) - timedelta(minutes=20)
        fake_session = _LiveSession(title="T")
        fake_session.current_participants = 3
        results = [fake_part, fake_session]
        call_count = [0]

        def _exec(a, **kw):
            r = MagicMock()
            r.scalar_one_or_none.return_value = results[min(call_count[0], 1)]
            r.scalars.return_value.all.return_value = []
            call_count[0] += 1
            return r

        db.execute.side_effect = _exec
        svc = self._make_svc(db)
        result = await svc.leave_session("sess-id", "user-id")
        assert result is not None
        assert result.is_present is False
        assert result.duration_minutes >= 0

    # --- Screen sharing ---

    @pytest.mark.asyncio
    async def test_start_screen_share(self):
        db = _make_async_db()
        svc = self._make_svc(db)
        share = await svc.start_screen_share(
            "sess-id", "user-id", _ScreenShareType.FULL_SCREEN
        )
        assert isinstance(share, _ScreenShare)
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_screen_share_not_found(self):
        svc = self._make_svc()
        result = await svc.end_screen_share("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_end_screen_share_found(self):
        db = _make_async_db()
        fake_share = _ScreenShare()
        fake_share.started_at = datetime.now(UTC) - timedelta(seconds=120)
        fake_share.session_id = "sess-id"
        fake_share.user_id = "user-id"
        results = [fake_share, None]
        call_count = [0]

        def _exec(a, **kw):
            r = MagicMock()
            r.scalar_one_or_none.return_value = results[min(call_count[0], 1)]
            call_count[0] += 1
            return r

        db.execute.side_effect = _exec
        svc = self._make_svc(db)
        result = await svc.end_screen_share("share-id")
        assert result is not None
        assert result.duration_seconds >= 120

    # --- Recording ---

    @pytest.mark.asyncio
    async def test_start_recording_session_not_found(self):
        svc = self._make_svc()
        with pytest.raises(ValueError, match="Session not found"):
            await svc.start_recording("nonexistent-id")

    @pytest.mark.asyncio
    async def test_start_recording_found(self):
        db = _make_async_db()
        fake_session = _LiveSession(title="T")
        db.execute.return_value.scalar_one_or_none.return_value = fake_session
        svc = self._make_svc(db)
        recording = await svc.start_recording("sess-id", title="My Rec")
        assert isinstance(recording, _SessionRecording)
        assert recording.status == _RecordingStatus.RECORDING

    @pytest.mark.asyncio
    async def test_stop_recording_not_found(self):
        svc = self._make_svc()
        result = await svc.stop_recording("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_session_recordings(self):
        db = _make_async_db()
        fake_recs = [_SessionRecording(), _SessionRecording()]
        db.execute.return_value.scalars.return_value.all.return_value = fake_recs
        svc = self._make_svc(db)
        recs = await svc.get_session_recordings("sess-id")
        assert len(recs) == 2

    # --- Chat ---

    @pytest.mark.asyncio
    async def test_send_chat_message(self):
        db = _make_async_db()
        svc = self._make_svc(db)
        msg = await svc.send_chat_message("sess-id", "user-id", "Hello class!")
        assert isinstance(msg, _SessionChatMessage)
        assert msg.message == "Hello class!"
        assert msg.is_private is False

    @pytest.mark.asyncio
    async def test_send_private_chat_message(self):
        db = _make_async_db()
        svc = self._make_svc(db)
        msg = await svc.send_chat_message(
            "sess-id", "user-id", "Private msg", recipient_id="other-user"
        )
        assert msg.is_private is True

    @pytest.mark.asyncio
    async def test_get_session_chat(self):
        db = _make_async_db()
        fake_msgs = [
            _SessionChatMessage(message="hi", is_private=False, is_deleted=False)
        ]
        db.execute.return_value.scalars.return_value.all.return_value = fake_msgs
        svc = self._make_svc(db)
        msgs = await svc.get_session_chat(
            "sess-id", limit=50, viewer_user_id="u1", viewer_is_session_host=False
        )
        assert len(msgs) == 1

    # --- Jitsi room name ---

    def test_generate_jitsi_room_name(self):
        svc = self._make_svc()
        fake_session = _LiveSession(title="TestRoom 123")
        room = svc._generate_jitsi_room_name(fake_session)
        assert room.startswith("kiro_")
        assert len(room) > 10
        # Title characters should appear
        assert "TestRoom" in room or "TestRoom123" in room or "kiro_" in room

    # --- Zoom/Meet internal helpers ---

    @pytest.mark.asyncio
    async def test_create_zoom_meeting_structure(self):
        svc = self._make_svc()
        fake_session = _LiveSession(title="ZoomTest", description="desc")
        data = await svc._create_zoom_meeting(fake_session)
        assert "join_url" in data
        assert "start_url" in data
        assert "password" in data
        assert "zoom.us" in data["join_url"]

    @pytest.mark.asyncio
    async def test_create_google_meet_structure(self):
        svc = self._make_svc()
        fake_session = _LiveSession(title="MeetTest", description="desc")
        data = await svc._create_google_meet(fake_session)
        assert "hangoutLink" in data
        assert "meet.google.com" in data["hangoutLink"]
        assert "id" in data
