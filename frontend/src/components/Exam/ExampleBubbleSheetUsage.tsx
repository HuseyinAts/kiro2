/**
 * Optik Form Arayüzü Kullanım Örneği
 * BubbleSheetInterface ve BubbleSheetPanel bileşenlerinin entegrasyonu
 * 
 * Bu dosya, mevcut OSYMExamInterface bileşenine optik form görünümünün
 * nasıl entegre edileceğini gösterir.
 */
import React, { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  ToggleButton,
  ToggleButtonGroup,
  Divider
} from '@mui/material'
import {
  ViewList,
  GridView,
  RadioButtonChecked
} from '@mui/icons-material'
import BubbleSheetInterface from './BubbleSheetInterface'
import BubbleSheetPanel from './BubbleSheetPanel'

/**
 * Örnek: Tek soru için optik form kullanımı
 */
export const SingleQuestionExample: React.FC = () => {
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null)

  return (
    <Paper elevation={3} sx={{ p: 3, maxWidth: 800, mx: 'auto', my: 4 }}>
      <Typography variant="h5" gutterBottom>
        Tek Soru - Optik Form Örneği
      </Typography>
      <Divider sx={{ my: 2 }} />

      <Typography variant="body1" sx={{ mb: 3 }}>
        Aşağıdaki sorunun doğru cevabını optik formda işaretleyiniz:
      </Typography>

      <Typography variant="h6" sx={{ mb: 2 }}>
        1. Türkiye'nin başkenti neresidir?
      </Typography>

      <BubbleSheetInterface
        questionNumber={1}
        options={['A', 'B', 'C', 'D', 'E']}
        selectedAnswer={selectedAnswer}
        onAnswerSelect={setSelectedAnswer}
        size="large"
      />

      <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
        <Typography variant="body2" color="textSecondary">
          Seçilen cevap: {selectedAnswer || 'Henüz seçilmedi'}
        </Typography>
        <Button
          variant="outlined"
          size="small"
          onClick={() => setSelectedAnswer(null)}
        >
          Temizle
        </Button>
      </Box>
    </Paper>
  )
}

/**
 * Örnek: Çoklu soru için optik form paneli kullanımı
 */
export const MultipleQuestionsExample: React.FC = () => {
  const [answers, setAnswers] = useState<Record<string, string>>({
    'q1': 'A',
    'q2': 'C',
    'q3': ''
  })

  const [currentQuestion, setCurrentQuestion] = useState(0)

  const questions = [
    { id: 'q1', number: 1, subject: 'Matematik', topic: 'Cebir' },
    { id: 'q2', number: 2, subject: 'Matematik', topic: 'Geometri' },
    { id: 'q3', number: 3, subject: 'Türkçe', topic: 'Dil Bilgisi' },
    { id: 'q4', number: 4, subject: 'Türkçe', topic: 'Anlam Bilgisi' },
    { id: 'q5', number: 5, subject: 'Fen', topic: 'Fizik' },
    { id: 'q6', number: 6, subject: 'Fen', topic: 'Kimya' },
    { id: 'q7', number: 7, subject: 'Sosyal', topic: 'Tarih' },
    { id: 'q8', number: 8, subject: 'Sosyal', topic: 'Coğrafya' }
  ]

  const handleAnswerChange = (questionId: string, answer: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }))
  }

  return (
    <Paper elevation={3} sx={{ p: 3, maxWidth: 1200, mx: 'auto', my: 4 }}>
      <Typography variant="h5" gutterBottom>
        Çoklu Soru - Optik Form Paneli Örneği
      </Typography>
      <Divider sx={{ my: 2 }} />

      <BubbleSheetPanel
        questions={questions}
        answers={answers}
        onAnswerChange={handleAnswerChange}
        currentQuestionIndex={currentQuestion}
        onQuestionNavigate={setCurrentQuestion}
        showSubjects={true}
        columns={2}
        size="medium"
      />

      <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.100', borderRadius: 2 }}>
        <Typography variant="body2" color="textSecondary">
          <strong>İpucu:</strong> Soruların üzerine tıklayarak o soruya geçebilirsiniz.
          Boş soruları vurgulamak için göz ikonuna tıklayın.
        </Typography>
      </Box>
    </Paper>
  )
}

/**
 * Örnek: Mevcut OSYMExamInterface'e entegrasyon
 */
export const IntegrationExample: React.FC = () => {
  const [viewMode, setViewMode] = useState<'standard' | 'bubble'>('standard')
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>('B')

  return (
    <Paper elevation={3} sx={{ p: 3, maxWidth: 800, mx: 'auto', my: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">
          Görünüm Modu Seçimi
        </Typography>

        <ToggleButtonGroup
          value={viewMode}
          exclusive
          onChange={(_, newMode) => newMode && setViewMode(newMode)}
          size="small"
        >
          <ToggleButton value="standard">
            <ViewList sx={{ mr: 1 }} />
            Standart
          </ToggleButton>
          <ToggleButton value="bubble">
            <RadioButtonChecked sx={{ mr: 1 }} />
            Optik Form
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Divider sx={{ my: 2 }} />

      <Typography variant="h6" sx={{ mb: 2 }}>
        1. Aşağıdakilerden hangisi doğrudur?
      </Typography>

      {viewMode === 'standard' ? (
        // Standart radio button görünümü
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {['A', 'B', 'C', 'D', 'E'].map(option => (
            <Button
              key={option}
              variant={selectedAnswer === option ? 'contained' : 'outlined'}
              onClick={() => setSelectedAnswer(option)}
              sx={{ justifyContent: 'flex-start', textAlign: 'left' }}
            >
              {option}) Seçenek {option}
            </Button>
          ))}
        </Box>
      ) : (
        // Optik form görünümü
        <BubbleSheetInterface
          questionNumber={1}
          options={['A', 'B', 'C', 'D', 'E']}
          selectedAnswer={selectedAnswer}
          onAnswerSelect={setSelectedAnswer}
          size="large"
        />
      )}

      <Box sx={{ mt: 3, p: 2, bgcolor: 'info.50', borderRadius: 2 }}>
        <Typography variant="body2" color="info.main">
          <strong>Not:</strong> Öğrenciler sınav sırasında görünüm modunu değiştirebilir.
          Optik form görünümü, gerçek ÖSYM sınavlarına daha çok benzer.
        </Typography>
      </Box>
    </Paper>
  )
}

/**
 * Ana örnek bileşeni - Tüm örnekleri gösterir
 */
export const BubbleSheetExamples: React.FC = () => {
  return (
    <Box sx={{ py: 4 }}>
      <Typography variant="h4" align="center" gutterBottom>
        Optik Form Arayüzü Örnekleri
      </Typography>
      <Typography variant="body1" align="center" color="textSecondary" sx={{ mb: 4 }}>
        ÖSYM sınavlarında kullanılan optik form görünümü
      </Typography>

      <SingleQuestionExample />
      <MultipleQuestionsExample />
      <IntegrationExample />
    </Box>
  )
}

export default BubbleSheetExamples
