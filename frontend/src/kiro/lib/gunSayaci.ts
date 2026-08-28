// ============================================================================
// KIRO2 — Gün sayacı (SPRINT7 §A · açık-nokta-3 çözümü)
// Tek kaynak: /me.yksTarihi. Sınav Geri Sayım ekranı bunu kullanır.
// NOT (SPRINT7 audit flag): SPEC §A satır 43 "Bugün hub'ı da aynı util'i kullanır"
// der ama Bugün'ün "tuğla"sı ÇABA metaforudur (günlük iş; "Bugünün tuğlasını koy"),
// gün-sayacı DEĞİL. Bu util yalnız Geri Sayım'da; Bugün çaba-tuğlası korunur.
// Motor değil (düz takvim farkı) → istemcide hesaplanabilir (kanon ihlali değil).
// ============================================================================

function gunBasi(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

/** Sınava kalan gün: ceil((yksTarihi − bugün) / 1 gün). bugun test için enjekte edilebilir. */
export function gunKalan(yksTarihi: string, bugun: Date = new Date()): number {
  const yks = new Date(yksTarihi + 'T00:00:00');
  const fark = yks.getTime() - gunBasi(bugun).getTime();
  return Math.max(0, Math.ceil(fark / 86_400_000));
}

/** Sınava kalan (yukarı yuvarlanmış) hafta. DC birebir alt-sınır: en az 1 (sınav günü de "1 hafta"). */
export function haftaKalan(yksTarihi: string, bugun?: Date): number {
  return Math.max(1, Math.ceil(gunKalan(yksTarihi, bugun) / 7));
}
