/**
 * Matematik Çözüm Custom Hook
 * Requirements: REQ-51.21-51.40
 */

import axios from 'axios';
import { useState, useCallback } from 'react';

interface MathSolution {
  problem_id: string;
  problem_statement: string;
  problem_type: string;
  difficulty_level: string;
  steps: any[];
  total_steps: number;
  total_duration_estimate_seconds: number;
  prerequisites: string[];
  related_concepts: string[];
  alternative_methods: string[];
  created_at: string;
}

export const useMathSolution = () => {
  const [solution, setSolution] = useState<MathSolution | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(1);

  const generateSolution = useCallback(async (
    problemId: string,
    problemStatement: string,
    problemType: string,
    difficultyLevel: string = 'medium',
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/v1/math-solution-steps/generate', {
        problem_id: problemId,
        problem_statement: problemStatement,
        problem_type: problemType,
        difficulty_level: difficultyLevel,
      });

      if (response?.data?.success) {
        setSolution(response.data.data);
        setCurrentStep(1);
      } else {
        setError(response?.data?.message || 'Çözüm oluşturulamadı');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  }, []);

  const getStep = useCallback(async (problemId: string, stepNumber: number) => {
    try {
      const response = await axios.get(
        `/api/v1/math-solution-steps/step/${problemId}/${stepNumber}`,
      );
      return response?.data?.data;
    } catch (err: any) {
      console.error('Step fetch error:', err);
      return null;
    }
  }, []);

  const getHint = useCallback(async (
    problemId: string,
    stepNumber: number,
    hintLevel: number,
  ) => {
    try {
      const response = await axios.post('/api/v1/math-solution-steps/hint', {
        problem_id: problemId,
        step_number: stepNumber,
        hint_level: hintLevel,
      });
      return response?.data?.data?.hint;
    } catch (err: any) {
      console.error('Hint fetch error:', err);
      return null;
    }
  }, []);

  return {
    solution,
    loading,
    error,
    currentStep,
    setCurrentStep,
    generateSolution,
    getStep,
    getHint,
  };
};
