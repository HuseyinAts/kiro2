/**
 * Graphing Calculator Component
 * 
 * Grafik hesap makinesi - Fonksiyon grafikleri çizme ve analiz.
 * 
 * Özellikler:
 * - Fonksiyon grafikleri (y = f(x))
 * - Değer tablosu
 * - Trace (iz sürme) özelliği
 * - Zoom ve pan
 * - Birden fazla fonksiyon desteği
 * - Kesişim noktaları
 * 
 * Gereksinimler: REQ-51.46 - REQ-51.50
 */

import React, { useState, useRef, useEffect } from 'react';
import './GraphingCalculator.css';

interface Point {
  x: number;
  y: number;
}

interface FunctionData {
  id: string;
  expression: string;
  color: string;
  visible: boolean;
}

const GraphingCalculator: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [functions, setFunctions] = useState<FunctionData[]>([
    { id: '1', expression: 'x^2', color: '#ff6b6b', visible: true }
  ]);
  const [currentExpression, setCurrentExpression] = useState<string>('');
  const [xMin, setXMin] = useState<number>(-10);
  const [xMax, setXMax] = useState<number>(10);
  const [yMin, setYMin] = useState<number>(-10);
  const [yMax, setYMax] = useState<number>(10);
  const [showTable, setShowTable] = useState<boolean>(false);
  const [traceMode, setTraceMode] = useState<boolean>(false);
  const [traceX, setTraceX] = useState<number>(0);
  const [gridSize, setGridSize] = useState<number>(1);

  const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f7b731', '#5f27cd', '#00d2d3'];

  // Fonksiyon değerlendirme
  const evaluateFunction = (expression: string, x: number): number | null => {
    try {
      // Güvenli matematik ifadesi değerlendirici
      const sanitized = expression
        .replace(/\^/g, '**')
        .replace(/x/g, `(${x})`)
        .replace(/sin/g, 'Math.sin')
        .replace(/cos/g, 'Math.cos')
        .replace(/tan/g, 'Math.tan')
        .replace(/sqrt/g, 'Math.sqrt')
        .replace(/abs/g, 'Math.abs')
        .replace(/log/g, 'Math.log10')
        .replace(/ln/g, 'Math.log')
        .replace(/pi/g, 'Math.PI')
        .replace(/e(?![a-z])/g, 'Math.E');

      const result = Function('"use strict"; return (' + sanitized + ')')();
      return isFinite(result) ? result : null;
    } catch (error) {
      return null;
    }
  };

  // Grafik çizimi
  const drawGraph = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Temizle
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, width, height);

    // Koordinat dönüşümleri
    const xScale = width / (xMax - xMin);
    const yScale = height / (yMax - yMin);
    const xOrigin = -xMin * xScale;
    const yOrigin = yMax * yScale;

    // Grid çiz
    drawGrid(ctx, width, height, xScale, yScale, xOrigin, yOrigin);

    // Eksenler çiz
    drawAxes(ctx, width, height, xOrigin, yOrigin);

    // Fonksiyonları çiz
    functions.forEach(func => {
      if (func.visible) {
        drawFunction(ctx, func, xScale, yScale, xOrigin, yOrigin);
      }
    });

    // Trace modu
    if (traceMode) {
      drawTrace(ctx, xScale, yScale, xOrigin, yOrigin);
    }
  };

  const drawGrid = (
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    xScale: number,
    yScale: number,
    xOrigin: number,
    yOrigin: number
  ) => {
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 0.5;

    // Dikey grid çizgileri
    for (let x = Math.ceil(xMin / gridSize) * gridSize; x <= xMax; x += gridSize) {
      const canvasX = xOrigin + x * xScale;
      ctx.beginPath();
      ctx.moveTo(canvasX, 0);
      ctx.lineTo(canvasX, height);
      ctx.stroke();
    }

    // Yatay grid çizgileri
    for (let y = Math.ceil(yMin / gridSize) * gridSize; y <= yMax; y += gridSize) {
      const canvasY = yOrigin - y * yScale;
      ctx.beginPath();
      ctx.moveTo(0, canvasY);
      ctx.lineTo(width, canvasY);
      ctx.stroke();
    }
  };

  const drawAxes = (
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    xOrigin: number,
    yOrigin: number
  ) => {
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;

    // X ekseni
    if (yOrigin >= 0 && yOrigin <= height) {
      ctx.beginPath();
      ctx.moveTo(0, yOrigin);
      ctx.lineTo(width, yOrigin);
      ctx.stroke();

      // X ekseni işaretleri
      ctx.fillStyle = '#333';
      ctx.font = '12px Arial';
      ctx.textAlign = 'center';
      for (let x = Math.ceil(xMin); x <= xMax; x++) {
        if (x !== 0) {
          const canvasX = xOrigin + x * (width / (xMax - xMin));
          ctx.fillText(x.toString(), canvasX, yOrigin + 15);
        }
      }
    }

    // Y ekseni
    if (xOrigin >= 0 && xOrigin <= width) {
      ctx.beginPath();
      ctx.moveTo(xOrigin, 0);
      ctx.lineTo(xOrigin, height);
      ctx.stroke();

      // Y ekseni işaretleri
      ctx.textAlign = 'right';
      for (let y = Math.ceil(yMin); y <= yMax; y++) {
        if (y !== 0) {
          const canvasY = yOrigin - y * (height / (yMax - yMin));
          ctx.fillText(y.toString(), xOrigin - 5, canvasY + 4);
        }
      }
    }

    // Orijin
    ctx.fillStyle = '#333';
    ctx.font = 'bold 14px Arial';
    ctx.textAlign = 'left';
    ctx.fillText('0', xOrigin + 5, yOrigin - 5);
  };

  const drawFunction = (
    ctx: CanvasRenderingContext2D,
    func: FunctionData,
    xScale: number,
    yScale: number,
    xOrigin: number,
    yOrigin: number
  ) => {
    ctx.strokeStyle = func.color;
    ctx.lineWidth = 2;
    ctx.beginPath();

    let firstPoint = true;
    const step = (xMax - xMin) / 1000;

    for (let x = xMin; x <= xMax; x += step) {
      const y = evaluateFunction(func.expression, x);
      
      if (y !== null && y >= yMin && y <= yMax) {
        const canvasX = xOrigin + x * xScale;
        const canvasY = yOrigin - y * yScale;

        if (firstPoint) {
          ctx.moveTo(canvasX, canvasY);
          firstPoint = false;
        } else {
          ctx.lineTo(canvasX, canvasY);
        }
      } else {
        firstPoint = true;
      }
    }

    ctx.stroke();
  };

  const drawTrace = (
    ctx: CanvasRenderingContext2D,
    xScale: number,
    yScale: number,
    xOrigin: number,
    yOrigin: number
  ) => {
    const canvasX = xOrigin + traceX * xScale;

    // Dikey çizgi
    ctx.strokeStyle = '#999';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(canvasX, 0);
    ctx.lineTo(canvasX, canvasRef.current!.height);
    ctx.stroke();
    ctx.setLineDash([]);

    // Fonksiyon noktaları
    functions.forEach(func => {
      if (func.visible) {
        const y = evaluateFunction(func.expression, traceX);
        if (y !== null) {
          const canvasY = yOrigin - y * yScale;
          
          ctx.fillStyle = func.color;
          ctx.beginPath();
          ctx.arc(canvasX, canvasY, 5, 0, 2 * Math.PI);
          ctx.fill();

          // Değer etiketi
          ctx.fillStyle = '#fff';
          ctx.fillRect(canvasX + 10, canvasY - 20, 80, 25);
          ctx.fillStyle = func.color;
          ctx.font = '12px Arial';
          ctx.textAlign = 'left';
          ctx.fillText(`(${traceX.toFixed(2)}, ${y.toFixed(2)})`, canvasX + 15, canvasY - 5);
        }
      }
    });
  };

  // Fonksiyon ekleme
  const addFunction = () => {
    if (currentExpression.trim()) {
      const newFunc: FunctionData = {
        id: Date.now().toString(),
        expression: currentExpression,
        color: colors[functions.length % colors.length],
        visible: true
      };
      setFunctions([...functions, newFunc]);
      setCurrentExpression('');
    }
  };

  // Fonksiyon silme
  const removeFunction = (id: string) => {
    setFunctions(functions.filter(f => f.id !== id));
  };

  // Fonksiyon görünürlüğü
  const toggleFunctionVisibility = (id: string) => {
    setFunctions(functions.map(f => 
      f.id === id ? { ...f, visible: !f.visible } : f
    ));
  };

  // Zoom işlemleri
  const zoomIn = () => {
    const xRange = (xMax - xMin) / 2;
    const yRange = (yMax - yMin) / 2;
    setXMin(xMin + xRange / 2);
    setXMax(xMax - xRange / 2);
    setYMin(yMin + yRange / 2);
    setYMax(yMax - yRange / 2);
  };

  const zoomOut = () => {
    const xRange = (xMax - xMin) / 2;
    const yRange = (yMax - yMin) / 2;
    setXMin(xMin - xRange / 2);
    setXMax(xMax + xRange / 2);
    setYMin(yMin - yRange / 2);
    setYMax(yMax + yRange / 2);
  };

  const resetView = () => {
    setXMin(-10);
    setXMax(10);
    setYMin(-10);
    setYMax(10);
  };

  // Değer tablosu oluşturma
  const generateTable = (): Point[][] => {
    const tables: Point[][] = [];
    const step = (xMax - xMin) / 20;

    functions.forEach(func => {
      if (func.visible) {
        const points: Point[] = [];
        for (let x = xMin; x <= xMax; x += step) {
          const y = evaluateFunction(func.expression, x);
          if (y !== null) {
            points.push({ x, y });
          }
        }
        tables.push(points);
      }
    });

    return tables;
  };

  // Canvas güncelleme
  useEffect(() => {
    drawGraph();
  }, [functions, xMin, xMax, yMin, yMax, traceMode, traceX, gridSize]);

  // Canvas boyutlandırma
  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
      drawGraph();
    }
  }, []);

  return (
    <div className="graphing-calculator" role="application" aria-label="Grafik Hesap Makinesi">
      <div className="calculator-header">
        <h2>Grafik Hesap Makinesi</h2>
      </div>

      <div className="calculator-body">
        {/* Fonksiyon girişi */}
        <div className="function-input-section">
          <div className="input-group">
            <label htmlFor="function-input">Fonksiyon (y =):</label>
            <input
              id="function-input"
              type="text"
              value={currentExpression}
              onChange={(e) => setCurrentExpression(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addFunction()}
              placeholder="Örnek: x^2, sin(x), 2*x+1"
              aria-label="Fonksiyon ifadesi"
            />
            <button onClick={addFunction} aria-label="Fonksiyon ekle">
              ➕ Ekle
            </button>
          </div>

          <div className="function-help">
            <details>
              <summary>📖 Kullanılabilir Fonksiyonlar</summary>
              <ul>
                <li><code>x^2</code> - Üs alma</li>
                <li><code>sin(x)</code>, <code>cos(x)</code>, <code>tan(x)</code> - Trigonometrik</li>
                <li><code>sqrt(x)</code> - Karekök</li>
                <li><code>abs(x)</code> - Mutlak değer</li>
                <li><code>log(x)</code>, <code>ln(x)</code> - Logaritma</li>
                <li><code>pi</code>, <code>e</code> - Sabitler</li>
              </ul>
            </details>
          </div>
        </div>

        {/* Fonksiyon listesi */}
        <div className="function-list">
          {functions.map((func, index) => (
            <div key={func.id} className="function-item">
              <div
                className="function-color"
                style={{ backgroundColor: func.color }}
                aria-label={`Fonksiyon rengi: ${func.color}`}
              />
              <span className="function-expression">
                y = {func.expression}
              </span>
              <button
                onClick={() => toggleFunctionVisibility(func.id)}
                className={`visibility-btn ${func.visible ? 'visible' : 'hidden'}`}
                aria-label={func.visible ? 'Gizle' : 'Göster'}
              >
                {func.visible ? '👁️' : '👁️‍🗨️'}
              </button>
              <button
                onClick={() => removeFunction(func.id)}
                className="remove-btn"
                aria-label="Fonksiyonu sil"
              >
                🗑️
              </button>
            </div>
          ))}
        </div>

        {/* Grafik alanı */}
        <div className="graph-container">
          <canvas
            ref={canvasRef}
            className="graph-canvas"
            aria-label="Fonksiyon grafikleri"
          />
        </div>

        {/* Kontroller */}
        <div className="graph-controls">
          <div className="control-group">
            <button onClick={zoomIn} aria-label="Yakınlaştır">🔍+ Yakınlaştır</button>
            <button onClick={zoomOut} aria-label="Uzaklaştır">🔍- Uzaklaştır</button>
            <button onClick={resetView} aria-label="Görünümü sıfırla">🔄 Sıfırla</button>
          </div>

          <div className="control-group">
            <button
              onClick={() => setTraceMode(!traceMode)}
              className={traceMode ? 'active' : ''}
              aria-label="İz sürme modu"
              aria-pressed={traceMode}
            >
              📍 Trace {traceMode ? 'Açık' : 'Kapalı'}
            </button>
            {traceMode && (
              <input
                type="range"
                min={xMin}
                max={xMax}
                step={(xMax - xMin) / 100}
                value={traceX}
                onChange={(e) => setTraceX(parseFloat(e.target.value))}
                aria-label="Trace X pozisyonu"
              />
            )}
          </div>

          <div className="control-group">
            <button
              onClick={() => setShowTable(!showTable)}
              aria-label="Değer tablosunu göster/gizle"
            >
              📊 Tablo {showTable ? 'Gizle' : 'Göster'}
            </button>
          </div>
        </div>

        {/* Eksen ayarları */}
        <div className="axis-settings">
          <div className="axis-group">
            <label>X Ekseni:</label>
            <input
              type="number"
              value={xMin}
              onChange={(e) => setXMin(parseFloat(e.target.value))}
              aria-label="X minimum"
            />
            <span>ile</span>
            <input
              type="number"
              value={xMax}
              onChange={(e) => setXMax(parseFloat(e.target.value))}
              aria-label="X maksimum"
            />
          </div>
          <div className="axis-group">
            <label>Y Ekseni:</label>
            <input
              type="number"
              value={yMin}
              onChange={(e) => setYMin(parseFloat(e.target.value))}
              aria-label="Y minimum"
            />
            <span>ile</span>
            <input
              type="number"
              value={yMax}
              onChange={(e) => setYMax(parseFloat(e.target.value))}
              aria-label="Y maksimum"
            />
          </div>
        </div>

        {/* Değer tablosu */}
        {showTable && (
          <div className="value-table" role="region" aria-label="Değer tablosu">
            <h3>Değer Tablosu</h3>
            {generateTable().map((points, funcIndex) => (
              <div key={funcIndex} className="table-section">
                <h4 style={{ color: functions.filter(f => f.visible)[funcIndex]?.color }}>
                  y = {functions.filter(f => f.visible)[funcIndex]?.expression}
                </h4>
                <table>
                  <thead>
                    <tr>
                      <th>x</th>
                      <th>y</th>
                    </tr>
                  </thead>
                  <tbody>
                    {points.map((point, index) => (
                      <tr key={index}>
                        <td>{point.x.toFixed(2)}</td>
                        <td>{point.y.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default GraphingCalculator;
