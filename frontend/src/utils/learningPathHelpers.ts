/**
 * Learning Path Utility Functions
 *
 * Pure utility functions for learning path operations
 * Extracted from LearningPathPage.tsx
 */

import { PathNodeData } from '../components/LearningPath/PathNode';

/**
 * Extract subject from module/topic title
 *
 * @param title - Module or topic title
 * @returns Subject name (matematik, fizik, etc.)
 */
export const extractSubject = (title: string): string => {
  const lowerTitle = title.toLowerCase();
  if (lowerTitle.includes('matematik')) {return 'matematik';}
  if (lowerTitle.includes('fizik')) {return 'fizik';}
  if (lowerTitle.includes('kimya')) {return 'kimya';}
  if (lowerTitle.includes('biyoloji')) {return 'biyoloji';}
  if (lowerTitle.includes('türkçe')) {return 'türkçe';}
  return 'matematik'; // default
};

/**
 * Extract specific topic from topic name
 *
 * @param topicName - Topic name
 * @returns Topic keyword or undefined
 */
export const extractTopic = (topicName: string): string | undefined => {
  const lowerTopic = topicName.toLowerCase();

  // Matematik konuları
  if (lowerTopic.includes('türev')) {return 'türev';}
  if (lowerTopic.includes('integral')) {return 'integral';}
  if (lowerTopic.includes('limit')) {return 'limit';}
  if (lowerTopic.includes('fonksiyon')) {return 'fonksiyon';}

  // Fizik konuları
  if (lowerTopic.includes('hareket')) {return 'hareket';}
  if (lowerTopic.includes('kuvvet')) {return 'kuvvet';}
  if (lowerTopic.includes('enerji')) {return 'enerji';}
  if (lowerTopic.includes('elektrik')) {return 'elektrik';}

  // Kimya konuları
  if (lowerTopic.includes('atom')) {return 'atom';}
  if (lowerTopic.includes('reaksiyon')) {return 'reaksiyon';}
  if (lowerTopic.includes('molekül')) {return 'molekül';}

  return undefined;
};

/**
 * Generate connections between learning path nodes
 *
 * @param nodes - Array of path nodes
 * @returns Array of connections (from -> to)
 */
export const generateConnections = (
  nodes: PathNodeData[],
): Array<{ from: string; to: string }> => {
  const connections: Array<{ from: string; to: string }> = [];

  nodes.forEach((node, index) => {
    if (index < nodes.length - 1) {
      connections.push({
        from: node.id,
        to: nodes[index + 1].id,
      });
    }
  });

  return connections;
};

/**
 * Convert learning path modules to node data structure
 *
 * @param path - Learning path object
 * @param completionStatus - Map of node ID to completion status
 * @returns Array of path nodes
 */
export const convertPathToNodes = (
  path: any,
  completionStatus: Record<string, boolean> = {},
): PathNodeData[] => {
  const nodes: PathNodeData[] = [];
  let yPosition = 0;

  path.modules?.forEach((module: any, moduleIndex: number) => {
    module.topics?.forEach((topic: any, topicIndex: number) => {
      const nodeId = `${module.module_id}-${topic.topic_id}`;
      const isFirst = moduleIndex === 0 && topicIndex === 0;
      const isCompleted = completionStatus[nodeId] || false;

      nodes.push({
        id: nodeId,
        title: topic.name,
        description: `${module.title} - ${topic.name}`,
        type: 'lesson',
        status: isCompleted ? 'completed' : isFirst ? 'current' : 'available',
        progress: isCompleted ? 100 : isFirst ? 30 : 0,
        estimatedTime: `${topic.duration_minutes} dakika`,
        difficulty: 'intermediate',
        points: 100,
        prerequisites: topicIndex > 0 ? [`${module.module_id}-TOP${topicIndex}`] : [],
        resources: topic.resources?.length || 0,
        position: { x: 100 + moduleIndex * 300, y: 100 + yPosition },
      });

      yPosition += 150;
      if (topicIndex === module.topics.length - 1) {
        yPosition = 0;
      }
    });
  });

  return nodes;
};

/**
 * Calculate overall progress percentage
 *
 * @param nodes - Array of path nodes
 * @returns Progress percentage (0-100)
 */
export const calculateOverallProgress = (nodes: PathNodeData[]): number => {
  if (nodes.length === 0) {return 0;}
  const completedCount = nodes.filter(n => n.status === 'completed').length;
  return Math.round((completedCount / nodes.length) * 100);
};

/**
 * Calculate total estimated time in minutes
 *
 * @param nodes - Array of path nodes
 * @returns Total time in minutes
 */
export const calculateTotalTime = (nodes: PathNodeData[]): number => {
  return nodes.reduce((sum, node) => {
    const match = node.estimatedTime?.match(/(\d+)/);
    return sum + (match ? parseInt(match[1]) : 0);
  }, 0);
};

/**
 * Group nodes by module
 *
 * @param nodes - Array of path nodes
 * @returns Map of module ID to nodes
 */
export const groupNodesByModule = (
  nodes: PathNodeData[],
): Map<string, PathNodeData[]> => {
  const groups = new Map<string, PathNodeData[]>();

  nodes.forEach(node => {
    // Extract module ID from node ID (format: MOD1-TOP1)
    const moduleId = node.id.split('-')[0];
    if (!groups.has(moduleId)) {
      groups.set(moduleId, []);
    }
    groups.get(moduleId)!.push(node);
  });

  return groups;
};

/**
 * Calculate module progress
 *
 * @param moduleNodes - Nodes in a specific module
 * @returns Progress percentage (0-100)
 */
export const calculateModuleProgress = (moduleNodes: PathNodeData[]): number => {
  if (moduleNodes.length === 0) {return 0;}
  const completedCount = moduleNodes.filter(n => n.status === 'completed').length;
  return Math.round((completedCount / moduleNodes.length) * 100);
};

/**
 * Get module title by index
 *
 * @param moduleIndex - Module index (0-based)
 * @returns Module title
 */
export const getModuleTitle = (moduleIndex: number): string => {
  const titles = ['Temel Kavramlar', 'Orta Seviye', 'İleri Seviye'];
  return titles[moduleIndex] || `Modül ${moduleIndex + 1}`;
};

/**
 * Format difficulty level to Turkish
 *
 * @param difficulty - Difficulty level (beginner, intermediate, advanced)
 * @returns Turkish difficulty label
 */
export const formatDifficulty = (difficulty: string): string => {
  const difficultyMap: Record<string, string> = {
    beginner: 'Başlangıç',
    intermediate: 'Orta',
    advanced: 'İleri',
  };
  return difficultyMap[difficulty] || difficulty;
};

export default {
  extractSubject,
  extractTopic,
  generateConnections,
  convertPathToNodes,
  calculateOverallProgress,
  calculateTotalTime,
  groupNodesByModule,
  calculateModuleProgress,
  getModuleTitle,
  formatDifficulty,
};
