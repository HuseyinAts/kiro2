from services.turkish_readability_service import TurkishReadabilityService


def test_count_syllables():
    # 2 hece
    assert TurkishReadabilityService.count_syllables("okul") == 2
    # 4 hece
    assert TurkishReadabilityService.count_syllables("psikoloji") == 4
    # 9 hece
    assert TurkishReadabilityService.count_syllables("elektroensefalografi") == 9
    # 1 hece
    assert TurkishReadabilityService.count_syllables("ve") == 1
    # 0 sesli harf ama yine de kelime (kısaltma vs.)
    assert TurkishReadabilityService.count_syllables("BYE") == 1


def test_split_sentences():
    text = "Bu birinci cümle. Bu da ikinci cümle! Peki ya üçüncü?"
    sentences = TurkishReadabilityService.split_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "Bu birinci cümle."
    assert sentences[1] == "Bu da ikinci cümle!"
    assert sentences[2] == "Peki ya üçüncü?"


def test_split_words():
    text = "Bu birinci cümle. İçinde noktalama var, değil mi?"
    words = TurkishReadabilityService.split_words(text)
    assert len(words) == 8
    assert "İçinde" in words
    assert "değil" in words


def test_analyze_text():
    # Örnek kısa metin
    # Cümleler: "Ali okula gitti." (1)
    # Kelimeler: Ali (2), okula (3), gitti (2) -> Toplam 3 kelime, 7 hece
    text = "Ali okula gitti."
    result = TurkishReadabilityService.analyze_text(text)

    assert result["syllable_count"] == 7
    assert result["word_count"] == 3
    assert result["sentence_count"] == 1

    # Ateşman = 198.825 - (40.175 * 7/3) - (2.610 * 3/1)
    # 40.175 * 2.3333333 = 93.741666
    # 2.610 * 3 = 7.83
    # 198.825 - 93.741666 - 7.83 = 97.2533... (rounded to 3 decimal places -> 97.253)
    assert result["atesman_index"] == 97.253


def test_analyze_empty_text():
    result = TurkishReadabilityService.analyze_text("   ")
    assert result["word_count"] == 0
    assert result["atesman_index"] == 0.0
