/**
 * Responsive Design Hook'u
 * Ekran boyutlarına göre responsive davranış
 */
import { useTheme, useMediaQuery } from '@mui/material'
import { Breakpoint } from '@mui/material/styles'

export const useResponsive = () => {
  const theme = useTheme()
  
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const isTablet = useMediaQuery(theme.breakpoints.between('md', 'lg'))
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'))
  const isSmallScreen = useMediaQuery(theme.breakpoints.down('sm'))
  const isLargeScreen = useMediaQuery(theme.breakpoints.up('xl'))

  /**
   * Belirli bir breakpoint'ten küçük mü kontrol et
   */
  const isDown = (breakpoint: Breakpoint) => {
    return useMediaQuery(theme.breakpoints.down(breakpoint))
  }

  /**
   * Belirli bir breakpoint'ten büyük mü kontrol et
   */
  const isUp = (breakpoint: Breakpoint) => {
    return useMediaQuery(theme.breakpoints.up(breakpoint))
  }

  /**
   * İki breakpoint arasında mı kontrol et
   */
  const isBetween = (start: Breakpoint, end: Breakpoint) => {
    return useMediaQuery(theme.breakpoints.between(start, end))
  }

  /**
   * Responsive değerler getir
   */
  const getResponsiveValue = <T>(values: {
    xs?: T
    sm?: T
    md?: T
    lg?: T
    xl?: T
  }): T | undefined => {
    if (isLargeScreen && values.xl !== undefined) return values.xl
    if (isDesktop && values.lg !== undefined) return values.lg
    if (isTablet && values.md !== undefined) return values.md
    if (!isSmallScreen && values.sm !== undefined) return values.sm
    if (values.xs !== undefined) return values.xs
    
    // Fallback: en büyük tanımlı değeri döndür
    return values.xl || values.lg || values.md || values.sm || values.xs
  }

  /**
   * Sınav arayüzü için özel responsive ayarlar
   */
  const examLayout = {
    // Soru navigasyonu
    questionNavigation: {
      showFullGrid: isDesktop,
      showQuickNav: isMobile,
      maxVisibleQuestions: isMobile ? 5 : isTablet ? 10 : 20,
      gridColumns: isMobile ? 5 : isTablet ? 8 : 10
    },
    
    // Timer
    timer: {
      showProgress: !isMobile,
      showSeconds: !isSmallScreen,
      size: isMobile ? 'small' : 'medium'
    },
    
    // Soru alanı
    question: {
      fontSize: isMobile ? '0.95rem' : '1rem',
      optionSpacing: isMobile ? 1.5 : 1,
      showQuestionNumber: true,
      compactMode: isMobile
    },
    
    // Header
    header: {
      height: isMobile ? 'auto' : 80,
      showFullInfo: !isMobile,
      stackVertical: isMobile
    },
    
    // Footer
    footer: {
      height: isMobile ? 'auto' : 60,
      showAllButtons: !isMobile,
      compactButtons: isMobile
    }
  }

  /**
   * Touch cihaz kontrolü
   */
  const isTouchDevice = () => {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0
  }

  /**
   * Ekran yönelimi
   */
  const isLandscape = () => {
    return window.innerWidth > window.innerHeight
  }

  const isPortrait = () => {
    return window.innerHeight > window.innerWidth
  }

  /**
   * Viewport boyutları
   */
  const viewport = {
    width: window.innerWidth,
    height: window.innerHeight,
    isLandscape: isLandscape(),
    isPortrait: isPortrait()
  }

  /**
   * Sınav için önerilen layout
   */
  const getExamLayoutConfig = () => {
    if (isMobile) {
      return {
        layout: 'mobile',
        headerCollapsed: true,
        navigationCompact: true,
        timerMinimized: false,
        questionFullWidth: true,
        footerSticky: true
      }
    }
    
    if (isTablet) {
      return {
        layout: 'tablet',
        headerCollapsed: false,
        navigationCompact: false,
        timerMinimized: false,
        questionFullWidth: false,
        footerSticky: false
      }
    }
    
    return {
      layout: 'desktop',
      headerCollapsed: false,
      navigationCompact: false,
      timerMinimized: false,
      questionFullWidth: false,
      footerSticky: false
    }
  }

  return {
    // Temel responsive durumlar
    isMobile,
    isTablet,
    isDesktop,
    isSmallScreen,
    isLargeScreen,
    
    // Utility fonksiyonlar
    isDown,
    isUp,
    isBetween,
    getResponsiveValue,
    
    // Cihaz bilgileri
    isTouchDevice: isTouchDevice(),
    viewport,
    
    // Sınav özel ayarları
    examLayout,
    getExamLayoutConfig: getExamLayoutConfig(),
    
    // Theme breakpoints
    breakpoints: theme.breakpoints.values
  }
}

export default useResponsive