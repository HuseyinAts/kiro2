import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { configureKiroApi, type MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';

const D = kiroData as unknown as MockData;

vi.mock('@/utils/apiHelpers', () => ({
  apiRequest: vi.fn().mockResolvedValue({ success: true, student_id: 'STU_test123' }),
}));

import KiroSokratikRoute from './KiroSokratikRoute';

describe('KiroSokratikRoute (F4-S1b/c App-router adaptörü)', () => {
  it('useKiroStudentId (GET /my-profile) SokratikPage studentId propuna geçer; render kırılmaz (mock mod)', async () => {
    configureKiroApi({ mode: 'mock', mockData: D });
    render(<KiroSokratikRoute />);
    expect(await screen.findByText(D.sokratik.acilis)).toBeInTheDocument();
  });
});
