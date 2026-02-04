/**
 * Task 103: Department Information Component
 *
 * Displays curriculum, career opportunities, salary expectations, and sector analysis
 */

import React, { useState, useEffect } from 'react';
import './DepartmentInfo.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// ============================================================
// Types
// ============================================================

interface Curriculum {
  total_credits: number;
  duration_years: number;
  specializations: string[];
  internship_required: boolean;
  skills_gained: string[];
}

interface CareerOpportunity {
  job_title: string;
  industry: string | null;
  demand_level: string;
  employment_rate: number | null;
  career_growth: string;
}

interface SalaryProgression {
  [level: string]: {
    average: number;
    min: number;
    max: number;
    count: number;
  };
}

interface RegionalSalary {
  city: string;
  average_salary: number;
  min_salary: number;
  max_salary: number;
  data_points: number;
}

interface Sector {
  name: string;
  growth_rate: number;
  future_demand: string;
  automation_risk: string;
}

interface JobMarketTrends {
  overall_growth: string;
  annual_growth_rate: number;
  total_job_openings: number;
  sectors_analyzed: number;
  top_skills: string[];
  employment_rate: number;
  sectors: any[];
}

interface Statistics {
  employment_rate: number | null;
  avg_hiring_time: number | null;
  entry_salary: number | null;
  salary_growth_rate: number | null;
}

interface ComprehensiveInfo {
  curriculum: Curriculum;
  career_opportunities: CareerOpportunity[];
  salary_progression: SalaryProgression;
  regional_salaries: RegionalSalary[];
  sectors: Sector[];
  job_market_trends: JobMarketTrends;
  statistics: Statistics;
}

interface DepartmentInfoProps {
  departmentId: string;
  year?: number;
}

// ============================================================
// Component
// ============================================================

export const DepartmentInfo: React.FC<DepartmentInfoProps> = ({
  departmentId,
  year = 2024
}) => {
  const [info, setInfo] = useState<ComprehensiveInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'curriculum' | 'careers' | 'salaries' | 'sectors'>('curriculum');

  useEffect(() => {
    fetchDepartmentInfo();
  }, [departmentId, year]);

  const fetchDepartmentInfo = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/department-info/comprehensive/${departmentId}?year=${year}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch department information');
      }

      const data = await response.json();
      setInfo(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="department-info loading">
        <div className="spinner"></div>
        <p>Loading department information...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="department-info error">
        <p className="error-message">Error: {error}</p>
        <button onClick={fetchDepartmentInfo} className="btn-retry">
          Retry
        </button>
      </div>
    );
  }

  if (!info) {
    return null;
  }

  return (
    <div className="department-info">
      <div className="info-header">
        <h2>Department Information</h2>
        <div className="quick-stats">
          {info.statistics.employment_rate && (
            <div className="stat-card">
              <span className="stat-label">Employment Rate</span>
              <span className="stat-value">{info.statistics.employment_rate.toFixed(1)}%</span>
            </div>
          )}
          {info.statistics.entry_salary && (
            <div className="stat-card">
              <span className="stat-label">Entry Salary</span>
              <span className="stat-value">{formatSalary(info.statistics.entry_salary)}</span>
            </div>
          )}
          {info.statistics.salary_growth_rate && (
            <div className="stat-card">
              <span className="stat-label">Salary Growth</span>
              <span className="stat-value">{info.statistics.salary_growth_rate.toFixed(1)}%/year</span>
            </div>
          )}
        </div>
      </div>

      <div className="info-tabs">
        <button
          className={`tab ${activeTab === 'curriculum' ? 'active' : ''}`}
          onClick={() => setActiveTab('curriculum')}
        >
          Curriculum
        </button>
        <button
          className={`tab ${activeTab === 'careers' ? 'active' : ''}`}
          onClick={() => setActiveTab('careers')}
        >
          Careers
        </button>
        <button
          className={`tab ${activeTab === 'salaries' ? 'active' : ''}`}
          onClick={() => setActiveTab('salaries')}
        >
          Salaries
        </button>
        <button
          className={`tab ${activeTab === 'sectors' ? 'active' : ''}`}
          onClick={() => setActiveTab('sectors')}
        >
          Job Market
        </button>
      </div>

      <div className="info-content">
        {activeTab === 'curriculum' && (
          <CurriculumTab curriculum={info.curriculum} />
        )}
        {activeTab === 'careers' && (
          <CareersTab
            careers={info.career_opportunities}
            employmentRate={info.statistics.employment_rate}
            hiringTime={info.statistics.avg_hiring_time}
          />
        )}
        {activeTab === 'salaries' && (
          <SalariesTab
            progression={info.salary_progression}
            regional={info.regional_salaries}
          />
        )}
        {activeTab === 'sectors' && (
          <SectorsTab
            sectors={info.sectors}
            trends={info.job_market_trends}
          />
        )}
      </div>
    </div>
  );
};

// ============================================================
// Tab Components
// ============================================================

const CurriculumTab: React.FC<{ curriculum: Curriculum }> = ({ curriculum }) => {
  return (
    <div className="curriculum-tab">
      <div className="curriculum-overview">
        <div className="overview-item">
          <span className="label">Duration</span>
          <span className="value">{curriculum.duration_years} years</span>
        </div>
        <div className="overview-item">
          <span className="label">Total Credits</span>
          <span className="value">{curriculum.total_credits}</span>
        </div>
        <div className="overview-item">
          <span className="label">Internship</span>
          <span className="value">{curriculum.internship_required ? 'Required' : 'Optional'}</span>
        </div>
      </div>

      {curriculum.specializations && curriculum.specializations.length > 0 && (
        <div className="specializations">
          <h3>Specialization Tracks</h3>
          <div className="specialization-list">
            {curriculum.specializations.map((spec, idx) => (
              <div key={idx} className="specialization-badge">
                {spec}
              </div>
            ))}
          </div>
        </div>
      )}

      {curriculum.skills_gained && curriculum.skills_gained.length > 0 && (
        <div className="skills-section">
          <h3>Skills You'll Gain</h3>
          <div className="skills-list">
            {curriculum.skills_gained.map((skill, idx) => (
              <div key={idx} className="skill-tag">
                {skill}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const CareersTab: React.FC<{
  careers: CareerOpportunity[];
  employmentRate: number | null;
  hiringTime: number | null;
}> = ({ careers, employmentRate, hiringTime }) => {
  return (
    <div className="careers-tab">
      <div className="employment-stats">
        {employmentRate && (
          <div className="stat-box">
            <span className="stat-title">Employment Rate</span>
            <span className="stat-number">{employmentRate.toFixed(1)}%</span>
          </div>
        )}
        {hiringTime && (
          <div className="stat-box">
            <span className="stat-title">Avg. Hiring Time</span>
            <span className="stat-number">{hiringTime} days</span>
          </div>
        )}
        <div className="stat-box">
          <span className="stat-title">Career Paths</span>
          <span className="stat-number">{careers.length}</span>
        </div>
      </div>

      <div className="careers-list">
        {careers.map((career, idx) => (
          <div key={idx} className="career-card">
            <div className="career-header">
              <h4>{career.job_title}</h4>
              {career.demand_level && (
                <span className={`demand-badge ${career.demand_level}`}>
                  {career.demand_level.toUpperCase()} DEMAND
                </span>
              )}
            </div>
            {career.industry && (
              <div className="career-industry">{career.industry}</div>
            )}
            <div className="career-stats">
              {career.employment_rate && (
                <div className="career-stat">
                  <span className="label">Employment Rate:</span>
                  <span className="value">{career.employment_rate.toFixed(1)}%</span>
                </div>
              )}
              {career.career_growth && (
                <div className="career-stat">
                  <span className="label">Growth Potential:</span>
                  <span className="value capitalize">{career.career_growth}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {careers.length === 0 && (
        <div className="empty-state">
          <p>No career information available yet.</p>
        </div>
      )}
    </div>
  );
};

const SalariesTab: React.FC<{
  progression: SalaryProgression;
  regional: RegionalSalary[];
}> = ({ progression, regional }) => {
  return (
    <div className="salaries-tab">
      <div className="salary-progression">
        <h3>Salary Progression by Experience</h3>
        <div className="progression-chart">
          {Object.entries(progression).map(([level, data]) => (
            <div key={level} className="progression-item">
              <div className="level-name">{formatExperienceLevel(level)}</div>
              <div className="salary-bar">
                <div className="salary-range">
                  <span className="min">{formatSalary(data.min)}</span>
                  <span className="avg">{formatSalary(data.average)}</span>
                  <span className="max">{formatSalary(data.max)}</span>
                </div>
                <div
                  className="bar-fill"
                  style={{ width: `${(data.average / Math.max(...Object.values(progression).map(d => d.max))) * 100}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {regional && regional.length > 0 && (
        <div className="regional-salaries">
          <h3>Regional Salary Comparison</h3>
          <div className="regional-list">
            {regional.slice(0, 10).map((region, idx) => (
              <div key={idx} className="regional-item">
                <div className="city-name">{region.city}</div>
                <div className="city-salary">
                  <span className="avg-salary">{formatSalary(region.average_salary)}</span>
                  <span className="salary-range-text">
                    {formatSalary(region.min_salary)} - {formatSalary(region.max_salary)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const SectorsTab: React.FC<{
  sectors: Sector[];
  trends: JobMarketTrends;
}> = ({ sectors, trends }) => {
  return (
    <div className="sectors-tab">
      <div className="market-overview">
        <h3>Job Market Overview</h3>
        <div className="market-stats">
          <div className="market-stat">
            <span className="label">Overall Growth</span>
            <span className={`value growth-${trends.overall_growth}`}>
              {trends.overall_growth.toUpperCase()}
            </span>
          </div>
          <div className="market-stat">
            <span className="label">Annual Growth Rate</span>
            <span className="value">{trends.annual_growth_rate.toFixed(1)}%</span>
          </div>
          <div className="market-stat">
            <span className="label">Job Openings</span>
            <span className="value">{trends.total_job_openings.toLocaleString()}</span>
          </div>
          <div className="market-stat">
            <span className="label">Employment Rate</span>
            <span className="value">{trends.employment_rate.toFixed(1)}%</span>
          </div>
        </div>
      </div>

      {trends.top_skills && trends.top_skills.length > 0 && (
        <div className="top-skills">
          <h3>In-Demand Skills</h3>
          <div className="skills-grid">
            {trends.top_skills.map((skill, idx) => (
              <div key={idx} className="skill-badge">
                {skill}
              </div>
            ))}
          </div>
        </div>
      )}

      {sectors && sectors.length > 0 && (
        <div className="sectors-list">
          <h3>Related Sectors</h3>
          {sectors.map((sector, idx) => (
            <div key={idx} className="sector-card">
              <div className="sector-header">
                <h4>{sector.name}</h4>
                <span className={`demand-indicator ${sector.future_demand}`}>
                  {sector.future_demand}
                </span>
              </div>
              <div className="sector-metrics">
                <div className="metric">
                  <span className="metric-label">Growth Rate:</span>
                  <span className="metric-value">{sector.growth_rate.toFixed(1)}%</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Automation Risk:</span>
                  <span className={`metric-value risk-${sector.automation_risk}`}>
                    {sector.automation_risk}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ============================================================
// Utility Functions
// ============================================================

function formatSalary(amount: number): string {
  if (amount >= 1000) {
    return `₺${(amount / 1000).toFixed(0)}K`;
  }
  return `₺${amount}`;
}

function formatExperienceLevel(level: string): string {
  const levels: { [key: string]: string } = {
    entry: 'Entry Level',
    junior: 'Junior',
    mid: 'Mid-Level',
    senior: 'Senior',
    expert: 'Expert'
  };
  return levels[level] || level;
}

export type { DepartmentInfoProps, ComprehensiveInfo };
