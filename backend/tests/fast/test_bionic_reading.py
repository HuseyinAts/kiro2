from services.accessibility.bionic_reading import BionicReadingConverter


class TestBionicReading:
    def test_convert_word_length_1(self):
        assert BionicReadingConverter.convert_word("O") == "<b>O</b>"

    def test_convert_word_length_3(self):
        assert BionicReadingConverter.convert_word("Bir") == "<b>B</b>ir"

    def test_convert_word_length_4(self):
        assert BionicReadingConverter.convert_word("masa") == "<b>ma</b>sa"

    def test_convert_word_length_5(self):
        # 5 * 0.45 = 2.25 -> 2 harf
        assert BionicReadingConverter.convert_word("kalem") == "<b>ka</b>lem"

    def test_convert_word_length_7(self):
        # 7 * 0.45 = 3.15 -> 3 harf
        assert BionicReadingConverter.convert_word("merhaba") == "<b>mer</b>haba"

    def test_convert_word_with_punctuation(self):
        # Noktalama işaretleri kelimenin içine b etiketine dahil olmamalı
        assert BionicReadingConverter.convert_word("kalem,") == "<b>ka</b>lem,"
        assert BionicReadingConverter.convert_word("(merhaba)") == "(<b>mer</b>haba)"
        assert BionicReadingConverter.convert_word('"elma"') == '"<b>el</b>ma"'

    def test_convert_full_text(self):
        text = "Bu bir test metnidir."
        result = BionicReadingConverter.convert_text(text)
        # Buyuk/kucuk harf korunur: "Bu" -> <b>B</b>u, "bir" -> <b>b</b>ir
        assert "<b>B</b>u" in result
        assert "<b>b</b>ir" in result
        assert "<b>te</b>st" in result
        assert "<b>met</b>nidir." in result

    def test_convert_full_text_with_newlines(self):
        text = "İlk satır.\nİkinci satır."
        result = BionicReadingConverter.convert_text(text)
        assert "\n" in result
        assert "<b>İ</b>lk" in result
        assert "<b>İk</b>inci" in result
