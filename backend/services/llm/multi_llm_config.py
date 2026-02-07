"""
Multi-LLM Configuration and Provider Management
Supports: OpenAI GPT-4, Anthropic Claude, Alibaba Qwen

Author: KIRO AI Team
Date: 2025-10-19
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field
import os


class LLMProvider(str, Enum):
    """Supported LLM Providers"""

    OPENAI = "openai"
    CLAUDE = "claude"
    QWEN = "qwen"
    GEMINI = "gemini"


class LLMCapability(str, Enum):
    """LLM Capabilities"""

    QUESTION_GENERATION = "question_generation"
    DISTRACTOR_GENERATION = "distractor_generation"
    QUALITY_SCORING = "quality_scoring"
    CONTENT_ANALYSIS = "content_analysis"
    FINE_TUNING = "fine_tuning"
    SEQUENTIAL_THINKING = "sequential_thinking"
    MATH_REASONING = "math_reasoning"
    STEP_BY_STEP = "step_by_step"


class LLMModelConfig(BaseModel):
    """LLM Model Configuration"""

    provider: LLMProvider
    model_name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    capabilities: List[LLMCapability] = Field(default_factory=list)

    # Fine-tuning specific
    fine_tuned_model_id: Optional[str] = None
    training_config: Optional[Dict[str, Any]] = None

    # Cost and performance
    cost_per_1k_tokens: float = 0.0
    avg_response_time_ms: float = 0.0

    model_config = ConfigDict(use_enum_values=True)


class MultiLLMConfig:
    """Multi-LLM System Configuration"""

    # OpenAI GPT-4 Configuration
    OPENAI_CONFIG = LLMModelConfig(
        provider=LLMProvider.OPENAI,
        model_name="gpt-4o",  # Updated to GPT-4o (latest stable model)
        api_key=os.getenv("OPENAI_API_KEY"),
        max_tokens=4096,
        temperature=0.7,
        capabilities=[
            LLMCapability.QUESTION_GENERATION,
            LLMCapability.DISTRACTOR_GENERATION,
            LLMCapability.QUALITY_SCORING,
            LLMCapability.CONTENT_ANALYSIS,
            LLMCapability.FINE_TUNING,
        ],
        cost_per_1k_tokens=0.01,  # $0.01 per 1K tokens (prompt)
        avg_response_time_ms=2000.0,
    )

    # Anthropic Claude Configuration
    CLAUDE_CONFIG = LLMModelConfig(
        provider=LLMProvider.CLAUDE,
        model_name="claude-sonnet-4-5-20250929",  # Claude Sonnet 4.5 (Latest)
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=4096,
        temperature=0.7,
        capabilities=[
            LLMCapability.QUESTION_GENERATION,
            LLMCapability.DISTRACTOR_GENERATION,
            LLMCapability.QUALITY_SCORING,
            LLMCapability.CONTENT_ANALYSIS,
        ],
        cost_per_1k_tokens=0.003,  # $3 per million tokens
        avg_response_time_ms=1500.0,
    )

    # Alibaba Qwen Configuration (Local/Cloud)
    QWEN_CONFIG = LLMModelConfig(
        provider=LLMProvider.QWEN,
        model_name="Qwen/Qwen2.5-72B-Instruct",  # Qwen 2.5 72B Instruct
        api_key=os.getenv("QWEN_API_KEY"),  # For cloud API
        api_base=os.getenv(
            "QWEN_API_BASE", "http://localhost:8001"
        ),  # Local deployment
        max_tokens=4096,
        temperature=0.7,
        capabilities=[
            LLMCapability.QUESTION_GENERATION,
            LLMCapability.DISTRACTOR_GENERATION,
            LLMCapability.CONTENT_ANALYSIS,
            LLMCapability.FINE_TUNING,
            LLMCapability.SEQUENTIAL_THINKING,
            LLMCapability.STEP_BY_STEP,
        ],
        cost_per_1k_tokens=0.0,  # Free if self-hosted
        avg_response_time_ms=3000.0,
    )

    # Google Gemini Configuration (Thinking Mode)
    GEMINI_CONFIG = LLMModelConfig(
        provider=LLMProvider.GEMINI,
        model_name="gemini-2.0-flash-thinking-exp",  # Gemini 2.0 Flash Thinking
        api_key=os.getenv("GOOGLE_API_KEY"),
        max_tokens=8192,
        temperature=0.7,
        capabilities=[
            LLMCapability.QUESTION_GENERATION,
            LLMCapability.DISTRACTOR_GENERATION,
            LLMCapability.QUALITY_SCORING,
            LLMCapability.CONTENT_ANALYSIS,
            LLMCapability.SEQUENTIAL_THINKING,
            LLMCapability.MATH_REASONING,
            LLMCapability.STEP_BY_STEP,
        ],
        cost_per_1k_tokens=0.0,  # Free tier available
        avg_response_time_ms=2500.0,
    )

    # Fine-tuning configurations
    FINE_TUNING_CONFIGS = {
        LLMProvider.OPENAI: {
            "training_file": "osym_questions_train.jsonl",
            "validation_file": "osym_questions_val.jsonl",
            "n_epochs": 3,
            "batch_size": 4,
            "learning_rate_multiplier": 0.1,
            "suffix": "osym-question-gen-v1",
        },
        LLMProvider.QWEN: {
            "training_file": "osym_questions_train.jsonl",
            "validation_file": "osym_questions_val.jsonl",
            "n_epochs": 5,
            "batch_size": 8,
            "learning_rate": 2e-5,
            "lora_r": 8,
            "lora_alpha": 32,
            "save_steps": 100,
        },
    }

    # Ensemble Strategy Configuration
    ENSEMBLE_STRATEGY = {
        "voting": {
            "enabled": True,
            "min_agreement": 0.5,  # 2 out of 4 LLMs must agree
            "weights": {
                LLMProvider.GEMINI: 0.30,  # Best for sequential thinking
                LLMProvider.OPENAI: 0.25,
                LLMProvider.CLAUDE: 0.25,
                LLMProvider.QWEN: 0.20,
            },
        },
        "quality_threshold": {
            "min_bleu_score": 0.4,
            "min_bertscore": 0.7,
            "min_irt_difficulty": 0.3,
            "max_irt_difficulty": 0.8,
        },
        "fallback_order": [
            LLMProvider.GEMINI,  # Best for thinking/reasoning
            LLMProvider.CLAUDE,  # Fastest and cost-effective
            LLMProvider.QWEN,  # Free if self-hosted
            LLMProvider.OPENAI,  # Most capable but expensive
        ],
        "sequential_thinking_order": [
            LLMProvider.GEMINI,  # Native thinking mode
            LLMProvider.CLAUDE,  # Strong reasoning
            LLMProvider.OPENAI,  # GPT-4 o1 style
            LLMProvider.QWEN,  # Local option
        ],
    }

    # Turkish Language Specific Prompts
    TURKISH_OSYM_PROMPTS = {
        "system_prompt": """Sen bir ÖSYM soru uzmanısısın. Türkiye'de üniversite sınavlarına hazırlanan öğrenciler için YKS (TYT/AYT/YDT) formatında sorular üretiyorsun.

Görevin:
1. MEB müfredatına uygun sorular oluşturmak
2. ÖSYM formatında (çoktan seçmeli, 5 şık) sorular yazmak
3. Türkçe dilbilgisi ve terminolojiye tam uyum sağlamak
4. Zorluk seviyesini belirtilen IRT parametrelerine göre ayarlamak""",
        "question_generation_prompt": """Aşağıdaki kriterlere göre bir ÖSYM sorusu oluştur:

Konu: {topic}
Alt Konu: {subtopic}
Zorluk Seviyesi: {difficulty}  # kolay (0.2-0.4), orta (0.4-0.6), zor (0.6-0.8)
Bloom Seviyesi: {bloom_level}  # 1:Hatırlama, 2:Anlama, 3:Uygulama, 4:Analiz, 5:Sentez, 6:Değerlendirme
Sınav Türü: {exam_type}  # TYT, AYT, YDT

Çıktı formatı (JSON):
{{
    "stem": "Soru metni buraya",
    "options": [
        "A) Doğru cevap",
        "B) Çeldirici 1",
        "C) Çeldirici 2",
        "D) Çeldirici 3",
        "E) Çeldirici 4"
    ],
    "correct_answer": 0,  # Index of correct answer (0-4)
    "explanation": "Çözüm açıklaması",
    "keywords": ["anahtar", "kelimeler"],
    "estimated_time_seconds": 90
}}""",
        "distractor_generation_prompt": """Aşağıdaki ÖSYM sorusu için 4 adet çeldirici (distractor) üret:

Soru: {question_stem}
Doğru Cevap: {correct_answer}
Konu: {topic}

Çeldiriciler:
1. Akla yatkın olmalı (plausible)
2. Yaygın öğrenci hatalarını içermeli
3. Doğru cevapla benzer yapıda olmalı
4. Birbirinden farklı olmalı

Çıktı formatı (JSON):
{{
    "distractors": [
        "Çeldirici 1 metni",
        "Çeldirici 2 metni",
        "Çeldirici 3 metni",
        "Çeldirici 4 metni"
    ],
    "reasoning": [
        "Çeldirici 1 neden akla yatkın",
        "Çeldirici 2 neden akla yatkın",
        "Çeldirici 3 neden akla yatkın",
        "Çeldirici 4 neden akla yatkın"
    ]
}}""",
        "quality_scoring_prompt": """Aşağıdaki ÖSYM sorusunu 0-100 arası puanla:

Soru: {question_stem}
Şıklar: {options}
Doğru Cevap: {correct_answer}

Değerlendirme Kriterleri:
1. ÖSYM formatına uygunluk (0-20 puan)
2. Türkçe dilbilgisi ve akıcılık (0-20 puan)
3. Çeldiricilerin kalitesi (0-20 puan)
4. Konu uygunluğu (0-20 puan)
5. Zorluk seviyesi uygunluğu (0-20 puan)

Çıktı formatı (JSON):
{{
    "total_score": 85,
    "scores": {{
        "format_compliance": 18,
        "language_quality": 19,
        "distractor_quality": 17,
        "topic_relevance": 16,
        "difficulty_appropriate": 15
    }},
    "feedback": "Detaylı geri bildirim",
    "improvements": ["İyileştirme önerisi 1", "İyileştirme önerisi 2"]
}}""",
    }

    @classmethod
    def get_config(cls, provider: LLMProvider) -> LLMModelConfig:
        """Get configuration for specific provider"""
        configs = {
            LLMProvider.OPENAI: cls.OPENAI_CONFIG,
            LLMProvider.CLAUDE: cls.CLAUDE_CONFIG,
            LLMProvider.QWEN: cls.QWEN_CONFIG,
            LLMProvider.GEMINI: cls.GEMINI_CONFIG,
        }
        return configs.get(provider)

    @classmethod
    def get_best_provider_for_capability(
        cls, capability: LLMCapability, prefer_cost_effective: bool = False
    ) -> LLMProvider:
        """Get best LLM provider for specific capability"""

        # Sequential thinking: Gemini is best
        if capability in [
            LLMCapability.SEQUENTIAL_THINKING,
            LLMCapability.MATH_REASONING,
            LLMCapability.STEP_BY_STEP,
        ]:
            if capability in cls.GEMINI_CONFIG.capabilities:
                return LLMProvider.GEMINI
            elif capability in cls.CLAUDE_CONFIG.capabilities:
                return LLMProvider.CLAUDE

        if prefer_cost_effective:
            # Prefer Gemini (free) > Qwen (free if self-hosted) > Claude (cheap)
            if capability in cls.GEMINI_CONFIG.capabilities:
                return LLMProvider.GEMINI
            elif capability in cls.QWEN_CONFIG.capabilities:
                return LLMProvider.QWEN
            elif capability in cls.CLAUDE_CONFIG.capabilities:
                return LLMProvider.CLAUDE
            elif capability in cls.OPENAI_CONFIG.capabilities:
                return LLMProvider.OPENAI
        else:
            # Prefer quality: Gemini (thinking) > OpenAI > Claude > Qwen
            if capability in cls.GEMINI_CONFIG.capabilities:
                return LLMProvider.GEMINI
            elif capability in cls.OPENAI_CONFIG.capabilities:
                return LLMProvider.OPENAI
            elif capability in cls.CLAUDE_CONFIG.capabilities:
                return LLMProvider.CLAUDE
            elif capability in cls.QWEN_CONFIG.capabilities:
                return LLMProvider.QWEN

        raise ValueError(f"No provider supports capability: {capability}")
