import { CssBaseline } from '@mui/material';
import { ThemeProvider } from '@mui/material/styles';
import { lazy, Suspense, useEffect } from 'react';
import { QueryClientProvider } from 'react-query';
import { BrowserRouter as Router, Navigate, Route } from 'react-router-dom';
import { AnimatedRoutes } from './components/Animations/AnimatedRoutes';

import { PageTransition } from './components/Animations/PageTransition';
import { useAccessibilityStyles } from './hooks/useAccessibilityStyles';
import { ProtectedRoute } from './components/Auth/ProtectedRoute';
import { AccessibilityProvider } from './components/Common/AccessibilityProvider';
import ErrorBoundary from './components/Common/ErrorBoundary';
import { PageSkeleton } from './components/Common/PageSkeleton';
import { RoleBasedLayout } from './components/Layout/RoleBasedLayout';
import { OfflineIndicator, PWAInstallButton } from './components/PWAStatus';
import { AuthProvider } from './context/AuthProvider';
import { GlobalCognitiveWrapper } from './components/Cognitive/GlobalCognitiveWrapper';
import { SocraticAIAvatar } from './components/Cognitive/SocraticAIAvatar';
// F4-S1a/A2.2b: kademeli-swap → kiro GirisPage (live, eager — entry page).
// 7 Ağu 2026: çalışma ağacında ModernLoginPage'e geri alınmıştı; 05ccfae1f ile
// inen ürün kararı olduğu için geri getirildi (görev #419).
import KiroLoginRoute from './kiro/routes/KiroLoginRoute';
import { Modern404Page } from './pages/Modern404Page';
import { ModernErrorPage } from './pages/ModernErrorPage';
import { ModernRegisterPage as RegisterPage } from './pages/ModernRegisterPage';
import { VeliOnayPage } from './pages/VeliOnayPage';
import { EpostaDogrulaPage } from './pages/EpostaDogrulaPage';
import { UnauthorizedPage } from './pages/UnauthorizedPage';
// S179 (F-P0-2): ParentDashboard route now redirects to /parent/dashboard;
// no eager import needed. ParentDashboardPage (Modern) is still lazy.
import './styles/touch-optimized.css';
import { modernLightTheme as lightTheme } from './theme/modern-theme';
import {
  cleanupPerformanceTracking,
  createOptimizedQueryClient,
  initializePerformanceTracking,
} from './utils/performanceOptimizer.tsx';
import { initWebVitals, initWebVitalsFallback } from './utils/webVitals';

// ============================================
// LAZY-LOADED PAGES (Code Splitting)
// ============================================
// Only loaded when user navigates to that route
// Reduces initial bundle size by ~40-50%

// Pages - Student (lazy-loaded)
const StudentDashboardPage = lazy(() => import('./pages/ModernStudentDashboard'));
const ChatPage = lazy(() => import('./kiro/routes/KiroAISohbetRoute')); // F4-S1b: kademeli-swap → kiro AI Sohbet (live)
const CevrimdisiPage = lazy(() => import('./kiro/screens/CevrimdisiPage')); // F4-S2: yeni rota (backend artik calisiyor)
const SokratikAIPage = lazy(() => import('./kiro/routes/KiroSokratikRoute')); // F4-S1b: yeni rota (App'te karşılığı yok)
const YerlestirmePage = lazy(() => import('./kiro/screens/AdaptifTestPage')); // F4: yeni rota — CAT yerlestirme (/cat ders-secimi DOKUNULMADI)
const InteraktifCozumPage = lazy(() => import('./kiro/screens/InteraktifCozumPage')); // F4-S2: yeni rota — saf istemci-matematik, backend/store YOK
const VeliPaneliPage = lazy(() => import('./kiro/screens/VeliPaneliPage')); // F4-S2: yeni rota — getVeliDashboard canlı, VeliBaglamaPage'den bağımsız (o mimari-blokeli, ayrı karar)
const HesapKurtarmaPage = lazy(() => import('./kiro/screens/HesapKurtarmaPage')); // blocker #1: ekran + testleri vardı ama HİÇ mount edilmemişti — GirisPage'in "şifremi unuttum" linki ölüydü

// Pages - Teacher (lazy-loaded)
const TeacherDashboardPage = lazy(() => import('./pages/ModernTeacherDashboard'));
const TeacherClassesPage = lazy(() => import('./pages/ModernTeacherClassesPage'));
const TeacherStudentsPage = lazy(() => import('./pages/ModernTeacherStudentsPage'));
const TeacherExamsPage = lazy(() => import('./pages/ModernTeacherExamsPage'));
const TeacherAssignmentsPage = lazy(() => import('./pages/ModernTeacherAssignmentsPage'));
const TeacherReportsPage = lazy(() => import('./pages/ModernTeacherReportsPage'));
const TeacherContentPage = lazy(() => import('./pages/ModernTeacherContentPage'));
const TeacherCoPilotPage = lazy(() => import('./pages/ModernTeacherCoPilotPage'));

// Pages - Parent (lazy-loaded)
const ParentDashboardPage = lazy(() => import('./pages/ModernParentDashboard'));
const ParentChildrenPage = lazy(() => import('./pages/ModernParentChildrenPage'));
const ParentReportsPage = lazy(() => import('./pages/ModernParentReportsPage'));
const ParentNotificationsPage = lazy(() => import('./pages/ModernParentNotificationsPage'));

// Pages - Admin (lazy-loaded)
const AdminDashboardPage = lazy(() => import('./pages/ModernAdminDashboard'));
const AdminPanel = lazy(() => import('./components/Admin/AdminPanel'));
const AdminUsersPage = lazy(() => import('./pages/ModernAdminUsersPage'));
const AdminContentPage = lazy(() => import('./pages/ModernAdminContentPage'));
const AdminSettingsPage = lazy(() => import('./pages/ModernAdminSettingsPage'));
const OrgOnboardingPage = lazy(() => import('./pages/ModernOrgOnboardingPage'));
const OSYMQuestionGeneratorPage = lazy(() => import('./pages/OSYMQuestionGeneratorPage'));
const TokenOptimizationDashboard = lazy(() => import('./pages/TokenOptimizationDashboard'));
const ABTestResultsPage = lazy(() => import('./pages/ABTestResultsPage'));
const CuratorPage = lazy(() => import('./pages/Admin/CuratorPage'));

// Pages - Question Upload (YOLO)
const QuestionUploadPage = lazy(() => import('./pages/QuestionUploadPage'));
const YOLODetectionPage = lazy(() => import('./pages/YOLODetectionPage'));

// Pages - Exam (lazy-loaded)
const ExamStartPage = lazy(() => import('./pages/ModernExamStartPage'));
const ExamPage = lazy(() => import('./pages/ExamPage'));
const ExamHistoryPage = lazy(() => import('./pages/ModernExamHistoryPage'));
const ExamResultsPage = lazy(() => import('./pages/ModernExamResultsPage'));

// Pages - Common (lazy-loaded)
const ProfilePage = lazy(() => import('./pages/ModernProfilePage'));
const SettingsPage = lazy(() => import('./pages/ModernSettingsPage'));
const RBACTestPage = lazy(() => import('./pages/RBACTestPage'));
const AccessibilityDemoPage = lazy(() => import('./pages/AccessibilityDemoPage'));
const LearningPathPage = lazy(() => import('./pages/ModernLearningPathPage'));

// Pages - New Features (F3, F5)
const PhotoAskPage = lazy(() => import('./pages/PhotoAskPage'));
const PlacementAssessmentPage = lazy(() => import('./pages/PlacementAssessmentPage'));
const CATPage = lazy(() => import('./pages/CATPage'));

// FAZ-5: Realm Map
const RealmPage = lazy(() => import('./pages/RealmPage'));

// YKS Tahmin Sayfası
const YKSEstimatePage = lazy(() => import('./pages/YKSEstimatePage'));

// FSRS Tekrar Sayfası
const FSRSReviewPage = lazy(() => import('./pages/FSRSReviewPage'));
// Lig + Duel + KIRO Destanı + Kalibrasyon
const LeaguePage            = lazy(() => import('./pages/LeaguePage'));
const DuelPage              = lazy(() => import('./kiro/screens/DuelloPage')); // F4-S1: kademeli-swap → kiro DuelloPage (live)
const KiroDestanPage        = lazy(() => import('./pages/KiroDestanPage'));
const CalibrationStatusPage = lazy(() => import('./pages/CalibrationStatusPage'));
// Learning Path Daily + Map (ZPD+DAG+IRT+FSRS)
const DailyPlanPage         = lazy(() => import('./pages/DailyPlanPage'));
const LearningPathMapPage   = lazy(() => import('./pages/LearningPathMapPage'));
// Veli Paneli (yeni) — kept as lazy import for future route wiring (#258 spec)
// const ParentDashboardNew    = lazy(() => import('./pages/ParentDashboardNew'));
// Oba (Guild) + Daily Quests + Boss Fight
const ObaPage               = lazy(() => import('./pages/ObaPage'));
const DailyQuestPage        = lazy(() => import('./pages/DailyQuestPage'));
const BossFightPage         = lazy(() => import('./pages/BossFightPage'));

// Yeni Eklenen Rotalar
const HaftalikPlanPage      = lazy(() => import('./kiro/screens/HaftalikPlanPage'));
const SoruCozmePage         = lazy(() => import('./kiro/screens/SoruCozmePage'));
// Social Features (F0-F6)
const SocialHubPage         = lazy(() => import('./pages/SocialHubPage'));
const SoruMeydaniPage       = lazy(() => import('./pages/SoruMeydaniPage'));
const PomodoroPage          = lazy(() => import('./pages/PomodoroPage'));
const BirlikteStreakPage    = lazy(() => import('./pages/BirlikteStreakPage'));
const UstaCirakPage         = lazy(() => import('./pages/UstaCirakPage'));
const CozumDuellosuPage     = lazy(() => import('./pages/CozumDuellosuPage'));
const ObaSeferleriPage      = lazy(() => import('./pages/ObaSeferleriPage'));

// Labs: Revolutionary Features (experimental)
const RevolutionaryDashboard = lazy(() => import('./components/Revolutionary/RevolutionaryDashboard'));
const SystematicDebuggingPage = lazy(() => import('./pages/SystematicDebuggingPage'));
// Optimize edilmiş QueryClient
const queryClient = createOptimizedQueryClient();

// Performance optimized App component
function AppContent() {
  // Sync accessibility prefs (fontSize, lineHeight, highContrast) to CSS vars
  useAccessibilityStyles();

  useEffect(() => {
    // Performance tracking'i başlat
    initializePerformanceTracking();

    // Web Vitals monitoring'i başlat
    initWebVitals().catch(() => {
      // Fallback to PerformanceObserver if web-vitals library not available
      console.warn('[Web Vitals] Using fallback implementation');
      initWebVitalsFallback();
    });

    // PWA Service Worker kaydı (Geliştirme ortamında dev cache engellemek için unregister et, sadece production'da kaydet)
    if ('serviceWorker' in navigator) {
      if (import.meta.env.DEV) {
        // Geliştirici ortamında önbellekleme takılmasını (stale cache) önlemek için var olan SW kayıtlarını temizle
        navigator.serviceWorker.getRegistrations().then((registrations) => {
          for (const registration of registrations) {
            registration.unregister().then((unregistered) => {
              if (unregistered) {
                console.info('[PWA Dev] Active Service Worker unregistered for development HMR stability.');
              }
            });
          }
        }).catch((err) => {
          console.warn('[PWA Dev] Failed to query SW registrations:', err);
        });
      } else {
        window.addEventListener('load', () => {
          navigator.serviceWorker.register('/sw.js')
            .then((registration) => {
              console.info('SW registered: ', registration);

              // Yeni SW aktif olduğunda sayfayı otomatik yenile (stale cache önleme)
              registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                if (newWorker) {
                  newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'activated' && navigator.serviceWorker.controller) {
                      // Sonsuz döngü koruması: 10s içinde tekrar reload engelle
                      const lastReload = sessionStorage.getItem('sw-reload-ts');
                      if (lastReload && Date.now() - Number(lastReload) < 10000) {return;}
                      sessionStorage.setItem('sw-reload-ts', String(Date.now()));
                      window.location.reload();
                    }
                  });
                }
              });
            })
            .catch((registrationError) => {
              console.error('SW registration failed: ', registrationError);
            });
        });
      }
    }

    // Cleanup function
    return () => {
      cleanupPerformanceTracking();
    };
  }, []);

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // Log to error reporting service (Sentry, LogRocket, etc.)
        console.error('Application Error:', error, errorInfo);

        // Send to analytics
        const analyticsWindow = window as Window & {
          gtag?: (...args: unknown[]) => void;
        };

        if (typeof window !== 'undefined' && analyticsWindow.gtag) {
          analyticsWindow.gtag('event', 'exception', {
            description: error.message,
            fatal: true,
          });
        }
      }}
    >
      <ThemeProvider theme={lightTheme}>
        <CssBaseline />
        <GlobalCognitiveWrapper />
        <SocraticAIAvatar
          message="Merhaba, ben Kiro! Sana doğrudan cevabı vermek yerine, doğru yolu bulman için buradayım. Bir soruda takılırsan bana tıklayabilirsin."
          state="idle"
        />
        {/*
         * S179 fix (F-P0-3): Mount AccessibilityProvider so any consumer
         * of useAccessibility() throws no longer at runtime. Provider was
         * defined but never reached the tree in production.
         */}
        <AccessibilityProvider>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <Router>
              {/* PWA Components */}
              <OfflineIndicator />
              <PWAInstallButton />

              <RoleBasedLayout>
                <Suspense fallback={<PageSkeleton />}>
                    <AnimatedRoutes>
              {/* Public Routes */}
              <Route path="/login" element={<PageTransition><KiroLoginRoute /></PageTransition>} />
              <Route path="/register" element={<PageTransition><RegisterPage /></PageTransition>} />
              <Route path="/veli-onay" element={<PageTransition><VeliOnayPage /></PageTransition>} />
              {/* L2 — A1 altın yolunun ikinci ayağı. Backend e-postaya
                  {FRONTEND_URL}/eposta-dogrula?token=... linkini koyuyor
                  (core/eposta_dogrulama.py); bu rota olmadan link 404 verir. */}
              <Route path="/eposta-dogrula" element={<PageTransition><EpostaDogrulaPage /></PageTransition>} />
              {/* Şifre kurtarma (blocker #1). GirisPage:337 zaten buraya link
                  veriyordu ama rota kayıtlı değildi. ModernLoginPage:430 ise
                  /forgot-password diyor — o da ölü linkti, yönlendiriyoruz
                  (bkz. /veli-takip deseni, .claude/rules/path-naming.md). */}
              <Route path="/hesap-kurtarma" element={<PageTransition><HesapKurtarmaPage /></PageTransition>} />
              <Route path="/forgot-password" element={<Navigate to="/hesap-kurtarma" replace />} />
              <Route path="/unauthorized" element={<PageTransition><UnauthorizedPage /></PageTransition>} />
              <Route path="/404" element={<PageTransition><Modern404Page /></PageTransition>} />
              <Route path="/error" element={<PageTransition><ModernErrorPage /></PageTransition>} />
              {/* S179 fix (F-P0-2): Turkish `/veli-takip` route deprecated.
                  Canonical English route is `/parent/dashboard`; keep an
                  HTTP redirect so existing bookmarks/notification links
                  still land on the right page. See .claude/rules/path-naming.md. */}
              <Route path="/veli-takip" element={<Navigate to="/parent/dashboard" replace />} />

              {/* Student Routes */}
              <Route
                path="/dashboard"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <StudentDashboardPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/chat"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <ChatPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/sokratik"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <SokratikAIPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/offline"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <CevrimdisiPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/yerlestirme"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <YerlestirmePage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/interaktif-cozum"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <InteraktifCozumPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              {/* Exam Routes */}
              <Route
                path="/exam/start"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <ExamStartPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/exam/history"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <ExamHistoryPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/exam/:sinavId"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <ExamPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/exam/:sinavId/results"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <ExamResultsPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/exams"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <ExamHistoryPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/photo-ask"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <PhotoAskPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/assessment"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <PlacementAssessmentPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/cat"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <CATPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/estimate"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <YKSEstimatePage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/fsrs-review"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <FSRSReviewPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/league"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <LeaguePage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/duel"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <DuelPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/daily-plan"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <DailyPlanPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/weekly-plan"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <HaftalikPlanPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/soru-cozme"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <SoruCozmePage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/learning-path-map"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <LearningPathMapPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              {/* S179 fix (F-P0-2): `/parent-new` deprecated alongside
                  `/veli-takip`. Redirect to canonical `/parent/dashboard`. */}
              <Route path="/parent-new" element={<Navigate to="/parent/dashboard" replace />} />
              <Route
                path="/oba"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <ObaPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/daily-quests"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <DailyQuestPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/boss-fight/:realmSlug"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <BossFightPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              {/* Social Features (F0-F6) */}
              <Route
                path="/social"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <SocialHubPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/soru-meydani"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <SoruMeydaniPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/pomodoro"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <PomodoroPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/birlikte-streak"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <BirlikteStreakPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/usta-cirak"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <UstaCirakPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/cozum-duellosu"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <CozumDuellosuPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/oba-seferleri"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <ObaSeferleriPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/kiro-destan"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <KiroDestanPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/admin/calibration"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin']}>
                    <CalibrationStatusPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/leagues"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <LeaguePage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/learning-path"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <LearningPathPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/profile"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'ogretmen', 'veli', 'admin']}>
                    <ProfilePage />
                  </ProtectedRoute>
                </PageTransition>}
              />

              {/* Teacher Routes */}
              <Route
                path="/teacher/dashboard"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogretmen']}>
                    <TeacherDashboardPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/teacher/classes"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogretmen']}>
                    <TeacherClassesPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/teacher/students"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogretmen']}>
                    <TeacherStudentsPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/teacher/exams"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogretmen']}>
                    <TeacherExamsPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/teacher/assignments"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogretmen']}>
                    <TeacherAssignmentsPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/teacher/reports"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogretmen']}>
                    <TeacherReportsPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/teacher/content"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogretmen']}>
                    <TeacherContentPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/teacher/copilot"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogretmen']}>
                    <TeacherCoPilotPage />
                  </ProtectedRoute>
                </PageTransition>}
              />

              {/* Parent Routes */}
              <Route
                path="/veli"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['veli']}>
                    <VeliPaneliPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/parent/dashboard"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['veli']}>
                    <ParentDashboardPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/parent/children"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['veli']}>
                    <ParentChildrenPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/parent/reports"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['veli']}>
                    <ParentReportsPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/parent/notifications"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['veli']}>
                    <ParentNotificationsPage />
                  </ProtectedRoute>
                </PageTransition>}
              />

              {/* Admin Routes */}
              <Route
                path="/admin/dashboard"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin']}>
                    <AdminDashboardPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/admin/panel"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin']}>
                    <AdminPanel />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/admin/users"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin']}>
                    <AdminUsersPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/admin/content"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin']}>
                    <AdminContentPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/admin/settings"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin']}>
                    <AdminSettingsPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/admin/organizasyon"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin']}>
                    <OrgOnboardingPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/admin/osym-generator"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin']}>
                    <OSYMQuestionGeneratorPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/admin/yolo-detection"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin']}>
                    <YOLODetectionPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/admin/token-dashboard"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin']}>
                    <TokenOptimizationDashboard />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/admin/ab-test-results"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin']}>
                    <ABTestResultsPage />
                  </ProtectedRoute>
                </PageTransition>}
              />
              <Route
                path="/admin/curator"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin']}>
                    <CuratorPage />
                  </ProtectedRoute>
                </PageTransition>}
              />

              {/* Labs: Experimental Features */}
              <Route
                path="/admin/labs"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin']}>
                    <RevolutionaryDashboard />
                  </ProtectedRoute>
                </PageTransition>}
              />

              {/* Systematic Debugging Workstation */}
              <Route
                path="/admin/debug"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin']}>
                    <SystematicDebuggingPage />
                  </ProtectedRoute>
                </PageTransition>}
              />

              {/* Question Upload - YOLO AI Detection */}
              <Route
                path="/question-upload"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin', 'ogretmen']}>
                    <QuestionUploadPage />
                  </ProtectedRoute>
                </PageTransition>}
              />

              {/* Settings Route - All authenticated users */}
              <Route
                path="/settings"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'ogretmen', 'veli', 'admin']}>
                    <SettingsPage />
                  </ProtectedRoute>
                </PageTransition>}
              />

              {/* RBAC Test Route - Admin only */}
              <Route
                path="/rbac-test"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['admin']}>
                    <RBACTestPage />
                  </ProtectedRoute>
                </PageTransition>}
              />

              {/* Accessibility Demo - Public for testing */}
              <Route
                path="/accessibility-demo"
                element={<PageTransition><AccessibilityDemoPage /></PageTransition>}
              />

              {/* FAZ-5: Realm Map */}
              <Route
                path="/realms"
                element={<PageTransition>
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <RealmPage />
                  </ProtectedRoute>
                </PageTransition>}
              />

              {/* Default redirects */}
              <Route path="/" element={<Navigate to="/login" replace />} />
              <Route path="*" element={<Navigate to="/404" replace />} />
                    </AnimatedRoutes>
                  </Suspense>
              </RoleBasedLayout>
            </Router>
          </AuthProvider>
        </QueryClientProvider>
        </AccessibilityProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export function App() {
  return <AppContent />;
}

/**
 * PHASE 4 - SESSION 4: ROUTE-BASED CODE SPLITTING ✅
 *
 * Optimizations Applied:
 * ✅ Converted 28 page components to lazy loading (React.lazy)
 * ✅ Kept 3 auth pages eager-loaded (Login, Register, Unauthorized)
 * ✅ Created PageSkeleton component for better UX during loading
 * ✅ Updated Suspense fallback from LoadingSpinner to PageSkeleton
 *
 * Expected Impact:
 * - 40-50% reduction in initial bundle size
 * - Faster initial load time
 * - Better perceived performance with skeleton UI
 * - Pages load on-demand (first click: 100-200ms, cached after)
 *
 * Pages Lazy-Loaded:
 * - Student: 2 pages (Dashboard, Chat)
 * - Teacher: 7 pages (Dashboard, Classes, Students, Exams, Assignments, Reports, Content)
 * - Parent: 4 pages (Dashboard, Children, Reports, Notifications)
 * - Admin: 8 pages (Dashboard, Panel, Users, Content, Settings, OSYMGenerator, TokenDashboard, ABTestResults)
 * - Exam: 4 pages (Start, Exam, History, Results)
 * - Common: 5 pages (Profile, Settings, RBACTest, AccessibilityDemo, LearningPath)
 *
 * Total: 30 pages = 28 lazy-loaded + 2 refactored (LearningPathPage uses LearningPathPageRefactored)
 *
 * Date: November 14, 2025
 */
