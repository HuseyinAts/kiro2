from services.nlp.osym_validator import OsymValidator


class TestOsymValidator:
    def test_valid_stem(self):
        is_valid, errors = OsymValidator.validate_question_stem(
            "Buna göre yazarın asıl anlatılmak istenen nedir?"
        )
        assert is_valid is True
        assert len(errors) == 0

    def test_banned_stem_yanlistir(self):
        is_valid, errors = OsymValidator.validate_question_stem(
            "Aşağıdakilerden hangisi yanlıştır?"
        )
        assert is_valid is False
        assert len(errors) == 1
        assert "Standart dışı soru kökü" in errors[0]

    def test_degildir_negative(self):
        is_valid, errors = OsymValidator.validate_question_stem(
            "Bu durumun sebebi aşağıdakilerden biri değildir?"
        )
        assert is_valid is False
        assert len(errors) == 1
        assert "-mez/-maz" in errors[0]

    def test_jargon_mixing_biology_in_literature(self):
        is_valid, warnings = OsymValidator.analyze_vocabulary(
            "Şiirin kök hücrelerine inmek gerekir", "edebiyat"
        )
        assert is_valid is False
        assert len(warnings) == 1
        assert "Biyoloji jargonu" in warnings[0]

    def test_jargon_mixing_chemistry_in_physics(self):
        is_valid, warnings = OsymValidator.analyze_vocabulary(
            "Bu iki kuvvetin oluşturduğu çözelti nedir?", "fizik"
        )
        assert is_valid is False
        assert len(warnings) == 1
        assert "Kimya jargonu" in warnings[0]
