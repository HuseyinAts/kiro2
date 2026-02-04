import {
  addDocument,
  addEducationalContent,
  searchDocuments,
  searchEducationalContent,
  queryWithContext,
  clearRAGDatabase,
} from '../api';

export interface Document {
  content: string;
  metadata?: {
    title?: string;
    subject?: string;
    grade?: number;
    tags?: string[];
    [key: string]: any;
  };
}

export interface EducationalContent {
  content_type: 'lesson' | 'exercise' | 'solution' | 'exam' | 'summary';
  content: string;
  metadata?: {
    subject?: string;
    grade?: number;
    topic?: string;
    difficulty?: string;
    [key: string]: any;
  };
}

export interface SearchResult {
  content: string;
  metadata: any;
  score: number;
}

class RAGService {
  private cache: Map<string, any> = new Map();

  async addDocument(document: Document) {
    try {
      const response = await addDocument(document);
      if (response.success) {
        this.clearCache();
        return response;
      }
      throw new Error(response.error || 'Failed to add document');
    } catch (error) {
      console.error('Error adding document:', error);
      throw error;
    }
  }

  async addEducationalMaterial(content: EducationalContent) {
    try {
      const response = await addEducationalContent(content);
      if (response.success) {
        this.clearCache();
        return response;
      }
      throw new Error(response.error || 'Failed to add educational content');
    } catch (error) {
      console.error('Error adding educational content:', error);
      throw error;
    }
  }

  async search(query: string, options?: {
    k?: number;
    filter?: any;
    scoreThreshold?: number;
  }) {
    const cacheKey = `search:${query}:${JSON.stringify(options || {})}`;
    
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }

    try {
      const response = await searchDocuments({
        query,
        k: options?.k,
        filter: options?.filter,
        score_threshold: options?.scoreThreshold,
      });

      if (response.success) {
        this.cache.set(cacheKey, response.results);
        return response.results as SearchResult[];
      }
      throw new Error(response.error || 'Failed to search documents');
    } catch (error) {
      console.error('Error searching documents:', error);
      throw error;
    }
  }

  async searchEducational(query: string, options?: {
    subject?: string;
    grade?: number;
    examType?: string;
    contentType?: string;
    k?: number;
  }) {
    const cacheKey = `searchEdu:${query}:${JSON.stringify(options || {})}`;
    
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }

    try {
      const response = await searchEducationalContent({
        query,
        subject: options?.subject,
        grade: options?.grade,
        exam_type: options?.examType,
        content_type: options?.contentType,
        k: options?.k,
      });

      if (response.success) {
        this.cache.set(cacheKey, response.results);
        return response.results as SearchResult[];
      }
      throw new Error(response.error || 'Failed to search educational content');
    } catch (error) {
      console.error('Error searching educational content:', error);
      throw error;
    }
  }

  async askWithContext(query: string, options?: {
    contextSize?: number;
    promptTemplate?: string;
  }) {
    try {
      const response = await queryWithContext({
        query,
        context_size: options?.contextSize,
        prompt_template: options?.promptTemplate,
      });

      if (response.success) {
        return {
          answer: response.response,
          context: response.context,
          sources: response.relevant_docs,
        };
      }
      throw new Error(response.error || 'Failed to query with context');
    } catch (error) {
      console.error('Error querying with context:', error);
      throw error;
    }
  }

  async clearDatabase() {
    try {
      const response = await clearRAGDatabase();
      if (response.success) {
        this.clearCache();
        return true;
      }
      throw new Error(response.error || 'Failed to clear database');
    } catch (error) {
      console.error('Error clearing RAG database:', error);
      throw error;
    }
  }

  clearCache() {
    this.cache.clear();
  }

  async bulkAddDocuments(documents: Document[]) {
    const results = [];
    const errors = [];

    for (const doc of documents) {
      try {
        const result = await this.addDocument(doc);
        results.push(result);
      } catch (error) {
        errors.push({ document: doc, error });
      }
    }

    return {
      successful: results,
      failed: errors,
      total: documents.length,
      successCount: results.length,
      failureCount: errors.length,
    };
  }
}

export default new RAGService();