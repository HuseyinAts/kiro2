/**
 * FSRS Dashboard
 * Free Spaced Repetition Scheduler - Smart flashcard review system
 */
import {
  School,
  PlayArrow,
  Stop,
  Psychology,
  TrendingUp,
  Lightbulb,
  AutoAwesome,
  CheckCircle,
  Schedule,
} from '@mui/icons-material';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  Alert,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  TextField,
} from '@mui/material';
import { useState, useEffect } from 'react';
// Note: recharts imports are available for future chart implementations
// import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
//   LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
//   ResponsiveContainer, BarChart, Bar } from 'recharts';

interface Flashcard {
  id: string;
  subject: string;
  topic: string;
  content: string;
  answer: string;
  difficulty: number;
  stability: number;
  retrievability: number;
  due_date?: string;
  state: string;
  review_count: number;
  retention_probability: number;
  is_overdue: boolean;
}

interface StudyRecommendations {
  due_cards_count: number;
  upcoming_cards_count: number;
  difficult_cards_count: number;
  cultural_period: string;
  period_advice: string;
  recommended_study_time: number;
  priority_subjects: string[];
  total_cards: number;
  new_cards: number;
  learning_cards: number;
  review_cards: number;
}

interface StudyStatistics {
  total_cards: number;
  cards_due_today: number;
  avg_retention: number;
  study_streak_days: number;
  total_reviews: number;
  success_rate: number;
  subjects: any[];
}

export function FSRSDashboardPage() {
  const [_loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<StudyRecommendations | null>(null);
  const [statistics, setStatistics] = useState<StudyStatistics | null>(null);
  const [dueCards, setDueCards] = useState<Flashcard[]>([]);
  const [currentCard, setCurrentCard] = useState<Flashcard | null>(null);
  const [showAnswer, setShowAnswer] = useState(false);
  const [studySessionActive, setStudySessionActive] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [cardsReviewed, setCardsReviewed] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Create card dialog
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newCardSubject, setNewCardSubject] = useState('matematik');
  const [newCardTopic, setNewCardTopic] = useState('');
  const [newCardContent, setNewCardContent] = useState('');
  const [newCardAnswer, setNewCardAnswer] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const token = localStorage.getItem('token');

      const [recsRes, statsRes, cardsRes] = await Promise.allSettled([
        fetch(`${API_URL}/api/v1/fsrs/recommendations`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
        fetch(`${API_URL}/api/v1/fsrs/statistics`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
        fetch(`${API_URL}/api/v1/fsrs/flashcards/due`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
      ]);

      if (recsRes.status === 'fulfilled' && recsRes.value.ok) {
        const data = await recsRes.value.json();
        setRecommendations(data.data);
      }

      if (statsRes.status === 'fulfilled' && statsRes.value.ok) {
        const data = await statsRes.value.json();
        setStatistics(data.data);
      }

      if (cardsRes.status === 'fulfilled' && cardsRes.value.ok) {
        const data = await cardsRes.value.json();
        setDueCards(data.data?.flashcards || []);
        if (data.data?.flashcards?.length > 0 && !currentCard) {
          setCurrentCard(data.data.flashcards[0]);
        }
      }

    } catch (err: any) {
      console.error('Dashboard data loading error:', err);
      setError(err.message || 'Veriler yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const startStudySession = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const token = localStorage.getItem('token');

      const response = await fetch(`${API_URL}/api/v1/fsrs/study-sessions/start`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setSessionId(data.data.session_id);
        setStudySessionActive(true);
        setCardsReviewed(0);
      }
    } catch (err) {
      console.error('Start session error:', err);
    }
  };

  const endStudySession = async () => {
    if (!sessionId) {return;}

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const token = localStorage.getItem('token');

      const response = await fetch(`${API_URL}/api/v1/fsrs/study-sessions/${sessionId}/end`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        setStudySessionActive(false);
        setSessionId(null);
        loadDashboardData(); // Refresh data
      }
    } catch (err) {
      console.error('End session error:', err);
    }
  };

  const handleReview = async (grade: number) => {
    if (!currentCard) {return;}

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const token = localStorage.getItem('token');

      const response = await fetch(`${API_URL}/api/v1/fsrs/flashcards/${currentCard.id}/review`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          grade: grade,
          response_time_ms: 5000,
        }),
      });

      if (response.ok) {
        setCardsReviewed(prev => prev + 1);
        setShowAnswer(false);

        // Move to next card
        const nextCards = dueCards.filter(c => c.id !== currentCard.id);
        setDueCards(nextCards);
        setCurrentCard(nextCards[0] || null);

        // If no more cards, end session
        if (nextCards.length === 0) {
          endStudySession();
        }
      }
    } catch (err) {
      console.error('Review error:', err);
    }
  };

  const handleCreateCard = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const token = localStorage.getItem('token');

      const response = await fetch(`${API_URL}/api/v1/fsrs/flashcards`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          subject: newCardSubject,
          topic: newCardTopic,
          content: newCardContent,
          answer: newCardAnswer,
        }),
      });

      if (response.ok) {
        alert('✅ Flashcard oluşturuldu!');
        setShowCreateDialog(false);
        setNewCardTopic('');
        setNewCardContent('');
        setNewCardAnswer('');
        loadDashboardData();
      }
    } catch (err) {
      console.error('Create card error:', err);
      alert('❌ Flashcard oluşturulamadı');
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Psychology sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
          <Box>
            <Typography variant="h4" fontWeight="bold">
              FSRS - Akıllı Tekrar Sistemi
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Bilimsel aralıklı tekrar ile etkili öğrenme
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<AutoAwesome />}
            onClick={() => setShowCreateDialog(true)}
          >
            Kart Oluştur
          </Button>
          {!studySessionActive ? (
            <Button
              variant="contained"
              startIcon={<PlayArrow />}
              onClick={startStudySession}
              size="large"
            >
              Çalışmaya Başla
            </Button>
          ) : (
            <Button
              variant="outlined"
              color="error"
              startIcon={<Stop />}
              onClick={endStudySession}
            >
              Oturumu Bitir
            </Button>
          )}
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Recommendations */}
      {recommendations && (
        <Alert severity="info" icon={<Lightbulb />} sx={{ mb: 3 }}>
          <Typography variant="body1" fontWeight="bold">
            {recommendations.cultural_period} - {recommendations.period_advice}
          </Typography>
          <Typography variant="body2">
            Önerilen çalışma süresi: {recommendations.recommended_study_time} dakika |
            Öncelikli dersler: {recommendations.priority_subjects.join(', ')}
          </Typography>
        </Alert>
      )}

      {/* Statistics Cards */}
      {statistics && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center' }}>
                <School sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant="h4" color="primary">
                  {statistics.total_cards}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Toplam Kart
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Schedule sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                <Typography variant="h4" color="warning.main">
                  {statistics.cards_due_today}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Bugün Tekrar
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center' }}>
                <TrendingUp sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                <Typography variant="h4" color="success.main">
                  {(statistics.avg_retention * 100).toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Ortalama Tutma
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center' }}>
                <CheckCircle sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
                <Typography variant="h4" color="info.main">
                  {statistics.study_streak_days}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Günlük Seri
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Study Session */}
      {studySessionActive && currentCard ? (
        <Paper elevation={3} sx={{ p: 4, mb: 3, backgroundColor: 'primary.light', color: 'white' }}>
          <Box sx={{ mb: 3 }}>
            <Chip
              label={`${currentCard.subject} - ${currentCard.topic}`}
              sx={{ backgroundColor: 'rgba(255,255,255,0.3)', color: 'white', mb: 2 }}
            />
            <Typography variant="caption" display="block">
              Kart {cardsReviewed + 1} / {dueCards.length + cardsReviewed} |
              Zorluk: {(currentCard.difficulty * 100).toFixed(0)}% |
              Tutma Olasılığı: {(currentCard.retention_probability * 100).toFixed(0)}%
            </Typography>
          </Box>

          <Paper sx={{ p: 3, mb: 3, minHeight: 200 }}>
            <Typography variant="h6" gutterBottom>
              Soru:
            </Typography>
            <Typography variant="body1" paragraph>
              {currentCard.content}
            </Typography>

            {showAnswer && (
              <>
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" gutterBottom color="success.main">
                  Cevap:
                </Typography>
                <Typography variant="body1">
                  {currentCard.answer}
                </Typography>
              </>
            )}
          </Paper>

          {!showAnswer ? (
            <Button
              variant="contained"
              fullWidth
              size="large"
              onClick={() => setShowAnswer(true)}
            >
              Cevabı Göster
            </Button>
          ) : (
            <Grid container spacing={2}>
              <Grid item xs={6} md={3}>
                <Button
                  variant="contained"
                  fullWidth
                  color="error"
                  onClick={() => handleReview(1)}
                >
                  Hatırlamadım (1)
                </Button>
              </Grid>
              <Grid item xs={6} md={3}>
                <Button
                  variant="contained"
                  fullWidth
                  color="warning"
                  onClick={() => handleReview(2)}
                >
                  Zor (2)
                </Button>
              </Grid>
              <Grid item xs={6} md={3}>
                <Button
                  variant="contained"
                  fullWidth
                  color="info"
                  onClick={() => handleReview(3)}
                >
                  İyi (3)
                </Button>
              </Grid>
              <Grid item xs={6} md={3}>
                <Button
                  variant="contained"
                  fullWidth
                  color="success"
                  onClick={() => handleReview(4)}
                >
                  Kolay (4)
                </Button>
              </Grid>
            </Grid>
          )}

          <LinearProgress
            variant="determinate"
            value={(cardsReviewed / (dueCards.length + cardsReviewed)) * 100}
            sx={{ mt: 3, height: 8, borderRadius: 4 }}
          />
        </Paper>
      ) : (
        !studySessionActive && (
          <Paper elevation={2} sx={{ p: 4, textAlign: 'center' }}>
            <School sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Çalışma başlatmak için &quot;Çalışmaya Başla&quot; butonuna tıklayın
            </Typography>
            {recommendations && (
              <Typography variant="body2" color="text.secondary">
                {recommendations.due_cards_count} kart tekrar için hazır
              </Typography>
            )}
          </Paper>
        )
      )}

      {/* Create Flashcard Dialog */}
      <Dialog open={showCreateDialog} onClose={() => setShowCreateDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Yeni Flashcard Oluştur</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              label="Ders"
              select
              fullWidth
              value={newCardSubject}
              onChange={(e) => setNewCardSubject(e.target.value)}
              sx={{ mb: 2 }}
              SelectProps={{ native: true }}
            >
              <option value="matematik">Matematik</option>
              <option value="fizik">Fizik</option>
              <option value="kimya">Kimya</option>
              <option value="biyoloji">Biyoloji</option>
              <option value="turkce">Türkçe</option>
            </TextField>

            <TextField
              label="Konu"
              fullWidth
              value={newCardTopic}
              onChange={(e) => setNewCardTopic(e.target.value)}
              sx={{ mb: 2 }}
            />

            <TextField
              label="Soru/İçerik"
              fullWidth
              multiline
              rows={4}
              value={newCardContent}
              onChange={(e) => setNewCardContent(e.target.value)}
              sx={{ mb: 2 }}
            />

            <TextField
              label="Cevap"
              fullWidth
              multiline
              rows={3}
              value={newCardAnswer}
              onChange={(e) => setNewCardAnswer(e.target.value)}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>İptal</Button>
          <Button
            onClick={handleCreateCard}
            variant="contained"
            disabled={!newCardTopic || !newCardContent || !newCardAnswer}
          >
            Oluştur
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default FSRSDashboardPage;
