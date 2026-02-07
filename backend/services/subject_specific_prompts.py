"""
Subject-Specific Prompt Templates for ÖSYM-Style Question Generation

Based on research: DERS_BAZLI_SORU_ANALIZI.md
Implements subject-specific characteristics for each TYT/AYT subject
"""

from typing import Dict, List, Optional


class SubjectConfig:
    """Configuration for subject-specific question generation"""

    def __init__(
        self,
        subject: str,
        target_length: int,
        length_tolerance: float = 0.30,  # ±30% default (relaxed from 15%)
        bloom_preferences: Dict[str, float] = None,
        common_misconceptions: List[str] = None,
        question_style_notes: List[str] = None,
        formula_based: bool = False,
        scenario_based: bool = False,
    ):
        self.subject = subject
        self.target_length = target_length
        self.min_length = int(target_length * (1 - length_tolerance))
        self.max_length = int(target_length * (1 + length_tolerance))
        self.bloom_preferences = bloom_preferences or {}
        self.common_misconceptions = common_misconceptions or []
        self.question_style_notes = question_style_notes or []
        self.formula_based = formula_based
        self.scenario_based = scenario_based


# Subject-Specific Configurations (from research: DERS_BAZLI_SORU_ANALIZI.md)

# Export target lengths for compatibility
SUBJECT_TARGET_LENGTHS = {
    "Matematik": 388,
    "Fizik": 453,
    "Kimya": 202,
    "Biyoloji": 291,
    "Türkçe": 660,
    "Tarih": 481,
    "Coğrafya": 432,
    "Edebiyat": 536,
    "DEFAULT": 400,
}


KIMYA_CONFIG = SubjectConfig(
    subject="Kimya",
    target_length=202,
    length_tolerance=0.30,  # ±30% = 141-263 chars (relaxed for better generation)
    bloom_preferences={
        "Hatırlama": 0.15,
        "Anlama": 0.40,
        "Uygulama": 0.30,
        "Analiz": 0.15,
    },
    common_misconceptions=[
        "Mol kavramı: Madde miktarı ile kütle karıştırılması",
        "Kimyasal denge: Konsantrasyonların eşit olması gerektiği yanılgısı",
        "Asit-baz: Güçlü asit = daha fazla H+ iyonu her zaman",
        "Stokiyometri: Katsayıların doğrudan kütle oranları olduğu",
        "Elektrokimya: Katot her zaman negatif kutup",
        "Isı-sıcaklık karıştırılması",
        "Çözünürlük: Daha çok çözücü = daha çok çözünen madde",
    ],
    question_style_notes=[
        "KISA ve DOĞRUDAN sorular tercih edin (202 karakter hedef)",
        "Formül ve hesaplama ağırlıklı",
        "Sayısal değerler ve birimler net olmalı",
        "Kimyasal denklemler dengeli olmalı",
        "Mol kavramı sorularında dikkatli olun (en yaygın yanılgı)",
    ],
    formula_based=True,
    scenario_based=False,
)

MATEMATIK_CONFIG = SubjectConfig(
    subject="Matematik",
    target_length=388,
    length_tolerance=0.30,  # ±30% = 272-504 chars (relaxed for better generation)
    bloom_preferences={
        "Hatırlama": 0.10,
        "Anlama": 0.20,
        "Uygulama": 0.50,
        "Analiz": 0.20,
    },
    common_misconceptions=[
        "Her şey toplanabilir yanılgısı (kesir, üs, kök toplama)",
        "Karekök ± sonuç verir yanılgısı",
        "Negatif sayılarla işlemler ((-a)² = -a²)",
        "Fonksiyon-denklem karıştırılması",
        "Türev sadece eğim değil, değişim oranıdır",
        "Limit = fonksiyon değeri yanılgısı",
        "Oran-orantı karıştırılması",
        "Mutlak değer her zaman pozitif yapar yanılgısı",
    ],
    question_style_notes=[
        "Problem çözme odaklı (Uygulama %50)",
        "Çözüm adımları net olmalı",
        "Sayısal hesaplamalar kesin sonuç vermeli",
        "Grafikler ve şekiller kullanılabilir (metin içinde tanımlanmalı)",
        "Orta uzunlukta (388 karakter) - detaylı ama verbose değil",
    ],
    formula_based=True,
    scenario_based=False,
)

FIZIK_CONFIG = SubjectConfig(
    subject="Fizik",
    target_length=453,
    length_tolerance=0.30,  # ±30% = 317-589 chars (relaxed for better generation)
    bloom_preferences={
        "Hatırlama": 0.10,
        "Anlama": 0.25,
        "Uygulama": 0.45,
        "Analiz": 0.20,
    },
    common_misconceptions=[
        "Kuvvet-hareket karıştırılması (Kuvvet = hareket değil, ivme)",
        "Ağır cisimler daha hızlı düşer yanılgısı",
        "Newton 1: Durgun cisim için kuvvet yok yanılgısı",
        "Sürtünme her zaman harekete zıt yönde",
        "Enerji korunumu: Enerji kaybolur yanılgısı",
        "Elektrik: Akım tükenir yanılgısı",
        "Optik: Ayna düz gösterir yanılgısı",
    ],
    question_style_notes=[
        "SENARYO-BAZLI sorular tercih edin (453 karakter - en uzun!)",
        "Tüm fiziksel büyüklükler ve birimleri net belirtin",
        "Başlangıç koşulları açıkça tanımlayın",
        "Kuvvet Kavram Envanteri (FCI) yaklaşımı: Yanılgı-bazlı çeldiriciler",
        "Gerçek hayat senaryoları kullanın (araba, top, rampa vb.)",
    ],
    formula_based=True,
    scenario_based=True,
)

BIYOLOJI_CONFIG = SubjectConfig(
    subject="Biyoloji",
    target_length=291,
    length_tolerance=0.30,  # ±30% = 204-378 chars (relaxed for better generation)
    bloom_preferences={
        "Hatırlama": 0.20,
        "Anlama": 0.35,
        "Uygulama": 0.25,
        "Analiz": 0.20,
    },
    common_misconceptions=[
        "Fotosentez: Bitkiler toprağın kütlesini kullanır yanılgısı",
        "Evrim: Organizmalar ihtiyaç duyduğu için evrimleşir",
        "Genetik: Dominant özellik her zaman daha yaygın",
        "Hücre: Tüm hücreler aynı boyutta",
        "Mitozda kromozom sayısı yarıya iner yanılgısı",
        "Solunumda sadece oksijen alınır, CO₂ verilir",
    ],
    question_style_notes=[
        "Kavramsal anlama odaklı (Anlama %35 - en yüksek)",
        "Şekil ve diyagramlar çok kullanılır (metin içinde tanımlayın)",
        "Süreç ve döngüleri adım adım anlatın",
        "Kısa-orta uzunlukta (291 karakter)",
    ],
    formula_based=False,
    scenario_based=False,
)

TURKCE_CONFIG = SubjectConfig(
    subject="Türkçe",
    target_length=660,
    length_tolerance=0.30,  # ±30% = 462-858 chars (relaxed for better generation)
    bloom_preferences={
        "Hatırlama": 0.15,
        "Anlama": 0.45,
        "Uygulama": 0.25,
        "Analiz": 0.15,
    },
    common_misconceptions=[],  # Less applicable for language
    question_style_notes=[
        "EN UZUN SORULAR (660 karakter - tüm dersler içinde en uzun!)",
        "Okuduğunu anlama soruları %45 oranında",
        "Parça-tabanlı sorular: Bir metin verilir, metin hakkında sorulur",
        "Dilbilgisi soruları %30 oranında",
        "Sözcük bilgisi soruları %25 oranında",
        "Bağlam çok önemli - metin uzun ve detaylı olmalı",
    ],
    formula_based=False,
    scenario_based=True,
)


# Configuration registry
SUBJECT_CONFIGS: Dict[str, SubjectConfig] = {
    "Kimya": KIMYA_CONFIG,
    "Matematik": MATEMATIK_CONFIG,
    "Fizik": FIZIK_CONFIG,
    "Biyoloji": BIYOLOJI_CONFIG,
    "Türkçe": TURKCE_CONFIG,
}


def get_subject_config(subject: str) -> Optional[SubjectConfig]:
    """Get configuration for a subject"""
    return SUBJECT_CONFIGS.get(subject)


def generate_subject_specific_prompt_addition(config: SubjectConfig) -> str:
    """
    Generate subject-specific prompt addition based on configuration

    Uses XML tags for Claude optimization (DEEP_RESEARCH_FINDINGS_2024.md)
    This text is appended to the base ÖSYM prompt to customize for each subject.
    """

    # Base length enforcement (CRITICAL!) - XML structured
    prompt = f"""
<subject_specific_rules>
<subject>{config.subject}</subject>

<length_target priority="critical">
  <target>{config.target_length} karakter</target>
  <acceptable_range>{config.min_length}-{config.max_length} karakter</acceptable_range>
  <warning>BU ARALIKTAN KESINLIKLE ÇIKMA!</warning>
  <reference>ÖSYM {config.subject} soruları ortalama {config.target_length} karakter uzunluğundadır.</reference>
</length_target>
"""

    # Add formula/scenario notes
    if config.formula_based:
        prompt += """
<calculation_requirements>
  <instruction>Formül ve hesaplama gerektiren soru oluştur</instruction>
  <requirements>
    - Tüm sayısal değerleri net belirtin
    - Birimleri unutmayın
    - Formülleri doğru yazın
    - Hesaplanabilir sorular oluşturun
  </requirements>
</calculation_requirements>
"""

    if config.scenario_based:
        prompt += """
<scenario_design>
  <instruction>Gerçek hayat senaryosu tabanlı soru oluştur</instruction>
  <requirements>
    - Gerçek hayat durumları kullanın
    - Başlangıç koşullarını net tanımlayın
    - Tüm gerekli bilgileri verin
    - Eksik bilgi bırakmayın
  </requirements>
</scenario_design>
"""

    # Add misconception-based distractors
    if config.common_misconceptions:
        prompt += """
<distractor_strategy>
  <instruction>Aşağıdaki yaygın öğrenci yanılgılarını çeldiriciler için kullanın</instruction>
  <common_misconceptions>
"""
        for i, misconception in enumerate(config.common_misconceptions[:5], 1):
            prompt += f'    <misconception id="{i}">{misconception}</misconception>\n'
        prompt += """  </common_misconceptions>
</distractor_strategy>
"""

    # Add style notes
    if config.question_style_notes:
        prompt += f"""
<style_guide>
  <subject>{config.subject}</subject>
  <notes>
"""
        for note in config.question_style_notes:
            prompt += f"    - {note}\n"
        prompt += """  </notes>
</style_guide>
"""

    # Add Bloom taxonomy guidance (EXPLICIT - Wave 1 improvement)
    if config.bloom_preferences:
        top_level = max(config.bloom_preferences.items(), key=lambda x: x[1])
        prompt += f"""
<cognitive_level>
  <primary_level>{top_level[0]}</primary_level>
  <priority>{int(top_level[1]*100)}%</priority>
  <instruction>Bu bilişsel seviyeye ({top_level[0]}) uygun soru tasarlayın</instruction>
  <bloom_taxonomy>
"""
        for level, percentage in config.bloom_preferences.items():
            prompt += f'    <level name="{level}" weight="{int(percentage*100)}%"/>\n'
        prompt += """  </bloom_taxonomy>
</cognitive_level>
"""

    prompt += "</subject_specific_rules>"
    return prompt


# Example usage
def get_enhanced_prompt(subject: str, base_prompt: str, exam_type: str = "TYT") -> str:
    """
    Enhance base ÖSYM prompt with subject-specific additions

    Args:
        subject: Subject name (e.g., "Kimya", "Matematik")
        base_prompt: Base ÖSYM generation prompt
        exam_type: TYT or AYT

    Returns:
        Enhanced prompt with subject-specific guidance
    """

    config = get_subject_config(subject)

    if not config:
        # No subject-specific config available, return base prompt
        return base_prompt

    # Generate subject-specific addition
    subject_addition = generate_subject_specific_prompt_addition(config)

    # Combine base + subject-specific
    enhanced_prompt = base_prompt + "\n" + subject_addition

    return enhanced_prompt


# Statistics for monitoring
def get_subject_statistics() -> Dict:
    """Get statistics about subject configurations"""

    stats = {
        "total_subjects": len(SUBJECT_CONFIGS),
        "length_range": {
            "shortest": min(c.target_length for c in SUBJECT_CONFIGS.values()),
            "longest": max(c.target_length for c in SUBJECT_CONFIGS.values()),
        },
        "subjects": {},
    }

    for name, config in SUBJECT_CONFIGS.items():
        stats["subjects"][name] = {
            "target_length": config.target_length,
            "length_range": f"{config.min_length}-{config.max_length}",
            "misconceptions_count": len(config.common_misconceptions),
            "formula_based": config.formula_based,
            "scenario_based": config.scenario_based,
        }

    return stats
