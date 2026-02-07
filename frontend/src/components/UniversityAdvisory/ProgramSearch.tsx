/**
 * Task 101: University Program Search
 *
 * Search programs with base scores, quotas, and filters
 */

import * as React from 'react';
import {  useState, useEffect  } from 'react';
import './ProgramSearch.css';

export interface Program {
  id: string;
  programName: string;
  universityName: string;
  departmentName: string;
  city: string;
  year: number;
  scoreType: string;
  baseScore: number;
  topScore: number;
  medianScore: number;
  totalQuota: number;
  filledQuota: number;
  acceptanceRate: number;
  scholarship: boolean;
  tuitionFee: number | null;
}

export interface ProgramSearchProps {
  onSelectProgram?: (program: Program) => void;
}

const API_BASE = '/api/university-advisory';

export const ProgramSearch: React.FC<ProgramSearchProps> = ({
  onSelectProgram,
}) => {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(false);

  // Filters
  const [year, setYear] = useState(2024);
  const [scoreType, setScoreType] = useState<string>('SAY');
  const [minScore, setMinScore] = useState<number | string>('');
  const [maxScore, setMaxScore] = useState<number | string>('');
  const [city, setCity] = useState<string>('');
  const [universityType, setUniversityType] = useState<string>('');
  const [departmentName, setDepartmentName] = useState<string>('');
  const [hasScholarship, setHasScholarship] = useState<boolean | null>(null);

  // Cities list
  const [cities, setCities] = useState<string[]>([]);

  useEffect(() => {
    loadCities();
    handleSearch(); // Initial search
  }, []);

  const loadCities = async () => {
    try {
      const response = await fetch(`${API_BASE}/cities`);
      const data = await response.json();
      setCities(data);
    } catch (error) {
      console.error('Failed to load cities:', error);
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('year', year.toString());
      if (scoreType) {params.append('score_type', scoreType);}
      if (minScore) {params.append('min_score', minScore.toString());}
      if (maxScore) {params.append('max_score', maxScore.toString());}
      if (city) {params.append('city', city);}
      if (universityType) {params.append('university_type', universityType);}
      if (departmentName) {params.append('department_name', departmentName);}
      if (hasScholarship !== null) {params.append('has_scholarship', hasScholarship.toString());}
      params.append('limit', '100');

      const response = await fetch(`${API_BASE}/programs?${params}`);
      const data = await response.json();

      setPrograms(data.map((p: any) => ({
        id: p.id,
        programName: p.program_name,
        universityName: p.university_name,
        departmentName: p.department_name,
        city: p.city,
        year: p.year,
        scoreType: p.score_type,
        baseScore: p.base_score,
        topScore: p.top_score,
        medianScore: p.median_score,
        totalQuota: p.total_quota,
        filledQuota: p.filled_quota,
        acceptanceRate: p.acceptance_rate,
        scholarship: p.scholarship,
        tuitionFee: p.tuition_fee,
      })));
    } catch (error) {
      console.error('Failed to search programs:', error);
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = () => {
    setMinScore('');
    setMaxScore('');
    setCity('');
    setUniversityType('');
    setDepartmentName('');
    setHasScholarship(null);
  };

  return (
    <div className="program-search">
      <div className="search-header">
        <h2>Üniversite Programları Arama</h2>
      </div>

      <div className="search-filters">
        <div className="filter-row">
          <div className="filter-group">
            <label htmlFor="year">Yıl</label>
            <select
              id="year"
              value={year}
              onChange={(e) => setYear(parseInt(e.target.value))}
            >
              <option value="2024">2024</option>
              <option value="2023">2023</option>
              <option value="2022">2022</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="scoreType">Puan Türü</label>
            <select
              id="scoreType"
              value={scoreType}
              onChange={(e) => setScoreType(e.target.value)}
            >
              <option value="SAY">SAY (Sayısal)</option>
              <option value="EA">EA (Eşit Ağırlık)</option>
              <option value="SOZ">SÖZ (Sözel)</option>
              <option value="DIL">DİL (Dil)</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="minScore">Min. Taban Puan</label>
            <input
              id="minScore"
              type="number"
              placeholder="Örn: 300"
              value={minScore}
              onChange={(e) => setMinScore(e.target.value)}
              step="0.01"
            />
          </div>

          <div className="filter-group">
            <label htmlFor="maxScore">Max. Taban Puan</label>
            <input
              id="maxScore"
              type="number"
              placeholder="Örn: 500"
              value={maxScore}
              onChange={(e) => setMaxScore(e.target.value)}
              step="0.01"
            />
          </div>
        </div>

        <div className="filter-row">
          <div className="filter-group">
            <label htmlFor="city">Şehir</label>
            <select
              id="city"
              value={city}
              onChange={(e) => setCity(e.target.value)}
            >
              <option value="">Tümü</option>
              {cities.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="universityType">Üniversite Türü</label>
            <select
              id="universityType"
              value={universityType}
              onChange={(e) => setUniversityType(e.target.value)}
            >
              <option value="">Tümü</option>
              <option value="devlet">Devlet</option>
              <option value="vakif">Vakıf</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="departmentName">Bölüm Adı</label>
            <input
              id="departmentName"
              type="text"
              placeholder="Örn: Bilgisayar"
              value={departmentName}
              onChange={(e) => setDepartmentName(e.target.value)}
            />
          </div>

          <div className="filter-group">
            <label htmlFor="scholarship">Burs</label>
            <select
              id="scholarship"
              value={hasScholarship === null ? '' : hasScholarship.toString()}
              onChange={(e) => setHasScholarship(e.target.value === '' ? null : e.target.value === 'true')}
            >
              <option value="">Tümü</option>
              <option value="true">Burslu</option>
              <option value="false">Burssuz</option>
            </select>
          </div>
        </div>

        <div className="filter-actions">
          <button
            className="btn-primary"
            onClick={handleSearch}
            disabled={loading}
          >
            {loading ? 'Aranıyor...' : 'Ara'}
          </button>
          <button
            className="btn-secondary"
            onClick={clearFilters}
          >
            Filtreleri Temizle
          </button>
        </div>
      </div>

      <div className="search-results">
        <div className="results-header">
          <h3>{programs.length} Program Bulundu</h3>
        </div>

        {loading ? (
          <div className="loading">Programlar yükleniyor...</div>
        ) : programs.length === 0 ? (
          <div className="empty-state">
            Filtrelere uygun program bulunamadı
          </div>
        ) : (
          <div className="programs-list">
            {programs.map((program) => (
              <div
                key={program.id}
                className="program-card"
                onClick={() => onSelectProgram?.(program)}
              >
                <div className="program-header">
                  <h4>{program.programName}</h4>
                  {program.scholarship && (
                    <span className="scholarship-badge">Burslu</span>
                  )}
                </div>

                <div className="program-university">
                  {program.universityName} - {program.city}
                </div>

                <div className="program-scores">
                  <div className="score-item">
                    <span className="score-label">Taban Puan:</span>
                    <span className="score-value">{program.baseScore?.toFixed(2) || 'N/A'}</span>
                  </div>
                  <div className="score-item">
                    <span className="score-label">Tavan Puan:</span>
                    <span className="score-value">{program.topScore?.toFixed(2) || 'N/A'}</span>
                  </div>
                  <div className="score-item">
                    <span className="score-label">Ortalama:</span>
                    <span className="score-value">{program.medianScore?.toFixed(2) || 'N/A'}</span>
                  </div>
                </div>

                <div className="program-quota">
                  <div className="quota-item">
                    <span className="quota-label">Kontenjan:</span>
                    <span className="quota-value">{program.totalQuota || 'N/A'}</span>
                  </div>
                  <div className="quota-item">
                    <span className="quota-label">Yerleşen:</span>
                    <span className="quota-value">{program.filledQuota || 'N/A'}</span>
                  </div>
                  {program.acceptanceRate && (
                    <div className="quota-item">
                      <span className="quota-label">Yerleşme:</span>
                      <span className="quota-value">{program.acceptanceRate.toFixed(1)}%</span>
                    </div>
                  )}
                </div>

                {program.tuitionFee && (
                  <div className="program-fee">
                    Öğrenim Ücreti: {program.tuitionFee.toLocaleString('tr-TR')} TL/yıl
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgramSearch;
