/**
 * PhotoAskPage — F3: "Fotoğrafla Sor" Pipeline
 *
 * Camera/file upload → OCR text extraction → pgvector similarity search → AI solution
 * Uses existing backend: OCR API + pgvector (21ms avg) + AI chat
 */
import { useState, useRef, useCallback, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Paper,
  Typography,
  Alert,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Stack,
} from '@mui/material';
import {
  CameraAlt as CameraIcon,
  CloudUpload as UploadIcon,
  ArrowBack as BackIcon,
  AutoFixHigh as AIIcon,
  Search as SearchIcon,
  Image as ImageIcon,
} from '@mui/icons-material';

interface SimilarQuestion {
  question_id: string;
  similarity: number;
  question_text: string;
  subject: string;
  topic: string;
  correct_answer: string;
  has_solution: boolean;
}

interface UploadResult {
  ocr_text: string;
  similar_questions: SimilarQuestion[];
  processing_time_ms: number;
}

interface SolutionResult {
  solution_text: string;
  source: 'database' | 'ai_generated';
  question_text?: string;
}

type PageState = 'upload' | 'processing' | 'results' | 'solution' | 'error';

export default function PhotoAskPage() {
  const [state, setState] = useState<PageState>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [solution, setSolution] = useState<SolutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Lütfen bir görsel dosyası seçin (JPG, PNG)');
      return;
    }
    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('Dosya boyutu 10MB\'dan küçük olmalıdır');
      return;
    }

    setSelectedFile(file);
    setError(null);

    // Create preview using object URL (avoids base64 encoding ~33% memory overhead)
    const objectUrl = URL.createObjectURL(file);
    setPreview(objectUrl);
  }, []);

  // Revoke object URL on unmount or when preview changes to prevent memory leak
  useEffect(() => {
    return () => {
      if (preview && preview.startsWith('blob:')) {
        URL.revokeObjectURL(preview);
      }
    };
  }, [preview]);

  const handleUpload = useCallback(async () => {
    if (!selectedFile) return;

    setState('processing');
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('/api/v1/photo-ask/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Yükleme hatası: ${response.status}`);
      }

      const data: UploadResult = await response.json();
      setUploadResult(data);
      setState('results');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bir hata oluştu');
      setState('error');
    }
  }, [selectedFile]);

  const handleViewSolution = useCallback(async (questionId: string) => {
    setAiLoading(true);
    try {
      const response = await fetch(`/api/v1/photo-ask/solution/${questionId}`, {
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Çözüm yüklenemedi');

      const data: SolutionResult = await response.json();
      setSolution(data);
      setState('solution');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Çözüm yüklenemedi');
    } finally {
      setAiLoading(false);
    }
  }, []);

  const handleAISolve = useCallback(async () => {
    if (!uploadResult?.ocr_text) return;

    setAiLoading(true);
    try {
      const response = await fetch('/api/v1/photo-ask/ai-solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ ocr_text: uploadResult.ocr_text }),
      });

      if (!response.ok) throw new Error('AI çözüm oluşturulamadı');

      const data: SolutionResult = await response.json();
      setSolution(data);
      setState('solution');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI çözüm hatası');
    } finally {
      setAiLoading(false);
    }
  }, [uploadResult]);

  const handleReset = useCallback(() => {
    setState('upload');
    setSelectedFile(null);
    setPreview(null);
    setUploadResult(null);
    setSolution(null);
    setError(null);
  }, []);

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', p: 2 }}>
      <Typography variant="h5" gutterBottom fontWeight={700}>
        📸 Fotoğrafla Sor
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Sorunun fotoğrafını çek veya yükle, benzer soruları bul ve çözümünü gör.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Upload State */}
      {state === 'upload' && (
        <Card variant="outlined">
          <CardContent>
            {preview ? (
              <Box sx={{ textAlign: 'center', mb: 2 }}>
                <img
                  src={preview}
                  alt="Seçilen soru"
                  style={{ maxWidth: '100%', maxHeight: 300, borderRadius: 8 }}
                />
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  {selectedFile?.name}
                </Typography>
              </Box>
            ) : (
              <Paper
                variant="outlined"
                sx={{
                  p: 4,
                  textAlign: 'center',
                  border: '2px dashed',
                  borderColor: 'grey.300',
                  cursor: 'pointer',
                  '&:hover': { borderColor: 'primary.main', bgcolor: 'action.hover' },
                }}
                onClick={() => fileInputRef.current?.click()}
              >
                <ImageIcon sx={{ fontSize: 48, color: 'grey.400', mb: 1 }} />
                <Typography>Soru fotoğrafını buraya sürükle veya tıkla</Typography>
              </Paper>
            )}

            <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
              <Button
                variant="outlined"
                startIcon={<CameraIcon />}
                onClick={() => cameraInputRef.current?.click()}
                fullWidth
              >
                Kamera
              </Button>
              <Button
                variant="outlined"
                startIcon={<UploadIcon />}
                onClick={() => fileInputRef.current?.click()}
                fullWidth
              >
                Galeri
              </Button>
            </Stack>

            {selectedFile && (
              <Button
                variant="contained"
                startIcon={<SearchIcon />}
                onClick={handleUpload}
                fullWidth
                sx={{ mt: 2 }}
                size="large"
              >
                Soruyu Ara
              </Button>
            )}

            {/* Hidden file inputs */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              hidden
              onChange={handleFileSelect}
            />
            <input
              ref={cameraInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              hidden
              onChange={handleFileSelect}
            />
          </CardContent>
        </Card>
      )}

      {/* Processing State */}
      {state === 'processing' && (
        <Card variant="outlined">
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <CircularProgress size={48} sx={{ mb: 2 }} />
            <Typography variant="h6">Soru analiz ediliyor...</Typography>
            <Typography variant="body2" color="text.secondary">
              OCR ile metin çıkarılıyor ve benzer sorular aranıyor
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Results State */}
      {state === 'results' && uploadResult && (
        <Box>
          <Card variant="outlined" sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">
                OCR Sonucu ({uploadResult.processing_time_ms}ms)
              </Typography>
              <Typography variant="body2" sx={{ mt: 1, fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                {uploadResult.ocr_text.slice(0, 200)}
                {uploadResult.ocr_text.length > 200 ? '...' : ''}
              </Typography>
            </CardContent>
          </Card>

          {uploadResult.similar_questions.length > 0 ? (
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                  Benzer Sorular ({uploadResult.similar_questions.length})
                </Typography>
                <List disablePadding>
                  {uploadResult.similar_questions.map((q, idx) => (
                    <Box key={q.question_id}>
                      {idx > 0 && <Divider />}
                      <ListItem disablePadding>
                        <ListItemButton onClick={() => handleViewSolution(q.question_id)} disabled={aiLoading}>
                          <ListItemText
                            primary={q.question_text.slice(0, 100) + (q.question_text.length > 100 ? '...' : '')}
                            secondary={
                              <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }}>
                                <Chip label={q.subject} size="small" />
                                <Chip label={q.topic} size="small" variant="outlined" />
                                <Chip
                                  label={`%${Math.round(q.similarity * 100)} benzerlik`}
                                  size="small"
                                  color={q.similarity > 0.8 ? 'success' : 'default'}
                                />
                              </Stack>
                            }
                          />
                        </ListItemButton>
                      </ListItem>
                    </Box>
                  ))}
                </List>
              </CardContent>
            </Card>
          ) : (
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="text.secondary" sx={{ mb: 2 }}>
                  Benzer soru bulunamadı. AI ile çözmek ister misin?
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<AIIcon />}
                  onClick={handleAISolve}
                  disabled={aiLoading}
                >
                  {aiLoading ? 'AI Çözüyor...' : 'AI ile Çöz'}
                </Button>
              </CardContent>
            </Card>
          )}

          <Button
            startIcon={<BackIcon />}
            onClick={handleReset}
            sx={{ mt: 2 }}
          >
            Yeni Soru
          </Button>
        </Box>
      )}

      {/* Solution State */}
      {state === 'solution' && solution && (
        <Box>
          <Card variant="outlined">
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
                <Typography variant="subtitle1" fontWeight={600}>
                  Çözüm
                </Typography>
                <Chip
                  label={solution.source === 'database' ? 'Veritabanı' : 'AI Üretim'}
                  size="small"
                  color={solution.source === 'database' ? 'success' : 'info'}
                />
              </Stack>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {solution.solution_text}
              </Typography>
            </CardContent>
          </Card>

          <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
            <Button startIcon={<BackIcon />} onClick={() => setState('results')}>
              Sonuçlara Dön
            </Button>
            <Button variant="outlined" onClick={handleReset}>
              Yeni Soru
            </Button>
          </Stack>
        </Box>
      )}

      {/* Error State */}
      {state === 'error' && (
        <Card variant="outlined">
          <CardContent sx={{ textAlign: 'center' }}>
            <Typography color="error" sx={{ mb: 2 }}>
              İşlem sırasında bir hata oluştu.
            </Typography>
            <Button variant="contained" onClick={handleReset}>
              Tekrar Dene
            </Button>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
