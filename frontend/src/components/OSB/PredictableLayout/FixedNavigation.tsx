/**
 * Task 93.2: Fixed Navigation Component
 * OSB desteği için sabit ve değişmeyen menü sistemi
 *
 * Özellikler:
 * - Hiç hareket etmeyen menü pozisyonları
 * - Her zaman aynı yerde bulunan linkler
 * - Tutarlı menü sıralaması
 * - Öngörülebilir navigasyon
 */

import * as React from 'react';
import {  useState  } from 'react';
import './FixedNavigation.css';

export interface NavigationItem {
  id: string;
  label: string;
  href: string;
  icon?: string; // Icon character or emoji
  ariaLabel?: string;
  position: number; // Sabit pozisyon - asla değişmez
}

export interface FixedNavigationProps {
  /** Navigation items - pozisyona göre sıralanır */
  items: NavigationItem[];

  /** Aktif sayfa */
  activePage?: string;

  /** Logo/başlık - her zaman solda */
  logoText?: string;

  /** Logo tıklama */
  onLogoClick?: () => void;

  /** Navigation tipi */
  variant?: 'horizontal' | 'vertical';

  /** OSB modu - ekstra tahmin edilebilirlik */
  osbMode?: boolean;

  /** Sabit pozisyon - varsayılan: top */
  position?: 'top' | 'left' | 'bottom';
}

/**
 * Sabit navigasyon bileşeni
 * Asla hareket etmeyen, her zaman aynı yerde olan menü
 */
export const FixedNavigation: React.FC<FixedNavigationProps> = ({
  items,
  activePage,
  logoText = 'KIRO Platform',
  onLogoClick,
  variant = 'horizontal',
  osbMode = true,
  position = 'top',
}) => {
  // Items'ı pozisyona göre sırala - her zaman aynı sıra
  const sortedItems = [...items].sort((a, b) => a.position - b.position);

  const [_focusedIndex, setFocusedIndex] = useState<number>(-1);

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (variant === 'horizontal') {
      // Yatay navigasyon - sol/sağ ok tuşları
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        const nextIndex = (index + 1) % sortedItems.length;
        setFocusedIndex(nextIndex);
        document.getElementById(`nav-item-${sortedItems[nextIndex].id}`)?.focus();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        const prevIndex = (index - 1 + sortedItems.length) % sortedItems.length;
        setFocusedIndex(prevIndex);
        document.getElementById(`nav-item-${sortedItems[prevIndex].id}`)?.focus();
      }
    } else {
      // Dikey navigasyon - yukarı/aşağı ok tuşları
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        const nextIndex = (index + 1) % sortedItems.length;
        setFocusedIndex(nextIndex);
        document.getElementById(`nav-item-${sortedItems[nextIndex].id}`)?.focus();
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        const prevIndex = (index - 1 + sortedItems.length) % sortedItems.length;
        setFocusedIndex(prevIndex);
        document.getElementById(`nav-item-${sortedItems[prevIndex].id}`)?.focus();
      }
    }
  };

  return (
    <nav
      className={`fixed-navigation fixed-navigation--${variant} fixed-navigation--${position} ${osbMode ? 'osb-mode' : ''}`}
      role="navigation"
      aria-label="Ana navigasyon"
    >
      {/* Logo - her zaman ilk element */}
      <div className="fixed-navigation__logo">
        {onLogoClick ? (
          <button
            className="logo-button"
            onClick={onLogoClick}
            aria-label="Ana sayfaya git"
            type="button"
          >
            <span className="logo-text">{logoText}</span>
          </button>
        ) : (
          <span className="logo-text">{logoText}</span>
        )}
      </div>

      {/* Navigation items - her zaman aynı sırada */}
      <ul className="fixed-navigation__menu" role="menubar">
        {sortedItems.map((item, index) => {
          const isActive = activePage === item.id;

          return (
            <li
              key={item.id}
              className="fixed-navigation__item"
              role="none"
              data-position={item.position}
            >
              <a
                id={`nav-item-${item.id}`}
                href={item.href}
                className={`nav-link ${isActive ? 'nav-link--active' : ''}`}
                aria-label={item.ariaLabel || item.label}
                aria-current={isActive ? 'page' : undefined}
                role="menuitem"
                tabIndex={index === 0 ? 0 : -1}
                onKeyDown={(e) => handleKeyDown(e, index)}
                onFocus={() => setFocusedIndex(index)}
              >
                {/* Icon - varsa her zaman solda */}
                {item.icon && (
                  <span className="nav-link__icon" aria-hidden="true">
                    {item.icon}
                  </span>
                )}

                {/* Label - her zaman aynı font */}
                <span className="nav-link__label">{item.label}</span>

                {/* Active indicator - aktif sayfa göstergesi */}
                {isActive && (
                  <span className="nav-link__indicator" aria-hidden="true" />
                )}
              </a>
            </li>
          );
        })}
      </ul>

      {/* User section - her zaman sağda (horizontal) veya en altta (vertical) */}
      <div className="fixed-navigation__user">
        <span className="user-indicator" aria-label="Kullanıcı menüsü">
          👤
        </span>
      </div>
    </nav>
  );
};

export default FixedNavigation;
