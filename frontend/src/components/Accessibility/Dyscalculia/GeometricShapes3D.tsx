/**
 * GeometricShapes3D Component - Diskalkuli Desteği
 * 
 * 3D geometrik şekilleri render eden ve manipüle edilebilen interaktif component.
 * Öğrencilerin 3D şekilleri, hacim ve yüzey alanı kavramlarını görsel olarak anlamalarına yardımcı olur.
 * 
 * Gereksinimler: REQ-51.11 - REQ-51.15
 * 
 * Not: Bu component basit CSS 3D transforms kullanır. 
 * Daha gelişmiş 3D için Three.js entegrasyonu gerekir.
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import './GeometricShapes3D.css';

type ShapeType = 'cube' | 'sphere' | 'cylinder' | 'cone' | 'pyramid';

interface Shape3DProps {
  initialShape?: ShapeType;
  initialSize?: number;
  showMeasurements?: boolean;
  showNet?: boolean;
  onShapeChange?: (shape: ShapeType, size: number) => void;
  readOnly?: boolean;
}

interface ShapeInfo {
  name: string;
  volume: string;
  surfaceArea: string;
  description: string;
}

const GeometricShapes3D: React.FC<Shape3DProps> = ({
  initialShape = 'cube',
  initialSize = 100,
  showMeasurements = true,
  showNet = false,
  onShapeChange,
  readOnly = false
}) => {
  const [currentShape, setCurrentShape] = useState<ShapeType>(initialShape);
  const [size, setSize] = useState<number>(initialSize);
  const [rotation, setRotation] = useState({ x: 20, y: 45 });
  const [isRotating, setIsRotating] = useState(false);
  const [showNetView, setShowNetView] = useState(showNet);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const shapeRef = useRef<HTMLDivElement>(null);

  // REQ-51.11: Farklı 3D şekilleri render et
  const shapeInfo: Record<ShapeType, ShapeInfo> = {
    cube: {
      name: 'Küp',
      volume: `${(size / 10) ** 3} cm³`,
      surfaceArea: `${6 * (size / 10) ** 2} cm²`,
      description: '6 eşit kare yüzü olan düzgün çokyüzlü'
    },
    sphere: {
      name: 'Küre',
      volume: `${((4 / 3) * Math.PI * (size / 20) ** 3).toFixed(2)} cm³`,
      surfaceArea: `${(4 * Math.PI * (size / 20) ** 2).toFixed(2)} cm²`,
      description: 'Merkezden eşit uzaklıktaki noktaların oluşturduğu yuvarlak cisim'
    },
    cylinder: {
      name: 'Silindir',
      volume: `${(Math.PI * (size / 20) ** 2 * (size / 10)).toFixed(2)} cm³`,
      surfaceArea: `${(2 * Math.PI * (size / 20) * ((size / 20) + (size / 10))).toFixed(2)} cm²`,
      description: 'Dairesel taban ve üst yüzeyi olan cisim'
    },
    cone: {
      name: 'Koni',
      volume: `${((1 / 3) * Math.PI * (size / 20) ** 2 * (size / 10)).toFixed(2)} cm³`,
      surfaceArea: `${(Math.PI * (size / 20) * ((size / 20) + Math.sqrt((size / 10) ** 2 + (size / 20) ** 2))).toFixed(2)} cm²`,
      description: 'Dairesel tabandan tepesine doğru daralan cisim'
    },
    pyramid: {
      name: 'Piramit',
      volume: `${((1 / 3) * (size / 10) ** 2 * (size / 10)).toFixed(2)} cm³`,
      surfaceArea: `${((size / 10) ** 2 + 2 * (size / 10) * Math.sqrt((size / 20) ** 2 + (size / 10) ** 2)).toFixed(2)} cm²`,
      description: 'Kare tabandan tepesine doğru daralan cisim'
    }
  };

  // REQ-51.12: 360 derece rotasyon
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (readOnly) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  }, [readOnly]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return;
    
    const deltaX = e.clientX - dragStart.x;
    const deltaY = e.clientY - dragStart.y;
    
    setRotation(prev => ({
      x: (prev.x + deltaY * 0.5) % 360,
      y: (prev.y + deltaX * 0.5) % 360
    }));
    
    setDragStart({ x: e.clientX, y: e.clientY });
  }, [isDragging, dragStart]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // Auto-rotation
  useEffect(() => {
    if (!isRotating) return;
    
    const interval = setInterval(() => {
      setRotation(prev => ({
        x: prev.x,
        y: (prev.y + 1) % 360
      }));
    }, 30);
    
    return () => clearInterval(interval);
  }, [isRotating]);

  const handleShapeChange = useCallback((shape: ShapeType) => {
    setCurrentShape(shape);
    onShapeChange?.(shape, size);
  }, [size, onShapeChange]);

  const handleSizeChange = useCallback((newSize: number) => {
    const clampedSize = Math.max(50, Math.min(newSize, 200));
    setSize(clampedSize);
    onShapeChange?.(currentShape, clampedSize);
  }, [currentShape, onShapeChange]);

  // REQ-51.11: 3D şekil render
  const renderShape = () => {
    const style = {
      transform: `rotateX(${rotation.x}deg) rotateY(${rotation.y}deg)`,
      width: `${size}px`,
      height: `${size}px`
    };

    switch (currentShape) {
      case 'cube':
        return (
          <div className="shape-3d cube-3d" style={style}>
            <div className="face front">Ön</div>
            <div className="face back">Arka</div>
            <div className="face right">Sağ</div>
            <div className="face left">Sol</div>
            <div className="face top">Üst</div>
            <div className="face bottom">Alt</div>
          </div>
        );
      
      case 'sphere':
        return (
          <div className="shape-3d sphere-3d" style={style}>
            <div className="sphere-inner"></div>
          </div>
        );
      
      case 'cylinder':
        return (
          <div className="shape-3d cylinder-3d" style={style}>
            <div className="cylinder-top"></div>
            <div className="cylinder-body"></div>
            <div className="cylinder-bottom"></div>
          </div>
        );
      
      case 'cone':
        return (
          <div className="shape-3d cone-3d" style={style}>
            <div className="cone-tip"></div>
            <div className="cone-body"></div>
            <div className="cone-base"></div>
          </div>
        );
      
      case 'pyramid':
        return (
          <div className="shape-3d pyramid-3d" style={style}>
            <div className="pyramid-face front-face"></div>
            <div className="pyramid-face back-face"></div>
            <div className="pyramid-face left-face"></div>
            <div className="pyramid-face right-face"></div>
            <div className="pyramid-base"></div>
          </div>
        );
      
      default:
        return null;
    }
  };

  // REQ-51.15: Şeklin açılımını (net) göster
  const renderNet = () => {
    if (!showNetView) return null;

    return (
      <div className="shape-net">
        <h4>Şeklin Açılımı (Net)</h4>
        <div className={`net-diagram ${currentShape}-net`}>
          {currentShape === 'cube' && (
            <div className="cube-net-layout">
              <div className="net-face">Üst</div>
              <div className="net-face">Sol</div>
              <div className="net-face">Ön</div>
              <div className="net-face">Sağ</div>
              <div className="net-face">Arka</div>
              <div className="net-face">Alt</div>
            </div>
          )}
          {currentShape === 'pyramid' && (
            <div className="pyramid-net-layout">
              <div className="net-triangle">Ön</div>
              <div className="net-triangle">Sağ</div>
              <div className="net-triangle">Arka</div>
              <div className="net-triangle">Sol</div>
              <div className="net-square">Taban</div>
            </div>
          )}
          {(currentShape === 'sphere' || currentShape === 'cylinder' || currentShape === 'cone') && (
            <div className="curved-net-note">
              <p>Bu şekil kavisli yüzeylere sahip olduğu için tam açılımı gösterilemez.</p>
              <p>Yaklaşık açılım gösterimi yapılmaktadır.</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="geometric-shapes-3d-container" role="region" aria-label="3D geometric shapes visualization">
      <div className="shapes-header">
        <h3>3D Geometrik Şekiller</h3>
      </div>

      <div className="shape-selector">
        <label>Şekil Seç:</label>
        <div className="shape-buttons">
          {(Object.keys(shapeInfo) as ShapeType[]).map(shape => (
            <button
              key={shape}
              onClick={() => handleShapeChange(shape)}
              className={`shape-btn ${currentShape === shape ? 'active' : ''}`}
              disabled={readOnly}
            >
              {shapeInfo[shape].name}
            </button>
          ))}
        </div>
      </div>

      <div className="shape-display-area">
        <div 
          className="shape-viewport"
          onMouseDown={handleMouseDown}
          ref={shapeRef}
          style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        >
          {renderShape()}
        </div>

        <div className="shape-controls">
          <div className="control-group">
            <label>Boyut: {size}px</label>
            <input
              type="range"
              min={50}
              max={200}
              value={size}
              onChange={(e) => handleSizeChange(parseInt(e.target.value))}
              disabled={readOnly}
            />
          </div>

          <div className="control-group">
            <button
              onClick={() => setIsRotating(!isRotating)}
              className={`control-btn ${isRotating ? 'active' : ''}`}
              disabled={readOnly}
            >
              {isRotating ? 'Otomatik Döndürmeyi Durdur' : 'Otomatik Döndür'}
            </button>
          </div>

          <div className="control-group">
            <button
              onClick={() => setRotation({ x: 20, y: 45 })}
              className="control-btn"
              disabled={readOnly}
            >
              Sıfırla
            </button>
          </div>

          {showNet && (
            <div className="control-group">
              <button
                onClick={() => setShowNetView(!showNetView)}
                className="control-btn"
              >
                {showNetView ? 'Açılımı Gizle' : 'Açılımı Göster'}
              </button>
            </div>
          )}
        </div>
      </div>

      {showMeasurements && (
        <div className="shape-info">
          <h4>{shapeInfo[currentShape].name}</h4>
          <p className="shape-description">{shapeInfo[currentShape].description}</p>
          <div className="measurements">
            <div className="measurement-item">
              <span className="measurement-label">Hacim:</span>
              <span className="measurement-value">{shapeInfo[currentShape].volume}</span>
            </div>
            <div className="measurement-item">
              <span className="measurement-label">Yüzey Alanı:</span>
              <span className="measurement-value">{shapeInfo[currentShape].surfaceArea}</span>
            </div>
          </div>
        </div>
      )}

      {renderNet()}

      <div className="usage-hint">
        <p>💡 Şekli döndürmek için fare ile sürükleyin</p>
      </div>
    </div>
  );
};

export default GeometricShapes3D;
