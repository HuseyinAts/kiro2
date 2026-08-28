"""Birim testleri — veli paneli KPI toplama yardımcıları (DB'siz).

`services.parent_service` içindeki saf fonksiyonları sentetik
ExamSession / StudentAnswer / WeeklyGoal benzeri nesnelerle test eder.
Gerçek DB / engine gerekmez; matematik birebir doğrulanır.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from services.parent_service import (
    classify_subjects,
    compute_current_streak,
    compute_exams_delta,
    compute_net_change,
    compute_plan_adherence,
    compute_recent_exams,
    compute_solved_delta,
    compute_weekly_activity,
)

NOW = datetime(2026, 7, 26, 12, 0, 0, tzinfo=UTC)


def _exam(
    days_ago: float, raw_score: float, minutes: int = 60, exam_type=None, name=None
):
    """Hafif ExamSession sahtesi."""
    return SimpleNamespace(
        completed_at=NOW - timedelta(days=days_ago),
        raw_score=raw_score,
        duration_minutes=minutes,
        exam_type=exam_type,
        exam_name=name,
    )


# ---------------------------------------------------------------------------
# compute_recent_exams
# ---------------------------------------------------------------------------
def test_recent_exams_orders_newest_first_and_limits():
    exams = [_exam(10, 40.0), _exam(1, 90.0), _exam(5, 70.0), _exam(20, 10.0)]
    out = compute_recent_exams(exams, limit=3)
    assert len(out) == 3
    # En yeni (1 gün önce) ilk sırada olmalı
    assert out[0]["score"] == 90.0
    assert out[1]["score"] == 70.0
    assert out[2]["score"] == 40.0
    # date alanı gerçek completed_at datetime'ı
    assert out[0]["date"] == NOW - timedelta(days=1)


def test_recent_exams_includes_type_and_name_when_present():
    enum_like = SimpleNamespace(value="tyt")
    exams = [_exam(1, 50.0, exam_type=enum_like, name="TYT Deneme 1")]
    out = compute_recent_exams(exams)
    assert out[0]["type"] == "tyt"
    assert out[0]["name"] == "TYT Deneme 1"


def test_recent_exams_skips_incomplete_and_rounds_score():
    incomplete = SimpleNamespace(
        completed_at=None,
        raw_score=99.0,
        duration_minutes=0,
        exam_type=None,
        exam_name=None,
    )
    exams = [incomplete, _exam(2, 33.333)]
    out = compute_recent_exams(exams)
    assert len(out) == 1
    assert out[0]["score"] == 33.33


# ---------------------------------------------------------------------------
# compute_weekly_activity
# ---------------------------------------------------------------------------
def test_weekly_activity_has_seven_buckets_ordered_old_to_new():
    activity, hours = compute_weekly_activity([], NOW)
    assert len(activity) == 7
    dates = [a["date"] for a in activity]
    assert dates == sorted(dates)  # eski→yeni
    assert dates[-1] == NOW.date().isoformat()  # son kova bugün
    assert hours == 0.0
    assert all(a["minutes"] == 0 for a in activity)


def test_weekly_activity_buckets_minutes_by_day_and_totals_hours():
    exams = [
        _exam(0, 50.0, minutes=30),  # bugün
        _exam(0, 60.0, minutes=90),  # bugün (aynı gün toplanır)
        _exam(2, 40.0, minutes=60),  # 2 gün önce
        _exam(30, 10.0, minutes=120),  # pencere dışı → sayılmaz
    ]
    activity, hours = compute_weekly_activity(exams, NOW)
    by_date = {a["date"]: a["minutes"] for a in activity}
    assert by_date[NOW.date().isoformat()] == 120  # 30 + 90
    assert by_date[(NOW - timedelta(days=2)).date().isoformat()] == 60
    # Toplam pencere içi dakika = 120 + 60 = 180 → 3.0 saat
    assert hours == 3.0


# ---------------------------------------------------------------------------
# compute_net_change
# ---------------------------------------------------------------------------
def test_net_change_zero_when_fewer_than_two_exams():
    assert compute_net_change([]) == 0.0
    assert compute_net_change([_exam(1, 50.0)]) == 0.0


def test_net_change_positive_when_recent_half_improves():
    # eski→yeni skorlar: 40, 60 → yeni yarı (60) - eski yarı (40) = +20
    exams = [_exam(10, 40.0), _exam(1, 60.0)]
    assert compute_net_change(exams) == 20.0


def test_net_change_negative_when_recent_half_declines():
    exams = [_exam(10, 80.0), _exam(1, 50.0)]
    assert compute_net_change(exams) == -30.0


def test_net_change_odd_count_puts_middle_in_recent_half():
    # eski→yeni: 30, 60, 90. half=1 → önceki=[30], yeni=[60,90] ort=75
    # net = 75 - 30 = 45
    exams = [_exam(9, 30.0), _exam(5, 60.0), _exam(1, 90.0)]
    assert compute_net_change(exams) == 45.0


# ---------------------------------------------------------------------------
# compute_current_streak
# ---------------------------------------------------------------------------
def test_streak_counts_consecutive_days_ending_today():
    exams = [_exam(0, 1.0), _exam(1, 1.0), _exam(2, 1.0)]
    assert compute_current_streak(exams, NOW) == 3


def test_streak_zero_when_today_missing():
    # bugün aktivite yok → seri 0 (bugünde biter tanımı)
    exams = [_exam(1, 1.0), _exam(2, 1.0)]
    assert compute_current_streak(exams, NOW) == 0


def test_streak_breaks_on_gap():
    # bugün + dün var, 2 gün önce yok, 3 gün önce var → seri = 2
    exams = [_exam(0, 1.0), _exam(1, 1.0), _exam(3, 1.0)]
    assert compute_current_streak(exams, NOW) == 2


def test_streak_dedupes_multiple_exams_same_day():
    exams = [_exam(0, 1.0), _exam(0, 1.0), _exam(1, 1.0)]
    assert compute_current_streak(exams, NOW) == 2


# ---------------------------------------------------------------------------
# compute_exams_delta / compute_solved_delta (kayan 7 günlük pencereler)
# ---------------------------------------------------------------------------
def test_exams_delta_this_week_minus_last_week():
    exams = [
        _exam(1, 1.0),  # bu hafta
        _exam(3, 1.0),  # bu hafta
        _exam(9, 1.0),  # geçen hafta
    ]
    # bu hafta 2 - geçen hafta 1 = +1
    assert compute_exams_delta(exams, NOW) == 1


def test_solved_delta_uses_answered_dates():
    dates = [
        NOW - timedelta(days=2),  # bu hafta
        NOW - timedelta(days=4),  # bu hafta
        NOW - timedelta(days=10),  # geçen hafta
        NOW - timedelta(days=20),  # iki pencere dışı
    ]
    # bu hafta 2 - geçen hafta 1 = +1
    assert compute_solved_delta(dates, NOW) == 1


def test_window_boundary_excludes_older_than_14_days():
    dates = [NOW - timedelta(days=13, hours=23), NOW - timedelta(days=15)]
    # ilki geçen hafta içinde (>14g değil), ikincisi dışında
    assert compute_solved_delta(dates, NOW) == -1  # 0 bu hafta - 1 geçen hafta


# ---------------------------------------------------------------------------
# classify_subjects
# ---------------------------------------------------------------------------
def test_classify_subjects_weak_strong_and_progress():
    stats = [
        ("MATEMATIK", 2, 10),  # %20 → zayıf
        ("TURKCE", 8, 10),  # %80 → güçlü
        ("FIZIK", 6, 10),  # %60 → ne zayıf ne güçlü
    ]
    weak, strong, progress = classify_subjects(stats)
    assert weak == ["MATEMATIK"]
    assert strong == ["TURKCE"]
    # progress mastery'ye göre azalan sıralı
    assert [p["subject"] for p in progress] == ["TURKCE", "FIZIK", "MATEMATIK"]
    assert progress[0]["mastery"] == 80.0
    assert progress[2]["answered"] == 10


def test_classify_subjects_ignores_low_sample_subjects():
    stats = [("KIMYA", 0, 2)]  # total < min_questions (3) → dahil edilmez
    weak, strong, progress = classify_subjects(stats)
    assert weak == []
    assert strong == []
    assert progress == []


def test_classify_subjects_weak_sorted_worst_first_and_capped():
    stats = [
        ("A", 1, 10),  # %10
        ("B", 2, 10),  # %20
        ("C", 3, 10),  # %30
        ("D", 4, 10),  # %40
    ]
    weak, _, _ = classify_subjects(stats, top_n=3)
    assert weak == ["A", "B", "C"]  # en kötü 3, artan doğrulukla


# ---------------------------------------------------------------------------
# compute_plan_adherence
# ---------------------------------------------------------------------------
def _goal(tq=0, cq=0, tr=0, cr=0):
    return SimpleNamespace(
        target_questions=tq,
        completed_questions=cq,
        target_reviews=tr,
        completed_reviews=cr,
    )


def test_plan_adherence_none_when_no_targets():
    assert compute_plan_adherence([]) is None
    assert compute_plan_adherence([_goal(tq=0, cq=0)]) is None


def test_plan_adherence_percentage_of_completed_over_target():
    goals = [_goal(tq=50, cq=25, tr=10, cr=5), _goal(tq=40, cq=40)]
    # done = (25+5) + 40 = 70 ; target = (50+10) + 40 = 100 → %70
    assert compute_plan_adherence(goals) == 70.0


def test_plan_adherence_capped_at_100():
    goals = [_goal(tq=10, cq=25)]  # aşırı tamamlama → %100 tavan
    assert compute_plan_adherence(goals) == 100.0
