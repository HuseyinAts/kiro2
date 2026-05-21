/**
 * ParentDashboardNew — Veli Paneli
 * Çocuğun θ değerleri, YKS tahmini, günlük plan özeti
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const SUBJECT_TR: Record<string, string> = {
  MATEMATIK: 'Matematik', TURKCE: 'Türkçe', FIZIK: 'Fizik',
  KIMYA: 'Kimya', BIYOLOJI: 'Biyoloji', GEOMETRI: 'Geometri',
  TARIH: 'Tarih', COGRAFYA: 'Coğrafya', SOSYAL: 'Sosyal',
  EDEBIYAT: 'Edebiyat', FEN: 'Fen', GENEL: 'Genel Kültür',
};
const LEVEL_COLOR: Record<string, string> = {
  'Temel': '#ef4444', 'Başlangıç': '#f97316',
  'Orta': '#f59e0b', 'İleri': '#10b981', 'Uzman': '#6366f1',
};
const SUBJECT_EMOJI: Record<string, string> = {
  MATEMATIK: '📐', TURKCE: '📖', FIZIK: '⚛️', KIMYA: '🧪',
  BIYOLOJI: '🧬', GEOMETRI: '📏', TARIH: '🏛️', COGRAFYA: '🌍',
  SOSYAL: '🌐', EDEBIYAT: '✍️', FEN: '🔬',
};

interface SubjectStatus {
  subject: string; theta: number; mastery_pct: number;
  fsrs_due_count: number; level_label: string;
}
interface ChildSummary {
  id: string; name: string; email: string;
  statuses: SubjectStatus[]; plan: any; estimate: any;
}

export default function ParentDashboardNew() {
  const navigate = useNavigate();
  const [children, setChildren] = useState<ChildSummary[]>([]);
  const [selected, setSelected] = useState<ChildSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const opts = { credentials: 'include' as RequestCredentials };

    fetch('/api/v1/veli/cocuklar', opts, { credentials: 'include' })
      .then(r => r.ok ? r.json() : [])
      .then(async (data: any[]) => {
        if (!Array.isArray(data) || data.length === 0) {
          setLoading(false); return;
        }
        const enriched: ChildSummary[] = await Promise.all(
          data.map(async (child) => {
            const eRes = await fetch(`/api/v1/veli/cocuk/${child.id}/performans`, opts);
            const estimate = eRes.ok ? await eRes.json() : null;
            return { ...child, statuses: [], plan: null, estimate };
          })
        );
        setChildren(enriched);
        setSelected(enriched[0]);
      })
      .catch(() => setError('Veri alınamadı'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={s.center}><div style={s.spinner} /><p style={s.hint}>Yükleniyor…</p></div>;

  return (
    <div style={s.page}>
      {/* Header */}
      <div style={s.header}>
        <button onClick={() => navigate('/dashboard')} style={s.backBtn}>← Geri</button>
        <div>
          <h1 style={s.title}>👨‍👩‍👧 Veli Paneli</h1>
          <p style={s.hint}>Çocuğunuzun YKS hazırlık durumu</p>
        </div>
      </div>

      {error && <div style={s.errorBox}>{error}</div>}

      {/* Çocuk yoksa */}
      {children.length === 0 && !error && (
        <div style={s.emptyCard}>
          <p style={{ fontSize: 32, marginBottom: 12 }}>👶</p>
          <p style={{ fontWeight: 700, marginBottom: 8 }}>Kayıtlı çocuk hesabı bulunamadı</p>
          <p style={s.hint}>Çocuğunuzun hesabı oluşturulduktan sonra bu panelde görünecektir.</p>
        </div>
      )}

      {/* Çocuk sekmeleri */}
      {children.length > 1 && (
        <div style={s.tabs}>
          {children.map(c => (
            <button key={c.id} onClick={() => setSelected(c)}
              style={{ ...s.tab, ...(selected?.id === c.id ? s.tabActive : {}) }}>
              👤 {c.name}
            </button>
          ))}
        </div>
      )}

      {selected && <ChildDetail child={selected} />}
    </div>
  );
}

// ─── ChildDetail bileşeni ─────────────────────────────────────────────────────
function ChildDetail({ child }: { child: ChildSummary }) {
  const est = child.estimate;
  const plan = child.plan;

  return (
    <div>
      {/* YKS Puan Tahmini */}
      <div style={s.section}>
        <h3 style={s.sectionTitle}>🎯 YKS Puan Tahmini</h3>
        {est && !est.detail ? (
          <div style={s.estimateGrid}>
            {[
              ['Tahmini Puan', est.puan?.toFixed(1)],
              ['Alt Sınır', est.alt_sinir?.toFixed(1)],
              ['Üst Sınır', est.ust_sinir?.toFixed(1)],
              ['Tahmini Sıralama', est.tahmini_siralama?.toLocaleString('tr-TR')],
              ['Yüzdelik', `%${est.yuzdelik?.toFixed(1)}`],
              ['Güvenilirlik', est.guvenilirlik],
            ].map(([lbl, val]) => (
              <div key={lbl as string} style={s.estItem}>
                <span style={s.estLabel}>{lbl}</span>
                <span style={s.estValue}>{val ?? '—'}</span>
              </div>
            ))}
          </div>
        ) : (
          <p style={s.hint}>Henüz yeterli CAT verisi yok. Çocuğunuz adaptif test tamamladıktan sonra görünecek.</p>
        )}
      </div>

      {/* Günlük Plan Özeti */}
      {plan && !plan.detail && (
        <div style={s.section}>
          <h3 style={s.sectionTitle}>📅 Bugünkü Plan</h3>
          <div style={s.planCard}>
            <p style={s.motivText}>{plan.motivational_note}</p>
            <div style={s.planMeta}>
              <span style={s.chip}>📅 {plan.days_remaining} gün kaldı</span>
              <span style={s.chip}>⏱ {plan.total_minutes} dk hedef</span>
              <span style={s.chip}>🔄 {plan.fsrs_review_count} tekrar</span>
              {plan.weak_subject && <span style={{ ...s.chip, background: '#fee2e2', color: '#dc2626' }}>⚠️ Zayıf: {SUBJECT_TR[plan.weak_subject] ?? plan.weak_subject}</span>}
              {plan.strong_subject && <span style={{ ...s.chip, background: '#d1fae5', color: '#059669' }}>✅ Güçlü: {SUBJECT_TR[plan.strong_subject] ?? plan.strong_subject}</span>}
            </div>
          </div>
        </div>
      )}

      {/* Ders Durumları */}
      <div style={s.section}>
        <h3 style={s.sectionTitle}>📊 Ders Seviyeleri</h3>
        {child.statuses.length === 0 ? (
          <p style={s.hint}>Henüz test tamamlanmamış.</p>
        ) : (
          <div style={s.subjectGrid}>
            {child.statuses
              .sort((a, b) => a.mastery_pct - b.mastery_pct)
              .map(st => {
                const color = LEVEL_COLOR[st.level_label] ?? '#6b7280';
                return (
                  <div key={st.subject} style={s.subjectCard}>
                    <div style={s.subjectHeader}>
                      <span style={s.subjectEmoji}>{SUBJECT_EMOJI[st.subject] ?? '📚'}</span>
                      <span style={s.subjectName}>{SUBJECT_TR[st.subject] ?? st.subject}</span>
                      <span style={{ ...s.levelBadge, background: color + '22', color }}>{st.level_label}</span>
                    </div>
                    <div style={s.barBg}>
                      <div style={{ ...s.barFill, width: `${st.mastery_pct}%`, background: color }} />
                    </div>
                    <div style={s.subjectMeta}>
                      <span>θ = {st.theta.toFixed(2)}</span>
                      <span>{st.mastery_pct.toFixed(0)}%</span>
                      {st.fsrs_due_count > 0 && <span style={{ color: '#f59e0b' }}>🔄{st.fsrs_due_count}</span>}
                    </div>
                  </div>
                );
              })}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Stiller ──────────────────────────────────────────────────────────────────
const s: Record<string, any> = {
  page:        { minHeight: '100vh', background: '#0f172a', color: '#f8fafc', padding: '24px 16px', fontFamily: "'Inter',sans-serif" },
  center:      { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' },
  spinner:     { width: 40, height: 40, border: '3px solid #334155', borderTop: '3px solid #6366f1', borderRadius: '50%', animation: 'spin 1s linear infinite' },
  header:      { display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24, flexWrap: 'wrap' as const },
  backBtn:     { background: '#1e293b', border: '1px solid #334155', color: '#94a3b8', padding: '8px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 14 },
  title:       { margin: 0, fontSize: 22, fontWeight: 700, color: '#f8fafc' },
  hint:        { margin: '4px 0 0', fontSize: 13, color: '#64748b' },
  errorBox:    { background: '#450a0a', border: '1px solid #dc2626', color: '#fca5a5', padding: 12, borderRadius: 8, marginBottom: 16 },
  emptyCard:   { background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 32, textAlign: 'center' as const },
  tabs:        { display: 'flex', gap: 8, marginBottom: 20 },
  tab:         { flex: 1, padding: '10px 16px', border: '1px solid #334155', background: '#1e293b', color: '#94a3b8', borderRadius: 8, cursor: 'pointer', fontSize: 14 },
  tabActive:   { background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', borderColor: '#6366f1', color: '#fff' },
  section:     { marginBottom: 24 },
  sectionTitle:{ margin: '0 0 12px', fontSize: 16, fontWeight: 700, color: '#f8fafc' },
  estimateGrid:{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(140px,1fr))', gap: 10 },
  estItem:     { background: '#1e293b', border: '1px solid #334155', borderRadius: 10, padding: 14, display: 'flex', flexDirection: 'column' as const, gap: 4 },
  estLabel:    { fontSize: 11, color: '#64748b' },
  estValue:    { fontSize: 18, fontWeight: 700, color: '#f8fafc' },
  planCard:    { background: 'linear-gradient(135deg,#1e1b4b,#2e1065)', border: '1px solid #4338ca', borderRadius: 12, padding: 16 },
  motivText:   { margin: '0 0 12px', fontSize: 14, color: '#c7d2fe', lineHeight: 1.5 },
  planMeta:    { display: 'flex', gap: 8, flexWrap: 'wrap' as const },
  chip:        { background: '#312e81', color: '#a5b4fc', padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600 },
  subjectGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(160px,1fr))', gap: 10 },
  subjectCard: { background: '#1e293b', border: '1px solid #334155', borderRadius: 10, padding: 14 },
  subjectHeader:{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 },
  subjectEmoji:{ fontSize: 18 },
  subjectName: { fontWeight: 700, fontSize: 13, color: '#f8fafc', flex: 1 },
  levelBadge:  { padding: '2px 7px', borderRadius: 20, fontSize: 10, fontWeight: 700 },
  barBg:       { background: '#0f172a', borderRadius: 3, height: 5, marginBottom: 6, overflow: 'hidden' },
  barFill:     { height: '100%', borderRadius: 3, transition: 'width .5s ease' },
  subjectMeta: { display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#64748b' },
};
