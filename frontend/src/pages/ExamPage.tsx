/**
 * Ana Sınav Sayfası - Modern Tasarım
 * Glassmorphism ile sınav başlatma ve arayüz yönetimi
 */
import { Home, Refresh } from '@mui/icons-material';
import {
  Box,
  Container,
  Alert,
  Typography,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import * as React from 'react';
import {  useState, useEffect  } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';

import { ModernExamResults } from '../components/Exam/ModernExamResults';
import { ModernExamStart } from '../components/Exam/ModernExamStart';
import { ModernOSYMExamInterface } from '../components/Exam/ModernOSYMExamInterface';
import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { ModernLoader } from '../components/ui/ModernLoader';
import { examService, ExamType, ExamStatus, ExamSessionResponse } from '../services/examService';
import modernColors from '../theme/modern-colors';

export const ExamPage: React.FC = () => {
  const { sinavId: sessionId } = useParams<{ sinavId?: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // State yönetimi
  const [currentView, setCurrentView] = useState<'start' | 'exam' | 'results'>('start');
  const [_session, setSession] = useState<ExamSessionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [examType, setExamType] = useState<ExamType>(ExamType.TYT);

  /**
   * Sayfa yüklendiğinde durumu kontrol et
   */
  useEffect(() => {
    initializePage();
  }, [sessionId]);

  /**
   * Sayfa başlatma
   */
  const initializePage = async () => {
    try {
      setLoading(true);
      setError(null);

      // URL'den sınav türünü al
      const examTypeParam = searchParams.get('type') as ExamType;
      if (examTypeParam && Object.values(ExamType).includes(examTypeParam)) {
        setExamType(examTypeParam);
      }

      // Eğer session ID'si varsa, mevcut oturumu kontrol et
      if (sessionId) {
        try {
          const sessionData = await examService.getExamSession(sessionId);
          setSession(sessionData);

          // Sınav durumuna göre view belirle
          if (sessionData.status === ExamStatus.COMPLETED) {
            navigate(`/exam/${sessionId}/results`, { replace: true });
            return;
          } else if (sessionData.status === ExamStatus.IN_PROGRESS) {
            setCurrentView('exam');
          } else if (sessionData.status === ExamStatus.NOT_STARTED) {
            // Session oluşturulmuş ama başlatılmamış — checklist göster
            setCurrentView('start');
          } else {
            setCurrentView('start');
          }
        } catch (err) {
          console.error('Sınav oturumu bulunamadı:', err);
          setCurrentView('start');
        }
      } else {
        // Yeni sınav başlatma
        setCurrentView('start');
      }
    } catch (err: any) {
      setError(err.message || 'Sayfa yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Sınav başlatıldığında
   */
  const handleExamStart = (newSessionId: string) => {
    // URL'yi güncelle
    navigate(`/exam/${newSessionId}`, { replace: true });
    setCurrentView('exam');
  };

  /**
   * Sınavdan çıkış
   */
  const handleExamExit = () => {
    navigate('/dashboard');
  };

  /**
   * Sınav tekrar çözme
   */
  const handleRetakeExam = () => {
    setCurrentView('start');
    setSession(null);
    navigate(`/exam?type=${examType}`, { replace: true });
  };

  /**
   * Ana sayfaya dön
   */
  const handleGoHome = () => {
    navigate('/dashboard');
  };

  // Loading durumu
  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.primary,
        }}
      >
        <ModernLoader message="Sınav yükleniyor..." size="large" />
      </Box>
    );
  }

  // Hata durumu
  if (error) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.primary,
          p: 2,
        }}
      >
        <Container maxWidth="sm">
          <GlassCard glassIntensity="medium" elevated>
            <Alert severity="error" sx={{ mb: 3 }}>
              <Typography variant="h6">Hata</Typography>
              <Typography>{error}</Typography>
            </Alert>

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
              <ModernButton
                variant="glass"
                icon={<Refresh />}
                onClick={initializePage}
              >
                Tekrar Dene
              </ModernButton>
              <ModernButton
                variant="gradient"
                gradient={modernColors.gradients.primary}
                icon={<Home />}
                onClick={handleGoHome}
              >
                Ana Sayfa
              </ModernButton>
            </Box>
          </GlassCard>
        </Container>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <AnimatePresence mode="wait">
        {currentView === 'start' && (
          <motion.div
            key="start"
            initial={{ opacity: 0, x: -100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 100 }}
            transition={{ duration: 0.3 }}
          >
            <ModernExamStart
              examType={examType}
              sessionId={sessionId}
              onStart={handleExamStart}
              onCancel={handleExamExit}
            />
          </motion.div>
        )}

        {currentView === 'exam' && sessionId && (
          <motion.div
            key="exam"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.05 }}
            transition={{ duration: 0.3 }}
          >
            <ModernOSYMExamInterface
              sessionId={sessionId}
              onExit={handleExamExit}
            />
          </motion.div>
        )}

        {currentView === 'results' && sessionId && (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 100 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -100 }}
            transition={{ duration: 0.3 }}
          >
            <ModernExamResults
              sessionId={sessionId}
              onRetake={handleRetakeExam}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </Box>
  );
};

export default ExamPage;