// ============================================================================
// KIRO2 — Faz 1 örnek sayfa: configureKiroApi mock modu render kanıtı.
// Amaç: tokens + types + api-client derlenir + mock modda kiro-data.json akar.
// Ekran türü = analitik/panel → PAPER teması (kanon: tema toggle DEĞİL, ekran türü).
// Motorlar (θ/CAT/FSRS/BKT) SUNUCUDA; burada yalnız sunucu-otoriter veriyi render ederiz.
// ============================================================================
import * as React from 'react';

import { getMe, getSubjects, getLevel } from '../api/api-client';
import { color, radius, space } from '../tokens';
import type { Persona, Subject, SeviyeBilgi } from '../types';
import { KiroThemeProvider, surf, baseText, numText } from '../ui/theme';
import '../tokens/tokens.css';

// Mock modda yapılandır — ekran kodu YALNIZ api-client'ı çağırır (mock→live tek konfig).

export function OrnekPage(): React.ReactElement {
  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [subjects, setSubjects] = React.useState<Subject[]>([]);
  const [level, setLevel] = React.useState<SeviyeBilgi | null>(null);
  const [hata, setHata] = React.useState<string | null>(null);

  React.useEffect(() => {
    let alive = true;
    Promise.all([getMe(), getSubjects(), getLevel()])
      .then(([p, s, l]) => {
        if (!alive) return;
        setPersona(p);
        setSubjects(s);
        setLevel(l);
      })
      .catch((e: unknown) => {
        if (alive) setHata(e instanceof Error ? e.message : 'Bilinmeyen hata');
      });
    return () => {
      alive = false;
    };
  }, []);

  const s = surf('paper');

  return (
    <KiroThemeProvider theme="paper">
      <div
        className="k-paper"
        style={{ ...baseText, background: s.bg, color: s.text, minHeight: '100vh', padding: space[7] }}
      >
        <h1 style={{ fontSize: 24, fontWeight: 800, margin: 0 }}>KIRO2 · Kiro alanı hazır</h1>
        <p style={{ color: s.muted, marginTop: space[2] }}>
          Mock modda api-client → kiro-data.json akıyor (motorlar sunucuda).
        </p>

        {hata ? (
          <p style={{ color: color.semantic.riskTextOnLight, marginTop: space[4] }} data-testid="hata">
            {hata}
          </p>
        ) : !persona || !level ? (
          <p style={{ color: s.muted, marginTop: space[4] }} data-testid="yukleniyor">
            Yükleniyor…
          </p>
        ) : (
          <section style={{ marginTop: space[5] }}>
            <div
              style={{
                background: s.card,
                border: `1px solid ${s.border}`,
                borderRadius: radius.card,
                padding: space[5],
              }}
            >
              <div style={{ fontSize: 17, fontWeight: 700 }} data-testid="persona-ad">
                {persona.ad}
              </div>
              <div style={{ color: s.muted, marginTop: space[1] }}>
                <span style={numText}>{persona.sinif}</span> · Seviye{' '}
                <span style={numText} data-testid="seviye">
                  {level.seviye}
                </span>{' '}
                · Seri <span style={numText}>{persona.seri}</span> gün
              </div>
            </div>

            <ul
              style={{
                listStyle: 'none',
                padding: 0,
                marginTop: space[4],
                display: 'grid',
                gap: space[2],
              }}
              data-testid="ders-listesi"
            >
              {subjects.map((d) => (
                <li
                  key={d.key}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    background: s.card,
                    border: `1px solid ${s.border}`,
                    borderRadius: radius.chip,
                    padding: `${space[2]}px ${space[4]}px`,
                  }}
                >
                  <span>{d.ad}</span>
                  <span style={numText}>%{d.hakimiyet}</span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </KiroThemeProvider>
  );
}

export default OrnekPage;
