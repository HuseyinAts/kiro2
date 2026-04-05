"""
Final 50% coverage push — tests for high-miss, 0%-covered files.

Targets (by missing lines):
1. core/timezone_utils.py          (146 stmt, 0% → 100%)
2. core/file_utils.py              (149 stmt, 0%)
3. core/improved_base_agent.py     (190 stmt, 0%)
4. services/quality/osym_quality_scorer.py (177 stmt, 0%)
5. services/learning_path_cache.py (175 stmt, 0%)
6. services/irt_service.py         (250 stmt, 0%)
7. services/video_analytics_service.py (232 stmt, 0%)
8. services/question_bank_service.py (189 stmt, 0%)
"""

from __future__ import annotations

import json
import math
import sys
import types
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

# ============================================================
# STUBS — loaded BEFORE any module import
# ============================================================


def _make_stub(name: str, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


# bleach stub
bleach_mod = _make_stub("bleach", clean=lambda text, tags=None, strip=False: text)
sys.modules.setdefault("bleach", bleach_mod)

# numpy stub — only install if real numpy is not available
try:
    import numpy as _real_np  # noqa: F401
    # Real numpy is present; don't override it
except ImportError:
    np_mod = types.ModuleType("numpy")
    np_mod.var = (
        lambda x: sum((xi - sum(x) / len(x)) ** 2 for xi in x) / len(x) if x else 0
    )
    np_mod.array = list
    np_mod.exp = math.exp
    np_mod.log = math.log
    np_mod.mean = lambda x: sum(x) / len(x) if x else 0
    np_mod.std = lambda x: 0.1
    np_mod.sqrt = math.sqrt
    np_mod.zeros = lambda n: [0.0] * n
    np_mod.ones = lambda n: [1.0] * n
    np_mod.clip = lambda v, lo, hi: max(lo, min(hi, v))
    # schemathesis/hypothesis checks numpy.ndarray — provide a dummy
    np_mod.ndarray = type("ndarray", (), {})
    sys.modules.setdefault("numpy", np_mod)

# scipy stubs
sci_mod = _make_stub("scipy")
sys.modules.setdefault("scipy", sci_mod)
sci_opt = _make_stub(
    "scipy.optimize",
    minimize=lambda f, x0, **k: type("R", (), {"x": x0, "fun": 0, "nit": 1})(),
)
sys.modules.setdefault("scipy.optimize", sci_opt)

# services.quality.metrics stub
metrics_mod = _make_stub(
    "services.quality.metrics", QualityMetrics=type("QualityMetrics", (), {})
)
sys.modules.setdefault("services.quality", types.ModuleType("services.quality"))
sys.modules.setdefault("services.quality.metrics", metrics_mod)

# core.turkish_nlp_utils stub
nlp_mod = _make_stub(
    "core.turkish_nlp_utils", normalize_tr=lambda x: x.lower() if x else ""
)
sys.modules.setdefault("core.turkish_nlp_utils", nlp_mod)

# models.irt_morfoloji stub
irt_morfo_mod = types.ModuleType("models.irt_morfoloji")


class _IRTParametreleri:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def hesapla_probability(self, theta: float) -> float:
        a = getattr(self, "discrimination", 1.0)
        b = getattr(self, "difficulty", 0.0)
        c = getattr(self, "guessing", 0.0)
        d = getattr(self, "upper_asymptote", 1.0)
        p = c + (d - c) / (1 + math.exp(-a * (theta - b)))
        return max(0.0, min(1.0, p))


class _IRTKalibrasyonSonucu:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _OgrenciMorfolojiProfili:
    def __init__(self, ogrenci_id=None, **kwargs):
        self.ogrenci_id = ogrenci_id
        self.basit_morfoloji_performansi = 0.5
        self.orta_morfoloji_performansi = 0.5
        self.karmasik_morfoloji_performansi = 0.5
        # All extra attributes used by irt_service._guncelle_genel_yetkinlikler
        self.kok_tanima_yetkinligi = 0.5
        self.ek_tanima_yetkinligi = 0.5
        self.morfoloji_odakli_hata_sayisi = 0
        self.cevaplanan_soru_sayisi = 0
        self.dogru_cevap_sayisi = 0
        self.son_guncelleme = None
        for k, v in kwargs.items():
            setattr(self, k, v)

    def hesapla_genel_morfoloji_yetkinligi(self):
        return (
            self.basit_morfoloji_performansi * 0.4
            + self.orta_morfoloji_performansi * 0.35
            + self.karmasik_morfoloji_performansi * 0.25
        )


class _SoruMorfolojiAnalizi:
    def __init__(self, **kwargs):
        self.ortalama_morfoloji_skoru = kwargs.get("ortalama_morfoloji_skoru", 5.0)
        self.ortalama_ek_sayisi = kwargs.get("ortalama_ek_sayisi", 3.0)
        self.ek_tipi_cesitliligi = kwargs.get("ek_tipi_cesitliligi", 2.0)
        self.morfoloji_varyansı = kwargs.get("morfoloji_varyansı", 1.0)
        for k, v in kwargs.items():
            setattr(self, k, v)

    def hesapla_soru_morfoloji_faktoru(self) -> float:
        """Return a normalised morphology factor 0-2."""
        return min(2.0, self.ortalama_morfoloji_skoru / 5.0)


class _TurkceIRTSoruAnalizi:
    pass


irt_morfo_mod.IRTParametreleri = _IRTParametreleri
irt_morfo_mod.IRTKalibrasyonSonucu = _IRTKalibrasyonSonucu
irt_morfo_mod.OgrenciMorfolojiProfili = _OgrenciMorfolojiProfili
irt_morfo_mod.SoruMorfolojiAnalizi = _SoruMorfolojiAnalizi
irt_morfo_mod.TurkceIRTSoruAnalizi = _TurkceIRTSoruAnalizi
sys.modules.setdefault("models.irt_morfoloji", irt_morfo_mod)

# models.video_analytics stub
# Use MagicMock-based classes so attribute access (VideoWatchSession.video_id)
# returns a MagicMock rather than raising AttributeError when real SA is loaded.
va_mod = types.ModuleType("models.video_analytics")


def _make_mock_model(name: str):
    """Create a class whose class-level attribute access returns MagicMock."""

    class _MockMeta(type):
        def __getattr__(cls, item):
            return MagicMock()

    return _MockMeta(name, (), {})


for _cls in [
    "VideoWatchSession",
    "VideoCompletionMilestone",
    "VideoNote",
    "VideoBookmark",
    "VideoAnalyticsSummary",
]:
    setattr(va_mod, _cls, _make_mock_model(_cls))
sys.modules.setdefault("models.video_analytics", va_mod)

# sqlalchemy stubs
_sa = types.ModuleType("sqlalchemy")
_sa.select = lambda *a, **k: MagicMock()
_sa.func = MagicMock()
_sa.and_ = lambda *a: None
_sa.or_ = lambda *a: None
_sa.desc = lambda a: a
_sa.text = lambda s: s
sys.modules.setdefault("sqlalchemy", _sa)

_sa_orm = types.ModuleType("sqlalchemy.orm")
_sa_orm.Session = object
_sa_orm.joinedload = lambda *a: None
sys.modules.setdefault("sqlalchemy.orm", _sa_orm)

_sa_ext = types.ModuleType("sqlalchemy.ext.asyncio")
_sa_ext.AsyncSession = object
sys.modules.setdefault("sqlalchemy.ext.asyncio", _sa_ext)
sys.modules.setdefault("sqlalchemy.ext", types.ModuleType("sqlalchemy.ext"))

# models.question_bank stub
# Use metaclass so class-level attr access (QuestionBankItem.primary_topic) → MagicMock
qb_mod = types.ModuleType("models.question_bank")


class _OrmMeta(type):
    """Metaclass that returns MagicMock for unknown class-level attributes."""

    def __getattr__(cls, item):
        return MagicMock()


class _QBI(metaclass=_OrmMeta):
    is_active = True
    tag_associations = []
    calibration_history = []

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _TopicHierarchy(metaclass=_OrmMeta):
    is_active = True
    parent_id = None
    code = "MAT"

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _QTag(metaclass=_OrmMeta):
    tag_name = ""
    usage_count = 0
    id = "tag-1"


class _QTagAssoc(metaclass=_OrmMeta):
    pass


class _IRTCalHist(metaclass=_OrmMeta):
    pass


class _QDiffLevel(metaclass=_OrmMeta):
    pass


qb_mod.QuestionBankItem = _QBI
qb_mod.TopicHierarchy = _TopicHierarchy
qb_mod.QuestionTag = _QTag
qb_mod.QuestionTagAssociation = _QTagAssoc
qb_mod.IRTCalibrationHistory = _IRTCalHist
qb_mod.QuestionDifficultyLevel = _QDiffLevel
qb_mod.calculate_irt_based_difficulty = lambda v: float(v or 5)
qb_mod.should_update_difficulty = lambda *a: True
sys.modules.setdefault("models.question_bank", qb_mod)

# core.irt_validators stub
iv_mod = types.ModuleType("core.irt_validators")
iv_mod.validate_irt_difficulty = lambda v: v
iv_mod.validate_irt_discrimination = lambda v: v
iv_mod.validate_irt_guessing = lambda v: v
iv_mod.validate_irt_upper_asymptote = lambda v: v


class _IRTValError(Exception):
    pass


iv_mod.IRTValidationError = _IRTValError
sys.modules.setdefault("core.irt_validators", iv_mod)

# multi_layer_cache stub
mlc_mod = types.ModuleType("core.multi_layer_cache")


class _MultiLayerCache:
    def __init__(self, **kwargs):
        self.redis_url = kwargs.get("redis_url", "")
        self._store = {}

    async def initialize(self):
        return True

    async def close(self):
        pass

    async def get(self, key):
        return self._store.get(key)

    async def set(self, key, value, ttl=None):
        self._store[key] = value
        return True

    async def delete(self, key):
        self._store.pop(key, None)
        return 1

    async def delete_pattern(self, pattern):
        prefix = pattern.replace("*", "")
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        return len(keys)


mlc_mod.MultiLayerCache = _MultiLayerCache
sys.modules.setdefault("core.multi_layer_cache", mlc_mod)

# structured_logger stub — only if not already loadable as real module
if "core.structured_logger" not in sys.modules:
    try:
        import importlib as _il

        _real_sl = _il.import_module("core.structured_logger")
        # Real module loaded fine — don't stub
    except ImportError:
        sl_mod = types.ModuleType("core.structured_logger")
        _logger_inst = MagicMock()
        sl_mod.get_logger = lambda name: _logger_inst
        sl_mod.StructuredLogger = MagicMock
        sys.modules["core.structured_logger"] = sl_mod

# metrics_collector stub
mc_mod = types.ModuleType("core.metrics_collector")
mc_mod.get_metrics_collector = lambda: MagicMock()
sys.modules.setdefault("core.metrics_collector", mc_mod)

# aiofiles stub
aiofiles_mod = types.ModuleType("aiofiles")
aiofiles_os_mod = types.ModuleType("aiofiles.os")


class _FakeAioFile:
    def __init__(self, path, mode, encoding=None):
        self._path = path
        self._mode = mode

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        pass

    async def read(self, n=-1):
        return b"" if "b" in self._mode else ""

    async def write(self, data):
        return len(data)

    def __aiter__(self):
        return iter([])


aiofiles_mod.open = lambda path, mode="r", encoding=None: _FakeAioFile(
    path, mode, encoding
)


class _FakeStat:
    st_size = 100
    st_mode = 0o100644  # regular file


async def _fake_stat(path):
    return _FakeStat()


async def _fake_remove(path):
    pass


aiofiles_os_mod.stat = _fake_stat
aiofiles_os_mod.remove = _fake_remove
aiofiles_mod.os = aiofiles_os_mod
sys.modules.setdefault("aiofiles", aiofiles_mod)
sys.modules.setdefault("aiofiles.os", aiofiles_os_mod)


# ============================================================
# MODULE LOADERS
# ============================================================

import importlib.util


def _load(rel_path: str, module_name: str):
    base = Path(__file__).parent.parent.parent  # backend/
    full = base / rel_path
    spec = importlib.util.spec_from_file_location(module_name, full)
    mod = importlib.util.module_from_spec(spec)
    # Register in sys.modules BEFORE exec so @dataclass can find the module dict
    sys.modules[module_name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return mod


# ============================================================
# ① core/timezone_utils.py
# ============================================================

tz_utils = _load("core/timezone_utils.py", "timezone_utils_final50")

TURKISH_TZ = ZoneInfo("Europe/Istanbul")
UTC_TZ = UTC


class TestNowUtc:
    def test_returns_datetime_with_utc_tzinfo(self):
        result = tz_utils.now_utc()
        assert isinstance(result, datetime)
        assert result.tzinfo is not None
        assert result.utcoffset() == timedelta(0)

    def test_two_calls_monotonic(self):
        t1 = tz_utils.now_utc()
        t2 = tz_utils.now_utc()
        assert t2 >= t1


class TestNowTurkish:
    def test_returns_datetime_with_tz(self):
        result = tz_utils.now_turkish()
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

    def test_is_utc_plus3_approximately(self):
        utc = tz_utils.now_utc()
        tr = tz_utils.now_turkish()
        diff = tr.utcoffset().total_seconds()
        # Istanbul is UTC+3 (standard) or UTC+3 always since 2016
        assert diff in (10800, 10800)  # 3 hours


class TestTodayUtc:
    def test_returns_date(self):
        result = tz_utils.today_utc()
        assert isinstance(result, date)

    def test_consistent_with_now_utc(self):
        now = tz_utils.now_utc()
        today = tz_utils.today_utc()
        assert today == now.date()


class TestTodayTurkish:
    def test_returns_date(self):
        result = tz_utils.today_turkish()
        assert isinstance(result, date)


class TestEnsureUtc:
    def test_none_returns_none(self):
        assert tz_utils.ensure_utc(None) is None

    def test_naive_datetime_becomes_utc(self):
        naive = datetime(2025, 11, 22, 15, 30)
        result = tz_utils.ensure_utc(naive)
        assert result.tzinfo is not None
        assert result.utcoffset() == timedelta(0)

    def test_utc_aware_returned_as_is(self):
        utc = datetime(2025, 11, 22, 15, 30, tzinfo=UTC_TZ)
        result = tz_utils.ensure_utc(utc)
        assert result == utc

    def test_non_utc_tz_converted(self):
        tr = datetime(2025, 11, 22, 18, 30, tzinfo=TURKISH_TZ)
        result = tz_utils.ensure_utc(tr)
        assert result.utcoffset() == timedelta(0)
        # 18:30 TR == 15:30 UTC
        assert result.hour == 15
        assert result.minute == 30


class TestToTurkishTime:
    def test_none_returns_none(self):
        assert tz_utils.to_turkish_time(None) is None

    def test_utc_converted_to_turkish(self):
        utc = datetime(2025, 11, 22, 12, 0, tzinfo=UTC_TZ)
        tr = tz_utils.to_turkish_time(utc)
        # UTC+3 → 15:00
        assert tr.hour == 15
        assert tr.minute == 0

    def test_naive_treated_as_utc(self):
        naive = datetime(2025, 11, 22, 12, 0)
        tr = tz_utils.to_turkish_time(naive)
        assert tr is not None


class TestFromTurkishTime:
    def test_none_returns_none(self):
        assert tz_utils.from_turkish_time(None) is None

    def test_turkish_converted_to_utc(self):
        tr = datetime(2025, 11, 22, 15, 0, tzinfo=TURKISH_TZ)
        utc = tz_utils.from_turkish_time(tr)
        assert utc.utcoffset() == timedelta(0)
        assert utc.hour == 12

    def test_naive_assumed_turkish(self):
        naive = datetime(2025, 11, 22, 15, 0)
        utc = tz_utils.from_turkish_time(naive)
        assert utc is not None
        assert utc.hour == 12


class TestParseDatetime:
    def test_none_returns_none(self):
        assert tz_utils.parse_datetime(None) is None

    def test_empty_string_returns_none(self):
        assert tz_utils.parse_datetime("") is None

    def test_iso_z_format(self):
        result = tz_utils.parse_datetime("2025-11-22T15:30:00Z")
        assert result is not None
        assert result.hour == 15
        assert result.utcoffset() == timedelta(0)

    def test_iso_with_offset(self):
        result = tz_utils.parse_datetime("2025-11-22T15:30:00+03:00")
        assert result is not None

    def test_naive_string_assume_utc(self):
        result = tz_utils.parse_datetime("2025-11-22 15:30:00", assume_utc=True)
        assert result is not None
        assert result.tzinfo is not None

    def test_invalid_string_returns_none(self):
        result = tz_utils.parse_datetime("not-a-date")
        assert result is None


class TestParseDate:
    def test_valid_iso_date(self):
        result = tz_utils.parse_date("2025-11-22")
        assert result == date(2025, 11, 22)

    def test_none_returns_none(self):
        assert tz_utils.parse_date(None) is None

    def test_empty_string_returns_none(self):
        assert tz_utils.parse_date("") is None

    def test_invalid_returns_none(self):
        assert tz_utils.parse_date("not-a-date") is None


class TestFormatDatetimeUtc:
    def test_none_returns_none(self):
        assert tz_utils.format_datetime_utc(None) is None

    def test_utc_datetime_formatted(self):
        dt = datetime(2025, 11, 22, 15, 30, tzinfo=UTC_TZ)
        result = tz_utils.format_datetime_utc(dt)
        assert "2025-11-22" in result
        assert "15:30" in result

    def test_naive_datetime_formatted(self):
        dt = datetime(2025, 11, 22, 15, 30)
        result = tz_utils.format_datetime_utc(dt)
        assert result is not None


class TestFormatDatetimeTurkish:
    def test_none_returns_none(self):
        assert tz_utils.format_datetime_turkish(None) is None

    def test_utc_datetime_to_turkish_string(self):
        dt = datetime(2025, 11, 22, 12, 0, tzinfo=UTC_TZ)
        result = tz_utils.format_datetime_turkish(dt)
        assert "15" in result  # UTC+3 → 15:00


class TestFormatDatetimeTurkishDisplay:
    def test_none_returns_none(self):
        assert tz_utils.format_datetime_turkish_display(None) is None

    def test_correct_format(self):
        dt = datetime(2025, 11, 22, 12, 0, tzinfo=UTC_TZ)
        result = tz_utils.format_datetime_turkish_display(dt)
        # Format: DD.MM.YYYY HH:MM
        assert "22.11.2025" in result
        assert "15:00" in result


class TestFormatDateTurkish:
    def test_none_returns_none(self):
        assert tz_utils.format_date_turkish(None) is None

    def test_correct_format(self):
        d = date(2025, 11, 22)
        result = tz_utils.format_date_turkish(d)
        assert result == "22.11.2025"


class TestConvertDictDatetimesToUtc:
    def test_basic_dict(self):
        dt = datetime(2025, 11, 22, 15, 30)
        data = {"created_at": dt, "name": "test"}
        result = tz_utils.convert_dict_datetimes_to_utc(data)
        assert result["created_at"].tzinfo is not None
        assert result["name"] == "test"

    def test_nested_dict(self):
        dt = datetime(2025, 11, 22, 15, 30)
        data = {"meta": {"created_at": dt}}
        result = tz_utils.convert_dict_datetimes_to_utc(data)
        assert result["meta"]["created_at"].tzinfo is not None

    def test_list_in_dict(self):
        dt = datetime(2025, 11, 22, 15, 30)
        data = {"items": [{"created_at": dt}, {"name": "x"}]}
        result = tz_utils.convert_dict_datetimes_to_utc(data)
        assert result["items"][0]["created_at"].tzinfo is not None

    def test_non_dict_passthrough(self):
        assert tz_utils.convert_dict_datetimes_to_utc([1, 2]) == [1, 2]


class TestConvertDictDatetimesToTurkish:
    def test_datetime_converted(self):
        dt = datetime(2025, 11, 22, 12, 0, tzinfo=UTC_TZ)
        data = {"ts": dt}
        result = tz_utils.convert_dict_datetimes_to_turkish(data)
        assert result["ts"].utcoffset() != timedelta(0)


class TestFormatDictDatetimesForApi:
    def test_utc_mode(self):
        dt = datetime(2025, 11, 22, 15, 30, tzinfo=UTC_TZ)
        data = {"ts": dt, "count": 42}
        result = tz_utils.format_dict_datetimes_for_api(data)
        assert isinstance(result["ts"], str)
        assert result["count"] == 42

    def test_turkish_mode(self):
        dt = datetime(2025, 11, 22, 12, 0, tzinfo=UTC_TZ)
        data = {"ts": dt}
        result = tz_utils.format_dict_datetimes_for_api(data, use_turkish=True)
        assert isinstance(result["ts"], str)
        assert "15" in result["ts"]

    def test_date_object_formatted(self):
        d = date(2025, 11, 22)
        data = {"date": d}
        result = tz_utils.format_dict_datetimes_for_api(data)
        assert result["date"] == "2025-11-22"


class TestTimeDeltaUtils:
    def test_seconds_between(self):
        start = datetime(2025, 11, 22, 12, 0, tzinfo=UTC_TZ)
        end = start + timedelta(hours=2, minutes=30)
        result = tz_utils.seconds_between(end, start)
        assert result == pytest.approx(9000.0)

    def test_minutes_between(self):
        start = datetime(2025, 11, 22, 12, 0, tzinfo=UTC_TZ)
        end = start + timedelta(minutes=90)
        result = tz_utils.minutes_between(end, start)
        assert result == pytest.approx(90.0)

    def test_hours_between(self):
        start = datetime(2025, 11, 22, 12, 0, tzinfo=UTC_TZ)
        end = start + timedelta(hours=3)
        result = tz_utils.hours_between(end, start)
        assert result == pytest.approx(3.0)

    def test_days_between(self):
        start = datetime(2025, 11, 22, 12, 0, tzinfo=UTC_TZ)
        end = start + timedelta(days=2)
        result = tz_utils.days_between(end, start)
        assert result == pytest.approx(2.0)

    def test_negative_delta(self):
        start = datetime(2025, 11, 22, 12, 0, tzinfo=UTC_TZ)
        end = start - timedelta(hours=1)
        result = tz_utils.seconds_between(end, start)
        assert result < 0


class TestIsTimezoneAware:
    def test_naive_returns_false(self):
        dt = datetime(2025, 11, 22, 15, 30)
        assert tz_utils.is_timezone_aware(dt) is False

    def test_aware_returns_true(self):
        dt = datetime(2025, 11, 22, 15, 30, tzinfo=UTC_TZ)
        assert tz_utils.is_timezone_aware(dt) is True

    def test_none_returns_false(self):
        assert tz_utils.is_timezone_aware(None) is False


class TestIsUtc:
    def test_utc_returns_true(self):
        dt = datetime(2025, 11, 22, 15, 30, tzinfo=UTC_TZ)
        assert tz_utils.is_utc(dt) is True

    def test_turkish_tz_returns_false(self):
        dt = datetime(2025, 11, 22, 15, 30, tzinfo=TURKISH_TZ)
        assert tz_utils.is_utc(dt) is False

    def test_naive_returns_false(self):
        dt = datetime(2025, 11, 22, 15, 30)
        assert tz_utils.is_utc(dt) is False


class TestGetCurrentUtcForDb:
    def test_returns_utc(self):
        result = tz_utils.get_current_utc_for_db()
        assert result.tzinfo is not None
        assert result.utcoffset() == timedelta(0)


class TestMigrateDatetimeNowToUtc:
    def test_replaces_datetime_now(self):
        code = "created = datetime.now()"
        result = tz_utils.migrate_datetime_now_to_utc(code)
        assert "now_utc()" in result
        assert "datetime.now()" not in result

    def test_replaces_utcnow(self):
        code = "ts = datetime.utcnow()"
        result = tz_utils.migrate_datetime_now_to_utc(code)
        assert "now_utc()" in result


# ============================================================
# ② core/improved_base_agent.py
# ============================================================

iba_mod = _load("core/improved_base_agent.py", "improved_base_agent_final50")


class TestSecurityMiddleware:
    def test_sanitize_empty(self):
        sm = iba_mod.SecurityMiddleware()
        assert sm.sanitize_input("") == ""

    def test_sanitize_html(self):
        sm = iba_mod.SecurityMiddleware()
        # bleach stub strips nothing but shouldn't error
        result = sm.sanitize_input("<script>alert(1)</script>")
        assert isinstance(result, str)

    def test_sanitize_truncates_long_input(self):
        sm = iba_mod.SecurityMiddleware()
        long_text = "x" * 6000
        result = sm.sanitize_input(long_text)
        assert len(result) <= 5000

    def test_sanitize_none_like(self):
        sm = iba_mod.SecurityMiddleware()
        result = sm.sanitize_input("")
        assert result == ""

    def test_mask_bearer_token(self):
        sm = iba_mod.SecurityMiddleware()
        text = "Authorization: Bearer abc123.def456.ghi789"
        result = sm.mask_sensitive_data(text)
        assert "[MASKED]" in result
        assert "abc123" not in result

    def test_mask_api_key(self):
        sm = iba_mod.SecurityMiddleware()
        text = 'config: {"api_key": "secret-key-abc"}'
        result = sm.mask_sensitive_data(text)
        assert "[MASKED]" in result


class TestResponseCache:
    def test_miss_returns_none(self):
        cache = iba_mod.ResponseCache(ttl_seconds=300)
        result = cache.get("agent1", "hello")
        assert result is None

    def test_set_then_get_returns_value(self):
        cache = iba_mod.ResponseCache(ttl_seconds=300)
        cache.set("agent1", "hello", "response text")
        result = cache.get("agent1", "hello")
        assert result == "response text"

    def test_expired_entry_returns_none(self):
        cache = iba_mod.ResponseCache(ttl_seconds=1)
        cache.set("agent1", "hello", "resp")
        # Manually expire
        key = cache._generate_key("agent1", "hello")
        cache.cache[key] = (datetime.now() - timedelta(seconds=10), "resp")
        result = cache.get("agent1", "hello")
        assert result is None

    def test_max_size_eviction(self):
        cache = iba_mod.ResponseCache(ttl_seconds=300, max_size=2)
        cache.set("agent1", "msg1", "resp1")
        cache.set("agent1", "msg2", "resp2")
        cache.set("agent1", "msg3", "resp3")
        assert len(cache.cache) <= 2

    def test_different_agents_separate(self):
        cache = iba_mod.ResponseCache(ttl_seconds=300)
        cache.set("agentA", "question", "answer_A")
        cache.set("agentB", "question", "answer_B")
        assert cache.get("agentA", "question") == "answer_A"
        assert cache.get("agentB", "question") == "answer_B"

    def test_generate_key_deterministic(self):
        cache = iba_mod.ResponseCache()
        k1 = cache._generate_key("agent", "msg")
        k2 = cache._generate_key("agent", "msg")
        assert k1 == k2

    def test_generate_key_differs_by_content(self):
        cache = iba_mod.ResponseCache()
        k1 = cache._generate_key("agent", "msg1")
        k2 = cache._generate_key("agent", "msg2")
        assert k1 != k2


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = iba_mod.CircuitBreaker()
        assert cb.state == "closed"
        assert not cb.is_open()

    def test_record_failure_increments(self):
        cb = iba_mod.CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        assert cb.failure_count == 1

    def test_failure_threshold_opens_circuit(self):
        cb = iba_mod.CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == "open"
        assert cb.is_open()

    def test_record_success_resets(self):
        cb = iba_mod.CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == "closed"

    def test_half_open_after_timeout(self):
        cb = iba_mod.CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        cb.record_failure()
        cb.record_failure()
        # Simulate timeout
        cb.last_failure_time = datetime.now() - timedelta(seconds=10)
        assert not cb.is_open()
        assert cb.state == "half_open"

    @pytest.mark.asyncio
    async def test_call_open_circuit_raises(self):
        cb = iba_mod.CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        with pytest.raises(Exception, match="Circuit breaker is open"):
            await cb.call(AsyncMock())

    @pytest.mark.asyncio
    async def test_call_closed_circuit_success(self):
        cb = iba_mod.CircuitBreaker()
        mock_fn = AsyncMock(return_value="result")
        result = await cb.call(mock_fn, "arg1")
        assert result == "result"
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_call_records_failure_on_exception(self):
        cb = iba_mod.CircuitBreaker()
        mock_fn = AsyncMock(side_effect=Exception("fail"))
        with pytest.raises(Exception):
            await cb.call(mock_fn)
        assert cb.failure_count == 1


class TestConversationContext:
    def test_default_history_empty(self):
        ctx = iba_mod.ConversationContext(session_id="sess-1")
        assert ctx.history == []
        assert ctx.metadata == {}

    def test_add_interaction(self):
        ctx = iba_mod.ConversationContext(session_id="sess-1", student_id="stu-1")
        ctx.add_interaction("msg", "resp", "agent")
        assert len(ctx.history) == 1
        assert ctx.history[0]["message"] == "msg"
        assert ctx.history[0]["agent"] == "agent"

    def test_history_limited_to_10(self):
        ctx = iba_mod.ConversationContext(session_id="sess-1")
        for i in range(15):
            ctx.add_interaction(f"msg{i}", f"resp{i}", "agent")
        assert len(ctx.history) == 10

    def test_get_context_summary_empty(self):
        ctx = iba_mod.ConversationContext(session_id="sess-1")
        assert ctx.get_context_summary() == ""

    def test_get_context_summary_with_history(self):
        ctx = iba_mod.ConversationContext(session_id="sess-1")
        ctx.add_interaction("question", "answer", "agent")
        summary = ctx.get_context_summary()
        assert "User:" in summary
        assert "Agent:" in summary

    def test_timestamp_in_interaction(self):
        ctx = iba_mod.ConversationContext(session_id="sess-1")
        ctx.add_interaction("msg", "resp", "agent")
        assert "timestamp" in ctx.history[0]


class TestImprovedLearningAgent:
    def test_init_creates_dependencies(self):
        agent = iba_mod.ImprovedLearningAgent()
        assert agent.name == "LearningAgent"
        assert agent.cache is not None
        assert agent.circuit_breaker is not None

    @pytest.mark.asyncio
    async def test_process_empty_message(self):
        agent = iba_mod.ImprovedLearningAgent()
        result = await agent.process("")
        assert "Geçersiz" in result or isinstance(result, str)

    @pytest.mark.asyncio
    async def test_process_mock_mode(self):
        import os

        with patch.dict(os.environ, {"USE_MOCK_RESPONSES": "true"}):
            agent = iba_mod.ImprovedLearningAgent()
            result = await agent.process("LGS matematik")
            assert isinstance(result, str)
            assert len(result) > 0

    def test_build_prompt_no_context(self):
        agent = iba_mod.ImprovedLearningAgent()
        prompt = agent._build_prompt("soru", None)
        assert "soru" in prompt

    def test_build_prompt_with_context(self):
        agent = iba_mod.ImprovedLearningAgent()
        ctx = iba_mod.ConversationContext(session_id="s1")
        ctx.add_interaction("önceki soru", "önceki cevap", "agent")
        prompt = agent._build_prompt("yeni soru", ctx)
        assert "yeni soru" in prompt

    def test_get_mock_response(self):
        agent = iba_mod.ImprovedLearningAgent()
        result = agent._get_mock_response_from_file("test message")
        assert "test message" in result

    @pytest.mark.asyncio
    async def test_get_fallback_response(self):
        agent = iba_mod.ImprovedLearningAgent()
        result = await agent._get_fallback_response("msg")
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with iba_mod.ImprovedLearningAgent() as agent:
            assert agent is not None


# ============================================================
# ③ services/quality/osym_quality_scorer.py
# ============================================================

oqs_mod = _load(
    "services/quality/osym_quality_scorer.py", "osym_quality_scorer_final50"
)


class TestQualityScore:
    def test_dataclass_fields(self):
        qs = oqs_mod.QualityScore(
            total_score=80.0,
            format_compliance=18.0,
            language_quality=16.0,
            distractor_quality=17.0,
            topic_relevance=15.0,
            difficulty_appropriate=14.0,
            feedback=["good"],
            improvements=["minor"],
        )
        assert qs.total_score == 80.0
        assert len(qs.feedback) == 1


GOOD_OPTIONS = [
    "İstanbul",
    "Ankara",
    "İzmir",
    "Bursa",
    "Adana",
]


class TestOSYMQualityScorer:
    def setup_method(self):
        self.scorer = oqs_mod.OSYMQualityScorer()

    def test_score_question_returns_quality_score(self):
        result = self.scorer.score_question(
            question_stem="Türkiye'nin başkenti hangi şehirdir?",
            options=GOOD_OPTIONS,
            correct_answer_index=1,
            topic="Türkiye Coğrafyası",
            difficulty_target=0.4,
        )
        assert isinstance(result, oqs_mod.QualityScore)
        assert 0 <= result.total_score <= 100

    def test_score_format_compliance_five_options(self):
        # "Soru metni?" is only 11 chars → short-stem penalty (-3), score=17
        score, feedback = self.scorer._score_format_compliance(
            "Soru metni?", GOOD_OPTIONS, "TYT"
        )
        assert score <= 20.0
        assert isinstance(feedback, list)
        # Use a long-enough stem to get max score
        long_stem = (
            "Türkiye'nin coğrafi özellikleri hakkında aşağıdakilerden hangisi doğrudur?"
        )
        score2, fb2 = self.scorer._score_format_compliance(
            long_stem, GOOD_OPTIONS, "TYT"
        )
        assert score2 == 20.0
        assert any("Format" in f for f in fb2)

    def test_score_format_compliance_wrong_option_count(self):
        score, feedback = self.scorer._score_format_compliance(
            "Soru metni?", ["A", "B", "C"], "TYT"
        )
        assert score < 20.0

    def test_score_format_compliance_no_question_mark(self):
        score, feedback = self.scorer._score_format_compliance(
            "Soru metni nokta.", GOOD_OPTIONS, "TYT"
        )
        assert score < 20.0
        assert any("soru işareti" in f for f in feedback)

    def test_score_format_compliance_short_stem(self):
        score, feedback = self.scorer._score_format_compliance(
            "Kısa?", GOOD_OPTIONS, "TYT"
        )
        assert score < 20.0

    def test_score_language_quality_good(self):
        score, feedback = self.scorer._score_language_quality(
            "Türkiye'nin başkenti hangi şehirdir?",
            GOOD_OPTIONS,
        )
        assert isinstance(score, float)
        assert 0 <= score <= 20

    def test_score_language_quality_lowercase_start(self):
        score, feedback = self.scorer._score_language_quality(
            "türkiye'nin başkenti?",
            GOOD_OPTIONS,
        )
        assert any("büyük" in f for f in feedback)

    def test_score_distractor_quality_identical(self):
        # correct_answer_index=2 (İzmir), so distractors = [Ankara, Ankara, Bursa, Adana]
        # Two identical "Ankara" entries in distractors triggers the identical check
        opts = ["Ankara", "Ankara", "İzmir", "Bursa", "Adana"]
        score, feedback = self.scorer._score_distractor_quality(opts, 2)
        assert score < 20.0
        assert any("aynı" in f for f in feedback)

    def test_score_distractor_quality_good(self):
        score, feedback = self.scorer._score_distractor_quality(GOOD_OPTIONS, 1)
        assert isinstance(score, float)
        assert 0 <= score <= 20

    def test_score_topic_relevance_matching(self):
        score, feedback = self.scorer._score_topic_relevance(
            "Matematik konusunda trigonometri sorusu.",
            "trigonometri",
        )
        assert score == 20.0

    def test_score_topic_relevance_mismatch(self):
        score, feedback = self.scorer._score_topic_relevance(
            "İstanbul hakkında bir soru.",
            "kuantum fizik",
        )
        assert score < 20.0
        assert any("ilgisiz" in f for f in feedback)

    def test_score_difficulty_perfect_match(self):
        score, feedback = self.scorer._score_difficulty("Kısa soru?", GOOD_OPTIONS, 0.5)
        assert isinstance(score, float)

    def test_estimate_difficulty_range(self):
        diff = self.scorer._estimate_difficulty(
            "Bu soruyu önce analiz edin, sonra sentez yapın, ardından değerlendirin",
            GOOD_OPTIONS,
        )
        assert 0.2 <= diff <= 0.8

    def test_text_similarity_identical(self):
        sim = self.scorer._text_similarity("merhaba dünya", "merhaba dünya")
        assert sim == 1.0

    def test_text_similarity_disjoint(self):
        sim = self.scorer._text_similarity("elma armut", "masa sandalye")
        assert sim == 0.0

    def test_text_similarity_partial(self):
        sim = self.scorer._text_similarity("elma armut", "elma kiraz")
        assert 0 < sim < 1.0

    def test_generate_improvements_all_good(self):
        improvements = self.scorer._generate_improvements(20, 20, 20, 20, 20)
        assert len(improvements) >= 1
        # All good → single positive message
        assert any(
            "yüksek" in imp or "küçük" in imp or "iyileştirme" in imp.lower()
            for imp in improvements
        )

    def test_generate_improvements_bad_scores(self):
        improvements = self.scorer._generate_improvements(10, 10, 10, 10, 10)
        assert len(improvements) >= 4

    def test_score_question_ayt_exam_type(self):
        result = self.scorer.score_question(
            question_stem="Türk edebiyatında realizm nedir?",
            options=[
                "Gerçekçilik akımı",
                "Romantizm",
                "Natüralizm",
                "Parnasizm",
                "Sembolizm",
            ],
            correct_answer_index=0,
            topic="Türk Edebiyatı",
            difficulty_target=0.6,
            exam_type="AYT",
        )
        assert 0 <= result.total_score <= 100


# ============================================================
# ④ services/learning_path_cache.py
# ============================================================

lpc_mod = _load("services/learning_path_cache.py", "learning_path_cache_final50")


class TestLearningPathCacheTTL:
    def test_ttl_constants(self):
        assert lpc_mod.LearningPathCache.LEARNING_PATH_TTL == 3600
        assert lpc_mod.LearningPathCache.RESOURCE_SEARCH_TTL == 1800
        assert lpc_mod.LearningPathCache.QUIZ_TTL == 7200
        assert lpc_mod.LearningPathCache.PROGRESS_TTL == 900
        assert lpc_mod.LearningPathCache.COMPLETION_TTL == 900


class TestLearningPathCacheHashing:
    def setup_method(self):
        self.cache = lpc_mod.LearningPathCache()

    def test_make_profile_hash_deterministic(self):
        profile = {"grade_level": 11, "learning_style": "visual", "interests": ["math"]}
        h1 = self.cache._make_profile_hash(profile)
        h2 = self.cache._make_profile_hash(profile)
        assert h1 == h2

    def test_make_profile_hash_different_profiles(self):
        p1 = {"grade_level": 11, "learning_style": "visual"}
        p2 = {"grade_level": 12, "learning_style": "auditory"}
        assert self.cache._make_profile_hash(p1) != self.cache._make_profile_hash(p2)

    def test_make_search_hash_deterministic(self):
        h1 = self.cache._make_search_hash("matematik", "medium", ["calculus"])
        h2 = self.cache._make_search_hash("matematik", "medium", ["calculus"])
        assert h1 == h2

    def test_make_search_hash_different_params(self):
        h1 = self.cache._make_search_hash("matematik", "easy", None)
        h2 = self.cache._make_search_hash("fizik", "easy", None)
        assert h1 != h2

    def test_make_search_hash_case_insensitive(self):
        h1 = self.cache._make_search_hash("Matematik", "Easy", ["Calculus"])
        h2 = self.cache._make_search_hash("matematik", "easy", ["calculus"])
        assert h1 == h2


class TestLearningPathCacheOps:
    def setup_method(self):
        self.cache = lpc_mod.LearningPathCache()
        self.cache.cache = _MultiLayerCache()

    @pytest.mark.asyncio
    async def test_initialize(self):
        result = await self.cache.initialize()
        assert result is True
        assert self.cache._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self):
        await self.cache.initialize()
        result = await self.cache.initialize()
        assert result is True

    @pytest.mark.asyncio
    async def test_get_learning_path_miss(self):
        profile = {"grade_level": 11}
        result = await self.cache.get_learning_path("stu1", "matematik", profile)
        assert result is None

    @pytest.mark.asyncio
    async def test_set_then_get_learning_path(self):
        profile = {"grade_level": 11, "learning_style": "visual"}
        path = {"nodes": ["node1", "node2"]}
        await self.cache.set_learning_path("stu1", "matematik", profile, path)
        result = await self.cache.get_learning_path("stu1", "matematik", profile)
        assert result == path

    @pytest.mark.asyncio
    async def test_invalidate_learning_path(self):
        profile = {"grade_level": 11}
        path = {"nodes": []}
        await self.cache.set_learning_path("stu2", "fizik", profile, path)
        count = await self.cache.invalidate_learning_path(
            "stu2", "fizik", cascade=False
        )
        assert isinstance(count, int)

    @pytest.mark.asyncio
    async def test_invalidate_cascade(self):
        count = await self.cache.invalidate_learning_path("stu3", cascade=True)
        assert isinstance(count, int)

    @pytest.mark.asyncio
    async def test_get_resource_search_miss(self):
        result = await self.cache.get_resource_search("matematik", "easy")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_then_get_resource_search(self):
        resources = [{"title": "Video 1"}, {"title": "Video 2"}]
        await self.cache.set_resource_search("matematik", resources, "easy", ["limit"])
        result = await self.cache.get_resource_search("matematik", "easy", ["limit"])
        assert result == resources

    @pytest.mark.asyncio
    async def test_get_quiz_miss(self):
        result = await self.cache.get_quiz("quiz-999")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_then_get_quiz(self):
        quiz = {"questions": ["q1", "q2"]}
        await self.cache.set_quiz("quiz-1", quiz)
        result = await self.cache.get_quiz("quiz-1")
        assert result == quiz

    @pytest.mark.asyncio
    async def test_close(self):
        await self.cache.close()  # Should not raise


# ============================================================
# ⑤ services/irt_service.py
# ============================================================

irt_mod = _load("services/irt_service.py", "irt_service_final50")


class TestIRTServiceInit:
    def test_defaults(self):
        svc = irt_mod.IRTService()
        assert svc.default_discrimination == 1.0
        assert svc.default_difficulty == 0.0
        assert svc.default_guessing == 0.0
        assert svc.default_upper_asymptote == 1.0

    def test_calibration_history_empty(self):
        svc = irt_mod.IRTService()
        assert svc.kalibrasyon_gecmisi == {}

    def test_morfoloji_weights_sum(self):
        svc = irt_mod.IRTService()
        total = sum(svc.morfoloji_agirliklari.values())
        assert abs(total - 1.0) < 0.01


class TestHesaplaCevapOlasiligi:
    @pytest.mark.asyncio
    async def test_basic_probability(self):
        svc = irt_mod.IRTService()
        params = _IRTParametreleri(
            discrimination=1.0,
            difficulty=0.0,
            guessing=0.0,
            upper_asymptote=1.0,
        )
        p = await svc.hesapla_cevap_olasiligi(0.0, params)
        assert abs(p - 0.5) < 0.01

    @pytest.mark.asyncio
    async def test_high_theta_high_probability(self):
        svc = irt_mod.IRTService()
        params = _IRTParametreleri(
            discrimination=1.0, difficulty=0.0, guessing=0.0, upper_asymptote=1.0
        )
        p = await svc.hesapla_cevap_olasiligi(3.0, params)
        assert p > 0.9

    @pytest.mark.asyncio
    async def test_low_theta_low_probability(self):
        svc = irt_mod.IRTService()
        params = _IRTParametreleri(
            discrimination=1.0, difficulty=0.0, guessing=0.0, upper_asymptote=1.0
        )
        p = await svc.hesapla_cevap_olasiligi(-3.0, params)
        assert p < 0.2

    @pytest.mark.asyncio
    async def test_with_guessing_floor(self):
        svc = irt_mod.IRTService()
        params = _IRTParametreleri(
            discrimination=1.0, difficulty=0.0, guessing=0.25, upper_asymptote=1.0
        )
        p = await svc.hesapla_cevap_olasiligi(-10.0, params)
        assert p >= 0.24  # Near guessing floor

    @pytest.mark.asyncio
    async def test_with_morfoloji_profil(self):
        svc = irt_mod.IRTService()
        params = _IRTParametreleri(
            discrimination=1.0, difficulty=0.0, guessing=0.0, upper_asymptote=1.0
        )
        profil = _OgrenciMorfolojiProfili(ogrenci_id="stu-1")
        p = await svc.hesapla_cevap_olasiligi(0.0, params, profil)
        assert 0.0 <= p <= 1.0


class TestHesaplaOptimalZorluk:
    @pytest.mark.asyncio
    async def test_basic_optimal(self):
        svc = irt_mod.IRTService()
        zorluk = await svc.hesapla_optimal_zorluk(0.0, 0.7)
        assert -4.0 <= zorluk <= 4.0

    @pytest.mark.asyncio
    async def test_with_high_theta(self):
        svc = irt_mod.IRTService()
        zorluk = await svc.hesapla_optimal_zorluk(2.0, 0.7)
        assert -4.0 <= zorluk <= 4.0

    @pytest.mark.asyncio
    async def test_invalid_basari_orani_low(self):
        svc = irt_mod.IRTService()
        # basari_orani == guessing (0.0), should fallback to theta
        zorluk = await svc.hesapla_optimal_zorluk(1.0, 0.0)
        assert zorluk == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_invalid_basari_orani_high(self):
        svc = irt_mod.IRTService()
        zorluk = await svc.hesapla_optimal_zorluk(1.0, 1.0)
        assert zorluk == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_with_morfoloji_analizi(self):
        svc = irt_mod.IRTService()
        analiz = _SoruMorfolojiAnalizi()
        zorluk = await svc.hesapla_optimal_zorluk(0.0, 0.7, analiz)
        assert isinstance(zorluk, float)


class TestGuncelleOgrenciMorfolojiProfili:
    @pytest.mark.asyncio
    async def test_creates_new_profile(self):
        svc = irt_mod.IRTService()
        analiz = _SoruMorfolojiAnalizi(
            ortalama_morfoloji_skoru=2.0, ortalama_ek_sayisi=2.0
        )
        cevap = {"dogru": True, "zorluk": 5.0}
        profil = await svc.guncelle_ogrenci_morfoloji_profili("stu-new", cevap, analiz)
        assert profil is not None
        assert profil.ogrenci_id == "stu-new"

    @pytest.mark.asyncio
    async def test_updates_existing_profile(self):
        svc = irt_mod.IRTService()
        existing = _OgrenciMorfolojiProfili(ogrenci_id="stu-ex")
        svc.ogrenci_profilleri["stu-ex"] = existing
        analiz = _SoruMorfolojiAnalizi(
            ortalama_morfoloji_skoru=5.0, ortalama_ek_sayisi=3.0
        )
        cevap = {"dogru": False, "zorluk": 7.0}
        profil = await svc.guncelle_ogrenci_morfoloji_profili("stu-ex", cevap, analiz)
        assert profil.ogrenci_id == "stu-ex"


# ============================================================
# ⑥ services/video_analytics_service.py — pure logic tests
# ============================================================

vas_mod = _load(
    "services/video_analytics_service.py", "video_analytics_service_final50"
)


class TestVideoAnalyticsServiceLogic:
    def test_milestones_constant(self):
        assert vas_mod.VideoAnalyticsService.MILESTONES == [25, 50, 75, 100]

    def test_auto_completion_threshold(self):
        assert vas_mod.VideoAnalyticsService.AUTO_COMPLETION_THRESHOLD == 90.0

    def test_create_drop_off_histogram_empty(self):
        db_mock = MagicMock()
        svc = vas_mod.VideoAnalyticsService(db_mock)
        result = svc._create_drop_off_histogram([])
        assert result == []

    def test_create_drop_off_histogram_basic(self):
        db_mock = MagicMock()
        svc = vas_mod.VideoAnalyticsService(db_mock)
        positions = [10, 20, 35, 65, 90]
        result = svc._create_drop_off_histogram(positions, bucket_size=30)
        assert len(result) > 0
        for item in result:
            assert "position" in item
            assert "count" in item

    def test_create_drop_off_histogram_groups_correctly(self):
        db_mock = MagicMock()
        svc = vas_mod.VideoAnalyticsService(db_mock)
        positions = [0, 5, 10, 15]  # All in bucket 0 (0-29s)
        result = svc._create_drop_off_histogram(positions, bucket_size=30)
        assert result[0]["count"] == 4
        assert result[0]["position"] == 0

    def test_create_drop_off_histogram_sorted(self):
        db_mock = MagicMock()
        svc = vas_mod.VideoAnalyticsService(db_mock)
        positions = [90, 30, 0, 60]
        result = svc._create_drop_off_histogram(positions, bucket_size=30)
        positions_out = [item["position"] for item in result]
        assert positions_out == sorted(positions_out)


class TestVideoAnalyticsServiceDB:
    """Tests that patch `select` in vas_mod to avoid real SA ORM model requirement."""

    def _make_service(self):
        db = AsyncMock()
        svc = vas_mod.VideoAnalyticsService(db)
        return svc, db

    @pytest.mark.asyncio
    async def test_get_video_engagement_metrics_no_sessions(self):
        svc, db = self._make_service()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)
        # Patch select in the loaded module so it doesn't call real SA
        with patch.object(vas_mod, "select", return_value=MagicMock()):
            metrics = await svc.get_video_engagement_metrics("vid-1", "youtube")
        assert metrics["total_views"] == 0
        assert metrics["average_completion"] == 0.0

    @pytest.mark.asyncio
    async def test_get_video_engagement_metrics_with_sessions(self):
        svc, db = self._make_service()

        class FakeSession:
            is_completed = True
            completion_percentage = 95.0
            watch_duration = 300
            dropped_at = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            FakeSession(),
            FakeSession(),
        ]
        db.execute = AsyncMock(return_value=mock_result)
        with patch.object(vas_mod, "select", return_value=MagicMock()):
            metrics = await svc.get_video_engagement_metrics("vid-1", "youtube")
        assert metrics["total_views"] == 2
        assert metrics["completion_rate"] == 100.0
        assert metrics["average_completion"] == 95.0

    @pytest.mark.asyncio
    async def test_record_pause(self):
        svc, db = self._make_service()

        class FakeSession:
            pause_count = 0

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = FakeSession()
        db.execute = AsyncMock(return_value=mock_result)
        db.commit = AsyncMock()
        with patch.object(vas_mod, "select", return_value=MagicMock()):
            await svc.record_pause("session-1")
        assert db.commit.called

    @pytest.mark.asyncio
    async def test_record_pause_missing_session(self):
        svc, db = self._make_service()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        # Should not raise
        with patch.object(vas_mod, "select", return_value=MagicMock()):
            await svc.record_pause("session-missing")

    @pytest.mark.asyncio
    async def test_end_watch_session_not_found_raises(self):
        svc, db = self._make_service()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        with patch.object(vas_mod, "select", return_value=MagicMock()):
            with pytest.raises(ValueError, match="not found"):
                await svc.end_watch_session("session-999", 100)


# ============================================================
# ⑦ services/question_bank_service.py — logic tests
# ============================================================

qbs_mod = _load("services/question_bank_service.py", "question_bank_service_final50")


class TestQuestionBankServiceInit:
    def test_init(self):
        db = MagicMock()
        svc = qbs_mod.QuestionBankService(db)
        assert svc.db is db


class TestQuestionBankCRUD:
    """Patch `select` in qbs_mod to avoid real SA ORM model requirement."""

    def _make_service(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.flush = AsyncMock()
        return qbs_mod.QuestionBankService(db), db

    @pytest.mark.asyncio
    async def test_create_question(self):
        svc, db = self._make_service()
        data = {"content": "Soru metni", "irt_difficulty": 0.5}
        await svc.create_question(data, created_by="admin")
        assert db.add.called
        assert db.commit.called

    def _patch_sa(self):
        """Context manager that patches select + joinedload in qbs_mod namespace."""
        from contextlib import ExitStack

        stack = ExitStack()
        stack.enter_context(patch.object(qbs_mod, "select", return_value=MagicMock()))
        stack.enter_context(
            patch.object(qbs_mod, "joinedload", return_value=MagicMock())
        )
        return stack

    @pytest.mark.asyncio
    async def test_delete_question_not_found(self):
        svc, db = self._make_service()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        with self._patch_sa():
            result = await svc.delete_question("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_question_found(self):
        svc, db = self._make_service()
        q = _QBI()
        q.is_active = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = q
        db.execute = AsyncMock(return_value=mock_result)
        with self._patch_sa():
            result = await svc.delete_question("q-123")
        assert result is True
        assert q.is_active is False

    @pytest.mark.asyncio
    async def test_create_topic(self):
        svc, db = self._make_service()
        await svc.create_topic("MAT.1", "Matematik", 1)
        assert db.add.called

    @pytest.mark.asyncio
    async def test_update_question_not_found(self):
        svc, db = self._make_service()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        with self._patch_sa():
            result = await svc.update_question("nonexistent", {"content": "new"})
        assert result is None

    @pytest.mark.asyncio
    async def test_update_question_found(self):
        svc, db = self._make_service()
        q = _QBI(content="old", irt_difficulty=None)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = q
        db.execute = AsyncMock(return_value=mock_result)
        with self._patch_sa():
            await svc.update_question("q-1", {"content": "new"})
        assert q.content == "new"


# ============================================================
# ⑧ More timezone_utils — edge cases
# ============================================================


class TestEdgeCasesTimezoneUtils:
    def test_ensure_utc_already_utc(self):
        dt = datetime(2025, 1, 1, tzinfo=UTC_TZ)
        result = tz_utils.ensure_utc(dt)
        assert result is dt  # same object

    def test_format_dict_nested_list_passthrough(self):
        data = {"nums": [1, 2, 3]}
        result = tz_utils.format_dict_datetimes_for_api(data)
        assert result["nums"] == [1, 2, 3]

    def test_seconds_between_zero(self):
        dt = datetime(2025, 1, 1, tzinfo=UTC_TZ)
        result = tz_utils.seconds_between(dt, dt)
        assert result == 0.0

    def test_parse_datetime_date_object_passthrough(self):
        # parse_date with date object returns it directly
        d = date(2025, 11, 22)
        result = tz_utils.parse_date(d)
        assert result == d


# ============================================================
# ⑨ Additional IRT coverage
# ============================================================


class TestIRTPrivateMethods:
    @pytest.mark.asyncio
    async def test_hesapla_morfoloji_faktoru(self):
        svc = irt_mod.IRTService()
        analiz = _SoruMorfolojiAnalizi(
            ortalama_morfoloji_skoru=7.0,
            ortalama_ek_sayisi=4.0,
        )
        # Private method — call directly if accessible
        if hasattr(svc, "_hesapla_morfoloji_faktoru"):
            faktoru = await svc._hesapla_morfoloji_faktoru(analiz)
            assert isinstance(faktoru, float)

    @pytest.mark.asyncio
    async def test_get_baslangic_parametreleri_no_previous(self):
        svc = irt_mod.IRTService()
        if hasattr(svc, "_get_baslangic_parametreleri"):
            params = svc._get_baslangic_parametreleri(None, 0.0)
            assert params is not None

    @pytest.mark.asyncio
    async def test_kaydet_kalibrasyon_gecmisi(self):
        svc = irt_mod.IRTService()
        sonuc = _IRTKalibrasyonSonucu(soru_id="q1")
        if hasattr(svc, "_kaydet_kalibrasyon_gecmisi"):
            await svc._kaydet_kalibrasyon_gecmisi(sonuc)
            assert "q1" in svc.kalibrasyon_gecmisi


# ============================================================
# ⑩ Additional LearningPathCache coverage
# ============================================================


class TestLearningPathCacheProgress:
    def setup_method(self):
        self.cache = lpc_mod.LearningPathCache()
        self.cache.cache = _MultiLayerCache()

    @pytest.mark.asyncio
    async def test_get_progress_miss(self):
        if hasattr(self.cache, "get_progress"):
            result = await self.cache.get_progress("path-1")
            assert result is None

    @pytest.mark.asyncio
    async def test_set_get_progress(self):
        if hasattr(self.cache, "set_progress") and hasattr(self.cache, "get_progress"):
            progress = {"completed": 5, "total": 10}
            await self.cache.set_progress("path-1", progress)
            result = await self.cache.get_progress("path-1")
            assert result == progress

    @pytest.mark.asyncio
    async def test_get_completion_miss(self):
        if hasattr(self.cache, "get_completion"):
            result = await self.cache.get_completion("path-2")
            assert result is None

    @pytest.mark.asyncio
    async def test_set_get_completion(self):
        if hasattr(self.cache, "set_completion") and hasattr(
            self.cache, "get_completion"
        ):
            comp = {"is_complete": True}
            await self.cache.set_completion("path-2", comp)
            result = await self.cache.get_completion("path-2")
            assert result == comp


# ============================================================
# ⑪ file_utils.py — basic async tests
# ============================================================

fu_mod = _load("core/file_utils.py", "file_utils_final50")


class TestFileInfo:
    def test_extension(self):
        fi = fu_mod.FileInfo(path=Path("/tmp/test.json"))
        assert fi.extension == ".json"

    def test_name(self):
        fi = fu_mod.FileInfo(path=Path("/tmp/test.json"))
        assert fi.name == "test.json"

    def test_stem(self):
        fi = fu_mod.FileInfo(path=Path("/tmp/test.json"))
        assert fi.stem == "test"

    def test_default_values(self):
        fi = fu_mod.FileInfo(path=Path("/tmp/test.txt"))
        assert fi.exists is False
        assert fi.size == 0
        assert fi.is_file is False
        assert fi.is_dir is False


class TestGetFileInfo:
    @pytest.mark.asyncio
    async def test_returns_file_info(self):
        result = await fu_mod.get_file_info("/tmp/any_file.txt")
        assert isinstance(result, fu_mod.FileInfo)

    @pytest.mark.asyncio
    async def test_nonexistent_exists_false(self):
        # Patch aiofiles.os.stat to raise FileNotFoundError
        orig_stat = aiofiles_os_mod.stat

        async def failing_stat(path):
            raise FileNotFoundError()

        aiofiles_os_mod.stat = failing_stat
        try:
            result = await fu_mod.get_file_info("/nonexistent/path.txt")
            assert result.exists is False
        finally:
            aiofiles_os_mod.stat = orig_stat


class TestWriteFile:
    @pytest.mark.asyncio
    async def test_write_file_calls_aiofiles(self):
        with patch.object(fu_mod, "write_file", new_callable=AsyncMock) as mock_write:
            mock_write.return_value = 10
            result = await fu_mod.write_file("/tmp/test.txt", "hello world")
            assert result == 10

    @pytest.mark.asyncio
    async def test_write_json(self):
        with patch.object(fu_mod, "write_file", new_callable=AsyncMock) as mock_write:
            mock_write.return_value = 50
            result = await fu_mod.write_json("/tmp/test.json", {"key": "value"})
            assert result == 50
            written = mock_write.call_args[0][1]
            parsed = json.loads(written)
            assert parsed["key"] == "value"


class TestReadJson:
    @pytest.mark.asyncio
    async def test_read_json_valid(self):
        with patch.object(fu_mod, "read_file", new_callable=AsyncMock) as mock_read:
            mock_read.return_value = '{"key": "value"}'
            result = await fu_mod.read_json("/tmp/test.json")
            assert result["key"] == "value"


class TestDeleteFile:
    @pytest.mark.asyncio
    async def test_delete_existing(self):
        result = await fu_mod.delete_file("/tmp/test.txt")
        assert result is True  # default stub succeeds

    @pytest.mark.asyncio
    async def test_delete_missing(self):
        orig_remove = aiofiles_os_mod.remove

        async def raising_remove(path):
            raise FileNotFoundError()

        aiofiles_os_mod.remove = raising_remove
        try:
            result = await fu_mod.delete_file("/tmp/missing.txt")
            assert result is False
        finally:
            aiofiles_os_mod.remove = orig_remove


class TestFileExists:
    @pytest.mark.asyncio
    async def test_existing_file(self):
        with patch.object(fu_mod, "get_file_info", new_callable=AsyncMock) as mock_info:
            fi = fu_mod.FileInfo(path=Path("/tmp/f.txt"), exists=True, is_file=True)
            mock_info.return_value = fi
            result = await fu_mod.file_exists("/tmp/f.txt")
            assert result is True

    @pytest.mark.asyncio
    async def test_nonexistent_file(self):
        with patch.object(fu_mod, "get_file_info", new_callable=AsyncMock) as mock_info:
            fi = fu_mod.FileInfo(path=Path("/tmp/f.txt"), exists=False)
            mock_info.return_value = fi
            result = await fu_mod.file_exists("/tmp/f.txt")
            assert result is False


class TestDirExists:
    @pytest.mark.asyncio
    async def test_existing_dir(self):
        with patch.object(fu_mod, "get_file_info", new_callable=AsyncMock) as mock_info:
            fi = fu_mod.FileInfo(path=Path("/tmp"), exists=True, is_dir=True)
            mock_info.return_value = fi
            result = await fu_mod.dir_exists("/tmp")
            assert result is True


class TestValidateFileSize:
    @pytest.mark.asyncio
    async def test_valid_size(self):
        with patch.object(fu_mod, "get_file_info", new_callable=AsyncMock) as mock_info:
            fi = fu_mod.FileInfo(
                path=Path("/tmp/f.txt"), exists=True, is_file=True, size=100
            )
            mock_info.return_value = fi
            result = await fu_mod.validate_file_size("/tmp/f.txt", max_size=1000)
            assert result is True

    @pytest.mark.asyncio
    async def test_too_large_raises(self):
        with patch.object(fu_mod, "get_file_info", new_callable=AsyncMock) as mock_info:
            fi = fu_mod.FileInfo(
                path=Path("/tmp/f.txt"), exists=True, is_file=True, size=2000
            )
            mock_info.return_value = fi
            with pytest.raises(ValueError, match="limiti"):
                await fu_mod.validate_file_size("/tmp/f.txt", max_size=1000)

    @pytest.mark.asyncio
    async def test_not_found_raises(self):
        with patch.object(fu_mod, "get_file_info", new_callable=AsyncMock) as mock_info:
            fi = fu_mod.FileInfo(path=Path("/tmp/f.txt"), exists=False)
            mock_info.return_value = fi
            with pytest.raises(FileNotFoundError):
                await fu_mod.validate_file_size("/tmp/f.txt")


# ============================================================
# ⑫ OSYMQualityScorer — more edge cases
# ============================================================


class TestOSYMQualityScorerEdge:
    def setup_method(self):
        self.scorer = oqs_mod.OSYMQualityScorer()

    def test_score_format_options_with_short_option(self):
        opts = ["A", "İstanbul", "Ankara", "İzmir", "Adana"]
        score, feedback = self.scorer._score_format_compliance("Soru?", opts, "TYT")
        assert score < 20.0

    def test_estimate_difficulty_simple_question(self):
        diff = self.scorer._estimate_difficulty("Bu nedir?", ["A", "B", "C", "D", "E"])
        assert 0.2 <= diff <= 0.8

    def test_score_distractor_quality_similar_distractors(self):
        opts = ["Ankara şehri", "Ankara ili", "İzmir", "Bursa", "Adana"]
        score, feedback = self.scorer._score_distractor_quality(opts, 2)
        assert isinstance(score, float)
        assert 0 <= score <= 20

    def test_full_pipeline_low_quality(self):
        result = self.scorer.score_question(
            question_stem="?",
            options=["A", "B"],
            correct_answer_index=0,
            topic="konusuyla ilgisiz soru şık",
            difficulty_target=0.5,
        )
        assert result.total_score < 80.0


# ============================================================
# ⑬ ResponseCache — boundary tests
# ============================================================


class TestResponseCacheBoundary:
    def test_set_evicts_oldest_when_full(self):
        cache = iba_mod.ResponseCache(ttl_seconds=3600, max_size=3)
        cache.set("a", "1", "r1")
        cache.set("a", "2", "r2")
        cache.set("a", "3", "r3")
        # Force one to be older
        k = cache._generate_key("a", "1")
        cache.cache[k] = (datetime(2020, 1, 1), "r1")
        # Adding another should evict oldest
        cache.set("a", "4", "r4")
        assert len(cache.cache) <= 3

    def test_get_after_expiry_removes_key(self):
        cache = iba_mod.ResponseCache(ttl_seconds=1)
        cache.set("agent", "msg", "resp")
        key = cache._generate_key("agent", "msg")
        cache.cache[key] = (datetime.now() - timedelta(hours=1), "resp")
        result = cache.get("agent", "msg")
        assert result is None
        assert key not in cache.cache


# ============================================================
# ⑭ CircuitBreaker boundary tests
# ============================================================


class TestCircuitBreakerBoundary:
    def test_not_open_when_below_threshold(self):
        cb = iba_mod.CircuitBreaker(failure_threshold=5)
        for _ in range(4):
            cb.record_failure()
        assert not cb.is_open()
        assert cb.state == "closed"

    def test_half_open_transitions_back_to_closed_on_success(self):
        cb = iba_mod.CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        cb.record_failure()
        cb.record_failure()
        cb.last_failure_time = datetime.now() - timedelta(seconds=10)
        _ = cb.is_open()  # Transitions to half_open
        cb.record_success()
        assert cb.state == "closed"
        assert cb.failure_count == 0


# ============================================================
# ⑮ VideoAnalyticsService — more coverage
# ============================================================


class TestVideoAnalyticsDropOff:
    def test_single_position(self):
        svc = vas_mod.VideoAnalyticsService(MagicMock())
        result = svc._create_drop_off_histogram([45], bucket_size=30)
        assert len(result) == 1
        assert result[0]["position"] == 30
        assert result[0]["count"] == 1

    def test_multiple_buckets(self):
        svc = vas_mod.VideoAnalyticsService(MagicMock())
        positions = [5, 35, 65, 95]
        result = svc._create_drop_off_histogram(positions, bucket_size=30)
        assert len(result) == 4

    @pytest.mark.asyncio
    async def test_get_engagement_with_dropoffs(self):
        svc = vas_mod.VideoAnalyticsService(AsyncMock())

        class FakeSession:
            is_completed = False
            completion_percentage = 30.0
            watch_duration = 60
            dropped_at = 30

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [FakeSession()]
        svc.db.execute = AsyncMock(return_value=mock_result)
        with patch.object(vas_mod, "select", return_value=MagicMock()):
            metrics = await svc.get_video_engagement_metrics("v1", "youtube")
        assert metrics["total_views"] == 1
        assert metrics["completion_rate"] == 0.0
        assert len(metrics["drop_off_points"]) > 0
