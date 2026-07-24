// ============================================================================
// KIRO2 — Faz 4 F4-S1b: App-router adaptörü. SokratikPage'i gerçek authStore'a
// bağlar (student_id kaynağı = user.id — bkz KiroAISohbetRoute.tsx).
// ============================================================================
import * as React from 'react';

import { useAuthStore } from '@/store/authStore';

import { SokratikPage } from '../screens/SokratikPage';

export default function KiroSokratikRoute(): React.ReactElement {
  const { user } = useAuthStore();
  return <SokratikPage studentId={user?.id} />;
}
