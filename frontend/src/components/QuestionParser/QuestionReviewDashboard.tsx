import {
  Edit,
  Check,
  Warning,
  Image as ImageIcon,
  Functions,
} from '@mui/icons-material';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  LinearProgress,
} from '@mui/material';
import axios from 'axios';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

interface ParsedQuestion {
  id: number;
  question_number: number;
  subject: string;
  topic: string;
  question_text: string;
  options: Record<string, string>;
  correct_answer?: string;
  has_image: boolean;
  has_equation: boolean;
  is_verified: boolean;
  detection_confidence: number;
  ocr_confidence: number;
  has_problematic_keywords: boolean;
}

const QuestionReviewDashboard: React.FC = () => {
  const [questions, setQuestions] = useState<ParsedQuestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedQuestion, setSelectedQuestion] = useState<ParsedQuestion | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [filter, setFilter] = useState({
    subject: 'all',
    verified: 'all',
    hasProblems: 'all',
  });

  // İstatistikler
  const [stats, setStats] = useState({
    total: 0,
    verified: 0,
    withProblems: 0,
    avgConfidence: 0,
  });

  useEffect(() => {
    loadQuestions();
    loadStats();
  }, [filter]);

  const loadQuestions = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/parsed-questions', { params: filter });
      setQuestions(response.data);
    } catch (error) {
      console.error('Failed to load questions:', error);
    }
    setLoading(false);
  };

  const loadStats = async () => {
    try {
      const response = await axios.get('/api/parsed-questions/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleVerify = async (id: number) => {
    try {
      await axios.patch(`/api/parsed-questions/${id}/verify`);
      await loadQuestions();
      await loadStats();
    } catch (error) {
      console.error('Failed to verify question:', error);
    }
  };

  const handleEdit = (question: ParsedQuestion) => {
    setSelectedQuestion(question);
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!selectedQuestion) {return;}

    try {
      await axios.patch(`/api/parsed-questions/${selectedQuestion.id}`, selectedQuestion);
      setEditDialogOpen(false);
      await loadQuestions();
    } catch (error) {
      console.error('Failed to save edits:', error);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.9) {return 'success';}
    if (confidence > 0.7) {return 'warning';}
    return 'error';
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* İstatistik Kartları */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Toplam Soru
              </Typography>
              <Typography variant="h4">
                {stats.total}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Doğrulanmış
              </Typography>
              <Typography variant="h4" sx={{ color: '#4caf50' }}>
                {stats.verified}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(stats.verified / stats.total) * 100}
                color="success"
                sx={{ mt: 2 }}
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Problemli
              </Typography>
              <Typography variant="h4" sx={{ color: '#ff9800' }}>
                {stats.withProblems}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Ortalama Güven
              </Typography>
              <Typography variant="h4">
                {(stats.avgConfidence * 100).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filtreler */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={4}>
          <FormControl fullWidth size="small">
            <InputLabel>Ders</InputLabel>
            <Select
              value={filter.subject}
              onChange={(e) => setFilter({ ...filter, subject: e.target.value })}
            >
              <MenuItem value="all">Tümü</MenuItem>
              <MenuItem value="Matematik">Matematik</MenuItem>
              <MenuItem value="Fizik">Fizik</MenuItem>
              <MenuItem value="Kimya">Kimya</MenuItem>
              <MenuItem value="Biyoloji">Biyoloji</MenuItem>
              <MenuItem value="Türkçe">Türkçe</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={4}>
          <FormControl fullWidth size="small">
            <InputLabel>Doğrulama Durumu</InputLabel>
            <Select
              value={filter.verified}
              onChange={(e) => setFilter({ ...filter, verified: e.target.value })}
            >
              <MenuItem value="all">Tümü</MenuItem>
              <MenuItem value="true">Doğrulanmış</MenuItem>
              <MenuItem value="false">Bekliyor</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={4}>
          <FormControl fullWidth size="small">
            <InputLabel>Problem Durumu</InputLabel>
            <Select
              value={filter.hasProblems}
              onChange={(e) => setFilter({ ...filter, hasProblems: e.target.value })}
            >
              <MenuItem value="all">Tümü</MenuItem>
              <MenuItem value="true">Problemli</MenuItem>
              <MenuItem value="false">Temiz</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      {/* Soru Tablosu */}
      {loading ? (
        <LinearProgress />
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Soru #</TableCell>
                <TableCell>Ders</TableCell>
                <TableCell>Konu</TableCell>
                <TableCell>Güven</TableCell>
                <TableCell>Özellikler</TableCell>
                <TableCell>Durum</TableCell>
                <TableCell>İşlemler</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {questions.map((question) => (
                <TableRow key={question.id}>
                  <TableCell>{question.question_number}</TableCell>
                  <TableCell>{question.subject}</TableCell>
                  <TableCell>{question.topic}</TableCell>
                  <TableCell>
                    <Chip
                      label={`${(question.ocr_confidence * 100).toFixed(0)}%`}
                      color={getConfidenceColor(question.ocr_confidence)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {question.has_image && <ImageIcon fontSize="small" />}
                    {question.has_equation && <Functions fontSize="small" />}
                    {question.has_problematic_keywords && <Warning fontSize="small" color="warning" />}
                  </TableCell>
                  <TableCell>
                    {question.is_verified ? (
                      <Chip label="Doğrulandı" color="success" size="small" />
                    ) : (
                      <Chip label="Bekliyor" color="warning" size="small" />
                    )}
                  </TableCell>
                  <TableCell>
                    <IconButton onClick={() => handleEdit(question)} size="small">
                      <Edit />
                    </IconButton>
                    {!question.is_verified && (
                      <IconButton onClick={() => handleVerify(question.id)} size="small" color="success">
                        <Check />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Düzenleme Dialog'u */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <Box sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Soru Düzenle
          </Typography>
          {selectedQuestion && (
            <Box>
              <TextField
                label="Soru Metni"
                multiline
                rows={4}
                fullWidth
                value={selectedQuestion.question_text}
                onChange={(e) => setSelectedQuestion({ ...selectedQuestion, question_text: e.target.value })}
                sx={{ mb: 2 }}
              />
              {Object.entries(selectedQuestion.options).map(([key, value]) => (
                <TextField
                  key={key}
                  label={`Seçenek ${key}`}
                  fullWidth
                  value={value}
                  onChange={(e) =>
                    setSelectedQuestion({
                      ...selectedQuestion,
                      options: { ...selectedQuestion.options, [key]: e.target.value },
                    })
                  }
                  sx={{ mb: 2 }}
                />
              ))}
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                <Button onClick={() => setEditDialogOpen(false)} sx={{ mr: 1 }}>
                  İptal
                </Button>
                <Button variant="contained" onClick={handleSaveEdit}>
                  Kaydet
                </Button>
              </Box>
            </Box>
          )}
        </Box>
      </Dialog>
    </Box>
  );
};

export default QuestionReviewDashboard;
