/**
 * Modern Exam Results Page
 * Glassmorphism ile detaylı sınav sonuçları analizi
 */

import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Container,
  Typography,
  Box,
  Grid,
  Chip,
  LinearProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Divider
} from '@mui/material'
import {
  Assessment as AssessmentIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  HelpOutline as EmptyIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  Replay as ReplayIcon,
  Home as HomeIcon,
  EmojiEvents as TrophyIcon
} from '@mui/icons-material'
import { GlassCard } from '../components/ui/GlassCard'
import { ModernButton } from '../components/ui/ModernButton'
import { modernColors } from '../theme/modern-colors'

interface ExamResult {
  sinav_id: string
  exam_type: string
  subject: string
  question_count: number
  correct_count: number
  wrong_count: number
  empty_count: number
  score: number
  duration: number
  completed_at: string
  questions: Array<{
    question_id: string
    question_text: string
    user_answer: string | null
    correct_answer: string
    is_correct: boolean
    time_spent: number
  }>
  subject_breakdown: Array<{
    subject: string
    correct: number
    wrong: number
    empty: number
    total: number
  }>
}

export const ModernExamResultsPage: React.FC = () => {
  const { sinavId } = useParams<{ sinavId: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [result, setResult] = useState<ExamResult | null>(null)

  useEffect(() => {
    if (sinavId) {
      fetchExamResults()
    }
  }, [sinavId])

  const fetchExamResults = async () => {
    try {
      const response = await fetch(`/api/v1/exams/${sinavId}/results`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      if (!response.ok) throw new Error()
      const data = await response.json()
      setResult(data)
    } catch {
      // Mock data
      setResult({
        sinav_id: sinavId!,
        exam_type: 'TYT',
        subject: 'Matematik',
        question_count: 40,
        correct_count: 32,
        wrong_count: 5,
        empty_count: 3,
        score: 85,
        duration: 65,
        completed_at: '2025-11-21T10:30:00',
        questions: Array.from({ length: 40 }, (_, i) => ({
          question_id: `q${i + 1}`,
          question_text: `Soru ${i + 1}`,
          user_answer: i < 32 ? 'A' : i < 37 ? 'B' : null,
          correct_answer: 'A',
          is_correct: i < 32,
          time_spent: Math.floor(Math.random() * 120) + 30
        })),
        subject_breakdown: [
          { subject: 'Sayılar', correct: 8, wrong: 1, empty: 1, total: 10 },
          { subject: 'Geometri', correct: 7, wrong: 2, empty: 1, total: 10 },
          { subject: 'Cebir', correct: 10, wrong: 0, empty: 0, total: 10 },
          { subject: 'Olasılık', correct: 7, wrong: 2, empty: 1, total: 10 }
        ]
      })
    } finally {
      setLoading(false)
    }
  }

  if (!sinavId) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">Sınav ID bulunamadı</Alert>
      </Container>
    )
  }

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <LinearProgress />
        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block', textAlign: 'center' }}>
          Sonuçlar yükleniyor...
        </Typography>
      </Container>
    )
  }

  if (!result) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">Sonuçlar yüklenemedi</Alert>
      </Container>
    )
  }

  const getScoreGradient = (score: number): string => {
    if (score >= 85) return modernColors.gradients.success
    if (score >= 70) return modernColors.gradients.primary
    if (score >= 50) return modernColors.gradients.warning
    return modernColors.gradients.error
  }

  const getScoreIcon = (score: number) => {
    if (score >= 85) return '🏆'
    if (score >= 70) return '🎯'
    if (score >= 50) return '📈'
    return '💪'
  }

  const getScoreMessage = (score: number) => {
    if (score >= 85) return 'Mükemmel! Harika bir performans sergiledinizyürümeye devam edin!'
    if (score >= 70) return 'Çok iyi! Biraz daha çalışarak daha da iyiye gidebilirsiniz.'
    if (score >= 50) return 'İyi bir başlangıç! Eksik konularınızı çalışmaya devam edin.'
    return 'Daha fazla çalışmanız gerekiyor. Pes etmeyin, başarısız olabilirsiniz!'
  }

  const successRate = ((result.correct_count / result.question_count) * 100).toFixed(1)
  const avgTimePerQuestion = (result.duration / result.question_count).toFixed(1)

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Box sx={{ mb: 4 }}>
          <Box
            sx={{
              width: 56,
              height: 56,
              borderRadius: '16px',
              background: getScoreGradient(result.score),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mb: 2
            }}
          >
            <AssessmentIcon sx={{ fontSize: 32, color: 'white' }} />
          </Box>

          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              background: getScoreGradient(result.score),
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 1
            }}
          >
            Sınav Sonuçları {getScoreIcon(result.score)}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip label={result.exam_type} size="small" color="primary" />
            <Chip label={result.subject} size="small" variant="outlined" />
            <Typography variant="caption" color="text.secondary">
              {new Date(result.completed_at).toLocaleDateString('tr-TR', {
                day: 'numeric',
                month: 'long',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </Typography>
          </Box>
        </Box>
      </motion.div>

      {/* Ana Skor Kartı */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
      >
        <GlassCard sx={{ mb: 3, textAlign: 'center', py: 4 }}>
          <Box
            sx={{
              width: 120,
              height: 120,
              borderRadius: '50%',
              background: getScoreGradient(result.score),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mx: 'auto',
              mb: 2
            }}
          >
            <Typography variant="h2" fontWeight={700} color="white">
              {result.score}
            </Typography>
          </Box>

          <Typography variant="h6" gutterBottom>{getScoreMessage(result.score)}</Typography>

          <Grid container spacing={2} sx={{ mt: 3 }}>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">Doğru</Typography>
              <Typography variant="h5" fontWeight={600} color="success.main">
                <CheckIcon sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                {result.correct_count}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">Yanlış</Typography>
              <Typography variant="h5" fontWeight={600} color="error.main">
                <CancelIcon sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                {result.wrong_count}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">Boş</Typography>
              <Typography variant="h5" fontWeight={600} color="text.secondary">
                <EmptyIcon sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                {result.empty_count}
              </Typography>
            </Grid>
          </Grid>
        </GlassCard>
      </motion.div>

      {/* İstatistikler */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <GlassCard>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">Başarı Oranı</Typography>
                <TrendingUpIcon sx={{ color: 'success.main' }} />
              </Box>
              <Typography variant="h4" fontWeight={700}>{successRate}%</Typography>
              <LinearProgress
                variant="determinate"
                value={parseFloat(successRate)}
                sx={{
                  mt: 1,
                  height: 6,
                  borderRadius: 3,
                  background: 'rgba(0,0,0,0.1)',
                  '& .MuiLinearProgress-bar': {
                    background: getScoreGradient(result.score)
                  }
                }}
              />
            </GlassCard>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.25 }}
          >
            <GlassCard>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">Toplam Süre</Typography>
                <SpeedIcon sx={{ color: 'primary.main' }} />
              </Box>
              <Typography variant="h4" fontWeight={700}>{result.duration}<Typography variant="caption">dk</Typography></Typography>
              <Typography variant="caption" color="text.secondary">
                {result.time_limit} dakika limit
              </Typography>
            </GlassCard>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
          >
            <GlassCard>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">Ort. Süre/Soru</Typography>
                <SpeedIcon sx={{ color: 'warning.main' }} />
              </Box>
              <Typography variant="h4" fontWeight={700}>{avgTimePerQuestion}<Typography variant="caption">dk</Typography></Typography>
              <Typography variant="caption" color="text.secondary">
                soru başına
              </Typography>
            </GlassCard>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.35 }}
          >
            <GlassCard>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">Toplam Soru</Typography>
                <TrophyIcon sx={{ color: 'error.main' }} />
              </Box>
              <Typography variant="h4" fontWeight={700}>{result.question_count}</Typography>
              <Typography variant="caption" color="text.secondary">
                soru çözüldü
              </Typography>
            </GlassCard>
          </motion.div>
        </Grid>
      </Grid>

      {/* Konu Bazlı Analiz */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <GlassCard sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
            Konu Bazlı Performans
          </Typography>

          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Konu</strong></TableCell>
                <TableCell align="center"><strong>Doğru</strong></TableCell>
                <TableCell align="center"><strong>Yanlış</strong></TableCell>
                <TableCell align="center"><strong>Boş</strong></TableCell>
                <TableCell align="center"><strong>Başarı</strong></TableCell>
                <TableCell><strong>Durum</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {result.subject_breakdown.map((item, index) => {
                const success = ((item.correct / item.total) * 100).toFixed(0)
                return (
                  <TableRow key={index}>
                    <TableCell>{item.subject}</TableCell>
                    <TableCell align="center">
                      <Chip label={item.correct} size="small" color="success" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label={item.wrong} size="small" color="error" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label={item.empty} size="small" />
                    </TableCell>
                    <TableCell align="center">{success}%</TableCell>
                    <TableCell>
                      <LinearProgress
                        variant="determinate"
                        value={parseFloat(success)}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          background: 'rgba(0,0,0,0.1)',
                          '& .MuiLinearProgress-bar': {
                            background: getScoreGradient(parseFloat(success))
                          }
                        }}
                      />
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </GlassCard>
      </motion.div>

      {/* Aksiyonlar */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <ModernButton
            variant="contained"
            startIcon={<ReplayIcon />}
            onClick={() => navigate('/exam/start')}
            sx={{ background: modernColors.gradients.primary }}
          >
            Yeni Sınav Başlat
          </ModernButton>
          <ModernButton
            variant="outlined"
            startIcon={<HomeIcon />}
            onClick={() => navigate('/dashboard')}
          >
            Ana Sayfaya Dön
          </ModernButton>
        </Box>
      </motion.div>
    </Container>
  )
}

export default ModernExamResultsPage
