/**
 * Task 107: Teacher Pool Component
 *
 * Main component for teacher search, profiles, booking, and management
 */

import * as React from 'react';
import {  useState, useEffect  } from 'react';
import './TeacherPool.css';
import { config } from '../../config';

const API_BASE = config.api.baseURL;

// ============================================================
// Types
// ============================================================

type SubjectExpertise = 'mathematics' | 'physics' | 'chemistry' | 'biology' | 'turkish' | 'history' | 'geography' | 'english' | 'philosophy' | 'literature' | 'geometry';
type AppointmentType = 'one_on_one' | 'group_session' | 'question_answer' | 'exam_prep';
type AppointmentStatus = 'pending' | 'confirmed' | 'cancelled' | 'completed' | 'no_show';

interface TeacherExpertise {
  id: string;
  subject: SubjectExpertise;
  grade_levels: string[];
  proficiency_level: string;
  years_teaching_subject: number;
  specializations: string[];
  exam_types: string[];
  is_verified: boolean;
}

interface TeacherCertification {
  id: string;
  certification_type: string;
  title: string;
  issuing_organization: string;
  issue_date: string;
  verification_status: string;
}

interface Teacher {
  id: string;
  user_id: string;
  full_name: string;
  title: string;
  bio: string;
  profile_photo_url?: string;
  city: string;
  district: string;
  years_of_experience: number;
  education_level: string;
  university: string;
  department: string;
  average_rating: number;
  total_reviews: number;
  total_sessions: number;
  hourly_rate: number;
  currency: string;
  is_accepting_students: boolean;
  online_teaching: boolean;
  in_person_teaching: boolean;
  expertise: TeacherExpertise[];
  certifications: TeacherCertification[];
}

interface AvailabilitySlot {
  id: string;
  day_of_week: string;
  start_time: string;
  end_time: string;
  specific_date?: string;
  is_recurring: boolean;
  status: string;
  max_students: number;
  current_bookings: number;
}

interface Appointment {
  id: string;
  teacher_id: string;
  scheduled_date: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  appointment_type: AppointmentType;
  subject: SubjectExpertise;
  topic: string;
  status: AppointmentStatus;
  price: number;
  meeting_url?: string;
}

interface TeacherPoolProps {
  userId: string;
  viewMode?: 'search' | 'profile' | 'appointments';
}

// ============================================================
// Component
// ============================================================

export const TeacherPool: React.FC<TeacherPoolProps> = ({
  userId,
  viewMode: initialViewMode = 'search',
}) => {
  const [viewMode, setViewMode] = useState<'search' | 'profile' | 'appointments' | 'booking'>(initialViewMode);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [selectedTeacher, setSelectedTeacher] = useState<Teacher | null>(null);
  const [_availability, setAvailability] = useState<AvailabilitySlot[]>([]);
  const [myAppointments, setMyAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Search filters
  const [searchFilters, setSearchFilters] = useState({
    subject: '' as SubjectExpertise | '',
    city: '',
    minRating: 0,
    maxHourlyRate: 0,
    onlineOnly: false,
  });

  // Booking form
  const [bookingForm, setBookingForm] = useState({
    selectedDate: '',
    selectedTime: '',
    appointmentType: 'one_on_one' as AppointmentType,
    subject: 'mathematics' as SubjectExpertise,
    topic: '',
    description: '',
  });

  useEffect(() => {
    if (viewMode === 'search') {
      searchTeachers();
    } else if (viewMode === 'appointments') {
      fetchMyAppointments();
    }
  }, [viewMode]);

  const searchTeachers = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (searchFilters.subject) {params.append('subject', searchFilters.subject);}
      if (searchFilters.city) {params.append('city', searchFilters.city);}
      if (searchFilters.minRating > 0) {params.append('min_rating', searchFilters.minRating.toString());}
      if (searchFilters.maxHourlyRate > 0) {params.append('max_hourly_rate', searchFilters.maxHourlyRate.toString());}
      if (searchFilters.onlineOnly) {params.append('online_only', 'true');}

      const response = await fetch(`${API_BASE}/api/v1/teachers/search?${params.toString()}`);
      if (!response.ok) {throw new Error('Failed to search teachers');}

      const data = await response.json();
      setTeachers(data.teachers);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search teachers');
    } finally {
      setLoading(false);
    }
  };

  const fetchTeacherProfile = async (teacherId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/v1/teachers/profile/${teacherId}`);
      if (!response.ok) {throw new Error('Failed to fetch teacher profile');}

      const teacher = await response.json();
      setSelectedTeacher(teacher);

      // Fetch availability
      const availResponse = await fetch(`${API_BASE}/api/v1/teachers/${teacherId}/availability`);
      if (availResponse.ok) {
        const availData = await availResponse.json();
        setAvailability(availData.availability);
      }

      setViewMode('profile');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load teacher');
    } finally {
      setLoading(false);
    }
  };

  const fetchMyAppointments = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/v1/teachers/my-appointments?student_id=${userId}`);
      if (!response.ok) {throw new Error('Failed to fetch appointments');}

      const data = await response.json();
      setMyAppointments(data.appointments);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load appointments');
    } finally {
      setLoading(false);
    }
  };

  const handleBookAppointment = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedTeacher) {return;}

    setLoading(true);
    setError(null);

    try {
      const [hours, minutes] = bookingForm.selectedTime.split(':');
      const startTime = `${hours}:${minutes}:00`;
      const endHour = parseInt(hours) + 1;
      const endTime = `${endHour.toString().padStart(2, '0')}:${minutes}:00`;

      const response = await fetch(`${API_BASE}/api/v1/teachers/appointments?student_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          teacher_id: selectedTeacher.id,
          scheduled_date: bookingForm.selectedDate,
          start_time: startTime,
          end_time: endTime,
          appointment_type: bookingForm.appointmentType,
          subject: bookingForm.subject,
          topic: bookingForm.topic,
          description: bookingForm.description,
        }),
      });

      if (!response.ok) {throw new Error('Failed to create appointment');}

      const data = await response.json();
      alert(`Randevu oluşturuldu! Fiyat: ${data.price} ${data.currency}\nÖğretmen onayı bekleniyor.`);

      // Reset form and go back
      setBookingForm({
        selectedDate: '',
        selectedTime: '',
        appointmentType: 'one_on_one',
        subject: 'mathematics',
        topic: '',
        description: '',
      });
      setViewMode('profile');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Randevu oluşturulamadı');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelAppointment = async (appointmentId: string) => {
    if (!confirm('Randevuyu iptal etmek istediğinizden emin misiniz?')) {return;}

    const reason = prompt('İptal nedeni:');
    if (!reason) {return;}

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/teachers/appointments/${appointmentId}/cancel?cancelled_by=${userId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cancellation_reason: reason }),
        },
      );

      if (!response.ok) {throw new Error('Failed to cancel appointment');}

      alert('Randevu iptal edildi');
      fetchMyAppointments();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'İptal işlemi başarısız');
    }
  };

  return (
    <div className="teacher-pool">
      {/* Header */}
      <div className="teacher-pool-header">
        <h1>Öğretmen Havuzu</h1>
        <div className="view-tabs">
          <button
            className={viewMode === 'search' ? 'active' : ''}
            onClick={() => setViewMode('search')}
          >
            Öğretmen Ara
          </button>
          <button
            className={viewMode === 'appointments' ? 'active' : ''}
            onClick={() => setViewMode('appointments')}
          >
            Randevularım
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Search View */}
      {viewMode === 'search' && (
        <div className="search-view">
          {/* Search Filters */}
          <div className="search-filters">
            <h3>Filtreler</h3>

            <div className="filter-group">
              <label>Ders:</label>
              <select
                value={searchFilters.subject}
                onChange={(e) => setSearchFilters({ ...searchFilters, subject: e.target.value as SubjectExpertise })}
              >
                <option value="">Tümü</option>
                <option value="mathematics">Matematik</option>
                <option value="physics">Fizik</option>
                <option value="chemistry">Kimya</option>
                <option value="biology">Biyoloji</option>
                <option value="turkish">Türkçe</option>
                <option value="history">Tarih</option>
                <option value="geography">Coğrafya</option>
                <option value="english">İngilizce</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Şehir:</label>
              <input
                type="text"
                placeholder="İstanbul, Ankara..."
                value={searchFilters.city}
                onChange={(e) => setSearchFilters({ ...searchFilters, city: e.target.value })}
              />
            </div>

            <div className="filter-group">
              <label>Minimum Puan:</label>
              <input
                type="number"
                min="0"
                max="5"
                step="0.5"
                value={searchFilters.minRating}
                onChange={(e) => setSearchFilters({ ...searchFilters, minRating: parseFloat(e.target.value) })}
              />
            </div>

            <div className="filter-group">
              <label>Max Ücret (₺/saat):</label>
              <input
                type="number"
                min="0"
                value={searchFilters.maxHourlyRate}
                onChange={(e) => setSearchFilters({ ...searchFilters, maxHourlyRate: parseInt(e.target.value) })}
              />
            </div>

            <div className="filter-group checkbox">
              <label>
                <input
                  type="checkbox"
                  checked={searchFilters.onlineOnly}
                  onChange={(e) => setSearchFilters({ ...searchFilters, onlineOnly: e.target.checked })}
                />
                Sadece Online
              </label>
            </div>

            <button className="btn-search" onClick={searchTeachers} disabled={loading}>
              {loading ? 'Aranıyor...' : 'Ara'}
            </button>
          </div>

          {/* Teacher List */}
          <div className="teacher-list">
            {loading && <div className="loading">Öğretmenler yükleniyor...</div>}

            {teachers.map(teacher => (
              <div key={teacher.id} className="teacher-card" onClick={() => fetchTeacherProfile(teacher.id)}>
                <div className="teacher-avatar">
                  {teacher.profile_photo_url ? (
                    <img src={teacher.profile_photo_url} alt={teacher.full_name} />
                  ) : (
                    <div className="avatar-placeholder">{teacher.full_name.charAt(0)}</div>
                  )}
                </div>

                <div className="teacher-info">
                  <h3>{teacher.full_name}</h3>
                  <p className="teacher-title">{teacher.title}</p>
                  <p className="teacher-bio">{teacher.bio?.substring(0, 120)}...</p>

                  <div className="teacher-meta">
                    <span className="rating">⭐ {teacher.average_rating.toFixed(1)} ({teacher.total_reviews})</span>
                    <span className="experience">{teacher.years_of_experience} yıl</span>
                    <span className="location">📍 {teacher.city}</span>
                  </div>

                  <div className="teacher-rate">
                    <strong>{teacher.hourly_rate} {teacher.currency}</strong> / saat
                  </div>
                </div>
              </div>
            ))}

            {!loading && teachers.length === 0 && (
              <div className="no-results">Öğretmen bulunamadı</div>
            )}
          </div>
        </div>
      )}

      {/* Teacher Profile View */}
      {viewMode === 'profile' && selectedTeacher && (
        <div className="profile-view">
          <button className="btn-back" onClick={() => setViewMode('search')}>
            ← Geri
          </button>

          <div className="teacher-profile">
            {/* Profile Header */}
            <div className="profile-header">
              <div className="profile-avatar">
                {selectedTeacher.profile_photo_url ? (
                  <img src={selectedTeacher.profile_photo_url} alt={selectedTeacher.full_name} />
                ) : (
                  <div className="avatar-placeholder large">{selectedTeacher.full_name.charAt(0)}</div>
                )}
              </div>

              <div className="profile-info">
                <h2>{selectedTeacher.full_name}</h2>
                <p className="profile-title">{selectedTeacher.title}</p>
                <div className="profile-rating">
                  ⭐ {selectedTeacher.average_rating.toFixed(1)} / 5.0
                  <span className="review-count">({selectedTeacher.total_reviews} değerlendirme)</span>
                </div>
                <div className="profile-stats">
                  <span>{selectedTeacher.total_sessions} ders</span>
                  <span>{selectedTeacher.years_of_experience} yıl deneyim</span>
                  <span>📍 {selectedTeacher.city}</span>
                </div>
                <div className="profile-rate">
                  <strong>{selectedTeacher.hourly_rate} {selectedTeacher.currency}</strong> / saat
                </div>
              </div>
            </div>

            {/* Bio */}
            <div className="profile-section">
              <h3>Hakkında</h3>
              <p>{selectedTeacher.bio}</p>
            </div>

            {/* Education */}
            <div className="profile-section">
              <h3>Eğitim</h3>
              <p><strong>{selectedTeacher.education_level}</strong></p>
              <p>{selectedTeacher.university} - {selectedTeacher.department}</p>
            </div>

            {/* Expertise */}
            <div className="profile-section">
              <h3>Uzmanlık Alanları</h3>
              <div className="expertise-list">
                {selectedTeacher.expertise.map(exp => (
                  <div key={exp.id} className="expertise-item">
                    <div className="expertise-header">
                      <strong>{getSubjectLabel(exp.subject)}</strong>
                      {exp.is_verified && <span className="verified-badge">✓ Doğrulanmış</span>}
                    </div>
                    <div className="expertise-details">
                      <span>Seviye: {exp.proficiency_level}</span>
                      <span>{exp.years_teaching_subject} yıl</span>
                    </div>
                    {exp.exam_types.length > 0 && (
                      <div className="exam-types">
                        Sınavlar: {exp.exam_types.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Certifications */}
            {selectedTeacher.certifications.length > 0 && (
              <div className="profile-section">
                <h3>Sertifikalar ve Belgeler</h3>
                <div className="certifications-list">
                  {selectedTeacher.certifications.map(cert => (
                    <div key={cert.id} className="certification-item">
                      <div className="cert-title">{cert.title}</div>
                      <div className="cert-org">{cert.issuing_organization}</div>
                      <div className="cert-date">{cert.issue_date}</div>
                      {cert.verification_status === 'approved' && (
                        <span className="verified-badge">✓ Doğrulanmış</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Book Button */}
            {selectedTeacher.is_accepting_students && (
              <div className="booking-action">
                <button className="btn-book" onClick={() => setViewMode('booking')}>
                  Randevu Al
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Booking View */}
      {viewMode === 'booking' && selectedTeacher && (
        <div className="booking-view">
          <button className="btn-back" onClick={() => setViewMode('profile')}>
            ← Geri
          </button>

          <h2>Randevu Oluştur - {selectedTeacher.full_name}</h2>

          <form onSubmit={handleBookAppointment} className="booking-form">
            <div className="form-group">
              <label>Tarih *</label>
              <input
                type="date"
                required
                min={new Date().toISOString().split('T')[0]}
                value={bookingForm.selectedDate}
                onChange={(e) => setBookingForm({ ...bookingForm, selectedDate: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Saat *</label>
              <input
                type="time"
                required
                value={bookingForm.selectedTime}
                onChange={(e) => setBookingForm({ ...bookingForm, selectedTime: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Ders Türü *</label>
              <select
                required
                value={bookingForm.appointmentType}
                onChange={(e) => setBookingForm({ ...bookingForm, appointmentType: e.target.value as AppointmentType })}
              >
                <option value="one_on_one">Birebir Ders</option>
                <option value="question_answer">Soru-Cevap</option>
                <option value="exam_prep">Sınav Hazırlık</option>
              </select>
            </div>

            <div className="form-group">
              <label>Ders *</label>
              <select
                required
                value={bookingForm.subject}
                onChange={(e) => setBookingForm({ ...bookingForm, subject: e.target.value as SubjectExpertise })}
              >
                {selectedTeacher.expertise.map(exp => (
                  <option key={exp.id} value={exp.subject}>{getSubjectLabel(exp.subject)}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Konu *</label>
              <input
                type="text"
                required
                placeholder="Örn: Türev, Kuvvet ve Hareket"
                value={bookingForm.topic}
                onChange={(e) => setBookingForm({ ...bookingForm, topic: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Açıklama</label>
              <textarea
                rows={4}
                placeholder="Daha detaylı açıklama..."
                value={bookingForm.description}
                onChange={(e) => setBookingForm({ ...bookingForm, description: e.target.value })}
              />
            </div>

            <div className="booking-summary">
              <div>Süre: 1 saat</div>
              <div>Ücret: <strong>{selectedTeacher.hourly_rate} {selectedTeacher.currency}</strong></div>
            </div>

            <button type="submit" className="btn-submit" disabled={loading}>
              {loading ? 'Oluşturuluyor...' : 'Randevu Oluştur'}
            </button>
          </form>
        </div>
      )}

      {/* Appointments View */}
      {viewMode === 'appointments' && (
        <div className="appointments-view">
          <h2>Randevularım</h2>

          {loading && <div className="loading">Randevular yükleniyor...</div>}

          <div className="appointments-list">
            {myAppointments.map(appointment => (
              <div key={appointment.id} className={`appointment-card status-${appointment.status}`}>
                <div className="appointment-header">
                  <h4>{appointment.topic}</h4>
                  <span className={`status-badge ${appointment.status}`}>
                    {getStatusLabel(appointment.status)}
                  </span>
                </div>

                <div className="appointment-details">
                  <div>📅 {appointment.scheduled_date}</div>
                  <div>🕐 {appointment.start_time} - {appointment.end_time}</div>
                  <div>📚 {getSubjectLabel(appointment.subject)}</div>
                  <div>💰 {appointment.price} TRY</div>
                </div>

                {appointment.meeting_url && (
                  <div className="meeting-link">
                    <a href={appointment.meeting_url} target="_blank" rel="noopener noreferrer">
                      🔗 Toplantıya Katıl
                    </a>
                  </div>
                )}

                <div className="appointment-actions">
                  {appointment.status === 'pending' && (
                    <button
                      className="btn-cancel"
                      onClick={() => handleCancelAppointment(appointment.id)}
                    >
                      İptal Et
                    </button>
                  )}
                  {appointment.status === 'confirmed' && (
                    <button
                      className="btn-cancel"
                      onClick={() => handleCancelAppointment(appointment.id)}
                    >
                      İptal Et
                    </button>
                  )}
                </div>
              </div>
            ))}

            {!loading && myAppointments.length === 0 && (
              <div className="no-appointments">Henüz randevunuz yok</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================
// Utility Functions
// ============================================================

function getSubjectLabel(subject: SubjectExpertise): string {
  const labels: Record<SubjectExpertise, string> = {
    mathematics: 'Matematik',
    physics: 'Fizik',
    chemistry: 'Kimya',
    biology: 'Biyoloji',
    turkish: 'Türkçe',
    history: 'Tarih',
    geography: 'Coğrafya',
    english: 'İngilizce',
    philosophy: 'Felsefe',
    literature: 'Edebiyat',
    geometry: 'Geometri',
  };
  return labels[subject] || subject;
}

function getStatusLabel(status: AppointmentStatus): string {
  const labels: Record<AppointmentStatus, string> = {
    pending: 'Onay Bekliyor',
    confirmed: 'Onaylandı',
    cancelled: 'İptal Edildi',
    completed: 'Tamamlandı',
    no_show: 'Katılmadı',
  };
  return labels[status] || status;
}

export type { TeacherPoolProps, Teacher, Appointment };
