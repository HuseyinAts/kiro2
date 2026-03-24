/**
 * Modern Navigation Component
 * Glassmorphism design with smooth animations
 */

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
  BarChart,
  Person,
  Close,
  CameraAlt,
  SportsEsports,
  EmojiEvents,
  Explore,
  AutoStories,
} from '@mui/icons-material';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Avatar,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Badge,
  useTheme,
  useMediaQuery,
  Menu,
  MenuItem,
  Divider,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import * as React from 'react';
import {  useState  } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

import { useRoleAccess } from '@/hooks/useRoleAccess';
import { useAuthStore } from '@/store/authStore';
import modernColors from '@/theme/modern-colors';
import { UserRole } from '@/types';

interface NavigationItem {
  label: string
  path: string
  icon: React.ReactElement
  roles: UserRole[]
  badge?: number
  gradient?: string
}

const navigationItems: NavigationItem[] = [
  // Student
  {
    label: 'Dashboard',
    path: '/dashboard',
    icon: <Dashboard />,
    roles: ['ogrenci'],
    gradient: modernColors.gradients.primary,
  },
  {
    label: 'Sınavlar',
    path: '/exam/start',
    icon: <Assessment />,
    roles: ['ogrenci'],
    gradient: modernColors.gradients.fire,
  },
  {
    label: 'Öğrenme Yolu',
    path: '/learning-path',
    icon: <School />,
    roles: ['ogrenci'],
    gradient: modernColors.gradients.forest,
  },
  {
    label: 'AI Sohbet',
    path: '/chat',
    icon: <Chat />,
    roles: ['ogrenci'],
    gradient: modernColors.gradients.ocean,
  },
  {
    label: 'KIRO Destani',
    path: '/kiro-destan',
    icon: <AutoStories />,
    roles: ['ogrenci'],
    gradient: 'linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%)',
  },
  {
    label: 'Lig Siralamasi',
    path: '/league',
    icon: <EmojiEvents />,
    roles: ['ogrenci'],
    gradient: modernColors.gradients.warning,
  },
  {
    label: 'Duello',
    path: '/duel',
    icon: <SportsEsports />,
    roles: ['ogrenci'],
    gradient: modernColors.gradients.fire,
  },
  {
    label: 'Alemler Haritasi',
    path: '/realms',
    icon: <Explore />,
    roles: ['ogrenci'],
    gradient: modernColors.gradients.purple,
  },

  // Teacher
  {
    label: 'Dashboard',
    path: '/teacher/dashboard',
    icon: <Dashboard />,
    roles: ['ogretmen'],
    gradient: modernColors.gradients.primary,
  },
  {
    label: 'Sınıflarım',
    path: '/teacher/classes',
    icon: <Class />,
    roles: ['ogretmen'],
    gradient: modernColors.gradients.ocean,
  },
  {
    label: 'Öğrencilerim',
    path: '/teacher/students',
    icon: <People />,
    roles: ['ogretmen'],
    gradient: modernColors.gradients.forest,
  },
  {
    label: 'Sınavlar',
    path: '/teacher/exams',
    icon: <Assessment />,
    roles: ['ogretmen'],
    gradient: modernColors.gradients.fire,
  },
  {
    label: 'Soru Yükle',
    path: '/question-upload',
    icon: <CameraAlt />,
    roles: ['ogretmen'],
    gradient: modernColors.gradients.sunset,
  },

  // Parent
  {
    label: 'Dashboard',
    path: '/parent/dashboard',
    icon: <Dashboard />,
    roles: ['veli'],
    gradient: modernColors.gradients.primary,
  },
  {
    label: 'Çocuklarım',
    path: '/parent/children',
    icon: <ChildCare />,
    roles: ['veli'],
    gradient: modernColors.gradients.sunset,
  },
  {
    label: 'Raporlar',
    path: '/parent/reports',
    icon: <BarChart />,
    roles: ['veli'],
    gradient: modernColors.gradients.ocean,
  },
  {
    label: 'Bildirimler',
    path: '/parent/notifications',
    icon: <Notifications />,
    roles: ['veli'],
    badge: 3,
    gradient: modernColors.gradients.warning,
  },

  // Admin
  {
    label: 'Dashboard',
    path: '/admin/dashboard',
    icon: <Dashboard />,
    roles: ['admin'],
    gradient: modernColors.gradients.primary,
  },
  {
    label: 'Admin Panel',
    path: '/admin/panel',
    icon: <AdminPanelSettings />,
    roles: ['admin'],
    gradient: modernColors.gradients.fire,
  },
  {
    label: 'Sınavlar',
    path: '/exam/start',
    icon: <Assessment />,
    roles: ['admin'],
    gradient: modernColors.gradients.purple,
  },
  {
    label: 'Kullanıcılar',
    path: '/admin/users',
    icon: <People />,
    roles: ['admin'],
    gradient: modernColors.gradients.ocean,
  },
  {
    label: 'Soru Yükle',
    path: '/question-upload',
    icon: <CameraAlt />,
    roles: ['admin'],
    gradient: modernColors.gradients.sunset,
  },
];

export const ModernNavigation: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileMenuAnchor, setProfileMenuAnchor] = useState<null | HTMLElement>(null);

  const { user, logout } = useAuthStore();
  const { canView } = useRoleAccess();
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const filteredNavItems = navigationItems.filter(
    (item) => user && canView(item.roles),
  );

  const handleNavigation = (path: string) => {
    navigate(path);
    if (isMobile) {setMobileOpen(false);}
  };

  const getRoleInfo = (role?: UserRole) => {
    const roles = {
      ogrenci: { name: 'Öğrenci', color: modernColors.gradients.primary },
      ogretmen: { name: 'Öğretmen', color: modernColors.gradients.forest },
      veli: { name: 'Veli', color: modernColors.gradients.sunset },
      admin: { name: 'Admin', color: modernColors.gradients.fire },
    };
    return role ? roles[role] : { name: 'Kullanıcı', color: modernColors.gradients.primary };
  };

  const roleInfo = getRoleInfo(user?.rol);

  return (
    <>
      {/* Modern AppBar */}
      <AppBar
        position="fixed"
        elevation={0}
        component="header"
        role="banner"
        aria-label="Site başlığı ve navigasyon"
        sx={{
          background: modernColors.glass.white.light,
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          borderBottom: `1px solid ${modernColors.glass.border}`,
          boxShadow: modernColors.shadow.sm,
          zIndex: theme.zIndex.drawer + 1,
        }}
      >
        <Toolbar>
          {/* Mobile Menu Button */}
          {isMobile && (
            <motion.div whileTap={{ scale: 0.95 }}>
              <IconButton
                onClick={() => setMobileOpen(true)}
                aria-label="Navigasyon menüsünü aç"
                aria-expanded={mobileOpen}
                aria-controls="mobile-navigation-drawer"
                sx={{
                  mr: 2,
                  background: modernColors.glass.white.medium,
                  '&:hover': {
                    background: modernColors.glass.white.light,
                  },
                }}
              >
                <MenuIcon />
              </IconButton>
            </motion.div>
          )}

          {/* Logo & Brand */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
            >
              <Box
                sx={{
                  width: 40,
                  height: 40,
                  borderRadius: '10px',
                  background: roleInfo.color,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: modernColors.shadow.md,
                }}
              >
                <School sx={{ color: 'white', fontSize: 24 }} />
              </Box>
            </motion.div>

            <Box>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 800,
                  background: roleInfo.color,
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  lineHeight: 1.2,
                }}
              >
                KIRO2
              </Typography>
              {!isMobile && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', lineHeight: 1 }}>
                  {roleInfo.name}
                </Typography>
              )}
            </Box>
          </Box>

          <Box sx={{ flexGrow: 1 }} />

          {/* Desktop Quick Actions */}
          {!isMobile && (
            <Box sx={{ display: 'flex', gap: 1, mr: 2 }}>
              {filteredNavItems.slice(0, 4).map((item, index) => (
                <motion.div
                  key={item.path}
                  initial={{ opacity: 0, y: -20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <IconButton
                    onClick={() => handleNavigation(item.path)}
                    aria-label={`${item.label} sayfasına git`}
                    aria-current={location.pathname === item.path ? 'page' : undefined}
                    sx={{
                      background:
                        location.pathname === item.path
                          ? item.gradient
                          : modernColors.glass.white.medium,
                      color: location.pathname === item.path ? 'white' : 'text.primary',
                      boxShadow: location.pathname === item.path ? modernColors.shadow.glow : 'none',
                      transition: 'all 0.3s',
                      '&:hover': {
                        background: item.gradient,
                        color: 'white',
                        boxShadow: modernColors.shadow.glow,
                      },
                    }}
                  >
                    {item.badge ? (
                      <Badge badgeContent={item.badge} color="error">
                        {item.icon}
                      </Badge>
                    ) : (
                      item.icon
                    )}
                  </IconButton>
                </motion.div>
              ))}
            </Box>
          )}

          {/* Notifications */}
          <motion.div whileTap={{ scale: 0.95 }}>
            <IconButton
              sx={{
                background: modernColors.glass.white.medium,
                mr: 1,
                '&:hover': {
                  background: modernColors.glass.white.light,
                },
              }}
            >
              <Badge badgeContent={3} color="error">
                <Notifications />
              </Badge>
            </IconButton>
          </motion.div>

          {/* Profile Menu */}
          {user && (
            <>
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Box
                  onClick={(e) => setProfileMenuAnchor(e.currentTarget)}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.5,
                    padding: '6px 12px',
                    borderRadius: '12px',
                    background: modernColors.glass.white.medium,
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    '&:hover': {
                      background: modernColors.glass.white.light,
                    },
                  }}
                >
                  <Avatar
                    sx={{
                      width: 36,
                      height: 36,
                      background: roleInfo.color,
                      fontWeight: 700,
                      boxShadow: modernColors.shadow.sm,
                    }}
                  >
                    {user.ad?.[0]}{user.soyad?.[0]}
                  </Avatar>
                  {!isMobile && (
                    <Box>
                      <Typography variant="body2" fontWeight={600} lineHeight={1.2}>
                        {user.ad} {user.soyad}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" lineHeight={1}>
                        {roleInfo.name}
                      </Typography>
                    </Box>
                  )}
                </Box>
              </motion.div>

              <Menu
                anchorEl={profileMenuAnchor}
                open={Boolean(profileMenuAnchor)}
                onClose={() => setProfileMenuAnchor(null)}
                PaperProps={{
                  sx: {
                    mt: 1.5,
                    minWidth: 200,
                    borderRadius: '12px',
                    background: modernColors.glass.white.light,
                    backdropFilter: 'blur(16px)',
                    boxShadow: modernColors.shadow.modern,
                  },
                }}
              >
                <MenuItem onClick={() => { handleNavigation('/profile'); setProfileMenuAnchor(null); }}>
                  <ListItemIcon><Person /></ListItemIcon>
                  Profil
                </MenuItem>
                <MenuItem onClick={() => { handleNavigation('/settings'); setProfileMenuAnchor(null); }}>
                  <ListItemIcon><Settings /></ListItemIcon>
                  Ayarlar
                </MenuItem>
                <Divider sx={{ my: 0.5 }} />
                <MenuItem onClick={() => { logout(); navigate('/login'); setProfileMenuAnchor(null); }}>
                  <ListItemIcon><Logout /></ListItemIcon>
                  Çıkış Yap
                </MenuItem>
              </Menu>
            </>
          )}
        </Toolbar>
      </AppBar>

      {/* Modern Sidebar Drawer */}
      <AnimatePresence>
        {(mobileOpen || !isMobile) && (
          <Drawer
            id="mobile-navigation-drawer"
            variant={isMobile ? 'temporary' : 'permanent'}
            open={mobileOpen}
            onClose={() => setMobileOpen(false)}
            PaperProps={{
              component: 'nav',
              role: 'navigation',
              'aria-label': 'Ana navigasyon menüsü',
            }}
            sx={{
              width: isMobile ? 0 : 280,
              flexShrink: 0,
              '& .MuiDrawer-paper': {
                width: 280,
                boxSizing: 'border-box',
                background: modernColors.glass.white.light,
                backdropFilter: 'blur(16px)',
                border: 'none',
                borderRight: `1px solid ${modernColors.glass.border}`,
              },
            }}
          >
            <Toolbar />

            {/* Mobile Close Button */}
            {isMobile && (
              <Box sx={{ p: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <IconButton
                  onClick={() => setMobileOpen(false)}
                  aria-label="Menüyü kapat"
                >
                  <Close />
                </IconButton>
              </Box>
            )}

            {/* Navigation Items */}
            <List sx={{ px: 2 }}>
              {filteredNavItems.map((item, index) => (
                <motion.div
                  key={item.path}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <ListItem disablePadding sx={{ mb: 1 }}>
                    <ListItemButton
                      selected={location.pathname === item.path}
                      onClick={() => handleNavigation(item.path)}
                      sx={{
                        borderRadius: '12px',
                        minHeight: 48,
                        background:
                          location.pathname === item.path
                            ? item.gradient
                            : 'transparent',
                        color: location.pathname === item.path ? 'white' : 'text.primary',
                        boxShadow: location.pathname === item.path ? modernColors.shadow.md : 'none',
                        transition: 'all 0.2s',
                        '&:hover': {
                          background:
                            location.pathname === item.path
                              ? item.gradient
                              : modernColors.glass.white.medium,
                          transform: 'translateX(4px)',
                        },
                        '&.Mui-selected': {
                          '&:hover': {
                            background: item.gradient,
                          },
                        },
                      }}
                    >
                      <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                        {item.badge ? (
                          <Badge badgeContent={item.badge} color="error">
                            {item.icon}
                          </Badge>
                        ) : (
                          item.icon
                        )}
                      </ListItemIcon>
                      <ListItemText
                        primary={item.label}
                        primaryTypographyProps={{
                          fontWeight: location.pathname === item.path ? 700 : 500,
                        }}
                      />
                    </ListItemButton>
                  </ListItem>
                </motion.div>
              ))}
            </List>

            {/* Bottom Section */}
            <Box sx={{ flexGrow: 1 }} />
            <Box sx={{ p: 2 }}>
              <Box
                sx={{
                  p: 2,
                  borderRadius: '12px',
                  background: roleInfo.color,
                  boxShadow: modernColors.shadow.md,
                  textAlign: 'center',
                }}
              >
                <Typography variant="body2" sx={{ color: 'white', fontWeight: 600, mb: 0.5 }}>
                  🎯 Hedefine ulaş!
                </Typography>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                  Her gün biraz daha iyileş
                </Typography>
              </Box>
            </Box>
          </Drawer>
        )}
      </AnimatePresence>
    </>
  );
};

export default ModernNavigation;
