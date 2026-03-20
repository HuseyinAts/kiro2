/**
 * Dijital Tangram - Task 87.4
 * REQ-51.96-51.100: Tangram puzzle interface, shape recognition, spatial reasoning
 */
import axios from 'axios';
import * as React from 'react';
import {  useState, useRef, useEffect  } from 'react';

interface TangramPiece {
  id: string;
  type: 'large-triangle' | 'medium-triangle' | 'small-triangle' | 'square' | 'parallelogram';
  color: string;
  x: number;
  y: number;
  rotation: number;
  isDragging: boolean;
}

interface TangramPuzzle {
  id: string;
  name: string;
  difficulty: string;
  pieces: number;
  target_shape: string;
  description: string;
}

interface DigitalTangramProps {
  onPuzzleComplete?: (puzzleId: string) => void;
}

const DigitalTangram: React.FC<DigitalTangramProps> = ({ onPuzzleComplete }) => {
  const [pieces, setPieces] = useState<TangramPiece[]>([]);
  const [puzzles, setPuzzles] = useState<TangramPuzzle[]>([]);
  const [selectedPuzzle, setSelectedPuzzle] = useState<TangramPuzzle | null>(null);
  const [attempts, setAttempts] = useState(0);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [draggedPiece, setDraggedPiece] = useState<TangramPiece | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Tangram parçalarını başlat
  useEffect(() => {
    initializePieces();
    loadPuzzles();
  }, []);

  const initializePieces = () => {
    const initialPieces: TangramPiece[] = [
      // 2 büyük üçgen
      { id: 'large-1', type: 'large-triangle', color: '#FF5722', x: 50, y: 50, rotation: 0, isDragging: false },
      { id: 'large-2', type: 'large-triangle', color: '#FF9800', x: 150, y: 50, rotation: 0, isDragging: false },
      // 1 orta üçgen
      { id: 'medium-1', type: 'medium-triangle', color: '#FFC107', x: 250, y: 50, rotation: 0, isDragging: false },
      // 2 küçük üçgen
      { id: 'small-1', type: 'small-triangle', color: '#4CAF50', x: 350, y: 50, rotation: 0, isDragging: false },
      { id: 'small-2', type: 'small-triangle', color: '#2196F3', x: 450, y: 50, rotation: 0, isDragging: false },
      // 1 kare
      { id: 'square-1', type: 'square', color: '#9C27B0', x: 550, y: 50, rotation: 0, isDragging: false },
      // 1 paralelkenar
      { id: 'parallelogram-1', type: 'parallelogram', color: '#E91E63', x: 650, y: 50, rotation: 0, isDragging: false },
    ];
    setPieces(initialPieces);
  };

  const loadPuzzles = async () => {
    try {
      const response = await axios.get('/api/v1/manipulatives/tangram/puzzles');
      if (response.data.success) {
        setPuzzles(response.data.data);
        if (response.data.data.length > 0) {
          setSelectedPuzzle(response.data.data[0]);
        }
      }
    } catch (error) {
      console.error('Puzzle listesi yüklenemedi:', error);
    }
  };

  // Canvas'a çiz
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {return;}

    const ctx = canvas.getContext('2d');
    if (!ctx) {return;}

    // Canvas'ı temizle
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Hedef şekil alanı
    ctx.strokeStyle = '#BDBDBD';
    ctx.setLineDash([10, 5]);
    ctx.strokeRect(50, 200, 400, 400);
    ctx.setLineDash([]);

    // Parçaları çiz
    pieces.forEach(piece => {
      drawPiece(ctx, piece);
    });
  }, [pieces]);

  // Parça çiz
  const drawPiece = (ctx: CanvasRenderingContext2D, piece: TangramPiece) => {
    ctx.save();
    ctx.translate(piece.x, piece.y);
    ctx.rotate((piece.rotation * Math.PI) / 180);

    ctx.fillStyle = piece.color;
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;

    switch (piece.type) {
      case 'large-triangle':
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(80, 0);
        ctx.lineTo(40, 80);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        break;

      case 'medium-triangle':
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(60, 0);
        ctx.lineTo(30, 60);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        break;

      case 'small-triangle':
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(40, 0);
        ctx.lineTo(20, 40);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        break;

      case 'square':
        ctx.fillRect(0, 0, 40, 40);
        ctx.strokeRect(0, 0, 40, 40);
        break;

      case 'parallelogram':
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(50, 0);
        ctx.lineTo(40, 30);
        ctx.lineTo(-10, 30);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        break;
    }

    ctx.restore();
  };

  // Mouse olayları
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) {return;}

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Tıklanan parçayı bul (ters sırada kontrol et - en üstteki parça)
    for (let i = pieces.length - 1; i >= 0; i--) {
      const piece = pieces[i];
      if (isPointInPiece(x, y, piece)) {
        setDraggedPiece(piece);
        setPieces(pieces.map(p =>
          p.id === piece.id ? { ...p, isDragging: true } : p,
        ));
        break;
      }
    }
  };

  const isPointInPiece = (x: number, y: number, piece: TangramPiece): boolean => {
    // Basit bounding box kontrolü
    const size = piece.type.includes('large') ? 80 : piece.type.includes('medium') ? 60 : 40;
    return x >= piece.x && x <= piece.x + size &&
           y >= piece.y && y <= piece.y + size;
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!draggedPiece) {return;}

    const canvas = canvasRef.current;
    if (!canvas) {return;}

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setPieces(pieces.map(p =>
      p.id === draggedPiece.id ? { ...p, x, y } : p,
    ));
  };

  const handleMouseUp = () => {
    if (draggedPiece) {
      setPieces(pieces.map(p =>
        p.id === draggedPiece.id ? { ...p, isDragging: false } : p,
      ));
      setDraggedPiece(null);
      setAttempts(attempts + 1);
    }
  };

  // Parçayı döndür
  const rotatePiece = (pieceId: string) => {
    setPieces(pieces.map(p =>
      p.id === pieceId ? { ...p, rotation: (p.rotation + 45) % 360 } : p,
    ));
  };

  // Puzzle'ı kontrol et
  const checkPuzzle = () => {
    // Basit kontrol - tüm parçalar hedef alanda mı?
    const inTargetArea = pieces.filter(p =>
      p.x >= 50 && p.x <= 450 && p.y >= 200 && p.y <= 600,
    );

    if (inTargetArea.length === pieces.length) {
      alert('Tebrikler! Puzzle tamamlandı!');
      savePuzzle(true);
    } else {
      alert(`${inTargetArea.length}/${pieces.length} parça doğru konumda. Devam edin!`);
    }
  };

  // Puzzle'ı kaydet
  const savePuzzle = async (completed: boolean) => {
    if (!selectedPuzzle) {return;}

    try {
      const duration = Math.floor((Date.now() - startTime) / 1000);

      await axios.post('/api/v1/manipulatives/tangram/puzzle', {
        user_id: 0, // Backend'de current_user'dan alınacak
        puzzle_id: selectedPuzzle.id,
        pieces_used: pieces.map(p => ({
          id: p.id,
          type: p.type,
          x: p.x,
          y: p.y,
          rotation: p.rotation,
        })),
        completed,
        attempts,
        duration_seconds: duration,
      });

      if (completed && onPuzzleComplete) {
        onPuzzleComplete(selectedPuzzle.id);
      }

      if (!completed) {
        alert('İlerleme kaydedildi!');
      }
    } catch (error) {
      console.error('Puzzle kaydedilemedi:', error);
      alert('Puzzle kaydedilemedi. Lütfen tekrar deneyin.');
    }
  };

  // Puzzle değiştir
  const changePuzzle = (puzzle: TangramPuzzle) => {
    setSelectedPuzzle(puzzle);
    initializePieces();
    setAttempts(0);
    setStartTime(Date.now());
  };

  return (
    <div className="digital-tangram-container p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-4">Dijital Tangram</h2>

      {/* Puzzle seçici */}
      <div className="puzzle-selector mb-4">
        <label className="block text-sm font-medium mb-2">Puzzle Seç:</label>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          {puzzles.map(puzzle => (
            <button
              key={puzzle.id}
              onClick={() => changePuzzle(puzzle)}
              className={`p-2 border-2 rounded text-sm ${
                selectedPuzzle?.id === puzzle.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-blue-300'
              }`}
            >
              <div className="font-bold">{puzzle.name}</div>
              <div className="text-xs text-gray-600">{puzzle.difficulty}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        width={800}
        height={650}
        className="border-2 border-gray-300 rounded mb-4 cursor-move"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      />

      {/* Kontroller */}
      <div className="controls mb-4">
        <div className="flex justify-between items-center mb-2">
          <div className="stats text-sm text-gray-600">
            Denemeler: {attempts} | Süre: {Math.floor((Date.now() - startTime) / 1000)}s
          </div>
          <div className="actions flex gap-2">
            <button
              onClick={initializePieces}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              Sıfırla
            </button>
            <button
              onClick={() => savePuzzle(false)}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Kaydet
            </button>
            <button
              onClick={checkPuzzle}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              Kontrol Et
            </button>
          </div>
        </div>

        {/* Parça döndürme */}
        <div className="piece-controls">
          <span className="text-sm font-medium mr-2">Parça Döndür:</span>
          <div className="flex flex-wrap gap-2">
            {pieces.map(piece => (
              <button
                key={piece.id}
                onClick={() => rotatePiece(piece.id)}
                className="px-2 py-1 text-xs rounded"
                style={{ backgroundColor: piece.color, color: '#FFFFFF' }}
                title={`${piece.type} - ${piece.rotation}°`}
              >
                🔄 {piece.id}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Yardım metni */}
      <div className="help-text p-4 bg-blue-50 rounded">
        <p className="text-sm text-gray-700">
          <strong>Tangram Nedir?</strong><br />
          Tangram, 7 geometrik parçadan oluşan Çin kökenli bir bulmacadır.
          Parçaları kullanarak çeşitli şekiller oluşturabilirsiniz.<br /><br />
          <strong>Nasıl Oynanır:</strong><br />
          1. Bir puzzle seçin<br />
          2. Parçaları sürükleyerek hedef alana yerleştirin<br />
          3. Parçaları döndürmek için butonları kullanın<br />
          4. &quot;Kontrol Et&quot; ile çözümünüzü kontrol edin<br /><br />
          <strong>İpuçları:</strong><br />
          • Büyük parçalardan başlayın<br />
          • Parçaları 45° döndürebilirsiniz<br />
          • Tüm parçaları kullanmalısınız
        </p>
      </div>
    </div>
  );
};

export default DigitalTangram;
