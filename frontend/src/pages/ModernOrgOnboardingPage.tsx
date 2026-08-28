/**
 * Modern Org Onboarding Page - Glassmorphism Design
 * Okul (kurum) onboarding — üye yönetimi + DPA + koltuk durumu
 */

import {
  Business,
  Add,
  Delete,
  MoreVert,
  CheckCircle,
  Warning,
  Email,
  Gavel,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  Grid,
  Chip,
  Avatar,
  TextField,
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
  LinearProgress,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect, useCallback } from 'react';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { ModernLoader } from '../components/ui/ModernLoader';
import organizationService, {
  OrgInfo,
  OrgMember,
  OrgRole,
  DpaStatus,
  LicenseInfo,
} from '../services/organizationService';
import modernColors from '../theme/modern-colors';

const ROLE_LABELS: Record<OrgRole, string> = {
  SCHOOL_ADMIN: 'Okul Yöneticisi',
  TEACHER: 'Öğretmen',
  STUDENT: 'Öğrenci',
  PARENT: 'Veli',
  OBSERVER: 'Gözlemci',
};

const ROLE_GRADIENTS: Record<OrgRole, string> = {
  SCHOOL_ADMIN: modernColors.gradients.fire,
  TEACHER: modernColors.gradients.forest,
  STUDENT: modernColors.gradients.primary,
  PARENT: modernColors.gradients.sunset,
  OBSERVER: modernColors.gradients.ocean,
};

const getInitials = (email?: string | null): string =>
  (email || '?').charAt(0).toUpperCase();

export function ModernOrgOnboardingPage() {
  const [orgInfo, setOrgInfo] = useState<OrgInfo | null>(null);
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [dpaStatus, setDpaStatus] = useState<DpaStatus | null>(null);
  const [license, setLicense] = useState<LicenseInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState<string | null>(null);

  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [newMember, setNewMember] = useState<{ email: string; org_role: OrgRole }>({
    email: '',
    org_role: 'STUDENT',
  });

  const [dpaDialogOpen, setDpaDialogOpen] = useState(false);
  const [dpaSigner, setDpaSigner] = useState({ signer_name: '', signer_email: '' });

  const [roleDialogOpen, setRoleDialogOpen] = useState(false);
  const [roleDraft, setRoleDraft] = useState<OrgRole>('STUDENT');

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedMember, setSelectedMember] = useState<OrgMember | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      setLoading(true);
      const [info, memberList, dpa, lic] = await Promise.all([
        organizationService.getInfo(),
        organizationService.getMembers(),
        organizationService.getDpa(),
        organizationService.getLicense(),
      ]);
      setOrgInfo(info);
      setMembers(memberList);
      setDpaStatus(dpa);
      setLicense(lic);
    } catch (error) {
      console.error('Kurum verileri yüklenemedi:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const handleAddMember = async () => {
    if (!newMember.email.trim()) {
      setActionError('E-posta zorunlu');
      return;
    }
    try {
      setActionError(null);
      await organizationService.addMember(newMember.email, newMember.org_role);
      setAddDialogOpen(false);
      setNewMember({ email: '', org_role: 'STUDENT' });
      await fetchAll();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Üye eklenemedi');
    }
  };

  const handleSignDpa = async () => {
    try {
      setActionError(null);
      await organizationService.signDpa(dpaSigner);
      setDpaDialogOpen(false);
      await fetchAll();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'DPA imzalanamadı');
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, member: OrgMember) => {
    setAnchorEl(event.currentTarget);
    setSelectedMember(member);
  };

  const handleMenuClose = () => setAnchorEl(null);

  const handleOpenRoleDialog = () => {
    if (selectedMember) {
      setRoleDraft(selectedMember.org_role);
      setRoleDialogOpen(true);
    }
    handleMenuClose();
  };

  const handleChangeRole = async () => {
    if (!selectedMember) {return;}
    try {
      setActionError(null);
      await organizationService.updateMember(selectedMember.user_id, { org_role: roleDraft });
      setRoleDialogOpen(false);
      await fetchAll();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Rol değiştirilemedi');
    }
  };

  const handleDeactivate = async () => {
    if (!selectedMember) {return;}
    handleMenuClose();
    if (!window.confirm(`${selectedMember.email || selectedMember.user_id} deaktive edilsin mi?`)) {
      return;
    }
    try {
      setActionError(null);
      await organizationService.removeMember(selectedMember.user_id);
      await fetchAll();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Üye deaktive edilemedi');
    }
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
        <ModernLoader message="Kurum bilgileri yükleniyor..." size="large" />
      </Box>
    );
  }

  const seatUsage = license?.seat_usage;
  const seatPercent =
    seatUsage?.limit && seatUsage.limit > 0
      ? Math.min(100, Math.round((seatUsage.used / seatUsage.limit) * 100))
      : 0;

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
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
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
                <Business sx={{ fontSize: 32, color: 'white' }} />
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
                  Okul Yönetimi
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  {orgInfo?.name || 'Kurum'} — üye ve lisans yönetimi
                </Typography>
              </Box>
            </Box>
          </Box>
        </motion.div>

        {actionError && (
          <Box sx={{ mb: 3 }}>
            <GlassCard glassIntensity="light" sx={{ borderLeft: `4px solid ${modernColors.gradients.error}` }}>
              <Typography variant="body2" color="error">{actionError}</Typography>
            </GlassCard>
          </Box>
        )}

        {/* DPA Banner */}
        {dpaStatus && !dpaStatus.signed && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <GlassCard glassIntensity="medium" elevated sx={{ mb: 3, borderLeft: '4px solid #f59e0b' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Warning sx={{ color: '#f59e0b' }} />
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                      Veri İşleme Sözleşmesi (DPA) imzalanmadı
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Kurum aktivasyonu için DPA imzası gereklidir.
                    </Typography>
                  </Box>
                </Box>
                <ModernButton
                  variant="gradient"
                  gradient={modernColors.gradients.fire}
                  startIcon={<Gavel />}
                  onClick={() => setDpaDialogOpen(true)}
                >
                  İmzala
                </ModernButton>
              </Box>
            </GlassCard>
          </motion.div>
        )}

        {/* Org Info + Seat Meter */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} md={6}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.primary}>
                <Typography variant="caption" color="text.secondary">Kurum Durumu</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                  <Chip
                    icon={orgInfo?.status === 'active' ? <CheckCircle fontSize="small" /> : <Warning fontSize="small" />}
                    label={orgInfo?.status || 'bilinmiyor'}
                    size="small"
                    sx={{ background: modernColors.gradients.primary, color: 'white', fontWeight: 600 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    {orgInfo?.member_count ?? 0} aktif üye
                  </Typography>
                </Box>
              </GlassCard>
            </Grid>
            <Grid item xs={12} md={6}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.forest}>
                <Typography variant="caption" color="text.secondary">Koltuk Kullanımı (Öğrenci/Öğretmen)</Typography>
                <Typography variant="body2" sx={{ fontWeight: 700, mt: 0.5 }}>
                  {seatUsage ? `${seatUsage.used} / ${seatUsage.limit ?? '∞'}` : '—'}
                </Typography>
                {seatUsage?.limit !== null && seatUsage?.limit !== undefined && (
                  <LinearProgress
                    variant="determinate"
                    value={seatPercent}
                    color={seatUsage.over_limit ? 'error' : 'primary'}
                    sx={{ mt: 1, height: 8, borderRadius: 4 }}
                  />
                )}
              </GlassCard>
            </Grid>
          </Grid>
        </motion.div>

        {/* Members Table */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}>
          <GlassCard glassIntensity="medium" elevated>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Üye</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Rol</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>İşlemler</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <AnimatePresence mode="wait">
                    {members.map((member, index) => (
                      <TableRow
                        key={member.user_id}
                        component={motion.tr}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        transition={{ duration: 0.2, delay: index * 0.02 }}
                        hover
                      >
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                            <Avatar sx={{ width: 36, height: 36, background: ROLE_GRADIENTS[member.org_role], fontWeight: 700 }}>
                              {getInitials(member.email)}
                            </Avatar>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              <Email fontSize="small" color="action" />
                              <Typography variant="body2">{member.email || member.user_id}</Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={ROLE_LABELS[member.org_role] || member.org_role}
                            size="small"
                            sx={{ background: ROLE_GRADIENTS[member.org_role], color: 'white', fontWeight: 600 }}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <IconButton size="small" onClick={(e) => handleMenuOpen(e, member)}>
                            <MoreVert />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </AnimatePresence>
                </TableBody>
              </Table>
            </TableContainer>

            {members.length === 0 && (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <Typography variant="h6" color="text.secondary">Henüz üye yok</Typography>
              </Box>
            )}
          </GlassCard>
        </motion.div>

        {/* FAB */}
        <Fab
          color="primary"
          aria-label="add member"
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            background: modernColors.gradients.fire,
            '&:hover': { background: modernColors.gradients.fire },
          }}
          onClick={() => setAddDialogOpen(true)}
        >
          <Add />
        </Fab>

        {/* Member Context Menu */}
        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
          <MenuItemComponent onClick={handleOpenRoleDialog}>
            <MoreVert fontSize="small" sx={{ mr: 1 }} />
            Rolü Değiştir
          </MenuItemComponent>
          <MenuItemComponent onClick={handleDeactivate} sx={{ color: 'error.main' }}>
            <Delete fontSize="small" sx={{ mr: 1 }} />
            Deaktive Et
          </MenuItemComponent>
        </Menu>

        {/* Add Member Dialog */}
        <Dialog
          open={addDialogOpen}
          onClose={() => setAddDialogOpen(false)}
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
            <Typography variant="h6" sx={{ fontWeight: 700 }}>Üye Ekle</Typography>
          </DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                label="E-posta"
                type="email"
                value={newMember.email}
                onChange={(e) => setNewMember({ ...newMember, email: e.target.value })}
                helperText="Platformda kayıtlı bir kullanıcının e-postası olmalı"
              />
              <FormControl fullWidth>
                <InputLabel>Rol</InputLabel>
                <Select
                  value={newMember.org_role}
                  label="Rol"
                  onChange={(e) => setNewMember({ ...newMember, org_role: e.target.value as OrgRole })}
                >
                  {(Object.keys(ROLE_LABELS) as OrgRole[]).map((role) => (
                    <MenuItem key={role} value={role}>{ROLE_LABELS[role]}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          </DialogContent>
          <DialogActions>
            <ModernButton variant="glass" onClick={() => setAddDialogOpen(false)}>İptal</ModernButton>
            <ModernButton
              variant="gradient"
              gradient={modernColors.gradients.success}
              onClick={handleAddMember}
              glow
            >
              Ekle
            </ModernButton>
          </DialogActions>
        </Dialog>

        {/* Change Role Dialog */}
        <Dialog open={roleDialogOpen} onClose={() => setRoleDialogOpen(false)} maxWidth="xs" fullWidth>
          <DialogTitle>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>Rolü Değiştir</Typography>
          </DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 1 }}>
              <FormControl fullWidth>
                <InputLabel>Rol</InputLabel>
                <Select
                  value={roleDraft}
                  label="Rol"
                  onChange={(e) => setRoleDraft(e.target.value as OrgRole)}
                >
                  {(Object.keys(ROLE_LABELS) as OrgRole[]).map((role) => (
                    <MenuItem key={role} value={role}>{ROLE_LABELS[role]}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          </DialogContent>
          <DialogActions>
            <ModernButton variant="glass" onClick={() => setRoleDialogOpen(false)}>İptal</ModernButton>
            <ModernButton variant="gradient" gradient={modernColors.gradients.primary} onClick={handleChangeRole} glow>
              Kaydet
            </ModernButton>
          </DialogActions>
        </Dialog>

        {/* Sign DPA Dialog */}
        <Dialog open={dpaDialogOpen} onClose={() => setDpaDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>DPA İmzala</Typography>
          </DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                label="İmzalayan Ad Soyad"
                value={dpaSigner.signer_name}
                onChange={(e) => setDpaSigner({ ...dpaSigner, signer_name: e.target.value })}
              />
              <TextField
                fullWidth
                label="İmzalayan E-posta"
                type="email"
                value={dpaSigner.signer_email}
                onChange={(e) => setDpaSigner({ ...dpaSigner, signer_email: e.target.value })}
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <ModernButton variant="glass" onClick={() => setDpaDialogOpen(false)}>İptal</ModernButton>
            <ModernButton variant="gradient" gradient={modernColors.gradients.success} onClick={handleSignDpa} glow>
              İmzala
            </ModernButton>
          </DialogActions>
        </Dialog>
      </Container>
    </Box>
  );
}

export default ModernOrgOnboardingPage;
