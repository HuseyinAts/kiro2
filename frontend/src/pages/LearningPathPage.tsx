import { useState, useEffect, useRef } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Tabs,
  Tab,
  Button,
  CircularProgress,
  Alert,
  Divider
} from '@mui/material';
import {
  Timeline,
  VideoLibrary,
  Assessment,
  Refresh
} from '@mui/icons-material';
import { PathNodeData } from '../components/LearningPath/PathNode';
import learningPathService from '../services/learningPathService';
import { searchLearningResources, detectLearningStyle, VideoResponse } from '../api';
import { VideoLoadingManager, VideoLoadingState } from '../services/VideoLoadingManager';
import { difficultyToTurkish } from '../utils/difficultyTranslation';
import { VideoErrorHandler } from '../services/VideoErrorHandler';

// Import new sub-components
import { PathHeader } from '../components/LearningPath/PathHeader';
import { PathVisualizationTab } from '../components/LearningPath/PathVisualizationTab';
import { PathVideoResourcesTab } from '../components/LearningPath/PathVideoResourcesTab';
import { PathProgressTab } from '../components/LearningPath/PathProgressTab';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`learning-path-tabpanel-${index}`}
      aria-labelledby={`learning-path-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export function LearningPathPage() {
  // Tab state
  const [tabValue, setTabValue] = useState(0);

  // Loading states
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Path data
  const [pathNodes, setPathNodes] = useState<PathNodeData[]>([]);
  const [learningStyle, setLearningStyle] = useState<string>('');
  const [currentNodeId, setCurrentNodeId] = useState<string>('');
  const [showNodeDetails, setShowNodeDetails] = useState(false);

  // Video states
  const [videos, setVideos] = useState<VideoResponse[]>([]);
  const [videosLoading, setVideosLoading] = useState(false);
  const [videosError, setVideosError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  // VideoLoadingManager state
  const [videoLoadingState, setVideoLoadingState] = useState<VideoLoadingState>({
    status: 'idle',
    videos: [],
    error: null,
    loadingProgress: 0,
    retryCount: 0,
    requestId: '',
    loadingTime: 0,
    cacheHit: false,
    errorMessage: null,
  });

  // Refs
  const videoManagerRef = useRef<VideoLoadingManager | null>(null);
  const videoErrorHandlerRef = useRef<VideoErrorHandler | null>(null);

  // Subjects being loaded
  const [loadingSubjects, setLoadingSubjects] = useState<string[]>([]);

  // Initialize VideoLoadingManager and VideoErrorHandler
  useEffect(() => {
    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

    videoManagerRef.current = new VideoLoadingManager(API_BASE_URL, 20000, 2);
    videoErrorHandlerRef.current = new VideoErrorHandler(false, true);

    const unsubscribe = videoManagerRef.current.subscribe((state) => {
      setVideoLoadingState(state);

      setVideosLoading(state.status === 'loading');
      if (state.status === 'error' || state.status === 'fallback') {
        setVideosError(state.errorMessage || state.error?.message || 'Video yükleme hatası');
      } else if (state.status === 'success') {
        setVideosError(null);
        const allVideos: VideoResponse[] = [];
        state.videos.forEach(subjectVideo => {
          if (subjectVideo.videos) {
            allVideos.push(...subjectVideo.videos);
          }
        });
        setVideos(allVideos);
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  useEffect(() => {
    loadLearningPath();
  }, []);

  const loadLearningPath = async () => {
    try {
      setLoading(true);
      setError(null);

      const studentId = learningPathService.getStudentId();

      if (!studentId) {
        const profile = await learningPathService.createProfile({
          name: 'Demo Öğrenci',
          grade: 12,
          subjects: ['matematik', 'fizik', 'kimya'],
          goals: ['YKS hazırlık', 'Matematik geliştirme'],
          learning_style: 'visual',
          available_time: 120
        });
        console.log('Demo profile created:', profile);
      }

      let path = learningPathService.getCurrentPath();

      if (!path) {
        path = await learningPathService.generateLearningPath('matematik', 4);
      }

      const nodes = await convertPathToNodes(path);
      setPathNodes(nodes);

      const current = nodes.find(n => n.status === 'current');
      if (current) {
        setCurrentNodeId(current.id);
      }

      if (studentId) {
        try {
          const styleResponse = await detectLearningStyle(studentId);
          if (styleResponse.success) {
            setLearningStyle(styleResponse.learning_style?.hybrid_code || 'V-ASVS');
          }
        } catch (err) {
          console.warn('Could not detect learning style:', err);
          setLearningStyle('V-ASVS');
        }
      }

      await loadVideosForPath(path);

    } catch (err: any) {
      console.error('Error loading learning path:', err);
      setError(err.message || 'Öğrenme yolu yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const convertPathToNodes = async (path: any): Promise<PathNodeData[]> => {
    const nodes: PathNodeData[] = [];
    let yPosition = 0;

    const studentId = learningPathService.getStudentId();

    let completionStatus: Record<string, boolean> = {};
    try {
      if (studentId) {
        const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
        const response = await fetch(`${API_URL}/api/learning-path-v2/completion/${studentId}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          }
        });
        if (response.ok) {
          const data = await response.json();
          completionStatus = data.data || {};
        }
      }
    } catch (error) {
      console.warn('Could not load completion status:', error);
    }

    path.modules?.forEach((module: any, moduleIndex: number) => {
      module.topics?.forEach((topic: any, topicIndex: number) => {
        const nodeId = `${module.module_id}-${topic.topic_id}`;
        const isFirst = moduleIndex === 0 && topicIndex === 0;
        const isCompleted = completionStatus[nodeId] || false;

        nodes.push({
          id: nodeId,
          title: topic.name,
          description: `${module.title} - ${topic.name}`,
          type: 'lesson',
          status: isCompleted ? 'completed' : isFirst ? 'current' : 'available',
          progress: isCompleted ? 100 : isFirst ? 30 : 0,
          estimatedTime: `${topic.duration_minutes} dakika`,
          difficulty: 'intermediate',
          points: 100,
          prerequisites: topicIndex > 0 ? [`${module.module_id}-TOP${topicIndex}`] : [],
          resources: topic.resources?.length || 0,
          position: { x: 100 + moduleIndex * 300, y: 100 + yPosition }
        });

        yPosition += 150;
        if (topicIndex === module.topics.length - 1) {
          yPosition = 0;
        }
      });
    });

    return nodes;
  };

  const loadVideosForPath = async (path: any, retry: number = 0) => {
    if (!videoManagerRef.current) {
      console.error('VideoLoadingManager not initialized');
      return;
    }

    try {
      const subjects = (path.modules || []).map((module: any) => extractSubject(module.title));
      setLoadingSubjects(subjects);

      const studentProfile = {
        goals: subjects.map((s: string) => `${s} öğrenme`),
        currentLevel: subjects.reduce((acc: any, s: string) => {
          acc[s] = 50;
          return acc;
        }, {}),
        learningStyle: learningStyle || 'visual',
        preferences: {
          grade: 12,
          exam_type: 'YKS',
        }
      };

      console.log('Loading videos with VideoLoadingManager...', studentProfile);
      await videoManagerRef.current.loadVideos(studentProfile);

    } catch (err: any) {
      console.error('Error loading videos:', err);

      if (videoErrorHandlerRef.current) {
        const errorContext = {
          component: 'LearningPathPage',
          action: 'loadVideosForPath',
          subjects: loadingSubjects,
          retryCount: retry,
        };
        videoErrorHandlerRef.current.logError(err, errorContext);
      }
    }
  };

  const extractSubject = (title: string): string => {
    const lowerTitle = title.toLowerCase();
    if (lowerTitle.includes('matematik')) return 'matematik';
    if (lowerTitle.includes('fizik')) return 'fizik';
    if (lowerTitle.includes('kimya')) return 'kimya';
    if (lowerTitle.includes('biyoloji')) return 'biyoloji';
    if (lowerTitle.includes('türkçe')) return 'türkçe';
    return 'matematik';
  };

  const extractTopic = (topicName: string): string | undefined => {
    const lowerTopic = topicName.toLowerCase();

    if (lowerTopic.includes('türev')) return 'türev';
    if (lowerTopic.includes('integral')) return 'integral';
    if (lowerTopic.includes('limit')) return 'limit';
    if (lowerTopic.includes('fonksiyon')) return 'fonksiyon';
    if (lowerTopic.includes('hareket')) return 'hareket';
    if (lowerTopic.includes('kuvvet')) return 'kuvvet';
    if (lowerTopic.includes('enerji')) return 'enerji';
    if (lowerTopic.includes('elektrik')) return 'elektrik';
    if (lowerTopic.includes('atom')) return 'atom';
    if (lowerTopic.includes('reaksiyon')) return 'reaksiyon';
    if (lowerTopic.includes('molekül')) return 'molekül';

    return undefined;
  };

  const handleRetryVideos = async () => {
    if (!videoManagerRef.current) return;

    const path = learningPathService.getCurrentPath();
    if (path) {
      setRetryCount(prev => prev + 1);
      await videoManagerRef.current.retryLoad();
    }
  };

  const handleShowFallback = async () => {
    console.log('Loading fallback/example videos...', loadingSubjects);

    if (!videoManagerRef.current) {
      console.error('VideoLoadingManager not initialized');
      return;
    }

    try {
      setVideosLoading(true);
      setVideosError(null);

      const subject = loadingSubjects[0] || 'matematik';

      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
      const response = await fetch(`${API_URL}/api/learning-path-v2/fallback-videos/${subject}?limit=10`, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.videos && data.videos.length > 0) {
          const fallbackVideos = data.videos.map((v: any) => ({
            video_id: v.resource_id,
            title: v.title,
            description: v.description,
            url: v.url,
            thumbnail_url: v.thumbnail,
            duration: v.duration,
            duration_minutes: v.duration_minutes,
            channel_name: v.channel_name,
            scores: v.scores,
            is_accessible: v.is_accessible,
            is_turkish: true,
            is_example: v.is_example,
            tags: v.tags
          }));

          setVideos(fallbackVideos);
          setVideosError(null);

          console.log(`✅ Loaded ${fallbackVideos.length} fallback videos for ${subject}`);
          alert(`✅ ${fallbackVideos.length} örnek video yüklendi! ${subject} için kaliteli eğitim videoları gösteriliyor.`);
        } else {
          setVideosError('Örnek video bulunamadı');
          alert('⚠️ Henüz bu konu için örnek video eklenmemiş.');
        }
      } else {
        throw new Error('Fallback video API failed');
      }
    } catch (error: any) {
      console.error('Error loading fallback videos:', error);
      setVideosError('Örnek video yükleme hatası');
      alert('❌ Örnek videolar yüklenirken hata oluştu. Lütfen daha sonra tekrar deneyin.');
    } finally {
      setVideosLoading(false);
    }
  };

  const handleCancelVideoLoad = () => {
    if (!videoManagerRef.current) return;
    videoManagerRef.current.cancelLoad();
    console.log('Video loading cancelled by user');
  };

  const handleNodeClick = async (node: PathNodeData) => {
    console.log('Node clicked:', node);
    setCurrentNodeId(node.id);
    setShowNodeDetails(true);

    try {
      setVideosLoading(true);
      setVideosError(null);

      const subject = extractSubject(node.description);
      const topic = extractTopic(node.title);
      const difficultyTurkish = difficultyToTurkish(node.difficulty);

      console.log(`Loading resources for node: ${node.id}, subject: ${subject}, topic: ${topic}, difficulty: ${difficultyTurkish}`);

      const result = await searchLearningResources({
        subject: subject,
        topic: topic,
        difficulty: difficultyTurkish,
        max_results: 10,
        student_profile: {
          learning_style: learningStyle,
          grade: 12,
        }
      });

      if (result.success && result.resources) {
        console.log(`Loaded ${result.resources.length} resources for node ${node.id}`);

        const sortedResources = result.resources.sort((a, b) => {
          const scoreA = a.scores?.final_score || 0;
          const scoreB = b.scores?.final_score || 0;
          return scoreB - scoreA;
        });

        setVideos(sortedResources);
      } else if (result.error) {
        setVideosError(result.error.message);
      }
    } catch (error: any) {
      console.error('Error loading node resources:', error);
      setVideosError(error.message || 'Kaynaklar yüklenirken hata oluştu');
    } finally {
      setVideosLoading(false);
    }
  };

  const handleVideoPlay = (video: VideoResponse) => {
    console.log('Playing video:', video);
    window.open(video.url, '_blank');
  };

  const handleRefresh = () => {
    loadLearningPath();
  };

  const handleCloseNodeDetails = () => {
    setShowNodeDetails(false);
  };

  // Loading state
  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box className="flex flex-col items-center justify-center" sx={{ minHeight: '60vh' }}>
          <CircularProgress size={60} thickness={4} />
          <Typography variant="h6" sx={{ mt: 3 }} color="text.secondary">
            Öğrenme yolunuz hazırlanıyor...
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }} color="text.secondary">
            Kişiselleştirilmiş içerikler yükleniyor
          </Typography>
        </Box>
      </Container>
    );
  }

  // Error state
  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={handleRefresh} startIcon={<Refresh />}>
          Tekrar Dene
        </Button>
      </Container>
    );
  }

  // Main content
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header with Learning Style Badge */}
      <PathHeader
        learningStyle={learningStyle}
        onRefresh={handleRefresh}
      />

      <Divider sx={{ mb: 3 }} />

      {/* Tabs */}
      <Paper elevation={2} sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          variant="fullWidth"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab
            icon={<Timeline />}
            label="Yol Haritası"
            iconPosition="start"
          />
          <Tab
            icon={<VideoLibrary />}
            label="Size Özel Kaynaklar"
            iconPosition="start"
          />
          <Tab
            icon={<Assessment />}
            label="İlerleme"
            iconPosition="start"
          />
        </Tabs>

        {/* Tab 1: Yol Haritası */}
        <TabPanel value={tabValue} index={0}>
          <PathVisualizationTab
            pathNodes={pathNodes}
            currentNodeId={currentNodeId}
            showNodeDetails={showNodeDetails}
            onNodeClick={handleNodeClick}
            onCloseNodeDetails={handleCloseNodeDetails}
          />
        </TabPanel>

        {/* Tab 2: Size Özel Kaynaklar (Video) */}
        <TabPanel value={tabValue} index={1}>
          <PathVideoResourcesTab
            videos={videos}
            videosLoading={videosLoading}
            videosError={videosError}
            videoLoadingState={videoLoadingState}
            loadingSubjects={loadingSubjects}
            onRetryVideos={handleRetryVideos}
            onShowFallback={handleShowFallback}
            onCancelVideoLoad={handleCancelVideoLoad}
            onVideoPlay={handleVideoPlay}
          />
        </TabPanel>

        {/* Tab 3: İlerleme */}
        <TabPanel value={tabValue} index={2}>
          <PathProgressTab pathNodes={pathNodes} />
        </TabPanel>
      </Paper>
    </Container>
  );
}

export default LearningPathPage;
