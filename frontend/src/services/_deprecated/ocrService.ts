/**
 * KIRO2 OCR Service
 * =================
 *
 * YOLO detection ile entegre OCR frontend servisi.
 *
 * Kullanım:
 * ```typescript
 * import { ocrService } from '@/services/ocrService';
 *
 * // Tek görsel OCR
 * const result = await ocrService.extractText(file);
 *
 * // Soru OCR
 * const question = await ocrService.processQuestion(file);
 *
 * // YOLO + OCR pipeline
 * const detected = await ocrService.detectAndOCR(file);
 * ```
 */

import { apiClient as api } from './apiClient';

// ============================================================
// Types
// ============================================================

export type OCREngine = 'easyocr' | 'paddleocr' | 'tesseract' | 'claude_vision';

export interface OCRBox {
  text: string;
  confidence: number;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
}

export interface OCRResult {
  text: string;
  raw_text: string;
  confidence: number;
  boxes: OCRBox[];
  engine: string;
  language: string;
  processing_time_ms: number;
  has_math: boolean;
  latex: string | null;
  metadata: Record<string, unknown>;
}

export interface QuestionOCRResult {
  question_number: number | null;
  question_text: string;
  options: Record<string, string>; // {A: "...", B: "...", ...}
  has_image: boolean;
  has_equation: boolean;
  latex_content: string | null;
  confidence: number;
  raw_ocr: OCRResult;
}

export interface YOLOOCRResult {
  success: boolean;
  detection_count: number;
  question_count: number;
  questions: Array<{
    detection: {
      class_id: number;
      class_name: string;
      confidence: number;
      bbox: {
        x1: number;
        y1: number;
        x2: number;
        y2: number;
      };
    };
    ocr: {
      question_number: number | null;
      question_text: string;
      options: Record<string, string>;
      has_image: boolean;
      has_equation: boolean;
      latex_content: string | null;
      confidence: number;
    };
  }>;
  metadata: Record<string, string>;
  yolo_detections: Array<{
    class_id: number;
    class_name: string;
    confidence: number;
    bbox: {
      x1: number;
      y1: number;
      x2: number;
      y2: number;
    };
  }>;
}

export interface OCREngineInfo {
  name: string;
  available: boolean;
  description: string;
}

export interface OCRHealthStatus {
  status: string;
  primary_engine: string;
  fallback_engine: string;
  loaded_engines: string[];
}

export interface OCRServiceInfo {
  primary_engine: string;
  fallback_engine: string;
  use_gpu: boolean;
  languages: string[];
  loaded_engines: string[];
  supported_engines: string[];
}

// ============================================================
// OCR Service Class
// ============================================================

class OCRService {
  private baseUrl = '/api/ocr';

  /**
   * Dosyayı base64'e çevir
   */
  async fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        // Data URL'den sadece base64 kısmını al
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  /**
   * Tek görselten metin çıkar (file upload)
   */
  async extractText(file: File, engine?: OCREngine): Promise<OCRResult> {
    const formData = new FormData();
    formData.append('file', file);
    if (engine) {
      formData.append('engine', engine);
    }

    const response = await api.post<OCRResult>(`${this.baseUrl}/extract`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * Base64 görselten metin çıkar
   */
  async extractTextBase64(imageBase64: string, engine?: OCREngine): Promise<OCRResult> {
    const response = await api.post<OCRResult>(`${this.baseUrl}/extract-base64`, {
      image: imageBase64,
      engine,
    });

    return response.data;
  }

  /**
   * Batch görsel OCR
   */
  async extractTextBatch(
    files: File[],
    engine?: OCREngine,
    maxConcurrent = 5,
  ): Promise<OCRResult[]> {
    const base64Images = await Promise.all(
      files.map((file) => this.fileToBase64(file)),
    );

    const response = await api.post<OCRResult[]>(`${this.baseUrl}/extract-batch`, {
      images: base64Images,
      engine,
      max_concurrent: maxConcurrent,
    });

    return response.data;
  }

  /**
   * Soru görselini işle (file upload)
   */
  async processQuestion(file: File, engine?: OCREngine): Promise<QuestionOCRResult> {
    const formData = new FormData();
    formData.append('file', file);
    if (engine) {
      formData.append('engine', engine);
    }

    const response = await api.post<QuestionOCRResult>(`${this.baseUrl}/question`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * Base64 soru görselini işle
   */
  async processQuestionBase64(
    imageBase64: string,
    engine?: OCREngine,
  ): Promise<QuestionOCRResult> {
    const response = await api.post<QuestionOCRResult>(`${this.baseUrl}/question-base64`, {
      image: imageBase64,
      engine,
    });

    return response.data;
  }

  /**
   * YOLO detection + OCR pipeline
   */
  async detectAndOCR(
    file: File,
    options?: {
      confidenceThreshold?: number;
      cropPadding?: number;
      ocrEngine?: OCREngine;
    },
  ): Promise<YOLOOCRResult> {
    const imageBase64 = await this.fileToBase64(file);

    const response = await api.post<YOLOOCRResult>(`${this.baseUrl}/yolo-detect-ocr`, {
      image: imageBase64,
      confidence_threshold: options?.confidenceThreshold ?? 0.25,
      crop_padding: options?.cropPadding ?? 10,
      ocr_engine: options?.ocrEngine,
    });

    return response.data;
  }

  /**
   * YOLO detection + OCR pipeline (base64)
   */
  async detectAndOCRBase64(
    imageBase64: string,
    options?: {
      confidenceThreshold?: number;
      cropPadding?: number;
      ocrEngine?: OCREngine;
    },
  ): Promise<YOLOOCRResult> {
    const response = await api.post<YOLOOCRResult>(`${this.baseUrl}/yolo-detect-ocr`, {
      image: imageBase64,
      confidence_threshold: options?.confidenceThreshold ?? 0.25,
      crop_padding: options?.cropPadding ?? 10,
      ocr_engine: options?.ocrEngine,
    });

    return response.data;
  }

  /**
   * Kullanılabilir OCR motorlarını listele
   */
  async getEngines(): Promise<OCREngineInfo[]> {
    const response = await api.get<OCREngineInfo[]>(`${this.baseUrl}/engines`);
    return response.data;
  }

  /**
   * Sağlık kontrolü
   */
  async healthCheck(): Promise<OCRHealthStatus> {
    const response = await api.get<OCRHealthStatus>(`${this.baseUrl}/health`);
    return response.data;
  }

  /**
   * Servis bilgisi
   */
  async getInfo(): Promise<OCRServiceInfo> {
    const response = await api.get<OCRServiceInfo>(`${this.baseUrl}/info`);
    return response.data;
  }

  /**
   * Canvas üzerine OCR kutularını çiz
   */
  drawOCRBoxes(
    canvas: HTMLCanvasElement,
    image: HTMLImageElement,
    boxes: OCRBox[],
    options?: {
      boxColor?: string;
      textColor?: string;
      lineWidth?: number;
      showText?: boolean;
      showConfidence?: boolean;
    },
  ): void {
    const ctx = canvas.getContext('2d');
    if (!ctx) {return;}

    const {
      boxColor = '#00ff00',
      textColor = '#ffffff',
      lineWidth = 2,
      showText = true,
      showConfidence = true,
    } = options || {};

    // Canvas boyutunu ayarla
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;

    // Görseli çiz
    ctx.drawImage(image, 0, 0);

    // Kutuları çiz
    boxes.forEach((box) => {
      const [x1, y1, x2, y2] = box.bbox;
      const width = x2 - x1;
      const height = y2 - y1;

      // Kutu
      ctx.strokeStyle = boxColor;
      ctx.lineWidth = lineWidth;
      ctx.strokeRect(x1, y1, width, height);

      // Metin
      if (showText) {
        const label = showConfidence
          ? `${box.text} (${(box.confidence * 100).toFixed(1)}%)`
          : box.text;

        ctx.fillStyle = boxColor;
        ctx.fillRect(x1, y1 - 20, ctx.measureText(label).width + 10, 20);

        ctx.fillStyle = textColor;
        ctx.font = '14px Arial';
        ctx.fillText(label, x1 + 5, y1 - 5);
      }
    });
  }

  /**
   * OCR istatistiklerini hesapla
   */
  calculateStats(result: OCRResult): {
    totalBoxes: number;
    averageConfidence: number;
    totalCharacters: number;
    totalWords: number;
    mathDetected: boolean;
  } {
    return {
      totalBoxes: result.boxes.length,
      averageConfidence: result.confidence,
      totalCharacters: result.text.length,
      totalWords: result.text.split(/\s+/).filter(Boolean).length,
      mathDetected: result.has_math,
    };
  }

  /**
   * Soru OCR sonucunu formatla
   */
  formatQuestionResult(result: QuestionOCRResult): string {
    let formatted = '';

    if (result.question_number) {
      formatted += `**Soru ${result.question_number}**\n\n`;
    }

    formatted += `${result.question_text}\n\n`;

    if (Object.keys(result.options).length > 0) {
      Object.entries(result.options)
        .sort(([a], [b]) => a.localeCompare(b))
        .forEach(([letter, text]) => {
          formatted += `**${letter})** ${text}\n`;
        });
    }

    if (result.has_equation && result.latex_content) {
      formatted += `\n**LaTeX:** ${result.latex_content}`;
    }

    return formatted;
  }
}

// ============================================================
// Singleton Export
// ============================================================

export const ocrService = new OCRService();
export default ocrService;

// ============================================================
// React Hook (optional)
// ============================================================

import { useState, useCallback } from 'react';

export interface UseOCROptions {
  engine?: OCREngine;
  onSuccess?: (result: OCRResult) => void;
  onError?: (error: Error) => void;
}

export function useOCR(options?: UseOCROptions) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OCRResult | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const extractText = useCallback(
    async (file: File) => {
      setLoading(true);
      setError(null);

      try {
        const ocrResult = await ocrService.extractText(file, options?.engine);
        setResult(ocrResult);
        options?.onSuccess?.(ocrResult);
        return ocrResult;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        options?.onError?.(error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [options],
  );

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return {
    extractText,
    loading,
    result,
    error,
    reset,
  };
}

export interface UseQuestionOCROptions {
  engine?: OCREngine;
  onSuccess?: (result: QuestionOCRResult) => void;
  onError?: (error: Error) => void;
}

export function useQuestionOCR(options?: UseQuestionOCROptions) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QuestionOCRResult | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const processQuestion = useCallback(
    async (file: File) => {
      setLoading(true);
      setError(null);

      try {
        const ocrResult = await ocrService.processQuestion(file, options?.engine);
        setResult(ocrResult);
        options?.onSuccess?.(ocrResult);
        return ocrResult;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        options?.onError?.(error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [options],
  );

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return {
    processQuestion,
    loading,
    result,
    error,
    reset,
  };
}

export interface UseYOLOOCROptions {
  confidenceThreshold?: number;
  cropPadding?: number;
  ocrEngine?: OCREngine;
  onSuccess?: (result: YOLOOCRResult) => void;
  onError?: (error: Error) => void;
}

export function useYOLOOCR(options?: UseYOLOOCROptions) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<YOLOOCRResult | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const detectAndOCR = useCallback(
    async (file: File) => {
      setLoading(true);
      setError(null);

      try {
        const yoloResult = await ocrService.detectAndOCR(file, {
          confidenceThreshold: options?.confidenceThreshold,
          cropPadding: options?.cropPadding,
          ocrEngine: options?.ocrEngine,
        });
        setResult(yoloResult);
        options?.onSuccess?.(yoloResult);
        return yoloResult;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        options?.onError?.(error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [options],
  );

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return {
    detectAndOCR,
    loading,
    result,
    error,
    reset,
  };
}
