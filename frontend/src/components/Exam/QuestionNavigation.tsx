/**
 * Gelişmiş Soru Navigasyon Bileşeni
 * Tüm soruları görüntüleyebilen ve hızlı geçiş sağlayan navigasyon
 */
import {
  NavigateNext,
  NavigateBefore,
  Bookmark,
  BookmarkBorder,
  CheckCircle,
  RadioButtonUnchecked,
  ExpandMore,
  ExpandLess,
  GridView,
  List as ListIcon,
} from '@mui/icons-material';
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
  useMediaQuery,
} from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';
import {  useState  } from 'react';

import { ExamSessionResponse } from '../../services/examService';
import { SinavOturumu } from '../../types';

interface QuestionNavigationProps {
  oturum: SinavOturumu | ExamSessionResponse
  onQuestionSelect: (questionIndex: number) => void
  onFlagToggle: (questionId: string) => void
  onNext: () => void
  onPrevious: () => void
  disabled?: boolean
}

export const QuestionNavigation: React.FC<QuestionNavigationProps> = ({
  oturum,
  onQuestionSelect,
  onFlagToggle,
  onNext,
  onPrevious,
  disabled = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [showAllQuestions, setShowAllQuestions] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [expanded, setExpanded] = useState(false);

  // Helper function to get property values from either interface type
  const getCurrentQuestionIndex = () => 'current_question_index' in oturum ? oturum.current_question_index : oturum.mevcut_soru_index;
  const getTotalQuestions = () => 'total_questions' in oturum ? oturum.total_questions : oturum.toplam_soru_sayisi;
  const getQuestionList = () => 'soru_listesi' in oturum ? oturum.soru_listesi : [];
  const getAnsweredQuestions = () => 'cevaplanan_sorular' in oturum ? oturum.cevaplanan_sorular : {};
  const getFlaggedQuestions = () => 'isaretlenen_sorular' in oturum ? oturum.isaretlenen_sorular : [];

  const currentQuestionIndex = getCurrentQuestionIndex();
  const totalQuestions = getTotalQuestions();
  const questionList = getQuestionList();
  const answeredQuestions = getAnsweredQuestions();
  const flaggedQuestions = getFlaggedQuestions();

  const isFirstQuestion = currentQuestionIndex === 0;
  const isLastQuestion = currentQuestionIndex === totalQuestions - 1;

  /**
   * Soru durumunu belirle
   */
  const getQuestionStatus = (questionIndex: number) => {
    const questionId = questionList[questionIndex] || `question_${questionIndex}`;
    const isAnswered = !!answeredQuestions[questionId];
    const isFlagged = flaggedQuestions.includes(questionId);
    const isCurrent = questionIndex === currentQuestionIndex;

    return {
      isAnswered,
      isFlagged,
      isCurrent,
      questionId,
    };
  };

  /**
   * Soru durumuna göre renk getir
   */
  const getQuestionColor = (status: ReturnType<typeof getQuestionStatus>) => {
    if (status.isCurrent) {return theme.palette.primary.main;}
    if (status.isAnswered) {return theme.palette.success.main;}
    return theme.palette.grey[300];
  };

  /**
   * Soru durumuna göre metin rengi getir
   */
  const getQuestionTextColor = (status: ReturnType<typeof getQuestionStatus>) => {
    if (status.isCurrent || status.isAnswered) {return 'white';}
    return theme.palette.text.primary;
  };

  /**
   * İstatistikleri hesapla
   */
  const stats = {
    answered: Object.keys(answeredQuestions).length,
    flagged: flaggedQuestions.length,
    remaining: totalQuestions - Object.keys(answeredQuestions).length,
  };

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
        '&::-webkit-scrollbar-thumb': { backgroundColor: theme.palette.grey[400], borderRadius: 2 },
      }}>
        {Array.from({ length: Math.min(totalQuestions, 10) }, (_, index) => {
          const actualIndex = Math.max(0, currentQuestionIndex - 5) + index;
          if (actualIndex >= totalQuestions) {return null;}

          const status = getQuestionStatus(actualIndex);

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
                    transform: 'scale(1.1)',
                  },
                }}
              >
                {actualIndex + 1}
              </Box>
            </Tooltip>
          );
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
  );

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
        maxHeight: expanded ? 'none' : '120px',
        overflow: 'hidden',
        transition: 'max-height 0.3s',
      }}>
        {Array.from({ length: totalQuestions }, (_, index) => {
          const status = getQuestionStatus(index);

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
                        boxShadow: theme.shadows[4],
                      },
                    }}
                  >
                    {index + 1}
                  </Box>
                </motion.div>
              </Badge>
            </Tooltip>
          );
        })}
      </Box>

      {/* Genişlet/Daralt butonu */}
      {totalQuestions > 20 && (
        <Box sx={{ textAlign: 'center', mt: 1 }}>
          <IconButton
            onClick={() => setExpanded(!expanded)}
            size="small"
          >
            {expanded ? <ExpandLess /> : <ExpandMore />}
          </IconButton>
        </Box>
      )}

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
          {currentQuestionIndex + 1} / {totalQuestions}
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
  );

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
            <Box sx={{ display: 'flex', gap: 1 }}>
              <IconButton
                onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
                size="small"
              >
                {viewMode === 'grid' ? <ListIcon /> : <GridView />}
              </IconButton>
            </Box>
          </Box>
        </DialogTitle>

        <DialogContent>
          {/* İstatistikler */}
          <Box sx={{ display: 'flex', gap: 2, mb: 3, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Chip
              label={`Toplam: ${totalQuestions}`}
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

          {/* Soru listesi/grid */}
          {viewMode === 'grid' ? (
            <Grid container spacing={1}>
              {Array.from({ length: totalQuestions }, (_, index) => {
                const status = getQuestionStatus(index);

                return (
                  <Grid item xs={2} sm={1.5} md={1} key={index}>
                    <Badge
                      badgeContent={status.isFlagged ? <Bookmark sx={{ fontSize: 10 }} /> : null}
                      color="warning"
                      overlap="circular"
                    >
                      <Box
                        onClick={() => {
                          onQuestionSelect(index);
                          setShowAllQuestions(false);
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
                            boxShadow: theme.shadows[4],
                          },
                        }}
                      >
                        {index + 1}
                      </Box>
                    </Badge>
                  </Grid>
                );
              })}
            </Grid>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {Array.from({ length: totalQuestions }, (_, index) => {
                const status = getQuestionStatus(index);

                return (
                  <Paper
                    key={index}
                    elevation={status.isCurrent ? 3 : 1}
                    sx={{
                      p: 2,
                      cursor: 'pointer',
                      bgcolor: status.isCurrent ? 'primary.50' : 'background.paper',
                      border: status.isCurrent ? 1 : 0,
                      borderColor: 'primary.main',
                      '&:hover': {
                        bgcolor: 'grey.50',
                      },
                    }}
                    onClick={() => {
                      onQuestionSelect(index);
                      setShowAllQuestions(false);
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body1" fontWeight={status.isCurrent ? 'bold' : 'normal'}>
                        Soru {index + 1}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                        {status.isAnswered && (
                          <Chip label="Cevaplandı" color="success" size="small" />
                        )}
                        {status.isFlagged && (
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              onFlagToggle(status.questionId);
                            }}
                          >
                            <Bookmark color="warning" />
                          </IconButton>
                        )}
                        {!status.isFlagged && (
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              onFlagToggle(status.questionId);
                            }}
                          >
                            <BookmarkBorder />
                          </IconButton>
                        )}
                      </Box>
                    </Box>
                  </Paper>
                );
              })}
            </Box>
          )}
        </DialogContent>

        <DialogActions>
          <Button onClick={() => setShowAllQuestions(false)}>
            Kapat
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default QuestionNavigation;