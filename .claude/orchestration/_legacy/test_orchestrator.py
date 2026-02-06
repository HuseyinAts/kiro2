#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the orchestrator with various prompts"""

import sys
import os
import io

# Fix UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.orchestrator_v2 import OrchestratorV2
import json

def test_orchestrator():
    """Test orchestrator with various prompts"""
    
    test_prompts = [
        ('React component yaz modern dashboard için', 'kiro2-frontend-specialist'),
        ('Bu kodda bir hata var düzelt lütfen', 'debugger'),
        ('Test coverage artır %80 üzerine', 'test-runner'),
        ('Deploy the application to production', 'kiro2-devops-engineer'),
        ('OSYM sorularını yükle veritabanına', 'kiro2-content-manager'),
        ('Review this pull request for security issues', 'code-reviewer'),
        ('Optimize database queries for better performance', 'kiro2-backend-api'),
        ('Türkçe NLP analizi yap bu metin için', 'turkish-nlp-specialist'),
        ('Create user authentication endpoints with JWT', 'kiro2-backend-api'),
        ('Fix the failing integration tests', 'debugger'),
    ]
    
    orchestrator = OrchestratorV2()
    
    results = []
    correct = 0
    
    print("\n" + "="*70)
    print("🧪 ORKESTRATÖR TEST SONUÇLARI")
    print("="*70)
    
    for prompt, expected_agent in test_prompts:
        result = orchestrator.process(prompt)
        actual_agent = result['routing']['primary_agent']
        confidence = result['routing']['confidence']
        is_correct = actual_agent == expected_agent
        
        if is_correct:
            correct += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"\n{status} Prompt: {prompt[:50]}...")
        print(f"   Beklenen: {expected_agent}")
        print(f"   Gerçek: {actual_agent}")
        print(f"   Güven: {confidence:.1%}")
        
        results.append({
            'prompt': prompt,
            'expected': expected_agent,
            'actual': actual_agent,
            'confidence': confidence,
            'correct': is_correct
        })
    
    accuracy = correct / len(test_prompts)
    
    print("\n" + "="*70)
    print(f"📊 ÖZET:")
    print(f"   Doğruluk: {accuracy:.1%} ({correct}/{len(test_prompts)})")
    print(f"   Ortalama Güven: {sum(r['confidence'] for r in results)/len(results):.1%}")
    print("="*70)
    
    # Save results
    with open('.claude/orchestration/test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results

if __name__ == "__main__":
    test_orchestrator()