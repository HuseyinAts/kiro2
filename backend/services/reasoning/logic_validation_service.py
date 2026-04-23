"""
Logic Validation Service
Formal logic engine for reasoning validation (REQ-5)

Features:
- Consistency checking between reasoning steps
- Circular reasoning detection
- Inference validation (Modus Ponens, Modus Tollens, etc.)
- Assumption tracking
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class InferenceRule(str, Enum):
    """Supported inference rules"""
    MODUS_PONENS = "modus_ponens"  # P → Q, P ⊢ Q
    MODUS_TOLLENS = "modus_tollens"  # P → Q, ¬Q ⊢ ¬P
    HYPOTHETICAL_SYLLOGISM = "hypothetical_syllogism"  # P → Q, Q → R ⊢ P → R
    DISJUNCTIVE_SYLLOGISM = "disjunctive_syllogism"  # P ∨ Q, ¬P ⊢ Q
    CONJUNCTION = "conjunction"  # P, Q ⊢ P ∧ Q
    SIMPLIFICATION = "simplification"  # P ∧ Q ⊢ P
    ADDITION = "addition"  # P ⊢ P ∨ Q
    CONSTRUCTIVE_DILEMMA = "constructive_dilemma"  # (P → Q) ∧ (R → S), P ∨ R ⊢ Q ∨ S
    UNKNOWN = "unknown"


@dataclass
class Proposition:
    """A logical proposition"""
    content: str
    is_negated: bool = False
    original_text: str = ""

    def __hash__(self) -> int:
        return hash((self.content.lower().strip(), self.is_negated))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Proposition):
            return False
        return (
            self.content.lower().strip() == other.content.lower().strip()
            and self.is_negated == other.is_negated
        )

    def negate(self) -> "Proposition":
        """Return negated version"""
        return Proposition(
            content=self.content,
            is_negated=not self.is_negated,
            original_text=f"not({self.original_text})" if self.original_text else ""
        )


@dataclass
class Implication:
    """A logical implication P → Q"""
    antecedent: Proposition  # P
    consequent: Proposition  # Q
    original_text: str = ""


@dataclass
class Assumption:
    """An assumption made during reasoning"""
    proposition: Proposition
    step_number: int
    is_explicit: bool = True
    justification: str = ""


@dataclass
class ConsistencyResult:
    """Result of consistency check"""
    is_consistent: bool
    conflicts: list[tuple[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: str = ""


@dataclass
class InferenceResult:
    """Result of inference validation"""
    is_valid: bool
    rule: InferenceRule
    confidence: float = 1.0
    explanation: str = ""


@dataclass
class CircularReasoningResult:
    """Result of circular reasoning detection"""
    has_circular_reasoning: bool
    cycles: list[list[int]] = field(default_factory=list)
    explanation: str = ""


class LogicValidationService:
    """
    Formal logic validation service

    Provides:
    - Consistency checking between reasoning steps
    - Circular reasoning detection
    - Inference validation
    - Assumption tracking
    """

    def __init__(self) -> None:
        self._propositions: dict[int, list[Proposition]] = defaultdict(list)
        self._implications: dict[int, list[Implication]] = defaultdict(list)
        self._assumptions: list[Assumption] = []
        self._dependency_graph: dict[int, set[int]] = defaultdict(set)

        # Keywords for proposition extraction (Turkish)
        self._implication_keywords = [
            "ise", "olursa", "durumunda", "halinde",
            "neden", "sonuc", "dolayisi", "bu yuzden"
        ]

        self._negation_keywords = [
            "degil", "olmaz", "yoktur", "bulunmaz",
            "asla", "hic", "imkansiz"
        ]

        self._assumption_keywords = [
            "varsayalim", "farz edelim", "kabul edelim",
            "diyelim ki", "tutarsak", "olsun"
        ]

    def extract_propositions(self, text: str) -> list[Proposition]:
        """Extract logical propositions from text"""
        propositions: list[Proposition] = []

        # Split into sentences
        sentences = re.split(r'[.!?]', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check for negation
            is_negated = any(kw in sentence.lower() for kw in self._negation_keywords)

            # Clean the sentence
            content = sentence
            for kw in self._negation_keywords:
                content = re.sub(rf'\b{kw}\b', '', content, flags=re.IGNORECASE)
            content = content.strip()

            if content:
                propositions.append(Proposition(
                    content=content,
                    is_negated=is_negated,
                    original_text=sentence
                ))

        return propositions

    def extract_implications(self, text: str) -> list[Implication]:
        """Extract logical implications from text"""
        implications: list[Implication] = []

        # Pattern: "Eger X ise Y"
        eger_pattern = r"[Ee]ger\s+(.+?)\s+ise\s+(.+?)(?:\.|$)"
        for match in re.finditer(eger_pattern, text):
            antecedent = Proposition(content=match.group(1).strip(), original_text=match.group(0))
            consequent = Proposition(content=match.group(2).strip(), original_text=match.group(0))
            implications.append(Implication(
                antecedent=antecedent,
                consequent=consequent,
                original_text=match.group(0)
            ))

        # Pattern: "X olursa Y"
        olursa_pattern = r"(.+?)\s+olursa\s+(.+?)(?:\.|$)"
        for match in re.finditer(olursa_pattern, text):
            antecedent = Proposition(content=match.group(1).strip(), original_text=match.group(0))
            consequent = Proposition(content=match.group(2).strip(), original_text=match.group(0))
            implications.append(Implication(
                antecedent=antecedent,
                consequent=consequent,
                original_text=match.group(0)
            ))

        # Pattern: "X bu yuzden Y" or "X dolayisiyla Y"
        result_pattern = r"(.+?)\s+(?:bu yuzden|dolayisiyla|sonuc olarak)\s+(.+?)(?:\.|$)"
        for match in re.finditer(result_pattern, text, re.IGNORECASE):
            antecedent = Proposition(content=match.group(1).strip(), original_text=match.group(0))
            consequent = Proposition(content=match.group(2).strip(), original_text=match.group(0))
            implications.append(Implication(
                antecedent=antecedent,
                consequent=consequent,
                original_text=match.group(0)
            ))

        return implications

    async def check_consistency(
        self,
        steps: list[dict],  # List of ReasoningStep-like dicts
    ) -> ConsistencyResult:
        """
        Check logical consistency between reasoning steps

        Args:
            steps: List of reasoning steps with 'description' and 'result' fields

        Returns:
            ConsistencyResult with conflicts and warnings
        """
        conflicts: list[tuple[str, str]] = []
        warnings: list[str] = []
        all_propositions: list[tuple[int, Proposition]] = []

        # Extract propositions from each step
        for step in steps:
            step_num = step.get("step_number", 0)
            text = f"{step.get('description', '')} {step.get('result', '')}"

            props = self.extract_propositions(text)
            for prop in props:
                all_propositions.append((step_num, prop))
                self._propositions[step_num].append(prop)

            # Extract and store implications
            impls = self.extract_implications(text)
            self._implications[step_num].extend(impls)

        # Check for direct contradictions
        for i, (step1, prop1) in enumerate(all_propositions):
            for step2, prop2 in all_propositions[i+1:]:
                # Check if prop2 is negation of prop1
                if prop1.content.lower().strip() == prop2.content.lower().strip():
                    if prop1.is_negated != prop2.is_negated:
                        conflicts.append((
                            f"Adim {step1}: {prop1.original_text}",
                            f"Adim {step2}: {prop2.original_text}"
                        ))

        # Check for implied contradictions through implications
        for step_num, impls in self._implications.items():
            for impl in impls:
                # If we have P and P → Q, but also ¬Q, there's a conflict
                has_antecedent = False
                has_negated_consequent = False

                for _, prop in all_propositions:
                    if prop == impl.antecedent:
                        has_antecedent = True
                    if prop == impl.consequent.negate():
                        has_negated_consequent = True

                if has_antecedent and has_negated_consequent:
                    warnings.append(
                        f"Olasi celiskili cikarim: '{impl.original_text}' ama sonuc negatiflendi"
                    )

        is_consistent = len(conflicts) == 0
        details = ""

        if conflicts:
            details = f"{len(conflicts)} celiskili iddia bulundu."
        elif warnings:
            details = f"Dogrudan celiski yok ama {len(warnings)} uyari var."
        else:
            details = "Tum adimlar tutarli."

        return ConsistencyResult(
            is_consistent=is_consistent,
            conflicts=conflicts,
            warnings=warnings,
            details=details
        )

    async def detect_circular_reasoning(
        self,
        steps: list[dict],
    ) -> CircularReasoningResult:
        """
        Detect circular reasoning in steps

        Circular reasoning occurs when a conclusion is used as a premise
        for reaching that same conclusion.
        """
        cycles: list[list[int]] = []

        # Build dependency graph from implications
        self._dependency_graph.clear()

        for step in steps:
            step_num = step.get("step_number", 0)
            text = f"{step.get('description', '')} {step.get('result', '')}"

            # Check for references to previous steps
            ref_pattern = r"(?:adim|step)\s*(\d+)"
            for match in re.finditer(ref_pattern, text, re.IGNORECASE):
                ref_step = int(match.group(1))
                if ref_step != step_num:
                    self._dependency_graph[step_num].add(ref_step)

            # Check for references to conclusions used as premises
            impls = self.extract_implications(text)
            for impl in impls:
                # Look for the antecedent in previous step conclusions
                for prev_step in steps:
                    if prev_step.get("step_number", 0) >= step_num:
                        continue

                    prev_result = prev_step.get("result", "")
                    if impl.antecedent.content.lower() in prev_result.lower():
                        self._dependency_graph[step_num].add(prev_step["step_number"])

        # Find cycles using DFS
        visited: set[int] = set()
        rec_stack: set[int] = set()

        def find_cycle(node: int, path: list[int]) -> list[int] | None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._dependency_graph.get(node, set()):
                if neighbor not in visited:
                    result = find_cycle(neighbor, path.copy())
                    if result:
                        return result
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            rec_stack.remove(node)
            return None

        for node in self._dependency_graph:
            if node not in visited:
                cycle = find_cycle(node, [])
                if cycle:
                    cycles.append(cycle)

        has_circular = len(cycles) > 0

        if has_circular:
            cycle_strs = [" -> ".join(map(str, c)) for c in cycles]
            explanation = f"Dongusel akil yurutme tespit edildi: {'; '.join(cycle_strs)}"
        else:
            explanation = "Dongusel akil yurutme bulunamadi."

        return CircularReasoningResult(
            has_circular_reasoning=has_circular,
            cycles=cycles,
            explanation=explanation
        )

    async def validate_inference(
        self,
        premise: str,
        conclusion: str,
        rule: InferenceRule | None = None,
    ) -> InferenceResult:
        """
        Validate an inference from premise to conclusion

        Args:
            premise: The premise statement(s)
            conclusion: The conclusion statement
            rule: Optional specific rule to check

        Returns:
            InferenceResult with validity and rule used
        """
        premise_props = self.extract_propositions(premise)
        premise_impls = self.extract_implications(premise)
        conclusion_props = self.extract_propositions(conclusion)

        if not premise_props and not premise_impls:
            return InferenceResult(
                is_valid=False,
                rule=InferenceRule.UNKNOWN,
                confidence=0.0,
                explanation="Onculde mantiksal ifade bulunamadi"
            )

        if not conclusion_props:
            return InferenceResult(
                is_valid=False,
                rule=InferenceRule.UNKNOWN,
                confidence=0.0,
                explanation="Sonucta mantiksal ifade bulunamadi"
            )

        conclusion_prop = conclusion_props[0]
        detected_rule = InferenceRule.UNKNOWN
        is_valid = False
        confidence = 0.5
        explanation = ""

        # Check Modus Ponens: P → Q, P ⊢ Q
        for impl in premise_impls:
            for prop in premise_props:
                if prop == impl.antecedent and conclusion_prop == impl.consequent:
                    detected_rule = InferenceRule.MODUS_PONENS
                    is_valid = True
                    confidence = 0.95
                    explanation = f"Modus Ponens: '{impl.antecedent.content}' ve '{impl.original_text}' => '{conclusion_prop.content}'"
                    break
            if is_valid:
                break

        # Check Modus Tollens: P → Q, ¬Q ⊢ ¬P
        if not is_valid:
            for impl in premise_impls:
                for prop in premise_props:
                    if prop == impl.consequent.negate() and conclusion_prop == impl.antecedent.negate():
                        detected_rule = InferenceRule.MODUS_TOLLENS
                        is_valid = True
                        confidence = 0.95
                        explanation = f"Modus Tollens: '{impl.original_text}' ve '¬{impl.consequent.content}' => '¬{impl.antecedent.content}'"
                        break
                if is_valid:
                    break

        # Check Hypothetical Syllogism: P → Q, Q → R ⊢ P → R
        if not is_valid and len(premise_impls) >= 2:
            for i, impl1 in enumerate(premise_impls):
                for impl2 in premise_impls[i+1:]:
                    if impl1.consequent == impl2.antecedent:
                        # Check if conclusion is P → R
                        conclusion_impls = self.extract_implications(conclusion)
                        for conc_impl in conclusion_impls:
                            if conc_impl.antecedent == impl1.antecedent and conc_impl.consequent == impl2.consequent:
                                detected_rule = InferenceRule.HYPOTHETICAL_SYLLOGISM
                                is_valid = True
                                confidence = 0.9
                                explanation = "Hypothetical Syllogism: P→Q, Q→R ⊢ P→R"
                                break
                    if is_valid:
                        break
                if is_valid:
                    break

        # Check Conjunction: P, Q ⊢ P ∧ Q
        if not is_valid and len(premise_props) >= 2:
            combined_content = " ve ".join(p.content for p in premise_props[:2])
            if combined_content.lower() in conclusion.lower():
                detected_rule = InferenceRule.CONJUNCTION
                is_valid = True
                confidence = 0.85
                explanation = "Conjunction: P, Q ⊢ P ∧ Q"

        # Check Simplification: P ∧ Q ⊢ P
        if not is_valid:
            for prop in premise_props:
                if " ve " in prop.content.lower():
                    parts = prop.content.lower().split(" ve ")
                    for part in parts:
                        if part.strip() in conclusion.lower():
                            detected_rule = InferenceRule.SIMPLIFICATION
                            is_valid = True
                            confidence = 0.85
                            explanation = "Simplification: P ∧ Q ⊢ P"
                            break
                if is_valid:
                    break

        # If specific rule requested, check if it matches
        if rule and rule != InferenceRule.UNKNOWN:
            if detected_rule != rule:
                return InferenceResult(
                    is_valid=False,
                    rule=detected_rule,
                    confidence=0.3,
                    explanation=f"Beklenen kural '{rule.value}' ama tespit edilen '{detected_rule.value}'"
                )

        if not is_valid:
            # Could not validate with formal rules, but might still be valid
            # Use heuristic similarity check
            premise_words = set(premise.lower().split())
            conclusion_words = set(conclusion.lower().split())

            overlap = len(premise_words & conclusion_words)
            if overlap > 3:
                confidence = min(0.7, overlap * 0.1)
                explanation = f"Formal kural tanimlanamadi ama icerik benzerlik var ({overlap} ortak kelime)"
            else:
                confidence = 0.3
                explanation = "Formal mantik kurali ile dogrulanamadi"

        return InferenceResult(
            is_valid=is_valid,
            rule=detected_rule,
            confidence=confidence,
            explanation=explanation
        )

    async def track_assumptions(
        self,
        steps: list[dict],
    ) -> list[Assumption]:
        """
        Track assumptions made during reasoning

        Returns list of assumptions found in steps
        """
        assumptions: list[Assumption] = []

        for step in steps:
            step_num = step.get("step_number", 0)
            text = f"{step.get('description', '')} {step.get('result', '')}"

            # Check for explicit assumption keywords
            for keyword in self._assumption_keywords:
                if keyword in text.lower():
                    # Extract the assumption content
                    pattern = rf"{keyword}\s+(.+?)(?:\.|,|$)"
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        prop = Proposition(
                            content=match.group(1).strip(),
                            original_text=match.group(0)
                        )
                        assumptions.append(Assumption(
                            proposition=prop,
                            step_number=step_num,
                            is_explicit=True,
                            justification=f"Anahtar kelime: {keyword}"
                        ))

            # Check for implicit assumptions (statements without justification)
            props = self.extract_propositions(text)
            for prop in props:
                # Check if this proposition is derived from previous steps
                is_derived = False

                for prev_step in steps:
                    if prev_step.get("step_number", 0) >= step_num:
                        continue

                    prev_text = f"{prev_step.get('description', '')} {prev_step.get('result', '')}"
                    if prop.content.lower() in prev_text.lower():
                        is_derived = True
                        break

                if not is_derived and not any(kw in prop.original_text.lower() for kw in self._assumption_keywords):
                    # This might be an implicit assumption
                    assumptions.append(Assumption(
                        proposition=prop,
                        step_number=step_num,
                        is_explicit=False,
                        justification="Onceki adimlardan turetilmemis"
                    ))

        self._assumptions = assumptions
        return assumptions

    def reset(self) -> None:
        """Reset internal state"""
        self._propositions.clear()
        self._implications.clear()
        self._assumptions.clear()
        self._dependency_graph.clear()


# Singleton instance
_logic_validation_service: LogicValidationService | None = None


def get_logic_validation_service() -> LogicValidationService:
    """Get or create singleton LogicValidationService instance"""
    global _logic_validation_service
    if _logic_validation_service is None:
        _logic_validation_service = LogicValidationService()
    return _logic_validation_service
