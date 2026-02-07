"""
Turkish Prompt Optimizer
Optimizes prompts for token efficiency with Turkish text

Author: KIRO AI Team
Date: 2025-10-19
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class OptimizationResult:
    """Result of prompt optimization"""

    original_prompt: str
    optimized_prompt: str
    original_tokens: int
    optimized_tokens: int
    token_savings: int
    savings_percentage: float
    optimizations_applied: List[str]


class TurkishPromptOptimizer:
    """
    Turkish Prompt Optimizer

    Optimizes prompts for token efficiency by:
    1. Using morphologically efficient Turkish words
    2. Replacing verbose phrases with concise alternatives
    3. Removing redundant Turkish grammar
    4. Using compact Turkish expressions
    """

    def __init__(self, common_words_path: Optional[str] = None):
        """
        Initialize optimizer

        Args:
            common_words_path: Path to common Turkish words file
        """
        self.common_words_path = common_words_path
        self.common_words = self._load_common_words()

        # Token-efficient replacements for Turkish
        self.replacements = {
            # Verbose phrases -> Concise alternatives
            "lütfen aşağıdaki": "aşağıdaki",
            "lütfen şunu": "şunu",
            "lütfen bunu": "bunu",
            "sizden rica ediyorum": "",
            "eğer mümkünse": "",
            "mümkün olduğunca": "",
            "olabildiğince": "",
            # Redundant polite forms
            "rica etsem": "",
            "lütfen lütfen": "lütfen",
            # Verbose connectors
            "bundan dolayı": "bu yüzden",
            "bu nedenle": "bu yüzden",
            "bu sebepten": "bu yüzden",
            "bunun sonucunda": "sonuçta",
            # Wordy expressions
            "göz önünde bulundurarak": "dikkate alarak",
            "dikkate alınarak": "dikkate alarak",
            "hesaba katılarak": "dikkate alarak",
            # Academic verbosity
            "yukarıda belirtilen": "yukarıdaki",
            "aşağıda gösterilen": "aşağıdaki",
            "daha önce bahsedilen": "bahsedilen",
            # Question forms
            "hangisidir?": "hangisi?",
            "nedir?": "ne?",
            "kimdir?": "kim?",
            "nasıldır?": "nasıl?",
            # Redundant determiners
            "bir adet": "bir",
            "toplam olarak": "toplam",
            "tam olarak": "tam",
        }

        # Morphological optimizations
        self.morphological_patterns = {
            # Plural + possessive can often be simplified
            r"(\w+)ların(\w+)": r"\1ların\2",  # Keep as is if already optimal
            # Redundant case markers in context
            r"için için": "için",
            r"ile ile": "ile",
            r"den den": "den",
        }

    def _load_common_words(self) -> set:
        """Load common Turkish words for optimization"""
        if not self.common_words_path:
            # Return built-in common words
            return self._get_builtin_common_words()

        try:
            path = Path(self.common_words_path)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return set(data.get("words", []))
        except Exception as e:
            print(
                f"Warning: Could not load common words from {self.common_words_path}: {e}"
            )

        return self._get_builtin_common_words()

    def _get_builtin_common_words(self) -> set:
        """Get built-in set of common Turkish words"""
        return {
            # Top 100 most common Turkish words
            "bir",
            "bu",
            "ve",
            "için",
            "ile",
            "ne",
            "mi",
            "var",
            "yok",
            "çok",
            "çünkü",
            "ama",
            "fakat",
            "ancak",
            "veya",
            "ya",
            "da",
            "de",
            "ki",
            "şey",
            "gibi",
            "kadar",
            "daha",
            "en",
            "her",
            "hiç",
            "bazı",
            "tüm",
            "hep",
            "yani",
            "şimdi",
            "sonra",
            "önce",
            "biz",
            "siz",
            "onlar",
            "ben",
            "sen",
            "o",
            "olan",
            "eden",
            "yapan",
            "gelen",
            "giden",
            "alan",
            "veren",
            "iyi",
            "kötü",
            "büyük",
            "küçük",
            "yeni",
            "eski",
            "güzel",
            "soru",
            "cevap",
            "doğru",
            "yanlış",
            "sınavı",
            "test",
            "matematik",
            "fen",
            "edebiyat",
            "tarih",
            "coğrafya",
            "sayı",
            "rakam",
            "hesap",
            "işlem",
            "sonuç",
            "toplam",
            "fark",
            "oran",
            "yüzde",
            "değer",
            "miktar",
            "adet",
        }

    def optimize(self, prompt: str, estimate_tokens: bool = True) -> OptimizationResult:
        """
        Optimize Turkish prompt for token efficiency

        Args:
            prompt: Original prompt text
            estimate_tokens: Whether to estimate token counts

        Returns:
            OptimizationResult with optimization details
        """
        optimizations_applied = []
        optimized = prompt

        # 1. Apply direct replacements
        for verbose, concise in self.replacements.items():
            if verbose in optimized:
                optimized = optimized.replace(verbose, concise)
                optimizations_applied.append(f"Replaced '{verbose}' -> '{concise}'")

        # 2. Remove excessive whitespace
        original_spaces = optimized
        optimized = re.sub(r"\s+", " ", optimized)
        optimized = optimized.strip()
        if original_spaces != optimized:
            optimizations_applied.append("Removed excessive whitespace")

        # 3. Apply morphological patterns
        for pattern, replacement in self.morphological_patterns.items():
            matches = re.findall(pattern, optimized)
            if matches:
                optimized = re.sub(pattern, replacement, optimized)
                optimizations_applied.append(
                    f"Applied morphological pattern: {pattern}"
                )

        # 4. Remove redundant punctuation
        optimized = re.sub(r"\.\.+", ".", optimized)
        optimized = re.sub(r"\?\?+", "?", optimized)
        optimized = re.sub(r"!!+", "!", optimized)

        # 5. Simplify question endings
        optimized = re.sub(r"\?\.", "?", optimized)
        optimized = re.sub(r"\.?$", "", optimized.strip())

        # Estimate token counts (rough approximation)
        if estimate_tokens:
            original_tokens = self._estimate_tokens(prompt)
            optimized_tokens = self._estimate_tokens(optimized)
        else:
            original_tokens = len(prompt.split())
            optimized_tokens = len(optimized.split())

        token_savings = original_tokens - optimized_tokens
        savings_percentage = (
            (token_savings / original_tokens * 100) if original_tokens > 0 else 0
        )

        return OptimizationResult(
            original_prompt=prompt,
            optimized_prompt=optimized,
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            token_savings=token_savings,
            savings_percentage=savings_percentage,
            optimizations_applied=optimizations_applied,
        )

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for Turkish text

        Uses heuristic: 1 Turkish word ≈ 1.7 tokens (average for GPT-4)
        """
        words = text.split()

        # Count Turkish characters (ğ, ş, ü, ö, ç, ı, İ)
        turkish_char_count = sum(1 for char in text if char in "ğüşıöçĞÜŞİÖÇ")

        # Base token count
        base_tokens = len(words) * 1.7

        # Add penalty for Turkish characters (they often split into multiple tokens)
        turkish_penalty = turkish_char_count * 0.3

        # Add penalty for long words
        long_word_penalty = sum(0.5 for word in words if len(word) > 10)

        estimated = int(base_tokens + turkish_penalty + long_word_penalty)
        return estimated

    def optimize_osym_prompt(self, prompt_data: Dict[str, str]) -> Dict[str, str]:
        """
        Optimize OSYM question generation prompt

        Args:
            prompt_data: Dict with keys like 'system', 'user', 'instructions'

        Returns:
            Optimized prompt data
        """
        optimized_data = {}

        for key, value in prompt_data.items():
            if isinstance(value, str):
                result = self.optimize(value)
                optimized_data[key] = result.optimized_prompt
                print(
                    f"[{key}] Token savings: {result.token_savings} ({result.savings_percentage:.1f}%)"
                )
            else:
                optimized_data[key] = value

        return optimized_data

    def batch_optimize(self, prompts: List[str]) -> List[OptimizationResult]:
        """
        Optimize multiple prompts

        Args:
            prompts: List of prompt texts

        Returns:
            List of optimization results
        """
        results = []
        for prompt in prompts:
            result = self.optimize(prompt)
            results.append(result)

        return results

    def get_optimization_stats(
        self, results: List[OptimizationResult]
    ) -> Dict[str, float]:
        """
        Get statistics from batch optimization

        Args:
            results: List of optimization results

        Returns:
            Statistics dictionary
        """
        total_original = sum(r.original_tokens for r in results)
        total_optimized = sum(r.optimized_tokens for r in results)
        total_savings = total_original - total_optimized

        return {
            "total_prompts": len(results),
            "total_original_tokens": total_original,
            "total_optimized_tokens": total_optimized,
            "total_token_savings": total_savings,
            "average_savings_percentage": (total_savings / total_original * 100)
            if total_original > 0
            else 0,
            "max_savings_percentage": max(r.savings_percentage for r in results)
            if results
            else 0,
            "min_savings_percentage": min(r.savings_percentage for r in results)
            if results
            else 0,
        }


def create_optimized_osym_prompts() -> Dict[str, str]:
    """
    Create optimized OSYM question generation prompts

    Returns:
        Dictionary of optimized prompts
    """
    optimizer = TurkishPromptOptimizer()

    # Original verbose prompts
    original_prompts = {
        "system": """Sen ÖSYM sınavları için soru hazırlayan bir uzmansın.
        Lütfen aşağıdaki kurallara dikkat ederek soru hazırla:
        - Soru Türkçe dilbilgisi kurallarına uygun olmalı
        - Lütfen 5 şık hazırla (A, B, C, D, E)
        - Lütfen çeldiriciler akla yatkın olmalı
        - Lütfen doğru cevap net olmalı
        - Eğer mümkünse soru ÖSYM formatına uygun olmalı""",
        "user": """Lütfen şu konuda bir soru hazırla: {topic}
        Alt konu: {subtopic}
        Zorluk seviyesi: {difficulty}
        Bloom taksonomisi seviyesi: {bloom_level}
        Sınav türü: {exam_type}

        Lütfen soruyu JSON formatında ver:
        - stem: soru metni
        - options: 5 şık listesi
        - correct_answer: doğru cevabın indeksi
        - explanation: açıklama""",
    }

    # Optimize
    optimized = optimizer.optimize_osym_prompt(original_prompts)

    return optimized


# Example usage and testing
if __name__ == "__main__":
    import sys
    import io

    # Fix UTF-8 encoding for Windows console
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== Turkish Prompt Optimizer Test ===\n")

    optimizer = TurkishPromptOptimizer()

    # Test 1: Simple optimization
    test_prompt = "Lütfen aşağıdaki soruyu cevaplayınız. Eğer mümkünse detaylı bir şekilde açıklayınız."
    result = optimizer.optimize(test_prompt)

    print(f"Original: {result.original_prompt}")
    print(f"Optimized: {result.optimized_prompt}")
    print(f"Token savings: {result.token_savings} ({result.savings_percentage:.1f}%)")
    print(f"Optimizations: {result.optimizations_applied}\n")

    # Test 2: OSYM prompt optimization
    print("=== OSYM Prompt Optimization ===\n")
    optimized_osym = create_optimized_osym_prompts()

    for key, value in optimized_osym.items():
        print(f"[{key}]")
        print(value)
        print()

    # Test 3: Batch optimization
    test_prompts = [
        "Lütfen bu soruyu cevaplayınız. Yukarıda belirtilen kurallara göre hareket ediniz.",
        "Aşağıda gösterilen şıklardan doğru olanı işaretleyiniz. Bundan dolayı dikkatli olunuz.",
        "Bu nedenle lütfen lütfen çok dikkatli olunuz. Eğer mümkünse tüm şıkları okuyunuz.",
    ]

    batch_results = optimizer.batch_optimize(test_prompts)
    stats = optimizer.get_optimization_stats(batch_results)

    print("=== Batch Optimization Stats ===")
    print(f"Total prompts: {stats['total_prompts']}")
    print(f"Total original tokens: {stats['total_original_tokens']}")
    print(f"Total optimized tokens: {stats['total_optimized_tokens']}")
    print(
        f"Total savings: {stats['total_token_savings']} tokens ({stats['average_savings_percentage']:.1f}%)"
    )
    print(f"Max savings: {stats['max_savings_percentage']:.1f}%")
    print(f"Min savings: {stats['min_savings_percentage']:.1f}%")
