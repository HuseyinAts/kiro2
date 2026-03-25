/**
 * CATPage — /cat route
 * Ders seçimi + CAT widget
 */
import { useState } from 'react';
import {
  Container, Typography, Box, Grid, Card,
  CardActionArea, Chip, Stack, Alert, Button,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { CATWidget } from '../components/CAT/CATWidget';

const SUBJECTS = [
  { id: 'matematik',    name: 'Matematik',    emoji: '🔢', color: '#1976d2' },
  { id: 'turkce',       name: 'Türkçe',       emoji: '📖', color: '#388e3c' },
  { id: 'fizik',        name: 'Fizik',        emoji: '⚛️', color: '#7b1fa2' },
  { id: 'kimya',        name: 'Kimya',        emoji: '🧪', color: '#f57c00' },
  { id: 'biyoloji',     name: 'Biyoloji',     emoji: '🧬', color: '#0097a7' },
  { id: 'tarih',        name: 'Tarih',        emoji: '🏛️', color: '#5d4037' },
  { id: 'cografya',     name: 'Coğrafya',     emoji: '🌍', color: '#455a64' },
  { id: 'geometri',     name: 'Geometri',     emoji: '📐', color: '#c62828' },
];

export default function CATPage() {
  const navigate = useNavigate();
  const [selectedSubject, setSelectedSubject] = useState<typeof SUBJECTS[0] | null>(null);
  const [completedResults, setCompletedResults] = useState<Record<string, { theta: number; n: number }>>({});

  const handleComplete = (theta: number, _se: number, n: number) => {
    if (!selectedSubject) return;
    setCompletedResults(prev => ({
      ...prev,
      [selectedSubject.id]: { theta, n },
    }));
    // 2 saniye sonra ders seçimine dön
    setTimeout(() => setSelectedSubject(null), 2500);
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Stack direction="row" alignItems="center" spacing={2} mb={3}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate(-1)} variant="text">
          Geri
        </Button>
        <Typography variant="h5" fontWeight={700}>
          🎯 Adaptif Test (CAT)
        </Typography>
      </Stack>

      {!selectedSubject ? (
        <>
          <Typography variant="body2" color="text.secondary" mb={3}>
            Test etmek istediğin dersi seç. Sistem seviyene göre soru seçer.
          </Typography>

          {Object.keys(completedResults).length > 0 && (
            <Alert severity="success" sx={{ mb: 3 }}>
              <strong>Tamamlanan testler:</strong>{' '}
              {Object.entries(completedResults).map(([id, r]) => {
                const s = SUBJECTS.find(x => x.id === id);
                return `${s?.name} (θ=${r.theta.toFixed(2)}, ${r.n} soru)`;
              }).join(' • ')}
            </Alert>
          )}

          <Grid container spacing={2}>
            {SUBJECTS.map(subj => {
              const done = completedResults[subj.id];
              return (
                <Grid item xs={6} sm={4} md={3} key={subj.id}>
                  <Card variant={done ? 'outlined' : 'elevation'}
                    sx={{ borderColor: done ? 'success.main' : undefined,
                          opacity: done ? 0.85 : 1 }}>
                    <CardActionArea onClick={() => setSelectedSubject(subj)} sx={{ p: 2, textAlign: 'center' }}>
                      <Typography fontSize={36}>{subj.emoji}</Typography>
                      <Typography variant="body2" fontWeight={600} mt={0.5}>
                        {subj.name}
                      </Typography>
                      {done && (
                        <Chip size="small" label={`θ ${done.theta.toFixed(1)}`}
                          color="success" sx={{ mt: 1 }} />
                      )}
                    </CardActionArea>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </>
      ) : (
        <Box>
          <Stack direction="row" alignItems="center" spacing={1} mb={3}>
            <Button size="small" onClick={() => setSelectedSubject(null)} startIcon={<ArrowBack />}>
              Ders Seç
            </Button>
            <Typography variant="h6" fontWeight={600}>
              {selectedSubject.emoji} {selectedSubject.name}
            </Typography>
          </Stack>
          <CATWidget
            subjectId={selectedSubject.id}
            subjectName={selectedSubject.name}
            onComplete={handleComplete}
          />
        </Box>
      )}
    </Container>
  );
}
