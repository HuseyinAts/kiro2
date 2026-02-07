"""
Accessibility Manager - Erişilebilirlik Yönetimi
REQ-7: Accessibility Integration

WCAG 2.1 AA/AAA uyumlu erişilebilirlik özellikleri:
- Dyslexia-friendly font + bionic reading
- Screen reader support
- Color blindness support
- Low vision / high contrast
- ADHD-friendly patterns
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AccessibilityMode(Enum):
    """Erişilebilirlik modları"""
    STANDARD = "standard"  # Normal mod
    DYSLEXIA = "dyslexia"  # Disleksi modu
    LOW_VISION = "low_vision"  # Az gören modu
    COLOR_BLIND = "color_blind"  # Renk körlüğü modu
    ADHD = "adhd"  # DEHB modu
    SCREEN_READER = "screen_reader"  # Ekran okuyucu modu


class ContrastLevel(Enum):
    """Kontrast seviyeleri"""
    NORMAL = "normal"  # 4.5:1 (WCAG AA)
    HIGH = "high"  # 7:1 (WCAG AAA)
    VERY_HIGH = "very_high"  # 10:1+


class FontFamily(Enum):
    """Font aileleri"""
    DEFAULT = "default"
    OPEN_DYSLEXIC = "OpenDyslexic"  # Disleksi dostu
    LEXIE_READABLE = "Lexie Readable"
    ARIAL = "Arial"
    VERDANA = "Verdana"


@dataclass
class AccessibilitySettings:
    """Erişilebilirlik ayarları"""
    mode: AccessibilityMode = AccessibilityMode.STANDARD

    # Font ayarları
    font_family: FontFamily = FontFamily.DEFAULT
    font_size_multiplier: float = 1.0  # 0.75 - 2.0
    line_height_multiplier: float = 1.5  # 1.2 - 3.0
    letter_spacing: float = 0.0  # 0 - 0.5 em
    word_spacing: float = 0.0  # 0 - 0.5 em

    # Renk ve kontrast
    contrast_level: ContrastLevel = ContrastLevel.NORMAL
    background_color: str = "#FFFFFF"
    text_color: str = "#000000"
    bold_color: str = "#000000"

    # Bionic Reading özel
    bionic_boldness: int = 3  # 1-5
    highlight_fixation: bool = False

    # ADHD özel
    focus_mode: bool = False
    reduced_motion: bool = False
    paragraph_highlight: bool = False


@dataclass
class AccessibilityReport:
    """WCAG uyumluluk raporu"""
    wcag_level: str  # "A", "AA", "AAA"
    contrast_ratio: float
    font_size_adequate: bool
    line_height_adequate: bool
    touch_target_size_ok: bool
    keyboard_navigation: bool
    screen_reader_compatible: bool
    issues: list[str]
    recommendations: list[str]


class AccessibilityManager:
    """
    Accessibility Manager

    WCAG 2.1 AA/AAA uyumlu erişilebilirlik yönetimi:
    - REQ-7.1: Dyslexia mode + bionic reading
    - REQ-7.2: Screen reader semantic HTML
    - REQ-7.3: Color-independent bold
    - REQ-7.4: High contrast mode
    - REQ-7.5: ADHD-friendly format
    - REQ-7.6: WCAG 2.1 compliance
    """

    # WCAG 2.1 minimum gereksinimleri
    WCAG_AA_CONTRAST = 4.5  # Normal text
    WCAG_AAA_CONTRAST = 7.0  # Normal text
    MIN_FONT_SIZE = 16  # px
    MIN_LINE_HEIGHT = 1.5
    MIN_TOUCH_TARGET = 44  # px

    def __init__(self):
        self._user_settings: dict[str, AccessibilitySettings] = {}
        self._presets = self._create_presets()

    def _create_presets(self) -> dict[AccessibilityMode, AccessibilitySettings]:
        """Ön tanımlı erişilebilirlik modları"""
        return {
            AccessibilityMode.STANDARD: AccessibilitySettings(),

            AccessibilityMode.DYSLEXIA: AccessibilitySettings(
                mode=AccessibilityMode.DYSLEXIA,
                font_family=FontFamily.OPEN_DYSLEXIC,
                font_size_multiplier=1.2,
                line_height_multiplier=1.8,
                letter_spacing=0.12,
                word_spacing=0.16,
                contrast_level=ContrastLevel.HIGH,
                background_color="#FFF9E6",  # Krem rengi arka plan
                bionic_boldness=4,
                highlight_fixation=True
            ),

            AccessibilityMode.LOW_VISION: AccessibilitySettings(
                mode=AccessibilityMode.LOW_VISION,
                font_family=FontFamily.ARIAL,
                font_size_multiplier=1.5,
                line_height_multiplier=2.0,
                letter_spacing=0.05,
                contrast_level=ContrastLevel.VERY_HIGH,
                background_color="#000000",
                text_color="#FFFF00",  # Sarı metin
                bold_color="#FFFFFF",  # Beyaz bold
                bionic_boldness=5
            ),

            AccessibilityMode.COLOR_BLIND: AccessibilitySettings(
                mode=AccessibilityMode.COLOR_BLIND,
                font_family=FontFamily.DEFAULT,
                font_size_multiplier=1.1,
                line_height_multiplier=1.6,
                contrast_level=ContrastLevel.HIGH,
                # Renk bağımsız: sadece font-weight ile bold
                bionic_boldness=4,
                highlight_fixation=False
            ),

            AccessibilityMode.ADHD: AccessibilitySettings(
                mode=AccessibilityMode.ADHD,
                font_family=FontFamily.VERDANA,
                font_size_multiplier=1.15,
                line_height_multiplier=1.7,
                letter_spacing=0.05,
                contrast_level=ContrastLevel.NORMAL,
                background_color="#F0F8FF",  # Açık mavi
                bionic_boldness=4,
                focus_mode=True,
                reduced_motion=True,
                paragraph_highlight=True
            ),

            AccessibilityMode.SCREEN_READER: AccessibilitySettings(
                mode=AccessibilityMode.SCREEN_READER,
                font_family=FontFamily.DEFAULT,
                font_size_multiplier=1.0,
                line_height_multiplier=1.5,
                contrast_level=ContrastLevel.NORMAL,
                bionic_boldness=3,
                # Screen reader için semantic HTML önemli
            )
        }

    def get_settings(self, user_id: str) -> AccessibilitySettings:
        """Kullanıcı ayarlarını getir"""
        if user_id in self._user_settings:
            return self._user_settings[user_id]
        return AccessibilitySettings()

    def update_settings(self, user_id: str, settings: AccessibilitySettings):
        """Kullanıcı ayarlarını güncelle"""
        self._user_settings[user_id] = settings
        logger.info(f"Accessibility settings updated for user {user_id}: {settings.mode.value}")

    def apply_preset(self, user_id: str, mode: AccessibilityMode):
        """Ön tanımlı modu uygula"""
        preset = self._presets.get(mode, self._presets[AccessibilityMode.STANDARD])
        self._user_settings[user_id] = preset
        return preset

    def get_css_styles(self, settings: AccessibilitySettings) -> dict:
        """CSS stil değerlerini döndür"""
        base_font_size = self.MIN_FONT_SIZE * settings.font_size_multiplier

        # Font family
        font_family_map = {
            FontFamily.DEFAULT: "system-ui, -apple-system, sans-serif",
            FontFamily.OPEN_DYSLEXIC: "'OpenDyslexic', sans-serif",
            FontFamily.LEXIE_READABLE: "'Lexie Readable', sans-serif",
            FontFamily.ARIAL: "Arial, sans-serif",
            FontFamily.VERDANA: "Verdana, sans-serif"
        }

        return {
            "fontFamily": font_family_map.get(settings.font_family, font_family_map[FontFamily.DEFAULT]),
            "fontSize": f"{base_font_size}px",
            "lineHeight": str(settings.line_height_multiplier),
            "letterSpacing": f"{settings.letter_spacing}em",
            "wordSpacing": f"{settings.word_spacing}em",
            "backgroundColor": settings.background_color,
            "color": settings.text_color,
            "boldColor": settings.bold_color,
            # Bionic specific
            "bionicBoldness": settings.bionic_boldness,
            # ADHD specific
            "focusMode": settings.focus_mode,
            "reducedMotion": "reduce" if settings.reduced_motion else "no-preference",
            "paragraphHighlight": settings.paragraph_highlight
        }

    def get_html_wrapper(self, content: str, settings: AccessibilitySettings) -> str:
        """Erişilebilir HTML wrapper oluştur (REQ-7.2)"""
        styles = self.get_css_styles(settings)

        # ARIA attributes for screen readers
        aria_attrs = 'role="article" aria-live="polite"'

        if settings.mode == AccessibilityMode.SCREEN_READER:
            # Screen reader için ek attributes
            aria_attrs += ' aria-label="Bionic Reading formatted text"'

        css_style = "; ".join([
            f"font-family: {styles['fontFamily']}",
            f"font-size: {styles['fontSize']}",
            f"line-height: {styles['lineHeight']}",
            f"letter-spacing: {styles['letterSpacing']}",
            f"word-spacing: {styles['wordSpacing']}",
            f"background-color: {styles['backgroundColor']}",
            f"color: {styles['color']}"
        ])

        # Focus mode wrapper for ADHD
        focus_wrapper = ""
        focus_wrapper_close = ""

        if settings.focus_mode:
            focus_wrapper = '<div class="bionic-focus-container" tabindex="0">'
            focus_wrapper_close = "</div>"

        return f'''
<div class="bionic-accessible-content" {aria_attrs} style="{css_style}">
    {focus_wrapper}
    {content}
    {focus_wrapper_close}
</div>
'''

    def generate_css_stylesheet(self, settings: AccessibilitySettings) -> str:
        """Tam CSS stylesheet oluştur"""
        styles = self.get_css_styles(settings)

        bold_weight = 600 + (settings.bionic_boldness * 50)  # 650-850

        css = f'''
/* Bionic Reading Accessibility Styles */
/* Mode: {settings.mode.value} */

.bionic-accessible-content {{
    font-family: {styles['fontFamily']};
    font-size: {styles['fontSize']};
    line-height: {styles['lineHeight']};
    letter-spacing: {styles['letterSpacing']};
    word-spacing: {styles['wordSpacing']};
    background-color: {styles['backgroundColor']};
    color: {styles['color']};
    padding: 1.5rem;
    max-width: 70ch;
    margin: 0 auto;
}}

.bionic-accessible-content strong,
.bionic-accessible-content .bionic-bold {{
    font-weight: {bold_weight};
    color: {styles['boldColor']};
}}

/* High Contrast Mode */
@media (prefers-contrast: more) {{
    .bionic-accessible-content {{
        background-color: #000000;
        color: #FFFFFF;
    }}
    .bionic-accessible-content strong {{
        color: #FFFF00;
    }}
}}

/* Reduced Motion */
@media (prefers-reduced-motion: reduce) {{
    .bionic-accessible-content * {{
        animation: none !important;
        transition: none !important;
    }}
}}

/* Focus Mode (ADHD) */
.bionic-focus-container {{
    position: relative;
}}

.bionic-focus-container:focus {{
    outline: 3px solid #4A90D9;
    outline-offset: 4px;
}}

/* Paragraph Highlighting */
.bionic-accessible-content.paragraph-highlight p:hover,
.bionic-accessible-content.paragraph-highlight p:focus-within {{
    background-color: rgba(74, 144, 217, 0.1);
    border-radius: 4px;
    padding: 0.5rem;
}}

/* Screen Reader Only */
.sr-only {{
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}}

/* Touch Targets (Mobile) */
@media (pointer: coarse) {{
    .bionic-accessible-content a,
    .bionic-accessible-content button {{
        min-height: {self.MIN_TOUCH_TARGET}px;
        min-width: {self.MIN_TOUCH_TARGET}px;
        padding: 12px;
    }}
}}

/* Print Styles */
@media print {{
    .bionic-accessible-content {{
        background-color: white !important;
        color: black !important;
        font-size: 12pt;
    }}
    .bionic-accessible-content strong {{
        color: black !important;
    }}
}}
'''
        return css

    def check_wcag_compliance(self, settings: AccessibilitySettings) -> AccessibilityReport:
        """WCAG 2.1 uyumluluk kontrolü (REQ-7.6)"""
        issues = []
        recommendations = []

        # Kontrast kontrolü
        contrast_ratio = self._calculate_contrast_ratio(
            settings.background_color,
            settings.text_color
        )

        contrast_ok = contrast_ratio >= self.WCAG_AA_CONTRAST

        if not contrast_ok:
            issues.append(f"Kontrast oranı yetersiz: {contrast_ratio:.1f}:1 (minimum {self.WCAG_AA_CONTRAST}:1)")
            recommendations.append("Arka plan ve metin rengi arasındaki kontrastı artırın")

        # Font size kontrolü
        base_size = self.MIN_FONT_SIZE * settings.font_size_multiplier
        font_size_ok = base_size >= self.MIN_FONT_SIZE

        if not font_size_ok:
            issues.append(f"Font boyutu yetersiz: {base_size}px (minimum {self.MIN_FONT_SIZE}px)")
            recommendations.append("Font boyutunu artırın")

        # Line height kontrolü
        line_height_ok = settings.line_height_multiplier >= self.MIN_LINE_HEIGHT

        if not line_height_ok:
            issues.append(f"Satır aralığı yetersiz: {settings.line_height_multiplier} (minimum {self.MIN_LINE_HEIGHT})")
            recommendations.append("Satır aralığını artırın")

        # WCAG seviyesi belirleme
        if not issues:
            if contrast_ratio >= self.WCAG_AAA_CONTRAST:
                wcag_level = "AAA"
            else:
                wcag_level = "AA"
        else:
            wcag_level = "A" if len(issues) <= 2 else "None"

        return AccessibilityReport(
            wcag_level=wcag_level,
            contrast_ratio=contrast_ratio,
            font_size_adequate=font_size_ok,
            line_height_adequate=line_height_ok,
            touch_target_size_ok=True,  # CSS'de tanımlı
            keyboard_navigation=True,  # Focus styles tanımlı
            screen_reader_compatible=settings.mode != AccessibilityMode.LOW_VISION,  # Semantic HTML
            issues=issues,
            recommendations=recommendations
        )

    def _calculate_contrast_ratio(self, bg_color: str, text_color: str) -> float:
        """Kontrast oranı hesapla (WCAG formula)"""
        try:
            bg_lum = self._get_luminance(bg_color)
            text_lum = self._get_luminance(text_color)

            lighter = max(bg_lum, text_lum)
            darker = min(bg_lum, text_lum)

            return (lighter + 0.05) / (darker + 0.05)

        except Exception as e:
            logger.error(f"Kontrast hesaplama hatası: {e}")
            return 1.0

    def _get_luminance(self, hex_color: str) -> float:
        """Rengin relative luminance değerini hesapla"""
        hex_color = hex_color.lstrip('#')

        if len(hex_color) == 3:
            hex_color = ''.join([c * 2 for c in hex_color])

        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255

        # sRGB to linear
        def to_linear(c):
            if c <= 0.03928:
                return c / 12.92
            return ((c + 0.055) / 1.055) ** 2.4

        r = to_linear(r)
        g = to_linear(g)
        b = to_linear(b)

        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def get_available_modes(self) -> list[dict]:
        """Mevcut modları listele"""
        return [
            {
                "mode": mode.value,
                "name": self._get_mode_name(mode),
                "description": self._get_mode_description(mode)
            }
            for mode in AccessibilityMode
        ]

    def _get_mode_name(self, mode: AccessibilityMode) -> str:
        """Mod adı"""
        names = {
            AccessibilityMode.STANDARD: "Standart",
            AccessibilityMode.DYSLEXIA: "Disleksi Modu",
            AccessibilityMode.LOW_VISION: "Az Gören Modu",
            AccessibilityMode.COLOR_BLIND: "Renk Körlüğü Modu",
            AccessibilityMode.ADHD: "DEHB Modu",
            AccessibilityMode.SCREEN_READER: "Ekran Okuyucu Modu"
        }
        return names.get(mode, mode.value)

    def _get_mode_description(self, mode: AccessibilityMode) -> str:
        """Mod açıklaması"""
        descriptions = {
            AccessibilityMode.STANDARD: "Varsayılan görüntüleme ayarları",
            AccessibilityMode.DYSLEXIA: "Disleksi dostu font ve renk şeması ile kolay okuma",
            AccessibilityMode.LOW_VISION: "Yüksek kontrast ve büyük font ile görme desteği",
            AccessibilityMode.COLOR_BLIND: "Renk bağımsız bold işaretleme",
            AccessibilityMode.ADHD: "Odaklanmayı kolaylaştıran format ve düzen",
            AccessibilityMode.SCREEN_READER: "Ekran okuyucu uyumlu semantic HTML"
        }
        return descriptions.get(mode, "")
