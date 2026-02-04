/**
 * OSYM Question Generator Page
 * AI-powered OSYM question generation with Turkish optimization
 */

import React, { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
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
  Divider
} from '@mui/material'
import {
  AutoAwesome,
  Science,
  Calculate,
  MenuBook,
  Language,
  Psychology,
  Lightbulb
} from '@mui/icons-material'

interface QuestionGenerationParams {
  topic: string
  subtopic: string
  examType: 'TYT' | 'AYT' | 'YDT' | 'LGS'
  subject: string
  difficulty: number
  bloomLevel: number
  provider: 'ensemble' | 'openai' | 'claude' | 'qwen'
}

interface GeneratedQuestion {
  id: string
  stem: string
  options: string[]
  correct_answer: number
  explanation: string
  keywords: string[]
  difficulty: number
  quality_score: number
  tokens_used: number
  cost_usd: number
  generation_time_ms: number
}

export const OSYMQuestionGeneratorPage: React.FC = () => {
  const [params, setParams] = useState<QuestionGenerationParams>({
    topic: '',
    subtopic: '',
    examType: 'TYT',
    subject: 'Matematik',
    difficulty: 0.5,
    bloomLevel: 3,
    provider: 'ensemble'
  })

  const [generating, setGenerating] = useState(false)
  const [question, setQuestion] = useState<GeneratedQuestion | null>(null)
  const [error, setError] = useState<string | null>(null)

  const subjects = {
    TYT: ['Matematik', 'Türkçe', 'Fen Bilimleri', 'Sosyal Bilimler'],
    AYT: ['Matematik', 'Fizik', 'Kimya', 'Biyoloji', 'Edebiyat', 'Tarih', 'Coğrafya'],
    YDT: ['İngilizce', 'Almanca', 'Fransızca'],
    LGS: ['Matematik', 'Türkçe', 'Fen Bilimleri', 'İnkılap Tarihi', 'Din Kültürü', 'İngilizce']
  }

  const bloomLevels = [
    { level: 1, label: 'Bilgi (Hatırlama)', icon: '📝' },
    { level: 2, label: 'Kavrama (Anlama)', icon: '💡' },
    { level: 3, label: 'Uygulama', icon: '🔧' },
    { level: 4, label: 'Analiz', icon: '🔍' },
    { level: 5, label: 'Sentez (Değerlendirme)', icon: '⚖️' },
    { level: 6, label: 'Yaratma', icon: '🎨' }
  ]

  const handleGenerate = async () => {
    if (!params.topic || !params.subtopic) {
      setError('Lütfen konu ve alt konu alanlarını doldurun')
      return
    }

    setGenerating(true)
    setError(null)
    setQuestion(null)

    try {
      const response = await fetch('/api/osym/generate-question', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      })

      if (!response.ok) {
        throw new Error('Soru üretimi başarısız oldu')
      }

      const data = await response.json()
      setQuestion(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bir hata oluştu')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AutoAwesome color="primary" />
          AI-Powered OSYM Soru Üretici
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Multi-LLM ensemble ile Türkçe optimize edilmiş ÖSYM soruları üretin
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Left Panel - Parameters */}
        <Grid item xs={12} md={5}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Soru Parametreleri
              </Typography>

              {/* Exam Type */}
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Sınav Türü</InputLabel>
                <Select
                  value={params.examType}
                  label="Sınav Türü"
                  onChange={(e) => setParams({ ...params, examType: e.target.value as any })}
                >
                  <MenuItem value="TYT">TYT</MenuItem>
                  <MenuItem value="AYT">AYT</MenuItem>
                  <MenuItem value="YDT">YDT</MenuItem>
                  <MenuItem value="LGS">LGS</MenuItem>
                </Select>
              </FormControl>

              {/* Subject */}
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Ders</InputLabel>
                <Select
                  value={params.subject}
                  label="Ders"
                  onChange={(e) => setParams({ ...params, subject: e.target.value })}
                >
                  {subjects[params.examType].map((subject) => (
                    <MenuItem key={subject} value={subject}>
                      {subject}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Topic */}
              <TextField
                fullWidth
                label="Konu"
                placeholder="Örn: Türev"
                value={params.topic}
                onChange={(e) => setParams({ ...params, topic: e.target.value })}
                sx={{ mb: 2 }}
              />

              {/* Subtopic */}
              <TextField
                fullWidth
                label="Alt Konu"
                placeholder="Örn: Türev Alma Kuralları"
                value={params.subtopic}
                onChange={(e) => setParams({ ...params, subtopic: e.target.value })}
                sx={{ mb: 2 }}
              />

              {/* Difficulty */}
              <Box sx={{ mb: 2 }}>
                <Typography gutterBottom>
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
                    { value: 1, label: 'Zor' }
                  ]}
                />
              </Box>

              {/* Bloom Level */}
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Bloom Taksonomisi</InputLabel>
                <Select
                  value={params.bloomLevel}
                  label="Bloom Taksonomisi"
                  onChange={(e) => setParams({ ...params, bloomLevel: e.target.value as number })}
                >
                  {bloomLevels.map((bloom) => (
                    <MenuItem key={bloom.level} value={bloom.level}>
                      {bloom.icon} {bloom.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Provider */}
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>AI Provider</InputLabel>
                <Select
                  value={params.provider}
                  label="AI Provider"
                  onChange={(e) => setParams({ ...params, provider: e.target.value as any })}
                >
                  <MenuItem value="ensemble">🎯 Ensemble (Önerilen)</MenuItem>
                  <MenuItem value="openai">🤖 OpenAI GPT-4</MenuItem>
                  <MenuItem value="claude">⚡ Claude 3.5</MenuItem>
                  <MenuItem value="qwen">🚀 Qwen 2.5 (Türkçe Optimize)</MenuItem>
                </Select>
              </FormControl>

              <Button
                variant="contained"
                fullWidth
                size="large"
                onClick={handleGenerate}
                disabled={generating || !params.topic || !params.subtopic}
                startIcon={generating ? <CircularProgress size={20} /> : <AutoAwesome />}
              >
                {generating ? 'Soru Üretiliyor...' : 'Soru Üret'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Right Panel - Generated Question */}
        <Grid item xs={12} md={7}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {question && (
            <Card>
              <CardContent>
                <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="h6">Üretilen Soru</Typography>
                  <Chip
                    label={`Kalite: ${question.quality_score.toFixed(1)}/100`}
                    color={question.quality_score >= 80 ? 'success' : question.quality_score >= 60 ? 'warning' : 'error'}
                  />
                </Box>

                {/* Question Stem */}
                <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default', mb: 2 }}>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                    {question.stem}
                  </Typography>
                </Paper>

                {/* Options */}
                <Box sx={{ mb: 2 }}>
                  {question.options.map((option, index) => (
                    <Paper
                      key={index}
                      elevation={0}
                      sx={{
                        p: 1.5,
                        mb: 1,
                        bgcolor: index === question.correct_answer ? 'success.light' : 'background.default',
                        border: index === question.correct_answer ? '2px solid' : '1px solid',
                        borderColor: index === question.correct_answer ? 'success.main' : 'divider'
                      }}
                    >
                      <Typography variant="body2">
                        <strong>{String.fromCharCode(65 + index)})</strong> {option}
                      </Typography>
                    </Paper>
                  ))}
                </Box>

                <Divider sx={{ my: 2 }} />

                {/* Explanation */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Açıklama:
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {question.explanation}
                  </Typography>
                </Box>

                {/* Keywords */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Anahtar Kelimeler:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {question.keywords.map((keyword, index) => (
                      <Chip key={index} label={keyword} size="small" variant="outlined" />
                    ))}
                  </Box>
                </Box>

                <Divider sx={{ my: 2 }} />

                {/* Metrics */}
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">
                      Token Kullanımı
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {question.tokens_used}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">
                      Maliyet
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">
                      ${question.cost_usd.toFixed(4)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">
                      Zorluk (IRT)
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {question.difficulty.toFixed(2)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">
                      Süre
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {(question.generation_time_ms / 1000).toFixed(1)}s
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}

          {!question && !error && (
            <Card>
              <CardContent>
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  <AutoAwesome sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    Henüz soru üretilmedi
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Sol panelden parametreleri ayarlayın ve "Soru Üret" butonuna tıklayın
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  )
}

export default OSYMQuestionGeneratorPage
