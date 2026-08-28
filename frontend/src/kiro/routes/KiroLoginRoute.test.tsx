import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, afterEach } from 'vitest';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

const mockLogin = vi.fn();
const mockVerifyTwoFactor = vi.fn();
let mockUser: { id: string; rol: string } | undefined;
vi.mock('@/store/authStore', () => {
  const fn = () => ({ login: mockLogin, verifyTwoFactor: mockVerifyTwoFactor, user: mockUser });
  fn.getState = () => ({ user: mockUser });
  return { useAuthStore: fn };
});

// Gerçek getRedirectPathByRole'ü (admin dahil tam kanon) izole test eder — burada
// sadece KiroLoginRoute'un onLanding'te BU fonksiyonu (kiro'nun kendi roleLanding'i
// DEĞİL) çağırdığını doğrulamak için basit bir mock yeterli.
vi.mock('@/components/Auth/ProtectedRoute', () => ({
  getRedirectPathByRole: (rol?: string) => (rol === 'ogretmen' ? '/teacher/dashboard' : '/dashboard'),
}));

import KiroLoginRoute from './KiroLoginRoute';

describe('KiroLoginRoute (F4-S1a/A2.2b App-router adaptörü)', () => {
  afterEach(() => {
    vi.clearAllMocks();
    mockUser = undefined;
  });

  it('onLogin: kiro {eposta,sifre} → gerçek authStore.login({email,password}) map eder', async () => {
    mockLogin.mockResolvedValue(true);
    mockUser = { id: 'u1', rol: 'ogrenci' };
    render(<KiroLoginRoute />);
    await userEvent.type(screen.getByLabelText('E-posta adresin'), 'ali@eposta.com');
    await userEvent.type(screen.getByLabelText('Şifren'), 'sifre123');
    await userEvent.click(screen.getByRole('button', { name: 'Devam edelim' }));
    expect(mockLogin).toHaveBeenCalledWith({ email: 'ali@eposta.com', password: 'sifre123' });
  });

  it('onLanding: getRedirectPathByRole(gerçek user.rol) ile navigate eder (kiro roleLanding DEĞİL, admin dahil tam kanon)', async () => {
    mockLogin.mockResolvedValue(true);
    mockUser = { id: 'u1', rol: 'ogretmen' };
    render(<KiroLoginRoute />);
    await userEvent.type(screen.getByLabelText('E-posta adresin'), 'ali@eposta.com');
    await userEvent.type(screen.getByLabelText('Şifren'), 'sifre123');
    await userEvent.click(screen.getByRole('button', { name: 'Devam edelim' }));
    await userEvent.click(await screen.findByRole('button', { name: 'Panele geç' }));
    expect(mockNavigate).toHaveBeenCalledWith('/teacher/dashboard');
  });

  it('onLogin false (yanlış kimlik) → hint gösterir, navigate ÇAĞRILMAZ', async () => {
    mockLogin.mockResolvedValue(false);
    render(<KiroLoginRoute />);
    await userEvent.type(screen.getByLabelText('E-posta adresin'), 'ali@eposta.com');
    await userEvent.type(screen.getByLabelText('Şifren'), 'yanlis');
    await userEvent.click(screen.getByRole('button', { name: 'Devam edelim' }));
    expect(await screen.findByText(/eşleşmedi/)).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('onRegister: gerçek authStore.register YERİNE /register sayfasına yönlendirir (KVKK-minor alan eksikliği — soyad/birth_date/veli_email kiro formunda yok)', async () => {
    render(<KiroLoginRoute />);
    await userEvent.click(screen.getByRole('radio', { name: 'Kayıt' }));
    await userEvent.type(screen.getByLabelText('Adın'), 'Ali');
    await userEvent.type(screen.getByLabelText('E-posta adresin'), 'ali@eposta.com');
    await userEvent.type(screen.getByLabelText('Şifren'), 'sifre123');
    await userEvent.click(screen.getByRole('button', { name: 'Hesabımı aç' }));
    expect(mockNavigate).toHaveBeenCalledWith('/register');
  });
});
