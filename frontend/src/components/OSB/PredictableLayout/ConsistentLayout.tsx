/**
 * Task 93.1: Consistent Layout System
 * OSB (Otizm Spektrum Bozukluğu) desteği için tutarlı düzen bileşeni
 *
 * Özellikler:
 * - Tüm sayfalarda aynı düzen
 * - Öngörülebilir element konumları
 * - Beklenmedik değişiklik yok
 * - Grid-based predictable structure
 */

import React, { ReactNode } from 'react';
import './ConsistentLayout.css';

export interface ConsistentLayoutProps {
  /** Ana içerik */
  children: ReactNode;

  /** Sayfa başlığı - her zaman aynı konumda */
  title?: string;

  /** Alt başlık */
  subtitle?: string;

  /** Sağ sidebar içeriği (opsiyonel) */
  sidebar?: ReactNode;

  /** Footer içeriği (opsiyonel) */
  footer?: ReactNode;

  /** Layout tipi - tüm sayfalar için standart */
  layoutType?: 'default' | 'centered' | 'wide';

  /** Breadcrumb navigasyon - her zaman aynı konumda */
  breadcrumbs?: Array<{ label: string; href: string }>;

  /** Sayfanın ana aksiyonu (örn: "Sınavı Başlat") */
  primaryAction?: {
    label: string;
    onClick: () => void;
    icon?: ReactNode;
  };

  /** OSB modu aktif mi? */
  osbMode?: boolean;
}

/**
 * Tutarlı düzen bileşeni
 * Tüm sayfalarda aynı yapıyı garanti eder
 */
export const ConsistentLayout: React.FC<ConsistentLayoutProps> = ({
  children,
  title,
  subtitle,
  sidebar,
  footer,
  layoutType = 'default',
  breadcrumbs,
  primaryAction,
  osbMode = true
}) => {
  return (
    <div
      className={`consistent-layout consistent-layout--${layoutType} ${osbMode ? 'osb-mode' : ''}`}
      data-layout-type={layoutType}
    >
      {/* Header bölümü - her zaman aynı yerde */}
      <header className="consistent-layout__header">
        {/* Breadcrumb - her zaman header'ın üstünde */}
        {breadcrumbs && breadcrumbs.length > 0 && (
          <nav className="consistent-layout__breadcrumbs" aria-label="Breadcrumb navigasyon">
            <ol className="breadcrumbs-list">
              {breadcrumbs.map((crumb, index) => (
                <li key={index} className="breadcrumbs-item">
                  {index < breadcrumbs.length - 1 ? (
                    <>
                      <a href={crumb.href} className="breadcrumbs-link">
                        {crumb.label}
                      </a>
                      <span className="breadcrumbs-separator" aria-hidden="true">›</span>
                    </>
                  ) : (
                    <span className="breadcrumbs-current" aria-current="page">
                      {crumb.label}
                    </span>
                  )}
                </li>
              ))}
            </ol>
          </nav>
        )}

        {/* Başlık bölümü - her zaman aynı konumda */}
        <div className="consistent-layout__header-content">
          {title && (
            <h1 className="consistent-layout__title">
              {title}
            </h1>
          )}

          {subtitle && (
            <p className="consistent-layout__subtitle">
              {subtitle}
            </p>
          )}

          {/* Primary action - her zaman başlığın sağında */}
          {primaryAction && (
            <div className="consistent-layout__primary-action">
              <button
                className="primary-action-button"
                onClick={primaryAction.onClick}
                type="button"
              >
                {primaryAction.icon && (
                  <span className="primary-action-icon" aria-hidden="true">
                    {primaryAction.icon}
                  </span>
                )}
                <span className="primary-action-label">{primaryAction.label}</span>
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main content area - grid yapısı */}
      <div className="consistent-layout__body">
        <main className="consistent-layout__main" role="main">
          {children}
        </main>

        {/* Sidebar - varsa her zaman sağda */}
        {sidebar && (
          <aside className="consistent-layout__sidebar" role="complementary">
            {sidebar}
          </aside>
        )}
      </div>

      {/* Footer - varsa her zaman en altta */}
      {footer && (
        <footer className="consistent-layout__footer">
          {footer}
        </footer>
      )}
    </div>
  );
};

export default ConsistentLayout;
