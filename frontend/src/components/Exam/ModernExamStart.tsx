/**
 * Modern Sınav Başlatma Bileşeni
 * Glassmorphism tasarım ile ÖSYM formatında sınav hazırlık arayüzü
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
  Computer,
  Close,
  CloudDone,
  CloudOff,
  Wifi,
  WifiOff,
} from '@mui/icons-material';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Alert,
  Checkbox,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import * as React from 'react';
import {  useState  } from 'react';

import { examService, ExamType } from '../../services/examService';
import { GlassCard } from '@/components/ui/GlassCard';
import { ModernButton } from '@/components/ui/ModernButton';
import { ModernLoader } from '@/components/ui/ModernLoader';
import modernColors from '@/theme/modern-colors';

interface ModernExamStartProps {
  examType: ExamType
  sessionId?: string
  onStart: (sessionId: string) => void
  onCancel?: () => void
}

export const ModernExamStart: React.FC<ModernExamStartProps> = ({
  examType,
  sessionId,
  onStart,
  onCancel,
}) => {
  // State yönetimi
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showInstructions, setShowInstructions] = useState(false);
  const [showSystemCheck, setShowSystemCheck] = useState(false);
  const [systemCheckResults, setSystemCheckResults] = useState<Record<string, boolean>>({});
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [readInstructions, setReadInstructions] = useState(false);
  const [systemCheckPassed, setSystemCheckPassed] = useState(false);
  const [checkingSystem, setCheckingSystem] = useState(false);

  // Sınav bilgileri
  const examInfo = examService.getExamDuration(examType);
  const examDescription = examService.getExamTypeDescription(examType);

  // Exam type configurations
  const examTypes = {
    [ExamType.TYT]: {
      name: 'TYT (Temel Yeterlilik Testi)',
      icon: <School sx={{ fontSize: 48 }} />,
      gradient: modernColors.gradients.primary,
      questionCount: examInfo.total_questions,
      duration: `${examInfo.duration_minutes} dakika`,
      sections: [
        { name: 'Türkçe', count: 40 },
        { name: 'Matematik', count: 40 },
        { name: 'Fen Bilimleri', count: 20 },
        { name: 'Sosyal Bilimler', count: 20 },
      ],
    },
    [ExamType.AYT]: {
      name: 'AYT (Alan Yeterlilik Testi)',
      icon: <MenuBook sx={{ fontSize: 48 }} />,
      gradient: modernColors.gradients.forest,
      questionCount: examInfo.total_questions,
      duration: `${examInfo.duration_minutes} dakika`,
      sections: [
        { name: 'Matematik', count: 40 },
        { name: 'Fen Bilimleri', count: 40 },
      ],
    },
    [ExamType.YDT]: {
      name: 'YDT (Yabancı Dil Testi)',
      icon: <Psychology sx={{ fontSize: 48 }} />,
      gradient: modernColors.gradients.ocean,
      questionCount: examInfo.total_questions,
      duration: `${examInfo.duration_minutes} dakika`,
      sections: [{ name: 'Yabancı Dil', count: 80 }],
    },
    [ExamType.LGS]: {
      name: 'LGS (Liselere Geçiş Sınavı)',
      icon: <Speed sx={{ fontSize: 48 }} />,
      gradient: modernColors.gradients.sunset,
      questionCount: examInfo.total_questions,
      duration: `${examInfo.duration_minutes} dakika`,
      sections: [
        { name: 'Türkçe', count: 20 },
        { name: 'Matematik', count: 20 },
        { name: 'Fen Bilimleri', count: 20 },
        { name: 'İngilizce', count: 10 },
        { name: 'Din Kültürü', count: 10 },
      ],
    },
  };

  const currentExam = examTypes[examType];

  /**
   * Sistem kontrolü
   */
  const performSystemCheck = async () => {
    setCheckingSystem(true);
    setShowSystemCheck(true);

    const checks = {
      internet: false,
      browser: false,
      javascript: false,
      localStorage: false,
    };

    try {
      // İnternet kontrolü
      try {
        const response = await fetch('/health');
        checks.internet = response.ok;
      } catch {
        checks.internet = false;
      }

      // Tarayıcı uyumluluğu
      checks.browser = !!(window.WebSocket && window.localStorage && window.JSON);

      // JavaScript
      checks.javascript = true;

      // LocalStorage
      try {
        localStorage.setItem('test', 'test');
        localStorage.removeItem('test');
        checks.localStorage = true;
      } catch {
        checks.localStorage = false;
      }
    } catch (error) {
      console.error('Sistem kontrolü hatası:', error);
    }

    setSystemCheckResults(checks);
    setSystemCheckPassed(Object.values(checks).every((v) => v));
    setCheckingSystem(false);
  };

  /**
   * Sınav başlatma
   */
  const handleStartExam = async () => {
    if (!acceptedTerms || !readInstructions) {
      setError('Lütfen tüm şartları kabul edin ve talimatları okuyun');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      if (sessionId) {
        // Mevcut session'ı başlat (ModernExamStartPage zaten oluşturmuş)
        await examService.startExam(sessionId);
        onStart(sessionId);
      } else {
        // Fallback: session yoksa yeni oluştur
        const session = await examService.createExam({
          exam_type: examType,
          custom_config: examInfo.difficulty_distribution ? {
            difficulty_distribution: examInfo.difficulty_distribution,
          } : undefined,
        });
        onStart(session.session_id);
      }
    } catch (err: any) {
      setError(err.message || 'Sınav başlatılamadı');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: currentExam.gradient,
        py: 4,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Animated Background */}
      <motion.div
        style={{
          position: 'absolute',
          width: '500px',
          height: '500px',
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.1)',
          top: '-200px',
          right: '-100px',
          filter: 'blur(80px)',
        }}
        animate={{
          scale: [1, 1.2, 1],
          rotate: [0, 90, 0],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: 'linear',
        }}
      />

      <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 10 }}
            >
              <Box
                sx={{
                  width: 100,
                  height: 100,
                  borderRadius: '24px',
                  background: 'rgba(255, 255, 255, 0.2)',
                  backdropFilter: 'blur(10px)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto',
                  boxShadow: modernColors.shadow.modern,
                  color: 'white',
                }}
              >
                {currentExam.icon}
              </Box>
            </motion.div>

            <Typography
              variant="h3"
              sx={{
                fontWeight: 800,
                color: 'white',
                mt: 3,
                textShadow: '0 2px 10px rgba(0,0,0,0.2)',
              }}
            >
              {currentExam.name}
            </Typography>
            <Typography
              variant="body1"
              sx={{
                color: 'rgba(255,255,255,0.9)',
                mt: 1,
              }}
            >
              {examDescription}
            </Typography>
          </Box>

          {/* Error Alert */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <Alert severity="error" sx={{ mb: 3 }}>
                  {error}
                </Alert>
              </motion.div>
            )}
          </AnimatePresence>

          <Grid container spacing={3}>
            {/* Exam Info Card */}
            <Grid item xs={12} md={8}>
              <GlassCard
                title="Sınav Bilgileri"
                gradient={currentExam.gradient}
                elevated
              >
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={4}>
                    <Box
                      sx={{
                        p: 2,
                        background: modernColors.glass.white.light,
                        borderRadius: '12px',
                        textAlign: 'center',
                      }}
                    >
                      <Assignment sx={{ fontSize: 32, color: 'primary.main', mb: 1 }} />
                      <Typography variant="h5" fontWeight={800}>
                        {currentExam.questionCount}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Soru
                      </Typography>
                    </Box>
                  </Grid>

                  <Grid item xs={12} sm={4}>
                    <Box
                      sx={{
                        p: 2,
                        background: modernColors.glass.white.light,
                        borderRadius: '12px',
                        textAlign: 'center',
                      }}
                    >
                      <Timer sx={{ fontSize: 32, color: 'warning.main', mb: 1 }} />
                      <Typography variant="h5" fontWeight={800}>
                        {currentExam.duration}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Süre
                      </Typography>
                    </Box>
                  </Grid>

                  <Grid item xs={12} sm={4}>
                    <Box
                      sx={{
                        p: 2,
                        background: modernColors.glass.white.light,
                        borderRadius: '12px',
                        textAlign: 'center',
                      }}
                    >
                      <School sx={{ fontSize: 32, color: 'success.main', mb: 1 }} />
                      <Typography variant="h5" fontWeight={800}>
                        {currentExam.sections.length}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Bölüm
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                {/* Sections */}
                <Box sx={{ mt: 3 }}>
                  <Typography variant="h6" fontWeight={700} gutterBottom>
                    Sınav Bölümleri
                  </Typography>
                  <List>
                    {currentExam.sections.map((section, index) => (
                      <ListItem
                        key={index}
                        sx={{
                          background: modernColors.glass.white.light,
                          borderRadius: '8px',
                          mb: 1,
                        }}
                      >
                        <ListItemIcon>
                          <CheckCircle sx={{ color: 'success.main' }} />
                        </ListItemIcon>
                        <ListItemText
                          primary={section.name}
                          secondary={`${section.count} soru`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              </GlassCard>
            </Grid>

            {/* Checklist Card */}
            <Grid item xs={12} md={4}>
              <GlassCard title="Hazırlık Kontrol Listesi" gradient={modernColors.gradients.warning} elevated>
                <List>
                  <ListItem>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={readInstructions}
                          onChange={(e) => setReadInstructions(e.target.checked)}
                          sx={{ color: 'white' }}
                        />
                      }
                      label={
                        <Typography variant="body2" sx={{ color: 'white' }}>
                          Sınav talimatlarını okudum
                        </Typography>
                      }
                    />
                  </ListItem>

                  <ListItem>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={systemCheckPassed}
                          disabled
                          sx={{ color: systemCheckPassed ? 'success.main' : 'error.main' }}
                        />
                      }
                      label={
                        <Typography variant="body2" sx={{ color: 'white' }}>
                          Sistem kontrolü tamamlandı
                        </Typography>
                      }
                    />
                  </ListItem>

                  <ListItem>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={acceptedTerms}
                          onChange={(e) => setAcceptedTerms(e.target.checked)}
                          sx={{ color: 'white' }}
                        />
                      }
                      label={
                        <Typography variant="body2" sx={{ color: 'white' }}>
                          Sınav kurallarını kabul ediyorum
                        </Typography>
                      }
                    />
                  </ListItem>
                </List>

                <ModernButton
                  fullWidth
                  variant="glass"
                  onClick={() => setShowInstructions(true)}
                  sx={{ mb: 2 }}
                >
                  Talimatları Oku
                </ModernButton>

                <ModernButton
                  fullWidth
                  variant="glass"
                  onClick={performSystemCheck}
                  loading={checkingSystem}
                >
                  Sistem Kontrolü
                </ModernButton>
              </GlassCard>
            </Grid>

            {/* Start Button */}
            <Grid item xs={12}>
              <GlassCard elevated>
                <Box sx={{ textAlign: 'center' }}>
                  <ModernButton
                    variant="gradient"
                    gradient={currentExam.gradient}
                    glow
                    size="large"
                    loading={loading}
                    icon={<PlayArrow />}
                    disabled={!acceptedTerms || !readInstructions || !systemCheckPassed}
                    onClick={handleStartExam}
                    sx={{
                      minWidth: 300,
                      py: 2,
                      fontSize: '1.2rem',
                    }}
                  >
                    Sınavı Başlat
                  </ModernButton>

                  {onCancel && (
                    <Button
                      onClick={onCancel}
                      sx={{ mt: 2, color: 'text.secondary' }}
                    >
                      İptal
                    </Button>
                  )}
                </Box>
              </GlassCard>
            </Grid>
          </Grid>
        </motion.div>
      </Container>

      {/* Instructions Dialog */}
      <Dialog
        open={showInstructions}
        onClose={() => setShowInstructions(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            background: modernColors.glass.white.light,
            backdropFilter: 'blur(16px)',
          },
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6" fontWeight={700}>
              Sınav Talimatları
            </Typography>
            <IconButton onClick={() => setShowInstructions(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <List>
            <ListItem>
              <ListItemIcon>
                <Info color="primary" />
              </ListItemIcon>
              <ListItemText
                primary="Süre Kısıtlaması"
                secondary={`Sınav süresi ${currentExam.duration}'dır. Süre bittiğinde otomatik olarak tamamlanacaktır.`}
              />
            </ListItem>

            <ListItem>
              <ListItemIcon>
                <Assignment color="primary" />
              </ListItemIcon>
              <ListItemText
                primary="Soru Sayısı"
                secondary={`Toplam ${currentExam.questionCount} soru cevaplayacaksınız.`}
              />
            </ListItem>

            <ListItem>
              <ListItemIcon>
                <CheckCircle color="success" />
              </ListItemIcon>
              <ListItemText
                primary="Cevaplama"
                secondary="Her soru için tek bir şık işaretleyebilirsiniz. İşaretinizi değiştirebilirsiniz."
              />
            </ListItem>

            <ListItem>
              <ListItemIcon>
                <Warning color="warning" />
              </ListItemIcon>
              <ListItemText
                primary="Otomatik Kayıt"
                secondary="Cevaplarınız otomatik olarak kaydedilmektedir."
              />
            </ListItem>
          </List>
        </DialogContent>
        <DialogActions>
          <ModernButton
            variant="gradient"
            gradient={currentExam.gradient}
            onClick={() => {
              setReadInstructions(true);
              setShowInstructions(false);
            }}
          >
            Anladım
          </ModernButton>
        </DialogActions>
      </Dialog>

      {/* System Check Dialog */}
      <Dialog
        open={showSystemCheck}
        onClose={() => setShowSystemCheck(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            background: modernColors.glass.white.light,
            backdropFilter: 'blur(16px)',
          },
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6" fontWeight={700}>
              Sistem Kontrolü
            </Typography>
            <IconButton onClick={() => setShowSystemCheck(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {checkingSystem ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <ModernLoader message="Sistem kontrol ediliyor..." />
            </Box>
          ) : (
            <List>
              <ListItem>
                <ListItemIcon>
                  {systemCheckResults.internet ? (
                    <Wifi sx={{ color: 'success.main' }} />
                  ) : (
                    <WifiOff sx={{ color: 'error.main' }} />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary="İnternet Bağlantısı"
                  secondary={systemCheckResults.internet ? 'Bağlı' : 'Bağlı değil'}
                />
                {systemCheckResults.internet ? <CheckCircle color="success" /> : <Warning color="error" />}
              </ListItem>

              <ListItem>
                <ListItemIcon>
                  <Computer
                    sx={{
                      color: systemCheckResults.browser ? 'success.main' : 'error.main',
                    }}
                  />
                </ListItemIcon>
                <ListItemText
                  primary="Tarayıcı Uyumluluğu"
                  secondary={systemCheckResults.browser ? 'Uyumlu' : 'Uyumlu değil'}
                />
                {systemCheckResults.browser ? <CheckCircle color="success" /> : <Warning color="error" />}
              </ListItem>

              <ListItem>
                <ListItemIcon>
                  {systemCheckResults.localStorage ? (
                    <CloudDone sx={{ color: 'success.main' }} />
                  ) : (
                    <CloudOff sx={{ color: 'error.main' }} />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary="Yerel Depolama"
                  secondary={systemCheckResults.localStorage ? 'Kullanılabilir' : 'Kullanılamaz'}
                />
                {systemCheckResults.localStorage ? <CheckCircle color="success" /> : <Warning color="error" />}
              </ListItem>
            </List>
          )}

          {!checkingSystem && systemCheckPassed && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Sisteminiz sınav için hazır!
            </Alert>
          )}

          {!checkingSystem && !systemCheckPassed && (
            <Alert severity="error" sx={{ mt: 2 }}>
              Bazı sistem kontrolleri başarısız oldu. Lütfen internet bağlantınızı kontrol edin ve tarayıcınızı güncelleyin.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <ModernButton onClick={() => setShowSystemCheck(false)}>Kapat</ModernButton>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ModernExamStart;
