#!/usr/bin/env python3
"""
KIRO2 Orchestrator Test Script
Mevcut orchestrator bileşenlerini test eder
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Windows console encoding fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Import mevcut modüller
from orchestrator.core.routing import RoutingEngine, get_routing_engine
from orchestrator.core.quality_gates import QualityGatePipeline, get_quality_pipeline
from orchestrator.core.self_improvement import SelfImprovementEngine, MetricsCollector, ImprovementAction
from orchestrator.core.agents import AgentRole, Agent, PlannerAgent
from orchestrator.core.llm_gateway import LLMGateway
from orchestrator.core.memory import MemoryStore

# Test için sabit database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2_test"


async def complete_system_test():
    """Mevcut sistemi test et"""
    
    print("\n" + "="*80)
    print("🚀 KIRO2 ORCHESTRATOR - SİSTEM TESTİ")
    print("="*80)
    print(f"Test Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    test_results = {
        'routing': False,
        'quality_gates': False,
        'self_improvement': False,
        'agents': False,
        'memory': False
    }
    
    try:
        # 1. Routing Engine test
        print("\n" + "="*60)
        print("📐 BÖLÜM 1: ROUTING ENGINE")
        print("="*60)
        
        routing_engine = get_routing_engine()
        print(f"  ✓ Routing Engine yüklendi")
        test_results['routing'] = True
        
    except Exception as e:
        print(f"  ❌ Routing Engine hatası: {e}")
        
    try:
        # 2. Quality Gates test
        print("\n" + "="*60)
        print("🔍 BÖLÜM 2: QUALITY GATES")
        print("="*60)
        
        quality_pipeline = get_quality_pipeline()
        print(f"  ✓ Quality Pipeline yüklendi")
        test_results['quality_gates'] = True
        
    except Exception as e:
        print(f"  ❌ Quality Gates hatası: {e}")
        
    try:
        # 3. Self Improvement test
        print("\n" + "="*60)
        print("🧠 BÖLÜM 3: SELF IMPROVEMENT")
        print("="*60)
        
        # MemoryStore ve MetricsCollector oluştur (self improvement için gerekli)
        memory_for_si = MemoryStore(database_url=TEST_DATABASE_URL)
        metrics_collector = MetricsCollector()
        improvement_engine = SelfImprovementEngine(memory_store=memory_for_si, metrics_collector=metrics_collector)
        print(f"  ✓ Self Improvement Engine yüklendi")
        test_results['self_improvement'] = True
        
    except Exception as e:
        print(f"  ❌ Self Improvement hatası: {e}")
        
    try:
        # 4. Agents test
        print("\n" + "="*60)
        print("🤖 BÖLÜM 4: AGENTS")
        print("="*60)
        
        planner = PlannerAgent()
        print(f"  ✓ PlannerAgent yüklendi: {planner.role}")
        test_results['agents'] = True
        
    except Exception as e:
        print(f"  ❌ Agents hatası: {e}")
        
    try:
        # 5. Memory test
        print("\n" + "="*60)
        print("💾 BÖLÜM 5: MEMORY STORE")
        print("="*60)
        
        memory = MemoryStore(database_url=TEST_DATABASE_URL)
        print(f"  ✓ Memory Store yüklendi: {memory.database_url}")
        test_results['memory'] = True
        
    except Exception as e:
        print(f"  ❌ Memory Store hatası: {e}")
    
    # Sonuç özeti
    print("\n" + "="*80)
    print("📊 TEST SONUÇLARI")
    print("="*80)
    
    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"  {test_name}: {status}")
    
    print(f"\nToplam: {passed}/{total} test başarılı")
    print("="*80)
    
    return all(test_results.values())


if __name__ == "__main__":
    success = asyncio.run(complete_system_test())
    sys.exit(0 if success else 1)
