// ============================================================================
// KIRO2 — Faz 4 F4-S1b/F4-S1c: App-router adaptörü. AISohbetPage'i gerçek backend'e
// bağlar. student_id kaynağı: GET /api/v1/learning-path/my-profile (useKiroStudentId)
// — users.id DEĞİL, gerçek öğrenme-yolu student_id'si (STU_xxx). Bkz useKiroStudentId.ts
// keşif notu. Ekranın kendisi store-bağımsız kalır (mock/Storybook izolasyonu
// korunur) — kuplaj SADECE bu adaptörde.
// ============================================================================
import * as React from 'react';

import { AISohbetPage } from '../screens/AISohbetPage';

import { useKiroStudentId } from './useKiroStudentId';

export default function KiroAISohbetRoute(): React.ReactElement {
  const studentId = useKiroStudentId();
  return <AISohbetPage studentId={studentId} />;
}
