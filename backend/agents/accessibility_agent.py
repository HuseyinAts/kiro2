"""
Erişilebilirlik İçerik Geliştirici YZ Ajanı
Teknofest 2025 - Eğitim Eylemci Projesi

Bu ajan:
- Görseller için alt metin oluşturur
- Karmaşık cümleleri sadeleştirir
- Jargon ve kısaltmaları açıklar
- Ekran okuyucu uyumluluğu sağlar
- Yapısal erişilebilirlik kontrolü yapar
"""

import logging
import os
import re

# Core services
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.llm_service import llm_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentType(Enum):
    """İçerik tipleri"""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    PDF = "pdf"
    HTML = "html"
    DOCUMENT = "document"


class AccessibilityLevel(Enum):
    """Erişilebilirlik seviyeleri (WCAG)"""

    A = "A"  # Minimum
    AA = "AA"  # Önerilen
    AAA = "AAA"  # Gelişmiş


class IssueType(Enum):
    """Erişilebilirlik sorun tipleri"""

    MISSING_ALT_TEXT = "missing_alt_text"
    COMPLEX_LANGUAGE = "complex_language"
    POOR_CONTRAST = "poor_contrast"
    MISSING_HEADERS = "missing_headers"
    NO_CAPTIONS = "no_captions"
    INACCESSIBLE_PDF = "inaccessible_pdf"
    MISSING_LABELS = "missing_labels"
    NO_KEYBOARD_NAV = "no_keyboard_nav"


@dataclass
class AccessibilityIssue:
    """Erişilebilirlik sorunu"""

    issue_type: IssueType
    severity: str  # high, medium, low
    description: str
    location: str  # Sorunun konumu
    suggestion: str  # Çözüm önerisi
    wcag_criterion: Optional[str] = None  # İlgili WCAG kriteri


@dataclass
class AccessibilityReport:
    """Erişilebilirlik raporu"""

    report_id: str
    content_type: ContentType
    issues: List[AccessibilityIssue]
    score: float  # 0-100 erişilebilirlik skoru
    level: AccessibilityLevel
    recommendations: List[str]
    improved_content: Optional[str]  # İyileştirilmiş içerik
    metadata: Dict[str, Any]


@dataclass
class AltText:
    """Alternatif metin"""

    image_id: str
    original_context: str
    generated_alt: str
    confidence: float
    language: str
    metadata: Optional[Dict[str, Any]] = None


class AccessibilityAgent:
    """Erişilebilirlik İçerik Geliştirici Ajanı"""

    def __init__(self):
        self.reports = {}  # Raporlar
        self.alt_texts = {}  # Alt metin cache
        self.simplified_content = {}  # Sadeleştirilmiş içerikler
        self.terminology_db = {}  # Terim veritabanı
        self._load_terminology()

    def _load_terminology(self):
        """Terim veritabanını yükle"""
        # Örnek terimler (gerçek uygulamada daha kapsamlı olacak)
        self.terminology_db = {
            "LGS": "Liselere Giriş Sınavı - 8. sınıf öğrencilerinin girdiği merkezi sınav",
            "YKS": "Yükseköğretim Kurumları Sınavı - Üniversiteye giriş sınavı",
            "TYT": "Temel Yeterlilik Testi - YKS'nin ilk oturumu",
            "AYT": "Alan Yeterlilik Testi - YKS'nin ikinci oturumu",
            "DNA": "Deoksiribonükleik Asit - Kalıtsal bilgiyi taşıyan molekül",
            "ATP": "Adenozin Trifosfat - Hücrenin enerji molekülü",
            "pH": "Hidrojen iyonu konsantrasyonu - Asitlik/bazlık ölçüsü",
        }

    async def analyze_content(
        self, content: str, content_type: ContentType, context: Optional[str] = None
    ) -> AccessibilityReport:
        """
        İçeriği erişilebilirlik açısından analiz et

        Args:
            content: İçerik
            content_type: İçerik tipi
            context: Bağlam bilgisi

        Returns:
            Erişilebilirlik raporu
        """
        try:
            issues = []
            recommendations = []

            # İçerik tipine göre analiz
            if content_type == ContentType.TEXT:
                # Metin analizi
                text_issues = await self._analyze_text(content)
                issues.extend(text_issues)

            elif content_type == ContentType.HTML:
                # HTML analizi
                html_issues = self._analyze_html(content)
                issues.extend(html_issues)

            elif content_type == ContentType.IMAGE:
                # Görsel analizi
                image_issues = await self._analyze_image(content, context)
                issues.extend(image_issues)

            # Skor hesapla
            score = self._calculate_accessibility_score(issues)

            # Seviye belirle
            level = self._determine_level(score)

            # Öneriler oluştur
            for issue in issues:
                recommendations.append(issue.suggestion)

            # İyileştirilmiş içerik oluştur
            improved_content = None
            if content_type == ContentType.TEXT:
                improved_content = await self.simplify_text(content)

            # Rapor oluştur
            report_id = f"report_{datetime.now().timestamp()}"
            report = AccessibilityReport(
                report_id=report_id,
                content_type=content_type,
                issues=issues,
                score=score,
                level=level,
                recommendations=recommendations,
                improved_content=improved_content,
                metadata={
                    "analyzed_at": datetime.now().isoformat(),
                    "content_length": len(content),
                    "context": context,
                },
            )

            # Cache'e kaydet
            self.reports[report_id] = report

            logger.info(
                f"Accessibility analysis completed: {report_id} - Score: {score}"
            )
            return report

        except Exception as e:
            logger.error(f"Analyze content error: {str(e)}")
            raise

    async def _analyze_text(self, text: str) -> List[AccessibilityIssue]:
        """Metin erişilebilirlik analizi"""
        issues = []

        # Karmaşıklık analizi
        complexity_score = self._calculate_text_complexity(text)
        if complexity_score > 0.7:
            issues.append(
                AccessibilityIssue(
                    issue_type=IssueType.COMPLEX_LANGUAGE,
                    severity="medium",
                    description="Metin çok karmaşık",
                    location="Genel",
                    suggestion="Cümleleri kısaltın ve basit kelimeler kullanın",
                    wcag_criterion="3.1.5",
                )
            )

        # Jargon ve kısaltma kontrolü
        jargon_terms = self._find_jargon(text)
        if jargon_terms:
            issues.append(
                AccessibilityIssue(
                    issue_type=IssueType.COMPLEX_LANGUAGE,
                    severity="low",
                    description=f"Açıklanmamış terimler: {', '.join(jargon_terms[:5])}",
                    location="Metin içi",
                    suggestion="Teknik terimleri açıklayın",
                    wcag_criterion="3.1.3",
                )
            )

        # Uzun cümle kontrolü
        long_sentences = [s for s in text.split(".") if len(s.split()) > 30]
        if long_sentences:
            issues.append(
                AccessibilityIssue(
                    issue_type=IssueType.COMPLEX_LANGUAGE,
                    severity="low",
                    description=f"{len(long_sentences)} adet çok uzun cümle var",
                    location="Metin içi",
                    suggestion="Uzun cümleleri bölün",
                    wcag_criterion="3.1.5",
                )
            )

        return issues

    def _analyze_html(self, html: str) -> List[AccessibilityIssue]:
        """HTML erişilebilirlik analizi"""
        issues = []

        # Başlık hiyerarşisi kontrolü
        h1_count = html.count("<h1")
        if h1_count == 0:
            issues.append(
                AccessibilityIssue(
                    issue_type=IssueType.MISSING_HEADERS,
                    severity="high",
                    description="Ana başlık (H1) eksik",
                    location="HTML yapısı",
                    suggestion="Sayfaya bir H1 başlık ekleyin",
                    wcag_criterion="2.4.6",
                )
            )
        elif h1_count > 1:
            issues.append(
                AccessibilityIssue(
                    issue_type=IssueType.MISSING_HEADERS,
                    severity="medium",
                    description="Birden fazla H1 başlık var",
                    location="HTML yapısı",
                    suggestion="Tek bir H1 kullanın",
                    wcag_criterion="2.4.6",
                )
            )

        # Alt metin kontrolü
        img_tags = re.findall(r"<img[^>]*>", html)
        for img in img_tags:
            if "alt=" not in img:
                issues.append(
                    AccessibilityIssue(
                        issue_type=IssueType.MISSING_ALT_TEXT,
                        severity="high",
                        description="Görsel alt metni eksik",
                        location=img[:50],
                        suggestion="Alt özelliği ekleyin",
                        wcag_criterion="1.1.1",
                    )
                )

        # Form etiket kontrolü
        input_tags = re.findall(r"<input[^>]*>", html)
        for input_tag in input_tags:
            if "id=" in input_tag:
                input_id = re.search(r'id="([^"]*)"', input_tag)
                if input_id:
                    label_for = f'for="{input_id.group(1)}"'
                    if label_for not in html:
                        issues.append(
                            AccessibilityIssue(
                                issue_type=IssueType.MISSING_LABELS,
                                severity="high",
                                description="Form elemanı etiketi eksik",
                                location=input_tag[:50],
                                suggestion="Label elementi ekleyin",
                                wcag_criterion="3.3.2",
                            )
                        )

        # Dil etiketi kontrolü
        if "lang=" not in html[:200]:
            issues.append(
                AccessibilityIssue(
                    issue_type=IssueType.MISSING_LABELS,
                    severity="medium",
                    description="HTML dil özelliği eksik",
                    location="<html> etiketi",
                    suggestion='lang="tr" ekleyin',
                    wcag_criterion="3.1.1",
                )
            )

        return issues

    async def _analyze_image(
        self, image_data: str, context: Optional[str] = None
    ) -> List[AccessibilityIssue]:
        """Görsel erişilebilirlik analizi"""
        issues = []

        # Görsel için alt metin önerisi gerekli
        issues.append(
            AccessibilityIssue(
                issue_type=IssueType.MISSING_ALT_TEXT,
                severity="high",
                description="Görsel için alternatif metin gerekli",
                location="Görsel",
                suggestion="Görseli tanımlayan alt metin ekleyin",
                wcag_criterion="1.1.1",
            )
        )

        return issues

    def _calculate_text_complexity(self, text: str) -> float:
        """Metin karmaşıklığı hesapla (0-1)"""
        # Basit Flesch Reading Ease benzeri hesaplama
        sentences = text.split(".")
        words = text.split()

        if not sentences or not words:
            return 0

        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Normalize et (0-1 arası)
        complexity = min(1.0, (avg_sentence_length / 30 + avg_word_length / 10) / 2)
        return complexity

    def _find_jargon(self, text: str) -> List[str]:
        """Metindeki jargon ve kısaltmaları bul"""
        jargon_terms = []

        # Bilinen terimleri kontrol et
        for term in self.terminology_db.keys():
            if term in text and term not in jargon_terms:
                # Terim metinde var ama açıklanmamış mı?
                explanation = self.terminology_db[term]
                if explanation not in text:
                    jargon_terms.append(term)

        # Büyük harfli kısaltmaları bul (2-5 karakter)
        abbreviations = re.findall(r"\b[A-Z]{2,5}\b", text)
        for abbr in abbreviations:
            if abbr not in self.terminology_db and abbr not in jargon_terms:
                jargon_terms.append(abbr)

        return jargon_terms

    def _calculate_accessibility_score(self, issues: List[AccessibilityIssue]) -> float:
        """Erişilebilirlik skoru hesapla (0-100)"""
        if not issues:
            return 100

        # Sorun ağırlıkları
        severity_weights = {"high": 10, "medium": 5, "low": 2}

        total_penalty = sum(severity_weights.get(issue.severity, 0) for issue in issues)
        score = max(0, 100 - total_penalty)

        return score

    def _determine_level(self, score: float) -> AccessibilityLevel:
        """Erişilebilirlik seviyesi belirle"""
        if score >= 90:
            return AccessibilityLevel.AAA
        elif score >= 70:
            return AccessibilityLevel.AA
        else:
            return AccessibilityLevel.A

    async def generate_alt_text(
        self, image_data: str, context: Optional[str] = None, language: str = "tr"
    ) -> AltText:
        """
        Görsel için alternatif metin oluştur

        Args:
            image_data: Görsel verisi (base64 veya URL)
            context: Bağlam bilgisi
            language: Dil

        Returns:
            Alt metin
        """
        try:
            # LLM ile alt metin oluştur
            prompt = f"""
            Görsel için erişilebilir alternatif metin oluştur.
            
            Bağlam: {context if context else 'Eğitim materyali'}
            Dil: {language}
            
            Alt metin:
            - Kısa ve öz olmalı (125 karakter altında)
            - Görselin amacını ve içeriğini açıklamalı
            - "Resim" veya "Görsel" kelimelerini içermemeli
            - Bağlama uygun olmalı
            
            Örnek: "Mitoz bölünmenin 4 aşamasını gösteren diyagram"
            """

            result = await llm_service.generate(prompt=prompt, temperature=0.3)

            alt_text_str = "Eğitim görseli"
            confidence = 0.5

            if result["success"]:
                alt_text_str = result["text"].strip()[:125]
                confidence = 0.8

            # Alt metin objesi oluştur
            alt_text = AltText(
                image_id=f"img_{datetime.now().timestamp()}",
                original_context=context or "",
                generated_alt=alt_text_str,
                confidence=confidence,
                language=language,
                metadata={"source": "generated"},
            )

            # Cache'e kaydet
            self.alt_texts[alt_text.image_id] = alt_text

            logger.info(f"Alt text generated: {alt_text.image_id}")
            return alt_text

        except Exception as e:
            logger.error(f"Generate alt text error: {str(e)}")
            # Fallback alt text
            return AltText(
                image_id=f"img_{datetime.now().timestamp()}",
                original_context=context or "",
                generated_alt="Görsel içerik",
                confidence=0.1,
                language=language,
            )

    async def simplify_text(self, text: str, target_level: str = "intermediate") -> str:
        """
        Metni sadeleştir

        Args:
            text: Orijinal metin
            target_level: Hedef seviye (beginner, intermediate, advanced)

        Returns:
            Sadeleştirilmiş metin
        """
        try:
            result = await llm_service.generate_for_education(
                task_type="simplification",
                content=text,
                parameters={"target_level": target_level},
            )

            if result["success"]:
                simplified = result["content"]

                # Terimleri açıkla
                simplified = self._add_term_explanations(simplified)

                # Cache'e kaydet
                cache_key = f"simplified_{hash(text)}"
                self.simplified_content[cache_key] = simplified

                return simplified
            else:
                return text

        except Exception as e:
            logger.error(f"Simplify text error: {str(e)}")
            return text

    def _add_term_explanations(self, text: str) -> str:
        """Metindeki terimlere açıklama ekle"""
        result = text

        for term, explanation in self.terminology_db.items():
            if term in result and explanation not in result:
                # İlk geçtiği yere açıklama ekle
                first_occurrence = result.find(term)
                if first_occurrence != -1:
                    insert_pos = first_occurrence + len(term)
                    result = (
                        result[:insert_pos] + f" ({explanation})" + result[insert_pos:]
                    )

        return result

    async def improve_structure(
        self, content: str, content_type: ContentType
    ) -> Dict[str, Any]:
        """
        İçerik yapısını iyileştir

        Args:
            content: İçerik
            content_type: İçerik tipi

        Returns:
            İyileştirme önerileri
        """
        suggestions = {
            "headings": [],
            "lists": [],
            "tables": [],
            "navigation": [],
            "semantic": [],
        }

        try:
            if content_type == ContentType.HTML:
                # Başlık önerileri
                if "<h1" not in content:
                    suggestions["headings"].append(
                        {
                            "action": "add",
                            "element": "h1",
                            "suggestion": "Ana başlık ekleyin",
                        }
                    )

                # Liste önerileri
                bullet_points = re.findall(r"^\s*[-*•]\s+", content, re.MULTILINE)
                if bullet_points and "<ul" not in content:
                    suggestions["lists"].append(
                        {
                            "action": "convert",
                            "element": "ul",
                            "suggestion": "Madde işaretlerini HTML listesine dönüştürün",
                        }
                    )

                # Tablo önerileri
                if "<table" in content:
                    if "<th" not in content:
                        suggestions["tables"].append(
                            {
                                "action": "add",
                                "element": "th",
                                "suggestion": "Tablo başlıkları ekleyin",
                            }
                        )
                    if "summary=" not in content:
                        suggestions["tables"].append(
                            {
                                "action": "add",
                                "attribute": "summary",
                                "suggestion": "Tablo özeti ekleyin",
                            }
                        )

                # Navigasyon önerileri
                if len(re.findall(r"<h[1-6]", content)) > 5:
                    suggestions["navigation"].append(
                        {
                            "action": "add",
                            "element": "nav",
                            "suggestion": "İçindekiler/navigasyon menüsü ekleyin",
                        }
                    )

                # Semantik öneriler
                suggestions["semantic"].append(
                    {
                        "action": "use",
                        "elements": ["article", "section", "aside", "nav"],
                        "suggestion": "Semantik HTML5 elementleri kullanın",
                    }
                )

            elif content_type == ContentType.TEXT:
                # Metin için yapısal öneriler
                paragraphs = content.split("\n\n")
                if len(paragraphs) > 10:
                    suggestions["headings"].append(
                        {
                            "action": "add",
                            "element": "sections",
                            "suggestion": "Metni bölümlere ayırın ve başlıklar ekleyin",
                        }
                    )

            return suggestions

        except Exception as e:
            logger.error(f"Improve structure error: {str(e)}")
            return suggestions

    async def check_contrast(
        self, foreground_color: str, background_color: str
    ) -> Dict[str, Any]:
        """
        Renk kontrastını kontrol et

        Args:
            foreground_color: Ön plan rengi (hex)
            background_color: Arka plan rengi (hex)

        Returns:
            Kontrast raporu
        """
        try:
            # Hex'i RGB'ye çevir
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip("#")
                return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

            # Relative luminance hesapla
            def relative_luminance(rgb):
                r, g, b = [x / 255 for x in rgb]
                r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
                g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
                b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
                return 0.2126 * r + 0.7152 * g + 0.0722 * b

            fg_rgb = hex_to_rgb(foreground_color)
            bg_rgb = hex_to_rgb(background_color)

            fg_lum = relative_luminance(fg_rgb)
            bg_lum = relative_luminance(bg_rgb)

            # Kontrast oranı hesapla
            lighter = max(fg_lum, bg_lum)
            darker = min(fg_lum, bg_lum)
            contrast_ratio = (lighter + 0.05) / (darker + 0.05)

            # WCAG standartlarına göre değerlendir
            passes_aa_normal = contrast_ratio >= 4.5
            passes_aa_large = contrast_ratio >= 3
            passes_aaa_normal = contrast_ratio >= 7
            passes_aaa_large = contrast_ratio >= 4.5

            return {
                "contrast_ratio": round(contrast_ratio, 2),
                "passes_aa_normal": passes_aa_normal,
                "passes_aa_large": passes_aa_large,
                "passes_aaa_normal": passes_aaa_normal,
                "passes_aaa_large": passes_aaa_large,
                "recommendation": self._get_contrast_recommendation(contrast_ratio),
            }

        except Exception as e:
            logger.error(f"Check contrast error: {str(e)}")
            return {"error": str(e), "recommendation": "Kontrast hesaplanamadı"}

    def _get_contrast_recommendation(self, ratio: float) -> str:
        """Kontrast oranına göre öneri"""
        if ratio >= 7:
            return "Mükemmel kontrast (AAA)"
        elif ratio >= 4.5:
            return "İyi kontrast (AA)"
        elif ratio >= 3:
            return "Sadece büyük metin için yeterli"
        else:
            return "Yetersiz kontrast, renkleri değiştirin"

    async def create_accessible_version(
        self,
        content: str,
        content_type: ContentType,
        target_level: AccessibilityLevel = AccessibilityLevel.AA,
    ) -> str:
        """
        İçeriğin erişilebilir versiyonunu oluştur

        Args:
            content: Orijinal içerik
            content_type: İçerik tipi
            target_level: Hedef erişilebilirlik seviyesi

        Returns:
            Erişilebilir içerik
        """
        try:
            # Önce analiz yap
            report = await self.analyze_content(content, content_type)

            # İçerik tipine göre iyileştirme
            if content_type == ContentType.TEXT:
                # Metni sadeleştir
                accessible_content = await self.simplify_text(content)

                # Terimleri açıkla
                accessible_content = self._add_term_explanations(accessible_content)

            elif content_type == ContentType.HTML:
                accessible_content = content

                # Alt metin ekle
                img_pattern = r"<img([^>]*)>"

                def add_alt(match):
                    img_tag = match.group(0)
                    if "alt=" not in img_tag:
                        return img_tag[:-1] + ' alt="Eğitim görseli">'
                    return img_tag

                accessible_content = re.sub(img_pattern, add_alt, accessible_content)

                # Dil etiketi ekle
                if (
                    "<html" in accessible_content
                    and "lang=" not in accessible_content[:200]
                ):
                    accessible_content = accessible_content.replace(
                        "<html", '<html lang="tr"'
                    )

                # Başlık hiyerarşisi düzelt
                if "<h1" not in accessible_content and "<h2" in accessible_content:
                    # İlk h2'yi h1 yap
                    accessible_content = accessible_content.replace("<h2", "<h1", 1)
                    accessible_content = accessible_content.replace("</h2>", "</h1>", 1)

            else:
                accessible_content = content

            return accessible_content

        except Exception as e:
            logger.error(f"Create accessible version error: {str(e)}")
            return content

    def get_report(self, report_id: str) -> Optional[AccessibilityReport]:
        """Rapor getir"""
        return self.reports.get(report_id)

    def get_wcag_guidelines(self, level: AccessibilityLevel) -> List[str]:
        """WCAG yönergelerini getir"""
        guidelines = {
            AccessibilityLevel.A: [
                "1.1.1 - Metin olmayan içerik için alternatif metin",
                "1.3.1 - Bilgi ve ilişkiler",
                "2.1.1 - Klavye erişimi",
                "2.4.2 - Sayfa başlığı",
                "3.1.1 - Sayfanın dili",
                "4.1.1 - Ayrıştırma",
            ],
            AccessibilityLevel.AA: [
                "1.4.3 - Minimum kontrast",
                "1.4.5 - Metin görselleri",
                "2.4.6 - Başlıklar ve etiketler",
                "2.4.7 - Odak görünür",
                "3.1.2 - Parçaların dili",
                "3.3.2 - Etiketler veya talimatlar",
            ],
            AccessibilityLevel.AAA: [
                "1.4.6 - Gelişmiş kontrast",
                "1.4.8 - Görsel sunum",
                "2.4.10 - Bölüm başlıkları",
                "3.1.5 - Okuma seviyesi",
                "3.3.5 - Yardım",
            ],
        }

        result = []
        if level == AccessibilityLevel.A:
            result.extend(guidelines[AccessibilityLevel.A])
        elif level == AccessibilityLevel.AA:
            result.extend(guidelines[AccessibilityLevel.A])
            result.extend(guidelines[AccessibilityLevel.AA])
        elif level == AccessibilityLevel.AAA:
            result.extend(guidelines[AccessibilityLevel.A])
            result.extend(guidelines[AccessibilityLevel.AA])
            result.extend(guidelines[AccessibilityLevel.AAA])

        return result


# Singleton instance
accessibility_agent = AccessibilityAgent()
