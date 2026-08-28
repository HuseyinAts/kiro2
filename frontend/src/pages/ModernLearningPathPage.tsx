import React, { useState, useEffect } from 'react';
import { Box, Container, Tabs, Tab } from '@mui/material';
import { Timeline, VideoLibrary, Assessment } from '@mui/icons-material';
import { motion } from 'framer-motion';

import { useLearningPath } from '../hooks/useLearningPath';
import { useLearningPathVideos } from '../hooks/useLearningPathVideos';
import { ModernLoader } from '../components/ui/ModernLoader';
import { OnboardingWizard } from '../components/LearningPath/OnboardingWizard';
import { GlassCard } from '../components/ui/GlassCard';
import { SuccessAnimation } from '../components/ADHD/InstantFeedback/SuccessAnimation';
import modernColors from '../theme/modern-colors';

// New Extracted Components
import { ModernLearningPathHeader } from '../components/LearningPath/ModernTabs/ModernLearningPathHeader';
import { ModernPathVisualizationTab } from '../components/LearningPath/ModernTabs/ModernPathVisualizationTab';
import { ModernVideoResourcesTab } from '../components/LearningPath/ModernTabs/ModernVideoResourcesTab';
import { ModernProgressTrackingTab } from '../components/LearningPath/ModernTabs/ModernProgressTrackingTab';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} id={`modern-tabpanel-${index}`} aria-labelledby={`modern-tab-${index}`} {...other}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export function ModernLearningPathPage() {
  const learningPath = useLearningPath();
  const videoData = useLearningPathVideos();

  const [tabValue, setTabValue] = useState(0);
  const [celebration, setCelebration] = useState({ visible: false, type: 'streak', message: '' });

  // Load videos when path is loaded
  useEffect(() => {
    if (!learningPath.loading && learningPath.pathNodes.length > 0) {
      videoData.loadVideosForPath(
        { modules: [{ title: learningPath.pathNodes[0]?.title || 'matematik' }] },
        learningPath.learningStyle,
        learningPath.selectedSubject
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [learningPath.loading, learningPath.pathNodes.length, learningPath.learningStyle, learningPath.selectedSubject]);

  if (learningPath.loading) {
    return (
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: modernColors.gradients.mesh }}>
        <ModernLoader message="Öğrenme yolunuz yükleniyor..." size="large" />
      </Box>
    );
  }

  if (learningPath.needsOnboarding) {
    return (
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: modernColors.gradients.mesh, p: 2 }}>
        <Container maxWidth="sm">
          <OnboardingWizard studentId={learningPath.studentId || ''} onComplete={learningPath.submitOnboardingResult} onSkip={learningPath.skipOnboarding} />
        </Container>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', background: modernColors.gradients.mesh, py: 4 }}>
      <SuccessAnimation
        isVisible={celebration.visible} type={celebration.type as any} message={celebration.message}
        onComplete={() => setCelebration(prev => ({ ...prev, visible: false }))} showConfetti
      />

      <Container maxWidth="xl">
        <ModernLearningPathHeader learningPath={learningPath} />

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
          <GlassCard glassIntensity="medium" elevated>
            <Tabs
              value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} variant="fullWidth"
              sx={{ borderBottom: 1, borderColor: 'divider', '& .MuiTab-root': { fontWeight: 600, fontSize: 16, textTransform: 'none', minHeight: 64 }, '& .Mui-selected': { color: '#3b82f6' }, '& .MuiTabs-indicator': { background: modernColors.gradients.primary, height: 3, borderRadius: '3px 3px 0 0' } }}
            >
              <Tab icon={<Timeline />} label="Yol Haritası" iconPosition="start" />
              <Tab icon={<VideoLibrary />} label="Size Özel Kaynaklar" iconPosition="start" />
              <Tab icon={<Assessment />} label="İlerleme Takibi" iconPosition="start" />
            </Tabs>

            <TabPanel value={tabValue} index={0}>
              <ModernPathVisualizationTab learningPath={learningPath} videoData={videoData} />
            </TabPanel>
            
            <TabPanel value={tabValue} index={1}>
              <ModernVideoResourcesTab videoData={videoData} />
            </TabPanel>
            
            <TabPanel value={tabValue} index={2}>
              <ModernProgressTrackingTab learningPath={learningPath} />
            </TabPanel>
          </GlassCard>
        </motion.div>
      </Container>
    </Box>
  );
}

export default ModernLearningPathPage;
