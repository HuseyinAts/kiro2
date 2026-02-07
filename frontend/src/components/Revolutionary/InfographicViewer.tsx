/**
 * Infographic Viewer Component - İnfografik Görüntüleyici
 * Task 81.2: İnfografikler (REQ-50.77-80)
 */

import { Add as AddIcon } from '@mui/icons-material';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import * as React from 'react';
import {  useState  } from 'react';

const InfographicViewer: React.FC = () => {
  const [templates, _setTemplates] = useState([
    { id: 'timeline', name: 'Zaman Çizelgesi', icon: '📅' },
    { id: 'comparison', name: 'Karşılaştırma', icon: '⚖️' },
    { id: 'process', name: 'Süreç Akışı', icon: '🔄' },
    { id: 'hierarchy', name: 'Hiyerarşi', icon: '🏛️' },
  ]);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    subject: '',
    topic: '',
    template: 'timeline',
  });

  // REQ-50.77: Visual summary generation
  const handleCreate = async () => {
    try {
      const response = await fetch('/api/v1/visual-supports/infographics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          data: [{ content: 'Örnek veri' }],
        }),
      });

      if (response.ok) {
        alert('İnfografik oluşturuldu!');
        setCreateDialogOpen(false);
      }
    } catch (error) {
      console.error('Infographic creation failed:', error);
    }
  };

  return (
    <Box>
      <Button
        variant="contained"
        startIcon={<AddIcon />}
        onClick={() => setCreateDialogOpen(true)}
        sx={{ mb: 2 }}
      >
        Yeni İnfografik
      </Button>

      {/* REQ-50.79: Customizable templates */}
      <Typography variant="h6" sx={{ mb: 2 }}>Şablonlar</Typography>
      <Grid container spacing={2}>
        {templates.map(template => (
          <Grid item xs={12} sm={6} md={3} key={template.id}>
            <Card sx={{ cursor: 'pointer', '&:hover': { boxShadow: 4 } }}>
              <CardContent>
                <Typography variant="h3" align="center">{template.icon}</Typography>
                <Typography variant="h6" align="center">{template.name}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Create Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Yeni İnfografik Oluştur</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Başlık"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              fullWidth
            />
            <TextField
              label="Ders"
              value={formData.subject}
              onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
              fullWidth
            />
            <TextField
              label="Konu"
              value={formData.topic}
              onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Şablon</InputLabel>
              <Select
                value={formData.template}
                label="Şablon"
                onChange={(e) => setFormData({ ...formData, template: e.target.value })}
              >
                {templates.map(t => (
                  <MenuItem key={t.id} value={t.id}>{t.icon} {t.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>İptal</Button>
          <Button onClick={handleCreate} variant="contained">Oluştur</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default InfographicViewer;
