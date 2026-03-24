/**
 * SocialHubPage -- /social
 * Ana sosyal merkez — tum sosyal ozelliklere erisim noktasi
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Box,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  Container,
  Grid,
  Stack,
  Typography,
} from '@mui/material';
import {
  Forum,
  Timer,
  LocalFireDepartment,
  School,
  Shield,
  EmojiEvents,
  SportsKabaddi,
  Groups,
} from '@mui/icons-material';
import { socialSummary, SocialXPSummary } from '../services/socialService';

interface FeatureCard {
  title: string;
  description: string;
  icon: React.ReactNode;
  route: string;
  color: string;
  badge?: string;
}

const FEATURES: FeatureCard[] = [
  {
    title: 'Soru Meydani',
    description: 'Soru sor, cozum oner, oy ver. Sablon bazli guvenli Q&A.',
    icon: <Forum sx={{ fontSize: 40 }} />,
    route: '/soru-meydani',
    color: '#1976d2',
    badge: 'F1',
  },
  {
    title: 'Cozum Duellosu',
    description: 'Ayni soruyu coz, topluluk oylasin. En iyi cozum kazanir!',
    icon: <SportsKabaddi sx={{ fontSize: 40 }} />,
    route: '/cozum-duellosu',
    color: '#ed6c02',
    badge: 'F2',
  },
  {
    title: 'Oba Seferleri',
    description: 'Haftalik takim gorevi. Birlikte hedefe ulas, bonus XP kazan.',
    icon: <Groups sx={{ fontSize: 40 }} />,
    route: '/oba-seferleri',
    color: '#2e7d32',
    badge: 'F3',
  },
  {
    title: 'Pomodoro Odalari',
    description: 'Birlikte calis, 25dk odaklan, 5dk mola. Konu bazli eslestirme.',
    icon: <Timer sx={{ fontSize: 40 }} />,
    route: '/pomodoro',
    color: '#d32f2f',
    badge: 'F4',
  },
  {
    title: 'Birlikte Streak',
    description: 'Ortaginla birlikte gunluk gorev tamamla. 7 ve 30 gun bonuslari.',
    icon: <LocalFireDepartment sx={{ fontSize: 40 }} />,
    route: '/birlikte-streak',
    color: '#ed6c02',
    badge: 'F5',
  },
  {
    title: 'Usta-Cirak',
    description: 'Konunda iyiysen cirak al, ogreniyorsan usta bul. Sistem eslestirir.',
    icon: <School sx={{ fontSize: 40 }} />,
    route: '/usta-cirak',
    color: '#9c27b0',
    badge: 'F6',
  },
];

export default function SocialHubPage() {
  const navigate = useNavigate();
  const [xp, setXp] = useState<SocialXPSummary | null>(null);

  useEffect(() => {
    socialSummary.getXP().then((res) => {
      if (res.success) setXp(res.data);
    }).catch(() => {});
  }, []);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 4 }}>
        <EmojiEvents sx={{ fontSize: 36, color: 'primary.main' }} />
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Sosyal Merkez
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Birlikte calis, birlikte ogren. Guvenli, odakli, tesvik edici.
          </Typography>
        </Box>
      </Stack>

      {/* Safety banner */}
      <Alert
        severity="info"
        icon={<Shield />}
        sx={{ mb: 3, borderRadius: 2 }}
      >
        Tum icerikler 7 katmanli guvenlik filtresiyle korunur. Kisisel bilgi,
        uygunsuz icerik ve flort girisimlerine izin verilmez.
      </Alert>

      {/* Feature cards */}
      <Grid container spacing={3}>
        {FEATURES.map((f) => (
          <Grid item xs={12} sm={6} md={3} key={f.route}>
            <Card
              sx={{
                height: '100%',
                borderTop: `4px solid ${f.color}`,
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6,
                },
              }}
            >
              <CardActionArea
                onClick={() => navigate(f.route)}
                sx={{ height: '100%', p: 2 }}
              >
                <CardContent>
                  <Stack spacing={2} alignItems="center" textAlign="center">
                    <Box sx={{ color: f.color }}>{f.icon}</Box>
                    <Typography variant="h6" fontWeight={600}>
                      {f.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {f.description}
                    </Typography>
                    {f.badge && (
                      <Chip
                        label={f.badge}
                        size="small"
                        sx={{
                          bgcolor: f.color,
                          color: 'white',
                          fontWeight: 600,
                        }}
                      />
                    )}
                  </Stack>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* XP summary */}
      <Card sx={{ mt: 4, p: 3, bgcolor: 'grey.50', borderRadius: 2 }}>
        <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
          <Typography variant="h6" fontWeight={600}>
            Sosyal XP Ozeti
          </Typography>
          {xp && (
            <Chip
              label={`Toplam: ${xp.total_xp} XP`}
              color="primary"
              size="small"
              sx={{ fontWeight: 700 }}
            />
          )}
        </Stack>
        <Stack direction="row" spacing={4} flexWrap="wrap">
          <Box>
            <Typography variant="body2" color="text.secondary">
              Soru Meydani
            </Typography>
            <Typography variant="h5" fontWeight={700} color="primary">
              {xp ? xp.forum_xp : '--'}
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Duello
            </Typography>
            <Typography variant="h5" fontWeight={700} color="warning.main">
              {xp ? xp.duel_xp : '--'}
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Oba
            </Typography>
            <Typography variant="h5" fontWeight={700} color="success.main">
              {xp ? xp.oba_xp : '--'}
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Pomodoro
            </Typography>
            <Typography variant="h5" fontWeight={700} color="error">
              {xp ? xp.pomodoro_xp : '--'}
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Streak
            </Typography>
            <Typography variant="h5" fontWeight={700} color="warning.main">
              {xp ? xp.streak_xp : '--'}
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Usta-Cirak
            </Typography>
            <Typography variant="h5" fontWeight={700} color="secondary">
              {xp ? xp.mentor_xp : '--'}
            </Typography>
          </Box>
        </Stack>
      </Card>
    </Container>
  );
}
