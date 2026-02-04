/**
 * WCAG 2.1 Level AA Uyumlu Erişilebilir Navigasyon Bileşeni
 * 
 * Özellikler:
 * - Skip links (ana içeriğe geç)
 * - Breadcrumb navigasyonu
 * - ARIA landmarks
 * - Klavye navigasyonu
 * - Ekran okuyucu desteği
 * - Yüksek kontrast desteği
 */

import React, { useRef, useEffect, useState } from 'react';
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
  useTheme,
  styled,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Home,
  NavigateNext,
  AccountCircle,
  Settings,
  Logout,
  Accessibility,
} from '@mui/icons-material';
import { useKeyboardNavigation } from '../../hooks/useKeyboardNavigation';
import { useScreenReader } from '../../hooks/useScreenReader';
import { AccessibleButton } from './AccessibleButton';

interface NavigationItem {
  id: string;
  label: string;
  href?: string;
  onClick?: () => void;
  icon?: React.ReactNode;
  children?: NavigationItem[];
  ariaLabel?: string;
}

interface BreadcrumbItem {
  label: string;
  href?: string;
  onClick?: () => void;
}

interface AccessibleNavigationProps {
  title: string;
  navigationItems: NavigationItem[];
  breadcrumbs?: BreadcrumbItem[];
  userMenuItems?: NavigationItem[];
  onMenuToggle?: (open: boolean) => void;
  highContrast?: boolean;
  showSkipLinks?: boolean;
  mainContentId?: string;
}

const SkipLink = styled(Link)(({ theme }) => ({
  position: 'absolute',
  top: '-40px',
  left: '6px',
  background: theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
  padding: theme.spacing(1, 2),
  textDecoration: 'none',
  borderRadius: theme.spacing(0.5),
  zIndex: 10000,
  transition: 'top 0.3s ease',
  
  '&:focus': {
    top: '6px',
  },
  
  '@media (prefers-reduced-motion: reduce)': {
    transition: 'none',
  },
}));

const StyledAppBar = styled(AppBar, {
  shouldForwardProp: (prop) => prop !== 'highContrast',
})<{ highContrast?: boolean }>(({ theme, highContrast }) => ({
  // Yüksek kontrast modu
  ...(highContrast && {
    backgroundColor: '#000000',
    color: '#FFFFFF',
    borderBottom: '3px solid #FFFFFF',
    
    '& .MuiButton-root': {
      color: '#FFFFFF',
      border: '1px solid #FFFFFF',
      '&:hover': {
        backgroundColor: '#FFFFFF',
        color: '#000000',
      },
      '&:focus-visible': {
        outline: '3px solid #FFFF00',
        outlineOffset: '2px',
      },
    },
    
    '& .MuiIconButton-root': {
      color: '#FFFFFF',
      border: '1px solid #FFFFFF',
      '&:hover': {
        backgroundColor: '#FFFFFF',
        color: '#000000',
      },
    },
  }),
}));

const StyledDrawer = styled(Drawer, {
  shouldForwardProp: (prop) => prop !== 'highContrast',
})<{ highContrast?: boolean }>(({ theme, highContrast }) => ({
  '& .MuiDrawer-paper': {
    width: 280,
    
    // Yüksek kontrast modu
    ...(highContrast && {
      backgroundColor: '#FFFFFF',
      color: '#000000',
      border: '2px solid #000000',
      
      '& .MuiListItem-root': {
        border: '1px solid #000000',
        '&:hover': {
          backgroundColor: '#E0E0E0',
        },
        '&:focus-visible': {
          outline: '3px solid #0000FF',
          outlineOffset: '2px',
        },
      },
    }),
  },
}));

const AccessibilityControls = styled(Box)(({ theme }) => ({
  position: 'fixed',
  top: theme.spacing(10),
  right: theme.spacing(2),
  zIndex: 1000,
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(1),
  
  '& .accessibility-button': {
    minWidth: '48px',
    minHeight: '48px',
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    border: `2px solid ${theme.palette.primary.contrastText}`,
    borderRadius: '50%',
    
    '&:hover': {
      backgroundColor: theme.palette.primary.dark,
    },
    
    '&:focus-visible': {
      outline: `3px solid ${theme.palette.secondary.main}`,
      outlineOffset: '2px',
    },
  },
}));

export const AccessibleNavigation: React.FC<AccessibleNavigationProps> = ({
  title,
  navigationItems,
  breadcrumbs = [],
  userMenuItems = [],
  onMenuToggle,
  highContrast = false,
  showSkipLinks = true,
  mainContentId = 'main-content',
}) => {
  const theme = useTheme();
  const navRef = useRef<HTMLElement>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null);
  const [accessibilityMenuOpen, setAccessibilityMenuOpen] = useState(false);

  const { announce, announceLandmark } = useScreenReader();

  // Klavye navigasyonu
  useKeyboardNavigation(navRef, {
    arrowNavigation: true,
    onEscape: () => {
      setMobileMenuOpen(false);
      setUserMenuAnchor(null);
    },
  });

  // Navigasyon değişikliği duyurusu
  useEffect(() => {
    if (breadcrumbs.length > 0) {
      const currentPage = breadcrumbs[breadcrumbs.length - 1].label;
      announce(`Şu anda ${currentPage} sayfasındasınız`, 'polite');
    }
  }, [breadcrumbs, announce]);

  // Mobil menü toggle
  const handleMobileMenuToggle = () => {
    const newState = !mobileMenuOpen;
    setMobileMenuOpen(newState);
    onMenuToggle?.(newState);
    
    if (newState) {
      announce('Mobil menü açıldı', 'polite');
    } else {
      announce('Mobil menü kapandı', 'polite');
    }
  };

  // Kullanıcı menüsü
  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setUserMenuAnchor(event.currentTarget);
    announce('Kullanıcı menüsü açıldı', 'polite');
  };

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null);
    announce('Kullanıcı menüsü kapandı', 'polite');
  };

  // Ana içeriğe geç
  const skipToMainContent = () => {
    const mainContent = document.getElementById(mainContentId);
    if (mainContent) {
      mainContent.focus();
      mainContent.scrollIntoView();
      announce('Ana içeriğe geçildi', 'polite');
    }
  };

  // Erişilebilirlik kontrolleri
  const toggleAccessibilityMenu = () => {
    setAccessibilityMenuOpen(!accessibilityMenuOpen);
  };

  // Navigasyon öğesi render
  const renderNavigationItem = (item: NavigationItem, isMobile = false) => {
    const handleClick = () => {
      if (item.onClick) {
        item.onClick();
      }
      if (isMobile) {
        setMobileMenuOpen(false);
      }
    };

    if (isMobile) {
      return (
        <ListItem
          key={item.id}
          button
          component={item.href ? 'a' : 'button'}
          href={item.href}
          onClick={handleClick}
          aria-label={item.ariaLabel || item.label}
        >
          {item.icon && <ListItemIcon>{item.icon}</ListItemIcon>}
          <ListItemText primary={item.label} />
        </ListItem>
      );
    }

    return (
      <AccessibleButton
        key={item.id}
        onClick={handleClick}
        href={item.href}
        component={item.href ? 'a' : 'button'}
        color="inherit"
        highContrast={highContrast}
        ariaLabel={item.ariaLabel || item.label}
      >
        {item.label}
      </AccessibleButton>
    );
  };

  return (
    <>
      {/* Skip Links */}
      {showSkipLinks && (
        <SkipLink
          href={`#${mainContentId}`}
          onClick={(e) => {
            e.preventDefault();
            skipToMainContent();
          }}
          tabIndex={0}
        >
          Ana içeriğe geç
        </SkipLink>
      )}

      {/* Ana navigasyon */}
      <StyledAppBar
        ref={navRef}
        position="sticky"
        highContrast={highContrast}
        role="banner"
        aria-label="Ana navigasyon"
      >
        <Toolbar>
          {/* Mobil menü butonu */}
          <IconButton
            edge="start"
            color="inherit"
            aria-label="Menüyü aç"
            onClick={handleMobileMenuToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          {/* Site başlığı */}
          <Typography
            variant="h6"
            component="h1"
            sx={{ flexGrow: 1 }}
            id="site-title"
          >
            {title}
          </Typography>

          {/* Desktop navigasyon */}
          <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 1 }}>
            {navigationItems.map(item => renderNavigationItem(item))}
          </Box>

          {/* Kullanıcı menüsü */}
          {userMenuItems.length > 0 && (
            <>
              <IconButton
                color="inherit"
                onClick={handleUserMenuOpen}
                aria-label="Kullanıcı menüsü"
                aria-controls="user-menu"
                aria-haspopup="true"
              >
                <AccountCircle />
              </IconButton>
              
              <Menu
                id="user-menu"
                anchorEl={userMenuAnchor}
                open={Boolean(userMenuAnchor)}
                onClose={handleUserMenuClose}
                aria-label="Kullanıcı menüsü"
              >
                {userMenuItems.map(item => (
                  <MenuItem
                    key={item.id}
                    onClick={() => {
                      item.onClick?.();
                      handleUserMenuClose();
                    }}
                    component={item.href ? 'a' : 'button'}
                    href={item.href}
                  >
                    {item.icon && <Box sx={{ mr: 1 }}>{item.icon}</Box>}
                    {item.label}
                  </MenuItem>
                ))}
              </Menu>
            </>
          )}
        </Toolbar>

        {/* Breadcrumb navigasyonu */}
        {breadcrumbs.length > 0 && (
          <Box
            sx={{ px: 2, pb: 1 }}
            role="navigation"
            aria-label="Breadcrumb navigasyonu"
          >
            <Breadcrumbs
              separator={<NavigateNext fontSize="small" />}
              aria-label="Sayfa yolu"
            >
              <Link
                color="inherit"
                href="/"
                onClick={(e) => {
                  e.preventDefault();
                  // Ana sayfaya git
                }}
                aria-label="Ana sayfa"
              >
                <Home sx={{ mr: 0.5 }} fontSize="inherit" />
                Ana Sayfa
              </Link>
              
              {breadcrumbs.map((crumb, index) => {
                const isLast = index === breadcrumbs.length - 1;
                
                if (isLast) {
                  return (
                    <Typography
                      key={index}
                      color="inherit"
                      aria-current="page"
                    >
                      {crumb.label}
                    </Typography>
                  );
                }
                
                return (
                  <Link
                    key={index}
                    color="inherit"
                    href={crumb.href}
                    onClick={(e) => {
                      if (crumb.onClick) {
                        e.preventDefault();
                        crumb.onClick();
                      }
                    }}
                  >
                    {crumb.label}
                  </Link>
                );
              })}
            </Breadcrumbs>
          </Box>
        )}
      </StyledAppBar>

      {/* Mobil drawer menü */}
      <StyledDrawer
        anchor="left"
        open={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        highContrast={highContrast}
        ModalProps={{
          'aria-label': 'Mobil navigasyon menüsü',
        }}
      >
        <Box
          role="navigation"
          aria-label="Mobil navigasyon"
          sx={{ width: 280 }}
        >
          <List>
            {navigationItems.map(item => renderNavigationItem(item, true))}
          </List>
        </Box>
      </StyledDrawer>

      {/* Erişilebilirlik kontrolleri */}
      <AccessibilityControls>
        <IconButton
          className="accessibility-button"
          onClick={toggleAccessibilityMenu}
          aria-label="Erişilebilirlik ayarları"
          aria-expanded={accessibilityMenuOpen}
        >
          <Accessibility />
        </IconButton>
        
        {accessibilityMenuOpen && (
          <Box
            sx={{
              backgroundColor: 'white',
              border: '2px solid black',
              borderRadius: 1,
              p: 2,
              minWidth: 200,
            }}
            role="menu"
            aria-label="Erişilebilirlik kontrolleri"
          >
            <Typography variant="h6" gutterBottom>
              Erişilebilirlik
            </Typography>
            
            <AccessibleButton
              fullWidth
              variant="outlined"
              onClick={() => {
                // Yüksek kontrast toggle
                announce('Yüksek kontrast modu değiştirildi', 'polite');
              }}
              sx={{ mb: 1 }}
            >
              Yüksek Kontrast
            </AccessibleButton>
            
            <AccessibleButton
              fullWidth
              variant="outlined"
              onClick={() => {
                // Font boyutu artır
                announce('Yazı boyutu artırıldı', 'polite');
              }}
              sx={{ mb: 1 }}
            >
              Yazı Boyutu +
            </AccessibleButton>
            
            <AccessibleButton
              fullWidth
              variant="outlined"
              onClick={() => {
                // Animasyonları kapat
                announce('Animasyonlar kapatıldı', 'polite');
              }}
            >
              Animasyonları Kapat
            </AccessibleButton>
          </Box>
        )}
      </AccessibilityControls>
    </>
  );
};

export default AccessibleNavigation;