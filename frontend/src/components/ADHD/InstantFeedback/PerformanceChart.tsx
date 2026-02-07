/**
 * Task 92.4: Performance Chart Component
 * Başarı grafiği ve ilerleme görselleştirmesi
 */
import type { FC } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Line } from 'recharts';
import './PerformanceChart.css';

interface PerformanceDataPoint {
  time: string;
  score: number;
  streak: number;
  average: number;
}

interface PerformanceChartProps {
  data: PerformanceDataPoint[];
  showTrend?: boolean;
  showAverage?: boolean;
  height?: number;
  compact?: boolean;
}

export const PerformanceChart: FC<PerformanceChartProps> = ({
  data,
  showTrend: _showTrend = true,
  showAverage = true,
  height = 300,
  compact = false,
}) => {
  if (data.length === 0) {
    return (
      <div className="performance-chart empty">
        <div className="empty-state">
          <span className="empty-icon">📊</span>
          <p className="empty-message">Henüz performans verisi yok</p>
          <p className="empty-hint">Sorular çözmeye başladığında grafiğin burada görünecek!</p>
        </div>
      </div>
    );
  }

  const latestScore = data[data.length - 1]?.score || 0;
  const averageScore = data.reduce((sum, d) => sum + d.score, 0) / data.length;
  const trend = latestScore > averageScore ? 'up' : latestScore < averageScore ? 'down' : 'stable';

  return (
    <div className={`performance-chart ${compact ? 'compact' : ''}`}>
      {!compact && (
        <div className="chart-header">
          <h3>Performans Grafiği</h3>
          <div className="chart-stats">
            <div className="stat">
              <span className="stat-label">Son Skor:</span>
              <span className="stat-value">{latestScore}%</span>
            </div>
            <div className="stat">
              <span className="stat-label">Ortalama:</span>
              <span className="stat-value">{averageScore.toFixed(1)}%</span>
            </div>
            <div className="stat">
              <span className="stat-label">Trend:</span>
              <span className={`stat-trend trend-${trend}`}>
                {trend === 'up' && '📈 Yükseliyor'}
                {trend === 'down' && '📉 Düşüyor'}
                {trend === 'stable' && '➡️ Stabil'}
              </span>
            </div>
          </div>
        </div>
      )}

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#667eea" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#667eea" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="time" stroke="#9ca3af" style={{ fontSize: '12px' }} />
            <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} domain={[0, 100]} />
            <Tooltip content={<CustomTooltip />} />
            {!compact && <Legend />}
            <Area
              type="monotone"
              dataKey="score"
              stroke="#667eea"
              strokeWidth={3}
              fill="url(#scoreGradient)"
              name="Skor"
            />
            {showAverage && (
              <Line
                type="monotone"
                dataKey="average"
                stroke="#f59e0b"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                name="Ortalama"
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <p className="tooltip-time">{payload[0].payload.time}</p>
        <p className="tooltip-score">Skor: <strong>{payload[0].value}%</strong></p>
        {payload[0].payload.streak > 0 && (
          <p className="tooltip-streak">🔥 Seri: {payload[0].payload.streak}</p>
        )}
      </div>
    );
  }
  return null;
};

export default PerformanceChart;
