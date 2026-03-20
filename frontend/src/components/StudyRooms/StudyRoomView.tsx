/**
 * Task 109: Study Room View - Main Container
 *
 * Integrates all study room features:
 * - Chat, File Manager, Video Conference, Whiteboard
 */

import {
  ArrowBack as BackIcon,
  Chat as ChatIcon,
  Folder as FolderIcon,
  VideoCall as VideoIcon,
  Dashboard as WhiteboardIcon,
  Settings as SettingsIcon,
  MoreVert as MoreVertIcon,
  ExitToApp as ExitIcon,
} from '@mui/icons-material';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  IconButton,
  Avatar,
  AvatarGroup,
  Chip,
  Badge,
  Menu,
  MenuItem,
  Tooltip,
} from '@mui/material';
import axios from 'axios';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import ChatInterface from './ChatInterface';
import CollaborativeWhiteboard from './CollaborativeWhiteboard';
import FileManager from './FileManager';
import VideoConference from './VideoConference';

// ============================================================
// Types
// ============================================================

interface StudyRoom {
  id: string;
  name: string;
  description: string;
  topic: string;
  subject: string;
  visibility: 'public' | 'private' | 'password';
  status: 'active' | 'archived' | 'deleted';
  max_members: number;
  member_count: number;
  owner_id: string;
  owner_name?: string;
  created_at: string;
  updated_at: string;
}

interface Member {
  id: string;
  user_id: string;
  name: string;
  avatar?: string;
  role: 'owner' | 'admin' | 'moderator' | 'member';
  is_online: boolean;
  joined_at: string;
}

interface StudyRoomViewProps {
  roomId: string;
  currentUserId: string;
  currentUserName: string;
  onBack: () => void;
}

// ============================================================
// Component
// ============================================================

const StudyRoomView: React.FC<StudyRoomViewProps> = ({
  roomId,
  currentUserId,
  currentUserName,
  onBack,
}) => {
  const [room, setRoom] = useState<StudyRoom | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [activeTab, setActiveTab] = useState(0); // 0: Chat, 1: Files, 2: Video, 3: Whiteboard
  const [unreadMessages, _setUnreadMessages] = useState(0);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [isVideoActive, setIsVideoActive] = useState(false);

  useEffect(() => {
    fetchRoomDetails();
    fetchMembers();
  }, [roomId]);

  const fetchRoomDetails = async () => {
    try {
      const response = await axios.get(`/api/v1/study-rooms/${roomId}`);
      setRoom(response.data);
    } catch (error) {
      console.error('Error fetching room details:', error);
    }
  };

  const fetchMembers = async () => {
    try {
      const response = await axios.get(`/api/v1/study-rooms/${roomId}/members`);
      setMembers(response.data);
    } catch (error) {
      console.error('Error fetching members:', error);
    }
  };

  const handleLeaveRoom = async () => {
    if (!window.confirm('Odadan ayrılmak istediğinizden emin misiniz?')) {return;}

    try {
      await axios.post(`/api/v1/study-rooms/${roomId}/leave`);
      onBack();
    } catch (error) {
      console.error('Error leaving room:', error);
    }
  };

  const handleArchiveRoom = async () => {
    if (!window.confirm('Bu odayı arşivlemek istediğinizden emin misiniz?')) {return;}

    try {
      await axios.post(`/api/v1/study-rooms/${roomId}/archive`);
      onBack();
    } catch (error) {
      console.error('Error archiving room:', error);
    }
  };

  const handleDeleteRoom = async () => {
    if (!window.confirm('Bu odayı silmek istediğinizden emin misiniz? Bu işlem geri alınamaz!'))
      {return;}

    try {
      await axios.delete(`/api/v1/study-rooms/${roomId}`);
      onBack();
    } catch (error) {
      console.error('Error deleting room:', error);
    }
  };

  const isOwner = room?.owner_id === currentUserId;
  const currentMember = members.find((m) => m.user_id === currentUserId);
  const isAdmin = currentMember?.role === 'admin' || currentMember?.role === 'owner';

  if (!room) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography>Yükleniyor...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Header */}
      <Paper
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        <IconButton onClick={onBack}>
          <BackIcon />
        </IconButton>

        <Box sx={{ flex: 1 }}>
          <Typography variant="h6" fontWeight="bold">
            {room.name}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mt: 0.5 }}>
            {room.subject && <Chip label={room.subject} size="small" color="primary" />}
            {room.topic && <Chip label={room.topic} size="small" variant="outlined" />}
            <Typography variant="caption" color="text.secondary">
              {members.length} üye
            </Typography>
          </Box>
        </Box>

        {/* Online Members */}
        <Tooltip title="Çevrimiçi Üyeler">
          <AvatarGroup max={5} sx={{ cursor: 'pointer' }}>
            {members
              .filter((m) => m.is_online)
              .map((member) => (
                <Badge
                  key={member.id}
                  overlap="circular"
                  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                  variant="dot"
                  sx={{
                    '& .MuiBadge-badge': {
                      backgroundColor: '#44b700',
                      color: '#44b700',
                      boxShadow: '0 0 0 2px white',
                    },
                  }}
                >
                  <Avatar src={member.avatar} alt={member.name}>
                    {member.name.charAt(0).toUpperCase()}
                  </Avatar>
                </Badge>
              ))}
          </AvatarGroup>
        </Tooltip>

        {/* Room Menu */}
        <IconButton onClick={(e) => setAnchorEl(e.currentTarget)}>
          <MoreVertIcon />
        </IconButton>

        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={() => setAnchorEl(null)}>
          <MenuItem onClick={() => setAnchorEl(null)}>
            <SettingsIcon sx={{ mr: 1 }} fontSize="small" />
            Oda Ayarları
          </MenuItem>
          {isAdmin && (
            <MenuItem
              onClick={() => {
                handleArchiveRoom();
                setAnchorEl(null);
              }}
            >
              Arşivle
            </MenuItem>
          )}
          <MenuItem
            onClick={() => {
              handleLeaveRoom();
              setAnchorEl(null);
            }}
          >
            <ExitIcon sx={{ mr: 1 }} fontSize="small" />
            Odadan Ayrıl
          </MenuItem>
          {isOwner && (
            <MenuItem
              onClick={() => {
                handleDeleteRoom();
                setAnchorEl(null);
              }}
              sx={{ color: 'error.main' }}
            >
              Odayı Sil
            </MenuItem>
          )}
        </Menu>
      </Paper>

      {/* Tabs */}
      <Paper sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={activeTab} onChange={(_e, newValue) => setActiveTab(newValue)}>
          <Tab
            icon={
              <Badge badgeContent={unreadMessages} color="primary">
                <ChatIcon />
              </Badge>
            }
            label="Sohbet"
          />
          <Tab icon={<FolderIcon />} label="Dosyalar" />
          <Tab
            icon={
              isVideoActive ? (
                <Badge variant="dot" color="error">
                  <VideoIcon />
                </Badge>
              ) : (
                <VideoIcon />
              )
            }
            label="Video"
          />
          <Tab icon={<WhiteboardIcon />} label="Beyaz Tahta" />
        </Tabs>
      </Paper>

      {/* Content Area */}
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        {activeTab === 0 && (
          <ChatInterface
            roomId={roomId}
            currentUserId={currentUserId}
            currentUserName={currentUserName}
          />
        )}
        {activeTab === 1 && <FileManager roomId={roomId} currentUserId={currentUserId} />}
        {activeTab === 2 && (
          <VideoConference
            roomId={roomId}
            currentUserId={currentUserId}
            currentUserName={currentUserName}
            onLeave={() => setIsVideoActive(false)}
          />
        )}
        {activeTab === 3 && (
          <CollaborativeWhiteboard roomId={roomId} currentUserId={currentUserId} />
        )}
      </Box>
    </Box>
  );
};

export default StudyRoomView;
