/**
 * Modern Admin Users Page - Glassmorphism Design
 * Admin kullanıcı yönetimi
 */

import {
  Person,
  Add,
  Edit,
  Delete,
  Search,
  MoreVert,
  AdminPanelSettings,
  School,
  People,
  Block,
  CheckCircle,
  Email,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  Grid,
  Chip,
  Avatar,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Menu,
  MenuItem as MenuItemComponent,
  Fab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { ModernLoader } from '../components/ui/ModernLoader';
import apiClient from '../services/apiClient';
import modernColors from '../theme/modern-colors';
import { useAuthStore } from '@/store/authStore';

interface User {
  id: string
  ad_soyad: string
  email: string
  rol: 'admin' | 'ogretmen' | 'ogrenci' | 'veli'
  durum: 'aktif' | 'pasif' | 'askida'
  kayit_tarihi: string
  son_giris?: string
}

export function ModernAdminUsersPage() {
  const { user: _user } = useAuthStore();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [newUser, setNewUser] = useState({
    ad_soyad: '',
    email: '',
    rol: 'ogrenci' as 'admin' | 'ogretmen' | 'ogrenci' | 'veli',
    sifre: '',
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/admin/users');
      setUsers(response.data.users || []);
    } catch (error) {
      console.error('Kullanıcılar yüklenemedi:', error);
      // Mock data
      setUsers([
        {
          id: '1',
          ad_soyad: 'Ahmet Yılmaz',
          email: 'ahmet@example.com',
          rol: 'ogrenci',
          durum: 'aktif',
          kayit_tarihi: '2025-09-01T10:00:00',
          son_giris: '2025-11-21T09:30:00',
        },
        {
          id: '2',
          ad_soyad: 'Ayşe Demir',
          email: 'ayse@example.com',
          rol: 'ogretmen',
          durum: 'aktif',
          kayit_tarihi: '2025-08-15T14:20:00',
          son_giris: '2025-11-20T16:45:00',
        },
        {
          id: '3',
          ad_soyad: 'Mehmet Kaya',
          email: 'mehmet@example.com',
          rol: 'veli',
          durum: 'aktif',
          kayit_tarihi: '2025-09-10T11:30:00',
          son_giris: '2025-11-21T08:15:00',
        },
        {
          id: '4',
          ad_soyad: 'Fatma Öz',
          email: 'fatma@example.com',
          rol: 'ogrenci',
          durum: 'pasif',
          kayit_tarihi: '2025-07-20T09:00:00',
        },
        {
          id: '5',
          ad_soyad: 'Ali Şahin',
          email: 'ali@example.com',
          rol: 'admin',
          durum: 'aktif',
          kayit_tarihi: '2025-06-01T10:00:00',
          son_giris: '2025-11-21T10:00:00',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async () => {
    if (!newUser.ad_soyad || !newUser.email || !newUser.sifre) {
      alert('Lütfen tüm alanları doldurun');
      return;
    }

    try {
      await apiClient.post('/api/v1/admin/users', newUser);
      setCreateDialogOpen(false);
      fetchUsers();
      setNewUser({ ad_soyad: '', email: '', rol: 'ogrenci', sifre: '' });
    } catch (error) {
      console.error('Kullanıcı oluşturulamadı:', error);
      alert('Kullanıcı oluşturulurken bir hata oluştu');
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, user: User) => {
    setAnchorEl(event.currentTarget);
    setSelectedUser(user);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleEditUser = () => {
    alert(`Kullanıcıyı düzenle: ${selectedUser?.ad_soyad}`);
    handleMenuClose();
  };

  const handleDeleteUser = async () => {
    if (selectedUser && window.confirm('Bu kullanıcıyı silmek istediğinizden emin misiniz?')) {
      try {
        await apiClient.delete(`/api/v1/admin/users/${selectedUser.id}`);
        fetchUsers();
      } catch (error) {
        console.error('Kullanıcı silinemedi:', error);
      }
    }
    handleMenuClose();
  };

  const handleToggleStatus = async () => {
    if (selectedUser) {
      const newStatus = selectedUser.durum === 'aktif' ? 'pasif' : 'aktif';
      try {
        await apiClient.patch(`/api/v1/admin/users/${selectedUser.id}/status`, {
          durum: newStatus,
        });
        fetchUsers();
      } catch (error) {
        console.error('Durum değiştirilemedi:', error);
      }
    }
    handleMenuClose();
  };

  const getRoleGradient = (rol: string): string => {
    switch (rol) {
      case 'admin':
        return modernColors.gradients.fire;
      case 'ogretmen':
        return modernColors.gradients.forest;
      case 'ogrenci':
        return modernColors.gradients.primary;
      case 'veli':
        return modernColors.gradients.sunset;
      default:
        return modernColors.gradients.ocean;
    }
  };

  const getRoleIcon = (rol: string) => {
    switch (rol) {
      case 'admin':
        return <AdminPanelSettings />;
      case 'ogretmen':
        return <School />;
      case 'ogrenci':
        return <Person />;
      case 'veli':
        return <People />;
      default:
        return <Person />;
    }
  };

  const getRoleLabel = (rol: string): string => {
    switch (rol) {
      case 'admin':
        return 'Admin';
      case 'ogretmen':
        return 'Öğretmen';
      case 'ogrenci':
        return 'Öğrenci';
      case 'veli':
        return 'Veli';
      default:
        return rol;
    }
  };

  const getStatusGradient = (durum: string): string => {
    switch (durum) {
      case 'aktif':
        return modernColors.gradients.success;
      case 'pasif':
        return modernColors.gradients.error;
      case 'askida':
        return modernColors.gradients.warning;
      default:
        return modernColors.gradients.ocean;
    }
  };

  const getInitials = (name: string): string => {
    return name
      .split(' ')
      .map((n) => n.charAt(0))
      .join('')
      .toUpperCase();
  };

  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      user.ad_soyad.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = filterRole === 'all' || user.rol === filterRole;
    const matchesStatus = filterStatus === 'all' || user.durum === filterStatus;
    return matchesSearch && matchesRole && matchesStatus;
  });

  const getUserCountByRole = (rol: string) => {
    return users.filter((u) => u.rol === rol).length;
  };

  const getUserCountByStatus = (durum: string) => {
    return users.filter((u) => u.durum === durum).length;
  };

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.mesh,
        }}
      >
        <ModernLoader message="Kullanıcılar yükleniyor..." size="large" />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: modernColors.gradients.mesh,
        py: 4,
      }}
    >
      <Container maxWidth="xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Box sx={{ mb: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Box
                sx={{
                  width: 56,
                  height: 56,
                  borderRadius: 3,
                  background: modernColors.gradients.fire,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <AdminPanelSettings sx={{ fontSize: 32, color: 'white' }} />
              </Box>
              <Box>
                <Typography
                  variant="h3"
                  sx={{
                    fontWeight: 900,
                    background: modernColors.gradients.fire,
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                  }}
                >
                  Kullanıcı Yönetimi
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Tüm kullanıcıları yönetin ve düzenleyin
                </Typography>
              </Box>
            </Box>
          </Box>
        </motion.div>

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <GlassCard glassIntensity="medium" elevated sx={{ mb: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  placeholder="Kullanıcı ara..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Search />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Rol</InputLabel>
                  <Select
                    value={filterRole}
                    label="Rol"
                    onChange={(e) => setFilterRole(e.target.value)}
                  >
                    <MenuItem value="all">Tümü</MenuItem>
                    <MenuItem value="admin">Admin</MenuItem>
                    <MenuItem value="ogretmen">Öğretmen</MenuItem>
                    <MenuItem value="ogrenci">Öğrenci</MenuItem>
                    <MenuItem value="veli">Veli</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Durum</InputLabel>
                  <Select
                    value={filterStatus}
                    label="Durum"
                    onChange={(e) => setFilterStatus(e.target.value)}
                  >
                    <MenuItem value="all">Tümü</MenuItem>
                    <MenuItem value="aktif">Aktif</MenuItem>
                    <MenuItem value="pasif">Pasif</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </GlassCard>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={6} sm={3} md={2}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.fire}>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {getUserCountByRole('admin')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Admin
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={6} sm={3} md={2}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.forest}>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {getUserCountByRole('ogretmen')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Öğretmen
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={6} sm={3} md={2}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.primary}>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {getUserCountByRole('ogrenci')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Öğrenci
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={6} sm={3} md={2}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.sunset}>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {getUserCountByRole('veli')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Veli
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={6} sm={3} md={2}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.success}>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {getUserCountByStatus('aktif')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Aktif
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={6} sm={3} md={2}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.error}>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {getUserCountByStatus('pasif')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Pasif
                </Typography>
              </GlassCard>
            </Grid>
          </Grid>
        </motion.div>

        {/* Users Table */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <GlassCard glassIntensity="medium" elevated>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Kullanıcı</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Email</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Rol</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Durum</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Kayıt Tarihi</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Son Giriş</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>
                      İşlemler
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <AnimatePresence mode="wait">
                    {filteredUsers.map((user, index) => (
                      <TableRow
                        key={user.id}
                        component={motion.tr}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        transition={{ duration: 0.2, delay: index * 0.02 }}
                        hover
                      >
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                            <Avatar
                              sx={{
                                width: 40,
                                height: 40,
                                background: getRoleGradient(user.rol),
                                fontWeight: 700,
                              }}
                            >
                              {getInitials(user.ad_soyad)}
                            </Avatar>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              {user.ad_soyad}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Email fontSize="small" color="action" />
                            <Typography variant="body2">{user.email}</Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            icon={getRoleIcon(user.rol)}
                            label={getRoleLabel(user.rol)}
                            size="small"
                            sx={{
                              background: getRoleGradient(user.rol),
                              color: 'white',
                              fontWeight: 600,
                            }}
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            icon={
                              user.durum === 'aktif' ? (
                                <CheckCircle fontSize="small" />
                              ) : (
                                <Block fontSize="small" />
                              )
                            }
                            label={user.durum}
                            size="small"
                            sx={{
                              background: getStatusGradient(user.durum),
                              color: 'white',
                              fontWeight: 600,
                            }}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption">
                            {new Date(user.kayit_tarihi).toLocaleDateString('tr-TR')}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption">
                            {user.son_giris
                              ? new Date(user.son_giris).toLocaleDateString('tr-TR')
                              : '-'}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={(e) => handleMenuOpen(e, user)}
                          >
                            <MoreVert />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </AnimatePresence>
                </TableBody>
              </Table>
            </TableContainer>

            {filteredUsers.length === 0 && (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <Typography variant="h6" color="text.secondary">
                  Kullanıcı bulunamadı
                </Typography>
              </Box>
            )}
          </GlassCard>
        </motion.div>

        {/* FAB */}
        <Fab
          color="primary"
          aria-label="add user"
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            background: modernColors.gradients.fire,
            '&:hover': {
              background: modernColors.gradients.fire,
            },
          }}
          onClick={() => setCreateDialogOpen(true)}
        >
          <Add />
        </Fab>

        {/* Context Menu */}
        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
          <MenuItemComponent onClick={handleEditUser}>
            <Edit fontSize="small" sx={{ mr: 1 }} />
            Düzenle
          </MenuItemComponent>
          <MenuItemComponent onClick={handleToggleStatus}>
            {selectedUser?.durum === 'aktif' ? (
              <>
                <Block fontSize="small" sx={{ mr: 1 }} />
                Pasif Yap
              </>
            ) : (
              <>
                <CheckCircle fontSize="small" sx={{ mr: 1 }} />
                Aktif Yap
              </>
            )}
          </MenuItemComponent>
          <MenuItemComponent onClick={handleDeleteUser} sx={{ color: 'error.main' }}>
            <Delete fontSize="small" sx={{ mr: 1 }} />
            Sil
          </MenuItemComponent>
        </Menu>

        {/* Create Dialog */}
        <Dialog
          open={createDialogOpen}
          onClose={() => setCreateDialogOpen(false)}
          maxWidth="sm"
          fullWidth
          PaperProps={{
            sx: {
              background: modernColors.glass.white.light,
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
            },
          }}
        >
          <DialogTitle>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Yeni Kullanıcı Oluştur
            </Typography>
          </DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                label="Ad Soyad"
                value={newUser.ad_soyad}
                onChange={(e) => setNewUser({ ...newUser, ad_soyad: e.target.value })}
              />
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={newUser.email}
                onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
              />
              <FormControl fullWidth>
                <InputLabel>Rol</InputLabel>
                <Select
                  value={newUser.rol}
                  label="Rol"
                  onChange={(e) =>
                    setNewUser({ ...newUser, rol: e.target.value as any })
                  }
                >
                  <MenuItem value="ogrenci">Öğrenci</MenuItem>
                  <MenuItem value="ogretmen">Öğretmen</MenuItem>
                  <MenuItem value="veli">Veli</MenuItem>
                  <MenuItem value="admin">Admin</MenuItem>
                </Select>
              </FormControl>
              <TextField
                fullWidth
                label="Şifre"
                type="password"
                value={newUser.sifre}
                onChange={(e) => setNewUser({ ...newUser, sifre: e.target.value })}
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <ModernButton variant="glass" onClick={() => setCreateDialogOpen(false)}>
              İptal
            </ModernButton>
            <ModernButton
              variant="gradient"
              gradient={modernColors.gradients.success}
              onClick={handleCreateUser}
              glow
            >
              Oluştur
            </ModernButton>
          </DialogActions>
        </Dialog>
      </Container>
    </Box>
  );
}

export default ModernAdminUsersPage;
