"""
KIRO2 — Prerequisite DAG Engine
=================================
YKS konu bağımlılık grafiği — saf Python, DB bağımlılığı yok.

Neden DAG (Directed Acyclic Graph)?
  Konular arası öğrenme sırası önemlidir:
    TYT Matematik: Sayılar → Üslü İfadeler → Polinomlar → Denklemler → Fonksiyonlar
    AYT Matematik: Fonksiyonlar → Türev → İntegral  (seri bağımlılık)
    TYT Fizik:     Kuvvet → Hareket → Enerji (hiyerarşik)
    TYT Kimya:     Atomun Yapısı → Periyodik Tablo → Bağlar → Reaksiyonlar

  DAG olmadan: öğrenci türev sorusu görür ama limit bilmez → hayal kırıklığı → dropout

Önkoşul tipleri:
  HARD (zorunlu): Öğrenilmeden ileri geçilmez. Mastery < eşik → bloklama.
      Örnek: İntegral, Türev bilmeden gerçekten çözülemez.
  SOFT (önerilen): Bilinmesi faydalı ama zorunlu değil. Uyarı verilir.
      Örnek: Trigonometri, Analitik Geometri için önerilir ama çözülebilir.

Mastery hesabı (IRT bazlı):
  mastery = P(θ > θ_cutoff)  — belirli eşiğin üzerinde olma olasılığı
  Varsayılan eşik: θ_cutoff = 0.0 (orta seviye)
  HARD önkoşul için minimum mastery: %70

Döngü tespiti:
  YKS müfredatı teoride döngüsüz ama veri girişi hatalara açık.
  Kahn algoritması ile O(V+E) hızında topological sort + döngü tespiti.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Set, Tuple


# ─── Sabitler ─────────────────────────────────────────────────────────────────

MASTERY_CUTOFF_HARD = 0.70   # HARD önkoşul için min mastery oranı
MASTERY_CUTOFF_SOFT = 0.40   # SOFT önkoşul için uyarı eşiği
THETA_MASTERY_CUTOFF = 0.0   # P(θ > bu değer) = mastery olasılığı


# ─── Veri yapıları ────────────────────────────────────────────────────────────

class PrereqType(str, Enum):
    HARD = "hard"   # zorunlu önkoşul — bloklama
    SOFT = "soft"   # önerilen önkoşul — uyarı


@dataclass(frozen=True)
class Prerequisite:
    """Bir bağımlılık kenarı: topic_id → prereq_id."""
    topic_id:   str
    prereq_id:  str
    ptype:      PrereqType = PrereqType.HARD
    strength:   float      = 1.0   # 0.0–1.0, 1.0 = tam bağımlı


@dataclass
class TopicNode:
    """DAG'daki bir konu düğümü."""
    topic_id:    str
    name:        str
    subject_id:  str
    level:       int = 0   # topological order'daki derinlik (0 = temel)
    prereqs:     List[Prerequisite] = field(default_factory=list)


@dataclass
class MasteryCheck:
    """Bir konuya geçiş için mastery kontrol sonucu."""
    topic_id:         str
    can_proceed:      bool
    blocking_prereqs: List[str]   # HARD önkoşul ID'leri — yeterli mastery yok
    warning_prereqs:  List[str]   # SOFT önkoşul ID'leri — uyarı
    mastery_scores:   Dict[str, float]   # prereq_id → mastery skoru


@dataclass
class LearningPath:
    """Önerilen öğrenme yolu."""
    topic_id:      str
    ordered_steps: List[str]   # konu ID'leri, öğrenme sırası
    total_topics:  int
    estimated_sessions: int   # tahmini oturum sayısı (kaba tahmin)


# ─── DAG Engine ───────────────────────────────────────────────────────────────

class PrerequisiteDAG:
    """
    YKS konu önkoşul grafiği.

    Kullanım:
      dag = PrerequisiteDAG()
      dag.add_topic("turlu-ifadeler", "Üslü İfadeler", "matematik")
      dag.add_topic("polinomlar",    "Polinomlar",    "matematik")
      dag.add_prereq("polinomlar", "turlu-ifadeler", PrereqType.HARD)
      dag.build()   # topological sort + döngü tespiti

      check = dag.check_mastery("polinomlar", mastery_scores)
      path  = dag.get_learning_path("integral")
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, TopicNode]   = {}
        self._edges: List[Prerequisite]     = []
        self._topo_order: List[str]         = []
        self._built: bool                   = False

    # ── Graf inşa ─────────────────────────────────────────────────

    def add_topic(self, topic_id: str, name: str, subject_id: str) -> None:
        """Konu düğümü ekle."""
        self._nodes[topic_id] = TopicNode(
            topic_id=topic_id, name=name, subject_id=subject_id
        )
        self._built = False

    def add_prereq(self, topic_id: str, prereq_id: str,
                   ptype: PrereqType = PrereqType.HARD,
                   strength: float = 1.0) -> None:
        """
        Önkoşul kenarı ekle: prereq_id önce öğrenilmeli, sonra topic_id.
        topic_id → prereq_id yönünde kenar (topic prereq'a bağımlı).
        """
        if topic_id not in self._nodes:
            raise ValueError(f"Konu bulunamadı: {topic_id}")
        if prereq_id not in self._nodes:
            raise ValueError(f"Önkoşul konu bulunamadı: {prereq_id}")

        p = Prerequisite(topic_id=topic_id, prereq_id=prereq_id,
                         ptype=ptype, strength=strength)
        self._edges.append(p)
        self._nodes[topic_id].prereqs.append(p)
        self._built = False

    def build(self) -> Tuple[bool, List[str]]:
        """
        Topological sort çalıştır (Kahn algoritması).
        Döndürür: (başarılı, hata_mesajları)
        Döngü varsa başarısız döner.
        """
        # In-degree hesapla
        in_degree: Dict[str, int] = {nid: 0 for nid in self._nodes}
        adj: Dict[str, List[str]] = defaultdict(list)

        for edge in self._edges:
            # topic, prereq'a bağımlı → prereq'dan topic'e kenar
            adj[edge.prereq_id].append(edge.topic_id)
            in_degree[edge.topic_id] += 1

        # Kahn: sıfır in-degree ile başla
        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        topo: List[str] = []

        while queue:
            node = queue.popleft()
            topo.append(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(topo) != len(self._nodes):
            # Döngü var — hangi düğümler işlenemedi?
            unprocessed = [nid for nid in self._nodes if nid not in topo]
            self._built = False
            return False, [f"Döngü tespit edildi: {unprocessed}"]

        self._topo_order = topo

        # BUG-16 FIX: Level ataması topo sırası tamamen bittikten SONRA yapılır.
        # Kahn döngüsü içinde level okumak, henüz işlenmemiş prereq'lar için
        # yanlış level=0 dönebilir. Ayrı pass ile bu riski ortadan kaldırıyoruz.
        topo_rank = {nid: i for i, nid in enumerate(topo)}
        for nid in topo:
            node_obj = self._nodes[nid]
            prereq_levels = [
                self._nodes[e.prereq_id].level
                for e in self._edges
                if e.topic_id == nid and e.prereq_id in self._nodes
            ]
            node_obj.level = (max(prereq_levels) + 1) if prereq_levels else 0

        self._built = True
        return True, []

    # ── Mastery Kontrolü ──────────────────────────────────────────

    def check_mastery(
        self,
        topic_id: str,
        mastery_scores: Dict[str, float],   # topic_id → 0.0–1.0
        hard_cutoff: float = MASTERY_CUTOFF_HARD,
        soft_cutoff: float = MASTERY_CUTOFF_SOFT,
    ) -> MasteryCheck:
        """
        Bir konuya geçmek için önkoşul mastery'sini kontrol et.

        Argümanlar:
          topic_id:      kontrol edilecek konu
          mastery_scores: kullanıcının tüm konulardaki mastery oranları

        Döndürür:
          MasteryCheck(can_proceed, blocking_prereqs, warning_prereqs)
        """
        if topic_id not in self._nodes:
            return MasteryCheck(topic_id=topic_id, can_proceed=True,
                                blocking_prereqs=[], warning_prereqs=[],
                                mastery_scores={})

        node = self._nodes[topic_id]
        blocking: List[str] = []
        warnings: List[str] = []
        scores:   Dict[str, float] = {}

        for prereq in node.prereqs:
            pid = prereq.prereq_id
            score = mastery_scores.get(pid, 0.0)
            scores[pid] = score

            if prereq.ptype == PrereqType.HARD:
                # Ağırlıklı eşik: yüksek strength → daha sıkı kontrol
                threshold = hard_cutoff * prereq.strength
                if score < threshold:
                    blocking.append(pid)
            else:  # SOFT
                threshold = soft_cutoff * prereq.strength
                if score < threshold:
                    warnings.append(pid)

        return MasteryCheck(
            topic_id=topic_id,
            can_proceed=(len(blocking) == 0),
            blocking_prereqs=blocking,
            warning_prereqs=warnings,
            mastery_scores=scores,
        )

    # ── Learning Path ─────────────────────────────────────────────

    def get_learning_path(
        self,
        target_topic_id: str,
        mastery_scores: Optional[Dict[str, float]] = None,
        skip_mastered: bool = True,
        mastery_threshold: float = MASTERY_CUTOFF_HARD,
    ) -> LearningPath:
        """
        Hedef konuya ulaşmak için gereken öğrenme yolunu hesapla.

        DFS ile tüm gerekli önkoşulları bul, topological sırayla döndür.
        skip_mastered=True ise zaten ustalaşılan konuları atla.

        Örnek:
          target = "integral"
          path   = [sayılar, üslü, polinomlar, denklemler,
                    fonksiyonlar, limit, türev, integral]
        """
        if target_topic_id not in self._nodes:
            return LearningPath(target_topic_id, [target_topic_id], 1, 1)

        mastery = mastery_scores or {}

        # DFS ile tüm gerekli konuları topla
        required: Set[str] = set()
        self._collect_prerequisites(target_topic_id, required, set())
        required.add(target_topic_id)

        # Zaten ustalaşılanları filtrele
        if skip_mastered:
            required = {
                tid for tid in required
                if mastery.get(tid, 0.0) < mastery_threshold
            }

        # Topological sırayla filtrele
        if self._built:
            ordered = [tid for tid in self._topo_order if tid in required]
        else:
            ordered = sorted(required, key=lambda t: self._nodes[t].level)

        # Tahmini oturum sayısı: her konu ortalama 2 oturum
        est_sessions = len(ordered) * 2

        return LearningPath(
            topic_id=target_topic_id,
            ordered_steps=ordered,
            total_topics=len(ordered),
            estimated_sessions=est_sessions,
        )

    def _collect_prerequisites(self, topic_id: str,
                                collected: Set[str],
                                visiting: Set[str]) -> None:
        """DFS ile tüm gerekli önkoşulları topla (döngü korumalı)."""
        if topic_id in visiting:
            return   # döngü koruması
        visiting.add(topic_id)

        node = self._nodes.get(topic_id)
        if not node:
            return

        for prereq in node.prereqs:
            pid = prereq.prereq_id
            if pid not in collected:
                collected.add(pid)
                self._collect_prerequisites(pid, collected, visiting.copy())

    # ── Yardımcı ──────────────────────────────────────────────────

    def get_topic(self, topic_id: str) -> Optional[TopicNode]:
        return self._nodes.get(topic_id)

    def get_all_topics(self) -> List[TopicNode]:
        if self._built:
            return [self._nodes[tid] for tid in self._topo_order]
        return list(self._nodes.values())

    def get_subject_topics(self, subject_id: str) -> List[TopicNode]:
        nodes = [n for n in self._nodes.values() if n.subject_id == subject_id]
        if self._built:
            order = {tid: i for i, tid in enumerate(self._topo_order)}
            nodes.sort(key=lambda n: order.get(n.topic_id, 9999))
        return nodes

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)


# ─── YKS Müfredatı DAG Fabrikası ─────────────────────────────────────────────

def build_yks_dag() -> PrerequisiteDAG:
    """
    YKS (TYT + AYT) müfredatı için tam önkoşul grafiği.
    MEB müfredatı + ÖSYM konu dağılımı baz alındı.

    Konu ID'leri slug formatında (veritabanıyla eşleşmeli).
    Gerçek veritabanında subject_id UUID olacak; burada slug kullanıyoruz.
    """
    dag = PrerequisiteDAG()

    # ================================================================
    # TYT MATEMATİK
    # ================================================================
    tyt_mat_topics = [
        ("tyt-mat-sayilar",         "Sayılar ve İşlemler",       "tyt-matematik"),
        ("tyt-mat-uslu",            "Üslü ve Köklü İfadeler",    "tyt-matematik"),
        ("tyt-mat-carpanlarastirma","Çarpanlara Ayırma",         "tyt-matematik"),
        ("tyt-mat-polinomlar",      "Polinomlar",                "tyt-matematik"),
        ("tyt-mat-denklemler",      "Denklemler ve Eşitsizlikler","tyt-matematik"),
        ("tyt-mat-oran",            "Oran-Orantı ve Problemler", "tyt-matematik"),
        ("tyt-mat-kume",            "Kümeler",                   "tyt-matematik"),
        ("tyt-mat-mantik",          "Mantık",                    "tyt-matematik"),
        ("tyt-mat-fonksiyon",       "Fonksiyonlar",              "tyt-matematik"),
        ("tyt-mat-istatistik",      "İstatistik ve Olasılık",    "tyt-matematik"),
        ("tyt-mat-geometri-temel",  "Temel Geometri",            "tyt-matematik"),
        ("tyt-mat-ucgenler",        "Üçgenler",                  "tyt-matematik"),
        ("tyt-mat-dortgenler",      "Dörtgenler",                "tyt-matematik"),
        ("tyt-mat-cember",          "Çember ve Daire",           "tyt-matematik"),
        ("tyt-mat-katicisinler",    "Katı Cisimler",             "tyt-matematik"),
        ("tyt-mat-permutasyon",     "Permütasyon ve Kombinasyon","tyt-matematik"),
    ]

    tyt_mat_prereqs = [
        # (konu, önkoşul, tip)
        ("tyt-mat-uslu",            "tyt-mat-sayilar",         PrereqType.HARD),
        ("tyt-mat-carpanlarastirma","tyt-mat-uslu",            PrereqType.HARD),
        ("tyt-mat-polinomlar",      "tyt-mat-carpanlarastirma",PrereqType.HARD),
        ("tyt-mat-denklemler",      "tyt-mat-polinomlar",      PrereqType.HARD),
        ("tyt-mat-oran",            "tyt-mat-denklemler",      PrereqType.SOFT),
        ("tyt-mat-fonksiyon",       "tyt-mat-denklemler",      PrereqType.HARD),
        ("tyt-mat-istatistik",      "tyt-mat-sayilar",         PrereqType.SOFT),
        ("tyt-mat-permutasyon",     "tyt-mat-istatistik",      PrereqType.SOFT),
        ("tyt-mat-ucgenler",        "tyt-mat-geometri-temel",  PrereqType.HARD),
        ("tyt-mat-dortgenler",      "tyt-mat-ucgenler",        PrereqType.SOFT),
        ("tyt-mat-cember",          "tyt-mat-ucgenler",        PrereqType.SOFT),
        ("tyt-mat-katicisinler",    "tyt-mat-dortgenler",      PrereqType.SOFT),
    ]

    # ================================================================
    # AYT MATEMATİK
    # ================================================================
    ayt_mat_topics = [
        ("ayt-mat-sayi-teorisi",    "Sayı Teorisi",             "ayt-matematik"),
        ("ayt-mat-trigonometri",    "Trigonometri",             "ayt-matematik"),
        ("ayt-mat-analitik-geo",    "Analitik Geometri",        "ayt-matematik"),
        ("ayt-mat-logaritma",       "Logaritma",                "ayt-matematik"),
        ("ayt-mat-diziler",         "Diziler",                  "ayt-matematik"),
        ("ayt-mat-limit",           "Limit ve Süreklilik",      "ayt-matematik"),
        ("ayt-mat-turev",           "Türev",                    "ayt-matematik"),
        ("ayt-mat-integral",        "İntegral",                 "ayt-matematik"),
        ("ayt-mat-olasilik",        "Olasılık",                 "ayt-matematik"),
        ("ayt-mat-matris",          "Matrisler",                "ayt-matematik"),
    ]

    ayt_mat_prereqs = [
        ("ayt-mat-trigonometri",    "tyt-mat-geometri-temel",  PrereqType.HARD),
        ("ayt-mat-trigonometri",    "tyt-mat-fonksiyon",       PrereqType.SOFT),
        ("ayt-mat-analitik-geo",    "tyt-mat-geometri-temel",  PrereqType.HARD),
        ("ayt-mat-analitik-geo",    "tyt-mat-denklemler",      PrereqType.HARD),
        ("ayt-mat-logaritma",       "tyt-mat-uslu",            PrereqType.HARD),
        ("ayt-mat-logaritma",       "tyt-mat-fonksiyon",       PrereqType.HARD),
        ("ayt-mat-diziler",         "tyt-mat-fonksiyon",       PrereqType.SOFT),
        ("ayt-mat-limit",           "tyt-mat-fonksiyon",       PrereqType.HARD),
        ("ayt-mat-limit",           "ayt-mat-trigonometri",    PrereqType.SOFT),
        ("ayt-mat-turev",           "ayt-mat-limit",           PrereqType.HARD),
        ("ayt-mat-integral",        "ayt-mat-turev",           PrereqType.HARD),
        ("ayt-mat-olasilik",        "tyt-mat-permutasyon",     PrereqType.HARD),
    ]

    # ================================================================
    # TYT FİZİK
    # ================================================================
    tyt_fiz_topics = [
        ("tyt-fiz-olcme",          "Ölçme ve Birimler",        "tyt-fizik"),
        ("tyt-fiz-vektor",         "Vektörler",                "tyt-fizik"),
        ("tyt-fiz-kuvvet",         "Kuvvet ve Hareket",        "tyt-fizik"),
        ("tyt-fiz-enerji",         "İş-Enerji-Güç",           "tyt-fizik"),
        ("tyt-fiz-momentum",       "Momentum ve İtme",         "tyt-fizik"),
        ("tyt-fiz-dalgahareketi",  "Dalgalar",                 "tyt-fizik"),
        ("tyt-fiz-optik",          "Optik",                    "tyt-fizik"),
        ("tyt-fiz-elektrik",       "Elektrik",                 "tyt-fizik"),
        ("tyt-fiz-manyetizma",     "Manyetizma",               "tyt-fizik"),
    ]

    tyt_fiz_prereqs = [
        ("tyt-fiz-kuvvet",         "tyt-fiz-vektor",          PrereqType.HARD),
        ("tyt-fiz-enerji",         "tyt-fiz-kuvvet",          PrereqType.HARD),
        ("tyt-fiz-momentum",       "tyt-fiz-kuvvet",          PrereqType.HARD),
        ("tyt-fiz-manyetizma",     "tyt-fiz-elektrik",        PrereqType.HARD),
    ]

    # ================================================================
    # TYT KİMYA
    # ================================================================
    tyt_kim_topics = [
        ("tyt-kim-atomyapisi",     "Atomun Yapısı",            "tyt-kimya"),
        ("tyt-kim-periyodik",      "Periyodik Tablo",          "tyt-kimya"),
        ("tyt-kim-baglar",         "Kimyasal Bağlar",          "tyt-kimya"),
        ("tyt-kim-reaksiyonlar",   "Kimyasal Tepkimeler",      "tyt-kimya"),
        ("tyt-kim-asitbaz",        "Asit-Baz",                 "tyt-kimya"),
        ("tyt-kim-cozeltiler",     "Çözeltiler",               "tyt-kimya"),
        ("tyt-kim-mol",            "Mol Kavramı",              "tyt-kimya"),
    ]

    tyt_kim_prereqs = [
        ("tyt-kim-periyodik",      "tyt-kim-atomyapisi",      PrereqType.HARD),
        ("tyt-kim-baglar",         "tyt-kim-periyodik",       PrereqType.HARD),
        ("tyt-kim-reaksiyonlar",   "tyt-kim-baglar",          PrereqType.HARD),
        ("tyt-kim-mol",            "tyt-kim-reaksiyonlar",    PrereqType.HARD),
        ("tyt-kim-asitbaz",        "tyt-kim-cozeltiler",      PrereqType.SOFT),
    ]

    # ================================================================
    # TYT BİYOLOJİ
    # ================================================================
    tyt_bio_topics = [
        ("tyt-bio-hucre",          "Hücre",                    "tyt-biyoloji"),
        ("tyt-bio-dokular",        "Dokular",                  "tyt-biyoloji"),
        ("tyt-bio-sindirim",       "Sindirim Sistemi",         "tyt-biyoloji"),
        ("tyt-bio-dolas",          "Dolaşım Sistemi",          "tyt-biyoloji"),
        ("tyt-bio-solunum",        "Solunum Sistemi",          "tyt-biyoloji"),
        ("tyt-bio-ureyen",         "Üreme ve Gelişme",         "tyt-biyoloji"),
        ("tyt-bio-kalitim",        "Kalıtım",                  "tyt-biyoloji"),
        ("tyt-bio-ekosistem",      "Ekosistem",                "tyt-biyoloji"),
    ]

    tyt_bio_prereqs = [
        ("tyt-bio-dokular",        "tyt-bio-hucre",           PrereqType.HARD),
        ("tyt-bio-sindirim",       "tyt-bio-dokular",         PrereqType.SOFT),
        ("tyt-bio-kalitim",        "tyt-bio-hucre",           PrereqType.HARD),
    ]

    # ================================================================
    # TYT TÜRKÇe (büyük ölçüde bağımsız konular)
    # ================================================================
    tyt_turkce_topics = [
        ("tyt-tr-sesbirgisi",      "Ses Bilgisi",              "tyt-turkce"),
        ("tyt-tr-yazim",           "Yazım Kuralları",          "tyt-turkce"),
        ("tyt-tr-noktalama",       "Noktalama İşaretleri",     "tyt-turkce"),
        ("tyt-tr-sozkoku",         "Sözcükte Anlam",           "tyt-turkce"),
        ("tyt-tr-cumlede",         "Cümlede Anlam",            "tyt-turkce"),
        ("tyt-tr-paragraf",        "Paragraf",                 "tyt-turkce"),
        ("tyt-tr-dilbilgisi",      "Dil Bilgisi",              "tyt-turkce"),
    ]

    tyt_turkce_prereqs = [
        # Paragraf; anlam bilgisini gerektirir
        ("tyt-tr-paragraf",        "tyt-tr-sozkoku",          PrereqType.SOFT),
        ("tyt-tr-paragraf",        "tyt-tr-cumlede",          PrereqType.SOFT),
    ]

    # ================================================================
    # Tüm konuları ve kenarları ekle
    # ================================================================
    all_topics = (
        tyt_mat_topics + ayt_mat_topics +
        tyt_fiz_topics + tyt_kim_topics +
        tyt_bio_topics + tyt_turkce_topics
    )
    all_prereqs = (
        tyt_mat_prereqs + ayt_mat_prereqs +
        tyt_fiz_prereqs + tyt_kim_prereqs +
        tyt_bio_prereqs + tyt_turkce_prereqs
    )

    for topic_id, name, subject_id in all_topics:
        dag.add_topic(topic_id, name, subject_id)

    for topic_id, prereq_id, ptype in all_prereqs:
        dag.add_prereq(topic_id, prereq_id, ptype)

    ok, errors = dag.build()
    if not ok:
        raise RuntimeError(f"YKS DAG inşa hatası: {errors}")

    return dag


# ─── Mastery skoru hesaplayıcı (IRT tabanlı) ─────────────────────────────────

def compute_mastery_from_theta(
    theta: float,
    theta_se: float = 0.5,
    cutoff: float = THETA_MASTERY_CUTOFF,
) -> float:
    """
    IRT θ tahmininden mastery oranı hesapla.
    P(θ > cutoff) — Normal dağılım CDF kullanarak.

    Örnek:
      θ=0.5, SE=0.4, cutoff=0.0 → P(θ > 0) ≈ 0.89
      θ=-0.5, SE=0.4, cutoff=0.0 → P(θ > 0) ≈ 0.10
    """
    import math

    if theta_se <= 0:
        return 1.0 if theta >= cutoff else 0.0

    # z-score: (cutoff - θ) / SE
    z = (cutoff - theta) / theta_se

    # P(θ > cutoff) = 1 - Φ(z) = Φ(-z)
    # erfc yaklaşımı ile standard normal CDF
    p = 0.5 * (1.0 + math.erf(-z / math.sqrt(2.0)))
    return round(min(max(p, 0.0), 1.0), 4)
