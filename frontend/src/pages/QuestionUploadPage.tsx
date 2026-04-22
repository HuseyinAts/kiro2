/**
 * Question Upload Page
 * ====================
 * YOLO tabanlı soru tespit sayfası.
 *
 * Özellikler:
 * - Drag & drop görsel yükleme
 * - Otomatik soru tespiti
 * - Tespit sonuçlarını görselleştirme
 * - Soruları kırpma ve kaydetme
 * - Toplu işlem desteği
 */

import {
  CameraAlt as CameraIcon,
  Collections as GalleryIcon,
  CloudUpload as UploadIcon,
  AutoAwesome as AIIcon,
  CheckCircle as SuccessIcon,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  Alert,
  Button,
  Tabs,
  Tab,
  Chip,
} from '@mui/material';
import { useState } from 'react';

import YOLOQuestionDetector from '../components/QuestionParser/YOLOQuestionDetector';
import {
  Detection,
  DetectionResult,
  CroppedQuestion,
  CLASS_LABELS,
} from '../services/yoloService';

// Tab panel component
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index} style={{ paddingTop: 16 }}>
    {value === index && children}
  </div>
);

// Main Page Component
const QuestionUploadPage: React.FC = () => {
  const [tab, setTab] = useState(0);
  const [_detectedQuestions, setDetectedQuestions] = useState<Detection[]>([]);
  const [lastResult, setLastResult] = useState<DetectionResult | null>(null);
  const [croppedQuestions, setCroppedQuestions] = useState<CroppedQuestion[]>([]);
  const [savedCount, setSavedCount] = useState(0);

  // Handle detection complete
  const handleQuestionsDetected = (questions: Detection[], result: DetectionResult) => {
    setDetectedQuestions(questions);
    setLastResult(result);
  };

  // Handle cropped questions
  const handleQuestionsCropped = (cropped: CroppedQuestion[]) => {
    setCroppedQuestions(cropped);
  };

  // Kırpılmış görsellerde henüz metin/şık yok; kalıcı kayıt question-crud + OCR/elle giriş gerektirir
  const handleSaveToBank = async () => {
    if (croppedQuestions.length === 0) {
      alert('Önce soruları kırpın.');
      return;
    }
    setSavedCount(0);
    alert(
      `${croppedQuestions.length} görüntü hazır. ` +
        'Soru metni ve şıklar tespit edilmediği için toplu kayıt bu ekranda yapılmaz; ' +
        'soruları soru yönetimi ekranından girin veya görüntüyü dışa aktarın.',
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CameraIcon color="primary" />
          Soru Yükleme
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Sınav sayfalarını yükleyin, yapay zeka ile soruları otomatik tespit edin.
        </Typography>
      </Box>

      {/* Stats Cards */}
      {lastResult && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={6} sm={3}>
            <Card sx={{ bgcolor: 'primary.light', color: 'primary.contrastText' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3">{lastResult.questions_count}</Typography>
                <Typography variant="body2">Tespit Edilen Soru</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card sx={{ bgcolor: 'secondary.light', color: 'secondary.contrastText' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3">{lastResult.total_detections}</Typography>
                <Typography variant="body2">Toplam Tespit</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card sx={{ bgcolor: 'success.light', color: 'success.contrastText' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3">{croppedQuestions.length}</Typography>
                <Typography variant="body2">Kırpılmış Soru</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card sx={{ bgcolor: 'info.light', color: 'info.contrastText' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3">{lastResult.processing_time_ms.toFixed(0)}</Typography>
                <Typography variant="body2">ms İşlem Süresi</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="fullWidth">
          <Tab icon={<UploadIcon />} label="Tek Görsel" />
          <Tab icon={<GalleryIcon />} label="Toplu Yükleme" disabled />
          <Tab icon={<CameraIcon />} label="Kamera" disabled />
        </Tabs>
      </Paper>

      {/* Single Upload Tab */}
      <TabPanel value={tab} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <YOLOQuestionDetector
              onQuestionsDetected={handleQuestionsDetected}
              onQuestionsCropped={handleQuestionsCropped}
              confidence={0.25}
              autoCrop={false}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            {/* Instructions */}
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AIIcon color="primary" />
                Nasıl Çalışır?
              </Typography>
              <Box component="ol" sx={{ pl: 2, m: 0 }}>
                <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                  Sınav sayfası görselini yükleyin
                </Typography>
                <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                  &quot;Soruları Tespit Et&quot; butonuna tıklayın
                </Typography>
                <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                  AI otomatik olarak soruları, cevapları ve metadata&apos;yı tespit eder
                </Typography>
                <Typography component="li" variant="body2">
                  Tespit edilen soruları kırpıp soru bankasına kaydedin
                </Typography>
              </Box>
            </Paper>

            {/* Detection Classes */}
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Tespit Edilen Öğeler
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {Object.entries(CLASS_LABELS).map(([key, label]) => (
                  <Chip key={key} label={label} size="small" variant="outlined" />
                ))}
              </Box>
            </Paper>

            {/* Model Info */}
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Model Bilgisi
              </Typography>
              <Typography variant="body2" color="textSecondary">
                YOLO11m • mAP@50: 97.5%
              </Typography>
              <Typography variant="body2" color="textSecondary">
                141 görsel ile eğitildi
              </Typography>
            </Paper>

            {/* Save Button */}
            {croppedQuestions.length > 0 && (
              <Button
                variant="contained"
                color="success"
                fullWidth
                size="large"
                startIcon={<SuccessIcon />}
                onClick={handleSaveToBank}
              >
                {croppedQuestions.length} Soruyu Kaydet
              </Button>
            )}
          </Grid>
        </Grid>
      </TabPanel>

      {/* Batch Upload Tab */}
      <TabPanel value={tab} index={1}>
        <Alert severity="info">
          Toplu yükleme özelliği yakında eklenecek.
        </Alert>
      </TabPanel>

      {/* Camera Tab */}
      <TabPanel value={tab} index={2}>
        <Alert severity="info">
          Kamera ile çekim özelliği yakında eklenecek.
        </Alert>
      </TabPanel>

      {/* Saved Success */}
      {savedCount > 0 && (
        <Alert severity="success" sx={{ mt: 2 }} onClose={() => setSavedCount(0)}>
          {savedCount} soru başarıyla soru bankasına kaydedildi!
        </Alert>
      )}
    </Container>
  );
};

export default QuestionUploadPage;
