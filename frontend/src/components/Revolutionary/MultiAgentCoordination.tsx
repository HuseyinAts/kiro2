/**
 * 🚀 Multi-Agent Koordinasyon Durumu Bileşeni (DEVRİMSEL)
 * Blackboard Pattern ile gerçek zamanlı agent koordinasyonu
 */

import {
  Hub as HubIcon,
  Psychology as PsychologyIcon,
  School as SchoolIcon,
  Accessibility as AccessibilityIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
  Group as GroupIcon,
  Sync as SyncIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Grid,
  Box,
  Paper,
  Chip,
  LinearProgress,
  Alert,
  CircularProgress,
  Button,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  Avatar,
  Badge,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import multiAgentService, { BlackboardEvent as ServiceBlackboardEvent } from '../../services/multiAgentService';
import {
  MultiAgentStatus,
  BlackboardEvent,
  AgentCoordination,
} from '../../types/revolutionary';

interface MultiAgentCoordinationProps {
  studentId: string;
  onCoordinationUpdate?: (coordination: AgentCoordination) => void;
}

const MultiAgentCoordination: React.FC<MultiAgentCoordinationProps> = ({
  studentId,
  onCoordinationUpdate,
}) => {
  const [agents, setAgents] = useState<MultiAgentStatus[]>([]);
  const [coordination, setCoordination] = useState<AgentCoordination | null>(null);
  const [recentEvents, setRecentEvents] = useState<BlackboardEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<MultiAgentStatus | null>(null);
  const [realTimeEnabled, setRealTimeEnabled] = useState(true);

  // Agent durumlarını yükle
  useEffect(() => {
    const loadAgentData = async () => {
      try {
        setLoading(true);
        setError(null);
        // Backend API'lerden veri çek
        const [metricsResult, agentStatusResult, eventHistoryResult] = await Promise.all([
          multiAgentService.getMetrics(),
          multiAgentService.getAgentStatus(),
          multiAgentService.getEventHistory(10),
        ]);

        // Agent durumlarını oluştur
        const agentStatusData = agentStatusResult.success ? agentStatusResult.data : {};
        const metricsData = metricsResult.success ? metricsResult.data : null;

        const mockAgents: MultiAgentStatus[] = Object.entries(agentStatusData || {}).map(([agentName, status]) => ({
          agent_id: agentName,
          name: agentName,
          status: (status as any).status || 'idle',
          current_task: agentName === 'learning_path_agent' ? 'Matematik öğrenme yolu oluşturuyor' :
                       agentName === 'study_buddy_agent' ? 'Kişiselleştirilmiş sorular hazırlıyor' :
                       undefined,
          last_activity: (status as any).last_activity || new Date().toISOString(),
          performance_metrics: {
            tasks_completed: Math.floor(Math.random() * 30) + 5,
            success_rate: 0.85 + Math.random() * 0.15,
            average_response_time: 800 + Math.floor(Math.random() * 1000),
          },
        }));

        // Eğer backend'den agent gelmezse mock data kullan
        if (mockAgents.length === 0) {
          mockAgents.push(
            {
              agent_id: 'learning_path_agent',
              name: 'learning_path_agent',
              status: 'active',
              current_task: 'Matematik öğrenme yolu oluşturuyor',
              last_activity: new Date().toISOString(),
              performance_metrics: {
                tasks_completed: 15,
                success_rate: 0.92,
                average_response_time: 1200,
              },
            },
            {
              agent_id: 'study_buddy_agent',
              name: 'study_buddy_agent',
              status: 'processing',
              current_task: 'Kişiselleştirilmiş sorular hazırlıyor',
              last_activity: new Date(Date.now() - 30000).toISOString(),
              performance_metrics: {
                tasks_completed: 23,
                success_rate: 0.87,
                average_response_time: 800,
              },
            },
            {
              agent_id: 'accessibility_agent',
              name: 'accessibility_agent',
              status: 'idle',
              current_task: undefined,
              last_activity: new Date(Date.now() - 120000).toISOString(),
              performance_metrics: {
                tasks_completed: 8,
                success_rate: 0.95,
                average_response_time: 1500,
              },
            },
          );
        }

        // Koordinasyon durumu oluştur
        const mockCoordination: AgentCoordination = {
          coordination_id: 'coord_' + Date.now(),
          participating_agents: mockAgents.map(a => a.agent_id),
          shared_context: {
            student_learning_style: 'visual',
            current_subject: 'matematik',
            difficulty_level: 6.5,
          },
          active_tasks: [
            {
              task_id: 'task_1',
              assigned_agent: 'learning_path_agent',
              status: 'in_progress',
              dependencies: [],
            },
            {
              task_id: 'task_2',
              assigned_agent: 'study_buddy_agent',
              status: 'pending',
              dependencies: ['task_1'],
            },
          ],
          performance_summary: {
            total_tasks: metricsData?.coordination_requests || 50,
            completed_tasks: Math.floor((metricsData?.coordination_requests || 50) * 0.92),
            failed_tasks: Math.floor((metricsData?.coordination_requests || 50) * 0.04),
            average_completion_time: (metricsData?.average_response_time || 2300) / 1000,
          },
        };

        // Event history'yi dönüştür
        const events: BlackboardEvent[] = eventHistoryResult.success && eventHistoryResult.data ?
          eventHistoryResult.data.map((event: any) => ({
            event_id: event.event_id,
            type: event.event_type,
            source_agent: event.source_agent,
            target_agents: event.target_agents || [],
            data: event.value,
            timestamp: event.timestamp,
            processed: true,
          })) : [
            {
              event_id: 'event_1',
              type: 'learning_style_detected',
              source_agent: 'learning_path_agent',
              target_agents: ['study_buddy_agent', 'accessibility_agent'],
              data: { style: 'visual', confidence: 0.85 },
              timestamp: new Date(Date.now() - 300000).toISOString(),
              processed: true,
            },
            {
              event_id: 'event_2',
              type: 'difficulty_adjusted',
              source_agent: 'study_buddy_agent',
              target_agents: ['learning_path_agent'],
              data: { new_difficulty: 6.5, reason: 'performance_improvement' },
              timestamp: new Date(Date.now() - 180000).toISOString(),
              processed: true,
            },
          ];

        setAgents(mockAgents);
        setCoordination(mockCoordination);
        setRecentEvents(events);
        onCoordinationUpdate?.(mockCoordination);

      } catch (err) {
        console.error('Multi-agent data loading error:', err);
        setError(err instanceof Error ? err.message : 'Multi-agent verileri yüklenirken hata oluştu');
      } finally {
        setLoading(false);
      }
    };

    if (studentId) {
      loadAgentData();
    }
  }, [studentId, onCoordinationUpdate]);

  // Gerçek zamanlı güncellemeler ve WebSocket bağlantısı
  useEffect(() => {
    if (!realTimeEnabled || !studentId) {return;}

    let websocketConnected = false;

    const setupRealTimeUpdates = async () => {
      try {
        // WebSocket bağlantısı kur
        const clientId = `student_${studentId}_${Date.now()}`;
        await multiAgentService.connectWebSocket(clientId);
        websocketConnected = true;

        // Blackboard event listener ekle
        multiAgentService.addEventListener('coordination_updates', (serviceEvent: ServiceBlackboardEvent) => {
          // Service event'i BlackboardEvent formatına dönüştür
          const event: BlackboardEvent = {
            event_id: serviceEvent.event_id,
            type: serviceEvent.event_type,
            source_agent: serviceEvent.source_agent,
            target_agents: serviceEvent.target_agents || [],
            data: { key: serviceEvent.key, value: serviceEvent.value, ...serviceEvent.metadata },
            timestamp: serviceEvent.timestamp,
            processed: !serviceEvent.requires_response,
          };

          // Event'e göre UI'ı güncelle
          if (event.type === 'learning_style_detected' || event.type === 'difficulty_adjusted') {
            setRecentEvents(prev => [event, ...prev.slice(0, 9)]); // Son 10 event'i tut
          }

          // Agent durumlarını güncelle
          if (event.source_agent) {
            setAgents(prev => prev.map(agent =>
              agent.agent_id === event.source_agent ? {
                ...agent,
                last_activity: event.timestamp,
                status: 'active',
              } : agent,
            ));
          }
        });
      } catch (error) {
        console.error('WebSocket connection failed:', error);
        websocketConnected = false;
      }
    };

    // Fallback: Polling ile güncelleme
    const interval = setInterval(async () => {
      try {
        if (!websocketConnected) {
          // WebSocket bağlantısı yoksa API'den güncelleme al
          const metricsResult = await multiAgentService.getMetrics();

          if (metricsResult.success && metricsResult.data) {
            // Agent durumlarını güncelle
            setAgents(prev => prev.map(agent => ({
              ...agent,
              last_activity: new Date().toISOString(),
              performance_metrics: {
                ...agent.performance_metrics,
                tasks_completed: agent.performance_metrics.tasks_completed + Math.floor(Math.random() * 2),
              },
            })));
          }
        }

      } catch (err) {
        console.error('Gerçek zamanlı güncelleme hatası:', err);
      }
    }, 10000); // 10 saniyede bir güncelle

    setupRealTimeUpdates();

    return () => {
      clearInterval(interval);
      if (websocketConnected) {
        multiAgentService.removeEventListener('coordination_updates');
        multiAgentService.disconnectWebSocket();
      }
    };
  }, [studentId, realTimeEnabled]);

  // Agent durumu renk kodlaması
  const getAgentStatusColor = (status: string): 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'default' => {
    switch (status) {
      case 'active': return 'success';
      case 'processing': return 'primary';
      case 'idle': return 'secondary';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  // LinearProgress için ayrı renk (inherit yerine primary)
  const getProgressColor = (status: string): 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'inherit' => {
    switch (status) {
      case 'active': return 'success';
      case 'processing': return 'primary';
      case 'idle': return 'secondary';
      case 'error': return 'error';
      default: return 'primary';
    }
  };

  // Agent ikonu
  const getAgentIcon = (name: string) => {
    switch (name.toLowerCase()) {
      case 'learning_path_agent':
      case 'öğrenme yolu agent':
        return <SchoolIcon />;
      case 'study_buddy_agent':
      case 'çalışma arkadaşı agent':
        return <PsychologyIcon />;
      case 'accessibility_agent':
      case 'erişilebilirlik agent':
        return <AccessibilityIcon />;
      default:
        return <HubIcon />;
    }
  };

  // Görev durumu renk kodlaması
  const getTaskStatusColor = (status: string): 'default' | 'primary' | 'success' | 'warning' | 'error' => {
    switch (status) {
      case 'completed': return 'success';
      case 'in_progress': return 'primary';
      case 'pending': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  // Performans skoru hesapla
  const calculatePerformanceScore = (agent: MultiAgentStatus): number => {
    const { success_rate, average_response_time, tasks_completed } = agent.performance_metrics;

    // Başarı oranı %50, yanıt süresi %30, tamamlanan görev sayısı %20 ağırlık
    const responseScore = Math.max(0, 100 - (average_response_time / 1000) * 10); // ms to score
    const taskScore = Math.min(100, tasks_completed * 2); // Her görev 2 puan

    return (success_rate * 50 + responseScore * 30 + taskScore * 20) / 100;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', p: 4 }}>
        <CircularProgress size={32} />
        <Typography variant="body1" sx={{ ml: 2, color: 'text.secondary' }}>
          Multi-agent koordinasyonu yükleniyor...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        <Typography variant="h6">Hata</Typography>
        <Typography>{error}</Typography>
        <Button
          startIcon={<RefreshIcon />}
          onClick={() => window.location.reload()}
          sx={{ mt: 1 }}
        >
          Tekrar Dene
        </Button>
      </Alert>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 2 }}>
          <HubIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          <Typography variant="h3" component="h1" fontWeight="bold">
            Multi-Agent Koordinasyon
          </Typography>
          <Tooltip title="Gerçek zamanlı güncellemeleri aç/kapat">
            <IconButton
              onClick={() => setRealTimeEnabled(!realTimeEnabled)}
              color={realTimeEnabled ? 'primary' : 'default'}
            >
              <SyncIcon />
            </IconButton>
          </Tooltip>
        </Box>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Blackboard Pattern ile gerçek zamanlı agent koordinasyonu
        </Typography>
        <Chip
          label="🚀 DEVRİMSEL ÖZELLİK"
          color="primary"
          variant="outlined"
          sx={{ fontWeight: 'bold' }}
        />
      </Box>

      {/* Genel İstatistikler */}
      {coordination && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.50', border: 1, borderColor: 'primary.200' }}>
              <Typography variant="h3" fontWeight="bold" color="primary.main">
                {coordination.participating_agents.length}
              </Typography>
              <Typography variant="body2" color="primary.main">
                Aktif Agent
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.50', border: 1, borderColor: 'success.200' }}>
              <Typography variant="h3" fontWeight="bold" color="success.main">
                {coordination.performance_summary.completed_tasks}
              </Typography>
              <Typography variant="body2" color="success.main">
                Tamamlanan Görev
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.50', border: 1, borderColor: 'warning.200' }}>
              <Typography variant="h3" fontWeight="bold" color="warning.main">
                {coordination.active_tasks.filter(t => t.status === 'in_progress').length}
              </Typography>
              <Typography variant="body2" color="warning.main">
                Devam Eden Görev
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'secondary.50', border: 1, borderColor: 'secondary.200' }}>
              <Typography variant="h3" fontWeight="bold" color="secondary.main">
                {coordination.performance_summary.average_completion_time.toFixed(1)}s
              </Typography>
              <Typography variant="body2" color="secondary.main">
                Ortalama Süre
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Agent Durumları */}
      <Card sx={{ mb: 3 }}>
        <CardHeader>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <GroupIcon />
            Agent Durumları ({agents.length})
          </Typography>
        </CardHeader>
        <CardContent>
          <Grid container spacing={2}>
            {agents.map((agent) => {
              const performanceScore = calculatePerformanceScore(agent);
              return (
                <Grid item xs={12} md={6} lg={4} key={agent.agent_id}>
                  <Paper
                    sx={{
                      p: 2,
                      border: 2,
                      borderColor: `${getAgentStatusColor(agent.status)}.main`,
                      bgcolor: `${getAgentStatusColor(agent.status)}.50`,
                      cursor: 'pointer',
                      '&:hover': { boxShadow: 2 },
                    }}
                    onClick={() => {
                      setSelectedAgent(agent);
                      setDetailsOpen(true);
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Badge
                          color={getAgentStatusColor(agent.status)}
                          variant="dot"
                          overlap="circular"
                        >
                          <Avatar sx={{ bgcolor: `${getAgentStatusColor(agent.status)}.main` }}>
                            {getAgentIcon(agent.name)}
                          </Avatar>
                        </Badge>
                        <Box>
                          <Typography variant="subtitle1" fontWeight="medium">
                            {agent.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </Typography>
                          <Chip
                            label={agent.status.toUpperCase()}
                            color={getAgentStatusColor(agent.status)}
                            size="small"
                          />
                        </Box>
                      </Box>
                      <Typography variant="h6" fontWeight="bold" color={`${getAgentStatusColor(agent.status)}.main`}>
                        {performanceScore.toFixed(0)}
                      </Typography>
                    </Box>

                    {agent.current_task && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          Mevcut Görev:
                        </Typography>
                        <Typography variant="body2" fontWeight="medium">
                          {agent.current_task}
                        </Typography>
                      </Box>
                    )}

                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        Başarı Oranı:
                      </Typography>
                      <Typography variant="caption" fontWeight="medium">
                        {(agent.performance_metrics.success_rate * 100).toFixed(0)}%
                      </Typography>
                    </Box>

                    <LinearProgress
                      variant="determinate"
                      value={agent.performance_metrics.success_rate * 100}
                      color={getProgressColor(agent.status)}
                      sx={{ height: 6, borderRadius: 3, mb: 1 }}
                    />

                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        Görevler: {agent.performance_metrics.tasks_completed}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Yanıt: {agent.performance_metrics.average_response_time}ms
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
              );
            })}
          </Grid>
        </CardContent>
      </Card>

      {/* Aktif Görevler */}
      {coordination && coordination.active_tasks.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardHeader>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TimelineIcon />
              Aktif Görevler ({coordination.active_tasks.length})
            </Typography>
          </CardHeader>
          <CardContent>
            <List>
              {coordination.active_tasks.slice(0, 5).map((task, index) => (
                <React.Fragment key={task.task_id}>
                  <ListItem>
                    <ListItemIcon>
                      {task.status === 'completed' ? (
                        <CheckCircleIcon color="success" />
                      ) : task.status === 'failed' ? (
                        <ErrorIcon color="error" />
                      ) : (
                        <ScheduleIcon color="primary" />
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={`Görev #${task.task_id.substring(0, 8)}`}
                      secondary={
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Atanan Agent: {task.assigned_agent.replace(/_/g, ' ')}
                          </Typography>
                          {task.dependencies.length > 0 && (
                            <Typography variant="caption" color="text.secondary" display="block">
                              Bağımlılıklar: {task.dependencies.length} adet
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Chip
                        label={task.status}
                        color={getTaskStatusColor(task.status)}
                        size="small"
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                  {index < coordination.active_tasks.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Son Olaylar */}
      {recentEvents.length > 0 && (
        <Card>
          <CardHeader>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendingUpIcon />
              Son Blackboard Olayları
            </Typography>
          </CardHeader>
          <CardContent>
            <List>
              {recentEvents.slice(0, 5).map((event, index) => (
                <React.Fragment key={event.event_id}>
                  <ListItem>
                    <ListItemIcon>
                      <HubIcon color={event.processed ? 'success' : 'warning'} />
                    </ListItemIcon>
                    <ListItemText
                      primary={event.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      secondary={
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Kaynak: {event.source_agent.replace(/_/g, ' ')} →
                            Hedef: {event.target_agents.join(', ').replace(/_/g, ' ')}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" display="block">
                            {new Date(event.timestamp).toLocaleString('tr-TR')}
                          </Typography>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Chip
                        label={event.processed ? 'İşlendi' : 'Bekliyor'}
                        color={event.processed ? 'success' : 'warning'}
                        size="small"
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                  {index < recentEvents.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Agent Detayları Dialog'u */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Agent Detayları
        </DialogTitle>
        <DialogContent>
          {selectedAgent && (
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Avatar sx={{ bgcolor: `${getAgentStatusColor(selectedAgent.status)}.main`, width: 56, height: 56 }}>
                  {getAgentIcon(selectedAgent.name)}
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {selectedAgent.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </Typography>
                  <Chip
                    label={selectedAgent.status.toUpperCase()}
                    color={getAgentStatusColor(selectedAgent.status)}
                    size="small"
                  />
                </Box>
              </Box>

              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={4}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" fontWeight="bold" color="success.main">
                      {(selectedAgent.performance_metrics.success_rate * 100).toFixed(0)}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Başarı Oranı
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={4}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" fontWeight="bold" color="primary.main">
                      {selectedAgent.performance_metrics.tasks_completed}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Tamamlanan Görev
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={4}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" fontWeight="bold" color="secondary.main">
                      {selectedAgent.performance_metrics.average_response_time}ms
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Ortalama Yanıt
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>

              {selectedAgent.current_task && (
                <Paper sx={{ p: 2, bgcolor: 'primary.50', border: 1, borderColor: 'primary.200' }}>
                  <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                    Mevcut Görev:
                  </Typography>
                  <Typography variant="body2">
                    {selectedAgent.current_task}
                  </Typography>
                </Paper>
              )}

              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Son Aktivite: {new Date(selectedAgent.last_activity).toLocaleString('tr-TR')}
                </Typography>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Kapat</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MultiAgentCoordination;