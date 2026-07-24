// ============================================================================
// KIRO2 — Faz 4 F4-S1b: App-router adaptörü. AISohbetPage'i gerçek authStore'a
// bağlar (student_id kaynağı = user.id — mevcut chatService.ts/ModernChatPage ile
// AYNI sözleşme; STU_ öğrenme-yolu id'si DEĞİL, bkz backend verify_student_access).
// Ekranın kendisi store-bağımsız kalır (mock/Storybook izolasyonu korunur) — kuplaj
// SADECE bu adaptörde.
// ============================================================================
import * as React from 'react';

import { useAuthStore } from '@/store/authStore';

import { AISohbetPage } from '../screens/AISohbetPage';

export default function KiroAISohbetRoute(): React.ReactElement {
  const { user } = useAuthStore();
  return <AISohbetPage studentId={user?.id} />;
}
