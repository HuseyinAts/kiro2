/**
 * ExamInterface Kullanım Örneği
 * 
 * Task 69: Sınav Arayüzü özellikleri demonstrasyonu
 */
import React, { useState, useCallback, useEffect } from 'react'
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Alert,
  LinearProgress,
  Divider
} from '@mui/material'
import { Timer, Save } from '@mui/icons-material'
import ExamInterface, { ExamQuestion, ExamAnswer } from './ExamInterface'

/**
 * Örnek sınav soruları
 */
const sampleQuestions: ExamQuestion[] = [
  {
    id: 'q1',
    number: 1,
    content: 'Aşağıdaki sayılardan hangisi asal sayıdır?',
    options: ['A', 'B', 'C', 'D', 'E'],
    subject: 'Matematik',
    topic: 'Sayılar'
  },
  {
    id: 'q2',
    number: 2,
    content: 'Türkçe\'de kaç tane ünlü harf vardır?',
    options: ['A', 'B', 'C', 'D', 'E'],
    subject: 'Türkçe',
    topic: 'Ses Bilgisi'
  },
  {
    id: 'q3',
    number: 3,
    content: 'Newton\'un hareket yasaları kaç tanedir?',
    options: ['A', 'B', 'C', 'D', 'E'],
    subject: 'Fizik',
    topic: 'Hareket'
  },
  {
    id: 'q4',
    number: 4,
    content: 'Osmanlı Devleti hangi yüzyılda kurulmuştur?',
    options: ['A', 'B', 'C', 'D', 'E'],
    subject: 'Tarih',
    topic: 'Osmanlı Tarihi'
  },
  {
    id: 'q5',
    number: 5,
    content: 'Periyodik tabloda kaç element vardır?',
    options: ['A', 'B', 'C', 'D', 'E'],
    subject: 'Kimya',
    topic: 'Periyodik Tablo'
  }
]

/**
 * ExamInterface kullanım örneği
 */
export const ExamInterfaceExample: React.FC = () => {
  const [answers, setAnswers] = useState<Record<string, ExamAnswer>>({})
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [examStarted, setExamStarted] = useState(false)
  const [examFinished, setExamFinished] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(300) // 5 dakika
  const [autoSaveStatus, setAutoSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle')

  /**
   * Sınav süre sayacı
   */
  useEffect(() => {
    if (!examStarted || examFinished) return

    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          handleFinishExam()
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [examStarted, examFinished])

  /**
   * Otomatik kaydetme (her 30 saniyede bir)
   * REQ-1.6: Otomatik kaydetme ile veri kaybını önleme
   */
  useEffect(() => {
    if (!examStarted || examFinished) return

    const autoSaveInterval = setInterval(() => {
      handleAutoSave()
    }, 30000) // 30 saniye

    return () => clearInterval(autoSaveInterval)
  }, [examStarted, examFinished, answers])

  /**
   * Cevap değiştirme işleyicisi
   */
  const handleAnswerChange = useCallback((questionId: string, answer: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: {
        questionId,
        answer,
        flaggedForReview: prev[questionId]?.flaggedForReview || false,
        timestamp: new Date()
      }
    }))
  }, [])

  /**
   * Şüpheli işaretleme işleyicisi
   */
  const handleFlagToggle = useCallback((questionId: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: {
        questionId,
        answer: prev[questionId]?.answer || '',
        flaggedForReview: !prev[questionId]?.flaggedForReview,
        timestamp: new Date()
      }
    }))
  }, [])

  /**
   * Soru navigasyonu işleyicisi
   */
  const handleQuestionNavigate = useCallback((index: number) => {
    setCurrentQuestionIndex(index)
  }, [])

  /**
   * Sınavı başlat
   */
  const handleStartExam = () => {
    setExamStarted(true)
    setAnswers({})
    setCurrentQuestionIndex(0)
    setTimeRemaining(300)
  }

  /**
   * Sınavı bitir
   */
  const handleFinishExam = () => {
    setExamFinished(true)
    handleAutoSave()
  }

  /**
   * Otomatik kaydetme
   */
  const handleAutoSave = async () => {
    setAutoSaveStatus('saving')
    
    // Simüle edilmiş kaydetme işlemi
    await new Promise(resolve => setTimeout(resolve, 500))
    
    console.log('Cevaplar kaydedildi:', answers)
    setAutoSaveStatus('saved')
    
    setTimeout(() => setAutoSaveStatus('idle'), 2000)
  }

  /**
   * Süreyi formatla
   */
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  /**
   * İstatistikleri hesapla
   */
  const stats = {
    total: sampleQuestions.length,
    answered: Object.values(answers).filter(a => a.answer).length,
    flagged: Object.values(answers).filter(a => a.flaggedForReview).length,
    percentage: Math.round((Object.values(answers).filter(a => a.answer).length / sampleQuestions.length) * 100)
  }

  /**
   * Sınav başlamadıysa başlangıç ekranı
   */
  if (!examStarted) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h4" gutterBottom>
            Sınav Arayüzü Demo
          </Typography>
          <Typography variant="body1" color="textSecondary" paragraph>
            Task 69: Sınav Arayüzü özellikleri demonstrasyonu
          </Typography>

          <Divider sx={{ my: 3 }} />

          <Box sx={{ textAlign: 'left', mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Özellikler:
            </Typography>
            <Typography variant="body2" paragraph>
              ✅ <strong>69.1 İşaretleme Sistemi:</strong> Cevap seçme, değiştirme ve görsel onay
            </Typography>
            <Typography variant="body2" paragraph>
              ✅ <strong>69.2 Boş Bırakma:</strong> Boş soru takibi ve tamamlanma yüzdesi
            </Typography>
            <Typography variant="body2" paragraph>
              ✅ <strong>69.3 Şüpheli İşaretleme:</strong> İnceleme için soru işaretleme
            </Typography>
            <Typography variant="body2" paragraph>
              ✅ <strong>69.4 Soru Navigasyonu:</strong> Soru haritası ve hızlı gezinme
            </Typography>
          </Box>

          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Klavye Kısayolları:</strong><br />
              • ← → : Sorular arası gezinme<br />
              • A-E : Cevap seçimi<br />
              • F : Şüpheli işaretleme
            </Typography>
          </Alert>

          <Button
            variant="contained"
            size="large"
            onClick={handleStartExam}
            sx={{ mt: 2 }}
          >
            Sınavı Başlat
          </Button>
        </Paper>
      </Container>
    )
  }

  /**
   * Sınav bittiyse sonuç ekranı
   */
  if (examFinished) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h4" gutterBottom color="success.main">
            Sınav Tamamlandı!
          </Typography>

          <Divider sx={{ my: 3 }} />

          <Box sx={{ textAlign: 'left', mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Sonuçlar:
            </Typography>
            <Typography variant="body1" paragraph>
              Toplam Soru: {stats.total}
            </Typography>
            <Typography variant="body1" paragraph>
              Cevaplanan: {stats.answered}
            </Typography>
            <Typography variant="body1" paragraph>
              Boş: {stats.total - stats.answered}
            </Typography>
            <Typography variant="body1" paragraph>
              İşaretli: {stats.flagged}
            </Typography>
            <Typography variant="body1" paragraph>
              Tamamlanma: %{stats.percentage}
            </Typography>
          </Box>

          <Button
            variant="contained"
            onClick={() => {
              setExamStarted(false)
              setExamFinished(false)
              setAnswers({})
            }}
          >
            Yeni Sınav Başlat
          </Button>
        </Paper>
      </Container>
    )
  }

  /**
   * Sınav ekranı
   */
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', py: 2 }}>
      <Container maxWidth="xl">
        {/* Üst bilgi çubuğu */}
        <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Typography variant="h6">
              Demo Sınavı
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              {/* Süre */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Timer color={timeRemaining < 60 ? 'error' : 'primary'} />
                <Typography
                  variant="h6"
                  color={timeRemaining < 60 ? 'error' : 'primary'}
                >
                  {formatTime(timeRemaining)}
                </Typography>
              </Box>

              {/* Otomatik kaydetme durumu */}
              {autoSaveStatus === 'saving' && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Save fontSize="small" />
                  <Typography variant="body2">Kaydediliyor...</Typography>
                </Box>
              )}
              {autoSaveStatus === 'saved' && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Save fontSize="small" color="success" />
                  <Typography variant="body2" color="success.main">
                    Kaydedildi
                  </Typography>
                </Box>
              )}

              {/* Bitir butonu */}
              <Button
                variant="contained"
                color="error"
                onClick={handleFinishExam}
              >
                Sınavı Bitir
              </Button>
            </Box>
          </Box>

          {/* İlerleme çubuğu */}
          <Box sx={{ mt: 2 }}>
            <LinearProgress
              variant="determinate"
              value={stats.percentage}
              sx={{ height: 8, borderRadius: 4 }}
            />
            <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5, display: 'block' }}>
              %{stats.percentage} Tamamlandı ({stats.answered}/{stats.total})
            </Typography>
          </Box>
        </Paper>

        {/* Sınav arayüzü */}
        <ExamInterface
          questions={sampleQuestions}
          answers={answers}
          currentQuestionIndex={currentQuestionIndex}
          onAnswerChange={handleAnswerChange}
          onFlagToggle={handleFlagToggle}
          onQuestionNavigate={handleQuestionNavigate}
          disabled={false}
          showNavigationPanel={true}
        />
      </Container>
    </Box>
  )
}

export default ExamInterfaceExample
