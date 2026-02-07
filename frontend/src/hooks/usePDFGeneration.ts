/**
 * usePDFGeneration Hook
 *
 * Custom hook for generating and downloading PDF reports
 * Handles polling and download logic
 */

import { useState } from 'react';

import { advancedReportsService } from '../services/advancedReportsService';

interface UsePDFGenerationReturn {
  generating: boolean
  error: string | null
  generateAndDownload: () => Promise<void>
}

/**
 * Hook for generating and downloading PDF exam reports
 *
 * @param sinavId - Exam ID to generate report for
 * @returns PDF generation state and download function
 *
 * @example
 * const { generating, generateAndDownload } = usePDFGeneration(sinavId)
 */
export const usePDFGeneration = (sinavId: string): UsePDFGenerationReturn => {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateAndDownload = async () => {
    try {
      setGenerating(true);
      setError(null);

      // Generate PDF
      const result = await advancedReportsService.generatePDFReport(sinavId);

      // Wait for PDF generation (simple polling - could be improved with WebSocket)
      // In production, consider using a proper polling mechanism or WebSocket
      await new Promise((resolve) => setTimeout(resolve, 3000));

      // Download PDF
      const blob = await advancedReportsService.downloadPDFReport(result.pdf_filename);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = result.pdf_filename;
      document.body.appendChild(link);
      link.click();

      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
    } catch (err: any) {
      const errorMessage = err.message || 'PDF oluşturma hatası';
      setError(errorMessage);
      console.error('PDF generation error:', err);
      throw err;
    } finally {
      setGenerating(false);
    }
  };

  return {
    generating,
    error,
    generateAndDownload,
  };
};

export default usePDFGeneration;
