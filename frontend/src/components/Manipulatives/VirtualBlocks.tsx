/**
 * Sanal Bloklar Bileşeni - Task 87.1
 * REQ-51.81-51.85: Virtual manipulative blocks, drag-and-drop, quantity operations
 */
import axios from 'axios';
import * as React from 'react';
import {  useState, useRef, useEffect  } from 'react';

interface Block {
  id: string;
  type: 'unit' | 'ten' | 'hundred';
  value: number;
  x: number;
  y: number;
  isDragging: boolean;
}

interface VirtualBlocksProps {
  onOperationComplete?: (result: number) => void;
}

const VirtualBlocks: React.FC<VirtualBlocksProps> = ({ onOperationComplete }) => {
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [selectedOperation, setSelectedOperation] = useState<'add' | 'subtract' | 'multiply' | 'divide'>('add');
  const [result, setResult] = useState<number>(0);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [draggedBlock, setDraggedBlock] = useState<Block | null>(null);

  // Blok renkleri
  const blockColors = {
    unit: '#4CAF50',      // Yeşil - 1'ler
    ten: '#2196F3',       // Mavi - 10'lar
    hundred: '#FF9800',    // Turuncu - 100'ler
  };

  // Blok boyutları
  const blockSizes = {
    unit: { width: 30, height: 30 },
    ten: { width: 30, height: 300 },
    hundred: { width: 300, height: 300 },
  };

  // Yeni blok ekle
  const addBlock = (type: 'unit' | 'ten' | 'hundred') => {
    const newBlock: Block = {
      id: `block-${Date.now()}-${Math.random()}`,
      type,
      value: type === 'unit' ? 1 : type === 'ten' ? 10 : 100,
      x: 50,
      y: 50,
      isDragging: false,
    };
    setBlocks([...blocks, newBlock]);
    calculateResult([...blocks, newBlock]);
  };

  // Sonucu hesapla
  const calculateResult = (currentBlocks: Block[]) => {
    const total = currentBlocks.reduce((sum, block) => sum + block.value, 0);
    setResult(total);
  };

  // Blok sil (reserved for future use)
  void function removeBlock(id: string) {
    const newBlocks = blocks.filter(b => b.id !== id);
    setBlocks(newBlocks);
    calculateResult(newBlocks);
  };

  // Canvas'a çiz
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {return;}

    const ctx = canvas.getContext('2d');
    if (!ctx) {return;}

    // Canvas'ı temizle
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Blokları çiz
    blocks.forEach(block => {
      const size = blockSizes[block.type];
      ctx.fillStyle = blockColors[block.type];
      ctx.fillRect(block.x, block.y, size.width, size.height);

      // Blok değerini yaz
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '16px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(
        block.value.toString(),
        block.x + size.width / 2,
        block.y + size.height / 2,
      );
    });
  }, [blocks]);

  // Mouse olayları
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) {return;}

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Tıklanan bloğu bul
    const clickedBlock = blocks.find(block => {
      const size = blockSizes[block.type];
      return x >= block.x && x <= block.x + size.width &&
             y >= block.y && y <= block.y + size.height;
    });

    if (clickedBlock) {
      setDraggedBlock(clickedBlock);
      setBlocks(blocks.map(b =>
        b.id === clickedBlock.id ? { ...b, isDragging: true } : b,
      ));
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!draggedBlock) {return;}

    const canvas = canvasRef.current;
    if (!canvas) {return;}

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setBlocks(blocks.map(b =>
      b.id === draggedBlock.id ? { ...b, x, y } : b,
    ));
  };

  const handleMouseUp = () => {
    if (draggedBlock) {
      setBlocks(blocks.map(b =>
        b.id === draggedBlock.id ? { ...b, isDragging: false } : b,
      ));
      setDraggedBlock(null);
    }
  };

  // İşlemi kaydet
  const saveOperation = async () => {
    try {
      const duration = Math.floor((Date.now() - startTime) / 1000);
      const blocksUsed = blocks.reduce((acc, block) => {
        const existing = acc.find(b => b.type === block.type);
        if (existing) {
          existing.count++;
        } else {
          acc.push({ type: block.type, count: 1 });
        }
        return acc;
      }, [] as Array<{ type: string; count: number }>);

      await axios.post('/api/manipulatives/virtual-blocks/operation', {
        operation_type: selectedOperation,
        blocks_used: blocksUsed,
        result,
        duration_seconds: duration,
      });

      if (onOperationComplete) {
        onOperationComplete(result);
      }

      // Başarı mesajı
      alert(`İşlem kaydedildi! Sonuç: ${result}`);

      // Yeni işlem için sıfırla
      setBlocks([]);
      setResult(0);
      setStartTime(Date.now());
    } catch (error) {
      console.error('İşlem kaydedilemedi:', error);
      alert('İşlem kaydedilemedi. Lütfen tekrar deneyin.');
    }
  };

  return (
    <div className="virtual-blocks-container p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-4">Sanal Bloklar</h2>

      {/* Blok ekleme butonları */}
      <div className="block-buttons mb-4 flex gap-2">
        <button
          onClick={() => addBlock('unit')}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
          style={{ backgroundColor: blockColors.unit }}
        >
          + Birler (1)
        </button>
        <button
          onClick={() => addBlock('ten')}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          style={{ backgroundColor: blockColors.ten }}
        >
          + Onlar (10)
        </button>
        <button
          onClick={() => addBlock('hundred')}
          className="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600"
          style={{ backgroundColor: blockColors.hundred }}
        >
          + Yüzler (100)
        </button>
      </div>

      {/* İşlem seçimi */}
      <div className="operation-selector mb-4">
        <label className="block text-sm font-medium mb-2">İşlem Türü:</label>
        <select
          value={selectedOperation}
          onChange={(e) => setSelectedOperation(e.target.value as any)}
          className="px-4 py-2 border rounded"
        >
          <option value="add">Toplama</option>
          <option value="subtract">Çıkarma</option>
          <option value="multiply">Çarpma</option>
          <option value="divide">Bölme</option>
        </select>
      </div>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        width={800}
        height={600}
        className="border-2 border-gray-300 rounded mb-4 cursor-move"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      />

      {/* Sonuç ve kontroller */}
      <div className="controls flex justify-between items-center">
        <div className="result text-xl font-bold">
          Toplam: <span className="text-blue-600">{result}</span>
        </div>
        <div className="actions flex gap-2">
          <button
            onClick={() => {
              setBlocks([]);
              setResult(0);
              setStartTime(Date.now());
            }}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Temizle
          </button>
          <button
            onClick={saveOperation}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            disabled={blocks.length === 0}
          >
            İşlemi Kaydet
          </button>
        </div>
      </div>

      {/* Yardım metni */}
      <div className="help-text mt-4 p-4 bg-blue-50 rounded">
        <p className="text-sm text-gray-700">
          <strong>Nasıl Kullanılır:</strong><br />
          1. Yukarıdaki butonlardan blok ekleyin<br />
          2. Blokları sürükleyerek yerleştirin<br />
          3. Toplam değeri görün<br />
          4. İşlemi kaydedin
        </p>
      </div>
    </div>
  );
};

export default VirtualBlocks;
