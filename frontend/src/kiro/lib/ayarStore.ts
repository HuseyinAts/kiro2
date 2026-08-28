// ============================================================================
// KIRO2 — Kullanıcı Ayar Store'u (SPRINT10-C)
// Ayarlar ekranının tek durum kaynağı. Zustand + persist (localStorage).
// Kültürel Tema Motoru (Theme Engine) eklendi: Zihinsel gelişim evreleri.
// ============================================================================
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/** Bildirim türü aç/kapa bayrakları. */
export interface BildirimAyar {
  /** FSRS tekrar hatırlatması */
  fsrs: boolean;
  /** Zayıf konu uyarısı */
  zayifKonu: boolean;
  /** Seri (streak) hatırlatması */
  seri: boolean;
  /** Düello daveti / sonucu */
  duello: boolean;
  /** Başarım (rozet) bildirimi */
  basarim: boolean;
}

export type KulturelTema = 'varsayilan' | 'cezeri' | 'harezmi' | 'fergani' | 'killigil' | 'ebru'
  | 'ibnisina' | 'farabi' | 'biruni' | 'pirireis' | 'evliyacelebi' | 'sairnabi' | 'alikuscu' | 'vecihi'
  | 'mimarsinan' | 'bayraktar' | 'azizsancar' | 'cahitarf' | 'oktaysinanoglu' | 'hulusibehcet' | 'canandagdeviren'
  | 'feryalozel' | 'bilgedemirkoz' | 'meteatature' | 'gaziyasargil' | 'behramkursunoglu' | 'nuzhetgokdogan'
  | 'halilinalcik' | 'ilberortayli' | 'ulugbey' | 'elbuzcani' | 'cemsid' | 'hazini' | 'cabirbinhayyan'
  | 'errazi' | 'seydialireis' | 'lagari' | 'hezarfen' | 'yusufhashacib' | 'asikpasazade' | 'yanyaliesad';

/** Ayar durumu (veri) + eylemler (setter'lar). */
export interface KullaniciAyar {
  kulturelTema: KulturelTema;
  dailyGoalMinutes: number;
  bildirim: BildirimAyar;
  calmMode: boolean;
  hideRanking: boolean;
  setDailyGoal: (n: number) => void;
  toggleBildirim: (key: keyof BildirimAyar) => void;
  setCalmMode: (v: boolean) => void;
  setHideRanking: (v: boolean) => void;
  setKulturelTema: (t: KulturelTema) => void;
}

/** Yalnız veri alanları (setter'lar hariç). */
type AyarVeri = Pick<KullaniciAyar, 'kulturelTema' | 'dailyGoalMinutes' | 'bildirim' | 'calmMode' | 'hideRanking'>;

const STORAGE_KEY = 'kiro-ayar';

/** Her çağrıda taze default nesne (paylaşılan referans sızıntısı yok). */
function varsayilanVeri(): AyarVeri {
  return {
    kulturelTema: 'varsayilan',
    dailyGoalMinutes: 30,
    bildirim: { fsrs: true, zayifKonu: true, seri: true, duello: true, basarim: true },
    calmMode: false,
    hideRanking: false,
  };
}

/** Salt-okunur default anlık görüntüsü (ekran/varsayılan referansı için). */
export const ayarDefaults: AyarVeri = varsayilanVeri();

export const useAyar = create<KullaniciAyar>()(
  persist(
    (set) => ({
      ...varsayilanVeri(),
      setDailyGoal: (n) => set({ dailyGoalMinutes: n }),
      toggleBildirim: (key) =>
        set((s) => ({ bildirim: { ...s.bildirim, [key]: !s.bildirim[key] } })),
      setCalmMode: (v) => set({ calmMode: v }),
      setHideRanking: (v) => set({ hideRanking: v }),
      setKulturelTema: (t) => set({ kulturelTema: t }),
    }),
    {
      name: STORAGE_KEY,
      partialize: (s): AyarVeri => ({
        kulturelTema: s.kulturelTema,
        dailyGoalMinutes: s.dailyGoalMinutes,
        bildirim: s.bildirim,
        calmMode: s.calmMode,
        hideRanking: s.hideRanking,
      }),
    }
  )
);

/** Durumu default'a döndürür + persist edilmiş localStorage anahtarını temizler.
 *  Store global olduğundan testlerde beforeEach/afterEach ile çağır. */
export function resetAyar(): void {
  useAyar.setState(varsayilanVeri());
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // jsdom/SSR ortamında localStorage yoksa sessiz geç
  }
}
