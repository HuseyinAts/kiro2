/**
 * Modern Teacher Co-Pilot Page (2026 Q3-Q4)
 * ZPD (Yakınsal Gelişim Alanı) ve FSRS Unutma Eğrisi Takip Ekranı Sayfası
 */

import React from 'react';
import { Box, Container } from '@mui/material';
import { TeacherCoPilotDashboard } from '@/components/Teacher/TeacherCoPilotDashboard';
import { RoleBasedLayout } from '@/components/Layout/RoleBasedLayout';

export const ModernTeacherCoPilotPage: React.FC = () => {
  return (
    <RoleBasedLayout>
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Box sx={{ minHeight: '80vh' }}>
          <TeacherCoPilotDashboard />
        </Box>
      </Container>
    </RoleBasedLayout>
  );
};

export default ModernTeacherCoPilotPage;
