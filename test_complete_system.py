#!/usr/bin/env python3
"""
KIRO2 Master Test Script
Tüm orchestrator sistemini ve Claude Code ajanlarını test eder
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, '/home/claude/kiro2')

from orchestrator import (
    MasterOrchestrator,
    ClaudeCodeAgentManager,
    ItemResponseTheory,
    FSRS,
    ZoneProximalDevelopment,
    MultiArmedBandit,
    BloomTaxonomy
)


async def complete_system_test():
    """Tüm sistemi kapsamlı test et"""
    
    print("\n" + "="*80)
    print("🚀 KIRO2 MASTER ORCHESTRATOR - KAPSAMLI SİSTEM TESTİ")
    print("="*80)
    print(f"Test Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    test_results = {
        'algorithms': False,
        'agent_manager': False,
        'orchestrator': False,
        'emergency_workflow': False
    }
    
    try:
        # 1. Algoritmaları test et
        print("\n" + "="*60)
        print("📐 BÖLÜM 1: EĞİTİM ALGORİTMALARI")
        print("="*60)
        
        print("\n▶ IRT (Item Response Theory):")
        irt = ItemResponseTheory()
        prob = irt.calculate_probability(0.5, 1.2, 0.5, 0.25)
        print(f"  ✓ Başarı olasılığı hesaplandı: {prob:.2%}")
        
        print("\n▶ FSRS (17 Parametreli):")
        fsrs = FSRS(17)
        interval = fsrs.calculate_interval(2.5, 0.9)
        print(f"  ✓ Tekrar aralığı: {interval} gün")
        
        print("\n▶ ZPD (Zone of Proximal Development):")
        zpd = ZoneProximalDevelopment()
        zpd_range = zpd.calculate_zpd_range(0.6)
        print(f"  ✓ ZPD aralığı: [{zpd_range[0]:.2f}, {zpd_range[1]:.2f}]")
        
        print("\n▶ Multi-Armed Bandit:")
        mab = MultiArmedBandit(5)
        arm = mab.select_arm()
        print(f"  ✓ Seçilen kol: {arm}")
        
        print("\n▶ Bloom's Taxonomy:")
        bloom = BloomTaxonomy()
        level = bloom.classify_question("İntegrali hesaplayınız")
        print(f"  ✓ Soru seviyesi: {bloom.get_level_name(level)}")
        
        test_results['algorithms'] = True
        print("\n✅ Algoritmalar başarıyla test edildi!")
        
    except Exception as e:
        print(f"\n❌ Algoritma testi başarısız: {e}")
    
    try:
        # 2. Claude Code Agent Manager
        print("\n" + "="*60)
        print("🤖 BÖLÜM 2: CLAUDE CODE AGENT MANAGER")
        print("="*60)
        
        manager = ClaudeCodeAgentManager()
        
        print("\n▶ Yüklü Ajanlar:")
        for agent_name, agent in manager.agents.items():
            print(f"  • {agent_name:30} [{agent.model:10}]")
        
        # Test görevi
        test_task = {
            'id': 'test_001',
            'type': 'nlp_processing',
            'description': 'Türkçe metin analizi'
        }
        
        print("\n▶ Test Görevi Delegasyonu:")
        result = await manager.execute_task('turkish-nlp-specialist', test_task)
        print(f"  ✓ Görev durumu: {result['status']}")
        print(f"  ✓ Ajan: {result['agent']}")
        
        test_results['agent_manager'] = True
        print("\n✅ Agent Manager başarıyla test edildi!")
        
    except Exception as e:
        print(f"\n❌ Agent Manager testi başarısız: {e}")
    
    try:
        # 3. Master Orchestrator
        print("\n" + "="*60)
        print("🎯 BÖLÜM 3: MASTER ORCHESTRATOR")
        print("="*60)
        
        orchestrator = MasterOrchestrator()
        
        print("\n▶ Orchestrator Durumu:")
        status = orchestrator.get_agent_status()
        print(f"  Session ID: {status['session_id']}")
        print(f"  Aktif ajanlar: {len(status['agents'])}")
        
        # Basit workflow
        print("\n▶ Paralel Workflow Testi:")
        workflow = [{
            'description': 'Paralel görevler testi',
            'parallel': [
                {
                    'id': 'p1',
                    'type': 'content_loading',
                    'description': 'İçerik yükleme'
                },
                {
                    'id': 'p2',
                    'type': 'api_development',
                    'description': 'API geliştirme'
                },
                {
                    'id': 'p3',
                    'type': 'frontend_update',
                    'description': 'UI güncelleme'
                }
            ]
        }]
        
        workflow_result = await orchestrator.orchestrate_workflow(workflow)
        print(f"  ✓ Workflow durumu: {workflow_result['status']}")
        print(f"  ✓ Tamamlanan görevler: {len(workflow_result['tasks'])}")
        print(f"  ✓ Toplam süre: {workflow_result['total_duration']:.2f} saniye")
        
        test_results['orchestrator'] = True
        print("\n✅ Master Orchestrator başarıyla test edildi!")
        
    except Exception as e:
        print(f"\n❌ Orchestrator testi başarısız: {e}")
    
    try:
        # 4. Emergency Content Loading Workflow
        print("\n" + "="*60)
        print("🚨 BÖLÜM 4: EMERGENCY CONTENT LOADING")
        print("="*60)
        
        print("\n▶ 50 Soru Yükleme Workflow'u başlatılıyor...")
        
        emergency_result = await orchestrator.emergency_content_loading()
        
        print(f"\n📊 Workflow Sonuçları:")
        print(f"  ✓ Durum: {emergency_result['status']}")
        print(f"  ✓ İşlenen adım sayısı: {len(emergency_result['tasks'])}")
        
        print("\n📋 İşlem Detayları:")
        for idx, task in enumerate(emergency_result['tasks'], 1):
            print(f"  {idx}. {task['agent']:30} - {task['status']}")
        
        test_results['emergency_workflow'] = True
        print("\n✅ Emergency Content Loading başarıyla test edildi!")
        
    except Exception as e:
        print(f"\n❌ Emergency workflow testi başarısız: {e}")
    
    # Final rapor
    print("\n" + "="*80)
    print("📊 FİNAL TEST RAPORU")
    print("="*80)
    
    success_count = sum(1 for v in test_results.values() if v)
    total_count = len(test_results)
    
    print("\nTest Sonuçları:")
    for test_name, success in test_results.items():
        status_icon = "✅" if success else "❌"
        print(f"  {status_icon} {test_name.replace('_', ' ').title()}")
    
    print(f"\nBaşarı Oranı: {success_count}/{total_count} ({success_count/total_count*100:.0f}%)")
    
    if success_count == total_count:
        print("\n🎉 TÜM TESTLER BAŞARILI! Sistem production'a hazır!")
    elif success_count >= total_count * 0.75:
        print("\n⚠️ Çoğu test başarılı, küçük düzeltmeler gerekli.")
    else:
        print("\n❌ Kritik hatalar var, sistem gözden geçirilmeli.")
    
    # Agent performans özeti
    print("\n" + "="*60)
    print("📈 AGENT PERFORMANS ÖZETİ")
    print("="*60)
    
    final_status = orchestrator.get_agent_status()
    for agent_name, agent_info in final_status['agents'].items():
        print(f"\n{agent_name}:")
        print(f"  Durum: {agent_info['status']}")
        print(f"  Tamamlanan görev: {agent_info['tasks_completed']}")
        print(f"  Başarı oranı: {agent_info['success_rate']:.0%}")
    
    print("\n" + "="*80)
    print("✅ TEST TAMAMLANDI")
    print("="*80)
    
    return test_results


async def quick_test():
    """Hızlı test modu"""
    print("\n⚡ HIZLI TEST MODU")
    print("-"*40)
    
    # Sadece temel fonksiyonları test et
    orchestrator = MasterOrchestrator()
    status = orchestrator.get_agent_status()
    
    print(f"✓ Orchestrator aktif")
    print(f"✓ {len(status['agents'])} ajan hazır")
    print(f"✓ Session ID: {status['session_id']}")
    
    # Basit bir görev
    task = {
        'id': 'quick_test',
        'type': 'content_loading',
        'description': 'Hızlı test görevi'
    }
    
    result = await orchestrator.delegate_task(task)
    print(f"✓ Test görevi: {result['status']}")
    
    print("\n✅ Hızlı test tamamlandı!")


def main():
    """Ana çalıştırma fonksiyonu"""
    import argparse
    
    parser = argparse.ArgumentParser(description='KIRO2 Master Orchestrator Test')
    parser.add_argument('--quick', action='store_true', help='Hızlı test modu')
    parser.add_argument('--full', action='store_true', help='Tam test (varsayılan)')
    
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                  KIRO2 MASTER ORCHESTRATOR                   ║
║           Claude Code Agent Coordination System              ║
║                      Version 1.0.0                          ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Event loop oluştur
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        if args.quick:
            loop.run_until_complete(quick_test())
        else:
            loop.run_until_complete(complete_system_test())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test kullanıcı tarafından durduruldu.")
    except Exception as e:
        print(f"\n\n❌ Kritik hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loop.close()


if __name__ == "__main__":
    main()
