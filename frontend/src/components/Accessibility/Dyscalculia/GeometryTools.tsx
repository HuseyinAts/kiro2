/**
 * Geometry Tools Component
 *
 * Geometri araçları - Sanal cetvel, iletki, pergel ve şekil çizimi.
 *
 * Özellikler:
 * - Sanal cetvel (cm ve inch)
 * - İletki (açı ölçme)
 * - Pergel (daire çizme)
 * - Şekil çizim araçları
 * - Ölçüm araçları
 *
 * Gereksinimler: REQ-51.51 - REQ-51.55
 */

import * as React from 'react';
import {  useState, useRef, useEffect  } from 'react';
import './GeometryTools.css';

type Tool = 'ruler' | 'protractor' | 'compass' | 'line' | 'circle' | 'rectangle' | 'triangle' | 'polygon';
type Unit = 'cm' | 'inch';

interface Point {
  x: number;
  y: number;
}

interface Shape {
  type: 'line' | 'circle' | 'rectangle' | 'triangle' | 'polygon';
  points: Point[];
  color: string;
  id: string;
}

const GeometryTools: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tool, setTool] = useState<Tool>('ruler');
  const [unit, setUnit] = useState<Unit>('cm');
  const [shapes, setShapes] = useState<Shape[]>([]);
  const [currentShape, setCurrentShape] = useState<Point[]>([]);
  const [isDrawing, setIsDrawing] = useState<boolean>(false);
  const [rulerAngle, setRulerAngle] = useState<number>(0);
  const [protractorAngle, setProtractorAngle] = useState<number>(0);
  const [compassRadius, _setCompassRadius] = useState<number>(50);
  const [selectedColor, setSelectedColor] = useState<string>('#2196f3');
  const [gridVisible, setGridVisible] = useState<boolean>(true);
  const [measurements, setMeasurements] = useState<string[]>([]);

  const colors = ['#2196f3', '#f44336', '#4caf50', '#ff9800', '#9c27b0', '#00bcd4'];

  // Canvas başlatma
  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
      drawCanvas();
    }
  }, []);

  // Canvas çizimi
  useEffect(() => {
    drawCanvas();
  }, [shapes, currentShape, tool, gridVisible, rulerAngle, protractorAngle, compassRadius]);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) {return;}

    const ctx = canvas.getContext('2d');
    if (!ctx) {return;}

    // Temizle
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Grid çiz
    if (gridVisible) {
      drawGrid(ctx, canvas.width, canvas.height);
    }

    // Şekilleri çiz
    shapes.forEach(shape => drawShape(ctx, shape));

    // Mevcut şekli çiz
    if (currentShape.length > 0) {
      drawCurrentShape(ctx);
    }

    // Araçları çiz
    if (tool === 'ruler') {
      drawRuler(ctx, canvas.width / 2, canvas.height / 2);
    } else if (tool === 'protractor') {
      drawProtractor(ctx, canvas.width / 2, canvas.height / 2);
    }
  };

  const drawGrid = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 0.5;

    const gridSize = unit === 'cm' ? 20 : 25.4; // 1cm = 20px, 1inch = 25.4px

    // Dikey çizgiler
    for (let x = 0; x < width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }

    // Yatay çizgiler
    for (let y = 0; y < height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
  };

  const drawRuler = (ctx: CanvasRenderingContext2D, x: number, y: number) => {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate((rulerAngle * Math.PI) / 180);

    // Cetvel gövdesi
    ctx.fillStyle = 'rgba(255, 235, 59, 0.8)';
    ctx.fillRect(-200, -20, 400, 40);
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;
    ctx.strokeRect(-200, -20, 400, 40);

    // Ölçü çizgileri
    ctx.strokeStyle = '#333';
    ctx.fillStyle = '#333';
    ctx.font = '10px Arial';
    ctx.textAlign = 'center';

    const unitSize = unit === 'cm' ? 20 : 25.4;
    const maxUnits = Math.floor(400 / unitSize);

    for (let i = 0; i <= maxUnits; i++) {
      const xPos = -200 + i * unitSize;

      // Ana çizgi
      ctx.beginPath();
      ctx.moveTo(xPos, -20);
      ctx.lineTo(xPos, -10);
      ctx.stroke();

      // Sayı
      if (i % 1 === 0) {
        ctx.fillText(i.toString(), xPos, -5);
      }

      // Ara çizgiler (mm veya 1/8 inch)
      if (i < maxUnits) {
        const subDivisions = unit === 'cm' ? 10 : 8;
        for (let j = 1; j < subDivisions; j++) {
          const subX = xPos + (j * unitSize) / subDivisions;
          ctx.beginPath();
          ctx.moveTo(subX, -20);
          ctx.lineTo(subX, j % (subDivisions / 2) === 0 ? -15 : -17);
          ctx.stroke();
        }
      }
    }

    ctx.restore();
  };

  const drawProtractor = (ctx: CanvasRenderingContext2D, x: number, y: number) => {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate((protractorAngle * Math.PI) / 180);

    const radius = 150;

    // İletki gövdesi
    ctx.fillStyle = 'rgba(76, 175, 80, 0.3)';
    ctx.beginPath();
    ctx.arc(0, 0, radius, 0, Math.PI, true);
    ctx.closePath();
    ctx.fill();

    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(0, 0, radius, 0, Math.PI, true);
    ctx.stroke();

    // Derece çizgileri
    ctx.strokeStyle = '#333';
    ctx.fillStyle = '#333';
    ctx.font = '10px Arial';
    ctx.textAlign = 'center';

    for (let angle = 0; angle <= 180; angle += 10) {
      const rad = (angle * Math.PI) / 180;
      const x1 = Math.cos(rad) * (radius - 10);
      const y1 = -Math.sin(rad) * (radius - 10);
      const x2 = Math.cos(rad) * radius;
      const y2 = -Math.sin(rad) * radius;

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();

      if (angle % 10 === 0) {
        const textX = Math.cos(rad) * (radius - 25);
        const textY = -Math.sin(rad) * (radius - 25);
        ctx.fillText(angle.toString(), textX, textY);
      }
    }

    // Merkez noktası
    ctx.fillStyle = '#f44336';
    ctx.beginPath();
    ctx.arc(0, 0, 5, 0, 2 * Math.PI);
    ctx.fill();

    ctx.restore();
  };

  const drawShape = (ctx: CanvasRenderingContext2D, shape: Shape) => {
    ctx.strokeStyle = shape.color;
    ctx.fillStyle = shape.color + '40';
    ctx.lineWidth = 2;

    switch (shape.type) {
      case 'line':
        if (shape.points.length >= 2) {
          ctx.beginPath();
          ctx.moveTo(shape.points[0].x, shape.points[0].y);
          ctx.lineTo(shape.points[1].x, shape.points[1].y);
          ctx.stroke();
        }
        break;

      case 'circle': {
        if (shape.points.length >= 2) {
          const radius = Math.sqrt(
            Math.pow(shape.points[1].x - shape.points[0].x, 2) +
            Math.pow(shape.points[1].y - shape.points[0].y, 2),
          );
          ctx.beginPath();
          ctx.arc(shape.points[0].x, shape.points[0].y, radius, 0, 2 * Math.PI);
          ctx.stroke();
          ctx.fill();
        }
        break;
      }

      case 'rectangle': {
        if (shape.points.length >= 2) {
          const width = shape.points[1].x - shape.points[0].x;
          const height = shape.points[1].y - shape.points[0].y;
          ctx.beginPath();
          ctx.rect(shape.points[0].x, shape.points[0].y, width, height);
          ctx.stroke();
          ctx.fill();
        }
        break;
      }

      case 'triangle':
        if (shape.points.length >= 3) {
          ctx.beginPath();
          ctx.moveTo(shape.points[0].x, shape.points[0].y);
          ctx.lineTo(shape.points[1].x, shape.points[1].y);
          ctx.lineTo(shape.points[2].x, shape.points[2].y);
          ctx.closePath();
          ctx.stroke();
          ctx.fill();
        }
        break;

      case 'polygon':
        if (shape.points.length >= 3) {
          ctx.beginPath();
          ctx.moveTo(shape.points[0].x, shape.points[0].y);
          for (let i = 1; i < shape.points.length; i++) {
            ctx.lineTo(shape.points[i].x, shape.points[i].y);
          }
          ctx.closePath();
          ctx.stroke();
          ctx.fill();
        }
        break;
    }
  };

  const drawCurrentShape = (ctx: CanvasRenderingContext2D) => {
    if (currentShape.length === 0) {return;}

    ctx.strokeStyle = selectedColor;
    ctx.fillStyle = selectedColor + '40';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);

    if (tool === 'line' && currentShape.length >= 1) {
      ctx.beginPath();
      ctx.moveTo(currentShape[0].x, currentShape[0].y);
      if (currentShape.length === 2) {
        ctx.lineTo(currentShape[1].x, currentShape[1].y);
      }
      ctx.stroke();
    } else if (tool === 'circle' && currentShape.length >= 1) {
      if (currentShape.length === 2) {
        const radius = Math.sqrt(
          Math.pow(currentShape[1].x - currentShape[0].x, 2) +
          Math.pow(currentShape[1].y - currentShape[0].y, 2),
        );
        ctx.beginPath();
        ctx.arc(currentShape[0].x, currentShape[0].y, radius, 0, 2 * Math.PI);
        ctx.stroke();
      }
    } else if (tool === 'rectangle' && currentShape.length >= 1) {
      if (currentShape.length === 2) {
        const width = currentShape[1].x - currentShape[0].x;
        const height = currentShape[1].y - currentShape[0].y;
        ctx.beginPath();
        ctx.rect(currentShape[0].x, currentShape[0].y, width, height);
        ctx.stroke();
      }
    } else if ((tool === 'triangle' || tool === 'polygon') && currentShape.length >= 1) {
      ctx.beginPath();
      ctx.moveTo(currentShape[0].x, currentShape[0].y);
      for (let i = 1; i < currentShape.length; i++) {
        ctx.lineTo(currentShape[i].x, currentShape[i].y);
      }
      ctx.stroke();
    }

    ctx.setLineDash([]);
  };

  // Mouse olayları
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (tool === 'ruler' || tool === 'protractor') {return;}

    const canvas = canvasRef.current;
    if (!canvas) {return;}

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setIsDrawing(true);
    setCurrentShape([{ x, y }]);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || tool === 'ruler' || tool === 'protractor') {return;}

    const canvas = canvasRef.current;
    if (!canvas) {return;}

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (tool === 'line' || tool === 'circle' || tool === 'rectangle') {
      setCurrentShape([currentShape[0], { x, y }]);
    } else if (tool === 'triangle' && currentShape.length < 3) {
      setCurrentShape([...currentShape.slice(0, currentShape.length), { x, y }]);
    } else if (tool === 'polygon') {
      setCurrentShape([...currentShape.slice(0, currentShape.length), { x, y }]);
    }
  };

  const handleMouseUp = () => {
    if (!isDrawing) {return;}

    if (currentShape.length >= 2 && (tool === 'line' || tool === 'circle' || tool === 'rectangle')) {
      const newShape: Shape = {
        type: tool,
        points: currentShape,
        color: selectedColor,
        id: Date.now().toString(),
      };
      setShapes([...shapes, newShape]);
      setCurrentShape([]);
      addMeasurement(newShape);
    }

    setIsDrawing(false);
  };

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (tool !== 'triangle' && tool !== 'polygon') {return;}

    const canvas = canvasRef.current;
    if (!canvas) {return;}

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const newPoints = [...currentShape, { x, y }];
    setCurrentShape(newPoints);

    if (tool === 'triangle' && newPoints.length === 3) {
      const newShape: Shape = {
        type: 'triangle',
        points: newPoints,
        color: selectedColor,
        id: Date.now().toString(),
      };
      setShapes([...shapes, newShape]);
      setCurrentShape([]);
      addMeasurement(newShape);
    }
  };

  const handleDoubleClick = () => {
    if (tool === 'polygon' && currentShape.length >= 3) {
      const newShape: Shape = {
        type: 'polygon',
        points: currentShape,
        color: selectedColor,
        id: Date.now().toString(),
      };
      setShapes([...shapes, newShape]);
      setCurrentShape([]);
      addMeasurement(newShape);
    }
  };

  // Ölçüm ekleme
  const addMeasurement = (shape: Shape) => {
    let measurement = '';

    switch (shape.type) {
      case 'line': {
        const length = Math.sqrt(
          Math.pow(shape.points[1].x - shape.points[0].x, 2) +
          Math.pow(shape.points[1].y - shape.points[0].y, 2),
        );
        const lengthInUnits = unit === 'cm' ? length / 20 : length / 25.4;
        measurement = `Çizgi uzunluğu: ${lengthInUnits.toFixed(2)} ${unit}`;
        break;
      }

      case 'circle': {
        const radius = Math.sqrt(
          Math.pow(shape.points[1].x - shape.points[0].x, 2) +
          Math.pow(shape.points[1].y - shape.points[0].y, 2),
        );
        const radiusInUnits = unit === 'cm' ? radius / 20 : radius / 25.4;
        const area = Math.PI * radius * radius;
        const areaInUnits = unit === 'cm' ? area / 400 : area / 645.16;
        measurement = `Daire - Yarıçap: ${radiusInUnits.toFixed(2)} ${unit}, Alan: ${areaInUnits.toFixed(2)} ${unit}²`;
        break;
      }

      case 'rectangle': {
        const width = Math.abs(shape.points[1].x - shape.points[0].x);
        const height = Math.abs(shape.points[1].y - shape.points[0].y);
        const widthInUnits = unit === 'cm' ? width / 20 : width / 25.4;
        const heightInUnits = unit === 'cm' ? height / 20 : height / 25.4;
        const rectArea = width * height;
        const rectAreaInUnits = unit === 'cm' ? rectArea / 400 : rectArea / 645.16;
        measurement = `Dikdörtgen - Genişlik: ${widthInUnits.toFixed(2)} ${unit}, Yükseklik: ${heightInUnits.toFixed(2)} ${unit}, Alan: ${rectAreaInUnits.toFixed(2)} ${unit}²`;
        break;
      }

      case 'triangle': {
        // Kenar uzunlukları
        const a = Math.sqrt(Math.pow(shape.points[1].x - shape.points[0].x, 2) + Math.pow(shape.points[1].y - shape.points[0].y, 2));
        const b = Math.sqrt(Math.pow(shape.points[2].x - shape.points[1].x, 2) + Math.pow(shape.points[2].y - shape.points[1].y, 2));
        const c = Math.sqrt(Math.pow(shape.points[0].x - shape.points[2].x, 2) + Math.pow(shape.points[0].y - shape.points[2].y, 2));
        const s = (a + b + c) / 2;
        const triArea = Math.sqrt(s * (s - a) * (s - b) * (s - c));
        const triAreaInUnits = unit === 'cm' ? triArea / 400 : triArea / 645.16;
        measurement = `Üçgen - Alan: ${triAreaInUnits.toFixed(2)} ${unit}²`;
        break;
      }
    }

    if (measurement) {
      setMeasurements([measurement, ...measurements].slice(0, 10));
    }
  };

  // Temizleme
  const clearCanvas = () => {
    setShapes([]);
    setCurrentShape([]);
    setMeasurements([]);
  };

  const undoLastShape = () => {
    if (shapes.length > 0) {
      setShapes(shapes.slice(0, -1));
      setMeasurements(measurements.slice(1));
    }
  };

  return (
    <div className="geometry-tools" role="application" aria-label="Geometri Araçları">
      <div className="tools-header">
        <h2>Geometri Araçları</h2>
      </div>

      <div className="tools-body">
        {/* Araç seçimi */}
        <div className="tool-selection">
          <h3>Araçlar</h3>
          <div className="tool-buttons">
            <button
              onClick={() => setTool('ruler')}
              className={tool === 'ruler' ? 'active' : ''}
              aria-label="Cetvel"
              aria-pressed={tool === 'ruler'}
            >
              📏 Cetvel
            </button>
            <button
              onClick={() => setTool('protractor')}
              className={tool === 'protractor' ? 'active' : ''}
              aria-label="İletki"
              aria-pressed={tool === 'protractor'}
            >
              📐 İletki
            </button>
            <button
              onClick={() => setTool('compass')}
              className={tool === 'compass' ? 'active' : ''}
              aria-label="Pergel"
              aria-pressed={tool === 'compass'}
            >
              🧭 Pergel
            </button>
          </div>

          <h3>Şekiller</h3>
          <div className="tool-buttons">
            <button
              onClick={() => setTool('line')}
              className={tool === 'line' ? 'active' : ''}
              aria-label="Çizgi"
              aria-pressed={tool === 'line'}
            >
              ➖ Çizgi
            </button>
            <button
              onClick={() => setTool('circle')}
              className={tool === 'circle' ? 'active' : ''}
              aria-label="Daire"
              aria-pressed={tool === 'circle'}
            >
              ⭕ Daire
            </button>
            <button
              onClick={() => setTool('rectangle')}
              className={tool === 'rectangle' ? 'active' : ''}
              aria-label="Dikdörtgen"
              aria-pressed={tool === 'rectangle'}
            >
              ▭ Dikdörtgen
            </button>
            <button
              onClick={() => setTool('triangle')}
              className={tool === 'triangle' ? 'active' : ''}
              aria-label="Üçgen"
              aria-pressed={tool === 'triangle'}
            >
              △ Üçgen
            </button>
            <button
              onClick={() => setTool('polygon')}
              className={tool === 'polygon' ? 'active' : ''}
              aria-label="Çokgen"
              aria-pressed={tool === 'polygon'}
            >
              ⬡ Çokgen
            </button>
          </div>
        </div>

        {/* Ayarlar */}
        <div className="tool-settings">
          <div className="setting-group">
            <label>Birim:</label>
            <select value={unit} onChange={(e) => setUnit(e.target.value as Unit)} aria-label="Ölçü birimi">
              <option value="cm">Santimetre (cm)</option>
              <option value="inch">İnç (inch)</option>
            </select>
          </div>

          <div className="setting-group">
            <label>Renk:</label>
            <div className="color-picker">
              {colors.map(color => (
                <button
                  key={color}
                  className={`color-btn ${selectedColor === color ? 'active' : ''}`}
                  style={{ backgroundColor: color }}
                  onClick={() => setSelectedColor(color)}
                  aria-label={`Renk: ${color}`}
                />
              ))}
            </div>
          </div>

          {tool === 'ruler' && (
            <div className="setting-group">
              <label>Cetvel Açısı: {rulerAngle}°</label>
              <input
                type="range"
                min="0"
                max="360"
                value={rulerAngle}
                onChange={(e) => setRulerAngle(parseInt(e.target.value))}
                aria-label="Cetvel açısı"
              />
            </div>
          )}

          {tool === 'protractor' && (
            <div className="setting-group">
              <label>İletki Açısı: {protractorAngle}°</label>
              <input
                type="range"
                min="0"
                max="360"
                value={protractorAngle}
                onChange={(e) => setProtractorAngle(parseInt(e.target.value))}
                aria-label="İletki açısı"
              />
            </div>
          )}

          <div className="setting-group">
            <label>
              <input
                type="checkbox"
                checked={gridVisible}
                onChange={(e) => setGridVisible(e.target.checked)}
                aria-label="Grid görünürlüğü"
              />
              Grid Göster
            </label>
          </div>
        </div>

        {/* Canvas */}
        <div className="canvas-container">
          <canvas
            ref={canvasRef}
            className="geometry-canvas"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onClick={handleClick}
            onDoubleClick={handleDoubleClick}
            aria-label="Geometri çizim alanı"
          />
        </div>

        {/* Kontroller */}
        <div className="canvas-controls">
          <button onClick={undoLastShape} aria-label="Geri al">
            ↶ Geri Al
          </button>
          <button onClick={clearCanvas} className="clear-btn" aria-label="Tümünü temizle">
            🗑️ Temizle
          </button>
        </div>

        {/* Ölçümler */}
        {measurements.length > 0 && (
          <div className="measurements-panel" role="region" aria-label="Ölçümler">
            <h3>Ölçümler</h3>
            <ul>
              {measurements.map((measurement, index) => (
                <li key={index}>{measurement}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Yardım */}
        <div className="tool-help">
          <details>
            <summary>❓ Nasıl Kullanılır?</summary>
            <ul>
              <li><strong>Cetvel:</strong> Açı ayarlayıcı ile döndürün</li>
              <li><strong>İletki:</strong> Açı ölçmek için kullanın</li>
              <li><strong>Çizgi/Dikdörtgen/Daire:</strong> Tıklayıp sürükleyin</li>
              <li><strong>Üçgen:</strong> 3 nokta tıklayın</li>
              <li><strong>Çokgen:</strong> Noktaları tıklayın, bitirmek için çift tıklayın</li>
            </ul>
          </details>
        </div>
      </div>
    </div>
  );
};

export default GeometryTools;
