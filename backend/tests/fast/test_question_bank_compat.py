"""QuestionBankItem geriye-uyumluluk katmani (STRANGLER) bekcisi.

69 alan question_bank'tan question_content / question_metadata /
question_statistics'e tasindi. Depodaki ~2400 ornek-duzeyi cagri yerini tek
seferde gocurmemek icin devrediciler kuruldu. Bu testler o katmanin
sozlesmesini civiler:

  1. Ornek duzeyi OKUMA ilgili tabloya devreder
  2. Ornek duzeyi YAZMA ilgili tabloya isler
  3. Iliskili kayit yoksa okuma None doner (cokmez)
  4. SINIF duzeyi erisim (SQL ifadesi) ACIK hata verir -- sessizce None DEGIL

(4) kasitli: `select(QuestionBankItem.irt_difficulty)` yazan 108 yer JOIN'e
cevrilmeli; sessiz None onlari gorunmez kilardi.
"""

import pytest

from models.question_bank import (
    QuestionBankItem,
    QuestionContent,
    QuestionStatistics,
)


class TestCompatDelegates:
    def test_instance_read_delegates_to_content(self):
        item = QuestionBankItem()
        item.content = QuestionContent(
            question_text="Soru metni", option_a="A şıkkı", correct_answer="B"
        )

        assert item.question_text == "Soru metni"
        assert item.option_a == "A şıkkı"
        assert item.correct_answer == "B"

    def test_instance_read_delegates_to_statistics(self):
        item = QuestionBankItem()
        item.statistics = QuestionStatistics(irt_difficulty=1.25)

        assert item.irt_difficulty == 1.25

    def test_instance_write_reaches_related_row(self):
        item = QuestionBankItem()
        item.content = QuestionContent(question_text="Eski")

        item.question_text = "Yeni"

        assert item.content.question_text == "Yeni"

    def test_missing_relation_reads_none_without_crashing(self):
        # İlişkili kayıt yüklenmemiş/yok — çökmemeli, None dönmeli.
        assert QuestionBankItem().question_text is None
        assert QuestionBankItem().irt_difficulty is None

    def test_write_without_relation_raises_actionable_error(self):
        item = QuestionBankItem()
        with pytest.raises(
            AttributeError, match="önce o ilişkili kaydı|once o iliskili"
        ):
            item.question_text = "X"

    @pytest.mark.parametrize(
        "field", ["question_text", "correct_answer", "irt_difficulty", "exam_type"]
    )
    def test_class_level_access_raises_not_silently_none(self, field):
        """SQL ifadesi olarak kullanim ACIK hata vermeli.

        Sessiz None, 108 JOIN'e cevrilmesi gereken yeri gizlerdi.
        """
        with pytest.raises(AttributeError, match="sinif duzeyinde kullanilamaz"):
            getattr(QuestionBankItem, field)

    def test_real_columns_are_not_shadowed(self):
        """Gercek 12 kolon devrediciyle ezilmemeli (sinif duzeyi calismali)."""
        for real_column in ("id", "is_active", "primary_topic_id", "soru_hash"):
            assert QuestionBankItem.__table__.columns.get(real_column) is not None
            # Kolon sinif duzeyinde SQL ifadesi olarak kullanilabilmeli
            assert getattr(QuestionBankItem, real_column) is not None
