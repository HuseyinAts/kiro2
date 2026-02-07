/**
 * GraphPlotter Component - Diskalkuli Desteği
 *
 * İnteraktif fonksiyon grafik çizim aracı.
 * Öğrencilerin matematiksel fonksiyonları görselleştirmelerine ve koordinat sistemini anlamalarına yardımcı olur.
 *
 * Gereksinimler: REQ-51.16 - REQ-51.20
 */

import * as React from 'react';
import {  useState, useCallback, useRef, useEffect, useMemo  } from 'react';
import './GraphPlotter.css';

interface Point {
  x: number;
  y: number;
}

interface GraphPlotterProps {
  initialFunction?: string;
  xMin?: number;
  xMax?: number;
  yMin?: number;
  yMax?: number;
  gridSize?: number;
  onFunctionChange?: (func: string) => void;
  readOnly?: boolean;
}

const GraphPlotter: React.FC<GraphPlotterProps> = ({
  initialFunction = 'x^2',
  xMin = -10,
  xMax = 10,
  yMin = -10,
  yMax = 10,
  gridSize = 1,
  onFunctionChange,
  readOnly = false,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [functionStr, setFunctionStr] = useState<string>(initialFunction);
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<Point>({ x: 0, y: 0 });
  const [selectedPoint, setSelectedPoint] = useState<Point | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<Point | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<Point>({ x: 0, y: 0 });
  const [error, setError] = useState<string>('');

  const canvasWidth = 800;
  const canvasHeight = 600;

  // REQ-51.16: İnteraktif koordinat sistemi
  const getCanvasCoordinates = useCallback((x: number, y: number): Point => {
    const centerX = canvasWidth / 2 + pan.x;
    const centerY = canvasHeight / 2 + pan.y;
    const scale = 30 * zoom;

    return {
      x: centerX + x * scale,
      y: centerY - y * scale,
    };
  }, [pan, zoom]);

  const getGraphCoordinates = useCallback((canvasX: number, canvasY: number): Point => {
    const centerX = canvasWidth / 2 + pan.x;
    const centerY = canvasHeight / 2 + pan.y;
    const scale = 30 * zoom;

    return {
      x: (canvasX - centerX) / scale,
      y: (centerY - canvasY) / scale,
    };
  }, [pan, zoom]);

  // REQ-51.17: Fonksiyon değerlendirme
  const evaluateFunction = useCallback((x: number): number | null => {
    try {
      // Basit matematik fonksiyonlarını değerlendir
      let expr = functionStr
        .replace(/\^/g, '**')
        .replace(/sin/g, 'Math.sin')
        .replace(/cos/g, 'Math.cos')
        .replace(/tan/g, 'Math.tan')
        .replace(/sqrt/g, 'Math.sqrt')
        .replace(/abs/g, 'Math.abs')
        .replace(/log/g, 'Math.log')
        .replace(/exp/g, 'Math.exp')
        .replace(/pi/g, 'Math.PI')
        .replace(/e(?![a-z])/g, 'Math.E');

      // x değerini yerine koy
      expr = expr.replace(/x/g, `(${x})`);

      // Güvenli değerlendirme
      const result = Function(`"use strict"; return (${expr})`)();

      if (typeof result !== 'number' || !isFinite(result)) {
        return null;
      }

      return result;
    } catch {
      return null;
    }
  }, [functionStr]);

  // REQ-51.17: Gerçek zamanlı grafik çizimi
  const drawGraph = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) {return;}

    const ctx = canvas.getContext('2d');
    if (!ctx) {return;}

    // Temizle
    ctx.clearRect(0, 0, canvasWidth, canvasHeight);

    // Arka plan
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // REQ-51.19: Renkli kodlanmış eksenler
    // Grid çiz
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;

    const scale = 30 * zoom;
    const centerX = canvasWidth / 2 + pan.x;
    const centerY = canvasHeight / 2 + pan.y;

    // Dikey grid çizgileri
    for (let x = xMin; x <= xMax; x += gridSize) {
      const canvasX = centerX + x * scale;
      if (canvasX >= 0 && canvasX <= canvasWidth) {
        ctx.beginPath();
        ctx.moveTo(canvasX, 0);
        ctx.lineTo(canvasX, canvasHeight);
        ctx.stroke();
      }
    }

    // Yatay grid çizgileri
    for (let y = yMin; y <= yMax; y += gridSize) {
      const canvasY = centerY - y * scale;
      if (canvasY >= 0 && canvasY <= canvasHeight) {
        ctx.beginPath();
        ctx.moveTo(0, canvasY);
        ctx.lineTo(canvasWidth, canvasY);
        ctx.stroke();
      }
    }

    // X ekseni (kırmızı)
    ctx.strokeStyle = '#FF6B6B';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(canvasWidth, centerY);
    ctx.stroke();

    // Y ekseni (mavi)
    ctx.strokeStyle = '#2196F3';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(centerX, 0);
    ctx.lineTo(centerX, canvasHeight);
    ctx.stroke();

    // Eksen etiketleri
    ctx.fillStyle = '#333';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';

    // X ekseni etiketleri
    for (let x = Math.ceil(xMin); x <= Math.floor(xMax); x++) {
      if (x === 0) {continue;}
      const canvasX = centerX + x * scale;
      if (canvasX >= 0 && canvasX <= canvasWidth) {
        ctx.fillText(x.toString(), canvasX, centerY + 20);
      }
    }

    // Y ekseni etiketleri
    ctx.textAlign = 'right';
    for (let y = Math.ceil(yMin); y <= Math.floor(yMax); y++) {
      if (y === 0) {continue;}
      const canvasY = centerY - y * scale;
      if (canvasY >= 0 && canvasY <= canvasHeight) {
        ctx.fillText(y.toString(), centerX - 10, canvasY + 5);
      }
    }

    // Orijin
    ctx.fillStyle = '#333';
    ctx.font = 'bold 14px Arial';
    ctx.textAlign = 'right';
    ctx.fillText('0', centerX - 10, centerY + 20);

    // Fonksiyon grafiğini çiz
    ctx.strokeStyle = '#4CAF50';
    ctx.lineWidth = 3;
    ctx.beginPath();

    let firstPoint = true;
    const step = 0.05 / zoom;

    for (let x = xMin; x <= xMax; x += step) {
      const y = evaluateFunction(x);

      if (y !== null && y >= yMin && y <= yMax) {
        const point = getCanvasCoordinates(x, y);

        if (firstPoint) {
          ctx.moveTo(point.x, point.y);
          firstPoint = false;
        } else {
          ctx.lineTo(point.x, point.y);
        }
      } else {
        firstPoint = true;
      }
    }

    ctx.stroke();

    // Seçili nokta
    if (selectedPoint) {
      const canvasPoint = getCanvasCoordinates(selectedPoint.x, selectedPoint.y);
      ctx.fillStyle = '#FF6B6B';
      ctx.beginPath();
      ctx.arc(canvasPoint.x, canvasPoint.y, 6, 0, 2 * Math.PI);
      ctx.fill();

      // REQ-51.20: Koordinat değerlerini tooltip ile göster
      ctx.fillStyle = '#333';
      ctx.font = 'bold 14px Arial';
      ctx.textAlign = 'left';
      ctx.fillText(
        `(${selectedPoint.x.toFixed(2)}, ${selectedPoint.y.toFixed(2)})`,
        canvasPoint.x + 10,
        canvasPoint.y - 10,
      );
    }

    // Hover nokta
    if (hoveredPoint) {
      const canvasPoint = getCanvasCoordinates(hoveredPoint.x, hoveredPoint.y);
      ctx.fillStyle = 'rgba(33, 150, 243, 0.5)';
      ctx.beginPath();
      ctx.arc(canvasPoint.x, canvasPoint.y, 4, 0, 2 * Math.PI);
      ctx.fill();
    }
  }, [functionStr, zoom, pan, selectedPoint, hoveredPoint, xMin, xMax, yMin, yMax, gridSize, evaluateFunction, getCanvasCoordinates]);

  useEffect(() => {
    drawGraph();
  }, [drawGraph]);

  // REQ-51.18: Zoom, pan ve nokta seçimi
  const handleCanvasClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) {return;}

    const rect = canvas.getBoundingClientRect();
    const canvasX = e.clientX - rect.left;
    const canvasY = e.clientY - rect.top;

    const graphPoint = getGraphCoordinates(canvasX, canvasY);
    const y = evaluateFunction(graphPoint.x);

    if (y !== null) {
      setSelectedPoint({ x: graphPoint.x, y });
    }
  }, [getGraphCoordinates, evaluateFunction]);

  const handleCanvasMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDragging) {
      const deltaX = e.clientX - dragStart.x;
      const deltaY = e.clientY - dragStart.y;

      setPan(prev => ({
        x: prev.x + deltaX,
        y: prev.y + deltaY,
      }));

      setDragStart({ x: e.clientX, y: e.clientY });
    } else {
      const canvas = canvasRef.current;
      if (!canvas) {return;}

      const rect = canvas.getBoundingClientRect();
      const canvasX = e.clientX - rect.left;
      const canvasY = e.clientY - rect.top;

      const graphPoint = getGraphCoordinates(canvasX, canvasY);
      const y = evaluateFunction(graphPoint.x);

      if (y !== null) {
        setHoveredPoint({ x: graphPoint.x, y });
      } else {
        setHoveredPoint(null);
      }
    }
  }, [isDragging, dragStart, getGraphCoordinates, evaluateFunction]);

  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  }, []);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleWheel = useCallback((e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom(prev => Math.max(0.1, Math.min(prev * delta, 5)));
  }, []);

  const handleFunctionChange = useCallback((newFunc: string) => {
    setFunctionStr(newFunc);
    setError('');
    onFunctionChange?.(newFunc);

    // Fonksiyonu test et
    const testResult = evaluateFunction(0);
    if (testResult === null && newFunc.trim() !== '') {
      setError('Geçersiz fonksiyon. Lütfen kontrol edin.');
    }
  }, [evaluateFunction, onFunctionChange]);

  const handleReset = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setSelectedPoint(null);
  }, []);

  const commonFunctions = useMemo(() => [
    { label: 'Doğrusal: x', value: 'x' },
    { label: 'Karesel: x²', value: 'x^2' },
    { label: 'Kübik: x³', value: 'x^3' },
    { label: 'Karekök: √x', value: 'sqrt(x)' },
    { label: 'Sinüs: sin(x)', value: 'sin(x)' },
    { label: 'Kosinüs: cos(x)', value: 'cos(x)' },
    { label: 'Üstel: eˣ', value: 'exp(x)' },
    { label: 'Logaritma: ln(x)', value: 'log(x)' },
  ], []);

  return (
    <div className="graph-plotter-container" role="region" aria-label="Function graph plotter">
      <div className="graph-header">
        <h3>Grafik Çizim Aracı</h3>
      </div>

      <div className="function-input-section">
        <div className="function-input-group">
          <label htmlFor="function-input">Fonksiyon (y =):</label>
          <input
            id="function-input"
            type="text"
            value={functionStr}
            onChange={(e) => handleFunctionChange(e.target.value)}
            placeholder="Örnek: x^2, sin(x), 2*x + 1"
            disabled={readOnly}
            className={error ? 'error' : ''}
          />
          {error && <span className="error-message">{error}</span>}
        </div>

        <div className="common-functions">
          <div className="function-label" role="group" aria-label="Hızlı Seçim">Hızlı Seçim:</div>
          <div className="function-buttons">
            {commonFunctions.map(func => (
              <button
                key={func.value}
                onClick={() => handleFunctionChange(func.value)}
                className="function-btn"
                disabled={readOnly}
              >
                {func.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="graph-display">
        <canvas
          ref={canvasRef}
          width={canvasWidth}
          height={canvasHeight}
          onClick={handleCanvasClick}
          onMouseMove={handleCanvasMouseMove}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
          style={{ cursor: isDragging ? 'grabbing' : 'crosshair' }}
        />
      </div>

      <div className="graph-controls">
        <div className="control-group">
          <label>Zoom: {zoom.toFixed(2)}x</label>
          <input
            type="range"
            min={0.1}
            max={5}
            step={0.1}
            value={zoom}
            onChange={(e) => setZoom(parseFloat(e.target.value))}
            disabled={readOnly}
          />
        </div>

        <div className="control-buttons">
          <button onClick={handleReset} className="control-btn" disabled={readOnly}>
            Sıfırla
          </button>
          <button onClick={() => setZoom(z => Math.min(z * 1.2, 5))} className="control-btn" disabled={readOnly}>
            Yakınlaştır (+)
          </button>
          <button onClick={() => setZoom(z => Math.max(z * 0.8, 0.1))} className="control-btn" disabled={readOnly}>
            Uzaklaştır (−)
          </button>
        </div>
      </div>

      {selectedPoint && (
        <div className="point-info">
          <h4>Seçili Nokta</h4>
          <div className="point-coordinates">
            <div className="coordinate-item">
              <span className="coordinate-label">x:</span>
              <span className="coordinate-value">{selectedPoint.x.toFixed(3)}</span>
            </div>
            <div className="coordinate-item">
              <span className="coordinate-label">y:</span>
              <span className="coordinate-value">{selectedPoint.y.toFixed(3)}</span>
            </div>
          </div>
        </div>
      )}

      <div className="usage-hints">
        <h4>Kullanım İpuçları</h4>
        <ul>
          <li>🖱️ Grafiği kaydırmak için sürükleyin</li>
          <li>🔍 Yakınlaştırmak için fare tekerleğini kullanın</li>
          <li>📍 Bir noktaya tıklayarak koordinatlarını görün</li>
          <li>📝 Fonksiyon yazarken: x^2 (kare), sqrt(x) (karekök), sin(x) (sinüs)</li>
        </ul>
      </div>

      <div className="axis-legend">
        <div className="legend-item">
          <div className="legend-color x-axis"></div>
          <span>X Ekseni (Yatay)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color y-axis"></div>
          <span>Y Ekseni (Dikey)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color function-line"></div>
          <span>Fonksiyon Grafiği</span>
        </div>
      </div>
    </div>
  );
};

export default GraphPlotter;
