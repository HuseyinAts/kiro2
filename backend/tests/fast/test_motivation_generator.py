from services.nlp.motivation_generator import MotivationGenerator


class TestMotivationGenerator:
    def test_drop_priority(self):
        metrics = {
            "has_dropped": True,
            "recent_improvement": 10.0,  # Improvement should be ignored if dropped is True
            "streak": 5,
            "focus_subject": "Matematik",
        }
        msg = MotivationGenerator.generate_daily_message(metrics)
        # It should pick a drop template
        assert any(
            t.format(subject="Matematik") == msg
            for t in MotivationGenerator.DROP_TEMPLATES
        )

    def test_improvement_priority(self):
        metrics = {
            "has_dropped": False,
            "recent_improvement": 15.0,
            "streak": 5,
            "focus_subject": "Fizik",
            "days": 3,
        }
        msg = MotivationGenerator.generate_daily_message(metrics)
        assert any(
            t.format(subject="Fizik", improvement=15, days=3) == msg
            for t in MotivationGenerator.SUCCESS_TEMPLATES
        )

    def test_streak_priority(self):
        metrics = {
            "has_dropped": False,
            "recent_improvement": 2.0,  # Not high enough for improvement template
            "streak": 7,
        }
        msg = MotivationGenerator.generate_daily_message(metrics)
        assert any(
            t.format(streak=7) == msg for t in MotivationGenerator.STREAK_TEMPLATES
        )

    def test_neutral_fallback(self):
        metrics = {"has_dropped": False, "recent_improvement": 0.0, "streak": 1}
        msg = MotivationGenerator.generate_daily_message(metrics)
        assert msg in MotivationGenerator.NEUTRAL_TEMPLATES
