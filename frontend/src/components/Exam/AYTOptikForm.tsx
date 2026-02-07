/**
 * AYT Optik Form Arayüzü
 * Multi-section bubble sheet with section navigation and progress indicators
 * REQ-1.2, REQ-1.6
 */
import {
  CheckCircle,
  RadioButtonUnchecked,
  Bookmark,
  NavigateNext,
  NavigateBefore,
} from '@mui/icons-material';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Chip,
  Button,
  Tabs,
  Tab,
  LinearProgress,
  Tooltip,
  IconButton,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import * as React from 'react';
import {  useState, useMemo  } from 'react';

interface AYTSection {
  name: string
  displayName: string
  startIndex: number
  endIndex: number
  questionCount: number
  color: string
}

interface AYTOptikFormProps {
  totalQuestions: number
  currentQuestionIndex: number
  answers: Record<string, string>
  flaggedQuestions: Set<string>
  questionIds: string[]
  sections?: AYTSection[]
  onQuestionSelect: (index: number) => void
  onFlagQuestion: (questionId: string) => void
  compact?: boolean
}

/**
 * Varsayılan AYT bölümleri - REQ-1.2
 */
const DEFAULT_AYT_SECTIONS: AYTSection[] = [
  {
    name: 'matematik',
    displayName: 'Matematik',
    startIndex: 0,
    endIndex: 39,
    questionCount: 40,
    color: '#1976d2',
  },
  {
    name: 'fizik',
    displayName: 'Fizik',
    startIndex: 40,
    endIndex: 53,
    questionCount: 14,
    color: '#388e3c',
  },
  {
    name: 'kimya',
    displayName: 'Kimya',
    startIndex: 54,
    endIndex: 66,
    questionCount: 13,
    color: '#f57c00',
  },
  {
    name: 'biyoloji',
    displayName: 'Biyoloji',
    startIndex: 67,
    endIndex: 79,
    questionCount: 13,
    color: '#7b1fa2',
  },
  {
    name: 'edebiyat',
    displayName: 'Edebiyat',
    startIndex: 80,
    endIndex: 103,
    questionCount: 24,
    color: '#c62828',
  },
  {
    name: 'tarih',
    displayName: 'Tarih',
    startIndex: 104,
    endIndex: 113,
    questionCount: 10,
    color: '#00796b',
  },
  {
    name: 'cografya',
    displayName: 'Coğrafya',
    startIndex: 114,
    endIndex: 119,
    questionCount: 6,
    color: '#5d4037',
  },
  {
    name: 'felsefe',
    displayName: 'Felsefe',
    startIndex: 120,
    endIndex: 131,
    questionCount: 12,
    color: '#455a64',
  },
  {
    name: 'din',
    displayName: 'Din Kültürü',
    startIndex: 132,
    endIndex: 137,
    questionCount: 6,
    color: '#6a1b9a',
  },
  {
    name: 'dil',
    displayName: 'Yabancı Dil',
    startIndex: 138,
    endIndex: 159,
    questionCount: 22,
    color: '#0277bd',
  },
];

export const AYTOptikForm: React.FC<AYTOptikFormProps> = ({
  totalQuestions,
  currentQuestionIndex,
  answers,
  flaggedQuestions,
  questionIds,
  sections = DEFAULT_AYT_SECTIONS,
  onQuestionSelect,
  onFlagQuestion,
  compact = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Aktif bölümü belirle
  const [activeTab, setActiveTab] = useState(() => {
    const section = sections.find(
      s => currentQuestionIndex >= s.startIndex && currentQuestionIndex <= s.endIndex,
    );
    return section ? sections.indexOf(section) : 0;
  });

  // Bölüm istatistikleri
  const sectionStats = useMemo(() => {
    return sections.map(section => {
      let answered = 0;
      let flagged = 0;

      for (let i = section.startIndex; i <= section.endIndex; i++) {
        const questionId = questionIds[i];
        if (questionId) {
          if (answers[questionId]) {answered++;}
          if (flaggedQuestions.has(questionId)) {flagged++;}
        }
      }

      return {
        answered,
        flagged,
        total: section.questionCount,
        percentage: (answered / section.questionCount) * 100,
      };
    });
  }, [sections, answers, flaggedQuestions, questionIds]);

  // Soru durumunu belirle
  const getQuestionStatus = (index: number): 'current' | 'answered' | 'flagged' | 'empty' => {
    if (index === currentQuestionIndex) {return 'current';}

    const questionId = questionIds[index];
    if (!questionId) {return 'empty';}

    if (flaggedQuestions.has(questionId)) {return 'flagged';}
    if (answers[questionId]) {return 'answered';}

    return 'empty';
  };

  // Soru rengi
  const getQuestionColor = (status: string) => {
    switch (status) {
      case 'current':
        return theme.palette.primary.main;
      case 'answered':
        return theme.palette.success.main;
      case 'flagged':
        return theme.palette.warning.main;
      default:
        return theme.palette.grey[300];
    }
  };

  // Soru ikonu
  const getQuestionIcon = (status: string) => {
    switch (status) {
      case 'answered':
        return <CheckCircle fontSize="small" />;
      case 'flagged':
        return <Bookmark fontSize="small" />;
      default:
        return <RadioButtonUnchecked fontSize="small" />;
    }
  };

  // Bölüm değiştir
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
    // İlk soruya git
    const section = sections[newValue];
    if (section) {
      onQuestionSelect(section.startIndex);
    }
  };

  // Kompakt mod
  if (compact) {
    return (
      <Paper elevation={2} sx={{ p: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Soru Haritası
        </Typography>
        <Grid container spacing={0.5}>
          {Array.from({ length: totalQuestions }, (_, i) => {
            const status = getQuestionStatus(i);
            return (
              <Grid item key={i}>
                <Tooltip title={`Soru ${i + 1}`}>
                  <IconButton
                    size="small"
                    onClick={() => onQuestionSelect(i)}
                    sx={{
                      width: 32,
                      height: 32,
                      bgcolor: getQuestionColor(status),
                      color: 'white',
                      '&:hover': {
                        bgcolor: getQuestionColor(status),
                        opacity: 0.8,
                      },
                    }}
                  >
                    <Typography variant="caption">{i + 1}</Typography>
                  </IconButton>
                </Tooltip>
              </Grid>
            );
          })}
        </Grid>
      </Paper>
    );
  }

  // Tam mod
  const activeSection = sections[activeTab];

  return (
    <Paper elevation={3} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Bölüm Sekmeleri */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant={isMobile ? 'scrollable' : 'fullWidth'}
          scrollButtons={isMobile ? 'auto' : false}
          sx={{
            '& .MuiTab-root': {
              minHeight: 48,
              fontSize: { xs: '0.75rem', sm: '0.875rem' },
            },
          }}
        >
          {sections.map((section, index) => (
            <Tab
              key={section.name}
              label={
                <Box>
                  <Typography variant="caption" display="block">
                    {section.displayName}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {sectionStats[index].answered}/{section.questionCount}
                  </Typography>
                </Box>
              }
              sx={{
                borderBottom: 3,
                borderColor: activeTab === index ? section.color : 'transparent',
              }}
            />
          ))}
        </Tabs>
      </Box>

      {/* Bölüm İstatistikleri */}
      {activeSection && (
        <Box sx={{ p: 2, bgcolor: 'grey.50' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="subtitle1" fontWeight="bold">
              {activeSection.displayName}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip
                label={`${sectionStats[activeTab].answered}/${activeSection.questionCount}`}
                size="small"
                color="primary"
                variant="outlined"
              />
              {sectionStats[activeTab].flagged > 0 && (
                <Chip
                  icon={<Bookmark />}
                  label={sectionStats[activeTab].flagged}
                  size="small"
                  color="warning"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
          <LinearProgress
            variant="determinate"
            value={sectionStats[activeTab].percentage}
            sx={{
              height: 8,
              borderRadius: 4,
              bgcolor: 'grey.200',
              '& .MuiLinearProgress-bar': {
                bgcolor: activeSection.color,
              },
            }}
          />
        </Box>
      )}

      {/* Soru Haritası */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        <Grid container spacing={1}>
          {activeSection && Array.from({ length: activeSection.questionCount }, (_, i) => {
            const questionIndex = activeSection.startIndex + i;
            const questionNumber = questionIndex + 1;
            const status = getQuestionStatus(questionIndex);
            const questionId = questionIds[questionIndex];

            return (
              <Grid item xs={3} sm={2} md={1.5} key={questionIndex}>
                <Tooltip
                  title={
                    <Box>
                      <Typography variant="caption">Soru {questionNumber}</Typography>
                      {status === 'answered' && <Typography variant="caption" display="block">Cevaplanmış</Typography>}
                      {status === 'flagged' && <Typography variant="caption" display="block">İşaretli</Typography>}
                    </Box>
                  }
                >
                  <Button
                    fullWidth
                    variant={status === 'current' ? 'contained' : 'outlined'}
                    onClick={() => onQuestionSelect(questionIndex)}
                    onDoubleClick={() => questionId && onFlagQuestion(questionId)}
                    sx={{
                      minWidth: 0,
                      height: 48,
                      borderColor: getQuestionColor(status),
                      bgcolor: status === 'current' ? activeSection.color : 'transparent',
                      color: status === 'current' ? 'white' : getQuestionColor(status),
                      '&:hover': {
                        bgcolor: status === 'current' ? activeSection.color : 'grey.100',
                        opacity: 0.9,
                      },
                      position: 'relative',
                    }}
                  >
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <Typography variant="body2" fontWeight="bold">
                        {questionNumber}
                      </Typography>
                      {status !== 'current' && (
                        <Box sx={{ position: 'absolute', top: 2, right: 2 }}>
                          {getQuestionIcon(status)}
                        </Box>
                      )}
                    </Box>
                  </Button>
                </Tooltip>
              </Grid>
            );
          })}
        </Grid>
      </Box>

      {/* Navigasyon */}
      {activeSection && (
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between' }}>
          <Button
            startIcon={<NavigateBefore />}
            onClick={() => {
              if (activeTab > 0) {
                setActiveTab(activeTab - 1);
                onQuestionSelect(sections[activeTab - 1].startIndex);
              }
            }}
            disabled={activeTab === 0}
          >
            Önceki Bölüm
          </Button>
          <Button
            endIcon={<NavigateNext />}
            onClick={() => {
              if (activeTab < sections.length - 1) {
                setActiveTab(activeTab + 1);
                onQuestionSelect(sections[activeTab + 1].startIndex);
              }
            }}
            disabled={activeTab === sections.length - 1}
          >
            Sonraki Bölüm
          </Button>
        </Box>
      )}

      {/* Lejant */}
      <Box sx={{ p: 2, bgcolor: 'grey.50', borderTop: 1, borderColor: 'divider' }}>
        <Typography variant="caption" color="textSecondary" gutterBottom display="block">
          Lejant:
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Box sx={{ width: 16, height: 16, bgcolor: theme.palette.primary.main, borderRadius: 1 }} />
            <Typography variant="caption">Mevcut</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <CheckCircle fontSize="small" color="success" />
            <Typography variant="caption">Cevaplanmış</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Bookmark fontSize="small" color="warning" />
            <Typography variant="caption">İşaretli</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <RadioButtonUnchecked fontSize="small" sx={{ color: 'grey.300' }} />
            <Typography variant="caption">Boş</Typography>
          </Box>
        </Box>
      </Box>
    </Paper>
  );
};

export default AYTOptikForm;
