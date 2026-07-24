import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { configureKiroApi, type MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';

vi.mock('@/utils/apiHelpers', () => ({
  apiRequest: vi.fn().mockResolvedValue({ success: true, student_id: 'STU_test123' }),
}));

import KiroAISohbetRoute from './KiroAISohbetRoute';

describe('KiroAISohbetRoute (F4-S1b/c App-router adaptörü)', () => {
  it('useKiroStudentId (GET /my-profile) AISohbetPage studentId propuna geçer; render kırılmaz (mock mod)', async () => {
    configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });
    render(<KiroAISohbetRoute />);
    expect(await screen.findByRole('navigation')).toBeInTheDocument();
    expect(await screen.findByRole('log')).toBeInTheDocument();
  });
});
