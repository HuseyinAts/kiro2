import * as React from 'react';

import { color, font, motion, radius } from '../tokens';
import type { HaftaGun } from '../types';
import { useReducedMotion } from './ConfettiDawn';

// Kaynak: KIRO2 Öğrenci-Özeti / Veli Paneli DC — haftalık çalışma çubukları.
// PAYLAŞILAN: Veli · Öğretmen · Öğrenci-Özeti panelleri kullanır.
// KANON:
//  - Layout-anim YASAK: yükseklik/margin ANİMASYONU yok; büyüme YALNIZ transform:scaleY
//    (+ opacity). Nihai yükseklik statik `height:%` ile (animasyon değil layout).
//  - prefers-reduced-motion → animasyon TAMAMEN kapalı (keyframes bile enjekte edilmez).
//  - Her çubuk görünmez SR metni taşır ("{label}: {dk} dk"); görünen gün etiketi aria-hidden
//    (çift okuma olmasın). Grup adı ariaLabel prop'undan.
//  - Aktif = dawn coral (dekoratif dolgu), pasif = şeftali tint (kaygı-duyarlı, alarm değil).
//  - box-sizing:border-box her kapta.
// SUNUCU-OTORİTE: dk/aktif sunucudan gelir; bileşen metrik HESAPLAMAZ (yalnız yükseklik oranı).

const AKTIF = color.dawn.coral;   // #FF6F5C — çalışma olan gün
const PASIF = '#FFD3C4';          // şeftali tint — çalışma yok (DC kanon inaktif rengi)

const GROW =
  '@keyframes kiroBarGrow { from { transform: scaleY(0); opacity: 0.55; } to { transform: scaleY(1); opacity: 1; } }';

const SR_ONLY: React.CSSProperties = {
  position: 'absolute',
  width: 1,
  height: 1,
  padding: 0,
  margin: -1,
  overflow: 'hidden',
  clip: 'rect(0 0 0 0)',
  whiteSpace: 'nowrap',
  border: 0,
};

export interface WeeklyActivityBarsProps {
  /** 7 günlük çalışma (label + dk + aktif) — sunucudan; bileşen metrik ÜRETMEZ */
  gunler: HaftaGun[];
  /** Çubuk grubunun erişilebilir adı (ör. "Haftalık aktivite") */
  ariaLabel: string;
  /** Opsiyonel başlık toplamı (saat) — verilirse üstte "X sa" satırı çizilir */
  toplamSa?: number;
  /** Opsiyonel trend etiketi (ör. "+1,1 sa") — yeşil gösterilir */
  trend?: string;
  /** Çubuk alanı yüksekliği (px) */
  height?: number;
}

/** Haftalık aktivite çubukları (bespoke div-bar; transform-only büyüme, SR-erişilebilir). */
export function WeeklyActivityBars({ gunler, ariaLabel, toplamSa, trend, height = 96 }: WeeklyActivityBarsProps) {
  const reduced = useReducedMotion();
  const maxDk = Math.max(1, ...gunler.map((g) => g.dk));

  return (
    <div style={{ boxSizing: 'border-box', width: '100%' }}>
      {toplamSa != null ? (
        <div style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 12 }}>
          <span style={{ fontFamily: font.sans, fontVariantNumeric: 'tabular-nums', fontSize: 20, fontWeight: 800, color: color.ink.primary }}>
            {String(toplamSa).replace('.', ',')}
            <span style={{ fontSize: 13, fontWeight: 600, color: color.ink.muted }}> sa</span>
          </span>
          {trend ? (
            <span style={{ fontFamily: font.sans, fontVariantNumeric: 'tabular-nums', fontSize: 11.5, fontWeight: 700, color: color.semantic.success }}>
              {trend}
            </span>
          ) : null}
        </div>
      ) : null}

      {!reduced ? <style>{GROW}</style> : null}

      <div
        role="group"
        aria-label={ariaLabel}
        style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'flex-end', gap: 10, height }}
      >
        {gunler.map((g, i) => {
          const pct = Math.max(6, Math.round((g.dk / maxDk) * 100));
          return (
            <div
              key={g.label + '-' + i}
              style={{
                boxSizing: 'border-box',
                flex: 1,
                minWidth: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 8,
                height: '100%',
                justifyContent: 'flex-end',
              }}
            >
              <div style={{ boxSizing: 'border-box', width: '100%', height: '100%', display: 'flex', alignItems: 'flex-end' }}>
                <div
                  style={{
                    boxSizing: 'border-box',
                    width: '100%',
                    height: `${pct}%`,
                    borderRadius: `${radius.chip}px ${radius.chip}px 3px 3px`,
                    background: g.aktif ? AKTIF : PASIF,
                    transformOrigin: 'bottom',
                    animation: reduced
                      ? undefined
                      : `kiroBarGrow 0.5s ${motion.easing} ${Math.min(i * 0.05, 0.3)}s both`,
                  }}
                />
              </div>
              <span aria-hidden="true" style={{ fontFamily: font.sans, fontSize: 11, fontWeight: 600, color: color.ink.muted }}>
                {g.label}
              </span>
              <span style={SR_ONLY}>{`${g.label}: ${g.dk} dk`}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
