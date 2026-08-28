export interface DashboardStats {
  tamamlanan_dersler: number;
  toplam_dersler: number;
  tamamlanan_sinavlar: number;
  ortalama_puan: number;
  toplam_calisma_suresi: number;
  haftalik_ilerleme: number;
  gunluk_seri: number;
  toplam_puan: number;
  seviye: number;
  deneyim: number;
}

export interface RecentExam {
  sinav_id: string;
  sinav_adi: string;
  sinav_tipi: string;
  tarih: string;
  puan: number;
  dogru_sayisi: number;
  yanlis_sayisi: number;
  bos_sayisi: number;
  sure: number;
}

export interface GamificationProfile {
  total_xp: number;
  current_level: number;
  xp_for_next_level: number;
  streak: number;
  streak_active_today: boolean;
  total_badges: number;
  leaderboard_rank: number | null;
}

export interface DailyQuestSummary {
  completed_count: number;
  total_count: number;
  all_completed: boolean;
  bonus_available: boolean;
}
