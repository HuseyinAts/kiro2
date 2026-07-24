// ============================================================================
// KIRO2 — Route Guard (FAZ 3 KAPANIŞ · Auth kalıntı)
// Rol → giriş-sonrası landing rota eşlemesi + AuthGate. Navigasyon PROP-ENJEKTE
// (onRedirect); sabit `useNavigate` KOYULMAZ — router'sız test/Storybook kırılmaz.
// Faz 4 (gerçek router bağlanınca): yeni guard İCAT ETME → mevcut ProtectedRoute +
// getRedirectPathByRole'ü REUSE et; TR/EN rota drift'ini tek kanona (ROL_LANDING)
// hizala. Rol AYRI kaynak (Persona'ya EKLENMEZ; api-client.getRol / GET /me/rol).
// ============================================================================
import * as React from 'react';

import type { KiroRol } from '../types';

/** Rol → giriş sonrası landing rotası. İNGİLİZCE KANON — components/Auth/ProtectedRoute
 *  `getRedirectPathByRole` ile AYNI olmalı (değişirse ikisini birlikte güncelle; F4-S1'de
 *  kiro ekranları ProtectedRoute ile mount edilince o fonksiyon tek-kaynak olur). */
export const ROL_LANDING: Record<KiroRol, string> = {
  ogrenci: '/dashboard',
  veli: '/parent/dashboard',
  ogretmen: '/teacher/dashboard',
};

/** Rolün landing rotası (ROL_LANDING araması). */
export function roleLanding(rol: KiroRol): string {
  return ROL_LANDING[rol];
}

/** AuthGate props — rol null (kimlik yok) → /login; rol var → rolün landing'i.
 *  Navigasyon PROP-ENJEKTE (onRedirect); children opsiyonel (guard geçince içerik). */
export interface AuthGateProps {
  rol: KiroRol | null;
  onRedirect: (rota: string) => void;
  children?: React.ReactNode;
}

/** Rol yoksa girişe, varsa rolün landing'ine yönlendirir (prop-enjekte onRedirect;
 *  sabit useNavigate YOK → router'sız test/story kırılmaz). children verilirse render eder. */
export function AuthGate(props: AuthGateProps): React.ReactElement | null {
  const { rol, onRedirect, children } = props;
  React.useEffect(() => {
    onRedirect(rol == null ? '/login' : roleLanding(rol));
  }, [rol, onRedirect]);
  return children != null ? React.createElement(React.Fragment, null, children) : null;
}
