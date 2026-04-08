/**
 * PWA (Progressive Web App) Hook
 * PWA kurulum ve offline özelliklerini yönetir
 */

import { useState, useEffect, useCallback } from 'react';

import { backgroundSyncService, SyncStatus } from '../services/backgroundSyncService';
import { offlineStorageService } from '../services/offlineStorageService';

interface PWAInstallPrompt {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

interface PWAState {
  isInstallable: boolean;
  isInstalled: boolean;
  isOnline: boolean;
  syncStatus: SyncStatus | null;
  offlineStats: {
    totalQuestions: number;
    totalExams: number;
    totalNotes: number;
    unsyncedItems: number;
    storageUsed: number;
  } | null;
}

interface PWAActions {
  installPWA: () => Promise<boolean>;
  triggerSync: () => Promise<void>;
  downloadQuestionsForOffline: (subject: string, count?: number) => Promise<void>;
  clearOfflineData: () => Promise<void>;
  subscribeToPushNotifications: () => Promise<boolean>;
}

export function usePWA(): PWAState & PWAActions {
  const [installPrompt, setInstallPrompt] = useState<PWAInstallPrompt | null>(null);
  const [isInstallable, setIsInstallable] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [offlineStats, setOfflineStats] = useState<PWAState['offlineStats']>(null);

  /**
   * PWA kurulum event'lerini dinle
   */
  useEffect(() => {
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setInstallPrompt(e as any);
      setIsInstallable(true);
    };

    const handleAppInstalled = () => {
      setIsInstalled(true);
      setIsInstallable(false);
      setInstallPrompt(null);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    // PWA kurulu mu kontrol et
    const checkIfInstalled = () => {
      // Standalone mode'da çalışıyor mu?
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
      // iOS Safari'de home screen'e eklenmiş mi?
      const isIOSInstalled = (window.navigator as any).standalone === true;

      setIsInstalled(isStandalone || isIOSInstalled);
    };

    checkIfInstalled();

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  /**
   * Online/offline durumunu dinle
   */
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  /**
   * Sync durumunu periyodik olarak güncelle
   */
  useEffect(() => {
    const updateSyncStatus = async () => {
      try {
        const status = await backgroundSyncService.getSyncStatus();
        setSyncStatus(status);
      } catch (error) {
        console.error('Sync durumu alınamadı:', error);
      }
    };

    const updateOfflineStats = async () => {
      try {
        const stats = await offlineStorageService.getOfflineStats();
        setOfflineStats(stats);
      } catch (error) {
        console.error('Offline istatistikleri alınamadı:', error);
      }
    };

    // İlk yükleme
    updateSyncStatus();
    updateOfflineStats();

    // Her 30 saniyede bir güncelle
    const interval = setInterval(() => {
      updateSyncStatus();
      updateOfflineStats();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  /**
   * PWA'yı kur
   */
  const installPWA = useCallback(async (): Promise<boolean> => {
    if (!installPrompt) {
      console.warn('PWA kurulum prompt\'u mevcut değil');
      return false;
    }

    try {
      await installPrompt.prompt();
      const { outcome } = await installPrompt.userChoice;

      if (outcome === 'accepted') {
        setIsInstallable(false);
        setInstallPrompt(null);
        return true;
      } else {
        return false;
      }
    } catch (error) {
      console.error('PWA kurulum hatası:', error);
      return false;
    }
  }, [installPrompt]);

  /**
   * Manuel senkronizasyon tetikle
   */
  const triggerSync = useCallback(async (): Promise<void> => {
    try {
      const result = await backgroundSyncService.triggerManualSync();

      if (result.success) {
      } else {
        console.error('Senkronizasyon hatası:', result.errors);
      }

      // Durumu güncelle
      const status = await backgroundSyncService.getSyncStatus();
      setSyncStatus(status);
    } catch (error) {
      console.error('Manuel senkronizasyon hatası:', error);
    }
  }, []);

  /**
   * Çevrimdışı kullanım için soru indir
   */
  const downloadQuestionsForOffline = useCallback(async (
    subject: string,
    count: number = 50,
  ): Promise<void> => {
    try {
      await offlineStorageService.downloadQuestionsForOffline(subject, count);
      // İstatistikleri güncelle
      const stats = await offlineStorageService.getOfflineStats();
      setOfflineStats(stats);
    } catch (error) {
      console.error('Soru indirme hatası:', error);
      throw error;
    }
  }, []);

  /**
   * Çevrimdışı verileri temizle
   */
  const clearOfflineData = useCallback(async (): Promise<void> => {
    try {
      await offlineStorageService.clearOfflineData(true); // Ayarları koru
      // İstatistikleri güncelle
      const stats = await offlineStorageService.getOfflineStats();
      setOfflineStats(stats);

      const status = await backgroundSyncService.getSyncStatus();
      setSyncStatus(status);
    } catch (error) {
      console.error('Veri temizleme hatası:', error);
      throw error;
    }
  }, []);

  /**
   * Push notification'lara abone ol
   */
  const subscribeToPushNotifications = useCallback(async (): Promise<boolean> => {
    try {
      // Notification izni iste
      const permission = await Notification.requestPermission();

      if (permission !== 'granted') {
        return false;
      }

      // Push subscription oluştur
      const subscription = await backgroundSyncService.subscribeToPushNotifications();

      if (subscription) {
        return true;
      } else {
        return false;
      }
    } catch (error) {
      console.error('Push notification subscription hatası:', error);
      return false;
    }
  }, []);

  return {
    // State
    isInstallable,
    isInstalled,
    isOnline,
    syncStatus,
    offlineStats,

    // Actions
    installPWA,
    triggerSync,
    downloadQuestionsForOffline,
    clearOfflineData,
    subscribeToPushNotifications,
  };
}

/**
 * PWA kurulum durumunu kontrol eden hook
 */
export function usePWAInstallPrompt() {
  const [installPrompt, setInstallPrompt] = useState<PWAInstallPrompt | null>(null);
  const [isInstallable, setIsInstallable] = useState(false);

  useEffect(() => {
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setInstallPrompt(e as any);
      setIsInstallable(true);
    };

    const handleAppInstalled = () => {
      setIsInstallable(false);
      setInstallPrompt(null);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const install = useCallback(async () => {
    if (!installPrompt) {return false;}

    try {
      await installPrompt.prompt();
      const { outcome } = await installPrompt.userChoice;
      return outcome === 'accepted';
    } catch (error) {
      console.error('PWA kurulum hatası:', error);
      return false;
    }
  }, [installPrompt]);

  return {
    isInstallable,
    install,
  };
}

/**
 * Network durumunu takip eden hook
 */
export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [connectionType, setConnectionType] = useState<string>('unknown');

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Network Information API (experimental)
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      setConnectionType(connection.effectiveType || 'unknown');

      const handleConnectionChange = () => {
        setConnectionType(connection.effectiveType || 'unknown');
      };

      connection.addEventListener('change', handleConnectionChange);

      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
        connection.removeEventListener('change', handleConnectionChange);
      };
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return {
    isOnline,
    connectionType,
  };
}