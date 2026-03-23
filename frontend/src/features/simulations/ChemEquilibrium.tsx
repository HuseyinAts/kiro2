/**
 * ChemEquilibrium — Interactive Le Chatelier's Principle simulation
 * FAZ-6: 3D Simulasyon Modüller
 *
 * Visualizes a chemical equilibrium A + B ⇌ C + D
 * Interactive controls: temperature, pressure, concentration
 */
import React, { useEffect, useRef, useState, useCallback } from 'react';
import { ErrorBoundary3D } from './ErrorBoundary3D';
import { LoadingSkeleton3D } from './LoadingSkeleton3D';

interface Molecule {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  type: 'A' | 'B' | 'C' | 'D';
  radius: number;
}


const MOLECULE_COLORS: Record<string, string> = {
  A: '#3B82F6',
  B: '#EF4444',
  C: '#10B981',
  D: '#F59E0B',
};

const MOLECULE_LABELS: Record<string, string> = {
  A: 'A',
  B: 'B',
  C: 'C',
  D: 'D',
};

const CANVAS_W = 560;
const CANVAS_H = 300;
const MOLECULE_R = 14;
const N_MOLECULES = 30;

function calcKEq(temperature: number): number {
  // Exothermic reaction: K decreases with T (van't Hoff)
  // K = exp(-ΔH/RT + ΔS/R) simplified
  const dH = -20000; // J/mol
  const R = 8.314;
  return Math.exp(-dH / (R * temperature)) * 0.001;
}

function initMolecules(): Molecule[] {
  return Array.from({ length: N_MOLECULES }, (_, i) => ({
    id: i,
    x: 20 + Math.random() * (CANVAS_W - 40),
    y: 20 + Math.random() * (CANVAS_H - 40),
    vx: (Math.random() - 0.5) * 2,
    vy: (Math.random() - 0.5) * 2,
    type: ((['A', 'B', 'C', 'D'] as const)[Math.floor(Math.random() * 4)]),
    radius: MOLECULE_R,
  }));
}

function countTypes(mols: Molecule[]) {
  return {
    A: mols.filter((m) => m.type === 'A').length,
    B: mols.filter((m) => m.type === 'B').length,
    C: mols.filter((m) => m.type === 'C').length,
    D: mols.filter((m) => m.type === 'D').length,
  };
}

function drawMolecules(
  ctx: CanvasRenderingContext2D,
  molecules: Molecule[],
  w: number,
  h: number
) {
  ctx.clearRect(0, 0, w, h);

  // Background
  ctx.fillStyle = '#0F172A';
  ctx.fillRect(0, 0, w, h);

  // Grid dots
  ctx.fillStyle = 'rgba(255,255,255,0.04)';
  for (let x = 20; x < w; x += 40) {
    for (let y = 20; y < h; y += 40) {
      ctx.beginPath();
      ctx.arc(x, y, 1, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // Equilibrium divider
  ctx.strokeStyle = 'rgba(255,255,255,0.1)';
  ctx.setLineDash([6, 4]);
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(w / 2, 10);
  ctx.lineTo(w / 2, h - 10);
  ctx.stroke();
  ctx.setLineDash([]);

  // Labels
  ctx.fillStyle = 'rgba(255,255,255,0.2)';
  ctx.font = '10px system-ui';
  ctx.textAlign = 'center';
  ctx.fillText('Reaktanlar (A+B)', w / 4, h - 8);
  ctx.fillText('Ürünler (C+D)', (3 * w) / 4, h - 8);

  // Molecules
  molecules.forEach((m) => {
    const color = MOLECULE_COLORS[m.type];

    // Glow
    const grad = ctx.createRadialGradient(m.x, m.y, 0, m.x, m.y, m.radius * 2);
    grad.addColorStop(0, color + '40');
    grad.addColorStop(1, 'transparent');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(m.x, m.y, m.radius * 2, 0, Math.PI * 2);
    ctx.fill();

    // Body
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(m.x, m.y, m.radius, 0, Math.PI * 2);
    ctx.fill();

    // Highlight
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    ctx.beginPath();
    ctx.arc(m.x - m.radius * 0.3, m.y - m.radius * 0.3, m.radius * 0.35, 0, Math.PI * 2);
    ctx.fill();

    // Label
    ctx.fillStyle = 'white';
    ctx.font = `bold ${m.radius * 0.9}px system-ui`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(MOLECULE_LABELS[m.type], m.x, m.y);
    ctx.textBaseline = 'alphabetic';
  });
}

const ChemSimCore: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const molsRef = useRef<Molecule[]>(initMolecules());

  const [temperature, setTemperature] = useState(400);
  const [pressure, setPressure] = useState(1.0);
  const [counts, setCounts] = useState({ A: 0, B: 0, C: 0, D: 0 });
  const [kEq, setKEq] = useState(calcKEq(400));
  const [isRunning, setIsRunning] = useState(true);

  const stepSimulation = useCallback(
    (mols: Molecule[], temp: number, pres: number, k: number): Molecule[] => {
      const speedFactor = Math.sqrt(temp / 400) * pres;

      const updated = mols.map((m) => {
        let { x, y, vx, vy } = m;
        vx *= speedFactor / Math.sqrt(speedFactor); // normalize speed variation
        vx = Math.max(-4, Math.min(4, vx + (Math.random() - 0.5) * 0.3));
        vy = Math.max(-4, Math.min(4, vy + (Math.random() - 0.5) * 0.3));
        x += vx;
        y += vy;

        // Wall bounce
        if (x < m.radius) { x = m.radius; vx = Math.abs(vx); }
        if (x > CANVAS_W - m.radius) { x = CANVAS_W - m.radius; vx = -Math.abs(vx); }
        if (y < m.radius) { y = m.radius; vy = Math.abs(vy); }
        if (y > CANVAS_H - m.radius) { y = CANVAS_H - m.radius; vy = -Math.abs(vy); }

        return { ...m, x, y, vx, vy };
      });

      // Collision + reaction
      for (let i = 0; i < updated.length; i++) {
        for (let j = i + 1; j < updated.length; j++) {
          const a = updated[i];
          const b = updated[j];
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < a.radius + b.radius) {
            // Elastic bounce
            const angle = Math.atan2(dy, dx);
            const sin = Math.sin(angle);
            const cos = Math.cos(angle);
            const vx1 = a.vx * cos + a.vy * sin;
            const vy1 = -a.vx * sin + a.vy * cos;
            const vx2 = b.vx * cos + b.vy * sin;
            const vy2 = -b.vx * sin + b.vy * cos;
            updated[i] = { ...a, vx: vx2 * cos - vy1 * sin, vy: vx2 * sin + vy1 * cos };
            updated[j] = { ...b, vx: vx1 * cos - vy2 * sin, vy: vx1 * sin + vy2 * cos };

            // Reaction chance
            const reactionProb = Math.min(0.05, 0.01 * speedFactor);
            if (Math.random() < reactionProb) {
              const cnt = countTypes(updated);
              const q = (cnt.C * cnt.D) / Math.max(1, cnt.A * cnt.B);

              if (a.type === 'A' && b.type === 'B' && q < k * 2) {
                // Forward: A+B → C+D
                updated[i] = { ...updated[i], type: 'C' };
                updated[j] = { ...updated[j], type: 'D' };
              } else if (a.type === 'C' && b.type === 'D' && q > k * 0.5) {
                // Reverse: C+D → A+B
                updated[i] = { ...updated[i], type: 'A' };
                updated[j] = { ...updated[j], type: 'B' };
              }
            }
          }
        }
      }

      return updated;
    },
    []
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let frame = 0;

    const animate = () => {
      if (isRunning) {
        molsRef.current = stepSimulation(molsRef.current, temperature, pressure, kEq);
        if (frame % 10 === 0) {
          setCounts(countTypes(molsRef.current));
        }
        frame++;
      }
      drawMolecules(ctx, molsRef.current, CANVAS_W, CANVAS_H);
      animRef.current = requestAnimationFrame(animate);
    };

    animRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animRef.current);
  }, [isRunning, temperature, pressure, kEq, stepSimulation]);

  const handleTempChange = (v: number) => {
    setTemperature(v);
    setKEq(calcKEq(v));
  };

  const handleReset = () => {
    molsRef.current = initMolecules();
    setCounts({ A: 0, B: 0, C: 0, D: 0 });
  };

  const total = counts.A + counts.B + counts.C + counts.D || 1;

  return (
    <div className="rounded-2xl overflow-hidden border border-white/10 bg-gray-900 p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-white font-bold font-display text-sm">
            Kimyasal Denge Simülasyonu
          </h3>
          <p className="text-white/40 text-xs">A + B ⇌ C + D (Le Chatelier İlkesi)</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setIsRunning((v) => !v)}
            className="text-xs px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors"
          >
            {isRunning ? '⏸ Durdur' : '▶ Başlat'}
          </button>
          <button
            onClick={handleReset}
            className="text-xs px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors"
          >
            ↺ Sıfırla
          </button>
        </div>
      </div>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        width={CANVAS_W}
        height={CANVAS_H}
        className="w-full rounded-xl"
        style={{ imageRendering: 'pixelated' }}
      />

      {/* Molecule count bars */}
      <div className="grid grid-cols-4 gap-2">
        {(['A', 'B', 'C', 'D'] as const).map((t) => (
          <div key={t} className="text-center">
            <div className="h-16 flex items-end justify-center mb-1">
              <div
                className="w-8 rounded-t-lg transition-all duration-300"
                style={{
                  height: `${(counts[t] / total) * 64}px`,
                  background: MOLECULE_COLORS[t],
                  minHeight: 4,
                }}
              />
            </div>
            <p className="text-xs font-bold" style={{ color: MOLECULE_COLORS[t] }}>
              {t}: {counts[t]}
            </p>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <label className="flex justify-between text-xs text-white/60">
            <span>🌡 Sıcaklık</span>
            <span className="text-white font-mono">{temperature} K</span>
          </label>
          <input
            type="range"
            min={200}
            max={800}
            value={temperature}
            onChange={(e) => handleTempChange(Number(e.target.value))}
            className="w-full accent-red-500"
          />
          <p className="text-xs text-white/30">
            {temperature > 500 ? '↑ Ters reaksiyon artar (ekzotermik)' : '↓ İleri reaksiyon avantajlı'}
          </p>
        </div>

        <div className="space-y-1">
          <label className="flex justify-between text-xs text-white/60">
            <span>⚡ Basınç</span>
            <span className="text-white font-mono">{pressure.toFixed(1)} atm</span>
          </label>
          <input
            type="range"
            min={5}
            max={30}
            value={pressure * 10}
            onChange={(e) => setPressure(Number(e.target.value) / 10)}
            className="w-full accent-blue-500"
          />
          <p className="text-xs text-white/30">
            K<sub>eq</sub> = {kEq.toFixed(4)}
          </p>
        </div>
      </div>

      {/* Info box */}
      <div className="bg-white/5 rounded-xl p-3 text-xs text-white/60 leading-relaxed">
        <strong className="text-white/80">Le Chatelier İlkesi:</strong>{' '}
        Bir denge sistemi bozulunca, denge bozulmayı azaltacak yönde kayar.
        Sıcaklığı artırmak ekzotermik tepkimede ters yönü destekler.
      </div>
    </div>
  );
};

export const ChemEquilibrium: React.FC = () => (
  <ErrorBoundary3D>
    <React.Suspense fallback={<LoadingSkeleton3D label="Kimya simülasyonu yükleniyor..." />}>
      <ChemSimCore />
    </React.Suspense>
  </ErrorBoundary3D>
);

export default ChemEquilibrium;
