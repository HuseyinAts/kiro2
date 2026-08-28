/**
 * ModernLoginPage — 2FA challenge step
 *
 * S200 audit found login() already returns the '2fa_required' signal
 * (authStore.ts) but ModernLoginPage never read it — TOTP-enabled users
 * got a generic "wrong password" error with no way to actually log in.
 * This locks in the fix: on '2fa_required', show a TOTP code step that
 * calls verifyTwoFactor().
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

const mockLogin = vi.fn()
const mockVerifyTwoFactor = vi.fn()

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({
    login: mockLogin,
    verifyTwoFactor: mockVerifyTwoFactor,
    isAuthenticated: false,
    user: null,
  }),
}))

import { ModernLoginPage } from '../ModernLoginPage'

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/login']}>
      <ModernLoginPage />
    </MemoryRouter>,
  )

describe('ModernLoginPage — 2FA challenge (S200 audit fix)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows the TOTP code step when login() signals 2fa_required', async () => {
    mockLogin.mockResolvedValue('2fa_required')
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText(/E-posta Adresi/i), 'ogrenci@kiro2.com')
    await user.type(screen.getByLabelText(/^Şifre$/i), 'Sifre123!')
    await user.click(screen.getByRole('button', { name: /Giriş Yap/i }))

    expect(await screen.findByLabelText(/Doğrulama Kodu/i)).toBeInTheDocument()
    expect(screen.queryByLabelText(/E-posta Adresi/i)).not.toBeInTheDocument()
  })

  it('calls verifyTwoFactor with email/password/code and does not show a generic login error', async () => {
    mockLogin.mockResolvedValue('2fa_required')
    mockVerifyTwoFactor.mockResolvedValue(true)
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText(/E-posta Adresi/i), 'ogrenci@kiro2.com')
    await user.type(screen.getByLabelText(/^Şifre$/i), 'Sifre123!')
    await user.click(screen.getByRole('button', { name: /Giriş Yap/i }))

    const codeField = await screen.findByLabelText(/Doğrulama Kodu/i)
    await user.type(codeField, '123456')
    await user.click(screen.getByRole('button', { name: /Doğrula/i }))

    await waitFor(() =>
      expect(mockVerifyTwoFactor).toHaveBeenCalledWith('ogrenci@kiro2.com', 'Sifre123!', '123456'),
    )
    expect(screen.queryByText('E-posta veya şifre hatalı')).not.toBeInTheDocument()
  })

  it('shows an error and stays on the TOTP step when the code is wrong', async () => {
    mockLogin.mockResolvedValue('2fa_required')
    mockVerifyTwoFactor.mockResolvedValue(false)
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText(/E-posta Adresi/i), 'ogrenci@kiro2.com')
    await user.type(screen.getByLabelText(/^Şifre$/i), 'Sifre123!')
    await user.click(screen.getByRole('button', { name: /Giriş Yap/i }))

    const codeField = await screen.findByLabelText(/Doğrulama Kodu/i)
    await user.type(codeField, '000000')
    await user.click(screen.getByRole('button', { name: /Doğrula/i }))

    expect(await screen.findByText(/Doğrulama kodu hatalı/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Doğrulama Kodu/i)).toBeInTheDocument()
  })

  it('"Geri dön" returns to the normal login form', async () => {
    mockLogin.mockResolvedValue('2fa_required')
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText(/E-posta Adresi/i), 'ogrenci@kiro2.com')
    await user.type(screen.getByLabelText(/^Şifre$/i), 'Sifre123!')
    await user.click(screen.getByRole('button', { name: /Giriş Yap/i }))

    await screen.findByLabelText(/Doğrulama Kodu/i)
    await user.click(screen.getByRole('button', { name: /Geri dön/i }))

    expect(screen.getByLabelText(/E-posta Adresi/i)).toBeInTheDocument()
    expect(screen.queryByLabelText(/Doğrulama Kodu/i)).not.toBeInTheDocument()
  })
})
