import {
  Menu as MenuIcon,
  Dashboard,
  School,
  People,
  Assessment,
  Chat,
  Settings,
  Logout,
  Notifications,
  AdminPanelSettings,
  Class,
  ChildCare,
  Assignment,
  BarChart,
  LibraryBooks,
  Person,
} from '@mui/icons-material';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  useTheme,
  useMediaQuery,
  Badge,
} from '@mui/material';
import * as React from 'react';
import {  useState  } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

import { useRoleAccess } from '../../hooks/useRoleAccess.tsx';
import { UserRole } from '../../types';
import { useAuthStore } from '@/store/authStore';

interface NavigationItem {
  label: string
  path: string
  icon: React.ReactElement
  roles: UserRole[]
  badge?: number
}

const navigationItems: NavigationItem[] = [
  // Öğrenci navigasyonu
  {
    label: 'Dashboard',
    path: '/dashboard',
    icon: <Dashboard />,
    roles: ['ogrenci'],
  },
  {
    label: 'Sınavlar',
    path: '/exams',
    icon: <Assessment />,
    roles: ['ogrenci'],
  },
  {
    label: 'Öğrenme Yolu',
    path: '/learning-path',
    icon: <School />,
    roles: ['ogrenci'],
  },
  {
    label: 'AI Sohbet',
    path: '/chat',
    icon: <Chat />,
    roles: ['ogrenci'],
  },
  {
    label: 'Profil',
    path: '/profile',
    icon: <Person />,
    roles: ['ogrenci'],
  },

  // Öğretmen navigasyonu
  {
    label: 'Öğretmen Dashboard',
    path: '/teacher/dashboard',
    icon: <Dashboard />,
    roles: ['ogretmen'],
  },
  {
    label: 'Sınıflarım',
    path: '/teacher/classes',
    icon: <Class />,
    roles: ['ogretmen'],
  },
  {
    label: 'Öğrencilerim',
    path: '/teacher/students',
    icon: <People />,
    roles: ['ogretmen'],
  },
  {
    label: 'Sınavlar',
    path: '/teacher/exams',
    icon: <Assessment />,
    roles: ['ogretmen'],
  },
  {
    label: 'Ödevler',
    path: '/teacher/assignments',
    icon: <Assignment />,
    roles: ['ogretmen'],
  },
  {
    label: 'Raporlar',
    path: '/teacher/reports',
    icon: <BarChart />,
    roles: ['ogretmen'],
  },
  {
    label: 'İçerik',
    path: '/teacher/content',
    icon: <LibraryBooks />,
    roles: ['ogretmen'],
  },

  // Veli navigasyonu
  {
    label: 'Veli Dashboard',
    path: '/parent/dashboard',
    icon: <Dashboard />,
    roles: ['veli'],
  },
  {
    label: 'Çocuklarım',
    path: '/parent/children',
    icon: <ChildCare />,
    roles: ['veli'],
  },
  {
    label: 'İlerleme Raporları',
    path: '/parent/reports',
    icon: <BarChart />,
    roles: ['veli'],
  },
  {
    label: 'Bildirimler',
    path: '/parent/notifications',
    icon: <Notifications />,
    roles: ['veli'],
    badge: 3,
  },

  // Admin navigasyonu
  {
    label: 'Admin Dashboard',
    path: '/admin/dashboard',
    icon: <Dashboard />,
    roles: ['admin'],
  },
  {
    label: 'Admin Panel',
    path: '/admin/panel',
    icon: <AdminPanelSettings />,
    roles: ['admin'],
  },
  {
    label: 'Kullanıcı Yönetimi',
    path: '/admin/users',
    icon: <People />,
    roles: ['admin'],
  },
  {
    label: 'İçerik Yönetimi',
    path: '/admin/content',
    icon: <LibraryBooks />,
    roles: ['admin'],
  },
  {
    label: 'Sistem Ayarları',
    path: '/admin/settings',
    icon: <Settings />,
    roles: ['admin'],
  },
];

export const RoleBasedNavigation: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const {  user, logout  } = useAuthStore();
  const { canView } = useRoleAccess();
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    handleProfileMenuClose();
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    if (isMobile) {
      setMobileOpen(false);
    }
  };

  // Kullanıcının rolüne göre navigasyon öğelerini filtrele
  const filteredNavigationItems = navigationItems.filter(item =>
    user && canView(item.roles),
  );

  const getRoleDisplayName = (role: UserRole): string => {
    switch (role) {
      case 'ogrenci':
        return 'Öğrenci';
      case 'ogretmen':
        return 'Öğretmen';
      case 'veli':
        return 'Veli';
      case 'admin':
        return 'Admin';
      default:
        return 'Kullanıcı';
    }
  };

  const getInitials = (ad?: string, soyad?: string): string => {
    if (!ad || !soyad) {return 'U';}
    return `${ad.charAt(0)}${soyad.charAt(0)}`.toUpperCase();
  };

  const drawer = (
    <Box>
      {/* Logo ve Başlık */}
      <Box sx={{ p: 2, textAlign: 'center', borderBottom: 1, borderColor: 'divider' }}>
        <School sx={{ fontSize: 32, color: 'primary.main', mb: 1 }} />
        <Typography variant="h6" color="primary">
          EğitimEylemci
        </Typography>
        {user && (
          <Typography variant="body2" color="text.secondary">
            {getRoleDisplayName(user.rol)}
          </Typography>
        )}
      </Box>

      {/* Navigasyon Menüsü */}
      <List>
        {filteredNavigationItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
            >
              <ListItemIcon>
                {item.badge ? (
                  <Badge badgeContent={item.badge} color="error">
                    {item.icon}
                  </Badge>
                ) : (
                  item.icon
                )}
              </ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider />

      {/* Alt Menü */}
      <List>
        <ListItem disablePadding>
          <ListItemButton onClick={() => handleNavigation('/settings')}>
            <ListItemIcon>
              <Settings />
            </ListItemIcon>
            <ListItemText primary="Ayarlar" />
          </ListItemButton>
        </ListItem>
        <ListItem disablePadding>
          <ListItemButton onClick={handleLogout}>
            <ListItemIcon>
              <Logout />
            </ListItemIcon>
            <ListItemText primary="Çıkış Yap" />
          </ListItemButton>
        </ListItem>
      </List>
    </Box>
  );

  return (
    <>
      <AppBar position="fixed" sx={{ zIndex: theme.zIndex.drawer + 1 }}>
        <Toolbar>
          {isMobile && (
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}

          <School sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            EğitimEylemci
          </Typography>

          {/* Desktop Navigation */}
          {!isMobile && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {filteredNavigationItems.slice(0, 4).map((item) => (
                <Button
                  key={item.path}
                  color="inherit"
                  startIcon={
                    item.badge ? (
                      <Badge badgeContent={item.badge} color="error">
                        {item.icon}
                      </Badge>
                    ) : (
                      item.icon
                    )
                  }
                  onClick={() => handleNavigation(item.path)}
                  sx={{
                    backgroundColor: location.pathname === item.path ? 'rgba(255,255,255,0.1)' : 'transparent',
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Box>
          )}

          {/* Profil Menüsü */}
          {user && (
            <Box sx={{ ml: 2 }}>
              <IconButton
                size="medium"
                aria-label="account of current user"
                aria-controls="profile-menu"
                aria-haspopup="true"
                onClick={handleProfileMenuOpen}
                color="inherit"
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
                  {getInitials(user.ad, user.soyad)}
                </Avatar>
              </IconButton>
              <Menu
                id="profile-menu"
                anchorEl={anchorEl}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                open={Boolean(anchorEl)}
                onClose={handleProfileMenuClose}
              >
                <MenuItem disabled>
                  <Box>
                    <Typography variant="body1">
                      {user.ad} {user.soyad}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {getRoleDisplayName(user.rol)}
                    </Typography>
                  </Box>
                </MenuItem>
                <Divider />
                <MenuItem onClick={() => { handleNavigation('/profile'); handleProfileMenuClose(); }}>
                  <ListItemIcon>
                    <Person fontSize="small" />
                  </ListItemIcon>
                  Profil
                </MenuItem>
                <MenuItem onClick={() => { handleNavigation('/settings'); handleProfileMenuClose(); }}>
                  <ListItemIcon>
                    <Settings fontSize="small" />
                  </ListItemIcon>
                  Ayarlar
                </MenuItem>
                <Divider />
                <MenuItem onClick={handleLogout}>
                  <ListItemIcon>
                    <Logout fontSize="small" />
                  </ListItemIcon>
                  Çıkış Yap
                </MenuItem>
              </Menu>
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* Mobile Drawer */}
      {isMobile && (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 280 },
          }}
        >
          {drawer}
        </Drawer>
      )}

      {/* Desktop Drawer */}
      {!isMobile && (
        <Drawer
          variant="permanent"
          sx={{
            width: 280,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: 280,
              boxSizing: 'border-box',
            },
          }}
        >
          <Toolbar />
          {drawer}
        </Drawer>
      )}
    </>
  );
};

export default RoleBasedNavigation;