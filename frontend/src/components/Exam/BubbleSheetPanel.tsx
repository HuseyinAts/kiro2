/**
 * Optik Form Paneli - Çoklu Soru Görünümü
 * ÖSYM optik formlarına benzer tam sayfa görünümü
 * 
 * REQ-1.1: TYT/AYT/YDT sınav formatı desteği
 * REQ-1.6: Otomatik kaydetme ile veri kaybı önleme
 */
import React, { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Divider,
  Chip,
  IconButton,
  Tooltip,
  useTheme,
  alpha,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material'
import {
  Visibility,
  VisibilityOff,
  GridView,
  ViewList,
  Info,
  CheckCircle,
  Warning
} from '@mui/icons-material'
import BubbleSheetInterface from './BubbleSheetInterface'

interface Question {
  id: string
  number: number
  subject?: string
  topic?: string
}

interface BubbleSheetPanelProps {
  questions: Question[]
  answers: Record<string, string>
  onAnswerChange: (questionId: string, answer: string) => void
  currentQuestionIndex?: number
  onQuestionNavigate?: (index: number) => void
  disabled?: boolean
  showSubjects?: boolean
  columns?: 1 | 2 | 3 | 4
  size?: 'small' | 'medium' | 'large'
}

/**
 * Optik form paneli - Tüm soruların bubble sheet görünümü
 */
export const BubbleSheetPanel: React.FC<BubbleSheetPanelProps> = ({
  questions,
  answers,
  onAnswerChange,
  currentQuestionIndex,
  onQuestionNavigate,
  disabled = false,
  showSubjects = true,
  columns = 2,
  size = 'medium'
}) => {
  const theme = useTheme()
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [showInfo, setShowInfo] = useState(false)
  const [highlightUnanswered, setHighlightUnanswered] = useState(false)

  // Standart ÖSYM seçenekleri
  const standardOptions = ['A', 'B', 'C', 'D', 'E']

  /**
   * İstatistikleri hesapla
   */
  const stats = useMemo(() => {
    const answered = Object.keys(answers).filter(key => answers[key]).length
    const unanswered = questions.length - answered
    const percentage = questions.length > 0 ? (answered / questions.length) * 100 : 0

    return {
      total: questions.length,
      answered,
      unanswered,
      percentage: Math.round(percentage)
    }
  }, [questions, answers])

  /**
   * Konuya göre soruları grupla
   */
  const groupedQuestions = useMemo(() => {
    if (!showSubjects) return { 'Tüm Sorular': questions }

    return questions.reduce((groups, question) => {
      const subject = question.subject || 'Diğer'
      if (!groups[subject]) {
        groups[subject] = []
      }
      groups[subject].push(question)
      return groups
    }, {} as Record<string, Question[]>)
  }, [questions, showSubjects])

  /**
   * Soru tıklama işleyicisi
   */
  const handleQuestionClick = (questionIndex: number) => {
    if (onQuestionNavigate && !disabled) {
      onQuestionNavigate(questionIndex)
    }
  }

  /**
   * Grid görünümü
   */
  const renderGridView = () => (
    <Grid container spacing={2}>
      {Object.entries(groupedQuestions).map(([subject, subjectQuestions]) => (
        <Grid item xs={12} key={subject}>
          {showSubjects && Object.keys(groupedQuestions).length > 1 && (
            <>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Typography variant="h6" color="primary">
                  {subject}
                </Typography>
                <Chip
                  label={`${subjectQuestions.length} soru`}
                  size="small"
                  variant="outlined"
                />
              </Box>
              <Divider sx={{ mb: 2 }} />
            </>
          )}

          <Grid container spacing={1}>
            {subjectQuestions.map((question) => {
              const isCurrentQuestion = currentQuestionIndex === question.number - 1
              const isAnswered = !!answers[question.id]
              const shouldHighlight = highlightUnanswered && !isAnswered

              return (
                <Grid item xs={12} sm={12 / columns} key={question.id}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: question.number * 0.01 }}
                  >
                    <Paper
                      elevation={isCurrentQuestion ? 4 : 1}
                      sx={{
                        p: 1.5,
                        cursor: onQuestionNavigate ? 'pointer' : 'default',
                        border: 2,
                        borderColor: isCurrentQuestion
                          ? theme.palette.primary.main
                          : shouldHighlight
                          ? theme.palette.warning.main
                          : 'transparent',
                        bgcolor: isCurrentQuestion
                          ? alpha(theme.palette.primary.main, 0.05)
                          : shouldHighlight
                          ? alpha(theme.palette.warning.main, 0.05)
                          : 'background.paper',
                        transition: 'all 0.2s',
                        '&:hover': onQuestionNavigate && !disabled ? {
                          boxShadow: theme.shadows[4],
                          transform: 'translateY(-2px)'
                        } : {}
                      }}
                      onClick={() => handleQuestionClick(question.number - 1)}
                    >
                      <BubbleSheetInterface
                        questionNumber={question.number}
                        options={standardOptions}
                        selectedAnswer={answers[question.id] || null}
                        onAnswerSelect={(answer) => onAnswerChange(question.id, answer)}
                        disabled={disabled}
                        size={size}
                      />

                      {question.topic && (
                        <Typography
                          variant="caption"
                          color="textSecondary"
                          sx={{ mt: 1, display: 'block', textAlign: 'center' }}
                        >
                          {question.topic}
                        </Typography>
                      )}
                    </Paper>
                  </motion.div>
                </Grid>
              )
            })}
          </Grid>
        </Grid>
      ))}
    </Grid>
  )

  /**
   * Liste görünümü
   */
  const renderListView = () => (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      {questions.map((question) => {
        const isCurrentQuestion = currentQuestionIndex === question.number - 1
        const isAnswered = !!answers[question.id]
        const shouldHighlight = highlightUnanswered && !isAnswered

        return (
          <motion.div
            key={question.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: question.number * 0.005 }}
          >
            <Paper
              elevation={isCurrentQuestion ? 4 : 1}
              sx={{
                p: 2,
                cursor: onQuestionNavigate ? 'pointer' : 'default',
                border: 2,
                borderColor: isCurrentQuestion
                  ? theme.palette.primary.main
                  : shouldHighlight
                  ? theme.palette.warning.main
                  : 'transparent',
                bgcolor: isCurrentQuestion
                  ? alpha(theme.palette.primary.main, 0.05)
                  : shouldHighlight
                  ? alpha(theme.palette.warning.main, 0.05)
                  : 'background.paper',
                transition: 'all 0.2s',
                '&:hover': onQuestionNavigate && !disabled ? {
                  boxShadow: theme.shadows[4]
                } : {}
              }}
              onClick={() => handleQuestionClick(question.number - 1)}
            >
              <BubbleSheetInterface
                questionNumber={question.number}
                options={standardOptions}
                selectedAnswer={answers[question.id] || null}
                onAnswerSelect={(answer) => onAnswerChange(question.id, answer)}
                disabled={disabled}
                size={size}
              />
            </Paper>
          </motion.div>
        )
      })}
    </Box>
  )

  return (
    <Box>
      {/* Başlık ve kontroller */}
      <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          {/* İstatistikler */}
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip
              icon={<CheckCircle />}
              label={`${stats.answered}/${stats.total} Cevaplandı`}
              color="primary"
              variant="outlined"
            />
            <Chip
              icon={<Warning />}
              label={`${stats.unanswered} Boş`}
              color={stats.unanswered > 0 ? 'warning' : 'default'}
              variant="outlined"
            />
            <Chip
              label={`%${stats.percentage} Tamamlandı`}
              color={stats.percentage === 100 ? 'success' : 'default'}
              variant="outlined"
            />
          </Box>

          {/* Kontroller */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Bilgi">
              <IconButton size="small" onClick={() => setShowInfo(true)}>
                <Info />
              </IconButton>
            </Tooltip>

            <Tooltip title={highlightUnanswered ? 'Vurgulamayı kapat' : 'Boş soruları vurgula'}>
              <IconButton
                size="small"
                color={highlightUnanswered ? 'warning' : 'default'}
                onClick={() => setHighlightUnanswered(!highlightUnanswered)}
              >
                {highlightUnanswered ? <Visibility /> : <VisibilityOff />}
              </IconButton>
            </Tooltip>

            <Tooltip title={viewMode === 'grid' ? 'Liste görünümü' : 'Grid görünümü'}>
              <IconButton
                size="small"
                onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
              >
                {viewMode === 'grid' ? <ViewList /> : <GridView />}
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Paper>

      {/* Optik form içeriği */}
      <Box>
        {viewMode === 'grid' ? renderGridView() : renderListView()}
      </Box>

      {/* Bilgi dialog */}
      <Dialog open={showInfo} onClose={() => setShowInfo(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Optik Form Kullanımı</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="body2">
              <strong>Cevap İşaretleme:</strong> Doğru cevabı seçmek için ilgili bubble'a (daire) tıklayın.
            </Typography>
            <Typography variant="body2">
              <strong>İşareti Kaldırma:</strong> Seçili bubble'a tekrar tıklayarak işareti kaldırabilirsiniz.
            </Typography>
            <Typography variant="body2">
              <strong>Klavye Kullanımı:</strong> Tab tuşu ile bubble'lar arasında gezinebilir, Enter veya Space tuşu ile seçim yapabilirsiniz.
            </Typography>
            <Typography variant="body2">
              <strong>Otomatik Kaydetme:</strong> Cevaplarınız her 30 saniyede bir otomatik olarak kaydedilir.
            </Typography>
            <Typography variant="body2" color="warning.main">
              <strong>Önemli:</strong> Sınav süreniz dolduğunda cevaplarınız otomatik olarak gönderilecektir.
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowInfo(false)} variant="contained">
            Anladım
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default BubbleSheetPanel
