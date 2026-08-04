import * as React from 'react';
import { font } from '../tokens';

// Kaynak: KIRO2 Sokratik AI.dc.html — sohbet balonu.
// AI: gradyan avatar + beyaz balon (4/14 köşe). Öğrenci: coral balon sağda.
// Sokratik ton: cevabı vermez, birlikte düşünür — kopya prototipten birebir taşınır.

export interface ChatBubbleProps {
  role: 'ai' | 'me';
  children: React.ReactNode;
  /** AI balonunun altında küçük etiket (örn. "İpucu 2/4") */
  tag?: string;
  tagBg?: string;
  tagFg?: string;
  /** "düşünüyor…" durumu için soluk stil */
  pending?: boolean;
  /** Opsiyonel görsel URL'i veya DataURI */
  image?: string;
}

export function ChatBubble({ role, children, tag, tagBg = '#FFF3EE', tagFg = '#C2452B', pending, image }: ChatBubbleProps) {
  if (role === 'me') {
    return (
      <div style={{ alignSelf: 'flex-end', maxWidth: '78%', background: '#C2452B', color: '#fff',
        borderRadius: '14px 4px 14px 14px', padding: '12px 16px', fontFamily: font.sans,
        fontSize: 14, lineHeight: 1.55, fontWeight: 500, overflowWrap: 'anywhere', wordBreak: 'break-word' }}>
        {image && <img src={image} alt="Kullanıcı görseli" style={{ maxWidth: '100%', borderRadius: 8, marginBottom: children ? 8 : 0, display: 'block' }} />}
        {children}
      </div>
    );
  }
  return (
    <div style={{ display: 'flex', gap: 11, alignItems: 'flex-start', maxWidth: '90%' }}>
      <div aria-hidden style={{ width: 32, height: 32, flexShrink: 0, borderRadius: 9,
        background: 'linear-gradient(135deg,#C2452B,#FF6F5C)', display: 'flex',
        alignItems: 'center', justifyContent: 'center', marginTop: 2 }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M5 12h14a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-6a1 1 0 0 1 1-1ZM12 8V4M8 4h8" />
        </svg>
      </div>
      <div style={{ minWidth: 0 }}>
        <div style={{ background: '#fff', border: '1px solid #ECE6DD', borderRadius: '4px 14px 14px 14px',
          padding: '13px 16px', fontFamily: font.sans, fontSize: 14, color: '#2A2433',
          lineHeight: 1.6, opacity: pending ? 0.65 : 1, overflowWrap: 'anywhere', wordBreak: 'break-word' }}>
          {image && <img src={image} alt="AI görseli" style={{ maxWidth: '100%', borderRadius: 8, marginBottom: children ? 8 : 0, display: 'block' }} />}
          {children}
        </div>
        {tag ? (
          <div style={{ marginTop: 6, display: 'inline-flex', alignItems: 'center', gap: 5,
            fontFamily: font.sans, fontSize: 10.5, fontWeight: 700, color: tagFg,
            background: tagBg, padding: '3px 9px', borderRadius: 7 }}>
            {tag}
          </div>
        ) : null}
      </div>
    </div>
  );
}
