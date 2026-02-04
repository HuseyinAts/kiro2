"""
ÖSYM-Inspired Question Generator
Uses real ÖSYM questions as examples for AI generation
"""
import asyncpg
import json
import random
from typing import List, Dict, Optional
import anthropic
import openai

# Import subject-specific configurations
from services.subject_specific_prompts import (
    get_subject_config,
    get_enhanced_prompt,
    SUBJECT_TARGET_LENGTHS,
)

# Import reranker (Wave 1 improvement - DEEP_RESEARCH_FINDINGS_2024.md)
from services.question_reranker import KeywordQuestionReranker

# Import quality improvement templates (Wave 2B improvement - Physics pattern)
from services.enhanced_question_templates import (
    get_quality_improved_prompt,
    needs_enhancement,
)


class OSYMInspiredGenerator:
    """
    Generate questions inspired by real ÖSYM questions

    Methods:
    1. Few-shot learning: Use ÖSYM questions as examples
    2. Template extraction: Extract patterns from ÖSYM questions
    3. Style mimicking: Analyze and replicate ÖSYM question style
    """

    def __init__(self, openai_api_key: str = None, anthropic_api_key: str = None):
        self.openai_client = (
            openai.AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None
        )
        self.anthropic_client = (
            anthropic.Anthropic(api_key=anthropic_api_key)
            if anthropic_api_key
            else None
        )
        # Wave 1: Keyword reranker for better example selection (+15-25% improvement)
        self.reranker = KeywordQuestionReranker()
        # Phase 1 Visual Questions: Table generator for data-based questions
        from services.visual_content_generator import VisualContentGenerator

        self.visual_generator = VisualContentGenerator()

    async def get_db_connection(self):
        """Get database connection"""
        from core.config import settings
        import re

        pattern = r"postgresql\+?.*://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)"
        match = re.match(pattern, settings.database_url)

        if match:
            return await asyncpg.connect(
                host=match.group(3),
                port=int(match.group(4)),
                user=match.group(1),
                password=match.group(2),
                database=match.group(5),
            )
        raise Exception("Database configuration error")

    async def get_similar_osym_questions(
        self,
        subject: str,
        exam_type: str = "TYT",
        count: int = 3,
        topic: Optional[str] = None,
        use_reranking: bool = True,
    ) -> List[Dict]:
        """
        Get similar ÖSYM questions as examples

        Wave 1 Improvement: Now with keyword-based reranking!
        - Fetch 10 candidates (instead of 3)
        - Rerank by topic relevance
        - Return top 3

        Expected improvement: +15-25% (DEEP_RESEARCH_FINDINGS_2024.md)
        """
        conn = await self.get_db_connection()

        try:
            # Wave 1: Fetch MORE candidates for reranking (3x multiplier)
            fetch_count = count * 3 if use_reranking and topic else count

            # Get random ÖSYM questions from same subject
            query = """
                SELECT question_id, subject, stem, options, correct_answer, year
                FROM questions
                WHERE source = 'ÖSYM'
                  AND subject = $1
                  AND exam_type = $2
                  AND correct_answer IS NOT NULL
                ORDER BY RANDOM()
                LIMIT $3
            """

            rows = await conn.fetch(query, subject, exam_type.upper(), fetch_count)

            questions = []
            for row in rows:
                questions.append(
                    {
                        "question_id": str(row["question_id"]),
                        "subject": row["subject"],
                        "stem": row["stem"],
                        "options": json.loads(row["options"])
                        if isinstance(row["options"], str)
                        else row["options"],
                        "correct_answer": row["correct_answer"],
                        "year": row["year"],
                    }
                )

            # Wave 1: Rerank if topic provided
            if use_reranking and topic and questions:
                # Get target length for subject
                target_length = SUBJECT_TARGET_LENGTHS.get(subject, 400)

                print(
                    f"[RERANKER] Fetched {len(questions)} candidates, reranking for topic: '{topic}'"
                )

                # Rerank by relevance
                questions = self.reranker.rerank(
                    candidates=questions,
                    topic=topic,
                    target_length=target_length,
                    top_k=count,
                )

                print(
                    f"[RERANKER] Selected top {len(questions)} questions by relevance"
                )

                # Debug: Show scores for top 3
                if questions:
                    for i, q in enumerate(questions[:3], 1):
                        explanation = self.reranker.explain_ranking(
                            q, topic, target_length
                        )
                        print(
                            f"  #{i}: Score={explanation['total_score']:.3f} | "
                            f"Year={q.get('year', 'N/A')} | "
                            f"Length={len(q['stem'])} chars"
                        )

            return questions

        finally:
            await conn.close()

    def format_osym_examples(self, osym_questions: List[Dict]) -> str:
        """
        Format ÖSYM questions as few-shot examples
        """
        examples = []

        for i, q in enumerate(osym_questions, 1):
            example = f"""
ÖRNEK {i} (ÖSYM {q['year']} - {q['subject']}):

SORU: {q['stem']}

SEÇENEKLER:
"""
            for key, value in q["options"].items():
                marker = "✓" if key == q["correct_answer"] else " "
                example += f"{marker} {key}) {value}\n"

            examples.append(example)

        return "\n".join(examples)

    async def generate_with_few_shot(
        self,
        subject: str,
        topic: str,
        exam_type: str = "TYT",
        difficulty: str = "orta",
        provider: str = "claude",  # "claude" or "openai"
        style_guide: Optional[Dict] = None,  # OPTION A: Pass database average
        include_table: bool = False,  # Phase 1: Generate question with table
        table_type: str = "frequency_table",  # Type of table to include
        include_graph: bool = False,  # Phase 2: Generate question with graph
        graph_type: str = "line",  # Type of graph to include (line, bar, pie, scatter, histogram)
        include_geometry: bool = False,  # Phase 3: Generate question with geometry
        geometry_type: str = "triangle",  # Type of geometry (triangle, circle, quadrilateral, polygon, 3d_shape)
        shape_subtype: Optional[
            str
        ] = None,  # Specific shape (e.g., "right_triangle", "square", auto-selected if None)
        include_map_diagram: bool = False,  # Phase 4: Generate question with map/diagram
        diagram_type: str = "geographic_map",  # Type of diagram (geographic_map, process_diagram, classification_diagram, timeline)
        diagram_subtype: Optional[
            str
        ] = None,  # Specific diagram (e.g., "turkey_regions", "flowchart", auto-selected if None)
    ) -> Dict:
        """
        METHOD 1: Few-Shot Learning
        Use real ÖSYM questions as examples in the prompt

        Args:
            style_guide: Optional style guide with database-wide avg_stem_length.
                        If provided, uses database average instead of example average.

        Note: Retry logic is handled by the wrapper in hybrid_question_generator.py
        """

        # Wave 1: Get 3 similar ÖSYM questions (with reranking!)
        osym_examples = await self.get_similar_osym_questions(
            subject=subject,
            exam_type=exam_type,
            count=3,
            topic=topic,  # Pass topic for keyword reranking
            use_reranking=True,  # Enable Wave 1 reranker
        )

        if not osym_examples:
            raise Exception(f"No ÖSYM examples found for {subject}")

        # Format examples
        examples_text = self.format_osym_examples(osym_examples)

        # OPTION A: Use database average if style_guide provided, else calculate from examples
        if style_guide and "avg_stem_length" in style_guide:
            # Use stable database-wide average (from 50 questions)
            avg_example_length = style_guide["avg_stem_length"]
            print(
                f"[OPTION A] Using database average: {avg_example_length} chars (from {style_guide.get('total_analyzed', 50)} questions)"
            )
        else:
            # Fallback: Calculate from retrieved examples (old method)
            avg_example_length = sum(len(ex["stem"]) for ex in osym_examples) / len(
                osym_examples
            )
            print(
                f"[FALLBACK] Using example average: {avg_example_length} chars (from {len(osym_examples)} examples)"
            )

        min_length = int(avg_example_length * 0.8)
        max_length = int(avg_example_length * 1.2)

        # Get subject-specific configuration
        subject_config = get_subject_config(subject)

        # If subject has specific config, use its narrower length range
        if subject_config:
            min_length = subject_config.min_length
            max_length = subject_config.max_length
            print(
                f"[SUBJECT-SPECIFIC] Using {subject} config: {min_length}-{max_length} chars (±15% of {subject_config.target_length})"
            )

        # PHASE 1 VISUAL QUESTIONS: Generate table if requested
        table_data = None
        table_prompt_section = ""

        if include_table:
            print(f"[VISUAL-TABLE] Generating {table_type} for {subject}/{topic}")
            table_data = self.visual_generator.generate_table(
                subject=subject, topic=topic, data_type=table_type, rows=4, columns=3
            )

            # Add table example to prompt
            table_prompt_section = f"""

<visual_content>
<instruction>Bu soru aşağıdaki TABLO ile birlikte sunulacaktır. Soruyu tabloya referans vererek oluştur.</instruction>

<table_example>
{table_data['content']}
</table_example>

<table_usage_guide>
- Soru metninde tabloya referans ver: "Aşağıdaki tabloya göre...", "Tabloda verilen..."
- Tablo verilerini kullanarak sorular oluştur
- Öğrencinin tabloyu okuması ve yorumlaması gereksin
- Seçeneklerde tablo verilerine dayalı cevaplar sun
</table_usage_guide>
</visual_content>"""
            print(
                f"[VISUAL-TABLE] Table with {table_data['metadata']['rows']} rows, {table_data['metadata']['columns']} columns generated"
            )

        # PHASE 2 VISUAL QUESTIONS: Generate graph if requested
        graph_data = None
        graph_prompt_section = ""

        if include_graph:
            print(f"[VISUAL-GRAPH] Generating {graph_type} graph for {subject}/{topic}")
            graph_data = self.visual_generator.generate_graph(
                subject=subject, topic=topic, graph_type=graph_type, complexity="medium"
            )

            # Add graph example to prompt
            graph_prompt_section = f"""

<visual_content>
<instruction>Bu soru aşağıdaki GRAFİK ile birlikte sunulacaktır. Soruyu grafiğe referans vererek oluştur.</instruction>

<graph_description>
Grafik Tipi: {graph_data['metadata']['graph_type']}
Başlık: {graph_data['metadata']['title']}
X Ekseni: {graph_data['metadata']['x_label']}
Y Ekseni: {graph_data['metadata']['y_label']}
</graph_description>

<graph_usage_guide>
- Soru metninde grafiğe referans ver: "Aşağıdaki grafiğe göre...", "Grafikte verilen..."
- Grafikteki eğilimleri, karşılaştırmaları veya değerleri kullanarak sorular oluştur
- Öğrencinin grafiği okuması ve yorumlaması gereksin
- Seçeneklerde grafik verilerine dayalı cevaplar sun
- Grafik türüne uygun sorular sor (çizgi grafik: trend, bar: karşılaştırma, pasta: oran, vb.)
</graph_usage_guide>
</visual_content>"""
            print(
                f"[VISUAL-GRAPH] {graph_type} graph generated with SVG content ({len(graph_data['content'])} chars)"
            )

        # PHASE 3 VISUAL QUESTIONS: Generate geometry if requested
        geometry_data = None
        geometry_prompt_section = ""

        if include_geometry:
            print(
                f"[VISUAL-GEOMETRY] Generating {geometry_type} geometry for {subject}/{topic}"
            )
            geometry_data = self.visual_generator.generate_geometry(
                subject=subject,
                topic=topic,
                geometry_type=geometry_type,
                shape_subtype=shape_subtype,
                complexity="medium",
            )

            # Add geometry example to prompt
            geometry_prompt_section = f"""

<visual_content>
<instruction>Bu soru aşağıdaki GEOMETRİK ŞEKİL ile birlikte sunulacaktır. Soruyu şekle referans vererek oluştur.</instruction>

<geometry_description>
Şekil Tipi: {geometry_data['metadata']['geometry_type']}
Alt Tip: {geometry_data['metadata']['shape_subtype']}
Boyutlar: {', '.join([f'{k}: {v}' for k, v in geometry_data['metadata']['dimensions'].items()])}
</geometry_description>

<geometry_usage_guide>
- Soru metninde şekle referans ver: "Aşağıdaki şekle göre...", "Şekilde verilen..."
- Geometrik şeklin boyutlarını, açılarını veya özelliklerini kullanarak sorular oluştur
- Öğrencinin şekli analiz etmesi ve geometrik hesaplamalar yapması gereksin
- Seçeneklerde şekil verilerine dayalı cevaplar sun
- Geometri türüne uygun sorular sor (üçgen: alan/çevre, daire: yarıçap/çap/alan, 3B şekil: hacim/yüzey alanı, vb.)
- Şekildeki ölçüler ve etiketlere atıfta bulun
</geometry_usage_guide>
</visual_content>"""
            print(
                f"[VISUAL-GEOMETRY] {geometry_type}/{geometry_data['metadata']['shape_subtype']} generated with SVG content ({len(geometry_data['content'])} chars)"
            )

        # PHASE 4 VISUAL QUESTIONS: Generate map/diagram if requested
        map_diagram_data = None
        map_diagram_prompt_section = ""

        if include_map_diagram:
            print(
                f"[VISUAL-MAP-DIAGRAM] Generating {diagram_type}/{diagram_subtype or 'auto'} for {subject}/{topic}"
            )
            map_diagram_data = self.visual_generator.generate_map_diagram(
                subject=subject,
                topic=topic,
                diagram_type=diagram_type,
                diagram_subtype=diagram_subtype,
                complexity="medium",
            )

            # Add map/diagram example to prompt
            map_diagram_prompt_section = f"""

<visual_content>
<instruction>Bu soru aşağıdaki HARİTA/DİYAGRAM ile birlikte sunulacaktır. Soruyu görsele referans vererek oluştur.</instruction>

<diagram_description>
Diyagram Tipi: {map_diagram_data['metadata']['diagram_type']}
Alt Tip: {map_diagram_data['metadata']['diagram_subtype']}
Açıklama: {map_diagram_data['metadata']['description']}
</diagram_description>

<diagram_usage_guide>
- Soru metninde görsele referans ver: "Haritada gösterilen...", "Diyagramda verilen...", "Yukarıdaki şekle göre..."
- Görsel içeriğe dayalı sorular oluştur (coğrafi bölgeler, zaman çizelgesi, süreç adımları, küme ilişkileri, vb.)
- Öğrencinin görseli analiz etmesi ve yorumlaması gereksin
- Seçeneklerde görsel verilerine dayalı cevaplar sun
- Diyagram türüne uygun sorular sor:
  * Coğrafi haritalar: bölge özellikleri, konumlar, karşılaştırmalar
  * Süreç diyagramları: adım sırası, akış mantığı, ilişkiler
  * Sınıflandırma: kategoriler, hiyerarşi, üyelik ilişkileri
  * Zaman çizelgeleri: tarihsel sıra, olay aralıkları, dönem özellikleri
</diagram_usage_guide>
</visual_content>"""
            print(
                f"[VISUAL-MAP-DIAGRAM] {diagram_type}/{map_diagram_data['metadata']['diagram_subtype']} generated with SVG content ({len(map_diagram_data['content'])} chars)"
            )

        # Create BASE prompt with XML tags (Claude best practice - DEEP_RESEARCH_FINDINGS_2024.md)
        base_prompt = f"""<role>Sen ÖSYM sınav soruları uzmanısın. Görevin: Gerçek ÖSYM sorularını taklit ederek yeni sorular oluşturmak.</role>

<examples>
<instruction>Aşağıda GERÇEK ÖSYM sorularından örnekler gösteriliyor. Bu örneklerdeki stil, format ve kaliteyi dikkatle incele.</instruction>

{examples_text}

<style_notes>
- Ortalama soru uzunluğu: {int(avg_example_length)} karakter
- Dil: Resmi, akademik Türkçe
- Format: ÖSYM standardı
</style_notes>
</examples>{table_prompt_section}{graph_prompt_section}{geometry_prompt_section}{map_diagram_prompt_section}

<task>
<subject>{subject}</subject>
<topic>{topic}</topic>
<exam_type>{exam_type}</exam_type>
<difficulty>{difficulty}</difficulty>

<instruction>
Yukarıdaki ÖSYM örneklerini taklit ederek bu konu için YENİ bir soru oluştur.
</instruction>
</task>

<constraints>
<length>
  <requirement>ZORUNLU: Soru metni (stem) {min_length}-{max_length} karakter arasında OLMALIDIR</requirement>
  <reference>Örnek soruların ortalama uzunluğu: {int(avg_example_length)} karakter</reference>
  <warning>Bu uzunluk aralığından kesinlikle ÇIKMA!</warning>
</length>

<content>
  - Tüm gerekli bilgileri ver (sayısal değerler, bağlam, koşullar)
  - ÖSYM tarzı soru yapıları kullan: "... kaçtır?", "... hangisidir?", "... bulunur?"
  - Yukarıdaki örneklerdeki dil ve üsluba sadık kal
</content>

<format>
  - 5 seçenek (A, B, C, D, E)
  - Sadece 1 doğru cevap
  - Çeldiriciler mantıklı ve zorlayıcı olmalı
  - Türkçe dilbilgisi kurallarına tam uyum
</format>
</constraints>

<quality_check>
Soruyu oluşturduktan sonra kontrol et:
✓ Uzunluk {min_length}-{max_length} karakter arasında mı?
✓ ÖSYM örneklerine benziyor mu?
✓ Tüm bilgiler verilmiş mi?
</quality_check>"""

        # ENHANCE with subject-specific prompt (if available)
        if subject_config:
            prompt = get_enhanced_prompt(subject, base_prompt, exam_type)
            print(
                f"[SUBJECT-SPECIFIC] Enhanced prompt with {subject} misconceptions and style notes"
            )
        else:
            prompt = base_prompt
            print(
                f"[GENERIC] No subject-specific config for {subject}, using base prompt"
            )

        # WAVE 2B QUALITY IMPROVEMENT: Apply Physics success pattern to Math & Turkish
        if needs_enhancement(subject):
            prompt = get_quality_improved_prompt(subject, prompt)
            print(
                f"[WAVE2B-QUALITY] [ENHANCED] Applied Physics success pattern to {subject} (targets 0.85+ quality)"
            )

        # Add JSON format instruction with XML tags
        # Visual content note for JSON format
        visual_json_note = ""
        if include_table:
            visual_json_note = """
    "visual_content": null  // Tablo bilgisi backend tarafından otomatik eklenecek, boş bırak"""

        prompt += f"""

<output_format>
<instruction>Çıktıyı tam olarak aşağıdaki JSON formatında döndür:</instruction>

<json_schema>
{{
    "stem": "Soru metni burada... (DİKKAT: {{min_length}}-{{max_length}} karakter arası)",
    "options": {{
        "A": "Seçenek A metni",
        "B": "Seçenek B metni",
        "C": "Seçenek C metni",
        "D": "Seçenek D metni",
        "E": "Seçenek E metni"
    }},
    "correct_answer": "C",
    "explanation": "Doğru cevabın neden C olduğunu açıkla..."{visual_json_note}
}}
</json_schema>

<requirements>
- JSON formatı geçerli olmalı
- stem alanı {{min_length}}-{{max_length}} karakter arası olmalı
- 5 seçenek (A-E) tam olmalı
- correct_answer A-E arasında olmalı
</requirements>
</output_format>
"""

        # Generate with selected provider
        if provider == "claude" and self.anthropic_client:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            result_text = response.content[0].text

        elif provider == "openai" and self.openai_client:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
            )
            result_text = response.choices[0].message.content

        else:
            raise Exception(f"Provider {provider} not configured")

        # Parse JSON response
        import re

        # Try to extract JSON object (handle multiple formats)
        # First try: Look for JSON code block
        json_block_match = re.search(
            r"```json\s*(\{.*?\})\s*```", result_text, re.DOTALL
        )
        if json_block_match:
            json_text = json_block_match.group(1)
        else:
            # Second try: Look for first complete JSON object
            json_match = re.search(
                r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", result_text, re.DOTALL
            )
            if json_match:
                json_text = json_match.group()
            else:
                # Last resort: try the whole text
                json_text = result_text.strip()

        try:
            result = json.loads(json_text)
            result["method"] = "few-shot"
            result["osym_examples_used"] = len(osym_examples)

            # PHASE 1, 2, 3 & 4 VISUAL QUESTIONS: Add table, graph, geometry, or map/diagram data if generated
            if table_data:
                result["visual_content"] = table_data
                print(
                    f"[VISUAL-TABLE] Added table to question: {table_data['metadata']['caption']}"
                )
            elif graph_data:
                result["visual_content"] = graph_data
                print(
                    f"[VISUAL-GRAPH] Added graph to question: {graph_data['metadata']['title']}"
                )
            elif geometry_data:
                result["visual_content"] = geometry_data
                print(
                    f"[VISUAL-GEOMETRY] Added geometry to question: {geometry_data['metadata']['shape_subtype']}"
                )
            elif map_diagram_data:
                result["visual_content"] = map_diagram_data
                print(
                    f"[VISUAL-MAP-DIAGRAM] Added map/diagram to question: {map_diagram_data['metadata']['diagram_subtype']}"
                )
            else:
                result["visual_content"] = None

            return result
        except json.JSONDecodeError as e:
            raise Exception(
                f"Failed to parse AI response: {e}. Response snippet: {result_text[:200]}..."
            )

    async def analyze_osym_style(self, subject: str, exam_type: str = "TYT") -> Dict:
        """
        METHOD 2: Style Analysis
        Analyze ÖSYM questions to extract patterns

        Returns style guide with database-wide statistics.
        If insufficient database data, uses research-based fallbacks.
        """
        conn = await self.get_db_connection()

        try:
            # Get many ÖSYM questions for analysis
            query = """
                SELECT stem, options
                FROM questions
                WHERE source = 'ÖSYM'
                  AND subject = $1
                  AND exam_type = $2
                LIMIT 50
            """

            rows = await conn.fetch(query, subject, exam_type.upper())

            # Analyze patterns
            if rows and len(rows) >= 10:
                # Sufficient data: use database statistics
                avg_stem_length = sum(len(row["stem"]) for row in rows) / len(rows)
                avg_word_count = sum(len(row["stem"].split()) for row in rows) / len(
                    rows
                )
                data_source = "database"
            else:
                # Insufficient data: use research-based fallback
                avg_stem_length = SUBJECT_TARGET_LENGTHS.get(
                    subject, SUBJECT_TARGET_LENGTHS["DEFAULT"]
                )
                avg_word_count = avg_stem_length / 5  # Rough estimate: 5 chars per word
                data_source = "research_fallback"
                print(
                    f"[FALLBACK] Using research-based target for {subject}: {avg_stem_length} chars"
                )

            # Common question starters
            starters = {}
            for row in rows:
                first_words = " ".join(row["stem"].split()[:3])
                starters[first_words] = starters.get(first_words, 0) + 1

            return {
                "total_analyzed": len(rows),
                "avg_stem_length": int(avg_stem_length),
                "avg_word_count": int(avg_word_count),
                "data_source": data_source,
                "common_starters": sorted(
                    starters.items(), key=lambda x: x[1], reverse=True
                )[:5]
                if starters
                else [],
                "style_notes": [
                    f"ÖSYM {subject} soruları ortalama {int(avg_word_count)} kelime içeriyor",
                    f"Ortalama soru uzunluğu: {int(avg_stem_length)} karakter (kaynak: {data_source})",
                    "Sorular açık ve net, belirsizlik içermiyor",
                    "Çeldiriciler mantıklı ve özenle seçilmiş",
                ],
            }

        finally:
            await conn.close()

    async def generate_with_template(
        self, subject: str, topic: str, exam_type: str = "TYT"
    ) -> Dict:
        """
        METHOD 3: Template-Based Generation
        Extract template from ÖSYM question and fill with new content
        """

        # Get a template question
        osym_questions = await self.get_similar_osym_questions(
            subject, exam_type, count=1
        )

        if not osym_questions:
            raise Exception(f"No ÖSYM templates found for {subject}")

        template_q = osym_questions[0]

        # Extract structure
        template = {
            "stem_structure": f"Template from ÖSYM {template_q['year']}",
            "num_options": len(template_q["options"]),
            "original_stem": template_q["stem"][:100] + "...",
            "generation_note": f"Yeni soru {topic} konusunda bu template'i taklit edecek",
        }

        return template

    async def get_osym_statistics(self) -> Dict:
        """
        Get comprehensive ÖSYM question bank statistics
        """
        conn = await self.get_db_connection()

        try:
            # Total questions
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM questions WHERE source = 'ÖSYM'"
            )

            # By subject
            by_subject = await conn.fetch(
                "SELECT subject, COUNT(*) as count FROM questions WHERE source = 'ÖSYM' GROUP BY subject"
            )

            # With answers (usable for training)
            with_answers = await conn.fetchval(
                "SELECT COUNT(*) FROM questions WHERE source = 'ÖSYM' AND correct_answer IS NOT NULL"
            )

            return {
                "total_osym_questions": total,
                "usable_for_training": with_answers,
                "by_subject": {row["subject"]: row["count"] for row in by_subject},
                "training_ready": with_answers > 0,
            }

        finally:
            await conn.close()


# USAGE EXAMPLE
async def example_usage():
    """
    Example: How to use ÖSYM-inspired generator
    """

    # Initialize
    generator = OSYMInspiredGenerator(
        openai_api_key="your-openai-key", anthropic_api_key="your-anthropic-key"
    )

    # METHOD 1: Few-shot learning (BEST)
    new_question = await generator.generate_with_few_shot(
        subject="Matematik",
        topic="Türev",
        exam_type="TYT",
        difficulty="orta",
        provider="claude",
    )

    print("Generated Question:")
    print(f"Stem: {new_question['stem']}")
    print(f"Correct: {new_question['correct_answer']}")
    print(f"Method: {new_question['method']}")

    # METHOD 2: Style analysis
    style_guide = await generator.analyze_osym_style(
        subject="Matematik", exam_type="TYT"
    )

    print("\nÖSYM Style Guide:")
    for note in style_guide["style_notes"]:
        print(f"  - {note}")

    # Statistics
    stats = await generator.get_osym_statistics()
    print(f"\nOSYM Bank: {stats['total_osym_questions']} questions")
    print(f"Training Ready: {stats['usable_for_training']} questions")
