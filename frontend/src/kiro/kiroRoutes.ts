// ============================================================================
// KIRO2 — Kiro tam-ekran (full-bleed) rota kaydı (Faz 4 F4-S1)
// Bu yollardaki kiro ekranları App'in RoleBasedLayout kabuğunu (ModernNavigation +
// header + toolbar) BYPASS eder — ekran KENDİ tema/SideNav'ını (KiroThemeProvider)
// getirir ve tüm ekranı kaplar. Yeni bir kiro ekranı full-bleed mount edilecekse:
//   1. App.tsx <Routes>'a <Route path> ekle (ProtectedRoute ile),
//   2. yolunu BURAYA ekle (RoleBasedLayout tek-kaynak burayı okur).
// İkisi birlikte güncellenir; aksi halde ya kabuk-içi (unutulmuş) ya çıplak-yetkisiz kalır.
// ============================================================================

/** Kiro full-bleed (App kabuğu bypass) rotaları. */
export const KIRO_FULLBLEED_ROUTES: readonly string[] = ['/duel', '/chat', '/sokratik', '/login', '/offline', '/interaktif-cozum'];

/** pathname bir kiro full-bleed rotası mı (exact eşleşme veya alt-yol, ör. /duel/123). */
export function isKiroFullBleed(pathname: string): boolean {
  return KIRO_FULLBLEED_ROUTES.some((p) => pathname === p || pathname.startsWith(p + '/'));
}
