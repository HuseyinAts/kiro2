import {
  Add,
  Edit,
  Delete,
  Visibility,
  Upload,
  Download,
  CheckCircle,
  Cancel,
} from '@mui/icons-material';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
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
  Alert,
  CircularProgress,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { ContentQuestion, EducationalContent } from '../../services/adminService';

// Question ve EducationalContent tipleri artık adminService'den geliyor

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`content-tabpanel-${index}`}
      aria-labelledby={`content-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export const ContentManagement: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [questions, setQuestions] = useState<ContentQuestion[]>([]);
  const [contents, setContents] = useState<EducationalContent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Dialog states
  const [openQuestionDialog, setOpenQuestionDialog] = useState(false);
  const [openContentDialog, setOpenContentDialog] = useState(false);
  const [_editingQuestion, _setEditingQuestion] = useState<ContentQuestion | null>(null);
  const [_editingContent, _setEditingContent] = useState<EducationalContent | null>(null);

  // Form states
  const [questionForm, setQuestionForm] = useState({
    soru_metni: '',
    secenekler: ['', '', '', '', ''],
    dogru_cevap: 'A',
    konu: '',
    zorluk_seviyesi: 'orta',
    sinav_tipi: 'TYT',
  });

  const [contentForm, setContentForm] = useState({
    baslik: '',
    icerik_tipi: 'video',
    konu: '',
    seviye: 'orta',
    url: '',
    aciklama: '',
  });

  useEffect(() => {
    if (currentTab === 0) {
      fetchQuestions();
    } else if (currentTab === 1) {
      fetchContents();
    }
  }, [currentTab]);

  const fetchQuestions = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/v1/admin/content/questions', {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Sorular alınamadı');
      }

      const data = await response.json();

      if (data.success) {
        setQuestions(data.data);
      } else {
        throw new Error(data.message || 'Veri alınamadı');
      }
    } catch (err) {
      console.error('Questions fetch error:', err);
      setError(err instanceof Error ? err.message : 'Bilinmeyen hata');

      // Mock data
      const mockQuestions: ContentQuestion[] = [
        {
          soru_id: '1',
          soru_metni: 'Türkiye\'nin başkenti neresidir?',
          secenekler: ['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya'],
          dogru_cevap: 'B',
          konu: 'Coğrafya',
          alt_konu: 'Türkiye Coğrafyası',
          zorluk_seviyesi: 'KOLAY',
          sinav_tipi: 'TYT',
          olusturma_tarihi: '2024-01-01T00:00:00Z',
          durum: 'aktif',
          onay_durumu: 'onaylandi',
          olusturan: 'admin',
        },
      ];
      setQuestions(mockQuestions);
    } finally {
      setLoading(false);
    }
  };

  const fetchContents = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/v1/admin/content/educational', {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('İçerikler alınamadı');
      }

      const data = await response.json();

      if (data.success) {
        setContents(data.data);
      } else {
        throw new Error(data.message || 'Veri alınamadı');
      }
    } catch (err) {
      console.error('Contents fetch error:', err);
      setError(err instanceof Error ? err.message : 'Bilinmeyen hata');

      // Mock data
      const mockContents: EducationalContent[] = [
        {
          icerik_id: '1',
          baslik: 'Matematik Türev Konusu',
          aciklama: 'Türev konusunu anlatan eğitim videosu',
          icerik_tipi: 'video',
          konu: 'Matematik',
          zorluk_seviyesi: 'ORTA',
          seviye: 'orta',
          url: 'https://youtube.com/watch?v=example',
          etiketler: ['matematik', 'türev', 'analiz'],
          olusturma_tarihi: '2024-01-01T00:00:00Z',
          durum: 'aktif',
          goruntulenme_sayisi: 150,
          begeni_sayisi: 25,
          onay_durumu: 'onaylandi',
          olusturan: 'ogretmen1',
        },
      ];
      setContents(mockContents);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateQuestion = async () => {
    try {
      const response = await fetch('/api/v1/admin/content/questions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(questionForm),
      });

      if (!response.ok) {
        throw new Error('Soru oluşturulamadı');
      }

      const data = await response.json();

      if (data.success) {
        setOpenQuestionDialog(false);
        resetQuestionForm();
        fetchQuestions();
      } else {
        throw new Error(data.message || 'Soru oluşturulamadı');
      }
    } catch (err) {
      console.error('Create question error:', err);
      setError(err instanceof Error ? err.message : 'Soru oluşturulamadı');
    }
  };

  const handleCreateContent = async () => {
    try {
      const response = await fetch('/api/v1/admin/content/educational', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(contentForm),
      });

      if (!response.ok) {
        throw new Error('İçerik oluşturulamadı');
      }

      const data = await response.json();

      if (data.success) {
        setOpenContentDialog(false);
        resetContentForm();
        fetchContents();
      } else {
        throw new Error(data.message || 'İçerik oluşturulamadı');
      }
    } catch (err) {
      console.error('Create content error:', err);
      setError(err instanceof Error ? err.message : 'İçerik oluşturulamadı');
    }
  };

  const handleApproveQuestion = async (questionId: string) => {
    try {
      const response = await fetch(`/api/v1/admin/content/questions/${questionId}/approve`, {
        method: 'PUT',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Soru onaylanamadı');
      }

      fetchQuestions();
    } catch (err) {
      console.error('Approve question error:', err);
      setError(err instanceof Error ? err.message : 'Soru onaylanamadı');
    }
  };

  const handleRejectQuestion = async (questionId: string) => {
    try {
      const response = await fetch(`/api/v1/admin/content/questions/${questionId}/reject`, {
        method: 'PUT',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Soru reddedilemedi');
      }

      fetchQuestions();
    } catch (err) {
      console.error('Reject question error:', err);
      setError(err instanceof Error ? err.message : 'Soru reddedilemedi');
    }
  };

  const resetQuestionForm = () => {
    setQuestionForm({
      soru_metni: '',
      secenekler: ['', '', '', '', ''],
      dogru_cevap: 'A',
      konu: '',
      zorluk_seviyesi: 'orta',
      sinav_tipi: 'TYT',
    });
  };

  const resetContentForm = () => {
    setContentForm({
      baslik: '',
      icerik_tipi: 'video',
      konu: '',
      seviye: 'orta',
      url: '',
      aciklama: '',
    });
  };

  const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (status) {
      case 'onaylandi': return 'success';
      case 'reddedildi': return 'error';
      case 'bekliyor': return 'warning';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'onaylandi': return 'Onaylandı';
      case 'reddedildi': return 'Reddedildi';
      case 'bekliyor': return 'Bekliyor';
      default: return status;
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h2">
          İçerik Yönetimi
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Upload />}
            sx={{ mr: 1 }}
          >
            Toplu Yükle
          </Button>
          <Button
            variant="outlined"
            startIcon={<Download />}
          >
            Dışa Aktar
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper>
        <Tabs
          value={currentTab}
          onChange={(_, newValue) => setCurrentTab(newValue)}
          aria-label="content management tabs"
        >
          <Tab label="Soru Bankası" />
          <Tab label="Eğitim İçerikleri" />
          <Tab label="Kategoriler" />
        </Tabs>

        <TabPanel value={currentTab} index={0}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Soru Bankası</Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setOpenQuestionDialog(true)}
            >
              Yeni Soru
            </Button>
          </Box>

          {loading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : (
            <Grid container spacing={2}>
              {questions.map((question) => (
                <Grid item xs={12} md={6} key={question.soru_id}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {question.soru_metni.substring(0, 100)}...
                      </Typography>
                      <Box display="flex" gap={1} mb={2}>
                        <Chip label={question.konu} size="small" />
                        <Chip label={question.sinav_tipi} size="small" color="primary" />
                        <Chip label={question.zorluk_seviyesi} size="small" color="secondary" />
                        <Chip
                          label={getStatusText(question.onay_durumu)}
                          size="small"
                          color={getStatusColor(question.onay_durumu)}
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        Oluşturan: {question.olusturan}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Tarih: {new Date(question.olusturma_tarihi).toLocaleDateString('tr-TR')}
                      </Typography>
                    </CardContent>
                    <CardActions>
                      <Tooltip title="Görüntüle">
                        <IconButton size="small" aria-label="Soruyu görüntüle">
                          <Visibility />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Düzenle">
                        <IconButton size="small" aria-label="Soruyu düzenle">
                          <Edit />
                        </IconButton>
                      </Tooltip>
                      {question.onay_durumu === 'bekliyor' && (
                        <>
                          <Tooltip title="Onayla">
                            <IconButton
                              size="small"
                              color="success"
                              onClick={() => handleApproveQuestion(question.soru_id)}
                              aria-label="Soruyu onayla"
                            >
                              <CheckCircle />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Reddet">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleRejectQuestion(question.soru_id)}
                              aria-label="Soruyu reddet"
                            >
                              <Cancel />
                            </IconButton>
                          </Tooltip>
                        </>
                      )}
                      <Tooltip title="Sil">
                        <IconButton size="small" color="error" aria-label="Soruyu sil">
                          <Delete />
                        </IconButton>
                      </Tooltip>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </TabPanel>

        <TabPanel value={currentTab} index={1}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Eğitim İçerikleri</Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setOpenContentDialog(true)}
            >
              Yeni İçerik
            </Button>
          </Box>

          {loading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : (
            <Grid container spacing={2}>
              {contents.map((content) => (
                <Grid item xs={12} md={6} key={content.icerik_id}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {content.baslik}
                      </Typography>
                      <Typography variant="body2" paragraph>
                        {content.aciklama}
                      </Typography>
                      <Box display="flex" gap={1} mb={2}>
                        <Chip label={content.icerik_tipi} size="small" />
                        <Chip label={content.konu} size="small" color="primary" />
                        <Chip label={content.seviye} size="small" color="secondary" />
                        <Chip
                          label={getStatusText(content.onay_durumu)}
                          size="small"
                          color={getStatusColor(content.onay_durumu)}
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        Oluşturan: {content.olusturan}
                      </Typography>
                    </CardContent>
                    <CardActions>
                      <Tooltip title="Görüntüle">
                        <IconButton size="small">
                          <Visibility />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Düzenle">
                        <IconButton size="small">
                          <Edit />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Sil">
                        <IconButton size="small" color="error">
                          <Delete />
                        </IconButton>
                      </Tooltip>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </TabPanel>

        <TabPanel value={currentTab} index={2}>
          <Typography variant="h6">Kategori Yönetimi</Typography>
          <Alert severity="info" sx={{ mt: 2 }}>
            Kategori yönetimi yakında eklenecek.
          </Alert>
        </TabPanel>
      </Paper>

      {/* Question Dialog */}
      <Dialog open={openQuestionDialog} onClose={() => setOpenQuestionDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Yeni Soru Oluştur</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Soru Metni"
              multiline
              rows={3}
              value={questionForm.soru_metni}
              onChange={(e) => setQuestionForm({ ...questionForm, soru_metni: e.target.value })}
              margin="normal"
              required
            />

            {questionForm.secenekler.map((secenek, index) => (
              <TextField
                key={index}
                fullWidth
                label={`Seçenek ${String.fromCharCode(65 + index)}`}
                value={secenek}
                onChange={(e) => {
                  const newSecenekler = [...questionForm.secenekler];
                  newSecenekler[index] = e.target.value;
                  setQuestionForm({ ...questionForm, secenekler: newSecenekler });
                }}
                margin="normal"
                required
              />
            ))}

            <FormControl fullWidth margin="normal" required>
              <InputLabel>Doğru Cevap</InputLabel>
              <Select
                value={questionForm.dogru_cevap}
                onChange={(e) => setQuestionForm({ ...questionForm, dogru_cevap: e.target.value })}
                label="Doğru Cevap"
              >
                <MenuItem value="A">A</MenuItem>
                <MenuItem value="B">B</MenuItem>
                <MenuItem value="C">C</MenuItem>
                <MenuItem value="D">D</MenuItem>
                <MenuItem value="E">E</MenuItem>
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Konu"
              value={questionForm.konu}
              onChange={(e) => setQuestionForm({ ...questionForm, konu: e.target.value })}
              margin="normal"
              required
            />

            <FormControl fullWidth margin="normal" required>
              <InputLabel>Zorluk Seviyesi</InputLabel>
              <Select
                value={questionForm.zorluk_seviyesi}
                onChange={(e) => setQuestionForm({ ...questionForm, zorluk_seviyesi: e.target.value })}
                label="Zorluk Seviyesi"
              >
                <MenuItem value="kolay">Kolay</MenuItem>
                <MenuItem value="orta">Orta</MenuItem>
                <MenuItem value="zor">Zor</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth margin="normal" required>
              <InputLabel>Sınav Tipi</InputLabel>
              <Select
                value={questionForm.sinav_tipi}
                onChange={(e) => setQuestionForm({ ...questionForm, sinav_tipi: e.target.value })}
                label="Sınav Tipi"
              >
                <MenuItem value="TYT">TYT</MenuItem>
                <MenuItem value="AYT">AYT</MenuItem>
                <MenuItem value="YDT">YDT</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenQuestionDialog(false)}>İptal</Button>
          <Button onClick={handleCreateQuestion} variant="contained">Oluştur</Button>
        </DialogActions>
      </Dialog>

      {/* Content Dialog */}
      <Dialog open={openContentDialog} onClose={() => setOpenContentDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Yeni İçerik Oluştur</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Başlık"
              value={contentForm.baslik}
              onChange={(e) => setContentForm({ ...contentForm, baslik: e.target.value })}
              margin="normal"
              required
            />

            <FormControl fullWidth margin="normal" required>
              <InputLabel>İçerik Tipi</InputLabel>
              <Select
                value={contentForm.icerik_tipi}
                onChange={(e) => setContentForm({ ...contentForm, icerik_tipi: e.target.value })}
                label="İçerik Tipi"
              >
                <MenuItem value="video">Video</MenuItem>
                <MenuItem value="makale">Makale</MenuItem>
                <MenuItem value="dokuman">Doküman</MenuItem>
                <MenuItem value="interaktif">İnteraktif</MenuItem>
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Konu"
              value={contentForm.konu}
              onChange={(e) => setContentForm({ ...contentForm, konu: e.target.value })}
              margin="normal"
              required
            />

            <TextField
              fullWidth
              label="URL"
              value={contentForm.url}
              onChange={(e) => setContentForm({ ...contentForm, url: e.target.value })}
              margin="normal"
            />

            <TextField
              fullWidth
              label="Açıklama"
              multiline
              rows={3}
              value={contentForm.aciklama}
              onChange={(e) => setContentForm({ ...contentForm, aciklama: e.target.value })}
              margin="normal"
              required
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenContentDialog(false)}>İptal</Button>
          <Button onClick={handleCreateContent} variant="contained">Oluştur</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ContentManagement;