"""
Dictionary Trainer Module

Custom dictionary training for Zemberek.
Adds domain-specific terms for Turkish education content.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DictionaryEntry:
    """A dictionary entry with morphological information."""

    word: str
    lemma: str
    pos: str  # Part of speech: Noun, Verb, Adj, etc.
    root: Optional[str] = None
    attributes: List[str] = field(default_factory=list)
    pronunciation: Optional[str] = None
    frequency: int = 0

    def to_zemberek_format(self) -> str:
        """Convert to Zemberek dictionary format."""
        # Format: lemma [P:POS, A:Attr1, A:Attr2]
        parts = [self.lemma]

        attrs = [f"P:{self.pos}"]
        for attr in self.attributes:
            attrs.append(f"A:{attr}")

        if attrs:
            parts.append(f"[{', '.join(attrs)}]")

        return " ".join(parts)


class DictionaryTrainer:
    """
    Custom dictionary trainer for Turkish educational domain.

    Features:
    - Add domain-specific terms (YKS, TYT, etc.)
    - Learn informal -> formal mappings
    - Export to Zemberek-compatible format
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("dictionaries")
        self._entries: Dict[str, DictionaryEntry] = {}
        self._informal_mappings: Dict[str, str] = {}

        # Educational domain terms (pre-loaded)
        self._load_educational_terms()

    def _load_educational_terms(self) -> None:
        """Load pre-defined educational domain terms."""
        educational_terms = [
            # Exam types
            DictionaryEntry("YKS", "YKS", "Noun", attributes=["Abbr", "ProperNoun"]),
            DictionaryEntry("TYT", "TYT", "Noun", attributes=["Abbr", "ProperNoun"]),
            DictionaryEntry("AYT", "AYT", "Noun", attributes=["Abbr", "ProperNoun"]),
            DictionaryEntry("LGS", "LGS", "Noun", attributes=["Abbr", "ProperNoun"]),
            DictionaryEntry("ÖSYM", "ÖSYM", "Noun", attributes=["Abbr", "ProperNoun"]),

            # Educational terms
            DictionaryEntry("fonksiyon", "fonksiyon", "Noun"),
            DictionaryEntry("integral", "integral", "Noun"),
            DictionaryEntry("türev", "türev", "Noun"),
            DictionaryEntry("logaritma", "logaritma", "Noun"),
            DictionaryEntry("trigonometri", "trigonometri", "Noun"),
            DictionaryEntry("geometri", "geometri", "Noun"),
            DictionaryEntry("analitik", "analitik", "Adj"),
            DictionaryEntry("polinom", "polinom", "Noun"),
            DictionaryEntry("matris", "matris", "Noun"),
            DictionaryEntry("determinant", "determinant", "Noun"),

            # Science terms
            DictionaryEntry("molekül", "molekül", "Noun"),
            DictionaryEntry("atom", "atom", "Noun"),
            DictionaryEntry("proton", "proton", "Noun"),
            DictionaryEntry("nötron", "nötron", "Noun"),
            DictionaryEntry("elektron", "elektron", "Noun"),
            DictionaryEntry("kuantum", "kuantum", "Noun"),
            DictionaryEntry("relativite", "relativite", "Noun"),

            # Common abbreviations
            DictionaryEntry("ör.", "örneğin", "Adv", attributes=["Abbr"]),
            DictionaryEntry("bkz.", "bakınız", "Verb", attributes=["Abbr"]),
            DictionaryEntry("vb.", "ve benzeri", "Noun", attributes=["Abbr"]),
        ]

        for entry in educational_terms:
            self._entries[entry.word.lower()] = entry

        logger.info(f"Loaded {len(educational_terms)} educational terms")

    def add_entry(self, entry: DictionaryEntry) -> None:
        """Add a new dictionary entry."""
        self._entries[entry.word.lower()] = entry
        logger.debug(f"Added entry: {entry.word}")

    def add_word(
        self,
        word: str,
        pos: str = "Noun",
        attributes: Optional[List[str]] = None
    ) -> None:
        """Add a simple word entry."""
        entry = DictionaryEntry(
            word=word,
            lemma=word,
            pos=pos,
            attributes=attributes or []
        )
        self.add_entry(entry)

    def add_informal_mapping(self, informal: str, formal: str) -> None:
        """
        Add informal -> formal text mapping.

        Examples:
            "naber" -> "ne haber"
            "slm" -> "selam"
            "tmm" -> "tamam"
        """
        self._informal_mappings[informal.lower()] = formal
        logger.debug(f"Added mapping: {informal} -> {formal}")

    def load_mappings_from_file(self, path: Path) -> int:
        """
        Load informal mappings from JSON file.

        Expected format:
        {
            "naber": "ne haber",
            "slm": "selam",
            "tmm": "tamam"
        }
        """
        with open(path, "r", encoding="utf-8") as f:
            mappings = json.load(f)

        for informal, formal in mappings.items():
            self.add_informal_mapping(informal, formal)

        return len(mappings)

    def learn_from_text(self, text: str, min_frequency: int = 3) -> List[str]:
        """
        Learn new words from text corpus.

        Identifies words not in dictionary and suggests additions.
        """
        # Tokenize
        words = re.findall(r"\b[a-zA-ZçğıöşüÇĞİÖŞÜ]+\b", text.lower())

        # Count frequencies
        word_freq: Dict[str, int] = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Find unknown words above frequency threshold
        unknown_words = []
        for word, freq in word_freq.items():
            if freq >= min_frequency and word not in self._entries:
                unknown_words.append(word)

        logger.info(f"Found {len(unknown_words)} unknown words (freq >= {min_frequency})")
        return unknown_words

    def export_zemberek_dictionary(self, path: Optional[Path] = None) -> Path:
        """
        Export dictionary in Zemberek-compatible format.

        Format: lemma [P:POS, A:Attr1, ...]
        """
        output_path = path or (self.output_dir / "custom_dictionary.txt")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Custom Dictionary for Turkish Education Domain\n")
            f.write("# Generated by Zemberek-NLP MCP Server\n\n")

            for entry in sorted(self._entries.values(), key=lambda e: e.word):
                f.write(entry.to_zemberek_format() + "\n")

        logger.info(f"Exported {len(self._entries)} entries to {output_path}")
        return output_path

    def export_informal_mappings(self, path: Optional[Path] = None) -> Path:
        """Export informal -> formal mappings to JSON."""
        output_path = path or (self.output_dir / "informal_mappings.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self._informal_mappings, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported {len(self._informal_mappings)} mappings to {output_path}")
        return output_path

    def get_stats(self) -> Dict[str, Any]:
        """Get dictionary statistics."""
        pos_counts: Dict[str, int] = {}
        for entry in self._entries.values():
            pos_counts[entry.pos] = pos_counts.get(entry.pos, 0) + 1

        return {
            "total_entries": len(self._entries),
            "informal_mappings": len(self._informal_mappings),
            "pos_distribution": pos_counts,
        }


# Pre-defined Turkish informal mappings (common internet/SMS language)
TURKISH_INFORMAL_MAPPINGS = {
    # Greetings
    "slm": "selam",
    "mrb": "merhaba",
    "naber": "ne haber",
    "nbr": "ne haber",
    "sa": "selamun aleyküm",
    "as": "aleyküm selam",

    # Common words
    "tmm": "tamam",
    "ok": "tamam",
    "tşk": "teşekkürler",
    "tşkler": "teşekkürler",
    "eyw": "eyvallah",
    "hg": "hoş geldin",
    "hb": "hoş bulduk",

    # Question words
    "ndn": "neden",
    "nsl": "nasıl",
    "nere": "nerede",
    "kim": "kim",

    # Study-related
    "çlşmk": "çalışmak",
    "snv": "sınav",
    "ders": "ders",

    # Expressions
    "blm": "bilmiyorum",
    "anlmadm": "anlamadım",
    "anldm": "anladım",
    "grşrz": "görüşürüz",
    "bb": "bay bay",
}


def create_crowdsourced_collector() -> "CrowdsourcedCollector":
    """Create a crowdsourced correction collector."""
    return CrowdsourcedCollector()


class CrowdsourcedCollector:
    """
    Collects user-submitted corrections for crowdsourced dictionary improvement.

    Allows users to submit:
    - Spelling corrections
    - Informal -> formal mappings
    - New domain terms
    """

    def __init__(self):
        self._corrections: List[Dict[str, Any]] = []
        self._new_terms: List[Dict[str, Any]] = []
        self._votes: Dict[str, int] = {}

    def submit_correction(
        self,
        original: str,
        corrected: str,
        context: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Submit a spelling correction."""
        correction = {
            "id": f"corr_{len(self._corrections)}",
            "original": original,
            "corrected": corrected,
            "context": context,
            "user_id": user_id,
            "votes": 0,
            "status": "pending",
        }
        self._corrections.append(correction)
        return correction["id"]

    def submit_term(
        self,
        term: str,
        pos: str,
        definition: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Submit a new domain term."""
        new_term = {
            "id": f"term_{len(self._new_terms)}",
            "term": term,
            "pos": pos,
            "definition": definition,
            "user_id": user_id,
            "votes": 0,
            "status": "pending",
        }
        self._new_terms.append(new_term)
        return new_term["id"]

    def vote(self, item_id: str, upvote: bool = True) -> int:
        """Vote on a submitted correction or term."""
        delta = 1 if upvote else -1
        self._votes[item_id] = self._votes.get(item_id, 0) + delta
        return self._votes[item_id]

    def get_approved_corrections(self, min_votes: int = 3) -> List[Dict[str, Any]]:
        """Get corrections with enough votes for approval."""
        approved = []
        for corr in self._corrections:
            if self._votes.get(corr["id"], 0) >= min_votes:
                approved.append(corr)
        return approved

    def export_to_dictionary_trainer(
        self, trainer: DictionaryTrainer, min_votes: int = 3
    ) -> int:
        """Export approved submissions to dictionary trainer."""
        count = 0

        # Export corrections as informal mappings
        for corr in self.get_approved_corrections(min_votes):
            trainer.add_informal_mapping(corr["original"], corr["corrected"])
            count += 1

        # Export new terms
        for term in self._new_terms:
            if self._votes.get(term["id"], 0) >= min_votes:
                trainer.add_word(term["term"], term["pos"])
                count += 1

        return count
