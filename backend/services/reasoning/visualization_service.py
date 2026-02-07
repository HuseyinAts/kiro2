"""
KIRO2 Reasoning Visualization Service
Mermaid diagram üretimi için servis (REQ-6.2)

Thought tree visualization, critical path highlighting,
ve interactive exploration için altyapı sağlar.
"""

import logging
from dataclasses import dataclass, field
from typing import Any
from enum import Enum

logger = logging.getLogger(__name__)


class NodeStyle(str, Enum):
    """Mermaid node stilleri."""
    DEFAULT = "default"
    CRITICAL = "critical"        # Critical path
    VERIFIED = "verified"        # Math verified
    ERROR = "error"              # Verification failed
    FINAL = "final"              # Final answer
    START = "start"              # Starting node


@dataclass
class ThoughtNode:
    """Düşünce ağacı node'u."""
    id: str
    label: str
    step_number: int
    step_type: str
    confidence: float = 1.0
    is_verified: bool = False
    is_critical: bool = False
    children: list[str] = field(default_factory=list)
    parent: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MermaidDiagram:
    """Mermaid diagram çıktısı."""
    code: str
    node_count: int
    edge_count: int
    critical_path: list[str]
    has_branches: bool
    metadata: dict[str, Any] = field(default_factory=dict)


class VisualizationService:
    """
    Reasoning visualization servisi.

    Mermaid flowchart formatında thought tree oluşturur.

    Kullanım:
        svc = VisualizationService()
        diagram = svc.generate_thought_tree(steps)
        print(diagram.code)
    """

    # Node style mappings
    STYLE_COLORS = {
        NodeStyle.DEFAULT: "#e3f2fd",      # Light blue
        NodeStyle.CRITICAL: "#fff3e0",      # Light orange
        NodeStyle.VERIFIED: "#e8f5e9",      # Light green
        NodeStyle.ERROR: "#ffebee",         # Light red
        NodeStyle.FINAL: "#90EE90",         # Green
        NodeStyle.START: "#bbdefb",         # Blue
    }

    # Step type icons (Türkçe)
    STEP_TYPE_ICONS = {
        "understanding": "📖",
        "decomposition": "🔀",
        "inference": "💭",
        "calculation": "🔢",
        "verification": "✅",
        "synthesis": "🎯",
        "hypothesis": "❓",
        "observation": "👁️",
    }

    def __init__(self):
        """Initialize visualization service."""
        pass

    def generate_thought_tree(
        self,
        steps: list[dict[str, Any]],
        show_confidence: bool = True,
        highlight_critical_path: bool = True,
        orientation: str = "TD",  # TD=top-down, LR=left-right
    ) -> MermaidDiagram:
        """
        Reasoning adımlarından Mermaid flowchart oluştur.

        Args:
            steps: Reasoning step listesi
            show_confidence: Confidence değerlerini göster
            highlight_critical_path: Critical path'i vurgula
            orientation: Diagram yönü (TD veya LR)

        Returns:
            MermaidDiagram object
        """
        if not steps:
            return MermaidDiagram(
                code="graph TD\n    A[Adım yok]",
                node_count=1,
                edge_count=0,
                critical_path=[],
                has_branches=False,
            )

        # Build thought tree
        nodes = self._build_nodes(steps)
        edges = self._build_edges(nodes)
        critical_path = self._find_critical_path(nodes) if highlight_critical_path else []

        # Generate Mermaid code
        mermaid_lines = [f"graph {orientation}"]

        # Add nodes
        for node in nodes:
            node_def = self._node_to_mermaid(node, show_confidence)
            mermaid_lines.append(f"    {node_def}")

        # Add edges
        for source, target in edges:
            mermaid_lines.append(f"    {source} --> {target}")

        # Add styles
        style_lines = self._generate_styles(nodes, critical_path)
        mermaid_lines.extend(style_lines)

        return MermaidDiagram(
            code="\n".join(mermaid_lines),
            node_count=len(nodes),
            edge_count=len(edges),
            critical_path=critical_path,
            has_branches=self._has_branches(nodes),
            metadata={
                "orientation": orientation,
                "show_confidence": show_confidence,
                "total_steps": len(steps),
            }
        )

    def _build_nodes(self, steps: list[dict[str, Any]]) -> list[ThoughtNode]:
        """Reasoning step'lerden ThoughtNode listesi oluştur."""
        nodes = []

        for i, step in enumerate(steps):
            node_id = f"S{i + 1}"
            step_type = step.get("step_type", "inference")
            icon = self.STEP_TYPE_ICONS.get(step_type, "💭")

            # Create label
            description = step.get("description", f"Adım {i + 1}")
            # Truncate long descriptions
            if len(description) > 50:
                description = description[:47] + "..."

            label = f"{icon} {description}"

            node = ThoughtNode(
                id=node_id,
                label=label,
                step_number=step.get("step_number", i + 1),
                step_type=step_type,
                confidence=step.get("confidence", 1.0),
                is_verified=step.get("is_verified", False),
                parent=f"S{i}" if i > 0 else None,
                metadata={
                    "result": step.get("result"),
                    "reasoning": step.get("reasoning"),
                }
            )

            # Add parent reference
            if i > 0:
                nodes[i - 1].children.append(node_id)

            nodes.append(node)

        return nodes

    def _build_edges(self, nodes: list[ThoughtNode]) -> list[tuple[str, str]]:
        """Node'lar arasındaki edge'leri oluştur."""
        edges = []

        for node in nodes:
            for child_id in node.children:
                edges.append((node.id, child_id))

        return edges

    def _node_to_mermaid(self, node: ThoughtNode, show_confidence: bool) -> str:
        """ThoughtNode'u Mermaid syntax'ına çevir."""
        # Escape special characters in label
        label = node.label.replace('"', "'").replace("\n", " ")

        # Add confidence if requested
        if show_confidence and node.confidence < 1.0:
            label = f"{label} ({node.confidence:.0%})"

        # Determine node shape based on step type
        if node.step_type == "understanding":
            return f'{node.id}["{label}"]'  # Rectangle
        elif node.step_type == "verification":
            return f'{node.id}{{"{label}"}}'  # Diamond
        elif node.step_type == "synthesis":
            return f'{node.id}(["{label}"])'  # Stadium
        else:
            return f'{node.id}["{label}"]'  # Default rectangle

    def _find_critical_path(self, nodes: list[ThoughtNode]) -> list[str]:
        """
        Critical path'i bul (ana reasoning line).

        En yüksek confidence'a sahip path.
        """
        if not nodes:
            return []

        # For linear trees, all nodes are on critical path
        path = [node.id for node in nodes]
        return path

    def _has_branches(self, nodes: list[ThoughtNode]) -> bool:
        """Tree'de branch var mı kontrol et."""
        for node in nodes:
            if len(node.children) > 1:
                return True
        return False

    def _generate_styles(
        self,
        nodes: list[ThoughtNode],
        critical_path: list[str],
    ) -> list[str]:
        """Mermaid style tanımları oluştur."""
        styles = []

        for node in nodes:
            style_class = self._get_node_style(node, critical_path)
            color = self.STYLE_COLORS.get(style_class, self.STYLE_COLORS[NodeStyle.DEFAULT])
            styles.append(f"    style {node.id} fill:{color}")

        return styles

    def _get_node_style(self, node: ThoughtNode, critical_path: list[str]) -> NodeStyle:
        """Node için uygun style belirle."""
        if node.step_type == "synthesis":
            return NodeStyle.FINAL
        if node.is_verified:
            return NodeStyle.VERIFIED
        if node.step_number == 1:
            return NodeStyle.START
        if node.id in critical_path:
            return NodeStyle.CRITICAL
        return NodeStyle.DEFAULT

    def generate_subproblem_tree(
        self,
        sub_problems: list[dict[str, Any]],
        orientation: str = "TD",
    ) -> MermaidDiagram:
        """
        Sub-problem decomposition'dan Mermaid diagram oluştur.

        Args:
            sub_problems: Sub-problem listesi
            orientation: Diagram yönü

        Returns:
            MermaidDiagram object
        """
        if not sub_problems:
            return MermaidDiagram(
                code="graph TD\n    A[Alt problem yok]",
                node_count=1,
                edge_count=0,
                critical_path=[],
                has_branches=False,
            )

        mermaid_lines = [f"graph {orientation}"]
        edges = []

        # Root node
        mermaid_lines.append('    ROOT["🎯 Ana Problem"]')

        # Add sub-problems
        for i, sp in enumerate(sub_problems):
            node_id = f"SP{i + 1}"
            description = sp.get("description", f"Alt Problem {i + 1}")
            if len(description) > 40:
                description = description[:37] + "..."

            mermaid_lines.append(f'    {node_id}["{description}"]')

            # Add edge from root
            edges.append(("ROOT", node_id))

            # Add dependency edges
            dependencies = sp.get("dependencies", [])
            for dep_idx in dependencies:
                if isinstance(dep_idx, int) and 0 <= dep_idx < len(sub_problems):
                    edges.append((f"SP{dep_idx + 1}", node_id))

        # Add edges
        for source, target in edges:
            mermaid_lines.append(f"    {source} --> {target}")

        # Add styles
        mermaid_lines.append("    style ROOT fill:#bbdefb")
        for i in range(len(sub_problems)):
            mermaid_lines.append(f"    style SP{i + 1} fill:#e3f2fd")

        return MermaidDiagram(
            code="\n".join(mermaid_lines),
            node_count=len(sub_problems) + 1,
            edge_count=len(edges),
            critical_path=[],
            has_branches=len(sub_problems) > 1,
            metadata={"type": "subproblem_tree"}
        )

    def steps_to_json_tree(
        self,
        steps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Reasoning steps'i JSON tree formatına çevir.

        Frontend interactivity için kullanılır.

        Args:
            steps: Reasoning step listesi

        Returns:
            JSON tree structure
        """
        if not steps:
            return {"nodes": [], "edges": [], "metadata": {}}

        nodes = []
        edges = []

        for i, step in enumerate(steps):
            node = {
                "id": f"step_{i + 1}",
                "step_number": step.get("step_number", i + 1),
                "step_type": step.get("step_type", "inference"),
                "description": step.get("description", ""),
                "reasoning": step.get("reasoning", ""),
                "result": step.get("result"),
                "confidence": step.get("confidence", 1.0),
                "is_verified": step.get("is_verified", False),
            }
            nodes.append(node)

            if i > 0:
                edges.append({
                    "source": f"step_{i}",
                    "target": f"step_{i + 1}",
                    "type": "sequence"
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_steps": len(steps),
                "has_verification": any(s.get("is_verified") for s in steps),
            }
        }


# Singleton instance
_visualization_service: VisualizationService | None = None


def get_visualization_service() -> VisualizationService:
    """Get singleton VisualizationService instance."""
    global _visualization_service
    if _visualization_service is None:
        _visualization_service = VisualizationService()
    return _visualization_service
