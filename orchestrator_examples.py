"""
Master Orchestrator Kullanım Örnekleri
"""
import asyncio
import sys
sys.path.insert(0, 'orchestrator')

from master_orchestrator import MasterOrchestrator

# ============================================
# ÖRNEK 1: Emergency Content Loading
# ============================================
async def load_emergency_content():
    """50 ÖSYM sorusunu otomatik yükle"""
    orchestrator = MasterOrchestrator()

    print("🚀 Emergency content loading başlıyor...")
    result = await orchestrator.emergency_content_loading()

    print(f"✅ Durum: {result['status']}")
    print(f"📊 İşlenen adım: {result['steps_completed']}")
    print(f"⏱️  Süre: {result['duration']:.2f} saniye")

    return result

# ============================================
# ÖRNEK 2: Paralel Task Execution
# ============================================
async def parallel_tasks_example():
    """Birden fazla görevi paralel çalıştır"""
    orchestrator = MasterOrchestrator()

    workflow = [
        {
            'agent': 'kiro2-content-manager',
            'type': 'content_loading',
            'description': 'Database optimizasyonu yap',
            'parallel_group': 1
        },
        {
            'agent': 'kiro2-backend-api',
            'type': 'api_development',
            'description': 'Yeni endpoint ekle',
            'parallel_group': 1  # Aynı grup = paralel çalışır
        },
        {
            'agent': 'kiro2-frontend-specialist',
            'type': 'frontend_update',
            'description': 'UI component güncelle',
            'parallel_group': 1
        }
    ]

    result = await orchestrator.coordinate_agents(workflow)
    print(f"✅ {len(workflow)} görev paralel tamamlandı!")

    return result

# ============================================
# ÖRNEK 3: Agent Status Kontrolü
# ============================================
def check_agent_status():
    """Tüm agent'ların durumunu kontrol et"""
    orchestrator = MasterOrchestrator()

    print("\n📊 AGENT STATUS RAPORU\n")
    print("=" * 60)

    for role, agent_info in orchestrator.agents.items():
        print(f"\n🤖 {agent_info['name']}")
        print(f"   Status: {agent_info['status']}")
        print(f"   Capabilities: {len(agent_info['capabilities'])} yetenek")

        perf = agent_info['performance']
        print(f"   Tamamlanan görev: {perf['tasks_completed']}")
        print(f"   Başarı oranı: {perf['success_rate']*100}%")

    print("\n" + "=" * 60)

# ============================================
# ÖRNEK 4: Custom Workflow Oluşturma
# ============================================
async def custom_workflow_example():
    """Özel bir workflow tanımla ve çalıştır"""
    orchestrator = MasterOrchestrator()

    # Senaryo: Yeni bir analiz raporu oluştur
    workflow = [
        {
            'agent': 'kiro2-content-manager',
            'type': 'content_loading',
            'description': 'Soru bankasından istatistikleri topla'
        },
        {
            'agent': 'turkish-nlp-specialist',
            'type': 'nlp_processing',
            'description': 'Soru metinlerini analiz et'
        },
        {
            'agent': 'kiro2-backend-api',
            'type': 'api_development',
            'description': 'Rapor API endpoint\'i oluştur'
        },
        {
            'agent': 'kiro2-frontend-specialist',
            'type': 'frontend_update',
            'description': 'Rapor görüntüleme UI\'ı yap'
        },
        {
            'agent': 'kiro2-devops-engineer',
            'type': 'testing',
            'description': 'Tüm sistemi test et'
        }
    ]

    print("🎯 Custom workflow çalıştırılıyor...")
    result = await orchestrator.coordinate_agents(workflow)

    return result

# ============================================
# ÖRNEK 5: Single Agent Task
# ============================================
async def single_agent_task():
    """Tek bir agent'a özel görev ver"""
    orchestrator = MasterOrchestrator()

    # NLP agent'ına özel bir görev
    result = await orchestrator.delegate_task(
        task_type='nlp_processing',
        description='PostgreSQL\'deki 41 soruyu kategorize et ve analiz et'
    )

    print(f"✅ NLP analizi tamamlandı: {result}")
    return result

# ============================================
# ÖRNEK 6: Performance Monitoring
# ============================================
async def monitor_performance():
    """Agent performansını izle"""
    orchestrator = MasterOrchestrator()

    # Önce bir workflow çalıştır
    await orchestrator.emergency_content_loading()

    # Sonra performans raporunu al
    print("\n📈 PERFORMANS RAPORU\n")
    print("=" * 60)

    for entry in orchestrator.execution_history:
        print(f"Task: {entry['task_type']}")
        print(f"Agent: {entry['agent']}")
        print(f"Durum: {entry['status']}")
        print(f"Süre: {entry.get('duration', 'N/A')}")
        print("-" * 60)

# ============================================
# MAIN - Tüm örnekleri çalıştır
# ============================================
async def main():
    print("\n" + "="*70)
    print("🎯 MASTER ORCHESTRATOR - KULLANIM ÖRNEKLERİ")
    print("="*70 + "\n")

    # Agent durumunu kontrol et
    check_agent_status()

    # İstediğiniz örneği çalıştırın:

    # Örnek 1: Emergency Content Loading
    # await load_emergency_content()

    # Örnek 2: Paralel görevler
    # await parallel_tasks_example()

    # Örnek 3: Custom workflow
    # await custom_workflow_example()

    # Örnek 4: Single agent task
    # await single_agent_task()

    # Örnek 5: Performance monitoring
    # await monitor_performance()

    print("\n✅ İşlem tamamlandı!\n")

if __name__ == "__main__":
    asyncio.run(main())
