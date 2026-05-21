/**
 * Batch Queue Monitor Component
 * Real-time monitoring for batch question generation and PDF processing
 */

import {
  Refresh as RefreshIcon,
  Cancel as CancelIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as HourglassIcon,
  PlayArrow as PlayArrowIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  Button,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

// ==================== TYPES ====================

/**
 * Batch soru üretim görevi
 */
interface BatchJob {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  batch_size: number;
  completed_count: number;
  failed_count: number;
  exam_type: string;
  subject: string;
  /** Görev oluşturulma zamanı (ISO 8601: "2024-06-15T10:00:00Z") */
  created_at: string;
  /** İşleme başlama zamanı (ISO 8601: "2024-06-15T10:05:00Z") */
  started_at?: string;
  /** Tamamlanma zamanı (ISO 8601: "2024-06-15T10:30:00Z") */
  completed_at?: string;
  estimated_time_remaining?: number;
  error_message?: string;
}

/**
 * PDF işleme görevi (OSYM PDF parse)
 */
interface PDFJob {
  job_id: string;
  filename: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_page?: number;
  total_pages?: number;
  /** Görev oluşturulma zamanı (ISO 8601: "2024-06-15T08:00:00Z") */
  created_at: string;
  /** İşleme başlama zamanı (ISO 8601: "2024-06-15T08:02:00Z") */
  started_at?: string;
  /** Tamamlanma zamanı (ISO 8601: "2024-06-15T08:45:00Z") */
  completed_at?: string;
  error?: string;
}

interface QueueStats {
  total_tasks: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  worker_count: number;
  avg_processing_time: number;
}

// ==================== COMPONENT ====================

export const BatchQueueMonitor: React.FC = () => {
  const [batchJobs, setBatchJobs] = useState<BatchJob[]>([]);
  const [pdfJobs, setPDFJobs] = useState<PDFJob[]>([]);
  const [queueStats, setQueueStats] = useState<QueueStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<BatchJob | PDFJob | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // ==================== API CALLS ====================

  const fetchBatchJobs = async () => {
    try {
      const response = await fetch('/api/v1/batch/queue/active', { credentials: 'include' });
      if (!response.ok) {throw new Error('Failed to fetch batch jobs');}
      const data = await response.json();
      setBatchJobs(data);
    } catch (err) {
      console.error('Error fetching batch jobs:', err);
    }
  };

  const fetchPDFJobs = async () => {
    try {
      const response = await fetch('/api/v1/pdf/jobs?limit=20', { credentials: 'include' });
      if (!response.ok) {throw new Error('Failed to fetch PDF jobs');}
      const data = await response.json();
      setPDFJobs(data);
    } catch (err) {
      console.error('Error fetching PDF jobs:', err);
    }
  };

  const fetchQueueStats = async () => {
    try {
      const response = await fetch('/api/v1/batch/queue/stats', { credentials: 'include' });
      if (!response.ok) {throw new Error('Failed to fetch queue stats');}
      const data = await response.json();
      setQueueStats(data);
    } catch (err) {
      console.error('Error fetching queue stats:', err);
    }
  };

  const refreshAll = async () => {
    setLoading(true);
    setError(null);

    try {
      await Promise.all([
        fetchBatchJobs(),
        fetchPDFJobs(),
        fetchQueueStats(),
      ]);
    } catch {
      setError('Failed to refresh data');
    } finally {
      setLoading(false);
    }
  };

  const cancelJob = async (taskId: string, type: 'batch' | 'pdf') => {
    try {
      const endpoint = type === 'batch'
        ? `/api/v1/batch/cancel/${taskId}`
        : `/api/v1/pdf/cancel/${taskId}`;

      const response = await fetch(endpoint, { method: 'DELETE' });
      if (!response.ok) {throw new Error('Failed to cancel job');}

      await refreshAll();
    } catch (err) {
      setError(`Failed to cancel job: ${err}`);
    }
  };

  // ==================== EFFECTS ====================

  useEffect(() => {
    refreshAll();
  }, []);

  useEffect(() => {
    if (!autoRefresh) {return;}

    const interval = setInterval(refreshAll, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [autoRefresh]);

  // ==================== HELPERS ====================

  const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'primary';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon />;
      case 'processing': return <PlayArrowIcon />;
      case 'failed': return <ErrorIcon />;
      case 'pending':
      case 'queued': return <HourglassIcon />;
      default: return <InfoIcon />;
    }
  };

  const formatTime = (seconds?: number): string => {
    if (!seconds) {return 'N/A';}
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatDate = (dateString?: string): string => {
    if (!dateString) {return 'N/A';}
    return new Date(dateString).toLocaleString('tr-TR');
  };

  // ==================== RENDER ====================

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Batch Queue Monitor</Typography>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant={autoRefresh ? 'contained' : 'outlined'}
            onClick={() => setAutoRefresh(!autoRefresh)}
            size="small"
          >
            {autoRefresh ? 'Auto Refresh: ON' : 'Auto Refresh: OFF'}
          </Button>

          <IconButton onClick={refreshAll} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Queue Statistics */}
      {queueStats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={2}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Total Tasks
                </Typography>
                <Typography variant="h4">{queueStats.total_tasks}</Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={2}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Processing
                </Typography>
                <Typography variant="h4" color="primary">{queueStats.processing}</Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={2}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Completed
                </Typography>
                <Typography variant="h4" color="success.main">{queueStats.completed}</Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={2}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Failed
                </Typography>
                <Typography variant="h4" color="error.main">{queueStats.failed}</Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={2}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Workers
                </Typography>
                <Typography variant="h4">{queueStats.worker_count}</Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={2}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Avg Time
                </Typography>
                <Typography variant="h4">{formatTime(queueStats.avg_processing_time)}</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Batch Generation Jobs */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Batch Question Generation
          </Typography>

          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Task ID</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Subject</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {batchJobs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      No batch jobs found
                    </TableCell>
                  </TableRow>
                ) : (
                  batchJobs.map((job) => (
                    <TableRow key={job.task_id} hover>
                      <TableCell>
                        <Tooltip title={job.task_id}>
                          <Typography variant="body2" sx={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {job.task_id.substring(0, 8)}...
                          </Typography>
                        </Tooltip>
                      </TableCell>

                      <TableCell>
                        <Chip
                          icon={getStatusIcon(job.status)}
                          label={job.status}
                          color={getStatusColor(job.status)}
                          size="small"
                        />
                      </TableCell>

                      <TableCell sx={{ minWidth: 150 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={job.progress * 100}
                            sx={{ flexGrow: 1, height: 8, borderRadius: 1 }}
                          />
                          <Typography variant="caption">
                            {Math.round(job.progress * 100)}%
                          </Typography>
                        </Box>
                        <Typography variant="caption" color="textSecondary">
                          {job.completed_count}/{job.batch_size}
                        </Typography>
                      </TableCell>

                      <TableCell>{job.exam_type}</TableCell>
                      <TableCell>{job.subject}</TableCell>
                      <TableCell>{job.batch_size}</TableCell>
                      <TableCell>{formatDate(job.created_at)}</TableCell>

                      <TableCell>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedJob(job);
                              setDetailsOpen(true);
                            }}
                          >
                            <InfoIcon />
                          </IconButton>
                        </Tooltip>

                        {(job.status === 'pending' || job.status === 'processing') && (
                          <Tooltip title="Cancel">
                            <IconButton
                              size="small"
                              onClick={() => cancelJob(job.task_id, 'batch')}
                            >
                              <CancelIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* PDF Processing Jobs */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            PDF Processing
          </Typography>

          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Job ID</TableCell>
                  <TableCell>Filename</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Pages</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {pdfJobs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      No PDF jobs found
                    </TableCell>
                  </TableRow>
                ) : (
                  pdfJobs.map((job) => (
                    <TableRow key={job.job_id} hover>
                      <TableCell>
                        <Tooltip title={job.job_id}>
                          <Typography variant="body2" sx={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {job.job_id.substring(0, 8)}...
                          </Typography>
                        </Tooltip>
                      </TableCell>

                      <TableCell>
                        <Tooltip title={job.filename}>
                          <Typography variant="body2" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {job.filename}
                          </Typography>
                        </Tooltip>
                      </TableCell>

                      <TableCell>
                        <Chip
                          icon={getStatusIcon(job.status)}
                          label={job.status}
                          color={getStatusColor(job.status)}
                          size="small"
                        />
                      </TableCell>

                      <TableCell sx={{ minWidth: 150 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={job.progress * 100}
                            sx={{ flexGrow: 1, height: 8, borderRadius: 1 }}
                          />
                          <Typography variant="caption">
                            {Math.round(job.progress * 100)}%
                          </Typography>
                        </Box>
                      </TableCell>

                      <TableCell>
                        {job.current_page && job.total_pages
                          ? `${job.current_page}/${job.total_pages}`
                          : 'N/A'}
                      </TableCell>

                      <TableCell>{formatDate(job.created_at)}</TableCell>

                      <TableCell>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedJob(job);
                              setDetailsOpen(true);
                            }}
                          >
                            <InfoIcon />
                          </IconButton>
                        </Tooltip>

                        {(job.status === 'queued' || job.status === 'processing') && (
                          <Tooltip title="Cancel">
                            <IconButton
                              size="small"
                              onClick={() => cancelJob(job.job_id, 'pdf')}
                            >
                              <CancelIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Job Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Job Details</DialogTitle>
        <DialogContent>
          {selectedJob && (
            <Box sx={{ pt: 2 }}>
              <pre style={{ overflow: 'auto', backgroundColor: '#f5f5f5', padding: '16px', borderRadius: '4px' }}>
                {JSON.stringify(selectedJob, null, 2)}
              </pre>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BatchQueueMonitor;
