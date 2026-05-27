/**
 * Task 109.1: Study Room List Component
 *
 * Displays list of study rooms with filtering and search.
 * Shows room cards with quick info and join buttons.
 */

import {
  Add as AddIcon,
  Search as SearchIcon,
  Lock as LockIcon,
  LockOpen as LockOpenIcon,
  Public as PublicIcon,
  People as PeopleIcon,
  VideoCall as VideoCallIcon,
  Chat as ChatIcon,
} from '@mui/icons-material';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Badge,
} from '@mui/material';
import * as React from 'react';
import { useState, useEffect } from 'react';

import { useStudyRooms } from '../../hooks/useStudyRooms';
import { studyRoomService } from '../../services/studyRoomService';
import type { StudyRoom as ApiStudyRoom } from '../../services/studyRoomService';

// ============================================================
// Types
// ============================================================

// Local display type extends the API type with optional UI-only fields
type StudyRoom = ApiStudyRoom & {
  // UI-only fields not returned by backend (kept for future compatibility)
  has_active_video?: boolean;
  unread_messages?: number;
};

interface StudyRoomListProps {
  onRoomSelect: (roomId: string) => void;
}

// ============================================================
// Component
// ============================================================

const StudyRoomList: React.FC<StudyRoomListProps> = ({ onRoomSelect }) => {
  // Wire to real API via useStudyRooms hook
  const { rooms: apiRooms, isLoading: loading, createRoom } = useStudyRooms();
  const [rooms, setRooms] = useState<StudyRoom[]>([]);
  const [filteredRooms, setFilteredRooms] = useState<StudyRoom[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [visibilityFilter, setVisibilityFilter] = useState<string>('all');
  const [tabValue, setTabValue] = useState(0); // 0: All (my-rooms), 1: Owned, 2: Joined
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newRoom, setNewRoom] = useState({
    name: '',
    description: '',
    topic: '',
    visibility: 'public' as 'public' | 'private',
    max_members: 50,
    tags: [] as string[],
  });

  // subject field does not exist on the backend StudyRoom model — use topic/tags for filtering

  // Sync API rooms into local state (supports tab-level client filtering)
  useEffect(() => {
    setRooms(apiRooms as StudyRoom[]);
  }, [apiRooms]);

  useEffect(() => {
    filterRooms();
  }, [rooms, searchQuery, visibilityFilter, tabValue]);

  const filterRooms = () => {
    let filtered = [...rooms];

    // Tab filter: 1 = rooms I own, 2 = rooms I joined (not owner)
    // Tab 0 = all my rooms (owned + joined) — backend my-rooms returns both
    if (tabValue === 1) {
      filtered = filtered.filter((room) => room.user_role === 'owner');
    } else if (tabValue === 2) {
      filtered = filtered.filter((room) => room.user_role !== 'owner');
    }

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (room) =>
          room.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (room.description ?? '').toLowerCase().includes(searchQuery.toLowerCase()) ||
          (room.topic ?? '').toLowerCase().includes(searchQuery.toLowerCase()),
      );
    }

    // Visibility filter
    if (visibilityFilter !== 'all') {
      filtered = filtered.filter((room) => room.visibility === visibilityFilter);
    }

    setFilteredRooms(filtered);
  };

  const handleCreateRoom = async () => {
    try {
      await createRoom({
        name: newRoom.name,
        description: newRoom.description || undefined,
        topic: newRoom.topic || undefined,
        visibility: newRoom.visibility,
        max_members: newRoom.max_members,
        tags: newRoom.tags,
      });
      setCreateDialogOpen(false);
      setNewRoom({
        name: '',
        description: '',
        topic: '',
        visibility: 'public',
        max_members: 50,
        tags: [],
      });
    } catch (error) {
      console.error('Error creating room:', error);
    }
  };

  const handleJoinRoom = async (roomId: string, visibility: string) => {
    try {
      if (visibility === 'private') {
        // Private rooms require invitation — guide user instead
        alert('Bu oda davetiye gerektirir. Oda sahibinden davet isteyin.');
        return;
      }
      await studyRoomService.joinRoom(roomId);
      onRoomSelect(roomId);
    } catch (error) {
      console.error('Error joining room:', error);
      alert('Odaya katılırken bir hata oluştu.');
    }
  };

  const getVisibilityIcon = (visibility: string) => {
    switch (visibility) {
      case 'public':
        return <PublicIcon fontSize="small" />;
      case 'private':
        return <LockIcon fontSize="small" />;
      case 'password':
        return <LockOpenIcon fontSize="small" />;
      default:
        return <PublicIcon fontSize="small" />;
    }
  };

  const getVisibilityLabel = (visibility: string) => {
    switch (visibility) {
      case 'public':
        return 'Herkese Açık';
      case 'private':
        return 'Özel';
      case 'password':
        return 'Şifre Korumalı';
      default:
        return visibility;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          📚 Grup Çalışma Odaları
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
          sx={{ borderRadius: 2 }}
        >
          Yeni Oda Oluştur
        </Button>
      </Box>

      {/* Tabs */}
      <Tabs value={tabValue} onChange={(_e, newValue) => setTabValue(newValue)} sx={{ mb: 2 }}>
        <Tab label="Tüm Odalar" />
        <Tab label="Benim Odalarım" />
        <Tab label="Katıldığım Odalar" />
      </Tabs>

      {/* Filters */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <TextField
          placeholder="Oda ara..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
          sx={{ flex: 1, minWidth: 250 }}
        />
        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel>Gizlilik</InputLabel>
          <Select
            value={visibilityFilter}
            label="Gizlilik"
            onChange={(e) => setVisibilityFilter(e.target.value)}
          >
            <MenuItem value="all">Tümü</MenuItem>
            <MenuItem value="public">Herkese Açık</MenuItem>
            <MenuItem value="private">Özel</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Room Grid */}
      <Grid container spacing={3}>
        {loading ? (
          <Grid item xs={12}>
            <Typography>Yükleniyor...</Typography>
          </Grid>
        ) : filteredRooms.length === 0 ? (
          <Grid item xs={12}>
            <Card sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary">
                Henüz çalışma odası yok
              </Typography>
              <Typography color="text.secondary" sx={{ mt: 1 }}>
                İlk odayı siz oluşturun!
              </Typography>
            </Card>
          </Grid>
        ) : (
          filteredRooms.map((room) => (
            <Grid item xs={12} sm={6} md={4} key={room.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  '&:hover': {
                    boxShadow: 4,
                    transform: 'translateY(-4px)',
                    transition: 'all 0.3s ease',
                  },
                }}
              >
                <CardContent sx={{ flex: 1 }}>
                  {/* Room Name and Visibility */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" component="h2" fontWeight="bold" sx={{ flex: 1 }}>
                      {room.name}
                    </Typography>
                    <Chip
                      icon={getVisibilityIcon(room.visibility)}
                      label={getVisibilityLabel(room.visibility)}
                      size="small"
                      sx={{ ml: 1 }}
                    />
                  </Box>

                  {/* Topic and Tags */}
                  <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                    {room.topic && (
                      <Chip label={room.topic} color="primary" size="small" />
                    )}
                    {room.tags.slice(0, 2).map((tag) => (
                      <Chip key={tag} label={tag} variant="outlined" size="small" />
                    ))}
                  </Box>

                  {/* Description */}
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      mb: 2,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                    }}
                  >
                    {room.description || 'Açıklama yok'}
                  </Typography>

                  {/* Stats */}
                  <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <PeopleIcon fontSize="small" color="action" />
                      <Typography variant="body2" color="text.secondary">
                        {room.current_member_count}/{room.max_members}
                      </Typography>
                    </Box>
                    {room.has_active_video && (
                      <Badge color="error" variant="dot">
                        <VideoCallIcon fontSize="small" color="action" />
                      </Badge>
                    )}
                    {room.unread_messages && room.unread_messages > 0 && (
                      <Badge badgeContent={room.unread_messages} color="primary">
                        <ChatIcon fontSize="small" color="action" />
                      </Badge>
                    )}
                  </Box>
                </CardContent>

                <CardActions sx={{ p: 2, pt: 0 }}>
                  <Button
                    fullWidth
                    variant="contained"
                    onClick={() => handleJoinRoom(room.id, room.visibility)}
                    disabled={room.current_member_count >= room.max_members}
                  >
                    {room.current_member_count >= room.max_members ? 'Dolu' : 'Katıl'}
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))
        )}
      </Grid>

      {/* Create Room Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Yeni Çalışma Odası Oluştur</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <TextField
              label="Oda Adı"
              value={newRoom.name}
              onChange={(e) => setNewRoom({ ...newRoom, name: e.target.value })}
              required
              fullWidth
            />
            <TextField
              label="Açıklama"
              value={newRoom.description}
              onChange={(e) => setNewRoom({ ...newRoom, description: e.target.value })}
              multiline
              rows={3}
              fullWidth
            />
            <TextField
              label="Konu"
              value={newRoom.topic}
              onChange={(e) => setNewRoom({ ...newRoom, topic: e.target.value })}
              placeholder="Örn: TYT Matematik - Denklemler"
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Gizlilik</InputLabel>
              <Select
                value={newRoom.visibility}
                label="Gizlilik"
                onChange={(e) =>
                  setNewRoom({ ...newRoom, visibility: e.target.value as 'public' | 'private' })
                }
              >
                <MenuItem value="public">Herkese Açık</MenuItem>
                <MenuItem value="private">Özel (Sadece Davetli)</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Maksimum Üye Sayısı"
              type="number"
              value={newRoom.max_members}
              onChange={(e) => setNewRoom({ ...newRoom, max_members: parseInt(e.target.value) })}
              inputProps={{ min: 2, max: 100 }}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>İptal</Button>
          <Button onClick={handleCreateRoom} variant="contained" disabled={!newRoom.name}>
            Oluştur
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StudyRoomList;
