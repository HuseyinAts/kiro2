/**
 * LearningPathMapPage — Konu Haritası (DAG Görünümü)
 * Haftalık plan + ders öncelik görselleştirmesi
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const API = '/api/v1/learning-path';

interface WeekDay {
  date: string;
  day_label: string;
  is_today: boolean;
  primary_subject: string;
  secondary_subject: string;
  estimated_minutes: number;
  days_to_exam: number;
  focus_reason: string;
}

interface SubjectStatus {
  subject: string;
  theta: number;
  mastery_pct: number;
  fsrs_due_count: number;
  priority_score: number;
  level_label: string;
  zpd_lower: number;
  zpd_upper: number;
}

const SUBJECT_TR: Record<string, string> = {
  MATEMATIK: 'Matematik', TURKCE: 'Türkçe', FIZIK: 'Fizik',
  KIMYA: 'Kimya', BIYOLOJI: 'Biyoloji', GEOMETRI: 'Geometri',
  TARIH: 'Tarih', COGRAFYA: 'Coğrafya', SOSYAL: 'Sosyal',
  EDEBIYAT: 'Edebiyat', FEN: 'Fen', GENEL: 'Genel Kültür',
};

const SUBJECT_EMOJI: Record<string, string> = {
  MATEMATIK: '📐', TURKCE: '📖', FIZIK: '⚛️', KIMYA: '🧪',
  BIYOLOJI: '🧬', GEOMETRI: '📏', TARIH: '🏛️', COGRAFYA: '🌍',
  SOSYAL: '🌐', EDEBIYAT: '✍️', FEN: '🔬', GENEL: '💡',
};

const SUBJECT_COLOR: Record<string, string> = {
  MATEMATIK: '#6366f1', TURKCE: '#ec4899', FIZIK: '#06b6d4',
  KIMYA: '#f59e0b', BIYOLOJI: '#10b981', GEOMETRI: '#8b5cf6',
  TARIH: '#f97316', COGRAFYA: '#14b8a6', SOSYAL: '#84cc16',
  EDEBIYAT: '#e879f9', FEN: '#22d3ee', GENEL: '#94a3b8',
};

export default function LearningPathMapPage() {
  const navigate = useNavigate();
  const [weekly, setWeekly] = useState<WeekDay[]>([]);
  const [statuses, setStatuses] = useState<SubjectStatus[]>([]);
  const [examDate, setExamDate] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedSubject, setSelectedSubject] = useState<string | null>(null);
  const [goalForm, setGoalForm] = useState({ exam_type: 'TYT', exam_date: '', daily_minutes: 120 });
  const [goalSaved, setGoalSaved] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/weekly`, { credentials: 'include' }).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }),
      fetch(`${API}/status`, { credentials: 'include' }).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }),
    ]).then(([weekData, statusData]) => {
      if (weekData.weekly_plan) { setWeekly(weekData.weekly_plan); setExamDate(weekData.exam_date); }
      if (Array.isArray(statusData)) setStatuses(statusData);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const saveGoal = async () => {
    try {
      const r = await fetch(`${API}/goal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(goalForm),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setGoalSaved(true);
      setTimeout(() => setGoalSaved(false), 3000);
    } catch {
      setGoalSaved(false);
    }
  };

  const sorted = [...statuses].sort((a, b) => b.priority_score - a.priority_score);
  const selected = statuses.find(s => s.subject === selectedSubject);

  if (loading) return (
    <div style={s.center}><div style={s.spinner} /><p style={{ color: '#94a3b8', marginTop: 16 }}>Harita yükleniyor…</p></div>
  );

  return (
    <div style={s.page}>
      {/* Header */}
      <div style={s.header}>
        <button onClick={() => navigate('/dashboard')} style={s.backBtn}>← Geri</button>
        <div>
          <h1 style={s.title}>🗺️ Öğrenme Haritası</h1>
          {examDate && <p style={s.subtitle}>Sınav: {new Date(examDate).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })}</p>}
        </div>
        <button onClick={() => navigate('/daily-plan')} style={s.planBtn}>📋 Bugünkü Plan</button>
      </div>

      {/* Hedef Formu */}
      <div style={s.goalCard}>
        <h3 style={s.sectionTitle}>🎯 Sınav Hedefi</h3>
        <div style={s.goalRow}>
          <select value={goalForm.exam_type} onChange={e => setGoalForm(f => ({ ...f, exam_type: e.target.value }))} style={s.select}>
            <option value="TYT">TYT</option>
            <option value="AYT_SAY">AYT Sayısal</option>
            <option value="AYT_EA">AYT EA</option>
            <option value="AYT_SOZ">AYT Sözel</option>
          </select>
          <input type="date" value={goalForm.exam_date} onChange={e => setGoalForm(f => ({ ...f, exam_date: e.target.value }))} style={s.input} />
          <input type="number" value={goalForm.daily_minutes} min={30} max={480} step={15}
            onChange={e => setGoalForm(f => ({ ...f, daily_minutes: +e.target.value }))} style={{ ...s.input, width: 90 }} placeholder="dk/gün" />
          <button onClick={saveGoal} style={s.saveBtn}>{goalSaved ? '✅ Kaydedildi' : 'Kaydet'}</button>
        </div>
      </div>

      {/* Ders Öncelik Grafiği */}
      <div style={s.section}>
        <h3 style={s.sectionTitle}>📊 Ders Öncelik Haritası</h3>
        <p style={s.hint}>Derse tıklayarak detay gör</p>
        <div style={s.subjectGrid}>
          {sorted.map(st => {
            const color = SUBJECT_COLOR[st.subject] ?? '#6b7280';
            const isSelected = selectedSubject === st.subject;
            return (
              <div key={st.subject} onClick={() => setSelectedSubject(isSelected ? null : st.subject)}
                style={{ ...s.subjectNode, borderColor: isSelected ? color : '#334155', boxShadow: isSelected ? `0 0 20px ${color}44` : 'none' }}>
                <div style={{ ...s.subjectDot, background: color }} />
                <span style={s.subjectEmoji}>{SUBJECT_EMOJI[st.subject] ?? '📚'}</span>
                <span style={s.subjectName}>{SUBJECT_TR[st.subject] ?? st.subject}</span>
                <div style={s.subjectBar}>
                  <div style={{ ...s.subjectBarFill, width: `${st.mastery_pct}%`, background: color }} />
                </div>
                <div style={s.subjectMeta}>
                  <span style={{ color }}>{st.level_label}</span>
                  {st.fsrs_due_count > 0 && <span style={{ color: '#f59e0b', fontSize: 10 }}>🔄{st.fsrs_due_count}</span>}
                </div>
                {/* Priority ring */}
                <div style={{ ...s.priorityRing, opacity: st.priority_score / 100 }}>
                  {st.priority_score.toFixed(0)}
                </div>
              </div>
            );
          })}
        </div>

        {/* Seçili ders detayı */}
        {selected && (
          <div style={{ ...s.detailCard, borderColor: SUBJECT_COLOR[selected.subject] ?? '#6366f1' }}>
            <h4 style={{ margin: '0 0 10px', color: SUBJECT_COLOR[selected.subject] ?? '#a5b4fc' }}>
              {SUBJECT_EMOJI[selected.subject]} {SUBJECT_TR[selected.subject] ?? selected.subject}
            </h4>
            <div style={s.detailGrid}>
              <div style={s.detailItem}><span style={s.detailLabel}>IRT θ</span><span style={s.detailValue}>{selected.theta.toFixed(3)}</span></div>
              <div style={s.detailItem}><span style={s.detailLabel}>Mastery</span><span style={s.detailValue}>{selected.mastery_pct.toFixed(1)}%</span></div>
              <div style={s.detailItem}><span style={s.detailLabel}>ZPD Alt</span><span style={s.detailValue}>{selected.zpd_lower.toFixed(2)}</span></div>
              <div style={s.detailItem}><span style={s.detailLabel}>ZPD Üst</span><span style={s.detailValue}>{selected.zpd_upper.toFixed(2)}</span></div>
              <div style={s.detailItem}><span style={s.detailLabel}>FSRS Vade</span><span style={{ ...s.detailValue, color: selected.fsrs_due_count > 0 ? '#f59e0b' : '#10b981' }}>{selected.fsrs_due_count} kart</span></div>
              <div style={s.detailItem}><span style={s.detailLabel}>Öncelik</span><span style={s.detailValue}>{selected.priority_score.toFixed(0)}/100</span></div>
            </div>
            <button onClick={() => navigate('/cat')} style={{ ...s.saveBtn, marginTop: 12 }}>🎯 CAT Başlat</button>
          </div>
        )}
      </div>

      {/* 7 Günlük Plan */}
      <div style={s.section}>
        <h3 style={s.sectionTitle}>📅 Bu Haftanın Planı</h3>
        <div style={s.weekGrid}>
          {weekly.map((day, i) => (
            <div key={i} style={{ ...s.dayCard, borderColor: day.is_today ? '#6366f1' : '#334155', background: day.is_today ? '#1e1b4b' : '#1e293b' }}>
              <div style={s.dayHeader}>
                <span style={{ ...s.dayLabel, color: day.is_today ? '#818cf8' : '#64748b' }}>{day.day_label}</span>
                {day.is_today && <span style={s.todayBadge}>Bugün</span>}
              </div>
              <div style={s.daySubjects}>
                <div style={{ ...s.daySubjectTag, background: (SUBJECT_COLOR[day.primary_subject] ?? '#6b7280') + '22', color: SUBJECT_COLOR[day.primary_subject] ?? '#6b7280' }}>
                  {SUBJECT_EMOJI[day.primary_subject]} {SUBJECT_TR[day.primary_subject] ?? day.primary_subject}
                </div>
                <div style={{ ...s.daySubjectTag, background: (SUBJECT_COLOR[day.secondary_subject] ?? '#6b7280') + '22', color: SUBJECT_COLOR[day.secondary_subject] ?? '#6b7280', fontSize: 11 }}>
                  {SUBJECT_EMOJI[day.secondary_subject]} {SUBJECT_TR[day.secondary_subject] ?? day.secondary_subject}
                </div>
              </div>
              <div style={s.dayMeta}>{day.estimated_minutes} dk • {day.days_to_exam} gün kaldı</div>
              <div style={s.dayReason}>{day.focus_reason}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Stiller ──────────────────────────────────────────────────────────────────
const s: Record<string, any> = {
  page: { minHeight: '100vh', background: '#0f172a', color: '#f8fafc', padding: '24px 16px', fontFamily: "'Inter', sans-serif" },
  center: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' },
  spinner: { width: 40, height: 40, border: '3px solid #334155', borderTop: '3px solid #6366f1', borderRadius: '50%', animation: 'spin 1s linear infinite' },
  header: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 },
  backBtn: { background: '#1e293b', border: '1px solid #334155', color: '#94a3b8', padding: '8px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 14 },
  planBtn: { background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', border: 'none', color: '#fff', padding: '8px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 14, fontWeight: 600 },
  title: { margin: 0, fontSize: 22, fontWeight: 700, color: '#f8fafc' },
  subtitle: { margin: '4px 0 0', fontSize: 14, color: '#94a3b8' },
  section: { marginBottom: 28 },
  sectionTitle: { margin: '0 0 4px', fontSize: 16, fontWeight: 700, color: '#f8fafc' },
  hint: { margin: '0 0 14px', fontSize: 12, color: '#64748b' },
  goalCard: { background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 16, marginBottom: 24 },
  goalRow: { display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center', marginTop: 10 },
  select: { background: '#0f172a', border: '1px solid #475569', color: '#f8fafc', padding: '8px 12px', borderRadius: 8, fontSize: 14 },
  input: { background: '#0f172a', border: '1px solid #475569', color: '#f8fafc', padding: '8px 12px', borderRadius: 8, fontSize: 14, flex: 1, minWidth: 120 },
  saveBtn: { background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', border: 'none', color: '#fff', padding: '8px 18px', borderRadius: 8, cursor: 'pointer', fontSize: 14, fontWeight: 600, whiteSpace: 'nowrap' as const },
  subjectGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 12 },
  subjectNode: { background: '#1e293b', border: '2px solid #334155', borderRadius: 12, padding: 12, cursor: 'pointer', position: 'relative' as const, transition: 'all 0.2s' },
  subjectDot: { width: 8, height: 8, borderRadius: '50%', position: 'absolute' as const, top: 10, right: 10 },
  subjectEmoji: { display: 'block', fontSize: 24, marginBottom: 4 },
  subjectName: { display: 'block', fontSize: 12, fontWeight: 600, color: '#f8fafc', marginBottom: 8 },
  subjectBar: { background: '#0f172a', borderRadius: 3, height: 4, marginBottom: 6, overflow: 'hidden' },
  subjectBarFill: { height: '100%', borderRadius: 3, transition: 'width 0.5s ease' },
  subjectMeta: { display: 'flex', justifyContent: 'space-between', fontSize: 11, fontWeight: 600 },
  priorityRing: { position: 'absolute' as const, bottom: 8, right: 8, fontSize: 10, color: '#64748b', fontWeight: 700 },
  detailCard: { background: '#1e293b', border: '2px solid #334155', borderRadius: 12, padding: 16, marginTop: 16 },
  detailGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 },
  detailItem: { display: 'flex', flexDirection: 'column' as const, gap: 2 },
  detailLabel: { fontSize: 11, color: '#64748b' },
  detailValue: { fontSize: 15, fontWeight: 700, color: '#f8fafc' },
  weekGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10 },
  dayCard: { background: '#1e293b', border: '1px solid #334155', borderRadius: 10, padding: 12 },
  dayHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  dayLabel: { fontSize: 13, fontWeight: 700 },
  todayBadge: { background: '#312e81', color: '#818cf8', padding: '2px 6px', borderRadius: 8, fontSize: 10, fontWeight: 700 },
  daySubjects: { display: 'flex', flexDirection: 'column' as const, gap: 4, marginBottom: 8 },
  daySubjectTag: { padding: '3px 8px', borderRadius: 6, fontSize: 12, fontWeight: 600 },
  dayMeta: { fontSize: 11, color: '#64748b', marginBottom: 3 },
  dayReason: { fontSize: 10, color: '#475569', fontStyle: 'italic' },
};
