"""
Bionic Formatter - Çoklu Format Desteği
REQ-6: Multi-Format Support

Desteklenen formatlar:
- HTML: <strong> tag
- Markdown: **bold** syntax
- Plain Text: UPPERCASE fallback
- CSS: font-weight: bold
- React: JSX formatı
"""

import html
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from .fixation import FixationPoint, FixationPointDetector

logger = logging.getLogger(__name__)


class OutputFormat(Enum):
    """Çıktı format tipleri"""
    HTML = "html"
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    CSS_SPAN = "css_span"
    REACT_JSX = "react_jsx"
    EPUB = "epub"
    LATEX = "latex"


@dataclass
class FormattedWord:
    """Formatlanmış kelime"""
    original: str
    formatted: str
    format_type: OutputFormat


@dataclass
class FormattedText:
    """Formatlanmış metin sonucu"""
    original_text: str
    formatted_text: str
    output_format: OutputFormat
    word_count: int
    bold_ratio: float
    processing_details: dict


class BionicFormatter:
    """
    Bionic Reading Formatter

    Birden fazla format desteği ile bionic text üretir:
    - HTML web uygulamaları için
    - Markdown dokümanlar için
    - CSS span özel stil için
    - React JSX React uygulamaları için
    """

    def __init__(
        self,
        default_format: OutputFormat = OutputFormat.HTML,
        boldness_level: int = 3,  # 1-5 arası
        custom_css_class: str = "bionic-bold"
    ):
        """
        Args:
            default_format: Varsayılan çıktı formatı
            boldness_level: Bold yoğunluğu (1-5)
            custom_css_class: Özel CSS sınıf adı
        """
        self.default_format = default_format
        self.boldness_level = max(1, min(5, boldness_level))
        self.custom_css_class = custom_css_class

        self.fixation_detector = FixationPointDetector()

        # Format handlers
        self._format_handlers: dict[OutputFormat, Callable[[FixationPoint], str]] = {
            OutputFormat.HTML: self._format_html,
            OutputFormat.MARKDOWN: self._format_markdown,
            OutputFormat.PLAIN_TEXT: self._format_plain_text,
            OutputFormat.CSS_SPAN: self._format_css_span,
            OutputFormat.REACT_JSX: self._format_react_jsx,
            OutputFormat.EPUB: self._format_epub,
            OutputFormat.LATEX: self._format_latex,
        }

    def format_word(
        self,
        word: str,
        output_format: OutputFormat | None = None
    ) -> FormattedWord:
        """
        Tek kelimeyi formatla

        Args:
            word: Formatlanacak kelime
            output_format: Çıktı formatı (None ise default)

        Returns:
            FormattedWord: Formatlanmış kelime
        """
        if not word:
            return FormattedWord(
                original=word,
                formatted=word,
                format_type=output_format or self.default_format
            )

        fmt = output_format or self.default_format

        # Noktalama işaretlerini ayır
        clean_word, prefix, suffix = self._extract_punctuation(word)

        if len(clean_word) < 2:
            # Çok kısa kelimeler için bionic uygulanmaz
            return FormattedWord(
                original=word,
                formatted=word,
                format_type=fmt
            )

        # Fixation point hesapla
        fixation = self.fixation_detector.detect(clean_word)

        # Boldness level'a göre ayarla
        adjusted_fixation = self._adjust_for_boldness(fixation)

        # Formatla
        handler = self._format_handlers.get(fmt, self._format_markdown)
        formatted_core = handler(adjusted_fixation)

        formatted = f"{prefix}{formatted_core}{suffix}"

        return FormattedWord(
            original=word,
            formatted=formatted,
            format_type=fmt
        )

    def format_text(
        self,
        text: str,
        output_format: OutputFormat | None = None
    ) -> FormattedText:
        """
        Metni formatla

        Args:
            text: Formatlanacak metin
            output_format: Çıktı formatı

        Returns:
            FormattedText: Formatlanmış metin
        """
        if not text:
            return FormattedText(
                original_text=text,
                formatted_text=text,
                output_format=output_format or self.default_format,
                word_count=0,
                bold_ratio=0.0,
                processing_details={}
            )

        fmt = output_format or self.default_format

        # Kelimeleri ayır (whitespace'leri koru)
        tokens = re.split(r'(\s+)', text)
        formatted_tokens = []
        word_count = 0
        total_chars = 0
        bold_chars = 0

        for token in tokens:
            if token.strip():
                formatted_word = self.format_word(token, fmt)
                formatted_tokens.append(formatted_word.formatted)
                word_count += 1

                # İstatistik hesaplama
                clean_word, _, _ = self._extract_punctuation(token)
                total_chars += len(clean_word)

                fixation = self.fixation_detector.detect(clean_word)
                bold_chars += fixation.bold_end
            else:
                formatted_tokens.append(token)

        formatted_text = "".join(formatted_tokens)
        bold_ratio = bold_chars / max(total_chars, 1)

        return FormattedText(
            original_text=text,
            formatted_text=formatted_text,
            output_format=fmt,
            word_count=word_count,
            bold_ratio=bold_ratio,
            processing_details={
                "boldness_level": self.boldness_level,
                "total_characters": total_chars,
                "bold_characters": bold_chars
            }
        )

    def _extract_punctuation(self, word: str) -> tuple[str, str, str]:
        """Kelimeden prefix ve suffix noktalama işaretlerini ayır"""
        punctuation = r'.,!?;:()[]{}"\'-–—…'

        prefix = ""
        suffix = ""
        clean = word

        # Prefix
        while clean and clean[0] in punctuation:
            prefix += clean[0]
            clean = clean[1:]

        # Suffix
        while clean and clean[-1] in punctuation:
            suffix = clean[-1] + suffix
            clean = clean[:-1]

        return clean, prefix, suffix

    def _adjust_for_boldness(self, fixation: FixationPoint) -> FixationPoint:
        """Boldness level'a göre fixation point'i ayarla"""
        # Boldness 3 (default) için değişiklik yok
        if self.boldness_level == 3:
            return fixation

        word = fixation.word
        original_end = fixation.bold_end

        # Boldness'a göre ayarla
        adjustment = (self.boldness_level - 3) * 0.15  # Her level için %15
        new_ratio = (original_end / len(word)) + adjustment
        new_ratio = max(0.1, min(0.6, new_ratio))  # %10-%60 arası

        new_end = int(len(word) * new_ratio)
        new_end = max(1, min(len(word), new_end))

        return FixationPoint(
            word=word,
            bold_start=0,
            bold_end=new_end,
            bold_text=word[:new_end],
            normal_text=word[new_end:],
            word_length_category=fixation.word_length_category,
            syllable_aware=fixation.syllable_aware,
            confidence=fixation.confidence
        )

    # Format handlers
    def _format_html(self, fixation: FixationPoint) -> str:
        """HTML formatı: <strong>bold</strong>normal"""
        bold_escaped = html.escape(fixation.bold_text)
        normal_escaped = html.escape(fixation.normal_text)
        return f"<strong>{bold_escaped}</strong>{normal_escaped}"

    def _format_markdown(self, fixation: FixationPoint) -> str:
        """Markdown formatı: **bold**normal"""
        return f"**{fixation.bold_text}**{fixation.normal_text}"

    def _format_plain_text(self, fixation: FixationPoint) -> str:
        """Plain text formatı: BOLD normal"""
        return f"{fixation.bold_text.upper()}{fixation.normal_text}"

    def _format_css_span(self, fixation: FixationPoint) -> str:
        """CSS span formatı: <span class="bionic-bold">bold</span>normal"""
        bold_escaped = html.escape(fixation.bold_text)
        normal_escaped = html.escape(fixation.normal_text)
        return f'<span class="{self.custom_css_class}">{bold_escaped}</span>{normal_escaped}'

    def _format_react_jsx(self, fixation: FixationPoint) -> str:
        """React JSX formatı: <strong>bold</strong>normal"""
        # JSX'de {} içinde özel karakterler escape edilmeli
        bold = fixation.bold_text.replace("{", "&#123;").replace("}", "&#125;")
        normal = fixation.normal_text.replace("{", "&#123;").replace("}", "&#125;")
        return f"<strong>{bold}</strong>{normal}"

    def _format_epub(self, fixation: FixationPoint) -> str:
        """EPUB formatı: HTML ile aynı ama XHTML uyumlu"""
        bold_escaped = html.escape(fixation.bold_text)
        normal_escaped = html.escape(fixation.normal_text)
        return f'<span style="font-weight:bold">{bold_escaped}</span>{normal_escaped}'

    def _format_latex(self, fixation: FixationPoint) -> str:
        """LaTeX formatı: \\textbf{bold}normal"""
        # LaTeX özel karakterlerini escape et
        bold = self._escape_latex(fixation.bold_text)
        normal = self._escape_latex(fixation.normal_text)
        return f"\\textbf{{{bold}}}{normal}"

    def _escape_latex(self, text: str) -> str:
        """LaTeX özel karakterlerini escape et"""
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text

    def set_boldness_level(self, level: int):
        """Boldness level'ı ayarla (1-5)"""
        self.boldness_level = max(1, min(5, level))

    def get_supported_formats(self) -> list[str]:
        """Desteklenen formatları döndür"""
        return [fmt.value for fmt in OutputFormat]

    def clear_cache(self):
        """Cache'i temizle"""
        self.fixation_detector.clear_cache()

    def get_cache_stats(self) -> dict:
        """Cache istatistiklerini döndür"""
        return {
            "formatter_settings": {
                "default_format": self.default_format.value,
                "boldness_level": self.boldness_level,
                "custom_css_class": self.custom_css_class
            },
            "fixation_detector": self.fixation_detector.get_cache_stats()
        }
