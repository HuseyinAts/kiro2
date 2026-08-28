/**
 * PlacementAssessmentPage — /assessment route
 * Yeni /api/v1/placement API ile çalışır
 */
import { useState } from 'react';
import {
  Container, Typography, Box, Grid, Card,
  CardActionArea, Stack, Button, Alert, Chip,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { PlacementWidget } from '../components/CAT/PlacementWidget';

const SUBJECTS = [
  { id: 'matematik', name: 'Matematik', emoji: '🔢' },
  { id: 'turkce',    name: 'Türkçe',    emoji: '📖' },
  { id: 'fizik',     name: 'Fizik',     emoji: '⚛️' },
  { id: 'kimya',     name: 'Kimya',     emoji: '🧪' },
  { id: 'biyoloji',  name: 'Biyoloji',  emoji: '🧬' },
  { id: 'tarih',     name: 'Tarih',     emoji: '🏛️' },
];

const SCHOOL_TYPES = [
  { id: 'default', label: 'Standart' },
  { id: 'fen',     label: 'Fen Lisesi' },
  { id: 'anadolu', label: 'Anadolu Lisesi' },
  { id: 'meslek',  label: 'Meslek Lisesi' },
];

export default function PlacementAssessmentPage() {
  const navigate = useNavigate();
  const [selectedSubject, setSelectedSubject] = useState<typeof SUBJECTS[0] | null>(null);
  const [schoolType, setSchoolType] = useState('default');
  const [results, setResults] = useState<Record<string, { level_label: string; theta: number }>>({});

  const handleComplete = (r: { theta: number; level: string; level_label: string }) => {
    if (!selectedSubject) {return;}
    setResults(prev => ({ ...prev, [selectedSubject.id]: { theta: r.theta, level_label: r.level_label } }));
    setTimeout(() => setSelectedSubject(null), 3000);
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Stack direction="row" alignItems="center" spacing={2} mb={3}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate(-1)} variant="text">Geri</Button>
        <Box>
          <Typography variant="h5" fontWeight={700}>🎓 Seviye Tespiti</Typography>
          <Typography variant="caption" color="text.secondary">
            Her ders için seviyeni belirle
          </Typography>
        </Box>
      </Stack>

      {!selectedSubject && (
        <Box mb={3}>
          <Typography variant="subtitle2" fontWeight={600} mb={1}>Okul Türü</Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {SCHOOL_TYPES.map(st => (
              <Chip key={st.id} label={st.label} clickable
                onClick={() => setSchoolType(st.id)}
                color={schoolType === st.id ? 'primary' : 'default'}
                variant={schoolType === st.id ? 'filled' : 'outlined'} />
            ))}
          </Stack>
        </Box>
      )}

      {!selectedSubject && Object.keys(results).length > 0 && (
        <Alert severity="success" sx={{ mb: 3 }}>
          <strong>Tamamlanan:</strong>{' '}
          {Object.entries(results).map(([id, r]) => `${SUBJECTS.find(x=>x.id===id)?.name}: ${r.level_label}`).join(' • ')}
        </Alert>
      )}

      {!selectedSubject ? (
        <Grid container spacing={2}>
          {SUBJECTS.map(subj => {
            const done = results[subj.id];
            return (
              <Grid item xs={6} sm={4} key={subj.id}>
                <Card variant={done ? 'outlined' : 'elevation'}
                  sx={{ borderColor: done ? 'success.main' : undefined }}>
                  <CardActionArea onClick={() => setSelectedSubject(subj)} sx={{ p: 2.5, textAlign: 'center' }}>
                    <Typography fontSize={40}>{subj.emoji}</Typography>
                    <Typography variant="body2" fontWeight={600} mt={1}>{subj.name}</Typography>
                    {done && <Chip size="small" label={done.level_label} color="success" sx={{ mt: 1 }} />}
                  </CardActionArea>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      ) : (
        <Box>
          <Stack direction="row" alignItems="center" spacing={1} mb={3}>
            <Button size="small" onClick={() => setSelectedSubject(null)} startIcon={<ArrowBack />}>Ders Seç</Button>
            <Typography variant="h6" fontWeight={600}>{selectedSubject.emoji} {selectedSubject.name}</Typography>
          </Stack>
          <PlacementWidget
            subjectId={selectedSubject.id}
            subjectName={selectedSubject.name}
            schoolType={schoolType}
            onComplete={handleComplete}
          />
        </Box>
      )}
    </Container>
  );
}
