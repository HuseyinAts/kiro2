"""
KIRO2 Template Manager - Prompt Şablon Yönetim Sistemi
======================================================
Orchestrator için merkezi prompt şablon yönetimi.
Claude ve Codex için optimize edilmiş şablonlar sağlar.

Özellikler:
- Şablon versiyonlama
- Değişken interpolasyon
- Şablon kalıtımı
- Çoklu model desteği (Claude, Codex, GPT-4)
- Türkçe YKS domain-specific şablonlar
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional
import json

logger = logging.getLogger(__name__)


class TemplateCategory(Enum):
    """Şablon kategorileri"""
    PLANNING = "planning"         # Planlama şablonları
    CODING = "coding"             # Kod yazma şablonları
    REVIEW = "review"             # Kod inceleme şablonları
    TESTING = "testing"           # Test şablonları
    DEBUGGING = "debugging"       # Hata ayıklama şablonları
    DOCUMENTATION = "documentation"  # Dokümantasyon şablonları
    NLP = "nlp"                   # Türkçe NLP şablonları
    YKS = "yks"                   # YKS-spesifik şablonlar


class ModelTarget(Enum):
    """Hedef model"""
    CLAUDE = "claude"
    CODEX = "codex"
    GPT4 = "gpt4"
    ANY = "any"


@dataclass
class TemplateVariable:
    """Şablon değişkeni tanımı"""
    name: str
    description: str
    required: bool = True
    default: Optional[Any] = None
    validator: Optional[Callable[[Any], bool]] = None
    
    def validate(self, value: Any) -> bool:
        """Değeri doğrula"""
        if value is None:
            return not self.required
        if self.validator:
            return self.validator(value)
        return True


@dataclass
class Template:
    """Tek bir prompt şablonu"""
    id: str
    name: str
    category: TemplateCategory
    target_model: ModelTarget
    content: str
    description: str
    variables: list[TemplateVariable] = field(default_factory=list)
    version: str = "1.0.0"
    parent_id: Optional[str] = None  # Kalıtım için
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    success_rate: float = 1.0
    
    def render(self, context: dict[str, Any]) -> str:
        """
        Şablonu değişkenlerle render et
        
        Args:
            context: Değişken değerleri
            
        Returns:
            Render edilmiş prompt
            
        Raises:
            ValueError: Eksik veya geçersiz değişken varsa
        """
        # Değişkenleri doğrula
        for var in self.variables:
            value = context.get(var.name, var.default)
            if not var.validate(value):
                raise ValueError(f"Invalid value for variable '{var.name}': {value}")
            if value is None and var.required:
                raise ValueError(f"Required variable '{var.name}' is missing")
        
        # Interpolasyon
        result = self.content
        for var in self.variables:
            value = context.get(var.name, var.default)
            if value is not None:
                placeholder = f"{{{{{var.name}}}}}"  # {{variable}}
                result = result.replace(placeholder, str(value))
        
        self.usage_count += 1
        return result
    
    def get_variable_names(self) -> list[str]:
        """Şablondaki değişken isimlerini çıkar"""
        pattern = r'\{\{(\w+)\}\}'
        return re.findall(pattern, self.content)


class TemplateManager:
    """
    Merkezi Şablon Yöneticisi
    
    Orchestrator için tüm prompt şablonlarını yönetir.
    Şablon kalıtımı, versiyonlama ve kullanım takibi destekler.
    """
    
    def __init__(self, template_dir: Optional[Path] = None):
        self.templates: dict[str, Template] = {}
        self.template_dir = template_dir
        self._register_builtin_templates()
        logger.info(f"TemplateManager initialized with {len(self.templates)} templates")
    
    def register(self, template: Template) -> None:
        """Yeni şablon kaydet"""
        self.templates[template.id] = template
        logger.debug(f"Registered template: {template.id}")
    
    def get(self, template_id: str) -> Optional[Template]:
        """Şablon getir"""
        return self.templates.get(template_id)
    
    def render(self, template_id: str, context: dict[str, Any]) -> str:
        """
        Şablonu render et
        
        Args:
            template_id: Şablon ID
            context: Değişken değerleri
            
        Returns:
            Render edilmiş prompt
        """
        template = self.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        if not template.enabled:
            raise ValueError(f"Template is disabled: {template_id}")
        
        # Kalıtım varsa, parent şablonu önce render et
        if template.parent_id:
            parent = self.get(template.parent_id)
            if parent:
                parent_rendered = parent.render(context)
                context['parent_content'] = parent_rendered
        
        return template.render(context)
    
    def get_templates_by_category(self, category: TemplateCategory) -> list[Template]:
        """Kategoriye göre şablonları getir"""
        return [t for t in self.templates.values() if t.category == category]
    
    def get_templates_by_model(self, model: ModelTarget) -> list[Template]:
        """Modele göre şablonları getir"""
        return [t for t in self.templates.values() 
                if t.target_model == model or t.target_model == ModelTarget.ANY]
    
    def get_best_template(
        self, 
        category: TemplateCategory, 
        model: ModelTarget
    ) -> Optional[Template]:
        """
        Kategori ve model için en iyi şablonu seç
        
        En yüksek success_rate ve usage_count'a göre seçer.
        """
        candidates = [
            t for t in self.templates.values()
            if t.category == category 
            and t.enabled
            and (t.target_model == model or t.target_model == ModelTarget.ANY)
        ]
        
        if not candidates:
            return None
        
        # Success rate ve usage count'a göre sırala
        return max(candidates, key=lambda t: (t.success_rate, t.usage_count))
    
    def record_success(self, template_id: str, success: bool) -> None:
        """Şablon kullanım sonucunu kaydet"""
        template = self.get(template_id)
        if template:
            # Rolling average
            alpha = 0.1  # Smoothing factor
            template.success_rate = (1 - alpha) * template.success_rate + alpha * (1.0 if success else 0.0)
            template.updated_at = datetime.now()
    
    def export_templates(self, filepath: Path) -> None:
        """Şablonları JSON'a export et"""
        data = {}
        for tid, template in self.templates.items():
            data[tid] = {
                "id": template.id,
                "name": template.name,
                "category": template.category.value,
                "target_model": template.target_model.value,
                "content": template.content,
                "description": template.description,
                "version": template.version,
                "enabled": template.enabled,
                "usage_count": template.usage_count,
                "success_rate": template.success_rate,
            }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(data)} templates to {filepath}")
    
    def import_templates(self, filepath: Path) -> int:
        """JSON'dan şablonları import et"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        for tid, tdata in data.items():
            template = Template(
                id=tdata["id"],
                name=tdata["name"],
                category=TemplateCategory(tdata["category"]),
                target_model=ModelTarget(tdata["target_model"]),
                content=tdata["content"],
                description=tdata["description"],
                version=tdata.get("version", "1.0.0"),
                enabled=tdata.get("enabled", True),
            )
            self.register(template)
            count += 1
        
        logger.info(f"Imported {count} templates from {filepath}")
        return count
    
    def get_stats(self) -> dict:
        """Şablon istatistikleri"""
        total = len(self.templates)
        by_category = {}
        by_model = {}
        total_usage = 0
        avg_success = 0.0
        
        for template in self.templates.values():
            cat = template.category.value
            model = template.target_model.value
            by_category[cat] = by_category.get(cat, 0) + 1
            by_model[model] = by_model.get(model, 0) + 1
            total_usage += template.usage_count
            avg_success += template.success_rate
        
        return {
            "total_templates": total,
            "by_category": by_category,
            "by_model": by_model,
            "total_usage": total_usage,
            "average_success_rate": avg_success / total if total > 0 else 0.0,
            "enabled_count": sum(1 for t in self.templates.values() if t.enabled),
        }
    
    # ============ BUILTIN TEMPLATES ============
    
    def _register_builtin_templates(self):
        """Yerleşik şablonları kaydet"""
        
        # Planning Templates
        self.register(Template(
            id="PLAN_TASK",
            name="Task Planning",
            category=TemplateCategory.PLANNING,
            target_model=ModelTarget.CLAUDE,
            description="Görev planlama şablonu",
            content="""# Görev Planlama

## Görev
{{task_description}}

## Bağlam
{{context}}

## Mevcut Dosyalar
{{relevant_files}}

## Gereksinimler
1. "Doğru Kod" prensiplerine uy
2. Minimal değişiklik yap (maksimum 50 satır)
3. Mevcut patternları takip et
4. Test edilebilir kod üret

## Plan Formatı
1. Hangi dosyalar değişecek?
2. Her dosyada ne yapılacak?
3. Test stratejisi nedir?
4. Risk değerlendirmesi nedir?

Planı adım adım oluştur:""",
            variables=[
                TemplateVariable("task_description", "Görev açıklaması", required=True),
                TemplateVariable("context", "Proje bağlamı", required=False, default=""),
                TemplateVariable("relevant_files", "İlgili dosyalar", required=False, default=""),
            ]
        ))
        
        self.register(Template(
            id="PLAN_REFACTOR",
            name="Refactoring Plan",
            category=TemplateCategory.PLANNING,
            target_model=ModelTarget.CLAUDE,
            description="Refactoring planlama şablonu",
            content="""# Refactoring Planı

## Hedef
{{refactor_goal}}

## Mevcut Kod
```{{language}}
{{current_code}}
```

## Sorunlar
{{issues}}

## Kısıtlamalar
- Davranış değişmemeli
- Testler geçmeli
- API uyumluluğu korunmalı

## Refactoring Stratejisi
1. Hangi pattern uygulanacak?
2. Adım adım değişiklikler neler?
3. Geriye uyumluluk nasıl sağlanacak?

Detaylı plan:""",
            variables=[
                TemplateVariable("refactor_goal", "Refactoring hedefi", required=True),
                TemplateVariable("language", "Programlama dili", required=True),
                TemplateVariable("current_code", "Mevcut kod", required=True),
                TemplateVariable("issues", "Mevcut sorunlar", required=False, default=""),
            ]
        ))
        
        # Coding Templates
        self.register(Template(
            id="CODE_IMPLEMENT",
            name="Implementation",
            category=TemplateCategory.CODING,
            target_model=ModelTarget.CODEX,
            description="Kod implementasyon şablonu",
            content="""# Implementasyon

## Görev
{{task}}

## Spesifikasyon
{{spec}}

## Mevcut Yapı
{{existing_structure}}

## Kurallar
- Type hints kullan
- Docstring ekle
- Error handling yap
- Unit test düşün

## Kod:""",
            variables=[
                TemplateVariable("task", "Görev açıklaması", required=True),
                TemplateVariable("spec", "Teknik spesifikasyon", required=True),
                TemplateVariable("existing_structure", "Mevcut kod yapısı", required=False, default=""),
            ]
        ))
        
        # Review Templates
        self.register(Template(
            id="REVIEW_CODE",
            name="Code Review",
            category=TemplateCategory.REVIEW,
            target_model=ModelTarget.CLAUDE,
            description="Kod inceleme şablonu",
            content="""# Kod İnceleme

## Değişiklikler
```diff
{{diff}}
```

## İnceleme Kriterleri
1. **Doğruluk**: Kod beklendiği gibi çalışıyor mu?
2. **Güvenlik**: Güvenlik açığı var mı?
3. **Performans**: Performans sorunu var mı?
4. **Okunabilirlik**: Kod anlaşılır mı?
5. **Test**: Yeterli test coverage var mı?

## Değerlendirme
Her kriter için:
- ✅ PASS / ⚠️ WARNING / ❌ FAIL
- Açıklama
- Öneri (varsa)

İncelemeye başla:""",
            variables=[
                TemplateVariable("diff", "Kod değişiklikleri (diff formatında)", required=True),
            ]
        ))
        
        # Testing Templates
        self.register(Template(
            id="TEST_GENERATE",
            name="Test Generation",
            category=TemplateCategory.TESTING,
            target_model=ModelTarget.CODEX,
            description="Test üretim şablonu",
            content="""# Test Üretimi

## Test Edilecek Kod
```{{language}}
{{code}}
```

## Test Framework
{{framework}}

## Test Tipleri
- Unit tests
- Edge cases
- Error handling
- Integration (varsa)

## Gereksinimler
- Her fonksiyon için en az 2 test
- Edge case'ler dahil
- Mock kullan (gerekirse)
- Türkçe açıklamalar

Testleri oluştur:""",
            variables=[
                TemplateVariable("code", "Test edilecek kod", required=True),
                TemplateVariable("language", "Programlama dili", required=True),
                TemplateVariable("framework", "Test framework", required=True, default="pytest"),
            ]
        ))
        
        # Debugging Templates
        self.register(Template(
            id="DEBUG_ERROR",
            name="Error Debugging",
            category=TemplateCategory.DEBUGGING,
            target_model=ModelTarget.CLAUDE,
            description="Hata ayıklama şablonu",
            content="""# Hata Analizi

## Hata Mesajı
```
{{error_message}}
```

## Stack Trace
```
{{stack_trace}}
```

## İlgili Kod
```{{language}}
{{relevant_code}}
```

## Bağlam
{{context}}

## Analiz Adımları
1. Hatanın kök nedeni nedir?
2. Hangi satır/fonksiyon sorumlu?
3. Düzeltme önerisi nedir?
4. Benzer hataları önlemek için ne yapılmalı?

Analizi başlat:""",
            variables=[
                TemplateVariable("error_message", "Hata mesajı", required=True),
                TemplateVariable("stack_trace", "Stack trace", required=False, default=""),
                TemplateVariable("relevant_code", "İlgili kod", required=False, default=""),
                TemplateVariable("language", "Programlama dili", required=True, default="python"),
                TemplateVariable("context", "Ek bağlam", required=False, default=""),
            ]
        ))
        
        # YKS-Specific Templates
        self.register(Template(
            id="YKS_QUESTION_GENERATE",
            name="YKS Question Generation",
            category=TemplateCategory.YKS,
            target_model=ModelTarget.CLAUDE,
            description="YKS soru üretim şablonu",
            content="""# YKS Soru Üretimi

## Konu
{{topic}}

## Alt Konu
{{subtopic}}

## Zorluk Seviyesi
{{difficulty}} (1-10)

## Soru Tipi
{{question_type}}

## Örnek Sorular
{{example_questions}}

## Kurallar
1. ÖSYM formatına uy
2. Türkçe dil bilgisi kurallarına dikkat et
3. Şıklar mantıklı olsun
4. Doğru cevap tek olmalı
5. Açıklama ekle

## Üretilecek Soru Sayısı
{{count}}

Soruları oluştur:""",
            variables=[
                TemplateVariable("topic", "Ana konu", required=True),
                TemplateVariable("subtopic", "Alt konu", required=True),
                TemplateVariable("difficulty", "Zorluk (1-10)", required=True, default="5"),
                TemplateVariable("question_type", "Soru tipi", required=True, default="çoktan seçmeli"),
                TemplateVariable("example_questions", "Örnek sorular", required=False, default=""),
                TemplateVariable("count", "Soru sayısı", required=True, default="3"),
            ]
        ))
        
        self.register(Template(
            id="YKS_ANSWER_MATCH",
            name="YKS Answer Matching",
            category=TemplateCategory.YKS,
            target_model=ModelTarget.CLAUDE,
            description="YKS soru-cevap eşleştirme şablonu",
            content="""# Soru-Cevap Eşleştirme

## Soru
{{question_text}}

## Soru Numarası
{{question_number}}

## Sayfa
{{page_number}}

## Kitap
{{book_name}}

## Cevap Anahtarı Adayları
{{answer_candidates}}

## Eşleştirme Kriterleri
1. Soru numarası eşleşmeli
2. Sayfa numarası tutarlı olmalı
3. Kitap adı doğru olmalı

## Güven Skoru Hesapla
- Exact match: 1.0
- Fuzzy match: 0.8-0.99
- Low confidence: <0.8

Eşleştirme sonucu:""",
            variables=[
                TemplateVariable("question_text", "Soru metni", required=True),
                TemplateVariable("question_number", "Soru numarası", required=True),
                TemplateVariable("page_number", "Sayfa numarası", required=False),
                TemplateVariable("book_name", "Kitap adı", required=True),
                TemplateVariable("answer_candidates", "Aday cevaplar", required=True),
            ]
        ))
        
        # Turkish NLP Templates
        self.register(Template(
            id="NLP_TURKISH_NORMALIZE",
            name="Turkish Text Normalization",
            category=TemplateCategory.NLP,
            target_model=ModelTarget.ANY,
            description="Türkçe metin normalizasyon şablonu",
            content="""# Türkçe Metin Normalizasyonu

## Metin
{{text}}

## Normalizasyon Adımları
1. Unicode NFC normalizasyonu
2. Türkçe karakter düzeltme (İ→i, I→ı)
3. OCR hata düzeltme
4. Noktalama standartlaştırma
5. Boşluk temizleme

## OCR Hata Düzeltmeleri
- 1/l/I karışıklığı
- ş/s, ğ/g, ü/u, ö/o, ç/c
- Sayı/harf karışıklığı

## Normalize edilmiş metin:""",
            variables=[
                TemplateVariable("text", "Normalize edilecek metin", required=True),
            ]
        ))


# Singleton instance
_template_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """Singleton TemplateManager instance"""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager
