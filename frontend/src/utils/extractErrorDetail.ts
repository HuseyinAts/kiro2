/**
 * extractErrorDetail — Backend error response'unu kullanıcı-dostu mesaja çevirir.
 *
 * Backend Pydantic 422: { detail: [{ type, loc, msg, input }] }  (array)
 * Backend HTTPException 4xx: { detail: "Mesaj" }                  (string)
 * Backend slowapi 429:       { detail: "Rate limit exceeded: ..." }
 *
 * Output: User-facing string (Türkçe).
 */

import { AxiosError } from 'axios';

interface PydanticValidationError {
  type?: string;
  loc?: (string | number)[];
  msg?: string;
  input?: unknown;
}

interface BackendErrorBody {
  detail?: string | PydanticValidationError[];
}

export function extractErrorDetail(err: unknown, fallback = 'Beklenmeyen bir hata oluştu'): string {
  if (err instanceof AxiosError) {
    // Network error (no response received)
    if (!err.response) {
      return 'Bağlantı hatası, lütfen internetinizi kontrol edin';
    }

    const status = err.response.status;
    const data = err.response.data as BackendErrorBody | undefined;

    // Rate limit (429) — always show user-friendly Turkish
    if (status === 429) {
      return 'Çok fazla istek gönderdiniz, lütfen biraz bekleyin';
    }

    // Conflict (409) — duplicate or constraint, show backend detail (Turkish)
    if (status === 409 && typeof data?.detail === 'string') {
      return data.detail;
    }

    // 422 Pydantic validation — detail is array
    if (Array.isArray(data?.detail)) {
      const first = data.detail[0];
      if (first?.msg) {
        // Strip "body" prefix from loc, join remaining as field path
        const fieldPath = first.loc?.slice(1).join('.');
        return fieldPath ? `${fieldPath}: ${first.msg}` : first.msg;
      }
      return 'Form doğrulama hatası';
    }

    // 5xx — never expose backend internals (check before string detail)
    if (status >= 500) {
      return 'Sunucu hatası, lütfen daha sonra tekrar deneyin';
    }

    // 4xx with string detail (after 5xx guard)
    if (typeof data?.detail === 'string') {
      return data.detail;
    }

    return err.message || fallback;
  }

  if (err instanceof Error) {
    return err.message || fallback;
  }

  return fallback;
}
