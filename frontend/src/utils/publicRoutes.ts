/**
 * 401 sonrasi /login'e SERT yonlendirme yapilMAyacak rotalar.
 *
 * NEDEN VAR (23 Agu 2026'da olculdu — docs/audits/2026-08-23_i0_yonlendirme_kok_neden.md)
 * -------------------------------------------------------------------------------------
 * Anonim ziyaretci /eposta-dogrula'ya geldiginde hesabi DOGRULANIYOR
 * (POST verify -> 200, DB is_verified True) ama ~500ms sonra /login'e
 * firlatiliyor ve onay mesajini HIC gormuyor:
 *
 *   250ms  /eposta-dogrula  status="Dogrulaniyor..."
 *   500ms  /login           <- firlatildi
 *
 * Kanitlanmis zincir:
 *   useAccessibilitySettings.ts (her sayfada mount)
 *    -> osbService.ts:165  apiClient.get('/api/v1/osb/settings/')  -> 401
 *     -> apiClient.ts:64   interceptor -> refreshAccessToken() duser
 *      -> apiClient.ts:76-78  window.location.href = '/login'
 *
 * Karsi-olgusal: 401'ler 200'e stub'laninca sicrama KAYBOLDU, belge tek kez
 * yuklendi ve kullanici "E-posta adresiniz dogrulandi" mesajini gordu.
 *
 * Muafiyet kavrami zaten VARDI; listesinde yalniz '/login' yaziyordu ve uc
 * dosyaya kopyalanmisti, dorduncude (learningStyleService.ts) unutulmustu.
 *
 * NEDEN "ProtectedRoute ICERMEYEN HER ROTA" DEGIL
 * ------------------------------------------------
 * App.tsx'te ProtectedRoute icermeyen 14 rota var ama yalnizca 9'u anlamsal
 * olarak public. '*' (catch-all), '/', '/veli-takip', '/parent-new' KORUMALI
 * hedeflere <Navigate> ediyor. Otomatik turetme catch-all'i muaf yapar ve
 * kusuru GENISLETIRDI. Bu yuzden liste KURATORLU; kayma bekcisi
 * publicRoutes.kayma.test.ts'te uc invaryantla tutuluyor.
 */

export const PUBLIC_ROUTES = [
  '/login',
  '/register',
  '/veli-onay',
  '/eposta-dogrula',
  '/hesap-kurtarma',
  '/forgot-password',
  '/unauthorized',
  '/404',
  '/error',
] as const;

/**
 * ASCII kucultme KASITLI: `toLowerCase()` yerel-ayar BAGIMSIZDIR.
 * `toLocaleLowerCase()` Turkce ayarda 'I' -> 'ı' yapip yolu bozardi
 * (.claude/rules/case-convention.md Endpoint Gate ile ayni tuzak).
 *
 * Kucultme gerekli cunku React Router v6 eslesmesi varsayilan olarak
 * buyuk/kucuk harf DUYARSIZ: /LOGIN sayfayi acar. Liste duyarli olsaydi
 * o sayfa muaf sayilmaz ve sonsuz sicrama uretirdi.
 */
function yolNormalize(pathname: string | null | undefined): string {
  const ham = (pathname ?? '/').split('?')[0].split('#')[0].toLowerCase();
  if (ham === '') return '/';
  return ham.length > 1 && ham.endsWith('/') ? ham.slice(0, -1) : ham;
}

/** Bu yolda 401 sonrasi /login'e sert yonlendirme yapilmali mi? */
export function girisYonlendirmesiGerekli(pathname: string | null | undefined): boolean {
  return !(PUBLIC_ROUTES as readonly string[]).includes(yolNormalize(pathname));
}
