/**
 * Audit Log Viewer
 * Admin page for viewing and filtering audit logs
 */
import {
  Refresh,
  Search,
  FilterList,
  ExpandMore,
  ExpandLess,
  Download,
  Delete,
  Security,
  Person,
  Category,
  Assessment,
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Collapse,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { apiClient } from '../../services/apiClient';

interface AuditLog {
  id: string;
  user_id?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  old_values?: any;
  new_values?: any;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

interface AuditStats {
  total_logs: number;
  total_users: number;
  total_actions: number;
  recent_security_events: number;
}

export function AuditLogViewerPage() {
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [totalCount, setTotalCount] = useState(0);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  // Filters
  const [filterUserId, setFilterUserId] = useState('');
  const [filterAction, setFilterAction] = useState('');
  const [filterResourceType, setFilterResourceType] = useState('');
  const [filterStartDate, setFilterStartDate] = useState('');
  const [filterEndDate, setFilterEndDate] = useState('');
  const [showCleanupDialog, setShowCleanupDialog] = useState(false);

  useEffect(() => {
    loadAuditLogs();
    loadAuditStats();
  }, [page, rowsPerPage]);

  const loadAuditLogs = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        limit: rowsPerPage.toString(),
        offset: (page * rowsPerPage).toString(),
      });

      if (filterUserId) {params.append('user_id', filterUserId);}
      if (filterAction) {params.append('action', filterAction);}
      if (filterResourceType) {params.append('resource_type', filterResourceType);}
      if (filterStartDate) {params.append('start_date', filterStartDate);}
      if (filterEndDate) {params.append('end_date', filterEndDate);}

      const response = await apiClient.get(`/api/v1/audit/logs?${params.toString()}`);
      const data = response.data;
      setLogs(data || []);
      // Assuming backend returns total count in headers or response
      setTotalCount(data.length > 0 ? 1000 : 0); // Placeholder

    } catch (err: any) {
      console.error('Audit logs loading error:', err);
      setError(err.message || 'Audit logları yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const loadAuditStats = async () => {
    try {
      const response = await apiClient.get('/api/v1/audit/stats');
      const data = response.data;
      setStats(data.data || data);
    } catch (err) {
      console.error('Stats loading error:', err);
    }
  };

  const handleSearch = () => {
    setPage(0);
    loadAuditLogs();
  };

  const handleClearFilters = () => {
    setFilterUserId('');
    setFilterAction('');
    setFilterResourceType('');
    setFilterStartDate('');
    setFilterEndDate('');
    setPage(0);
    loadAuditLogs();
  };

  const handleExportLogs = async () => {
    try {
      const response = await apiClient.get('/api/v1/audit/export', {
        responseType: 'blob',
      });

      const blob = response.data;
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-logs-${new Date().toISOString()}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Export error:', err);
      alert('❌ Export başarısız oldu');
    }
  };

  const handleCleanupOldLogs = async () => {
    if (!confirm('30 günden eski logları silmek istediğinizden emin misiniz?')) {return;}

    try {
      await apiClient.post('/api/v1/audit/cleanup', { days: 30 });
      alert('✅ Eski loglar başarıyla temizlendi');
      setShowCleanupDialog(false);
      loadAuditLogs();
      loadAuditStats();
    } catch (err) {
      console.error('Cleanup error:', err);
      alert('❌ Temizleme başarısız oldu');
    }
  };

  const getActionColor = (action: string) => {
    if (action.includes('create')) {return 'success';}
    if (action.includes('update')) {return 'info';}
    if (action.includes('delete')) {return 'error';}
    if (action.includes('login')) {return 'primary';}
    return 'default';
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Security sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
          <Box>
            <Typography variant="h4" fontWeight="bold">
              Audit Log Viewer
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Sistem aktivitelerini ve güvenlik olaylarını izleyin
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={handleExportLogs}
          >
            Export CSV
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<Delete />}
            onClick={() => setShowCleanupDialog(true)}
          >
            Temizle
          </Button>
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={20} /> : <Refresh />}
            onClick={loadAuditLogs}
            disabled={loading}
          >
            Yenile
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Assessment sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant="h4" color="primary">
                  {stats.total_logs || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Toplam Log Kaydı
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Person sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                <Typography variant="h4" color="success.main">
                  {stats.total_users || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Aktif Kullanıcı
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Category sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
                <Typography variant="h4" color="info.main">
                  {stats.total_actions || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Farklı Aksiyon
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Security sx={{ fontSize: 40, color: 'error.main', mb: 1 }} />
                <Typography variant="h4" color="error.main">
                  {stats.recent_security_events || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Güvenlik Olayı (24s)
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Filters */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <FilterList sx={{ mr: 1 }} />
          <Typography variant="h6">Filtreler</Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <TextField
              label="User ID"
              fullWidth
              size="small"
              value={filterUserId}
              onChange={(e) => setFilterUserId(e.target.value)}
            />
          </Grid>

          <Grid item xs={12} md={3}>
            <TextField
              label="Action"
              fullWidth
              size="small"
              select
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
            >
              <MenuItem value="">Tümü</MenuItem>
              <MenuItem value="create">Create</MenuItem>
              <MenuItem value="update">Update</MenuItem>
              <MenuItem value="delete">Delete</MenuItem>
              <MenuItem value="login">Login</MenuItem>
              <MenuItem value="logout">Logout</MenuItem>
            </TextField>
          </Grid>

          <Grid item xs={12} md={3}>
            <TextField
              label="Resource Type"
              fullWidth
              size="small"
              select
              value={filterResourceType}
              onChange={(e) => setFilterResourceType(e.target.value)}
            >
              <MenuItem value="">Tümü</MenuItem>
              <MenuItem value="user">User</MenuItem>
              <MenuItem value="exam">Exam</MenuItem>
              <MenuItem value="question">Question</MenuItem>
              <MenuItem value="learning_path">Learning Path</MenuItem>
            </TextField>
          </Grid>

          <Grid item xs={12} md={3}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                startIcon={<Search />}
                onClick={handleSearch}
                fullWidth
              >
                Ara
              </Button>
              <Button
                variant="outlined"
                onClick={handleClearFilters}
                fullWidth
              >
                Temizle
              </Button>
            </Box>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Başlangıç Tarihi"
              type="datetime-local"
              fullWidth
              size="small"
              value={filterStartDate}
              onChange={(e) => setFilterStartDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Bitiş Tarihi"
              type="datetime-local"
              fullWidth
              size="small"
              value={filterEndDate}
              onChange={(e) => setFilterEndDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Audit Logs Table */}
      <Paper elevation={2}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell />
                <TableCell>Tarih/Saat</TableCell>
                <TableCell>User ID</TableCell>
                <TableCell>Action</TableCell>
                <TableCell>Resource Type</TableCell>
                <TableCell>Resource ID</TableCell>
                <TableCell>IP Address</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : logs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography variant="body2" color="text.secondary">
                      Kayıt bulunamadı
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                logs.map((log) => (
                  <React.Fragment key={log.id}>
                    <TableRow hover>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => setExpandedRow(expandedRow === log.id ? null : log.id)}
                        >
                          {expandedRow === log.id ? <ExpandLess /> : <ExpandMore />}
                        </IconButton>
                      </TableCell>
                      <TableCell>
                        {new Date(log.created_at).toLocaleString('tr-TR')}
                      </TableCell>
                      <TableCell>
                        <Chip label={log.user_id || 'System'} size="small" />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={log.action}
                          color={getActionColor(log.action) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{log.resource_type}</TableCell>
                      <TableCell>{log.resource_id || '-'}</TableCell>
                      <TableCell>{log.ip_address || '-'}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={7}>
                        <Collapse in={expandedRow === log.id} timeout="auto" unmountOnExit>
                          <Box sx={{ p: 2, backgroundColor: 'grey.50' }}>
                            <Typography variant="body2" fontWeight="bold" gutterBottom>
                              Detaylar:
                            </Typography>
                            <Grid container spacing={2}>
                              {log.old_values && (
                                <Grid item xs={12} md={6}>
                                  <Typography variant="caption" color="text.secondary">
                                    Eski Değerler:
                                  </Typography>
                                  <pre style={{ fontSize: '0.75rem', overflow: 'auto' }}>
                                    {JSON.stringify(log.old_values, null, 2)}
                                  </pre>
                                </Grid>
                              )}
                              {log.new_values && (
                                <Grid item xs={12} md={6}>
                                  <Typography variant="caption" color="text.secondary">
                                    Yeni Değerler:
                                  </Typography>
                                  <pre style={{ fontSize: '0.75rem', overflow: 'auto' }}>
                                    {JSON.stringify(log.new_values, null, 2)}
                                  </pre>
                                </Grid>
                              )}
                              {log.user_agent && (
                                <Grid item xs={12}>
                                  <Typography variant="caption" color="text.secondary">
                                    User Agent: {log.user_agent}
                                  </Typography>
                                </Grid>
                              )}
                            </Grid>
                          </Box>
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  </React.Fragment>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          rowsPerPageOptions={[10, 25, 50, 100]}
          component="div"
          count={totalCount}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
        />
      </Paper>

      {/* Cleanup Dialog */}
      <Dialog open={showCleanupDialog} onClose={() => setShowCleanupDialog(false)}>
        <DialogTitle>Eski Logları Temizle</DialogTitle>
        <DialogContent>
          <Typography>
            30 günden eski audit loglarını silmek istediğinizden emin misiniz?
            Bu işlem geri alınamaz.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCleanupDialog(false)}>İptal</Button>
          <Button onClick={handleCleanupOldLogs} color="error" variant="contained">
            Temizle
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default AuditLogViewerPage;
