"""
Master Orchestrator Demo - Pratik Örnek
Bu script orchestrator'ın temel kullanımını gösterir
"""
import asyncio
import sys
sys.path.insert(0, 'orchestrator')

from master_orchestrator import MasterOrchestrator

async def demo_1_agent_status():
    """Demo 1: Agent durumunu kontrol et"""
    print("\n" + "="*60)
    print("🎯 DEMO 1: AGENT DURUM KONTROLÜ")
    print("="*60 + "\n")

    orchestrator = MasterOrchestrator()

    print("📊 Aktif Agent'lar:\n")
    for role, agent in orchestrator.agents.items():
        status_icon = "✅" if agent['status'] == 'ready' else "⏳"
        print(f"{status_icon} {agent['name']}")
        print(f"   └─ Yetenek sayısı: {len(agent['capabilities'])}")
        print(f"   └─ Durum: {agent['status']}")
        print()

    return orchestrator

async def demo_2_database_info():
    """Demo 2: Database bilgilerini göster"""
    print("\n" + "="*60)
    print("🎯 DEMO 2: DATABASE BİLGİLERİ")
    print("="*60 + "\n")

    orchestrator = MasterOrchestrator()

    # Simülasyon - gerçek task delegasyonu
    print("📊 PostgreSQL Durum:")
    print("   ✅ Bağlantı: localhost:5434")
    print("   ✅ Database: turkiye_sinav_db")
    print("   ✅ Soru sayısı: 41 (TYT: 22, AYT: 18, YDT: 1)")
    print()

    return orchestrator

async def demo_3_custom_workflow():
    """Demo 3: Özel workflow örneği"""
    print("\n" + "="*60)
    print("🎯 DEMO 3: CUSTOM WORKFLOW OLUŞTURMA")
    print("="*60 + "\n")

    orchestrator = MasterOrchestrator()

    # Örnek workflow tanımı
    workflow = [
        {
            'agent': 'turkish-nlp-specialist',
            'type': 'nlp_processing',
            'description': 'PostgreSQL\'deki 41 soruyu analiz et',
            'parallel_group': 1
        },
        {
            'agent': 'kiro2-backend-api',
            'type': 'api_development',
            'description': 'Soru istatistik API endpoint ekle',
            'parallel_group': 2
        }
    ]

    print("📋 Örnek Workflow:")
    for i, step in enumerate(workflow, 1):
        print(f"\n{i}. Adım:")
        print(f"   Agent: {step['agent']}")
        print(f"   Görev: {step['type']}")
        print(f"   Açıklama: {step['description']}")
        print(f"   Paralel Grup: {step['parallel_group']}")

    print("\n💡 Bu workflow'u çalıştırmak için:")
    print("   await orchestrator.coordinate_agents(workflow)")
    print()

async def main():
    """Ana demo fonksiyonu"""
    print("\n" + "🚀 "*30)
    print("MASTER ORCHESTRATOR - DEMO")
    print("🚀 "*30)

    # Demo 1: Agent durumu
    await demo_1_agent_status()

    # Demo 2: Database bilgileri
    await demo_2_database_info()

    # Demo 3: Custom workflow
    await demo_3_custom_workflow()

    print("\n" + "="*60)
    print("✅ DEMO TAMAMLANDI!")
    print("="*60)
    print("\nSonraki adımlar:")
    print("1. ORCHESTRATOR_KULLANIM_KILAVUZU.md dosyasını okuyun")
    print("2. orchestrator_examples.py'daki örnekleri deneyin")
    print("3. Kendi custom workflow'larınızı oluşturun")
    print()

if __name__ == "__main__":
    asyncio.run(main())
