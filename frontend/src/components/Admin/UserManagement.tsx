import {
  Edit,
  Delete,
  Add,
  Block,
  CheckCircle,
} from '@mui/icons-material';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Alert,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { adminService, AdminUser, CreateUserRequest, UpdateUserRequest } from '../../services/adminService';

interface UserFormData {
  email: string
  ad_soyad: string
  telefon: string
  rol: string
  sifre: string
}

export const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalUsers, setTotalUsers] = useState(0);

  // Filter states
  const [roleFilter, _setRoleFilter] = useState<string>('');
  const [statusFilter, _setStatusFilter] = useState<string>('all');
  const [searchTerm, _setSearchTerm] = useState<string>('');

  // Dialog states
  const [openDialog, setOpenDialog] = useState(false);
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [formData, setFormData] = useState<UserFormData>({
    email: '',
    ad_soyad: '',
    telefon: '',
    rol: 'ogrenci',
    sifre: '',
  });

  useEffect(() => {
    fetchUsers();
  }, [page, rowsPerPage]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);

      const users = await adminService.getUsers({
        sayfa: page + 1, // Backend 1-based pagination
        sayfa_boyutu: rowsPerPage,
        rol: (roleFilter as 'ogrenci' | 'ogretmen' | 'veli' | 'admin') || undefined,
        aktif: statusFilter !== 'all' ? statusFilter === 'active' : undefined,
        arama: searchTerm || undefined,
      });

      setUsers(users);
      setTotalUsers(users.length); // Backend should return total count
    } catch (err) {
      console.error('Users fetch error:', err);
      setError(err instanceof Error ? err.message : 'Kullanıcılar yüklenirken hata oluştu');

      // Mock data for development
      const mockUsers: AdminUser[] = [
        {
          kullanici_id: '1',
          email: 'admin@test.com',
          ad_soyad: 'Admin User',
          rol: 'admin',
          aktif: true,
          kayit_tarihi: '2024-01-01T00:00:00Z',
          son_giris: '2024-01-15T10:30:00Z',
        },
        {
          kullanici_id: '2',
          email: 'ogrenci@test.com',
          ad_soyad: 'Test Öğrenci',
          rol: 'ogrenci',
          aktif: true,
          kayit_tarihi: '2024-01-02T00:00:00Z',
          son_giris: '2024-01-15T09:15:00Z',
        },
      ];
      setUsers(mockUsers);
      setTotalUsers(mockUsers.length);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async () => {
    try {
      const createRequest: CreateUserRequest = {
        email: formData.email,
        ad_soyad: formData.ad_soyad,
        sifre: formData.sifre,
        rol: formData.rol as 'ogrenci' | 'ogretmen' | 'veli' | 'admin',
        profil_bilgileri: formData.telefon ? { telefon: formData.telefon } : undefined,
      };

      await adminService.createUser(createRequest);

      setOpenDialog(false);
      resetForm();
      fetchUsers();
    } catch (err) {
      console.error('Create user error:', err);
      setError(err instanceof Error ? err.message : 'Kullanıcı oluşturulamadı');
    }
  };

  const handleUpdateUser = async () => {
    if (!editingUser) {return;}

    try {
      const updateRequest: UpdateUserRequest = {
        ad_soyad: formData.ad_soyad,
        profil_bilgileri: formData.telefon ? { telefon: formData.telefon } : undefined,
      };

      await adminService.updateUser(editingUser.kullanici_id, updateRequest);

      setOpenDialog(false);
      setEditingUser(null);
      resetForm();
      fetchUsers();
    } catch (err) {
      console.error('Update user error:', err);
      setError(err instanceof Error ? err.message : 'Kullanıcı güncellenemedi');
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Bu kullanıcıyı silmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      await adminService.deleteUser(userId);
      fetchUsers();
    } catch (err) {
      console.error('Delete user error:', err);
      setError(err instanceof Error ? err.message : 'Kullanıcı silinemedi');
    }
  };

  const handleToggleUserStatus = async (userId: string, currentStatus: boolean) => {
    try {
      await adminService.toggleUserStatus(userId, !currentStatus);
      fetchUsers();
    } catch (err) {
      console.error('Toggle user status error:', err);
      setError(err instanceof Error ? err.message : 'Kullanıcı durumu değiştirilemedi');
    }
  };

  const resetForm = () => {
    setFormData({
      email: '',
      ad_soyad: '',
      telefon: '',
      rol: 'ogrenci',
      sifre: '',
    });
  };

  const openCreateDialog = () => {
    resetForm();
    setEditingUser(null);
    setOpenDialog(true);
  };

  const openEditDialog = (user: AdminUser) => {
    setFormData({
      email: user.email,
      ad_soyad: user.ad_soyad,
      telefon: user.telefon || '',
      rol: user.rol,
      sifre: '',
    });
    setEditingUser(user);
    setOpenDialog(true);
  };

  const getRoleColor = (role: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (role) {
      case 'admin': return 'error';
      case 'ogretmen': return 'primary';
      case 'veli': return 'warning';
      case 'ogrenci': return 'success';
      default: return 'default';
    }
  };

  const getRoleText = (role: string) => {
    switch (role) {
      case 'admin': return 'Admin';
      case 'ogretmen': return 'Öğretmen';
      case 'veli': return 'Veli';
      case 'ogrenci': return 'Öğrenci';
      default: return role;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h2">
          Kullanıcı Yönetimi
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={openCreateDialog}
        >
          Yeni Kullanıcı
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Ad Soyad</TableCell>
                <TableCell>E-posta</TableCell>
                <TableCell>Telefon</TableCell>
                <TableCell>Rol</TableCell>
                <TableCell>Durum</TableCell>
                <TableCell>Kayıt Tarihi</TableCell>
                <TableCell>Son Giriş</TableCell>
                <TableCell align="center">İşlemler</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.kullanici_id}>
                  <TableCell>{user.ad_soyad}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>{user.telefon || '-'}</TableCell>
                  <TableCell>
                    <Chip
                      label={getRoleText(user.rol)}
                      color={getRoleColor(user.rol)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={user.aktif ? 'Aktif' : 'Pasif'}
                      color={user.aktif ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(user.kayit_tarihi).toLocaleDateString('tr-TR')}
                  </TableCell>
                  <TableCell>
                    {user.son_giris
                      ? new Date(user.son_giris).toLocaleDateString('tr-TR')
                      : 'Hiç giriş yapmamış'
                    }
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip title="Düzenle">
                      <IconButton
                        size="small"
                        onClick={() => openEditDialog(user)}
                        aria-label={`${user.ad_soyad} kullanıcısını düzenle`}
                      >
                        <Edit />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={user.aktif ? 'Pasif Yap' : 'Aktif Yap'}>
                      <IconButton
                        size="small"
                        onClick={() => handleToggleUserStatus(user.kullanici_id, user.aktif)}
                        aria-label={user.aktif ? `${user.ad_soyad} kullanıcısını pasif yap` : `${user.ad_soyad} kullanıcısını aktif yap`}
                      >
                        {user.aktif ? <Block /> : <CheckCircle />}
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Sil">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteUser(user.kullanici_id)}
                        aria-label={`${user.ad_soyad} kullanıcısını sil`}
                      >
                        <Delete />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={totalUsers}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(event) => {
            setRowsPerPage(parseInt(event.target.value, 10));
            setPage(0);
          }}
          labelRowsPerPage="Sayfa başına satır:"
          labelDisplayedRows={({ from, to, count }) =>
            `${from}-${to} / ${count !== -1 ? count : `${to}'den fazla`}`
          }
        />
      </Paper>

      {/* User Form Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingUser ? 'Kullanıcı Düzenle' : 'Yeni Kullanıcı Oluştur'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Ad Soyad"
              value={formData.ad_soyad}
              onChange={(e) => setFormData({ ...formData, ad_soyad: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="E-posta"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              margin="normal"
              required
              disabled={!!editingUser}
            />
            <TextField
              fullWidth
              label="Telefon"
              value={formData.telefon}
              onChange={(e) => setFormData({ ...formData, telefon: e.target.value })}
              margin="normal"
            />
            <FormControl fullWidth margin="normal" required>
              <InputLabel>Rol</InputLabel>
              <Select
                value={formData.rol}
                onChange={(e) => setFormData({ ...formData, rol: e.target.value })}
                label="Rol"
              >
                <MenuItem value="ogrenci">Öğrenci</MenuItem>
                <MenuItem value="ogretmen">Öğretmen</MenuItem>
                <MenuItem value="veli">Veli</MenuItem>
                <MenuItem value="admin">Admin</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label={editingUser ? 'Yeni Şifre (boş bırakılabilir)' : 'Şifre'}
              type="password"
              value={formData.sifre}
              onChange={(e) => setFormData({ ...formData, sifre: e.target.value })}
              margin="normal"
              required={!editingUser}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>
            İptal
          </Button>
          <Button
            onClick={editingUser ? handleUpdateUser : handleCreateUser}
            variant="contained"
          >
            {editingUser ? 'Güncelle' : 'Oluştur'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserManagement;