/**
 * İnteraktif Geometri - Task 87.3
 * REQ-51.91-51.95: Construction tools, measurement tools, transformation tools
 */
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

interface Point {
  x: number;
  y: number;
}

interface Shape {
  id: string;
  type: 'line' | 'circle' | 'rectangle' | 'triangle';
  points: Point[];
  color: string;
}

interface Measurement {
  id: string;
  type: 'length' | 'angle';
  value: number;
  points: Point[];
}

type Tool = 'select' | 'line' | 'circle' | 'rectangle' | 'triangle' | 
            'ruler' | 'protractor' | 'rotate' | 'reflect' | 'translate';

interface InteractiveGeometryProps {
  onToolUsage?: (tool: Tool) => void;
}

const InteractiveGeometry: React.FC<InteractiveGeometryProps> = ({ onToolUsage }) => {
  const [shapes, setShapes] = useState<Shape[]>([]);
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [selectedTool, setSelectedTool] = useState<Tool>('select');
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState<Point | null>(null);
  const [currentPoint, setCurrentPoint] = useState<Point | null>(null);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Canvas'a çiz
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Canvas'ı temizle
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Grid çiz
    drawGrid(ctx, canvas.width, canvas.height);

    // Şekilleri çiz
    shapes.forEach(shape => {
      drawShape(ctx, shape);
    });

    // Çizim sırasında geçici şekil
    if (isDrawing && startPoint && currentPoint) {
      drawTemporaryShape(ctx);
    }

    // Ölçümleri göster
    measurements.forEach(measurement => {
      drawMeasurement(ctx, measurement);
    });
  }, [shapes, measurements, isDrawing, startPoint, currentPoint]);

  // Grid çiz
  const drawGrid = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;

    // Dikey çizgiler
    for (let x = 0; x <= width; x += 50) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }

    // Yatay çizgiler
    for (let y = 0; y <= height; y += 50) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
  };

  // Şekil çiz
  const drawShape = (ctx: CanvasRenderingContext2D, shape: Shape) => {
    ctx.strokeStyle = shape.color;
    ctx.fillStyle = shape.color + '40'; // Yarı saydam
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

      case 'circle':
        if (shape.points.length >= 2) {
          const radius = Math.sqrt(
            Math.pow(shape.points[1].x - shape.points[0].x, 2) +
            Math.pow(shape.points[1].y - shape.points[0].y, 2)
          );
          ctx.beginPath();
          ctx.arc(shape.points[0].x, shape.points[0].y, radius, 0, 2 * Math.PI);
          ctx.stroke();
          ctx.fill();
        }
        break;

      case 'rectangle':
        if (shape.points.length >= 2) {
          const width = shape.points[1].x - shape.points[0].x;
          const height = shape.points[1].y - shape.points[0].y;
          ctx.beginPath();
          ctx.rect(shape.points[0].x, shape.points[0].y, width, height);
          ctx.stroke();
          ctx.fill();
        }
        break;

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
    }
  };

  // Geçici şekil çiz
  const drawTemporaryShape = (ctx: CanvasRenderingContext2D) => {
    if (!startPoint || !currentPoint) return;

    ctx.strokeStyle = '#2196F3';
    ctx.setLineDash([5, 5]);
    ctx.lineWidth = 2;

    switch (selectedTool) {
      case 'line':
        ctx.beginPath();
        ctx.moveTo(startPoint.x, startPoint.y);
        ctx.lineTo(currentPoint.x, currentPoint.y);
        ctx.stroke();
        break;

      case 'circle':
        const radius = Math.sqrt(
          Math.pow(currentPoint.x - startPoint.x, 2) +
          Math.pow(currentPoint.y - startPoint.y, 2)
        );
        ctx.beginPath();
        ctx.arc(startPoint.x, startPoint.y, radius, 0, 2 * Math.PI);
        ctx.stroke();
        break;

      case 'rectangle':
        const width = currentPoint.x - startPoint.x;
        const height = currentPoint.y - startPoint.y;
        ctx.beginPath();
        ctx.rect(startPoint.x, startPoint.y, width, height);
        ctx.stroke();
        break;
    }

    ctx.setLineDash([]);
  };

  // Ölçüm çiz
  const drawMeasurement = (ctx: CanvasRenderingContext2D, measurement: Measurement) => {
    ctx.fillStyle = '#FF5722';
    ctx.font = '14px Arial';

    if (measurement.type === 'length' && measurement.points.length >= 2) {
      const midX = (measurement.points[0].x + measurement.points[1].x) / 2;
      const midY = (measurement.points[0].y + measurement.points[1].y) / 2;
      ctx.fillText(`${measurement.value.toFixed(1)} px`, midX, midY);
    } else if (measurement.type === 'angle' && measurement.points.length >= 3) {
      ctx.fillText(`${measurement.value.toFixed(1)}°`, measurement.points[1].x, measurement.points[1].y - 10);
    }
  };

  // Mouse olayları
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const point: Point = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };

    if (['line', 'circle', 'rectangle'].includes(selectedTool)) {
      setIsDrawing(true);
      setStartPoint(point);
      setCurrentPoint(point);
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const point: Point = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };

    setCurrentPoint(point);
  };

  const handleMouseUp = () => {
    if (!isDrawing || !startPoint || !currentPoint) return;

    // Yeni şekil oluştur
    const newShape: Shape = {
      id: `shape-${Date.now()}`,
      type: selectedTool as any,
      points: [startPoint, currentPoint],
      color: '#2196F3'
    };

    setShapes([...shapes, newShape]);
    setIsDrawing(false);
    setStartPoint(null);
    setCurrentPoint(null);

    if (onToolUsage) {
      onToolUsage(selectedTool);
    }
  };

  // Ölçüm yap
  const measureLength = () => {
    if (shapes.length === 0) {
      alert('Önce bir şekil çizin!');
      return;
    }

    const lastShape = shapes[shapes.length - 1];
    if (lastShape.points.length >= 2) {
      const length = Math.sqrt(
        Math.pow(lastShape.points[1].x - lastShape.points[0].x, 2) +
        Math.pow(lastShape.points[1].y - lastShape.points[0].y, 2)
      );

      const newMeasurement: Measurement = {
        id: `measurement-${Date.now()}`,
        type: 'length',
        value: length,
        points: lastShape.points
      };

      setMeasurements([...measurements, newMeasurement]);
    }
  };

  // Kullanımı kaydet
  const saveUsage = async () => {
    try {
      const duration = Math.floor((Date.now() - startTime) / 1000);

      await axios.post('/api/manipulatives/geometry/tool-usage', {
        user_id: 0, // Backend'de current_user'dan alınacak
        tool_type: selectedTool,
        shapes_created: shapes.map(s => ({ type: s.type, points: s.points.length })),
        measurements: measurements.map(m => ({ type: m.type, value: m.value })),
        duration_seconds: duration
      });

      alert('Kullanım kaydedildi!');
      
      // Yeni çalışma için sıfırla
      setShapes([]);
      setMeasurements([]);
      setStartTime(Date.now());
    } catch (error) {
      console.error('Kullanım kaydedilemedi:', error);
      alert('Kullanım kaydedilemedi. Lütfen tekrar deneyin.');
    }
  };

  return (
    <div className="interactive-geometry-container p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-4">İnteraktif Geometri</h2>

      {/* Araç çubuğu */}
      <div className="toolbar mb-4 flex flex-wrap gap-2">
        <div className="tool-group border-r pr-2">
          <span className="text-sm font-medium mr-2">Çizim:</span>
          <button
            onClick={() => setSelectedTool('line')}
            className={`px-3 py-2 rounded ${selectedTool === 'line' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            title="Doğru"
          >
            📏 Doğru
          </button>
          <button
            onClick={() => setSelectedTool('circle')}
            className={`px-3 py-2 rounded ${selectedTool === 'circle' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            title="Daire"
          >
            ⭕ Daire
          </button>
          <button
            onClick={() => setSelectedTool('rectangle')}
            className={`px-3 py-2 rounded ${selectedTool === 'rectangle' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            title="Dikdörtgen"
          >
            ▭ Dikdörtgen
          </button>
        </div>

        <div className="tool-group border-r pr-2">
          <span className="text-sm font-medium mr-2">Ölçüm:</span>
          <button
            onClick={measureLength}
            className="px-3 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            title="Uzunluk Ölç"
          >
            📐 Uzunluk
          </button>
        </div>

        <div className="tool-group">
          <span className="text-sm font-medium mr-2">Dönüşüm:</span>
          <button
            onClick={() => setSelectedTool('rotate')}
            className={`px-3 py-2 rounded ${selectedTool === 'rotate' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            title="Döndür"
          >
            🔄 Döndür
          </button>
          <button
            onClick={() => setSelectedTool('reflect')}
            className={`px-3 py-2 rounded ${selectedTool === 'reflect' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            title="Yansıt"
          >
            ↔️ Yansıt
          </button>
          <button
            onClick={() => setSelectedTool('translate')}
            className={`px-3 py-2 rounded ${selectedTool === 'translate' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            title="Ötle"
          >
            ➡️ Ötle
          </button>
        </div>
      </div>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        width={800}
        height={600}
        className="border-2 border-gray-300 rounded mb-4 cursor-crosshair"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      />

      {/* Kontroller */}
      <div className="controls flex justify-between items-center">
        <div className="stats text-sm text-gray-600">
          Şekiller: {shapes.length} | Ölçümler: {measurements.length}
        </div>
        <div className="actions flex gap-2">
          <button
            onClick={() => {
              setShapes([]);
              setMeasurements([]);
            }}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Temizle
          </button>
          <button
            onClick={saveUsage}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            disabled={shapes.length === 0}
          >
            Kaydet
          </button>
        </div>
      </div>

      {/* Yardım metni */}
      <div className="help-text mt-4 p-4 bg-blue-50 rounded">
        <p className="text-sm text-gray-700">
          <strong>Nasıl Kullanılır:</strong><br />
          1. Bir araç seçin (Doğru, Daire, Dikdörtgen)<br />
          2. Canvas üzerinde tıklayıp sürükleyin<br />
          3. Ölçüm araçlarıyla uzunluk ve açı ölçün<br />
          4. Dönüşüm araçlarıyla şekilleri değiştirin
        </p>
      </div>
    </div>
  );
};

export default InteractiveGeometry;
