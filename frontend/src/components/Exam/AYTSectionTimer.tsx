/**
 * AYT Bölüm Bazlı Zamanlayıcı
 * Section-specific timers, time allocation suggestions, and pacing guidance
 * REQ-1.2, REQ-1.6
 */
import React, { useState, useEffect, useMemo } from 'react'
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  Chip,
  Tooltip,
  IconButton,
  Collapse,
  Alert,
  useTheme
} from '@mui/material'
import {
  Timer,
  ExpandMore,
  ExpandLess,
  Warning,
  Speed,
  TrendingUp,
  TrendingDown
} from '@mui/icons-material'

interface SectionTimeAllocation {
  sectionName: string
  displayName: string
  questionCount: number
  recommendedMinutes: number
  color: string
}

interface AYTSectionTimerProps {
  totalTimeSeconds: number
  remainingTimeSeconds: number
  currentSectionIndex: number
  sections: SectionTimeAllocation[]
  answeredPerSection: number[]
  onTimeWarning?: (warningType: 'section' | 'final' | 'critical') => void
}

/**
 * Varsayılan AYT bölüm süre tahsisleri - REQ-1.2
 * Toplam 210 dakika (3.5 saat)
 */
const DEFAULT_SECTION_ALLOCATIONS: SectionTimeAllocation[] = [
  { sectionName: 'matematik', displayName: 'Matematik', questionCount: 40, recommendedMinutes: 60, color: '#1976d2' },
  { sectionName: 'fizik', displayName: 'Fizik', questionCount: 14, recommendedMinutes: 21, color: '#388e3c' },
  { sectionName: 'kimya', displayName: 'Kimya', questionCount: 13, recommendedMinutes: 20, color: '#f57c00' },
  { sectionName: 'biyoloji', displayName: 'Biyoloji', questionCount: 13, recommendedMinutes: 20, color: '#7b1fa2' },
  { sectionName: 'edebiyat', displayName: 'Edebiyat', questionCount: 24, recommendedMinutes: 30, color: '#c62828' },
  { sectionName: 'tarih', displayName: 'Tarih', questionCount: 10, recommendedMinutes: 12, color: '#00796b' },
  { sectionName: 'cografya', displayName: 'Coğrafya', questionCount: 6, recommendedMinutes: 8, color: '#5d4037' },
  { sectionName: 'felsefe', displayName: 'Felsefe', questionCount: 12, recommendedMinutes: 15, color: '#455a64' },
  { sectionName: 'din', displayName: 'Din Kültürü', questionCount: 6, recommendedMinutes: 8, color: '#6a1b9a' },
  { sectionName: 'dil', displayName: 'Yabancı Dil', questionCount: 22, recommendedMinutes: 26, color: '#0277bd' }
]

export const AYTSectionTimer: React.FC<AYTSectionTimerProps> = ({
  totalTimeSeconds,
  remainingTimeSeconds,
  currentSectionIndex,
  sections = DEFAULT_SECTION_ALLOCATIONS,
  answeredPerSection,
  onTimeWarning
}) => {
  const theme = useTheme()
  const [expanded, setExpanded] = useState(false)
  const [lastWarning, setLastWarning] = useState<string | null>(null)

  // Geçen süre
  const elapsedSeconds = totalTimeSeconds - remainingTimeSeconds
  const elapsedMinutes = Math.floor(elapsedSeconds / 60)

  // Kalan süre formatı
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  // Bölüm bazlı süre analizi
  const sectionAnalysis = useMemo(() => {
    let cumulativeTime = 0
    
    return sections.map((section, index) => {
      const recommendedSeconds = section.recommendedMinutes * 60
      const startTime = cumulativeTime
      const endTime = cumulativeTime + recommendedSeconds
      cumulativeTime = endTime

      // Bu bölüm için harcanan süre tahmini
      const isCurrentSection = index === currentSectionIndex
      const isPastSection = index < currentSectionIndex
      
      let spentSeconds = 0
      if (isPastSection) {
        spentSeconds = recommendedSeconds // Geçmiş bölümler için tahmini süre
      } else if (isCurrentSection) {
        // Mevcut bölüm için gerçek harcanan süre
        const previousSectionsTime = sections
          .slice(0, index)
          .reduce((sum, s) => sum + s.recommendedMinutes * 60, 0)
        spentSeconds = Math.max(0, elapsedSeconds - previousSectionsTime)
      }

      // Hız analizi
      const answered = answeredPerSection[index] || 0
      const avgTimePerQuestion = answered > 0 ? spentSeconds / answered : 0
      const recommendedTimePerQuestion = recommendedSeconds / section.questionCount
      
      let pace: 'fast' | 'optimal' | 'slow' = 'optimal'
      if (avgTimePerQuestion > 0) {
        if (avgTimePerQuestion < recommendedTimePerQuestion * 0.8) {
          pace = 'fast'
        } else if (avgTimePerQuestion > recommendedTimePerQuestion * 1.2) {
          pace = 'slow'
        }
      }

      return {
        ...section,
        startTime,
        endTime,
        spentSeconds,
        answered,
        avgTimePerQuestion,
        recommendedTimePerQuestion,
        pace,
        progress: (answered / section.questionCount) * 100
      }
    })
  }, [sections, currentSectionIndex, elapsedSeconds, answeredPerSection])

  // Uyarı kontrolü
  useEffect(() => {
    const currentSection = sectionAnalysis[currentSectionIndex]
    if (!currentSection) return

    // Bölüm süresi uyarısı
    const sectionTimeUsage = currentSection.spentSeconds / (currentSection.recommendedMinutes * 60)
    if (sectionTimeUsage > 0.9 && lastWarning !== 'section') {
      setLastWarning('section')
      onTimeWarning?.('section')
    }

    // Genel süre uyarıları
    const timeUsage = elapsedSeconds / totalTimeSeconds
    if (timeUsage > 0.9 && lastWarning !== 'critical') {
      setLastWarning('critical')
      onTimeWarning?.('critical')
    } else if (timeUsage > 0.75 && lastWarning !== 'final') {
      setLastWarning('final')
      onTimeWarning?.('final')
    }
  }, [currentSectionIndex, elapsedSeconds, totalTimeSeconds, sectionAnalysis, lastWarning, onTimeWarning])

  // Renk belirleme
  const getTimeColor = (percentage: number): string => {
    if (percentage > 75) return theme.palette.error.main
    if (percentage > 50) return theme.palette.warning.main
    return theme.palette.success.main
  }

  const currentSection = sectionAnalysis[currentSectionIndex]
  const timePercentage = (elapsedSeconds / totalTimeSeconds) * 100

  return (
    <Paper elevation={2} sx={{ overflow: 'hidden' }}>
      {/* Ana Zamanlayıcı */}
      <Box sx={{ p: 2, bgcolor: 'grey.50' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Timer color="primary" />
            <Typography variant="h6" fontWeight="bold">
              {formatTime(remainingTimeSeconds)}
            </Typography>
          </Box>
          <IconButton size="small" onClick={() => setExpanded(!expanded)}>
            {expanded ? <ExpandLess /> : <ExpandMore />}
          </IconButton>
        </Box>
        
        <LinearProgress
          variant="determinate"
          value={timePercentage}
          sx={{
            height: 8,
            borderRadius: 4,
            bgcolor: 'grey.200',
            '& .MuiLinearProgress-bar': {
              bgcolor: getTimeColor(timePercentage)
            }
          }}
        />
        
        <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5, display: 'block' }}>
          Toplam: {Math.floor(totalTimeSeconds / 60)} dakika
        </Typography>
      </Box>

      {/* Mevcut Bölüm Bilgisi */}
      {currentSection && (
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="subtitle2" fontWeight="bold">
              {currentSection.displayName}
            </Typography>
            <Chip
              label={`${currentSection.answered}/${currentSection.questionCount}`}
              size="small"
              sx={{ bgcolor: currentSection.color, color: 'white' }}
            />
          </Box>

          <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
            <Tooltip title="Önerilen süre">
              <Chip
                icon={<Timer />}
                label={`${currentSection.recommendedMinutes} dk`}
                size="small"
                variant="outlined"
              />
            </Tooltip>
            
            {currentSection.pace === 'fast' && (
              <Tooltip title="Hızlı ilerliyorsunuz">
                <Chip
                  icon={<TrendingUp />}
                  label="Hızlı"
                  size="small"
                  color="success"
                  variant="outlined"
                />
              </Tooltip>
            )}
            
            {currentSection.pace === 'slow' && (
              <Tooltip title="Yavaş ilerliyorsunuz">
                <Chip
                  icon={<TrendingDown />}
                  label="Yavaş"
                  size="small"
                  color="warning"
                  variant="outlined"
                />
              </Tooltip>
            )}
            
            {currentSection.pace === 'optimal' && (
              <Tooltip title="Optimal hızdasınız">
                <Chip
                  icon={<Speed />}
                  label="Optimal"
                  size="small"
                  color="info"
                  variant="outlined"
                />
              </Tooltip>
            )}
          </Box>

          <LinearProgress
            variant="determinate"
            value={currentSection.progress}
            sx={{
              height: 6,
              borderRadius: 3,
              bgcolor: 'grey.200',
              '& .MuiLinearProgress-bar': {
                bgcolor: currentSection.color
              }
            }}
          />
        </Box>
      )}

      {/* Detaylı Bölüm Analizi */}
      <Collapse in={expanded}>
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', bgcolor: 'grey.50' }}>
          <Typography variant="subtitle2" gutterBottom fontWeight="bold">
            Bölüm Bazlı Süre Dağılımı
          </Typography>
          
          {sectionAnalysis.map((section, index) => {
            const isActive = index === currentSectionIndex
            const isPast = index < currentSectionIndex
            const timeUsage = (section.spentSeconds / (section.recommendedMinutes * 60)) * 100

            return (
              <Box
                key={section.sectionName}
                sx={{
                  mb: 1.5,
                  p: 1.5,
                  borderRadius: 1,
                  bgcolor: isActive ? 'white' : 'transparent',
                  border: 1,
                  borderColor: isActive ? section.color : 'transparent',
                  opacity: isPast ? 0.7 : 1
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                  <Typography variant="caption" fontWeight={isActive ? 'bold' : 'normal'}>
                    {section.displayName}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                    <Typography variant="caption" color="textSecondary">
                      {section.answered}/{section.questionCount}
                    </Typography>
                    {section.pace === 'slow' && <Warning fontSize="small" color="warning" />}
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min(100, timeUsage)}
                    sx={{
                      flex: 1,
                      height: 4,
                      borderRadius: 2,
                      bgcolor: 'grey.200',
                      '& .MuiLinearProgress-bar': {
                        bgcolor: section.color
                      }
                    }}
                  />
                  <Typography variant="caption" color="textSecondary" sx={{ minWidth: 40 }}>
                    {section.recommendedMinutes}dk
                  </Typography>
                </Box>

                {isActive && section.avgTimePerQuestion > 0 && (
                  <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5, display: 'block' }}>
                    Soru başına: {Math.round(section.avgTimePerQuestion)}s 
                    (Önerilen: {Math.round(section.recommendedTimePerQuestion)}s)
                  </Typography>
                )}
              </Box>
            )
          })}

          {/* Hız Önerileri */}
          {currentSection && currentSection.pace !== 'optimal' && (
            <Alert
              severity={currentSection.pace === 'slow' ? 'warning' : 'info'}
              sx={{ mt: 2 }}
              icon={currentSection.pace === 'slow' ? <Warning /> : <Speed />}
            >
              <Typography variant="caption">
                {currentSection.pace === 'slow' ? (
                  <>
                    <strong>Dikkat:</strong> Bu bölümde yavaş ilerliyorsunuz. 
                    Soru başına ortalama {Math.round(currentSection.recommendedTimePerQuestion)}s hedefleyin.
                  </>
                ) : (
                  <>
                    <strong>İyi gidiyorsunuz!</strong> Hızlı ilerliyorsunuz ama cevaplarınızı kontrol etmeyi unutmayın.
                  </>
                )}
              </Typography>
            </Alert>
          )}
        </Box>
      </Collapse>
    </Paper>
  )
}

export default AYTSectionTimer
