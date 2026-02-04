/**
 * Şüpheli Sorular Paneli - REQ-1.6
 * İşaretlenmiş soruların listesi ve hızlı navigasyon
 */
import React, { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  IconButton,
  Chip,
  Collapse,
  Badge,
  Divider,
  Tooltip,
  useTheme
} from '@mui/material'
import {
  Bookmark,
  BookmarkBorder,
  ExpandMore,
  ExpandLess,
  Flag,
  NavigateNext,
  CheckCircle,
  RadioButtonUnchecked,
  Warning
} from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'

interface FlaggedQuestionsPanelProps {
  flaggedQuestions: Set<string>
  answers: Record<string, string>
  currentQuestionIndex: number
  totalQuestions: number
  onQuestionSelect: (questionIndex: number) => void
  onFlagToggle: (questionId: string) => void
  disabled?: boolean
}

export const FlaggedQuestionsPanel: React.FC<FlaggedQuestionsPanelProps> = ({
  flaggedQuestions,
  answers,
  currentQuestionIndex,
  totalQuestions,
  onQuestionSelect,
  onFlagToggle,
  disabled = false
}) => {
  const theme = useTheme()
  const [isExpanded, setIsExpanded] = useState(true)

  /**
   * İşaretli soruların listesini oluştur
   */
  const flaggedQuestionsList = Array.from(flaggedQuestions).map(questionId => {
    // Question ID'den index'i çıkar (format: question_0, question_1, etc.)
    const questionIndex = parseInt(questionId.split('_')[1])
    const isAnswered = !!answers[questionId]
    const isCurrent = questionIndex === currentQuestionIndex

    return {
      questionId,
      questionIndex,
      isAnswered,
      isCurrent
    }
  }).sort((a, b) => a.questionIndex - b.questionIndex)

  /**
   * İstatistikleri hesapla
   */
  const stats = {
    total: flaggedQuestions.size,
    answered: flaggedQuestionsList.filter(q => q.isAnswered).length,
    unanswered: flaggedQuestionsList.filter(q => !q.isAnswered).length
  }

  /**
   * Boş durum
   */
  if (flaggedQuestions.size === 0) {
    return (
      <Paper elevation={2} sx={{ p: 3, textAlign: 'center' }}>
        <BookmarkBorder sx={{ fontSize: 48, color: 'grey.400', mb: 1 }} />
        <Typography variant="body2" color="textSecondary">
          Henüz işaretlenmiş soru yok
        </Typography>
        <Typography variant="caption" color="textSecondary">
          Şüpheli sorularınızı işaretleyerek daha sonra gözden geçirebilirsiniz
        </Typography>
      </Paper>
    )
  }

  return (
    <Paper elevation={2} sx={{ overflow: 'hidden' }}>
      {/* Header */}
      <Box
        sx={{
          p: 2,
          bgcolor: 'warning.50',
          borderBottom: 1,
          borderColor: 'divider',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer'
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Flag color="warning" />
          <Typography variant="h6" sx={{ fontSize: '1rem' }}>
            Şüpheli Sorular
          </Typography>
          <Badge badgeContent={stats.total} color="warning" max={99}>
            <Box />
          </Badge>
        </Box>
        
        <IconButton size="small">
          {isExpanded ? <ExpandLess /> : <ExpandMore />}
        </IconButton>
      </Box>

      {/* İstatistikler */}
      <Collapse in={isExpanded}>
        <Box sx={{ p: 2, bgcolor: 'grey.50', borderBottom: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip
              label={`Toplam: ${stats.total}`}
              size="small"
              color="warning"
              variant="outlined"
            />
            <Chip
              label={`Cevaplanan: ${stats.answered}`}
              size="small"
              color="success"
              icon={<CheckCircle />}
            />
            <Chip
              label={`Cevaplanmayan: ${stats.unanswered}`}
              size="small"
              color="default"
              icon={<RadioButtonUnchecked />}
            />
          </Box>
        </Box>

        {/* Soru Listesi */}
        <List sx={{ maxHeight: 400, overflow: 'auto', p: 0 }}>
          <AnimatePresence>
            {flaggedQuestionsList.map((question, index) => (
              <motion.div
                key={question.questionId}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.2, delay: index * 0.05 }}
              >
                <ListItem
                  disablePadding
                  secondaryAction={
                    <Tooltip title="İşareti kaldır">
                      <IconButton
                        edge="end"
                        onClick={(e) => {
                          e.stopPropagation()
                          onFlagToggle(question.questionId)
                        }}
                        disabled={disabled}
                        size="small"
                      >
                        <Bookmark color="warning" />
                      </IconButton>
                    </Tooltip>
                  }
                  sx={{
                    borderBottom: index < flaggedQuestionsList.length - 1 ? 1 : 0,
                    borderColor: 'divider'
                  }}
                >
                  <ListItemButton
                    onClick={() => onQuestionSelect(question.questionIndex)}
                    disabled={disabled}
                    selected={question.isCurrent}
                    sx={{
                      py: 1.5,
                      '&.Mui-selected': {
                        bgcolor: 'primary.50',
                        borderLeft: 3,
                        borderColor: 'primary.main'
                      }
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 40 }}>
                      <Box
                        sx={{
                          width: 32,
                          height: 32,
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '0.875rem',
                          fontWeight: question.isCurrent ? 'bold' : 'normal',
                          bgcolor: question.isAnswered 
                            ? 'success.main' 
                            : question.isCurrent 
                            ? 'primary.main' 
                            : 'grey.300',
                          color: question.isAnswered || question.isCurrent ? 'white' : 'text.primary',
                          border: 2,
                          borderColor: 'warning.main'
                        }}
                      >
                        {question.questionIndex + 1}
                      </Box>
                    </ListItemIcon>
                    
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" fontWeight={question.isCurrent ? 'bold' : 'normal'}>
                            Soru {question.questionIndex + 1}
                          </Typography>
                          {question.isCurrent && (
                            <Chip label="Şu an" size="small" color="primary" />
                          )}
                        </Box>
                      }
                      secondary={
                        <Typography variant="caption" color="textSecondary">
                          {question.isAnswered ? 'Cevaplandı' : 'Cevaplanmadı'}
                        </Typography>
                      }
                    />
                    
                    <NavigateNext sx={{ color: 'grey.400' }} />
                  </ListItemButton>
                </ListItem>
              </motion.div>
            ))}
          </AnimatePresence>
        </List>

        {/* Footer - Hızlı Eylemler */}
        <Box sx={{ p: 2, bgcolor: 'grey.50', borderTop: 1, borderColor: 'divider' }}>
          <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 1 }}>
            💡 İpucu: Şüpheli sorularınızı işaretleyerek sınav sonunda tekrar gözden geçirebilirsiniz
          </Typography>
          
          {stats.unanswered > 0 && (
            <Chip
              label={`${stats.unanswered} cevaplanmayan şüpheli soru var`}
              size="small"
              color="warning"
              icon={<Warning />}
              sx={{ mt: 0.5 }}
            />
          )}
        </Box>
      </Collapse>
    </Paper>
  )
}

export default FlaggedQuestionsPanel
