/**
 * Öğrenci dashboard — `student_dashboard` API ile hizalı.
 */

import { apiClient } from './apiClient';

/** `GET /api/v1/student-dashboard/istatistikler` gövdesi (Pydantic ile uyumlu alanlar). */
export interface DashboardStats {
  tamamlanan_dersler: number
  toplam_dersler: number
  tamamlanan_sinavlar: number
  ortalama_puan: number
  toplam_calisma_suresi?: number
  haftalik_hedef?: number
  haftalik_ilerleme?: number
  gunluk_seri?: number
  toplam_puan?: number
  seviye?: number
  deneyim?: number
  sonraki_seviye_deneyim?: number
}

export interface DashboardActivityItem {
  id: string
  baslik: string
  alt_baslik?: string
  tarih?: string
}

export interface DashboardNotificationItem {
  id: string
  baslik: string
  mesaj?: string
  tip?: string
  okundu?: boolean
  olusturulma_tarihi?: string
}

function _pickStr(v: unknown, fallback: string): string {
  if (v == null || v === '') {return fallback;}
  return String(v);
}

function _mapSinavToActivity(row: Record<string, unknown>): DashboardActivityItem {
  const id = _pickStr(
    row.id ?? row.sinav_id ?? row.session_id,
    `act-${Math.random().toString(36).slice(2)}`,
  );
  const baslik = _pickStr(
    row.sinav_adi ?? row.exam_title ?? row.title ?? row.sinav_tipi,
    'Sınav aktivitesi',
  );
  const alt = row.sinav_tipi != null ? String(row.sinav_tipi) : undefined;
  const tarih =
    row.tamamlanma_tarihi != null
      ? String(row.tamamlanma_tarihi)
      : row.olusturulma_tarihi != null
        ? String(row.olusturulma_tarihi)
        : undefined;
  return { id, baslik, alt_baslik: alt, tarih };
}

function _mapBildirim(row: Record<string, unknown>): DashboardNotificationItem {
  return {
    id: _pickStr(row.id ?? row.bildirim_id, 'n/a'),
    baslik: _pickStr(row.baslik ?? row.title, 'Bildirim'),
    mesaj: row.mesaj != null ? String(row.mesaj) : row.icerik != null ? String(row.icerik) : undefined,
    tip: row.tip != null ? String(row.tip) : undefined,
    okundu: typeof row.okundu === 'boolean' ? row.okundu : undefined,
    olusturulma_tarihi:
      row.olusturulma_tarihi != null
        ? String(row.olusturulma_tarihi)
        : row.created_at != null
          ? String(row.created_at)
          : undefined,
  };
}

class DashboardService {
  async getStats(_userId: string): Promise<DashboardStats> {
    const { data } = await apiClient.get<DashboardStats>('/api/v1/student-dashboard/istatistikler');
    return data;
  }

  async getRecentActivity(_userId: string, limit = 10): Promise<DashboardActivityItem[]> {
    const { data } = await apiClient.get<Record<string, unknown>[]>(
      '/api/v1/student-dashboard/sinav-gecmisi',
      { params: { limit, offset: 0 } },
    );
    if (!Array.isArray(data)) {return [];}
    return data.map((row) => _mapSinavToActivity(row));
  }

  async getNotifications(_userId: string, limit = 50): Promise<DashboardNotificationItem[]> {
    const { data } = await apiClient.get<Record<string, unknown>[]>(
      '/api/v1/student-dashboard/bildirimler',
      { params: { okunmamis_sadece: false, limit } },
    );
    if (!Array.isArray(data)) {return [];}
    return data.map((row) => _mapBildirim(row));
  }
}

export const dashboardService = new DashboardService();
export default dashboardService;
