/**
 * Optik Form (Bubble Sheet) Arayüzü
 * ÖSYM sınavlarında kullanılan optik form görünümü
 * 
 * REQ-1.1: TYT sınav formatı desteği
 * REQ-1.6: Otomatik kaydetme ile veri kaybı önleme
 */
import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Box,
  Paper,
  Typography,
  Tooltip,
  useTheme,
  alpha
} from '@mui/material'
import {
  CheckCircle,
  RadioButtonUnchecked,
  Circle
} from '@mui/icons-material'

interface BubbleSheetInterfaceProps {
  questionNumber: number
  options: string[]
  selectedAnswer: string | null
  onAnswerSelect: (answer: string) => void
  disabled?: boolean
  showFeedback?: boolean
  correctAnswer?: string
  size?: 'small' | 'medium' | 'large'
}

/**
 * Optik form bubble bileşeni
 */
export const BubbleSheetInterface: React.FC<BubbleSheetInterfaceProps> = ({
  questionNumber,
  options,
  selectedAnswer,
  onAnswerSelect,
  disabled = false,
  showFeedback = false,
  correctAnswer,
  size = 'medium'
}) => {
  const theme = useTheme()
  const [hoveredOption, setHoveredOption] = useState<string | null>(null)
  const [animatingOption, setAnimatingOption] = useState<string | null>(null)

  // Bubble boyutları
  const bubbleSizes = {
    small: { width: 32, height: 32, fontSize: '0.875rem' },
    medium: { width: 48, height: 48, fontSize: '1rem' },
    large: { width: 64, height: 64, fontSize: '1.25rem' }
  }

  const bubbleSize = bubbleSizes[size]

  /**
   * Cevap seçildiğinde animasyon tetikle
   */
  useEffect(() => {
    if (selectedAnswer) {
      setAnimatingOption(selectedAnswer)
      const timer = setTimeout(() => setAnimatingOption(null), 300)
      return () => clearTimeout(timer)
    }
  }, [selectedAnswer])

  /**
   * Bubble'ın durumuna göre stil belirle
   */
  const getBubbleStyle = (option: string) => {
    const isSelected = selectedAnswer === option
    const isHovered = hoveredOption === option
    const isAnimating = animatingOption === option
    const isCorrect = showFeedback && correctAnswer === option
    const isWrong = showFeedback && isSelected && correctAnswer !== option

    let backgroundColor = 'transparent'
    let borderColor = theme.palette.grey[400]
    let color = theme.palette.text.primary

    if (isSelected) {
      if (isWrong) {
        backgroundColor = theme.palette.error.main
        borderColor = theme.palette.error.dark
        color = 'white'
      } else if (isCorrect) {
        backgroundColor = theme.palette.success.main
        borderColor = theme.palette.success.dark
        color = 'white'
      } else {
        backgroundColor = theme.palette.primary.main
        borderColor = theme.palette.primary.dark
        color = 'white'
      }
    } else if (isCorrect && showFeedback) {
      backgroundColor = alpha(theme.palette.success.main, 0.2)
      borderColor = theme.palette.success.main
    } else if (isHovered && !disabled) {
      backgroundColor = alpha(theme.palette.primary.main, 0.1)
      borderColor = theme.palette.primary.main
    }

    return {
      backgroundColor,
      borderColor,
      color,
      transform: isAnimating ? 'scale(1.1)' : isHovered && !disabled ? 'scale(1.05)' : 'scale(1)',
      boxShadow: isSelected 
        ? `0 0 0 3px ${alpha(isWrong ? theme.palette.error.main : theme.palette.primary.main, 0.2)}`
        : 'none'
    }
  }

  /**
   * Bubble tıklama işleyicisi
   */
  const handleBubbleClick = (option: string) => {
    if (disabled) return

    // Aynı cevaba tekrar tıklanırsa işareti kaldır
    if (selectedAnswer === option) {
      onAnswerSelect('')
    } else {
      onAnswerSelect(option)
    }
  }

  /**
   * Klavye erişilebilirliği
   */
  const handleKeyPress = (event: React.KeyboardEvent, option: string) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      handleBubbleClick(option)
    }
  }

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        p: 2,
        borderRadius: 2,
        bgcolor: alpha(theme.palette.background.paper, 0.5),
        border: 1,
        borderColor: 'divider'
      }}
      role="radiogroup"
      aria-label={`Soru ${questionNumber} cevap seçenekleri`}
    >
      {/* Soru numarası */}
      <Box
        sx={{
          minWidth: 48,
          height: 48,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '50%',
          bgcolor: theme.palette.grey[200],
          fontWeight: 'bold',
          fontSize: '1rem'
        }}
      >
        {questionNumber}
      </Box>

      {/* Bubble seçenekleri */}
      <Box
        sx={{
          display: 'flex',
          gap: 1.5,
          flexWrap: 'wrap',
          flex: 1
        }}
      >
        {options.map((option) => {
          const isSelected = selectedAnswer === option
          const bubbleStyle = getBubbleStyle(option)

          return (
            <Tooltip
              key={option}
              title={disabled ? '' : isSelected ? 'İşareti kaldırmak için tekrar tıklayın' : `${option} şıkkını işaretle`}
              arrow
            >
              <motion.div
                whileHover={disabled ? {} : { scale: 1.05 }}
                whileTap={disabled ? {} : { scale: 0.95 }}
                animate={{
                  scale: animatingOption === option ? [1, 1.2, 1] : 1
                }}
                transition={{ duration: 0.3 }}
              >
                <Box
                  onClick={() => handleBubbleClick(option)}
                  onKeyPress={(e) => handleKeyPress(e, option)}
                  onMouseEnter={() => !disabled && setHoveredOption(option)}
                  onMouseLeave={() => setHoveredOption(null)}
                  tabIndex={disabled ? -1 : 0}
                  role="radio"
                  aria-checked={isSelected}
                  aria-label={`Şık ${option}`}
                  sx={{
                    width: bubbleSize.width,
                    height: bubbleSize.height,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: 3,
                    cursor: disabled ? 'default' : 'pointer',
                    fontSize: bubbleSize.fontSize,
                    fontWeight: isSelected ? 'bold' : 'normal',
                    transition: 'all 0.2s ease-in-out',
                    userSelect: 'none',
                    position: 'relative',
                    ...bubbleStyle,
                    '&:focus': {
                      outline: `2px solid ${theme.palette.primary.main}`,
                      outlineOffset: 2
                    },
                    '&:focus-visible': {
                      outline: `2px solid ${theme.palette.primary.main}`,
                      outlineOffset: 2
                    }
                  }}
                >
                  {/* Seçili işareti */}
                  <AnimatePresence>
                    {isSelected && (
                      <motion.div
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        style={{
                          position: 'absolute',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                      >
                        <Circle
                          sx={{
                            fontSize: bubbleSize.width * 0.6,
                            color: bubbleStyle.color
                          }}
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Şık harfi */}
                  <Typography
                    component="span"
                    sx={{
                      fontSize: bubbleSize.fontSize,
                      fontWeight: 'inherit',
                      color: 'inherit',
                      zIndex: 1
                    }}
                  >
                    {option}
                  </Typography>
                </Box>
              </motion.div>
            </Tooltip>
          )
        })}
      </Box>

      {/* Görsel geri bildirim */}
      {showFeedback && (
        <Box sx={{ ml: 'auto' }}>
          {selectedAnswer === correctAnswer ? (
            <CheckCircle color="success" sx={{ fontSize: 32 }} />
          ) : selectedAnswer ? (
            <Circle color="error" sx={{ fontSize: 32 }} />
          ) : (
            <RadioButtonUnchecked color="disabled" sx={{ fontSize: 32 }} />
          )}
        </Box>
      )}
    </Box>
  )
}

export default BubbleSheetInterface
