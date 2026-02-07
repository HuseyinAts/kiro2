/**
 * Exam Results Helper Utilities
 *
 * Utility functions for exam results processing and display
 */

import { Star, TrendingUp, Assessment, TrendingDown } from '@mui/icons-material';
import * as React from 'react';

import { SinavSonucu, KonuPerformansi } from '../types';

export interface SuccessLevel {
  level: string
  color: 'success' | 'info' | 'warning' | 'error'
  icon: React.ReactNode
}

/**
 * Determine success level based on score
 *
 * @param puan - Score (0-100)
 * @returns Success level info with label, color, and icon
 */
export const getSuccessLevel = (puan: number): SuccessLevel => {
  if (puan >= 80) {
    return {
      level: 'Mükemmel',
      color: 'success',
      icon: React.createElement(Star),
    };
  } else if (puan >= 70) {
    return {
      level: 'İyi',
      color: 'info',
      icon: React.createElement(TrendingUp),
    };
  } else if (puan >= 60) {
    return {
      level: 'Orta',
      color: 'warning',
      icon: React.createElement(Assessment),
    };
  } else {
    return {
      level: 'Geliştirilmeli',
      color: 'error',
      icon: React.createElement(TrendingDown),
    };
  }
};

/**
 * Prepare data for pie chart (correct, wrong, empty answers)
 *
 * @param sonuc - Exam result
 * @returns Chart data array
 */
export const preparePieChartData = (sonuc: SinavSonucu) => {
  return [
    { name: 'Doğru', value: sonuc.dogru_sayisi, color: '#10b981' },
    { name: 'Yanlış', value: sonuc.yanlis_sayisi, color: '#ef4444' },
    { name: 'Boş', value: sonuc.bos_sayisi, color: '#6b7280' },
  ];
};

/**
 * Prepare topic performance data for bar chart
 *
 * @param konuPerformanslari - Topic performance array
 * @returns Chart data array with truncated topic names
 */
export const prepareTopicPerformanceData = (konuPerformanslari: KonuPerformansi[]) => {
  return konuPerformanslari.map((konu) => ({
    konu: konu.konu.length > 15 ? konu.konu.substring(0, 15) + '...' : konu.konu,
    basari: konu.basari_yuzdesi,
    dogru: konu.dogru_sayisi,
    yanlis: konu.yanlis_sayisi,
    bos: konu.bos_sayisi,
    fullName: konu.konu, // Keep full name for tooltip
  }));
};

/**
 * Calculate performance percentage
 *
 * @param dogru - Correct answers
 * @param toplam - Total questions
 * @returns Percentage (0-100)
 */
export const calculatePercentage = (dogru: number, toplam: number): number => {
  if (toplam === 0) {return 0;}
  return Math.round((dogru / toplam) * 100);
};

/**
 * Format score with one decimal place
 *
 * @param score - Raw score
 * @returns Formatted score string
 */
export const formatScore = (score: number): string => {
  return score.toFixed(1);
};

/**
 * Get color based on performance percentage
 *
 * @param percentage - Performance percentage (0-100)
 * @returns MUI color name
 */
export const getPerformanceColor = (
  percentage: number,
): 'success' | 'info' | 'warning' | 'error' => {
  if (percentage >= 80) {return 'success';}
  if (percentage >= 70) {return 'info';}
  if (percentage >= 60) {return 'warning';}
  return 'error';
};

/**
 * Truncate text with ellipsis
 *
 * @param text - Text to truncate
 * @param maxLength - Maximum length before truncating
 * @returns Truncated text
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) {return text;}
  return text.substring(0, maxLength) + '...';
};
