/**
 * 🚀 3 Seviyeli Türkçe Metin Basitleştirme Bileşeni (DEVRİMSEL)
 * Dünyada ilk 3 seviyeli Türkçe metin basitleştirme sistemi
 */

import {
  AutoFixHigh as ZapIcon,
  MenuBook as BookOpenIcon,
  Psychology as BrainIcon,
  Lightbulb as LightbulbIcon,
} from '@mui/icons-material';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  CircularProgress,
  Alert,
  Grid,
  Box,
  Paper,
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import * as React from 'react';
import {  useState  } from 'react';

import { revolutionaryFeaturesService } from '../../services/revolutionaryFeaturesService';
import { SimplificationResult } from '../../types';

// SimplificationResult tipi artık types/index.ts'de tanımlı

const TextSimplifier: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [simplificationLevel, setSimplificationLevel] = useState('semantic');
  const [preserveMeaning, setPreserveMeaning] = useState(true);
  const [result, setResult] = useState<SimplificationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const simplificationLevels = [
    {
      value: 'lexical',
      label: 'Kelime Seviyesi',
      icon: <BookOpenIcon />,
      description: 'Osmanlıca ve akademik kelimeleri modern Türkçe\'ye çevirir',
      color: 'success',
    },
    {
      value: 'syntactic',
      label: 'Sözdizimi Seviyesi',
      icon: <BrainIcon />,
      description: 'Karmaşık cümle yapılarını basit cümlelere böler',
      color: 'primary',
    },
    {
      value: 'semantic',
      label: 'Anlam Seviyesi',
      icon: <LightbulbIcon />,
      description: 'Metafor ve soyut kavramları somut açıklamalarla değiştirir',
      color: 'secondary',
    },
  ];

  const handleSimplify = async () => {
    if (!inputText.trim()) {
      setError('Lütfen basitleştirilecek metni girin');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await revolutionaryFeaturesService.simplifyText(
        inputText,
        simplificationLevel as 'lexical' | 'syntactic' | 'semantic',
        preserveMeaning,
      );

      setResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Beklenmeyen hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const getComplexityColor = (score: number): 'success' | 'warning' | 'error' => {
    if (score < 30) {return 'success';}
    if (score < 60) {return 'warning';}
    return 'error';
  };

  const getReadabilityColor = (score: number): 'success' | 'info' | 'warning' | 'error' => {
    if (score > 80) {return 'success';}
    if (score > 60) {return 'info';}
    if (score > 40) {return 'warning';}
    return 'error';
  };

  const selectedLevel = simplificationLevels.find(level => level.value === simplificationLevel);

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 2 }}>
          <ZapIcon sx={{ fontSize: 40, color: 'warning.main' }} />
          <Typography variant="h3" component="h1" fontWeight="bold">
            3 Seviyeli Türkçe Metin Basitleştirme
          </Typography>
        </Box>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Dünyada ilk 3 seviyeli Türkçe metin basitleştirme sistemi
        </Typography>
        <Chip
          label="🚀 DEVRİMSEL ÖZELLİK"
          color="warning"
          variant="outlined"
          sx={{ fontWeight: 'bold' }}
        />
      </Box>

      <Grid container spacing={3}>
        {/* Input Section */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardHeader>
              <Typography variant="h6" component="div" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <BookOpenIcon />
                Metin Girişi
              </Typography>
            </CardHeader>
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <TextField
                  multiline
                  rows={8}
                  placeholder="Basitleştirilecek metni buraya yazın..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  variant="outlined"
                  fullWidth
                />

                <FormControl fullWidth>
                  <InputLabel>Basitleştirme Seviyesi</InputLabel>
                  <Select
                    value={simplificationLevel}
                    label="Basitleştirme Seviyesi"
                    onChange={(e) => setSimplificationLevel(e.target.value)}
                  >
                    {simplificationLevels.map((level) => (
                      <MenuItem key={level.value} value={level.value}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {level.icon}
                          {level.label}
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                {selectedLevel && (
                  <Typography variant="caption" color="text.secondary">
                    {selectedLevel.description}
                  </Typography>
                )}

                <FormControlLabel
                  control={
                    <Checkbox
                      checked={preserveMeaning}
                      onChange={(e) => setPreserveMeaning(e.target.checked)}
                    />
                  }
                  label="Anlam korunumu (önerilen)"
                />

                <Button
                  variant="contained"
                  onClick={handleSimplify}
                  disabled={loading || !inputText.trim()}
                  startIcon={loading ? <CircularProgress size={20} /> : <ZapIcon />}
                  fullWidth
                  size="medium"
                >
                  {loading ? 'Basitleştiriliyor...' : 'Metni Basitleştir'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Result Section */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardHeader>
              <Typography variant="h6" component="div" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LightbulbIcon />
                Basitleştirilmiş Metin
              </Typography>
            </CardHeader>
            <CardContent>
              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}

              {result ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                      {result.simplified_text}
                    </Typography>
                  </Paper>

                  {/* Statistics */}
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.50' }}>
                        <Typography variant="h4" color={`${getComplexityColor(result.complexity_score)}.main`} fontWeight="bold">
                          {result.complexity_score.toFixed(1)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Karmaşıklık Skoru
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={6}>
                      <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.50' }}>
                        <Typography variant="h4" color={`${getReadabilityColor(result.readability_score)}.main`} fontWeight="bold">
                          {result.readability_score.toFixed(1)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Okunabilirlik Skoru
                        </Typography>
                      </Paper>
                    </Grid>
                  </Grid>

                  {/* Improvements */}
                  <Box>
                    <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                      İyileştirmeler:
                    </Typography>
                    <Grid container spacing={1}>
                      <Grid item xs={6}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">Uzunluk:</Typography>
                          <Typography variant="body2" fontWeight="medium">
                            {result.stats.length_reduction > 0 ? '-' : '+'}
                            {Math.abs(result.stats.length_reduction)} karakter
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">Karmaşıklık:</Typography>
                          <Typography variant="body2" fontWeight="medium" color="success.main">
                            -{result.stats.complexity_reduction.toFixed(1)}
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">Okunabilirlik:</Typography>
                          <Typography variant="body2" fontWeight="medium" color="success.main">
                            +{result.stats.readability_improvement.toFixed(1)}
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">Değişiklik:</Typography>
                          <Typography variant="body2" fontWeight="medium">
                            {result.stats.changes_count} adet
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </Box>

                  {/* Changes Made */}
                  {result.changes_made.length > 0 && (
                    <Box>
                      <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                        Yapılan Değişiklikler:
                      </Typography>
                      <Box sx={{ maxHeight: 120, overflowY: 'auto' }}>
                        {result.changes_made.map((change, index) => (
                          <Chip
                            key={index}
                            label={change}
                            size="small"
                            variant="outlined"
                            sx={{ m: 0.5, fontSize: '0.75rem' }}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}

                  <Typography variant="caption" color="text.secondary" textAlign="center">
                    İşlem süresi: {(result.stats.processing_time * 1000).toFixed(0)}ms
                  </Typography>
                </Box>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
                  <BrainIcon sx={{ fontSize: 48, opacity: 0.5, mb: 1 }} />
                  <Typography>Basitleştirme sonucu burada görünecek</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Level Information */}
      <Card sx={{ mt: 3 }}>
        <CardHeader>
          <Typography variant="h6">Basitleştirme Seviyeleri</Typography>
        </CardHeader>
        <CardContent>
          <Grid container spacing={2}>
            {simplificationLevels.map((level) => (
              <Grid item xs={12} md={4} key={level.value}>
                <Paper
                  sx={{
                    p: 2,
                    border: 2,
                    borderColor: simplificationLevel === level.value ? 'primary.main' : 'grey.300',
                    bgcolor: simplificationLevel === level.value ? 'primary.50' : 'background.paper',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onClick={() => setSimplificationLevel(level.value)}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    {level.icon}
                    <Typography variant="subtitle1" fontWeight="semibold">
                      {level.label}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {level.description}
                  </Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default TextSimplifier;