import { useState, useEffect, useCallback } from 'react';
import chatService from '../services/chatService';
import learningPathService from '../services/learningPathService';
import ragService from '../services/ragService';
import monitoringService from '../services/monitoringService';
import { getAgents } from '../api';

export interface Agent {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export function useApiIntegration() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [healthStatus, setHealthStatus] = useState<any>(null);

  // Load agents on mount
  useEffect(() => {
    loadAgents();
    startMonitoring();
    
    return () => {
      monitoringService.stopMonitoring();
    };
  }, []);

  const loadAgents = async () => {
    try {
      setIsLoading(true);
      const response = await getAgents();
      setAgents(response.agents || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agents');
    } finally {
      setIsLoading(false);
    }
  };

  const startMonitoring = () => {
    monitoringService.startMonitoring({
      healthInterval: 30000,
      onHealthChange: (status) => {
        setHealthStatus(status);
      },
    });
  };

  // Chat functions
  const sendMessage = useCallback(async (agentId: string, message: string) => {
    try {
      setIsLoading(true);
      const response = await chatService.sendMessage(agentId, message);
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const connectWebSocket = useCallback(() => {
    chatService.connectWebSocket();
  }, []);

  const disconnectWebSocket = useCallback(() => {
    chatService.disconnectWebSocket();
  }, []);

  // Learning Path functions
  const createStudentProfile = useCallback(async (profileData: any) => {
    try {
      setIsLoading(true);
      const profile = await learningPathService.createProfile(profileData);
      return profile;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create profile');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const generateLearningPath = useCallback(async (topic: string, weeks?: number) => {
    try {
      setIsLoading(true);
      const path = await learningPathService.generateLearningPath(topic, weeks);
      return path;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate learning path');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const searchResources = useCallback(async (topic: string, options?: any) => {
    try {
      setIsLoading(true);
      const resources = await learningPathService.findResources(topic, options);
      return resources;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search resources');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // RAG functions
  const addDocument = useCallback(async (content: string, metadata?: any) => {
    try {
      setIsLoading(true);
      const result = await ragService.addDocument({ content, metadata });
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add document');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const searchDocuments = useCallback(async (query: string, options?: any) => {
    try {
      setIsLoading(true);
      const results = await ragService.search(query, options);
      return results;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search documents');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const askWithContext = useCallback(async (query: string) => {
    try {
      setIsLoading(true);
      const answer = await ragService.askWithContext(query);
      return answer;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get answer');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Clear functions
  const clearChat = useCallback(async () => {
    try {
      await chatService.clearAllSessions();
      chatService.clearMessages();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clear chat');
    }
  }, []);

  const clearLearningData = useCallback(() => {
    learningPathService.clearData();
  }, []);

  const clearRAGDatabase = useCallback(async () => {
    try {
      await ragService.clearDatabase();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clear RAG database');
    }
  }, []);

  return {
    // State
    agents,
    isLoading,
    error,
    healthStatus,
    
    // Chat
    sendMessage,
    connectWebSocket,
    disconnectWebSocket,
    
    // Learning Path
    createStudentProfile,
    generateLearningPath,
    searchResources,
    
    // RAG
    addDocument,
    searchDocuments,
    askWithContext,
    
    // Clear functions
    clearChat,
    clearLearningData,
    clearRAGDatabase,
    
    // Utilities
    setError,
    reload: loadAgents,
  };
}