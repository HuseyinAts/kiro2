import React from 'react';
import styles from './ExamSession.module.css';
import { ExamSubmitResult } from '../../services/mockExamService';

interface ExamResultDashboardProps {
  results?: ExamSubmitResult | null;
  onRestart?: () => void;
}

export const ExamResultDashboard: React.FC<ExamResultDashboardProps> = ({ results, onRestart }) => {
  const totalCorrect = results ? results.total_correct : 95;
  const totalWrong = results ? results.total_wrong : 15;
  const totalEmpty = results ? results.total_empty : 10;
  const rawScore = results ? results.raw_score : 87.50;

  const branchData = results?.branch_breakdown ? [
    { name: 'TÜRKÇE', d: results.branch_breakdown.TUR?.correct ?? 0, y: results.branch_breakdown.TUR?.wrong ?? 0, b: results.branch_breakdown.TUR?.empty ?? 0, net: results.branch_breakdown.TUR?.net ?? 0 },
    { name: 'SOSYAL BİL.', d: results.branch_breakdown.SOS?.correct ?? 0, y: results.branch_breakdown.SOS?.wrong ?? 0, b: results.branch_breakdown.SOS?.empty ?? 0, net: results.branch_breakdown.SOS?.net ?? 0 },
    { name: 'MATEMATİK', d: results.branch_breakdown.MAT?.correct ?? 0, y: results.branch_breakdown.MAT?.wrong ?? 0, b: results.branch_breakdown.MAT?.empty ?? 0, net: results.branch_breakdown.MAT?.net ?? 0 },
    { name: 'FEN BİL.', d: results.branch_breakdown.FEN?.correct ?? 0, y: results.branch_breakdown.FEN?.wrong ?? 0, b: results.branch_breakdown.FEN?.empty ?? 0, net: results.branch_breakdown.FEN?.net ?? 0 },
  ] : [
    { name: 'TÜRKÇE', d: 32, y: 5, b: 3, net: 30.75 },
    { name: 'SOSYAL BİL.', d: 15, y: 3, b: 2, net: 14.25 },
    { name: 'MATEMATİK', d: 30, y: 4, b: 6, net: 29.00 },
    { name: 'FEN BİL.', d: 18, y: 3, b: 0, net: 17.25 }
  ];

  return (
    <div className={styles.container} style={{ flexDirection: 'column', overflowY: 'auto' }}>
      <header className={styles.header} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', justifyContent: 'space-between' }}>
        <div>
          <h1 className={styles.sidebarTitle} style={{ fontSize: '2rem' }}>Sınav Sonucu</h1>
          <div style={{ color: '#94a3b8' }}>TYT Deneme Sınavı</div>
        </div>
        {onRestart && (
          <button className={styles.finishBtn} onClick={onRestart}>
            Yeni Sınav Başlat
          </button>
        )}
      </header>

      <div style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
        {/* Top Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '40px' }}>
          {[
            { label: 'Toplam Net', value: rawScore.toFixed(2), color: '#3b82f6' },
            { label: 'Doğru', value: totalCorrect.toString(), color: '#10b981' },
            { label: 'Yanlış', value: totalWrong.toString(), color: '#ef4444' },
            { label: 'Boş', value: totalEmpty.toString(), color: '#94a3b8' }
          ].map((stat, i) => (
            <div key={i} style={{
              background: 'rgba(255,255,255,0.03)',
              borderRadius: '16px',
              padding: '24px',
              border: '1px solid rgba(255,255,255,0.05)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '3rem', fontWeight: '700', color: stat.color, marginBottom: '8px' }}>
                {stat.value}
              </div>
              <div style={{ color: '#cbd5e1', fontSize: '1.125rem', fontWeight: '500' }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        {/* Branch Breakdown */}
        <div style={{
          background: 'rgba(255,255,255,0.02)',
          borderRadius: '16px',
          border: '1px solid rgba(255,255,255,0.05)',
          padding: '32px'
        }}>
          <h2 style={{ fontSize: '1.5rem', color: '#f8fafc', marginBottom: '24px', fontWeight: '600' }}>Branş Analizi</h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {branchData.map((branch) => (
              <div key={branch.name} style={{
                display: 'grid',
                gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr',
                alignItems: 'center',
                padding: '16px',
                background: 'rgba(255,255,255,0.03)',
                borderRadius: '12px',
                borderLeft: '4px solid #3b82f6'
              }}>
                <div style={{ fontWeight: '600', color: '#e2e8f0' }}>{branch.name}</div>
                <div style={{ color: '#10b981' }}>{branch.d} Doğru</div>
                <div style={{ color: '#ef4444' }}>{branch.y} Yanlış</div>
                <div style={{ color: '#94a3b8' }}>{branch.b} Boş</div>
                <div style={{ fontWeight: '700', color: '#3b82f6', textAlign: 'right' }}>{branch.net.toFixed(2)} Net</div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
