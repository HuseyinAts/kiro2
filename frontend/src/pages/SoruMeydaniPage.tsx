/**
 * SoruMeydaniPage -- /soru-meydani
 * Sablon bazli Q&A forumu
 */
import { useEffect, useState, useCallback } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import {
  Forum,
  Add,
  CheckCircle,
  ThumbUp,
  ThumbDown,
  QuestionAnswer,
} from '@mui/icons-material';
import type { ForumQuestion, ForumSolution } from '../services/socialService';
import { soruMeydani } from '../services/socialService';

const SUBJECTS = [
  'matematik', 'fizik', 'kimya', 'biyoloji',
  'turkce', 'tarih', 'cografya', 'geometri',
];

export default function SoruMeydaniPage() {
  const [questions, setQuestions] = useState<ForumQuestion[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [subjectFilter, setSubjectFilter] = useState('');
  const [askOpen, setAskOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedQ, setSelectedQ] = useState<ForumQuestion | null>(null);
  const [solutions, setSolutions] = useState<ForumSolution[]>([]);

  // Ask form state
  const [askSubject, setAskSubject] = useState('');
  const [askType, setAskType] = useState('how_to_solve');
  const [askTitle, setAskTitle] = useState('');
  const [askBody, setAskBody] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Solution form
  const [solBody, setSolBody] = useState('');

  const fetchQuestions = useCallback(async () => {
    try {
      setLoading(true);
      const res = await soruMeydani.listQuestions({
        subject_area: subjectFilter || undefined,
        limit: 20,
      });
      setQuestions(res.data.items);
      setTotal(res.data.total);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [subjectFilter]);

  useEffect(() => { fetchQuestions(); }, [fetchQuestions]);

  const handleAsk = async () => {
    if (!askSubject || !askTitle) {return;}
    setSubmitting(true);
    try {
      await soruMeydani.askQuestion({
        subject_area: askSubject,
        question_type: askType,
        title: askTitle,
        body: askBody || undefined,
      });
      setAskOpen(false);
      setAskTitle('');
      setAskBody('');
      fetchQuestions();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const openDetail = async (q: ForumQuestion) => {
    setSelectedQ(q);
    setDetailOpen(true);
    try {
      const res = await soruMeydani.getQuestion(q.id);
      setSolutions(res.data.solutions);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleSubmitSolution = async () => {
    if (!selectedQ || !solBody) {return;}
    setSubmitting(true);
    try {
      await soruMeydani.submitSolution(selectedQ.id, { body: solBody });
      setSolBody('');
      // Refresh
      const res = await soruMeydani.getQuestion(selectedQ.id);
      setSolutions(res.data.solutions);
      fetchQuestions();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleVote = async (solutionId: string, type: 'helpful' | 'not_helpful') => {
    try {
      await soruMeydani.voteSolution(solutionId, type);
      if (selectedQ) {
        const res = await soruMeydani.getQuestion(selectedQ.id);
        setSolutions(res.data.solutions);
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Stack direction="row" spacing={1} alignItems="center">
          <Forum color="primary" />
          <Typography variant="h5" fontWeight={700}>Soru Meydani</Typography>
          <Chip label={`${total} soru`} size="small" />
        </Stack>
        <Button variant="contained" startIcon={<Add />} onClick={() => setAskOpen(true)}>
          Soru Sor
        </Button>
      </Stack>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

      {/* Subject filter */}
      <Stack direction="row" spacing={1} sx={{ mb: 3, flexWrap: 'wrap', gap: 1 }}>
        <Chip
          label="Tumu"
          variant={subjectFilter === '' ? 'filled' : 'outlined'}
          onClick={() => setSubjectFilter('')}
        />
        {SUBJECTS.map(s => (
          <Chip
            key={s}
            label={s.charAt(0).toUpperCase() + s.slice(1)}
            variant={subjectFilter === s ? 'filled' : 'outlined'}
            onClick={() => setSubjectFilter(s)}
          />
        ))}
      </Stack>

      {/* Questions list */}
      {loading ? (
        <Box textAlign="center" py={4}><CircularProgress /></Box>
      ) : questions.length === 0 ? (
        <Typography color="text.secondary" textAlign="center" py={4}>
          Henuz soru yok. Ilk soruyu siz sorun!
        </Typography>
      ) : (
        <Stack spacing={2}>
          {questions.map(q => (
            <Card key={q.id} sx={{ cursor: 'pointer' }} onClick={() => openDetail(q)}>
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                  <Box>
                    <Typography variant="subtitle1" fontWeight={600}>{q.title}</Typography>
                    <Stack direction="row" spacing={1} sx={{ mt: 0.5 }}>
                      <Chip label={q.subject_area} size="small" color="primary" variant="outlined" />
                      <Chip label={q.question_type.replace(/_/g, ' ')} size="small" />
                    </Stack>
                  </Box>
                  <Stack alignItems="center">
                    <QuestionAnswer fontSize="small" color="action" />
                    <Typography variant="caption">{q.solution_count}</Typography>
                    {q.status === 'closed' && <CheckCircle fontSize="small" color="success" />}
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}

      {/* Ask Dialog */}
      <Dialog open={askOpen} onClose={() => setAskOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Yeni Soru Sor</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <FormControl fullWidth>
              <InputLabel>Konu</InputLabel>
              <Select value={askSubject} label="Konu" onChange={e => setAskSubject(e.target.value)}>
                {SUBJECTS.map(s => <MenuItem key={s} value={s}>{s}</MenuItem>)}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Soru Tipi</InputLabel>
              <Select value={askType} label="Soru Tipi" onChange={e => setAskType(e.target.value)}>
                <MenuItem value="how_to_solve">Bu soruyu nasil cozerim?</MenuItem>
                <MenuItem value="explain_concept">Bu konuyu anlamiyorum</MenuItem>
                <MenuItem value="which_formula">Hangi formulu kullanmaliyim?</MenuItem>
                <MenuItem value="check_my_work">Cozumum dogru mu?</MenuItem>
                <MenuItem value="alternative_method">Farkli cozum yolu var mi?</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Soru Basligi"
              value={askTitle}
              onChange={e => setAskTitle(e.target.value)}
              inputProps={{ maxLength: 200 }}
              fullWidth
            />
            <TextField
              label="Detay (opsiyonel)"
              value={askBody}
              onChange={e => setAskBody(e.target.value)}
              multiline
              rows={3}
              inputProps={{ maxLength: 500 }}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAskOpen(false)}>Iptal</Button>
          <Button
            variant="contained"
            onClick={handleAsk}
            disabled={submitting || !askSubject || !askTitle}
          >
            {submitting ? <CircularProgress size={20} /> : 'Gonder'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={detailOpen} onClose={() => setDetailOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{selectedQ?.title}</DialogTitle>
        <DialogContent>
          {selectedQ && (
            <Box sx={{ mb: 2 }}>
              <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                <Chip label={selectedQ.subject_area} size="small" color="primary" />
                <Chip label={selectedQ.status} size="small" color={
                  selectedQ.status === 'closed' ? 'success' : selectedQ.status === 'answered' ? 'warning' : 'default'
                } />
              </Stack>
              {selectedQ.body && (
                <Typography variant="body2" color="text.secondary">{selectedQ.body}</Typography>
              )}
            </Box>
          )}

          <Divider sx={{ my: 2 }} />
          <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
            Cozumler ({solutions.length})
          </Typography>

          {solutions.map(s => (
            <Card key={s.id} sx={{ mb: 2, border: s.is_accepted ? '2px solid #4caf50' : undefined }}>
              <CardContent>
                <Typography variant="body1">{s.body}</Typography>
                <Stack direction="row" spacing={2} sx={{ mt: 1 }} alignItems="center">
                  <Button size="small" startIcon={<ThumbUp />} onClick={() => handleVote(s.id, 'helpful')}>
                    {s.helpful_count}
                  </Button>
                  <Button size="small" startIcon={<ThumbDown />} onClick={() => handleVote(s.id, 'not_helpful')}>
                    {s.not_helpful_count}
                  </Button>
                  {s.is_accepted && <Chip label="Kabul Edildi" color="success" size="small" icon={<CheckCircle />} />}
                </Stack>
              </CardContent>
            </Card>
          ))}

          {/* Submit solution */}
          {selectedQ?.status !== 'closed' && (
            <Box sx={{ mt: 2 }}>
              <TextField
                label="Cozum Onerin"
                value={solBody}
                onChange={e => setSolBody(e.target.value)}
                multiline
                rows={3}
                fullWidth
                inputProps={{ maxLength: 2000 }}
              />
              <Button
                variant="contained"
                sx={{ mt: 1 }}
                onClick={handleSubmitSolution}
                disabled={submitting || solBody.length < 10}
              >
                {submitting ? <CircularProgress size={20} /> : 'Cozum Gonder'}
              </Button>
            </Box>
          )}
        </DialogContent>
      </Dialog>
    </Container>
  );
}
