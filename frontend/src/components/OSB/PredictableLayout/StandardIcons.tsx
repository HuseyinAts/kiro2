/**
 * Task 93.4: Standard Icons Library
 * OSB desteği için evrensel ve tutarlı ikon sistemi
 *
 * Özellikler:
 * - Evrensel, tanınmış ikonlar
 * - Her ikon her zaman aynı anlama gelir
 * - Tutarlı ikon stili
 * - Her ikonda etiket (label) mevcut
 */

import React from 'react';
import './StandardIcons.css';

/**
 * Standart ikon tipleri
 * Her ikon ASLA değişmez ve her zaman aynı anlama gelir
 */
export type StandardIconType =
  // Navigation icons
  | 'home'          // Ev - Ana sayfa
  | 'back'          // Geri ok
  | 'forward'       // İleri ok
  | 'menu'          // Hamburger menü
  | 'close'         // Kapatma (X)

  // Action icons
  | 'add'           // Artı (+)
  | 'remove'        // Eksi (-)
  | 'edit'          // Düzenleme (kalem)
  | 'delete'        // Silme (çöp kutusu)
  | 'save'          // Kaydet (disk)
  | 'download'      // İndir
  | 'upload'        // Yükle
  | 'print'         // Yazdır
  | 'share'         // Paylaş

  // Status icons
  | 'success'       // Başarı (✓)
  | 'error'         // Hata (X)
  | 'warning'       // Uyarı (!)
  | 'info'          // Bilgi (i)
  | 'help'          // Yardım (?)

  // Content icons
  | 'document'      // Döküman
  | 'image'         // Resim
  | 'video'         // Video
  | 'audio'         // Ses
  | 'folder'        // Klasör
  | 'file'          // Dosya

  // User icons
  | 'user'          // Kullanıcı
  | 'users'         // Kullanıcılar (grup)
  | 'profile'       // Profil
  | 'settings'      // Ayarlar

  // Communication icons
  | 'email'         // E-posta
  | 'phone'         // Telefon
  | 'chat'          // Sohbet
  | 'notification'  // Bildirim

  // Education icons
  | 'book'          // Kitap
  | 'exam'          // Sınav
  | 'question'      // Soru
  | 'answer'        // Cevap
  | 'quiz'          // Quiz
  | 'study'         // Çalışma
  | 'calendar'      // Takvim
  | 'clock'         // Saat

  // UI icons
  | 'search'        // Arama
  | 'filter'        // Filtre
  | 'sort'          // Sıralama
  | 'view-list'     // Liste görünümü
  | 'view-grid'     // Grid görünümü
  | 'expand'        // Genişlet
  | 'collapse';     // Daralt

/**
 * Her ikon için sabit SVG tanımları
 * Bu tanımlar ASLA değişmez
 */
const ICON_PATHS: Record<StandardIconType, { path: string; viewBox: string }> = {
  // Navigation
  home: {
    path: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10',
    viewBox: '0 0 24 24'
  },
  back: {
    path: 'M19 12H5 M12 19l-7-7 7-7',
    viewBox: '0 0 24 24'
  },
  forward: {
    path: 'M5 12h14 M12 5l7 7-7 7',
    viewBox: '0 0 24 24'
  },
  menu: {
    path: 'M3 12h18 M3 6h18 M3 18h18',
    viewBox: '0 0 24 24'
  },
  close: {
    path: 'M18 6L6 18 M6 6l12 12',
    viewBox: '0 0 24 24'
  },

  // Actions
  add: {
    path: 'M12 5v14 M5 12h14',
    viewBox: '0 0 24 24'
  },
  remove: {
    path: 'M5 12h14',
    viewBox: '0 0 24 24'
  },
  edit: {
    path: 'M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7 M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z',
    viewBox: '0 0 24 24'
  },
  delete: {
    path: 'M3 6h18 M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2 M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6',
    viewBox: '0 0 24 24'
  },
  save: {
    path: 'M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z M17 21v-8H7v8 M7 3v5h8',
    viewBox: '0 0 24 24'
  },
  download: {
    path: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4 M7 10l5 5 5-5 M12 15V3',
    viewBox: '0 0 24 24'
  },
  upload: {
    path: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4 M17 8l-5-5-5 5 M12 3v12',
    viewBox: '0 0 24 24'
  },
  print: {
    path: 'M6 9V2h12v7 M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2 M6 14h12v8H6z',
    viewBox: '0 0 24 24'
  },
  share: {
    path: 'M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8 M16 6l-4-4-4 4 M12 2v13',
    viewBox: '0 0 24 24'
  },

  // Status
  success: {
    path: 'M22 11.08V12a10 10 0 1 1-5.93-9.14 M22 4L12 14.01l-3-3',
    viewBox: '0 0 24 24'
  },
  error: {
    path: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z',
    viewBox: '0 0 24 24'
  },
  warning: {
    path: 'M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z M12 9v4 M12 17h.01',
    viewBox: '0 0 24 24'
  },
  info: {
    path: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z',
    viewBox: '0 0 24 24'
  },
  help: {
    path: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z',
    viewBox: '0 0 24 24'
  },

  // Content
  document: {
    path: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8',
    viewBox: '0 0 24 24'
  },
  image: {
    path: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4 M14.5 3H19a2 2 0 0 1 2 2v4.5 M21 14l-5-5L4 21',
    viewBox: '0 0 24 24'
  },
  video: {
    path: 'M23 7l-7 5 7 5V7z M16 5H3a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h13a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2z',
    viewBox: '0 0 24 24'
  },
  audio: {
    path: 'M9 18V5l12-2v13 M9 18c0 1.66-1.34 3-3 3s-3-1.34-3-3 1.34-3 3-3 3 1.34 3 3zm12-2c0 1.66-1.34 3-3 3s-3-1.34-3-3 1.34-3 3-3 3 1.34 3 3z M9 9l12-2',
    viewBox: '0 0 24 24'
  },
  folder: {
    path: 'M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z',
    viewBox: '0 0 24 24'
  },
  file: {
    path: 'M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z M13 2v7h7',
    viewBox: '0 0 24 24'
  },

  // User
  user: {
    path: 'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2 M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
    viewBox: '0 0 24 24'
  },
  users: {
    path: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75',
    viewBox: '0 0 24 24'
  },
  profile: {
    path: 'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2 M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
    viewBox: '0 0 24 24'
  },
  settings: {
    path: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z',
    viewBox: '0 0 24 24'
  },

  // Communication
  email: {
    path: 'M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z M22 6l-10 7L2 6',
    viewBox: '0 0 24 24'
  },
  phone: {
    path: 'M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z',
    viewBox: '0 0 24 24'
  },
  chat: {
    path: 'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z',
    viewBox: '0 0 24 24'
  },
  notification: {
    path: 'M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9 M13.73 21a2 2 0 0 1-3.46 0',
    viewBox: '0 0 24 24'
  },

  // Education
  book: {
    path: 'M4 19.5A2.5 2.5 0 0 1 6.5 17H20 M4 19.5A2.5 2.5 0 0 0 6.5 22H20V2H6.5A2.5 2.5 0 0 0 4 4.5v15z',
    viewBox: '0 0 24 24'
  },
  exam: {
    path: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M9 15h6 M9 18h6 M9 12h1',
    viewBox: '0 0 24 24'
  },
  question: {
    path: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z',
    viewBox: '0 0 24 24'
  },
  answer: {
    path: 'M22 11.08V12a10 10 0 1 1-5.93-9.14 M22 4L12 14.01l-3-3',
    viewBox: '0 0 24 24'
  },
  quiz: {
    path: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M10 9h4 M10 13h4 M10 17h2',
    viewBox: '0 0 24 24'
  },
  study: {
    path: 'M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z',
    viewBox: '0 0 24 24'
  },
  calendar: {
    path: 'M19 4H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z M16 2v4 M8 2v4 M3 10h18',
    viewBox: '0 0 24 24'
  },
  clock: {
    path: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z M12.5 7H11v6l5.25 3.15.75-1.23-4.5-2.67z',
    viewBox: '0 0 24 24'
  },

  // UI
  search: {
    path: 'M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16z M21 21l-4.35-4.35',
    viewBox: '0 0 24 24'
  },
  filter: {
    path: 'M22 3H2l8 9.46V19l4 2v-8.54L22 3z',
    viewBox: '0 0 24 24'
  },
  sort: {
    path: 'M11 5h10 M11 9h7 M11 13h4 M3 17l3 3 3-3 M6 18V4',
    viewBox: '0 0 24 24'
  },
  'view-list': {
    path: 'M8 6h13 M8 12h13 M8 18h13 M3 6h.01 M3 12h.01 M3 18h.01',
    viewBox: '0 0 24 24'
  },
  'view-grid': {
    path: 'M10 3H3v7h7V3z M21 3h-7v7h7V3z M21 14h-7v7h7v-7z M10 14H3v7h7v-7z',
    viewBox: '0 0 24 24'
  },
  expand: {
    path: 'M15 3h6v6 M9 21H3v-6 M21 3l-7 7 M3 21l7-7',
    viewBox: '0 0 24 24'
  },
  collapse: {
    path: 'M4 14l6-6 M10 20h6v-6 M14 4h-6v6 M20 10l-6 6',
    viewBox: '0 0 24 24'
  }
};

/**
 * Türkçe etiketler - her ikon için
 * OSB için mutlaka label gerekli
 */
export const ICON_LABELS: Record<StandardIconType, string> = {
  // Navigation
  home: 'Ana Sayfa',
  back: 'Geri',
  forward: 'İleri',
  menu: 'Menü',
  close: 'Kapat',

  // Actions
  add: 'Ekle',
  remove: 'Çıkar',
  edit: 'Düzenle',
  delete: 'Sil',
  save: 'Kaydet',
  download: 'İndir',
  upload: 'Yükle',
  print: 'Yazdır',
  share: 'Paylaş',

  // Status
  success: 'Başarılı',
  error: 'Hata',
  warning: 'Uyarı',
  info: 'Bilgi',
  help: 'Yardım',

  // Content
  document: 'Döküman',
  image: 'Resim',
  video: 'Video',
  audio: 'Ses',
  folder: 'Klasör',
  file: 'Dosya',

  // User
  user: 'Kullanıcı',
  users: 'Kullanıcılar',
  profile: 'Profil',
  settings: 'Ayarlar',

  // Communication
  email: 'E-posta',
  phone: 'Telefon',
  chat: 'Sohbet',
  notification: 'Bildirim',

  // Education
  book: 'Kitap',
  exam: 'Sınav',
  question: 'Soru',
  answer: 'Cevap',
  quiz: 'Quiz',
  study: 'Çalışma',
  calendar: 'Takvim',
  clock: 'Saat',

  // UI
  search: 'Ara',
  filter: 'Filtrele',
  sort: 'Sırala',
  'view-list': 'Liste Görünümü',
  'view-grid': 'Izgara Görünümü',
  expand: 'Genişlet',
  collapse: 'Daralt'
};

export interface StandardIconProps {
  /** İkon tipi - ASLA değişmez */
  type: StandardIconType;

  /** İkon boyutu (px) - sabit boyutlar */
  size?: 16 | 20 | 24 | 32 | 40 | 48;

  /** İkon rengi */
  color?: string;

  /** Ekstra CSS sınıfı */
  className?: string;

  /** Label göster - OSB için önerilen */
  showLabel?: boolean;

  /** Özel label (varsayılan yerine) */
  label?: string;

  /** Aria label */
  ariaLabel?: string;

  /** Click handler */
  onClick?: () => void;

  /** OSB modu */
  osbMode?: boolean;
}

/**
 * Standart İkon Bileşeni
 * Her ikon evrensel, tanınmış ve her zaman aynı
 */
export const StandardIcon: React.FC<StandardIconProps> = ({
  type,
  size = 24,
  color = 'currentColor',
  className = '',
  showLabel = false,
  label,
  ariaLabel,
  onClick,
  osbMode = true
}) => {
  const iconDef = ICON_PATHS[type];
  const iconLabel = label || ICON_LABELS[type];
  const iconAriaLabel = ariaLabel || iconLabel;

  const isInteractive = onClick !== undefined;

  const iconElement = (
    <svg
      className={`standard-icon standard-icon--${type} ${className}`}
      width={size}
      height={size}
      viewBox={iconDef.viewBox}
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={showLabel ? 'true' : undefined}
      role={showLabel ? undefined : 'img'}
      aria-label={showLabel ? undefined : iconAriaLabel}
    >
      <path d={iconDef.path} />
    </svg>
  );

  if (showLabel || osbMode) {
    return (
      <span
        className={`standard-icon-wrapper ${isInteractive ? 'interactive' : ''} ${osbMode ? 'osb-mode' : ''}`}
        onClick={onClick}
        role={isInteractive ? 'button' : undefined}
        tabIndex={isInteractive ? 0 : undefined}
        aria-label={iconAriaLabel}
      >
        {iconElement}
        <span className="standard-icon-label">{iconLabel}</span>
      </span>
    );
  }

  if (isInteractive) {
    return (
      <button
        className="standard-icon-button"
        onClick={onClick}
        aria-label={iconAriaLabel}
        type="button"
      >
        {iconElement}
      </button>
    );
  }

  return iconElement;
};

export default StandardIcon;
