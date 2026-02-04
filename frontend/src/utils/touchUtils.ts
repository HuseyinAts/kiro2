/**
 * Touch ve PWA Yardımcı Fonksiyonları
 * Mobil cihazlar için touch gesture ve PWA özelliklerini yönetir
 */

export interface TouchPoint {
  x: number;
  y: number;
  timestamp: number;
}

export interface SwipeGesture {
  direction: 'left' | 'right' | 'up' | 'down';
  distance: number;
  duration: number;
  velocity: number;
}

export interface PinchGesture {
  scale: number;
  center: TouchPoint;
}

/**
 * Touch gesture detector sınıfı
 */
export class TouchGestureDetector {
  private startPoint: TouchPoint | null = null;
  private endPoint: TouchPoint | null = null;
  private minSwipeDistance = 50;
  private maxSwipeTime = 300;
  
  constructor(
    private element: HTMLElement,
    private callbacks: {
      onSwipe?: (gesture: SwipeGesture) => void;
      onTap?: (point: TouchPoint) => void;
      onLongPress?: (point: TouchPoint) => void;
      onPinch?: (gesture: PinchGesture) => void;
    }
  ) {
    this.setupEventListeners();
  }
  
  private setupEventListeners(): void {
    let longPressTimer: NodeJS.Timeout | null = null;
    let initialDistance = 0;
    let initialScale = 1;
    
    // Touch start
    this.element.addEventListener('touchstart', (e) => {
      e.preventDefault();
      
      const touch = e.touches[0];
      this.startPoint = {
        x: touch.clientX,
        y: touch.clientY,
        timestamp: Date.now()
      };
      
      // Long press timer
      longPressTimer = setTimeout(() => {
        if (this.startPoint && this.callbacks.onLongPress) {
          this.callbacks.onLongPress(this.startPoint);
          this.triggerHapticFeedback('medium');
        }
      }, 500);
      
      // Pinch gesture için iki parmak kontrolü
      if (e.touches.length === 2) {
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        initialDistance = this.getDistance(touch1, touch2);
        initialScale = 1;
      }
    }, { passive: false });
    
    // Touch move
    this.element.addEventListener('touchmove', (e) => {
      if (longPressTimer) {
        clearTimeout(longPressTimer);
        longPressTimer = null;
      }
      
      // Pinch gesture
      if (e.touches.length === 2 && this.callbacks.onPinch) {
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        const currentDistance = this.getDistance(touch1, touch2);
        const scale = currentDistance / initialDistance;
        
        const center: TouchPoint = {
          x: (touch1.clientX + touch2.clientX) / 2,
          y: (touch1.clientY + touch2.clientY) / 2,
          timestamp: Date.now()
        };
        
        this.callbacks.onPinch({ scale, center });
      }
    }, { passive: true });
    
    // Touch end
    this.element.addEventListener('touchend', (e) => {
      if (longPressTimer) {
        clearTimeout(longPressTimer);
        longPressTimer = null;
      }
      
      if (!this.startPoint) return;
      
      const touch = e.changedTouches[0];
      this.endPoint = {
        x: touch.clientX,
        y: touch.clientY,
        timestamp: Date.now()
      };
      
      const gesture = this.analyzeGesture();
      
      if (gesture) {
        if (this.callbacks.onSwipe) {
          this.callbacks.onSwipe(gesture);
          this.triggerHapticFeedback('light');
        }
      } else {
        // Tap gesture
        if (this.callbacks.onTap) {
          this.callbacks.onTap(this.startPoint);
        }
      }
      
      this.startPoint = null;
      this.endPoint = null;
    }, { passive: true });
  }
  
  private getDistance(touch1: Touch, touch2: Touch): number {
    const dx = touch1.clientX - touch2.clientX;
    const dy = touch1.clientY - touch2.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  }
  
  private analyzeGesture(): SwipeGesture | null {
    if (!this.startPoint || !this.endPoint) return null;
    
    const deltaX = this.endPoint.x - this.startPoint.x;
    const deltaY = this.endPoint.y - this.startPoint.y;
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
    const duration = this.endPoint.timestamp - this.startPoint.timestamp;
    
    // Minimum mesafe ve maksimum süre kontrolü
    if (distance < this.minSwipeDistance || duration > this.maxSwipeTime) {
      return null;
    }
    
    const velocity = distance / duration;
    
    // Yön belirleme
    let direction: SwipeGesture['direction'];
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      direction = deltaX > 0 ? 'right' : 'left';
    } else {
      direction = deltaY > 0 ? 'down' : 'up';
    }
    
    return {
      direction,
      distance,
      duration,
      velocity
    };
  }
  
  /**
   * Haptic feedback tetikle (destekleyen cihazlarda)
   */
  private triggerHapticFeedback(type: 'light' | 'medium' | 'heavy'): void {
    if ('vibrate' in navigator) {
      const patterns = {
        light: [10],
        medium: [20],
        heavy: [30]
      };
      navigator.vibrate(patterns[type]);
    }
    
    // CSS animasyon ile görsel feedback
    this.element.classList.add(`haptic-${type}`);
    setTimeout(() => {
      this.element.classList.remove(`haptic-${type}`);
    }, 200);
  }
  
  /**
   * Event listener'ları temizle
   */
  destroy(): void {
    // Event listener'lar otomatik olarak temizlenecek
    // Çünkü element referansı kaybolacak
  }
}

/**
 * Pull-to-refresh implementasyonu
 */
export class PullToRefresh {
  private startY = 0;
  private currentY = 0;
  private isRefreshing = false;
  private threshold = 80;
  
  constructor(
    private container: HTMLElement,
    private onRefresh: () => Promise<void>
  ) {
    this.setupPullToRefresh();
  }
  
  private setupPullToRefresh(): void {
    let indicator: HTMLElement | null = null;
    
    this.container.addEventListener('touchstart', (e) => {
      if (this.container.scrollTop === 0) {
        this.startY = e.touches[0].clientY;
      }
    }, { passive: true });
    
    this.container.addEventListener('touchmove', (e) => {
      if (this.isRefreshing || this.container.scrollTop > 0) return;
      
      this.currentY = e.touches[0].clientY;
      const pullDistance = this.currentY - this.startY;
      
      if (pullDistance > 0) {
        e.preventDefault();
        
        // Indicator oluştur
        if (!indicator) {
          indicator = document.createElement('div');
          indicator.className = 'pull-indicator';
          indicator.innerHTML = '↓';
          this.container.appendChild(indicator);
        }
        
        // Indicator pozisyonunu güncelle
        const progress = Math.min(pullDistance / this.threshold, 1);
        indicator.style.transform = `translateX(-50%) translateY(${pullDistance * 0.5}px) rotate(${progress * 180}deg)`;
        indicator.style.opacity = progress.toString();
        
        if (pullDistance > this.threshold) {
          indicator.classList.add('active');
        } else {
          indicator.classList.remove('active');
        }
      }
    }, { passive: false });
    
    this.container.addEventListener('touchend', async () => {
      if (this.isRefreshing) return;
      
      const pullDistance = this.currentY - this.startY;
      
      if (pullDistance > this.threshold) {
        this.isRefreshing = true;
        
        if (indicator) {
          indicator.innerHTML = '⟳';
          indicator.style.animation = 'spin 1s linear infinite';
        }
        
        try {
          await this.onRefresh();
        } finally {
          this.isRefreshing = false;
          
          if (indicator) {
            indicator.remove();
            indicator = null;
          }
        }
      } else if (indicator) {
        indicator.remove();
        indicator = null;
      }
      
      this.startY = 0;
      this.currentY = 0;
    }, { passive: true });
  }
}

/**
 * PWA kurulum yardımcı fonksiyonları
 */
export class PWAInstallHelper {
  private deferredPrompt: any = null;
  
  constructor() {
    this.setupInstallPrompt();
  }
  
  private setupInstallPrompt(): void {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.deferredPrompt = e;
    });
    
    window.addEventListener('appinstalled', () => {
      console.log('PWA kuruldu');
      this.deferredPrompt = null;
    });
  }
  
  /**
   * PWA kurulabilir mi kontrol et
   */
  isInstallable(): boolean {
    return this.deferredPrompt !== null;
  }
  
  /**
   * PWA kurulumu tetikle
   */
  async install(): Promise<boolean> {
    if (!this.deferredPrompt) {
      return false;
    }
    
    try {
      await this.deferredPrompt.prompt();
      const { outcome } = await this.deferredPrompt.userChoice;
      
      this.deferredPrompt = null;
      return outcome === 'accepted';
    } catch (error) {
      console.error('PWA kurulum hatası:', error);
      return false;
    }
  }
  
  /**
   * PWA kurulu mu kontrol et
   */
  isInstalled(): boolean {
    // Standalone mode kontrolü
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    
    // iOS Safari home screen kontrolü
    const isIOSInstalled = (window.navigator as any).standalone === true;
    
    return isStandalone || isIOSInstalled;
  }
}

/**
 * Network durumu yöneticisi
 */
export class NetworkManager {
  private callbacks: {
    onOnline?: () => void;
    onOffline?: () => void;
    onSlowConnection?: () => void;
  } = {};
  
  constructor(callbacks: NetworkManager['callbacks']) {
    this.callbacks = callbacks;
    this.setupNetworkListeners();
  }
  
  private setupNetworkListeners(): void {
    window.addEventListener('online', () => {
      if (this.callbacks.onOnline) {
        this.callbacks.onOnline();
      }
    });
    
    window.addEventListener('offline', () => {
      if (this.callbacks.onOffline) {
        this.callbacks.onOffline();
      }
    });
    
    // Network Information API (experimental)
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      
      const checkConnection = () => {
        if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
          if (this.callbacks.onSlowConnection) {
            this.callbacks.onSlowConnection();
          }
        }
      };
      
      connection.addEventListener('change', checkConnection);
      checkConnection(); // İlk kontrol
    }
  }
  
  /**
   * Bağlantı durumunu al
   */
  getConnectionInfo(): {
    isOnline: boolean;
    effectiveType?: string;
    downlink?: number;
    rtt?: number;
  } {
    const info: any = {
      isOnline: navigator.onLine
    };
    
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      info.effectiveType = connection.effectiveType;
      info.downlink = connection.downlink;
      info.rtt = connection.rtt;
    }
    
    return info;
  }
}

/**
 * Responsive breakpoint yardımcıları
 */
export const breakpoints = {
  mobile: 480,
  tablet: 768,
  desktop: 1024,
  wide: 1200
};

export function isMobile(): boolean {
  return window.innerWidth <= breakpoints.mobile;
}

export function isTablet(): boolean {
  return window.innerWidth > breakpoints.mobile && window.innerWidth <= breakpoints.tablet;
}

export function isDesktop(): boolean {
  return window.innerWidth > breakpoints.tablet;
}

/**
 * Safe area insets (iPhone X+ için)
 */
export function getSafeAreaInsets(): {
  top: number;
  right: number;
  bottom: number;
  left: number;
} {
  const style = getComputedStyle(document.documentElement);
  
  return {
    top: parseInt(style.getPropertyValue('env(safe-area-inset-top)') || '0'),
    right: parseInt(style.getPropertyValue('env(safe-area-inset-right)') || '0'),
    bottom: parseInt(style.getPropertyValue('env(safe-area-inset-bottom)') || '0'),
    left: parseInt(style.getPropertyValue('env(safe-area-inset-left)') || '0')
  };
}

/**
 * Orientation change listener
 */
export function onOrientationChange(callback: (orientation: 'portrait' | 'landscape') => void): () => void {
  const handleOrientationChange = () => {
    const orientation = window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
    callback(orientation);
  };
  
  window.addEventListener('orientationchange', handleOrientationChange);
  window.addEventListener('resize', handleOrientationChange);
  
  // İlk çağrı
  handleOrientationChange();
  
  // Cleanup function
  return () => {
    window.removeEventListener('orientationchange', handleOrientationChange);
    window.removeEventListener('resize', handleOrientationChange);
  };
}

/**
 * Keyboard visibility detection (mobil cihazlarda)
 */
export function onKeyboardToggle(callback: (isVisible: boolean) => void): () => void {
  let initialViewportHeight = window.visualViewport?.height || window.innerHeight;
  
  const handleViewportChange = () => {
    const currentHeight = window.visualViewport?.height || window.innerHeight;
    const heightDifference = initialViewportHeight - currentHeight;
    
    // 150px'den fazla küçülme klavye açılması olarak kabul edilir
    const isKeyboardVisible = heightDifference > 150;
    callback(isKeyboardVisible);
  };
  
  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', handleViewportChange);
    
    return () => {
      window.visualViewport?.removeEventListener('resize', handleViewportChange);
    };
  } else {
    window.addEventListener('resize', handleViewportChange);
    
    return () => {
      window.removeEventListener('resize', handleViewportChange);
    };
  }
}