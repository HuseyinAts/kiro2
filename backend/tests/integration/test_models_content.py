"""
Models Test - Basitleştirilmiş Versiyon
"""

import sys
from pathlib import Path

import pytest

# Backend klasörünü path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import ContentType, MakaleIcerik, VideoIcerik


# MakaleIcerik Testleri
def test_makale_icerik_creation():
    """MakaleIcerik modelinin oluşturulması"""
    makale = MakaleIcerik(
        baslik="Python Programlama",
        icerik="Python öğrenme içeriği burada yer alacak. Bu içerik programlama konularını kapsamlı şekilde anlatmaktadır.",
        yazar="Test Yazar",
        kategori="Programlama",
        okunma_suresi=15,
    )

    assert makale.baslik == "Python Programlama"
    assert isinstance(makale.okunma_suresi, int)
    assert makale.okunma_suresi >= 1  # auto-calculated from content length
    assert makale.aktif == True
    assert makale.goruntuleme_sayisi == 0


def test_makale_with_tags():
    """Etiketli makale oluşturma"""
    makale = MakaleIcerik(
        baslik="Web Development",
        icerik="HTML, CSS ve JavaScript öğreniyoruz. Web geliştirme temelleri için kapsamlı bir eğitim içeriği sunulmaktadır.",
        yazar="Developer",
        kategori="Web",
        okunma_suresi=20,
        etiketler=["HTML", "CSS", "JavaScript"],
    )

    # Etiketler lowercase olmalı
    assert makale.etiketler == ["html", "css", "javascript"]


def test_makale_validation_errors():
    """MakaleIcerik validasyon hataları"""
    with pytest.raises(ValueError):
        # Kısa başlık
        MakaleIcerik(
            baslik="AB",  # Min 3 karakter
            icerik="Test içerik",
            yazar="Test",
            kategori="Test",
            okunma_suresi=5,
        )


def test_makale_too_many_tags():
    """Çok fazla etiket kontrolü"""
    with pytest.raises(ValueError):
        MakaleIcerik(
            baslik="Test Makale",
            icerik="Test içeriği",
            yazar="Test",
            kategori="Test",
            okunma_suresi=5,
            etiketler=["tag" + str(i) for i in range(15)],  # Max 10 etiket
        )


# VideoIcerik Testleri
def test_video_icerik_creation():
    """VideoIcerik modelinin oluşturulması"""
    video = VideoIcerik(
        baslik="Matematik Dersi",
        video_url="https://youtube.com/watch?v=abc123",
        aciklama="Matematik dersi video açıklaması",
        sure=600,  # 10 dakika
        kategori="Matematik",
        yayinlayan="Öğretmen",
    )

    assert video.baslik == "Matematik Dersi"
    assert video.sure == 600
    assert video.get_duration_minutes() == 10
    assert video.izlenme_sayisi == 0


def test_video_url_validation():
    """Video URL validasyonu"""
    # Geçerli URL
    video = VideoIcerik(
        baslik="Test Video",
        video_url="https://www.youtube.com/watch?v=test",
        aciklama="Test açıklama",
        sure=300,
        kategori="Test",
        yayinlayan="Test",
    )
    assert "youtube.com" in video.video_url

    # Geçersiz URL
    with pytest.raises(ValueError):
        VideoIcerik(
            baslik="Test Video",
            video_url="https://invalid-site.com/video",
            aciklama="Test açıklama",
            sure=300,
            kategori="Test",
            yayinlayan="Test",
        )


def test_video_duration_formatting():
    """Video süre formatlama"""
    # 1 saat 30 dakika 45 saniye
    video = VideoIcerik(
        baslik="Uzun Video",
        video_url="https://youtube.com/watch?v=long",
        aciklama="Uzun video",
        sure=5445,  # 90 dakika 45 saniye
        kategori="Test",
        yayinlayan="Test",
    )

    assert video.get_duration_formatted() == "01:30:45"

    # 45 dakika 30 saniye
    video2 = VideoIcerik(
        baslik="Orta Video",
        video_url="https://youtube.com/watch?v=medium",
        aciklama="Orta video",
        sure=2730,
        kategori="Test",
        yayinlayan="Test",
    )

    assert video2.get_duration_formatted() == "45:30"


def test_video_too_long():
    """Çok uzun video kontrolü"""
    with pytest.raises(ValueError):
        VideoIcerik(
            baslik="Çok Uzun Video",
            video_url="https://youtube.com/watch?v=toolong",
            aciklama="Test",
            sure=14401,  # 4 saatten fazla
            kategori="Test",
            yayinlayan="Test",
        )


# ContentType Enum Testleri
def test_content_type_enum():
    """ContentType enum değerleri"""
    assert ContentType.MAKALE.value == "makale"
    assert ContentType.VIDEO.value == "video"
    assert ContentType.QUIZ.value == "quiz"
    assert ContentType.INFOGRAFIK.value == "infografik"


# Edge Case Testleri
def test_empty_tags_list():
    """Boş etiket listesi"""
    makale = MakaleIcerik(
        baslik="Etiketsiz Makale",
        icerik="Bu makalenin etiketi yok ama içerik en az 50 karakter olmalıdır.",
        yazar="Test",
        kategori="Test",
        okunma_suresi=5,
        etiketler=[],
    )

    assert makale.etiketler == []


def test_video_with_quality():
    """Video kalite ayarı"""
    video = VideoIcerik(
        baslik="HD Video",
        video_url="https://youtube.com/watch?v=hd",
        aciklama="HD kalitede video",
        sure=600,
        kategori="Test",
        yayinlayan="Test",
        kalite="1080p",
    )

    assert video.kalite == "1080p"


def test_makale_with_ozet():
    """Özetli makale"""
    makale = MakaleIcerik(
        baslik="Özetli Makale",
        icerik="Bu çok uzun bir makale içeriğidir ve en az 50 karakter içermelidir.",
        ozet="Kısa özet",
        yazar="Test",
        kategori="Test",
        okunma_suresi=30,
    )

    assert makale.ozet == "Kısa özet"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
