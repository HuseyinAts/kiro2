from services.yks_jargon_service import YKSJargonService


def test_get_jargon_prompt_injection():
    # Fizik dersi için kısıtlama XML'i dönmeli
    fizik_prompt = YKSJargonService.get_jargon_prompt_injection("Fizik")
    assert '<jargon_isolation priority="critical">' in fizik_prompt
    assert "iş" in fizik_prompt
    assert "kuvvet" in fizik_prompt.lower()

    # Küçük/büyük harf uyumu test edelim
    kimya_prompt = YKSJargonService.get_jargon_prompt_injection("kimya")
    assert "çözelti" in kimya_prompt

    # Tanımlı olmayan bir ders için boş dönmeli
    olmayan_prompt = YKSJargonService.get_jargon_prompt_injection("Beden Eğitimi")
    assert olmayan_prompt == ""


def test_validate_text_jargon_compliance():
    # Biyoloji'de "kök" + "denklem" ihlali
    biyoloji_text = (
        "Bitkinin kök sistemini inceleyen denklem aşağıdakilerden hangisidir?"
    )
    warnings = YKSJargonService.validate_text_jargon_compliance(
        biyoloji_text, "Biyoloji"
    )
    assert len(warnings) > 0
    assert "matematiksel veya dilbilgisi 'kök'" in warnings[0]

    # Biyolojide normal kök kullanımı ihlal sayılmamalı
    biyoloji_text_safe = "Topraktan su alan yapıya kök denir."
    warnings_safe = YKSJargonService.validate_text_jargon_compliance(
        biyoloji_text_safe, "Biyoloji"
    )
    assert len(warnings_safe) == 0

    # Fizikte iş + meslek ihlali
    fizik_text = "Bir iş yerinde çalışan işçinin yaptığı iş nedir?"
    warnings_fizik = YKSJargonService.validate_text_jargon_compliance(
        fizik_text, "Fizik"
    )
    assert len(warnings_fizik) > 0
    assert "günlük 'iş' kelimesi" in warnings_fizik[0]

    # Matematikte kök + yaprak ihlali
    matematik_text = "Denklemin bir kök değeri ağacın yaprak sayısı kadardır."
    warnings_mat = YKSJargonService.validate_text_jargon_compliance(
        matematik_text, "Matematik"
    )
    assert len(warnings_mat) > 0
    assert "biyolojik 'kök'" in warnings_mat[0]

    # Kimya'da metaforik çözelti
    kimya_text = "Bu toplumsal problem için bir çözelti bulmalıyız."
    warnings_kim = YKSJargonService.validate_text_jargon_compliance(kimya_text, "Kimya")
    assert len(warnings_kim) > 0
    assert "metaforik 'çözelti'" in warnings_kim[0]

    # Kimya'da metaforik alaşım
    kimya_alasim_text = "Farklı bir kültür alaşımı görüyoruz."
    warnings_kim_alasim = YKSJargonService.validate_text_jargon_compliance(
        kimya_alasim_text, "Kimya"
    )
    assert len(warnings_kim_alasim) > 0
    assert "sosyolojik bağlamda" in warnings_kim_alasim[0]
