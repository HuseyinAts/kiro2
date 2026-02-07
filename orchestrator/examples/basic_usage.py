"""
KIRO2 Orchestrator - Örnek Kullanım

Bu script, orchestrator'ın temel kullanımını gösterir.
"""

import asyncio
import os
from pathlib import Path

# Orchestrator modüllerini import et
from orchestrator import (
    create_orchestrator,
    run_task,
    RunState,
    RoutingEngine,
    TaskType,
    AgentFactory,
    AgentRole,
    LLMGateway,
    QualityGatePipeline,
)


async def example_simple_task():
    """En basit kullanım - tek satırda task çalıştır"""
    print("=" * 60)
    print("Örnek 1: Basit Task Çalıştırma")
    print("=" * 60)
    
    result = await run_task(
        task_description="Fix the authentication bug in auth/login.py",
        project_root="."
    )
    
    print(f"Başarılı: {result['success']}")
    print(f"İterasyon: {result['iterations']}")
    print(f"Değişen dosyalar: {result['files_changed']}")
    print(f"Toplam maliyet: ${result['cost_total']:.4f}")
    print()


async def example_routing():
    """Routing engine kullanımı"""
    print("=" * 60)
    print("Örnek 2: Task Routing")
    print("=" * 60)
    
    engine = RoutingEngine()
    
    # Farklı task tiplerini test et
    tasks = [
        "Türkçe sentiment analizi için model fine-tune et",
        "Fix SQL injection vulnerability in user API",
        "Create React component for student dashboard",
        "Refactor database migration scripts",
    ]
    
    for task in tasks:
        decision = engine.route(task)
        print(f"Task: {task[:50]}...")
        print(f"  → Tip: {decision.task_type.name}")
        print(f"  → Model: {decision.model}")
        print(f"  → Risk: {decision.risk_level.name}")
        print()


async def example_agents():
    """Agent kullanımı"""
    print("=" * 60)
    print("Örnek 3: Agent Kullanımı")
    print("=" * 60)
    
    factory = AgentFactory()
    
    # Planner agent oluştur
    planner = factory.create(AgentRole.PLANNER)
    print(f"Planner Agent: {planner.role.name}")
    print(f"  System prompt uzunluğu: {len(planner.system_prompt)} karakter")
    
    # Reviewer agent oluştur
    reviewer = factory.create(AgentRole.REVIEWER)
    print(f"Reviewer Agent: {reviewer.role.name}")
    print(f"  System prompt uzunluğu: {len(reviewer.system_prompt)} karakter")
    
    # Security auditor oluştur
    security = factory.create(AgentRole.SECURITY_AUDITOR)
    print(f"Security Agent: {security.role.name}")
    print(f"  System prompt uzunluğu: {len(security.system_prompt)} karakter")
    print()


async def example_quality_gates():
    """Quality gates kullanımı"""
    print("=" * 60)
    print("Örnek 4: Quality Gates")
    print("=" * 60)
    
    pipeline = QualityGatePipeline(project_root=".")
    
    # Pipeline'daki gate'leri listele
    print("Quality Gate Pipeline:")
    for i, gate in enumerate(pipeline.gates, 1):
        print(f"  {i}. {gate.__class__.__name__}")
    
    # Not: Gerçek çalıştırma için proje yapısı gerekli
    # results = await pipeline.run_all()
    print()


async def example_state_management():
    """State yönetimi"""
    print("=" * 60)
    print("Örnek 5: State Yönetimi")
    print("=" * 60)
    
    # Yeni run state oluştur
    state = RunState(task_id="example-task-001")
    
    print(f"Task ID: {state.task_id}")
    print(f"Status: {state.status.name}")
    print(f"İterasyon: {state.iteration}")
    print(f"Max İterasyon: {state.max_iterations}")
    
    # İterasyon artır
    state.increment_iteration()
    print(f"İterasyon sonrası: {state.iteration}")
    
    # Diff stats
    print(f"Diff Limitleri:")
    print(f"  Max dosya/iterasyon: {state.diff_stats.max_files_per_iteration}")
    print(f"  Max satır/iterasyon: {state.diff_stats.max_lines_per_iteration}")
    print(f"  Max toplam satır: {state.diff_stats.max_total_lines}")
    print()


async def example_full_workflow():
    """Tam workflow örneği"""
    print("=" * 60)
    print("Örnek 6: Tam Workflow (Simülasyon)")
    print("=" * 60)
    
    print("""
    Tam workflow şu adımları içerir:
    
    1. PLAN NODE
       └── Planner agent task'ı analiz eder
       └── Adım adım plan oluşturur
       └── Risk değerlendirmesi yapar
    
    2. IMPLEMENT NODE
       └── Her adım için Implementer agent çalışır
       └── Kod değişiklikleri yapar
       └── Diff limitlerine uyar
    
    3. REVIEW NODE
       └── Reviewer agent değişiklikleri inceler
       └── Sorunları tespit eder
       └── Onay veya red kararı verir
    
    4. FIX NODE (gerekirse)
       └── Fixer agent sorunları düzeltir
       └── Minimum değişiklik prensibi
       └── Review'a geri döner
    
    5. QUALITY GATES
       └── Lint kontrolü (ruff/eslint)
       └── Type check (mypy/tsc)
       └── Unit testler (pytest/jest)
       └── Security scan (bandit)
    
    6. COMPLETION
       └── Başarılı ise tamamlandı
       └── Başarısız ise hata raporu
       └── Öğrenilen dersler kaydedilir
    """)


async def main():
    """Ana örnek fonksiyon"""
    print("\n" + "=" * 60)
    print("KIRO2 Orchestrator - Kullanım Örnekleri")
    print("=" * 60 + "\n")
    
    # Basit örnekler (API key gerektirmez)
    await example_routing()
    await example_agents()
    await example_quality_gates()
    await example_state_management()
    await example_full_workflow()
    
    # API key kontrolü
    if os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"):
        print("\nAPI key bulundu, tam örnek çalıştırılabilir.")
        # await example_simple_task()  # Gerçek API çağrısı
    else:
        print("\nAPI key bulunamadı. Tam örnek için:")
        print("  export ANTHROPIC_API_KEY=sk-ant-...")
        print("  export OPENAI_API_KEY=sk-...")


if __name__ == "__main__":
    asyncio.run(main())
