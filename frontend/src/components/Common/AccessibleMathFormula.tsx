/**
 * WCAG 2.1 Level AA Uyumlu Matematik Formül Bileşeni
 * 
 * Özellikler:
 * - MathML desteği ile ekran okuyucu uyumluluğu
 * - Alternatif metin açıklamaları
 * - Klavye navigasyonu
 * - Görsel ve işitsel erişilebilirlik
 * - LaTeX ve MathML format desteği
 */

import React, { useEffect, useRef, useState } from 'react';
import { Box, Typography, IconButton, Tooltip, Paper, useTheme } from '@mui/material';
import { VolumeUp, ContentCopy, ZoomIn, ZoomOut, Info } from '@mui/icons-material';
import { useScreenReader } from '../../hooks/useScreenReader';
import { useAccessibilitySettings } from '../../hooks/useAccessibilitySettings';

interface AccessibleMathFormulaProps {
  // LaTeX formatında formül
  latex?: string;
  
  // MathML formatında formül
  mathml?: string;
  
  // Formülün Türkçe açıklaması (ekran okuyucu için)
  description: string;
  
  // Formülün kısa açıklaması
  label?: string;
  
  // Formül ID'si (benzersiz tanımlayıcı)
  id?: string;
  
  // Inline veya block display
  display?: 'inline' | 'block';
  
  // Zoom seviyesi
  initialZoom?: number;
  
  // Sesli okuma desteği
  enableAudio?: boolean;
  
  // Kopyalama desteği
  enableCopy?: boolean;
  
  // Detaylı açıklama göster
  showDetailedDescription?: boolean;
  
  className?: string;
}

const AccessibleMathFormula: React.FC<AccessibleMathFormulaProps> = ({
  latex,
  mathml,
  description,
  label,
  id,
  display = 'inline',
  initialZoom = 1,
  enableAudio = true,
  enableCopy = true,
  showDetailedDescription = false,
  className
}) => {
  const theme = useTheme();
  const { settings } = useAccessibilitySettings();
  const { announce } = useScreenReader();
  
  const formulaRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(initialZoom);
  const [showDescription, setShowDescription] = useState(showDetailedDescription);
  const [isSpeaking, setIsSpeaking] = useState(false);
  
  // Benzersiz ID oluştur
  const formulaId = id || `math-formula-${Math.random().toString(36).substring(2, 11)}`;
  const descriptionId = `${formulaId}-description`;
  const labelId = `${formulaId}-label`;

  // LaTeX'i MathML'e çevir (basit dönüşüm)
  const convertLatexToMathML = (latexStr: string): string => {
    // Bu gerçek bir projede MathJax veya KaTeX kullanılmalı
    // Burada basit bir örnek gösteriyoruz
    
    let mathmlStr = '<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">';
    
    // Basit dönüşümler
    if (latexStr.includes('\\frac')) {
      // Kesir: \frac{a}{b} -> <mfrac><mi>a</mi><mi>b</mi></mfrac>
      const fracMatch = latexStr.match(/\\frac\{([^}]+)\}\{([^}]+)\}/);
      if (fracMatch) {
        mathmlStr += `<mfrac><mi>${fracMatch[1]}</mi><mi>${fracMatch[2]}</mi></mfrac>`;
      }
    } else if (latexStr.includes('^')) {
      // Üs: x^2 -> <msup><mi>x</mi><mn>2</mn></msup>
      const supMatch = latexStr.match(/([a-zA-Z])\^(\d+)/);
      if (supMatch) {
        mathmlStr += `<msup><mi>${supMatch[1]}</mi><mn>${supMatch[2]}</mn></msup>`;
      }
    } else if (latexStr.includes('_')) {
      // Alt: x_1 -> <msub><mi>x</mi><mn>1</mn></msub>
      const subMatch = latexStr.match(/([a-zA-Z])_(\d+)/);
      if (subMatch) {
        mathmlStr += `<msub><mi>${subMatch[1]}</mi><mn>${subMatch[2]}</mn></msub>`;
      }
    } else if (latexStr.includes('\\sqrt')) {
      // Karekök: \sqrt{x} -> <msqrt><mi>x</mi></msqrt>
      const sqrtMatch = latexStr.match(/\\sqrt\{([^}]+)\}/);
      if (sqrtMatch) {
        mathmlStr += `<msqrt><mi>${sqrtMatch[1]}</mi></msqrt>`;
      }
    } else {
      // Basit ifade
      mathmlStr += `<mi>${latexStr}</mi>`;
    }
    
    mathmlStr += '</math>';
    return mathmlStr;
  };

  // MathML içeriğini al
  const getMathMLContent = (): string => {
    if (mathml) {
      return mathml;
    } else if (latex) {
      return convertLatexToMathML(latex);
    }
    return '';
  };

  // Formülü sesli oku
  const speakFormula = () => {
    if ('speechSynthesis' in window) {
      setIsSpeaking(true);
      
      // Mevcut konuşmayı durdur
      window.speechSynthesis.cancel();
      
      // Yeni konuşma oluştur
      const utterance = new SpeechSynthesisUtterance(description);
      utterance.lang = 'tr-TR';
      utterance.rate = settings.speechRate || 1;
      utterance.pitch = 1;
      
      utterance.onend = () => {
        setIsSpeaking(false);
        announce('Formül okunması tamamlandı', 'polite');
      };
      
      utterance.onerror = () => {
        setIsSpeaking(false);
        announce('Formül okunamadı', 'assertive');
      };
      
      window.speechSynthesis.speak(utterance);
      announce('Formül okunuyor', 'polite');
    } else {
      announce('Sesli okuma desteklenmiyor', 'assertive');
    }
  };

  // Formülü kopyala
  const copyFormula = async () => {
    const textToCopy = latex || mathml || description;
    
    try {
      await navigator.clipboard.writeText(textToCopy);
      announce('Formül panoya kopyalandı', 'polite');
    } catch (error) {
      announce('Formül kopyalanamadı', 'assertive');
    }
  };

  // Zoom kontrolü
  const handleZoomIn = () => {
    const newZoom = Math.min(zoom + 0.2, 3);
    setZoom(newZoom);
    announce(`Zoom seviyesi ${Math.round(newZoom * 100)}%`, 'polite');
  };

  const handleZoomOut = () => {
    const newZoom = Math.max(zoom - 0.2, 0.5);
    setZoom(newZoom);
    announce(`Zoom seviyesi ${Math.round(newZoom * 100)}%`, 'polite');
  };

  // Açıklama toggle
  const toggleDescription = () => {
    const newState = !showDescription;
    setShowDescription(newState);
    announce(
      newState ? 'Detaylı açıklama gösteriliyor' : 'Detaylı açıklama gizlendi',
      'polite'
    );
  };

  // Klavye kısayolları
  const handleKeyDown = (event: React.KeyboardEvent) => {
    switch (event.key) {
      case '+':
      case '=':
        event.preventDefault();
        handleZoomIn();
        break;
      case '-':
        event.preventDefault();
        handleZoomOut();
        break;
      case 's':
        if (enableAudio) {
          event.preventDefault();
          speakFormula();
        }
        break;
      case 'c':
        if (enableCopy && (event.ctrlKey || event.metaKey)) {
          event.preventDefault();
          copyFormula();
        }
        break;
      case 'i':
        event.preventDefault();
        toggleDescription();
        break;
    }
  };

  // Component mount
  useEffect(() => {
    // MathJax veya KaTeX render (gerçek implementasyonda)
    // Bu örnekte MathML direkt kullanıyoruz
    
    return () => {
      // Cleanup: Sesli okumayı durdur
      if (isSpeaking && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [isSpeaking]);

  const mathMLContent = getMathMLContent();

  return (
    <Box
      ref={formulaRef}
      className={className}
      sx={{
        display: display === 'inline' ? 'inline-flex' : 'flex',
        flexDirection: 'column',
        alignItems: display === 'inline' ? 'center' : 'flex-start',
        gap: 1,
        my: display === 'block' ? 2 : 0,
        mx: display === 'inline' ? 0.5 : 0,
      }}
      role="math"
      aria-labelledby={label ? labelId : undefined}
      aria-describedby={descriptionId}
      tabIndex={0}
      onKeyDown={handleKeyDown}
    >
      {/* Label */}
      {label && (
        <Typography
          id={labelId}
          variant="caption"
          sx={{
            fontWeight: 'bold',
            color: theme.palette.text.secondary,
            mb: 0.5,
          }}
        >
          {label}
        </Typography>
      )}

      {/* Formül Container */}
      <Paper
        elevation={display === 'block' ? 1 : 0}
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 1,
          p: display === 'block' ? 2 : 0.5,
          backgroundColor: display === 'block' ? 'background.paper' : 'transparent',
          border: settings.highContrast ? '2px solid black' : 'none',
          '&:focus-within': {
            outline: `3px solid ${theme.palette.primary.main}`,
            outlineOffset: 2,
          },
        }}
      >
        {/* MathML Formül */}
        <Box
          id={formulaId}
          sx={{
            transform: `scale(${zoom})`,
            transformOrigin: 'left center',
            transition: 'transform 0.2s ease',
            fontSize: {
              small: '1rem',
              medium: '1.2rem',
              large: '1.4rem',
              'extra-large': '1.6rem',
            }[settings.fontSize],
            // Yüksek kontrast
            ...(settings.highContrast && {
              filter: 'contrast(2)',
            }),
          }}
          dangerouslySetInnerHTML={{ __html: mathMLContent }}
        />

        {/* Kontrol Butonları */}
        {display === 'block' && (
          <Box sx={{ display: 'flex', gap: 0.5, ml: 'auto' }}>
            {/* Sesli Okuma */}
            {enableAudio && (
              <Tooltip title="Formülü sesli oku (S)">
                <IconButton
                  size="small"
                  onClick={speakFormula}
                  disabled={isSpeaking}
                  aria-label="Formülü sesli oku"
                  sx={{
                    minWidth: 44,
                    minHeight: 44,
                  }}
                >
                  <VolumeUp fontSize="small" />
                </IconButton>
              </Tooltip>
            )}

            {/* Kopyala */}
            {enableCopy && (
              <Tooltip title="Formülü kopyala (Ctrl+C)">
                <IconButton
                  size="small"
                  onClick={copyFormula}
                  aria-label="Formülü kopyala"
                  sx={{
                    minWidth: 44,
                    minHeight: 44,
                  }}
                >
                  <ContentCopy fontSize="small" />
                </IconButton>
              </Tooltip>
            )}

            {/* Zoom In */}
            <Tooltip title="Yakınlaştır (+)">
              <IconButton
                size="small"
                onClick={handleZoomIn}
                disabled={zoom >= 3}
                aria-label="Formülü yakınlaştır"
                sx={{
                  minWidth: 44,
                  minHeight: 44,
                }}
              >
                <ZoomIn fontSize="small" />
              </IconButton>
            </Tooltip>

            {/* Zoom Out */}
            <Tooltip title="Uzaklaştır (-)">
              <IconButton
                size="small"
                onClick={handleZoomOut}
                disabled={zoom <= 0.5}
                aria-label="Formülü uzaklaştır"
                sx={{
                  minWidth: 44,
                  minHeight: 44,
                }}
              >
                <ZoomOut fontSize="small" />
              </IconButton>
            </Tooltip>

            {/* Açıklama */}
            <Tooltip title="Detaylı açıklama (I)">
              <IconButton
                size="small"
                onClick={toggleDescription}
                aria-label="Detaylı açıklamayı göster"
                aria-expanded={showDescription}
                sx={{
                  minWidth: 44,
                  minHeight: 44,
                  color: showDescription ? 'primary.main' : 'inherit',
                }}
              >
                <Info fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        )}
      </Paper>

      {/* Ekran Okuyucu için Açıklama (gizli) */}
      <Typography
        id={descriptionId}
        sx={{
          position: 'absolute',
          left: -9999,
          width: 1,
          height: 1,
          overflow: 'hidden',
        }}
      >
        {description}
      </Typography>

      {/* Görünür Detaylı Açıklama */}
      {showDescription && (
        <Paper
          elevation={1}
          sx={{
            p: 2,
            mt: 1,
            backgroundColor: theme.palette.background.default,
            border: `1px solid ${theme.palette.divider}`,
            maxWidth: 600,
          }}
          role="region"
          aria-label="Formül açıklaması"
        >
          <Typography
            variant="body2"
            sx={{
              lineHeight: 1.8,
              fontSize: {
                small: '0.875rem',
                medium: '1rem',
                large: '1.125rem',
                'extra-large': '1.25rem',
              }[settings.fontSize],
            }}
          >
            {description}
          </Typography>
        </Paper>
      )}

      {/* Klavye Kısayolları Bilgisi */}
      {display === 'block' && settings.keyboardNavigation && (
        <Typography
          variant="caption"
          sx={{
            color: theme.palette.text.secondary,
            fontSize: '0.75rem',
            mt: 0.5,
          }}
        >
          Kısayollar: S (Sesli oku), +/- (Zoom), I (Açıklama), Ctrl+C (Kopyala)
        </Typography>
      )}
    </Box>
  );
};

export default AccessibleMathFormula;
