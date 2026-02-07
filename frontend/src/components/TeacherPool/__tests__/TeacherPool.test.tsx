/**
 * Test Suite: TeacherPool Component
 * Task 107: Teacher Pool - Search, Profile, Booking, Appointments Tests
 */

import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { TeacherPool } from '../TeacherPool';
import { vi, Mock } from 'vitest';

const fetchMock = vi.fn() as Mock;
global.fetch = fetchMock;

const mockTeachers = [
  {
    id: 'teacher-1',
    user_id: 'user-1',
    full_name: 'Dr. Ahmet Yılmaz',
    title: 'Doktor',
    bio: 'Matematik eğitimi uzmanı',
    city: 'İstanbul',
    district: 'Kadıköy',
    years_of_experience: 15,
    education_level: 'doctorate',
    university: 'İTÜ',
    department: 'Matematik',
    average_rating: 4.8,
    total_reviews: 120,
    total_sessions: 500,
    hourly_rate: 300,
    currency: 'TRY',
    is_accepting_students: true,
    online_teaching: true,
    in_person_teaching: true,
    expertise: [{
      id: 'exp-1',
      subject: 'mathematics',
      grade_levels: ['10', '11', '12'],
      proficiency_level: 'expert',
      years_teaching_subject: 15,
      specializations: ['Calculus', 'Algebra'],
      exam_types: ['YKS', 'AYT'],
      is_verified: true
    }],
    certifications: []
  },
  {
    id: 'teacher-2',
    user_id: 'user-2',
    full_name: 'Prof. Ayşe Demir',
    title: 'Profesör',
    bio: 'Fizik eğitimi',
    city: 'Ankara',
    district: 'Çankaya',
    years_of_experience: 20,
    education_level: 'doctorate',
    university: 'ODTÜ',
    department: 'Fizik',
    average_rating: 4.9,
    total_reviews: 200,
    total_sessions: 800,
    hourly_rate: 350,
    currency: 'TRY',
    is_accepting_students: true,
    online_teaching: true,
    in_person_teaching: false,
    expertise: [],
    certifications: []
  }
];

const mockAppointments = [
  {
    id: 'apt-1',
    teacher_id: 'teacher-1',
    scheduled_date: '2025-10-30',
    start_time: '14:00',
    end_time: '15:00',
    duration_minutes: 60,
    appointment_type: 'one_on_one',
    subject: 'mathematics',
    topic: 'Türev',
    status: 'confirmed',
    price: 300,
    meeting_url: 'https://meet.example.com/123'
  }
];

const mockAvailability = [
  {
    id: 'slot-1',
    day_of_week: 'Monday',
    start_time: '14:00',
    end_time: '16:00',
    is_recurring: true,
    status: 'available',
    max_students: 1,
    current_bookings: 0
  }
];

describe('TeacherPool - Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ teachers: mockTeachers })
    });
  });

  it('renders search interface', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      expect(screen.getByText(/Öğretmen Ara/i)).toBeInTheDocument();
    });
  });

  it('displays search filters', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Ders/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Şehir/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Min. Puan/i)).toBeInTheDocument();
    });
  });

  it('shows view mode tabs', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      expect(screen.getByText(/Ara/i)).toBeInTheDocument();
      expect(screen.getByText(/Randevularım/i)).toBeInTheDocument();
    });
  });
});

describe('TeacherPool - Teacher Search', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ teachers: mockTeachers })
    });
  });

  it('searches teachers on mount', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/teachers/search')
      );
    });
  });

  it('displays teacher cards', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      expect(screen.getByText('Dr. Ahmet Yılmaz')).toBeInTheDocument();
      expect(screen.getByText('Prof. Ayşe Demir')).toBeInTheDocument();
    });
  });

  it('displays teacher ratings', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      expect(screen.getByText('4.8')).toBeInTheDocument();
      expect(screen.getByText('4.9')).toBeInTheDocument();
    });
  });

  it('displays hourly rates', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      expect(screen.getByText(/300 TRY\/saat/i)).toBeInTheDocument();
      expect(screen.getByText(/350 TRY\/saat/i)).toBeInTheDocument();
    });
  });

  it('shows experience years', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      expect(screen.getByText(/15 yıl/i)).toBeInTheDocument();
      expect(screen.getByText(/20 yıl/i)).toBeInTheDocument();
    });
  });

  it('displays location', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      expect(screen.getByText(/İstanbul/i)).toBeInTheDocument();
      expect(screen.getByText(/Ankara/i)).toBeInTheDocument();
    });
  });
});

describe('TeacherPool - Search Filters', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ teachers: mockTeachers })
    });
  });

  it('filters by subject', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Ders/i)).toBeInTheDocument();
    });

    const subjectSelect = screen.getByLabelText(/Ders/i);
    fireEvent.change(subjectSelect, { target: { value: 'mathematics' } });

    const searchButton = screen.getByText(/Ara/i);
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('subject=mathematics')
      );
    });
  });

  it('filters by city', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      const cityInput = screen.getByLabelText(/Şehir/i);
      fireEvent.change(cityInput, { target: { value: 'İstanbul' } });
    });

    fireEvent.click(screen.getByText(/Ara/i));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('city=%C4%B0stanbul')
      );
    });
  });

  it('filters by minimum rating', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      const ratingInput = screen.getByLabelText(/Min. Puan/i);
      fireEvent.change(ratingInput, { target: { value: '4.5' } });
    });

    fireEvent.click(screen.getByText(/Ara/i));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('min_rating=4.5')
      );
    });
  });

  it('filters by max hourly rate', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      const rateInput = screen.getByLabelText(/Max. Ücret/i);
      fireEvent.change(rateInput, { target: { value: '400' } });
    });

    fireEvent.click(screen.getByText(/Ara/i));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('max_hourly_rate=400')
      );
    });
  });

  it('filters online only', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      const onlineCheckbox = screen.getByLabelText(/Sadece Online/i);
      fireEvent.click(onlineCheckbox);
    });

    fireEvent.click(screen.getByText(/Ara/i));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('online_only=true')
      );
    });
  });
});

describe('TeacherPool - Teacher Profile', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => ({ teachers: mockTeachers }) })
      .mockResolvedValueOnce({ ok: true, json: async () => mockTeachers[0] })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ availability: mockAvailability }) });
  });

  it('opens teacher profile', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      expect(screen.getByText('Dr. Ahmet Yılmaz')).toBeInTheDocument();
    });

    const profileButton = screen.getByText(/Profil Görüntüle/i);
    fireEvent.click(profileButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/teachers/profile/teacher-1')
      );
    });
  });

  it('displays teacher bio', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      fireEvent.click(screen.getByText(/Profil Görüntüle/i));
    });

    await waitFor(() => {
      expect(screen.getByText(/Matematik eğitimi uzmanı/i)).toBeInTheDocument();
    });
  });

  it('shows education details', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      fireEvent.click(screen.getByText(/Profil Görüntüle/i));
    });

    await waitFor(() => {
      expect(screen.getByText(/İTÜ/i)).toBeInTheDocument();
      expect(screen.getByText(/Matematik/i)).toBeInTheDocument();
    });
  });

  it('displays expertise', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      fireEvent.click(screen.getByText(/Profil Görüntüle/i));
    });

    await waitFor(() => {
      expect(screen.getByText(/Calculus/i)).toBeInTheDocument();
      expect(screen.getByText(/Algebra/i)).toBeInTheDocument();
    });
  });

  it('shows availability slots', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      fireEvent.click(screen.getByText(/Profil Görüntüle/i));
    });

    await waitFor(() => {
      expect(screen.getByText(/Monday/i)).toBeInTheDocument();
      expect(screen.getByText(/14:00 - 16:00/i)).toBeInTheDocument();
    });
  });
});

describe('TeacherPool - Booking', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => ({ teachers: mockTeachers }) })
      .mockResolvedValueOnce({ ok: true, json: async () => mockTeachers[0] })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ availability: mockAvailability }) });
  });

  it('opens booking form', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      fireEvent.click(screen.getByText(/Profil Görüntüle/i));
    });

    await waitFor(() => {
      const bookButton = screen.getByText(/Randevu Al/i);
      fireEvent.click(bookButton);
    });

    expect(screen.getByLabelText(/Tarih/i)).toBeInTheDocument();
  });

  it('selects appointment type', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      fireEvent.click(screen.getByText(/Profil Görüntüle/i));
      fireEvent.click(screen.getByText(/Randevu Al/i));
    });

    const typeSelect = screen.getByLabelText(/Randevu Türü/i);
    fireEvent.change(typeSelect, { target: { value: 'group_session' } });

    expect((typeSelect as HTMLSelectElement).value).toBe('group_session');
  });

  it('selects date and time', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      fireEvent.click(screen.getByText(/Profil Görüntüle/i));
      fireEvent.click(screen.getByText(/Randevu Al/i));
    });

    const dateInput = screen.getByLabelText(/Tarih/i);
    fireEvent.change(dateInput, { target: { value: '2025-10-30' } });

    expect((dateInput as HTMLInputElement).value).toBe('2025-10-30');
  });

  it('enters topic', async () => {
    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      fireEvent.click(screen.getByText(/Profil Görüntüle/i));
      fireEvent.click(screen.getByText(/Randevu Al/i));
    });

    const topicInput = screen.getByLabelText(/Konu/i);
    fireEvent.change(topicInput, { target: { value: 'Türev' } });

    expect((topicInput as HTMLInputElement).value).toBe('Türev');
  });

  it('submits booking', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAppointments[0]
    });

    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      fireEvent.click(screen.getByText(/Profil Görüntüle/i));
      fireEvent.click(screen.getByText(/Randevu Al/i));
    });

    const dateInput = screen.getByLabelText(/Tarih/i);
    fireEvent.change(dateInput, { target: { value: '2025-10-30' } });

    const submitButton = screen.getByText(/Onayla/i);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/book'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });
});

describe('TeacherPool - My Appointments', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ appointments: mockAppointments })
    });
  });

  it('switches to appointments view', async () => {
    render(<TeacherPool userId="student-123" viewMode="appointments" />);
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/my-appointments')
      );
    });
  });

  it('displays appointment list', async () => {
    render(<TeacherPool userId="student-123" viewMode="appointments" />);
    await waitFor(() => {
      expect(screen.getByText(/2025-10-30/)).toBeInTheDocument();
      expect(screen.getByText(/14:00 - 15:00/)).toBeInTheDocument();
    });
  });

  it('shows appointment status', async () => {
    render(<TeacherPool userId="student-123" viewMode="appointments" />);
    await waitFor(() => {
      expect(screen.getByText(/confirmed/i)).toBeInTheDocument();
    });
  });

  it('displays appointment topic', async () => {
    render(<TeacherPool userId="student-123" viewMode="appointments" />);
    await waitFor(() => {
      expect(screen.getByText('Türev')).toBeInTheDocument();
    });
  });

  it('shows meeting URL', async () => {
    render(<TeacherPool userId="student-123" viewMode="appointments" />);
    await waitFor(() => {
      expect(screen.getByText(/Toplantıya Katıl/i)).toBeInTheDocument();
    });
  });

  it('can cancel appointment', async () => {
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => ({}) });

    render(<TeacherPool userId="student-123" viewMode="appointments" />);
    await waitFor(() => {
      const cancelButton = screen.getByText(/İptal Et/i);
      fireEvent.click(cancelButton);
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/cancel'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });
});

describe('TeacherPool - Error Handling', () => {
  it('handles search error', async () => {
    fetchMock.mockRejectedValue(new Error('Network error'));

    render(<TeacherPool userId="student-123" />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to search teachers/i)).toBeInTheDocument();
    });
  });

  it('handles profile loading error', async () => {
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => ({ teachers: mockTeachers }) })
      .mockRejectedValueOnce(new Error('Failed to load'));

    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      fireEvent.click(screen.getByText(/Profil Görüntüle/i));
    });

    await waitFor(() => {
      expect(screen.getByText(/Failed to load teacher/i)).toBeInTheDocument();
    });
  });
});

describe('TeacherPool - Loading States', () => {
  it('shows loading during search', async () => {
    fetchMock.mockImplementation(() => new Promise(() => {}));

    render(<TeacherPool userId="student-123" />);

    await waitFor(() => {
      expect(screen.getByText(/Yükleniyor/i)).toBeInTheDocument();
    });
  });

  it('shows loading during profile fetch', async () => {
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => ({ teachers: mockTeachers }) })
      .mockImplementation(() => new Promise(() => {}));

    render(<TeacherPool userId="student-123" />);
    await waitFor(() => {
      fireEvent.click(screen.getByText(/Profil Görüntüle/i));
    });

    expect(screen.getByText(/Yükleniyor/i)).toBeInTheDocument();
  });
});

describe('TeacherPool - Empty States', () => {
  it('shows no teachers message', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ teachers: [] })
    });

    render(<TeacherPool userId="student-123" />);

    await waitFor(() => {
      expect(screen.getByText(/Öğretmen bulunamadı/i)).toBeInTheDocument();
    });
  });

  it('shows no appointments message', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ appointments: [] })
    });

    render(<TeacherPool userId="student-123" viewMode="appointments" />);

    await waitFor(() => {
      expect(screen.getByText(/Henüz randevunuz yok/i)).toBeInTheDocument();
    });
  });
});
