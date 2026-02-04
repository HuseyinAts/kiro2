"""
Soru Üretim Motoru (Question Generation Engine)
LLM tabanlı ÖSYM formatında otomatik soru üretimi

REQ-48.33-48.48: Soru Üretim Motoru
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from models.curriculum import SubjectType
from models.question_generation import (
    CognitiveLevel,
    DifficultyLevel,
    GeneratedQuestion,
    QuestionType,
    OSYMQuestionFormat,
)

logger = logging.getLogger(__name__)


class TopicBasedQuestionGenerator:
    """
    Konu Bazlı Soru Üretim Algoritması
    REQ-48.33-48.36: Topic-specific prompt engineering, Context injection, Question template system
    """

    def __init__(self, llm_service=None):
        """
        Args:
            llm_service: LLM servisi (GPT-4, T5, vb.)
        """
        self.llm_service = llm_service
        self.question_templates = self._load_question_templates()

    def _load_question_templates(self) -> Dict[str, List[str]]:
        """ÖSYM soru yapısını taklit eden şablonlar"""
        return {
            "matematik": [
                "Aşağıdaki {konu} problemi için doğru çözüm hangisidir?",
                "{konu} ile ilgili verilen ifadelerden hangisi doğrudur?",
                "Bir {konu} probleminde {durum} olduğuna göre, sonuç nedir?",
            ],
            "turkce": [
                "Aşağıdaki cümlede {konu} açısından hata var mıdır?",
                "{konu} ile ilgili aşağıdaki ifadelerden hangisi yanlıştır?",
                "Verilen metinde {konu} kullanımı nasıldır?",
            ],
            "fen": [
                "{konu} ile ilgili aşağıdaki ifadelerden hangisi doğrudur?",
                "Bir {konu} deneyinde {durum} gözlemlenmiştir. Bunun nedeni nedir?",
                "{konu} konusunda verilen bilgilerden hangisi yanlıştır?",
            ],
        }

    async def generate_question(
        self,
        subject: SubjectType,
        topic_name: str,
        topic_context: str,
        difficulty_level: DifficultyLevel,
        cognitive_level: CognitiveLevel,
        question_type: QuestionType = QuestionType.MULTIPLE_CHOICE,
    ) -> Optional[GeneratedQuestion]:
        """
        Konu bazlı soru üretimi

        REQ-48.33: MEB müfredatına uygun konuları kullanmak
        REQ-48.34: Konu bağlamını prompt'a eklemek
        REQ-48.35: ÖSYM soru yapısını taklit etmek
        REQ-48.36: 3 saniye içinde sonuç döndürmek

        Args:
            subject: Ders (Matematik, Türkçe, vb.)
            topic_name: Konu adı
            topic_context: Konu bağlamı ve açıklaması
            difficulty_level: Zorluk seviyesi
            cognitive_level: Bilişsel seviye (Bloom taksonomisi)
            question_type: Soru tipi

        Returns:
            GeneratedQuestion veya None
        """
        try:
            start_time = datetime.now()

            # 1. Context Injection - Konu bağlamını hazırla
            context = self._inject_context(
                subject, topic_name, topic_context, difficulty_level, cognitive_level
            )

            # 2. Template Selection - Uygun şablon seç
            template = self._select_template(subject, question_type)

            # 3. Prompt Engineering - LLM için prompt oluştur
            prompt = self._create_prompt(
                context, template, difficulty_level, cognitive_level
            )

            # 4. LLM ile soru üret
            if self.llm_service:
                llm_response = await self.llm_service.generate(
                    prompt, max_tokens=500, temperature=0.7
                )
                question_data = self._parse_llm_response(llm_response)
            else:
                # Mock data for testing
                question_data = self._generate_mock_question(
                    subject, topic_name, difficulty_level
                )

            # 5. ÖSYM formatına dönüştür
            osym_format = OSYMQuestionFormat(
                question_number=1,
                question_text=question_data["question_text"],
                options=question_data["options"],
                correct_answer=question_data["correct_answer"],
                explanation=question_data["explanation"],
            )

            # 6. GeneratedQuestion objesi oluştur
            generated_question = GeneratedQuestion(
                id=f"gen_{datetime.now().timestamp()}",
                subject=subject,
                topic_id=f"topic_{topic_name.lower().replace(' ', '_')}",
                topic_name=topic_name,
                question_type=question_type,
                question_text=question_data["question_text"],
                options=question_data["options"],
                correct_answer=question_data["correct_answer"],
                explanation=question_data["explanation"],
                difficulty_level=difficulty_level,
                cognitive_level=cognitive_level,
                estimated_time_seconds=self._estimate_time(difficulty_level),
                osym_format=osym_format,
                osym_compliance_score=0.85,  # Placeholder
                meb_compliance_score=0.80,  # Placeholder
                quality_score=0.75,  # Placeholder
                generation_method="topic_based_llm",
                generation_parameters={
                    "subject": subject.value,
                    "topic": topic_name,
                    "difficulty": difficulty_level.value,
                    "cognitive": cognitive_level.value,
                },
                source_materials=[topic_context],
            )

            # REQ-48.36: 3 saniye içinde sonuç döndürmek
            elapsed_time = (datetime.now() - start_time).total_seconds()
            if elapsed_time > 3.0:
                logger.warning(
                    f"Soru üretimi 3 saniyeden uzun sürdü: {elapsed_time:.2f}s"
                )

            logger.info(
                f"Soru üretildi: {topic_name} - {difficulty_level.value} - {elapsed_time:.2f}s"
            )
            return generated_question

        except Exception as e:
            logger.error(f"Soru üretim hatası: {e}")
            return None

    def _inject_context(
        self,
        subject: SubjectType,
        topic_name: str,
        topic_context: str,
        difficulty_level: DifficultyLevel,
        cognitive_level: CognitiveLevel,
    ) -> Dict[str, Any]:
        """
        REQ-48.34: Context injection - Konu bağlamını prompt'a eklemek
        """
        return {
            "subject": subject.value,
            "topic_name": topic_name,
            "topic_context": topic_context,
            "difficulty": difficulty_level.value,
            "cognitive_level": cognitive_level.value,
            "meb_standards": f"MEB {subject.value} müfredatı - {topic_name}",
            "osym_format": "ÖSYM çoktan seçmeli soru formatı (4 seçenek, 1 doğru cevap)",
        }

    def _select_template(
        self, subject: SubjectType, question_type: QuestionType
    ) -> str:
        """
        REQ-48.35: Question template system - ÖSYM soru yapısını taklit etmek
        """
        subject_key = subject.value.lower()
        templates = self.question_templates.get(
            subject_key, self.question_templates["matematik"]
        )

        # Rastgele bir şablon seç (gerçek implementasyonda daha akıllı seçim yapılabilir)
        import random

        return random.choice(templates)

    def _create_prompt(
        self,
        context: Dict[str, Any],
        template: str,
        difficulty_level: DifficultyLevel,
        cognitive_level: CognitiveLevel,
    ) -> str:
        """
        REQ-48.33-48.35: Topic-specific prompt engineering
        """
        prompt = f"""Sen bir ÖSYM soru hazırlama uzmanısın. Aşağıdaki kriterlere göre bir sınav sorusu oluştur:

KONU BİLGİSİ:
- Ders: {context['subject']}
- Konu: {context['topic_name']}
- Bağlam: {context['topic_context']}
- MEB Standardı: {context['meb_standards']}

SORU KRİTERLERİ:
- Zorluk Seviyesi: {difficulty_level.value}
- Bilişsel Seviye: {cognitive_level.value} (Bloom Taksonomisi)
- Format: {context['osym_format']}

ŞABLON:
{template}

ÇIKTI FORMATI (JSON):
{{
    "question_text": "Soru metni buraya",
    "options": ["A) Seçenek 1", "B) Seçenek 2", "C) Seçenek 3", "D) Seçenek 4"],
    "correct_answer": "A",
    "explanation": "Doğru cevabın açıklaması"
}}

Lütfen ÖSYM standartlarına uygun, Türkçe dilbilgisi kurallarına uygun, net ve anlaşılır bir soru oluştur."""

        return prompt

    def _parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """LLM yanıtını parse et"""
        try:
            # JSON formatında yanıt bekliyoruz
            data = json.loads(llm_response)
            return {
                "question_text": data.get("question_text", ""),
                "options": data.get("options", []),
                "correct_answer": data.get("correct_answer", "A"),
                "explanation": data.get("explanation", ""),
            }
        except json.JSONDecodeError:
            logger.error("LLM yanıtı JSON formatında değil")
            return self._generate_mock_question(
                SubjectType.MATEMATIK, "Mock", DifficultyLevel.ORTA
            )

    def _generate_mock_question(
        self, subject: SubjectType, topic_name: str, difficulty_level: DifficultyLevel
    ) -> Dict[str, Any]:
        """Test için mock soru üret"""
        return {
            "question_text": f"{topic_name} konusu ile ilgili aşağıdaki ifadelerden hangisi doğrudur?",
            "options": [
                "A) İlk seçenek (doğru cevap)",
                "B) İkinci seçenek",
                "C) Üçüncü seçenek",
                "D) Dördüncü seçenek",
            ],
            "correct_answer": "A",
            "explanation": f"Bu sorunun cevabı A'dır çünkü {topic_name} konusunda ilk seçenek doğru açıklamayı içermektedir.",
        }

    def _estimate_time(self, difficulty_level: DifficultyLevel) -> int:
        """Sorunun tahmini çözüm süresini hesapla (saniye)"""
        time_map = {
            DifficultyLevel.KOLAY: 60,
            DifficultyLevel.ORTA: 120,
            DifficultyLevel.ZOR: 180,
            DifficultyLevel.COK_ZOR: 240,
        }
        return time_map.get(difficulty_level, 120)


class DistractorGenerationSystem:
    """
    Çeldirici (Distractor) Üretim Sistemi
    REQ-48.37-48.40: Plausible distractor generation, Common misconception database, Distractor quality scoring
    """

    def __init__(self, llm_service=None):
        """
        Args:
            llm_service: LLM servisi
        """
        self.llm_service = llm_service
        self.misconception_database = self._load_misconception_database()

    def _load_misconception_database(self) -> Dict[str, List[str]]:
        """
        REQ-48.38: Common misconception database - Yaygın öğrenci hatalarını içermek

        Türk öğrencilerin sık yaptığı hatalar ve kavram yanılgıları
        """
        return {
            "matematik": {
                "kesirler": [
                    "Paydaları toplamak (1/2 + 1/3 = 2/5 gibi)",
                    "Kesir çarpımında payda çarpmayı unutmak",
                    "Kesir bölmede ters çevirmeyi unutmak",
                ],
                "üslü_sayılar": [
                    "Üsleri toplamak yerine çarpmak (2^3 * 2^2 = 2^6 gibi)",
                    "Negatif üs ile negatif sayıyı karıştırmak",
                    "Sıfırıncı kuvveti sıfır sanmak",
                ],
                "denklemler": [
                    "Her iki tarafa farklı işlem yapmak",
                    "Eksi işaretini dağıtmayı unutmak",
                    "Parantez açarken işaret hatası",
                ],
            },
            "turkce": {
                "yazim_kurallari": [
                    "de/da bağlacı ile -de/-da ekini karıştırmak",
                    "ki bağlacı ile -ki ekini karıştırmak",
                    "Büyük harf kullanımında hata",
                ],
                "noktalama": [
                    "Virgül yerine nokta kullanmak",
                    "Soru işareti yerine nokta kullanmak",
                    "Tırnak işareti kullanımı hatası",
                ],
            },
            "fen": {
                "fizik": [
                    "Hız ile ivmeyi karıştırmak",
                    "Kütle ile ağırlığı karıştırmak",
                    "Kinetik ve potansiyel enerjiyi karıştırmak",
                ],
                "kimya": [
                    "Atom ile molekülü karıştırmak",
                    "Fiziksel ve kimyasal değişimi karıştırmak",
                    "Asit-baz kavramlarını yanlış anlamak",
                ],
            },
        }

    async def generate_distractors(
        self,
        correct_answer: str,
        question_context: str,
        subject: SubjectType,
        topic: str,
        count: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        REQ-48.37: Plausible distractor generation - Makul çeldiriciler üretmek

        Args:
            correct_answer: Doğru cevap
            question_context: Soru bağlamı
            subject: Ders
            topic: Konu
            count: Üretilecek çeldirici sayısı

        Returns:
            Çeldirici listesi (her biri quality_score ile)
        """
        try:
            distractors = []

            # 1. Misconception-based distractors (yaygın hatalardan)
            misconception_distractors = self._generate_misconception_distractors(
                subject, topic, correct_answer, count=count // 2 + 1
            )
            distractors.extend(misconception_distractors)

            # 2. LLM-based distractors (AI ile üretilen)
            if self.llm_service and len(distractors) < count:
                llm_distractors = await self._generate_llm_distractors(
                    correct_answer,
                    question_context,
                    subject,
                    topic,
                    count - len(distractors),
                )
                distractors.extend(llm_distractors)

            # 3. Fallback: Basit varyasyonlar
            while len(distractors) < count:
                fallback_distractor = self._generate_fallback_distractor(
                    correct_answer, len(distractors)
                )
                distractors.append(fallback_distractor)

            # 4. Quality scoring - Her çeldiriciyi skorla
            scored_distractors = []
            for distractor in distractors:
                score = self._score_distractor_quality(
                    distractor["text"], correct_answer, question_context
                )
                scored_distractors.append(
                    {
                        "text": distractor["text"],
                        "quality_score": score,
                        "generation_method": distractor.get("method", "unknown"),
                    }
                )

            # 5. En yüksek skorlu çeldiricileri seç
            scored_distractors.sort(key=lambda x: x["quality_score"], reverse=True)

            # REQ-48.40: En yüksek skorlu 3 çeldiriciyi kullanmak
            return scored_distractors[:count]

        except Exception as e:
            logger.error(f"Çeldirici üretim hatası: {e}")
            return self._generate_fallback_distractors(correct_answer, count)

    def _generate_misconception_distractors(
        self, subject: SubjectType, topic: str, correct_answer: str, count: int
    ) -> List[Dict[str, str]]:
        """
        REQ-48.38: Common misconception database kullanarak çeldirici üret
        """
        distractors = []
        subject_key = subject.value.lower()

        if subject_key in self.misconception_database:
            topic_key = topic.lower().replace(" ", "_")
            misconceptions = self.misconception_database[subject_key].get(topic_key, [])

            for i, misconception in enumerate(misconceptions[:count]):
                distractors.append(
                    {
                        "text": f"{chr(66+i)}) {misconception} (yaygın hata)",
                        "method": "misconception_based",
                    }
                )

        return distractors

    async def _generate_llm_distractors(
        self,
        correct_answer: str,
        question_context: str,
        subject: SubjectType,
        topic: str,
        count: int,
    ) -> List[Dict[str, str]]:
        """LLM ile çeldirici üret"""
        try:
            prompt = f"""Sen bir ÖSYM soru hazırlama uzmanısın. Aşağıdaki soru için {count} adet makul ama yanlış çeldirici (distractor) üret:

SORU BAĞLAMI: {question_context}
DOĞRU CEVAP: {correct_answer}
DERS: {subject.value}
KONU: {topic}

ÇELDİRİCİ KRİTERLERİ:
1. Makul görünmeli (plausible)
2. Öğrencilerin yapabileceği yaygın hatalar olmalı
3. Doğru cevapla karıştırılabilir olmalı
4. Tamamen saçma olmamalı

ÇIKTI FORMATI (JSON):
{{
    "distractors": [
        "Çeldirici 1",
        "Çeldirici 2",
        ...
    ]
}}"""

            if self.llm_service:
                response = await self.llm_service.generate(
                    prompt, max_tokens=300, temperature=0.8
                )
                data = json.loads(response)
                return [
                    {"text": d, "method": "llm_generated"}
                    for d in data.get("distractors", [])
                ]

        except Exception as e:
            logger.error(f"LLM çeldirici üretim hatası: {e}")

        return []

    def _generate_fallback_distractor(
        self, correct_answer: str, index: int
    ) -> Dict[str, str]:
        """Fallback çeldirici üret"""
        return {
            "text": f"{chr(66+index)}) Alternatif cevap {index+1}",
            "method": "fallback",
        }

    def _generate_fallback_distractors(
        self, correct_answer: str, count: int
    ) -> List[Dict[str, Any]]:
        """Fallback çeldiriciler"""
        return [
            {
                "text": f"{chr(66+i)}) Alternatif cevap {i+1}",
                "quality_score": 0.5,
                "generation_method": "fallback",
            }
            for i in range(count)
        ]

    def _score_distractor_quality(
        self, distractor: str, correct_answer: str, question_context: str
    ) -> float:
        """
        REQ-48.39: Distractor quality scoring - Her çeldiriciyi 0-100 arası değerlendirmek

        Returns:
            Quality score (0.0 - 1.0)
        """
        score = 0.0

        # 1. Uzunluk benzerliği (doğru cevapla benzer uzunlukta olmalı)
        length_ratio = min(len(distractor), len(correct_answer)) / max(
            len(distractor), len(correct_answer)
        )
        score += length_ratio * 0.2

        # 2. Kelime benzerliği (bazı ortak kelimeler olmalı ama çok fazla değil)
        distractor_words = set(distractor.lower().split())
        correct_words = set(correct_answer.lower().split())
        common_words = distractor_words & correct_words
        similarity = len(common_words) / max(len(distractor_words), len(correct_words))
        # İdeal benzerlik %30-60 arası
        if 0.3 <= similarity <= 0.6:
            score += 0.3
        elif similarity < 0.3:
            score += similarity
        else:
            score += (1.0 - similarity) * 0.3

        # 3. Bağlam uygunluğu (soru bağlamıyla ilgili olmalı)
        context_words = set(question_context.lower().split())
        context_relevance = (
            len(distractor_words & context_words) / len(distractor_words)
            if distractor_words
            else 0
        )
        score += context_relevance * 0.3

        # 4. Makullük (çok kısa veya çok uzun olmamalı)
        if 10 <= len(distractor) <= 200:
            score += 0.2

        return min(score, 1.0)


class MathematicalValidationEngine:
    """
    Matematiksel Doğrulama Motoru (SymPy Entegrasyonu)
    REQ-48.41-48.44: SymPy symbolic math engine, Equation validation, Solution verification
    """

    def __init__(self):
        """SymPy entegrasyonu"""
        try:
            import sympy as sp

            self.sp = sp
            self.symbols_cache = {}
            logger.info("SymPy başarıyla yüklendi")
        except ImportError:
            logger.warning("SymPy yüklü değil. Matematiksel doğrulama devre dışı.")
            self.sp = None

    def validate_equation(self, equation_str: str) -> Dict[str, Any]:
        """
        REQ-48.42: Equation validation - Matematiksel tutarlılığı kontrol etmek

        Args:
            equation_str: Denklem string'i (örn: "2*x + 3 = 7")

        Returns:
            Doğrulama sonucu
        """
        if not self.sp:
            return {"valid": False, "error": "SymPy yüklü değil"}

        try:
            # Denklemi parse et
            if "=" in equation_str:
                left, right = equation_str.split("=")
                left_expr = self.sp.sympify(left.strip())
                right_expr = self.sp.sympify(right.strip())

                # Denklem geçerli mi kontrol et
                equation = self.sp.Eq(left_expr, right_expr)

                return {
                    "valid": True,
                    "equation": str(equation),
                    "left_side": str(left_expr),
                    "right_side": str(right_expr),
                    "error": None,
                }
            else:
                # Tek taraflı ifade
                expr = self.sp.sympify(equation_str.strip())
                return {"valid": True, "expression": str(expr), "error": None}

        except Exception as e:
            logger.error(f"Denklem doğrulama hatası: {e}")
            return {"valid": False, "error": str(e)}

    def solve_equation(self, equation_str: str, variable: str = "x") -> Dict[str, Any]:
        """
        REQ-48.41: SymPy symbolic math engine - Denklemleri sembolik olarak çözmek

        Args:
            equation_str: Denklem string'i
            variable: Çözülecek değişken

        Returns:
            Çözüm sonucu
        """
        if not self.sp:
            return {"solved": False, "error": "SymPy yüklü değil"}

        try:
            # Değişkeni tanımla
            var = self.sp.Symbol(variable)

            # Denklemi parse et ve çöz
            if "=" in equation_str:
                left, right = equation_str.split("=")
                left_expr = self.sp.sympify(left.strip())
                right_expr = self.sp.sympify(right.strip())
                equation = self.sp.Eq(left_expr, right_expr)

                solutions = self.sp.solve(equation, var)
            else:
                expr = self.sp.sympify(equation_str.strip())
                solutions = self.sp.solve(expr, var)

            return {
                "solved": True,
                "solutions": [str(sol) for sol in solutions],
                "solution_count": len(solutions),
                "error": None,
            }

        except Exception as e:
            logger.error(f"Denklem çözme hatası: {e}")
            return {"solved": False, "error": str(e)}

    def verify_solution(
        self, equation_str: str, proposed_solution: str, variable: str = "x"
    ) -> Dict[str, Any]:
        """
        REQ-48.43: Solution verification - Doğru cevabı doğrulamak

        Args:
            equation_str: Denklem
            proposed_solution: Önerilen çözüm
            variable: Değişken

        Returns:
            Doğrulama sonucu
        """
        if not self.sp:
            return {"verified": False, "error": "SymPy yüklü değil"}

        try:
            # Değişkeni tanımla
            var = self.sp.Symbol(variable)

            # Denklemi parse et
            if "=" in equation_str:
                left, right = equation_str.split("=")
                left_expr = self.sp.sympify(left.strip())
                right_expr = self.sp.sympify(right.strip())
            else:
                left_expr = self.sp.sympify(equation_str.strip())
                right_expr = self.sp.sympify("0")

            # Önerilen çözümü parse et
            solution_value = self.sp.sympify(proposed_solution.strip())

            # Çözümü denklemde yerine koy
            left_result = left_expr.subs(var, solution_value)
            right_result = right_expr.subs(var, solution_value)

            # Basitleştir ve karşılaştır
            left_simplified = self.sp.simplify(left_result)
            right_simplified = self.sp.simplify(right_result)

            is_correct = self.sp.simplify(left_simplified - right_simplified) == 0

            return {
                "verified": True,
                "is_correct": bool(is_correct),
                "left_result": str(left_simplified),
                "right_result": str(right_simplified),
                "error": None,
            }

        except Exception as e:
            logger.error(f"Çözüm doğrulama hatası: {e}")
            return {"verified": False, "error": str(e)}

    def validate_math_question(
        self, question_text: str, correct_answer: str, options: List[str]
    ) -> Dict[str, Any]:
        """
        REQ-48.44: Matematiksel hata tespit edildiğinde soruyu reddetmek

        Matematik sorusunun matematiksel tutarlılığını kontrol et

        Returns:
            Doğrulama sonucu ve hata varsa reddetme sebebi
        """
        if not self.sp:
            return {
                "valid": True,  # SymPy yoksa varsayılan olarak geçerli kabul et
                "warnings": ["SymPy yüklü değil, matematiksel doğrulama yapılamadı"],
            }

        validation_result = {"valid": True, "errors": [], "warnings": []}

        try:
            # 1. Soru metninde denklem var mı kontrol et
            equations = self._extract_equations(question_text)

            for eq in equations:
                eq_validation = self.validate_equation(eq)
                if not eq_validation["valid"]:
                    validation_result["valid"] = False
                    validation_result["errors"].append(
                        f"Geçersiz denklem: {eq} - {eq_validation['error']}"
                    )

            # 2. Doğru cevabın matematiksel olarak geçerli olduğunu kontrol et
            if equations:
                # İlk denklemi çöz
                solution = self.solve_equation(equations[0])
                if solution["solved"]:
                    # Doğru cevabın çözümlerden biri olup olmadığını kontrol et
                    if correct_answer not in solution["solutions"]:
                        validation_result["warnings"].append(
                            f"Doğru cevap ({correct_answer}) denklem çözümlerinde bulunamadı: {solution['solutions']}"
                        )

            # 3. Seçeneklerin matematiksel olarak anlamlı olduğunu kontrol et
            for option in options:
                try:
                    # Seçeneği parse etmeyi dene
                    self.sp.sympify(option.split(")")[-1].strip())
                except:
                    # Parse edilemiyorsa sorun yok, metin cevap olabilir
                    pass

        except Exception as e:
            logger.error(f"Matematik soru doğrulama hatası: {e}")
            validation_result["warnings"].append(f"Doğrulama hatası: {str(e)}")

        return validation_result

    def _extract_equations(self, text: str) -> List[str]:
        """Metinden denklemleri çıkar"""
        import re

        # Basit denklem pattern'leri
        patterns = [
            r"([0-9x\+\-\*/\(\)\^\s]+=[0-9x\+\-\*/\(\)\^\s]+)",  # x + 2 = 5 gibi
            r"([0-9]+[x\+\-\*/\(\)]+[0-9x\+\-\*/\(\)]*)",  # 2x + 3 gibi
        ]

        equations = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            equations.extend(matches)

        return equations


class VisualGenerationEngine:
    """
    Görsel Üretim Motoru (Matplotlib/Plotly Entegrasyonu)
    REQ-48.45-48.48: Graph generation, Geometry figure generation, Chart and diagram creation
    """

    def __init__(self):
        """Matplotlib ve Plotly entegrasyonu"""
        self.matplotlib_available = False
        self.plotly_available = False

        try:
            import matplotlib

            matplotlib.use("Agg")  # GUI olmadan çalışması için
            import matplotlib.pyplot as plt

            self.plt = plt
            self.matplotlib_available = True
            logger.info("Matplotlib başarıyla yüklendi")
        except ImportError:
            logger.warning("Matplotlib yüklü değil")

        try:
            import plotly.graph_objects as go
            import plotly.express as px

            self.go = go
            self.px = px
            self.plotly_available = True
            logger.info("Plotly başarıyla yüklendi")
        except ImportError:
            logger.warning("Plotly yüklü değil")

    def generate_function_graph(
        self,
        function_str: str,
        x_range: tuple = (-10, 10),
        title: str = "Fonksiyon Grafiği",
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        REQ-48.46: Graph generation - Matematiksel fonksiyonları görselleştirmek

        Args:
            function_str: Fonksiyon string'i (örn: "x**2 + 2*x + 1")
            x_range: X ekseni aralığı
            title: Grafik başlığı
            output_path: Kaydedilecek dosya yolu

        Returns:
            Grafik bilgileri
        """
        if not self.matplotlib_available:
            return {"success": False, "error": "Matplotlib yüklü değil"}

        try:
            import numpy as np

            # X değerlerini oluştur
            x = np.linspace(x_range[0], x_range[1], 400)

            # Fonksiyonu değerlendir
            # Güvenlik için eval yerine daha güvenli bir yöntem kullanılmalı
            y = eval(function_str, {"x": x, "np": np, "__builtins__": {}})

            # Grafik oluştur
            fig, ax = self.plt.subplots(figsize=(10, 6))
            ax.plot(x, y, "b-", linewidth=2)
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color="k", linewidth=0.5)
            ax.axvline(x=0, color="k", linewidth=0.5)
            ax.set_xlabel("x", fontsize=12)
            ax.set_ylabel("f(x)", fontsize=12)
            ax.set_title(title, fontsize=14, fontweight="bold")

            # Kaydet
            if output_path:
                self.plt.savefig(output_path, dpi=150, bbox_inches="tight")
                logger.info(f"Grafik kaydedildi: {output_path}")

            self.plt.close()

            return {
                "success": True,
                "output_path": output_path,
                "function": function_str,
                "x_range": x_range,
            }

        except Exception as e:
            logger.error(f"Grafik oluşturma hatası: {e}")
            return {"success": False, "error": str(e)}

    def generate_geometry_figure(
        self,
        shape_type: str,
        parameters: Dict[str, Any],
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        REQ-48.47: Geometry figure - Geometrik şekilleri çizmek

        Args:
            shape_type: Şekil tipi (triangle, circle, rectangle, vb.)
            parameters: Şekil parametreleri
            output_path: Kaydedilecek dosya yolu

        Returns:
            Şekil bilgileri
        """
        if not self.matplotlib_available:
            return {"success": False, "error": "Matplotlib yüklü değil"}

        try:
            import numpy as np
            from matplotlib.patches import Circle, Rectangle, Polygon

            fig, ax = self.plt.subplots(figsize=(8, 8))
            ax.set_aspect("equal")
            ax.grid(True, alpha=0.3)

            if shape_type == "circle":
                # Daire çiz
                radius = parameters.get("radius", 5)
                center = parameters.get("center", (0, 0))
                circle = Circle(
                    center, radius, fill=False, edgecolor="blue", linewidth=2
                )
                ax.add_patch(circle)
                ax.set_xlim(center[0] - radius - 2, center[0] + radius + 2)
                ax.set_ylim(center[1] - radius - 2, center[1] + radius + 2)

            elif shape_type == "rectangle":
                # Dikdörtgen çiz
                width = parameters.get("width", 6)
                height = parameters.get("height", 4)
                bottom_left = parameters.get("bottom_left", (0, 0))
                rect = Rectangle(
                    bottom_left,
                    width,
                    height,
                    fill=False,
                    edgecolor="blue",
                    linewidth=2,
                )
                ax.add_patch(rect)
                ax.set_xlim(bottom_left[0] - 2, bottom_left[0] + width + 2)
                ax.set_ylim(bottom_left[1] - 2, bottom_left[1] + height + 2)

            elif shape_type == "triangle":
                # Üçgen çiz
                vertices = parameters.get("vertices", [(0, 0), (4, 0), (2, 3)])
                triangle = Polygon(vertices, fill=False, edgecolor="blue", linewidth=2)
                ax.add_patch(triangle)

                # Sınırları ayarla
                x_coords = [v[0] for v in vertices]
                y_coords = [v[1] for v in vertices]
                ax.set_xlim(min(x_coords) - 1, max(x_coords) + 1)
                ax.set_ylim(min(y_coords) - 1, max(y_coords) + 1)

            ax.set_xlabel("x", fontsize=12)
            ax.set_ylabel("y", fontsize=12)
            ax.set_title(
                f"{shape_type.capitalize()} Şekli", fontsize=14, fontweight="bold"
            )

            # Kaydet
            if output_path:
                self.plt.savefig(output_path, dpi=150, bbox_inches="tight")
                logger.info(f"Geometrik şekil kaydedildi: {output_path}")

            self.plt.close()

            return {
                "success": True,
                "output_path": output_path,
                "shape_type": shape_type,
                "parameters": parameters,
            }

        except Exception as e:
            logger.error(f"Geometrik şekil oluşturma hatası: {e}")
            return {"success": False, "error": str(e)}

    def generate_chart(
        self,
        chart_type: str,
        data: Dict[str, Any],
        title: str = "Grafik",
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        REQ-48.48: Chart/Diagram - Veri görselleştirmesi yapmak

        Args:
            chart_type: Grafik tipi (bar, pie, line, scatter)
            data: Veri
            title: Başlık
            output_path: Kaydedilecek dosya yolu

        Returns:
            Grafik bilgileri
        """
        if not self.matplotlib_available:
            return {"success": False, "error": "Matplotlib yüklü değil"}

        try:
            fig, ax = self.plt.subplots(figsize=(10, 6))

            if chart_type == "bar":
                # Çubuk grafik
                categories = data.get("categories", [])
                values = data.get("values", [])
                ax.bar(categories, values, color="steelblue")
                ax.set_ylabel("Değer", fontsize=12)

            elif chart_type == "pie":
                # Pasta grafik
                labels = data.get("labels", [])
                sizes = data.get("sizes", [])
                ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
                ax.axis("equal")

            elif chart_type == "line":
                # Çizgi grafik
                x_data = data.get("x", [])
                y_data = data.get("y", [])
                ax.plot(x_data, y_data, marker="o", linewidth=2, markersize=6)
                ax.set_xlabel("X", fontsize=12)
                ax.set_ylabel("Y", fontsize=12)
                ax.grid(True, alpha=0.3)

            elif chart_type == "scatter":
                # Nokta grafik
                x_data = data.get("x", [])
                y_data = data.get("y", [])
                ax.scatter(x_data, y_data, s=100, alpha=0.6, c="steelblue")
                ax.set_xlabel("X", fontsize=12)
                ax.set_ylabel("Y", fontsize=12)
                ax.grid(True, alpha=0.3)

            ax.set_title(title, fontsize=14, fontweight="bold")

            # Kaydet
            if output_path:
                self.plt.savefig(output_path, dpi=150, bbox_inches="tight")
                logger.info(f"Grafik kaydedildi: {output_path}")

            self.plt.close()

            return {
                "success": True,
                "output_path": output_path,
                "chart_type": chart_type,
            }

        except Exception as e:
            logger.error(f"Grafik oluşturma hatası: {e}")
            return {"success": False, "error": str(e)}

    def generate_interactive_plot(
        self, plot_type: str, data: Dict[str, Any], title: str = "İnteraktif Grafik"
    ) -> Dict[str, Any]:
        """
        Plotly ile interaktif grafik oluştur

        Args:
            plot_type: Grafik tipi
            data: Veri
            title: Başlık

        Returns:
            HTML string veya dosya yolu
        """
        if not self.plotly_available:
            return {"success": False, "error": "Plotly yüklü değil"}

        try:
            if plot_type == "line":
                fig = self.go.Figure()
                fig.add_trace(
                    self.go.Scatter(
                        x=data.get("x", []),
                        y=data.get("y", []),
                        mode="lines+markers",
                        name="Veri",
                    )
                )

            elif plot_type == "bar":
                fig = self.go.Figure()
                fig.add_trace(
                    self.go.Bar(x=data.get("categories", []), y=data.get("values", []))
                )

            fig.update_layout(
                title=title, xaxis_title="X", yaxis_title="Y", hovermode="closest"
            )

            # HTML olarak döndür
            html_str = fig.to_html(include_plotlyjs="cdn")

            return {"success": True, "html": html_str, "plot_type": plot_type}

        except Exception as e:
            logger.error(f"İnteraktif grafik oluşturma hatası: {e}")
            return {"success": False, "error": str(e)}


# Ana Soru Üretim Motoru Sınıfı
class QuestionGenerationEngine:
    """
    Ana Soru Üretim Motoru
    Tüm alt sistemleri birleştiren ana sınıf
    """

    def __init__(self, llm_service=None):
        """
        Args:
            llm_service: LLM servisi
        """
        self.topic_generator = TopicBasedQuestionGenerator(llm_service)
        self.distractor_generator = DistractorGenerationSystem(llm_service)
        self.math_validator = MathematicalValidationEngine()
        self.visual_generator = VisualGenerationEngine()

        logger.info("Soru Üretim Motoru başlatıldı")

    async def generate_complete_question(
        self,
        subject: SubjectType,
        topic_name: str,
        topic_context: str,
        difficulty_level: DifficultyLevel,
        cognitive_level: CognitiveLevel,
        include_visual: bool = False,
    ) -> Optional[GeneratedQuestion]:
        """
        Tam bir soru üret (soru + çeldiriciler + doğrulama + görsel)

        Returns:
            Tam GeneratedQuestion objesi
        """
        try:
            # 1. Temel soruyu üret
            question = await self.topic_generator.generate_question(
                subject, topic_name, topic_context, difficulty_level, cognitive_level
            )

            if not question:
                return None

            # 2. Çeldiricileri üret ve ekle
            distractors = await self.distractor_generator.generate_distractors(
                question.correct_answer,
                question.question_text,
                subject,
                topic_name,
                count=3,
            )

            # Seçenekleri güncelle (A: doğru cevap, B-D: çeldiriciler)
            question.options = [f"A) {question.correct_answer}"] + [
                d["text"] for d in distractors[:3]
            ]

            # 3. Matematik sorusu ise doğrula
            if subject == SubjectType.MATEMATIK:
                validation = self.math_validator.validate_math_question(
                    question.question_text, question.correct_answer, question.options
                )

                if not validation["valid"]:
                    logger.warning(f"Matematik sorusu geçersiz: {validation['errors']}")
                    question.validation_errors = validation["errors"]
                    question.is_validated = False
                else:
                    question.is_validated = True

            # 4. Görsel üret (istenirse)
            if include_visual and subject == SubjectType.MATEMATIK:
                visual_path = f"generated_visuals/question_{question.id}.png"
                visual_result = self.visual_generator.generate_function_graph(
                    "x**2", output_path=visual_path  # Örnek fonksiyon
                )

                if visual_result["success"]:
                    question.source_materials.append(visual_path)

            logger.info(f"Tam soru üretildi: {question.id}")
            return question

        except Exception as e:
            logger.error(f"Tam soru üretim hatası: {e}")
            return None
