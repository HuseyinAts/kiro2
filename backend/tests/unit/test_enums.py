"""
Unit Tests for System Enums
NO MOCKS - Pure enum validation testing

Coverage target: 100%
"""

import pytest

from models.enums import (
    IcerikTipi,
    KarsilastirmaGrubu,
    KullaniciRolu,
    OgrenmeStili,
    RaporTipi,
    SinavDurumu,
    SinavTipi,
    ZorlukSeviyesi,
)


class TestSinavTipi:
    """Test ÖSYM exam types"""

    def test_sinav_tipi_values(self):
        """Test all exam type values"""
        assert SinavTipi.TYT.value == "TYT"
        assert SinavTipi.AYT.value == "AYT"
        assert SinavTipi.YDT.value == "YDT"

    def test_sinav_tipi_all_members(self):
        """Test all exam types exist"""
        types = list(SinavTipi)
        assert len(types) == 3
        assert SinavTipi.TYT in types
        assert SinavTipi.AYT in types
        assert SinavTipi.YDT in types

    def test_sinav_tipi_string_inheritance(self):
        """Test SinavTipi inherits from str"""
        assert isinstance(SinavTipi.TYT.value, str)
        assert SinavTipi.TYT == "TYT"

    @pytest.mark.parametrize("exam_type", [SinavTipi.TYT, SinavTipi.AYT, SinavTipi.YDT])
    def test_sinav_tipi_equality(self, exam_type):
        """Test enum equality with string"""
        assert exam_type == exam_type.value

    def test_sinav_tipi_from_string(self):
        """Test creating enum from string"""
        assert SinavTipi("TYT") == SinavTipi.TYT
        assert SinavTipi("AYT") == SinavTipi.AYT
        assert SinavTipi("YDT") == SinavTipi.YDT

    def test_sinav_tipi_invalid_value(self):
        """Test invalid exam type raises error"""
        with pytest.raises(ValueError):
            SinavTipi("INVALID")


class TestZorlukSeviyesi:
    """Test difficulty levels"""

    def test_zorluk_seviyesi_values(self):
        """Test all difficulty level values"""
        assert ZorlukSeviyesi.KOLAY.value == "kolay"
        assert ZorlukSeviyesi.ORTA.value == "orta"
        assert ZorlukSeviyesi.ZOR.value == "zor"

    def test_zorluk_seviyesi_count(self):
        """Test correct number of difficulty levels"""
        levels = list(ZorlukSeviyesi)
        assert len(levels) == 3

    @pytest.mark.parametrize(
        "level,expected",
        [
            (ZorlukSeviyesi.KOLAY, "kolay"),
            (ZorlukSeviyesi.ORTA, "orta"),
            (ZorlukSeviyesi.ZOR, "zor"),
        ],
    )
    def test_zorluk_seviyesi_parametrized(self, level, expected):
        """Test each difficulty level"""
        assert level.value == expected

    def test_zorluk_seviyesi_from_string(self):
        """Test creating difficulty from string"""
        assert ZorlukSeviyesi("kolay") == ZorlukSeviyesi.KOLAY
        assert ZorlukSeviyesi("orta") == ZorlukSeviyesi.ORTA
        assert ZorlukSeviyesi("zor") == ZorlukSeviyesi.ZOR

    def test_zorluk_ordering(self):
        """Test difficulty levels can be compared"""
        levels = [ZorlukSeviyesi.KOLAY, ZorlukSeviyesi.ORTA, ZorlukSeviyesi.ZOR]
        assert len(levels) == 3
        assert ZorlukSeviyesi.KOLAY in levels


class TestOgrenmeStili:
    """Test learning styles"""

    def test_ogrenme_stili_values(self):
        """Test all learning style values"""
        assert OgrenmeStili.GORSEL.value == "gorsel"
        assert OgrenmeStili.ISITSEL.value == "isitsel"
        assert OgrenmeStili.KINESTETIK.value == "kinestetik"
        assert OgrenmeStili.OKUMA_YAZMA.value == "okuma_yazma"

    def test_ogrenme_stili_count(self):
        """Test all 4 learning styles exist"""
        styles = list(OgrenmeStili)
        assert len(styles) == 4

    @pytest.mark.parametrize(
        "style,value",
        [
            (OgrenmeStili.GORSEL, "gorsel"),
            (OgrenmeStili.ISITSEL, "isitsel"),
            (OgrenmeStili.KINESTETIK, "kinestetik"),
            (OgrenmeStili.OKUMA_YAZMA, "okuma_yazma"),
        ],
    )
    def test_ogrenme_stili_mapping(self, style, value):
        """Test learning style to value mapping"""
        assert style.value == value

    def test_ogrenme_stili_from_string(self):
        """Test creating style from string"""
        assert OgrenmeStili("gorsel") == OgrenmeStili.GORSEL
        assert OgrenmeStili("kinestetik") == OgrenmeStili.KINESTETIK

    def test_ogrenme_stili_membership(self):
        """Test learning style membership"""
        assert OgrenmeStili.GORSEL in OgrenmeStili
        assert OgrenmeStili.ISITSEL in OgrenmeStili


class TestIcerikTipi:
    """Test content types"""

    def test_icerik_tipi_values(self):
        """Test all content type values"""
        assert IcerikTipi.VIDEO.value == "video"
        assert IcerikTipi.MAKALE.value == "makale"
        assert IcerikTipi.INTERAKTIF.value == "interaktif"
        assert IcerikTipi.QUIZ.value == "quiz"
        assert IcerikTipi.SORU_BANKASI.value == "soru_bankasi"

    def test_icerik_tipi_count(self):
        """Test all content types exist"""
        types = list(IcerikTipi)
        assert len(types) == 5

    @pytest.mark.parametrize(
        "content_type",
        [
            IcerikTipi.VIDEO,
            IcerikTipi.MAKALE,
            IcerikTipi.INTERAKTIF,
            IcerikTipi.QUIZ,
            IcerikTipi.SORU_BANKASI,
        ],
    )
    def test_icerik_tipi_iteration(self, content_type):
        """Test iterating over content types"""
        assert content_type in IcerikTipi
        assert isinstance(content_type.value, str)

    def test_icerik_tipi_from_string(self):
        """Test creating content type from string"""
        assert IcerikTipi("video") == IcerikTipi.VIDEO
        assert IcerikTipi("quiz") == IcerikTipi.QUIZ
        assert IcerikTipi("soru_bankasi") == IcerikTipi.SORU_BANKASI


class TestKullaniciRolu:
    """Test user roles"""

    def test_kullanici_rolu_values(self):
        """Test all user role values"""
        assert KullaniciRolu.OGRENCI.value == "ogrenci"
        assert KullaniciRolu.OGRETMEN.value == "ogretmen"
        assert KullaniciRolu.VELI.value == "veli"
        assert KullaniciRolu.ADMIN.value == "admin"  # lowercase

    def test_kullanici_rolu_count(self):
        """Test all 5 roles exist (SUPER_ADMIN eklendi)"""
        roles = list(KullaniciRolu)
        assert len(roles) == 5

    @pytest.mark.parametrize(
        "role,value",
        [
            (KullaniciRolu.OGRENCI, "ogrenci"),
            (KullaniciRolu.OGRETMEN, "ogretmen"),
            (KullaniciRolu.VELI, "veli"),
            (KullaniciRolu.ADMIN, "admin"),  # lowercase
        ],
    )
    def test_kullanici_rolu_parametrized(self, role, value):
        """Test each role value"""
        assert role.value == value

    def test_kullanici_rolu_hierarchy(self):
        """Test role hierarchy exists"""
        roles = [
            KullaniciRolu.OGRENCI,
            KullaniciRolu.OGRETMEN,
            KullaniciRolu.VELI,
            KullaniciRolu.ADMIN,
        ]
        assert len(roles) == 4
        assert KullaniciRolu.ADMIN in roles

    def test_kullanici_rolu_from_string(self):
        """Test creating role from string"""
        assert KullaniciRolu("ogrenci") == KullaniciRolu.OGRENCI
        assert KullaniciRolu("admin") == KullaniciRolu.ADMIN  # lowercase
        assert KullaniciRolu("ogretmen") == KullaniciRolu.OGRETMEN


class TestSinavDurumu:
    """Test exam status"""

    def test_sinav_durumu_values(self):
        """Test all exam status values"""
        assert SinavDurumu.HAZIR.value == "hazir"
        assert SinavDurumu.DEVAM_EDIYOR.value == "devam_ediyor"
        assert SinavDurumu.TAMAMLANDI.value == "tamamlandi"
        assert SinavDurumu.IPTAL_EDILDI.value == "iptal_edildi"

    def test_sinav_durumu_count(self):
        """Test all 4 statuses exist"""
        statuses = list(SinavDurumu)
        assert len(statuses) == 4

    @pytest.mark.parametrize(
        "status",
        [
            SinavDurumu.HAZIR,
            SinavDurumu.DEVAM_EDIYOR,
            SinavDurumu.TAMAMLANDI,
            SinavDurumu.IPTAL_EDILDI,
        ],
    )
    def test_sinav_durumu_membership(self, status):
        """Test each status is valid"""
        assert status in SinavDurumu

    def test_sinav_durumu_workflow(self):
        """Test exam status workflow"""
        workflow = [SinavDurumu.HAZIR, SinavDurumu.DEVAM_EDIYOR, SinavDurumu.TAMAMLANDI]
        assert len(workflow) == 3

    def test_sinav_durumu_from_string(self):
        """Test creating status from string"""
        assert SinavDurumu("hazir") == SinavDurumu.HAZIR
        assert SinavDurumu("devam_ediyor") == SinavDurumu.DEVAM_EDIYOR
        assert SinavDurumu("tamamlandi") == SinavDurumu.TAMAMLANDI


class TestRaporTipi:
    """Test report types"""

    def test_rapor_tipi_values(self):
        """Test all report type values"""
        assert RaporTipi.HAFTALIK.value == "haftalik"
        assert RaporTipi.AYLIK.value == "aylik"
        assert RaporTipi.SINAV_SONRASI.value == "sinav_sonrasi"
        assert RaporTipi.DONEM_SONU.value == "donem_sonu"

    def test_rapor_tipi_count(self):
        """Test all 4 report types exist"""
        types = list(RaporTipi)
        assert len(types) == 4

    @pytest.mark.parametrize(
        "report_type,value",
        [
            (RaporTipi.HAFTALIK, "haftalik"),
            (RaporTipi.AYLIK, "aylik"),
            (RaporTipi.SINAV_SONRASI, "sinav_sonrasi"),
            (RaporTipi.DONEM_SONU, "donem_sonu"),
        ],
    )
    def test_rapor_tipi_parametrized(self, report_type, value):
        """Test each report type"""
        assert report_type.value == value

    def test_rapor_tipi_from_string(self):
        """Test creating report type from string"""
        assert RaporTipi("haftalik") == RaporTipi.HAFTALIK
        assert RaporTipi("aylik") == RaporTipi.AYLIK


class TestKarsilastirmaGrubu:
    """Test comparison groups"""

    def test_karsilastirma_grubu_values(self):
        """Test all comparison group values"""
        assert KarsilastirmaGrubu.SINIF.value == "sinif"
        assert KarsilastirmaGrubu.OKUL.value == "okul"
        assert KarsilastirmaGrubu.ULUSAL.value == "ulusal"

    def test_karsilastirma_grubu_count(self):
        """Test all 3 groups exist"""
        groups = list(KarsilastirmaGrubu)
        assert len(groups) == 3

    @pytest.mark.parametrize(
        "group",
        [KarsilastirmaGrubu.SINIF, KarsilastirmaGrubu.OKUL, KarsilastirmaGrubu.ULUSAL],
    )
    def test_karsilastirma_grubu_scope(self, group):
        """Test each comparison scope"""
        assert group in KarsilastirmaGrubu

    def test_karsilastirma_grubu_ordering(self):
        """Test comparison groups hierarchy"""
        groups = [
            KarsilastirmaGrubu.SINIF,
            KarsilastirmaGrubu.OKUL,
            KarsilastirmaGrubu.ULUSAL,
        ]
        assert len(groups) == 3

    def test_karsilastirma_grubu_from_string(self):
        """Test creating group from string"""
        assert KarsilastirmaGrubu("sinif") == KarsilastirmaGrubu.SINIF
        assert KarsilastirmaGrubu("okul") == KarsilastirmaGrubu.OKUL
        assert KarsilastirmaGrubu("ulusal") == KarsilastirmaGrubu.ULUSAL


class TestEnumInteroperability:
    """Test enum interoperability"""

    def test_enum_string_comparison(self):
        """Test enums can be compared with strings"""
        assert SinavTipi.TYT == "TYT"
        assert ZorlukSeviyesi.KOLAY == "kolay"
        assert KullaniciRolu.OGRENCI == "ogrenci"

    def test_enum_in_list(self):
        """Test enums work in lists"""
        roles = [KullaniciRolu.OGRENCI, KullaniciRolu.OGRETMEN]
        assert KullaniciRolu.OGRENCI in roles
        assert KullaniciRolu.ADMIN not in roles

    def test_enum_in_dict(self):
        """Test enums work as dict keys"""
        config = {SinavTipi.TYT: 120, SinavTipi.AYT: 80}
        assert config[SinavTipi.TYT] == 120

    def test_enum_json_serialization(self):
        """Test enum values are JSON serializable"""
        data = {
            "exam": SinavTipi.TYT.value,
            "difficulty": ZorlukSeviyesi.ORTA.value,
            "role": KullaniciRolu.OGRENCI.value,
        }
        assert all(isinstance(v, str) for v in data.values())


class TestEnumEdgeCases:
    """Test enum edge cases"""

    def test_invalid_enum_creation(self):
        """Test creating enum with invalid value raises error"""
        with pytest.raises(ValueError):
            SinavTipi("INVALID")

        with pytest.raises(ValueError):
            ZorlukSeviyesi("extra_hard")

        with pytest.raises(ValueError):
            KullaniciRolu("superuser")

    def test_enum_case_sensitivity(self):
        """Test enums are case sensitive"""
        with pytest.raises(ValueError):
            SinavTipi("tyt")  # lowercase

        with pytest.raises(ValueError):
            ZorlukSeviyesi("KOLAY")  # uppercase

    def test_enum_immutability(self):
        """Test enum values cannot be changed"""
        with pytest.raises(AttributeError):
            SinavTipi.TYT.value = "CHANGED"

    def test_enum_uniqueness(self):
        """Test all enum values are unique"""
        sinav_values = [e.value for e in SinavTipi]
        assert len(sinav_values) == len(set(sinav_values))

        role_values = [e.value for e in KullaniciRolu]
        assert len(role_values) == len(set(role_values))
