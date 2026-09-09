from algorithms.isomorphic_generator import IsomorphicGenerator


class TestIsomorphicGenerator:
    def test_name_replacement(self):
        original = {
            "content": "Ali pazara gitti.",
            "options": [{"letter": "A", "text": "Elma"}],
        }
        iso = IsomorphicGenerator.generate_isomorphic_question(original)

        # 'Ali' should be replaced
        assert "Ali" not in iso["content"]
        assert iso["is_isomorphic"] is True

    def test_number_replacement(self):
        original = {
            "content": "Mehmet 5 tane elma aldı, toplam kaç elması var?",
            "options": [{"letter": "A", "text": "5"}, {"letter": "B", "text": "10"}],
        }
        iso = IsomorphicGenerator.generate_isomorphic_question(original)

        # 'Mehmet' should be replaced
        assert "Mehmet" not in iso["content"]

        # 5 should be offset
        assert "5 tane" not in iso["content"]

        # Options should be offset
        assert iso["options"][0]["text"] != "5"
        assert iso["options"][1]["text"] != "10"
        assert iso["is_isomorphic"] is True

    def test_no_change_without_keywords(self):
        original = {
            "content": "Mustafa Kemal Atatürk 1923 yılında ne ilan etmiştir?",
            "options": [{"letter": "A", "text": "Cumhuriyet"}],
        }
        iso = IsomorphicGenerator.generate_isomorphic_question(original)

        # 1923 should not be touched since no math keywords are present
        assert "1923" in iso["content"]
        assert iso["is_isomorphic"] is True


class TestIsimGeriDonusu:
    """9 Eyl 2026: CI'da test_number_replacement ~%1 rastgele kirmiziydi.

    Kok neden: isimler sirayla degistiriliyordu; "Mehmet" -> "Ali" sonra
    dongu "Ali"ye gelince "Ali" -> "Mehmet" olabiliyordu (orijinal isim geri
    donuyordu). Tek gecis + orijinal isimleri iceremeyen havuzla bu olasilik
    sifir. 400 tohumla olculur (eski kod 400 tohumda birden fazla kez duser).
    """

    def test_orijinal_isim_hicbir_tohumda_geri_donmez(self):
        import random

        for tohum in range(400):
            random.seed(tohum)
            iso = IsomorphicGenerator.generate_isomorphic_question(
                {"content": "Mehmet ile Ali 5 tane elma aldı.", "options": []}
            )
            assert "Mehmet" not in iso["content"], (tohum, iso["content"])
            assert "Ali" not in iso["content"], (tohum, iso["content"])
            assert "5 tane" not in iso["content"], (tohum, iso["content"])

    def test_bir_sayisi_da_degisir(self):
        """max(1, 1 - offset) = 1: eksi dalinda sayi degismiyordu."""
        import random

        for tohum in range(50):
            random.seed(tohum)
            iso = IsomorphicGenerator.generate_isomorphic_question(
                {"content": "Ali 1 tane kalem aldı.", "options": []}
            )
            assert " 1 tane" not in iso["content"], (tohum, iso["content"])
