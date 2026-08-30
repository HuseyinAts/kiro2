import * as React from 'react';
import { Box, Typography, useTheme, alpha, Paper } from '@mui/material';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface HeatmapData {
  topic: string;
  topicIndex: number;
  misconception: string;
  misconceptionIndex: number;
  studentCount: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

const mockData: HeatmapData[] = [
  { topic: 'Matematik', topicIndex: 1, misconception: 'İşlem Önceliği', misconceptionIndex: 1, studentCount: 14, severity: 'critical' },
  { topic: 'Matematik', topicIndex: 1, misconception: 'Kesirlerde Bölme', misconceptionIndex: 2, studentCount: 8, severity: 'medium' },
  { topic: 'Fizik', topicIndex: 2, misconception: 'Kuvvet ve Hareket', misconceptionIndex: 1, studentCount: 11, severity: 'high' },
  { topic: 'Fizik', topicIndex: 2, misconception: 'Vektörler', misconceptionIndex: 2, studentCount: 4, severity: 'low' },
  { topic: 'Biyoloji', topicIndex: 3, misconception: 'ATP Sentezi A Çeldiricisi', misconceptionIndex: 1, studentCount: 18, severity: 'critical' },
  { topic: 'Biyoloji', topicIndex: 3, misconception: 'Kalıtım Olasılıkları', misconceptionIndex: 2, studentCount: 6, severity: 'low' },
  { topic: 'Tarih', topicIndex: 4, misconception: 'Kronoloji Sıralaması', misconceptionIndex: 1, studentCount: 12, severity: 'high' },
  { topic: 'Kimya', topicIndex: 5, misconception: 'Mol Kavramı (C şıkkı)', misconceptionIndex: 1, studentCount: 9, severity: 'medium' },
];

const topics = ['', 'Matematik', 'Fizik', 'Biyoloji', 'Tarih', 'Kimya', ''];

export const TeacherMisconceptionHeatmap: React.FC = () => {
  const theme = useTheme();

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return theme.palette.error.main;
      case 'high':
        return theme.palette.warning.main;
      case 'medium':
        return theme.palette.info.main;
      case 'low':
        return theme.palette.success.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as HeatmapData;
      const color = getSeverityColor(data.severity);
      return (
        <Paper
          elevation={4}
          sx={{
            p: 2,
            borderRadius: 2,
            border: `1px solid ${alpha(color, 0.3)}`,
            background: `linear-gradient(135deg, ${alpha(color, 0.05)} 0%, ${alpha(
              theme.palette.background.paper,
              0.95,
            )} 100%)`,
            backdropFilter: 'blur(10px)',
          }}
        >
          <Typography variant="subtitle2" color="text.secondary" fontWeight="bold">
            {data.topic}
          </Typography>
          <Typography variant="body1" fontWeight="bold" sx={{ mb: 1 }}>
            {data.misconception}
          </Typography>
          <Typography variant="h6" color={color} fontWeight="900">
            {data.studentCount} <Typography component="span" variant="caption" color="text.primary">Öğrenci</Typography>
          </Typography>
        </Paper>
      );
    }
    return null;
  };

  return (
    <Box sx={{ p: 1, height: '100%' }}>
      <Box display="flex" alignItems="center" gap={1} mb={1}>
        <WarningAmberIcon color="warning" />
        <Typography variant="h6" fontWeight="bold">
          Sınıf Kavram Yanılgısı (Heatmap)
        </Typography>
      </Box>

      <Typography variant="body2" color="text.secondary" mb={2}>
        BKT motoru tarafından tespit edilen çeldirici yoğunluk haritası.
      </Typography>

      <Box sx={{ width: '100%', height: 350 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
            <XAxis
              type="number"
              dataKey="topicIndex"
              name="Ders"
              domain={[0, 6]}
              tickFormatter={(val) => topics[val] || ''}
              stroke={theme.palette.text.secondary}
              tick={{ fill: theme.palette.text.secondary }}
            />
            <YAxis
              type="number"
              dataKey="misconceptionIndex"
              name="Yanılgı"
              domain={[0, 3]}
              tick={false}
              stroke={theme.palette.text.secondary}
              axisLine={false}
            />
            <ZAxis type="number" dataKey="studentCount" range={[100, 1500]} name="Öğrenci Sayısı" />
            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3', stroke: theme.palette.divider }} />
            <Scatter data={mockData} shape="circle">
              {mockData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getSeverityColor(entry.severity)} opacity={0.8} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </Box>
    </Box>
  );
};
