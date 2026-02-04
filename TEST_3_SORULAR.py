#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST - 3 soru ile hızlı test
"""

import sys
import os
import json
from pathlib import Path

# Unbuffered output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# Force flush
def log(msg):
    print(msg, flush=True)

log("="*80)
log("3 SORU TEST")
log("="*80)

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from services.knowledge_graph_service import KnowledgeGraphService, QuestionNode

kg_service = KnowledgeGraphService()
log(f"KG nodes: {len(kg_service.graph.nodes())}")

try:
    import anthropic
    api_key = "[REDACTED_ANTHROPIC_KEY]"
    client = anthropic.Anthropic(api_key=api_key)
    log("[OK] Claude API ready")

    topics = [
        {"ders": "Matematik", "konu": "Türev", "zorluk": "orta"},
        {"ders": "Fizik", "konu": "Newton Yasaları", "zorluk": "orta"},
        {"ders": "Kimya", "konu": "Mol Kavramı", "zorluk": "kolay"},
    ]

    generated = []

    for idx, topic in enumerate(topics, 1):
        log(f"\n[{idx}/3] {topic['ders']} - {topic['konu']}")

        try:
            prompt = f"TYT {topic['ders']} sınavı için {topic['konu']} konusunda {topic['zorluk']} zorlukta bir çoktan seçmeli soru hazırla. JSON formatında döndür: {{\"soru_metni\": \"...\", \"secenekler\": {{\"A\": \"...\", \"B\": \"...\", \"C\": \"...\", \"D\": \"...\", \"E\": \"...\"}}, \"dogru_cevap\": \"C\", \"cozum\": \"...\"}}"

            log("  Calling Claude...")
            msg = client.messages.create(
                model='claude-sonnet-4-20250514',
                max_tokens=1000,
                temperature=0.7,
                messages=[{'role': 'user', 'content': prompt}]
            )

            response_text = msg.content[0].text
            log(f"  Got response: {len(response_text)} chars")

            # Parse JSON
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                json_text = response_text[start:end].strip()
            elif '{' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_text = response_text[start:end]
            else:
                json_text = response_text

            soru_data = json.loads(json_text)

            # Add to KG
            node = QuestionNode(
                id=f"TEST_Q{idx}",
                konu=f"{topic['ders']} - {topic['konu']}",
                kazanim=topic['konu'],
                bloom_level='apply',
                irt_difficulty=0.0,
                cognitive_skills=['problem_solving']
            )
            kg_service.add_question_node(node)

            soru_data['_id'] = node.id
            generated.append(soru_data)

            log(f"  [OK] {node.id} - {soru_data['soru_metni'][:50]}...")

        except Exception as e:
            log(f"  [ERROR] {str(e)[:80]}")

    with open('test_3_sorular.json', 'w', encoding='utf-8') as f:
        json.dump(generated, f, ensure_ascii=False, indent=2)

    log(f"\n[SUCCESS] {len(generated)}/3 questions generated!")
    log(f"KG nodes: {len(kg_service.graph.nodes())}")
    log(f"Saved to: test_3_sorular.json")

except Exception as e:
    log(f"[FATAL] {str(e)}")
    import traceback
    traceback.print_exc()
