/**
 * useLearningPath Hook
 *
 * Custom hook for managing learning path data and state
 * Extracted from LearningPathPage.tsx
 */

import { useState, useEffect, useCallback } from 'react';

import { detectLearningStyle } from '../api';
import { PathNodeData } from '../components/LearningPath/PathNode';
import config from '../config';
import learningPathService from '../services/learningPathService';
import { convertPathToNodes } from '../utils/learningPathHelpers';

export interface ProgressUpdate {
  nodeId: string
  progress?: number  // 0-100
  completed?: boolean
}

export interface UseLearningPathReturn {
  // Data
  pathNodes: PathNodeData[]
  learningStyle: string
  currentNodeId: string

  // State
  loading: boolean
  error: string | null

  // Actions
  loadPath: () => Promise<void>
  reload: () => void
  setCurrentNode: (nodeId: string) => void
  updateProgress: (update: ProgressUpdate) => Promise<boolean>
  markNodeComplete: (nodeId: string) => Promise<boolean>
}

/**
 * Hook for managing learning path data
 *
 * @returns Learning path state and actions
 *
 * @example
 * const { pathNodes, loading, error, loadPath } = useLearningPath()
 */
export const useLearningPath = (): UseLearningPathReturn => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pathNodes, setPathNodes] = useState<PathNodeData[]>([]);
  const [learningStyle, setLearningStyle] = useState<string>('');
  const [currentNodeId, setCurrentNodeId] = useState<string>('');

  /**
   * Load completion status from backend
   */
  const loadCompletionStatus = useCallback(async (studentId: string): Promise<Record<string, boolean>> => {
    try {
      const response = await fetch(`${config.api.baseURL}/api/learning-path/completion/${studentId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        return data.data || {};
      }
    } catch (error) {
      console.warn('Could not load completion status:', error);
    }

    return {};
  }, []);

  /**
   * Load learning style for student
   */
  const loadLearningStyle = useCallback(async (studentId: string): Promise<string> => {
    try {
      const styleResponse = await detectLearningStyle(studentId);
      if (styleResponse.success) {
        return styleResponse.learning_style?.hybrid_code || 'V-ASVS';
      }
    } catch (err) {
      console.warn('Could not detect learning style:', err);
    }

    return 'V-ASVS'; // Default
  }, []);

  /**
   * Load learning path data
   */
  const loadPath = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // 1. Get student ID
      let studentId = learningPathService.getStudentId();

      if (!studentId) {
        // Create a demo profile if none exists
        const profile = await learningPathService.createProfile({
          name: 'Demo Öğrenci',
          grade: 12,
          subjects: ['matematik', 'fizik', 'kimya'],
          goals: ['YKS hazırlık', 'Matematik geliştirme'],
          learning_style: 'visual',
          available_time: 120,
        });
        console.log('Demo profile created:', profile);
        studentId = learningPathService.getStudentId() || '';
      }

      // 2. Get or create learning path
      let path = learningPathService.getCurrentPath();

      if (!path) {
        path = await learningPathService.generateLearningPath('matematik', 4);
      }

      // 3. Load completion status
      const completionStatus = studentId ? await loadCompletionStatus(studentId) : {};

      // 4. Convert path to nodes
      const nodes = convertPathToNodes(path, completionStatus);
      setPathNodes(nodes);

      // 5. Find current node
      const current = nodes.find(n => n.status === 'current');
      if (current) {
        setCurrentNodeId(current.id);
      }

      // 6. Get learning style
      if (studentId) {
        const style = await loadLearningStyle(studentId);
        setLearningStyle(style);
      }

    } catch (err: any) {
      console.error('Error loading learning path:', err);
      setError(err.message || 'Öğrenme yolu yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  }, [loadCompletionStatus, loadLearningStyle]);

  /**
   * Reload path data
   */
  const reload = useCallback(() => {
    loadPath();
  }, [loadPath]);

  /**
   * Set current node ID
   */
  const setCurrentNode = useCallback((nodeId: string) => {
    setCurrentNodeId(nodeId);
  }, []);

  /**
   * Update progress for a node
   * Syncs with backend and updates local state
   */
  const updateProgress = useCallback(async (update: ProgressUpdate): Promise<boolean> => {
    const { nodeId, progress, completed } = update;
    const studentId = learningPathService.getStudentId();

    if (!studentId) {
      console.error('No student ID found');
      return false;
    }

    try {
      // Update backend
      const response = await fetch(
        `${config.api.baseURL}/api/learning-path/progress/${studentId}/${nodeId}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify({
            progress: progress ?? (completed ? 100 : undefined),
            completed: completed ?? false,
          }),
        },
      );

      if (!response.ok) {
        console.error('Failed to update progress:', response.status);
        return false;
      }

      // Update local state
      setPathNodes(prevNodes =>
        prevNodes.map(node => {
          if (node.id !== nodeId) {return node;}

          const newProgress = progress ?? (completed ? 100 : node.progress);
          const isCompleted = completed || newProgress === 100;

          return {
            ...node,
            progress: newProgress,
            status: isCompleted ? 'completed' : node.status,
          };
        }),
      );

      // If node was completed, find and set next available node as current
      if (completed || progress === 100) {
        const currentIndex = pathNodes.findIndex(n => n.id === nodeId);
        if (currentIndex >= 0 && currentIndex < pathNodes.length - 1) {
          const nextNode = pathNodes[currentIndex + 1];
          if (nextNode && nextNode.status !== 'completed') {
            setCurrentNodeId(nextNode.id);
            // Update next node to current status
            setPathNodes(prevNodes =>
              prevNodes.map(node =>
                node.id === nextNode.id
                  ? { ...node, status: 'current' }
                  : node,
              ),
            );
          }
        }
      }

      return true;
    } catch (error) {
      console.error('Error updating progress:', error);
      return false;
    }
  }, [pathNodes]);

  /**
   * Mark a node as complete
   * Convenience wrapper around updateProgress
   */
  const markNodeComplete = useCallback(async (nodeId: string): Promise<boolean> => {
    return updateProgress({ nodeId, completed: true, progress: 100 });
  }, [updateProgress]);

  /**
   * Auto-load on mount
   */
  useEffect(() => {
    loadPath();
  }, [loadPath]);

  return {
    pathNodes,
    learningStyle,
    currentNodeId,
    loading,
    error,
    loadPath,
    reload,
    setCurrentNode,
    updateProgress,
    markNodeComplete,
  };
};

export default useLearningPath;
