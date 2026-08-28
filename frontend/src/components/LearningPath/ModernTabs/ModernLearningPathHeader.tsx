import React, { useState, useEffect } from 'react';
import { Box, Typography, Alert, Chip } from '@mui/material';
import { Map, Warning, LocalFireDepartment, AutoAwesome, PlayArrow, Stop, Refresh, Timer } from '@mui/icons-material';
import { motion } from 'framer-motion';

import { GlassCard } from '@/components/ui/GlassCard';
import { ModernButton } from '@/components/ui/ModernButton';
import { LeaguePanel } from '@/components/LearningPath/LeaguePanel';
import { AccessibilitySettings } from '@/components/LearningPath/AccessibilitySettings';
import modernColors from '@/theme/modern-colors';

import type { UseLearningPathReturn } from '@/hooks/useLearningPath';

interface Props {
  learningPath: UseLearningPathReturn;
}

export const ModernLearningPathHeader: React.FC<Props> = ({ learningPath }) => {
  const { streak, error, learningStyle, reload, studySession, startSession, endSession } = learningPath;

  const [elapsedMinutes, setElapsedMinutes] = useState(0);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (studySession?.isActive && studySession.startedAt) {
      const updateElapsed = () => {
        const diffMs = Date.now() - new Date(studySession.startedAt!).getTime();
        setElapsedMinutes(Math.floor(diffMs / 60000));
      };
      updateElapsed();
      interval = setInterval(updateElapsed, 60000);
    } else {
      setElapsedMinutes(0);
    }
    return () => clearInterval(interval);
  }, [studySession?.isActive, studySession?.startedAt]);

  return (
    <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2, flexWrap: 'wrap', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ width: 56, height: 56, borderRadius: 3, background: modernColors.gradients.primary, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Map sx={{ fontSize: 32, color: 'white' }} />
            </Box>
            <Box>
              <Typography variant="h3" sx={{ fontWeight: 900, background: modernColors.gradients.primary, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Öğrenme Yolunuz
              </Typography>
              <Typography variant="body1" color="text.secondary">Kişiselleştirilmiş öğrenme yolunuz ve size özel kaynaklar</Typography>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
            <LeaguePanel compact />

            {streak?.dailyStreak > 0 && (
              <Chip icon={<LocalFireDepartment sx={{ color: '#f97316' }} />} label={`${streak.dailyStreak} gün`} variant="outlined" sx={{ fontWeight: 700, borderColor: '#f97316', color: '#f97316' }} />
            )}

            {studySession?.isActive ? (
              <ModernButton variant="gradient" gradient="linear-gradient(135deg, #ef4444, #dc2626)" icon={<Stop />} onClick={endSession}>
                <Timer sx={{ fontSize: 16, mr: 0.5 }} /> {elapsedMinutes} dk — Bitir
              </ModernButton>
            ) : (
              <ModernButton variant="gradient" gradient={modernColors.gradients.success} icon={<PlayArrow />} onClick={startSession}>Oturum Başlat</ModernButton>
            )}

            <AccessibilitySettings />
            <ModernButton variant="glass" icon={<Refresh />} onClick={reload}>Yenile</ModernButton>
          </Box>
        </Box>

        {learningStyle && (
          <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.sunset} sx={{ display: 'inline-block' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AutoAwesome sx={{ fontSize: 20 }} />
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                İçerik Tercihiniz: {
                  { visual: 'Görsel Öğrenen', auditory: 'İşitsel Öğrenen', reading: 'Okuma-Yazma Öğrenen', kinesthetic: 'Uygulamalı Öğrenen', mixed: 'Karma Öğrenen' }[learningStyle] || learningStyle
                }
              </Typography>
            </Box>
          </GlassCard>
        )}

        {error && <Alert severity="error" icon={<Warning />} sx={{ mt: 3, borderRadius: 2 }}>{error}</Alert>}
      </Box>
    </motion.div>
  );
};
