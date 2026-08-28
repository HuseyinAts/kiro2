/**
 * ErrorClusterCard — F15: Hata Kümeleme Önerileri
 *
 * Shows collaborative filtering recommendations after quiz:
 * "Students who made similar mistakes improved by studying X topic"
 */
import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Stack,
  Skeleton,
  Button,
} from '@mui/material';
import {
  TrendingUp as TrendIcon,
  Group as GroupIcon,
  ArrowForward as ArrowIcon,
} from '@mui/icons-material';

interface PeerRecommendation {
  cluster_id: string;
  source_topic: string;
  target_topic: string;
  improvement_rate: number;
  sample_size: number;
  error_pattern: string;
}

interface ErrorClusterCardProps {
  /** Subject filter */
  subject: string;
  /** Topic filter (optional, narrows results) */
  topicId?: string;
  /** Called when user clicks a recommendation */
  onNavigateToTopic?: (topic: string) => void;
}

export function ErrorClusterCard({ subject, topicId, onNavigateToTopic }: ErrorClusterCardProps) {
  const [recommendations, setRecommendations] = useState<PeerRecommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const url = topicId
          ? `/api/v1/error-clusters/${subject}/${topicId}`
          : `/api/v1/error-clusters/my-patterns/${subject}`;
        const res = await fetch(url, { credentials: 'include' });
        if (res.ok) {
          const data = await res.json();
          // Extract recommendations from clusters or use direct recommendations
          const recs = data.recommendations || data.clusters?.flatMap((c: any) => c.recommendations || []) || [];
          setRecommendations(recs.slice(0, 3)); // Show top 3
        }
      } catch {
        // Silently fail — this is an optional enhancement
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [subject, topicId]);

  if (loading) {
    return (
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="rectangular" height={60} sx={{ mt: 1, borderRadius: 1 }} />
        </CardContent>
      </Card>
    );
  }

  if (recommendations.length === 0) {return null;}

  return (
    <Card variant="outlined" sx={{ mb: 2, borderColor: 'info.light' }}>
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1.5 }}>
          <GroupIcon sx={{ color: 'info.main', fontSize: 20 }} />
          <Typography variant="subtitle2" fontWeight={700} color="info.dark">
            Benzer Öğrenciler Ne Yaptı?
          </Typography>
        </Stack>

        <Stack spacing={1}>
          {recommendations.map((rec, idx) => (
            <Box
              key={idx}
              sx={{
                p: 1.5,
                bgcolor: 'info.50',
                borderRadius: 1.5,
                border: '1px solid',
                borderColor: 'info.100',
              }}
            >
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 0.5 }}>
                <TrendIcon sx={{ color: 'success.main', fontSize: 18 }} />
                <Typography variant="body2" fontWeight={600}>
                  %{Math.round(rec.improvement_rate * 100)} iyileşme
                </Typography>
                <Chip
                  label={`${rec.sample_size} öğrenci`}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: 11 }}
                />
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Bu hatayı yapan öğrencilerin %{Math.round(rec.improvement_rate * 100)}'i{' '}
                <strong>{rec.target_topic}</strong> konusunu çalışarak iyileşti.
              </Typography>
              {onNavigateToTopic && (
                <Button
                  size="small"
                  endIcon={<ArrowIcon />}
                  onClick={() => onNavigateToTopic(rec.target_topic)}
                  sx={{ mt: 0.5, textTransform: 'none' }}
                >
                  Konuya Git
                </Button>
              )}
            </Box>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
