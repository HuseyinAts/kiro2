# 🎨 KIRO2 Frontend Specialist Agent - Yetenekler Kılavuzu

## 🛠️ 5 ANA YETENEK ALANI

### 1️⃣ React 18 Development
**Neler Yapabilir:**
- Modern React 18 componentleri oluşturma
- Hooks kullanımı (useState, useEffect, useContext, useMemo, useCallback)
- React Query ile veri yönetimi
- Context API ile state management
- Server Components ve Suspense kullanımı

**Pratik Örnekler:**
```python
# Yeni bir dashboard componenti oluştur
await orchestrator.delegate_task(
    'frontend_update',
    'React 18 ile öğrenci istatistik dashboard componenti oluştur'
)

# Mevcut component'i optimize et
await orchestrator.delegate_task(
    'frontend_update',
    'ExamInterface componentini React 18 best practices ile yeniden yaz'
)

# Custom hook oluştur
await orchestrator.delegate_task(
    'frontend_update',
    'Soru çözümü için useExamTimer custom hook\'u oluştur'
)
```

---

### 2️⃣ TypeScript
**Neler Yapabilir:**
- Type-safe component geliştirme
- Interface ve type tanımları oluşturma
- Generic types kullanımı
- Type guards ve utility types
- Strict mode ile güvenli kod yazma

**Pratik Örnekler:**
```python
# TypeScript type definitions oluştur
await orchestrator.delegate_task(
    'frontend_update',
    'Soru ve sınav için TypeScript type definitions oluştur'
)

# Mevcut JavaScript'i TypeScript'e çevir
await orchestrator.delegate_task(
    'frontend_update',
    'QuestionList componentini TypeScript\'e migrate et'
)

# Type-safe API client oluştur
await orchestrator.delegate_task(
    'frontend_update',
    'Backend API için type-safe axios client oluştur'
)
```

---

### 3️⃣ Educational UX (Eğitim UX)
**Neler Yapabilir:**
- Öğrenci odaklı arayüzler tasarlama
- Gamification elementleri ekleme
- Progress tracking göstergeleri
- Motivasyon artırıcı UI patterns
- Soru çözüm deneyimini optimize etme

**Pratik Örnekler:**
```python
# Gamification UI ekle
await orchestrator.delegate_task(
    'frontend_update',
    'Soru çözümü için puan, rozetler ve seviye sistemi UI componenti ekle'
)

# Progress visualization
await orchestrator.delegate_task(
    'frontend_update',
    'Öğrencinin ilerleme grafiği için interaktif chart componenti oluştur'
)

# Motivasyonel feedback
await orchestrator.delegate_task(
    'frontend_update',
    'Doğru/yanlış cevaplar için animasyonlu feedback componenti ekle'
)

# Adaptive learning interface
await orchestrator.delegate_task(
    'frontend_update',
    'Öğrenci performansına göre soru zorluk göstergesi ekle'
)
```

---

### 4️⃣ Accessibility Features (Erişilebilirlik)
**Neler Yapabilir:**
- WCAG 2.1 AA standardına uygun componentler
- Screen reader desteği (ARIA labels)
- Keyboard navigation
- Color contrast optimization
- Focus management
- Alt text ve semantic HTML

**Pratik Örnekler:**
```python
# Screen reader desteği ekle
await orchestrator.delegate_task(
    'frontend_update',
    'Tüm soru componentlerine ARIA labels ve screen reader desteği ekle'
)

# Keyboard navigation
await orchestrator.delegate_task(
    'frontend_update',
    'Sınav interface\'ine tam keyboard navigation desteği ekle (Tab, Enter, Space)'
)

# Görme engelli desteği
await orchestrator.delegate_task(
    'frontend_update',
    'Yüksek kontrast modu ve font büyütme özelliği ekle'
)

# ADHD desteği
await orchestrator.delegate_task(
    'frontend_update',
    'Dikkat dağınıklığı için focus mode ve minimal distraction UI oluştur'
)
```

---

### 5️⃣ Component Optimization (Performans)
**Neler Yapabilir:**
- React.memo ile re-render optimizasyonu
- useMemo ve useCallback ile hesaplama optimizasyonu
- Lazy loading ve code splitting
- Virtual scrolling uzun listeler için
- Bundle size optimizasyonu
- Performance profiling ve iyileştirme

**Pratik Örnekler:**
```python
# Re-render optimizasyonu
await orchestrator.delegate_task(
    'frontend_update',
    'QuestionList componentini React.memo ile optimize et'
)

# Lazy loading
await orchestrator.delegate_task(
    'frontend_update',
    'Tüm route componentlerine lazy loading ekle'
)

# Virtual scrolling
await orchestrator.delegate_task(
    'frontend_update',
    '1000+ soruluk listeleme için react-window ile virtual scrolling ekle'
)

# Bundle optimization
await orchestrator.delegate_task(
    'frontend_update',
    'Bundle size analizi yap ve gereksiz import\'ları temizle'
)
```

---

## 🎯 GERÇEK KULLANIM SENARYOLARı

### Senaryo 1: Yeni Feature Geliştirme
**Görev:** Soru istatistik dashboard oluştur

```python
import asyncio
from orchestrator import MasterOrchestrator

async def istatistik_dashboard():
    orchestrator = MasterOrchestrator()

    workflow = [
        {
            'agent': 'kiro2-backend-api',
            'type': 'api_development',
            'description': '''
                İstatistik API endpoint'leri oluştur:
                - Toplam çözülen soru sayısı
                - Doğru/yanlış oranları
                - Konu bazlı performans
                - Zaman içinde ilerleme
            ''',
            'parallel_group': 1
        },
        {
            'agent': 'kiro2-frontend-specialist',
            'type': 'frontend_update',
            'description': '''
                İstatistik Dashboard componenti oluştur:
                - React 18 + TypeScript
                - Recharts ile interaktif grafikler
                - Responsive design
                - Accessibility desteği
                - Performance optimization
            ''',
            'parallel_group': 2
        }
    ]

    await orchestrator.coordinate_agents(workflow)

asyncio.run(istatistik_dashboard())
```

---

### Senaryo 2: Mevcut Component İyileştirme
**Görev:** Sınav interface performansını artır

```python
await orchestrator.delegate_task(
    'frontend_update',
    '''
    ExamInterface componentini optimize et:
    1. 100+ sorulu sınavlarda lag problemi var
    2. Her soru değişiminde tüm component re-render oluyor
    3. Image'ler lazy load edilmiyor

    Yapılacaklar:
    - React.memo ekle
    - useMemo ile soru listesini cache'le
    - Lazy load images
    - Virtual scrolling ekle
    - Performance benchmark yap
    '''
)
```

---

### Senaryo 3: Accessibility İyileştirme
**Görev:** WCAG 2.1 AA standardını sağla

```python
await orchestrator.delegate_task(
    'frontend_update',
    '''
    Tüm platform'a accessibility desteği ekle:
    1. Screen reader testi yap ve eksikleri gider
    2. Keyboard navigation ekle (Tab order, Enter, Escape)
    3. Color contrast düzelt (min 4.5:1 ratio)
    4. ARIA labels ekle
    5. Focus indicators belirginleştir
    6. Skip to content link ekle

    Test Et:
    - axe DevTools ile test yap
    - NVDA screen reader ile dene
    - Lighthouse accessibility score: 100 hedefle
    '''
)
```

---

### Senaryo 4: UI/UX İyileştirme
**Görev:** Öğrenci motivasyonunu artır

```python
await orchestrator.delegate_task(
    'frontend_update',
    '''
    Gamification ve motivasyon UI ekle:

    1. Soru Çözüm Feedback:
       - Doğru cevap: Yeşil animasyon + "Harika!" mesajı
       - Yanlış cevap: Kırmızı animasyon + açıklama göster
       - Streak counter: Arka arkaya doğru sayısı

    2. Progress Visualization:
       - Circular progress ring
       - Konular için completion percentage
       - Haftalık hedef göstergesi

    3. Achievements:
       - Rozet koleksiyonu UI
       - Seviye sistemi (Başlangıç → Uzman)
       - Leaderboard componenti

    4. Micro-interactions:
       - Button hover animasyonları
       - Success konfeti efekti
       - Smooth transitions
    '''
)
```

---

### Senaryo 5: TypeScript Migration
**Görev:** JavaScript componentleri TypeScript'e çevir

```python
await orchestrator.delegate_task(
    'frontend_update',
    '''
    Priority componentleri TypeScript\'e migrate et:

    Phase 1 (Critical):
    - ExamInterface.jsx → ExamInterface.tsx
    - QuestionList.jsx → QuestionList.tsx
    - UserDashboard.jsx → UserDashboard.tsx

    Her component için:
    1. Props interface tanımla
    2. State types ekle
    3. Event handler types
    4. API response types
    5. Strict mode enable

    Sonuç:
    - 0 TypeScript error
    - Full type coverage
    - IntelliSense desteği
    '''
)
```

---

## 🔥 PARALEL WORKFLOW ÖRNEKLERİ

### Full-Stack Feature Development

```python
import asyncio
from orchestrator import MasterOrchestrator

async def adaptive_test_feature():
    """
    Adaptive test özelliği: Backend + Frontend paralel geliştirme
    """
    orchestrator = MasterOrchestrator()

    workflow = [
        # Phase 1: Paralel backend + frontend
        {
            'agent': 'kiro2-backend-api',
            'type': 'api_development',
            'description': 'IRT algoritması ile adaptive test API',
            'parallel_group': 1
        },
        {
            'agent': 'kiro2-frontend-specialist',
            'type': 'frontend_update',
            'description': 'Adaptive test UI componenti (React + TypeScript)',
            'parallel_group': 1
        },

        # Phase 2: Integration
        {
            'agent': 'kiro2-frontend-specialist',
            'type': 'frontend_update',
            'description': 'Backend API ile frontend integration',
            'parallel_group': 2
        },

        # Phase 3: Testing
        {
            'agent': 'kiro2-devops-engineer',
            'type': 'testing',
            'description': 'E2E testler + performance testing',
            'parallel_group': 3
        }
    ]

    await orchestrator.coordinate_agents(workflow)

asyncio.run(adaptive_test_feature())
```

---

## 📊 FRONTEND AGENT PERFORMANS TAKİBİ

```python
import asyncio
from orchestrator import MasterOrchestrator

async def frontend_performance_check():
    """Frontend agent performansını izle"""
    orchestrator = MasterOrchestrator()

    # Görev ver
    await orchestrator.delegate_task(
        'frontend_update',
        'Component performance audit yap'
    )

    # Performans raporunu göster
    from master_orchestrator import AgentRole
    frontend = orchestrator.agents[AgentRole.FRONTEND_SPECIALIST]

    print(f"Frontend Agent Performance:")
    print(f"  Tamamlanan: {frontend['performance']['tasks_completed']}")
    print(f"  Başarı: {frontend['performance']['success_rate']*100}%")
    print(f"  Durum: {frontend['status']}")

asyncio.run(frontend_performance_check())
```

---

## 🎓 ÖĞRENME KAYNAKLARI

Frontend agent şu teknolojilerde uzman:

| Teknoloji | Uzmanlık Seviyesi | Kullanım Alanı |
|-----------|-------------------|----------------|
| React 18 | ⭐⭐⭐⭐⭐ | Component geliştirme |
| TypeScript | ⭐⭐⭐⭐⭐ | Type-safe coding |
| Accessibility | ⭐⭐⭐⭐⭐ | WCAG 2.1 AA |
| Performance | ⭐⭐⭐⭐⭐ | Optimization |
| Educational UX | ⭐⭐⭐⭐⭐ | Öğrenci deneyimi |

---

## ⚡ HIZLI BAŞVURU

### Tek Satırda Frontend Görevi Ver
```bash
PYTHONIOENCODING=utf-8 py -c "import asyncio; from orchestrator import MasterOrchestrator; asyncio.run(MasterOrchestrator().delegate_task('frontend_update', 'GÖREV AÇIKLAMASI'))"
```

### Workflow ile Paralel Çalıştır
```python
workflow = [
    {'agent': 'kiro2-frontend-specialist', 'type': 'frontend_update', 'description': '...', 'parallel_group': 1}
]
await orchestrator.coordinate_agents(workflow)
```

---

**Versiyon:** 1.0.0
**Son Güncelleme:** 15 Kasım 2025
**Durum:** Production Ready ✅
