/**
 * Sınav Başlatma Bileşeni
 * ÖSYM formatında sınav öncesi hazırlık ve başlatma arayüzü
 */
import {
  PlayArrow,
  Timer,
  Assignment,
  CheckCircle,
  Warning,
  Info,
  School,
  MenuBook,
  Psychology,
  Speed,
  VolumeUp,
  Visibility,
  TouchApp,
  Computer,
} from '@mui/icons-material';
import {
  Paper,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Alert,
  Checkbox,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
} from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';
import {  useState  } from 'react';

import { examService, ExamType } from '../../services/examService';

interface ExamStartProps {
  examType: ExamType
  onStart: (sessionId: string) => void
  onCancel?: () => void
}

export const ExamStart: React.FC<ExamStartProps> = ({ examType, onStart, onCancel }) => {
  // State yönetimi
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showInstructions, setShowInstructions] = useState(false);
  const [, setShowSystemCheck] = useState(false);
  const [systemCheckResults, setSystemCheckResults] = useState<Record<string, boolean>>({});
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [readInstructions, setReadInstructions] = useState(false);
  const [systemCheckPassed, setSystemCheckPassed] = useState(false);

  /**
   * Sınav bilgilerini getir
   */
  const examInfo = examService.getExamDuration(examType);
  const examDescription = examService.getExamTypeDescription(examType);

  /**
   * Sistem kontrolü yap
   */
  const performSystemCheck = async () => {
    setShowSystemCheck(true);
    setLoading(true);

    const checks = {
      internet: false,
      browser: false,
      javascript: false,
      localStorage: false,
      webSocket: false,
      camera: false,
      microphone: false,
    };

    try {
      // İnternet bağlantısı kontrolü
      const response = await fetch('/health');
      checks.internet = response.ok;

      // Tarayıcı uyumluluğu
      checks.browser = !!(window.WebSocket && window.localStorage && window.JSON);

      // JavaScript aktif mi
      checks.javascript = true;

      // LocalStorage kullanılabilir mi
      try {
        localStorage.setItem('test', 'test');
        localStorage.removeItem('test');
        checks.localStorage = true;
      } catch {
        checks.localStorage = false;
      }

      // WebSocket desteği
      checks.webSocket = !!window.WebSocket;

      // Kamera erişimi (opsiyonel)
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        checks.camera = true;
        stream.getTracks().forEach(track => track.stop());
      } catch {
        checks.camera = false;
      }

      // Mikrofon erişimi (opsiyonel)
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        checks.microphone = true;
        stream.getTracks().forEach(track => track.stop());
      } catch {
        checks.microphone = false;
      }

    } catch (error) {
      console.error('Sistem kontrolü hatası:', error);
    }

    setSystemCheckResults(checks);

    // Temel kontroller geçildi mi
    const basicChecksPassed = checks.internet && checks.browser && checks.javascript && checks.localStorage;
    setSystemCheckPassed(basicChecksPassed);

    setLoading(false);
  };

  /**
   * Sınavı başlat
   */
  const handleStartExam = async () => {
    if (!acceptedTerms || !readInstructions) {
      setError('Lütfen tüm koşulları kabul edin ve talimatları okuyun');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Yeni sınav oturumu oluştur
      const session = await examService.createExam({
        exam_type: examType,
        custom_config: {
          system_check_results: systemCheckResults,
          start_time: new Date().toISOString(),
        },
      });

      // Sınavı başlat
      await examService.startExam(session.session_id);

      // Ana bileşene session ID'sini gönder
      onStart(session.session_id);

    } catch (err: any) {
      setError(err.message || 'Sınav başlatılırken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Sınav kuralları ve talimatları
   */
  const examRules = [
    'Sınav süresince başka bir sekme veya uygulama açmayın',
    'Sınav sırasında sayfayı yenilemeyin veya geri butonunu kullanmayın',
    'İnternet bağlantınızın stabil olduğundan emin olun',
    'Cevaplarınız otomatik olarak kaydedilir',
    'Süre bitiminde sınav otomatik olarak tamamlanır',
    'Soru işaretleme özelliğini kullanarak geri dönmek istediğiniz soruları işaretleyebilirsiniz',
    'Her soru için sadece bir cevap seçebilirsiniz',
    'Boş bıraktığınız sorular net hesaplamasını etkilemez',
  ];

  /**
   * Sistem gereksinimleri
   */
  const systemRequirements = [
    { name: 'Güncel web tarayıcısı', icon: <Computer />, required: true },
    { name: 'Stabil internet bağlantısı', icon: <Info />, required: true },
    { name: 'JavaScript desteği', icon: <Psychology />, required: true },
    { name: 'Yerel depolama desteği', icon: <TouchApp />, required: true },
    { name: 'WebSocket desteği', icon: <Speed />, required: true },
    { name: 'Kamera erişimi', icon: <Visibility />, required: false },
    { name: 'Mikrofon erişimi', icon: <VolumeUp />, required: false },
  ];

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Paper elevation={3} sx={{ p: 4, mb: 3, textAlign: 'center' }}>
          <Assignment sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
          <Typography variant="h4" gutterBottom>
            Sınav Başlatma
          </Typography>
          <Typography variant="h6" color="textSecondary" gutterBottom>
            {examDescription}
          </Typography>
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 2 }}>
            <Chip
              icon={<Timer />}
              label={`${examInfo.minutes} dakika`}
              color="primary"
              variant="outlined"
            />
            <Chip
              icon={<MenuBook />}
              label={`${examInfo.questionCount} soru`}
              color="secondary"
              variant="outlined"
            />
          </Box>
        </Paper>
      </motion.div>

      {/* Sınav Bilgileri */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={4}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Timer sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant="h6">Süre</Typography>
                <Typography variant="h4" color="primary">
                  {examInfo.minutes}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  dakika
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center' }}>
                <MenuBook sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
                <Typography variant="h6">Soru Sayısı</Typography>
                <Typography variant="h4" color="secondary">
                  {examInfo.questionCount}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  soru
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center' }}>
                <School sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                <Typography variant="h6">Format</Typography>
                <Typography variant="h4" color="success">
                  ÖSYM
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  uyumlu
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </motion.div>

      {/* Sistem Kontrolü */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              🔧 Sistem Kontrolü
            </Typography>
            <Button
              variant="outlined"
              onClick={performSystemCheck}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : <CheckCircle />}
            >
              {loading ? 'Kontrol Ediliyor...' : 'Sistemi Kontrol Et'}
            </Button>
          </Box>

          {Object.keys(systemCheckResults).length > 0 && (
            <Box>
              <List dense>
                {systemRequirements.map((req, index) => {
                  const checkKey = req.name.toLowerCase().includes('tarayıcı') ? 'browser' :
                                  req.name.toLowerCase().includes('internet') ? 'internet' :
                                  req.name.toLowerCase().includes('javascript') ? 'javascript' :
                                  req.name.toLowerCase().includes('depolama') ? 'localStorage' :
                                  req.name.toLowerCase().includes('websocket') ? 'webSocket' :
                                  req.name.toLowerCase().includes('kamera') ? 'camera' :
                                  req.name.toLowerCase().includes('mikrofon') ? 'microphone' : '';

                  const passed = systemCheckResults[checkKey];

                  return (
                    <ListItem key={index}>
                      <ListItemIcon>
                        {req.icon}
                      </ListItemIcon>
                      <ListItemText
                        primary={req.name}
                        secondary={req.required ? 'Gerekli' : 'Opsiyonel'}
                      />
                      <Chip
                        label={passed ? 'Geçti' : 'Başarısız'}
                        color={passed ? 'success' : req.required ? 'error' : 'warning'}
                        size="small"
                        icon={passed ? <CheckCircle /> : <Warning />}
                      />
                    </ListItem>
                  );
                })}
              </List>

              {systemCheckPassed ? (
                <Alert severity="success" sx={{ mt: 2 }}>
                  Sistem kontrolü başarıyla tamamlandı. Sınava başlayabilirsiniz.
                </Alert>
              ) : (
                <Alert severity="error" sx={{ mt: 2 }}>
                  Sistem kontrolü başarısız. Lütfen gerekli düzenlemeleri yapın ve tekrar deneyin.
                </Alert>
              )}
            </Box>
          )}
        </Paper>
      </motion.div>

      {/* Koşullar ve Onaylar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            📋 Sınav Koşulları ve Onaylar
          </Typography>

          <Box sx={{ mb: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={readInstructions}
                  onChange={(e) => setReadInstructions(e.target.checked)}
                />
              }
              label="Sınav talimatlarını okudum ve anladım"
            />
            <Button
              variant="text"
              size="small"
              onClick={() => setShowInstructions(true)}
              sx={{ ml: 1 }}
            >
              Talimatları Görüntüle
            </Button>
          </Box>

          <FormControlLabel
            control={
              <Checkbox
                checked={acceptedTerms}
                onChange={(e) => setAcceptedTerms(e.target.checked)}
              />
            }
            label="Sınav kurallarını kabul ediyorum ve uyacağımı taahhüt ediyorum"
          />
        </Paper>
      </motion.div>

      {/* Hata Mesajı */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Eylem Butonları */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
      >
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          {onCancel && (
            <Button
              variant="outlined"
              size="medium"
              onClick={onCancel}
              disabled={loading}
            >
              İptal
            </Button>
          )}
          <Button
            variant="contained"
            size="medium"
            startIcon={loading ? <CircularProgress size={20} /> : <PlayArrow />}
            onClick={handleStartExam}
            disabled={loading || !acceptedTerms || !readInstructions || (Object.keys(systemCheckResults).length > 0 && !systemCheckPassed)}
            sx={{ minWidth: 200 }}
          >
            {loading ? 'Başlatılıyor...' : 'Sınava Başla'}
          </Button>
        </Box>
      </motion.div>

      {/* Talimatlar Dialog */}
      <Dialog
        open={showInstructions}
        onClose={() => setShowInstructions(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          📖 Sınav Talimatları ve Kuralları
        </DialogTitle>
        <DialogContent>
          <Typography variant="h6" gutterBottom>
            Genel Kurallar:
          </Typography>
          <List>
            {examRules.map((rule, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <CheckCircle color="primary" />
                </ListItemIcon>
                <ListItemText primary={rule} />
              </ListItem>
            ))}
          </List>

          <Divider sx={{ my: 2 }} />

          <Typography variant="h6" gutterBottom>
            Teknik Bilgiler:
          </Typography>
          <Typography variant="body2" paragraph>
            • Sınav sırasında internet bağlantınız kesilirse, sistem otomatik olarak yeniden bağlanmaya çalışacaktır.
          </Typography>
          <Typography variant="body2" paragraph>
            • Cevaplarınız her 30 saniyede bir otomatik olarak kaydedilir.
          </Typography>
          <Typography variant="body2" paragraph>
            • Sınav süresinin son 5 dakikasında uyarı alacaksınız.
          </Typography>
          <Typography variant="body2" paragraph>
            • Süre bitiminde sınav otomatik olarak tamamlanır ve sonuçlarınız hesaplanır.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowInstructions(false)} variant="contained">
            Anladım
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ExamStart;