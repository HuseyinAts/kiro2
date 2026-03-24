/**
 * ObaPage -- /oba
 * Guild/Clan sistemi. Olustur, katil, uyeler, XP havuzu.
 */
import { useEffect, useState, useCallback } from 'react';
import {
  Alert, Avatar, Box, Button, Card, CardContent, Chip, CircularProgress,
  Dialog, DialogActions, DialogContent, DialogTitle, Divider, LinearProgress,
  Stack, TextField, Typography,
} from '@mui/material';
import { Groups, Add, ExitToApp, Star, Person, EmojiEvents } from '@mui/icons-material';
import { apiRequest } from '../utils/apiHelpers';

interface ObaInfo {
  id: number;
  name: string;
  description: string | null;
  xp_pool: number;
  max_members: number;
  member_count: number;
  my_role: string | null;
}

interface ObaUye {
  user_id: string;
  display_name: string;
  role: string;
  joined_at: string | null;
}

const ROLE_LABEL: Record<string, { label: string; color: 'error' | 'warning' | 'default' }> = {
  bey: { label: 'Bey', color: 'error' },
  noker: { label: 'Noker', color: 'warning' },
  toycu: { label: 'Toycu', color: 'default' },
};

export default function ObaPage() {
  const [myOba, setMyOba] = useState<ObaInfo | null>(null);
  const [allObalar, setAllObalar] = useState<ObaInfo[]>([]);
  const [members, setMembers] = useState<ObaUye[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createDesc, setCreateDesc] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [myRes, listRes] = await Promise.all([
        apiRequest<{ success: boolean; data: ObaInfo | null }>('/api/v1/oba/my'),
        apiRequest<{ success: boolean; data: ObaInfo[] }>('/api/v1/oba/list'),
      ]);
      const my = myRes.data ?? myRes;
      setMyOba(my && typeof my === 'object' && 'id' in my ? my as ObaInfo : null);
      const list = listRes.data ?? listRes;
      setAllObalar(Array.isArray(list) ? list : []);

      // Fetch members if in an oba
      if (my && typeof my === 'object' && 'id' in my) {
        const membersRes = await apiRequest<{ success: boolean; data: ObaUye[] }>(
          `/api/v1/oba/${(my as ObaInfo).id}/members`
        );
        setMembers(Array.isArray(membersRes.data) ? membersRes.data : []);
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreate = async () => {
    if (!createName.trim()) return;
    setSubmitting(true);
    try {
      await apiRequest('/api/v1/oba/create', {
        method: 'POST',
        body: JSON.stringify({ name: createName.trim(), description: createDesc.trim() || null }),
      });
      setCreateOpen(false);
      setCreateName('');
      setCreateDesc('');
      setLoading(true);
      await fetchData();
    } catch (e) {
      setError(String(e));
    } finally {
      setSubmitting(false);
    }
  };

  const handleJoin = async (obaId: number) => {
    setSubmitting(true);
    try {
      await apiRequest(`/api/v1/oba/${obaId}/join`, { method: 'POST' });
      setLoading(true);
      await fetchData();
    } catch (e) {
      setError(String(e));
    } finally {
      setSubmitting(false);
    }
  };

  const handleLeave = async () => {
    setSubmitting(true);
    try {
      await apiRequest('/api/v1/oba/leave', { method: 'POST' });
      setMyOba(null);
      setMembers([]);
      setLoading(true);
      await fetchData();
    } catch (e) {
      setError(String(e));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return (
    <Box textAlign="center" py={8}>
      <CircularProgress size={52} />
      <Typography mt={2} color="text.secondary">Oba bilgileri yukleniyor...</Typography>
    </Box>
  );

  return (
    <Box maxWidth={800} mx="auto" py={3}>
      {/* Header */}
      <Stack direction="row" spacing={2} alignItems="center" mb={3}>
        <Groups color="primary" sx={{ fontSize: 36 }} />
        <Box flex={1}>
          <Typography variant="h5" fontWeight={800}>Obalar</Typography>
          <Typography variant="body2" color="text.secondary">
            Topluluguna katil, birlikte guclen
          </Typography>
        </Box>
        {!myOba && (
          <Button variant="contained" startIcon={<Add />} onClick={() => setCreateOpen(true)}>
            Oba Kur
          </Button>
        )}
      </Stack>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}

      {/* My Oba Card */}
      {myOba && (
        <Card sx={{ mb: 3, borderRadius: 3, border: '2px solid', borderColor: 'primary.main' }}>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
              <Box>
                <Typography variant="h6" fontWeight={800}>{myOba.name}</Typography>
                {myOba.description && (
                  <Typography variant="body2" color="text.secondary">{myOba.description}</Typography>
                )}
              </Box>
              <Stack direction="row" spacing={1} alignItems="center">
                <Chip
                  label={ROLE_LABEL[myOba.my_role ?? 'toycu']?.label ?? 'Uye'}
                  color={ROLE_LABEL[myOba.my_role ?? 'toycu']?.color ?? 'default'}
                  size="small"
                />
                <Button
                  size="small" color="error" variant="outlined"
                  startIcon={<ExitToApp />} onClick={handleLeave}
                  disabled={submitting}
                >
                  Ayril
                </Button>
              </Stack>
            </Stack>

            {/* Stats */}
            <Stack direction="row" spacing={3} mb={2}>
              <Box textAlign="center">
                <Typography variant="h5" fontWeight={700} color="primary.main">
                  <EmojiEvents sx={{ fontSize: 20, verticalAlign: 'middle', mr: 0.5 }} />
                  {myOba.xp_pool.toLocaleString('tr-TR')}
                </Typography>
                <Typography variant="caption" color="text.secondary">XP Havuzu</Typography>
              </Box>
              <Box textAlign="center">
                <Typography variant="h5" fontWeight={700}>
                  {myOba.member_count}/{myOba.max_members}
                </Typography>
                <Typography variant="caption" color="text.secondary">Uye</Typography>
              </Box>
            </Stack>

            <LinearProgress
              variant="determinate"
              value={Math.round((myOba.member_count / myOba.max_members) * 100)}
              sx={{ height: 6, borderRadius: 3, mb: 2 }}
            />

            {/* Members */}
            <Typography variant="subtitle2" fontWeight={700} mb={1}>Uyeler</Typography>
            <Divider sx={{ mb: 1 }} />
            <Stack spacing={0.5}>
              {members.map(m => (
                <Stack key={m.user_id} direction="row" spacing={1.5} alignItems="center" py={0.5}>
                  <Avatar sx={{ width: 28, height: 28, fontSize: 12 }}>
                    {m.display_name[0]?.toUpperCase()}
                  </Avatar>
                  <Typography variant="body2" fontWeight={m.role === 'bey' ? 700 : 400} flex={1}>
                    {m.display_name}
                  </Typography>
                  <Chip
                    size="small" variant="outlined"
                    icon={m.role === 'bey' ? <Star fontSize="small" /> : <Person fontSize="small" />}
                    label={ROLE_LABEL[m.role]?.label ?? m.role}
                    color={ROLE_LABEL[m.role]?.color ?? 'default'}
                  />
                </Stack>
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* Available Obalar */}
      {!myOba && (
        <>
          <Typography variant="subtitle1" fontWeight={700} mb={2}>
            Katilabilecek Obalar ({allObalar.length})
          </Typography>
          {allObalar.length === 0 && (
            <Alert severity="info">Henuz aktif oba yok. Ilk obayi sen kur!</Alert>
          )}
          <Box display="grid" gridTemplateColumns="repeat(auto-fill, minmax(250px, 1fr))" gap={2}>
            {allObalar.map(oba => (
              <Card key={oba.id} variant="outlined" sx={{ borderRadius: 2 }}>
                <CardContent sx={{ pb: '12px !important' }}>
                  <Typography variant="subtitle2" fontWeight={700}>{oba.name}</Typography>
                  {oba.description && (
                    <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                      {oba.description}
                    </Typography>
                  )}
                  <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                    <Chip size="small" label={`${oba.member_count}/${oba.max_members} uye`} variant="outlined" />
                    <Chip size="small" label={`${oba.xp_pool} XP`} color="primary" variant="outlined" />
                  </Stack>
                  <Button
                    fullWidth size="small" variant="contained"
                    disabled={submitting || oba.member_count >= oba.max_members}
                    onClick={() => handleJoin(oba.id)}
                  >
                    {oba.member_count >= oba.max_members ? 'Dolu' : 'Katil'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </Box>
        </>
      )}

      {/* Create Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Yeni Oba Kur</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus fullWidth margin="dense" label="Oba Adi"
            value={createName} onChange={e => setCreateName(e.target.value)}
            inputProps={{ maxLength: 100 }}
          />
          <TextField
            fullWidth margin="dense" label="Aciklama (istege bagli)" multiline rows={2}
            value={createDesc} onChange={e => setCreateDesc(e.target.value)}
            inputProps={{ maxLength: 500 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Iptal</Button>
          <Button variant="contained" onClick={handleCreate} disabled={submitting || !createName.trim()}>
            Olustur
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
