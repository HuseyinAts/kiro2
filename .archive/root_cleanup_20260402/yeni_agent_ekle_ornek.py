"""
YENİ AGENT EKLEME - ADIM ADIM ÖRNEK
Bu script, Master Orchestrator'a yeni bir agent eklemeyi gösterir

SENARYO: Analytics Specialist Agent Ekleme
- Veri analizi
- Raporlama
- İstatistiksel göstergeler
"""
import asyncio
import sys
sys.path.insert(0, 'orchestrator')

from master_orchestrator import MasterOrchestrator

# ============================================
# ADIM 1: Yeni Agent Tanımını Göster
# ============================================
def adim_1_agent_tanimi():
    """Yeni agent için gerekli tanım"""
    print("\n" + "="*60)
    print("📝 ADIM 1: YENİ AGENT TANIMI")
    print("="*60 + "\n")

    agent_config = {
        "name": "kiro2-analytics-specialist",
        "model": "sonnet",
        "capabilities": [
            "statistical_analysis",
            "data_visualization",
            "performance_reporting",
            "predictive_modeling",
            "dashboard_creation"
        ]
    }

    print("🤖 Yeni Agent:")
    print(f"   İsim: {agent_config['name']}")
    print(f"   Model: {agent_config['model']}")
    print(f"   Yetenekler:")
    for cap in agent_config['capabilities']:
        print(f"      • {cap}")

    print("\n💡 Bu tanım için claude_code_manager.py dosyasını güncellemeniz gerekir")
    return agent_config

# ============================================
# ADIM 2: Code Update Yapılacak Yerler
# ============================================
def adim_2_code_update():
    """Hangi dosyalarda değişiklik yapılacak"""
    print("\n" + "="*60)
    print("🔧 ADIM 2: YAPILACAK DEĞİŞİKLİKLER")
    print("="*60 + "\n")

    print("📂 Dosya 1: orchestrator/claude_code_manager.py")
    print("   Satır ~23: known_agents listesine ekle:")
    print("""
    self.known_agents = [
        ('turkish-nlp-specialist', 'haiku'),
        ('kiro2-content-manager', 'sonnet'),
        ('kiro2-frontend-specialist', 'sonnet'),
        ('kiro2-backend-api', 'sonnet'),
        ('kiro2-devops-engineer', 'haiku'),
        ('kiro2-analytics-specialist', 'sonnet'),  # ← YENİ
    ]
    """)

    print("\n   Satır ~35: agent_capabilities'e ekle:")
    print("""
    self.agent_capabilities['kiro2-analytics-specialist'] = [
        'statistical_analysis',
        'data_visualization',
        'performance_reporting',
        'predictive_modeling',
        'dashboard_creation'
    ]
    """)

    print("\n📂 Dosya 2: orchestrator/master_orchestrator.py")
    print("   Satır ~60: agent_for_task metoduna ekle:")
    print("""
    task_mapping = {
        # ... mevcut mappings ...
        'analytics': 'kiro2-analytics-specialist',
        'statistical_analysis': 'kiro2-analytics-specialist',
        'reporting': 'kiro2-analytics-specialist',
    }
    """)

# ============================================
# ADIM 3: Test Workflow'u
# ============================================
async def adim_3_test_workflow():
    """Yeni agent'ı test etmek için örnek workflow"""
    print("\n" + "="*60)
    print("🧪 ADIM 3: TEST WORKFLOW'U")
    print("="*60 + "\n")

    print("📋 Test Senaryosu:")
    print("   1. Analytics agent PostgreSQL verilerini analiz eder")
    print("   2. Backend API raporlama endpoint'i oluşturur")
    print("   3. Frontend dashboard componenti ekler")
    print()

    test_workflow = [
        {
            'agent': 'kiro2-analytics-specialist',  # YENİ AGENT
            'type': 'statistical_analysis',
            'description': 'PostgreSQL\'deki 41 sorunun istatistiksel analizini yap',
            'parallel_group': 1
        },
        {
            'agent': 'kiro2-backend-api',
            'type': 'api_development',
            'description': 'Analytics raporu için API endpoint oluştur',
            'parallel_group': 2
        },
        {
            'agent': 'kiro2-frontend-specialist',
            'type': 'frontend_update',
            'description': 'Analytics dashboard componenti ekle',
            'parallel_group': 2
        }
    ]

    print("🔄 Workflow Adımları:")
    for i, step in enumerate(test_workflow, 1):
        print(f"\n   {i}. {step['agent']}")
        print(f"      Görev: {step['type']}")
        print(f"      Açıklama: {step['description'][:50]}...")

    print("\n\n💡 Bu workflow'u çalıştırmak için:")
    print("   orchestrator = MasterOrchestrator()")
    print("   await orchestrator.coordinate_agents(test_workflow)")

# ============================================
# ADIM 4: Pratik Kullanım Örnekleri
# ============================================
async def adim_4_pratik_ornekler():
    """Yeni agent ile yapılabilecek işlemler"""
    print("\n" + "="*60)
    print("🎯 ADIM 4: PRATİK KULLANIM ÖRNEKLERİ")
    print("="*60 + "\n")

    print("Örnek 1: Tek başına analytics görevi")
    print("="*50)
    print("""
async def analiz_yap():
    orchestrator = MasterOrchestrator()

    result = await orchestrator.delegate_task(
        task_type='statistical_analysis',
        description='Son 7 günün soru çözüm istatistiklerini analiz et'
    )

    return result

asyncio.run(analiz_yap())
    """)

    print("\nÖrnek 2: Haftalık rapor oluşturma")
    print("="*50)
    print("""
async def haftalik_rapor():
    orchestrator = MasterOrchestrator()

    workflow = [
        {
            'agent': 'kiro2-analytics-specialist',
            'type': 'reporting',
            'description': 'Haftalık kullanım raporu oluştur'
        }
    ]

    await orchestrator.coordinate_agents(workflow)

asyncio.run(haftalik_rapor())
    """)

    print("\nÖrnek 3: Dashboard geliştirme (Paralel)")
    print("="*50)
    print("""
async def dashboard_gelistir():
    orchestrator = MasterOrchestrator()

    workflow = [
        {
            'agent': 'kiro2-analytics-specialist',
            'type': 'data_visualization',
            'description': 'Grafik dataları hazırla',
            'parallel_group': 1
        },
        {
            'agent': 'kiro2-frontend-specialist',
            'type': 'frontend_update',
            'description': 'Dashboard UI oluştur',
            'parallel_group': 1  # Analytics ile paralel çalışır
        }
    ]

    await orchestrator.coordinate_agents(workflow)

asyncio.run(dashboard_gelistir())
    """)

# ============================================
# ADIM 5: Özet ve Sonraki Adımlar
# ============================================
def adim_5_ozet():
    """Özet ve yapılacaklar"""
    print("\n" + "="*60)
    print("📚 ADIM 5: ÖZET VE SONRAKİ ADIMLAR")
    print("="*60 + "\n")

    print("✅ Öğrendikleriniz:")
    print("   1. Yeni agent nasıl tanımlanır")
    print("   2. Hangi dosyalar güncellenir")
    print("   3. Test workflow'u nasıl oluşturulur")
    print("   4. Pratik kullanım örnekleri")
    print()

    print("📝 Yapmanız Gerekenler:")
    print("   1. orchestrator/claude_code_manager.py dosyasını açın")
    print("   2. Yukarıdaki değişiklikleri yapın")
    print("   3. Test workflow'unu çalıştırın")
    print()

    print("🚀 Hemen Deneyebilecekleriniz:")
    print("   • Emergency content loading: orchestrator_examples.py")
    print("   • Custom workflow oluşturma: ORCHESTRATOR_KULLANIM_KILAVUZU.md")
    print("   • Mevcut agent'ları kullanma: demo_orchestrator.py")
    print()

    print("📖 Kaynaklar:")
    print("   • ORCHESTRATOR_KULLANIM_KILAVUZU.md - Detaylı kullanım kılavuzu")
    print("   • agent/README.md - Kurulum talimatları")
    print("   • orchestrator_examples.py - 6 pratik örnek")
    print()

# ============================================
# MAIN - Tüm adımları göster
# ============================================
async def main():
    """Ana fonksiyon - tüm adımları sırayla gösterir"""
    print("\n🎓 "*30)
    print("YENİ AGENT EKLEME - ADIM ADIM KILAVUZ")
    print("🎓 "*30)

    # Adım 1: Agent tanımı
    adim_1_agent_tanimi()

    # Adım 2: Code update
    adim_2_code_update()

    # Adım 3: Test workflow
    await adim_3_test_workflow()

    # Adım 4: Pratik örnekler
    await adim_4_pratik_ornekler()

    # Adım 5: Özet
    adim_5_ozet()

    print("="*60)
    print("✅ KILAVUZ TAMAMLANDI!")
    print("="*60)
    print()

if __name__ == "__main__":
    asyncio.run(main())
