import React, { useState, useEffect, useRef, useCallback } from 'react';

// ─── Inject global styles ────────────────────────────────────────────────────

const GHOST_CSS = `
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:ital,wght@0,300;0,400;0,600;0,700;1,300&display=swap');

:root {
  --void:      #000a08;
  --surface:   #060f0d;
  --surface2:  #0c1c17;
  --border:    #0d2e22;
  --border-hi: #1a5c3a;
  --ph:        #00ff88;   /* phosphor */
  --ph-dim:    #00994d;
  --ph-glow:   #00ff8822;
  --ph-bright: #80ffbb;
  --red:       #ff3355;
  --amber:     #ffaa00;
  --blue:      #00aaff;
  --text:      #b0f0d0;
  --text-dim:  #3a6650;
  --text-hi:   #e8fff4;
}

@keyframes blink        { 0%,49%{opacity:1}50%,100%{opacity:0} }
@keyframes scanline     { 0%{top:-4px} 100%{top:100%} }
@keyframes stream-in    { from{opacity:0;transform:translateX(-6px)} to{opacity:1;transform:none} }
@keyframes bar-fill     { from{width:0} to{width:var(--w)} }
@keyframes glow-pulse   { 0%,100%{text-shadow:0 0 8px var(--ph-glow)} 50%{text-shadow:0 0 20px var(--ph),0 0 40px var(--ph-glow)} }
@keyframes status-ring  { to{stroke-dashoffset:0} }
@keyframes shimmer      { 0%{opacity:.5} 50%{opacity:1} 100%{opacity:.5} }
@keyframes rca-gate     { from{transform:scaleX(0)} to{transform:scaleX(1)} }

.ghost-debug-scanline {
  position:fixed; top:0; left:0; width:100%; height:4px;
  background:linear-gradient(transparent,rgba(0,255,136,.08),transparent);
  pointer-events:none; animation:scanline 6s linear infinite; z-index:9999;
}
.ghost-debug-noise {
  position:fixed; inset:0; pointer-events:none; z-index:9998;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
  opacity:.4; mix-blend-mode:screen;
}
`;

function injectStyles() {
  if (document.getElementById('ghost-debug-css')) {return;}
  const el = document.createElement('style');
  el.id = 'ghost-debug-css';
  el.textContent = GHOST_CSS;
  document.head.appendChild(el);
}

// ─── Types ───────────────────────────────────────────────────────────────────

type InfraStatus = 'idle' | 'checking' | 'ok' | 'error' | 'warn'

interface InfraItem {
  key: string
  name: string
  cmd: string
  detail: string
  status: InfraStatus
}

interface RCAField {
  key: string
  label: string
  hint: string
  value: string
}

interface CheckItem {
  id: string
  label: string
  checked: boolean
  critical: boolean
}

interface LogEntry {
  id: number
  ts: string
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG' | 'PASS' | 'GATE'
  msg: string
}

// ─── Constants ───────────────────────────────────────────────────────────────

const INFRA_INITIAL: InfraItem[] = [
  { key: 'pg',       name: 'PostgreSQL',  cmd: 'pg_isready -p 5434',        detail: ':5434',           status: 'idle' },
  { key: 'redis',    name: 'Redis',       cmd: 'redis-cli ping',             detail: ':6379',           status: 'idle' },
  { key: 'backend',  name: 'Backend',     cmd: 'curl /api/v1/health',        detail: ':8000',           status: 'idle' },
  { key: 'frontend', name: 'Frontend',    cmd: 'curl /healthz',              detail: ':3000',           status: 'idle' },
];

const RCA_FIELDS_INITIAL: RCAField[] = [
  { key: 'error',  label: 'HATA NEDİR?',       hint: 'curl/pytest/log çıktısı — tahmin değil, gerçek output', value: '' },
  { key: 'cause',  label: 'ROOT CAUSE?',        hint: 'dosya:satır — neden bozuk',                            value: '' },
  { key: 'table',  label: 'DOĞRU TABLO MU?',    hint: 'question_bank=77K prod  /  questions=BOŞ legacy',      value: '' },
  { key: 'infra',  label: 'ALTYAPI OK MU?',     hint: 'pg_isready -p 5434, redis-cli ping, curl /health',     value: '' },
  { key: 'scope',  label: 'FIX SCOPE?',         hint: 'dosya listesi — max 3 dosya',                          value: '' },
];

const CHECKS_INITIAL: CheckItem[] = [
  { id: 'c1',  label: 'RCA tablosu dolduruldu',                   checked: false, critical: true  },
  { id: 'c2',  label: 'ruff check geçiyor',                       checked: false, critical: true  },
  { id: 'c3',  label: 'mypy / tsc type-check geçiyor',            checked: false, critical: true  },
  { id: 'c4',  label: 'Fail eden test ÖNCE bulundu/yazıldı',       checked: false, critical: true  },
  { id: 'c5',  label: 'Fix sonrası test geçiyor',                  checked: false, critical: true  },
  { id: 'c6',  label: 'question_bank kullanılıyor (questions=BOŞ)',checked: false, critical: true  },
  { id: 'c7',  label: 'is_active == True filtresi var',            checked: false, critical: true  },
  { id: 'c8',  label: 'Altyapı kontrol edildi',                    checked: false, critical: false },
  { id: 'c9',  label: 'Max 3 dosya fix scope',                     checked: false, critical: false },
  { id: 'c10', label: 'Reward hacking pattern yok',                checked: false, critical: false },
];

const LOG_SEED: LogEntry[] = [
  { id: 1, ts: now(), level: 'INFO', msg: 'GHOST-DEBUG v2.0 initialized' },
  { id: 2, ts: now(), level: 'INFO', msg: 'Awaiting RCA gate unlock...' },
];

function now(): string {
  return new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

let _logId = 10;

// ─── Sub-components ──────────────────────────────────────────────────────────

const s = {
  // layout
  page: {
    fontFamily: "'JetBrains Mono', 'Courier New', monospace",
    background: 'var(--void)',
    color: 'var(--text)',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column' as const,
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '10px 24px',
    borderBottom: '1px solid var(--border)',
    background: 'var(--surface)',
    flexShrink: 0,
  },
  headerTitle: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '14px',
    fontWeight: 900,
    letterSpacing: '4px',
    color: 'var(--ph)',
    animation: 'glow-pulse 3s ease-in-out infinite',
  },
  headerMeta: {
    fontSize: '11px',
    color: 'var(--text-dim)',
    display: 'flex',
    gap: '20px',
  },
  headerMetaItem: {
    display: 'flex',
    gap: '6px',
  },
  grid: {
    flex: 1,
    display: 'grid',
    gridTemplateColumns: '260px 1fr 300px',
    gridTemplateRows: '1fr',
    overflow: 'hidden',
  },
  col: {
    display: 'flex',
    flexDirection: 'column' as const,
    borderRight: '1px solid var(--border)',
    overflow: 'hidden',
  },
  panel: {
    padding: '16px',
    borderBottom: '1px solid var(--border)',
    flexShrink: 0,
  },
  panelTitle: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '9px',
    fontWeight: 700,
    letterSpacing: '3px',
    color: 'var(--ph-dim)',
    marginBottom: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  panelTitleLine: {
    flex: 1,
    height: '1px',
    background: 'linear-gradient(to right, var(--border-hi), transparent)',
  },
  statusDot: (status: InfraStatus) => ({
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    background: status === 'ok' ? 'var(--ph)' : status === 'error' ? 'var(--red)' : status === 'warn' ? 'var(--amber)' : status === 'checking' ? 'var(--blue)' : 'var(--text-dim)',
    boxShadow: status === 'ok' ? '0 0 6px var(--ph)' : status === 'error' ? '0 0 6px var(--red)' : status === 'checking' ? '0 0 6px var(--blue)' : 'none',
    animation: status === 'checking' ? 'shimmer 1s ease-in-out infinite' : 'none',
    flexShrink: 0,
  }),
  infraRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '8px 0',
    borderBottom: '1px solid var(--border)',
    fontSize: '11px',
    animation: 'stream-in .2s ease-out',
  },
  infraName: {
    width: '80px',
    color: 'var(--text-hi)',
    fontWeight: 600,
  },
  infraCmd: {
    flex: 1,
    color: 'var(--text-dim)',
    fontSize: '10px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const,
  },
  infraStatus: (status: InfraStatus) => ({
    fontSize: '9px',
    fontWeight: 700,
    letterSpacing: '1px',
    color: status === 'ok' ? 'var(--ph)' : status === 'error' ? 'var(--red)' : status === 'warn' ? 'var(--amber)' : status === 'checking' ? 'var(--blue)' : 'var(--text-dim)',
    minWidth: '56px',
    textAlign: 'right' as const,
  }),
  // RCA
  rcaForm: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
  },
  rcaField: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '4px',
  },
  rcaLabel: {
    fontSize: '9px',
    fontWeight: 700,
    letterSpacing: '2px',
    color: 'var(--ph-dim)',
  },
  rcaHint: {
    fontSize: '9px',
    color: 'var(--text-dim)',
    fontStyle: 'italic',
    marginBottom: '2px',
  },
  rcaInput: {
    background: 'var(--surface2)',
    border: '1px solid var(--border)',
    borderRadius: '0',
    color: 'var(--text-hi)',
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: '11px',
    padding: '8px 10px',
    resize: 'vertical' as const,
    minHeight: '52px',
    outline: 'none',
    transition: 'border-color .15s',
    lineHeight: '1.5',
  },
  // Gate
  gate: (unlocked: boolean) => ({
    padding: '12px 16px',
    background: unlocked ? 'rgba(0,255,136,.06)' : 'rgba(255,51,85,.04)',
    border: `1px solid ${unlocked ? 'var(--border-hi)' : '#3a1520'}`,
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    margin: '16px',
    fontSize: '11px',
    transition: 'all .3s ease',
  }),
  gateIcon: (unlocked: boolean) => ({
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '20px',
    color: unlocked ? 'var(--ph)' : 'var(--red)',
    lineHeight: 1,
  }),
  gateText: (unlocked: boolean) => ({
    color: unlocked ? 'var(--ph)' : 'var(--red)',
    fontWeight: 600,
    letterSpacing: '1px',
    fontSize: '11px',
  }),
  // checklist
  checkRow: (checked: boolean, critical: boolean) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '6px 0',
    borderBottom: '1px solid var(--border)',
    fontSize: '11px',
    opacity: checked ? 1 : critical ? 0.9 : 0.6,
    cursor: 'pointer',
    animation: 'stream-in .15s ease-out',
  }),
  checkbox: (checked: boolean, critical: boolean) => ({
    width: '14px',
    height: '14px',
    border: `1px solid ${checked ? 'var(--ph)' : critical ? 'var(--border-hi)' : 'var(--border)'}`,
    background: checked ? 'var(--ph)' : 'transparent',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    transition: 'all .15s',
  }),
  checkLabel: (checked: boolean) => ({
    color: checked ? 'var(--ph-bright)' : 'var(--text)',
    textDecoration: checked ? 'line-through' : 'none',
    fontSize: '10.5px',
    lineHeight: '1.4',
  }),
  criticalBadge: {
    fontSize: '8px',
    fontWeight: 700,
    letterSpacing: '1px',
    color: 'var(--red)',
    opacity: 0.7,
    marginLeft: 'auto',
    flexShrink: 0,
  },
  // log
  logStream: {
    flex: 1,
    overflow: 'auto',
    padding: '12px',
    display: 'flex',
    flexDirection: 'column-reverse' as const,
    gap: '3px',
  },
  logEntry: {
    display: 'flex',
    gap: '8px',
    fontSize: '10px',
    lineHeight: '1.4',
    animation: 'stream-in .1s ease-out',
  },
  logTs: {
    color: 'var(--text-dim)',
    flexShrink: 0,
    fontSize: '9px',
  },
  logLevel: (level: LogEntry['level']) => ({
    flexShrink: 0,
    fontSize: '9px',
    fontWeight: 700,
    width: '36px',
    color: level === 'ERROR' ? 'var(--red)' : level === 'WARN' ? 'var(--amber)' : level === 'PASS' ? 'var(--ph)' : level === 'GATE' ? 'var(--blue)' : level === 'DEBUG' ? 'var(--text-dim)' : 'var(--ph-dim)',
  }),
  logMsg: (level: LogEntry['level']) => ({
    color: level === 'ERROR' ? '#ff6680' : level === 'WARN' ? '#ffcc55' : level === 'PASS' ? 'var(--ph-bright)' : level === 'GATE' ? '#55ccff' : 'var(--text)',
  }),
  // bottom bar
  bottomBar: {
    borderTop: '1px solid var(--border)',
    background: 'var(--surface)',
    padding: '8px 20px',
    display: 'flex',
    alignItems: 'center',
    gap: '20px',
    fontSize: '10px',
    flexShrink: 0,
  },
  bottomItem: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
  },
  // progress
  progressBar: {
    height: '2px',
    background: 'var(--border)',
    borderRadius: '1px',
    overflow: 'hidden',
    marginTop: '4px',
  },
  progressFill: (pct: number, color: string) => ({
    height: '100%',
    width: `${pct}%`,
    background: color,
    transition: 'width .4s ease',
    boxShadow: `0 0 8px ${color}`,
  }),
  // action button
  btn: (disabled: boolean) => ({
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '9px',
    fontWeight: 700,
    letterSpacing: '2px',
    padding: '8px 16px',
    border: `1px solid ${disabled ? 'var(--border)' : 'var(--ph)'}`,
    background: 'transparent',
    color: disabled ? 'var(--text-dim)' : 'var(--ph)',
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'all .15s',
  }),
  centerScroll: {
    flex: 1,
    overflow: 'auto',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '16px',
  },
};

// ─── Main Component ───────────────────────────────────────────────────────────

const SystematicDebuggingPage: React.FC = () => {
  const [infra, setInfra] = useState<InfraItem[]>(INFRA_INITIAL);
  const [rca, setRca] = useState<RCAField[]>(RCA_FIELDS_INITIAL);
  const [checks, setChecks] = useState<CheckItem[]>(CHECKS_INITIAL);
  const [logs, setLogs] = useState<LogEntry[]>(LOG_SEED);
  const [clock, setClock] = useState(now());
  const [bugTitle, setBugTitle] = useState('');
  const [checkingInfra, setCheckingInfra] = useState(false);
  const focusRef = useRef<HTMLInputElement>(null);

  useEffect(() => { injectStyles(); }, []);
  useEffect(() => {
    const t = setInterval(() => setClock(now()), 1000);
    return () => clearInterval(t);
  }, []);

  const addLog = useCallback((level: LogEntry['level'], msg: string) => {
    setLogs(prev => [{ id: ++_logId, ts: now(), level, msg }, ...prev.slice(0, 99)]);
  }, []);

  // RCA gate: all 5 fields must have content
  const rcaFilled = rca.every(f => f.value.trim().length >= 3);
  const criticalChecked = checks.filter(c => c.critical && c.checked).length;
  const criticalTotal = checks.filter(c => c.critical).length;
  const allChecked = checks.every(c => c.checked);

  const handleRcaChange = (key: string, val: string) => {
    setRca(prev => prev.map(f => f.key === key ? { ...f, value: val } : f));
    if (val.trim().length === 3) {
      addLog('DEBUG', `RCA field [${key}] unlocked`);
    }
  };

  const handleCheck = (id: string) => {
    if (!rcaFilled && id !== 'c1') {
      addLog('GATE', 'RCA tablosu önce doldurulmalı — edit/write YAPMA');
      return;
    }
    setChecks(prev => prev.map(c => c.id === id ? { ...c, checked: !c.checked } : c));
    const item = checks.find(c => c.id === id);
    if (item) {addLog(item.checked ? 'DEBUG' : 'PASS', `[${item.id.toUpperCase()}] ${item.label}`);}
  };

  const runInfraCheck = async () => {
    if (checkingInfra) {return;}
    setCheckingInfra(true);
    addLog('INFO', 'Altyapi kontrolu baslatildi...');
    setInfra(prev => prev.map(i => ({ ...i, status: 'checking' })));

    const delays = [800, 1400, 2000, 2600];
    const statuses: InfraStatus[] = ['ok', 'ok', 'ok', 'ok'];

    for (let i = 0; i < INFRA_INITIAL.length; i++) {
      await new Promise<void>(r => setTimeout(r, delays[i]));
      const status = statuses[i];
      setInfra(prev => prev.map((item, idx) => idx === i ? { ...item, status } : item));
      addLog(status === 'ok' ? 'PASS' : 'ERROR', `${INFRA_INITIAL[i].name}: ${status.toUpperCase()}`);
    }

    addLog('INFO', 'Altyapi kontrolu tamamlandi');
    setCheckingInfra(false);
  };

  const infraOk = infra.every(i => i.status === 'ok');
  const progress = { checks: Math.round((checks.filter(c => c.checked).length / checks.length) * 100) };

  return (
    <div style={s.page}>
      {/* Overlay effects */}
      <div className="ghost-debug-scanline" />
      <div className="ghost-debug-noise" />

      {/* ── Header ── */}
      <header style={s.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={s.headerTitle}>GHOST-DEBUG</div>
          <div style={{ fontSize: '10px', color: 'var(--ph-dim)', letterSpacing: '2px', fontFamily: "'Orbitron', sans-serif" }}>v2.0</div>
          {bugTitle && (
            <div style={{ fontSize: '11px', color: 'var(--amber)', borderLeft: '1px solid var(--border)', paddingLeft: '16px' }}>
              &#9656; {bugTitle}
            </div>
          )}
        </div>
        <div style={s.headerMeta}>
          <div style={s.headerMetaItem}><span style={{ color: 'var(--text-dim)' }}>SESSION</span><span style={{ color: 'var(--ph)' }}>109</span></div>
          <div style={s.headerMetaItem}><span style={{ color: 'var(--text-dim)' }}>BRANCH</span><span style={{ color: 'var(--ph)' }}>master</span></div>
          <div style={s.headerMetaItem}><span style={{ color: 'var(--text-dim)' }}>DB</span><span style={{ color: 'var(--ph)' }}>:5434</span></div>
          <div style={{ color: 'var(--ph)', animation: 'blink 1s step-end infinite' }}>{clock}</div>
        </div>
      </header>

      {/* ── 3-column grid ── */}
      <div style={s.grid}>

        {/* ───── LEFT: Infra + Session ───── */}
        <div style={s.col}>
          {/* Bug title input */}
          <div style={s.panel}>
            <div style={s.panelTitle}>
              BUG CONTEXT
              <div style={s.panelTitleLine} />
            </div>
            <input
              ref={focusRef}
              placeholder="Hata basligi..."
              value={bugTitle}
              onChange={e => setBugTitle(e.target.value)}
              style={{
                ...s.rcaInput,
                minHeight: 'unset',
                resize: 'none',
                width: '100%',
                boxSizing: 'border-box',
                padding: '7px 10px',
              }}
              onFocus={e => (e.target.style.borderColor = 'var(--border-hi)')}
              onBlur={e => (e.target.style.borderColor = 'var(--border)')}
            />
          </div>

          {/* Infra checks */}
          <div style={s.panel}>
            <div style={s.panelTitle}>
              ALTYAPI STATUS
              <div style={s.panelTitleLine} />
              <button
                onClick={runInfraCheck}
                disabled={checkingInfra}
                style={{ ...s.btn(checkingInfra), padding: '3px 8px', fontSize: '8px' }}
              >
                {checkingInfra ? 'CHK...' : 'RUN'}
              </button>
            </div>
            {infra.map(item => (
              <div key={item.key} style={s.infraRow}>
                <div style={s.statusDot(item.status)} />
                <div style={s.infraName}>{item.name}</div>
                <div style={s.infraCmd}>{item.cmd}</div>
                <div style={s.infraStatus(item.status)}>
                  {item.status === 'idle' ? '---' : item.status === 'checking' ? 'CHK' : item.status.toUpperCase()}
                </div>
              </div>
            ))}
            {infraOk && (
              <div style={{ fontSize: '9px', color: 'var(--ph)', marginTop: '10px', letterSpacing: '1px' }}>
                &#10003; TUM SERVISLER OK
              </div>
            )}
          </div>

          {/* Progress */}
          <div style={s.panel}>
            <div style={s.panelTitle}>
              FIX PROGRESS
              <div style={s.panelTitleLine} />
            </div>
            <div style={{ fontSize: '10px', marginBottom: '6px', display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-dim)' }}>VERIFICATION</span>
              <span style={{ color: 'var(--ph)' }}>{progress.checks}%</span>
            </div>
            <div style={s.progressBar}>
              <div style={s.progressFill(progress.checks, 'var(--ph)')} />
            </div>
            <div style={{ fontSize: '10px', marginTop: '12px', marginBottom: '6px', display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-dim)' }}>CRITICAL CHECKS</span>
              <span style={{ color: criticalChecked === criticalTotal ? 'var(--ph)' : 'var(--amber)' }}>
                {criticalChecked}/{criticalTotal}
              </span>
            </div>
            <div style={s.progressBar}>
              <div style={s.progressFill(Math.round((criticalChecked / criticalTotal) * 100), criticalChecked === criticalTotal ? 'var(--ph)' : 'var(--amber)')} />
            </div>
            <div style={{ fontSize: '10px', marginTop: '12px', marginBottom: '6px', display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-dim)' }}>RCA FIELDS</span>
              <span style={{ color: rcaFilled ? 'var(--ph)' : 'var(--red)' }}>
                {rca.filter(f => f.value.trim().length >= 3).length}/{rca.length}
              </span>
            </div>
            <div style={s.progressBar}>
              <div style={s.progressFill(
                Math.round((rca.filter(f => f.value.trim().length >= 3).length / rca.length) * 100),
                rcaFilled ? 'var(--ph)' : 'var(--red)',
              )} />
            </div>
          </div>

          {/* spacer */}
          <div style={{ flex: 1 }} />

          {/* commit gate */}
          <div style={{ padding: '12px' }}>
            <button
              disabled={!allChecked}
              style={{
                ...s.btn(!allChecked),
                width: '100%',
                padding: '12px',
                fontSize: '10px',
              }}
            >
              {allChecked ? '&#10003; COMMIT GATE OPEN' : 'COMMIT LOCKED'}
            </button>
          </div>
        </div>

        {/* ───── CENTER: RCA Form ───── */}
        <div style={{ ...s.col, borderRight: '1px solid var(--border)' }}>
          {/* Gate banner */}
          <div style={s.gate(rcaFilled)}>
            <div style={s.gateIcon(rcaFilled)}>{rcaFilled ? '■' : '□'}</div>
            <div>
              <div style={s.gateText(rcaFilled)}>
                {rcaFilled ? 'RCA GATE UNLOCKED — edit/write SERBEST' : 'RCA GATE LOCKED — edit/write YAPMA'}
              </div>
              <div style={{ fontSize: '9px', color: 'var(--text-dim)', marginTop: '3px' }}>
                {rcaFilled
                  ? 'Root cause dokumentlendi. Fix scope belirlendi.'
                  : 'Tum alanlari doldurmadan kod degisikligi yapma.'}
              </div>
            </div>
          </div>

          <div style={s.centerScroll}>
            {/* RCA table */}
            <div>
              <div style={{ ...s.panelTitle, marginBottom: '16px' }}>
                ROOT CAUSE ANALYSIS
                <div style={s.panelTitleLine} />
              </div>
              <div style={s.rcaForm}>
                {rca.map((field, idx) => (
                  <div key={field.key} style={s.rcaField}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: 'var(--text-dim)', fontSize: '10px' }}>
                        {String(idx + 1).padStart(2, '0')}
                      </span>
                      <span style={s.rcaLabel}>{field.label}</span>
                      {field.value.trim().length >= 3 && (
                        <span style={{ fontSize: '10px', color: 'var(--ph)', marginLeft: 'auto' }}>&#10003;</span>
                      )}
                    </div>
                    <div style={s.rcaHint}>{field.hint}</div>
                    <textarea
                      value={field.value}
                      onChange={e => handleRcaChange(field.key, e.target.value)}
                      placeholder={`> ${field.hint}`}
                      style={s.rcaInput}
                      onFocus={e => (e.target.style.borderColor = 'var(--ph-dim)')}
                      onBlur={e => (e.target.style.borderColor = 'var(--border)')}
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Infra rules reminder */}
            <div style={{ background: 'var(--surface2)', border: '1px solid var(--border)', padding: '14px' }}>
              <div style={{ ...s.panelTitle, marginBottom: '10px' }}>
                DEBUGGING KURALLAR
                <div style={s.panelTitleLine} />
              </div>
              {[
                ['503/500 → ÖNCE altyapı kontrol et', '75% infra sorunu'],
                ['200 + boş data → yanlış tablo veya is_active eksik', 'question_bank kullan'],
                ['Fix ÖNCESI fail test bul — yoksa önce yaz', 'TDD zorunlu'],
                ['3+ dosya → plan mode', 'scope daralt'],
              ].map(([rule, note]) => (
                <div key={rule} style={{ display: 'flex', gap: '10px', padding: '5px 0', borderBottom: '1px solid var(--border)', fontSize: '10px' }}>
                  <span style={{ color: 'var(--ph-dim)', fontWeight: 600 }}>&#9656;</span>
                  <span style={{ flex: 1, color: 'var(--text)' }}>{rule}</span>
                  <span style={{ color: 'var(--text-dim)', fontSize: '9px' }}>{note}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ───── RIGHT: Checks + Log ───── */}
        <div style={{ ...s.col, borderRight: 'none' }}>
          {/* Verification checklist */}
          <div style={{ ...s.panel, flex: '0 0 auto' }}>
            <div style={s.panelTitle}>
              VERIFICATION GATE
              <div style={s.panelTitleLine} />
            </div>
            {checks.map(item => (
              <div
                key={item.id}
                style={s.checkRow(item.checked, item.critical)}
                onClick={() => handleCheck(item.id)}
                role="checkbox"
                aria-checked={item.checked}
                tabIndex={0}
                onKeyDown={e => e.key === ' ' && handleCheck(item.id)}
              >
                <div style={s.checkbox(item.checked, item.critical)}>
                  {item.checked && (
                    <span style={{ color: 'var(--void)', fontSize: '9px', fontWeight: 900 }}>&#10003;</span>
                  )}
                </div>
                <span style={s.checkLabel(item.checked)}>{item.label}</span>
                {item.critical && !item.checked && (
                  <span style={s.criticalBadge}>P0</span>
                )}
              </div>
            ))}
          </div>

          {/* Log stream */}
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
            <div style={{ ...s.panelTitle, padding: '10px 12px 0', flexShrink: 0 }}>
              EVENT LOG
              <div style={s.panelTitleLine} />
              <button
                onClick={() => setLogs(LOG_SEED)}
                style={{ ...s.btn(false), padding: '2px 6px', fontSize: '7px' }}
              >
                CLR
              </button>
            </div>
            <div style={s.logStream}>
              {logs.map(entry => (
                <div key={entry.id} style={s.logEntry}>
                  <span style={s.logTs}>{entry.ts}</span>
                  <span style={s.logLevel(entry.level)}>{entry.level}</span>
                  <span style={s.logMsg(entry.level)}>{entry.msg}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom status bar ── */}
      <div style={s.bottomBar}>
        <div style={s.bottomItem}>
          <div style={{ ...s.statusDot(rcaFilled ? 'ok' : 'error') }} />
          <span style={{ color: rcaFilled ? 'var(--ph)' : 'var(--red)', letterSpacing: '1px' }}>
            RCA {rcaFilled ? 'PASS' : 'REQUIRED'}
          </span>
        </div>
        <div style={s.bottomItem}>
          <div style={{ ...s.statusDot(infraOk ? 'ok' : 'idle') }} />
          <span style={{ color: infraOk ? 'var(--ph)' : 'var(--text-dim)' }}>INFRA {infraOk ? 'OK' : 'UNVERIFIED'}</span>
        </div>
        <div style={s.bottomItem}>
          <div style={{ ...s.statusDot(allChecked ? 'ok' : 'warn') }} />
          <span style={{ color: 'var(--text-dim)' }}>CHECKS {checks.filter(c=>c.checked).length}/{checks.length}</span>
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ color: 'var(--text-dim)', fontSize: '9px', letterSpacing: '2px' }}>
          KIRO2 / 77,336Q / v3.5+ / :5434
        </div>
        <div style={{ color: 'var(--text-dim)', fontSize: '9px' }}>
          <span style={{ animation: 'blink 1.2s step-end infinite', color: 'var(--ph)' }}>&#9646;</span>
        </div>
      </div>
    </div>
  );
};

export default SystematicDebuggingPage;
