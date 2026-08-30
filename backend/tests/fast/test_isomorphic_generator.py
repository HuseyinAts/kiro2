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
