/**
 * Modern Learning Path Page - Glassmorphism Design
 * Kişiselleştirilmiş öğrenme yolu ve kaynaklar
 */

import { Timeline, VideoLibrary, Assessment, Refresh, AutoAwesome } from '@mui/icons-material';
import { Container, Box, Tabs, Tab, Typography } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect, useCallback, useMemo } from 'react';

// Custom hooks
import { VideoResponse } from '../api';
import { LearningStyleQuiz } from '../components/LearningPath/LearningStyleQuiz';
import { ModernLearningPathVisualizer } from '../components/LearningPath/ModernLearningPathVisualizer';
import { NodeDetailsPanel } from '../components/LearningPath/Page/NodeDetailsPanel';
import { PathNodeData } from '../components/LearningPath/PathNode';
import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { ModernLoader } from '../components/ui/ModernLoader';
import { useLearningPath } from '../hooks/useLearningPath';
import { useLearningPathVideos } from '../hooks/useLearningPathVideos';

import modernColors from '../theme/modern-colors';

// Types
import { generateConnections } from '../utils/learningPathHelpers';

// Lazy-loaded tab content components

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
      id={`modern-learning-path-tabpanel-${index}`}
      aria-labelledby={`modern-learning-path-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * Modern Learning Path Page
 */
export function ModernLearningPathPage() {
  // ========================================
  // Custom hooks for business logic
  // ========================================
  const {
    pathNodes,
    learningStyle,
    currentNodeId,
    loading,
    error,
    needsQuiz,
    reload,
    setCurrentNode,
    submitQuizResult,
    skipQuiz,
  } = useLearningPath();

  const {
    videos,
    videosLoading,
    loadVideosForPath,
    loadVideosForNode,
  } = useLearningPathVideos();

  // ========================================
  // Local UI state
  // ========================================
  const [tabValue, setTabValue] = useState(0);
  const [showNodeDetails, setShowNodeDetails] = useState(false);
  const [selectedNode, setSelectedNode] = useState<PathNodeData | null>(null);

  // ========================================
  // Effects
  // ========================================

  /**
   * Load videos when path is ready
   */
  useEffect(() => {
    if (pathNodes.length > 0 && learningStyle) {
      // Build a minimal path object from nodes for video loading
      const path = { modules: [{ title: pathNodes[0]?.title || 'matematik' }] };
      loadVideosForPath(path, learningStyle);
    }
  }, [pathNodes, learningStyle, loadVideosForPath]);

  // ========================================
  // Event handlers
  // ========================================

  /**
   * Handle node click in path visualizer
   */
  const handleNodeClick = useCallback(
    async (node: PathNodeData) => {
      setCurrentNode(node.id);
      setSelectedNode(node);
      setShowNodeDetails(true);
      await loadVideosForNode(
        node.id,
        node.title,
        node.description,
        node.difficulty,
        learningStyle,
      );
    },
    [setCurrentNode, loadVideosForNode, learningStyle],
  );

  /**
   * Handle video play
   */
  const handleVideoPlay = useCallback((video: VideoResponse) => {
    window.open(video.url, '_blank');
  }, []);

  /**
   * Handle close node details
   */
  const handleCloseDetails = useCallback(() => {
    setShowNodeDetails(false);
  }, []);

  // ========================================
  // Memoized values
  // ========================================

  /**
   * Check if path exists
   */
  const hasPath = useMemo(
    () => pathNodes.length > 0,
    [pathNodes.length],
  );

  /**
   * Calculate progress stats
   */
  const progressStats = useMemo(() => {
    const completed = pathNodes.filter((n) => n.status === 'completed').length;
    const inProgress = pathNodes.filter((n) => n.status === 'current').length;
    const available = pathNodes.filter((n) => n.status === 'available').length;
    const total = pathNodes.length;

    return {
      completed,
      inProgress,
      available,
      total,
      percentage: total > 0 ? Math.round((completed / total) * 100) : 0,
    };
  }, [pathNodes]);

  // ========================================
  // Render states
  // ========================================

  // Loading state
  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.mesh,
        }}
      >
        <ModernLoader message="Öğrenme yolunuz yükleniyor..." size="large" />
      </Box>
    );
  }

  // Quiz state — show VARK questionnaire before creating path
  if (needsQuiz) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.mesh,
          p: 2,
        }}
      >
        <Container maxWidth="sm">
          <LearningStyleQuiz
            onComplete={submitQuizResult}
            onSkip={skipQuiz}
          />
        </Container>
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.mesh,
          p: 2,
        }}
      >
        <Container maxWidth="sm">
          <GlassCard glassIntensity="medium" elevated>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h5" sx={{ fontWeight: 700, mb: 2, color: 'error.main' }}>
                Hata Oluştu
              </Typography>
              <Typography variant="body1" sx={{ mb: 3 }}>
                {error}
              </Typography>
              <ModernButton
                variant="gradient"
                gradient={modernColors.gradients.primary}
                icon={<Refresh />}
                onClick={reload}
              >
                Tekrar Dene
              </ModernButton>
            </Box>
          </GlassCard>
        </Container>
      </Box>
    );
  }

  // Main render
  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: modernColors.gradients.mesh,
        py: 4,
      }}
    >
      <Container maxWidth="xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Box sx={{ mb: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 56,
                    height: 56,
                    borderRadius: 3,
                    background: modernColors.gradients.primary,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Timeline sx={{ fontSize: 32, color: 'white' }} />
                </Box>
                <Box>
                  <Typography
                    variant="h3"
                    sx={{
                      fontWeight: 900,
                      background: modernColors.gradients.primary,
                      backgroundClip: 'text',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                    }}
                  >
                    Öğrenme Yolunuz
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Kişiselleştirilmiş öğrenme yolunuz ve size özel kaynaklar
                  </Typography>
                </Box>
              </Box>
              <ModernButton
                variant="glass"
                icon={<Refresh />}
                onClick={reload}
              >
                Yenile
              </ModernButton>
            </Box>

            {/* Learning Style Badge */}
            {learningStyle && (
              <GlassCard
                glassIntensity="light"
                hoverable
                gradient={modernColors.gradients.sunset}
                sx={{ display: 'inline-block' }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AutoAwesome sx={{ fontSize: 20 }} />
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    Öğrenme Stiliniz: {
                      {
                        visual: 'Görsel Öğrenen',
                        auditory: 'İşitsel Öğrenen',
                        reading: 'Okuma-Yazma Öğrenen',
                        kinesthetic: 'Uygulamalı Öğrenen',
                        mixed: 'Karma Öğrenen',
                      }[learningStyle] || learningStyle
                    }
                  </Typography>
                </Box>
              </GlassCard>
            )}
          </Box>
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <GlassCard glassIntensity="medium" elevated>
            <Tabs
              value={tabValue}
              onChange={(_, newValue) => setTabValue(newValue)}
              variant="fullWidth"
              sx={{
                borderBottom: 1,
                borderColor: 'divider',
                '& .MuiTab-root': {
                  fontWeight: 600,
                  fontSize: 16,
                  textTransform: 'none',
                  minHeight: 64,
                },
                '& .Mui-selected': {
                  color: '#3b82f6',
                },
                '& .MuiTabs-indicator': {
                  background: modernColors.gradients.primary,
                  height: 3,
                  borderRadius: '3px 3px 0 0',
                },
              }}
            >
              <Tab icon={<Timeline />} label="Yol Haritası" iconPosition="start" />
              <Tab icon={<VideoLibrary />} label="Size Özel Kaynaklar" iconPosition="start" />
              <Tab icon={<Assessment />} label="İlerleme Takibi" iconPosition="start" />
            </Tabs>

            {/* Tab 1: Path Visualization */}
            <TabPanel value={tabValue} index={0}>
              <AnimatePresence mode="wait">
                <motion.div
                  key="visualization"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                >
                  {/* Node Details Panel (conditional) */}
                  {showNodeDetails && selectedNode && (
                    <Box sx={{ mb: 3 }}>
                      <NodeDetailsPanel node={selectedNode} onClose={handleCloseDetails} />
                    </Box>
                  )}

                  {/* Learning Path Visualizer */}
                  {pathNodes.length > 0 ? (
                    <ModernLearningPathVisualizer
                      nodes={pathNodes}
                      connections={generateConnections(pathNodes)}
                      currentNodeId={currentNodeId}
                      onNodeClick={handleNodeClick}
                      viewMode="tree"
                    />
                  ) : (
                    <GlassCard glassIntensity="light">
                      <Box sx={{ textAlign: 'center', py: 8 }}>
                        <Timeline sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary">
                          Henüz öğrenme yolu oluşturulmamış
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          Sınav sonuçlarınıza göre kişiselleştirilmiş yolunuz oluşturulacak
                        </Typography>
                      </Box>
                    </GlassCard>
                  )}
                </motion.div>
              </AnimatePresence>
            </TabPanel>

            {/* Tab 2: Video Resources */}
            <TabPanel value={tabValue} index={1}>
              <AnimatePresence mode="wait">
                <motion.div
                  key="videos"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                >
                  <GlassCard glassIntensity="light">
                    {videosLoading ? (
                      <Box sx={{ textAlign: 'center', py: 8 }}>
                        <ModernLoader message="Videolar yükleniyor..." />
                      </Box>
                    ) : videos.length > 0 ? (
                      <Box>
                        <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                          Size Özel Video Kaynakları
                        </Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                          {videos.map((video, index) => (
                            <motion.div
                              key={(video as any).id || video.video_id || index}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.3, delay: index * 0.05 }}
                            >
                              <GlassCard
                                glassIntensity="light"
                                hoverable
                                role="button"
                                aria-label={`${video.title} videosunu oynat`}
                                tabIndex={0}
                                onClick={() => handleVideoPlay(video)}
                                onKeyDown={(e: React.KeyboardEvent) => {
                                  if (e.key === 'Enter' || e.key === ' ') {
                                    e.preventDefault();
                                    handleVideoPlay(video);
                                  }
                                }}
                                sx={{
                                  cursor: 'pointer',
                                  '&:focus': {
                                    outline: '2px solid rgba(59, 130, 246, 0.5)',
                                    outlineOffset: '2px',
                                  },
                                }}
                              >
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                  <VideoLibrary color="primary" />
                                  <Box sx={{ flex: 1 }}>
                                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                                      {video.title}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                      {video.description || 'Video açıklaması'}
                                    </Typography>
                                  </Box>
                                </Box>
                              </GlassCard>
                            </motion.div>
                          ))}
                        </Box>
                      </Box>
                    ) : (
                      <Box sx={{ textAlign: 'center', py: 8 }}>
                        <VideoLibrary sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary">
                          Henüz video kaynağı eklenmemiş
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          Öğrenme yolunuzdaki konulara uygun videolar burada görünecek
                        </Typography>
                      </Box>
                    )}
                  </GlassCard>
                </motion.div>
              </AnimatePresence>
            </TabPanel>

            {/* Tab 3: Progress Tracking */}
            <TabPanel value={tabValue} index={2}>
              <AnimatePresence mode="wait">
                <motion.div
                  key="progress"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                >
                  <GlassCard glassIntensity="light">
                    <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                      İlerleme İstatistikleri
                    </Typography>

                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 2 }}>
                      <GlassCard
                        glassIntensity="light"
                        hoverable
                        gradient={modernColors.gradients.success}
                      >
                        <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                          {progressStats.completed}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Tamamlanan Modül
                        </Typography>
                      </GlassCard>

                      <GlassCard
                        glassIntensity="light"
                        hoverable
                        gradient={modernColors.gradients.primary}
                      >
                        <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                          {progressStats.inProgress}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Devam Eden
                        </Typography>
                      </GlassCard>

                      <GlassCard
                        glassIntensity="light"
                        hoverable
                        gradient={modernColors.gradients.ocean}
                      >
                        <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                          {progressStats.available}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Erişilebilir
                        </Typography>
                      </GlassCard>

                      <GlassCard
                        glassIntensity="light"
                        hoverable
                        gradient={modernColors.gradients.warning}
                      >
                        <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                          {progressStats.percentage}%
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Tamamlanma Oranı
                        </Typography>
                      </GlassCard>
                    </Box>

                    {!hasPath && (
                      <Box sx={{ mt: 4, textAlign: 'center' }}>
                        <Assessment sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary">
                          İlerleme takibi için önce bir öğrenme yolu oluşturun
                        </Typography>
                      </Box>
                    )}
                  </GlassCard>
                </motion.div>
              </AnimatePresence>
            </TabPanel>
          </GlassCard>
        </motion.div>
      </Container>
    </Box>
  );
}

export default ModernLearningPathPage;
