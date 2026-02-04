/**
 * Arka Plan Senkronizasyon Servisi
 * Çevrimdışı verilerin otomatik senkronizasyonu için
 */

import { offlineStorageService } from './offlineStorageService';

export interface SyncResult {
  success: boolean;
  syncedItems: number;
  errors: string[];
  timestamp: string;
}

export interface SyncStatus {
  isOnline: boolean;
  lastSync: string | null;
  pendingItems: number;
  syncInProgress: boolean;
}

class BackgroundSyncService {
  private syncInProgress = false;
  private syncQueue: Array<() => Promise<void>> = [];
  private retryAttempts = new Map<string, number>();
  private maxRetries = 3;
  
  constructor() {
    this.setupEventListeners();
    this.startPeriodicSync();
  }
  
  /**
   * Event listener'ları kur
   */
  private setupEventListeners(): void {
    // Online/offline durumu değişikliklerini dinle
    window.addEventListener('online', () => {
      console.log('İnternet bağlantısı geri geldi, senkronizasyon başlatılıyor...');
      this.performSync();
    });
    
    window.addEventListener('offline', () => {
      console.log('İnternet bağlantısı kesildi, çevrimdışı moda geçiliyor...');
    });
    
    // Sayfa kapatılmadan önce senkronize et
    window.addEventListener('beforeunload', () => {
      if (navigator.onLine && !this.syncInProgress) {
        this.performSync();
      }
    });
    
    // Visibility API ile sayfa odağı değişikliklerini dinle
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && navigator.onLine && !this.syncInProgress) {
        this.performSync();
      }
    });
  }
  
  /**
   * Periyodik senkronizasyon başlat
   */
  private startPeriodicSync(): void {
    // Her 5 dakikada bir senkronize et
    setInterval(() => {
      if (navigator.onLine && !this.syncInProgress) {
        this.performSync();
      }
    }, 5 * 60 * 1000); // 5 dakika
  }
  
  /**
   * Ana senkronizasyon fonksiyonu
   */
  async performSync(): Promise<SyncResult> {
    if (this.syncInProgress) {
      console.log('Senkronizasyon zaten devam ediyor...');
      return {
        success: false,
        syncedItems: 0,
        errors: ['Senkronizasyon zaten devam ediyor'],
        timestamp: new Date().toISOString()
      };
    }
    
    if (!navigator.onLine) {
      console.log('İnternet bağlantısı yok, senkronizasyon atlanıyor...');
      return {
        success: false,
        syncedItems: 0,
        errors: ['İnternet bağlantısı yok'],
        timestamp: new Date().toISOString()
      };
    }
    
    this.syncInProgress = true;
    const errors: string[] = [];
    let syncedItems = 0;
    
    try {
      console.log('Senkronizasyon başlatıldı...');
      
      // Senkronize edilmemiş verileri al
      const unsyncedData = await offlineStorageService.getUnsyncedData();
      
      // Sınav sonuçlarını senkronize et
      if (unsyncedData.examSessions.length > 0) {
        try {
          const syncedExamIds = await this.syncExamSessions(unsyncedData.examSessions);
          syncedItems += syncedExamIds.length;
          
          if (syncedExamIds.length > 0) {
            await offlineStorageService.markAsSynced('examSessions', syncedExamIds);
          }
        } catch (error) {
          errors.push(`Sınav sonuçları senkronizasyon hatası: ${error}`);
        }
      }
      
      // Çalışma notlarını senkronize et
      if (unsyncedData.studyNotes.length > 0) {
        try {
          const syncedNoteIds = await this.syncStudyNotes(unsyncedData.studyNotes);
          syncedItems += syncedNoteIds.length;
          
          if (syncedNoteIds.length > 0) {
            await offlineStorageService.markAsSynced('studyNotes', syncedNoteIds);
          }
        } catch (error) {
          errors.push(`Çalışma notları senkronizasyon hatası: ${error}`);
        }
      }
      
      // İlerleme verilerini senkronize et
      if (unsyncedData.progress.length > 0) {
        try {
          const syncedProgressIds = await this.syncProgress(unsyncedData.progress);
          syncedItems += syncedProgressIds.length;
          
          if (syncedProgressIds.length > 0) {
            await offlineStorageService.markAsSynced('progress', syncedProgressIds);
          }
        } catch (error) {
          errors.push(`İlerleme verileri senkronizasyon hatası: ${error}`);
        }
      }
      
      console.log(`Senkronizasyon tamamlandı. ${syncedItems} öğe senkronize edildi.`);
      
      // Başarılı senkronizasyon sonrası retry sayaçlarını sıfırla
      this.retryAttempts.clear();
      
      return {
        success: errors.length === 0,
        syncedItems,
        errors,
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      console.error('Senkronizasyon genel hatası:', error);
      errors.push(`Genel senkronizasyon hatası: ${error}`);
      
      return {
        success: false,
        syncedItems,
        errors,
        timestamp: new Date().toISOString()
      };
    } finally {
      this.syncInProgress = false;
    }
  }
  
  /**
   * Sınav oturumlarını senkronize et
   */
  private async syncExamSessions(examSessions: any[]): Promise<string[]> {
    const syncedIds: string[] = [];
    
    for (const session of examSessions) {
      try {
        const response = await fetch('/api/v1/sync/exam-sessions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.getAuthToken()}`
          },
          body: JSON.stringify({
            sessionId: session.id,
            questions: session.questions.map((q: any) => q.id),
            answers: session.answers,
            startTime: session.startTime,
            endTime: session.endTime,
            score: session.score,
            completed: session.completed
          })
        });
        
        if (response.ok) {
          syncedIds.push(session.id);
          console.log(`Sınav oturumu senkronize edildi: ${session.id}`);
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
      } catch (error) {
        console.error(`Sınav oturumu senkronizasyon hatası (${session.id}):`, error);
        
        // Retry mekanizması
        const retryKey = `exam-${session.id}`;
        const attempts = this.retryAttempts.get(retryKey) || 0;
        
        if (attempts < this.maxRetries) {
          this.retryAttempts.set(retryKey, attempts + 1);
          // Retry queue'ya ekle
          this.addToRetryQueue(() => this.syncExamSessions([session]));
        }
        
        throw error;
      }
    }
    
    return syncedIds;
  }
  
  /**
   * Çalışma notlarını senkronize et
   */
  private async syncStudyNotes(studyNotes: any[]): Promise<string[]> {
    const syncedIds: string[] = [];
    
    for (const note of studyNotes) {
      try {
        const response = await fetch('/api/v1/sync/study-notes', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.getAuthToken()}`
          },
          body: JSON.stringify({
            noteId: note.id,
            title: note.title,
            content: note.content,
            subject: note.subject,
            createdAt: note.createdAt,
            updatedAt: note.updatedAt
          })
        });
        
        if (response.ok) {
          syncedIds.push(note.id);
          console.log(`Çalışma notu senkronize edildi: ${note.id}`);
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
      } catch (error) {
        console.error(`Çalışma notu senkronizasyon hatası (${note.id}):`, error);
        
        // Retry mekanizması
        const retryKey = `note-${note.id}`;
        const attempts = this.retryAttempts.get(retryKey) || 0;
        
        if (attempts < this.maxRetries) {
          this.retryAttempts.set(retryKey, attempts + 1);
          this.addToRetryQueue(() => this.syncStudyNotes([note]));
        }
        
        throw error;
      }
    }
    
    return syncedIds;
  }
  
  /**
   * İlerleme verilerini senkronize et
   */
  private async syncProgress(progressData: any[]): Promise<string[]> {
    const syncedIds: string[] = [];
    
    for (const progress of progressData) {
      try {
        const response = await fetch('/api/v1/sync/progress', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.getAuthToken()}`
          },
          body: JSON.stringify({
            userId: progress.userId,
            subject: progress.subject,
            totalQuestions: progress.totalQuestions,
            correctAnswers: progress.correctAnswers,
            studyTime: progress.studyTime,
            lastActivity: progress.lastActivity
          })
        });
        
        if (response.ok) {
          const progressId = `${progress.userId}-${progress.subject}`;
          syncedIds.push(progressId);
          console.log(`İlerleme verisi senkronize edildi: ${progressId}`);
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
      } catch (error) {
        console.error(`İlerleme verisi senkronizasyon hatası:`, error);
        
        // Retry mekanizması
        const retryKey = `progress-${progress.userId}-${progress.subject}`;
        const attempts = this.retryAttempts.get(retryKey) || 0;
        
        if (attempts < this.maxRetries) {
          this.retryAttempts.set(retryKey, attempts + 1);
          this.addToRetryQueue(() => this.syncProgress([progress]));
        }
        
        throw error;
      }
    }
    
    return syncedIds;
  }
  
  /**
   * Retry queue'ya görev ekle
   */
  private addToRetryQueue(task: () => Promise<void>): void {
    this.syncQueue.push(task);
    
    // 30 saniye sonra retry et
    setTimeout(() => {
      this.processRetryQueue();
    }, 30000);
  }
  
  /**
   * Retry queue'yu işle
   */
  private async processRetryQueue(): Promise<void> {
    if (this.syncQueue.length === 0 || !navigator.onLine) {
      return;
    }
    
    const task = this.syncQueue.shift();
    if (task) {
      try {
        await task();
      } catch (error) {
        console.error('Retry görevi başarısız:', error);
      }
    }
  }
  
  /**
   * Auth token'ı al
   */
  private getAuthToken(): string {
    // localStorage'dan token al
    return localStorage.getItem('auth-token') || '';
  }
  
  /**
   * Senkronizasyon durumunu al
   */
  async getSyncStatus(): Promise<SyncStatus> {
    const unsyncedData = await offlineStorageService.getUnsyncedData();
    const pendingItems = 
      unsyncedData.examSessions.length + 
      unsyncedData.studyNotes.length + 
      unsyncedData.progress.length;
    
    return {
      isOnline: navigator.onLine,
      lastSync: localStorage.getItem('last-sync-timestamp'),
      pendingItems,
      syncInProgress: this.syncInProgress
    };
  }
  
  /**
   * Manuel senkronizasyon tetikle
   */
  async triggerManualSync(): Promise<SyncResult> {
    console.log('Manuel senkronizasyon tetiklendi...');
    return await this.performSync();
  }
  
  /**
   * Senkronizasyon ayarlarını güncelle
   */
  updateSyncSettings(settings: {
    autoSync?: boolean;
    syncInterval?: number; // dakika cinsinden
  }): void {
    localStorage.setItem('sync-settings', JSON.stringify(settings));
    
    // Interval'ı güncelle
    if (settings.syncInterval) {
      this.startPeriodicSync();
    }
  }
  
  /**
   * Service Worker ile background sync kaydet
   */
  async registerBackgroundSync(tag: string): Promise<void> {
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      try {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register(tag);
        console.log(`Background sync kaydedildi: ${tag}`);
      } catch (error) {
        console.error('Background sync kayıt hatası:', error);
      }
    }
  }
  
  /**
   * Push notification için subscription al
   */
  async subscribeToPushNotifications(): Promise<PushSubscription | null> {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      try {
        const registration = await navigator.serviceWorker.ready;
        
        const subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: this.urlBase64ToUint8Array(
            process.env.REACT_APP_VAPID_PUBLIC_KEY || ''
          )
        });
        
        // Subscription'ı sunucuya gönder
        await this.sendSubscriptionToServer(subscription);
        
        return subscription;
      } catch (error) {
        console.error('Push notification subscription hatası:', error);
        return null;
      }
    }
    
    return null;
  }
  
  /**
   * VAPID key'i Uint8Array'e çevir
   */
  private urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');
    
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    
    return outputArray;
  }
  
  /**
   * Subscription'ı sunucuya gönder
   */
  private async sendSubscriptionToServer(subscription: PushSubscription): Promise<void> {
    try {
      await fetch('/api/v1/push/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`
        },
        body: JSON.stringify(subscription)
      });
    } catch (error) {
      console.error('Subscription sunucuya gönderme hatası:', error);
    }
  }
}

// Singleton instance
export const backgroundSyncService = new BackgroundSyncService();

// Export types
export type { SyncResult, SyncStatus };