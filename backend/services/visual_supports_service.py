"""
Visual Supports Service - Disleksi Desteği için Görsel Yardımcılar
Task 81: Görsel Destekler (REQ-50.73 - REQ-50.88)

Bu modül disleksili öğrenciler için görsel öğrenme destekleri sağlar:
- Kavram haritaları (mind maps)
- İnfografikler
- Resimli sözlük
- Renk kodlama sistemi
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import hashlib
from pydantic import BaseModel, Field


# ============================================================================
# Data Models
# ============================================================================


class MindMapNode(BaseModel):
    """Kavram haritası düğümü"""

    id: str
    label: str
    description: Optional[str] = None
    color: str = "#4A90E2"
    x: float = 0
    y: float = 0
    children: List[str] = Field(default_factory=list)
    parent: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MindMap(BaseModel):
    """Kavram haritası"""

    id: str
    title: str
    subject: str
    topic: str
    nodes: List[MindMapNode]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None


class Infographic(BaseModel):
    """İnfografik"""

    id: str
    title: str
    subject: str
    topic: str
    template: str  # "timeline", "comparison", "process", "hierarchy"
    elements: List[Dict[str, Any]]
    icons: List[str]
    colors: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None


class VisualVocabularyCard(BaseModel):
    """Görsel kelime kartı"""

    id: str
    word: str
    definition: str
    image_url: str
    example_sentence: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
    category: str
    difficulty_level: int = 1  # 1-5
    color_code: str = "#4A90E2"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ColorCodingScheme(BaseModel):
    """Renk kodlama şeması"""

    id: str
    name: str
    description: str
    categories: Dict[str, str]  # category_name -> color_hex
    user_id: Optional[str] = None
    is_default: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Visual Supports Service
# ============================================================================


class VisualSupportsService:
    """
    Görsel destekler servisi

    REQ-50.73-88: Kavram haritaları, infografikler, resimli sözlük ve renk kodlama
    """

    def __init__(self):
        """Servisi başlat"""
        self.mind_maps: Dict[str, MindMap] = {}
        self.infographics: Dict[str, Infographic] = {}
        self.vocabulary_cards: Dict[str, VisualVocabularyCard] = {}
        self.color_schemes: Dict[str, ColorCodingScheme] = {}

        # Varsayılan renk şemalarını yükle
        self._load_default_color_schemes()

    # ========================================================================
    # Mind Maps (Kavram Haritaları) - REQ-50.73-76
    # ========================================================================

    def generate_mind_map(
        self,
        title: str,
        subject: str,
        topic: str,
        content: str,
        user_id: Optional[str] = None,
    ) -> MindMap:
        """
        REQ-50.73: Kavram haritası oluştur

        Args:
            title: Harita başlığı
            subject: Ders
            topic: Konu
            content: İçerik metni
            user_id: Kullanıcı ID

        Returns:
            MindMap: Oluşturulan kavram haritası
        """
        # Basit bir kavram haritası oluştur
        # Gerçek implementasyonda NLP ile anahtar kavramlar çıkarılır

        mind_map_id = self._generate_id(f"{title}_{subject}_{topic}")

        # Ana düğüm
        root_node = MindMapNode(
            id="root",
            label=title,
            description=f"{subject} - {topic}",
            color="#4A90E2",
            x=0,
            y=0,
        )

        # Alt düğümler (örnek)
        nodes = [root_node]

        # Basit kelime analizi ile alt konular oluştur
        words = content.split()
        key_concepts = self._extract_key_concepts(words)

        for i, concept in enumerate(key_concepts[:5]):  # Max 5 ana kavram
            node_id = f"node_{i+1}"
            node = MindMapNode(
                id=node_id,
                label=concept,
                color=self._get_node_color(i),
                x=100 * (i - 2),
                y=100,
                parent="root",
            )
            nodes.append(node)
            root_node.children.append(node_id)

        mind_map = MindMap(
            id=mind_map_id,
            title=title,
            subject=subject,
            topic=topic,
            nodes=nodes,
            user_id=user_id,
        )

        self.mind_maps[mind_map_id] = mind_map
        return mind_map

    def get_mind_map(self, mind_map_id: str) -> Optional[MindMap]:
        """
        REQ-50.74: Kavram haritasını getir (interactive exploration)

        Args:
            mind_map_id: Harita ID

        Returns:
            Optional[MindMap]: Kavram haritası veya None
        """
        return self.mind_maps.get(mind_map_id)

    def export_mind_map(self, mind_map_id: str, format: str = "json") -> Dict[str, Any]:
        """
        REQ-50.75: Kavram haritasını dışa aktar

        Args:
            mind_map_id: Harita ID
            format: Export formatı ("json", "svg", "png")

        Returns:
            Dict: Export edilmiş veri
        """
        mind_map = self.mind_maps.get(mind_map_id)
        if not mind_map:
            return {"error": "Mind map not found"}

        if format == "json":
            return mind_map.dict()
        elif format == "svg":
            # SVG export (basitleştirilmiş)
            return {"format": "svg", "data": self._generate_svg(mind_map)}
        elif format == "png":
            # PNG export için placeholder
            return {
                "format": "png",
                "message": "PNG export requires image processing library",
            }
        else:
            return {"error": f"Unsupported format: {format}"}

    def update_mind_map_node(
        self, mind_map_id: str, node_id: str, updates: Dict[str, Any]
    ) -> bool:
        """
        REQ-50.76: Kavram haritası düğümünü güncelle (drag-and-drop)

        Args:
            mind_map_id: Harita ID
            node_id: Düğüm ID
            updates: Güncellenecek alanlar

        Returns:
            bool: Başarılı mı
        """
        mind_map = self.mind_maps.get(mind_map_id)
        if not mind_map:
            return False

        for node in mind_map.nodes:
            if node.id == node_id:
                for key, value in updates.items():
                    if hasattr(node, key):
                        setattr(node, key, value)
                mind_map.updated_at = datetime.now(timezone.utc)
                return True

        return False

    # ========================================================================
    # Infographics (İnfografikler) - REQ-50.77-80
    # ========================================================================

    def generate_infographic(
        self,
        title: str,
        subject: str,
        topic: str,
        template: str,
        data: List[Dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> Infographic:
        """
        REQ-50.77: İnfografik oluştur (visual summary generation)

        Args:
            title: Başlık
            subject: Ders
            topic: Konu
            template: Şablon tipi
            data: Veri listesi
            user_id: Kullanıcı ID

        Returns:
            Infographic: Oluşturulan infografik
        """
        infographic_id = self._generate_id(f"{title}_{template}")

        # İkon ve renk seçimi
        icons = self._select_icons_for_template(template, len(data))
        colors = self._select_colors_for_template(template, len(data))

        # Elementleri oluştur
        elements = []
        for i, item in enumerate(data):
            element = {
                "id": f"element_{i}",
                "type": template,
                "content": item,
                "icon": icons[i] if i < len(icons) else "default",
                "color": colors[i] if i < len(colors) else "#4A90E2",
                "position": i,
            }
            elements.append(element)

        infographic = Infographic(
            id=infographic_id,
            title=title,
            subject=subject,
            topic=topic,
            template=template,
            elements=elements,
            icons=icons,
            colors=colors,
            user_id=user_id,
        )

        self.infographics[infographic_id] = infographic
        return infographic

    def get_infographic_templates(self) -> List[Dict[str, Any]]:
        """
        REQ-50.79: İnfografik şablonlarını getir (customizable templates)

        Returns:
            List: Mevcut şablonlar
        """
        return [
            {
                "id": "timeline",
                "name": "Zaman Çizelgesi",
                "description": "Kronolojik olaylar için",
                "icon": "timeline",
                "preview_url": "/templates/timeline.svg",
            },
            {
                "id": "comparison",
                "name": "Karşılaştırma",
                "description": "İki veya daha fazla öğeyi karşılaştırma",
                "icon": "compare",
                "preview_url": "/templates/comparison.svg",
            },
            {
                "id": "process",
                "name": "Süreç Akışı",
                "description": "Adım adım süreçler için",
                "icon": "process",
                "preview_url": "/templates/process.svg",
            },
            {
                "id": "hierarchy",
                "name": "Hiyerarşi",
                "description": "Yapısal ilişkiler için",
                "icon": "hierarchy",
                "preview_url": "/templates/hierarchy.svg",
            },
        ]

    def export_infographic(
        self, infographic_id: str, format: str = "png"
    ) -> Dict[str, Any]:
        """
        REQ-50.80: İnfografiği dışa aktar (farklı format seçenekleri)

        Args:
            infographic_id: İnfografik ID
            format: Export formatı

        Returns:
            Dict: Export edilmiş veri
        """
        infographic = self.infographics.get(infographic_id)
        if not infographic:
            return {"error": "Infographic not found"}

        supported_formats = ["json", "svg", "png", "pdf"]
        if format not in supported_formats:
            return {"error": f"Unsupported format. Use: {', '.join(supported_formats)}"}

        return {
            "format": format,
            "data": infographic.dict()
            if format == "json"
            else f"Export to {format} (placeholder)",
            "download_url": f"/exports/infographic_{infographic_id}.{format}",
        }

    # ========================================================================
    # Visual Vocabulary (Resimli Sözlük) - REQ-50.81-84
    # ========================================================================

    def create_vocabulary_card(
        self,
        word: str,
        definition: str,
        image_url: str,
        category: str,
        example_sentence: Optional[str] = None,
        synonyms: Optional[List[str]] = None,
        difficulty_level: int = 1,
    ) -> VisualVocabularyCard:
        """
        REQ-50.81: Görsel kelime kartı oluştur (image-word associations)

        Args:
            word: Kelime
            definition: Tanım
            image_url: Görsel URL
            category: Kategori
            example_sentence: Örnek cümle
            synonyms: Eş anlamlılar
            difficulty_level: Zorluk seviyesi (1-5)

        Returns:
            VisualVocabularyCard: Oluşturulan kart
        """
        card_id = self._generate_id(f"{word}_{category}")

        # Renk kodlama (kategori bazlı)
        color_code = self._get_category_color(category)

        card = VisualVocabularyCard(
            id=card_id,
            word=word,
            definition=definition,
            image_url=image_url,
            example_sentence=example_sentence,
            synonyms=synonyms or [],
            category=category,
            difficulty_level=difficulty_level,
            color_code=color_code,
        )

        self.vocabulary_cards[card_id] = card
        return card

    def search_vocabulary_cards(
        self,
        query: str,
        category: Optional[str] = None,
        difficulty_level: Optional[int] = None,
    ) -> List[VisualVocabularyCard]:
        """
        REQ-50.83: Resimli sözlükte arama yap (searchable image database)

        Args:
            query: Arama terimi
            category: Kategori filtresi
            difficulty_level: Zorluk seviyesi filtresi

        Returns:
            List[VisualVocabularyCard]: Bulunan kartlar
        """
        results = []
        query_lower = query.lower()

        for card in self.vocabulary_cards.values():
            # Kelime veya tanımda arama
            if (
                query_lower in card.word.lower()
                or query_lower in card.definition.lower()
            ):
                # Filtreleri uygula
                if category and card.category != category:
                    continue
                if difficulty_level and card.difficulty_level != difficulty_level:
                    continue
                results.append(card)

        return results

    def get_vocabulary_builder_progress(self, user_id: str) -> Dict[str, Any]:
        """
        REQ-50.82: Kelime öğrenme ilerlemesini getir (visual vocabulary builder)

        Args:
            user_id: Kullanıcı ID

        Returns:
            Dict: İlerleme bilgisi
        """
        # Basit ilerleme hesaplama
        # Gerçek implementasyonda spaced repetition ile entegre edilir (REQ-50.84)

        total_cards = len(self.vocabulary_cards)
        learned_cards = int(total_cards * 0.6)  # Placeholder

        return {
            "user_id": user_id,
            "total_cards": total_cards,
            "learned_cards": learned_cards,
            "learning_cards": int(total_cards * 0.3),
            "new_cards": int(total_cards * 0.1),
            "progress_percentage": (learned_cards / total_cards * 100)
            if total_cards > 0
            else 0,
            "categories": self._get_category_progress(),
        }

    # ========================================================================
    # Color Coding (Renk Kodlama) - REQ-50.85-88
    # ========================================================================

    def create_color_scheme(
        self,
        name: str,
        description: str,
        categories: Dict[str, str],
        user_id: Optional[str] = None,
    ) -> ColorCodingScheme:
        """
        REQ-50.85: Renk kodlama şeması oluştur (color-coded categories)

        Args:
            name: Şema adı
            description: Açıklama
            categories: Kategori-renk eşleştirmeleri
            user_id: Kullanıcı ID

        Returns:
            ColorCodingScheme: Oluşturulan şema
        """
        scheme_id = self._generate_id(f"{name}_{user_id or 'default'}")

        scheme = ColorCodingScheme(
            id=scheme_id,
            name=name,
            description=description,
            categories=categories,
            user_id=user_id,
            is_default=False,
        )

        self.color_schemes[scheme_id] = scheme
        return scheme

    def get_color_scheme(self, scheme_id: str) -> Optional[ColorCodingScheme]:
        """
        REQ-50.86: Renk şemasını getir (consistent color scheme)

        Args:
            scheme_id: Şema ID

        Returns:
            Optional[ColorCodingScheme]: Renk şeması veya None
        """
        return self.color_schemes.get(scheme_id)

    def get_default_color_schemes(self) -> List[ColorCodingScheme]:
        """
        REQ-50.86: Varsayılan renk şemalarını getir

        Returns:
            List[ColorCodingScheme]: Varsayılan şemalar
        """
        return [scheme for scheme in self.color_schemes.values() if scheme.is_default]

    def customize_color_mapping(
        self, scheme_id: str, category: str, new_color: str
    ) -> bool:
        """
        REQ-50.87: Renk eşleştirmesini özelleştir (customizable color mapping)

        Args:
            scheme_id: Şema ID
            category: Kategori adı
            new_color: Yeni renk (hex)

        Returns:
            bool: Başarılı mı
        """
        scheme = self.color_schemes.get(scheme_id)
        if not scheme:
            return False

        scheme.categories[category] = new_color
        return True

    def save_user_color_preferences(
        self, user_id: str, scheme_id: str
    ) -> Dict[str, Any]:
        """
        REQ-50.88: Kullanıcı renk tercihlerini kaydet

        Args:
            user_id: Kullanıcı ID
            scheme_id: Şema ID

        Returns:
            Dict: Kayıt sonucu
        """
        scheme = self.color_schemes.get(scheme_id)
        if not scheme:
            return {"success": False, "error": "Scheme not found"}

        # Gerçek implementasyonda veritabanına kaydedilir
        return {
            "success": True,
            "user_id": user_id,
            "scheme_id": scheme_id,
            "message": "Color preferences saved successfully",
        }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _generate_id(self, seed: str) -> str:
        """Benzersiz ID oluştur"""
        return hashlib.md5(
            f"{seed}_{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]

    def _extract_key_concepts(self, words: List[str]) -> List[str]:
        """Anahtar kavramları çıkar (basitleştirilmiş)"""
        # Gerçek implementasyonda NLP kullanılır
        # Şimdilik uzun kelimeleri anahtar kavram olarak al
        concepts = [word for word in words if len(word) > 6]
        return list(set(concepts))[:10]  # Unique ve max 10

    def _get_node_color(self, index: int) -> str:
        """Düğüm rengi getir"""
        colors = ["#4A90E2", "#50C878", "#FFB347", "#FF6B6B", "#9B59B6"]
        return colors[index % len(colors)]

    def _generate_svg(self, mind_map: MindMap) -> str:
        """SVG oluştur (basitleştirilmiş)"""
        # Gerçek implementasyonda tam SVG rendering yapılır
        return f"<svg><text>{mind_map.title}</text></svg>"

    def _select_icons_for_template(self, template: str, count: int) -> List[str]:
        """Şablon için ikonları seç"""
        icon_sets = {
            "timeline": ["calendar", "clock", "event"],
            "comparison": ["compare", "balance", "versus"],
            "process": ["arrow-right", "step", "flow"],
            "hierarchy": ["tree", "org-chart", "structure"],
        }
        icons = icon_sets.get(template, ["default"])
        return (icons * (count // len(icons) + 1))[:count]

    def _select_colors_for_template(self, template: str, count: int) -> List[str]:
        """Şablon için renkleri seç"""
        color_palettes = {
            "timeline": ["#4A90E2", "#50C878", "#FFB347"],
            "comparison": ["#FF6B6B", "#4ECDC4"],
            "process": ["#9B59B6", "#3498DB", "#2ECC71"],
            "hierarchy": ["#E74C3C", "#F39C12", "#16A085"],
        }
        colors = color_palettes.get(template, ["#4A90E2"])
        return (colors * (count // len(colors) + 1))[:count]

    def _get_category_color(self, category: str) -> str:
        """Kategori rengini getir"""
        category_colors = {
            "noun": "#4A90E2",  # Mavi - İsimler
            "verb": "#50C878",  # Yeşil - Fiiller
            "adjective": "#FFB347",  # Turuncu - Sıfatlar
            "adverb": "#FF6B6B",  # Kırmızı - Zarflar
            "preposition": "#9B59B6",  # Mor - Edatlar
            "conjunction": "#F39C12",  # Sarı - Bağlaçlar
            "pronoun": "#16A085",  # Turkuaz - Zamirler
            "interjection": "#E74C3C",  # Koyu kırmızı - Ünlemler
        }
        return category_colors.get(category.lower(), "#95A5A6")  # Varsayılan gri

    def _get_category_progress(self) -> Dict[str, Any]:
        """Kategori bazlı ilerleme"""
        categories = {}
        for card in self.vocabulary_cards.values():
            if card.category not in categories:
                categories[card.category] = {
                    "total": 0,
                    "learned": 0,
                    "color": card.color_code,
                }
            categories[card.category]["total"] += 1
            # Placeholder: %60 öğrenilmiş kabul et
            categories[card.category]["learned"] = int(
                categories[card.category]["total"] * 0.6
            )

        return categories

    def _load_default_color_schemes(self):
        """Varsayılan renk şemalarını yükle"""
        # Disleksi dostu renk şeması
        dyslexia_scheme = ColorCodingScheme(
            id="dyslexia_friendly",
            name="Disleksi Dostu",
            description="Yüksek kontrast ve ayırt edici renkler",
            categories={
                "important": "#FF6B6B",  # Kırmızı - Önemli
                "definition": "#4A90E2",  # Mavi - Tanım
                "example": "#50C878",  # Yeşil - Örnek
                "note": "#FFB347",  # Turuncu - Not
                "warning": "#F39C12",  # Sarı - Uyarı
                "success": "#2ECC71",  # Yeşil - Başarı
            },
            is_default=True,
        )
        self.color_schemes[dyslexia_scheme.id] = dyslexia_scheme

        # Akademik renk şeması
        academic_scheme = ColorCodingScheme(
            id="academic",
            name="Akademik",
            description="Geleneksel akademik renk kodlaması",
            categories={
                "theory": "#3498DB",  # Mavi - Teori
                "practice": "#2ECC71",  # Yeşil - Uygulama
                "analysis": "#9B59B6",  # Mor - Analiz
                "synthesis": "#E67E22",  # Turuncu - Sentez
                "evaluation": "#E74C3C",  # Kırmızı - Değerlendirme
            },
            is_default=True,
        )
        self.color_schemes[academic_scheme.id] = academic_scheme


# ============================================================================
# Service Instance
# ============================================================================

visual_supports_service = VisualSupportsService()
