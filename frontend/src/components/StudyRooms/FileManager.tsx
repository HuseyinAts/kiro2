/**
 * Task 109.4: Study Room File Manager
 *
 * File upload, download, versioning, and metadata tracking.
 * Supports documents, images, videos, and archives.
 */

import {
  CloudUpload as UploadIcon,
  Description as DocumentIcon,
  Image as ImageIcon,
  VideoLibrary as VideoIcon,
  AudioFile as AudioIcon,
  Archive as ArchiveIcon,
  InsertDriveFile as FileIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  History as HistoryIcon,
  Info as InfoIcon,
  Folder as FolderIcon,
  GridView as GridViewIcon,
  ViewList as ListViewIcon,
} from '@mui/icons-material';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  LinearProgress,
  Chip,
  Menu,
  MenuItem,
  Tooltip,
  Grid,
  Card,
  CardContent,
  CardActions,
} from '@mui/material';
import axios from 'axios';
import * as React from 'react';
import {  useState, useEffect, useRef  } from 'react';

import { dateUtils } from '@/utils/dateUtils';

// ============================================================
// Types
// ============================================================

interface RoomFile {
  id: string;
  room_id: string;
  uploader_id: string;
  uploader_name: string;
  file_name: string;
  file_type: 'document' | 'image' | 'video' | 'audio' | 'archive' | 'other';
  file_size: number;
  file_url: string;
  mime_type: string;
  description?: string;
  version: number;
  is_current_version: boolean;
  download_count: number;
  created_at: string;
  updated_at: string;
  versions?: FileVersion[];
}

interface FileVersion {
  id: string;
  file_id: string;
  version: number;
  file_url: string;
  file_size: number;
  uploaded_by: string;
  uploaded_at: string;
  status: 'current' | 'archived';
}

interface FileManagerProps {
  roomId: string;
  currentUserId: string;
}

// ============================================================
// Component
// ============================================================

const FileManager: React.FC<FileManagerProps> = ({ roomId, currentUserId }) => {
  const [files, setFiles] = useState<RoomFile[]>([]);
  const [filteredFiles, setFilteredFiles] = useState<RoomFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filterType, setFilterType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFile, setSelectedFile] = useState<RoomFile | null>(null);
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);
  const [versionsDialogOpen, setVersionsDialogOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchFiles();
  }, [roomId]);

  useEffect(() => {
    filterFiles();
  }, [files, filterType, searchQuery]);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/v1/study-rooms/${roomId}/files`);
      setFiles(response.data);
    } catch (error) {
      console.error('Error fetching files:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterFiles = () => {
    let filtered = [...files];

    // Type filter
    if (filterType !== 'all') {
      filtered = filtered.filter((file) => file.file_type === filterType);
    }

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (file) =>
          file.file_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          file.description?.toLowerCase().includes(searchQuery.toLowerCase()),
      );
    }

    setFilteredFiles(filtered);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {return;}

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('room_id', roomId);

      const response = await axios.post(`/api/v1/study-rooms/${roomId}/files/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;
          setUploadProgress(progress);
        },
      });

      setFiles([response.data, ...files]);

      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Dosya yüklenirken bir hata oluştu.');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleFileDownload = async (file: RoomFile) => {
    try {
      // Update download count
      await axios.post(`/api/v1/study-rooms/${roomId}/files/${file.id}/download`);

      // Trigger download
      window.open(file.file_url, '_blank');

      // Update local state
      setFiles((prev) =>
        prev.map((f) =>
          f.id === file.id ? { ...f, download_count: f.download_count + 1 } : f,
        ),
      );
    } catch (error) {
      console.error('Error downloading file:', error);
    }
  };

  const handleFileDelete = async (fileId: string) => {
    if (!window.confirm('Bu dosyayı silmek istediğinizden emin misiniz?')) {return;}

    try {
      await axios.delete(`/api/v1/study-rooms/${roomId}/files/${fileId}`);
      setFiles((prev) => prev.filter((f) => f.id !== fileId));
      setAnchorEl(null);
    } catch (error) {
      console.error('Error deleting file:', error);
      alert('Dosya silinirken bir hata oluştu.');
    }
  };

  const handleShowVersions = async (file: RoomFile) => {
    try {
      const response = await axios.get(`/api/v1/study-rooms/${roomId}/files/${file.id}/versions`);
      setSelectedFile({ ...file, versions: response.data });
      setVersionsDialogOpen(true);
    } catch (error) {
      console.error('Error fetching versions:', error);
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, file: RoomFile) => {
    setAnchorEl(event.currentTarget);
    setSelectedFile(file);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case 'document':
        return <DocumentIcon sx={{ fontSize: 48, color: 'primary.main' }} />;
      case 'image':
        return <ImageIcon sx={{ fontSize: 48, color: 'success.main' }} />;
      case 'video':
        return <VideoIcon sx={{ fontSize: 48, color: 'error.main' }} />;
      case 'audio':
        return <AudioIcon sx={{ fontSize: 48, color: 'warning.main' }} />;
      case 'archive':
        return <ArchiveIcon sx={{ fontSize: 48, color: 'secondary.main' }} />;
      default:
        return <FileIcon sx={{ fontSize: 48, color: 'text.secondary' }} />;
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) {return `${bytes} B`;}
    if (bytes < 1024 * 1024) {return `${(bytes / 1024).toFixed(2)} KB`;}
    if (bytes < 1024 * 1024 * 1024) {return `${(bytes / 1024 / 1024).toFixed(2)} MB`;}
    return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
  };

  const renderGridView = () => (
    <Grid container spacing={2}>
      {filteredFiles.map((file) => (
        <Grid item xs={12} sm={6} md={4} lg={3} key={file.id}>
          <Card
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              '&:hover': {
                boxShadow: 4,
                transform: 'translateY(-2px)',
                transition: 'all 0.2s ease',
              },
            }}
          >
            <CardContent sx={{ flex: 1, textAlign: 'center' }}>
              {/* File Icon or Preview */}
              {file.file_type === 'image' ? (
                <Box
                  component="img"
                  src={file.file_url}
                  alt={file.file_name}
                  sx={{
                    width: '100%',
                    height: 120,
                    objectFit: 'cover',
                    borderRadius: 1,
                    mb: 2,
                  }}
                />
              ) : (
                <Box sx={{ mb: 2 }}>{getFileIcon(file.file_type)}</Box>
              )}

              {/* File Name */}
              <Tooltip title={file.file_name}>
                <Typography
                  variant="subtitle2"
                  fontWeight="bold"
                  noWrap
                  sx={{ mb: 0.5 }}
                >
                  {file.file_name}
                </Typography>
              </Tooltip>

              {/* File Info */}
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mb: 1 }}>
                <Chip label={formatFileSize(file.file_size)} size="small" />
                {file.version > 1 && (
                  <Chip label={`v${file.version}`} size="small" color="primary" />
                )}
              </Box>

              {/* Uploader and Date */}
              <Typography variant="caption" color="text.secondary" display="block">
                {file.uploader_name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {dateUtils.fromNow(file.created_at)}
              </Typography>
            </CardContent>

            <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
              <Button
                size="small"
                startIcon={<DownloadIcon />}
                onClick={() => handleFileDownload(file)}
              >
                İndir
              </Button>
              <IconButton size="small" onClick={(e) => handleMenuOpen(e, file)}>
                <MoreVertIcon />
              </IconButton>
            </CardActions>
          </Card>
        </Grid>
      ))}
    </Grid>
  );

  const renderListView = () => (
    <List>
      {filteredFiles.map((file) => (
        <ListItem
          key={file.id}
          sx={{
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            mb: 1,
            '&:hover': { bgcolor: 'action.hover' },
          }}
        >
          <ListItemIcon>{getFileIcon(file.file_type)}</ListItemIcon>
          <ListItemText
            primary={file.file_name}
            secondary={
              <Box component="span" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <span>{formatFileSize(file.file_size)}</span>
                <span>•</span>
                <span>{file.uploader_name}</span>
                <span>•</span>
                <span>
                  {dateUtils.fromNow(file.created_at)}
                </span>
                {file.version > 1 && (
                  <>
                    <span>•</span>
                    <Chip label={`v${file.version}`} size="small" color="primary" />
                  </>
                )}
              </Box>
            }
          />
          <ListItemSecondaryAction>
            <IconButton onClick={() => handleFileDownload(file)}>
              <DownloadIcon />
            </IconButton>
            <IconButton onClick={(e) => handleMenuOpen(e, file)}>
              <MoreVertIcon />
            </IconButton>
          </ListItemSecondaryAction>
        </ListItem>
      ))}
    </List>
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight="bold">
          📁 Dosyalar
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton
            color={viewMode === 'grid' ? 'primary' : 'default'}
            onClick={() => setViewMode('grid')}
          >
            <GridViewIcon />
          </IconButton>
          <IconButton
            color={viewMode === 'list' ? 'primary' : 'default'}
            onClick={() => setViewMode('list')}
          >
            <ListViewIcon />
          </IconButton>
          <input
            ref={fileInputRef}
            type="file"
            hidden
            onChange={handleFileUpload}
            disabled={uploading}
          />
          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            Dosya Yükle
          </Button>
        </Box>
      </Box>

      {/* Upload Progress */}
      {uploading && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            Yükleniyor... {uploadProgress}%
          </Typography>
          <LinearProgress variant="determinate" value={uploadProgress} />
        </Paper>
      )}

      {/* Filters */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <TextField
          placeholder="Dosya ara..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          size="small"
          sx={{ minWidth: 250 }}
        />
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip
            label="Tümü"
            onClick={() => setFilterType('all')}
            color={filterType === 'all' ? 'primary' : 'default'}
          />
          <Chip
            label="Dökümanlar"
            icon={<DocumentIcon />}
            onClick={() => setFilterType('document')}
            color={filterType === 'document' ? 'primary' : 'default'}
          />
          <Chip
            label="Resimler"
            icon={<ImageIcon />}
            onClick={() => setFilterType('image')}
            color={filterType === 'image' ? 'primary' : 'default'}
          />
          <Chip
            label="Videolar"
            icon={<VideoIcon />}
            onClick={() => setFilterType('video')}
            color={filterType === 'video' ? 'primary' : 'default'}
          />
        </Box>
      </Box>

      {/* File List/Grid */}
      {loading ? (
        <Typography>Yükleniyor...</Typography>
      ) : filteredFiles.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <FolderIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            Henüz dosya yok
          </Typography>
          <Typography color="text.secondary" sx={{ mt: 1 }}>
            İlk dosyayı sen yükle!
          </Typography>
        </Paper>
      ) : viewMode === 'grid' ? (
        renderGridView()
      ) : (
        renderListView()
      )}

      {/* File Context Menu */}
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
        <MenuItem
          onClick={() => {
            handleFileDownload(selectedFile!);
            handleMenuClose();
          }}
        >
          <DownloadIcon sx={{ mr: 1 }} fontSize="small" />
          İndir
        </MenuItem>
        <MenuItem
          onClick={() => {
            setInfoDialogOpen(true);
            handleMenuClose();
          }}
        >
          <InfoIcon sx={{ mr: 1 }} fontSize="small" />
          Bilgi
        </MenuItem>
        {selectedFile && selectedFile.version > 1 && (
          <MenuItem
            onClick={() => {
              handleShowVersions(selectedFile);
              handleMenuClose();
            }}
          >
            <HistoryIcon sx={{ mr: 1 }} fontSize="small" />
            Versiyonlar
          </MenuItem>
        )}
        {selectedFile?.uploader_id === currentUserId && (
          <MenuItem
            onClick={() => {
              handleFileDelete(selectedFile?.id || '');
            }}
            sx={{ color: 'error.main' }}
          >
            <DeleteIcon sx={{ mr: 1 }} fontSize="small" />
            Sil
          </MenuItem>
        )}
      </Menu>

      {/* File Info Dialog */}
      <Dialog open={infoDialogOpen} onClose={() => setInfoDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Dosya Bilgileri</DialogTitle>
        <DialogContent>
          {selectedFile && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Dosya Adı
                </Typography>
                <Typography>{selectedFile.file_name}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Boyut
                </Typography>
                <Typography>{formatFileSize(selectedFile.file_size)}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Tür
                </Typography>
                <Typography>{selectedFile.mime_type}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Yükleyen
                </Typography>
                <Typography>{selectedFile.uploader_name}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Yüklenme Tarihi
                </Typography>
                <Typography>
                  {new Date(selectedFile.created_at).toLocaleString('tr-TR')}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  İndirme Sayısı
                </Typography>
                <Typography>{selectedFile.download_count}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Versiyon
                </Typography>
                <Typography>{selectedFile.version}</Typography>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInfoDialogOpen(false)}>Kapat</Button>
        </DialogActions>
      </Dialog>

      {/* Versions Dialog */}
      <Dialog
        open={versionsDialogOpen}
        onClose={() => setVersionsDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Dosya Versiyonları</DialogTitle>
        <DialogContent>
          {selectedFile?.versions && (
            <List>
              {selectedFile.versions.map((version) => (
                <ListItem
                  key={version.id}
                  sx={{
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                  }}
                >
                  <ListItemText
                    primary={`Versiyon ${version.version}`}
                    secondary={
                      <>
                        {formatFileSize(version.file_size)} •{' '}
                        {new Date(version.uploaded_at).toLocaleString('tr-TR')} •{' '}
                        {version.uploaded_by}
                        {version.status === 'current' && (
                          <Chip
                            label="Güncel"
                            color="success"
                            size="small"
                            sx={{ ml: 1 }}
                          />
                        )}
                      </>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton onClick={() => window.open(version.file_url, '_blank')}>
                      <DownloadIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setVersionsDialogOpen(false)}>Kapat</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FileManager;
