import * as React from 'react';
import { font } from '../tokens';

// Kaynak: KIRO Kenar.dc.html (+ Kenar Veli / Kenar Ogretmen varyantları).
// - Tema: SideNav HER ZAMAN açık (paper) — çalışma yüzeyi.
// - 64px ikon-only daralma: prototipte @container (max-width:150px) ile;
//   üretimde `collapsed` prop'u VEYA aynı container-query korunmalı.
// - Öğrenci navında Ödevlerim ZORUNLU (ödev döngüsü ürün sözü).
// - Rotalar uygulamaya aittir: href'ler preset'te placeholder — kendi router
//   linkinizle sarmak için `renderLink` verin (Next <Link>, RR <NavLink>).

export type SideNavRole = 'ogrenci' | 'veli' | 'ogretmen';

export interface SideNavItem {
  id: string;
  label: string;
  href: string;
  /** 24x24 viewBox, stroke=currentColor, strokeWidth 1.8 bespoke SVG içeriği */
  icon: React.ReactNode;
  /** Sağa yaslı rozet (örn. CAT pili, tekrar sayısı) */
  badge?: React.ReactNode;
}

export interface SideNavSection {
  title: string;
  items: SideNavItem[];
}

const S = { fill: 'none' as const, stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
const ic = (children: React.ReactNode) => (
  <svg width="18" height="18" style={{ flexShrink: 0 }} viewBox="0 0 24 24" {...S}>{children}</svg>
);

/* ---- Bespoke ikon seti (Kenar DC'lerinden birebir path'ler) ---- */
export const NAV_ICONS = {
  panel: ic(<><rect x="3" y="3" width="7" height="7" rx="1.6" /><rect x="14" y="3" width="7" height="7" rx="1.6" /><rect x="14" y="14" width="7" height="7" rx="1.6" /><rect x="3" y="14" width="7" height="7" rx="1.6" /></>),
  plan: ic(<><rect x="3" y="4" width="18" height="17" rx="2" /><path d="M3 9h18M8 2v4M16 2v4" /><path d="m8 14 2.4 2.4L15 12" /></>),
  odev: ic(<><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" /><rect x="8" y="2" width="8" height="4" rx="1" /><path d="M9 12h6M9 16h4" /></>),
  path: ic(<><circle cx="6" cy="6" r="2.4" /><circle cx="6" cy="18" r="2.4" /><circle cx="18" cy="12" r="2.4" /><path d="M6 8.5v7" /><path d="M8.4 18H13a3 3 0 0 0 3-3v-.8" /></>),
  solve: ic(<><path d="M9 11l3 3 8-8" /><path d="M20 12v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h9" /></>),
  cat: ic(<><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="4.2" /><circle cx="12" cy="12" r="0.6" fill="currentColor" /></>),
  review: ic(<><path d="M3 12a9 9 0 0 1 15-6.6L21 8" /><path d="M21 4v4h-4" /><path d="M21 12a9 9 0 0 1-15 6.6L3 16" /><path d="M3 20v-4h4" /></>),
  deneme: ic(<path d="M16 3h5v5M8 3H3v5M21 3 3 21M16 21h5v-5" />),
  assistant: ic(<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2Z" />),
  ai: ic(<path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2Z" />),
  interaktif: ic(<><line x1="4" y1="21" x2="4" y2="14" /><line x1="4" y1="10" x2="4" y2="3" /><line x1="12" y1="21" x2="12" y2="12" /><line x1="12" y1="8" x2="12" y2="3" /><line x1="20" y1="21" x2="20" y2="16" /><line x1="20" y1="12" x2="20" y2="3" /><line x1="1" y1="14" x2="7" y2="14" /><line x1="9" y1="8" x2="15" y2="8" /><line x1="17" y1="16" x2="23" y2="16" /></>),
  practice: ic(<><circle cx="12" cy="12" r="9" /><path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 1.7-2.5 2-2.5 4" /><path d="M12 17h.01" /></>),
  league: ic(<path d="M4 20h16M7 20V10M12 20V5M17 20v-7" />),
  duel: ic(<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z" />),
  boss: ic(<path d="M12 2 4 6v6c0 5 8 10 8 10s8-5 8-10V6Z" />),
  arkadas: ic(<><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /></>),
  seri: ic(<path d="M12 2c1.2 3 4 4.2 4 7.8A4 4 0 0 1 8 10c0-1.4.5-2.4 1-3 .2 1 .9 1.6 1.6 1.6C9.6 6.4 10.8 4.2 12 2Z" />),
  basarim: ic(<><path d="M8 4h8v4a4 4 0 0 1-8 0Z" /><path d="M8 5H5v1a3 3 0 0 0 3 3M16 5h3v1a3 3 0 0 1-3 3" /><path d="M12 12v3" /><path d="M9.5 20h5l-.7-3h-3.6Z" /></>),
  mola: ic(<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />),
  raporlar: ic(<><path d="M3 3v18h18" /><rect x="7" y="10" width="3" height="7" rx="0.8" /><rect x="13" y="6" width="3" height="11" rx="0.8" /></>),
  performans: ic(<><polyline points="22 7 13 16 9 12 2 19" /><polyline points="16 7 22 7 22 13" /></>),
  bildirim: ic(<><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0" /></>),
  icerik: ic(<><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" /></>),
  ogrenci: ic(<><circle cx="12" cy="8" r="4" /><path d="M4 21v-1a8 8 0 0 1 16 0v1" /></>),
  ayarlar: ic(<><circle cx="12" cy="12" r="3.2" /><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1" /></>),
} as const;

/* ---- Rol preset'leri — href'leri kendi rotalarınızla değiştirin ---- */
export const STUDENT_NAV: SideNavSection[] = [
  { title: 'Çalışma', items: [
    { id: 'panel', label: 'Panel', href: '/panel', icon: NAV_ICONS.panel },
    { id: 'plan', label: 'Haftalık Plan', href: '/plan', icon: NAV_ICONS.plan },
    { id: 'odev', label: 'Ödevlerim', href: '/odevlerim', icon: NAV_ICONS.odev },
    { id: 'path', label: 'Öğrenme Yolu', href: '/ogrenme-yolu', icon: NAV_ICONS.path },
    { id: 'solve', label: 'Soru Çözme', href: '/soru-cozme', icon: NAV_ICONS.solve },
    { id: 'cat', label: 'Adaptif Test', href: '/adaptif-test', icon: NAV_ICONS.cat },
    { id: 'review', label: 'Tekrar', href: '/tekrar', icon: NAV_ICONS.review },
    { id: 'deneme', label: 'Harmanlanmış Deneme', href: '/deneme', icon: NAV_ICONS.deneme },
  ]},
  { title: 'AI & Çözüm', items: [
    { id: 'assistant', label: 'AI Sohbet', href: '/ai-sohbet', icon: NAV_ICONS.assistant },
    { id: 'ai', label: 'Sokratik AI', href: '/sokratik', icon: NAV_ICONS.ai },
    { id: 'interaktif', label: 'İnteraktif Çözüm', href: '/interaktif-cozum', icon: NAV_ICONS.interaktif },
    { id: 'practice', label: 'Neden Geri Bildirim', href: '/neden', icon: NAV_ICONS.practice },
  ]},
  { title: 'Yarışma & Seri', items: [
    { id: 'league', label: 'Lig Sıralaması', href: '/lig', icon: NAV_ICONS.league },
    { id: 'duel', label: '1v1 Düello', href: '/duello', icon: NAV_ICONS.duel },
    { id: 'boss', label: 'Boss Savaşı', href: '/boss', icon: NAV_ICONS.boss },
    { id: 'arkadas', label: 'Arkadaş Serisi', href: '/arkadas-serisi', icon: NAV_ICONS.arkadas },
    { id: 'seri', label: 'Seri & Nudge', href: '/seri', icon: NAV_ICONS.seri },
    { id: 'basarim', label: 'Başarımlar', href: '/basarimlar', icon: NAV_ICONS.basarim },
    { id: 'mola', label: 'Mola', href: '/mola', icon: NAV_ICONS.mola },
  ]},
];

export const PARENT_NAV: SideNavSection[] = [
  { title: 'Genel', items: [
    { id: 'overview', label: 'Genel Bakış', href: '/veli', icon: NAV_ICONS.panel },
    { id: 'children', label: 'Çocuklarım', href: '/veli/cocuklarim', icon: NAV_ICONS.arkadas },
  ]},
  { title: 'Takip', items: [
    { id: 'reports', label: 'Raporlar', href: '/veli/raporlar', icon: NAV_ICONS.raporlar },
    { id: 'performance', label: 'Performans', href: '/veli/performans', icon: NAV_ICONS.performans },
    { id: 'notifications', label: 'Bildirimler', href: '/veli/bildirimler', icon: NAV_ICONS.bildirim },
  ]},
  { title: 'İletişim', items: [
    { id: 'messages', label: 'Öğretmen Mesajları', href: '/veli/mesajlar', icon: NAV_ICONS.assistant },
  ]},
];

export const TEACHER_NAV: SideNavSection[] = [
  { title: 'Genel', items: [
    { id: 'panel', label: 'Panel', href: '/ogretmen', icon: NAV_ICONS.panel },
  ]},
  { title: 'Sınıf', items: [
    { id: 'classes', label: 'Sınıflarım', href: '/ogretmen/siniflar', icon: NAV_ICONS.arkadas },
    { id: 'students', label: 'Öğrenciler', href: '/ogretmen/ogrenciler', icon: NAV_ICONS.ogrenci },
  ]},
  { title: 'Öğretim', items: [
    { id: 'assignments', label: 'Ödevler', href: '/ogretmen/odevler', icon: NAV_ICONS.odev },
    { id: 'content', label: 'İçerik & Sorular', href: '/ogretmen/icerik', icon: NAV_ICONS.icerik },
    { id: 'reports', label: 'Raporlar', href: '/ogretmen/raporlar', icon: NAV_ICONS.raporlar },
  ]},
];

const PRESET: Record<SideNavRole, SideNavSection[]> = {
  ogrenci: STUDENT_NAV, veli: PARENT_NAV, ogretmen: TEACHER_NAV,
};

export interface SideNavProps {
  role?: SideNavRole;
  /** Preset yerine özel bölümler */
  sections?: SideNavSection[];
  activeId: string;
  accent?: string;
  /** 64px ikon-only mod (prototipte container-query karşılığı) */
  collapsed?: boolean;
  userName: string;
  userSub: string;
  /** Router entegrasyonu: (item, children, style...) → link elemanı */
  renderLink?: (item: SideNavItem, children: React.ReactNode, props: { style: React.CSSProperties; 'aria-label': string; 'aria-current'?: 'page' }) => React.ReactNode;
  /** Alt köşedeki KIRO Asistan düğmesi (yalnız öğrenci navında göster) */
  onAssistant?: () => void;
  /** Ayarlar en altta (veli/öğretmen navında prototip böyle) */
  showSettings?: boolean;
  settingsHref?: string;
}

export function SideNav({
  role = 'ogrenci', sections, activeId, accent = '#FF6F5C', collapsed = false,
  userName, userSub, renderLink, onAssistant, showSettings = false, settingsHref = '/ayarlar',
}: SideNavProps) {
  const secs = sections ?? PRESET[role];
  const initials = userName.split(' ').map((p) => p[0]).join('').slice(0, 2).toUpperCase();

  const itemStyle = (active: boolean): React.CSSProperties => ({
    display: 'flex', alignItems: 'center',
    gap: collapsed ? 0 : 11,
    justifyContent: collapsed ? 'center' : undefined,
    padding: collapsed ? '9px 0' : '9px 10px',
    minHeight: 44,
    borderRadius: 10, cursor: 'pointer', textDecoration: 'none',
    fontWeight: active ? 700 : 600,
    background: active ? '#FFF3EE' : undefined,
    color: active ? accent : '#6B6478',
    fontFamily: font.sans, fontSize: 14,
  });

  const renderItem = (item: SideNavItem) => {
    const active = item.id === activeId;
    const inner = (
      <>
        {item.icon}
        {!collapsed && <span>{item.label}</span>}
        {!collapsed && item.badge != null && <span style={{ marginLeft: 'auto' }}>{item.badge}</span>}
      </>
    );
    const linkProps = { style: itemStyle(active), 'aria-label': item.label, ...(active ? { 'aria-current': 'page' as const } : {}) };
    return renderLink
      ? <React.Fragment key={item.id}>{renderLink(item, inner, linkProps)}</React.Fragment>
      : <a key={item.id} href={item.href} {...linkProps}>{inner}</a>;
  };

  return (
    <aside style={{ width: collapsed ? 64 : 250, flexShrink: 0, background: '#FFFFFF',
      borderRight: '1px solid #ECE6DD', display: 'flex', flexDirection: 'column',
      height: '100vh', position: 'sticky', top: 0, overflow: 'hidden',
      fontFamily: font.sans, fontSize: 14, color: '#2A2433' }}>

      {/* Logo */}
      <div style={{ flexShrink: 0, padding: collapsed ? '18px 0 12px' : '18px 16px 12px',
        display: 'flex', justifyContent: collapsed ? 'center' : 'flex-start' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: collapsed ? 0 : '0 6px' }}>
          <div aria-hidden style={{ width: 34, height: 34, flexShrink: 0, borderRadius: 10, background: accent,
            display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: `0 4px 12px -3px ${accent}66` }}>
            <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 3 3 8l9 5 9-5-9-5Z" /><path d="M3 16l9 5 9-5" /><path d="M3 12l9 5 9-5" />
            </svg>
          </div>
          {!collapsed && (
            <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
              <span style={{ fontWeight: 800, fontSize: 17, letterSpacing: '-0.02em', color: '#2A2433' }}>
                KIRO<span style={{ color: accent }}>2</span>
              </span>
              <span style={{ fontSize: 10.5, fontWeight: 600, color: '#6B6478', letterSpacing: '0.02em' }}>YKS Hazırlık</span>
            </div>
          )}
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: collapsed ? '2px 8px 8px' : '2px 14px 8px',
        display: 'flex', flexDirection: 'column' }}>
        {secs.map((sec, i) => (
          <React.Fragment key={sec.title}>
            {!collapsed && (
              <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '0.07em', color: '#6B6478',
                textTransform: 'uppercase', padding: '0 10px', margin: i === 0 ? '4px 0 6px' : '16px 0 6px' }}>
                {sec.title}
              </div>
            )}
            {sec.items.map(renderItem)}
          </React.Fragment>
        ))}
        {showSettings && (
          <>
            <div style={{ flex: 1 }} />
            {renderItem({ id: 'settings', label: 'Ayarlar', href: settingsHref, icon: NAV_ICONS.ayarlar })}
          </>
        )}
      </nav>

      {/* Footer */}
      <div style={{ flexShrink: 0, padding: collapsed ? '8px 8px 14px' : '8px 14px 14px' }}>
        {onAssistant && (
          <button type="button" onClick={onAssistant} aria-label="KIRO Asistan"
            style={{ display: 'flex', alignItems: 'center', width: '100%', border: 'none',
              gap: collapsed ? 0 : 11, justifyContent: collapsed ? 'center' : undefined,
              padding: collapsed ? '11px 0' : '11px 12px', minHeight: 44, borderRadius: 12,
              background: '#2A2433', color: '#fff', fontFamily: font.sans, fontSize: 14,
              fontWeight: 700, cursor: 'pointer', marginBottom: 8 }}>
            <svg width="18" height="18" style={{ flexShrink: 0 }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2Z" /><path d="m11 8 1 2 2 1-2 1-1 2-1-2-2-1 2-1Z" />
            </svg>
            {!collapsed && <span>KIRO Asistan</span>}
            {!collapsed && (
              <svg style={{ marginLeft: 'auto' }} width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 6 15 12 9 18" />
              </svg>
            )}
          </button>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '9px 8px',
          justifyContent: collapsed ? 'center' : undefined, borderTop: '1px solid #ECE6DD' }}>
          <div aria-hidden style={{ width: 34, height: 34, flexShrink: 0, borderRadius: 10,
            background: 'linear-gradient(135deg,#2A2433,#4A4456)', color: '#fff', display: 'flex',
            alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 13 }}>
            {initials}
          </div>
          {!collapsed && (
            <div style={{ lineHeight: 1.2, minWidth: 0 }}>
              <div style={{ fontWeight: 700, fontSize: 13, color: '#2A2433', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{userName}</div>
              <div style={{ fontSize: 11, color: '#6B6478' }}>{userSub}</div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
