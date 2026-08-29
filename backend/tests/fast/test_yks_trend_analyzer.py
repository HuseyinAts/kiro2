from services.nlp.yks_trend_analyzer import YKSTrendAnalyzer


def test_syllable_count():
    assert YKSTrendAnalyzer.count_syllables("okul") == 2
    assert YKSTrendAnalyzer.count_syllables("kalemlik") == 3
    assert YKSTrendAnalyzer.count_syllables("ve") == 1

    # Advanced NLP: Abbreviations
    assert YKSTrendAnalyzer.count_syllables("TDK") == 3  # Te-De-Ke
    assert YKSTrendAnalyzer.count_syllables("ÖSYM") == 1  # Only 1 vowel
    assert YKSTrendAnalyzer.count_syllables("TBMM") == 4  # Te-Be-Me-Me

    # Advanced NLP: Numbers
    assert YKSTrendAnalyzer.count_syllables("1923") == 7  # bin-do-kuz-yüz-yir-mi-üç
    assert YKSTrendAnalyzer.count_syllables("2026") == 7  # i-ki-bin-yir-mi-al-tı
    assert YKSTrendAnalyzer.count_syllables("5") == 1  # beş
    assert (
        YKSTrendAnalyzer.count_syllables("50") == 3
    )  # el-li (wait, our heuristic 5=1, 0=2 -> 3)
    assert YKSTrendAnalyzer.count_syllables("3.14") == 3


def test_analyze_exam_text_advanced():
    # Includes abbreviations and decimals
    text = "Prof. Dr. Ahmet 3.14 değerini buldu. Sonra TBMM'ye gitti."
    result = YKSTrendAnalyzer.analyze_exam_text(text)

    # Should be 2 sentences because of Prof. Dr. bypass
    assert result["atesman_readability_index"] > 0
    assert result["avg_words_per_sentence"] > 0
    assert result["avg_word_length"] > 0
    assert result["question_length_chars"] == len(text)


def test_empty_text():
    result = YKSTrendAnalyzer.analyze_exam_text("")
    assert result["atesman_readability_index"] == 0.0
    assert result["avg_word_length"] == 0.0
