/**
 * Gelişmiş Raporlama Servisi
 * IRT, Morfoloji, ZPD ve Hibrit Öğrenme Stili analizleri için API servisi
 */

import { apiClient } from './apiClient'

export interface IRTAnalysis {
  soru_analizleri: Array<{
    konu: string
    irt_parametreleri: {
      difficulty: number
      discrimination: number
      guessing: number
      morfoloji_faktoru: number
    }
    morfoloji_analizi: {
      ortalama_morfoloji_skoru: number
      kelime_karmasikligi: number
      ek_cesitliligi: number
      toplam_kelime_sayisi: number
      ortalama_ek_sayisi: number
    }
    soru_kalite_skoru: number
    zorluk_seviyesi: string
  }>
  genel_istatistikler: {
    ortalama_zorluk: number
    ortalama_ayirt_edicilik: number
    ortalama_morfoloji_faktoru: number
    toplam_soru_sayisi: number
  }
  morfoloji_farkindaliği: {
    genel_seviye: string
    guclu_alanlar: string[]
    gelisim_alanlari: string[]
    oneri_skorlari: Record<string, number>
  }
  irt_performans_profili: {
    yetenek_tahmini: number
    guven_araligi: [number, number]
    standart_hata: number
  }
}

export interface ZPDAnalysis {
  konu_zpd_analizleri: Array<{
    konu: string
    mevcut_seviye: number
    alt_sinir: number
    ust_sinir: number
    optimal_zorluk: number
    kulturel_carpan: number
    maarif_uyum_katsayisi: number
    grup_calismasi_bonusu: number
    ogretmen_rehberlik_faktoru: number
    hesaplama_guveni: number
    kulturel_uyum_guveni: number
  }>
  genel_zpd_profili: {
    ortalama_mevcut_seviye: number
    ortalama_optimal_zorluk: number
    kulturel_uyum_seviyesi: string
    maarif_degerleri_uyumu: string
  }
  kisisellestirilmis_oneriler: Array<{
    konu: string
    oneri_tipi: string
    aciklama: string
    onerilen_zorluk: number
    ogrenme_yontemi: string
    tahmini_sure: string
  }>
  kulturel_faktorler: Record<string, number>
  maarif_degerleri_profili: Record<string, number>
}

export interface LearningStyleAnalysis {
  vark_profili: {
    visual: number
    auditory: number
    reading: number
    kinesthetic: number
  }
  felder_silverman_profili: {
    active_reflective: number
    sensing_intuitive: number
    visual_verbal: number
    sequential_global: number
  }
  hibrit_profil_ozeti: {
    dominant_vark_stili: string
    dominant_felder_boyutu: string
    hibrit_kod: string
    guven_seviyesi: number
    profil_aciklamasi: string
  }
  performans_uyumu: Array<{
    konu: string
    basari_yuzdesi: number
    ogrenme_stili_uyumu: number
    onerilen_yontem: string
    uyum_analizi: string
  }>
  ogrenme_onerileri: Array<{
    konu: string
    oneri: string
    detay: string
    oncelik: string
  }>
  stil_bazli_performans_analizi: {
    en_uyumlu_konular: string[]
    gelisim_gerektiren_konular: string[]
    ortalama_uyum_skoru: number
  }
}

export interface OSYMETSComparison {
  sinav_parametreleri: {
    ortalama_ayirt_edicilik: number
    ortalama_zorluk: number
    ortalama_sans_faktoru: number
    guvenilirlik_katsayisi: number
    morfoloji_avantaji: number
  }
  osym_karsilastirma: {
    ayirt_edicilik_durumu: { durum: string; skor: number; deger: number }
    zorluk_durumu: { durum: string; skor: number; deger: number }
    sans_faktoru_durumu: { durum: string; skor: number; deger: number }
    genel_uyum_skoru: number
  }
  ets_karsilastirma: {
    ayirt_edicilik_durumu: { durum: string; skor: number; deger: number }
    zorluk_durumu: { durum: string; skor: number; deger: number }
    sans_faktoru_durumu: { durum: string; skor: number; deger: number }
    genel_uyum_skoru: number
  }
  morfoloji_avantaji: {
    morfoloji_faktoru_etkisi: number
    dil_analizi_derinligi: string
    osym_ets_uzerindeki_avantaj: string
    ek_bilgi_boyutlari: string[]
  }
  sonuc_degerlendirmesi: string
  iyilestirme_onerileri: string[]
}

export interface AdvancedExamReport {
  sinav_id: string
  ogrenci_id: string
  rapor_tarihi: string
  temel_sonuc: any
  irt_morfoloji_analizi?: IRTAnalysis
  zpd_analizi?: ZPDAnalysis
  hibrit_ogrenme_stili_analizi?: LearningStyleAnalysis
  osym_ets_karsilastirmasi?: OSYMETSComparison
  kisisellestirilmis_oneriler: Array<{
    konu: string
    oneri_tipi: string
    aciklama: string
    oncelik: string
    tahmini_sure: string
    kaynak_onerileri: string[]
  }>
  performans_trendi: {
    son_5_sinav: number[]
    trend_yonu: string
    ortalama_artis: number
    en_iyi_performans: number
    en_dusuk_performans: number
    tutarlilik_skoru: number
  }
  gelisim_onerileri: string[]
}

class AdvancedReportsService {
  /**
   * Gelişmiş sınav raporu getir
   */
  async getAdvancedExamReport(sinavId: string): Promise<AdvancedExamReport> {
    try {
      const response = await apiClient.get(`/reports/exam/${sinavId}/advanced`)
      return response.data
    } catch (error) {
      console.error('Gelişmiş rapor getirme hatası:', error)
      throw error
    }
  }

  /**
   * IRT + Morfoloji analizi getir
   */
  async getIRTAnalysis(sinavId: string): Promise<IRTAnalysis> {
    try {
      const response = await apiClient.get(`/reports/exam/${sinavId}/irt-analysis`)
      return response.data.irt_morfoloji_analizi
    } catch (error) {
      console.error('IRT analizi getirme hatası:', error)
      throw error
    }
  }

  /**
   * ZPD önerileri getir
   */
  async getZPDRecommendations(sinavId: string): Promise<ZPDAnalysis> {
    try {
      const response = await apiClient.get(`/reports/exam/${sinavId}/zpd-recommendations`)
      return response.data.zpd_analizi
    } catch (error) {
      console.error('ZPD analizi getirme hatası:', error)
      throw error
    }
  }

  /**
   * Hibrit öğrenme stili analizi getir
   */
  async getLearningStyleAnalysis(sinavId: string): Promise<LearningStyleAnalysis> {
    try {
      const response = await apiClient.get(`/reports/exam/${sinavId}/learning-style-analysis`)
      return response.data.hibrit_ogrenme_stili_analizi
    } catch (error) {
      console.error('Öğrenme stili analizi getirme hatası:', error)
      throw error
    }
  }

  /**
   * ÖSYM/ETS karşılaştırması getir
   */
  async getOSYMETSComparison(sinavId: string): Promise<OSYMETSComparison> {
    try {
      const response = await apiClient.get(`/reports/exam/${sinavId}/osym-ets-comparison`)
      return response.data.osym_ets_karsilastirmasi
    } catch (error) {
      console.error('ÖSYM/ETS karşılaştırma hatası:', error)
      throw error
    }
  }

  /**
   * PDF rapor oluştur
   */
  async generatePDFReport(sinavId: string): Promise<{ message: string; pdf_filename: string; download_url: string }> {
    try {
      const response = await apiClient.post(`/reports/exam/${sinavId}/generate-pdf`)
      return response.data
    } catch (error) {
      console.error('PDF oluşturma hatası:', error)
      throw error
    }
  }

  /**
   * PDF rapor indir
   */
  async downloadPDFReport(filename: string): Promise<Blob> {
    try {
      const response = await apiClient.get(`/reports/download/${filename}`, {
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      console.error('PDF indirme hatası:', error)
      throw error
    }
  }
}

export const advancedReportsService = new AdvancedReportsService()