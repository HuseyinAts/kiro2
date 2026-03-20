/**
 * Batch Operations Dashboard
 * Admin page for bulk question generation and management
 */
import {
  PlayArrow,
  Refresh,
  CheckCircle,
  Error as ErrorIcon,
  Pending,
  AutoAwesome,
  Science,
  Speed,
  Cancel,
} from '@mui/icons-material';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  TextField,
  MenuItem,
  Stepper,
  Step,
  StepLabel,
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import { useState, useEffect } from 'react';

interface BatchRequest {
  batch_size: number;
  exam_type: string;
  subject: string;
  topics?: string[];
  difficulty_min: number;
  difficulty_max: number;
  bloom_levels?: number[];
  generation_method: string;
  priority: string;
}

interface BatchJob {
  task_id: string;
  state: string;
  current: number;
  total: number;
  percent: number;
  status: string;
  result?: any;
}

interface QueueStats {
  active: number;
  scheduled: number;
  reserved: number;
  total: number;
}

export function BatchOperationsPage() {
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [_jobs, _setJobs] = useState<BatchJob[]>([]);
  const [queueStats, setQueueStats] = useState<QueueStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [batchSize, setBatchSize] = useState(100);
  const [examType, setExamType] = useState('TYT');
  const [subject, setSubject] = useState('matematik');
  const [topics, _setTopics] = useState<string[]>([]);
  const [difficultyMin, setDifficultyMin] = useState(0.3);
  const [difficultyMax, setDifficultyMax] = useState(0.7);
  const [bloomLevels, setBloomLevels] = useState<number[]>([1, 2, 3, 4]);
  const [generationMethod, setGenerationMethod] = useState('ensemble');
  const [priority, setPriority] = useState('normal');

  // Active job tracking
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState<BatchJob | null>(null);

  const steps = ['Parametreleri Ayarla', 'Batch Başlat', 'İlerlemeyi İzle', 'Sonuçları Görüntüle'];

  useEffect(() => {
    loadQueueStats();
    const interval = setInterval(loadQueueStats, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (currentTaskId) {
      const interval = setInterval(() => {
        checkJobStatus(currentTaskId);
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [currentTaskId]);

  const loadQueueStats = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      const response = await fetch(`${API_URL}/api/batch/queue/stats`, {
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setQueueStats(data.data || data);
      }
    } catch (err) {
      console.error('Queue stats error:', err);
    }
  };

  const startBatchGeneration = async () => {
    try {
      setLoading(true);
      setError(null);

      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      const requestBody: BatchRequest = {
        batch_size: batchSize,
        exam_type: examType,
        subject: subject,
        topics: topics.length > 0 ? topics : undefined,
        difficulty_min: difficultyMin,
        difficulty_max: difficultyMax,
        bloom_levels: bloomLevels.length > 0 ? bloomLevels : undefined,
        generation_method: generationMethod,
        priority: priority,
      };

      const response = await fetch(`${API_URL}/api/batch/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentTaskId(data.task_id);
        setActiveStep(2); // Move to monitoring step
        alert(`✅ Batch işlem başlatıldı\nTask ID: ${data.task_id}\nTahmini süre: ${Math.round(data.estimated_time_seconds / 60)} dakika`);
      } else {
        throw new Error('Batch generation failed');
      }
    } catch (err: any) {
      console.error('Batch generation error:', err);
      setError(err.message || 'Batch işlem başlatılamadı');
    } finally {
      setLoading(false);
    }
  };

  const checkJobStatus = async (taskId: string) => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      const response = await fetch(`${API_URL}/api/batch/status/${taskId}`, {
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setJobProgress(data);

        if (data.state === 'SUCCESS') {
          setActiveStep(3); // Move to results step
        }
      }
    } catch (err) {
      console.error('Job status check error:', err);
    }
  };

  const cancelJob = async (taskId: string) => {
    if (!confirm('Bu işi iptal etmek istediğinizden emin misiniz?')) {return;}

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      const response = await fetch(`${API_URL}/api/batch/cancel/${taskId}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (response.ok) {
        alert('✅ İş iptal edildi');
        setCurrentTaskId(null);
        setJobProgress(null);
      }
    } catch (err) {
      console.error('Cancel job error:', err);
      alert('❌ İş iptal edilemedi');
    }
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'SUCCESS': return 'success';
      case 'FAILURE': return 'error';
      case 'PENDING': return 'warning';
      case 'STARTED': return 'info';
      default: return 'default';
    }
  };

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'SUCCESS': return <CheckCircle />;
      case 'FAILURE': return <ErrorIcon />;
      case 'PENDING': return <Pending />;
      case 'STARTED': return <AutoAwesome />;
      default: return <Pending />;
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Science sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
          <Box>
            <Typography variant="h4" fontWeight="bold">
              Batch Operations
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Toplu soru üretimi ve yönetimi
            </Typography>
          </Box>
        </Box>

        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={loadQueueStats}
        >
          Kuyruk Durumu
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Queue Statistics */}
      {queueStats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Speed sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                <Typography variant="h4" color="success.main">
                  {queueStats.active || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Aktif İşlemler
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Pending sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                <Typography variant="h4" color="warning.main">
                  {queueStats.scheduled || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Bekleyen İşlemler
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center' }}>
                <AutoAwesome sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
                <Typography variant="h4" color="info.main">
                  {queueStats.reserved || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Ayrılmış İşlemler
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center' }}>
                <CheckCircle sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant="h4" color="primary">
                  {queueStats.total || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Toplam İşlem
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Stepper */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Stepper activeStep={activeStep}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* Step Content */}
      <Paper elevation={2} sx={{ p: 3 }}>
        {/* Step 1: Parameters */}
        {activeStep === 0 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Batch Parametreleri
            </Typography>

            <Grid container spacing={3} sx={{ mt: 2 }}>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Batch Boyutu"
                  type="number"
                  fullWidth
                  value={batchSize}
                  onChange={(e) => setBatchSize(Number(e.target.value))}
                  InputProps={{ inputProps: { min: 50, max: 500 } }}
                  helperText="50-500 arası soru sayısı"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  label="Sınav Tipi"
                  select
                  fullWidth
                  value={examType}
                  onChange={(e) => setExamType(e.target.value)}
                >
                  <MenuItem value="TYT">TYT</MenuItem>
                  <MenuItem value="AYT">AYT</MenuItem>
                  <MenuItem value="YDT">YDT</MenuItem>
                </TextField>
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  label="Ders"
                  select
                  fullWidth
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                >
                  <MenuItem value="matematik">Matematik</MenuItem>
                  <MenuItem value="fizik">Fizik</MenuItem>
                  <MenuItem value="kimya">Kimya</MenuItem>
                  <MenuItem value="biyoloji">Biyoloji</MenuItem>
                  <MenuItem value="turkce">Türkçe</MenuItem>
                </TextField>
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  label="Üretim Metodu"
                  select
                  fullWidth
                  value={generationMethod}
                  onChange={(e) => setGenerationMethod(e.target.value)}
                >
                  <MenuItem value="ensemble">Ensemble (Önerilen)</MenuItem>
                  <MenuItem value="openai">OpenAI GPT-4</MenuItem>
                  <MenuItem value="claude">Claude 3.5</MenuItem>
                  <MenuItem value="qwen">Qwen2.5</MenuItem>
                </TextField>
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  label="Minimum Zorluk"
                  type="number"
                  fullWidth
                  value={difficultyMin}
                  onChange={(e) => setDifficultyMin(Number(e.target.value))}
                  InputProps={{ inputProps: { min: 0, max: 1, step: 0.1 } }}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  label="Maximum Zorluk"
                  type="number"
                  fullWidth
                  value={difficultyMax}
                  onChange={(e) => setDifficultyMax(Number(e.target.value))}
                  InputProps={{ inputProps: { min: 0, max: 1, step: 0.1 } }}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  label="Öncelik"
                  select
                  fullWidth
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                >
                  <MenuItem value="urgent">Acil</MenuItem>
                  <MenuItem value="normal">Normal</MenuItem>
                  <MenuItem value="low">Düşük</MenuItem>
                </TextField>
              </Grid>

              <Grid item xs={12}>
                <Box>
                  <Typography variant="body2" gutterBottom>
                    Bloom Seviyeleri:
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    {[1, 2, 3, 4, 5, 6].map((level) => (
                      <FormControlLabel
                        key={level}
                        control={
                          <Checkbox
                            checked={bloomLevels.includes(level)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setBloomLevels([...bloomLevels, level]);
                              } else {
                                setBloomLevels(bloomLevels.filter(l => l !== level));
                              }
                            }}
                          />
                        }
                        label={`Level ${level}`}
                      />
                    ))}
                  </Box>
                </Box>
              </Grid>
            </Grid>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                size="large"
                onClick={() => setActiveStep(1)}
              >
                Devam Et
              </Button>
            </Box>
          </Box>
        )}

        {/* Step 2: Confirm and Start */}
        {activeStep === 1 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Batch İşlemi Başlat
            </Typography>

            <Alert severity="info" sx={{ mt: 2, mb: 3 }}>
              {batchSize} adet {subject} sorusu üretilecek.
              Tahmini süre: {Math.round(batchSize / 10)} dakika
            </Alert>

            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableBody>
                  <TableRow>
                    <TableCell><strong>Batch Boyutu</strong></TableCell>
                    <TableCell>{batchSize} soru</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Sınav Tipi</strong></TableCell>
                    <TableCell>{examType}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Ders</strong></TableCell>
                    <TableCell>{subject}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Zorluk Aralığı</strong></TableCell>
                    <TableCell>{difficultyMin} - {difficultyMax}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Üretim Metodu</strong></TableCell>
                    <TableCell>{generationMethod}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Öncelik</strong></TableCell>
                    <TableCell>
                      <Chip
                        label={priority}
                        color={priority === 'urgent' ? 'error' : priority === 'normal' ? 'primary' : 'default'}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
              <Button onClick={() => setActiveStep(0)}>
                Geri
              </Button>
              <Button
                variant="contained"
                size="large"
                startIcon={loading ? <CircularProgress size={20} /> : <PlayArrow />}
                onClick={startBatchGeneration}
                disabled={loading}
                color="success"
              >
                Batch İşlemi Başlat
              </Button>
            </Box>
          </Box>
        )}

        {/* Step 3: Progress Monitoring */}
        {activeStep === 2 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              İşlem İlerlemesi
            </Typography>

            {jobProgress && (
              <Box sx={{ mt: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    {getStateIcon(jobProgress.state)}
                    <Typography variant="body1" sx={{ ml: 1 }}>
                      Durum: {jobProgress.state}
                    </Typography>
                  </Box>
                  <Chip
                    label={`${jobProgress.current} / ${jobProgress.total}`}
                    color={getStateColor(jobProgress.state) as any}
                  />
                </Box>

                <LinearProgress
                  variant="determinate"
                  value={jobProgress.percent}
                  sx={{ height: 10, borderRadius: 5 }}
                />

                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {jobProgress.status}
                </Typography>

                <Typography variant="body2" sx={{ mt: 2 }}>
                  İlerleme: {jobProgress.percent.toFixed(1)}%
                </Typography>

                {jobProgress.state === 'STARTED' && (
                  <Box sx={{ mt: 3 }}>
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={<Cancel />}
                      onClick={() => currentTaskId && cancelJob(currentTaskId)}
                    >
                      İşlemi İptal Et
                    </Button>
                  </Box>
                )}
              </Box>
            )}
          </Box>
        )}

        {/* Step 4: Results */}
        {activeStep === 3 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Batch Sonuçları
            </Typography>

            {jobProgress?.result && (
              <Box sx={{ mt: 3 }}>
                <Alert severity="success" icon={<CheckCircle />} sx={{ mb: 3 }}>
                  Batch işlemi başarıyla tamamlandı!
                </Alert>

                <Grid container spacing={2}>
                  <Grid item xs={12} md={3}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">Toplam</Typography>
                      <Typography variant="h5">{jobProgress.result.total || 0}</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">Başarılı</Typography>
                      <Typography variant="h5" color="success.main">
                        {jobProgress.result.successful || 0}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">Başarısız</Typography>
                      <Typography variant="h5" color="error.main">
                        {jobProgress.result.failed || 0}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">Başarı Oranı</Typography>
                      <Typography variant="h5">
                        {((jobProgress.result.success_rate || 0) * 100).toFixed(1)}%
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>

                <Box sx={{ mt: 3 }}>
                  <Button
                    variant="contained"
                    onClick={() => {
                      setActiveStep(0);
                      setCurrentTaskId(null);
                      setJobProgress(null);
                    }}
                  >
                    Yeni Batch Başlat
                  </Button>
                </Box>
              </Box>
            )}
          </Box>
        )}
      </Paper>
    </Container>
  );
}

export default BatchOperationsPage;
