"""
KIRO2 — DAG Engine Test Suite
================================
Test kategorileri:
  1. Temel DAG operasyonları
  2. Topological sort + döngü tespiti
  3. Mastery kontrolü (HARD/SOFT)
  4. Öğrenme yolu hesaplama
  5. YKS müfredatı bütünlüğü
  6. Mastery-theta dönüşümü
"""

from __future__ import annotations

import pytest

from app.services.dag_engine import (
    PrereqType,
    PrerequisiteDAG,
    build_yks_dag,
    compute_mastery_from_theta,
)

# ─── Yardımcı: küçük test DAG'ı ───────────────────────────────────────────────


def small_dag() -> PrerequisiteDAG:
    """
    Matematik zinciri: Sayılar → Üslü → Polinomlar → Fonksiyonlar → Türev
    """
    dag = PrerequisiteDAG()
    for tid, name in [
        ("sayilar", "Sayılar"),
        ("uslu", "Üslü İfadeler"),
        ("polinomlar", "Polinomlar"),
        ("fonksiyon", "Fonksiyonlar"),
        ("turev", "Türev"),
    ]:
        dag.add_topic(tid, name, "matematik")

    dag.add_prereq("uslu", "sayilar", PrereqType.HARD)
    dag.add_prereq("polinomlar", "uslu", PrereqType.HARD)
    dag.add_prereq("fonksiyon", "polinomlar", PrereqType.HARD)
    dag.add_prereq("turev", "fonksiyon", PrereqType.HARD)
    dag.build()
    return dag


# ─── BÖLÜM 1: Temel Operasyonlar ──────────────────────────────────────────────


class TestBasicOperations:
    def test_add_topic(self):
        dag = PrerequisiteDAG()
        dag.add_topic("a", "A Konusu", "subj")
        assert dag.node_count == 1
        assert dag.get_topic("a") is not None

    def test_add_prereq(self):
        dag = PrerequisiteDAG()
        dag.add_topic("a", "A", "s")
        dag.add_topic("b", "B", "s")
        dag.add_prereq("b", "a", PrereqType.HARD)
        assert dag.edge_count == 1

    def test_prereq_missing_topic_raises(self):
        dag = PrerequisiteDAG()
        dag.add_topic("a", "A", "s")
        with pytest.raises(ValueError):
            dag.add_prereq("b", "a")  # "b" yok

    def test_get_subject_topics(self):
        dag = small_dag()
        topics = dag.get_subject_topics("matematik")
        assert len(topics) == 5


# ─── BÖLÜM 2: Topological Sort ────────────────────────────────────────────────


class TestTopologicalSort:
    def test_build_success(self):
        dag = small_dag()
        assert dag._built is True
        assert len(dag._topo_order) == 5

    def test_topo_order_respects_prereqs(self):
        """Sayılar, Üslü'den önce gelmeli."""
        dag = small_dag()
        order = dag._topo_order
        assert order.index("sayilar") < order.index("uslu")
        assert order.index("uslu") < order.index("polinomlar")
        assert order.index("polinomlar") < order.index("fonksiyon")
        assert order.index("fonksiyon") < order.index("turev")

    def test_level_assignment(self):
        """Sayılar level=0, Türev en yüksek level'da."""
        dag = small_dag()
        sayilar_level = dag.get_topic("sayilar").level
        turev_level = dag.get_topic("turev").level
        assert sayilar_level == 0
        assert turev_level > sayilar_level

    def test_cycle_detection(self):
        """Döngü varsa build() False döndürmeli."""
        dag = PrerequisiteDAG()
        dag.add_topic("a", "A", "s")
        dag.add_topic("b", "B", "s")
        dag.add_topic("c", "C", "s")
        dag.add_prereq("b", "a")
        dag.add_prereq("c", "b")
        dag.add_prereq("a", "c")  # döngü: a→c→b→a
        ok, errors = dag.build()
        assert not ok
        assert len(errors) > 0

    def test_parallel_chains(self):
        """Bağımsız iki zincir — ikisi de topo sırada yer almalı."""
        dag = PrerequisiteDAG()
        dag.add_topic("m1", "Mat1", "m")
        dag.add_topic("m2", "Mat2", "m")
        dag.add_topic("f1", "Fiz1", "f")
        dag.add_topic("f2", "Fiz2", "f")
        dag.add_prereq("m2", "m1")
        dag.add_prereq("f2", "f1")
        ok, _ = dag.build()
        assert ok
        assert dag.node_count == 4

    def test_no_prereqs_level_zero(self):
        """Önkoşulsuz konu level=0 olmalı."""
        dag = PrerequisiteDAG()
        dag.add_topic("temel", "Temel", "s")
        dag.build()
        assert dag.get_topic("temel").level == 0


# ─── BÖLÜM 3: Mastery Kontrolü ────────────────────────────────────────────────


class TestMasteryCheck:
    def test_no_prereqs_can_proceed(self):
        """Önkoşulsuz konu — her zaman devam edebilir."""
        dag = small_dag()
        result = dag.check_mastery("sayilar", {})
        assert result.can_proceed is True
        assert result.blocking_prereqs == []

    def test_hard_prereq_met(self):
        """HARD önkoşul yeterliyse geçilebilir."""
        dag = small_dag()
        mastery = {"sayilar": 0.80}  # > 0.70
        result = dag.check_mastery("uslu", mastery)
        assert result.can_proceed is True

    def test_hard_prereq_not_met(self):
        """HARD önkoşul yetersizse bloklanır."""
        dag = small_dag()
        mastery = {"sayilar": 0.30}  # < 0.70
        result = dag.check_mastery("uslu", mastery)
        assert result.can_proceed is False
        assert "sayilar" in result.blocking_prereqs

    def test_hard_prereq_zero_mastery(self):
        """Hiç çalışılmamış HARD önkoşul — bloklanır."""
        dag = small_dag()
        result = dag.check_mastery("uslu", {})
        assert result.can_proceed is False

    def test_soft_prereq_only_warning(self):
        """SOFT önkoşul yetersizse uyarı, blok yok."""
        dag = PrerequisiteDAG()
        dag.add_topic("a", "A", "s")
        dag.add_topic("b", "B", "s")
        dag.add_prereq("b", "a", PrereqType.SOFT)
        dag.build()

        result = dag.check_mastery("b", {"a": 0.10})
        assert result.can_proceed is True  # SOFT → blok yok
        assert "a" in result.warning_prereqs

    def test_chain_mastery_all_met(self):
        """Türev için tüm zincir (sayılar→uslu→poli→fonk) yeterliyse geçilir."""
        dag = small_dag()
        mastery = {
            "sayilar": 0.85,
            "uslu": 0.80,
            "polinomlar": 0.75,
            "fonksiyon": 0.72,
        }
        result = dag.check_mastery("turev", mastery)
        assert result.can_proceed is True

    def test_chain_one_link_broken(self):
        """
        check_mastery SADECE doğrudan önkoşulları kontrol eder.
        Turev'in doğrudan prerequ: fonksiyon (mastery=0.90 → geçilir).
        Polinomlar düşük olsa bile turev bloklanmaz — çünkü turev polinomları
        doğrudan gerektirmiyor; fonksiyon bu bağı önceki adımda kırdı.
        Zincir güvencesi: CAT öğrenciyi fonksiyon konusuna yönlendirirken
        fonksiyon'un kendi check_mastery'si polinomları kontrol eder.
        Bu tasarım kasıtlı: transitif kontrol get_learning_path'e bırakılmış.
        """
        dag = small_dag()
        mastery = {
            "sayilar": 0.90,
            "uslu": 0.90,
            "polinomlar": 0.20,  # düşük, ama turev'in DOĞRUDAN prerequ değil
            "fonksiyon": 0.90,  # turev'in doğrudan prerequ — yüksek
        }
        # Turev: doğrudan prerequ sadece fonksiyon (0.90 > 0.70) → geçilir
        result_turev = dag.check_mastery("turev", mastery)
        assert result_turev.can_proceed is True

        # Fonksiyon: doğrudan prerequ polinomlar (0.20 < 0.70) → bloklanır
        result_fonk = dag.check_mastery("fonksiyon", mastery)
        assert result_fonk.can_proceed is False
        assert "polinomlar" in result_fonk.blocking_prereqs

    def test_mastery_scores_in_result(self):
        """Sonuçta prereq mastery skorları yer almalı."""
        dag = small_dag()
        mastery = {"sayilar": 0.65}
        result = dag.check_mastery("uslu", mastery)
        assert "sayilar" in result.mastery_scores
        assert result.mastery_scores["sayilar"] == 0.65


# ─── BÖLÜM 4: Öğrenme Yolu ────────────────────────────────────────────────────


class TestLearningPath:
    def test_path_to_root_is_just_root(self):
        """Önkoşulsuz konunun yolu sadece kendisi."""
        dag = small_dag()
        path = dag.get_learning_path("sayilar", {})
        assert "sayilar" in path.ordered_steps

    def test_path_to_turev_includes_chain(self):
        """Türev yolu tüm zinciri içermeli."""
        dag = small_dag()
        path = dag.get_learning_path("turev", {})
        steps = path.ordered_steps
        for expected in ["sayilar", "uslu", "polinomlar", "fonksiyon", "turev"]:
            assert expected in steps

    def test_path_order_respects_topo(self):
        """Öğrenme yolu topological sırayla olmalı."""
        dag = small_dag()
        path = dag.get_learning_path("turev", {})
        steps = path.ordered_steps
        assert steps.index("sayilar") < steps.index("uslu")
        assert steps.index("uslu") < steps.index("polinomlar")
        assert steps.index("fonksiyon") < steps.index("turev")

    def test_skip_mastered_topics(self):
        """Ustalaşılan konular atlansın."""
        dag = small_dag()
        mastery = {
            "sayilar": 0.90,  # ustalaşıldı
            "uslu": 0.90,  # ustalaşıldı
            "polinomlar": 0.10,  # henüz değil
        }
        path = dag.get_learning_path("turev", mastery, skip_mastered=True)
        steps = path.ordered_steps
        assert "sayilar" not in steps
        assert "uslu" not in steps
        assert "polinomlar" in steps

    def test_all_mastered_empty_path(self):
        """Her şey ustalaşıldıysa boş yol."""
        dag = small_dag()
        mastery = dict.fromkeys(
            ["sayilar", "uslu", "polinomlar", "fonksiyon", "turev"], 0.95
        )
        path = dag.get_learning_path("turev", mastery, skip_mastered=True)
        assert len(path.ordered_steps) == 0

    def test_estimated_sessions_positive(self):
        dag = small_dag()
        path = dag.get_learning_path("turev", {})
        assert path.estimated_sessions > 0


# ─── BÖLÜM 5: YKS Müfredatı Bütünlüğü ────────────────────────────────────────


class TestYKSCurriculum:
    """build_yks_dag() ile üretilen tam YKS DAG'ının bütünlük testleri."""

    @pytest.fixture(scope="class")
    def yks(self):
        return build_yks_dag()

    def test_dag_builds_without_errors(self, yks):
        assert yks._built is True

    def test_no_cycles(self, yks):
        ok, errors = yks.build()
        assert ok, f"Döngü var: {errors}"

    def test_minimum_topic_count(self, yks):
        """En az 30 konu olmalı."""
        assert yks.node_count >= 30

    def test_integral_requires_turev(self, yks):
        """İntegral, türev önkoşuluna sahip olmalı."""
        integral = yks.get_topic("ayt-mat-integral")
        if integral:
            prereq_ids = [p.prereq_id for p in integral.prereqs]
            assert "ayt-mat-turev" in prereq_ids

    def test_turev_requires_limit(self, yks):
        """Türev, limit önkoşuluna sahip olmalı."""
        turev = yks.get_topic("ayt-mat-turev")
        if turev:
            prereq_ids = [p.prereq_id for p in turev.prereqs]
            assert "ayt-mat-limit" in prereq_ids

    def test_integral_path_includes_full_chain(self, yks):
        """İntegral yolu tam zinciri içermeli."""
        path = yks.get_learning_path("ayt-mat-integral", {})
        for expected in [
            "tyt-mat-sayilar",
            "tyt-mat-fonksiyon",
            "ayt-mat-limit",
            "ayt-mat-turev",
            "ayt-mat-integral",
        ]:
            assert expected in path.ordered_steps, (
                f"{expected} yolda yok. Yol: {path.ordered_steps}"
            )

    def test_sayilar_no_prereqs(self, yks):
        """Sayılar ve İşlemler önkoşulsuz olmalı."""
        sayilar = yks.get_topic("tyt-mat-sayilar")
        if sayilar:
            assert len(sayilar.prereqs) == 0

    def test_all_prereq_topics_exist(self, yks):
        """Tüm önkoşul topic_id'leri DAG'da mevcut olmalı."""
        for edge in yks._edges:
            assert edge.prereq_id in yks._nodes, f"Önkoşul konu yok: {edge.prereq_id}"

    def test_tyt_fizik_kuvvet_requires_vektor(self, yks):
        kuvvet = yks.get_topic("tyt-fiz-kuvvet")
        if kuvvet:
            prereqs = [p.prereq_id for p in kuvvet.prereqs]
            assert "tyt-fiz-vektor" in prereqs

    def test_kimya_periyodik_requires_atomyapisi(self, yks):
        periyodik = yks.get_topic("tyt-kim-periyodik")
        if periyodik:
            prereqs = [p.prereq_id for p in periyodik.prereqs]
            assert "tyt-kim-atomyapisi" in prereqs


# ─── BÖLÜM 6: Mastery-Theta Dönüşümü ─────────────────────────────────────────


class TestMasteryFromTheta:
    def test_high_theta_high_mastery(self):
        """Yüksek θ → yüksek mastery."""
        m = compute_mastery_from_theta(theta=2.0, theta_se=0.3)
        assert m > 0.90

    def test_negative_theta_low_mastery(self):
        """Düşük θ → düşük mastery."""
        m = compute_mastery_from_theta(theta=-2.0, theta_se=0.3)
        assert m < 0.10

    def test_zero_theta_approx_half(self):
        """θ=0 → mastery ≈ 0.50 (cutoff=0.0 için)."""
        m = compute_mastery_from_theta(theta=0.0, theta_se=0.4)
        assert abs(m - 0.50) < 0.05

    def test_zero_se_deterministic(self):
        """SE=0 → kesin sonuç."""
        assert compute_mastery_from_theta(1.0, 0.0) == 1.0
        assert compute_mastery_from_theta(-1.0, 0.0) == 0.0

    def test_bounded_output(self):
        """Sonuç her zaman [0, 1] içinde olmalı."""
        for theta in (-5, -2, -1, 0, 1, 2, 5):
            m = compute_mastery_from_theta(float(theta), 0.5)
            assert 0.0 <= m <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
