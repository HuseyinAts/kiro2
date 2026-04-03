/**
 * Gelişmiş Sınav Sonuçları Bileşeni
 * Advanced Exam Results Component
 * IRT, Morfoloji, ZPD ve Hibrit Öğrenme Stili analizleri dahil
 */
import {
  Assessment,
  Science,
  Psychology,
  MenuBook,
  CompareArrows,
  Insights,
  Refresh,
} from '@mui/icons-material';
import {
  Box,
  Paper,
  Alert,
  CircularProgress,
  Typography,
  Tabs,
  Tab,
  Button,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { advancedReportsService, AdvancedExamReport } from '../../services/advancedReportsService';
import { examService } from '../../services/examService';
import { SinavSonucu, performanceToSinavSonucu } from '../../types';

// Import sub-components
import { BasicResultsTab } from './Results';
import { ComparisonTab } from './Results/ComparisonTab';
import { IRTMorphologyTab } from './Results/IRTMorphologyTab';
import { LearningStyleTab } from './Results/LearningStyleTab';
import { PerformanceTrendTab } from './Results/PerformanceTrendTab';
import { RecommendationsDialog } from './Results/RecommendationsDialog';
import { ResultsHeader } from './Results/ResultsHeader';
import { ZPDAnalysisTab } from './Results/ZPDAnalysisTab';

interface AdvancedExamResultsProps {
  sinavId: string;
  onRetake?: () => void;
}

export const AdvancedExamResults: React.FC<AdvancedExamResultsProps> = ({ sinavId, onRetake }) => {
  const [sonuc, setSonuc] = useState<SinavSonucu | null>(null);
  const [gelismisRapor, setGelismisRapor] = useState<AdvancedExamReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [pdfGenerating, setPdfGenerating] = useState(false);
  const [showRecommendations, setShowRecommendations] = useState(false);

  /**
   * Load exam results and advanced analysis
   */
  useEffect(() => {
    loadResults();
  }, [sinavId]);

  /**
   * Load exam results and advanced report
   */
  const loadResults = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load basic result and advanced report in parallel
      const [sonucData, gelismisRaporData] = await Promise.allSettled([
        examService.getExamResult(sinavId),
        advancedReportsService.getAdvancedExamReport(sinavId),
      ]);

      if (sonucData.status === 'fulfilled') {
        // Convert PerformanceResponse to SinavSonucu
        const convertedSonuc = performanceToSinavSonucu(sonucData.value, sinavId);
        setSonuc(convertedSonuc);
      } else {
        throw new Error('Temel sınav sonucu yüklenemedi');
      }

      if (gelismisRaporData.status === 'fulfilled') {
        setGelismisRapor(gelismisRaporData.value);
      } else {
        console.warn('Gelişmiş rapor yüklenemedi:', gelismisRaporData.reason);
      }

    } catch (err: any) {
      setError(err.message || 'Sonuçlar yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Generate and download PDF report
   */
  const handleGeneratePDF = async () => {
    try {
      setPdfGenerating(true);
      const result = await advancedReportsService.generatePDFReport(sinavId);

      // Wait for PDF generation (simple polling)
      setTimeout(async () => {
        try {
          const blob = await advancedReportsService.downloadPDFReport(result.pdf_filename);
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = result.pdf_filename;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        } catch (downloadError) {
          console.error('PDF indirme hatası:', downloadError);
        }
      }, 3000); // Wait 3 seconds

    } catch (err: any) {
      console.error('PDF oluşturma hatası:', err);
    } finally {
      setPdfGenerating(false);
    }
  };

  /**
   * Handle tab change
   */
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  /**
   * Handle show recommendations
   */
  const handleShowRecommendations = () => {
    setShowRecommendations(true);
  };

  /**
   * Handle close recommendations
   */
  const handleCloseRecommendations = () => {
    setShowRecommendations(false);
  };

  // Loading state
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Gelişmiş analiz yükleniyor...
        </Typography>
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        <Typography variant="h6">Hata</Typography>
        <Typography>{error}</Typography>
        <Button onClick={loadResults} startIcon={<Refresh />} sx={{ mt: 1 }}>
          Tekrar Dene
        </Button>
      </Alert>
    );
  }

  // No result state
  if (!sonuc) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        Sonuç bulunamadı
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <ResultsHeader
        sinavTipi={sonuc.sinav_tipi}
        hamPuan={sonuc.ham_puan}
        onGeneratePDF={handleGeneratePDF}
        onShowRecommendations={handleShowRecommendations}
        onRetake={onRetake}
        pdfGenerating={pdfGenerating}
      />

      {/* Tabs */}
      <Paper elevation={2} sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<Assessment />} label="Temel Sonuçlar" />
          <Tab icon={<Science />} label="IRT + Morfoloji" />
          <Tab icon={<Psychology />} label="ZPD Analizi" />
          <Tab icon={<MenuBook />} label="Öğrenme Stili" />
          <Tab icon={<CompareArrows />} label="ÖSYM/ETS Karşılaştırma" />
          <Tab icon={<Insights />} label="Performans Trendi" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {activeTab === 0 && <BasicResultsTab sonuc={sonuc} />}
          {activeTab === 1 && <IRTMorphologyTab analiz={gelismisRapor?.irt_morfoloji_analizi} />}
          {activeTab === 2 && <ZPDAnalysisTab analiz={gelismisRapor?.zpd_analizi} />}
          {activeTab === 3 && <LearningStyleTab analiz={gelismisRapor?.hibrit_ogrenme_stili_analizi} />}
          {activeTab === 4 && <ComparisonTab analiz={gelismisRapor?.osym_ets_karsilastirmasi} />}
          {activeTab === 5 && <PerformanceTrendTab trend={gelismisRapor?.performans_trendi} />}
        </Box>
      </Paper>

      {/* Recommendations Dialog */}
      <RecommendationsDialog
        open={showRecommendations}
        onClose={handleCloseRecommendations}
        oneriler={gelismisRapor?.kisisellestirilmis_oneriler}
        gelisimOnerileri={gelismisRapor?.gelisim_onerileri}
      />
    </Box>
  );
};

export default AdvancedExamResults;
