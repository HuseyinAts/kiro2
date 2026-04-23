"""
Entity Linking Tool (Advanced Feature)
Turkce varlik tanimlari icin bilgi tabanina baglama

Links named entities to knowledge base entries (Wikipedia, custom KB).
"""

import logging
import re
from typing import Any

from .base import BaseToolHandler

logger = logging.getLogger(__name__)


# Turkish entity knowledge base (sample data)
TURKISH_ENTITIES_KB = {
    "istanbul": {
        "id": "Q406",
        "type": "LOCATION",
        "label": "İstanbul",
        "description": "Türkiye'nin en büyük şehri",
        "aliases": ["Constantinople", "Byzantium", "Konstantinopolis"],
        "wikidata_url": "https://www.wikidata.org/wiki/Q406",
    },
    "ankara": {
        "id": "Q3322",
        "type": "LOCATION",
        "label": "Ankara",
        "description": "Türkiye'nin başkenti",
        "aliases": ["Angora"],
        "wikidata_url": "https://www.wikidata.org/wiki/Q3322",
    },
    "ataturk": {
        "id": "Q352",
        "type": "PERSON",
        "label": "Mustafa Kemal Atatürk",
        "description": "Türkiye Cumhuriyeti'nin kurucusu",
        "aliases": ["Mustafa Kemal", "Gazi Mustafa Kemal"],
        "wikidata_url": "https://www.wikidata.org/wiki/Q352",
    },
    "turkiye": {
        "id": "Q43",
        "type": "LOCATION",
        "label": "Türkiye",
        "description": "Avrupa ve Asya'da yer alan ülke",
        "aliases": ["Turkey", "Türkiye Cumhuriyeti"],
        "wikidata_url": "https://www.wikidata.org/wiki/Q43",
    },
}

# Turkish universities
TURKISH_UNIVERSITIES_KB = {
    "odtu": {
        "id": "Q931561",
        "type": "ORGANIZATION",
        "label": "Orta Doğu Teknik Üniversitesi",
        "description": "Ankara'da devlet üniversitesi",
        "aliases": ["METU", "ODTÜ"],
    },
    "bogazici": {
        "id": "Q599120",
        "type": "ORGANIZATION",
        "label": "Boğaziçi Üniversitesi",
        "description": "İstanbul'da devlet üniversitesi",
        "aliases": ["Bosphorus University", "BÜ"],
    },
    "itu": {
        "id": "Q599180",
        "type": "ORGANIZATION",
        "label": "İstanbul Teknik Üniversitesi",
        "description": "İstanbul'da teknik üniversite",
        "aliases": ["İTÜ", "Istanbul Technical University"],
    },
}


class EntityLinkerHandler(BaseToolHandler):
    """Entity linking tool handler - links entities to knowledge base."""

    tool_name = "entity_linker"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Merge knowledge bases
        self._kb = {**TURKISH_ENTITIES_KB, **TURKISH_UNIVERSITIES_KB}
        self._alias_index = self._build_alias_index()

    def _build_alias_index(self) -> dict[str, str]:
        """Build reverse index from aliases to entity IDs."""
        index = {}
        for key, entity in self._kb.items():
            # Main key
            index[key.lower()] = key
            # Label
            index[entity["label"].lower()] = key
            # Aliases
            for alias in entity.get("aliases", []):
                index[alias.lower()] = key
        return index

    def _normalize_text(self, text: str) -> str:
        """Normalize Turkish text for matching."""
        # Turkish lowercase
        text = text.lower()
        text = text.replace("İ", "i").replace("I", "ı")
        # Remove diacritics for fuzzy matching
        replacements = {
            "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
            "Ç": "c", "Ğ": "g", "İ": "i", "Ö": "o", "Ş": "s", "Ü": "u",
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text

    def _find_entity(self, text: str) -> dict[str, Any] | None:
        """Find entity in knowledge base."""
        # Try exact match first
        normalized = self._normalize_text(text)

        if normalized in self._alias_index:
            key = self._alias_index[normalized]
            return self._kb[key]

        # Try original text
        if text.lower() in self._alias_index:
            key = self._alias_index[text.lower()]
            return self._kb[key]

        return None

    async def _call_jpype(
        self,
        text: str,
        entities: list[dict[str, Any]] | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """
        Link entities to knowledge base using NER + KB lookup.

        Args:
            text: Turkish text containing entities
            entities: Pre-extracted entities (optional, will extract if not provided)

        Returns:
            Entity linking results with KB entries
        """
        # Get entities (either provided or extract via NER)
        if entities is None:
            if self.bridge:
                try:
                    entities = await self.bridge.extract_entities_async(text)
                except Exception as e:
                    logger.warning(f"NER extraction failed: {e}, using pattern matching")
                    entities = self._extract_entities_pattern(text)
            else:
                entities = self._extract_entities_pattern(text)

        # Link each entity to KB
        linked_entities = []
        unlinked_entities = []

        for entity in entities:
            entity_text = entity.get("text", "")
            kb_entry = self._find_entity(entity_text)

            if kb_entry:
                linked_entities.append({
                    "text": entity_text,
                    "type": entity.get("type", kb_entry["type"]),
                    "start": entity.get("start", 0),
                    "end": entity.get("end", len(entity_text)),
                    "kb_id": kb_entry["id"],
                    "kb_label": kb_entry["label"],
                    "kb_description": kb_entry["description"],
                    "kb_url": kb_entry.get("wikidata_url", ""),
                    "confidence": 0.95,
                })
            else:
                unlinked_entities.append({
                    "text": entity_text,
                    "type": entity.get("type", "UNKNOWN"),
                    "start": entity.get("start", 0),
                    "end": entity.get("end", len(entity_text)),
                    "kb_id": None,
                    "confidence": 0.0,
                })

        total = len(linked_entities) + len(unlinked_entities)
        link_rate = len(linked_entities) / total if total > 0 else 0.0

        return {
            "text": text,
            "linked_entities": linked_entities,
            "unlinked_entities": unlinked_entities,
            "total_entities": total,
            "linked_count": len(linked_entities),
            "link_rate": round(link_rate, 2),
        }

    async def _call_backend(
        self,
        text: str,
        entities: list[dict[str, Any]] | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """Fallback to HTTP backend for entity linking."""
        try:
            response = await self._post(
                "/entity-link",
                {"text": text, "entities": entities}
            )
            return response
        except Exception as e:
            logger.warning(f"HTTP entity linking failed: {e}, using local KB")
            # Fall back to local KB lookup
            return await self._call_jpype(text, entities, **kwargs)

    def _extract_entities_pattern(self, text: str) -> list[dict[str, Any]]:
        """Extract entities using pattern matching (fallback)."""
        entities = []

        # Turkish proper noun pattern (capitalized words)
        proper_noun_pattern = re.compile(r"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\b")

        for match in proper_noun_pattern.finditer(text):
            entities.append({
                "text": match.group(),
                "type": "UNKNOWN",
                "start": match.start(),
                "end": match.end(),
            })

        # Common Turkish entity patterns
        patterns = [
            (r"\b(?:Dr\.|Prof\.|Doç\.)\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+", "PERSON"),
            (r"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+Üniversitesi\b", "ORGANIZATION"),
            (r"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+Şirketi\b", "ORGANIZATION"),
        ]

        for pattern, entity_type in patterns:
            for match in re.finditer(pattern, text):
                entities.append({
                    "text": match.group(),
                    "type": entity_type,
                    "start": match.start(),
                    "end": match.end(),
                })

        return entities
