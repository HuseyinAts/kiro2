import { useState } from 'react';
import {
  AutoAwesome,
  Memory,
  Science,
  MenuBook,
  EmojiObjects,
  Settings,
  PrecisionManufacturing
} from '@mui/icons-material';
import {
  Box,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Slider,
  Paper,
  Divider,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard } from '../components/ui/GlassCard';
import modernColors from '../theme/modern-colors';

interface QuestionGenerationParams {
  topic: string;
  subtopic: string;
  examType: 'TYT' | 'AYT' | 'YDT' | 'LGS';
  subject: string;
  difficulty: number;
  bloomLevel: number;
  provider: 'ensemble' | 'openai' | 'claude' | 'qwen';
}

interface GeneratedQuestion {
  id: string;
  stem: string;
  options: string[];
  correct_answer: number;
  explanation: string;
  keywords: string[];
  difficulty: number;
  quality_score: number;
  tokens_used: number;
  cost_usd: number;
  generation_time_ms: number;
}

export const OSYMQuestionGeneratorPage: React.FC = () => {
  const [params, setParams] = useState<QuestionGenerationParams>({
    topic: '',
    subtopic: '',
    examType: 'TYT',
    subject: 'Matematik',
    difficulty: 0.5,
    bloomLevel: 3,
    provider: 'ensemble',
  });

  const [generating, setGenerating] = useState(false);
  const [question, setQuestion] = useState<GeneratedQuestion | null>(null);
  const [error, setError] = useState<string | null>(null);

  const subjects = {
    TYT: ['Matematik', 'Türkçe', 'Fen Bilimleri', 'Sosyal Bilimler'],
    AYT: ['Matematik', 'Fizik', 'Kimya', 'Biyoloji', 'Edebiyat', 'Tarih', 'Coğrafya'],
    YDT: ['İngilizce', 'Almanca', 'Fransızca'],
    LGS: ['Matematik', 'Türkçe', 'Fen Bilimleri', 'İnkılap Tarihi', 'Din Kültürü', 'İngilizce'],
  };

  const bloomLevels = [
    { level: 1, label: 'Bilgi (Hatırlama)', icon: '📝' },
    { level: 2, label: 'Kavrama (Anlama)', icon: '💡' },
    { level: 3, label: 'Uygulama', icon: '🔧' },
    { level: 4, label: 'Analiz', icon: '🔍' },
    { level: 5, label: 'Sentez (Değerlendirme)', icon: '⚖️' },
    { level: 6, label: 'Yaratma', icon: '🎨' },
  ];

  const handleGenerate = async () => {
    if (!params.topic || !params.subtopic) {
      setError('Lütfen konu ve alt konu alanlarını doldurun');
      return;
    }

    setGenerating(true);
    setError(null);
    setQuestion(null);

    try {
      const response = await fetch('/api/v1/osym/generate-question', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Soru üretimi başarısız oldu');
      }

      const data = await response.json();
      setQuestion(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bir hata oluştu');
    } finally {
      setGenerating(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { type: 'spring', damping: 20 } }
  };

  return (
    <Box sx={{ p: { xs: 2, md: 4 }, minHeight: '100vh', background: 'url(/assets/bg-pattern.svg) center/cover' }}>
      
      {/* Header */}
      <Box sx={{ mb: 5, textAlign: 'center' }}>
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <Chip 
            icon={<AutoAwesome sx={{ fontSize: 16 }} />} 
            label="Ultra Premium AI Engine" 
            sx={{ mb: 2, background: 'rgba(99,102,241,0.1)', color: modernColors.primary[600], fontWeight: 800, border: `1px solid ${modernColors.primary[200]}` }} 
          />
          <Typography variant="h3" fontWeight={900} sx={{ 
            mb: 1, 
            background: modernColors.gradients.primary,
            WebkitBackgroundClip: 'text', 
            WebkitTextFillColor: 'transparent',
            filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))'
          }}>
            Yapay Zeka Soru Üretici
          </Typography>
          <Typography variant="body1" color="text.secondary" fontWeight={500}>
            Multi-LLM ensemble altyapısıyla ÖSYM standartlarında, Türkçe optimize sorular.
          </Typography>
        </motion.div>
      </Box>

      <Grid container spacing={4} sx={{ maxWidth: 1400, mx: 'auto' }}>
        {/* Left Panel - Parameters */}
        <Grid item xs={12} lg={4}>
          <motion.div initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6, type: 'spring' }}>
            <GlassCard glassIntensity="medium" sx={{ p: 4, height: '100%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 4, gap: 1.5 }}>
                <Settings sx={{ color: modernColors.primary[500] }} />
                <Typography variant="h6" fontWeight={800} color={'#1e293b'}>
                  Soru Parametreleri
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <FormControl fullWidth variant="filled">
                  <InputLabel>Sınav Türü</InputLabel>
                  <Select
                    value={params.examType}
                    onChange={(e) => setParams({ ...params, examType: e.target.value as any })}
                    sx={{ backgroundColor: 'rgba(255,255,255,0.7)', borderRadius: 2 }}
                    disableUnderline
                  >
                    <MenuItem value="TYT">TYT</MenuItem>
                    <MenuItem value="AYT">AYT</MenuItem>
                    <MenuItem value="YDT">YDT</MenuItem>
                    <MenuItem value="LGS">LGS</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth variant="filled">
                  <InputLabel>Ders</InputLabel>
                  <Select
                    value={params.subject}
                    onChange={(e) => setParams({ ...params, subject: e.target.value })}
                    sx={{ backgroundColor: 'rgba(255,255,255,0.7)', borderRadius: 2 }}
                    disableUnderline
                  >
                    {subjects[params.examType].map((subject) => (
                      <MenuItem key={subject} value={subject}>{subject}</MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <TextField
                  fullWidth
                  variant="filled"
                  label="Konu"
                  placeholder="Örn: Türev"
                  value={params.topic}
                  onChange={(e) => setParams({ ...params, topic: e.target.value })}
                  sx={{ backgroundColor: 'rgba(255,255,255,0.7)', borderRadius: 2, '& .MuiFilledInput-root': {  } }}
                  InputProps={{ disableUnderline: true }}
                />

                <TextField
                  fullWidth
                  variant="filled"
                  label="Alt Konu"
                  placeholder="Örn: Türev Alma Kuralları"
                  value={params.subtopic}
                  onChange={(e) => setParams({ ...params, subtopic: e.target.value })}
                  sx={{ backgroundColor: 'rgba(255,255,255,0.7)', borderRadius: 2, '& .MuiFilledInput-root': {  } }}
                  InputProps={{ disableUnderline: true }}
                />

                <Box sx={{ p: 2, borderRadius: 3, backgroundColor: 'rgba(255,255,255,0.5)', border: '1px solid rgba(255,255,255,0.8)' }}>
                  <Typography variant="body2" fontWeight={700} color={'#475569'} gutterBottom>
                    Zorluk Seviyesi: {(params.difficulty * 100).toFixed(0)}%
                  </Typography>
                  <Slider
                    value={params.difficulty}
                    onChange={(_, value) => setParams({ ...params, difficulty: value as number })}
                    min={0}
                    max={1}
                    step={0.1}
                    marks={[
                      { value: 0, label: 'Kolay' },
                      { value: 0.5, label: 'Orta' },
                      { value: 1, label: 'Zor' },
                    ]}
                    sx={{ color: modernColors.primary[500], mt: 1 }}
                  />
                </Box>

                <FormControl fullWidth variant="filled">
                  <InputLabel>Bloom Taksonomisi</InputLabel>
                  <Select
                    value={params.bloomLevel}
                    onChange={(e) => setParams({ ...params, bloomLevel: e.target.value as number })}
                    sx={{ backgroundColor: 'rgba(255,255,255,0.7)', borderRadius: 2 }}
                    disableUnderline
                  >
                    {bloomLevels.map((bloom) => (
                      <MenuItem key={bloom.level} value={bloom.level}>
                        {bloom.icon} {bloom.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <FormControl fullWidth variant="filled">
                  <InputLabel>AI Provider</InputLabel>
                  <Select
                    value={params.provider}
                    onChange={(e) => setParams({ ...params, provider: e.target.value as any })}
                    sx={{ backgroundColor: 'rgba(255,255,255,0.7)', borderRadius: 2 }}
                    disableUnderline
                  >
                    <MenuItem value="ensemble">🎯 Ensemble (Önerilen)</MenuItem>
                    <MenuItem value="openai">🤖 OpenAI GPT-4</MenuItem>
                    <MenuItem value="claude">⚡ Claude 3.5</MenuItem>
                    <MenuItem value="qwen">🚀 Qwen 2.5 (Türkçe Optimize)</MenuItem>
                  </Select>
                </FormControl>

                <Button
                  variant="contained"
                  size="large"
                  onClick={handleGenerate}
                  disabled={generating || !params.topic || !params.subtopic}
                  startIcon={generating ? <CircularProgress size={20} color="inherit" /> : <PrecisionManufacturing />}
                  sx={{
                    mt: 2,
                    py: 2,
                    borderRadius: 3,
                    fontWeight: 800,
                    fontSize: '1.1rem',
                    background: modernColors.gradients.primary,
                    boxShadow: '0 8px 25px rgba(99,102,241,0.4)',
                    textTransform: 'none',
                    transition: 'all 0.3s',
                    '&:hover': {
                      background: modernColors.gradients.primary,
                      transform: 'translateY(-2px)',
                      boxShadow: '0 12px 30px rgba(99,102,241,0.6)',
                    }
                  }}
                >
                  {generating ? 'Yapay Zeka Çalışıyor...' : 'Yeni Soru Üret'}
                </Button>
              </Box>
            </GlassCard>
          </motion.div>
        </Grid>

        {/* Right Panel - Generated Question */}
        <Grid item xs={12} lg={8}>
          <AnimatePresence mode="wait">
            {error && (
              <motion.div key="error" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
                <Alert severity="error" sx={{ mb: 3, borderRadius: 3 }}>
                  {error}
                </Alert>
              </motion.div>
            )}

            {generating && !question && !error && (
              <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Box sx={{ textAlign: 'center', py: 10 }}>
                  <CircularProgress size={60} thickness={4} sx={{ color: modernColors.primary[500], mb: 3 }} />
                  <Typography variant="h5" fontWeight={800} color={modernColors.primary[700]}>
                    Sorunuz Hazırlanıyor...
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Bilişsel seviyeler, çeldiriciler ve soru kökü optimize ediliyor.
                  </Typography>
                </Box>
              </motion.div>
            )}

            {question && !generating && (
              <motion.div key="question" initial="hidden" animate="visible" variants={containerVariants}>
                <GlassCard glassIntensity="light" sx={{ p: { xs: 3, md: 5 }, position: 'relative', overflow: 'hidden' }}>
                  
                  <Box sx={{ position: 'absolute', top: -100, right: -100, width: 300, height: 300, background: modernColors.primary[100], filter: 'blur(80px)', opacity: 0.6, borderRadius: '50%', zIndex: 0 }} />

                  <Box sx={{ position: 'relative', zIndex: 1 }}>
                    <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2 }}>
                      <Box>
                        <Typography variant="h5" fontWeight={900} sx={{ color: '#1e293b', display: 'flex', alignItems: 'center', gap: 1 }}>
                          <MenuBook sx={{ color: modernColors.primary[500] }} /> Üretilen Soru
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, fontWeight: 600 }}>
                          {params.subject} &bull; {params.topic} &bull; {params.subtopic}
                        </Typography>
                      </Box>
                      
                      <Chip
                        icon={<EmojiObjects sx={{ fontSize: 16 }} />}
                        label={`Kalite: %${question.quality_score.toFixed(0)}`}
                        sx={{ 
                          fontWeight: 800, fontSize: '0.9rem', py: 2.5, px: 1,
                          backgroundColor: question.quality_score >= 80 ? 'rgba(34,197,94,0.1)' : 'rgba(245,158,11,0.1)',
                          color: question.quality_score >= 80 ? modernColors.success[500] : modernColors.warning[700],
                          border: `1px solid ${question.quality_score >= 80 ? 'rgba(34,197,94,0.3)' : 'rgba(245,158,11,0.3)'}`
                        }}
                      />
                    </Box>

                    {/* Question Stem */}
                    <motion.div variants={itemVariants}>
                      <Paper elevation={0} sx={{ p: 4, bgcolor: 'rgba(255,255,255,0.7)', backdropFilter: 'blur(10px)', mb: 4, borderRadius: 4, border: '1px solid rgba(255,255,255,0.9)', boxShadow: '0 4px 20px rgba(0,0,0,0.03)' }}>
                        <Typography variant="h6" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, color: '#1e293b', fontWeight: 600 }}>
                          {question.stem}
                        </Typography>
                      </Paper>
                    </motion.div>

                    {/* Options */}
                    <Box sx={{ mb: 5 }}>
                      {question.options.map((option, index) => (
                        <motion.div variants={itemVariants} key={index}>
                          <Paper
                            elevation={0}
                            sx={{
                              p: 2.5,
                              mb: 2,
                              display: 'flex',
                              alignItems: 'center',
                              gap: 2,
                              borderRadius: 3,
                              background: index === question.correct_answer ? 'linear-gradient(135deg, rgba(34,197,94,0.1), rgba(34,197,94,0.02))' : 'rgba(255,255,255,0.5)',
                              border: `2px solid ${index === question.correct_answer ? modernColors.success[400] : 'rgba(255,255,255,0.8)'}`,
                              boxShadow: index === question.correct_answer ? '0 4px 15px rgba(34,197,94,0.15)' : 'none',
                              transition: 'all 0.2s',
                              '&:hover': {
                                backgroundColor: index !== question.correct_answer ? 'rgba(255,255,255,0.8)' : undefined,
                                transform: 'translateX(5px)'
                              }
                            }}
                          >
                            <Box sx={{ 
                              width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                              backgroundColor: index === question.correct_answer ? modernColors.success[500] : 'rgba(0,0,0,0.05)',
                              color: index === question.correct_answer ? 'white' : '#64748b',
                              fontWeight: 800, fontSize: '1.1rem'
                            }}>
                              {String.fromCharCode(65 + index)}
                            </Box>
                            <Typography variant="body1" fontWeight={index === question.correct_answer ? 700 : 500} color={index === question.correct_answer ? modernColors.success[700] : '#334155'} sx={{ fontSize: '1.1rem' }}>
                              {option}
                            </Typography>
                          </Paper>
                        </motion.div>
                      ))}
                    </Box>

                    {/* Explanation */}
                    <motion.div variants={itemVariants}>
                      <Box sx={{ mb: 4, p: 3, borderRadius: 4, backgroundColor: 'rgba(99,102,241,0.05)', border: `1px solid ${modernColors.primary[100]}` }}>
                        <Typography variant="subtitle1" fontWeight={800} color={modernColors.primary[700]} sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Science fontSize="small" /> Çözüm Açıklaması
                        </Typography>
                        <Typography variant="body1" color={'#334155'} sx={{ lineHeight: 1.7 }}>
                          {question.explanation}
                        </Typography>
                      </Box>
                    </motion.div>

                    {/* Keywords */}
                    <motion.div variants={itemVariants}>
                      <Box sx={{ mb: 4 }}>
                        <Typography variant="subtitle2" fontWeight={800} color="text.secondary" gutterBottom>
                          Aİ Bilişsel Etiketleri
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {question.keywords.map((keyword, index) => (
                            <Chip 
                              key={index} 
                              label={keyword} 
                              sx={{ 
                                fontWeight: 600, 
                                backgroundColor: 'white', 
                                color: '#475569',
                                border: '1px solid rgba(0,0,0,0.08)',
                                boxShadow: '0 2px 5px rgba(0,0,0,0.02)'
                              }} 
                            />
                          ))}
                        </Box>
                      </Box>
                    </motion.div>

                    <Divider sx={{ my: 4, opacity: 0.5 }} />

                    {/* Metrics Footer */}
                    <motion.div variants={itemVariants}>
                      <Grid container spacing={2}>
                        <Grid item xs={6} sm={3}>
                          <Box sx={{ p: 2, borderRadius: 3, backgroundColor: 'rgba(255,255,255,0.5)', textAlign: 'center' }}>
                            <Typography variant="caption" fontWeight={700} color="text.secondary" display="block">TOKEN</Typography>
                            <Typography variant="h6" fontWeight={900} color={'#1e293b'}>
                              {question.tokens_used}
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Box sx={{ p: 2, borderRadius: 3, backgroundColor: 'rgba(255,255,255,0.5)', textAlign: 'center' }}>
                            <Typography variant="caption" fontWeight={700} color="text.secondary" display="block">MALİYET</Typography>
                            <Typography variant="h6" fontWeight={900} color={'#1e293b'}>
                              ${question.cost_usd.toFixed(4)}
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Box sx={{ p: 2, borderRadius: 3, backgroundColor: 'rgba(255,255,255,0.5)', textAlign: 'center' }}>
                            <Typography variant="caption" fontWeight={700} color="text.secondary" display="block">ZORLUK</Typography>
                            <Typography variant="h6" fontWeight={900} color={'#1e293b'}>
                              {question.difficulty.toFixed(2)}
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Box sx={{ p: 2, borderRadius: 3, backgroundColor: 'rgba(255,255,255,0.5)', textAlign: 'center' }}>
                            <Typography variant="caption" fontWeight={700} color="text.secondary" display="block">SÜRE</Typography>
                            <Typography variant="h6" fontWeight={900} color={'#1e293b'}>
                              {(question.generation_time_ms / 1000).toFixed(1)}s
                            </Typography>
                          </Box>
                        </Grid>
                      </Grid>
                    </motion.div>

                  </Box>
                </GlassCard>
              </motion.div>
            )}

            {!question && !generating && !error && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <GlassCard glassIntensity="light" sx={{ height: '100%', minHeight: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Box sx={{ textAlign: 'center', p: 5 }}>
                    <Memory sx={{ fontSize: 100, color: modernColors.primary[200], mb: 3 }} />
                    <Typography variant="h5" fontWeight={800} color={'#334155'} gutterBottom>
                      Hazırız!
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      Sol panelden parametreleri belirleyin ve yapay zekanın 
                      saniyeler içinde özgün bir ÖSYM sorusu hazırlamasını izleyin.
                    </Typography>
                  </Box>
                </GlassCard>
              </motion.div>
            )}
          </AnimatePresence>
        </Grid>
      </Grid>
    </Box>
  );
};

export default OSYMQuestionGeneratorPage;
