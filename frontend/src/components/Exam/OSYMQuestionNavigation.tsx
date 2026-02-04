/**
 * ÖSYM Soru Navigasyon Bileşeni
 * Yeni API ile uyumlu soru navigasyonu
 */
import React, { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Tooltip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Chip,
  Badge,
  useTheme,
  useMediaQuery
} from '@mui/material'
import {
  NavigateNext,
  NavigateBefore,
  Bookmark,
  BookmarkBorder,
  CheckCircle,
  RadioButtonUnchecked,
  GridView
} from '@mui/icons-material'
import { motion } from 'framer-motion'
import { ExamSessionResponse } from '../../services/examService'

interface OSYMQuestionNavigationProps {
  session: ExamSessionResponse
  answers: Record<string, string>
  flaggedQuestions: Set<string>
  onQuestionSelect: (questionIndex: number) => void
  onFlagToggle: (questionId: string) => void
  onNext: () => void
  onPrevious: () => void
  disabled?: boolean
}

export const OSYMQuestionNavigation: React.FC<OSYMQuestionNavigationProps> = ({
  session,
  answers,
  flaggedQuestions,
  onQuestionSelect,
  onFlagToggle,
  onNext,
  onPrevious,
  disabled = false
}) => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  
  const [showAllQuestions, setShowAllQuestions] = useState(false)

  const isFirstQuestion = session.current_question_index === 0
  const isLastQuestion = session.current_question_index === session.total_questions - 1

  /**
   * Soru durumunu belirle
   */
  const getQuestionStatus = (questionIndex: number) => {
    // Bu implementasyonda question ID'lerini index'e göre oluşturuyoruz
    // Gerçek implementasyonda backend'den gelen question ID'leri kullanılmalı
    const questionId = `question_${questionIndex}`
    const isAnswered = !!answers[questionId]
    const isFlagged = flaggedQuestions.has(questionId)
    const isCurrent = questionIndex === session.current_question_index

    return {
      isAnswered,
      isFlagged,
      isCurrent,
      questionId
    }
  }

  /**
   * Soru durumuna göre renk getir
   */
  const getQuestionColor = (status: ReturnType<typeof getQuestionStatus>) => {
    if (status.isCurrent) return theme.palette.primary.main
    if (status.isAnswered) return theme.palette.success.main
    return theme.palette.grey[300]
  }

  /**
   * Soru durumuna göre metin rengi getir
   */
  const getQuestionTextColor = (status: ReturnType<typeof getQuestionStatus>) => {
    if (status.isCurrent || status.isAnswered) return 'white'
    return theme.palette.text.primary
  }

  /**
   * İstatistikleri hesapla
   */
  const stats = {
    answered: Object.keys(answers).length,
    flagged: flaggedQuestions.size,
    remaining: session.total_questions - Object.keys(answers).length
  }

  /**
   * Hızlı navigasyon (mobil için)
   */
  const QuickNavigation = () => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
      <IconButton
        onClick={onPrevious}
        disabled={disabled || isFirstQuestion}
        size="small"
      >
        <NavigateBefore />
      </IconButton>

      <Box sx={{ 
        display: 'flex', 
        gap: 0.5, 
        overflow: 'auto',
        maxWidth: '200px',
        '&::-webkit-scrollbar': { height: 4 },
        '&::-webkit-scrollbar-thumb': { backgroundColor: theme.palette.grey[400], borderRadius: 2 }
      }}>
        {Array.from({ length: Math.min(session.total_questions, 10) }, (_, index) => {
          const actualIndex = Math.max(0, session.current_question_index - 5) + index
          if (actualIndex >= session.total_questions) return null
          
          const status = getQuestionStatus(actualIndex)
          
          return (
            <Tooltip key={actualIndex} title={`Soru ${actualIndex + 1}`}>
              <Box
                onClick={() => !disabled && onQuestionSelect(actualIndex)}
                sx={{
                  width: 28,
                  height: 28,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.75rem',
                  cursor: disabled ? 'default' : 'pointer',
                  bgcolor: getQuestionColor(status),
                  color: getQuestionTextColor(status),
                  border: status.isFlagged ? 2 : 0,
                  borderColor: theme.palette.warning.main,
                  transform: status.isCurrent ? 'scale(1.1)' : 'scale(1)',
                  transition: 'all 0.2s',
                  '&:hover': disabled ? {} : {
                    transform: 'scale(1.1)'
                  }
                }}
              >
                {actualIndex + 1}
              </Box>
            </Tooltip>
          )
        })}
      </Box>

      <IconButton
        onClick={onNext}
        disabled={disabled || isLastQuestion}
        size="small"
      >
        <NavigateNext />
      </IconButton>

      <Button
        variant="outlined"
        size="small"
        onClick={() => setShowAllQuestions(true)}
        startIcon={<GridView />}
      >
        Tümü
      </Button>
    </Box>
  )

  /**
   * Masaüstü navigasyon
   */
  const DesktopNavigation = () => (
    <Box>
      {/* İstatistikler */}
      <Box sx={{ display: 'flex', gap: 1, mb: 2, justifyContent: 'center' }}>
        <Chip
          label={`${stats.answered} Cevaplanan`}
          color="success"
          size="small"
          icon={<CheckCircle />}
        />
        <Chip
          label={`${stats.flagged} İşaretli`}
          color="warning"
          size="small"
          icon={<Bookmark />}
        />
        <Chip
          label={`${stats.remaining} Kalan`}
          color="default"
          size="small"
          icon={<RadioButtonUnchecked />}
        />
      </Box>

      {/* Soru grid'i */}
      <Box sx={{ 
        display: 'flex', 
        flexWrap: 'wrap', 
        gap: 0.5, 
        justifyContent: 'center',
        maxHeight: '120px',
        overflow: 'hidden'
      }}>
        {Array.from({ length: session.total_questions }, (_, index) => {
          const status = getQuestionStatus(index)
          
          return (
            <Tooltip key={index} title={`Soru ${index + 1}${status.isAnswered ? ' - Cevaplandı' : ''}${status.isFlagged ? ' - İşaretli' : ''}`}>
              <Badge
                badgeContent={status.isFlagged ? <Bookmark sx={{ fontSize: 12 }} /> : null}
                color="warning"
                overlap="circular"
                anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
              >
                <motion.div
                  whileHover={disabled ? {} : { scale: 1.1 }}
                  whileTap={disabled ? {} : { scale: 0.95 }}
                >
                  <Box
                    onClick={() => !disabled && onQuestionSelect(index)}
                    sx={{
                      width: 36,
                      height: 36,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.875rem',
                      fontWeight: status.isCurrent ? 'bold' : 'normal',
                      cursor: disabled ? 'default' : 'pointer',
                      bgcolor: getQuestionColor(status),
                      color: getQuestionTextColor(status),
                      border: status.isFlagged ? 2 : 0,
                      borderColor: theme.palette.warning.main,
                      transform: status.isCurrent ? 'scale(1.1)' : 'scale(1)',
                      transition: 'all 0.2s',
                      boxShadow: status.isCurrent ? theme.shadows[4] : theme.shadows[1],
                      '&:hover': disabled ? {} : {
                        boxShadow: theme.shadows[4]
                      }
                    }}
                  >
                    {index + 1}
                  </Box>
                </motion.div>
              </Badge>
            </Tooltip>
          )
        })}
      </Box>

      {/* Navigasyon butonları */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
        <Button
          variant="outlined"
          startIcon={<NavigateBefore />}
          onClick={onPrevious}
          disabled={disabled || isFirstQuestion}
        >
          Önceki
        </Button>

        <Typography variant="body2" color="textSecondary">
          {session.current_question_index + 1} / {session.total_questions}
        </Typography>

        <Button
          variant="contained"
          endIcon={<NavigateNext />}
          onClick={onNext}
          disabled={disabled || isLastQuestion}
        >
          Sonraki
        </Button>
      </Box>
    </Box>
  )

  return (
    <>
      <Paper elevation={2} sx={{ p: 2 }}>
        {isMobile ? <QuickNavigation /> : <DesktopNavigation />}
      </Paper>

      {/* Tüm Sorular Dialog */}
      <Dialog
        open={showAllQuestions}
        onClose={() => setShowAllQuestions(false)}
        maxWidth="md"
        fullWidth
        fullScreen={isMobile}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              Soru Navigasyonu
            </Typography>
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {/* İstatistikler */}
          <Box sx={{ display: 'flex', gap: 2, mb: 3, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Chip
              label={`Toplam: ${session.total_questions}`}
              color="primary"
              variant="outlined"
            />
            <Chip
              label={`Cevaplanan: ${stats.answered}`}
              color="success"
              icon={<CheckCircle />}
            />
            <Chip
              label={`İşaretli: ${stats.flagged}`}
              color="warning"
              icon={<Bookmark />}
            />
            <Chip
              label={`Kalan: ${stats.remaining}`}
              color="default"
              icon={<RadioButtonUnchecked />}
            />
          </Box>

          {/* Soru grid'i */}
          <Grid container spacing={1}>
            {Array.from({ length: session.total_questions }, (_, index) => {
              const status = getQuestionStatus(index)
              
              return (
                <Grid item xs={2} sm={1.5} md={1} key={index}>
                  <Badge
                    badgeContent={status.isFlagged ? <Bookmark sx={{ fontSize: 10 }} /> : null}
                    color="warning"
                    overlap="circular"
                  >
                    <Box
                      onClick={() => {
                        onQuestionSelect(index)
                        setShowAllQuestions(false)
                      }}
                      sx={{
                        width: '100%',
                        aspectRatio: '1',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.875rem',
                        fontWeight: status.isCurrent ? 'bold' : 'normal',
                        cursor: 'pointer',
                        bgcolor: getQuestionColor(status),
                        color: getQuestionTextColor(status),
                        border: status.isFlagged ? 2 : 0,
                        borderColor: theme.palette.warning.main,
                        transform: status.isCurrent ? 'scale(1.1)' : 'scale(1)',
                        transition: 'all 0.2s',
                        '&:hover': {
                          transform: 'scale(1.1)',
                          boxShadow: theme.shadows[4]
                        }
                      }}
                    >
                      {index + 1}
                    </Box>
                  </Badge>
                </Grid>
              )
            })}
          </Grid>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setShowAllQuestions(false)}>
            Kapat
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

export default OSYMQuestionNavigation