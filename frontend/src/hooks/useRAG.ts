/**
 * React Hook for RAG (Retrieval-Augmented Generation) Features
 * Provides easy access to advanced RAG functionality
 */

import { useState, useCallback } from 'react';

import {
  searchDocuments,
  hybridSearch,
  multiQuerySearch,
  indexDocument,
  indexFile,
  getRAGStats,
  getRAGHealth,
  addEducationalContent,
  searchEducationalContent,
  queryWithContext,
} from '../api';

export interface RAGSearchResult {
  content: string;
  text: string;
  score: number;
  metadata: any;
  original_score?: number;
  rerank_score?: number;
}

export interface RAGStats {
  total_documents: number;
  total_chunks: number;
  cache_size: number;
  cache_hit_ratio: number;
  vector_store_type: string;
  embedding_model: string;
  persist_directory: string;
  status: string;
}

export interface RAGHealth {
  status: string;
  service: string;
  embeddings_loaded: boolean;
  vector_store_loaded: boolean;
}

export function useRAG() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<RAGSearchResult[]>([]);
  const [stats, setStats] = useState<RAGStats | null>(null);
  const [health, setHealth] = useState<RAGHealth | null>(null);

  // Standard semantic search
  const search = useCallback(async (
    query: string,
    options?: {
      k?: number;
      filter?: any;
      score_threshold?: number;
    },
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await searchDocuments({
        query,
        k: options?.k || 5,
        filter: options?.filter,
        score_threshold: options?.score_threshold || 0.5,
      });

      setResults(response.results || []);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Search failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Hybrid search (semantic + keyword)
  const searchHybrid = useCallback(async (
    query: string,
    options?: {
      k?: number;
      alpha?: number; // 0=pure keyword, 1=pure semantic
    },
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await hybridSearch({
        query,
        k: options?.k || 5,
        alpha: options?.alpha || 0.5,
      });

      setResults(response.results || []);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Hybrid search failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Multi-query search with query expansion
  const searchMultiQuery = useCallback(async (
    query: string,
    options?: {
      k?: number;
      num_expansions?: number;
    },
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await multiQuerySearch({
        query,
        k: options?.k || 5,
        num_expansions: options?.num_expansions || 2,
      });

      setResults(response.results || []);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Multi-query search failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Search educational content
  const searchEducational = useCallback(async (
    query: string,
    options?: {
      subject?: string;
      grade?: number;
      exam_type?: string;
      content_type?: string;
      k?: number;
    },
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await searchEducationalContent({
        query,
        subject: options?.subject,
        grade: options?.grade,
        exam_type: options?.exam_type,
        content_type: options?.content_type,
        k: options?.k || 5,
      });

      setResults(response.results || []);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Educational search failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Query with context for RAG
  const queryContext = useCallback(async (
    query: string,
    options?: {
      context_size?: number;
      prompt_template?: string;
    },
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await queryWithContext({
        query,
        context_size: options?.context_size || 3,
        prompt_template: options?.prompt_template,
      });

      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Query with context failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Index text document
  const indexText = useCallback(async (
    content: string,
    metadata?: any,
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await indexDocument({
        content,
        metadata,
      });

      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Index failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Index file
  const indexFileDocument = useCallback(async (
    file: File,
    metadata?: any,
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await indexFile(file, metadata);

      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'File index failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Add educational content
  const addEducational = useCallback(async (
    content: string,
    contentType: string,
    metadata?: any,
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await addEducationalContent({
        content_type: contentType,
        content,
        metadata,
      });

      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Add educational content failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get RAG statistics
  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await getRAGStats();
      setStats(response.stats);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch stats';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Check RAG health
  const checkHealth = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await getRAGHealth();
      setHealth(response);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Health check failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Clear results
  const clearResults = useCallback(() => {
    setResults([]);
    setError(null);
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    // State
    loading,
    error,
    results,
    stats,
    health,

    // Search methods
    search,
    searchHybrid,
    searchMultiQuery,
    searchEducational,
    queryContext,

    // Index methods
    indexText,
    indexFileDocument,
    addEducational,

    // Utility methods
    fetchStats,
    checkHealth,
    clearResults,
    clearError,
  };
}

export default useRAG;
