/**
 * NumberBlocks Component - Diskalkuli Desteği
 *
 * Base-10 blok sistemi ile sayıları görselleştiren interaktif component.
 * Öğrencilerin basamak değerini ve sayı kavramını somut olarak anlamalarına yardımcı olur.
 *
 * Gereksinimler: REQ-51.1 - REQ-51.5
 */

import * as React from 'react';
import {  useState, useCallback, useMemo  } from 'react';
import './NumberBlocks.css';

interface NumberBlocksProps {
  initialValue?: number;
  maxValue?: number;
  showAnimation?: boolean;
  onValueChange?: (value: number) => void;
  readOnly?: boolean;
}

interface BlockRepresentation {
  thousands: number;
  hundreds: number;
  tens: number;
  ones: number;
}

const NumberBlocks: React.FC<NumberBlocksProps> = ({
  initialValue = 0,
  maxValue = 9999,
  showAnimation = true,
  onValueChange,
  readOnly = false,
}) => {
  const [value, setValue] = useState<number>(initialValue);
  const [draggedBlock, setDraggedBlock] = useState<string | null>(null);
  const [animatingBlocks, setAnimatingBlocks] = useState<Set<string>>(new Set());

  // REQ-51.1: Base-10 blok sistemini görselleştir
  const blockRepresentation = useMemo((): BlockRepresentation => {
    const thousands = Math.floor(value / 1000);
    const hundreds = Math.floor((value % 1000) / 100);
    const tens = Math.floor((value % 100) / 10);
    const ones = value % 10;

    return { thousands, hundreds, tens, ones };
  }, [value]);

  // REQ-51.3: Sayı girişinde otomatik blok temsili
  const handleNumberInput = useCallback((newValue: number) => {
    if (newValue < 0 || newValue > maxValue) {return;}

    setValue(newValue);
    onValueChange?.(newValue);

    // REQ-51.4: Animasyon göster
    if (showAnimation) {
      setAnimatingBlocks(new Set(['all']));
      setTimeout(() => setAnimatingBlocks(new Set()), 600);
    }
  }, [maxValue, onValueChange, showAnimation]);

  // REQ-51.2: Drag-and-drop ile interaktif manipülasyon
  const handleBlockDragStart = useCallback((blockType: string) => {
    if (readOnly) {return;}
    setDraggedBlock(blockType);
  }, [readOnly]);

  const handleBlockDragEnd = useCallback(() => {
    setDraggedBlock(null);
  }, []);

  const handleBlockClick = useCallback((blockType: string, operation: 'add' | 'remove') => {
    if (readOnly) {return;}

    const blockValues: Record<string, number> = {
      thousands: 1000,
      hundreds: 100,
      tens: 10,
      ones: 1,
    };

    const changeValue = blockValues[blockType];
    const newValue = operation === 'add'
      ? Math.min(value + changeValue, maxValue)
      : Math.max(value - changeValue, 0);

    handleNumberInput(newValue);
  }, [value, maxValue, readOnly, handleNumberInput]);

  // REQ-51.4: Toplama/çıkarma animasyonu
  const handleOperation = useCallback((operand: number, operation: 'add' | 'subtract') => {
    if (readOnly) {return;}

    const newValue = operation === 'add'
      ? Math.min(value + operand, maxValue)
      : Math.max(value - operand, 0);

    if (showAnimation) {
      setAnimatingBlocks(new Set(['operation']));
      setTimeout(() => {
        handleNumberInput(newValue);
        setAnimatingBlocks(new Set());
      }, 300);
    } else {
      handleNumberInput(newValue);
    }
  }, [value, maxValue, readOnly, showAnimation, handleNumberInput]);

  // REQ-51.5: Her basamağı farklı renk ve boyutta göster
  const renderBlock = (type: string, count: number, color: string, size: string) => {
    if (count === 0) {return null;}

    const isAnimating = animatingBlocks.has('all') || animatingBlocks.has('operation');

    return (
      <div className={`block-group ${type}-group`} key={type}>
        <div className="block-label">{type.charAt(0).toUpperCase() + type.slice(1)}</div>
        <div className="blocks-container">
          {Array.from({ length: count }).map((_, index) => (
            <div
              key={`${type}-${index}`}
              className={`block ${type}-block ${isAnimating ? 'animating' : ''} ${draggedBlock === type ? 'dragging' : ''}`}
              style={{
                backgroundColor: color,
                width: size,
                height: size,
              }}
              draggable={!readOnly}
              onDragStart={() => handleBlockDragStart(type)}
              onDragEnd={handleBlockDragEnd}
              onClick={() => !readOnly && handleBlockClick(type, 'remove')}
              onKeyDown={(e) => {
                if ((e.key === 'Enter' || e.key === ' ') && !readOnly) {
                  e.preventDefault();
                  handleBlockClick(type, 'remove');
                }
              }}
              role="button"
              tabIndex={readOnly ? -1 : 0}
              aria-label={`${type} bloğu ${index + 1} / ${count} - Kaldırmak için Enter veya Space tuşuna basın`}
            >
              <span className="block-value">
                {type === 'thousands' ? '1000' : type === 'hundreds' ? '100' : type === 'tens' ? '10' : '1'}
              </span>
            </div>
          ))}
        </div>
        {!readOnly && (
          <div className="block-controls">
            <button
              onClick={() => handleBlockClick(type, 'add')}
              className="block-btn add-btn"
              aria-label={`Add ${type} block`}
            >
              +
            </button>
            <button
              onClick={() => handleBlockClick(type, 'remove')}
              className="block-btn remove-btn"
              aria-label={`Remove ${type} block`}
              disabled={count === 0}
            >
              −
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="number-blocks-container" role="region" aria-label="Number blocks visualization">
      {/* REQ-9.2: Screen reader announcements for value changes */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        Güncel sayı: {value}
      </div>

      <div className="number-blocks-header">
        <h3>Sayı Blokları - Base-10 Sistemi</h3>
        <div className="current-value">
          <label htmlFor="number-input">Sayı:</label>
          <input
            id="number-input"
            type="number"
            value={value}
            onChange={(e) => handleNumberInput(parseInt(e.target.value) || 0)}
            min={0}
            max={maxValue}
            disabled={readOnly}
            aria-label="Current number value"
          />
        </div>
      </div>

      <div className="blocks-visualization">
        {renderBlock('thousands', blockRepresentation.thousands, '#D32F2F', '120px')}
        {renderBlock('hundreds', blockRepresentation.hundreds, '#1976D2', '90px')}
        {renderBlock('tens', blockRepresentation.tens, '#F57C00', '60px')}
        {renderBlock('ones', blockRepresentation.ones, '#388E3C', '30px')}
      </div>

      {!readOnly && (
        <div className="operation-controls">
          <h4>İşlemler</h4>
          <div className="operation-buttons">
            <button onClick={() => handleOperation(1, 'add')} className="op-btn">+1</button>
            <button onClick={() => handleOperation(10, 'add')} className="op-btn">+10</button>
            <button onClick={() => handleOperation(100, 'add')} className="op-btn">+100</button>
            <button onClick={() => handleOperation(1000, 'add')} className="op-btn">+1000</button>
            <button onClick={() => handleOperation(1, 'subtract')} className="op-btn">-1</button>
            <button onClick={() => handleOperation(10, 'subtract')} className="op-btn">-10</button>
            <button onClick={() => handleOperation(100, 'subtract')} className="op-btn">-100</button>
            <button onClick={() => handleOperation(1000, 'subtract')} className="op-btn">-1000</button>
          </div>
        </div>
      )}

      <div className="block-legend">
        <h4>Basamak Değerleri</h4>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#D32F2F' }}></div>
            <span>Binler (1000) - Kırmızı</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#1976D2' }}></div>
            <span>Yüzler (100) - Mavi</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#F57C00' }}></div>
            <span>Onlar (10) - Turuncu</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#388E3C' }}></div>
            <span>Birler (1) - Yeşil</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NumberBlocks;
