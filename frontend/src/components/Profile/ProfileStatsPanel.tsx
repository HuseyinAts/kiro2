import React from 'react';
import { Box, Typography, Grid } from '@mui/material';
import { motion } from 'framer-motion';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from 'recharts';
import { AutoGraph, Psychology } from '@mui/icons-material';

import { GlassCard } from '../ui/GlassCard';
import modernColors from '../../theme/modern-colors';

// Mock Data for IRT 3PL Ability (Theta)
const irData = [
  { subject: 'Matematik', ability: 85, fullMark: 100 },
  { subject: 'Fizik', ability: 65, fullMark: 100 },
  { subject: 'Kimya', ability: 75, fullMark: 100 },
  { subject: 'Biyoloji', ability: 90, fullMark: 100 },
  { subject: 'Türkçe', ability: 80, fullMark: 100 },
];

// Mock Data for FSRS-6 Memory Retention
const fsrsData = [
  { day: 'Pzt', retention: 95, target: 85 },
  { day: 'Sal', retention: 92, target: 85 },
  { day: 'Çar', retention: 88, target: 85 },
  { day: 'Per', retention: 94, target: 85 },
  { day: 'Cum', retention: 97, target: 85 },
  { day: 'Cts', retention: 99, target: 85 },
  { day: 'Paz', retention: 96, target: 85 },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } },
};

export const ProfileStatsPanel: React.FC = () => {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* IRT Radar Chart */}
        <Grid item xs={12} md={4}>
          <motion.div variants={itemVariants} style={{ height: '100%' }}>
            <GlassCard glassIntensity="medium" elevated sx={{ height: '100%', p: 3, display: 'flex', flexDirection: 'column' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
                <AutoGraph sx={{ color: modernColors.primary[500] }} />
                <Typography variant="h6" fontWeight={800} sx={{ color: 'white' }}>
                  IRT 3PL Yetenek Matrisi
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Gelişmiş Madde Tepki Kuramı ile hesaplanmış branş bazlı akademik yetenek (Theta) dağılımınız.
              </Typography>
              <Box sx={{ flexGrow: 1, minHeight: 250, position: 'relative' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="70%" data={irData}>
                    <PolarGrid stroke="rgba(255,255,255,0.1)" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 12, fontWeight: 600 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                    <Radar
                      name="Yetenek"
                      dataKey="ability"
                      stroke={modernColors.primary[400]}
                      fill={modernColors.primary[500]}
                      fillOpacity={0.5}
                    />
                    <RechartsTooltip 
                      contentStyle={{ backgroundColor: 'rgba(15,23,42,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#fff' }}
                      itemStyle={{ color: modernColors.primary[400], fontWeight: 'bold' }}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </Box>
            </GlassCard>
          </motion.div>
        </Grid>

        {/* FSRS-6 Area Chart */}
        <Grid item xs={12} md={8}>
          <motion.div variants={itemVariants} style={{ height: '100%' }}>
            <GlassCard glassIntensity="medium" elevated gradient={modernColors.gradients.ocean} sx={{ height: '100%', p: 3, display: 'flex', flexDirection: 'column' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
                <Psychology sx={{ color: 'white' }} />
                <Typography variant="h6" fontWeight={800} sx={{ color: 'white' }}>
                  FSRS-6 Hafıza Koruma Analizi
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ mb: 3, color: 'rgba(255,255,255,0.8)' }}>
                Aralıklı tekrar (Spaced Repetition) motorumuzun son 7 günlük kalıcı öğrenme endeksi.
              </Typography>
              <Box sx={{ flexGrow: 1, minHeight: 250 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={fsrsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorRetention" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#22c55e" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                    <XAxis dataKey="day" stroke="rgba(255,255,255,0.5)" tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 12 }} axisLine={false} tickLine={false} domain={[60, 100]} />
                    <RechartsTooltip 
                      contentStyle={{ backgroundColor: 'rgba(15,23,42,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                      itemStyle={{ fontWeight: 'bold' }}
                    />
                    <Area type="monotone" dataKey="target" stroke="rgba(255,255,255,0.3)" fill="none" strokeDasharray="5 5" name="Hedef" />
                    <Area type="monotone" dataKey="retention" stroke="#4ade80" fillOpacity={1} fill="url(#colorRetention)" name="Kalıcılık (%)" activeDot={{ r: 6, fill: '#fff', stroke: '#22c55e', strokeWidth: 2 }} />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </GlassCard>
          </motion.div>
        </Grid>
      </Grid>
    </motion.div>
  );
};
