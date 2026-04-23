"""
Internationalization (i18n) Manager
Multi-language support for KIRO2 platform
"""

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """Supported languages"""
    TURKISH = "tr"
    ENGLISH = "en"
    GERMAN = "de"


class I18nManager:
    """
    Internationalization Manager

    Features:
    - Multi-language string management
    - Lazy loading of translations
    - Fallback to default language
    - Pluralization support
    - Variable interpolation
    """

    def __init__(self, locales_dir: str = "backend/locales", default_lang: str = "tr"):
        self.locales_dir = Path(locales_dir)
        self.default_lang = default_lang
        self.translations: dict[str, dict[str, Any]] = {}
        self._load_all_translations()

    def _load_all_translations(self):
        """Load all translation files"""
        for lang in Language:
            self._load_language(lang.value)

    def _load_language(self, lang_code: str):
        """Load translation file for a language"""
        file_path = self.locales_dir / f"{lang_code}.json"

        try:
            if file_path.exists():
                with open(file_path, encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                logger.info(f"Loaded translations for {lang_code}")
            else:
                logger.warning(f"Translation file not found: {file_path}")
                self.translations[lang_code] = {}
        except Exception as e:
            logger.error(f"Failed to load translations for {lang_code}: {e}")
            self.translations[lang_code] = {}

    def translate(
        self,
        key: str,
        lang: str = None,
        **kwargs
    ) -> str:
        """
        Get translated string

        Args:
            key: Translation key (e.g., 'common.welcome')
            lang: Language code (None = default)
            **kwargs: Variables for interpolation

        Returns:
            Translated string

        Example:
            i18n.translate('question.difficulty', lang='en', level='hard')
        """
        lang = lang or self.default_lang

        # Get translation
        translation = self._get_nested_value(
            self.translations.get(lang, {}),
            key
        )

        # Fallback to default language
        if translation is None and lang != self.default_lang:
            translation = self._get_nested_value(
                self.translations.get(self.default_lang, {}),
                key
            )

        # Fallback to key itself
        if translation is None:
            logger.warning(f"Translation not found: {key} ({lang})")
            return key

        # Interpolate variables
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Variable not provided for {key}: {e}")

        return translation

    def _get_nested_value(self, data: dict, key: str) -> str | None:
        """Get nested dictionary value using dot notation"""
        keys = key.split('.')
        value = data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return None

        return value if isinstance(value, str) else None

    def t(self, key: str, lang: str = None, **kwargs) -> str:
        """Alias for translate()"""
        return self.translate(key, lang, **kwargs)

    def pluralize(
        self,
        key: str,
        count: int,
        lang: str = None,
        **kwargs
    ) -> str:
        """
        Get pluralized translation

        Args:
            key: Base translation key
            count: Count for pluralization
            lang: Language code
            **kwargs: Additional variables

        Example:
            i18n.pluralize('question.count', 5)  # "5 questions"
        """
        lang = lang or self.default_lang

        # Get plural rules for language
        if count == 0:
            plural_key = f"{key}.zero"
        elif count == 1:
            plural_key = f"{key}.one"
        else:
            plural_key = f"{key}.other"

        # Try plural key first
        translation = self._get_nested_value(
            self.translations.get(lang, {}),
            plural_key
        )

        # Fallback to base key
        if translation is None:
            translation = self.translate(key, lang)

        # Add count to kwargs
        kwargs['count'] = count

        # Interpolate
        try:
            return translation.format(**kwargs)
        except (KeyError, ValueError, IndexError):
            return translation

    def get_available_languages(self) -> dict[str, str]:
        """Get list of available languages"""
        return {
            lang: self.translate('language.name', lang)
            for lang in self.translations.keys()
        }

    def add_translation(self, lang: str, key: str, value: str):
        """Add/update a translation dynamically"""
        if lang not in self.translations:
            self.translations[lang] = {}

        # Set nested value
        keys = key.split('.')
        data = self.translations[lang]

        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value

    def reload(self):
        """Reload all translations"""
        self.translations = {}
        self._load_all_translations()


# Global instance
_i18n_manager = None


def get_i18n() -> I18nManager:
    """Get global i18n manager instance"""
    global _i18n_manager

    if _i18n_manager is None:
        _i18n_manager = I18nManager()

    return _i18n_manager


# Convenience functions
def t(key: str, lang: str = None, **kwargs) -> str:
    """Translate shorthand"""
    return get_i18n().translate(key, lang, **kwargs)


def pluralize(key: str, count: int, lang: str = None, **kwargs) -> str:
    """Pluralize shorthand"""
    return get_i18n().pluralize(key, count, lang, **kwargs)
