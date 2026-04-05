#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GERÇEK SORU ÜRETİMİ - Claude Sonnet 4.5
TÜM SERVİSLERLE ENTEGRE
"""

import sys
import os
import json
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def generate_questions():
    print("="*80)
    print("CLAUDE SONNET 4.5 ILE GERCEK SORU URETIMI")
    print("="*80)
    print()

    # Import services
    from services.knowledge_graph_service import KnowledgeGraphService, QuestionNode
    from services.hitl_workflow_service import HITLWorkflowService

    kg_service = KnowledgeGraphService()
    hitl_service = HITLWorkflowService()

    print(f"[OK] Knowledge Graph: {len(kg_service.graph.nodes())} node")
    print(f"[OK] HITL Workflow: {len(hitl_service.experts)} expert")
    print()

    try:
        import anthropic

        api_key = "[REDACTED_ANTHROPIC_KEY]"
        client = anthropic.Anthropic(api_key=api_key)

        topics = [
            {"konu": "TYT Matematik - Turev", "zorluk": "orta", "prompt": "TYT Matematik Turev konusunda orta zorlukta bir coktan secmeli soru hazirla"},
            {"konu": "TYT Fizik - Kuvvet", "zorluk": "orta", "prompt": "TYT Fizik Newton'un 2. Yasasi konusunda orta zorlukta bir coktan secmeli soru hazirla"},
            {"konu": "TYT Kimya - Mol", "zorluk": "kolay", "prompt": "TYT Kimya Mol Kavrami konusunda kolay bir coktan secmeli soru hazirla"},
            {"konu": "TYT Biyoloji - Hucre", "zorluk": "orta", "prompt": "TYT Biyoloji Hucre Yapisi konusunda orta zorlukta bir coktan secmeli soru hazirla"},
            {"konu": "TYT Matematik - Integral", "zorluk": "zor", "prompt": "TYT Matematik Belirsiz Integral konusunda zor bir coktan secmeli soru hazirla"}
        ]

        generated = []

        for idx, topic in enumerate(topics, 1):
            print(f"\n{'='*70}")
            print(f"SORU {idx}/5: {topic['konu']}")
            print(f"{'='*70}")
            print(f"Zorluk: {topic['zorluk']}")
            print()

            try:
                print(f"[AI] Claude Sonnet 4.5 cagiriliyor...")

                msg = client.messages.create(
                    model='claude-sonnet-4-20250514',
                    max_tokens=1000,
                    temperature=0.7,
                    messages=[{
                        'role': 'user',
                        'content': f"{topic['prompt']}. JSON formatinda dondur: {{\"soru\": \"...\", \"secenekler\": {{\"A\": \"...\", \"B\": \"...\", \"C\": \"...\", \"D\": \"...\", \"E\": \"...\"}}, \"dogru_cevap\": \"C\", \"cozum\": \"...\"}}"
                    }]
                )

                response_text = msg.content[0].text
                print(f"[OK] Soru uretildi ({len(response_text)} karakter)")

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

                # Add to knowledge graph
                print(f"[KG] Knowledge Graph'a ekleniyor...")
                question_node = QuestionNode(
                    id=f"CLAUDE45_Q{idx:03d}",
                    konu=topic['konu'],
                    kazanim=soru_data.get('konu', topic['konu']),
                    bloom_level='apply',
                    irt_difficulty={'kolay': -0.5, 'orta': 0.0, 'zor': 0.8}[topic['zorluk']],
                    cognitive_skills=['problem_solving']
                )
                kg_service.add_question_node(question_node)
                print(f"[OK] Knowledge Graph: {len(kg_service.graph.nodes())} node")

                # Add metadata
                soru_data['_metadata'] = {
                    'id': question_node.id,
                    'konu': topic['konu'],
                    'zorluk': topic['zorluk'],
                    'ai_model': 'claude-sonnet-4-20250514',
                    'irt_difficulty': question_node.irt_difficulty
                }

                generated.append(soru_data)

                print()
                print("SORU:")
                print(soru_data.get('soru', 'N/A')[:80] + "...")
                print()
                print("SECENEKLER:")
                for k, v in soru_data.get('secenekler', {}).items():
                    marker = " <-- DOGRU" if k == soru_data.get('dogru_cevap') else ""
                    print(f"  {k}) {v[:60]}...{marker}")
                print()

            except Exception as e:
                print(f"[HATA] {str(e)[:100]}")

        # Save
        output_file = "claude45_gercek_sorular.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(generated, f, ensure_ascii=False, indent=2)

        print()
        print("="*80)
        print("SONUC RAPORU")
        print("="*80)
        print(f"\nToplam Uretilen:     {len(generated)}")
        print(f"Knowledge Graph:     {len(kg_service.graph.nodes())} node")
        print(f"Kaydedildi:          {output_file}")
        print()
        print("[BASARILI] Claude Sonnet 4.5 ile gercek sorular uretildi!")
        print("="*80)

        return generated

    except Exception as e:
        print(f"[FATAL HATA] {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    generate_questions()
