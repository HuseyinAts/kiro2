// ============================================================================
// KIRO2 — Faz 4 F4-S1c: gerçek ogrenme-yolu student_id kaynağı.
//
// KEŞİF (curl ile doğrulanmış): backend'in IDOR-korumalı chat/duel-geçmişi uçları
// (verify_student_access, core/learning_path_auth.py) student_id'nin users.id
// DEĞİL learning_path_student_profiles.student_id (STU_xxx) olmasını şart koşar.
// Bu, EKSİK bir onboarding adımı DEĞİL — profil zaten var (backend zaten
// oluşturulmuş); sorun frontend'in bu id'ye erişecek bir yolunun olmamasıydı.
// GET /api/v1/learning-path/my-profile ("Returns student_id for use in other
// endpoints" — backend docstring) TAM bu amaç için var, kullanılmıyordu.
// ============================================================================
import * as React from 'react';

import { apiRequest } from '@/utils/apiHelpers';

interface MyProfileResponse {
  success: boolean;
  student_id?: string;
}

/** Gerçek öğrenme-yolu student_id'si (STU_xxx) — mount'ta bir kez çekilir.
 *  Profil yoksa (404, onboarding tamamlanmamış) undefined kalır; çağıran ekran
 *  backend'in kendi 403/422 hata durumunu zaten gösterir (yeni davranış eklenmez). */
export function useKiroStudentId(): string | undefined {
  const [studentId, setStudentId] = React.useState<string | undefined>(undefined);

  React.useEffect(() => {
    let alive = true;
    apiRequest<MyProfileResponse>('/api/v1/learning-path/my-profile')
      .then((data) => { if (alive && data.student_id) setStudentId(data.student_id); })
      .catch(() => undefined);
    return () => { alive = false; };
  }, []);

  return studentId;
}
