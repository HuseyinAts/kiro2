/**
 * DailyPlanPage — Günlük Çalışma Planı
 * ZPD + DAG + IRT + FSRS algoritmasıyla üretilen kişisel plan
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

const API = '/api/v1/learning-path';

interface StudyBlock {
  subject: string;
  topic_name: string;
  activity_type: string;
  duration_minutes: number;
  question_count: number;
  difficulty_band: string;
  reason: string;
  priority: number;
}

interface DailyPlan {
  plan_date: string;
  exam_date: string;
  days_remaining: number;
  total_minutes: number;
  blocks: StudyBlock[];
  fsrs_review_count: number;
  new_topic_count: number;
  weak_subject: string | null;
  strong_subject: string | null;
  motivational_note: string;
}

interface SubjectStatus {
  subject: string;
  theta: number;
  mastery_pct: number;
  fsrs_due_count: number;
  zpd_lower: number;
  zpd_upper: number;
  priority_score: number;
  level_label: string;
}

const SUBJECT_TR: Record<string, string> = {
  MATEMATIK: 'Matematik', TURKCE: 'Türkçe', FIZIK: 'Fizik',
  KIMYA: 'Kimya', BIYOLOJI: 'Biyoloji', GEOMETRI: 'Geometri',
  TARIH: 'Tarih', COGRAFYA: 'Coğrafya', SOSYAL: 'Sosyal Bilimler',
  EDEBIYAT: 'Edebiyat', FEN: 'Fen Bilimleri', GENEL: 'Genel Kültür',
};

const ACTIVITY_ICON: Record<string, string> = {
  cat: '🎯', fsrs_review: '🔄', practice: '💪', placement: '📊',
};

const DIFFICULTY_COLOR: Record<string, string> = {
  easy: '#10b981', medium: '#f59e0b', hard: '#ef4444', mixed: '#8b5cf6',
};

const LEVEL_COLOR: Record<string, string> = {
  'Temel': '#ef4444', 'Başlangıç': '#f97316', 'Orta': '#f59e0b',
  'İleri': '#10b981', 'Uzman': '#6366f1',
};

export default function DailyPlanPage() {
  const navigate = useNavigate();
  const [plan, setPlan] = useState<DailyPlan | null>(null);
  const [statuses, setStatuses] = useState<SubjectStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'plan' | 'status'>('plan');

  const fetchPlan = useCallback(() => {
    setLoading(true);
    setError('');
    Promise.all([
      fetch(`${API}/today`, { credentials: 'include' }).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }),
      fetch(`${API}/status`, { credentials: 'include' }).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }),
    ])
      .then(([planData, statusData]) => {
        if (planData.detail) setError(planData.detail);
        else setPlan(planData);
        if (Array.isArray(statusData)) setStatuses(statusData);
      })
      .catch(() => setError('Sunucuya bağlanılamadı.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchPlan(); }, [fetchPlan]);

  useEffect(() => {
    const handler = () => fetchPlan();
    window.addEventListener('cat-complete', handler);
    return () => window.removeEventListener('cat-complete', handler);
  }, [fetchPlan]);

  const startActivity = (block: StudyBlock) => {
    if (block.activity_type === 'cat') navigate('/cat');
    else if (block.activity_type === 'fsrs_review') navigate('/fsrs-review');
    else navigate('/cat');
  };

  if (loading) return (
    <div style={styles.center}>
      <div style={styles.spinner} />
      <p style={{ color: '#94a3b8', marginTop: 16 }}>Plan hazırlanıyor…</p>
    </div>
  );

  return (
    <div style={styles.page}>
      {/* Header */}
      <div style={styles.header}>
        <button onClick={() => navigate('/dashboard')} style={styles.backBtn}>← Geri</button>
        <div>
          <h1 style={styles.title}>📅 Bugünkü Planım</h1>
          {plan && (
            <p style={styles.subtitle}>
              Sınava <strong style={{ color: '#f59e0b' }}>{plan.days_remaining} gün</strong> kaldı •{' '}
              {new Date(plan.plan_date).toLocaleDateString('tr-TR', { weekday: 'long', day: 'numeric', month: 'long' })}
            </p>
          )}
        </div>
        <button onClick={() => navigate('/learning-path-map')} style={styles.mapBtn}>
          🗺️ Konu Haritası
        </button>
      </div>

      {error && <div style={styles.error}>{error}</div>}

      {/* Tab Switcher */}
      <div style={styles.tabs}>
        {(['plan', 'status'] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            style={{ ...styles.tab, ...(activeTab === tab ? styles.tabActive : {}) }}>
            {tab === 'plan' ? '📋 Günlük Plan' : '📊 Ders Durumları'}
          </button>
        ))}
      </div>

      {/* Plan Tab */}
      {activeTab === 'plan' && plan && (
        <div>
          {/* Motivasyon & Özet */}
          <div style={styles.motivCard}>
            <p style={styles.motivText}>{plan.motivational_note}</p>
            <div style={styles.statsRow}>
              <span style={styles.statChip}>⏱ {plan.total_minutes} dk</span>
              <span style={styles.statChip}>🔄 {plan.fsrs_review_count} tekrar</span>
              <span style={styles.statChip}>📚 {plan.new_topic_count} yeni konu</span>
              {plan.weak_subject && <span style={{ ...styles.statChip, background: '#fee2e2', color: '#dc2626' }}>⚠️ Zayıf: {SUBJECT_TR[plan.weak_subject] ?? plan.weak_subject}</span>}
              {plan.strong_subject && <span style={{ ...styles.statChip, background: '#d1fae5', color: '#059669' }}>✅ Güçlü: {SUBJECT_TR[plan.strong_subject] ?? plan.strong_subject}</span>}
            </div>
          </div>

          {/* Çalışma Blokları */}
          <div style={styles.blockList}>
            {plan.blocks.length === 0 && (
              <div style={styles.emptyState}>🎉 Bugün için tüm görevler tamamlandı!</div>
            )}
            {plan.blocks.map((block, i) => (
              <div key={i} style={styles.block}>
                <div style={styles.blockLeft}>
                  <span style={styles.blockIcon}>{ACTIVITY_ICON[block.activity_type] ?? '📖'}</span>
                  <div style={styles.blockPriority(block.priority)} />
                </div>
                <div style={styles.blockBody}>
                  <div style={styles.blockHeader}>
                    <span style={styles.blockSubject}>{SUBJECT_TR[block.subject] ?? block.subject}</span>
                    <span style={{ ...styles.diffBadge, background: DIFFICULTY_COLOR[block.difficulty_band] + '22', color: DIFFICULTY_COLOR[block.difficulty_band] }}>
                      {block.difficulty_band}
                    </span>
                  </div>
                  <p style={styles.blockTopic}>{block.topic_name}</p>
                  <p style={styles.blockReason}>💡 {block.reason}</p>
                  <div style={styles.blockFooter}>
                    <span style={styles.blockMeta}>⏱ {block.duration_minutes} dk</span>
                    <span style={styles.blockMeta}>❓ {block.question_count} soru</span>
                    <button onClick={() => startActivity(block)} style={styles.startBtn}>
                      Başla →
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Status Tab */}
      {activeTab === 'status' && (
        <div style={styles.statusGrid}>
          {statuses.map(s => (
            <div key={s.subject} style={styles.statusCard}>
              <div style={styles.statusHeader}>
                <span style={styles.statusSubject}>{SUBJECT_TR[s.subject] ?? s.subject}</span>
                <span style={{ ...styles.levelBadge, background: (LEVEL_COLOR[s.level_label] ?? '#6b7280') + '22', color: LEVEL_COLOR[s.level_label] ?? '#6b7280' }}>
                  {s.level_label}
                </span>
              </div>
              {/* Mastery bar */}
              <div style={styles.barBg}>
                <div style={{ ...styles.barFill, width: `${s.mastery_pct}%` }} />
              </div>
              <div style={styles.statusMeta}>
                <span>θ = {s.theta.toFixed(2)}</span>
                <span>{s.mastery_pct.toFixed(0)}% mastery</span>
                {s.fsrs_due_count > 0 && <span style={{ color: '#f59e0b' }}>🔄 {s.fsrs_due_count}</span>}
              </div>
              <div style={styles.statusZpd}>
                ZPD [{s.zpd_lower.toFixed(1)} – {s.zpd_upper.toFixed(1)}]
              </div>
            </div>
          ))}
          {statuses.length === 0 && (
            <div style={styles.emptyState}>Henüz CAT testi tamamlanmamış. Placement testini başlatın.</div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Stiller ──────────────────────────────────────────────────────────────────
const styles: Record<string, any> = {
  page: { minHeight: '100vh', background: '#0f172a', color: '#f8fafc', padding: '24px 16px', fontFamily: "'Inter', sans-serif" },
  center: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' },
  spinner: { width: 40, height: 40, border: '3px solid #334155', borderTop: '3px solid #6366f1', borderRadius: '50%', animation: 'spin 1s linear infinite' },
  header: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 },
  backBtn: { background: '#1e293b', border: '1px solid #334155', color: '#94a3b8', padding: '8px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 14 },
  mapBtn: { background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', border: 'none', color: '#fff', padding: '8px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 14, fontWeight: 600 },
  title: { margin: 0, fontSize: 22, fontWeight: 700, color: '#f8fafc' },
  subtitle: { margin: '4px 0 0', fontSize: 14, color: '#94a3b8' },
  error: { background: '#450a0a', border: '1px solid #dc2626', color: '#fca5a5', padding: 12, borderRadius: 8, marginBottom: 16 },
  tabs: { display: 'flex', gap: 8, marginBottom: 20 },
  tab: { flex: 1, padding: '10px 16px', border: '1px solid #334155', background: '#1e293b', color: '#94a3b8', borderRadius: 8, cursor: 'pointer', fontSize: 14, fontWeight: 500 },
  tabActive: { background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', borderColor: '#6366f1', color: '#fff' },
  motivCard: { background: 'linear-gradient(135deg,#1e1b4b,#2e1065)', border: '1px solid #4338ca', borderRadius: 12, padding: 20, marginBottom: 20 },
  motivText: { margin: '0 0 12px', fontSize: 15, color: '#c7d2fe', fontWeight: 500, lineHeight: 1.5 },
  statsRow: { display: 'flex', gap: 8, flexWrap: 'wrap' },
  statChip: { background: '#312e81', color: '#a5b4fc', padding: '4px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600 },
  blockList: { display: 'flex', flexDirection: 'column', gap: 12 },
  block: { background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 16, display: 'flex', gap: 12 },
  blockLeft: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, minWidth: 36 },
  blockIcon: { fontSize: 24 },
  blockPriority: (p: number) => ({ width: 4, flex: 1, borderRadius: 2, background: p === 1 ? '#ef4444' : p === 2 ? '#f59e0b' : '#10b981' }),
  blockBody: { flex: 1 },
  blockHeader: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 },
  blockSubject: { fontWeight: 700, fontSize: 15, color: '#f8fafc' },
  diffBadge: { padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 600 },
  blockTopic: { margin: '0 0 4px', fontSize: 13, color: '#cbd5e1' },
  blockReason: { margin: '0 0 10px', fontSize: 12, color: '#64748b', fontStyle: 'italic' },
  blockFooter: { display: 'flex', alignItems: 'center', gap: 10 },
  blockMeta: { fontSize: 12, color: '#64748b' },
  startBtn: { marginLeft: 'auto', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', border: 'none', color: '#fff', padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 13, fontWeight: 600 },
  statusGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 },
  statusCard: { background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 16 },
  statusHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  statusSubject: { fontWeight: 700, fontSize: 14, color: '#f8fafc' },
  levelBadge: { padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 700 },
  barBg: { background: '#0f172a', borderRadius: 4, height: 6, marginBottom: 8, overflow: 'hidden' },
  barFill: { height: '100%', background: 'linear-gradient(90deg,#6366f1,#8b5cf6)', borderRadius: 4, transition: 'width 0.5s ease' },
  statusMeta: { display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#64748b', marginBottom: 4 },
  statusZpd: { fontSize: 10, color: '#475569', textAlign: 'center' as const },
  emptyState: { textAlign: 'center' as const, padding: 32, color: '#64748b', fontSize: 14 },
};
