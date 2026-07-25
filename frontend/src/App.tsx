import { CssBaseline } from '@mui/material';
import { ThemeProvider } from '@mui/material/styles';
import { lazy, Suspense, useEffect } from 'react';
import { QueryClientProvider } from 'react-query';
import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom';

import { PageTransition } from './components/Animations/PageTransition';
import { useAccessibilityStyles } from './hooks/useAccessibilityStyles';
import { ProtectedRoute } from './components/Auth/ProtectedRoute';
import { AccessibilityProvider } from './components/Common/AccessibilityProvider';
import ErrorBoundary from './components/Common/ErrorBoundary';
import { PageSkeleton } from './components/Common/PageSkeleton';
import { RoleBasedLayout } from './components/Layout/RoleBasedLayout';
import { OfflineIndicator, PWAInstallButton } from './components/PWAStatus';
import { AuthProvider } from './context/AuthProvider';
import KiroLoginRoute from './kiro/routes/KiroLoginRoute'; // F4-S1a/A2.2b: kademeli-swap → kiro GirisPage (live, eager — entry page)
import { Modern404Page } from './pages/Modern404Page';
import { ModernErrorPage } from './pages/ModernErrorPage';
import { ModernRegisterPage as RegisterPage } from './pages/ModernRegisterPage';
import { VeliOnayPage } from './pages/VeliOnayPage';
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
const InteraktifCozumPage = lazy(() => import('./kiro/screens/InteraktifCozumPage')); // F4-S2: yeni rota — saf istemci-matematik, backend/store YOK

// Pages - Teacher (lazy-loaded)
const TeacherDashboardPage = lazy(() => import('./pages/ModernTeacherDashboard'));
const TeacherClassesPage = lazy(() => import('./pages/ModernTeacherClassesPage'));
const TeacherStudentsPage = lazy(() => import('./pages/ModernTeacherStudentsPage'));
const TeacherExamsPage = lazy(() => import('./pages/ModernTeacherExamsPage'));
const TeacherAssignmentsPage = lazy(() => import('./pages/ModernTeacherAssignmentsPage'));
const TeacherReportsPage = lazy(() => import('./pages/ModernTeacherReportsPage'));
const TeacherContentPage = lazy(() => import('./pages/ModernTeacherContentPage'));

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

    // PWA Service Worker kaydı
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
          .then((registration) => {
            console.warn('SW registered: ', registration);

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
                <PageTransition variant="fadeUp">
                  <Suspense fallback={<PageSkeleton />}>
                    <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<KiroLoginRoute />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/veli-onay" element={<VeliOnayPage />} />
              <Route path="/unauthorized" element={<UnauthorizedPage />} />
              <Route path="/404" element={<Modern404Page />} />
              <Route path="/error" element={<ModernErrorPage />} />
              {/* S179 fix (F-P0-2): Turkish `/veli-takip` route deprecated.
                  Canonical English route is `/parent/dashboard`; keep an
                  HTTP redirect so existing bookmarks/notification links
                  still land on the right page. See .claude/rules/path-naming.md. */}
              <Route path="/veli-takip" element={<Navigate to="/parent/dashboard" replace />} />

              {/* Student Routes */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <StudentDashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/chat"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <ChatPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/sokratik"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <SokratikAIPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/offline"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <CevrimdisiPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/interaktif-cozum"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <InteraktifCozumPage />
                  </ProtectedRoute>
                }
              />
              {/* Exam Routes */}
              <Route
                path="/exam/start"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <ExamStartPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/exam/history"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <ExamHistoryPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/exam/:sinavId"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <ExamPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/exam/:sinavId/results"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <ExamResultsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/exams"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <ExamHistoryPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/photo-ask"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <PhotoAskPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/assessment"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <PlacementAssessmentPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/cat"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <CATPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/estimate"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <YKSEstimatePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/fsrs-review"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <FSRSReviewPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/league"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <LeaguePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/duel"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <DuelPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/daily-plan"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <DailyPlanPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/learning-path-map"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <LearningPathMapPage />
                  </ProtectedRoute>
                }
              />
              {/* S179 fix (F-P0-2): `/parent-new` deprecated alongside
                  `/veli-takip`. Redirect to canonical `/parent/dashboard`. */}
              <Route path="/parent-new" element={<Navigate to="/parent/dashboard" replace />} />
              <Route
                path="/oba"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <ObaPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/daily-quests"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <DailyQuestPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/boss-fight/:realmSlug"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <BossFightPage />
                  </ProtectedRoute>
                }
              />
              {/* Social Features (F0-F6) */}
              <Route
                path="/social"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <SocialHubPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/soru-meydani"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <SoruMeydaniPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/pomodoro"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <PomodoroPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/birlikte-streak"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <BirlikteStreakPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/usta-cirak"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <UstaCirakPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/cozum-duellosu"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <CozumDuellosuPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/oba-seferleri"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <ObaSeferleriPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/kiro-destan"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <KiroDestanPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/calibration"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <CalibrationStatusPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/leagues"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <LeaguePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/learning-path"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci']}>
                    <LearningPathPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/profile"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'ogretmen', 'veli', 'admin']}>
                    <ProfilePage />
                  </ProtectedRoute>
                }
              />

              {/* Teacher Routes */}
              <Route
                path="/teacher/dashboard"
                element={
                  <ProtectedRoute requiredRoles={['ogretmen']}>
                    <TeacherDashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/classes"
                element={
                  <ProtectedRoute requiredRoles={['ogretmen']}>
                    <TeacherClassesPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/students"
                element={
                  <ProtectedRoute requiredRoles={['ogretmen']}>
                    <TeacherStudentsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/exams"
                element={
                  <ProtectedRoute requiredRoles={['ogretmen']}>
                    <TeacherExamsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/assignments"
                element={
                  <ProtectedRoute requiredRoles={['ogretmen']}>
                    <TeacherAssignmentsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/reports"
                element={
                  <ProtectedRoute requiredRoles={['ogretmen']}>
                    <TeacherReportsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/content"
                element={
                  <ProtectedRoute requiredRoles={['ogretmen']}>
                    <TeacherContentPage />
                  </ProtectedRoute>
                }
              />

              {/* Parent Routes */}
              <Route
                path="/parent/dashboard"
                element={
                  <ProtectedRoute requiredRoles={['veli']}>
                    <ParentDashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/parent/children"
                element={
                  <ProtectedRoute requiredRoles={['veli']}>
                    <ParentChildrenPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/parent/reports"
                element={
                  <ProtectedRoute requiredRoles={['veli']}>
                    <ParentReportsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/parent/notifications"
                element={
                  <ProtectedRoute requiredRoles={['veli']}>
                    <ParentNotificationsPage />
                  </ProtectedRoute>
                }
              />

              {/* Admin Routes */}
              <Route
                path="/admin/dashboard"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <AdminDashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/panel"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <AdminPanel />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/users"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <AdminUsersPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/content"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <AdminContentPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/settings"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <AdminSettingsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/organizasyon"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <OrgOnboardingPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/osym-generator"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <OSYMQuestionGeneratorPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/yolo-detection"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <YOLODetectionPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/token-dashboard"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <TokenOptimizationDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/ab-test-results"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <ABTestResultsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/curator"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <CuratorPage />
                  </ProtectedRoute>
                }
              />

              {/* Labs: Experimental Features */}
              <Route
                path="/admin/labs"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <RevolutionaryDashboard />
                  </ProtectedRoute>
                }
              />

              {/* Systematic Debugging Workstation */}
              <Route
                path="/admin/debug"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <SystematicDebuggingPage />
                  </ProtectedRoute>
                }
              />

              {/* Question Upload - YOLO AI Detection */}
              <Route
                path="/question-upload"
                element={
                  <ProtectedRoute requiredRoles={['admin', 'ogretmen']}>
                    <QuestionUploadPage />
                  </ProtectedRoute>
                }
              />

              {/* Settings Route - All authenticated users */}
              <Route
                path="/settings"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'ogretmen', 'veli', 'admin']}>
                    <SettingsPage />
                  </ProtectedRoute>
                }
              />

              {/* RBAC Test Route - Admin only */}
              <Route
                path="/rbac-test"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <RBACTestPage />
                  </ProtectedRoute>
                }
              />

              {/* Accessibility Demo - Public for testing */}
              <Route
                path="/accessibility-demo"
                element={<AccessibilityDemoPage />}
              />

              {/* FAZ-5: Realm Map */}
              <Route
                path="/realms"
                element={
                  <ProtectedRoute requiredRoles={['ogrenci', 'admin']}>
                    <RealmPage />
                  </ProtectedRoute>
                }
              />

              {/* Default redirects */}
              <Route path="/" element={<Navigate to="/login" replace />} />
              <Route path="*" element={<Navigate to="/404" replace />} />
                    </Routes>
                  </Suspense>
                </PageTransition>
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

