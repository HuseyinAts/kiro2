/**
 * Task 104: University Information Component
 *
 * Displays campus info, living costs, dormitories, and scholarships
 */

import React, { useState, useEffect } from 'react';
import './UniversityInfo.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// ============================================================
// Types
// ============================================================

interface Campus {
  id: string;
  name: string;
  type: string;
  city: string;
  total_area_sqm: number;
  student_clubs: number;
  has_health_center: boolean;
  has_career_center: boolean;
  wifi_available: boolean;
  shuttle_service: boolean;
}

interface LivingCost {
  city: string;
  avg_monthly_budget: number;
  avg_rent: number;
  food_budget: number;
  transport_monthly: number;
  cost_of_living_index: number;
}

interface Dormitory {
  id: string;
  name: string;
  type: string;
  price_avg: number;
  total_capacity: number;
  meals_included: boolean;
  distance_to_campus_km: number;
}

interface Scholarship {
  id: string;
  name: string;
  type: string;
  coverage_percentage: number;
  amount_avg: number;
  covers_tuition: boolean;
  covers_accommodation: boolean;
}

interface Statistics {
  total_campuses: number;
  total_student_clubs: number;
  avg_monthly_cost: number;
  total_dormitory_capacity: number;
  total_scholarships: number;
  affordability_score: number;
}

interface ComprehensiveInfo {
  campuses: Campus[];
  living_cost: LivingCost | null;
  dormitories: Dormitory[];
  dormitory_statistics: any;
  scholarships: Scholarship[];
  scholarship_statistics: any;
  statistics: Statistics | null;
}

interface UniversityInfoProps {
  universityId: string;
  year?: number;
}

// ============================================================
// Component
// ============================================================

export const UniversityInfo: React.FC<UniversityInfoProps> = ({
  universityId,
  year = 2024
}) => {
  const [info, setInfo] = useState<ComprehensiveInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'campus' | 'living' | 'dormitory' | 'scholarship'>('campus');

  useEffect(() => {
    fetchUniversityInfo();
  }, [universityId, year]);

  const fetchUniversityInfo = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/university-info/comprehensive/${universityId}?year=${year}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch university information');
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
      <div className="university-info loading">
        <div className="spinner"></div>
        <p>Loading university information...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="university-info error">
        <p className="error-message">Error: {error}</p>
        <button onClick={fetchUniversityInfo} className="btn-retry">
          Retry
        </button>
      </div>
    );
  }

  if (!info) {
    return null;
  }

  return (
    <div className="university-info">
      <div className="info-header">
        <h2>University Information</h2>
        {info.statistics && (
          <div className="quick-stats">
            <div className="stat-card">
              <span className="stat-label">Campuses</span>
              <span className="stat-value">{info.statistics.total_campuses}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Student Clubs</span>
              <span className="stat-value">{info.statistics.total_student_clubs}</span>
            </div>
            {info.statistics.avg_monthly_cost && (
              <div className="stat-card">
                <span className="stat-label">Avg. Monthly Cost</span>
                <span className="stat-value">₺{formatNumber(info.statistics.avg_monthly_cost)}</span>
              </div>
            )}
            {info.statistics.affordability_score && (
              <div className="stat-card">
                <span className="stat-label">Affordability Score</span>
                <span className="stat-value">{info.statistics.affordability_score.toFixed(1)}/10</span>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="info-tabs">
        <button
          className={`tab ${activeTab === 'campus' ? 'active' : ''}`}
          onClick={() => setActiveTab('campus')}
        >
          Campus
        </button>
        <button
          className={`tab ${activeTab === 'living' ? 'active' : ''}`}
          onClick={() => setActiveTab('living')}
        >
          Living Costs
        </button>
        <button
          className={`tab ${activeTab === 'dormitory' ? 'active' : ''}`}
          onClick={() => setActiveTab('dormitory')}
        >
          Dormitories
        </button>
        <button
          className={`tab ${activeTab === 'scholarship' ? 'active' : ''}`}
          onClick={() => setActiveTab('scholarship')}
        >
          Scholarships
        </button>
      </div>

      <div className="info-content">
        {activeTab === 'campus' && (
          <CampusTab campuses={info.campuses} />
        )}
        {activeTab === 'living' && (
          <LivingCostTab livingCost={info.living_cost} />
        )}
        {activeTab === 'dormitory' && (
          <DormitoryTab
            dormitories={info.dormitories}
            statistics={info.dormitory_statistics}
          />
        )}
        {activeTab === 'scholarship' && (
          <ScholarshipTab
            scholarships={info.scholarships}
            statistics={info.scholarship_statistics}
          />
        )}
      </div>
    </div>
  );
};

// ============================================================
// Tab Components
// ============================================================

const CampusTab: React.FC<{ campuses: Campus[] }> = ({ campuses }) => {
  if (campuses.length === 0) {
    return <div className="empty-state">No campus information available.</div>;
  }

  return (
    <div className="campus-tab">
      <div className="campus-list">
        {campuses.map((campus) => (
          <div key={campus.id} className="campus-card">
            <div className="campus-header">
              <h3>{campus.name}</h3>
              <span className="campus-type">{formatCampusType(campus.type)}</span>
            </div>
            <div className="campus-location">
              📍 {campus.city}
            </div>
            {campus.total_area_sqm && (
              <div className="campus-area">
                Area: {formatNumber(campus.total_area_sqm)} m²
              </div>
            )}
            <div className="campus-features">
              {campus.student_clubs > 0 && (
                <div className="feature">
                  <span className="feature-icon">🎯</span>
                  <span>{campus.student_clubs} Student Clubs</span>
                </div>
              )}
              {campus.has_health_center && (
                <div className="feature">
                  <span className="feature-icon">🏥</span>
                  <span>Health Center</span>
                </div>
              )}
              {campus.has_career_center && (
                <div className="feature">
                  <span className="feature-icon">💼</span>
                  <span>Career Center</span>
                </div>
              )}
              {campus.wifi_available && (
                <div className="feature">
                  <span className="feature-icon">📶</span>
                  <span>WiFi Available</span>
                </div>
              )}
              {campus.shuttle_service && (
                <div className="feature">
                  <span className="feature-icon">🚌</span>
                  <span>Shuttle Service</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const LivingCostTab: React.FC<{ livingCost: LivingCost | null }> = ({ livingCost }) => {
  if (!livingCost) {
    return <div className="empty-state">No living cost information available.</div>;
  }

  return (
    <div className="living-cost-tab">
      <div className="cost-overview">
        <h3>{livingCost.city} - Cost of Living</h3>
        <div className="cost-index">
          <span className="index-label">Cost of Living Index:</span>
          <span className={`index-value ${getCostIndexClass(livingCost.cost_of_living_index)}`}>
            {livingCost.cost_of_living_index.toFixed(1)}
          </span>
        </div>
      </div>

      <div className="cost-breakdown">
        <div className="cost-item">
          <div className="cost-label">
            <span className="icon">🏠</span>
            <span>Accommodation</span>
          </div>
          <div className="cost-amount">₺{formatNumber(livingCost.avg_rent)}/month</div>
        </div>

        <div className="cost-item">
          <div className="cost-label">
            <span className="icon">🍽️</span>
            <span>Food & Groceries</span>
          </div>
          <div className="cost-amount">₺{formatNumber(livingCost.food_budget)}/month</div>
        </div>

        <div className="cost-item">
          <div className="cost-label">
            <span className="icon">🚇</span>
            <span>Transportation</span>
          </div>
          <div className="cost-amount">₺{formatNumber(livingCost.transport_monthly)}/month</div>
        </div>

        <div className="cost-item total">
          <div className="cost-label">
            <span className="icon">💰</span>
            <span>Total Monthly Budget</span>
          </div>
          <div className="cost-amount">₺{formatNumber(livingCost.avg_monthly_budget)}/month</div>
        </div>

        <div className="annual-estimate">
          <strong>Annual Estimate:</strong> ₺{formatNumber(livingCost.avg_monthly_budget * 12)}
        </div>
      </div>
    </div>
  );
};

const DormitoryTab: React.FC<{
  dormitories: Dormitory[];
  statistics: any;
}> = ({ dormitories, statistics }) => {
  return (
    <div className="dormitory-tab">
      {statistics && (
        <div className="dormitory-stats">
          <div className="stat-box">
            <span className="stat-title">Total Dormitories</span>
            <span className="stat-number">{statistics.total_dormitories}</span>
          </div>
          <div className="stat-box">
            <span className="stat-title">Total Capacity</span>
            <span className="stat-number">{formatNumber(statistics.total_capacity)}</span>
          </div>
          <div className="stat-box">
            <span className="stat-title">Avg. Price</span>
            <span className="stat-number">₺{formatNumber(statistics.avg_price)}</span>
          </div>
        </div>
      )}

      <div className="dormitory-list">
        {dormitories.length === 0 ? (
          <div className="empty-state">No dormitory information available.</div>
        ) : (
          dormitories.map((dorm) => (
            <div key={dorm.id} className="dormitory-card">
              <div className="dormitory-header">
                <h4>{dorm.name}</h4>
                <span className="dormitory-type">{formatAccommodationType(dorm.type)}</span>
              </div>
              <div className="dormitory-details">
                <div className="detail-row">
                  <span className="detail-label">Price:</span>
                  <span className="detail-value price">₺{formatNumber(dorm.price_avg)}/month</span>
                </div>
                {dorm.total_capacity && (
                  <div className="detail-row">
                    <span className="detail-label">Capacity:</span>
                    <span className="detail-value">{dorm.total_capacity} students</span>
                  </div>
                )}
                {dorm.distance_to_campus_km !== null && (
                  <div className="detail-row">
                    <span className="detail-label">Distance to Campus:</span>
                    <span className="detail-value">{dorm.distance_to_campus_km} km</span>
                  </div>
                )}
                {dorm.meals_included && (
                  <div className="feature-badge">🍽️ Meals Included</div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

const ScholarshipTab: React.FC<{
  scholarships: Scholarship[];
  statistics: any;
}> = ({ scholarships, statistics }) => {
  return (
    <div className="scholarship-tab">
      {statistics && (
        <div className="scholarship-stats">
          <div className="stat-box">
            <span className="stat-title">Total Scholarships</span>
            <span className="stat-number">{statistics.total_scholarships}</span>
          </div>
          <div className="stat-box">
            <span className="stat-title">Full Scholarships</span>
            <span className="stat-number">{statistics.full_scholarships}</span>
          </div>
          <div className="stat-box">
            <span className="stat-title">Partial Scholarships</span>
            <span className="stat-number">{statistics.partial_scholarships}</span>
          </div>
          {statistics.avg_amount > 0 && (
            <div className="stat-box">
              <span className="stat-title">Avg. Amount</span>
              <span className="stat-number">₺{formatNumber(statistics.avg_amount)}</span>
            </div>
          )}
        </div>
      )}

      <div className="scholarship-list">
        {scholarships.length === 0 ? (
          <div className="empty-state">No scholarship information available.</div>
        ) : (
          scholarships.map((scholarship) => (
            <div key={scholarship.id} className="scholarship-card">
              <div className="scholarship-header">
                <h4>{scholarship.name}</h4>
                <span className={`coverage-badge coverage-${getCoverageClass(scholarship.coverage_percentage)}`}>
                  {scholarship.coverage_percentage}% Coverage
                </span>
              </div>
              <div className="scholarship-type">
                {formatScholarshipType(scholarship.type)}
              </div>
              <div className="scholarship-details">
                {scholarship.amount_avg > 0 && (
                  <div className="detail-row">
                    <span className="detail-label">Amount:</span>
                    <span className="detail-value">₺{formatNumber(scholarship.amount_avg)}</span>
                  </div>
                )}
                <div className="scholarship-coverage">
                  {scholarship.covers_tuition && (
                    <span className="coverage-item">✓ Tuition</span>
                  )}
                  {scholarship.covers_accommodation && (
                    <span className="coverage-item">✓ Accommodation</span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// ============================================================
// Utility Functions
// ============================================================

function formatNumber(num: number): string {
  return num.toLocaleString('tr-TR');
}

function formatCampusType(type: string): string {
  const types: { [key: string]: string } = {
    main_campus: 'Main Campus',
    satellite_campus: 'Satellite Campus',
    medical_campus: 'Medical Campus',
    research_campus: 'Research Campus'
  };
  return types[type] || type;
}

function formatAccommodationType(type: string): string {
  const types: { [key: string]: string } = {
    state_dormitory: 'State Dormitory',
    university_dormitory: 'University Dormitory',
    private_dormitory: 'Private Dormitory',
    apartment: 'Apartment',
    shared_apartment: 'Shared Apartment'
  };
  return types[type] || type;
}

function formatScholarshipType(type: string): string {
  const types: { [key: string]: string } = {
    full_scholarship: 'Full Scholarship',
    partial_scholarship: 'Partial Scholarship',
    merit_based: 'Merit-Based',
    need_based: 'Need-Based',
    sports: 'Sports Scholarship',
    academic_excellence: 'Academic Excellence',
    special_talent: 'Special Talent'
  };
  return types[type] || type;
}

function getCostIndexClass(index: number): string {
  if (index < 80) return 'low';
  if (index < 100) return 'medium';
  return 'high';
}

function getCoverageClass(percentage: number): string {
  if (percentage >= 100) return 'full';
  if (percentage >= 50) return 'high';
  return 'low';
}

export type { UniversityInfoProps, ComprehensiveInfo };
