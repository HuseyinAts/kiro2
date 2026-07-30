/**
 * Öğretmen "Öğrenciler" ekranı — sınıftan çıkarma (#444 / blocker #6).
 *
 * Backend'de `DELETE /api/v1/teacher/classes/{classroom_id}/students/{student_user_id}`
 * 29 Tem'de eklendi ve testlendi, ama ekranda ÇAĞIRAN hiçbir şey yoktu:
 * öğretmen bir öğrenciyi sınıftan çıkaramıyordu.
 *
 * Bu dosyanın çivilediği asıl şey URL'in HANGİ kimliklerden kurulduğu.
 * Satır üç ayrı kimlik taşıyor ve ikisi birbirine çok benziyor:
 *   `id`               -> ÜYELİK satırının kimliği (silme ucu bunu KABUL ETMEZ)
 *   `student_user_id`  -> öğrencinin kullanıcı kimliği (ucun istediği)
 *   `classroom_id`     -> sınıf kimliği (ucun istediği)
 * `id` ile `student_user_id` karıştırılırsa uç 404 döner ve ekran sessizce
 * "çıkarılamadı" der — testsiz fark edilmesi zor bir hata.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { ModernTeacherStudentsPage } from '../ModernTeacherStudentsPage';

vi.mock('../../services/apiClient', () => ({
  default: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
}));

// eslint-disable-next-line import/first
import apiClient from '../../services/apiClient';

const SATIR = {
  id: 'uyelik-999', // ÜYELİK kimliği — bilerek diğerlerinden farklı
  student_user_id: 'ogrenci-42',
  classroom_id: 'sinif-7',
  ad: 'Zeynep',
  soyad: 'Kaya',
  email: 'zeynep@example.test',
  sinif: '12-A',
  ortalama: 0,
  tamamlanan_sinav: 0,
  toplam_sinav: 0,
};

const mockApi = apiClient as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

beforeEach(() => {
  mockApi.get.mockImplementation((url: string) =>
    url.includes('/students')
      ? Promise.resolve({ data: { students: [SATIR] } })
      : Promise.resolve({ data: [{ sinif_id: 'sinif-7', sinif_adi: '12-A' }] }),
  );
  mockApi.delete.mockResolvedValue({ data: { ok: true } });
});

afterEach(() => {
  vi.clearAllMocks();
});

async function ekraniAc() {
  render(<ModernTeacherStudentsPage />);
  return screen.findByText('Zeynep Kaya');
}

describe('ModernTeacherStudentsPage · sınıftan çıkarma', () => {
  it('DELETE URL"ini classroom_id + student_user_id ile kurar (üyelik id"si DEĞİL)', async () => {
    const onay = vi.spyOn(window, 'confirm').mockReturnValue(true);
    await ekraniAc();

    await userEvent.click(screen.getByRole('button', { name: /sınıftan çıkar/i }));

    await waitFor(() =>
      expect(mockApi.delete).toHaveBeenCalledWith(
        '/api/v1/teacher/classes/sinif-7/students/ogrenci-42',
      ),
    );
    // Üyelik kimliği URL'e SIZMAMALI — uç onu tanımaz.
    expect(mockApi.delete.mock.calls[0][0]).not.toContain('uyelik-999');
    onay.mockRestore();
  });

  it('onay verilmezse hiçbir istek atmaz', async () => {
    const onay = vi.spyOn(window, 'confirm').mockReturnValue(false);
    await ekraniAc();

    await userEvent.click(screen.getByRole('button', { name: /sınıftan çıkar/i }));

    expect(mockApi.delete).not.toHaveBeenCalled();
    onay.mockRestore();
  });

  it('başarılı çıkarmadan sonra listeyi sunucudan tazeler', async () => {
    const onay = vi.spyOn(window, 'confirm').mockReturnValue(true);
    await ekraniAc();
    const oncekiGet = mockApi.get.mock.calls.length;

    await userEvent.click(screen.getByRole('button', { name: /sınıftan çıkar/i }));

    // Yerel state'ten satır silmek yeterli DEĞİL: sunucu reddi/yarış durumunda
    // ekran gerçekte var olan bir kaydı yokmuş gibi gösterirdi.
    await waitFor(() =>
      expect(mockApi.get.mock.calls.length).toBeGreaterThan(oncekiGet),
    );
    onay.mockRestore();
  });
});
