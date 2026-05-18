import { AxiosError, AxiosHeaders } from 'axios';
import { describe, it, expect } from 'vitest';

import { extractErrorDetail } from '../extractErrorDetail';

function makeAxiosError(status: number, data: unknown): AxiosError {
  return new AxiosError(
    'Request failed',
    String(status),
    undefined,
    null,
    {
      data,
      status,
      statusText: '',
      headers: {},
      config: { headers: new AxiosHeaders() },
    },
  );
}

describe('extractErrorDetail', () => {
  it('extracts string detail from 4xx HTTPException', () => {
    const err = makeAxiosError(400, { detail: 'question_id not found' });
    expect(extractErrorDetail(err)).toBe('question_id not found');
  });

  it('extracts first msg from Pydantic 422 array with field path', () => {
    const err = makeAxiosError(422, {
      detail: [
        { type: 'literal_error', loc: ['body', 'flag_type'], msg: 'Input should be valid' },
      ],
    });
    const result = extractErrorDetail(err);
    expect(result).toContain('flag_type');
    expect(result).toContain('Input should be valid');
  });

  it('returns Turkish rate-limit message for 429', () => {
    const err = makeAxiosError(429, { detail: 'Rate limit exceeded: 10 per 1 minute' });
    expect(extractErrorDetail(err)).toBe('Çok fazla istek gönderdiniz, lütfen biraz bekleyin');
  });

  it('returns backend detail for 409 conflict', () => {
    const err = makeAxiosError(409, { detail: 'Bu soruyu zaten aynı türde bildirdiniz.' });
    expect(extractErrorDetail(err)).toBe('Bu soruyu zaten aynı türde bildirdiniz.');
  });

  it('handles network error (no response)', () => {
    const err = new AxiosError('Network Error', 'ERR_NETWORK');
    expect(extractErrorDetail(err)).toContain('Bağlantı');
  });

  it('returns 500-class generic message', () => {
    const err = makeAxiosError(500, { detail: 'Internal Server Error' });
    expect(extractErrorDetail(err)).toContain('Sunucu hatası');
  });

  it('falls back for non-axios Error', () => {
    expect(extractErrorDetail(new Error('boom'))).toBe('boom');
  });

  it('returns fallback for null/unknown', () => {
    expect(extractErrorDetail(null, 'default')).toBe('default');
    expect(extractErrorDetail(undefined, 'fb')).toBe('fb');
    expect(extractErrorDetail({ random: 'obj' }, 'x')).toBe('x');
  });
});
