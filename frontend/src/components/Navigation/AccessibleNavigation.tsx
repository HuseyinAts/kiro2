/**
 * WCAG 2.1 Level AA Uyumlu Navigasyon Bileşeni
 * Erişilebilir menü yapısı ve klavye navigasyonu
 */

import {
  Menu as MenuIcon,
  Close as CloseIcon,
  ExpandLess,
  ExpandMore,
  Home as HomeIcon,
  NavigateNext as NavigateNextIcon,
  KeyboardArrowDown,
  Accessibility as AccessibilityIcon,
} from '@mui/icons-material';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Breadcrumbs,
  Link,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Divider,
  useTheme,
  useMediaQuery,
  Chip,
} from '@mui/material';
import * as React from 'react';
import {  useState, useRef, useCallback, useEffect  } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

import { useAccessibilitySettings } from '../../hooks/useAccessibilitySettings';
import { useKeyboardNavigation } from '../../hooks/useKeyboardNavigation';
import { useScreenReader } from '../../hooks/useScreenReader';

export interface NavigationItem {
  id: string;
  label: string;
  path?: string;
  icon?: React.ReactNode;
  children?: NavigationItem[];
  disabled?: boolean;
  external?: boolean;
  ariaLabel?: string;
}

export interface BreadcrumbItem {
  label: string;
  path?: string;
}

interface AccessibleNavigationProps {
  title: string;
  logo?: React.ReactNode;
  navigationItems: NavigationItem[];
  breadcrumbs?: BreadcrumbItem[];
  showAccessibilityButton?: boolean;
  onAccessibilityClick?: () => void;
  className?: string;
}

const AccessibleNavigation: React.FC<AccessibleNavigationProps> = ({
  title,
  logo,
  navigationItems,
  breadcrumbs = [],
  showAccessibilityButton = true,
  onAccessibilityClick,
  className,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();

  const { settings, toggleHighContrast } = useAccessibilitySettings();
  const { announce, manageFocus } = useScreenReader();
  const { trapFocus, handleArrowNavigation } = useKeyboardNavigation();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [expandedItems, setExpandedItems] = useState<string[]>([]);
  const [anchorEls, setAnchorEls] = useState<Record<string, HTMLElement | null>>({});
  const [focusedItemIndex, setFocusedItemIndex] = useState(-1);

  const navRef = useRef<HTMLElement>(null);
  const mobileMenuRef = useRef<HTMLDivElement>(null);
  const skipLinkRef = useRef<HTMLAnchorElement | null>(null);

  // Navigation ID'leri - available if needed for accessibility purposes
  // const navId = `navigation-${Math.random().toString(36).substr(2, 9)}`;
  // const mobileMenuId = `${navId}-mobile`;
  // const breadcrumbId = `${navId}-breadcrumb`;

  // Aktif sayfa tespiti
  const isActivePage = useCallback((path?: string): boolean => {
    if (!path) {return false;}
    return location.pathname === path || location.pathname.startsWith(path + '/');
  }, [location.pathname]);

  // Menü öğesi tıklama
  const handleItemClick = useCallback((item: NavigationItem, event?: React.MouseEvent) => {
    if (item.disabled) {
      event?.preventDefault();
      return;
    }

    if (item.path) {
      if (item.external) {
        window.open(item.path, '_blank', 'noopener,noreferrer');
      } else {
        navigate(item.path);
        announce(`${item.label} sayfasına gidiliyor`, 'polite');
      }
    }

    // Mobil menüyü kapat
    if (isMobile) {
      setMobileMenuOpen(false);
    }

    // Desktop dropdown'ları kapat
    setAnchorEls({});
  }, [navigate, announce, isMobile]);

  // Alt menü toggle
  const toggleSubmenu = useCallback((itemId: string, event?: React.MouseEvent) => {
    event?.stopPropagation();

    setExpandedItems(prev => {
      const isExpanded = prev.includes(itemId);
      const newExpanded = isExpanded
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId];

      const item = navigationItems.find(item => item.id === itemId);
      if (item) {
        announce(
          `${item.label} alt menüsü ${isExpanded ? 'kapatıldı' : 'açıldı'}`,
          'polite',
        );
      }

      return newExpanded;
    });
  }, [navigationItems, announce]);

  // Desktop dropdown menü
  const handleDropdownOpen = useCallback((itemId: string, event: React.MouseEvent<HTMLElement>) => {
    setAnchorEls(prev => ({ ...prev, [itemId]: event.currentTarget }));
  }, []);

  const handleDropdownClose = useCallback((itemId: string) => {
    setAnchorEls(prev => ({ ...prev, [itemId]: null }));
  }, []);

  // Mobil menü toggle
  const toggleMobileMenu = useCallback(() => {
    const newOpen = !mobileMenuOpen;
    setMobileMenuOpen(newOpen);

    if (newOpen) {
      announce('Mobil menü açıldı', 'polite');
      // Focus trap kurulacak
      setTimeout(() => {
        if (mobileMenuRef.current) {
          const cleanup = trapFocus(mobileMenuRef.current);
          return cleanup;
        }
      }, 100);
    } else {
      announce('Mobil menü kapatıldı', 'polite');
    }
  }, [mobileMenuOpen, announce, trapFocus]);

  // Klavye navigasyonu
  const handleKeyDown = useCallback((event: React.KeyboardEvent, items: NavigationItem[]) => {
    const newIndex = handleArrowNavigation(
      event.nativeEvent,
      items.map(item => document.getElementById(`nav-item-${item.id}`)).filter(Boolean) as HTMLElement[],
      focusedItemIndex,
      'horizontal',
    );

    if (newIndex !== focusedItemIndex) {
      setFocusedItemIndex(newIndex);
    }

    // Enter veya Space ile aktivasyon
    if ((event.key === 'Enter' || event.key === ' ') && focusedItemIndex >= 0) {
      event.preventDefault();
      const item = items[focusedItemIndex];
      if (item) {
        if (item.children && item.children.length > 0) {
          toggleSubmenu(item.id);
        } else {
          handleItemClick(item);
        }
      }
    }

    // Escape ile menüleri kapat
    if (event.key === 'Escape') {
      setAnchorEls({});
      setMobileMenuOpen(false);
    }
  }, [focusedItemIndex, handleArrowNavigation, toggleSubmenu, handleItemClick]);

  // Skip link oluştur
  useEffect(() => {
    if (!skipLinkRef.current) {
      const skipLink = document.createElement('a');
      skipLink.href = '#main-content';
      skipLink.textContent = 'Ana içeriğe geç';
      skipLink.className = 'skip-link';
      skipLink.style.cssText = `
        position: absolute;
        top: -40px;
        left: 6px;
        background: #000;
        color: #fff;
        padding: 8px;
        text-decoration: none;
        border-radius: 4px;
        z-index: 9999;
        transition: top 0.3s;
      `;

      skipLink.addEventListener('focus', () => {
        skipLink.style.top = '6px';
      });

      skipLink.addEventListener('blur', () => {
        skipLink.style.top = '-40px';
      });

      skipLink.addEventListener('click', (e) => {
        e.preventDefault();
        const mainContent = document.getElementById('main-content') ||
                           document.querySelector('main') ||
                           document.querySelector('[role="main"]');
        if (mainContent instanceof HTMLElement) {
          manageFocus(mainContent, 'Ana içeriğe geçildi');
        }
      });

      document.body.insertBefore(skipLink, document.body.firstChild);
      skipLinkRef.current = skipLink;
    }

    return () => {
      if (skipLinkRef.current && skipLinkRef.current.parentNode) {
        skipLinkRef.current.parentNode.removeChild(skipLinkRef.current);
        skipLinkRef.current = null;
      }
    };
  }, [manageFocus]);

  // Navigasyon öğesi render
  const renderNavigationItem = useCallback((item: NavigationItem, isMobile = false) => {
    const hasChildren = item.children && item.children.length > 0;
    const isActive = isActivePage(item.path);
    const isExpanded = expandedItems.includes(item.id);
    const anchorEl = anchorEls[item.id];

    if (isMobile) {
      return (
        <React.Fragment key={item.id}>
          <ListItem disablePadding>
            <ListItemButton
              id={`nav-item-${item.id}`}
              onClick={(e) => {
                if (hasChildren) {
                  toggleSubmenu(item.id, e);
                } else {
                  handleItemClick(item, e);
                }
              }}
              disabled={item.disabled}
              selected={isActive}
              aria-expanded={hasChildren ? isExpanded : undefined}
              aria-haspopup={hasChildren ? 'true' : undefined}
              aria-label={item.ariaLabel || item.label}
              className="wcag-aa-target-size"
              sx={{
                minHeight: 48,
                '&.Mui-selected': {
                  backgroundColor: theme.palette.primary.main,
                  color: theme.palette.primary.contrastText,
                  '&:hover': {
                    backgroundColor: theme.palette.primary.dark,
                  },
                },
              }}
            >
              {item.icon && (
                <ListItemIcon sx={{ color: isActive ? 'inherit' : undefined }}>
                  {item.icon}
                </ListItemIcon>
              )}
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{
                  fontWeight: isActive ? 'bold' : 'normal',
                }}
              />
              {hasChildren && (isExpanded ? <ExpandLess /> : <ExpandMore />)}
            </ListItemButton>
          </ListItem>

          {hasChildren && (
            <Collapse in={isExpanded} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                {item.children!.map((child) => (
                  <ListItem key={child.id} disablePadding>
                    <ListItemButton
                      sx={{ pl: 4, minHeight: 44 }}
                      onClick={(e) => handleItemClick(child, e)}
                      disabled={child.disabled}
                      selected={isActivePage(child.path)}
                      aria-label={child.ariaLabel || child.label}
                      className="wcag-aa-target-size"
                    >
                      {child.icon && (
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          {child.icon}
                        </ListItemIcon>
                      )}
                      <ListItemText
                        primary={child.label}
                        primaryTypographyProps={{
                          fontSize: '0.9rem',
                          fontWeight: isActivePage(child.path) ? 'bold' : 'normal',
                        }}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </Collapse>
          )}
        </React.Fragment>
      );
    }

    // Desktop navigasyon
    return (
      <React.Fragment key={item.id}>
        <Button
          id={`nav-item-${item.id}`}
          color="inherit"
          onClick={(e) => {
            if (hasChildren) {
              handleDropdownOpen(item.id, e);
            } else {
              handleItemClick(item, e);
            }
          }}
          onMouseEnter={(e) => {
            if (hasChildren) {
              handleDropdownOpen(item.id, e);
            }
          }}
          disabled={item.disabled}
          endIcon={hasChildren ? <KeyboardArrowDown /> : undefined}
          aria-expanded={hasChildren ? Boolean(anchorEl) : undefined}
          aria-haspopup={hasChildren ? 'true' : undefined}
          aria-label={item.ariaLabel || item.label}
          className="wcag-aa-target-size"
          sx={{
            mx: 0.5,
            minHeight: 44,
            fontWeight: isActive ? 'bold' : 'normal',
            backgroundColor: isActive ? 'rgba(255,255,255,0.1)' : 'transparent',
            '&:hover': {
              backgroundColor: 'rgba(255,255,255,0.1)',
            },
          }}
        >
          {item.icon && <Box sx={{ mr: 1, display: 'flex' }}>{item.icon}</Box>}
          {item.label}
        </Button>

        {hasChildren && (
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={() => handleDropdownClose(item.id)}
            onMouseLeave={() => handleDropdownClose(item.id)}
            MenuListProps={{
              'aria-labelledby': `nav-item-${item.id}`,
              role: 'menu',
            }}
            PaperProps={{
              sx: { mt: 1 },
            }}
          >
            {item.children!.map((child) => (
              <MenuItem
                key={child.id}
                onClick={(e) => {
                  handleItemClick(child, e);
                  handleDropdownClose(item.id);
                }}
                disabled={child.disabled}
                selected={isActivePage(child.path)}
                role="menuitem"
                aria-label={child.ariaLabel || child.label}
                className="wcag-aa-target-size"
                sx={{ minHeight: 44 }}
              >
                {child.icon && (
                  <Box sx={{ mr: 2, display: 'flex', minWidth: 24 }}>
                    {child.icon}
                  </Box>
                )}
                {child.label}
              </MenuItem>
            ))}
          </Menu>
        )}
      </React.Fragment>
    );
  }, [
    expandedItems, anchorEls, isActivePage, theme, toggleSubmenu, handleItemClick,
    handleDropdownOpen, handleDropdownClose,
  ]);

  return (
    <>
      {/* Ana Navigasyon */}
      <AppBar
        position="sticky"
        className={className}
        role="banner"
        sx={{
          '& .wcag-aa-target-size': {
            minHeight: 44,
            minWidth: 44,
          },
        }}
      >
        <Toolbar>
          {/* Logo ve Başlık */}
          <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
            {logo && (
              <Box sx={{ mr: 2, display: 'flex' }}>
                {logo}
              </Box>
            )}
            <Typography
              variant="h6"
              component="h1"
              sx={{
                flexGrow: isMobile ? 1 : 0,
                fontSize: { xs: '1.1rem', sm: '1.25rem' },
              }}
            >
              {title}
            </Typography>
          </Box>

          {/* Desktop Navigasyon */}
          {!isMobile && (
            <Box
              component="nav"
              ref={navRef}
              role="navigation"
              aria-label="Ana navigasyon"
              onKeyDown={(e) => handleKeyDown(e, navigationItems)}
              sx={{ display: 'flex', alignItems: 'center' }}
            >
              {navigationItems.map(item => renderNavigationItem(item, false))}
            </Box>
          )}

          {/* Erişilebilirlik Butonu */}
          {showAccessibilityButton && (
            <IconButton
              color="inherit"
              onClick={onAccessibilityClick || toggleHighContrast}
              aria-label="Erişilebilirlik ayarları"
              className="wcag-aa-target-size"
              sx={{ ml: 1 }}
            >
              <AccessibilityIcon />
            </IconButton>
          )}

          {/* Mobil Menü Butonu */}
          {isMobile && (
            <IconButton
              color="inherit"
              aria-label={mobileMenuOpen ? 'Menüyü kapat' : 'Menüyü aç'}
              onClick={toggleMobileMenu}
              className="wcag-aa-target-size"
              sx={{ ml: 1 }}
            >
              {mobileMenuOpen ? <CloseIcon /> : <MenuIcon />}
            </IconButton>
          )}
        </Toolbar>
      </AppBar>

      {/* Breadcrumb Navigasyonu */}
      {breadcrumbs.length > 0 && (
        <Box
          component="nav"
          role="navigation"
          aria-label="Sayfa konumu"
          sx={{ p: 2, bgcolor: 'grey.50' }}
        >
          <Breadcrumbs
            aria-label="breadcrumb"
            separator={<NavigateNextIcon fontSize="small" />}
          >
            <Link
              component="button"
              variant="body2"
              onClick={() => navigate('/')}
              sx={{
                display: 'flex',
                alignItems: 'center',
                textDecoration: 'none',
                '&:hover': { textDecoration: 'underline' },
              }}
              className="wcag-aa-target-size"
            >
              <HomeIcon sx={{ mr: 0.5, fontSize: 16 }} />
              Ana Sayfa
            </Link>

            {breadcrumbs.map((crumb, index) => {
              const isLast = index === breadcrumbs.length - 1;

              if (isLast || !crumb.path) {
                return (
                  <Typography
                    key={index}
                    color="text.primary"
                    variant="body2"
                    aria-current="page"
                  >
                    {crumb.label}
                  </Typography>
                );
              }

              return (
                <Link
                  key={index}
                  component="button"
                  variant="body2"
                  onClick={() => navigate(crumb.path!)}
                  sx={{
                    textDecoration: 'none',
                    '&:hover': { textDecoration: 'underline' },
                  }}
                  className="wcag-aa-target-size"
                >
                  {crumb.label}
                </Link>
              );
            })}
          </Breadcrumbs>
        </Box>
      )}

      {/* Mobil Drawer Menü */}
      <Drawer
        anchor="left"
        open={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        ModalProps={{
          keepMounted: true, // Performans için
        }}
        PaperProps={{
          ref: mobileMenuRef,
          sx: { width: 280 },
        }}
      >
        <Box
          role="navigation"
          aria-label="Mobil navigasyon menüsü"
          sx={{ width: 280 }}
        >
          {/* Mobil Menü Başlığı */}
          <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            <Typography variant="h6" component="h2">
              {title}
            </Typography>
          </Box>

          {/* Mobil Navigasyon Listesi */}
          <List>
            {navigationItems.map(item => renderNavigationItem(item, true))}
          </List>

          <Divider />

          {/* Erişilebilirlik Durumu */}
          {settings.highContrast && (
            <Box sx={{ p: 2 }}>
              <Chip
                label="Yüksek Kontrast Aktif"
                color="primary"
                size="small"
                icon={<AccessibilityIcon />}
              />
            </Box>
          )}
        </Box>
      </Drawer>

      {/* Klavye Kısayolları Yardımı */}
      {settings.keyboardNavigation && !isMobile && (
        <Box
          sx={{
            position: 'fixed',
            bottom: 16,
            right: 16,
            bgcolor: 'background.paper',
            p: 1,
            borderRadius: 1,
            boxShadow: 2,
            fontSize: '0.75rem',
            opacity: 0.8,
            zIndex: 1000,
          }}
        >
          <Typography variant="caption">
            <strong>Navigasyon:</strong> Tab: Menü | ←→: Öğeler | Enter: Seç | Esc: Kapat
          </Typography>
        </Box>
      )}
    </>
  );
};

export default AccessibleNavigation;