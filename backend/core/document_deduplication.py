"""
Document Deduplication Module
Detect and handle duplicate or near-duplicate documents
"""

import hashlib
import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DuplicateGroup:
    """Group of duplicate documents"""

    canonical: str  # The document to keep
    duplicates: list[str]  # Similar documents
    similarity: float  # Average similarity
    method: str  # Detection method used


class DocumentDeduplicator:
    """
    Document deduplication using multiple strategies
    - Exact hash matching
    - Fuzzy text similarity
    - Embedding similarity
    """

    def __init__(
        self,
        exact_threshold: float = 1.0,
        fuzzy_threshold: float = 0.95,
        embedding_threshold: float = 0.98,
    ):
        """
        Initialize deduplicator

        Args:
            exact_threshold: Threshold for exact matches (1.0)
            fuzzy_threshold: Threshold for fuzzy text similarity (0-1)
            embedding_threshold: Threshold for embedding similarity (0-1)
        """
        self.exact_threshold = exact_threshold
        self.fuzzy_threshold = fuzzy_threshold
        self.embedding_threshold = embedding_threshold

        # Caches
        self._hash_cache: dict[str, str] = {}
        self._embedding_cache: dict[str, np.ndarray] = {}

    def find_duplicates(
        self, documents: list[dict[str, Any]], method: str = "all"
    ) -> list[DuplicateGroup]:
        """
        Find duplicate documents

        Args:
            documents: List of documents with 'content' or 'text' field
            method: Detection method (exact, fuzzy, embedding, all)

        Returns:
            List of duplicate groups
        """
        duplicate_groups = []

        if method in ("exact", "all"):
            exact_dupes = self._find_exact_duplicates(documents)
            duplicate_groups.extend(exact_dupes)

        if method in ("fuzzy", "all"):
            fuzzy_dupes = self._find_fuzzy_duplicates(documents)
            duplicate_groups.extend(fuzzy_dupes)

        if method in ("embedding", "all"):
            embedding_dupes = self._find_embedding_duplicates(documents)
            duplicate_groups.extend(embedding_dupes)

        return duplicate_groups

    def _find_exact_duplicates(
        self, documents: list[dict[str, Any]]
    ) -> list[DuplicateGroup]:
        """Find exact duplicates using hash"""

        hash_map: dict[str, list[int]] = {}

        for idx, doc in enumerate(documents):
            content = doc.get("content") or doc.get("text", "")
            doc_hash = self._hash_content(content)

            if doc_hash not in hash_map:
                hash_map[doc_hash] = []
            hash_map[doc_hash].append(idx)

        # Build duplicate groups
        groups = []
        for doc_hash, indices in hash_map.items():
            if len(indices) > 1:
                canonical_idx = indices[0]
                canonical = documents[canonical_idx].get("content") or documents[
                    canonical_idx
                ].get("text", "")

                duplicates = [
                    documents[i].get("content") or documents[i].get("text", "")
                    for i in indices[1:]
                ]

                groups.append(
                    DuplicateGroup(
                        canonical=canonical,
                        duplicates=duplicates,
                        similarity=1.0,
                        method="exact_hash",
                    )
                )

        logger.info(f"Found {len(groups)} exact duplicate groups")
        return groups

    def _find_fuzzy_duplicates(
        self, documents: list[dict[str, Any]]
    ) -> list[DuplicateGroup]:
        """Find near-duplicates using Jaccard similarity"""

        groups = []
        processed: set[int] = set()

        for i, doc1 in enumerate(documents):
            if i in processed:
                continue

            content1 = doc1.get("content") or doc1.get("text", "")
            tokens1 = self._tokenize(content1)

            duplicates = []

            for j, doc2 in enumerate(documents[i + 1 :], start=i + 1):
                if j in processed:
                    continue

                content2 = doc2.get("content") or doc2.get("text", "")
                tokens2 = self._tokenize(content2)

                similarity = self._jaccard_similarity(tokens1, tokens2)

                if similarity >= self.fuzzy_threshold:
                    duplicates.append(content2)
                    processed.add(j)

            if duplicates:
                groups.append(
                    DuplicateGroup(
                        canonical=content1,
                        duplicates=duplicates,
                        similarity=self.fuzzy_threshold,
                        method="fuzzy_jaccard",
                    )
                )
                processed.add(i)

        logger.info(f"Found {len(groups)} fuzzy duplicate groups")
        return groups

    def _find_embedding_duplicates(
        self, documents: list[dict[str, Any]]
    ) -> list[DuplicateGroup]:
        """
        Find semantic duplicates using embedding similarity.

        Spec: REQ-5 Duplicate Detection
        - threshold > 0.95 = duplicate
        - 0.90-0.95 = near-duplicate (flagged)
        - Paraphrase detection via semantic similarity
        """
        groups = []
        processed: set[int] = set()

        # Try to get embeddings from documents or generate them
        embeddings: list[np.ndarray | None] = []
        for doc in documents:
            # Check if embedding is already in document
            if "embedding" in doc:
                emb = doc["embedding"]
                if isinstance(emb, list):
                    emb = np.array(emb)
                embeddings.append(emb)
            elif doc.get("id") and doc["id"] in self._embedding_cache:
                embeddings.append(self._embedding_cache[doc["id"]])
            else:
                embeddings.append(None)

        # Check if we have any embeddings to work with
        valid_embeddings = [e for e in embeddings if e is not None]
        if not valid_embeddings:
            logger.info("No embeddings available for semantic deduplication")
            return []

        # Find duplicates using cosine similarity
        for i, emb1 in enumerate(embeddings):
            if i in processed or emb1 is None:
                continue

            content1 = documents[i].get("content") or documents[i].get("text", "")
            duplicates = []
            similarities = []

            for j, emb2 in enumerate(embeddings[i + 1:], start=i + 1):
                if j in processed or emb2 is None:
                    continue

                # Calculate cosine similarity
                similarity = self._cosine_similarity(emb1, emb2)

                if similarity >= self.embedding_threshold:
                    # Exact semantic duplicate (>= 0.98)
                    content2 = documents[j].get("content") or documents[j].get("text", "")
                    duplicates.append(content2)
                    similarities.append(similarity)
                    processed.add(j)
                elif similarity >= 0.90:
                    # Near-duplicate - log but don't add to group
                    content2 = documents[j].get("content") or documents[j].get("text", "")
                    logger.info(
                        f"Near-duplicate detected (similarity={similarity:.3f}): "
                        f"'{content1[:50]}...' ~ '{content2[:50]}...'"
                    )

            if duplicates:
                avg_similarity = sum(similarities) / len(similarities)
                groups.append(
                    DuplicateGroup(
                        canonical=content1,
                        duplicates=duplicates,
                        similarity=avg_similarity,
                        method="embedding_semantic",
                    )
                )
                processed.add(i)

        logger.info(f"Found {len(groups)} embedding-based duplicate groups")
        return groups

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        if vec1 is None or vec2 is None:
            return 0.0

        # Normalize vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def add_embedding(self, doc_id: str, embedding: np.ndarray) -> None:
        """Add embedding to cache for a document"""
        self._embedding_cache[doc_id] = embedding

    def check_duplicate_by_embedding(
        self,
        embedding: np.ndarray,
        threshold: float | None = None,
    ) -> tuple[bool, str | None, float]:
        """
        Check if an embedding is duplicate against cached embeddings.

        Args:
            embedding: The embedding to check
            threshold: Similarity threshold (default: self.embedding_threshold)

        Returns:
            (is_duplicate, matching_doc_id, similarity_score)
        """
        threshold = threshold or self.embedding_threshold

        for doc_id, cached_emb in self._embedding_cache.items():
            similarity = self._cosine_similarity(embedding, cached_emb)
            if similarity >= threshold:
                return True, doc_id, similarity

        return False, None, 0.0

    def merge_metadata(
        self,
        canonical_metadata: dict[str, Any],
        duplicate_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Merge metadata from duplicate document into canonical.

        Spec: REQ-5.6 Metadata merge for duplicates
        """
        merged = canonical_metadata.copy()

        for key, value in duplicate_metadata.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(merged[key], list) and isinstance(value, list):
                # Merge lists
                merged[key] = list(set(merged[key] + value))
            elif key in ("view_count", "usage_count"):
                # Sum numeric counts
                merged[key] = merged.get(key, 0) + value

        return merged

    def _hash_content(self, content: str) -> str:
        """Generate hash for content"""

        # Normalize content
        normalized = content.strip().lower()

        # Remove extra whitespace
        normalized = " ".join(normalized.split())

        # Generate hash
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _tokenize(self, text: str) -> set[str]:
        """Tokenize text into words"""

        # Simple word tokenization
        words = text.lower().split()

        # Remove very short words
        words = [w for w in words if len(w) > 2]

        return set(words)

    def _jaccard_similarity(self, set1: set[str], set2: set[str]) -> float:
        """Calculate Jaccard similarity between two sets"""

        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def deduplicate(
        self, documents: list[dict[str, Any]], method: str = "all", keep: str = "first"
    ) -> list[dict[str, Any]]:
        """
        Remove duplicates from documents

        Args:
            documents: List of documents
            method: Detection method
            keep: Which duplicate to keep (first, last, longest, shortest)

        Returns:
            Deduplicated document list
        """

        # Find duplicates
        duplicate_groups = self.find_duplicates(documents, method)

        # Build set of duplicate contents to remove
        to_remove: set[str] = set()

        for group in duplicate_groups:
            if keep == "first":
                # Remove all duplicates (keep canonical)
                to_remove.update(group.duplicates)

            elif keep == "longest":
                # Keep the longest document
                all_docs = [group.canonical] + group.duplicates
                all_docs.sort(key=len, reverse=True)
                to_remove.update(all_docs[1:])

            elif keep == "shortest":
                # Keep the shortest document
                all_docs = [group.canonical] + group.duplicates
                all_docs.sort(key=len)
                to_remove.update(all_docs[1:])

        # Filter documents
        deduplicated = []
        for doc in documents:
            content = doc.get("content") or doc.get("text", "")
            if content not in to_remove:
                deduplicated.append(doc)

        logger.info(
            f"Deduplicated {len(documents)} -> {len(deduplicated)} documents "
            f"(removed {len(documents) - len(deduplicated)})"
        )

        return deduplicated


class IncrementalDeduplicator:
    """
    Incremental deduplication for real-time use
    Checks new documents against existing ones
    """

    def __init__(self, threshold: float = 0.95):
        """
        Initialize incremental deduplicator

        Args:
            threshold: Similarity threshold for duplicates
        """
        self.threshold = threshold
        self._seen_hashes: set[str] = set()
        self._seen_tokens: list[set[str]] = []
        self._seen_contents: list[str] = []

    def is_duplicate(
        self, content: str, method: str = "hash"
    ) -> tuple[bool, str | None]:
        """
        Check if content is duplicate

        Args:
            content: Content to check
            method: Detection method (hash, fuzzy)

        Returns:
            (is_duplicate, original_content)
        """

        if method == "hash":
            # Exact hash matching
            content_hash = self._hash_content(content)

            if content_hash in self._seen_hashes:
                # Find original content
                idx = list(self._seen_hashes).index(content_hash)
                return (
                    True,
                    self._seen_contents[idx]
                    if idx < len(self._seen_contents)
                    else None,
                )

            # Not duplicate - add to seen
            self._seen_hashes.add(content_hash)
            self._seen_contents.append(content)
            return False, None

        if method == "fuzzy":
            # Fuzzy matching
            tokens = self._tokenize(content)

            for idx, seen_tokens in enumerate(self._seen_tokens):
                similarity = self._jaccard_similarity(tokens, seen_tokens)

                if similarity >= self.threshold:
                    return True, self._seen_contents[idx]

            # Not duplicate - add to seen
            self._seen_tokens.append(tokens)
            self._seen_contents.append(content)
            return False, None

        return False, None

    def add_document(self, content: str):
        """Add document to seen set"""
        content_hash = self._hash_content(content)
        self._seen_hashes.add(content_hash)
        self._seen_tokens.append(self._tokenize(content))
        self._seen_contents.append(content)

    def clear(self):
        """Clear all seen documents"""
        self._seen_hashes.clear()
        self._seen_tokens.clear()
        self._seen_contents.clear()

    def _hash_content(self, content: str) -> str:
        """Generate normalized hash"""
        normalized = content.strip().lower()
        normalized = " ".join(normalized.split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _tokenize(self, text: str) -> set[str]:
        """Tokenize text"""
        words = text.lower().split()
        return {w for w in words if len(w) > 2}

    def _jaccard_similarity(self, set1: set[str], set2: set[str]) -> float:
        """Jaccard similarity"""
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0


# Global deduplicator instance
_global_deduplicator: IncrementalDeduplicator | None = None


def get_deduplicator() -> IncrementalDeduplicator:
    """Get or create global deduplicator"""
    global _global_deduplicator

    if _global_deduplicator is None:
        _global_deduplicator = IncrementalDeduplicator()

    return _global_deduplicator


# Example usage
"""
from core.document_deduplication import DocumentDeduplicator, get_deduplicator

# Batch deduplication
deduplicator = DocumentDeduplicator()

documents = [
    {"content": "Python programlama dili"},
    {"content": "Python programlama dili"},  # Exact duplicate
    {"content": "Python programlama dilidir"},  # Near duplicate
]

# Find duplicates
groups = deduplicator.find_duplicates(documents, method="all")

# Remove duplicates
clean_docs = deduplicator.deduplicate(documents, keep="first")

# Incremental deduplication
inc_dedup = get_deduplicator()

is_dup, original = inc_dedup.is_duplicate("Python programlama dili")
if is_dup:
    print(f"Duplicate of: {original}")
"""
