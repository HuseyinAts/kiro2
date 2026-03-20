/**
 * Text Simplification Page
 * 3-Level Turkish Text Simplification System
 * World's first 3-level Turkish text simplification system
 *
 * Features:
 * - Level 1: Lexical (Word-level simplification)
 * - Level 2: Syntactic (Sentence structure simplification)
 * - Level 3: Semantic (Meaning-level simplification)
 * - Complex word detection
 * - Flesch-Kincaid readability scoring
 * - Real-time analysis
 */
import {
  AutoFixHigh,
  Psychology,
  Assessment,
  ContentCopy,
  Info,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Lightbulb,
  CompareArrows,
  TextFields,
  MenuBook,
  Analytics,
} from '@mui/icons-material';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Alert,
  CircularProgress,
  Chip,
  Divider,
  Tabs,
  Tab,
  Slider,
  FormControlLabel,
  Switch,
  IconButton,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import { useState } from 'react';

interface ComplexWord {
  word: string;
  complexity_score: number;
  frequency_score: number;
  position: number;
  suggested_replacements: string[];
}

interface SimplificationResult {
  original_text: string;
  simplified_text: string;
  statistics: {
    complex_words_replaced: number;
    sentences_split: number;
    readability_improvement: number;
    original_flesch_score: number;
    simplified_flesch_score: number;
  };
  suggestions: string[];
  improvement_percentage: number;
}

interface FleschResult {
  flesch_reading_ease: number;
  flesch_kincaid_grade: number;
  grade_level: string;
  difficulty: string;
  statistics: {
    total_words: number;
    total_sentences: number;
    total_syllables: number;
    avg_words_per_sentence: number;
    avg_syllables_per_word: number;
  };
  interpretation: {
    score_range: string;
    target_audience: string;
    recommendations: string[];
  };
}

export function TextSimplificationPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Complex Words Detection
  const [complexWords, setComplexWords] = useState<ComplexWord[]>([]);
  const [complexityThreshold, setComplexityThreshold] = useState(0.6);

  // Text Simplification
  const [simplificationResult, setSimplificationResult] = useState<SimplificationResult | null>(null);
  const [maxSentenceLength, setMaxSentenceLength] = useState(20);
  const [replaceSynonyms, setReplaceSynonyms] = useState(true);
  const [splitSentences, setSplitSentences] = useState(true);

  // Flesch Score
  const [fleschResult, setFleschResult] = useState<FleschResult | null>(null);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

  // Sample texts for demo
  const sampleTexts = {
    simple: 'Bugün hava çok güzel. Okula gitmek istiyorum. Matematik dersini seviyorum.',
    medium: 'Teknolojinin implementasyonu, organizasyonun performansını optimize etmek için kritik bir faktördür. Müessesemizin teşebbüsü, müşterilerimizin muvaffakiyetini sağlamaktır.',
    complex: 'Medeniyetimizin mütalaa ve tetkik edilen münasebet ve müzakere süreçlerinde, istifade edilen metodoloji ve algoritmaların optimizasyonu, müesseselerimizin muvaffakiyeti için elzemdir.',
  };

  const handleDetectComplexWords = async () => {
    if (!inputText.trim()) {
      setError('Lütfen metin girin');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/v1/text-simplification/detect-complex-words`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          text: inputText,
          complexity_threshold: complexityThreshold,
        }),
      });

      if (!response.ok) {
        throw new Error('Karmaşık kelime tespiti başarısız oldu');
      }

      const data = await response.json();
      setComplexWords(data.data.complex_words || []);
    } catch (err: any) {
      console.error('Complex word detection error:', err);
      setError(err.message || 'Hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleSimplifyText = async () => {
    if (!inputText.trim()) {
      setError('Lütfen metin girin');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/v1/text-simplification/simplify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          text: inputText,
          complexity_threshold: complexityThreshold,
          max_sentence_length: maxSentenceLength,
          replace_synonyms: replaceSynonyms,
          split_sentences: splitSentences,
          require_confirmation: false,
        }),
      });

      if (!response.ok) {
        throw new Error('Metin basitleştirme başarısız oldu');
      }

      const data = await response.json();
      setSimplificationResult(data.data);
    } catch (err: any) {
      console.error('Text simplification error:', err);
      setError(err.message || 'Hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleCalculateFleschScore = async () => {
    if (!inputText.trim()) {
      setError('Lütfen metin girin');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/v1/text-simplification/flesch-score`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          text: inputText,
        }),
      });

      if (!response.ok) {
        throw new Error('Okunabilirlik skoru hesaplanamadı');
      }

      const data = await response.json();
      setFleschResult(data.data);
    } catch (err: any) {
      console.error('Flesch score calculation error:', err);
      setError(err.message || 'Hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('📋 Metín panoya kopyalandı!');
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) {return 'success.main';}
    if (score >= 60) {return 'info.main';}
    if (score >= 40) {return 'warning.main';}
    return 'error.main';
  };

  const getDifficultyIcon = (difficulty: string) => {
    if (difficulty.includes('Kolay')) {return <CheckCircle color="success" />;}
    if (difficulty.includes('Standart')) {return <Info color="info" />;}
    if (difficulty.includes('Zor')) {return <Warning color="warning" />;}
    return <ErrorIcon color="error" />;
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <AutoFixHigh sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
          <Box>
            <Typography variant="h4" fontWeight="bold">
              Türkçe Metin Basitleştirme
            </Typography>
            <Typography variant="body2" color="text.secondary">
              3 Seviyeli Akıllı Basitleştirme Sistemi • Disleksi Desteği
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            onClick={() => setInputText(sampleTexts.simple)}
          >
            Basit Örnek
          </Button>
          <Button
            variant="outlined"
            onClick={() => setInputText(sampleTexts.medium)}
          >
            Orta Örnek
          </Button>
          <Button
            variant="outlined"
            onClick={() => setInputText(sampleTexts.complex)}
          >
            Karmaşık Örnek
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Info Banner */}
      <Alert severity="info" icon={<Lightbulb />} sx={{ mb: 3 }}>
        <Typography variant="body2" fontWeight="bold">
          🌟 Dünyada İlk 3 Seviyeli Türkçe Metin Basitleştirme Sistemi
        </Typography>
        <Typography variant="caption">
          Seviye 1: Kelime (Osmanlıca/Akademik → Günlük) |
          Seviye 2: Cümle Yapısı |
          Seviye 3: Anlam Basitleştirme
        </Typography>
      </Alert>

      <Grid container spacing={3}>
        {/* Input Section */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
                <TextFields sx={{ mr: 1 }} />
                Giriş Metni
              </Typography>
              <Chip
                label={`${inputText.length} karakter`}
                size="small"
                color={inputText.length > 5000 ? 'error' : 'default'}
              />
            </Box>

            <TextField
              multiline
              rows={12}
              fullWidth
              placeholder="Basitleştirilecek metni buraya yazın..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              sx={{ mb: 2 }}
            />

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" gutterBottom>
                Karmaşıklık Eşiği: {(complexityThreshold * 100).toFixed(0)}%
              </Typography>
              <Slider
                value={complexityThreshold}
                onChange={(_, value) => setComplexityThreshold(value as number)}
                min={0}
                max={1}
                step={0.1}
                marks
                valueLabelDisplay="auto"
                valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
              />
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" gutterBottom>
                Maksimum Cümle Uzunluğu: {maxSentenceLength} kelime
              </Typography>
              <Slider
                value={maxSentenceLength}
                onChange={(_, value) => setMaxSentenceLength(value as number)}
                min={10}
                max={40}
                step={5}
                marks
                valueLabelDisplay="auto"
              />
            </Box>

            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={replaceSynonyms}
                    onChange={(e) => setReplaceSynonyms(e.target.checked)}
                  />
                }
                label="Eşanlamlı Değiştir"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={splitSentences}
                    onChange={(e) => setSplitSentences(e.target.checked)}
                  />
                }
                label="Cümle Böl"
              />
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Button
                  variant="contained"
                  fullWidth
                  startIcon={loading ? <CircularProgress size={20} /> : <Psychology />}
                  onClick={handleDetectComplexWords}
                  disabled={loading || !inputText.trim()}
                >
                  Karmaşık Kelimeler
                </Button>
              </Grid>
              <Grid item xs={12} md={4}>
                <Button
                  variant="contained"
                  fullWidth
                  color="secondary"
                  startIcon={loading ? <CircularProgress size={20} /> : <AutoFixHigh />}
                  onClick={handleSimplifyText}
                  disabled={loading || !inputText.trim()}
                >
                  Basitleştir
                </Button>
              </Grid>
              <Grid item xs={12} md={4}>
                <Button
                  variant="contained"
                  fullWidth
                  color="info"
                  startIcon={loading ? <CircularProgress size={20} /> : <Assessment />}
                  onClick={handleCalculateFleschScore}
                  disabled={loading || !inputText.trim()}
                >
                  Okunabilirlik
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Results Section */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
            <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)} sx={{ mb: 2 }}>
              <Tab icon={<Psychology />} label="Karmaşık Kelimeler" />
              <Tab icon={<AutoFixHigh />} label="Basitleştirilmiş" />
              <Tab icon={<Assessment />} label="Okunabilirlik" />
            </Tabs>

            {/* Complex Words Tab */}
            {activeTab === 0 && (
              <Box>
                {complexWords.length > 0 ? (
                  <>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                      <Typography variant="h6">
                        {complexWords.length} Karmaşık Kelime Bulundu
                      </Typography>
                      <Chip
                        label={`Ortalama Karmaşıklık: ${(complexWords.reduce((sum, w) => sum + w.complexity_score, 0) / complexWords.length * 100).toFixed(0)}%`}
                        color="warning"
                      />
                    </Box>

                    <TableContainer sx={{ maxHeight: 400 }}>
                      <Table size="small" stickyHeader>
                        <TableHead>
                          <TableRow>
                            <TableCell>Kelime</TableCell>
                            <TableCell>Karmaşıklık</TableCell>
                            <TableCell>Öneriler</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {complexWords.map((word, idx) => (
                            <TableRow key={idx}>
                              <TableCell>
                                <Typography fontWeight="bold">
                                  {word.word}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <LinearProgress
                                  variant="determinate"
                                  value={word.complexity_score * 100}
                                  sx={{
                                    width: 80,
                                    mr: 1,
                                    '& .MuiLinearProgress-bar': {
                                      backgroundColor: word.complexity_score > 0.7 ? 'error.main' : 'warning.main',
                                    },
                                  }}
                                />
                                <Typography variant="caption">
                                  {(word.complexity_score * 100).toFixed(0)}%
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                  {word.suggested_replacements.slice(0, 3).map((replacement, ridx) => (
                                    <Chip
                                      key={ridx}
                                      label={replacement}
                                      size="small"
                                      color="success"
                                      variant="outlined"
                                    />
                                  ))}
                                </Box>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </>
                ) : (
                  <Box sx={{ textAlign: 'center', py: 8 }}>
                    <Psychology sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary">
                      Karmaşık kelime analizi yapmak için &quot;Karmaşık Kelimeler&quot; butonuna tıklayın
                    </Typography>
                  </Box>
                )}
              </Box>
            )}

            {/* Simplified Text Tab */}
            {activeTab === 1 && (
              <Box>
                {simplificationResult ? (
                  <>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                      <Typography variant="h6">Basitleştirilmiş Metin</Typography>
                      <IconButton onClick={() => handleCopyToClipboard(simplificationResult.simplified_text)}>
                        <ContentCopy />
                      </IconButton>
                    </Box>

                    {/* Statistics */}
                    <Grid container spacing={2} sx={{ mb: 3 }}>
                      <Grid item xs={6}>
                        <Card elevation={1}>
                          <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                            <Typography variant="h4" color="primary">
                              {simplificationResult.statistics.complex_words_replaced}
                            </Typography>
                            <Typography variant="caption">Değiştirilen Kelime</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={6}>
                        <Card elevation={1}>
                          <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                            <Typography variant="h4" color="secondary">
                              {simplificationResult.statistics.sentences_split}
                            </Typography>
                            <Typography variant="caption">Bölünen Cümle</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={6}>
                        <Card elevation={1}>
                          <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                            <Typography variant="h4" color="success.main">
                              +{simplificationResult.statistics.readability_improvement.toFixed(1)}
                            </Typography>
                            <Typography variant="caption">Okunabilirlik İyileşmesi</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={6}>
                        <Card elevation={1}>
                          <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                            <Typography variant="h4" color="info.main">
                              {simplificationResult.improvement_percentage.toFixed(0)}%
                            </Typography>
                            <Typography variant="caption">İyileşme Oranı</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>

                    <Paper sx={{ p: 2, mb: 2, backgroundColor: 'success.light', color: 'white' }}>
                      <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                        {simplificationResult.simplified_text}
                      </Typography>
                    </Paper>

                    {simplificationResult.suggestions.length > 0 && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          💡 Öneriler:
                        </Typography>
                        <List dense>
                          {simplificationResult.suggestions.map((suggestion, idx) => (
                            <ListItem key={idx}>
                              <ListItemIcon>
                                <Lightbulb fontSize="small" color="warning" />
                              </ListItemIcon>
                              <ListItemText primary={suggestion} />
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    )}
                  </>
                ) : (
                  <Box sx={{ textAlign: 'center', py: 8 }}>
                    <AutoFixHigh sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary">
                      Metin basitleştirmek için &quot;Basitleştir&quot; butonuna tıklayın
                    </Typography>
                  </Box>
                )}
              </Box>
            )}

            {/* Flesch Score Tab */}
            {activeTab === 2 && (
              <Box>
                {fleschResult ? (
                  <>
                    <Box sx={{ textAlign: 'center', mb: 3 }}>
                      <Typography variant="h3" sx={{ color: getScoreColor(fleschResult.flesch_reading_ease) }}>
                        {fleschResult.flesch_reading_ease.toFixed(1)}
                      </Typography>
                      <Typography variant="h6" color="text.secondary">
                        Flesch Reading Ease
                      </Typography>
                      <Chip
                        label={fleschResult.difficulty}
                        icon={getDifficultyIcon(fleschResult.difficulty)}
                        sx={{ mt: 1 }}
                      />
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    {/* Statistics Grid */}
                    <Grid container spacing={2} sx={{ mb: 3 }}>
                      <Grid item xs={6}>
                        <Card elevation={1}>
                          <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                            <Typography variant="h5">
                              {fleschResult.statistics.total_words}
                            </Typography>
                            <Typography variant="caption">Toplam Kelime</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={6}>
                        <Card elevation={1}>
                          <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                            <Typography variant="h5">
                              {fleschResult.statistics.total_sentences}
                            </Typography>
                            <Typography variant="caption">Toplam Cümle</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={6}>
                        <Card elevation={1}>
                          <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                            <Typography variant="h5">
                              {fleschResult.statistics.avg_words_per_sentence.toFixed(1)}
                            </Typography>
                            <Typography variant="caption">Ort. Kelime/Cümle</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={6}>
                        <Card elevation={1}>
                          <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                            <Typography variant="h5">
                              {fleschResult.statistics.avg_syllables_per_word.toFixed(1)}
                            </Typography>
                            <Typography variant="caption">Ort. Hece/Kelime</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>

                    <Paper sx={{ p: 2, mb: 2, backgroundColor: 'info.light', color: 'white' }}>
                      <Typography variant="subtitle2" gutterBottom>
                        🎯 Hedef Kitle:
                      </Typography>
                      <Typography variant="body2">
                        {fleschResult.interpretation.target_audience}
                      </Typography>
                    </Paper>

                    <Paper sx={{ p: 2, mb: 2, backgroundColor: 'warning.light' }}>
                      <Typography variant="subtitle2" gutterBottom>
                        📊 Skor Aralığı:
                      </Typography>
                      <Typography variant="body2">
                        {fleschResult.interpretation.score_range}
                      </Typography>
                    </Paper>

                    {fleschResult.interpretation.recommendations.length > 0 && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          💡 Öneriler:
                        </Typography>
                        <List dense>
                          {fleschResult.interpretation.recommendations.map((rec, idx) => (
                            <ListItem key={idx}>
                              <ListItemIcon>
                                <CheckCircle fontSize="small" color="success" />
                              </ListItemIcon>
                              <ListItemText primary={rec} />
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    )}
                  </>
                ) : (
                  <Box sx={{ textAlign: 'center', py: 8 }}>
                    <Assessment sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary">
                      Okunabilirlik analizi için &quot;Okunabilirlik&quot; butonuna tıklayın
                    </Typography>
                  </Box>
                )}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Information Cards */}
      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} md={4}>
          <Card elevation={2} sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <MenuBook sx={{ fontSize: 30, color: 'primary.main', mr: 1 }} />
                <Typography variant="h6">Seviye 1: Kelime</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Osmanlıca, akademik ve yabancı kökenli kelimeleri günlük Türkçe karşılıklarına dönüştürür.
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Chip label="mütalaa → okuma" size="small" sx={{ mr: 1, mb: 1 }} />
                <Chip label="tetkik → inceleme" size="small" sx={{ mr: 1, mb: 1 }} />
                <Chip label="implementasyon → uygulama" size="small" sx={{ mb: 1 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={2} sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <CompareArrows sx={{ fontSize: 30, color: 'secondary.main', mr: 1 }} />
                <Typography variant="h6">Seviye 2: Cümle Yapısı</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Karmaşık cümle yapılarını basit ve anlaşılır cümlelere böler. Uzun cümleleri kısaltır.
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Chip label="Pasif → Aktif" size="small" sx={{ mr: 1, mb: 1 }} />
                <Chip label="Bağlaç Azaltma" size="small" sx={{ mr: 1, mb: 1 }} />
                <Chip label="Cümle Bölme" size="small" sx={{ mb: 1 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={2} sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Analytics sx={{ fontSize: 30, color: 'info.main', mr: 1 }} />
                <Typography variant="h6">Seviye 3: Anlam</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Anlamsal olarak karmaşık ifadeleri daha basit anlatım biçimlerine dönüştürür.
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Chip label="Mecaz → Gerçek" size="small" sx={{ mr: 1, mb: 1 }} />
                <Chip label="Teknik → Günlük" size="small" sx={{ mr: 1, mb: 1 }} />
                <Chip label="Soyut → Somut" size="small" sx={{ mb: 1 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}

export default TextSimplificationPage;
