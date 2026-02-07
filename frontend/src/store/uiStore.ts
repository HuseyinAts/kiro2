/**
 * UI Store (Zustand)
 *
 * Centralized UI state management
 * Manages modals, sidebars, notifications, and general UI state
 *
 * Features:
 * - Modal management (open/close/data)
 * - Sidebar/drawer state
 * - Toast notifications
 * - Loading states
 * - Theme mode (if not using MUI ThemeProvider)
 * - Breadcrumb navigation
 * - Page titles
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  message: string
  type: NotificationType
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
}

// ==============================================
// Discriminated Union Modal Types
// Type-safe modal data for different modal kinds
// ==============================================

/**
 * Modal Kinds - Discriminator for type-safe modal handling
 */
export type ModalKind =
  | 'confirmation'
  | 'form'
  | 'detail'
  | 'alert'
  | 'custom'

/**
 * Confirmation Modal Data
 * For delete, archive, submit confirmations
 */
export interface ConfirmationModalData {
  kind: 'confirmation'
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'warning' | 'info'
  onConfirm: () => void | Promise<void>
  onCancel?: () => void
}

/**
 * Form Modal Data
 * For create/edit forms with entity data
 */
export interface FormModalData<T = Record<string, unknown>> {
  kind: 'form'
  title: string
  mode: 'create' | 'edit' | 'view'
  entityType: string
  entityId?: string | number
  initialData?: T
  onSubmit?: (data: T) => void | Promise<void>
}

/**
 * Detail Modal Data
 * For viewing entity details
 */
export interface DetailModalData<T = Record<string, unknown>> {
  kind: 'detail'
  title: string
  entityType: string
  entityId: string | number
  data: T
  allowEdit?: boolean
  onEdit?: () => void
}

/**
 * Alert Modal Data
 * For notifications and messages
 */
export interface AlertModalData {
  kind: 'alert'
  title: string
  message: string
  variant: 'success' | 'error' | 'warning' | 'info'
  actions?: Array<{
    label: string
    onClick: () => void
    variant?: 'primary' | 'secondary'
  }>
}

/**
 * Custom Modal Data
 * For modals that don't fit other categories
 */
export interface CustomModalData<T = Record<string, unknown>> {
  kind: 'custom'
  componentId: string
  props?: T
}

/**
 * Union type for all modal data types
 */
export type ModalData =
  | ConfirmationModalData
  | FormModalData
  | DetailModalData
  | AlertModalData
  | CustomModalData

/**
 * Type-safe Modal interface with discriminated union
 */
export interface Modal<T extends ModalData = ModalData> {
  id: string
  isOpen: boolean
  data?: T
}

/**
 * Helper type guards for modal data
 */
export const isConfirmationModal = (data?: ModalData): data is ConfirmationModalData =>
  data?.kind === 'confirmation';

export const isFormModal = (data?: ModalData): data is FormModalData =>
  data?.kind === 'form';

export const isDetailModal = (data?: ModalData): data is DetailModalData =>
  data?.kind === 'detail';

export const isAlertModal = (data?: ModalData): data is AlertModalData =>
  data?.kind === 'alert';

export const isCustomModal = (data?: ModalData): data is CustomModalData =>
  data?.kind === 'custom';

export interface Breadcrumb {
  label: string
  path?: string
}

interface UIState {
  // Sidebar/Drawer
  sidebarOpen: boolean
  sidebarCollapsed: boolean
  mobileSidebarOpen: boolean

  // Modals
  modals: Record<string, Modal>

  // Notifications/Toasts
  toasts: Toast[]

  // Loading states
  globalLoading: boolean
  pageLoading: boolean

  // Navigation
  breadcrumbs: Breadcrumb[]
  pageTitle: string

  // Theme (optional - if not using MUI)
  isDarkMode: boolean

  // Fullscreen
  isFullscreen: boolean

  // Search
  searchOpen: boolean
  searchQuery: string
}

interface UIActions {
  // Sidebar actions
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  toggleSidebarCollapsed: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  toggleMobileSidebar: () => void
  setMobileSidebarOpen: (open: boolean) => void

  // Modal actions
  openModal: (id: string, data?: ModalData) => void
  openConfirmationModal: (id: string, data: Omit<ConfirmationModalData, 'kind'>) => void
  openFormModal: (id: string, data: Omit<FormModalData, 'kind'>) => void
  openDetailModal: (id: string, data: Omit<DetailModalData, 'kind'>) => void
  openAlertModal: (id: string, data: Omit<AlertModalData, 'kind'>) => void
  closeModal: (id: string) => void
  closeAllModals: () => void
  isModalOpen: (id: string) => boolean
  getModalData: (id: string) => ModalData | undefined

  // Toast/Notification actions
  showToast: (message: string, type?: NotificationType, duration?: number) => string
  showSuccess: (message: string, duration?: number) => string
  showError: (message: string, duration?: number) => string
  showWarning: (message: string, duration?: number) => string
  showInfo: (message: string, duration?: number) => string
  hideToast: (id: string) => void
  clearToasts: () => void

  // Loading actions
  setGlobalLoading: (loading: boolean) => void
  setPageLoading: (loading: boolean) => void

  // Navigation actions
  setBreadcrumbs: (breadcrumbs: Breadcrumb[]) => void
  setPageTitle: (title: string) => void

  // Theme actions
  toggleDarkMode: () => void
  setDarkMode: (isDark: boolean) => void

  // Fullscreen actions
  toggleFullscreen: () => void
  setFullscreen: (isFullscreen: boolean) => void

  // Search actions
  toggleSearch: () => void
  setSearchOpen: (open: boolean) => void
  setSearchQuery: (query: string) => void
  clearSearch: () => void
}

type UIStore = UIState & UIActions

const initialState: UIState = {
  sidebarOpen: true,
  sidebarCollapsed: false,
  mobileSidebarOpen: false,
  modals: {},
  toasts: [],
  globalLoading: false,
  pageLoading: false,
  breadcrumbs: [],
  pageTitle: '',
  isDarkMode: false,
  isFullscreen: false,
  searchOpen: false,
  searchQuery: '',
};

export const useUIStore = create<UIStore>()(
  devtools(
    (set, get) => ({
      ...initialState,

      // Sidebar actions
      toggleSidebar: () => {
        set((state) => ({ sidebarOpen: !state.sidebarOpen }));
      },

      setSidebarOpen: (open: boolean) => {
        set({ sidebarOpen: open });
      },

      toggleSidebarCollapsed: () => {
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }));
      },

      setSidebarCollapsed: (collapsed: boolean) => {
        set({ sidebarCollapsed: collapsed });
      },

      toggleMobileSidebar: () => {
        set((state) => ({ mobileSidebarOpen: !state.mobileSidebarOpen }));
      },

      setMobileSidebarOpen: (open: boolean) => {
        set({ mobileSidebarOpen: open });
      },

      // Modal actions
      openModal: (id: string, data?: ModalData) => {
        set((state) => ({
          modals: {
            ...state.modals,
            [id]: { id, isOpen: true, data },
          },
        }));
      },

      openConfirmationModal: (id: string, data: Omit<ConfirmationModalData, 'kind'>) => {
        set((state) => ({
          modals: {
            ...state.modals,
            [id]: { id, isOpen: true, data: { ...data, kind: 'confirmation' as const } },
          },
        }));
      },

      openFormModal: (id: string, data: Omit<FormModalData, 'kind'>) => {
        set((state) => ({
          modals: {
            ...state.modals,
            [id]: { id, isOpen: true, data: { ...data, kind: 'form' as const } },
          },
        }));
      },

      openDetailModal: (id: string, data: Omit<DetailModalData, 'kind'>) => {
        set((state) => ({
          modals: {
            ...state.modals,
            [id]: { id, isOpen: true, data: { ...data, kind: 'detail' as const } },
          },
        }));
      },

      openAlertModal: (id: string, data: Omit<AlertModalData, 'kind'>) => {
        set((state) => ({
          modals: {
            ...state.modals,
            [id]: { id, isOpen: true, data: { ...data, kind: 'alert' as const } },
          },
        }));
      },

      closeModal: (id: string) => {
        set((state) => ({
          modals: {
            ...state.modals,
            [id]: { ...state.modals[id], isOpen: false },
          },
        }));
      },

      closeAllModals: () => {
        set((state) => {
          const closedModals = Object.keys(state.modals).reduce((acc, key) => {
            acc[key] = { ...state.modals[key], isOpen: false };
            return acc;
          }, {} as Record<string, Modal>);

          return { modals: closedModals };
        });
      },

      isModalOpen: (id: string): boolean => {
        return get().modals[id]?.isOpen ?? false;
      },

      getModalData: (id: string): ModalData | undefined => {
        return get().modals[id]?.data;
      },

      // Toast actions
      showToast: (message: string, type: NotificationType = 'info', duration = 5000): string => {
        const id = `toast-${Date.now()}-${Math.random()}`;
        const toast: Toast = { id, message, type, duration };

        set((state) => ({
          toasts: [...state.toasts, toast],
        }));

        // Auto-remove after duration
        if (duration > 0) {
          setTimeout(() => {
            get().hideToast(id);
          }, duration);
        }

        return id;
      },

      showSuccess: (message: string, duration = 5000): string => {
        return get().showToast(message, 'success', duration);
      },

      showError: (message: string, duration = 7000): string => {
        return get().showToast(message, 'error', duration);
      },

      showWarning: (message: string, duration = 6000): string => {
        return get().showToast(message, 'warning', duration);
      },

      showInfo: (message: string, duration = 5000): string => {
        return get().showToast(message, 'info', duration);
      },

      hideToast: (id: string) => {
        set((state) => ({
          toasts: state.toasts.filter((toast) => toast.id !== id),
        }));
      },

      clearToasts: () => {
        set({ toasts: [] });
      },

      // Loading actions
      setGlobalLoading: (loading: boolean) => {
        set({ globalLoading: loading });
      },

      setPageLoading: (loading: boolean) => {
        set({ pageLoading: loading });
      },

      // Navigation actions
      setBreadcrumbs: (breadcrumbs: Breadcrumb[]) => {
        set({ breadcrumbs });
      },

      setPageTitle: (title: string) => {
        set({ pageTitle: title });

        // Also update document title
        if (typeof document !== 'undefined') {
          document.title = title ? `${title} | KIRO2` : 'KIRO2 - Eğitim Platformu';
        }
      },

      // Theme actions
      toggleDarkMode: () => {
        set((state) => {
          const newMode = !state.isDarkMode;
          // Persist to localStorage
          if (typeof localStorage !== 'undefined') {
            localStorage.setItem('theme', newMode ? 'dark' : 'light');
          }
          return { isDarkMode: newMode };
        });
      },

      setDarkMode: (isDark: boolean) => {
        set({ isDarkMode: isDark });
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem('theme', isDark ? 'dark' : 'light');
        }
      },

      // Fullscreen actions
      toggleFullscreen: () => {
        set((state) => {
          const newFullscreen = !state.isFullscreen;

          if (typeof document !== 'undefined') {
            if (newFullscreen) {
              document.documentElement.requestFullscreen?.();
            } else {
              document.exitFullscreen?.();
            }
          }

          return { isFullscreen: newFullscreen };
        });
      },

      setFullscreen: (isFullscreen: boolean) => {
        set({ isFullscreen });
      },

      // Search actions
      toggleSearch: () => {
        set((state) => ({ searchOpen: !state.searchOpen }));
      },

      setSearchOpen: (open: boolean) => {
        set({ searchOpen: open });
      },

      setSearchQuery: (query: string) => {
        set({ searchQuery: query });
      },

      clearSearch: () => {
        set({ searchQuery: '', searchOpen: false });
      },
    }),
    { name: 'UIStore' },
  ),
);

/**
 * Selector hooks for better performance
 */
export const useSidebarOpen = () => useUIStore((state) => state.sidebarOpen);
export const useSidebarCollapsed = () => useUIStore((state) => state.sidebarCollapsed);
export const useMobileSidebarOpen = () => useUIStore((state) => state.mobileSidebarOpen);
export const useToasts = () => useUIStore((state) => state.toasts);
export const useGlobalLoading = () => useUIStore((state) => state.globalLoading);
export const usePageLoading = () => useUIStore((state) => state.pageLoading);
export const useBreadcrumbs = () => useUIStore((state) => state.breadcrumbs);
export const usePageTitle = () => useUIStore((state) => state.pageTitle);
export const useIsDarkMode = () => useUIStore((state) => state.isDarkMode);
export const useIsFullscreen = () => useUIStore((state) => state.isFullscreen);
export const useSearchQuery = () => useUIStore((state) => state.searchQuery);

export default useUIStore;
