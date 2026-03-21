import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import ImageIcon from '@mui/icons-material/Image';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Grid,
  Chip,
  Paper,
} from '@mui/material';
import * as React from 'react';
import {  useState  } from 'react';

interface Detection {
  class: string;
  confidence: number;
  bbox: [number, number, number, number];
}

interface DetectionResult {
  image_path: string;
  num_detections: number;
  detections: Detection[];
  processing_time: number;
}

const YOLODetectionPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [error, setError] = useState<string>('');

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setResult(null);
      setError('');

      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDetect = async () => {
    if (!selectedFile) {return;}

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('/api/v1/yolo/detect', {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const getClassColor = (className: string) => {
    const colors: Record<string, string> = {
      soru: 'primary',
      cevaplar: 'success',
      zorluk_seviyesi: 'warning',
      kitap: 'info',
      test_no: 'secondary',
      sayfa: 'default',
    };
    return colors[className] || 'default';
  };

  const getClassLabel = (className: string) => {
    const labels: Record<string, string> = {
      soru: 'Soru',
      cevaplar: 'Cevaplar',
      zorluk_seviyesi: 'Zorluk Seviyesi',
      kitap: 'Kitap',
      test_no: 'Test No',
      sayfa: 'Sayfa',
    };
    return labels[className] || className;
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        YOLO Soru Tespit Sistemi
      </Typography>

      <Grid container spacing={3}>
        {/* Upload Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Görsel Yükle
              </Typography>

              <input
                accept="image/*"
                style={{ display: 'none' }}
                id="raised-button-file"
                type="file"
                onChange={handleFileSelect}
              />
              <label htmlFor="raised-button-file">
                <Button
                  variant="outlined"
                  component="span"
                  startIcon={<CloudUploadIcon />}
                  fullWidth
                  sx={{ mb: 2 }}
                >
                  Görsel Seç
                </Button>
              </label>

              {preview && (
                <Paper sx={{ p: 2, mb: 2, textAlign: 'center' }}>
                  <img
                    src={preview}
                    alt="Preview"
                    style={{ maxWidth: '100%', maxHeight: '400px' }}
                  />
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    {selectedFile?.name}
                  </Typography>
                </Paper>
              )}

              <Button
                variant="contained"
                fullWidth
                onClick={handleDetect}
                disabled={!selectedFile || loading}
                startIcon={loading ? <CircularProgress size={20} /> : <ImageIcon />}
              >
                {loading ? 'Tespit Ediliyor...' : 'Soruları Tespit Et'}
              </Button>

              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Results Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Tespit Sonuçları
              </Typography>

              {result ? (
                <>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      <strong>Toplam Tespit:</strong> {result.num_detections}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      <strong>İşlem Süresi:</strong> {result.processing_time.toFixed(2)}s
                    </Typography>
                  </Box>

                  {result.detections.length > 0 ? (
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Tespit Edilen Nesneler:
                      </Typography>
                      {result.detections.map((detection, index) => (
                        <Paper
                          key={index}
                          sx={{ p: 2, mb: 1, bgcolor: 'background.default' }}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Box>
                              <Chip
                                label={getClassLabel(detection.class)}
                                color={getClassColor(detection.class) as any}
                                size="small"
                                sx={{ mr: 1 }}
                              />
                              <Chip
                                label={`${(detection.confidence * 100).toFixed(1)}%`}
                                size="small"
                                variant="outlined"
                              />
                            </Box>
                            <CheckCircleIcon color="success" />
                          </Box>
                          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                            Konum: [{detection.bbox.map(b => b.toFixed(0)).join(', ')}]
                          </Typography>
                        </Paper>
                      ))}
                    </Box>
                  ) : (
                    <Alert severity="info">Hiç tespit yapılamadı</Alert>
                  )}
                </>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <ImageIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                  <Typography variant="body2" color="text.secondary">
                    Tespit sonuçları burada görünecek
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default YOLODetectionPage;
