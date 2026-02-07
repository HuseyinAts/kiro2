# BÖLÜM 3: Plan Mode

## 3.1 Plan Mode Nedir?

Plan Mode, Claude Code'un "düşünme" modudur. Bu modda Claude kod yazmak yerine strateji geliştirir, dosyaları inceler ve bir eylem planı oluşturur.

### Boris Cherny'nin Açıklaması

**Orijinal İngilizce:**
> "Most of my sessions start in Plan mode. If my goal is to write a pull request I use Plan mode and go back and forth with Claude until I like its plan. From there I shift to auto-accept edits mode, and Claude can usually finish in one shot. A good plan really matters!"

**Türkçe çeviri:**
> "Çoğu oturumum Plan mode'da başlıyor. Hedefim bir Pull Request yazmaksa Plan mode kullanıyorum ve planını beğenene kadar Claude ile gidip geliyorum. Oradan auto-accept edits moduna geçiyorum ve Claude genellikle tek seferde tamamlayabiliyor. İyi bir plan gerçekten önemli!"

### Plan Mode'un Değeri

| Senaryo | Plan Mode Olmadan | Plan Mode İle |
|---------|-------------------|---------------|
| Basit bug fix | Hemen düzeltir ✓ | Gereksiz overhead |
| Kompleks refactoring | Yarıda takılır, geri döner | Önce plan, sonra tek seferde |
| Yeni feature | Deneme-yanılma, çok turn | Mimari kararlar önceden |
| Code review | Rastgele inceleme | Sistematik checklist |

**Sonuç:** Kompleks görevlerde Plan Mode, toplam turn sayısını %50-70 azaltıyor.

---

## 3.2 Aktivasyon ve Navigasyon

### Keyboard Shortcuts

| Shortcut | Eylem | Not |
|----------|-------|-----|
| `Shift + Tab` (2 kez) | Plan Mode'a gir/çık | Toggle davranışı |
| `Shift + Tab` (1 kez) | Input mode değiştir | Normal → Multiline |
| `Escape` | Mevcut işlemi iptal | Plan yazımını durdurur |
| `Enter` | Mesaj gönder | Plan'ı Claude'a ilet |
| `Ctrl + C` | İşlemi sonlandır | Acil durumda |

### Plan Mode Göstergesi

Plan Mode aktifken CLI'da görsel gösterge:

```
┌─────────────────────────────────────────┐
│ 🎯 PLAN MODE                            │
│ Claude is planning, not executing       │
├─────────────────────────────────────────┤
│ > Describe what you want to achieve...  │
└─────────────────────────────────────────┘
```

### Plan Mode'dan Çıkış Yöntemleri

**Yöntem 1 - Keyboard:**
`Shift + Tab` tuşlarına 2 kez basarak normal moda dön.

**Yöntem 2 - Komut:**
Claude'a "implement this plan" veya "bu planı uygula" de.

**Yöntem 3 - Otomatik:**
Plan onaylandıktan sonra Claude otomatik olarak execution mode'a geçer.

---

## 3.3 Plan Mode'da Erişilebilir Araçlar

### Tam Liste

Plan Mode'da Claude'un erişebildiği ve erişemediği araçlar:

**✅ ERİŞİLEBİLİR (Read-Only ve Planlama):**

| Araç | Kategori | Açıklama |
|------|----------|----------|
| `Read` | Dosya | Dosya içeriğini oku |
| `Glob` | Dosya | Pattern ile dosya bul (`*.py`, `src/**/*.ts`) |
| `Grep` | Dosya | Metin ara (regex destekli) |
| `LS` | Dosya | Dizin listele |
| `Task` | Görev | Subagent başlat (plan modunda) |
| `TodoRead` | Görev | Görev listesi oku |
| `TodoWrite` | Görev | Görev listesi yaz |
| `WebFetch` | Web | URL'den içerik çek |
| `WebSearch` | Web | Web araması yap |
| `NotebookRead` | Notebook | Jupyter notebook oku |

**❌ ENGELLİ (Değişiklik Yapan):**

| Araç | Kategori | Neden Engelli |
|------|----------|---------------|
| `Edit` | Dosya | Dosya değiştirir |
| `Write` | Dosya | Dosya oluşturur/yazar |
| `MultiEdit` | Dosya | Çoklu düzenleme |
| `Bash` | Sistem | Komut çalıştırır, yan etki |
| `NotebookEdit` | Notebook | Notebook değiştirir |

### Araç Kullanım Örnekleri

**Dosya keşfi:**
```
Plan Mode'da Claude:
"Önce proje yapısını anlayayım..."
[Glob: **/*.py]
[Read: src/main.py]
[Grep: "def authenticate" --include="*.py"]
```

**Web araştırması:**
```
Plan Mode'da Claude:
"LangGraph StateGraph API'sini kontrol edeyim..."
[WebSearch: "langgraph statgraph add_node documentation"]
[WebFetch: https://langchain-ai.github.io/langgraph/...]
```

---

## 3.4 Opus 4.5 ile Plan Mode Kombinasyonu

### Model Seçimi Stratejisi

Boris Cherny'nin önerisi: Planlama için Opus, uygulama için Sonnet.

**Neden?**
- Opus: Derin reasoning, karmaşık analiz, uzun vadeli planlama
- Sonnet: Hızlı execution, cost-efficient, pratik implementasyon

### Konfigürasyon

**Dosya:** `.claude/settings.json`

```json
{
  "model": {
    "default": "claude-sonnet-4-5-20250929",
    "planning": "claude-opus-4-5-20251101",
    "execution": "claude-sonnet-4-5-20250929",
    "review": "claude-opus-4-5-20251101"
  },
  "planMode": {
    "autoSwitchModel": true,
    "requireApproval": true,
    "maxPlanningTurns": 10
  }
}
```

**Davranış:**
1. Plan Mode'a girildiğinde otomatik Opus'a geç
2. Plan onaylandığında Sonnet'e geç
3. Review aşamasında tekrar Opus kullan

### Maliyet Karşılaştırması

| Model | Input (1M token) | Output (1M token) |
|-------|------------------|-------------------|
| Opus 4.5 | $15 | $75 |
| Sonnet 4.5 | $3 | $15 |

**Tipik senaryo (kompleks feature):**
- Planning: 10K input, 5K output (Opus) = $0.525
- Execution: 50K input, 20K output (Sonnet) = $0.45
- **Toplam: ~$1.00**

**Sadece Opus kullansak:**
- Tüm süreç: 60K input, 25K output = $2.775
- **3x daha pahalı!**

---

## 3.5 Etkili Plan Oluşturma

### Plan Yapısı Şablonu

Claude'un ürettiği tipik plan formatı:

```markdown
## 🎯 Hedef
[Tek cümlelik net hedef tanımı]

## 📋 Ön Analiz
- İncelenen dosyalar: [liste]
- Tespit edilen bağımlılıklar: [liste]
- Potansiyel riskler: [liste]

## 🔨 Uygulama Adımları

### Adım 1: [Başlık]
- Dosya: `path/to/file.py`
- Değişiklik: [açıklama]
- Bağımlılıklar: [varsa]

### Adım 2: [Başlık]
...

## ✅ Doğrulama Kriterleri
- [ ] Tüm testler geçiyor
- [ ] Lint hataları yok
- [ ] Type check başarılı

## ⚠️ Dikkat Edilecekler
- [Önemli uyarı 1]
- [Önemli uyarı 2]
```

### Plan Onay Süreci

**Kullanıcı seçenekleri:**

| Yanıt | Anlam | Sonraki Adım |
|-------|-------|--------------|
| "Looks good" / "Tamam" | Plan onaylandı | Execution başlar |
| "Modify step 3" | Kısmi değişiklik | Plan güncellenir |
| "Add testing" | Eksik ekleme | Plan genişletilir |
| "Start over" | Reddet | Yeni plan istenir |
| "More detail on X" | Detay iste | X açıklanır |

### KIRO2 İçin Plan Örneği

**Kullanıcı isteği:**
> "Soru üretim pipeline'ına duplicate detection ekle"

**Claude'un planı:**
```markdown
## 🎯 Hedef
Soru bankasında semantik benzerlik ile duplicate tespiti eklemek.

## 📋 Ön Analiz
- İncelenen dosyalar:
  - orchestrator/validators/__init__.py
  - orchestrator/core/quality_gates.py
  - tests/test_validators.py
  
- Tespit edilen bağımlılıklar:
  - sentence-transformers paketi gerekli
  - PostgreSQL'de soru embedding'leri için yeni tablo
  
- Potansiyel riskler:
  - Model yükleme süresi (ilk çalıştırmada ~30sn)
  - Memory kullanımı (model ~500MB)

## 🔨 Uygulama Adımları

### Adım 1: Dependency ekleme
- Dosya: `pyproject.toml`
- Değişiklik: sentence-transformers>=2.2.0 ekle

### Adım 2: DuplicateDetector sınıfı
- Dosya: `orchestrator/validators/duplicate_detector.py`
- Değişiklik: Yeni dosya oluştur
- İçerik:
  - SentenceTransformer model yükleme
  - cosine_similarity hesaplama
  - threshold-based duplicate check

### Adım 3: Database migration
- Dosya: `migrations/002_add_embeddings.sql`
- Değişiklik: question_embeddings tablosu ekle

### Adım 4: Quality gates entegrasyonu
- Dosya: `orchestrator/core/quality_gates.py`
- Değişiklik: DuplicateGate sınıfı ekle

### Adım 5: Unit testler
- Dosya: `tests/test_duplicate_detector.py`
- Değişiklik: Test cases ekle

## ✅ Doğrulama Kriterleri
- [ ] pytest tests/test_duplicate_detector.py geçiyor
- [ ] Similarity threshold %85 ile test edildi
- [ ] 1000 soru ile performance testi < 5sn

## ⚠️ Dikkat Edilecekler
- Model ilk yüklemede internet gerektirir
- GPU varsa CUDA kullan, yoksa CPU fallback
- Embedding cache'leme production için gerekli
```

---

## 3.6 Plan Mode Best Practices

### Ne Zaman Kullanılmalı?

**✅ KULLAN:**
- 3+ dosyayı etkileyen değişiklikler
- Yeni feature implementasyonu
- Refactoring projeleri
- Mimari değişiklikler
- Bilinmeyen codebase keşfi
- Kompleks bug investigation

**❌ KULLANMA:**
- Tek satır düzeltme
- Typo fix
- Basit config değişikliği
- Bilinen pattern tekrarı
- Acil hotfix

### Etkili Prompt Yazımı

**Kötü prompt:**
> "Kodu düzelt"

**İyi prompt:**
> "Authentication modülündeki rate limiting bug'ını düzelt. Symptom: 429 hatası 10 request'ten sonra değil, 5'ten sonra dönüyor. Beklenen davranış: RATE_LIMIT_THRESHOLD=10 olmalı."

**Mükemmel prompt:**
```
GÖREV: Rate limiting bug fix

BAĞLAM:
- Dosya: src/auth/rate_limiter.py
- Sorun: Threshold değeri yanlış uygulanıyor
- Beklenen: 10 request/dakika
- Gerçek: 5 request/dakika

KISITLAMALAR:
- Redis cache yapısını değiştirme
- Backward compatible olmalı
- Test coverage düşmemeli

ÇIKTI:
1. Root cause analizi
2. Düzeltme planı
3. Test stratejisi
```

### Plan Review Checklist

Plan'ı onaylamadan önce kontrol et:

- [ ] Hedef net tanımlanmış mı?
- [ ] Tüm etkilenen dosyalar listelenmiş mi?
- [ ] Adımlar mantıklı sırada mı?
- [ ] Bağımlılıklar belirtilmiş mi?
- [ ] Doğrulama kriterleri var mı?
- [ ] Riskler değerlendirilmiş mi?
- [ ] Geri alma planı var mı?

---

## 3.7 Plan Mode ve Subagent Entegrasyonu

### Plan Modunda Task Tool

Plan Mode'da `Task` aracı kullanılabilir. Bu, subagent'ların da plan modunda çalışmasını sağlar.

**Örnek:**
```
Ana Claude (Plan Mode):
"Bu görevi parçalara ayıracağım..."

[Task: security-reviewer]
"Authentication modülünü güvenlik açısından incele"
→ Subagent plan modunda çalışır
→ Güvenlik raporu döner

[Task: performance-analyzer]
"Rate limiter'ın performansını analiz et"
→ Subagent plan modunda çalışır
→ Performans raporu döner

Ana Claude:
"Her iki raporı da değerlendirerek final planı oluşturuyorum..."
```

### Paralel Planlama

10 subagent paralel çalışabilir. Her biri:
- Kendi 200K context'inde
- Plan modunda (sadece okuma)
- Sonuçları parent'a döndürür

**KIRO2 senaryosu:**
```
Ana Claude (Plan Mode):
"YKS konularını paralel analiz edeceğim..."

[Paralel Tasks:]
- matematik-analyzer: Matematik müfredatını tara
- fizik-analyzer: Fizik müfredatını tara  
- turkce-analyzer: Türkçe müfredatını tara
- kimya-analyzer: Kimya müfredatını tara
- biyoloji-analyzer: Biyoloji müfredatını tara

"Tüm analizler tamamlandı. Ortak pattern'ler:
1. Tüm derslerde temel kavram eksikliği
2. Soru çeşitliliği yetersiz
3. Zorluk dağılımı dengesiz

Genel plan:
1. Önce temel kavram soruları üret (seviye 1-2)
2. Sonra uygulama soruları (seviye 3)
3. En son analiz soruları (seviye 4-5)"
```

---

## 3.8 Troubleshooting

### Sık Karşılaşılan Sorunlar

**Sorun 1: Plan çok uzun, context doluyor**

Çözüm:
```
"Planı özetle ve sadece kritik adımları listele.
Her adım max 2 cümle olsun."
```

**Sorun 2: Plan çok genel, detay yok**

Çözüm:
```
"Adım 3'ü detaylandır:
- Hangi fonksiyonlar değişecek?
- Parametreler ne olacak?
- Return type ne olacak?"
```

**Sorun 3: Claude plan modundan çıkmıyor**

Çözüm:
1. `Shift + Tab` x2 ile manuel çık
2. Veya açıkça söyle: "Plan tamamlandı, şimdi uygula"

**Sorun 4: Plan'daki dosyalar yanlış**

Çözüm:
```
"Dosya yollarını doğrula:
[Glob: **/rate_limiter.py]
Gerçek konum: src/auth/rate_limiter.py
Plan'ı güncelle."
```

### Debug Mode

Verbose plan çıktısı için:

```json
// .claude/settings.json
{
  "planMode": {
    "verbose": true,
    "showToolCalls": true,
    "showTokenUsage": true
  }
}
```

Çıktı:
```
[Plan Mode] Tool: Glob(**/*.py) → 47 files found
[Plan Mode] Tool: Read(src/main.py) → 2,341 tokens
[Plan Mode] Planning tokens: 5,234 input, 1,892 output
[Plan Mode] Estimated cost: $0.12
```

---

## 3.9 Özet

### Checklist

- [ ] Kompleks görevlerde Plan Mode kullan
- [ ] Shift+Tab x2 ile toggle
- [ ] Opus for planning, Sonnet for execution
- [ ] Plan'ı onaylamadan önce review et
- [ ] Doğrulama kriterleri belirle
- [ ] Subagent'ları paralel planlama için kullan

### Metrikler

| Metrik | Plan Mode Olmadan | Plan Mode İle |
|--------|-------------------|---------------|
| Ortalama turn sayısı | 15-20 | 5-8 |
| First-attempt success | %60 | %85 |
| Context overflow riski | Yüksek | Düşük |
| Maliyet (kompleks görev) | $3-5 | $1-2 |

---

**Önceki Bölüm:** [02 - Verification Feedback Loops](./02-verification-feedback-loops.md)  
**Sonraki Bölüm:** [04 - Paralel Oturum Yönetimi](./04-paralel-oturum-yonetimi.md)
