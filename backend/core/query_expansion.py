"""
Query Expansion Module
Expand user queries using LLM for better retrieval
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ExpandedQuery:
    """Expanded query result"""

    original: str
    expanded: list[str]
    keywords: list[str]
    synonyms: dict[str, list[str]]


class LLMQueryExpander:
    """
    Query expansion using LLM
    Generates alternative phrasings and related terms
    """

    def __init__(self, llm_service=None):
        """
        Initialize query expander

        Args:
            llm_service: LLM service instance (optional)
        """
        self.llm_service = llm_service
        self._cache = {}

    def expand(
        self, query: str, num_expansions: int = 3, use_cache: bool = True
    ) -> ExpandedQuery:
        """
        Expand query using LLM

        Args:
            query: Original query
            num_expansions: Number of alternative queries to generate
            use_cache: Use cached expansions

        Returns:
            Expanded query with alternatives
        """
        # Check cache
        if use_cache and query in self._cache:
            return self._cache[query]

        try:
            if self.llm_service:
                # Use LLM for expansion
                expanded = self._llm_expand(query, num_expansions)
            else:
                # Fallback to rule-based expansion
                expanded = self._rule_based_expand(query, num_expansions)

            # Cache result
            if use_cache:
                self._cache[query] = expanded

            return expanded

        except Exception as e:
            logger.error(f"Query expansion error: {e}")
            # Return original query
            return ExpandedQuery(
                original=query, expanded=[query], keywords=query.split(), synonyms={}
            )

    def _llm_expand(self, query: str, num_expansions: int) -> ExpandedQuery:
        """Expand query using LLM"""

        prompt = f"""Sen bir eğitim asistanısın. Aşağıdaki soruyu {num_expansions} farklı şekilde yeniden ifade et.
Her versiyon aynı anlamı korumalı ama farklı kelimeler kullanmalı.

Orijinal soru: {query}

Alternatif sorular (her satırda bir tane):"""

        try:
            # Call LLM
            response = self.llm_service.generate(
                prompt=prompt, max_tokens=200, temperature=0.7
            )

            # Parse response
            lines = response.strip().split("\n")
            expanded_queries = []

            for line in lines:
                line = line.strip()
                # Remove numbering
                if line and line[0].isdigit():
                    line = line.split(".", 1)[-1].strip()
                if line and line != query:
                    expanded_queries.append(line)

            # Extract keywords and synonyms
            keywords = self._extract_keywords(query)
            synonyms = self._extract_synonyms(query, expanded_queries)

            return ExpandedQuery(
                original=query,
                expanded=[query] + expanded_queries[:num_expansions],
                keywords=keywords,
                synonyms=synonyms,
            )

        except Exception as e:
            logger.error(f"LLM expansion failed: {e}")
            return self._rule_based_expand(query, num_expansions)

    def _rule_based_expand(self, query: str, num_expansions: int) -> ExpandedQuery:
        """Fallback rule-based expansion for Turkish"""

        # Turkish question patterns
        transformations = {
            "nedir": ["ne demektir", "nedir?", "tanımı", "açıklaması"],
            "nasıl": ["ne şekilde", "hangi yöntemle", "yolu nedir"],
            "neden": ["niçin", "sebebi", "nedeni", "hangi nedenle"],
            "ne zaman": ["hangi zaman", "hangi tarihte"],
            "kim": ["hangi kişi", "kimdir"],
            "nerede": ["hangi yerde", "nerededir"],
        }

        expanded = [query]
        query_lower = query.lower()

        # Apply transformations
        for pattern, alternatives in transformations.items():
            if pattern in query_lower:
                for alt in alternatives[:num_expansions]:
                    new_query = query_lower.replace(pattern, alt)
                    if new_query != query_lower:
                        expanded.append(new_query.capitalize())

        # Add with/without question mark
        if query.endswith("?"):
            expanded.append(query[:-1])
        else:
            expanded.append(query + "?")

        # Extract keywords
        keywords = self._extract_keywords(query)

        return ExpandedQuery(
            original=query,
            expanded=expanded[: num_expansions + 1],
            keywords=keywords,
            synonyms={},
        )

    def _extract_keywords(self, query: str) -> list[str]:
        """Extract important keywords from query"""

        # Turkish stopwords
        stopwords = {
            "bir",
            "bu",
            "şu",
            "ve",
            "veya",
            "için",
            "ile",
            "gibi",
            "kadar",
            "daha",
            "çok",
            "az",
            "de",
            "da",
            "mi",
            "mu",
            "mı",
            "mü",
            "ne",
            "nedir",
            "nasıl",
            "neden",
            "niçin",
            "o",
            "ben",
            "sen",
            "biz",
            "siz",
            "onlar",
            "olan",
            "olarak",
            "ise",
            "ya",
            "ki",
        }

        words = query.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        return keywords

    def _extract_synonyms(
        self, query: str, expanded_queries: list[str]
    ) -> dict[str, list[str]]:
        """Extract potential synonyms from expanded queries"""

        query_words = set(query.lower().split())
        synonyms = {}

        for expanded in expanded_queries:
            expanded_words = set(expanded.lower().split())

            # Find words that appear in expanded but not in original
            new_words = expanded_words - query_words

            for word in new_words:
                if len(word) > 3:  # Skip short words
                    if word not in synonyms:
                        synonyms[word] = []
                    synonyms[word].append(expanded)

        return synonyms


class MultiQueryRetriever:
    """
    Retriever that uses query expansion to retrieve from multiple queries
    """

    def __init__(self, vector_store, expander: LLMQueryExpander):
        """
        Initialize multi-query retriever

        Args:
            vector_store: Vector store to retrieve from
            expander: Query expander instance
        """
        self.vector_store = vector_store
        self.expander = expander

    async def retrieve(
        self,
        query: str,
        k: int = 5,
        num_expansions: int = 3,
        aggregation: str = "ranked_fusion",
    ) -> list[dict[str, Any]]:
        """
        Retrieve using multiple expanded queries

        Args:
            query: Original query
            k: Number of results to retrieve per query
            num_expansions: Number of query expansions
            aggregation: How to combine results (ranked_fusion, unique, merge)

        Returns:
            Aggregated retrieval results
        """
        # Expand query
        expanded_query = self.expander.expand(query, num_expansions)

        # Retrieve for each expanded query
        all_results = []

        for idx, exp_query in enumerate(expanded_query.expanded):
            try:
                # Perform search
                results = self.vector_store.similarity_search_with_score(
                    query=exp_query, k=k
                )

                # Store with source query
                for doc, score in results:
                    all_results.append(
                        {
                            "content": doc.page_content,
                            "text": doc.page_content,
                            "metadata": doc.metadata,
                            "score": score,
                            "source_query": exp_query,
                            "query_rank": idx,
                        }
                    )

            except Exception as e:
                logger.error(f"Error retrieving for query '{exp_query}': {e}")

        # Aggregate results
        if aggregation == "ranked_fusion":
            return self._ranked_fusion(all_results, k)
        if aggregation == "unique":
            return self._unique_results(all_results, k)
        return self._merge_results(all_results, k)

    def _ranked_fusion(
        self, results: list[dict[str, Any]], k: int
    ) -> list[dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF)
        Combines rankings from multiple queries
        """
        # Group by content
        content_scores = {}

        for result in results:
            content = result["content"]

            if content not in content_scores:
                content_scores[content] = {"ranks": [], "scores": [], "result": result}

            content_scores[content]["ranks"].append(result["query_rank"])
            content_scores[content]["scores"].append(result["score"])

        # Calculate RRF scores
        fused = []
        k_rrf = 60  # RRF constant

        for content, data in content_scores.items():
            # RRF formula: sum(1 / (k + rank))
            rrf_score = sum(1.0 / (k_rrf + rank + 1) for rank in data["ranks"])

            result = data["result"].copy()
            result["rrf_score"] = rrf_score
            result["num_occurrences"] = len(data["ranks"])

            fused.append(result)

        # Sort by RRF score
        fused.sort(key=lambda x: x["rrf_score"], reverse=True)

        return fused[:k]

    def _unique_results(
        self, results: list[dict[str, Any]], k: int
    ) -> list[dict[str, Any]]:
        """Return unique results by content"""

        seen = set()
        unique = []

        for result in results:
            content = result["content"]
            if content not in seen:
                seen.add(content)
                unique.append(result)

            if len(unique) >= k:
                break

        return unique

    def _merge_results(
        self, results: list[dict[str, Any]], k: int
    ) -> list[dict[str, Any]]:
        """Simple merge - deduplicate and sort by score"""

        # Group by content
        content_map = {}

        for result in results:
            content = result["content"]

            if content not in content_map or result["score"] > content_map[content]["score"]:
                content_map[content] = result

        # Sort by score
        merged = list(content_map.values())
        merged.sort(key=lambda x: x["score"], reverse=True)

        return merged[:k]


# Global expander instance
_global_expander: LLMQueryExpander | None = None


def get_query_expander(llm_service=None) -> LLMQueryExpander:
    """Get or create global query expander"""
    global _global_expander

    if _global_expander is None:
        _global_expander = LLMQueryExpander(llm_service)

    return _global_expander


# Example usage
"""
from core.query_expansion import get_query_expander, MultiQueryRetriever

# Get expander
expander = get_query_expander(llm_service)

# Expand query
expanded = expander.expand(
    query="Pythagoras teoremi nedir?",
    num_expansions=3
)

print(f"Original: {expanded.original}")
print(f"Expanded: {expanded.expanded}")
print(f"Keywords: {expanded.keywords}")

# Multi-query retrieval
multi_retriever = MultiQueryRetriever(vector_store, expander)

results = await multi_retriever.retrieve(
    query="Pythagoras teoremi nedir?",
    k=5,
    num_expansions=3,
    aggregation="ranked_fusion"
)

for result in results:
    print(f"Score: {result['rrf_score']:.3f}")
    print(f"Content: {result['content'][:100]}...")
"""
