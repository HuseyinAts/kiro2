"""
SignalDictionary: Sinyal-Aksiyon Eşleştirme Sistemi.

STABIL Faz - Modül 2/9
Kod tabanından gelen sinyalleri (pattern, hata, metrik) aksiyonlara dönüştürür.

Temel Özellikler:
- Sinyal tanımlama ve kategorizasyon
- Aksiyon şablonları ve mapping
- Öncelik ve güven skoru
- Öğrenme ve adaptasyon
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Callable, Any, Pattern
from enum import Enum, auto
from datetime import datetime


class SignalCategory(Enum):
    """Sinyal kategorileri."""
    ERROR = auto()          # Hata sinyalleri
    WARNING = auto()        # Uyarı sinyalleri
    PATTERN = auto()        # Kod pattern'leri
    METRIC = auto()         # Metrik eşik aşımları
    SECURITY = auto()       # Güvenlik sinyalleri
    PERFORMANCE = auto()    # Performans sinyalleri
    STYLE = auto()          # Kod stili sinyalleri
    TEST = auto()           # Test sinyalleri
    DEPENDENCY = auto()     # Bağımlılık sinyalleri
    CUSTOM = auto()         # Özel sinyaller


class ActionType(Enum):
    """Aksiyon tipleri."""
    FIX = auto()            # Otomatik düzeltme
    SUGGEST = auto()        # Öneri sun
    ALERT = auto()          # Uyarı ver
    BLOCK = auto()          # İşlemi engelle
    LOG = auto()            # Sadece logla
    ESCALATE = auto()       # Üst seviyeye yükselt
    IGNORE = auto()         # Yoksay (öğrenilmiş)


class SignalPriority(Enum):
    """Sinyal önceliği."""
    CRITICAL = 1    # Acil müdahale
    HIGH = 2        # Yüksek öncelik
    MEDIUM = 3      # Normal öncelik
    LOW = 4         # Düşük öncelik
    INFO = 5        # Bilgilendirme


@dataclass
class Signal:
    """Tek bir sinyal tanımı."""
    id: str
    name: str
    category: SignalCategory
    priority: SignalPriority
    
    # Pattern tanımları
    patterns: List[str] = field(default_factory=list)  # Regex patterns
    keywords: List[str] = field(default_factory=list)  # Anahtar kelimeler
    file_patterns: List[str] = field(default_factory=list)  # Dosya pattern'leri
    
    # Metadata
    description: str = ""
    examples: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Öğrenme
    hit_count: int = 0
    last_hit: Optional[datetime] = None
    false_positive_count: int = 0
    
    # Compiled patterns (runtime)
    _compiled_patterns: List[Pattern] = field(default_factory=list, repr=False)
    
    def __post_init__(self):
        """Pattern'leri derle."""
        self._compiled_patterns = []
        for p in self.patterns:
            try:
                self._compiled_patterns.append(re.compile(p, re.IGNORECASE | re.MULTILINE))
            except re.error:
                pass  # Invalid pattern, skip
    
    def matches(self, text: str, filename: str = "") -> bool:
        """Sinyal metinle eşleşiyor mu?"""
        # Dosya pattern kontrolü - önce dosya tipini kontrol et
        # Eğer file_patterns tanımlıysa VE dosya adı uyuşmuyorsa, False dön
        if self.file_patterns and filename:
            file_matches = False
            for fp in self.file_patterns:
                if re.match(fp, filename, re.IGNORECASE):
                    file_matches = True
                    break
            if not file_matches:
                return False  # Dosya tipi uyuşmuyor
        
        # Pattern kontrolü (içerik bazlı)
        for pattern in self._compiled_patterns:
            if pattern.search(text):
                return True
        
        # Keyword kontrolü (içerik bazlı)
        text_lower = text.lower()
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def record_hit(self) -> None:
        """Eşleşme kaydet."""
        self.hit_count += 1
        self.last_hit = datetime.now()
    
    def record_false_positive(self) -> None:
        """False positive kaydet."""
        self.false_positive_count += 1
    
    @property
    def confidence(self) -> float:
        """Güven skoru (0-1)."""
        if self.hit_count == 0:
            return 0.5  # Baseline
        
        total = self.hit_count + self.false_positive_count
        if total == 0:
            return 0.5
        
        return (self.hit_count - self.false_positive_count) / total
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.name,
            "priority": self.priority.name,
            "patterns": self.patterns,
            "keywords": self.keywords,
            "file_patterns": self.file_patterns,
            "description": self.description,
            "hit_count": self.hit_count,
            "false_positive_count": self.false_positive_count,
            "confidence": self.confidence,
        }


@dataclass
class Action:
    """Aksiyon tanımı."""
    id: str
    name: str
    action_type: ActionType
    
    # Aksiyon detayları
    template: str = ""  # Aksiyon şablonu (değişkenli)
    handler: Optional[str] = None  # Handler fonksiyon adı
    
    # Koşullar
    requires_confirmation: bool = False
    auto_apply: bool = False
    cooldown_seconds: int = 0  # Tekrar uygulanma süresi
    
    # Metadata
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    # İstatistik
    apply_count: int = 0
    success_count: int = 0
    last_applied: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Başarı oranı."""
        if self.apply_count == 0:
            return 0.0
        return self.success_count / self.apply_count
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "action_type": self.action_type.name,
            "template": self.template,
            "requires_confirmation": self.requires_confirmation,
            "auto_apply": self.auto_apply,
            "apply_count": self.apply_count,
            "success_rate": self.success_rate,
        }


@dataclass
class SignalActionMapping:
    """Sinyal-Aksiyon eşleştirmesi."""
    signal_id: str
    action_id: str
    
    # Eşleştirme koşulları
    min_confidence: float = 0.5
    context_conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Öncelik (düşük = yüksek öncelik)
    priority_override: Optional[int] = None
    
    # İstatistik
    trigger_count: int = 0
    effective_count: int = 0  # Gerçekten uygulanan
    
    @property
    def effectiveness(self) -> float:
        """Etkinlik oranı."""
        if self.trigger_count == 0:
            return 0.0
        return self.effective_count / self.trigger_count
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "action_id": self.action_id,
            "min_confidence": self.min_confidence,
            "trigger_count": self.trigger_count,
            "effectiveness": self.effectiveness,
        }


@dataclass
class SignalMatch:
    """Sinyal eşleşme sonucu."""
    signal: Signal
    action: Optional[Action]
    matched_text: str
    matched_pattern: str
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal.id,
            "signal_name": self.signal.name,
            "action_id": self.action.id if self.action else None,
            "action_type": self.action.action_type.name if self.action else None,
            "matched_text": self.matched_text[:100],  # Truncate
            "matched_pattern": self.matched_pattern,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }


class SignalDictionary:
    """
    Sinyal-Aksiyon sözlüğü yöneticisi.
    
    Kullanım:
        sd = SignalDictionary()
        sd.register_signal(Signal(...))
        sd.register_action(Action(...))
        sd.map_signal_to_action("signal_id", "action_id")
        
        matches = sd.detect_signals("some error text")
        for match in matches:
            print(f"{match.signal.name} -> {match.action.name}")
    """
    
    def __init__(self, persistence_path: Optional[str] = None):
        self.signals: Dict[str, Signal] = {}
        self.actions: Dict[str, Action] = {}
        self.mappings: List[SignalActionMapping] = []
        self.persistence_path = Path(persistence_path) if persistence_path else None
        
        # Yerleşik sinyalleri yükle
        self._load_builtin_signals()
        
        # Persistence'tan yükle
        if self.persistence_path and self.persistence_path.exists():
            self._load_from_file()
    
    def _load_builtin_signals(self) -> None:
        """Yerleşik sinyalleri yükle."""
        # ERROR sinyalleri
        self.register_signal(Signal(
            id="err_import",
            name="Import Error",
            category=SignalCategory.ERROR,
            priority=SignalPriority.HIGH,
            patterns=[
                r"ImportError:\s*(.+)",
                r"ModuleNotFoundError:\s*(.+)",
                r"No module named\s+['\"](\w+)['\"]",
            ],
            keywords=["import error", "module not found", "no module named"],
            description="Python import hatası tespit edildi",
        ))
        
        self.register_signal(Signal(
            id="err_syntax",
            name="Syntax Error",
            category=SignalCategory.ERROR,
            priority=SignalPriority.CRITICAL,
            patterns=[
                r"SyntaxError:\s*(.+)",
                r"IndentationError:\s*(.+)",
                r"TabError:\s*(.+)",
            ],
            keywords=["syntax error", "indentation error", "unexpected indent"],
            description="Python syntax hatası tespit edildi",
        ))
        
        self.register_signal(Signal(
            id="err_type",
            name="Type Error",
            category=SignalCategory.ERROR,
            priority=SignalPriority.HIGH,
            patterns=[
                r"TypeError:\s*(.+)",
                r"AttributeError:\s*(.+)",
            ],
            keywords=["type error", "attribute error", "has no attribute"],
            description="Python tip hatası tespit edildi",
        ))
        
        # WARNING sinyalleri
        self.register_signal(Signal(
            id="warn_deprecation",
            name="Deprecation Warning",
            category=SignalCategory.WARNING,
            priority=SignalPriority.MEDIUM,
            patterns=[
                r"DeprecationWarning:\s*(.+)",
                r"FutureWarning:\s*(.+)",
            ],
            keywords=["deprecated", "will be removed", "future version"],
            description="Deprecation uyarısı tespit edildi",
        ))
        
        # SECURITY sinyalleri
        self.register_signal(Signal(
            id="sec_hardcoded_secret",
            name="Hardcoded Secret",
            category=SignalCategory.SECURITY,
            priority=SignalPriority.CRITICAL,
            patterns=[
                r"^\s*(password|secret|api_key|token)\s*=\s*['\"][^'\"]{4,}['\"]",
                r"^\s*(AWS_SECRET|PRIVATE_KEY)\s*=\s*['\"][^'\"]+['\"]",
            ],
            keywords=[],  # Pattern-only detection
            file_patterns=[r".*\.py$", r".*\.js$", r".*\.ts$"],
            description="Hardcoded secret tespit edildi",
        ))
        
        self.register_signal(Signal(
            id="sec_sql_injection",
            name="SQL Injection Risk",
            category=SignalCategory.SECURITY,
            priority=SignalPriority.CRITICAL,
            patterns=[
                r"execute\s*\(\s*['\"].*%s",
                r"f\".*SELECT.*{",
                r"\".*SELECT.*\"\s*\+",
            ],
            keywords=["execute(", "raw sql", "string concatenation sql"],
            description="Potansiyel SQL injection riski",
        ))
        
        # STYLE sinyalleri
        self.register_signal(Signal(
            id="style_line_length",
            name="Long Line",
            category=SignalCategory.STYLE,
            priority=SignalPriority.LOW,
            patterns=[
                r"^.{120,}$",  # 120+ karakter satır
            ],
            description="Çok uzun satır tespit edildi",
        ))
        
        self.register_signal(Signal(
            id="style_todo",
            name="TODO Comment",
            category=SignalCategory.STYLE,
            priority=SignalPriority.INFO,
            patterns=[
                r"#\s*TODO:?\s*(.+)",
                r"//\s*TODO:?\s*(.+)",
                r"#\s*FIXME:?\s*(.+)",
            ],
            keywords=["TODO", "FIXME", "HACK", "XXX"],
            description="TODO/FIXME yorumu tespit edildi",
        ))
        
        # TEST sinyalleri
        self.register_signal(Signal(
            id="test_failure",
            name="Test Failure",
            category=SignalCategory.TEST,
            priority=SignalPriority.HIGH,
            patterns=[
                r"FAILED\s+(.+)",
                r"AssertionError:\s*(.+)",
                r"test.*FAILED",
            ],
            keywords=["FAILED", "assertion error", "test failed"],
            description="Test başarısızlığı tespit edildi",
        ))
        
        # PERFORMANCE sinyalleri
        self.register_signal(Signal(
            id="perf_n_plus_one",
            name="N+1 Query Pattern",
            category=SignalCategory.PERFORMANCE,
            priority=SignalPriority.MEDIUM,
            patterns=[
                r"for\s+.*\s+in\s+.*:\s*\n\s+.*\.query",
                r"for\s+.*\s+in\s+.*:\s*\n\s+.*SELECT",
            ],
            description="N+1 query pattern tespit edildi",
        ))
        
        # Yerleşik aksiyonları yükle
        self._load_builtin_actions()
        
        # Default mappings
        self._create_default_mappings()
    
    def _load_builtin_actions(self) -> None:
        """Yerleşik aksiyonları yükle."""
        self.register_action(Action(
            id="act_fix_import",
            name="Fix Import",
            action_type=ActionType.FIX,
            template="Add missing import: {module}",
            auto_apply=False,
            description="Eksik import'u ekle",
        ))
        
        self.register_action(Action(
            id="act_alert_security",
            name="Security Alert",
            action_type=ActionType.ALERT,
            template="SECURITY ISSUE: {description}",
            requires_confirmation=True,
            description="Güvenlik uyarısı ver",
        ))
        
        self.register_action(Action(
            id="act_block_commit",
            name="Block Commit",
            action_type=ActionType.BLOCK,
            template="Commit blocked due to: {reason}",
            requires_confirmation=False,
            description="Commit'i engelle",
        ))
        
        self.register_action(Action(
            id="act_suggest_fix",
            name="Suggest Fix",
            action_type=ActionType.SUGGEST,
            template="Suggested fix: {suggestion}",
            description="Düzeltme önerisi sun",
        ))
        
        self.register_action(Action(
            id="act_log_only",
            name="Log Only",
            action_type=ActionType.LOG,
            template="Logged: {message}",
            description="Sadece logla",
        ))
    
    def _create_default_mappings(self) -> None:
        """Varsayılan sinyal-aksiyon eşleştirmeleri."""
        # Import error -> Fix import
        self.map_signal_to_action("err_import", "act_fix_import")
        
        # Syntax error -> Block commit
        self.map_signal_to_action("err_syntax", "act_block_commit")
        
        # Security issues -> Alert + Block
        self.map_signal_to_action("sec_hardcoded_secret", "act_alert_security")
        self.map_signal_to_action("sec_sql_injection", "act_block_commit")
        
        # Style issues -> Suggest
        self.map_signal_to_action("style_line_length", "act_suggest_fix")
        self.map_signal_to_action("style_todo", "act_log_only")
        
        # Test failure -> Alert
        self.map_signal_to_action("test_failure", "act_alert_security")
    
    def register_signal(self, signal: Signal) -> None:
        """Sinyal kaydet."""
        self.signals[signal.id] = signal
    
    def register_action(self, action: Action) -> None:
        """Aksiyon kaydet."""
        self.actions[action.id] = action
    
    def map_signal_to_action(
        self,
        signal_id: str,
        action_id: str,
        min_confidence: float = 0.5,
        context_conditions: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Sinyal-aksiyon eşleştirmesi oluştur."""
        if signal_id not in self.signals:
            raise ValueError(f"Signal not found: {signal_id}")
        if action_id not in self.actions:
            raise ValueError(f"Action not found: {action_id}")
        
        mapping = SignalActionMapping(
            signal_id=signal_id,
            action_id=action_id,
            min_confidence=min_confidence,
            context_conditions=context_conditions or {},
        )
        self.mappings.append(mapping)
    
    def detect_signals(
        self,
        text: str,
        filename: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> List[SignalMatch]:
        """
        Metinde sinyalleri tespit et.
        
        Args:
            text: Analiz edilecek metin
            filename: Dosya adı (opsiyonel)
            context: Ek bağlam bilgisi
        
        Returns:
            Tespit edilen sinyal eşleşmeleri
        """
        matches = []
        context = context or {}
        
        for signal in self.signals.values():
            if signal.matches(text, filename):
                # Eşleşen pattern'i bul
                matched_pattern = ""
                matched_text = ""
                
                for pattern in signal._compiled_patterns:
                    match = pattern.search(text)
                    if match:
                        matched_pattern = pattern.pattern
                        matched_text = match.group(0)
                        break
                
                if not matched_text:
                    # Keyword match
                    for keyword in signal.keywords:
                        if keyword.lower() in text.lower():
                            matched_pattern = f"keyword:{keyword}"
                            idx = text.lower().find(keyword.lower())
                            matched_text = text[max(0, idx-20):idx+len(keyword)+20]
                            break
                
                # Aksiyon bul
                action = self._find_action_for_signal(signal, context)
                
                # Hit kaydet
                signal.record_hit()
                
                matches.append(SignalMatch(
                    signal=signal,
                    action=action,
                    matched_text=matched_text,
                    matched_pattern=matched_pattern,
                    confidence=signal.confidence,
                    context=context,
                ))
        
        # Önceliğe göre sırala
        matches.sort(key=lambda m: m.signal.priority.value)
        
        return matches
    
    def _find_action_for_signal(
        self,
        signal: Signal,
        context: Dict[str, Any],
    ) -> Optional[Action]:
        """Sinyal için uygun aksiyonu bul."""
        for mapping in self.mappings:
            if mapping.signal_id != signal.id:
                continue
            
            # Confidence kontrolü
            if signal.confidence < mapping.min_confidence:
                continue
            
            # Context koşulları kontrolü
            if mapping.context_conditions:
                if not all(
                    context.get(k) == v
                    for k, v in mapping.context_conditions.items()
                ):
                    continue
            
            # Aksiyonu döndür
            action = self.actions.get(mapping.action_id)
            if action:
                mapping.trigger_count += 1
                return action
        
        return None
    
    def get_signal(self, signal_id: str) -> Optional[Signal]:
        """Sinyal al."""
        return self.signals.get(signal_id)
    
    def get_action(self, action_id: str) -> Optional[Action]:
        """Aksiyon al."""
        return self.actions.get(action_id)
    
    def get_signals_by_category(self, category: SignalCategory) -> List[Signal]:
        """Kategoriye göre sinyalleri al."""
        return [s for s in self.signals.values() if s.category == category]
    
    def get_statistics(self) -> Dict[str, Any]:
        """İstatistikleri al."""
        return {
            "total_signals": len(self.signals),
            "total_actions": len(self.actions),
            "total_mappings": len(self.mappings),
            "signals_by_category": {
                cat.name: len(self.get_signals_by_category(cat))
                for cat in SignalCategory
            },
            "top_signals": sorted(
                [{"id": s.id, "hits": s.hit_count} for s in self.signals.values()],
                key=lambda x: x["hits"],
                reverse=True,
            )[:10],
        }
    
    def save(self) -> None:
        """Sözlüğü dosyaya kaydet."""
        if not self.persistence_path:
            return
        
        data = {
            "signals": {k: v.to_dict() for k, v in self.signals.items()},
            "actions": {k: v.to_dict() for k, v in self.actions.items()},
            "mappings": [m.to_dict() for m in self.mappings],
            "saved_at": datetime.now().isoformat(),
        }
        
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.persistence_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_from_file(self) -> None:
        """Dosyadan yükle (sadece istatistikler)."""
        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Mevcut sinyallerin istatistiklerini güncelle
            for signal_id, signal_data in data.get("signals", {}).items():
                if signal_id in self.signals:
                    self.signals[signal_id].hit_count = signal_data.get("hit_count", 0)
                    self.signals[signal_id].false_positive_count = signal_data.get("false_positive_count", 0)
        except Exception:
            pass  # Yükleme başarısız, varsayılanlarla devam


# Singleton instance
_dictionary: Optional[SignalDictionary] = None


def get_signal_dictionary(persistence_path: Optional[str] = None) -> SignalDictionary:
    """
    SignalDictionary singleton instance'ı al.
    
    Args:
        persistence_path: Kalıcılık dosyası yolu (opsiyonel)
    
    Returns:
        SignalDictionary instance
    """
    global _dictionary
    
    if _dictionary is None:
        _dictionary = SignalDictionary(persistence_path)
    
    return _dictionary


def reset_dictionary() -> None:
    """Dictionary'yi sıfırla."""
    global _dictionary
    _dictionary = None
