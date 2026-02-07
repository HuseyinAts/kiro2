/**
 * Scientific Calculator Component
 *
 * Bilimsel hesap makinesi - Diskalkuli desteği için gelişmiş matematik işlemleri.
 *
 * Özellikler:
 * - Temel aritmetik işlemler (+, -, *, /)
 * - Bilimsel fonksiyonlar (sin, cos, tan, log, ln, sqrt, pow)
 * - Sabitler (π, e)
 * - İşlem geçmişi
 * - Klavye desteği
 *
 * Gereksinimler: REQ-51.41 - REQ-51.45
 */

import * as React from 'react';
import {  useState, useEffect, useCallback  } from 'react';
import './ScientificCalculator.css';

interface CalculationHistory {
  expression: string;
  result: string;
  timestamp: Date;
}

const ScientificCalculator: React.FC = () => {
  const [display, setDisplay] = useState<string>('0');
  const [expression, setExpression] = useState<string>('');
  const [history, setHistory] = useState<CalculationHistory[]>([]);
  const [memory, setMemory] = useState<number>(0);
  const [angleMode, setAngleMode] = useState<'deg' | 'rad'>('deg');
  const [showHistory, setShowHistory] = useState<boolean>(false);

  // Temel işlemler
  const handleNumber = (num: string) => {
    if (display === '0' || display === 'Error') {
      setDisplay(num);
    } else {
      setDisplay(display + num);
    }
  };

  const handleOperator = (op: string) => {
    setExpression(display + ' ' + op + ' ');
    setDisplay('0');
  };

  const handleDecimal = () => {
    if (!display.includes('.')) {
      setDisplay(display + '.');
    }
  };

  const handleClear = () => {
    setDisplay('0');
    setExpression('');
  };

  const handleBackspace = () => {
    if (display.length > 1) {
      setDisplay(display.slice(0, -1));
    } else {
      setDisplay('0');
    }
  };

  // Bilimsel fonksiyonlar
  const handleScientificFunction = (func: string) => {
    try {
      const value = parseFloat(display);
      let result: number;

      switch (func) {
        case 'sin':
          result = angleMode === 'deg' ? Math.sin(value * Math.PI / 180) : Math.sin(value);
          break;
        case 'cos':
          result = angleMode === 'deg' ? Math.cos(value * Math.PI / 180) : Math.cos(value);
          break;
        case 'tan':
          result = angleMode === 'deg' ? Math.tan(value * Math.PI / 180) : Math.tan(value);
          break;
        case 'log':
          result = Math.log10(value);
          break;
        case 'ln':
          result = Math.log(value);
          break;
        case 'sqrt':
          result = Math.sqrt(value);
          break;
        case 'square':
          result = value * value;
          break;
        case 'cube':
          result = value * value * value;
          break;
        case 'reciprocal':
          result = 1 / value;
          break;
        case 'factorial':
          result = factorial(value);
          break;
        case 'abs':
          result = Math.abs(value);
          break;
        default:
          result = value;
      }

      const expr = `${func}(${display})`;
      addToHistory(expr, result.toString());
      setDisplay(result.toString());
    } catch {
      setDisplay('Error');
    }
  };

  const factorial = (n: number): number => {
    if (n < 0) {throw new Error('Negative factorial');}
    if (n === 0 || n === 1) {return 1;}
    return n * factorial(n - 1);
  };

  // Sabitler
  const handleConstant = (constant: string) => {
    switch (constant) {
      case 'pi':
        setDisplay(Math.PI.toString());
        break;
      case 'e':
        setDisplay(Math.E.toString());
        break;
    }
  };

  // Hesaplama
  const handleEquals = () => {
    try {
      const fullExpression = expression + display;
      // Güvenli eval alternatifi - sadece temel matematik işlemleri
      const result = evaluateExpression(fullExpression);
      addToHistory(fullExpression, result.toString());
      setDisplay(result.toString());
      setExpression('');
    } catch {
      setDisplay('Error');
    }
  };

  const evaluateExpression = (expr: string): number => {
    // Basit ve güvenli matematik ifadesi değerlendirici
    // Sadece sayılar ve temel operatörler (+, -, *, /) desteklenir
    const sanitized = expr.replace(/[^0-9+\-*/().]/g, '');
    return Function('"use strict"; return (' + sanitized + ')')();
  };

  // Bellek işlemleri
  const handleMemoryStore = () => {
    setMemory(parseFloat(display));
  };

  const handleMemoryRecall = () => {
    setDisplay(memory.toString());
  };

  const handleMemoryClear = () => {
    setMemory(0);
  };

  const handleMemoryAdd = () => {
    setMemory(memory + parseFloat(display));
  };

  const handleMemorySubtract = () => {
    setMemory(memory - parseFloat(display));
  };

  // Geçmiş yönetimi
  const addToHistory = (expr: string, result: string) => {
    const newEntry: CalculationHistory = {
      expression: expr,
      result: result,
      timestamp: new Date(),
    };
    setHistory([newEntry, ...history].slice(0, 50)); // Son 50 işlem
  };

  const clearHistory = () => {
    setHistory([]);
  };

  const loadFromHistory = (entry: CalculationHistory) => {
    setDisplay(entry.result);
    setShowHistory(false);
  };

  // Klavye desteği
  const handleKeyPress = useCallback((event: KeyboardEvent) => {
    const key = event.key;

    if (key >= '0' && key <= '9') {
      handleNumber(key);
    } else if (key === '.') {
      handleDecimal();
    } else if (key === '+' || key === '-' || key === '*' || key === '/') {
      handleOperator(key);
    } else if (key === 'Enter' || key === '=') {
      event.preventDefault();
      handleEquals();
    } else if (key === 'Escape') {
      handleClear();
    } else if (key === 'Backspace') {
      event.preventDefault();
      handleBackspace();
    }
  }, [display, expression]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [handleKeyPress]);

  return (
    <div className="scientific-calculator" role="application" aria-label="Bilimsel Hesap Makinesi">
      <div className="calculator-header">
        <h2>Bilimsel Hesap Makinesi</h2>
        <div className="calculator-controls">
          <button
            onClick={() => setAngleMode(angleMode === 'deg' ? 'rad' : 'deg')}
            className="mode-toggle"
            aria-label={`Açı modu: ${angleMode === 'deg' ? 'Derece' : 'Radyan'}`}
          >
            {angleMode.toUpperCase()}
          </button>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="history-toggle"
            aria-label="Geçmişi göster/gizle"
          >
            📜 Geçmiş
          </button>
        </div>
      </div>

      <div className="calculator-body">
        {/* Ekran */}
        <div className="calculator-display">
          {expression && <div className="expression-display">{expression}</div>}
          <div className="main-display" aria-live="polite" aria-atomic="true">
            {display}
          </div>
          {memory !== 0 && <div className="memory-indicator">M: {memory}</div>}
        </div>

        {/* Tuş takımı */}
        <div className="calculator-keypad">
          {/* Bellek tuşları */}
          <div className="memory-row">
            <button onClick={handleMemoryClear} aria-label="Belleği temizle">MC</button>
            <button onClick={handleMemoryRecall} aria-label="Bellekten getir">MR</button>
            <button onClick={handleMemoryStore} aria-label="Belleğe kaydet">MS</button>
            <button onClick={handleMemoryAdd} aria-label="Belleğe ekle">M+</button>
            <button onClick={handleMemorySubtract} aria-label="Bellekten çıkar">M-</button>
          </div>

          {/* Bilimsel fonksiyonlar - 1. satır */}
          <div className="function-row">
            <button onClick={() => handleScientificFunction('sin')} aria-label="Sinüs">sin</button>
            <button onClick={() => handleScientificFunction('cos')} aria-label="Kosinüs">cos</button>
            <button onClick={() => handleScientificFunction('tan')} aria-label="Tanjant">tan</button>
            <button onClick={() => handleScientificFunction('log')} aria-label="Logaritma taban 10">log</button>
            <button onClick={() => handleScientificFunction('ln')} aria-label="Doğal logaritma">ln</button>
          </div>

          {/* Bilimsel fonksiyonlar - 2. satır */}
          <div className="function-row">
            <button onClick={() => handleScientificFunction('sqrt')} aria-label="Karekök">√</button>
            <button onClick={() => handleScientificFunction('square')} aria-label="Kare">x²</button>
            <button onClick={() => handleScientificFunction('cube')} aria-label="Küp">x³</button>
            <button onClick={() => handleScientificFunction('reciprocal')} aria-label="Ters">1/x</button>
            <button onClick={() => handleScientificFunction('factorial')} aria-label="Faktöriyel">n!</button>
          </div>

          {/* Sabitler ve özel fonksiyonlar */}
          <div className="function-row">
            <button onClick={() => handleConstant('pi')} aria-label="Pi sayısı">π</button>
            <button onClick={() => handleConstant('e')} aria-label="Euler sayısı">e</button>
            <button onClick={() => handleScientificFunction('abs')} aria-label="Mutlak değer">|x|</button>
            <button onClick={handleBackspace} aria-label="Sil">⌫</button>
            <button onClick={handleClear} className="clear-btn" aria-label="Temizle">C</button>
          </div>

          {/* Sayı tuşları ve temel işlemler */}
          <div className="number-pad">
            <button onClick={() => handleNumber('7')} aria-label="7">7</button>
            <button onClick={() => handleNumber('8')} aria-label="8">8</button>
            <button onClick={() => handleNumber('9')} aria-label="9">9</button>
            <button onClick={() => handleOperator('/')} className="operator-btn" aria-label="Bölme">/</button>

            <button onClick={() => handleNumber('4')} aria-label="4">4</button>
            <button onClick={() => handleNumber('5')} aria-label="5">5</button>
            <button onClick={() => handleNumber('6')} aria-label="6">6</button>
            <button onClick={() => handleOperator('*')} className="operator-btn" aria-label="Çarpma">×</button>

            <button onClick={() => handleNumber('1')} aria-label="1">1</button>
            <button onClick={() => handleNumber('2')} aria-label="2">2</button>
            <button onClick={() => handleNumber('3')} aria-label="3">3</button>
            <button onClick={() => handleOperator('-')} className="operator-btn" aria-label="Çıkarma">-</button>

            <button onClick={() => handleNumber('0')} aria-label="0">0</button>
            <button onClick={handleDecimal} aria-label="Ondalık nokta">.</button>
            <button onClick={handleEquals} className="equals-btn" aria-label="Eşittir">=</button>
            <button onClick={() => handleOperator('+')} className="operator-btn" aria-label="Toplama">+</button>
          </div>
        </div>
      </div>

      {/* Geçmiş paneli */}
      {showHistory && (
        <div className="history-panel" role="region" aria-label="İşlem geçmişi">
          <div className="history-header">
            <h3>İşlem Geçmişi</h3>
            <button onClick={clearHistory} aria-label="Geçmişi temizle">
              🗑️ Temizle
            </button>
          </div>
          <div className="history-list">
            {history.length === 0 ? (
              <p className="empty-history">Henüz işlem yapılmadı</p>
            ) : (
              history.map((entry, index) => (
                <div
                  key={index}
                  className="history-item"
                  onClick={() => loadFromHistory(entry)}
                  role="button"
                  tabIndex={0}
                  aria-label={`${entry.expression} eşittir ${entry.result}`}
                >
                  <div className="history-expression">{entry.expression}</div>
                  <div className="history-result">= {entry.result}</div>
                  <div className="history-time">
                    {entry.timestamp.toLocaleTimeString('tr-TR')}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Klavye kısayolları yardımı */}
      <div className="keyboard-shortcuts" role="region" aria-label="Klavye kısayolları">
        <details>
          <summary>⌨️ Klavye Kısayolları</summary>
          <ul>
            <li><kbd>0-9</kbd>: Sayılar</li>
            <li><kbd>+</kbd> <kbd>-</kbd> <kbd>*</kbd> <kbd>/</kbd>: İşlemler</li>
            <li><kbd>Enter</kbd> veya <kbd>=</kbd>: Hesapla</li>
            <li><kbd>Esc</kbd>: Temizle</li>
            <li><kbd>Backspace</kbd>: Sil</li>
            <li><kbd>.</kbd>: Ondalık nokta</li>
          </ul>
        </details>
      </div>
    </div>
  );
};

export default ScientificCalculator;
