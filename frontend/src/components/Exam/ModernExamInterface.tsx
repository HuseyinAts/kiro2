/**
 * Modern Exam Interface Component
 * Enhanced exam interface with accessibility and mobile optimization
 */

import React, { useState, useCallback, useMemo, memo } from 'react'
import { 
  Box, 
  Typography, 
  LinearProgress,
  Paper,
  Chip,
  IconButton,
  useTheme,
  Fade,
  Grid,
  Divider
} from '@mui/material'
import { 
  Timer as TimerIcon,
  NavigateNext as NextIcon,
  NavigateBefore as PrevIcon,
  Flag as FlagIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material'

import { ModernCard } from '../ui/modern-card'
import { ModernButton } from '../ui/modern-button'
import { useResponsive } from '../../utils/responsive'

interface Question {
  id: number
  text: string
  options: string[]
  selectedAnswer?: number
  flagged?: boolean
}

interface ExamData {
  id: string
  title: string
  questions: Question[]
  timeLimit: number // minutes
  timeRemaining: number // seconds
}

interface ModernExamInterfaceProps {
  examData: ExamData
  onAnswerSelect: (questionId: number, answerIndex: number) => void
  onQuestionFlag: (questionId: number) => void
  onSubmit: () => void
  onNext: () => void
  onPrevious: () => void
  currentQuestionIndex: number
}

// Question navigation component
const QuestionNavigation = memo(({ 
  questions, 
  currentIndex, 
  onQuestionClick 
}: {
  questions: Question[]
  currentIndex: number
  onQuestionClick: (index: number) => void
}) => {
  const { isMobile } = useResponsive()
  
  return (
    <ModernCard title="Soru Haritası" size="small">
      <Grid container spacing={1}>
        {questions.map((question, index) => (
          <Grid item xs={isMobile ? 3 : 2} key={question.id}>
            <ModernButton
              size="small"
              variant={
                index === currentIndex ? 'contained' :
                question.selectedAnswer !== undefined ? 'outlined' : 'text'
              }
              color={
                index === currentIndex ? 'primary' :
                question.selectedAnswer !== undefined ? 'success' : 'inherit'
              }
              onClick={() => onQuestionClick(index)}
              sx={{
                minWidth: 40,
                height: 40,
                position: 'relative'
              }}
              touchOptimized
            >
              {index + 1}
              {question.flagged && (
                <FlagIcon 
                  sx={{ 
                    position: 'absolute',
                    top: -4,
                    right: -4,
                    fontSize: 12,
                    color: 'warning.main'
                  }} 
                />
              )}
            </ModernButton>
          </Grid>
        ))}
      </Grid>
    </ModernCard>
  )
})

QuestionNavigation.displayName = 'QuestionNavigation'

// Timer component
const ExamTimer = memo(({ timeRemaining }: { timeRemaining: number }) => {
  const theme = useTheme()
  
  const formatTime = useCallback((seconds: number) => {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }, [])
  
  const isLowTime = timeRemaining < 300 // 5 minutes
  const isCriticalTime = timeRemaining < 60 // 1 minute
  
  return (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        backgroundColor: isCriticalTime ? 'error.main' : isLowTime ? 'warning.main' : 'primary.main',
        color: 'white',
        borderRadius: 2
      }}
    >
      <TimerIcon />
      <Box>
        <Typography variant="body2" sx={{ opacity: 0.9 }}>
          Kalan Süre
        </Typography>
        <Typography variant="h6" sx={{ fontWeight: 700, fontFamily: 'monospace' }}>
          {formatTime(timeRemaining)}
        </Typography>
      </Box>
    </Paper>
  )
})

ExamTimer.displayName = 'ExamTimer'

// Question display component
const QuestionDisplay = memo(({ 
  question, 
  onAnswerSelect, 
  onFlag 
}: {
  question: Question
  onAnswerSelect: (answerIndex: number) => void
  onFlag: () => void
}) => {
  const { isMobile } = useResponsive()
  
  return (
    <ModernCard size="large">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
        <Typography variant="h6" component="h2" sx={{ flex: 1, fontWeight: 600 }}>
          {question.text}
        </Typography>
        
        <IconButton
          onClick={onFlag}
          color={question.flagged ? 'warning' : 'default'}
          aria-label={question.flagged ? 'bayrağı kaldır' : 'bayrak ekle'}
          sx={{ ml: 2 }}
        >
          <FlagIcon />
        </IconButton>
      </Box>
      
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {question.options.map((option, index) => {
          const isSelected = question.selectedAnswer === index
          const optionLetter = String.fromCharCode(65 + index) // A, B, C, D
          
          return (
            <Paper
              key={index}
              elevation={0}
              onClick={() => onAnswerSelect(index)}
              sx={{
                p: 2,
                border: 2,
                borderColor: isSelected ? 'primary.main' : 'divider',
                backgroundColor: isSelected ? 'primary.50' : 'background.paper',
                cursor: 'pointer',
                transition: 'all 0.2s ease-in-out',
                borderRadius: 2,
                minHeight: isMobile ? 56 : 48, // Touch-friendly height
                display: 'flex',
                alignItems: 'center',
                '&:hover': {
                  borderColor: 'primary.main',
                  backgroundColor: isSelected ? 'primary.100' : 'primary.50'
                }
              }}
              role="button"
              tabIndex={0}
              aria-pressed={isSelected}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onAnswerSelect(index)
                }
              }}
            >
              <Box
                sx={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  backgroundColor: isSelected ? 'primary.main' : 'grey.300',
                  color: isSelected ? 'white' : 'grey.700',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 600,
                  mr: 2,
                  flexShrink: 0
                }}
              >
                {optionLetter}
              </Box>
              
              <Typography 
                variant="body1" 
                sx={{ 
                  flex: 1,
                  color: isSelected ? 'primary.main' : 'text.primary'
                }}
              >
                {option}
              </Typography>
              
              {isSelected && (
                <CheckIcon 
                  sx={{ 
                    color: 'primary.main',
                    ml: 1
                  }} 
                />
              )}
            </Paper>
          )
        })}
      </Box>
    </ModernCard>
  )
})

QuestionDisplay.displayName = 'QuestionDisplay'

export const ModernExamInterface: React.FC<ModernExamInterfaceProps> = memo(({
  examData,
  onAnswerSelect,
  onQuestionFlag,
  onSubmit,
  onNext,
  onPrevious,
  currentQuestionIndex
}) => {
  const { isMobile } = useResponsive()
  const theme = useTheme()
  
  const currentQuestion = examData.questions[currentQuestionIndex]
  const totalQuestions = examData.questions.length
  const progress = ((currentQuestionIndex + 1) / totalQuestions) * 100
  const answeredCount = examData.questions.filter(q => q.selectedAnswer !== undefined).length
  
  const handleAnswerSelect = useCallback((answerIndex: number) => {
    onAnswerSelect(currentQuestion.id, answerIndex)
  }, [currentQuestion.id, onAnswerSelect])
  
  const handleQuestionFlag = useCallback(() => {
    onQuestionFlag(currentQuestion.id)
  }, [currentQuestion.id, onQuestionFlag])
  
  const handleQuestionClick = useCallback((index: number) => {
    // Navigation logic would be implemented by parent
    console.log('Navigate to question:', index)
  }, [])
  
  const isFirstQuestion = currentQuestionIndex === 0
  const isLastQuestion = currentQuestionIndex === totalQuestions - 1
  
  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: 'background.default' }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          backgroundColor: 'background.paper',
          borderBottom: 1,
          borderColor: 'divider',
          position: 'sticky',
          top: 0,
          zIndex: 1
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            {examData.title}
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <Chip 
              label={`${answeredCount}/${totalQuestions} Cevaplandı`} 
              color="primary" 
              size="small"
            />
            <ExamTimer timeRemaining={examData.timeRemaining} />
          </Box>
        </Box>
        
        <LinearProgress 
          variant="determinate" 
          value={progress} 
          sx={{ 
            height: 6, 
            borderRadius: 3,
            backgroundColor: 'grey.200',
            '& .MuiLinearProgress-bar': {
              borderRadius: 3
            }
          }} 
        />
      </Paper>
      
      {/* Main Content */}
      <Box sx={{ p: 2 }}>
        <Grid container spacing={3}>
          {/* Question Area */}
          <Grid item xs={12} md={8}>
            <Fade in key={currentQuestionIndex} timeout={300}>
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" color="text.secondary">
                    Soru {currentQuestionIndex + 1} / {totalQuestions}
                  </Typography>
                </Box>
                
                <QuestionDisplay
                  question={currentQuestion}
                  onAnswerSelect={handleAnswerSelect}
                  onFlag={handleQuestionFlag}
                />
                
                {/* Navigation Buttons */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
                  <ModernButton
                    variant="outlined"
                    startIcon={<PrevIcon />}
                    onClick={onPrevious}
                    disabled={isFirstQuestion}
                    size="large"
                  >
                    Önceki
                  </ModernButton>
                  
                  {isLastQuestion ? (
                    <ModernButton
                      variant="contained"
                      color="success"
                      onClick={onSubmit}
                      size="large"
                    >
                      Sınavı Bitir
                    </ModernButton>
                  ) : (
                    <ModernButton
                      variant="contained"
                      endIcon={<NextIcon />}
                      onClick={onNext}
                      size="large"
                    >
                      Sonraki
                    </ModernButton>
                  )}
                </Box>
              </Box>
            </Fade>
          </Grid>
          
          {/* Sidebar */}
          <Grid item xs={12} md={4}>
            <QuestionNavigation
              questions={examData.questions}
              currentIndex={currentQuestionIndex}
              onQuestionClick={handleQuestionClick}
            />
          </Grid>
        </Grid>
      </Box>
    </Box>
  )
})

ModernExamInterface.displayName = 'ModernExamInterface'

export default ModernExamInterface