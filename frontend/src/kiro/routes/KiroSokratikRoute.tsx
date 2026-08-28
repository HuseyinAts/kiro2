// ============================================================================
// KIRO2 — Faz 4 F4-S1b/F4-S1c: App-router adaptörü. SokratikPage'i gerçek backend'e
// bağlar (student_id kaynağı = gerçek öğrenme-yolu id'si — bkz KiroAISohbetRoute.tsx).
// ============================================================================
import * as React from 'react';

import { SokratikPage } from '../screens/SokratikPage';

import { useKiroStudentId } from './useKiroStudentId';

export default function KiroSokratikRoute(): React.ReactElement {
  const studentId = useKiroStudentId();
  return <SokratikPage studentId={studentId} />;
}
