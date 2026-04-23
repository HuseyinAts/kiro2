"""
Named Entity Recognition Tool (REQ-5)
Turkce ozel isim tespiti - PERSON, LOCATION, ORGANIZATION

Supports both JPype (direct Zemberek access) and HTTP backend.
"""

import logging
import re
from typing import Any

from ..models.tool_schemas import EntityType
from .base import BaseToolHandler

logger = logging.getLogger(__name__)

# Turkish person name patterns
PERSON_SUFFIXES = ["oğlu", "kızı", "bey", "hanım", "efendi"]
PERSON_TITLES = ["dr", "prof", "doç", "yrd", "av", "mr", "mrs", "ms", "bay", "bayan"]

# Turkish location patterns
LOCATION_SUFFIXES = ["ili", "ilçesi", "köyü", "mahallesi", "caddesi", "sokağı", "sokak"]
LOCATION_POSTPOSITIONS = ["'da", "'de", "'ta", "'te", "'dan", "'den", "'tan", "'ten"]

# Common Turkish cities
TURKISH_CITIES = {
    "istanbul", "ankara", "izmir", "bursa", "antalya", "adana", "konya",
    "gaziantep", "mersin", "diyarbakır", "kayseri", "eskişehir", "samsun",
    "denizli", "şanlıurfa", "adapazarı", "malatya", "trabzon", "erzurum",
    "van", "batman", "elazığ", "sivas", "manisa", "kahramanmaraş",
}

# Common Turkish locations (broader)
TURKISH_LOCATIONS = {
    "türkiye", "anadolu", "trakya", "ege", "akdeniz", "karadeniz",
    "marmara", "doğu anadolu", "güneydoğu anadolu", "iç anadolu",
    "boğaziçi", "boğaz", "haliç", "taksim", "kadıköy", "üsküdar",
}

# Organization patterns
ORG_SUFFIXES = ["a.ş.", "ltd.", "şti.", "a.ş", "ltd", "şti"]
ORG_KEYWORDS = [
    "holding", "vakfı", "derneği", "üniversitesi", "bakanlığı",
    "başkanlığı", "müdürlüğü", "kurumu", "ajansı", "bankası",
    "şirketi", "grubu", "enstitüsü", "fakültesi",
]


class NERHandler(BaseToolHandler):
    """Named Entity Recognition tool handler"""

    tool_name = "ner"

    async def _call_jpype(self, text: str, **kwargs) -> dict[str, Any]:
        """
        Extract named entities using JPype bridge.

        Args:
            text: Turkish text to analyze

        Returns:
            NERResult as dictionary
        """
        if not self.bridge:
            raise RuntimeError("JPype bridge not initialized")

        entities: list[dict[str, Any]] = []

        # Try JPype NER if available
        try:
            jpype_entities = await self.bridge.extract_entities_async(text)
            for entity in jpype_entities:
                entity_type = self._map_entity_type(entity.get("type", ""))
                entities.append({
                    "text": entity.get("text", ""),
                    "type": entity_type.value,
                    "start": entity.get("start", 0),
                    "end": entity.get("end", 0),
                    "confidence": 0.85,
                    "is_multi_word": " " in entity.get("text", ""),
                })
        except Exception as e:
            logger.warning(f"[NER] JPype NER not available: {e}, using pattern-based")

        # If no entities from JPype, use pattern-based fallback
        if not entities:
            # Get morphology for proper noun detection
            word_analyses = await self._get_morphology_jpype(text)

            proper_noun_entities = self._extract_proper_nouns(text, word_analyses)
            entities.extend(proper_noun_entities)

            pattern_entities = self._extract_pattern_entities(text)
            entities.extend(pattern_entities)

            capital_entities = self._extract_capitalized_groups(text, word_analyses)
            entities.extend(capital_entities)

            entities = self._merge_entities(entities)

        person_count = sum(1 for e in entities if e["type"] == EntityType.PERSON.value)
        location_count = sum(1 for e in entities if e["type"] == EntityType.LOCATION.value)
        org_count = sum(1 for e in entities if e["type"] == EntityType.ORGANIZATION.value)

        return {
            "text": text,
            "entities": entities,
            "entity_count": len(entities),
            "person_count": person_count,
            "location_count": location_count,
            "organization_count": org_count,
        }

    async def _get_morphology_jpype(self, text: str) -> dict[str, list[dict]]:
        """Get morphological analysis using JPype bridge."""
        word_analyses = {}
        words = text.split()

        for word in words:
            clean_word = re.sub(r"[^\w']", "", word)
            if not clean_word:
                continue

            try:
                analyses = await self.bridge.analyze_word_async(clean_word)
                word_analyses[clean_word] = analyses
            except Exception:
                word_analyses[clean_word] = []

        return word_analyses

    def _map_entity_type(self, zemberek_type: str) -> EntityType:
        """Map Zemberek entity type to our EntityType enum."""
        type_map = {
            "PERSON": EntityType.PERSON,
            "PER": EntityType.PERSON,
            "LOCATION": EntityType.LOCATION,
            "LOC": EntityType.LOCATION,
            "ORGANIZATION": EntityType.ORGANIZATION,
            "ORG": EntityType.ORGANIZATION,
        }
        return type_map.get(zemberek_type.upper(), EntityType.UNKNOWN)

    async def _call_backend(self, text: str, **kwargs) -> dict[str, Any]:
        """
        Extract named entities from Turkish text

        Args:
            text: Turkish text to analyze

        Returns:
            NERResult as dictionary
        """
        entities: list[dict[str, Any]] = []

        # 1. Get morphological analysis for proper noun detection
        word_analyses = await self._get_morphology(text)

        # 2. Extract entities using multiple strategies
        # Strategy 1: Proper noun detection via morphology
        proper_noun_entities = self._extract_proper_nouns(text, word_analyses)
        entities.extend(proper_noun_entities)

        # Strategy 2: Pattern-based detection
        pattern_entities = self._extract_pattern_entities(text)
        entities.extend(pattern_entities)

        # Strategy 3: Capitalized word grouping
        capital_entities = self._extract_capitalized_groups(text, word_analyses)
        entities.extend(capital_entities)

        # Deduplicate and merge overlapping entities
        entities = self._merge_entities(entities)

        # Count by type
        person_count = sum(1 for e in entities if e["type"] == EntityType.PERSON.value)
        location_count = sum(1 for e in entities if e["type"] == EntityType.LOCATION.value)
        org_count = sum(1 for e in entities if e["type"] == EntityType.ORGANIZATION.value)

        return {
            "text": text,
            "entities": entities,
            "entity_count": len(entities),
            "person_count": person_count,
            "location_count": location_count,
            "organization_count": org_count,
        }

    async def _get_morphology(self, text: str) -> dict[str, list[dict]]:
        """Get morphological analysis for all words"""
        word_analyses = {}
        words = text.split()

        for word in words:
            # Clean punctuation
            clean_word = re.sub(r"[^\w']", "", word)
            if not clean_word:
                continue

            try:
                response = await self._post("/analyze", {"word": clean_word})
                word_analyses[clean_word] = response.get("analyses", [])
            except Exception:
                word_analyses[clean_word] = []

        return word_analyses

    def _extract_proper_nouns(
        self, text: str, word_analyses: dict[str, list[dict]]
    ) -> list[dict[str, Any]]:
        """Extract entities from morphological proper noun tags"""
        entities = []

        for word, analyses in word_analyses.items():
            if not analyses:
                continue

            # Check if any analysis marks it as proper noun
            for analysis in analyses:
                pos = analysis.get("pos", "")
                if "Prop" in pos or "Noun,Prop" in pos:
                    # Classify the proper noun
                    entity_type = self._classify_proper_noun(word, pos)
                    start = text.find(word)
                    if start >= 0:
                        entities.append({
                            "text": word,
                            "type": entity_type.value,
                            "start": start,
                            "end": start + len(word),
                            "confidence": 0.8,
                            "is_multi_word": False,
                        })
                    break

        return entities

    def _extract_pattern_entities(self, text: str) -> list[dict[str, Any]]:
        """Extract entities using Turkish-specific patterns"""
        entities = []

        # Person patterns
        for pattern in self._get_person_patterns():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "text": match.group().strip(),
                    "type": EntityType.PERSON.value,
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.7,
                    "is_multi_word": " " in match.group(),
                })

        # Location patterns
        for pattern in self._get_location_patterns():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "text": match.group().strip(),
                    "type": EntityType.LOCATION.value,
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.7,
                    "is_multi_word": " " in match.group(),
                })

        # Organization patterns
        for pattern in self._get_org_patterns():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "text": match.group().strip(),
                    "type": EntityType.ORGANIZATION.value,
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.7,
                    "is_multi_word": " " in match.group(),
                })

        return entities

    def _extract_capitalized_groups(
        self, text: str, word_analyses: dict[str, list[dict]]
    ) -> list[dict[str, Any]]:
        """Extract entities from consecutive capitalized words"""
        entities = []

        # Find sequences of capitalized words
        pattern = r"\b([A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)+)\b"

        for match in re.finditer(pattern, text):
            group = match.group()
            words = group.split()

            # Skip if first word is at sentence start (might not be entity)
            if match.start() == 0 or text[match.start() - 1] in ".!?\n":
                # Check if it looks like a name (2-3 words)
                if len(words) > 3:
                    continue

            # Classify the multi-word entity
            entity_type = self._classify_multi_word(group, word_analyses)

            entities.append({
                "text": group,
                "type": entity_type.value,
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.6,
                "is_multi_word": True,
            })

        return entities

    def _classify_proper_noun(self, word: str, pos: str) -> EntityType:
        """Classify a proper noun by type"""
        word_lower = word.lower()

        # Check for location keywords
        if word_lower in TURKISH_CITIES or word_lower in TURKISH_LOCATIONS:
            return EntityType.LOCATION

        # Check for organization indicators
        for suffix in ORG_SUFFIXES:
            if word_lower.endswith(suffix):
                return EntityType.ORGANIZATION

        # Check for person indicators
        for suffix in PERSON_SUFFIXES:
            if word_lower.endswith(suffix):
                return EntityType.PERSON

        # Default to person for unclassified proper nouns
        return EntityType.PERSON

    def _classify_multi_word(
        self, text: str, word_analyses: dict[str, list[dict]]
    ) -> EntityType:
        """Classify a multi-word entity"""
        text_lower = text.lower()
        words = text.split()

        # Check for organization keywords
        for keyword in ORG_KEYWORDS:
            if keyword in text_lower:
                return EntityType.ORGANIZATION

        # Check for location patterns
        for suffix in LOCATION_SUFFIXES:
            if text_lower.endswith(suffix):
                return EntityType.LOCATION

        # Check if contains known city
        for city in TURKISH_CITIES:
            if city in text_lower:
                return EntityType.LOCATION

        # Check word count (person names usually 2-3 words)
        if 2 <= len(words) <= 3:
            # Check for person titles
            first_word = words[0].lower()
            if first_word in PERSON_TITLES:
                return EntityType.PERSON

            # Default multi-word capitalized to person
            return EntityType.PERSON

        return EntityType.UNKNOWN

    def _get_person_patterns(self) -> list[str]:
        """Get regex patterns for person detection"""
        patterns = []

        # Title + Name patterns
        title_pattern = "|".join(PERSON_TITLES)
        patterns.append(rf"\b({title_pattern})\.?\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+")

        # Name + suffix patterns
        for suffix in PERSON_SUFFIXES:
            patterns.append(rf"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+{suffix}\b")

        return patterns

    def _get_location_patterns(self) -> list[str]:
        """Get regex patterns for location detection"""
        patterns = []

        # Known cities (with optional postposition)
        cities_pattern = "|".join(re.escape(c) for c in TURKISH_CITIES)
        patterns.append(rf"\b({cities_pattern})(?:'[dt][ea]n?)?\b")

        # Location + suffix patterns
        for suffix in LOCATION_SUFFIXES:
            patterns.append(rf"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+{suffix}\b")

        return patterns

    def _get_org_patterns(self) -> list[str]:
        """Get regex patterns for organization detection"""
        patterns = []

        # Company suffix patterns
        for suffix in ORG_SUFFIXES:
            patterns.append(rf"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜa-zçğıöşü]+)*\s+{re.escape(suffix)}")

        # Organization keyword patterns
        for keyword in ORG_KEYWORDS:
            patterns.append(rf"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜa-zçğıöşü]+)*\s+{re.escape(keyword)}\b")

        return patterns

    def _merge_entities(
        self, entities: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Merge overlapping entities and deduplicate"""
        if not entities:
            return []

        # Sort by start position
        sorted_entities = sorted(entities, key=lambda e: (e["start"], -e["end"]))

        merged = []
        for entity in sorted_entities:
            # Check if overlaps with last merged entity
            if merged and self._overlaps(merged[-1], entity):
                # Keep the one with higher confidence or longer span
                if entity["confidence"] > merged[-1]["confidence"] or (
                    entity["confidence"] == merged[-1]["confidence"]
                    and len(entity["text"]) > len(merged[-1]["text"])
                ):
                    merged[-1] = entity
            else:
                merged.append(entity)

        return merged

    def _overlaps(self, e1: dict, e2: dict) -> bool:
        """Check if two entities overlap"""
        return not (e1["end"] <= e2["start"] or e2["end"] <= e1["start"])
