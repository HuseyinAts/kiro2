# Master Orchestrator Kullanım Kılavuzu

## 🎯 ŞU AN NE YAPABİLİRSİNİZ?

### 1. Hazır Workflow'ları Çalıştırma

#### Emergency Content Loading (50 soru yükleme)
```python
import asyncio
from orchestrator import MasterOrchestrator

async def main():
    orchestrator = MasterOrchestrator()
    result = await orchestrator.emergency_content_loading()
    print(f"✅ {result['status']}")

asyncio.run(main())
```

**Komut:**
```bash
cd C:\Users\husey\kiro2
PYTHONIOENCODING=utf-8 py -c "import asyncio; from orchestrator import MasterOrchestrator; asyncio.run(MasterOrchestrator().emergency_content_loading())"
```

#### Agent Durumunu Kontrol Etme
```bash
PYTHONIOENCODING=utf-8 py orchestrator_examples.py
```

### 2. Özel Görev Delegasyonu

#### Tek bir agent'a görev verme:
```python
import asyncio
from orchestrator import MasterOrchestrator

async def nlp_analizi():
    orchestrator = MasterOrchestrator()

    # PostgreSQL'deki soruları analiz et
    result = await orchestrator.delegate_task(
        task_type='nlp_processing',
        description='PostgreSQL\'deki 41 soruyu kategorize et ve zorluk seviyelerini analiz et'
    )

    print(f"✅ Analiz tamamlandı: {result}")

asyncio.run(nlp_analizi())
```

**Çalıştırma:**
```bash
py -c "import asyncio; from orchestrator import MasterOrchestrator; asyncio.run(MasterOrchestrator().delegate_task('nlp_processing', 'PostgreSQL soruları analizi'))"
```

### 3. Paralel Görevler

```python
import asyncio
from orchestrator import MasterOrchestrator

async def paralel_geliştirme():
    orchestrator = MasterOrchestrator()

    workflow = [
        {
            'agent': 'kiro2-backend-api',
            'type': 'api_development',
            'description': 'Soru istatistik API endpoint ekle',
            'parallel_group': 1
        },
        {
            'agent': 'kiro2-frontend-specialist',
            'type': 'frontend_update',
            'description': 'İstatistik dashboard componenti oluştur',
            'parallel_group': 1  # Aynı grup = paralel çalışır
        }
    ]

    result = await orchestrator.coordinate_agents(workflow)
    print(f"✅ Paralel görevler tamamlandı!")

asyncio.run(paralel_geliştirme())
```

---

## 🔧 YENİ AGENT NASIL EKLENİR?

### Adım 1: Claude Code Agent Tanımla

Yeni bir agent config dosyası oluşturun:
```json
// .claude/agents/kiro2-analytics-specialist.json
{
  "name": "kiro2-analytics-specialist",
  "description": "Data analytics and reporting specialist for KIRO2 platform",
  "model": "sonnet",
  "capabilities": [
    "Advanced statistical analysis",
    "Data visualization",
    "Performance metrics reporting",
    "Predictive analytics"
  ]
}
```

### Adım 2: Orchestrator'a Kaydet

`orchestrator/claude_code_manager.py` dosyasını güncelleyin:

```python
# Satır 23 civarı - known_agents listesine ekleyin:
self.known_agents = [
    ('turkish-nlp-specialist', 'haiku'),
    ('kiro2-content-manager', 'sonnet'),
    ('kiro2-frontend-specialist', 'sonnet'),
    ('kiro2-backend-api', 'sonnet'),
    ('kiro2-devops-engineer', 'haiku'),
    ('kiro2-analytics-specialist', 'sonnet'),  # YENİ AGENT
]

# Satır 35 civarı - Capabilities ekleyin:
self.agent_capabilities = {
    # ... mevcut agent'lar ...
    'kiro2-analytics-specialist': [
        'statistical_analysis',
        'data_visualization',
        'performance_reporting',
        'predictive_modeling',
        'dashboard_creation'
    ]
}
```

### Adım 3: Master Orchestrator'da Task Type Ekleyin

`orchestrator/master_orchestrator.py` dosyasında:

```python
# Satır 60 civarı - agent_for_task metoduna ekleyin:
def agent_for_task(self, task_type: str) -> str:
    task_mapping = {
        # ... mevcut mappings ...
        'analytics': 'kiro2-analytics-specialist',
        'statistical_analysis': 'kiro2-analytics-specialist',
        'reporting': 'kiro2-analytics-specialist',
    }
    return task_mapping.get(task_type, 'kiro2-backend-api')
```

### Adım 4: Yeni Agent'ı Test Edin

```python
import asyncio
from orchestrator import MasterOrchestrator

async def test_yeni_agent():
    orchestrator = MasterOrchestrator()

    # Analytics agent'ına görev ver
    result = await orchestrator.delegate_task(
        task_type='statistical_analysis',
        description='Son 30 günün kullanıcı istatistiklerini analiz et'
    )

    print(f"✅ Analytics agent çalıştı: {result}")

asyncio.run(test_yeni_agent())
```

---

## 🚀 YENİ ÖZELLİK NASIL EKLENİR?

### Örnek: Adaptive Test Recommendation Sistemi

#### 1. Custom Workflow Oluşturun

`orchestrator/master_orchestrator.py` dosyasına yeni metod ekleyin:

```python
async def adaptive_test_workflow(self) -> dict:
    """
    Adaptive test recommendation sistemi oluşturur
    1. Backend: IRT algoritması + API
    2. Frontend: Test interface
    3. Analytics: Performance tracking
    4. DevOps: Testing ve deployment
    """
    workflow = [
        {
            'agent': 'kiro2-backend-api',
            'type': 'api_development',
            'description': '''
                Adaptive test recommendation API oluştur:
                - IRT 3PL model ile soru seçimi
                - Öğrenci ability estimation
                - Real-time difficulty adjustment
                - PostgreSQL'den optimal soru çekme
            ''',
            'parallel_group': 1
        },
        {
            'agent': 'kiro2-frontend-specialist',
            'type': 'frontend_update',
            'description': '''
                Adaptive test interface komponenti:
                - Real-time soru görüntüleme
                - Difficulty göstergesi
                - Progress tracking
                - WebSocket bağlantısı
            ''',
            'parallel_group': 1
        },
        {
            'agent': 'kiro2-analytics-specialist',
            'type': 'analytics',
            'description': '''
                Performance tracking dashboard:
                - Ability estimation graphs
                - Question difficulty distribution
                - Success rate analytics
            ''',
            'parallel_group': 2  # İlk iki tamamlandıktan sonra
        },
        {
            'agent': 'kiro2-devops-engineer',
            'type': 'testing',
            'description': '''
                Tam sistem testi:
                - API endpoint tests
                - Frontend component tests
                - Integration tests
                - Performance benchmarks
            ''',
            'parallel_group': 3  # En sonda
        }
    ]

    result = await self.coordinate_agents(workflow)
    return result
```

#### 2. Yeni Workflow'u Çalıştırın

```python
import asyncio
from orchestrator import MasterOrchestrator

async def adaptive_test_geliştir():
    orchestrator = MasterOrchestrator()

    print("🚀 Adaptive test sistemi geliştiriliyor...")
    result = await orchestrator.adaptive_test_workflow()

    print(f"✅ Durum: {result['status']}")
    print(f"📊 Tamamlanan adımlar: {result['steps_completed']}")

asyncio.run(adaptive_test_geliştir())
```

---

## 📊 PERFORMANS MONİTÖRİNG

### Agent Performance İzleme

```python
import asyncio
from orchestrator import MasterOrchestrator

async def performans_raporu():
    orchestrator = MasterOrchestrator()

    # Önce bir workflow çalıştır
    await orchestrator.emergency_content_loading()

    # Performance raporunu göster
    print("\n📈 PERFORMANS RAPORU\n")
    print("=" * 60)

    for entry in orchestrator.execution_history:
        print(f"Task: {entry['task_type']}")
        print(f"Agent: {entry['agent']}")
        print(f"Durum: {entry['status']}")
        print(f"Süre: {entry.get('duration', 'N/A')}")
        print("-" * 60)

    # Agent istatistikleri
    for role, agent in orchestrator.agents.items():
        perf = agent['performance']
        print(f"\n🤖 {agent['name']}")
        print(f"   Tamamlanan: {perf['tasks_completed']}")
        print(f"   Başarı: {perf['success_rate']*100}%")
        print(f"   Ortalama süre: {perf['avg_duration']}s")

asyncio.run(performans_raporu())
```

---

## 🎓 GERÇEKÇİ KULLANIM SENARYOLARı

### Senaryo 1: Günlük Soru Yükleme
```bash
# Her gün otomatik 50 yeni ÖSYM sorusu yükle
PYTHONIOENCODING=utf-8 py -c "import asyncio; from orchestrator import MasterOrchestrator; asyncio.run(MasterOrchestrator().emergency_content_loading())"
```

### Senaryo 2: Haftalık Analiz Raporu
```python
import asyncio
from orchestrator import MasterOrchestrator

async def haftalik_rapor():
    orchestrator = MasterOrchestrator()

    workflow = [
        {
            'agent': 'turkish-nlp-specialist',
            'type': 'nlp_processing',
            'description': 'Son 7 günün sorularını analiz et'
        },
        {
            'agent': 'kiro2-analytics-specialist',
            'type': 'reporting',
            'description': 'Haftalık kullanım ve performans raporu oluştur'
        }
    ]

    await orchestrator.coordinate_agents(workflow)

asyncio.run(haftalik_rapor())
```

### Senaryo 3: CI/CD Pipeline
```python
import asyncio
from orchestrator import MasterOrchestrator

async def cicd_pipeline():
    orchestrator = MasterOrchestrator()

    workflow = [
        {
            'agent': 'kiro2-devops-engineer',
            'type': 'testing',
            'description': 'Tüm backend testleri çalıştır'
        },
        {
            'agent': 'kiro2-devops-engineer',
            'type': 'testing',
            'description': 'Tüm frontend testleri çalıştır',
            'parallel_group': 1  # Backend ile paralel
        },
        {
            'agent': 'kiro2-devops-engineer',
            'type': 'deployment',
            'description': 'Production deployment',
            'parallel_group': 2  # Testler başarılıysa
        }
    ]

    await orchestrator.coordinate_agents(workflow)

asyncio.run(cicd_pipeline())
```

---

## ⚡ HIZLI BAŞVURU

### Agent'ları Listele
```bash
PYTHONIOENCODING=utf-8 py orchestrator_examples.py
```

### Emergency Content Loading
```bash
PYTHONIOENCODING=utf-8 py -c "import asyncio; from orchestrator import MasterOrchestrator; asyncio.run(MasterOrchestrator().emergency_content_loading())"
```

### Custom Task Çalıştır
```bash
PYTHONIOENCODING=utf-8 py -c "import asyncio; from orchestrator import MasterOrchestrator; asyncio.run(MasterOrchestrator().delegate_task('nlp_processing', 'Soru analizi yap'))"
```

---

## 🔍 Troubleshooting

### Unicode Hatası
Her zaman `PYTHONIOENCODING=utf-8` ile çalıştırın:
```bash
PYTHONIOENCODING=utf-8 py script.py
```

### Agent Bulunamadı
Claude Code agent'larının kurulu olduğundan emin olun:
```bash
claude-code --list-agents
```

### Database Bağlantı Hatası
PostgreSQL'in çalıştığını kontrol edin:
```bash
net start postgresql-x64-18
```

---

**Son Güncelleme:** 15 Kasım 2025
**Versiyon:** 1.0.0
