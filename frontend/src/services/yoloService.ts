/**
 * YOLO Question Detection Service
 * ================================
 * Sınav sayfalarından soru tespiti için YOLO API servisi.
 *
 * Özellikler:
 * - Tek görsel tespiti
 * - Toplu tespit
 * - Soru kırpma
 * - Base64 desteği
 *
 * @example
 * ```tsx
 * import { yoloService } from '@/services/yoloService';
 *
 * const result = await yoloService.detectQuestions(file);
 * console.log(`${result.questions_count} soru tespit edildi`);
 * ```
 */

import axios, { AxiosProgressEvent } from 'axios';

import config from '../config';

const API_BASE_URL = config.api.baseURL;

// ==================== Types ====================

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  width: number;
  height: number;
}

export interface Detection {
  class_id: number;
  class_name: DetectionClassName;
  confidence: number;
  bbox: BoundingBox;
}

export type DetectionClassName =
  | 'soru'
  | 'cevaplar'
  | 'zorluk_seviyesi'
  | 'kitap'
  | 'test_no'
  | 'sayfa';

export interface DetectionMetadata {
  kitap: Detection | null;
  test_no: Detection | null;
  sayfa: Detection | null;
  zorluk_seviyesi: Detection | null;
  cevaplar: Detection | null;
}

export interface DetectionResult {
  image_path: string | null;
  image_size: {
    width: number;
    height: number;
  };
  total_detections: number;
  questions_count: number;
  detections: Detection[];
  questions: Detection[];
  metadata: DetectionMetadata;
  processing_time_ms: number;
  error?: string;
}

export interface CroppedQuestion {
  question_index: number;
  class_name: string;
  confidence: number;
  bbox: BoundingBox;
  image_base64: string;
  image_width: number;
  image_height: number;
}

export interface ModelInfo {
  model_path: string;
  model_loaded: boolean;
  device: string;
  confidence_threshold: number;
  iou_threshold: number;
  classes: Record<number, string>;
  num_classes: number;
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  model_loaded?: boolean;
  device?: string;
  classes?: string[];
  error?: string;
}

export interface DetectionOptions {
  confidence?: number;
  onProgress?: (progress: number) => void;
}

// ==================== Class Colors ====================

export const CLASS_COLORS: Record<DetectionClassName, string> = {
  soru: '#4CAF50',           // Yeşil
  cevaplar: '#2196F3',       // Mavi
  zorluk_seviyesi: '#FF9800', // Turuncu
  kitap: '#9C27B0',          // Mor
  test_no: '#F44336',        // Kırmızı
  sayfa: '#607D8B',          // Gri
};

export const CLASS_LABELS: Record<DetectionClassName, string> = {
  soru: 'Soru',
  cevaplar: 'Cevaplar',
  zorluk_seviyesi: 'Zorluk Seviyesi',
  kitap: 'Kitap',
  test_no: 'Test No',
  sayfa: 'Sayfa',
};

// ==================== Service Class ====================

class YOLOService {
  private baseUrl: string;

  constructor() {
    // Backend router is mounted at prefix "/api/v1/yolo"
    // (backend/api/yolo_detection_api.py) — S200 audit fix.
    this.baseUrl = `${API_BASE_URL}/api/v1/yolo`;
  }

  /**
   * Servis sağlık kontrolü
   */
  async healthCheck(): Promise<HealthStatus> {
    try {
      const response = await axios.get<HealthStatus>(`${this.baseUrl}/health`);
      return response.data;
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Model bilgilerini getir
   */
  async getModelInfo(): Promise<ModelInfo> {
    const response = await axios.get<ModelInfo>(`${this.baseUrl}/model-info`);
    return response.data;
  }

  /**
   * Görsel üzerinde soru tespiti yap
   *
   * @param file - Yüklenecek görsel dosyası
   * @param options - Tespit seçenekleri
   * @returns Tespit sonuçları
   */
  async detectQuestions(
    file: File,
    options: DetectionOptions = {},
  ): Promise<DetectionResult> {
    const { confidence = 0.25, onProgress } = options;

    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post<DetectionResult>(
      `${this.baseUrl}/detect`,
      formData,
      {
        params: { confidence },
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        },
      },
    );

    return response.data;
  }

  /**
   * Base64 görsel ile soru tespiti
   *
   * @param imageBase64 - Base64 encoded görsel
   * @param confidence - Güven eşiği
   * @returns Tespit sonuçları
   */
  async detectQuestionsBase64(
    imageBase64: string,
    confidence: number = 0.25,
  ): Promise<DetectionResult> {
    const formData = new FormData();
    formData.append('image_base64', imageBase64);

    const response = await axios.post<DetectionResult>(
      `${this.baseUrl}/detect-base64`,
      formData,
      {
        params: { confidence },
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      },
    );

    return response.data;
  }

  /**
   * Toplu soru tespiti
   *
   * @param files - Görsel dosyaları (max 20)
   * @param options - Tespit seçenekleri
   * @returns Tespit sonuçları listesi
   */
  async detectQuestionsBatch(
    files: File[],
    options: DetectionOptions = {},
  ): Promise<DetectionResult[]> {
    if (files.length > 20) {
      throw new Error('Maksimum 20 dosya yüklenebilir.');
    }

    const { confidence = 0.25, onProgress } = options;

    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await axios.post<DetectionResult[]>(
      `${this.baseUrl}/detect-batch`,
      formData,
      {
        params: { confidence },
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        },
      },
    );

    return response.data;
  }

  /**
   * Tespit edilen soruları kırp
   *
   * @param file - Görsel dosyası
   * @param options - Kırpma seçenekleri
   * @returns Kırpılmış soru görselleri
   */
  async cropQuestions(
    file: File,
    options: { confidence?: number; padding?: number } = {},
  ): Promise<CroppedQuestion[]> {
    const { confidence = 0.25, padding = 10 } = options;

    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post<CroppedQuestion[]>(
      `${this.baseUrl}/crop-questions`,
      formData,
      {
        params: { confidence, padding },
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      },
    );

    return response.data;
  }

  /**
   * File'ı Base64'e çevir
   */
  fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        // data:image/png;base64, prefix'ini kaldır
        const base64 = result.split(',')[1] || result;
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  /**
   * Bounding box'ı canvas üzerine çiz
   */
  drawDetections(
    canvas: HTMLCanvasElement,
    image: HTMLImageElement,
    detections: Detection[],
    options: {
      showLabels?: boolean;
      showConfidence?: boolean;
      lineWidth?: number;
      fontSize?: number;
    } = {},
  ): void {
    const {
      showLabels = true,
      showConfidence = true,
      lineWidth = 2,
      fontSize = 14,
    } = options;

    const ctx = canvas.getContext('2d');
    if (!ctx) {return;}

    // Canvas boyutunu ayarla
    canvas.width = image.width;
    canvas.height = image.height;

    // Görseli çiz
    ctx.drawImage(image, 0, 0);

    // Her tespit için kutu çiz
    detections.forEach((detection) => {
      const { bbox, class_name, confidence } = detection;
      const color = CLASS_COLORS[class_name] || '#FFFFFF';

      // Kutu çiz
      ctx.strokeStyle = color;
      ctx.lineWidth = lineWidth;
      ctx.strokeRect(bbox.x1, bbox.y1, bbox.width, bbox.height);

      // Yarı saydam arka plan
      ctx.fillStyle = `${color}33`; // 20% opacity
      ctx.fillRect(bbox.x1, bbox.y1, bbox.width, bbox.height);

      // Label çiz
      if (showLabels) {
        const label = CLASS_LABELS[class_name] || class_name;
        const confText = showConfidence ? ` ${(confidence * 100).toFixed(0)}%` : '';
        const text = `${label}${confText}`;

        ctx.font = `bold ${fontSize}px Arial`;
        const textWidth = ctx.measureText(text).width;
        const textHeight = fontSize;
        const padding = 4;

        // Label arka planı
        ctx.fillStyle = color;
        ctx.fillRect(
          bbox.x1,
          bbox.y1 - textHeight - padding * 2,
          textWidth + padding * 2,
          textHeight + padding * 2,
        );

        // Label metni
        ctx.fillStyle = '#FFFFFF';
        ctx.fillText(text, bbox.x1 + padding, bbox.y1 - padding);
      }
    });
  }

  /**
   * Tespit istatistiklerini hesapla
   */
  calculateStats(result: DetectionResult): {
    totalDetections: number;
    questionCount: number;
    avgConfidence: number;
    classCounts: Record<string, number>;
    processingTime: number;
  } {
    const classCounts: Record<string, number> = {};
    let totalConfidence = 0;

    result.detections.forEach((det) => {
      classCounts[det.class_name] = (classCounts[det.class_name] || 0) + 1;
      totalConfidence += det.confidence;
    });

    return {
      totalDetections: result.total_detections,
      questionCount: result.questions_count,
      avgConfidence: result.total_detections > 0
        ? totalConfidence / result.total_detections
        : 0,
      classCounts,
      processingTime: result.processing_time_ms,
    };
  }
}

// Singleton instance
export const yoloService = new YOLOService();

// Default export
export default yoloService;
