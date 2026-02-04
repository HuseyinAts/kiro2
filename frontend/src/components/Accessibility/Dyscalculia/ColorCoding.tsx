/**
 * ColorCoding Component - Renkli Kodlama Sistemi
 * 
 * Diskalkuli desteği için matematiksel ifadelerde renk kodlama.
 * Pozitif/negatif sayılar, işlemler, parantezler ve değişkenler için renk desteği.
 * 
 * Gereksinimler: REQ-51.61 - REQ-51.80
 * 
 * @author Kiro AI
 * @date 2025-10-24
 */

import React, { useState, useEffect } from 'react';
import './ColorCoding.css';

/**
 * Renk şeması tipleri
 */
export type ColorScheme = 'default' | 'high-contrast' | 'colorblind-friendly' | 'custom';

/**
 * Renk kodlama ayarları
 */
export interface ColorCodingSettings {
  // Pozitif/negatif renkleri (REQ-51.61-51.65)
  positiveColor: string;
  negativeColor: string;
  zeroColor: string;
  
  // İşlem renkleri (REQ-51.66-51.70)
  additionColor: string;
  subtractionColor: string;
  multiplicationColor: string;
  divisionColor: string;
  
  // Parantez seviyeleri (REQ-51.71-51.75)
  parenthesesColors: string[];
  
  // Değişken/sabit renkleri (REQ-51.76-51.80)
  variableColor: string;
  constantColor: string;
  coefficientColor: string;
  
  // Genel ayarlar
  colorScheme: ColorScheme;
  highContrast: boolean;
  showLegend: boolean;
}

/**
 * Varsayılan renk ayarları
 */
const DEFAULT_SETTINGS: ColorCodingSettings = {
  // Pozitif/negatif (REQ-51.61-51.65)
  positiveColor: '#10b981', // Yeşil - pozitif sayılar
  negativeColor: '#ef4444', // Kırmızı - negatif sayılar
  zeroColor: '#6b7280',     // Gri - sıfır
  
  // İşlemler (REQ-51.66-51.70)
  additionColor: '#3b82f6',      // Mavi - toplama
  subtractionColor: '#f59e0b',   // Turuncu - çıkarma
  multiplicationColor: '#8b5cf6', // Mor - çarpma
  divisionColor: '#ec4899',      // Pembe - bölme
  
  // Parantezler (REQ-51.71-51.75) - Rainbow parentheses
  parenthesesColors: [
    '#ef4444', // Kırmızı - seviye 1
    '#f59e0b', // Turuncu - seviye 2
    '#10b981', // Yeşil - seviye 3
    '#3b82f6', // Mavi - seviye 4
    '#8b5cf6', // Mor - seviye 5
    '#ec4899', // Pembe - seviye 6
  ],
  
  // Değişken/sabit (REQ-51.76-51.80)
  variableColor: '#06b6d4',   // Cyan - değişkenler (x, y, z)
  constantColor: '#84cc16',   // Lime - sabitler (π, e)
  coefficientColor: '#f97316', // Orange - katsayılar (2x, 3y)
  
  colorScheme: 'default',
  highContrast: false,
  showLegend: true,
};

/**
 * Yüksek kontrast renk şeması (WCAG AAA uyumlu)
 */
const HIGH_CONTRAST_SETTINGS: Partial<ColorCodingSettings> = {
  positiveColor: '#00ff00',
  negativeColor: '#ff0000',
  zeroColor: '#ffffff',
  additionColor: '#0000ff',
  subtractionColor: '#ffff00',
  multiplicationColor: '#ff00ff',
  divisionColor: '#00ffff',
  variableColor: '#00ffff',
  constantColor: '#ffff00',
  coefficientColor: '#ff8800',
};

/**
 * Renk körlüğü dostu renk şeması
 */
const COLORBLIND_FRIENDLY_SETTINGS: Partial<ColorCodingSettings> = {
  positiveColor: '#0173b2',  // Mavi
  negativeColor: '#de8f05',  // Turuncu
  zeroColor: '#949494',      // Gri
  additionColor: '#029e73',  // Yeşil-mavi
  subtractionColor: '#cc78bc', // Pembe-mor
  multiplicationColor: '#ca9161', // Kahverengi
  divisionColor: '#ece133',  // Sarı
  variableColor: '#56b4e9',  // Açık mavi
  constantColor: '#009e73',  // Yeşil
  coefficientColor: '#f0e442', // Sarı
};

/**
 * Token tipi
 */
type TokenType = 
  | 'positive' 
  | 'negative' 
  | 'zero'
  | 'addition'
  | 'subtraction'
  | 'multiplication'
  | 'division'
  | 'parenthesis'
  | 'variable'
  | 'constant'
  | 'coefficient'
  | 'text';

/**
 * Token interface
 */
interface Token {
  value: string;
  type: TokenType;
  level?: number; // Parantez seviyesi için
}

/**
 * Props interface
 */
interface ColorCodingProps {
  expression: string;
  settings?: Partial<ColorCodingSettings>;
  className?: string;
  'aria-label'?: string;
}

/**
 * ColorCoding Component
 * 
 * Matematiksel ifadeleri renk kodlayarak görselleştirir.
 * 
 * @example
 * ```tsx
 * <ColorCoding 
 *   expression="2x + 3y - 5 = 0"
 *   settings={{ highContrast: true }}
 * />
 * ```
 */
const ColorCoding: React.FC<ColorCodingProps> = ({
  expression,
  settings: customSettings,
  className = '',
  'aria-label': ariaLabel,
}) => {
  const [settings, setSettings] = useState<ColorCodingSettings>({
    ...DEFAULT_SETTINGS,
    ...customSettings,
  });

  // Ayarlar değiştiğinde güncelle
  useEffect(() => {
    let newSettings = { ...DEFAULT_SETTINGS, ...customSettings };
    
    // Yüksek kontrast modu
    if (newSettings.highContrast) {
      newSettings = { ...newSettings, ...HIGH_CONTRAST_SETTINGS };
    }
    
    // Renk körlüğü dostu mod
    if (newSettings.colorScheme === 'colorblind-friendly') {
      newSettings = { ...newSettings, ...COLORBLIND_FRIENDLY_SETTINGS };
    }
    
    setSettings(newSettings);
  }, [customSettings]);

  /**
   * İfadeyi token'lara ayır
   * REQ-51.61-51.80: Tüm renk kodlama kurallarını uygula
   */
  const tokenize = (expr: string): Token[] => {
    const tokens: Token[] = [];
    let i = 0;
    let parenthesisLevel = 0;

    while (i < expr.length) {
      const char = expr[i];

      // Boşlukları atla
      if (char === ' ') {
        i++;
        continue;
      }

      // Parantezler (REQ-51.71-51.75)
      if (char === '(') {
        tokens.push({ value: char, type: 'parenthesis', level: parenthesisLevel });
        parenthesisLevel++;
        i++;
        continue;
      }
      if (char === ')') {
        parenthesisLevel--;
        tokens.push({ value: char, type: 'parenthesis', level: parenthesisLevel });
        i++;
        continue;
      }

      // İşlemler (REQ-51.66-51.70)
      if (char === '+') {
        tokens.push({ value: char, type: 'addition' });
        i++;
        continue;
      }
      if (char === '-') {
        // Negatif sayı mı yoksa çıkarma işlemi mi?
        const prevToken = tokens[tokens.length - 1];
        const isNegativeNumber = !prevToken || 
          prevToken.type === 'addition' || 
          prevToken.type === 'subtraction' ||
          prevToken.type === 'multiplication' ||
          prevToken.type === 'division' ||
          prevToken.type === 'parenthesis' && prevToken.value === '(';
        
        if (isNegativeNumber) {
          // Negatif sayı olarak işle
          let numStr = '-';
          i++;
          while (i < expr.length && /[\d.]/.test(expr[i])) {
            numStr += expr[i];
            i++;
          }
          tokens.push({ value: numStr, type: 'negative' });
        } else {
          tokens.push({ value: char, type: 'subtraction' });
          i++;
        }
        continue;
      }
      if (char === '*' || char === '×') {
        tokens.push({ value: '×', type: 'multiplication' });
        i++;
        continue;
      }
      if (char === '/' || char === '÷') {
        tokens.push({ value: '÷', type: 'division' });
        i++;
        continue;
      }

      // Sayılar (REQ-51.61-51.65)
      if (/\d/.test(char)) {
        let numStr = '';
        let hasVariable = false;
        
        // Sayıyı oku
        while (i < expr.length && /[\d.]/.test(expr[i])) {
          numStr += expr[i];
          i++;
        }
        
        // Katsayı mı kontrol et (REQ-51.76-51.80)
        if (i < expr.length && /[a-zA-Z]/.test(expr[i])) {
          hasVariable = true;
          const varChar = expr[i];
          i++;
          tokens.push({ value: numStr, type: 'coefficient' });
          tokens.push({ value: varChar, type: 'variable' });
        } else {
          const num = parseFloat(numStr);
          if (num === 0) {
            tokens.push({ value: numStr, type: 'zero' });
          } else if (num > 0) {
            tokens.push({ value: numStr, type: 'positive' });
          } else {
            tokens.push({ value: numStr, type: 'negative' });
          }
        }
        continue;
      }

      // Değişkenler ve sabitler (REQ-51.76-51.80)
      // Özel sabitler (π, e)
      if (char === 'π') {
        tokens.push({ value: 'π', type: 'constant' });
        i++;
        continue;
      }
      
      if (/[a-zA-Z]/.test(char)) {
        // 'e' sabiti (Euler sayısı) - tek başına veya üs olarak
        if (char === 'e' && (i === 0 || !/[a-zA-Z]/.test(expr[i - 1]))) {
          const nextChar = i + 1 < expr.length ? expr[i + 1] : '';
          // e^x gibi durumlarda veya tek başına 'e' ise sabit
          if (nextChar === '^' || nextChar === ' ' || nextChar === '+' || nextChar === '-' || nextChar === ')' || i === expr.length - 1) {
            tokens.push({ value: 'e', type: 'constant' });
            i++;
            continue;
          }
        }
        
        // Diğer harfler değişken
        tokens.push({ value: char, type: 'variable' });
        i++;
        continue;
      }

      // Diğer karakterler
      tokens.push({ value: char, type: 'text' });
      i++;
    }

    return tokens;
  };

  /**
   * Token'a renk ata
   */
  const getTokenColor = (token: Token): string => {
    switch (token.type) {
      case 'positive':
        return settings.positiveColor;
      case 'negative':
        return settings.negativeColor;
      case 'zero':
        return settings.zeroColor;
      case 'addition':
        return settings.additionColor;
      case 'subtraction':
        return settings.subtractionColor;
      case 'multiplication':
        return settings.multiplicationColor;
      case 'division':
        return settings.divisionColor;
      case 'parenthesis':
        return settings.parenthesesColors[token.level! % settings.parenthesesColors.length];
      case 'variable':
        return settings.variableColor;
      case 'constant':
        return settings.constantColor;
      case 'coefficient':
        return settings.coefficientColor;
      default:
        return 'inherit';
    }
  };

  const tokens = tokenize(expression);

  return (
    <div 
      className={`color-coding ${className}`}
      role="math"
      aria-label={ariaLabel || `Renkli kodlanmış matematiksel ifade: ${expression}`}
    >
      <div className="color-coding__expression">
        {tokens.map((token, index) => (
          <span
            key={index}
            className={`color-coding__token color-coding__token--${token.type}`}
            style={{ color: getTokenColor(token) }}
            data-type={token.type}
            data-level={token.level}
          >
            {token.value}
          </span>
        ))}
      </div>

      {settings.showLegend && (
        <div className="color-coding__legend" role="region" aria-label="Renk açıklaması">
          <h4 className="color-coding__legend-title">Renk Açıklaması</h4>
          
          <div className="color-coding__legend-section">
            <h5>Sayılar</h5>
            <div className="color-coding__legend-item">
              <span className="color-coding__legend-color" style={{ backgroundColor: settings.positiveColor }} />
              <span>Pozitif sayılar</span>
            </div>
            <div className="color-coding__legend-item">
              <span className="color-coding__legend-color" style={{ backgroundColor: settings.negativeColor }} />
              <span>Negatif sayılar</span>
            </div>
            <div className="color-coding__legend-item">
              <span className="color-coding__legend-color" style={{ backgroundColor: settings.zeroColor }} />
              <span>Sıfır</span>
            </div>
          </div>

          <div className="color-coding__legend-section">
            <h5>İşlemler</h5>
            <div className="color-coding__legend-item">
              <span className="color-coding__legend-color" style={{ backgroundColor: settings.additionColor }} />
              <span>Toplama (+)</span>
            </div>
            <div className="color-coding__legend-item">
              <span className="color-coding__legend-color" style={{ backgroundColor: settings.subtractionColor }} />
              <span>Çıkarma (−)</span>
            </div>
            <div className="color-coding__legend-item">
              <span className="color-coding__legend-color" style={{ backgroundColor: settings.multiplicationColor }} />
              <span>Çarpma (×)</span>
            </div>
            <div className="color-coding__legend-item">
              <span className="color-coding__legend-color" style={{ backgroundColor: settings.divisionColor }} />
              <span>Bölme (÷)</span>
            </div>
          </div>

          <div className="color-coding__legend-section">
            <h5>Değişkenler</h5>
            <div className="color-coding__legend-item">
              <span className="color-coding__legend-color" style={{ backgroundColor: settings.variableColor }} />
              <span>Değişkenler (x, y, z)</span>
            </div>
            <div className="color-coding__legend-item">
              <span className="color-coding__legend-color" style={{ backgroundColor: settings.constantColor }} />
              <span>Sabitler (π, e)</span>
            </div>
            <div className="color-coding__legend-item">
              <span className="color-coding__legend-color" style={{ backgroundColor: settings.coefficientColor }} />
              <span>Katsayılar (2x, 3y)</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ColorCoding;
