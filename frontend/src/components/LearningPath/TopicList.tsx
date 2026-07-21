/**
 * TopicList — Sade konu listesi (DungeonMap yerine)
 *
 * Öğrenme yolu konu haritası. Dungeon/parşömen + fog-of-war teması yerine
 * okunabilir kart grid'i: kilit durumu, ilerleme, soru sayısı.
 * Yeni kullanıcıda (θ=0) "hep sis" sorunu yok — her konu net görünür.
 * Veri: useDungeonMap (GET /api/v1/dungeon/{subject}).
 */
import React, { useMemo } from 'react';
import {
  Box,
  Card,
  CardActionArea,
  Chip,
  CircularProgress,
  LinearProgress,
  Tooltip,
  Typography,
} from '@mui/material';
import { LockOutlined, CheckCircle, PlayArrow } from '@mui/icons-material';
import { useDungeonMap, type LayoutNode } from '@/hooks/useDungeonMap';

interface TopicListProps {
  subject: string;
  onNodeClick?: (node: LayoutNode) => void;
}

export const TopicList: React.FC<TopicListProps> = ({ subject, onNodeClick }) => {
  const { nodes, loading, error } = useDungeonMap(subject);

  const sorted = useMemo(
    () =>
      [...nodes].sort((a, b) => {
        // Açık konular önce
        if (a.prereqs_met !== b.prereqs_met) {return a.prereqs_met ? -1 : 1;}
        // Sonra DAG derinliği
        if (a.dag_depth !== b.dag_depth) {return a.dag_depth - b.dag_depth;}
        return a.name_tr.localeCompare(b.name_tr, 'tr');
      }),
    [nodes],
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (nodes.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography color="text.secondary">Bu ders için henüz konu bulunamadı.</Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr' },
        gap: 2,
      }}
    >
      {sorted.map((node) => {
        const locked = !node.prereqs_met;
        const completed = node.progress.completed;
        const inProgress = !completed && node.progress.attempt_count > 0;
        const best = Math.min(100, Math.max(0, node.progress.best_score));

        const card = (
          <Card
            variant="outlined"
            sx={{
              height: '100%',
              borderRadius: 2,
              opacity: locked ? 0.65 : 1,
              borderColor: completed
                ? 'success.main'
                : locked
                  ? 'divider'
                  : 'primary.light',
              transition: 'box-shadow .2s, transform .2s',
              '&:hover': locked ? {} : { boxShadow: 4, transform: 'translateY(-2px)' },
            }}
          >
            <CardActionArea
              disabled={locked}
              onClick={() => !locked && onNodeClick?.(node)}
              sx={{ p: 2, height: '100%', display: 'block' }}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  justifyContent: 'space-between',
                  gap: 1,
                  mb: 1,
                }}
              >
                <Typography variant="subtitle1" fontWeight={700} sx={{ lineHeight: 1.3 }}>
                  {node.name_tr}
                </Typography>
                {completed ? (
                  <CheckCircle color="success" fontSize="small" />
                ) : locked ? (
                  <LockOutlined fontSize="small" sx={{ color: 'text.disabled' }} />
                ) : (
                  <PlayArrow color="primary" fontSize="small" />
                )}
              </Box>

              <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap', mb: inProgress ? 1 : 0 }}>
                <Chip size="small" variant="outlined" label={`${node.question_count} soru`} />
                {completed && <Chip size="small" color="success" label="Tamamlandı" />}
                {locked && <Chip size="small" variant="outlined" label="Kilitli" />}
                {inProgress && (
                  <Chip size="small" color="primary" variant="outlined" label={`%${Math.round(best)}`} />
                )}
              </Box>

              {inProgress && (
                <LinearProgress
                  variant="determinate"
                  value={best}
                  sx={{ height: 6, borderRadius: 3 }}
                />
              )}
            </CardActionArea>
          </Card>
        );

        return locked ? (
          <Tooltip key={node.topic_id} title="Önce ön-koşul konuları tamamla">
            <span style={{ display: 'block', height: '100%' }}>{card}</span>
          </Tooltip>
        ) : (
          <React.Fragment key={node.topic_id}>{card}</React.Fragment>
        );
      })}
    </Box>
  );
};
