import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from services.knowledge_graph_service import KnowledgeGraphService

kg = KnowledgeGraphService()
print(f"Total nodes: {len(kg.graph.nodes())}")
print(f"Total edges: {len(kg.graph.edges())}")

nodes = list(kg.graph.nodes())
prod_nodes = [n for n in nodes if n.startswith('PROD_')]
test_nodes = [n for n in nodes if n.startswith('TEST_')]
claude_nodes = [n for n in nodes if n.startswith('CLAUDE')]

print(f"\nPROD_ nodes: {len(prod_nodes)}")
print(f"TEST_ nodes: {len(test_nodes)}")
print(f"CLAUDE nodes: {len(claude_nodes)}")

if prod_nodes:
    print(f"\nPROD examples: {prod_nodes[:5]}")
