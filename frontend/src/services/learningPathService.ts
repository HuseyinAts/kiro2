import {
  createStudentProfile,
  assessKnowledge,
  createLearningPath,
  searchResources,
  adaptLearningPath,
} from '../api';

export interface StudentProfile {
  name: string;
  grade: number;
  subjects: string[];
  goals: string[];
  learning_style?: string;
  available_time?: number;
}

export interface LearningResource {
  resource_id: string;
  title: string;
  source: string;
  url: string;
  type: string;
  estimated_time: number;
  difficulty: string;
  description: string;
  tags?: string[];
}

export interface LearningPath {
  path_id: string;
  student_name: string;
  total_time: number;
  phases: string[];
  resources: LearningResource[];
  reasoning: string;
}

class LearningPathService {
  private studentId: string | null = null;
  private currentPath: LearningPath | null = null;

  async createProfile(profileData: StudentProfile) {
    try {
      const response = await createStudentProfile(profileData);
      if (response.success) {
        this.studentId = response.profile.student_id;
        localStorage.setItem('studentId', this.studentId || '');
        return response.profile;
      }
      throw new Error(response.error || 'Failed to create profile');
    } catch (error) {
      console.error('Error creating student profile:', error);
      throw error;
    }
  }

  async assessStudentKnowledge(subject: string, questions?: string[]) {
    if (!this.studentId) {
      throw new Error('No student profile found. Please create a profile first.');
    }

    try {
      const response = await assessKnowledge({
        student_id: this.studentId,
        subject,
        questions,
      });

      if (response.success) {
        return response.assessment;
      }
      throw new Error(response.error || 'Failed to assess knowledge');
    } catch (error) {
      console.error('Error assessing knowledge:', error);
      throw error;
    }
  }

  async generateLearningPath(topic: string, durationWeeks: number = 4) {
    if (!this.studentId) {
      throw new Error('No student profile found. Please create a profile first.');
    }

    try {
      // ✅ BUG FIX #2: Flat structure matching backend schema
      const response = await createLearningPath({
        student_id: this.studentId,  // ← Flat structure (no nesting)!
        subject: topic,               // ← "subject" not "topic"
        duration_weeks: durationWeeks,
        difficulty_level: 'intermediate'
      });

      if (response.success) {
        this.currentPath = response.learning_path;
        localStorage.setItem('currentPath', JSON.stringify(this.currentPath));
        return this.currentPath;
      }
      throw new Error(response.error || 'Failed to create learning path');
    } catch (error) {
      console.error('Error creating learning path:', error);
      throw error;
    }
  }

  /**
   * Find learning resources
   * ✅ BUG FIX #3: Proper API contract with backend
   * Sends: {subject, topic?, difficulty?, student_profile}
   */
  async findResources(subject: string, options?: {
    topic?: string;
    difficulty?: string;  // "kolay" | "orta" | "zor"
    learning_style?: string;
    grade?: number;
    max_results?: number;
  }) {
    try {
      // ✅ Build proper request structure matching backend schema
      const response = await searchResources({
        subject,  // ← Required field (was "topic")
        topic: options?.topic,
        difficulty: options?.difficulty || 'orta',
        max_results: options?.max_results || 10,
        student_profile: {  // ← Nested structure!
          student_id: this.studentId || undefined,
          learning_style: options?.learning_style,
          grade: options?.grade,
          goals: [subject + ' öğrenme'],
          current_level: { [subject]: 50 },  // Default intermediate level
        },
      });

      if (response.success) {
        return response.resources;
      }
      throw new Error(response.error || 'Failed to search resources');
    } catch (error) {
      console.error('Error searching resources:', error);
      throw error;
    }
  }

  async updateLearningPath(progressData: any) {
    if (!this.currentPath) {
      throw new Error('No active learning path found.');
    }

    try {
      const response = await adaptLearningPath({
        path_id: this.currentPath.path_id,
        progress_data: progressData,
      });

      if (response.success) {
        this.currentPath = response.adapted_path;
        localStorage.setItem('currentPath', JSON.stringify(this.currentPath));
        return this.currentPath;
      }
      throw new Error(response.error || 'Failed to adapt learning path');
    } catch (error) {
      console.error('Error adapting learning path:', error);
      throw error;
    }
  }

  getStudentId(): string | null {
    if (!this.studentId) {
      this.studentId = localStorage.getItem('studentId');
    }
    return this.studentId;
  }

  getCurrentPath(): LearningPath | null {
    if (!this.currentPath) {
      const storedPath = localStorage.getItem('currentPath');
      if (storedPath) {
        this.currentPath = JSON.parse(storedPath);
      }
    }
    return this.currentPath;
  }

  clearData() {
    this.studentId = null;
    this.currentPath = null;
    localStorage.removeItem('studentId');
    localStorage.removeItem('currentPath');
  }
}

export default new LearningPathService();