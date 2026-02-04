/**
 * Formula Editor Component
 * 
 * Formül editörü - LaTeX-style matematik formül girişi ve görsel oluşturucu.
 * 
 * Özellikler:
 * - LaTeX formatında formül girişi
 * - Görsel formül oluşturucu
 * - Formül kütüphanesi
 * - Canlı önizleme
 * - Formül şablonları
 * 
 * Gereksinimler: REQ-51.56 - REQ-51.60
 */

import React, { useState, useEffect } from 'react';
import './FormulaEditor.css';

interface FormulaTemplate {
  name: string;
  latex: string;
  category: string;
  description: string;
}

const FormulaEditor: React.FC = () => {
  const [latexInput, setLatexInput] = useState<string>('');
  const [savedFormulas, setSavedFormulas] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showLibrary, setShowLibrary] = useState<boolean>(false);

  // Formül şablonları
  const templates: FormulaTemplate[] = [
    // Temel işlemler
    { name: 'Kesir', latex: '\\frac{a}{b}', category: 'basic', description: 'Basit kesir' },
    { name: 'Üs', latex: 'x^{n}', category: 'basic', description: 'Üs alma' },
    { name: 'Alt simge', latex: 'x_{n}', category: 'basic', description: 'Alt simge' },
    { name: 'Karekök', latex: '\\sqrt{x}', category: 'basic', description: 'Karekök' },
    { name: 'n. kök', latex: '\\sqrt[n]{x}', category: 'basic', description: 'n. dereceden kök' },
    
    // Cebir
    { name: 'İkinci derece', latex: 'ax^2 + bx + c = 0', category: 'algebra', description: 'İkinci derece denklem' },
    { name: 'Çözüm formülü', latex: 'x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}', category: 'algebra', description: 'İkinci derece çözüm' },
    { name: 'Binom', latex: '(a + b)^2 = a^2 + 2ab + b^2', category: 'algebra', description: 'Binom açılımı' },
    
    // Geometri
    { name: 'Pisagor', latex: 'a^2 + b^2 = c^2', category: 'geometry', description: 'Pisagor teoremi' },
    { name: 'Daire alanı', latex: 'A = \\pi r^2', category: 'geometry', description: 'Daire alanı formülü' },
    { name: 'Daire çevresi', latex: 'C = 2\\pi r', category: 'geometry', description: 'Daire çevresi' },
    { name: 'Üçgen alanı', latex: 'A = \\frac{1}{2}bh', category: 'geometry', description: 'Üçgen alanı' },
    
    // Trigonometri
    { name: 'Sinüs', latex: '\\sin(\\theta)', category: 'trigonometry', description: 'Sinüs fonksiyonu' },
    { name: 'Kosinüs', latex: '\\cos(\\theta)', category: 'trigonometry', description: 'Kosinüs fonksiyonu' },
    { name: 'Tanjant', latex: '\\tan(\\theta)', category: 'trigonometry', description: 'Tanjant fonksiyonu' },
    { name: 'Sinüs teoremi', latex: '\\frac{a}{\\sin A} = \\frac{b}{\\sin B} = \\frac{c}{\\sin C}', category: 'trigonometry', description: 'Sinüs teoremi' },
    
    // Kalkülüs
    { name: 'Türev', latex: '\\frac{d}{dx}f(x)', category: 'calculus', description: 'Türev notasyonu' },
    { name: 'İntegral', latex: '\\int f(x)dx', category: 'calculus', description: 'Belirsiz integral' },
    { name: 'Belirli integral', latex: '\\int_{a}^{b} f(x)dx', category: 'calculus', description: 'Belirli integral' },
    { name: 'Limit', latex: '\\lim_{x \\to a} f(x)', category: 'calculus', description: 'Limit notasyonu' },
    
    // Matrisler
    { name: '2x2 Matris', latex: '\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}', category: 'matrix', description: '2x2 matris' },
    { name: 'Determinant', latex: '\\begin{vmatrix} a & b \\\\ c & d \\end{vmatrix}', category: 'matrix', description: 'Determinant' },
    
    // İstatistik
    { name: 'Ortalama', latex: '\\bar{x} = \\frac{1}{n}\\sum_{i=1}^{n} x_i', category: 'statistics', description: 'Aritmetik ortalama' },
    { name: 'Standart sapma', latex: '\\sigma = \\sqrt{\\frac{1}{n}\\sum_{i=1}^{n}(x_i - \\bar{x})^2}', category: 'statistics', description: 'Standart sapma' },
  ];

  const categories = [
    { id: 'all', name: 'Tümü' },
    { id: 'basic', name: 'Temel' },
    { id: 'algebra', name: 'Cebir' },
    { id: 'geometry', name: 'Geometri' },
    { id: 'trigonometry', name: 'Trigonometri' },
    { id: 'calculus', name: 'Kalkülüs' },
    { id: 'matrix', name: 'Matris' },
    { id: 'statistics', name: 'İstatistik' },
  ];

  // Hızlı ekleme butonları
  const quickInserts = [
    { label: 'Kesir', latex: '\\frac{}{}' },
    { label: 'Üs', latex: '^{}' },
    { label: 'Alt', latex: '_{}' },
    { label: '√', latex: '\\sqrt{}' },
    { label: '∑', latex: '\\sum_{}^{}' },
    { label: '∫', latex: '\\int_{}^{}' },
    { label: 'π', latex: '\\pi' },
    { label: '∞', latex: '\\infty' },
    { label: '≤', latex: '\\leq' },
    { label: '≥', latex: '\\geq' },
    { label: '≠', latex: '\\neq' },
    { label: '±', latex: '\\pm' },
    { label: '×', latex: '\\times' },
    { label: '÷', latex: '\\div' },
    { label: 'α', latex: '\\alpha' },
    { label: 'β', latex: '\\beta' },
    { label: 'θ', latex: '\\theta' },
    { label: 'Δ', latex: '\\Delta' },
  ];

  // Formül ekleme
  const insertTemplate = (latex: string) => {
    setLatexInput(latexInput + latex);
  };

  // Formül kaydetme
  const saveFormula = () => {
    if (latexInput.trim() && !savedFormulas.includes(latexInput)) {
      setSavedFormulas([latexInput, ...savedFormulas]);
      // LocalStorage'a kaydet
      localStorage.setItem('savedFormulas', JSON.stringify([latexInput, ...savedFormulas]));
    }
  };

  // Kaydedilmiş formülü yükle
  const loadFormula = (formula: string) => {
    setLatexInput(formula);
    setShowLibrary(false);
  };

  // Formülü sil
  const deleteFormula = (formula: string) => {
    const updated = savedFormulas.filter(f => f !== formula);
    setSavedFormulas(updated);
    localStorage.setItem('savedFormulas', JSON.stringify(updated));
  };

  // LocalStorage'dan yükle
  useEffect(() => {
    const saved = localStorage.getItem('savedFormulas');
    if (saved) {
      try {
        setSavedFormulas(JSON.parse(saved));
      } catch (error) {
        console.error('Error loading saved formulas:', error);
      }
    }
  }, []);

  // Filtrelenmiş şablonlar
  const filteredTemplates = selectedCategory === 'all'
    ? templates
    : templates.filter(t => t.category === selectedCategory);

  return (
    <div className="formula-editor" role="application" aria-label="Formül Editörü">
      <div className="editor-header">
        <h2>Formül Editörü</h2>
        <button
          onClick={() => setShowLibrary(!showLibrary)}
          className="library-toggle"
          aria-label="Formül kütüphanesini göster/gizle"
        >
          📚 {showLibrary ? 'Kütüphaneyi Gizle' : 'Kütüphane'}
        </button>
      </div>

      <div className="editor-body">
        {/* LaTeX girişi */}
        <div className="latex-input-section">
          <label htmlFor="latex-input">LaTeX Kodu:</label>
          <textarea
            id="latex-input"
            value={latexInput}
            onChange={(e) => setLatexInput(e.target.value)}
            placeholder="Formülünüzü LaTeX formatında yazın... Örnek: \frac{a}{b}"
            rows={4}
            aria-label="LaTeX formül girişi"
          />
          <div className="input-actions">
            <button onClick={() => setLatexInput('')} aria-label="Temizle">
              🗑️ Temizle
            </button>
            <button onClick={saveFormula} className="save-btn" aria-label="Kaydet">
              💾 Kaydet
            </button>
          </div>
        </div>

        {/* Hızlı ekleme butonları */}
        <div className="quick-insert-section">
          <h3>Hızlı Ekle</h3>
          <div className="quick-buttons">
            {quickInserts.map((item, index) => (
              <button
                key={index}
                onClick={() => insertTemplate(item.latex)}
                className="quick-btn"
                aria-label={`${item.label} ekle`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {/* Önizleme */}
        <div className="preview-section">
          <h3>Önizleme</h3>
          <div className="formula-preview" aria-live="polite">
            {latexInput ? (
              <div className="latex-display">
                {/* Not: Gerçek uygulamada MathJax veya KaTeX kullanılmalı */}
                <code>{latexInput}</code>
                <p className="preview-note">
                  💡 Gerçek önizleme için MathJax/KaTeX entegrasyonu gereklidir
                </p>
              </div>
            ) : (
              <p className="empty-preview">Formül girişi bekleniyor...</p>
            )}
          </div>
        </div>

        {/* Formül kütüphanesi */}
        {showLibrary && (
          <div className="formula-library" role="region" aria-label="Formül kütüphanesi">
            <div className="library-header">
              <h3>Formül Kütüphanesi</h3>
              <div className="category-filter">
                <label htmlFor="category-select">Kategori:</label>
                <select
                  id="category-select"
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  aria-label="Kategori filtresi"
                >
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Şablonlar */}
            <div className="templates-grid">
              {filteredTemplates.map((template, index) => (
                <div key={index} className="template-card">
                  <div className="template-header">
                    <h4>{template.name}</h4>
                    <span className="template-category">{categories.find(c => c.id === template.category)?.name}</span>
                  </div>
                  <div className="template-formula">
                    <code>{template.latex}</code>
                  </div>
                  <p className="template-description">{template.description}</p>
                  <button
                    onClick={() => insertTemplate(template.latex)}
                    className="use-template-btn"
                    aria-label={`${template.name} şablonunu kullan`}
                  >
                    ➕ Kullan
                  </button>
                </div>
              ))}
            </div>

            {/* Kaydedilmiş formüller */}
            {savedFormulas.length > 0 && (
              <div className="saved-formulas">
                <h3>Kaydedilmiş Formüller</h3>
                <div className="saved-list">
                  {savedFormulas.map((formula, index) => (
                    <div key={index} className="saved-item">
                      <code>{formula}</code>
                      <div className="saved-actions">
                        <button
                          onClick={() => loadFormula(formula)}
                          aria-label="Formülü yükle"
                        >
                          📥 Yükle
                        </button>
                        <button
                          onClick={() => deleteFormula(formula)}
                          className="delete-btn"
                          aria-label="Formülü sil"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* LaTeX yardımı */}
        <div className="latex-help">
          <details>
            <summary>📖 LaTeX Komutları Rehberi</summary>
            <div className="help-content">
              <div className="help-section">
                <h4>Temel Komutlar</h4>
                <ul>
                  <li><code>\frac{'{a}'}{'{b}'}</code> - Kesir</li>
                  <li><code>x^{'{n}'}</code> - Üs</li>
                  <li><code>x_{'{n}'}</code> - Alt simge</li>
                  <li><code>\sqrt{'{x}'}</code> - Karekök</li>
                  <li><code>\sqrt[n]{'{x}'}</code> - n. kök</li>
                </ul>
              </div>
              <div className="help-section">
                <h4>Yunan Harfleri</h4>
                <ul>
                  <li><code>\alpha, \beta, \gamma, \delta</code></li>
                  <li><code>\theta, \lambda, \mu, \pi</code></li>
                  <li><code>\sigma, \phi, \omega</code></li>
                </ul>
              </div>
              <div className="help-section">
                <h4>Operatörler</h4>
                <ul>
                  <li><code>\sum_{'{i=1}'}^{'{n}'}</code> - Toplam</li>
                  <li><code>\int_{'{a}'}^{'{b}'}</code> - İntegral</li>
                  <li><code>\lim_{'{x \to a}'}</code> - Limit</li>
                  <li><code>\frac{'{d}'}{'{dx}'}</code> - Türev</li>
                </ul>
              </div>
              <div className="help-section">
                <h4>İlişkiler</h4>
                <ul>
                  <li><code>\leq, \geq</code> - Küçük/büyük eşit</li>
                  <li><code>\neq</code> - Eşit değil</li>
                  <li><code>\approx</code> - Yaklaşık eşit</li>
                  <li><code>\pm, \mp</code> - Artı/eksi</li>
                </ul>
              </div>
            </div>
          </details>
        </div>
      </div>
    </div>
  );
};

export default FormulaEditor;
