// ============================================================================
// KIRO2 — Faz 4 F4-S1a/A2.2b: App-router adaptörü. GirisPage'i gerçek authStore'a
// bağlar (cookie auth). Alan-adı map: kiro {eposta,sifre} → gerçek {email,password}.
// KAYIT (register) gerçek authStore.register'a BAĞLANMAZ — backend soyad/birth_date/
// veli_email (KVKK-minor) zorunlu tutuyor, kiro'nun minimal formu bunları toplamıyor;
// eksik veriyle kayıt denemek ya validation fail ya da KVKK-minor onay atlanması riski
// taşır. Bunun yerine mevcut TAM uyumlu /register (ModernRegisterPage) sayfasına
// yönlendirilir — registration mantığı yeniden icat edilmez.
// ============================================================================
import * as React from 'react';
import { useNavigate } from 'react-router-dom';

import { getRedirectPathByRole } from '@/components/Auth/ProtectedRoute';
import { useAuthStore } from '@/store/authStore';

import { GirisPage } from '../screens/GirisPage';
import type { KiroRol } from '../types';

/** Gerçek UserRole (admin dahil) → KiroRol (ogrenci|veli|ogretmen) daraltma —
 *  sadece kiro'nun CTA-görünüm etiketi için; GERÇEK yönlendirme onLanding'te
 *  getRedirectPathByRole (admin dahil tam kanon) ile yapılır. */
function toKiroRol(rol?: string): KiroRol | undefined {
  return rol === 'ogrenci' || rol === 'veli' || rol === 'ogretmen' ? rol : undefined;
}

export default function KiroLoginRoute(): React.ReactElement {
  const navigate = useNavigate();
  const { login, verifyTwoFactor, user } = useAuthStore();

  return (
    <GirisPage
      rol={toKiroRol(user?.rol)}
      onLogin={({ eposta, sifre }) => login({ email: eposta, password: sifre })}
      onVerify2fa={({ eposta, sifre, kod }) => verifyTwoFactor(eposta, sifre, kod)}
      onRegister={() => { navigate('/register'); }}
      onLanding={() => {
        navigate(getRedirectPathByRole(useAuthStore.getState().user?.rol));
      }}
    />
  );
}
