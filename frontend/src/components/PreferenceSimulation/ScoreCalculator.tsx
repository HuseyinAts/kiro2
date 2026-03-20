/**
 * Task 102.1: YKS Score Calculator
 *
 * Calculate YKS score with coefficients and bonus points
 */

import * as React from 'react';
import {  useState  } from 'react';
import './ScoreCalculator.css';

const API_BASE = '/api/v1/preference-simulation';

export const ScoreCalculator: React.FC = () => {
  const [scoreType, setScoreType] = useState<string>('SAY');
  const [tytScores, setTytScores] = useState({
    turkish: 0,
    math: 0,
    science: 0,
    social: 0,
  });
  const [aytScores, setAytScores] = useState({
    math: 0,
    physics: 0,
    chemistry: 0,
    biology: 0,
  });
  const [diplomaGrade, setDiplomaGrade] = useState<number | ''>('');
  const [languageCert, setLanguageCert] = useState<string>('');
  const [specialTalent, setSpecialTalent] = useState(false);

  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleCalculate = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/calculate-score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          score_type: scoreType,
          tyt_scores: tytScores,
          ayt_scores: aytScores,
          diploma_grade: diplomaGrade || null,
          language_certificate: languageCert || null,
          special_talent: specialTalent,
        }),
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Failed to calculate score:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="score-calculator">
      <h2>YKS Puan Hesaplama</h2>

      <div className="calculator-form">
        <div className="form-group">
          <label>Puan Türü</label>
          <select value={scoreType} onChange={(e) => setScoreType(e.target.value)}>
            <option value="SAY">SAY (Sayısal)</option>
            <option value="EA">EA (Eşit Ağırlık)</option>
            <option value="SOZ">SÖZ (Sözel)</option>
            <option value="DIL">DİL (Dil)</option>
          </select>
        </div>

        <div className="scores-section">
          <h3>TYT Netleri</h3>
          <div className="score-grid">
            <div className="score-input">
              <label>Türkçe (40)</label>
              <input
                type="number"
                min="0"
                max="40"
                step="0.25"
                value={tytScores.turkish}
                onChange={(e) => setTytScores({ ...tytScores, turkish: parseFloat(e.target.value) || 0 })}
              />
            </div>
            <div className="score-input">
              <label>Matematik (40)</label>
              <input
                type="number"
                min="0"
                max="40"
                step="0.25"
                value={tytScores.math}
                onChange={(e) => setTytScores({ ...tytScores, math: parseFloat(e.target.value) || 0 })}
              />
            </div>
            <div className="score-input">
              <label>Fen (20)</label>
              <input
                type="number"
                min="0"
                max="20"
                step="0.25"
                value={tytScores.science}
                onChange={(e) => setTytScores({ ...tytScores, science: parseFloat(e.target.value) || 0 })}
              />
            </div>
            <div className="score-input">
              <label>Sosyal (20)</label>
              <input
                type="number"
                min="0"
                max="20"
                step="0.25"
                value={tytScores.social}
                onChange={(e) => setTytScores({ ...tytScores, social: parseFloat(e.target.value) || 0 })}
              />
            </div>
          </div>
        </div>

        <div className="scores-section">
          <h3>AYT Netleri ({scoreType})</h3>
          <div className="score-grid">
            {scoreType === 'SAY' && (
              <>
                <div className="score-input">
                  <label>Matematik (40)</label>
                  <input type="number" min="0" max="40" step="0.25"
                    value={aytScores.math}
                    onChange={(e) => setAytScores({ ...aytScores, math: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div className="score-input">
                  <label>Fizik (14)</label>
                  <input type="number" min="0" max="14" step="0.25"
                    value={aytScores.physics}
                    onChange={(e) => setAytScores({ ...aytScores, physics: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div className="score-input">
                  <label>Kimya (13)</label>
                  <input type="number" min="0" max="13" step="0.25"
                    value={aytScores.chemistry}
                    onChange={(e) => setAytScores({ ...aytScores, chemistry: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div className="score-input">
                  <label>Biyoloji (13)</label>
                  <input type="number" min="0" max="13" step="0.25"
                    value={aytScores.biology}
                    onChange={(e) => setAytScores({ ...aytScores, biology: parseFloat(e.target.value) || 0 })}
                  />
                </div>
              </>
            )}
          </div>
        </div>

        <div className="bonus-section">
          <h3>Ek Puanlar</h3>
          <div className="bonus-grid">
            <div className="form-group">
              <label>Diploma Notu (0-100)</label>
              <input
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={diplomaGrade}
                onChange={(e) => setDiplomaGrade(parseFloat(e.target.value) || '')}
              />
            </div>
            <div className="form-group">
              <label>Dil Sertifikası</label>
              <select value={languageCert} onChange={(e) => setLanguageCert(e.target.value)}>
                <option value="">Yok</option>
                <option value="TOEFL">TOEFL</option>
                <option value="IELTS">IELTS</option>
                <option value="YDS">YDS</option>
                <option value="Cambridge">Cambridge</option>
              </select>
            </div>
            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={specialTalent}
                  onChange={(e) => setSpecialTalent(e.target.checked)}
                />
                Özel Yetenek
              </label>
            </div>
          </div>
        </div>

        <button className="btn-calculate" onClick={handleCalculate} disabled={loading}>
          {loading ? 'Hesaplanıyor...' : 'Puanımı Hesapla'}
        </button>
      </div>

      {result && (
        <div className="result-panel">
          <h3>Sonuçlar</h3>
          <div className="result-summary">
            <div className="result-main">
              <div className="result-label">Toplam Puan</div>
              <div className="result-value total">{result.total_score}</div>
            </div>
            <div className="result-breakdown">
              <div className="result-item">
                <span>TYT Puanı:</span>
                <strong>{result.tyt_score}</strong>
              </div>
              <div className="result-item">
                <span>AYT Puanı:</span>
                <strong>{result.ayt_score}</strong>
              </div>
              <div className="result-item">
                <span>Temel Puan:</span>
                <strong>{result.base_score}</strong>
              </div>
              <div className="result-item">
                <span>Ek Puan:</span>
                <strong>{result.bonus_points}</strong>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScoreCalculator;
