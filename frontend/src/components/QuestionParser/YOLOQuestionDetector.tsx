/**
 * YOLO Question Detector Component
 * =================================
 * Sınav sayfalarından otomatik soru tespiti yapan React komponenti.
 *
 * Özellikler:
 * - Drag & Drop dosya yükleme
 * - Gerçek zamanlı tespit görselleştirme
 * - Tespit edilen soruları listeleme
 * - İstatistikler ve performans metrikleri
 * - Toplu işlem desteği
 *
 * @example
 * ```tsx
 * <YOLOQuestionDetector
 *   onQuestionsDetected={(questions) => console.log(questions)}
 *   confidence={0.25}
 * />
 * ```
 */

import {
  CloudUpload as UploadIcon,
  Image as ImageIcon,
  CheckCircle as CheckIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  VisibilityOff as HideIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Info as InfoIcon,
  Quiz as QuizIcon,
  Book as BookIcon,
  Numbers as NumbersIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';
import {
  Box,
  Paper,
  Typography,
  Button,
  Slider,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Collapse,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import * as React from 'react';
import {  useState, useRef, useCallback, useEffect  } from 'react';

import {
  yoloService,
  DetectionResult,
  Detection,
  CLASS_COLORS,
  CLASS_LABELS,
  DetectionClassName,
  CroppedQuestion,
} from '../../services/yoloService';

// ==================== Types ====================

interface YOLOQuestionDetectorProps {
  /** Tespit tamamlandığında çağrılır */
  onQuestionsDetected?: (questions: Detection[], result: DetectionResult) => void;
  /** Kırpılmış sorular hazır olduğunda çağrılır */
  onQuestionsCropped?: (croppedQuestions: CroppedQuestion[]) => void;
  /** Varsayılan güven eşiği */
  confidence?: number;
  /** Maksimum dosya boyutu (MB) */
  maxFileSize?: number;
  /** Kabul edilen dosya türleri */
  acceptedTypes?: string[];
  /** Otomatik kırpma aktif mi */
  autoCrop?: boolean;
  /** Kompakt mod */
  compact?: boolean;
}

interface FileWithPreview extends File {
  preview?: string;
}

// ==================== Helper Functions ====================

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) {return `${bytes} B`;}
  if (bytes < 1024 * 1024) {return `${(bytes / 1024).toFixed(1)} KB`;}
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const getClassIcon = (className: DetectionClassName) => {
  switch (className) {
    case 'soru':
      return <QuizIcon />;
    case 'cevaplar':
      return <CheckIcon />;
    case 'kitap':
      return <BookIcon />;
    case 'test_no':
      return <NumbersIcon />;
    case 'sayfa':
      return <AssignmentIcon />;
    default:
      return <InfoIcon />;
  }
};

// ==================== Component ====================

export const YOLOQuestionDetector: React.FC<YOLOQuestionDetectorProps> = ({
  onQuestionsDetected,
  onQuestionsCropped,
  confidence: initialConfidence = 0.25,
  maxFileSize = 10,
  acceptedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'],
  autoCrop = false,
  compact = false,
}) => {
  // State
  const [file, setFile] = useState<FileWithPreview | null>(null);
  const [confidence, setConfidence] = useState(initialConfidence);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [croppedQuestions, setCroppedQuestions] = useState<CroppedQuestion[]>([]);
  const [showBoxes, setShowBoxes] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [zoom, setZoom] = useState(1);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedQuestion, setSelectedQuestion] = useState<number | null>(null);
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);

  // Refs
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Health check on mount
  useEffect(() => {
    const checkHealth = async () => {
      const status = await yoloService.healthCheck();
      setIsHealthy(status.status === 'healthy');
    };
    checkHealth();
  }, []);

  // Draw detections when result changes
  useEffect(() => {
    if (result && imageRef.current && canvasRef.current && showBoxes) {
      yoloService.drawDetections(
        canvasRef.current,
        imageRef.current,
        result.detections,
        {
          showLabels,
          showConfidence: true,
          lineWidth: 2 / zoom,
          fontSize: 14 / zoom,
        },
      );
    }
  }, [result, showBoxes, showLabels, zoom]);

  // Handle file selection
  const handleFileSelect = useCallback(
    async (selectedFile: File) => {
      // Validate file type
      if (!acceptedTypes.includes(selectedFile.type)) {
        setError(`Desteklenmeyen dosya türü. Kabul edilen: ${acceptedTypes.join(', ')}`);
        return;
      }

      // Validate file size
      if (selectedFile.size > maxFileSize * 1024 * 1024) {
        setError(`Dosya çok büyük. Maksimum: ${maxFileSize} MB`);
        return;
      }

      // Create preview
      const preview = URL.createObjectURL(selectedFile);
      const fileWithPreview = Object.assign(selectedFile, { preview });
      setFile(fileWithPreview);
      setError(null);
      setResult(null);
      setCroppedQuestions([]);

      // Load image for canvas
      const img = new Image();
      img.onload = () => {
        imageRef.current = img;
      };
      img.src = preview;
    },
    [acceptedTypes, maxFileSize],
  );

  // Handle drag events
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  // Handle detection
  const handleDetect = async () => {
    if (!file) {return;}

    setIsLoading(true);
    setProgress(0);
    setError(null);

    try {
      const detectionResult = await yoloService.detectQuestions(file, {
        confidence,
        onProgress: setProgress,
      });

      setResult(detectionResult);

      // Callback
      if (onQuestionsDetected) {
        onQuestionsDetected(detectionResult.questions, detectionResult);
      }

      // Auto crop if enabled
      if (autoCrop && detectionResult.questions_count > 0) {
        const cropped = await yoloService.cropQuestions(file, { confidence });
        setCroppedQuestions(cropped);
        if (onQuestionsCropped) {
          onQuestionsCropped(cropped);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Tespit sırasında hata oluştu');
    } finally {
      setIsLoading(false);
      setProgress(0);
    }
  };

  // Handle crop questions
  const handleCropQuestions = async () => {
    if (!file || !result) {return;}

    setIsLoading(true);
    try {
      const cropped = await yoloService.cropQuestions(file, { confidence });
      setCroppedQuestions(cropped);
      if (onQuestionsCropped) {
        onQuestionsCropped(cropped);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Kırpma sırasında hata oluştu');
    } finally {
      setIsLoading(false);
    }
  };

  // Clear everything
  const handleClear = () => {
    if (file?.preview) {
      URL.revokeObjectURL(file.preview);
    }
    setFile(null);
    setResult(null);
    setCroppedQuestions([]);
    setError(null);
    imageRef.current = null;
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Calculate stats
  const stats = result ? yoloService.calculateStats(result) : null;

  return (
    <Box sx={{ width: '100%' }}>
      {/* Health Status */}
      {isHealthy === false && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          YOLO servisi şu anda kullanılamıyor. Lütfen backend&apos;in çalıştığından emin olun.
        </Alert>
      )}

      {/* Upload Area */}
      <Paper
        elevation={isDragging ? 8 : 2}
        sx={{
          p: compact ? 2 : 3,
          border: '2px dashed',
          borderColor: isDragging ? 'primary.main' : 'divider',
          bgcolor: isDragging ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          '&:hover': {
            borderColor: 'primary.light',
            bgcolor: 'action.hover',
          },
        }}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedTypes.join(',')}
          onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
          style={{ display: 'none' }}
        />

        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 1,
          }}
        >
          <UploadIcon sx={{ fontSize: compact ? 32 : 48, color: 'primary.main' }} />
          <Typography variant={compact ? 'body2' : 'body1'} color="textSecondary">
            Sınav sayfası görselini sürükleyin veya tıklayarak seçin
          </Typography>
          <Typography variant="caption" color="textSecondary">
            PNG, JPG • Maks. {maxFileSize} MB
          </Typography>
        </Box>
      </Paper>

      {/* File Info & Controls */}
      {file && (
        <Paper sx={{ mt: 2, p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <ImageIcon color="primary" />
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="subtitle2" noWrap>
                {file.name}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {formatFileSize(file.size)}
              </Typography>
            </Box>
            <IconButton size="small" onClick={handleClear}>
              <DeleteIcon />
            </IconButton>
          </Box>

          {/* Confidence Slider */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" gutterBottom>
              Güven Eşiği: {(confidence * 100).toFixed(0)}%
            </Typography>
            <Slider
              value={confidence}
              onChange={(_, value) => setConfidence(value as number)}
              min={0.1}
              max={0.9}
              step={0.05}
              size="small"
              disabled={isLoading}
            />
          </Box>

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="contained"
              onClick={handleDetect}
              disabled={isLoading}
              startIcon={isLoading ? <CircularProgress size={16} /> : <ViewIcon />}
              fullWidth
            >
              {isLoading ? 'Tespit Ediliyor...' : 'Soruları Tespit Et'}
            </Button>
            {result && result.questions_count > 0 && (
              <Button
                variant="outlined"
                onClick={handleCropQuestions}
                disabled={isLoading}
                startIcon={<ZoomInIcon />}
              >
                Kırp
              </Button>
            )}
          </Box>

          {/* Progress */}
          {isLoading && progress > 0 && (
            <LinearProgress variant="determinate" value={progress} sx={{ mt: 1 }} />
          )}
        </Paper>
      )}

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Results */}
      {result && (
        <Paper sx={{ mt: 2, p: 2 }}>
          {/* Stats */}
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6} sm={3}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center', py: 1 }}>
                  <Typography variant="h4" color="primary">
                    {stats?.questionCount || 0}
                  </Typography>
                  <Typography variant="caption">Soru</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center', py: 1 }}>
                  <Typography variant="h4" color="secondary">
                    {stats?.totalDetections || 0}
                  </Typography>
                  <Typography variant="caption">Toplam Tespit</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center', py: 1 }}>
                  <Typography variant="h4" color="success.main">
                    {((stats?.avgConfidence || 0) * 100).toFixed(0)}%
                  </Typography>
                  <Typography variant="caption">Ort. Güven</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center', py: 1 }}>
                  <Typography variant="h4" color="info.main">
                    {(stats?.processingTime || 0).toFixed(0)}
                  </Typography>
                  <Typography variant="caption">ms</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* View Controls */}
          <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
            <Chip
              icon={showBoxes ? <ViewIcon /> : <HideIcon />}
              label="Kutular"
              onClick={() => setShowBoxes(!showBoxes)}
              color={showBoxes ? 'primary' : 'default'}
              variant={showBoxes ? 'filled' : 'outlined'}
              size="small"
            />
            <Chip
              icon={<InfoIcon />}
              label="Etiketler"
              onClick={() => setShowLabels(!showLabels)}
              color={showLabels ? 'primary' : 'default'}
              variant={showLabels ? 'filled' : 'outlined'}
              size="small"
              disabled={!showBoxes}
            />
            <Box sx={{ flexGrow: 1 }} />
            <IconButton size="small" onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))}>
              <ZoomOutIcon />
            </IconButton>
            <Typography variant="caption" sx={{ alignSelf: 'center' }}>
              {(zoom * 100).toFixed(0)}%
            </Typography>
            <IconButton size="small" onClick={() => setZoom((z) => Math.min(2, z + 0.25))}>
              <ZoomInIcon />
            </IconButton>
          </Box>

          {/* Canvas / Image */}
          <Box
            sx={{
              overflow: 'auto',
              maxHeight: 500,
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 1,
              bgcolor: 'grey.100',
            }}
          >
            {showBoxes ? (
              <canvas
                ref={canvasRef}
                style={{
                  maxWidth: '100%',
                  transform: `scale(${zoom})`,
                  transformOrigin: 'top left',
                }}
              />
            ) : (
              file?.preview && (
                <img
                  src={file.preview}
                  alt="Yüklenen görsel"
                  style={{
                    maxWidth: '100%',
                    transform: `scale(${zoom})`,
                    transformOrigin: 'top left',
                  }}
                />
              )
            )}
          </Box>

          {/* Detection List */}
          <Collapse in={result.detections.length > 0}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom>
              Tespit Edilen Öğeler
            </Typography>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
              {Object.entries(stats?.classCounts || {}).map(([className, count]) => (
                <Chip
                  key={className}
                  icon={getClassIcon(className as DetectionClassName)}
                  label={`${CLASS_LABELS[className as DetectionClassName] || className}: ${count}`}
                  size="small"
                  sx={{
                    bgcolor: `${CLASS_COLORS[className as DetectionClassName]}22`,
                    borderColor: CLASS_COLORS[className as DetectionClassName],
                    borderWidth: 1,
                    borderStyle: 'solid',
                  }}
                />
              ))}
            </Box>

            {/* Questions List */}
            {result.questions.length > 0 && (
              <List dense sx={{ maxHeight: 200, overflow: 'auto' }}>
                {result.questions.map((q, idx) => (
                  <ListItem
                    key={idx}
                    button
                    selected={selectedQuestion === idx}
                    onClick={() => setSelectedQuestion(selectedQuestion === idx ? null : idx)}
                    sx={{
                      borderLeft: `3px solid ${CLASS_COLORS.soru}`,
                      mb: 0.5,
                      borderRadius: 1,
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <QuizIcon sx={{ color: CLASS_COLORS.soru }} />
                    </ListItemIcon>
                    <ListItemText
                      primary={`Soru ${idx + 1}`}
                      secondary={`Güven: ${(q.confidence * 100).toFixed(0)}% • ${q.bbox.width}x${q.bbox.height}px`}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Collapse>
        </Paper>
      )}

      {/* Cropped Questions */}
      {croppedQuestions.length > 0 && (
        <Paper sx={{ mt: 2, p: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Kırpılmış Sorular ({croppedQuestions.length})
          </Typography>
          <Grid container spacing={2}>
            {croppedQuestions.map((cropped, idx) => (
              <Grid item xs={12} sm={6} md={4} key={idx}>
                <Card variant="outlined">
                  <Box
                    component="img"
                    src={`data:image/png;base64,${cropped.image_base64}`}
                    alt={`Soru ${idx + 1}`}
                    sx={{
                      width: '100%',
                      height: 150,
                      objectFit: 'contain',
                      bgcolor: 'grey.50',
                    }}
                  />
                  <CardContent sx={{ py: 1 }}>
                    <Typography variant="caption">
                      Soru {idx + 1} • {(cropped.confidence * 100).toFixed(0)}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}
    </Box>
  );
};

export default YOLOQuestionDetector;
