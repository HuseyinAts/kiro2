/**
 * Lazy Route Configuration - Task 58.1
 * Route-based code splitting for optimal bundle size
 */
import { lazyWithRetry, LoadingFallbacks } from '../utils/lazyLoad';

// ==================== AUTHENTICATION ROUTES ====================
export const LoginPage = lazyWithRetry(() => import('../pages/LoginPage'));
export const RegisterPage = lazyWithRetry(() => import('../pages/RegisterPage'));

// ==================== STUDENT ROUTES ====================
export const StudentDashboard = lazyWithRetry(() => import('../pages/StudentDashboard'));
export const ExamInterface = lazyWithRetry(() => import('../components/Exam/ExamInterface'));
export const OSYMExamInterface = lazyWithRetry(() => import('../components/Exam/OSYMExamInterface'));

// ==================== ACCESSIBILITY ROUTES ====================
export const ColorContrastSettingsPage = lazyWithRetry(() => import('../pages/ColorContrastSettingsPage'));
export const TypographySettingsPage = lazyWithRetry(() => import('../pages/TypographySettingsPage'));
export const DyscalculiaSupportPage = lazyWithRetry(() => import('../pages/DyscalculiaSupportPage'));

// ==================== MANIPULATIVES ====================
export const ManipulativesPage = lazyWithRetry(() => import('../components/Manipulatives/index'));

// ==================== TEACHER ROUTES ====================
export const TeacherDashboard = lazyWithRetry(() => import('../pages/TeacherDashboard'));
export const TeacherStudentsPage = lazyWithRetry(() => import('../pages/TeacherStudentsPage'));
export const TeacherExamsPage = lazyWithRetry(() => import('../pages/TeacherExamsPage'));
export const TeacherReportsPage = lazyWithRetry(() => import('../pages/TeacherReportsPage'));
export const TeacherAssignmentsPage = lazyWithRetry(() => import('../pages/TeacherAssignmentsPage'));
export const TeacherContentPage = lazyWithRetry(() => import('../pages/TeacherContentPage'));

// ==================== PARENT ROUTES ====================
export const ParentDashboard = lazyWithRetry(() => import('../pages/ParentDashboard'));
export const ParentReportsPage = lazyWithRetry(() => import('../pages/ParentReportsPage'));
export const ParentNotificationsPage = lazyWithRetry(() => import('../pages/ParentNotificationsPage'));

// ==================== ADMIN ROUTES ====================
export const AdminDashboard = lazyWithRetry(() => import('../pages/AdminDashboard'));
export const AdminUsersPage = lazyWithRetry(() => import('../pages/AdminUsersPage'));
export const AdminContentPage = lazyWithRetry(() => import('../pages/AdminContentPage'));
export const AdminSettingsPage = lazyWithRetry(() => import('../pages/AdminSettingsPage'));
export const ABTestResultsPage = lazyWithRetry(() => import('../pages/ABTestResultsPage'));
export const TokenOptimizationDashboard = lazyWithRetry(() => import('../pages/TokenOptimizationDashboard'));

// ==================== QUESTION GENERATION ====================
export const OSYMQuestionGeneratorPage = lazyWithRetry(() => import('../pages/OSYMQuestionGeneratorPage'));

// ==================== ROUTE CONFIGURATION ====================

export interface RouteConfig {
  path: string;
  component: React.LazyExoticComponent<any>;
  fallback?: React.ReactNode;
  preload?: boolean;
  roles?: string[]; // Access control
}

/**
 * Route definitions with lazy loading
 * Organized by user role and feature area
 */
export const routes: RouteConfig[] = [
  // Authentication (high priority - preload)
  {
    path: '/login',
    component: LoginPage,
    fallback: LoadingFallbacks.page,
    preload: true
  },
  {
    path: '/register',
    component: RegisterPage,
    fallback: LoadingFallbacks.page,
    preload: true
  },

  // Student Routes (high priority for students)
  {
    path: '/student/dashboard',
    component: StudentDashboard,
    fallback: LoadingFallbacks.dashboard,
    preload: true,
    roles: ['student']
  },
  {
    path: '/exam/:examId',
    component: ExamInterface,
    fallback: LoadingFallbacks.page,
    roles: ['student']
  },
  {
    path: '/osym-exam/:examId',
    component: OSYMExamInterface,
    fallback: LoadingFallbacks.page,
    roles: ['student']
  },

  // Accessibility Settings (load on demand)
  {
    path: '/settings/accessibility/color-contrast',
    component: ColorContrastSettingsPage,
    fallback: LoadingFallbacks.page
  },
  {
    path: '/settings/accessibility/typography',
    component: TypographySettingsPage,
    fallback: LoadingFallbacks.page
  },
  {
    path: '/accessibility/dyscalculia',
    component: DyscalculiaSupportPage,
    fallback: LoadingFallbacks.page
  },

  // Manipulatives (load on demand)
  {
    path: '/manipulatives',
    component: ManipulativesPage,
    fallback: LoadingFallbacks.page,
    roles: ['student']
  },

  // Teacher Routes
  {
    path: '/teacher/dashboard',
    component: TeacherDashboard,
    fallback: LoadingFallbacks.dashboard,
    preload: true,
    roles: ['teacher']
  },
  {
    path: '/teacher/students',
    component: TeacherStudentsPage,
    fallback: LoadingFallbacks.page,
    roles: ['teacher']
  },
  {
    path: '/teacher/exams',
    component: TeacherExamsPage,
    fallback: LoadingFallbacks.page,
    roles: ['teacher']
  },
  {
    path: '/teacher/reports',
    component: TeacherReportsPage,
    fallback: LoadingFallbacks.page,
    roles: ['teacher']
  },
  {
    path: '/teacher/assignments',
    component: TeacherAssignmentsPage,
    fallback: LoadingFallbacks.page,
    roles: ['teacher']
  },
  {
    path: '/teacher/content',
    component: TeacherContentPage,
    fallback: LoadingFallbacks.page,
    roles: ['teacher']
  },

  // Parent Routes
  {
    path: '/parent/dashboard',
    component: ParentDashboard,
    fallback: LoadingFallbacks.dashboard,
    preload: true,
    roles: ['parent']
  },
  {
    path: '/parent/reports',
    component: ParentReportsPage,
    fallback: LoadingFallbacks.page,
    roles: ['parent']
  },
  {
    path: '/parent/notifications',
    component: ParentNotificationsPage,
    fallback: LoadingFallbacks.page,
    roles: ['parent']
  },

  // Admin Routes
  {
    path: '/admin/dashboard',
    component: AdminDashboard,
    fallback: LoadingFallbacks.dashboard,
    preload: true,
    roles: ['admin']
  },
  {
    path: '/admin/users',
    component: AdminUsersPage,
    fallback: LoadingFallbacks.page,
    roles: ['admin']
  },
  {
    path: '/admin/content',
    component: AdminContentPage,
    fallback: LoadingFallbacks.page,
    roles: ['admin']
  },
  {
    path: '/admin/settings',
    component: AdminSettingsPage,
    fallback: LoadingFallbacks.page,
    roles: ['admin']
  },
  {
    path: '/admin/ab-tests',
    component: ABTestResultsPage,
    fallback: LoadingFallbacks.page,
    roles: ['admin']
  },
  {
    path: '/admin/token-optimization',
    component: TokenOptimizationDashboard,
    fallback: LoadingFallbacks.page,
    roles: ['admin']
  },

  // Question Generation (admin/teacher)
  {
    path: '/osym-generator',
    component: OSYMQuestionGeneratorPage,
    fallback: LoadingFallbacks.page,
    roles: ['admin', 'teacher']
  }
];

/**
 * Get routes by role
 * Filter routes based on user permissions
 */
export function getRoutesByRole(userRole: string): RouteConfig[] {
  return routes.filter(route =>
    !route.roles || route.roles.includes(userRole)
  );
}

/**
 * Preload critical routes
 * Call this after initial app load
 */
export function preloadCriticalRoutes(userRole?: string) {
  const criticalRoutes = routes.filter(r => r.preload);

  // Filter by role if provided
  const routesToPreload = userRole
    ? criticalRoutes.filter(r => !r.roles || r.roles.includes(userRole))
    : criticalRoutes;

  // Preload components after a short delay
  setTimeout(() => {
    routesToPreload.forEach(route => {
      const component = route.component as any;
      if (component._payload && component._payload._result === null) {
        component._payload._init(component._payload);
      }
    });
  }, 2000);
}
