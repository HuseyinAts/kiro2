/**
 * CuratorPage — Faz 3.2 + 3.3
 *
 * Admin-only question curation queue.
 * - Left 30%: paginated queue list + filter chips
 * - Right 70%: current question, options, image, action buttons
 * - Keyboard shortcuts (Faz 3.3): V/R/A/S/1-5/←/→/?
 *
 * Velocity target: 90-180 seconds per item (20-40 items/hour).
 * Desktop-only (curators work on desktop). UI: Türkçe.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import {
  useCuratorQueue,
  useCuratorStats,
  useCuratorVerdict,
  type CuratorVerdict,
  type QueueFilters,
  type QueueItem,
  type QueueStatus,
} from '../../hooks/useCuratorQueue';

// ============================================================================
// Constants
// ============================================================================

const SUBJECTS = [
  { value: '', label: 'Tüm Dersler' },
  { value: 'MATEMATIK', label: 'Matematik' },
  { value: 'FIZIK', label: 'Fizik' },
  { value: 'KIMYA', label: 'Kimya' },
  { value: 'BIYOLOJI', label: 'Biyoloji' },
  { value: 'TURKCE', label: 'Türkçe' },
  { value: 'EDEBIYAT', label: 'Edebiyat' },
  { value: 'TARIH', label: 'Tarih' },
  { value: 'COGRAFYA', label: 'Coğrafya' },
  { value: 'FELSEFE', label: 'Felsefe' },
  { value: 'DIN', label: 'Din' },
  { value: 'GEOMETRI', label: 'Geometri' },
];

const STATUSES: Array<{ value: QueueStatus; label: string }> = [
  { value: 'bronze_clean', label: 'Bronze Clean' },
  { value: 'pending', label: 'Pending' },
  { value: 'unverified', label: 'Unverified' },
  { value: 'flagged', label: '🚩 Öğrenci Bildirimleri' },
];

// Öğrenci flag_type → okunur Türkçe etiket (FlagButton ile aynı sözlük).
const FLAG_TYPE_LABELS: Record<string, string> = {
  wrong_answer: 'Cevap yanlış',
  wrong_topic: 'Konu yanlış',
  solution_visible: 'Çözüm görselde görünüyor',
  incomplete_text: 'Metin eksik/bozuk',
  circular: 'Soru kendini cevaplıyor (dairesel)',
  figure_needed: 'Şekil/görsel gerekiyor ama yok',
  other: 'Diğer',
};

const DIAGRAM_OPTIONS: Array<{ value: 'all' | 'yes' | 'no'; label: string }> = [
  { value: 'all', label: 'Tüm Sorular' },
  { value: 'yes', label: 'Diyagramlı' },
  { value: 'no', label: 'Diyagramsız' },
];

const OPTION_KEYS: Array<'A' | 'B' | 'C' | 'D' | 'E'> = ['A', 'B', 'C', 'D', 'E'];

// ============================================================================
// Helpers
// ============================================================================

function formatVelocity(seconds: number | null | undefined): string {
  if (seconds == null) return '-';
  if (seconds < 60) return `${seconds.toFixed(0)} sn`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m} dk ${s} sn`;
}

function subjectLabel(value: string): string {
  return SUBJECTS.find((s) => s.value === value)?.label || value;
}

// ============================================================================
// Sub-components
// ============================================================================

interface StatsBarProps {
  pendingCount: number | undefined;
  verifiedToday: number | undefined;
  rejectedToday: number | undefined;
  avgVelocitySec: number | null | undefined;
  isLoading: boolean;
}

function StatsBar({ pendingCount, verifiedToday, rejectedToday, avgVelocitySec, isLoading }: StatsBarProps) {
  const items = [
    { label: 'Bekleyen', value: pendingCount ?? '-', color: 'text-amber-600' },
    { label: 'Bugün Onaylanan', value: verifiedToday ?? '-', color: 'text-emerald-600' },
    { label: 'Bugün Reddedilen', value: rejectedToday ?? '-', color: 'text-rose-600' },
    { label: 'Ortalama Hız', value: formatVelocity(avgVelocitySec), color: 'text-indigo-600' },
  ];
  return (
    <div className="grid grid-cols-4 gap-3 mb-4" data-testid="curator-stats-bar">
      {items.map((it) => (
        <div
          key={it.label}
          className="bg-white border border-slate-200 rounded-xl px-4 py-3 shadow-sm"
        >
          <div className="text-xs uppercase tracking-wider text-slate-500 font-medium">
            {it.label}
          </div>
          <div className={`text-2xl font-bold ${it.color} font-mono`}>
            {isLoading ? '…' : it.value}
          </div>
        </div>
      ))}
    </div>
  );
}

interface FilterChipsProps {
  filters: QueueFilters;
  onChange: (patch: Partial<QueueFilters>) => void;
}

function FilterChips({ filters, onChange }: FilterChipsProps) {
  return (
    <div className="space-y-2 mb-3" data-testid="curator-filter-chips">
      <div className="flex flex-wrap gap-1.5">
        {STATUSES.map((s) => (
          <button
            key={s.value}
            type="button"
            onClick={() => onChange({ status: s.value, page: 1 })}
            className={
              filters.status === s.value
                ? 'px-3 py-1 text-xs font-semibold rounded-full bg-indigo-600 text-white'
                : 'px-3 py-1 text-xs font-semibold rounded-full bg-slate-100 text-slate-600 hover:bg-slate-200'
            }
            aria-pressed={filters.status === s.value}
          >
            {s.label}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-1.5">
        <select
          value={filters.subject ?? ''}
          onChange={(e) => onChange({ subject: e.target.value || undefined, page: 1 })}
          className="px-2 py-1 text-xs rounded-md border border-slate-300 bg-white text-slate-700"
          aria-label="Ders filtresi"
        >
          {SUBJECTS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
        <select
          value={filters.has_diagram ?? 'all'}
          onChange={(e) =>
            onChange({ has_diagram: e.target.value as 'all' | 'yes' | 'no', page: 1 })
          }
          className="px-2 py-1 text-xs rounded-md border border-slate-300 bg-white text-slate-700"
          aria-label="Diyagram filtresi"
        >
          {DIAGRAM_OPTIONS.map((d) => (
            <option key={d.value} value={d.value}>
              {d.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

interface QueueListProps {
  items: QueueItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  page: number;
  perPage: number;
  total: number;
  onPageChange: (page: number) => void;
  isLoading: boolean;
}

function QueueList({
  items,
  selectedId,
  onSelect,
  page,
  perPage,
  total,
  onPageChange,
  isLoading,
}: QueueListProps) {
  const totalPages = Math.max(1, Math.ceil(total / perPage));
  return (
    <div className="flex-1 overflow-y-auto border border-slate-200 rounded-xl bg-white">
      {isLoading && items.length === 0 ? (
        <div className="p-4 text-sm text-slate-500">Yükleniyor…</div>
      ) : items.length === 0 ? (
        <div className="p-4 text-sm text-slate-500">Kuyruk boş.</div>
      ) : (
        <ul className="divide-y divide-slate-100" data-testid="curator-queue-list">
          {items.map((it) => (
            <li
              key={it.id}
              onClick={() => onSelect(it.id)}
              className={
                'cursor-pointer px-3 py-2 hover:bg-indigo-50/60 transition-colors ' +
                (selectedId === it.id ? 'bg-indigo-50 border-l-4 border-indigo-600' : 'border-l-4 border-transparent')
              }
              data-testid={`queue-item-${it.id}`}
            >
              <div className="text-[11px] text-slate-500 uppercase tracking-wider font-medium">
                {subjectLabel(it.subject_area)} · {it.difficulty_level ?? '?'}
              </div>
              <div className="text-sm text-slate-800 line-clamp-2">
                {it.question_text.slice(0, 120)}
                {it.question_text.length > 120 ? '…' : ''}
              </div>
            </li>
          ))}
        </ul>
      )}
      <div className="flex items-center justify-between px-3 py-2 border-t border-slate-200 bg-slate-50 text-xs">
        <button
          type="button"
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={page <= 1}
          className="px-2 py-1 rounded bg-white border border-slate-300 disabled:opacity-40"
        >
          ←
        </button>
        <span className="text-slate-600">
          {page} / {totalPages} · toplam {total}
        </span>
        <button
          type="button"
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
          disabled={page >= totalPages}
          className="px-2 py-1 rounded bg-white border border-slate-300 disabled:opacity-40"
        >
          →
        </button>
      </div>
    </div>
  );
}

interface QuestionViewProps {
  item: QueueItem;
  highlightedOption: 'A' | 'B' | 'C' | 'D' | 'E' | null;
  onHighlight: (opt: 'A' | 'B' | 'C' | 'D' | 'E') => void;
}

function QuestionView({ item, highlightedOption, onHighlight }: QuestionViewProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-xs">
        <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium">
          {subjectLabel(item.subject_area)}
        </span>
        {item.difficulty_level && (
          <span className="px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-medium">
            {item.difficulty_level}
          </span>
        )}
        <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 font-medium">
          {item.quality_review_status}
        </span>
        <span className="ml-auto text-slate-400 font-mono">{item.id}</span>
      </div>

      {item.image_url && (
        <div className="flex justify-center bg-slate-50 rounded-xl border border-slate-200 p-3">
          <img
            src={item.image_url}
            alt="Soru görseli"
            className="max-h-96 object-contain"
            data-testid="curator-question-image"
          />
        </div>
      )}

      {item.student_flags && item.student_flags.length > 0 && (
        <div
          className="rounded-lg border border-amber-300 bg-amber-50 p-3"
          data-testid="curator-student-flags"
        >
          <div className="text-xs font-semibold text-amber-800 mb-1.5">
            🚩 Öğrenci bildirimleri ({item.flag_count})
          </div>
          <ul className="space-y-1">
            {item.student_flags.map((f) => (
              <li key={f.flag_type} className="text-sm text-amber-900">
                <span className="font-medium">
                  {FLAG_TYPE_LABELS[f.flag_type] ?? f.flag_type}
                </span>
                <span className="text-amber-700"> × {f.count}</span>
                {f.notes.length > 0 && (
                  <ul className="ml-4 mt-0.5 list-disc text-xs text-amber-800">
                    {f.notes.slice(0, 3).map((n, i) => (
                      <li key={i}>{n}</li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div
        className="text-base text-slate-900 leading-relaxed whitespace-pre-wrap"
        data-testid="curator-question-text"
      >
        {item.question_text}
      </div>

      <div className="space-y-2" data-testid="curator-question-options">
        {OPTION_KEYS.map((key) => {
          const text = item.options?.[key];
          if (!text) return null;
          const isCorrect = item.correct_answer?.toUpperCase() === key;
          const isHighlighted = highlightedOption === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() => onHighlight(key)}
              data-testid={`option-${key}`}
              className={
                'w-full text-left flex gap-3 px-3 py-2 rounded-lg border transition-all ' +
                (isCorrect
                  ? 'border-emerald-400 bg-emerald-50 '
                  : 'border-slate-200 bg-white ') +
                (isHighlighted ? 'ring-2 ring-indigo-500 ' : '')
              }
            >
              <span
                className={
                  'flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold ' +
                  (isCorrect ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-600')
                }
              >
                {key}
              </span>
              <span className="text-sm text-slate-800 leading-relaxed">{text}</span>
              {isCorrect && (
                <span className="ml-auto text-xs font-semibold text-emerald-700">DOĞRU</span>
              )}
            </button>
          );
        })}
      </div>

      {item.misconception_tags && item.misconception_tags.length > 0 && (
        <div>
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Çeldirici Etiketleri
          </div>
          <div className="flex flex-wrap gap-1.5">
            {item.misconception_tags.map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 text-xs"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      {item.solution_steps && item.solution_steps.length > 0 && (
        <div>
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Çözüm Adımları
          </div>
          <ol className="list-decimal list-inside space-y-1 text-sm text-slate-700">
            {item.solution_steps.map((step, idx) => (
              <li key={idx}>{step}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

interface ActionsBarProps {
  velocitySec: number;
  onAction: (verdict: CuratorVerdict | 'skip') => void;
  disabled: boolean;
}

function ActionsBar({ velocitySec, onAction, disabled }: ActionsBarProps) {
  const btn = 'px-4 py-2.5 rounded-xl font-semibold text-sm shadow-sm transition-transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2';
  return (
    <div className="sticky bottom-0 mt-4 -mx-6 px-6 py-3 bg-white/95 backdrop-blur-sm border-t border-slate-200 flex items-center gap-2">
      <div className="text-xs text-slate-500 font-mono mr-2" data-testid="velocity-timer">
        ⏱ {velocitySec}s
      </div>
      <button
        type="button"
        onClick={() => onAction('verify')}
        disabled={disabled}
        className={`${btn} bg-emerald-600 hover:bg-emerald-700 text-white`}
        data-testid="action-verify"
        title="Onayla (V)"
      >
        ✅ Onayla <kbd className="text-[10px] px-1 py-0.5 bg-emerald-800/30 rounded">V</kbd>
      </button>
      <button
        type="button"
        onClick={() => onAction('reject')}
        disabled={disabled}
        className={`${btn} bg-rose-600 hover:bg-rose-700 text-white`}
        data-testid="action-reject"
        title="Reddet (R)"
      >
        ❌ Reddet <kbd className="text-[10px] px-1 py-0.5 bg-rose-800/30 rounded">R</kbd>
      </button>
      <button
        type="button"
        onClick={() => onAction('archive')}
        disabled={disabled}
        className={`${btn} bg-slate-600 hover:bg-slate-700 text-white`}
        data-testid="action-archive"
        title="Arşivle (A)"
      >
        📦 Arşivle <kbd className="text-[10px] px-1 py-0.5 bg-slate-800/30 rounded">A</kbd>
      </button>
      <button
        type="button"
        onClick={() => onAction('skip')}
        disabled={disabled}
        className={`${btn} bg-white border border-slate-300 text-slate-700 hover:bg-slate-50`}
        data-testid="action-skip"
        title="Atla (S)"
      >
        ⏭ Sonraki <kbd className="text-[10px] px-1 py-0.5 bg-slate-200 rounded">S</kbd>
      </button>
    </div>
  );
}

function HelpOverlay({ open, onClose }: { open: boolean; onClose: () => void }) {
  // S179 fix (F-P1-6): role=dialog + aria-modal + Escape-to-close +
  // initial-focus on the close button. Pre-fix this `fixed inset-0`
  // <div> was invisible to screen readers and not keyboard-dismissable.
  // useEffect for Escape + initial focus is hooks-rules safe because
  // we return null AFTER the hooks fire.
  useEffect(() => {
    if (!open) return;
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 bg-slate-900/50 z-50 flex items-center justify-center p-6"
      onClick={onClose}
      data-testid="help-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="curator-help-title"
    >
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="curator-help-title" className="text-lg font-bold text-slate-900 mb-3">
          Klavye Kısayolları
        </h2>
        <ul className="space-y-2 text-sm text-slate-700">
          <li><kbd className="px-2 py-0.5 bg-slate-100 rounded font-mono">V</kbd> — Onayla</li>
          <li><kbd className="px-2 py-0.5 bg-slate-100 rounded font-mono">R</kbd> — Reddet</li>
          <li><kbd className="px-2 py-0.5 bg-slate-100 rounded font-mono">A</kbd> — Arşivle</li>
          <li><kbd className="px-2 py-0.5 bg-slate-100 rounded font-mono">S</kbd> — Atla</li>
          <li><kbd className="px-2 py-0.5 bg-slate-100 rounded font-mono">1-5</kbd> — Şıkları vurgula</li>
          <li><kbd className="px-2 py-0.5 bg-slate-100 rounded font-mono">←/→</kbd> — Önceki / Sonraki soru</li>
          <li><kbd className="px-2 py-0.5 bg-slate-100 rounded font-mono">?</kbd> — Bu yardımı aç</li>
          <li><kbd className="px-2 py-0.5 bg-slate-100 rounded font-mono">Esc</kbd> — Kapat</li>
        </ul>
        <button
          type="button"
          onClick={onClose}
          autoFocus
          aria-label="Yardım penceresini kapat"
          className="mt-4 w-full px-4 py-2 bg-indigo-600 text-white rounded-lg font-semibold"
        >
          Kapat
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// Main page
// ============================================================================

export function CuratorPage() {
  const [filters, setFilters] = useState<QueueFilters>({
    status: 'bronze_clean',
    page: 1,
    per_page: 25,
    has_diagram: 'all',
  });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [highlightedOption, setHighlightedOption] = useState<'A' | 'B' | 'C' | 'D' | 'E' | null>(null);
  const [helpOpen, setHelpOpen] = useState(false);
  const [velocitySec, setVelocitySec] = useState(0);
  const itemStartRef = useRef<number>(Date.now());

  const queueQuery = useCuratorQueue(filters);
  const statsQuery = useCuratorStats();
  const verdictMutation = useCuratorVerdict();

  const items = queueQuery.data?.items ?? [];
  const total = queueQuery.data?.total ?? 0;

  // Auto-select first item when queue arrives
  useEffect(() => {
    if (!selectedId && items.length > 0) {
      setSelectedId(items[0].id);
    }
    if (selectedId && !items.find((it) => it.id === selectedId) && items.length > 0) {
      setSelectedId(items[0].id);
    }
  }, [items, selectedId]);

  // Reset velocity timer when selected item changes
  useEffect(() => {
    itemStartRef.current = Date.now();
    setVelocitySec(0);
    setHighlightedOption(null);
  }, [selectedId]);

  // Tick velocity timer every second
  useEffect(() => {
    const t = window.setInterval(() => {
      setVelocitySec(Math.floor((Date.now() - itemStartRef.current) / 1000));
    }, 1000);
    return () => window.clearInterval(t);
  }, []);

  const currentIndex = useMemo(
    () => items.findIndex((it) => it.id === selectedId),
    [items, selectedId],
  );
  const currentItem = currentIndex >= 0 ? items[currentIndex] : null;

  const goToOffset = useCallback(
    (offset: number) => {
      if (items.length === 0) return;
      const next = currentIndex + offset;
      if (next < 0 || next >= items.length) return;
      setSelectedId(items[next].id);
    },
    [items, currentIndex],
  );

  const handleAction = useCallback(
    async (verdict: CuratorVerdict | 'skip') => {
      if (!currentItem) return;
      if (verdict === 'skip') {
        goToOffset(1);
        return;
      }
      try {
        await verdictMutation.mutateAsync({
          question_id: currentItem.id,
          verdict,
          reviewer_velocity_seconds: velocitySec,
        });
        // Advance to next item
        goToOffset(1);
      } catch {
        // mutation error state is exposed via verdictMutation.error
      }
    },
    [currentItem, velocitySec, verdictMutation, goToOffset],
  );

  // Memoize keyboard binding map so the hook effect re-attaches only when handlers change
  const keyBindings = useMemo(
    () => ({
      v: () => handleAction('verify'),
      V: () => handleAction('verify'),
      r: () => handleAction('reject'),
      R: () => handleAction('reject'),
      a: () => handleAction('archive'),
      A: () => handleAction('archive'),
      s: () => handleAction('skip'),
      S: () => handleAction('skip'),
      '1': () => setHighlightedOption('A'),
      '2': () => setHighlightedOption('B'),
      '3': () => setHighlightedOption('C'),
      '4': () => setHighlightedOption('D'),
      '5': () => setHighlightedOption('E'),
      ArrowLeft: () => goToOffset(-1),
      ArrowRight: () => goToOffset(1),
      '?': () => setHelpOpen((o) => !o),
      Escape: () => setHelpOpen(false),
    }),
    [handleAction, goToOffset],
  );

  useKeyboardShortcuts(keyBindings, { enabled: !verdictMutation.isLoading });

  const handleFilterChange = useCallback((patch: Partial<QueueFilters>) => {
    setFilters((prev) => ({ ...prev, ...patch }));
    setSelectedId(null);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 p-6 font-sans" data-testid="curator-page">
      {/* Header */}
      <header className="mb-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Soru Curator Kuyruğu</h1>
            <p className="text-sm text-slate-500">
              Bronze + pending sorular için manuel inceleme. Hedef hız: 90-180 sn/soru.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setHelpOpen(true)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white text-sm text-slate-700 hover:bg-slate-100"
            data-testid="help-button"
            title="Klavye kısayolları (?)"
          >
            ? Yardım
          </button>
        </div>

        <StatsBar
          pendingCount={statsQuery.data?.pending_count}
          verifiedToday={statsQuery.data?.verified_today}
          rejectedToday={statsQuery.data?.rejected_today}
          avgVelocitySec={statsQuery.data?.avg_velocity_sec}
          isLoading={statsQuery.isLoading}
        />
      </header>

      {/* Two-column layout */}
      <div className="grid grid-cols-10 gap-4 min-h-[70vh]">
        {/* Left: queue list (30%) */}
        <aside className="col-span-3 flex flex-col">
          <FilterChips filters={filters} onChange={handleFilterChange} />
          <QueueList
            items={items}
            selectedId={selectedId}
            onSelect={setSelectedId}
            page={filters.page}
            perPage={filters.per_page ?? 25}
            total={total}
            onPageChange={(p) => setFilters((f) => ({ ...f, page: p }))}
            isLoading={queueQuery.isLoading || queueQuery.isFetching}
          />
        </aside>

        {/* Right: current item (70%) */}
        <section className="col-span-7 bg-white border border-slate-200 rounded-2xl px-6 py-5 shadow-sm flex flex-col">
          {queueQuery.error ? (
            <div className="text-rose-600 text-sm" role="alert">
              Kuyruk yüklenemedi: {queueQuery.error.message}
            </div>
          ) : !currentItem ? (
            <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
              Soldaki listeden bir soru seçin.
            </div>
          ) : (
            <>
              <div className="flex-1 overflow-y-auto pr-1">
                <QuestionView
                  item={currentItem}
                  highlightedOption={highlightedOption}
                  onHighlight={setHighlightedOption}
                />
                {verdictMutation.error && (
                  <div
                    className="mt-4 px-3 py-2 rounded-lg bg-rose-50 border border-rose-200 text-sm text-rose-700"
                    role="alert"
                  >
                    Karar gönderilemedi: {verdictMutation.error.message}
                  </div>
                )}
              </div>
              <ActionsBar
                velocitySec={velocitySec}
                onAction={handleAction}
                disabled={verdictMutation.isLoading}
              />
            </>
          )}
        </section>
      </div>

      <HelpOverlay open={helpOpen} onClose={() => setHelpOpen(false)} />
    </div>
  );
}

export default CuratorPage;
