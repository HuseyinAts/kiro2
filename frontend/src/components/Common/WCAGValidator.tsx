/**
 * WCAG 2.1 Level AA Otomatik Erişilebilirlik Validator
 *
 * Bu bileşen sayfadaki erişilebilirlik sorunlarını tespit eder ve raporlar:
 * - Eksik alt metinler
 * - Yetersiz kontrast oranları
 * - Eksik ARIA etiketleri
 * - Klavye erişilebilirliği sorunları
 * - Başlık hiyerarşisi hataları
 * - Form erişilebilirliği
 */

import {
  Error,
  Warning,
  Info,
  CheckCircle,
  ExpandMore,
  ExpandLess,
  Refresh,
  Accessibility,
} from '@mui/icons-material';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Collapse,
  List,
  ListItem,
  ListItemIcon,
  Chip,
  Button,
  Divider,
  Alert,
  LinearProgress,
  useTheme,
} from '@mui/material';
import * as React from 'react';
import {  useEffect, useState, useCallback  } from 'react';

interface WCAGIssue {
  id: string;
  severity: 'error' | 'warning' | 'info';
  guideline: string;
  description: string;
  element?: HTMLElement;
  suggestion: string;
  wcagCriterion: string;
}

interface WCAGValidatorProps {
  // Otomatik validasyon
  autoValidate?: boolean;

  // Validasyon interval (ms)
  validationInterval?: number;

  // Sadece development modda göster
  developmentOnly?: boolean;

  // Pozisyon
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';

  // Callback
  onIssuesFound?: (issues: WCAGIssue[]) => void;
}

const WCAGValidator: React.FC<WCAGValidatorProps> = ({
  autoValidate = true,
  validationInterval = 5000,
  developmentOnly = true,
  position = 'bottom-right',
  onIssuesFound,
}) => {
  const theme = useTheme();
  const [issues, setIssues] = useState<WCAGIssue[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  // Development mode kontrolü
  const isDevelopment = process.env.NODE_ENV === 'development';
  const shouldRender = !developmentOnly || isDevelopment;

  // Kontrast oranı hesaplama
  const calculateContrastRatio = (color1: string, color2: string): number => {
    const getLuminance = (color: string): number => {
      const rgb = color.match(/\d+/g);
      if (!rgb || rgb.length < 3) {return 0;}

      const [r, g, b] = rgb.map(val => {
        const normalized = parseInt(val) / 255;
        return normalized <= 0.03928
          ? normalized / 12.92
          : Math.pow((normalized + 0.055) / 1.055, 2.4);
      });

      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };

    const lum1 = getLuminance(color1);
    const lum2 = getLuminance(color2);
    const lighter = Math.max(lum1, lum2);
    const darker = Math.min(lum1, lum2);

    return (lighter + 0.05) / (darker + 0.05);
  };

  // Validasyon fonksiyonları
  const validateImages = (): WCAGIssue[] => {
    const imageIssues: WCAGIssue[] = [];
    const images = document.querySelectorAll('img');

    images.forEach((img, index) => {
      if (!img.alt && !img.getAttribute('aria-label')) {
        imageIssues.push({
          id: `img-alt-${index}`,
          severity: 'error',
          guideline: 'Görsel İçerik',
          description: 'Resimde alternatif metin (alt) eksik',
          element: img,
          suggestion: 'Resme anlamlı bir alt metni ekleyin: <img alt="açıklama" />',
          wcagCriterion: 'WCAG 1.1.1 (Level A)',
        });
      }
    });

    return imageIssues;
  };

  const validateHeadings = (): WCAGIssue[] => {
    const headingIssues: WCAGIssue[] = [];
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');

    let previousLevel = 0;
    headings.forEach((heading, index) => {
      const level = parseInt(heading.tagName.substring(1));

      if (level - previousLevel > 1) {
        headingIssues.push({
          id: `heading-hierarchy-${index}`,
          severity: 'warning',
          guideline: 'Başlık Hiyerarşisi',
          description: `Başlık seviyesi atlandı: ${heading.tagName} (önceki: H${previousLevel})`,
          element: heading as HTMLElement,
          suggestion: 'Başlıkları sıralı kullanın (H1 → H2 → H3)',
          wcagCriterion: 'WCAG 1.3.1 (Level A)',
        });
      }

      previousLevel = level;
    });

    // H1 kontrolü
    const h1Count = document.querySelectorAll('h1').length;
    if (h1Count === 0) {
      headingIssues.push({
        id: 'missing-h1',
        severity: 'error',
        guideline: 'Başlık Hiyerarşisi',
        description: 'Sayfada H1 başlığı bulunamadı',
        suggestion: 'Her sayfada bir adet H1 başlığı olmalıdır',
        wcagCriterion: 'WCAG 1.3.1 (Level A)',
      });
    } else if (h1Count > 1) {
      headingIssues.push({
        id: 'multiple-h1',
        severity: 'warning',
        guideline: 'Başlık Hiyerarşisi',
        description: `Sayfada ${h1Count} adet H1 başlığı var`,
        suggestion: 'Sayfada sadece bir adet H1 başlığı olmalıdır',
        wcagCriterion: 'WCAG 1.3.1 (Level A)',
      });
    }

    return headingIssues;
  };

  const validateContrast = (): WCAGIssue[] => {
    const contrastIssues: WCAGIssue[] = [];
    const textElements = document.querySelectorAll('p, span, a, button, h1, h2, h3, h4, h5, h6, li, td, th');

    textElements.forEach((element, index) => {
      const htmlElement = element as HTMLElement;
      const styles = window.getComputedStyle(htmlElement);
      const color = styles.color;
      const backgroundColor = styles.backgroundColor;
      const fontSize = parseFloat(styles.fontSize);
      const fontWeight = styles.fontWeight;

      // Şeffaf arka plan kontrolü
      if (backgroundColor === 'rgba(0, 0, 0, 0)' || backgroundColor === 'transparent') {
        return;
      }

      const contrastRatio = calculateContrastRatio(color, backgroundColor);

      // WCAG AA standartları
      const isLargeText = fontSize >= 18 || (fontSize >= 14 && parseInt(fontWeight) >= 700);
      const minContrast = isLargeText ? 3 : 4.5;

      if (contrastRatio < minContrast) {
        contrastIssues.push({
          id: `contrast-${index}`,
          severity: 'error',
          guideline: 'Renk Kontrastı',
          description: `Yetersiz kontrast oranı: ${contrastRatio.toFixed(2)}:1 (minimum: ${minContrast}:1)`,
          element: htmlElement,
          suggestion: 'Metin ve arka plan arasındaki kontrast oranını artırın',
          wcagCriterion: 'WCAG 1.4.3 (Level AA)',
        });
      }
    });

    return contrastIssues;
  };

  const validateForms = (): WCAGIssue[] => {
    const formIssues: WCAGIssue[] = [];
    const inputs = document.querySelectorAll('input, textarea, select');

    inputs.forEach((input, index) => {
      const htmlInput = input as HTMLInputElement;
      const id = htmlInput.id;
      const ariaLabel = htmlInput.getAttribute('aria-label');
      const ariaLabelledBy = htmlInput.getAttribute('aria-labelledby');

      // Label kontrolü
      if (!id || !document.querySelector(`label[for="${id}"]`)) {
        if (!ariaLabel && !ariaLabelledBy) {
          formIssues.push({
            id: `form-label-${index}`,
            severity: 'error',
            guideline: 'Form Erişilebilirliği',
            description: 'Form alanında etiket (label) eksik',
            element: htmlInput,
            suggestion: 'Form alanına <label> veya aria-label ekleyin',
            wcagCriterion: 'WCAG 1.3.1, 3.3.2 (Level A)',
          });
        }
      }

      // Required alan kontrolü
      if (htmlInput.required && !htmlInput.getAttribute('aria-required')) {
        formIssues.push({
          id: `form-required-${index}`,
          severity: 'warning',
          guideline: 'Form Erişilebilirliği',
          description: 'Zorunlu alan aria-required ile işaretlenmemiş',
          element: htmlInput,
          suggestion: 'Zorunlu alanlara aria-required="true" ekleyin',
          wcagCriterion: 'WCAG 3.3.2 (Level A)',
        });
      }
    });

    return formIssues;
  };

  const validateKeyboardAccess = (): WCAGIssue[] => {
    const keyboardIssues: WCAGIssue[] = [];
    const interactiveElements = document.querySelectorAll('a, button, input, select, textarea, [onclick], [role="button"]');

    interactiveElements.forEach((element, index) => {
      const htmlElement = element as HTMLElement;
      const tabIndex = htmlElement.tabIndex;

      // Negatif tabindex kontrolü (skip links hariç)
      if (tabIndex < -1) {
        keyboardIssues.push({
          id: `keyboard-tabindex-${index}`,
          severity: 'warning',
          guideline: 'Klavye Erişilebilirliği',
          description: 'Etkileşimli öğe klavye ile erişilebilir değil (tabindex < -1)',
          element: htmlElement,
          suggestion: 'tabindex değerini -1, 0 veya pozitif yapın',
          wcagCriterion: 'WCAG 2.1.1 (Level A)',
        });
      }

      // Onclick olan ama button/link olmayan elementler
      if (htmlElement.onclick && !['A', 'BUTTON', 'INPUT'].includes(htmlElement.tagName)) {
        if (!htmlElement.getAttribute('role') && tabIndex < 0) {
          keyboardIssues.push({
            id: `keyboard-onclick-${index}`,
            severity: 'error',
            guideline: 'Klavye Erişilebilirliği',
            description: 'Tıklanabilir öğe klavye ile erişilebilir değil',
            element: htmlElement,
            suggestion: 'role="button" ve tabindex="0" ekleyin veya <button> kullanın',
            wcagCriterion: 'WCAG 2.1.1 (Level A)',
          });
        }
      }
    });

    return keyboardIssues;
  };

  const validateARIA = (): WCAGIssue[] => {
    const ariaIssues: WCAGIssue[] = [];

    // ARIA role kontrolü
    const elementsWithRole = document.querySelectorAll('[role]');
    elementsWithRole.forEach((element, index) => {
      const htmlElement = element as HTMLElement;
      const role = htmlElement.getAttribute('role');

      // Geçersiz role değerleri
      const validRoles = [
        'alert', 'alertdialog', 'application', 'article', 'banner', 'button',
        'checkbox', 'columnheader', 'combobox', 'complementary', 'contentinfo',
        'definition', 'dialog', 'directory', 'document', 'feed', 'figure',
        'form', 'grid', 'gridcell', 'group', 'heading', 'img', 'link', 'list',
        'listbox', 'listitem', 'log', 'main', 'marquee', 'math', 'menu',
        'menubar', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 'navigation',
        'none', 'note', 'option', 'presentation', 'progressbar', 'radio',
        'radiogroup', 'region', 'row', 'rowgroup', 'rowheader', 'scrollbar',
        'search', 'searchbox', 'separator', 'slider', 'spinbutton', 'status',
        'switch', 'tab', 'table', 'tablist', 'tabpanel', 'term', 'textbox',
        'timer', 'toolbar', 'tooltip', 'tree', 'treegrid', 'treeitem',
      ];

      if (role && !validRoles.includes(role)) {
        ariaIssues.push({
          id: `aria-invalid-role-${index}`,
          severity: 'error',
          guideline: 'ARIA Kullanımı',
          description: `Geçersiz ARIA role: "${role}"`,
          element: htmlElement,
          suggestion: 'Geçerli bir ARIA role kullanın veya role özelliğini kaldırın',
          wcagCriterion: 'WCAG 4.1.2 (Level A)',
        });
      }
    });

    // aria-labelledby kontrolü
    const elementsWithLabelledBy = document.querySelectorAll('[aria-labelledby]');
    elementsWithLabelledBy.forEach((element, index) => {
      const htmlElement = element as HTMLElement;
      const labelledBy = htmlElement.getAttribute('aria-labelledby');

      if (labelledBy) {
        const labelIds = labelledBy.split(' ');
        labelIds.forEach(labelId => {
          if (!document.getElementById(labelId)) {
            ariaIssues.push({
              id: `aria-labelledby-${index}`,
              severity: 'error',
              guideline: 'ARIA Kullanımı',
              description: `aria-labelledby referansı bulunamadı: "${labelId}"`,
              element: htmlElement,
              suggestion: 'Referans verilen ID\'nin sayfada mevcut olduğundan emin olun',
              wcagCriterion: 'WCAG 4.1.2 (Level A)',
            });
          }
        });
      }
    });

    return ariaIssues;
  };

  const validateLandmarks = (): WCAGIssue[] => {
    const landmarkIssues: WCAGIssue[] = [];

    // Ana landmark kontrolü
    const mainLandmarks = document.querySelectorAll('main, [role="main"]');
    if (mainLandmarks.length === 0) {
      landmarkIssues.push({
        id: 'missing-main-landmark',
        severity: 'error',
        guideline: 'Sayfa Yapısı',
        description: 'Sayfada <main> veya role="main" bulunamadı',
        suggestion: 'Ana içerik için <main> elementi kullanın',
        wcagCriterion: 'WCAG 1.3.1 (Level A)',
      });
    } else if (mainLandmarks.length > 1) {
      landmarkIssues.push({
        id: 'multiple-main-landmarks',
        severity: 'warning',
        guideline: 'Sayfa Yapısı',
        description: `Sayfada ${mainLandmarks.length} adet main landmark var`,
        suggestion: 'Sayfada sadece bir adet main landmark olmalıdır',
        wcagCriterion: 'WCAG 1.3.1 (Level A)',
      });
    }

    // Navigation landmark kontrolü
    const navLandmarks = document.querySelectorAll('nav, [role="navigation"]');
    if (navLandmarks.length === 0) {
      landmarkIssues.push({
        id: 'missing-nav-landmark',
        severity: 'info',
        guideline: 'Sayfa Yapısı',
        description: 'Sayfada <nav> veya role="navigation" bulunamadı',
        suggestion: 'Navigasyon için <nav> elementi kullanın',
        wcagCriterion: 'WCAG 1.3.1 (Level A)',
      });
    }

    return landmarkIssues;
  };

  // Tüm validasyonları çalıştır
  const runValidation = useCallback(async () => {
    setIsValidating(true);

    // Kısa bir gecikme ekle (DOM güncellemelerini bekle)
    await new Promise(resolve => setTimeout(resolve, 100));

    const allIssues: WCAGIssue[] = [
      ...validateImages(),
      ...validateHeadings(),
      ...validateContrast(),
      ...validateForms(),
      ...validateKeyboardAccess(),
      ...validateARIA(),
      ...validateLandmarks(),
    ];

    setIssues(allIssues);
    setIsValidating(false);

    if (onIssuesFound) {
      onIssuesFound(allIssues);
    }
  }, [onIssuesFound]);

  // Otomatik validasyon
  useEffect(() => {
    if (autoValidate) {
      runValidation();

      const interval = setInterval(runValidation, validationInterval);
      return () => clearInterval(interval);
    }
  }, [autoValidate, validationInterval, runValidation]);

  // Issue kategorileri
  const issuesByCategory = issues.reduce((acc, issue) => {
    if (!acc[issue.guideline]) {
      acc[issue.guideline] = [];
    }
    acc[issue.guideline].push(issue);
    return acc;
  }, {} as Record<string, WCAGIssue[]>);

  // Severity ikonları
  const getSeverityIcon = (severity: WCAGIssue['severity']) => {
    switch (severity) {
      case 'error':
        return <Error color="error" />;
      case 'warning':
        return <Warning color="warning" />;
      case 'info':
        return <Info color="info" />;
    }
  };

  // Severity renkleri
  const getSeverityColor = (severity: WCAGIssue['severity']) => {
    switch (severity) {
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
    }
  };

  // Issue sayıları
  const errorCount = issues.filter(i => i.severity === 'error').length;
  const warningCount = issues.filter(i => i.severity === 'warning').length;
  const infoCount = issues.filter(i => i.severity === 'info').length;

  // Pozisyon stilleri
  const getPositionStyles = () => {
    const base = {
      position: 'fixed' as const,
      zIndex: 9999,
      maxWidth: 400,
      maxHeight: '80vh',
    };

    switch (position) {
      case 'bottom-right':
        return { ...base, bottom: 16, right: 16 };
      case 'bottom-left':
        return { ...base, bottom: 16, left: 16 };
      case 'top-right':
        return { ...base, top: 16, right: 16 };
      case 'top-left':
        return { ...base, top: 16, left: 16 };
    }
  };

  // Element'e scroll
  const scrollToElement = (element?: HTMLElement) => {
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      element.style.outline = '3px solid red';
      element.style.outlineOffset = '2px';

      setTimeout(() => {
        element.style.outline = '';
        element.style.outlineOffset = '';
      }, 3000);
    }
  };

  // Kategori toggle
  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  // Development mode check - render nothing if not in dev mode
  if (!shouldRender) {
    return null;
  }

  return (
    <Paper
      elevation={8}
      sx={{
        ...getPositionStyles(),
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          backgroundColor: theme.palette.primary.main,
          color: theme.palette.primary.contrastText,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
        }}
        onClick={() => setIsOpen(!isOpen)}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Accessibility />
          <Typography variant="h6">WCAG Validator</Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {errorCount > 0 && (
            <Chip
              label={errorCount}
              size="small"
              color="error"
              sx={{ fontWeight: 'bold' }}
            />
          )}
          {warningCount > 0 && (
            <Chip
              label={warningCount}
              size="small"
              sx={{ backgroundColor: 'warning.main', color: 'white' }}
            />
          )}
          {infoCount > 0 && (
            <Chip
              label={infoCount}
              size="small"
              color="info"
            />
          )}

          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              setIsOpen(!isOpen);
            }}
            sx={{ color: 'inherit' }}
          >
            {isOpen ? <ExpandLess /> : <ExpandMore />}
          </IconButton>
        </Box>
      </Box>

      {/* Progress Bar */}
      {isValidating && <LinearProgress />}

      {/* Content */}
      <Collapse in={isOpen}>
        <Box sx={{ maxHeight: 'calc(80vh - 100px)', overflow: 'auto' }}>
          {/* Özet */}
          <Box sx={{ p: 2 }}>
            {issues.length === 0 ? (
              <Alert severity="success" icon={<CheckCircle />}>
                Erişilebilirlik sorunu bulunamadı! 🎉
              </Alert>
            ) : (
              <Alert severity="warning">
                {issues.length} erişilebilirlik sorunu tespit edildi
              </Alert>
            )}

            <Button
              fullWidth
              variant="outlined"
              startIcon={<Refresh />}
              onClick={runValidation}
              disabled={isValidating}
              sx={{ mt: 2 }}
            >
              Yeniden Kontrol Et
            </Button>
          </Box>

          <Divider />

          {/* Issue Listesi */}
          {Object.entries(issuesByCategory).map(([category, categoryIssues]) => (
            <Box key={category}>
              <Box
                sx={{
                  p: 2,
                  backgroundColor: theme.palette.grey[100],
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  '&:hover': {
                    backgroundColor: theme.palette.grey[200],
                  },
                }}
                onClick={() => toggleCategory(category)}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="subtitle2" fontWeight="bold">
                    {category}
                  </Typography>
                  <Chip
                    label={categoryIssues.length}
                    size="small"
                    color={getSeverityColor(categoryIssues[0].severity)}
                  />
                </Box>

                <IconButton size="small">
                  {expandedCategories.has(category) ? <ExpandLess /> : <ExpandMore />}
                </IconButton>
              </Box>

              <Collapse in={expandedCategories.has(category)}>
                <List dense>
                  {categoryIssues.map((issue) => (
                    <ListItem
                      key={issue.id}
                      sx={{
                        flexDirection: 'column',
                        alignItems: 'flex-start',
                        borderBottom: `1px solid ${theme.palette.divider}`,
                        cursor: issue.element ? 'pointer' : 'default',
                        '&:hover': issue.element ? {
                          backgroundColor: theme.palette.action.hover,
                        } : {},
                      }}
                      onClick={() => scrollToElement(issue.element)}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', width: '100%', gap: 1 }}>
                        <ListItemIcon sx={{ minWidth: 'auto', mt: 0.5 }}>
                          {getSeverityIcon(issue.severity)}
                        </ListItemIcon>

                        <Box sx={{ flex: 1 }}>
                          <Typography variant="body2" fontWeight="medium">
                            {issue.description}
                          </Typography>

                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                            {issue.wcagCriterion}
                          </Typography>

                          <Typography variant="caption" sx={{ display: 'block', mt: 1, fontStyle: 'italic' }}>
                            💡 {issue.suggestion}
                          </Typography>
                        </Box>
                      </Box>
                    </ListItem>
                  ))}
                </List>
              </Collapse>
            </Box>
          ))}
        </Box>
      </Collapse>
    </Paper>
  );
};

export default WCAGValidator;
