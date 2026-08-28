import React, { useState, useMemo } from 'react';
import { Box, Typography, Alert, Chip } from '@mui/material';
import { CalendarToday, Science, Timeline, AccountTree, Shuffle } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

import { ProactiveCoachWidget } from '@/components/LearningPath/ProactiveCoachWidget';
import { AdaptiveFeedbackPanel } from '@/components/LearningPath/AdaptiveFeedbackPanel';
import { ReviewQueuePanel } from '@/components/LearningPath/ReviewQueuePanel';
import { ProductiveFailureFlow } from '@/components/LearningPath/ProductiveFailureFlow';
import { StreakTracker } from '@/components/ADHD/InstantFeedback/StreakTracker';
import { QuizInterface, Question } from '@/components/Quiz/QuizInterface';
import { NodeDetailsPanel } from '@/components/LearningPath/Page/NodeDetailsPanel';
import { SkillGraphView } from '@/components/LearningPath/SkillGraphView';
import { ModernLearningPathVisualizer } from '@/components/LearningPath/ModernLearningPathVisualizer';
import { generateConnections } from '@/utils/learningPathHelpers';
import { mapApiToQuizQuestion } from '@/utils/questionMappers';
import { GlassCard } from '@/components/ui/GlassCard';
import { ModernButton } from '@/components/ui/ModernButton';

import type { PathNodeData } from '@/components/LearningPath/PathNode';
import type { UseLearningPathReturn } from '@/hooks/useLearningPath';
import type { UseLearningPathVideosReturn } from '@/hooks/useLearningPathVideos';

interface Props {
  learningPath: UseLearningPathReturn;
  videoData: UseLearningPathVideosReturn;
}

export const ModernPathVisualizationTab: React.FC<Props> = ({ learningPath, videoData }) => {
  const { pathNodes, currentNodeId, selectedSubject, changeSubject, reload } = learningPath;
  const { videos, videosLoading } = videoData;

  const [pathViewMode, setPathViewMode] = useState<'linear' | 'graph'>('linear');
  const [showNodeDetails, setShowNodeDetails] = useState(false);
  const [selectedNode, setSelectedNode] = useState<PathNodeData | null>(null);
  const [nodeQuizQuestions, setNodeQuizQuestions] = useState<Question[] | null>(null);
  const [activeQuizNode, setActiveQuizNode] = useState<PathNodeData | null>(null);
  const [interleavedQuestions, setInterleavedQuestions] = useState<Question[] | null>(null);
  const [productiveFailureActive, setProductiveFailureActive] = useState(false);
  const [quizStreak, setQuizStreak] = useState(0);
  const [bestStreak, setBestStreak] = useState(0);
  const [feedbackData, setFeedbackData] = useState({ visible: false, score: 0, total: 0, correct: 0, passed: false });

  const hasPath = pathNodes.length > 0;

  const dailyPlan = useMemo(() => {
    if (!hasPath) return { nodes: [], totalMinutes: 0 };
    let nodes: PathNodeData[] = [];
    const currentIdx = pathNodes.findIndex(n => n.id === currentNodeId);
    if (currentIdx !== -1) {
      nodes = pathNodes.slice(currentIdx, currentIdx + 3);
    } else {
      nodes = pathNodes.filter(n => n.status !== 'completed').slice(0, 3);
      if (nodes.length === 0) nodes = pathNodes.slice(0, 3);
    }
    const totalMinutes = nodes.reduce((acc, curr) => {
      const match = curr.estimatedTime.match(/\d+/);
      return acc + (match ? parseInt(match[0], 10) : 15);
    }, 0);
    return { nodes, totalMinutes };
  }, [pathNodes, currentNodeId, hasPath]);

  const handleNodeClick = (node: PathNodeData) => {
    setSelectedNode(node);
    setShowNodeDetails(true);
  };

  const handleCloseDetails = () => {
    setShowNodeDetails(false);
    setSelectedNode(null);
  };

  const handleStartQuiz = async (node: PathNodeData) => {
    try {
      const res = await fetch(`/api/v1/learning-path/nodes/${node.id}/quiz`, { credentials: 'include' });
      const data = await res.json();
      if (data.success && data.questions) {
        setNodeQuizQuestions(data.questions.map(mapApiToQuizQuestion));
        setActiveQuizNode(node);
        setShowNodeDetails(false);
      }
    } catch (err) {
      console.error('Quiz baslatilamadi', err);
    }
  };

  const handleStartProductiveFailure = (node: PathNodeData) => {
    setActiveQuizNode(node);
    setShowNodeDetails(false);
    setProductiveFailureActive(true);
  };

  const handleQuizComplete = async (results: any) => {
    const passed = results.score >= (activeQuizNode?.quiz?.passing_score || 60);
    if (activeQuizNode && passed) {
      learningPath.markNodeComplete(activeQuizNode.id);
      setQuizStreak(s => {
        const newS = s + 1;
        if (newS > bestStreak) setBestStreak(newS);
        return newS;
      });
    } else {
      setQuizStreak(0);
    }

    setFeedbackData({
      visible: true,
      score: results.score,
      total: results.total,
      correct: Object.values(results.answers).filter((v, i) => v === nodeQuizQuestions?.[i]?.correctAnswer).length,
      passed,
    });

    setNodeQuizQuestions(null);
    setActiveQuizNode(null);
  };

  return (
    <AnimatePresence mode="wait">
      <motion.div key="visualization" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} transition={{ duration: 0.3 }}>
        {!nodeQuizQuestions && !interleavedQuestions && <ProactiveCoachWidget />}

        {!nodeQuizQuestions && !interleavedQuestions && dailyPlan.nodes.length > 0 && (
          <GlassCard glassIntensity="light" sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
              <CalendarToday sx={{ color: '#3b82f6' }} />
              <Typography variant="h6" sx={{ fontWeight: 700 }}>Bugünün Planı</Typography>
              <Chip label={`~${dailyPlan.totalMinutes} dk`} size="small" sx={{ ml: 'auto', fontWeight: 600, backgroundColor: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' }} />
            </Box>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {dailyPlan.nodes.map((node, i) => (
                <Box
                  key={node.id}
                  onClick={() => handleNodeClick(node)}
                  sx={{
                    display: 'flex', alignItems: 'center', gap: 1.5, p: 1.5, borderRadius: 2, cursor: 'pointer', transition: 'background 0.2s',
                    backgroundColor: i === 0 ? 'rgba(59, 130, 246, 0.08)' : 'transparent', '&:hover': { backgroundColor: 'rgba(59, 130, 246, 0.12)' },
                  }}
                >
                  <Box sx={{ width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: i === 0 ? '#3b82f6' : 'rgba(0,0,0,0.08)', color: i === 0 ? 'white' : 'text.secondary', fontWeight: 700, fontSize: 14 }}>{i + 1}</Box>
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600 }} noWrap>{node.title}</Typography>
                    <Typography variant="caption" color="text.secondary">{node.estimatedTime} · {node.difficulty}</Typography>
                  </Box>
                  {node.status === 'current' && <Chip label="Devam" size="small" color="primary" variant="outlined" />}
                </Box>
              ))}
            </Box>
          </GlassCard>
        )}

        {feedbackData.visible && (
          <Box sx={{ mb: 3 }}>
            <AdaptiveFeedbackPanel
              quizScore={feedbackData.score} totalQuestions={feedbackData.total} correctCount={feedbackData.correct} passed={feedbackData.passed}
              onClose={() => setFeedbackData(prev => ({ ...prev, visible: false }))} onAdaptPath={reload}
            />
          </Box>
        )}

        {!nodeQuizQuestions && !interleavedQuestions && <ReviewQueuePanel />}

        {nodeQuizQuestions && activeQuizNode && (
          <Box sx={{ mb: 3 }}>
            {productiveFailureActive ? (
              <ProductiveFailureFlow
                topic={activeQuizNode.title}
                onComplete={() => { setNodeQuizQuestions(null); setActiveQuizNode(null); setProductiveFailureActive(false); }}
                onSkip={() => { setNodeQuizQuestions(null); setActiveQuizNode(null); setProductiveFailureActive(false); }}
              />
            ) : (
              <>
                {quizStreak > 0 && <Box sx={{ mb: 2 }}><StreakTracker currentStreak={quizStreak} bestStreak={bestStreak} position="top-right" /></Box>}
                <QuizInterface
                  config={{ title: `${activeQuizNode.title} Quiz`, description: `${activeQuizNode.title} konusunu test et`, questions: nodeQuizQuestions, passingScore: activeQuizNode.quiz?.passing_score || 60, immediateFeedback: true, showCorrectAnswers: true }}
                  onSubmit={handleQuizComplete} onExit={() => { setNodeQuizQuestions(null); setActiveQuizNode(null); }}
                />
              </>
            )}
          </Box>
        )}

        {interleavedQuestions && (
          <Box sx={{ mb: 3 }}>
            <QuizInterface
              config={{ title: 'Karışık Pratik', description: 'Farklı konulardan karışık sorularla çalış', questions: interleavedQuestions, passingScore: 60, immediateFeedback: true, showCorrectAnswers: true }}
              onSubmit={async (results) => {
                const wrongIds = interleavedQuestions.filter(q => results.answers[q.id] !== q.correctAnswer).map(q => q.id);
                if (wrongIds.length > 0) {
                  try {
                    await fetch('/api/v1/learning-path/register-wrong-answers', { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify({ question_ids: wrongIds }) });
                  } catch (err) {}
                }
              }}
              onExit={() => setInterleavedQuestions(null)}
            />
          </Box>
        )}

        {hasPath && !interleavedQuestions && (
          <Alert
            severity="info" icon={<Shuffle />} sx={{ mb: 3, borderRadius: 2 }}
            action={
              <ModernButton variant="glass" icon={<Science />} onClick={async () => {
                const subjects = [...new Set(pathNodes.map(n => n.title.split(' ')[0]))].slice(0, 5);
                try {
                  const res = await fetch(`/api/v1/learning-path/interleaved-practice?subjects=${subjects.join(',')}&count=10`, { credentials: 'include' });
                  const data = await res.json();
                  if (data.success && data.questions?.length > 0) {
                    setInterleavedQuestions(data.questions.map(mapApiToQuizQuestion));
                  }
                } catch (err) {}
              }}>Karışık Pratik</ModernButton>
            }
          >
            <Box>
              <Typography variant="subtitle2" fontWeight={700}>Karışık Pratik Modu</Typography>
              <Typography variant="body2">Farklı konulardan karışık sorularla çalış. Araştırmalar bu yöntemin %74 daha iyi sonuç verdiğini gösteriyor.</Typography>
              <Box sx={{ display: 'flex', gap: 0.5, mt: 1, flexWrap: 'wrap' }}>
                {[...new Set(pathNodes.map(n => n.title.split(' ')[0]))].slice(0, 5).map(topic => <Chip key={topic} label={topic} size="small" variant="outlined" />)}
              </Box>
            </Box>
          </Alert>
        )}

        {showNodeDetails && selectedNode && (
          <Box sx={{ mb: 3 }}>
            <NodeDetailsPanel node={selectedNode} onClose={handleCloseDetails} onStartQuiz={handleStartQuiz} onStartProductiveFailure={handleStartProductiveFailure} resources={videos} resourcesLoading={videosLoading} />
          </Box>
        )}

        {pathNodes.length > 0 && (
          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
            <Chip icon={<Timeline sx={{ fontSize: 16 }} />} label="Yol Haritası" size="small" onClick={() => setPathViewMode('linear')} sx={{ fontWeight: 600, cursor: 'pointer', ...(pathViewMode === 'linear' ? { bgcolor: '#3b82f620', color: '#3b82f6', borderColor: '#3b82f6', borderWidth: 1.5, borderStyle: 'solid' } : {}) }} />
            <Chip icon={<AccountTree sx={{ fontSize: 16 }} />} label="Skill Haritası" size="small" onClick={() => setPathViewMode('graph')} sx={{ fontWeight: 600, cursor: 'pointer', ...(pathViewMode === 'graph' ? { bgcolor: '#8b5cf620', color: '#8b5cf6', borderColor: '#8b5cf6', borderWidth: 1.5, borderStyle: 'solid' } : {}) }} />
          </Box>
        )}

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          {['matematik', 'fizik', 'kimya', 'biyoloji', 'turkce', 'geometri'].map((subj) => (
            <Chip key={subj} label={subj.charAt(0).toUpperCase() + subj.slice(1)} onClick={() => changeSubject(subj)} color={selectedSubject === subj ? 'primary' : 'default'} variant={selectedSubject === subj ? 'filled' : 'outlined'} size="small" />
          ))}
        </Box>

        {pathNodes.length > 0 ? (
          pathViewMode === 'graph' ? (
            <SkillGraphView subject={selectedSubject} />
          ) : (
            <ModernLearningPathVisualizer nodes={pathNodes} connections={generateConnections(pathNodes)} currentNodeId={currentNodeId} onNodeClick={handleNodeClick} viewMode="tree" />
          )
        ) : (
          <GlassCard glassIntensity="light">
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Timeline sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">Henüz öğrenme yolu oluşturulmamış</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>Sınav sonuçlarınıza göre kişiselleştirilmiş yolunuz oluşturulacak</Typography>
            </Box>
          </GlassCard>
        )}
      </motion.div>
    </AnimatePresence>
  );
};
