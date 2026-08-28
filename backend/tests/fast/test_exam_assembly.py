from algorithms.test_assembly import YksBellCurveAssembler


class TestYksBellCurveAssembler:
    def test_calculate_difficulty_distribution(self):
        # For a 120 question TYT exam
        dist = YksBellCurveAssembler.calculate_difficulty_distribution(120)

        assert dist["cok_kolay"] == 12  # 10%
        assert dist["kolay"] == 24  # 20%
        assert dist["orta"] == 48  # 40%
        assert dist["zor"] == 24  # 20%
        assert dist["cok_zor"] == 12  # 10%
        assert sum(dist.values()) == 120

    def test_calculate_difficulty_distribution_odd_numbers(self):
        # Test for 40 questions (Math test)
        dist = YksBellCurveAssembler.calculate_difficulty_distribution(40)

        assert dist["cok_kolay"] == 4  # 10%
        assert dist["kolay"] == 8  # 20%
        assert dist["orta"] == 16  # 40%
        assert dist["zor"] == 8  # 20%
        assert dist["cok_zor"] == 4  # 10%
        assert sum(dist.values()) == 40

    def test_assemble_test_ideal_pool(self):
        # Create an ideal pool with more than enough questions for each difficulty
        pool = []
        difficulties = ["cok_kolay", "kolay", "orta", "zor", "cok_zor"]
        for diff in difficulties:
            for i in range(50):
                pool.append({"id": f"{diff}_{i}", "zorluk": diff})

        # Assemble a 120 question test
        assembled = YksBellCurveAssembler.assemble_test(pool, 120)

        assert len(assembled) == 120

        # Count distributions
        counts = {"cok_kolay": 0, "kolay": 0, "orta": 0, "zor": 0, "cok_zor": 0}
        for q in assembled:
            counts[q["zorluk"]] += 1

        assert counts["cok_kolay"] == 12
        assert counts["kolay"] == 24
        assert counts["orta"] == 48
        assert counts["zor"] == 24
        assert counts["cok_zor"] == 12

    def test_assemble_test_fallback(self):
        # Create a pool that lacks "cok_zor" questions completely
        pool = []
        for i in range(200):
            pool.append({"id": f"orta_{i}", "zorluk": "orta"})
        for i in range(50):
            pool.append({"id": f"zor_{i}", "zorluk": "zor"})
        # Intentionally no "cok_zor", "kolay", or "cok_kolay"

        # Ask for 40 questions
        assembled = YksBellCurveAssembler.assemble_test(pool, 40)

        # Should still return 40 questions by falling back to available ones
        assert len(assembled) == 40

        counts = {"cok_kolay": 0, "kolay": 0, "orta": 0, "zor": 0, "cok_zor": 0}
        for q in assembled:
            counts[q["zorluk"]] += 1

        # Since cok_zor is missing, its 4 quota should fallback to 'zor'
        # Since cok_kolay and kolay are missing (12 quota), they fallback to 'orta'
        assert counts["cok_zor"] == 0
        assert counts["zor"] >= 8  # Original 8 + fallback from cok_zor
        assert counts["orta"] >= 16  # Original 16 + fallback from kolay/cok_kolay

    def test_assemble_test_with_anchors(self):
        pool = []
        difficulties = ["cok_kolay", "kolay", "orta", "zor", "cok_zor"]
        for diff in difficulties:
            for i in range(20):
                pool.append({"id": f"{diff}_{i}", "zorluk": diff, "is_anchor": False})

        # Add a few anchor questions
        pool.append({"id": "anchor_orta_1", "zorluk": "orta", "is_anchor": True})
        pool.append({"id": "anchor_zor_1", "zorluk": "zor", "is_anchor": True})

        # Assemble 40 question test with 2 anchors
        assembled = YksBellCurveAssembler.assemble_test(pool, 40, min_anchor_count=2)

        assert len(assembled) == 40

        anchor_count = sum(1 for q in assembled if q.get("is_anchor"))
        assert anchor_count == 2

        # Total distribution should still match the bell curve
        counts = {"cok_kolay": 0, "kolay": 0, "orta": 0, "zor": 0, "cok_zor": 0}
        for q in assembled:
            counts[q["zorluk"]] += 1

        assert counts["cok_kolay"] == 4
        assert counts["kolay"] == 8
        assert counts["orta"] == 16
        assert counts["zor"] == 8
        assert counts["cok_zor"] == 4
