import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, afterEach } from 'vitest';

import { apiRequest } from '@/utils/apiHelpers';

vi.mock('@/utils/apiHelpers', () => ({ apiRequest: vi.fn() }));

import { useKiroStudentId } from './useKiroStudentId';

describe('useKiroStudentId (F4-S1c — gerçek öğrenme-yolu student_id kaynağı)', () => {
  afterEach(() => vi.clearAllMocks());

  it('GET /my-profile başarılı → student_id (STU_xxx) döner', async () => {
    vi.mocked(apiRequest).mockResolvedValue({ success: true, student_id: 'STU_d04020744222' });
    const { result } = renderHook(() => useKiroStudentId());
    expect(result.current).toBeUndefined(); // ilk render: henüz gelmedi
    await waitFor(() => expect(result.current).toBe('STU_d04020744222'));
    expect(apiRequest).toHaveBeenCalledWith('/api/v1/learning-path/my-profile');
  });

  it('profil yok (404 → apiRequest throw) → undefined kalır, hata fırlatmaz', async () => {
    vi.mocked(apiRequest).mockRejectedValue(new Error('HTTP 404'));
    const { result } = renderHook(() => useKiroStudentId());
    await waitFor(() => expect(apiRequest).toHaveBeenCalled());
    expect(result.current).toBeUndefined();
  });
});
