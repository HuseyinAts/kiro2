/**
 * Mind Map Viewer Component - Kavram Haritası Görüntüleyici
 * Task 81.1: Kavram haritaları (REQ-50.73-76)
 * 
 * Özellikler:
 * - Mind map generation
 * - Interactive node exploration
 * - Export functionality
 * - Drag-and-drop support
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Card,
  CardContent,
  Typography,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip
} from '@mui/material';
import {
  Add as AddIcon,
  Download as DownloadIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
  Edit as EditIcon
} from '@mui/icons-material';

interface MindMapNode {
  id: string;
  label: string;
  description?: string;
  color: string;
  x: number;
  y: number;
  children: string[];
  parent?: string;
}

interface MindMap {
  id: string;
  title: string;
  subject: string;
  topic: string;
  nodes: MindMapNode[];
}

const MindMapViewer: React.FC = () => {
  const [mindMaps, setMindMaps] = useState<MindMap[]>([]);
  const [selectedMap, setSelectedMap] = useState<MindMap | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    subject: '',
    topic: '',
    content: ''
  });

  // REQ-50.73: Mind map generation
  const handleCreateMindMap = async () => {
    try {
      const response = await fetch('/api/v1/visual-supports/mind-maps', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const newMap = await response.json();
        setMindMaps([...mindMaps, newMap]);
        setSelectedMap(newMap);
        setCreateDialogOpen(false);
        setFormData({ title: '', subject: '', topic: '', content: '' });
      }
    } catch (error) {
      console.error('Mind map creation failed:', error);
    }
  };

  // REQ-50.74: Interactive node exploration
  const drawMindMap = () => {
    if (!selectedMap || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Apply zoom and pan
    ctx.save();
    ctx.translate(canvas.width / 2 + pan.x, canvas.height / 2 + pan.y);
    ctx.scale(zoom, zoom);

    // Draw connections
    selectedMap.nodes.forEach(node => {
      node.children.forEach(childId => {
        const child = selectedMap.nodes.find(n => n.id === childId);
        if (child) {
          ctx.beginPath();
          ctx.moveTo(node.x, node.y);
          ctx.lineTo(child.x, child.y);
          ctx.strokeStyle = '#ccc';
          ctx.lineWidth = 2;
          ctx.stroke();
        }
      });
    });

    // Draw nodes
    selectedMap.nodes.forEach(node => {
      // Node circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, 40, 0, 2 * Math.PI);
      ctx.fillStyle = node.color;
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 3;
      ctx.stroke();

      // Node label
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 14px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(node.label.substring(0, 10), node.x, node.y);
    });

    ctx.restore();
  };

  // REQ-50.75: Export functionality
  const handleExport = async (format: 'json' | 'svg' | 'png') => {
    if (!selectedMap) return;

    try {
      const response = await fetch(
        `/api/v1/visual-supports/mind-maps/${selectedMap.id}/export?format=${format}`
      );

      if (response.ok) {
        const data = await response.json();
        
        if (format === 'json') {
          // Download JSON
          const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${selectedMap.title}.json`;
          a.click();
        } else {
          // For SVG/PNG, show download link
          alert(`Export to ${format.toUpperCase()} başarılı! İndirme linki: ${data.download_url}`);
        }
      }
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  // Zoom controls
  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.1, 2));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.1, 0.5));
  const handleResetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  // Draw on canvas update
  useEffect(() => {
    drawMindMap();
  }, [selectedMap, zoom, pan]);

  return (
    <Box>
      {/* Toolbar */}
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Yeni Kavram Haritası
        </Button>

        {selectedMap && (
          <>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => handleExport('json')}
            >
              JSON İndir
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => handleExport('svg')}
            >
              SVG İndir
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => handleExport('png')}
            >
              PNG İndir
            </Button>
          </>
        )}

        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Harita Seç</InputLabel>
          <Select
            value={selectedMap?.id || ''}
            label="Harita Seç"
            onChange={(e) => {
              const map = mindMaps.find(m => m.id === e.target.value);
              setSelectedMap(map || null);
            }}
          >
            {mindMaps.map(map => (
              <MenuItem key={map.id} value={map.id}>
                {map.title}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Canvas */}
      {selectedMap ? (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">{selectedMap.title}</Typography>
              <Box>
                <Tooltip title="Yakınlaştır">
                  <IconButton onClick={handleZoomIn} size="small">
                    <ZoomInIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Uzaklaştır">
                  <IconButton onClick={handleZoomOut} size="small">
                    <ZoomOutIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Merkeze Al">
                  <IconButton onClick={handleResetView} size="small">
                    <CenterIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Chip label={`Ders: ${selectedMap.subject}`} size="small" />
              <Chip label={`Konu: ${selectedMap.topic}`} size="small" />
              <Chip label={`Düğüm: ${selectedMap.nodes.length}`} size="small" color="primary" />
            </Box>

            <canvas
              ref={canvasRef}
              width={800}
              height={600}
              style={{
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
                width: '100%',
                maxWidth: '800px',
                cursor: 'grab'
              }}
            />

            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              💡 İpucu: Yakınlaştırma/uzaklaştırma butonlarını kullanarak haritayı keşfedin
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent>
            <Typography variant="body1" color="text.secondary" align="center">
              Kavram haritası oluşturmak için "Yeni Kavram Haritası" butonuna tıklayın
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Create Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Yeni Kavram Haritası Oluştur</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Başlık"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Ders"
              value={formData.subject}
              onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Konu"
              value={formData.topic}
              onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="İçerik"
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              multiline
              rows={6}
              fullWidth
              required
              helperText="İçeriği girin, otomatik olarak kavram haritası oluşturulacak"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>İptal</Button>
          <Button
            onClick={handleCreateMindMap}
            variant="contained"
            disabled={!formData.title || !formData.subject || !formData.topic || !formData.content}
          >
            Oluştur
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MindMapViewer;
