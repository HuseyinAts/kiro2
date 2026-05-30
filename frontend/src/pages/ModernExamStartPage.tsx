/**
 * Modern Exam Start Page
 * Glassmorphism ile sınav başlatma deneyimi
 */

import {
  School as SchoolIcon,
  Timer as TimerIcon,
  Psychology as PsychologyIcon,
  TrendingUp as TrendingUpIcon,
  Start as StartIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  TextField,
  MenuItem,
  LinearProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent,
} from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';
import {  useState  } from 'react';
import { useNavigate } from 'react-router-dom';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { modernColors } from '../theme/modern-colors';
import { apiRequest } from '../utils/apiHelpers';

interface ExamConfig {
  exam_type: string
  subject: string
  difficulty: string
  question_count: number
  time_limit: number
}

export const ModernExamStartPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [config, setConfig] = useState<ExamConfig>({
    exam_type: 'TYT',
    subject: 'Matematik',
    difficulty: 'orta',
    question_count: 40,
    time_limit: 80,
  });

  const examTypes = [
    { value: 'TYT', label: 'TYT - Temel Yeterlilik Testi', icon: '📚' },
    { value: 'AYT', label: 'AYT - Alan Yeterlilik Testi', icon: '🎓' },
  ];

  const subjects: Record<string, string[]> = {
    TYT: ['Matematik', 'Geometri', 'Türkçe', 'Fizik', 'Kimya', 'Biyoloji', 'Tarih', 'Sosyal'],
    AYT: ['Matematik', 'Geometri', 'Fizik', 'Kimya', 'Biyoloji', 'Edebiyat', 'Tarih'],
  };

  const difficulties = [
    { value: 'kolay', label: 'Kolay', color: modernColors.gradients.success, icon: '😊' },
    { value: 'orta', label: 'Orta', color: modernColors.gradients.primary, icon: '🤔' },
    { value: 'zor', label: 'Zor', color: modernColors.gradients.warning, icon: '😤' },
    { value: 'cok_zor', label: 'Çok Zor', color: modernColors.gradients.error, icon: '🔥' },
  ];

  const handleChange = (field: keyof ExamConfig, value: string | number) => {
    setConfig(prev => ({ ...prev, [field]: value }));
    setError(null);
  };

  const handleStartExam = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiRequest<{ session_id: string }>('/api/v1/osym-exam/create', {
        method: 'POST',
        body: JSON.stringify({
          exam_type: config.exam_type.toUpperCase(),
          custom_config: {
            subject: config.subject.toUpperCase(),
            difficulty: config.difficulty,
            question_count: config.question_count,
            time_limit: config.time_limit,
          },
        }),
      });

      navigate(`/exam/${data.session_id}`);
    } catch (err: any) {
      setError(err.message || 'Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleStartBeta = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiRequest<{ session_id: string }>(
        '/api/v1/osym-exam/beta-practice?num_questions=20',
        { method: 'POST' },
      );
      navigate(`/exam/${data.session_id}`);
    } catch (err: any) {
      setError(err.message || 'Beta pratik başlatılamadı');
    } finally {
      setLoading(false);
    }
  };

  const selectedDifficulty = difficulties.find(d => d.value === config.difficulty);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Box sx={{ mb: 4 }}>
          <Box
            sx={{
              width: 56,
              height: 56,
              borderRadius: '16px',
              background: modernColors.gradients.primary,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mb: 2,
            }}
          >
            <SchoolIcon sx={{ fontSize: 32, color: 'white' }} />
          </Box>

          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              background: modernColors.gradients.primary,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 1,
            }}
          >
            Yeni Sınav Başlat
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Sınav parametrelerini seçin ve hazırlığınızı test edin
          </Typography>
        </Box>
      </motion.div>

      {error && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
        </motion.div>
      )}

      {/* Beta Pratik Testi — doğrulanmış çekirdek sorular */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
      >
        <GlassCard sx={{ mb: 3 }}>
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              alignItems: { sm: 'center' },
              justifyContent: 'space-between',
              gap: 2,
            }}
          >
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5 }}>
                🚀 Beta Pratik Testi
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Bağımsız olarak doğrulanmış, okunabilir sorulardan oluşan kısa
                karışık bir test (20 soru). Hızlıca başla, deneyimini bize bildir.
              </Typography>
            </Box>
            <ModernButton
              variant="gradient"
              onClick={handleStartBeta}
              disabled={loading}
              sx={{ whiteSpace: 'nowrap' }}
            >
              Beta Pratiğe Başla
            </ModernButton>
          </Box>
        </GlassCard>
      </motion.div>

      <Grid container spacing={3}>
        {/* Sol Kolon - Konfigürasyon */}
        <Grid item xs={12} md={7}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <GlassCard>
              <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                Sınav Ayarları
              </Typography>

              {/* Sınav Türü */}
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Sınav Türü</InputLabel>
                <Select
                  value={config.exam_type}
                  onChange={(e: SelectChangeEvent) => handleChange('exam_type', e.target.value)}
                  label="Sınav Türü"
                >
                  {examTypes.map(type => (
                    <MenuItem key={type.value} value={type.value}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <span>{type.icon}</span>
                        <span>{type.label}</span>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Ders */}
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Ders</InputLabel>
                <Select
                  value={config.subject}
                  onChange={(e: SelectChangeEvent) => handleChange('subject', e.target.value)}
                  label="Ders"
                >
                  {subjects[config.exam_type as keyof typeof subjects].map(subject => (
                    <MenuItem key={subject} value={subject}>{subject}</MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Zorluk */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600 }}>
                  Zorluk Seviyesi
                </Typography>
                <Grid container spacing={1.5}>
                  {difficulties.map((diff, index) => (
                    <Grid item xs={6} sm={3} key={diff.value}>
                      <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.2 + index * 0.05 }}
                      >
                        <Card
                          role="button"
                          aria-label={`${diff.label} zorluk seviyesi seç`}
                          aria-pressed={config.difficulty === diff.value}
                          tabIndex={0}
                          onClick={() => handleChange('difficulty', diff.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              handleChange('difficulty', diff.value);
                            }
                          }}
                          sx={{
                            cursor: 'pointer',
                            border: 2,
                            borderColor: config.difficulty === diff.value ? 'primary.main' : 'transparent',
                            transition: 'all 0.3s',
                            '&:hover': {
                              transform: 'translateY(-4px)',
                              boxShadow: 4,
                            },
                            '&:focus': {
                              outline: '2px solid rgba(59, 130, 246, 0.5)',
                              outlineOffset: '2px',
                            },
                          }}
                        >
                          <CardContent sx={{ textAlign: 'center', py: 2 }}>
                            <Typography variant="h4" sx={{ mb: 0.5 }}>{diff.icon}</Typography>
                            <Typography variant="body2" fontWeight={600}>{diff.label}</Typography>
                          </CardContent>
                        </Card>
                      </motion.div>
                    </Grid>
                  ))}
                </Grid>
              </Box>

              {/* Soru Sayısı */}
              <TextField
                fullWidth
                type="number"
                label="Soru Sayısı"
                value={config.question_count}
                onChange={(e) => handleChange('question_count', parseInt(e.target.value))}
                inputProps={{ min: 10, max: 100, step: 10 }}
                sx={{ mb: 3 }}
              />

              {/* Süre */}
              <TextField
                fullWidth
                type="number"
                label="Süre (dakika)"
                value={config.time_limit}
                onChange={(e) => handleChange('time_limit', parseInt(e.target.value))}
                inputProps={{ min: 20, max: 180, step: 10 }}
              />
            </GlassCard>
          </motion.div>
        </Grid>

        {/* Sağ Kolon - Özet & Başlat */}
        <Grid item xs={12} md={5}>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            {/* Sınav Özeti */}
            <GlassCard sx={{ mb: 3 }}>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                Sınav Özeti
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '12px',
                      background: modernColors.gradients.ocean,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <SchoolIcon sx={{ color: 'white' }} />
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Sınav Türü</Typography>
                    <Typography variant="body1" fontWeight={600}>{config.exam_type}</Typography>
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '12px',
                      background: modernColors.gradients.purple,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <PsychologyIcon sx={{ color: 'white' }} />
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Ders</Typography>
                    <Typography variant="body1" fontWeight={600}>{config.subject}</Typography>
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '12px',
                      background: selectedDifficulty?.color,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <TrendingUpIcon sx={{ color: 'white' }} />
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Zorluk</Typography>
                    <Typography variant="body1" fontWeight={600}>
                      {selectedDifficulty?.label} {selectedDifficulty?.icon}
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '12px',
                      background: modernColors.gradients.forest,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <TimerIcon sx={{ color: 'white' }} />
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="caption" color="text.secondary">Detaylar</Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {config.question_count} Soru • {config.time_limit} Dakika
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      (~{(config.time_limit / config.question_count).toFixed(1)} dk/soru)
                    </Typography>
                  </Box>
                </Box>
              </Box>

              {loading && (
                <Box sx={{ mt: 3 }}>
                  <LinearProgress />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block', textAlign: 'center' }}>
                    Sınav hazırlanıyor...
                  </Typography>
                </Box>
              )}
            </GlassCard>

            {/* Başlat Butonu */}
            <ModernButton
              fullWidth
              variant="solid"
              size="large"
              onClick={handleStartExam}
              disabled={loading}
              startIcon={<StartIcon />}
              sx={{
                height: 56,
                fontSize: '1.1rem',
                fontWeight: 600,
                background: modernColors.gradients.primary,
              }}
            >
              Sınavı Başlat
            </ModernButton>

            {/* Bilgi Kutusu */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
            >
              <Alert icon={<InfoIcon />} severity="info" sx={{ mt: 2 }}>
                <Typography variant="caption">
                  Sınav başladığında geri sayım otomatik olarak başlayacaktır. İyi şanslar!
                </Typography>
              </Alert>
            </motion.div>
          </motion.div>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ModernExamStartPage;
