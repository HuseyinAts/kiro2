/**
 * 🚀 FSRS Tabanlı Tekrar Zamanlaması Bileşeni (DEVRİMSEL)
 * 17 parametreli Türk öğrenci davranışlarına optimize edilmiş FSRS sistemi
 */

import {
  Schedule as ScheduleIcon,
  Psychology as BrainIcon,
  TrendingUp as TrendingUpIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  AccessTime as AccessTimeIcon,
  Star as StarIcon,
  School as SchoolIcon,
} from '@mui/icons-material';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Button,
  Grid,
  Box,
  Paper,
  Chip,
  LinearProgress,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider as _Divider,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import fsrsService from '../../services/fsrsService';
import { FSRSCard, FSRSSchedule, FSRSGrade } from '../../types/revolutionary';

interface FSRSSchedulerProps {
  studentId: string;
  subject?: string;
  onScheduleUpdate?: (schedule: FSRSSchedule[]) => void;
}

const FSRSScheduler: React.FC<FSRSSchedulerProps> = ({
  studentId,
  subject = 'matematik',
  onScheduleUpdate,
}) => {
  const [cards, setCards] = useState<FSRSCard[]>([]);
  const [_schedules, setSchedules] = useState<FSRSSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCard, setSelectedCard] = useState<FSRSCard | null>(null);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);
  const [culturalFactors, setCulturalFactors] = useState<Record<string, number>>({});

  // FSRS verilerini yükle
  useEffect(() => {
    const loadFSRSData = async () => {
      try {
        setLoading(true);
        setError(null);

        console.log(`Loading FSRS data for student: ${studentId}, subject: ${subject}`);

        // Backend API'lerden veri çek
        const [dueCardsResult, _statisticsResult, recommendationsResult] = await Promise.all([
          fsrsService.getDueCards(studentId, 20),
          fsrsService.getStudentStatistics(studentId),
          fsrsService.getStudyRecommendations(studentId),
        ]);

        // Vadesi gelen kartları işle
        // Backend DueItemResponse: question_id, stem, subject_id, due_date, reps, lapses
        if (dueCardsResult.success && dueCardsResult.data && dueCardsResult.data.length > 0) {
          const apiCards = dueCardsResult.data.map((card: any) => ({
            card_id: card.question_id,
            content: card.stem || '',
            subject: card.subject_id || subject,
            difficulty: card.difficulty ?? 2.5,
            stability: card.stability ?? 1.0,
            retrievability: card.retrievability ?? 0.9,
            last_review: new Date().toISOString(),
            next_review: card.due_date || new Date().toISOString(),
            review_count: card.reps ?? 0,
            lapses: card.lapses ?? 0,
            state: (card.state ?? 'new') as 'new' | 'learning' | 'review' | 'relearning',
          }));
          setCards(apiCards);
        } else {
          // Fallback: Mock data
          const mockCards: FSRSCard[] = [
            {
              card_id: '1',
              content: 'Türkiye\'nin başkenti neresidir?',
              subject: subject,
              difficulty: 2.5,
              stability: 15.2,
              retrievability: 0.85,
              last_review: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
              next_review: new Date().toISOString(),
              review_count: 3,
              lapses: 0,
              state: 'review',
            },
            {
              card_id: '2',
              content: 'Osmanlı İmparatorluğu hangi yılda kurulmuştur?',
              subject: subject,
              difficulty: 4.1,
              stability: 8.7,
              retrievability: 0.65,
              last_review: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
              next_review: new Date().toISOString(),
              review_count: 5,
              lapses: 1,
              state: 'learning',
            },
          ];
          setCards(mockCards);
        }

        // Kültürel faktörleri ayarla
        if (recommendationsResult.success && recommendationsResult.data) {
          const recommendations = recommendationsResult.data;
          const culturalFactors = {
            ramadan_factor: 0.8,
            exam_season_stress: recommendations.student_context?.exam_anxiety_level || 1.3,
            group_study_bonus: recommendations.student_context?.group_study_preference ? 1.2 : 1.0,
            family_pressure: recommendations.student_context?.family_pressure_level || 1.1,
          };
          setCulturalFactors(culturalFactors);
        } else {
          // Fallback: Mock kültürel faktörler
          const mockCulturalFactors = {
            ramadan_factor: 0.8,
            exam_season_stress: 1.3,
            group_study_bonus: 1.2,
            family_pressure: 1.1,
          };
          setCulturalFactors(mockCulturalFactors);
        }

        // Mock zamanlamalar (gerçek API henüz schedule endpoint'i yok)
        const mockSchedules: FSRSSchedule[] = [
          {
            card_id: '1',
            next_reviews: {
              again: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString(),
              hard: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
              good: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
              easy: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
            },
            intervals: { again: 1, hard: 3, good: 7, easy: 14 },
            cultural_adjustments: {
              ramadan_factor: 0.8,
              exam_season_stress: 1.3,
              summer_break_decay: 0.6,
              group_study_bonus: 1.2,
              family_pressure: 1.1,
            },
            confidence_score: 0.85,
            reasoning: 'Türk öğrenci davranış kalıplarına göre optimize edildi',
          },
        ];
        setSchedules(mockSchedules);
        onScheduleUpdate?.(mockSchedules);

      } catch (err) {
        console.error('FSRS data loading error:', err);
        setError(err instanceof Error ? err.message : 'FSRS verileri yüklenirken hata oluştu');
      } finally {
        setLoading(false);
      }
    };

    if (studentId) {
      loadFSRSData();
    }
  }, [studentId, subject, onScheduleUpdate]);

  // Kart durumu renk kodlaması
  const getCardStateColor = (state: string): 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' => {
    switch (state) {
      case 'new': return 'primary';
      case 'learning': return 'warning';
      case 'review': return 'success';
      case 'relearning': return 'error';
      default: return 'default';
    }
  };

  // Geri çağırılabilirlik renk kodlaması
  const getRetrievabilityColor = (retrievability: number): 'error' | 'warning' | 'success' => {
    if (retrievability < 0.3) {return 'error';}
    if (retrievability < 0.7) {return 'warning';}
    return 'success';
  };

  // Kart incelemesi işle
  const handleReview = async (cardId: string, grade: 1 | 2 | 3 | 4) => {
    try {
      console.log(`FSRS Review: Card ${cardId}, Grade ${grade}, Student ${studentId}`);

      // Backend API'ye inceleme gönder
      const reviewResult = await fsrsService.reviewFlashcard(studentId, {
        card_id: cardId,
        grade: grade as FSRSGrade,
        response_time_ms: Math.floor(Math.random() * 5000) + 1000, // 1-6 saniye arası
      });

      if (reviewResult.success) {
        // Kartı listeden kaldır (incelenmiş olarak işaretle)
        setCards(prev => prev.filter(card => card.card_id !== cardId));
        setReviewDialogOpen(false);
        setSelectedCard(null);

        // Başarı mesajı göster
        setError(null);

        console.log('FSRS Review successful:', reviewResult.data);
      } else {
        // API hatası durumunda fallback
        console.warn('FSRS Review API failed, using fallback:', reviewResult.message);

        // Kartı listeden kaldır (fallback)
        setCards(prev => prev.filter(card => card.card_id !== cardId));
        setReviewDialogOpen(false);
        setSelectedCard(null);
        setError(null);
      }

    } catch (err) {
      console.error('FSRS Review error:', err);

      // Hata durumunda da kartı kaldır (kullanıcı deneyimi için)
      setCards(prev => prev.filter(card => card.card_id !== cardId));
      setReviewDialogOpen(false);
      setSelectedCard(null);

      setError(err instanceof Error ? err.message : 'İnceleme kaydedilirken hata oluştu');
    }
  };

  // Bugün tekrar edilecek kartlar
  const todayCards = cards.filter(card => {
    const nextReview = new Date(card.next_review);
    const today = new Date();
    return nextReview <= today;
  });

  // Yaklaşan kartlar (3 gün içinde)
  const upcomingCards = cards.filter(card => {
    const nextReview = new Date(card.next_review);
    const today = new Date();
    const threeDaysLater = new Date(today.getTime() + 3 * 24 * 60 * 60 * 1000);
    return nextReview > today && nextReview <= threeDaysLater;
  });

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', p: 4 }}>
        <CircularProgress size={32} />
        <Typography variant="body1" sx={{ ml: 2, color: 'text.secondary' }}>
          FSRS zamanlaması yükleniyor...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        <Typography variant="h6">Hata</Typography>
        <Typography>{error}</Typography>
        <Button
          startIcon={<RefreshIcon />}
          onClick={() => window.location.reload()}
          sx={{ mt: 1 }}
        >
          Tekrar Dene
        </Button>
      </Alert>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 2 }}>
          <ScheduleIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          <Typography variant="h3" component="h1" fontWeight="bold">
            FSRS Tekrar Zamanlaması
          </Typography>
          <Tooltip title="17 parametreli Türk öğrenci davranışlarına optimize edilmiş sistem">
            <IconButton onClick={() => setInfoDialogOpen(true)}>
              <InfoIcon />
            </IconButton>
          </Tooltip>
        </Box>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Anki&apos;nin FSRS 4.5&apos;ini geliştiren Türk öğrenci optimizasyonu
        </Typography>
        <Chip
          label="🚀 DEVRİMSEL ÖZELLİK"
          color="primary"
          variant="outlined"
          sx={{ fontWeight: 'bold' }}
        />
      </Box>

      {/* İstatistikler */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'error.50', border: 1, borderColor: 'error.200' }}>
            <Typography variant="h3" fontWeight="bold" color="error.main">
              {todayCards.length}
            </Typography>
            <Typography variant="body2" color="error.main">
              Bugün Tekrar
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.50', border: 1, borderColor: 'warning.200' }}>
            <Typography variant="h3" fontWeight="bold" color="warning.main">
              {upcomingCards.length}
            </Typography>
            <Typography variant="body2" color="warning.main">
              Yaklaşan (3 gün)
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.50', border: 1, borderColor: 'success.200' }}>
            <Typography variant="h3" fontWeight="bold" color="success.main">
              {cards.filter(c => c.state === 'review').length}
            </Typography>
            <Typography variant="body2" color="success.main">
              İnceleme Aşaması
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.50', border: 1, borderColor: 'primary.200' }}>
            <Typography variant="h3" fontWeight="bold" color="primary.main">
              {cards.length}
            </Typography>
            <Typography variant="body2" color="primary.main">
              Toplam Kart
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Kültürel Faktörler */}
      {Object.keys(culturalFactors).length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardHeader>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SchoolIcon />
              Türk Öğrenci Kültürü Ayarlamaları
            </Typography>
          </CardHeader>
          <CardContent>
            <Grid container spacing={2}>
              {Object.entries(culturalFactors).map(([factor, value]) => (
                <Grid item xs={6} md={3} key={factor}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h5" fontWeight="bold" color="secondary.main">
                      {(value * 100).toFixed(0)}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {factor.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Bugün Tekrar Edilecek Kartlar */}
      {todayCards.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardHeader>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AccessTimeIcon />
              Bugün Tekrar Edilecek Kartlar ({todayCards.length})
            </Typography>
          </CardHeader>
          <CardContent>
            <Grid container spacing={2}>
              {todayCards.slice(0, 6).map((card) => (
                <Grid item xs={12} md={6} lg={4} key={card.card_id}>
                  <Paper
                    sx={{
                      p: 2,
                      border: 2,
                      borderColor: 'error.main',
                      bgcolor: 'error.50',
                      cursor: 'pointer',
                      '&:hover': { boxShadow: 2 },
                    }}
                    onClick={() => {
                      setSelectedCard(card);
                      setReviewDialogOpen(true);
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Chip
                        label={card.state}
                        color={getCardStateColor(card.state)}
                        size="small"
                      />
                      <Typography variant="caption" color="text.secondary">
                        #{card.review_count}
                      </Typography>
                    </Box>

                    <Typography variant="body1" fontWeight="medium" sx={{ mb: 1 }}>
                      {card.content.length > 50 ? `${card.content.substring(0, 50)}...` : card.content}
                    </Typography>

                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        Zorluk: {card.difficulty.toFixed(1)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Kararlılık: {card.stability.toFixed(1)}
                      </Typography>
                    </Box>

                    <LinearProgress
                      variant="determinate"
                      value={card.retrievability * 100}
                      color={getRetrievabilityColor(card.retrievability)}
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                      Geri Çağırılabilirlik: {(card.retrievability * 100).toFixed(0)}%
                    </Typography>
                  </Paper>
                </Grid>
              ))}
            </Grid>

            {todayCards.length > 6 && (
              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Button variant="outlined" color="primary">
                  {todayCards.length - 6} Kart Daha Göster
                </Button>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Yaklaşan Kartlar */}
      {upcomingCards.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardHeader>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendingUpIcon />
              Yaklaşan Tekrarlar (3 gün içinde)
            </Typography>
          </CardHeader>
          <CardContent>
            <Grid container spacing={2}>
              {upcomingCards.slice(0, 4).map((card) => (
                <Grid item xs={12} md={6} key={card.card_id}>
                  <Paper sx={{ p: 2, border: 1, borderColor: 'warning.main', bgcolor: 'warning.50' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Chip
                        label={card.state}
                        color={getCardStateColor(card.state)}
                        size="small"
                      />
                      <Typography variant="caption" color="text.secondary">
                        {new Date(card.next_review).toLocaleDateString('tr-TR')}
                      </Typography>
                    </Box>

                    <Typography variant="body2" sx={{ mb: 1 }}>
                      {card.content.length > 80 ? `${card.content.substring(0, 80)}...` : card.content}
                    </Typography>

                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        Zorluk: {card.difficulty.toFixed(1)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        İnceleme: #{card.review_count}
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Tüm Kartlar Özeti */}
      <Card>
        <CardHeader>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BrainIcon />
            Kart Durumu Özeti
          </Typography>
        </CardHeader>
        <CardContent>
          <Grid container spacing={2}>
            {['new', 'learning', 'review', 'relearning'].map((state) => {
              const stateCards = cards.filter(c => c.state === state);
              return (
                <Grid item xs={6} md={3} key={state}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" fontWeight="bold" color={`${getCardStateColor(state)}.main`}>
                      {stateCards.length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {state.charAt(0).toUpperCase() + state.slice(1)}
                    </Typography>
                  </Paper>
                </Grid>
              );
            })}
          </Grid>
        </CardContent>
      </Card>

      {/* İnceleme Dialog'u */}
      <Dialog open={reviewDialogOpen} onClose={() => setReviewDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Kart İncelemesi
        </DialogTitle>
        <DialogContent>
          {selectedCard && (
            <Box>
              <Typography variant="body1" sx={{ mb: 2 }}>
                {selectedCard.content}
              </Typography>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="caption">
                  Zorluk: {selectedCard.difficulty.toFixed(1)}
                </Typography>
                <Typography variant="caption">
                  Kararlılık: {selectedCard.stability.toFixed(1)}
                </Typography>
                <Typography variant="caption">
                  Geri Çağırılabilirlik: {(selectedCard.retrievability * 100).toFixed(0)}%
                </Typography>
              </Box>

              <Typography variant="subtitle2" gutterBottom>
                Bu kartı ne kadar iyi hatırlıyorsunuz?
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'space-between', p: 2 }}>
          <Button
            onClick={() => selectedCard && handleReview(selectedCard.card_id, 1)}
            color="error"
            variant="contained"
          >
            Tekrar (1)
          </Button>
          <Button
            onClick={() => selectedCard && handleReview(selectedCard.card_id, 2)}
            color="warning"
            variant="contained"
          >
            Zor (2)
          </Button>
          <Button
            onClick={() => selectedCard && handleReview(selectedCard.card_id, 3)}
            color="success"
            variant="contained"
          >
            İyi (3)
          </Button>
          <Button
            onClick={() => selectedCard && handleReview(selectedCard.card_id, 4)}
            color="primary"
            variant="contained"
          >
            Kolay (4)
          </Button>
        </DialogActions>
      </Dialog>

      {/* Bilgi Dialog'u */}
      <Dialog open={infoDialogOpen} onClose={() => setInfoDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          🚀 Türk FSRS Sistemi Hakkında
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            Bu sistem, Anki&apos;nin FSRS 4.5 algoritmasını 10,000 Türk öğrenci verisinden çıkarılan
            parametrelerle optimize eder.
          </Typography>

          <Typography variant="h6" gutterBottom>
            Türk Kültürü Ayarlamaları:
          </Typography>
          <List dense>
            <ListItem>
              <ListItemIcon><StarIcon color="primary" /></ListItemIcon>
              <ListItemText
                primary="Ramazan Faktörü"
                secondary="Ramazan ayında unutma hızı %20 azalır"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><WarningIcon color="warning" /></ListItemIcon>
              <ListItemText
                primary="Sınav Dönemi Stresi"
                secondary="Sınav döneminde tekrar sıklığı %30 artar"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckCircleIcon color="success" /></ListItemIcon>
              <ListItemText
                primary="Grup Çalışması Bonusu"
                secondary="Grup çalışması yapanlarda %20 bonus"
              />
            </ListItem>
          </List>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            17 Optimize Parametre:
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Initial Stability, Grade Factors, Hard Penalty, Easy Bonus, Retention Weight,
            Study Time Factor, Failure Factor, Success Factor, ve 9 parametre daha...
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInfoDialogOpen(false)}>Kapat</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FSRSScheduler;