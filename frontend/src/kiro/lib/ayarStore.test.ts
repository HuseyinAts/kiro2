import { beforeEach, afterEach, describe, it, expect, vi } from 'vitest';

import { useAyar, ayarDefaults, resetAyar } from './ayarStore';

// Store global — persist sızıntısını önlemek için her testte reset.
beforeEach(() => resetAyar());
afterEach(() => resetAyar());

describe('ayarStore', () => {
  it('varsayılan değerleri taşır', () => {
    const s = useAyar.getState();
    expect(s.dailyGoalMinutes).toBe(30);
    expect(s.bildirim).toEqual({
      fsrs: true,
      zayifKonu: true,
      seri: true,
      duello: true,
      basarim: true,
    });
    expect(s.calmMode).toBe(false);
    expect(s.hideRanking).toBe(false);
  });

  it('ayarDefaults sabiti default veriyi yansıtır', () => {
    expect(ayarDefaults.dailyGoalMinutes).toBe(30);
    expect(ayarDefaults.bildirim.basarim).toBe(true);
    expect(ayarDefaults.hideRanking).toBe(false);
  });

  it('setDailyGoal günlük hedefi günceller', () => {
    useAyar.getState().setDailyGoal(45);
    expect(useAyar.getState().dailyGoalMinutes).toBe(45);
  });

  it('toggleBildirim yalnız verilen anahtarı çevirir', () => {
    useAyar.getState().toggleBildirim('duello');
    const b = useAyar.getState().bildirim;
    expect(b.duello).toBe(false);
    expect(b.fsrs).toBe(true);
    expect(b.seri).toBe(true);
  });

  it('setCalmMode ve setHideRanking bayrakları günceller', () => {
    useAyar.getState().setCalmMode(true);
    useAyar.getState().setHideRanking(true);
    expect(useAyar.getState().calmMode).toBe(true);
    expect(useAyar.getState().hideRanking).toBe(true);
  });

  it('resetAyar durumu default yapar ve persist anahtarını temizler', () => {
    useAyar.getState().setDailyGoal(90);
    useAyar.getState().toggleBildirim('seri');
    useAyar.getState().setCalmMode(true);

    // localStorage bu ortamda mock'lu (setup.ts) — persist temizliğini
    // removeItem çağrısıyla doğrula (değer okuma anlamsız).
    const removeSpy = vi.spyOn(localStorage, 'removeItem');
    resetAyar();
    expect(removeSpy).toHaveBeenCalledWith('kiro-ayar');
    removeSpy.mockRestore();

    const s = useAyar.getState();
    expect(s.dailyGoalMinutes).toBe(30);
    expect(s.bildirim.seri).toBe(true);
    expect(s.calmMode).toBe(false);
  });
});
