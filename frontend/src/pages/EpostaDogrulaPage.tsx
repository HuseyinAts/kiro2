import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { authService } from '../services/authService';

/**
 * Başarılı doğrulamanın sekme-ömürlü kaydı.
 *
 * NEDEN GEREKLİ (26 Ağu 2026 canlı ölçümü): token TEK KULLANIMLIK. Sayfa
 * yeniden yüklenirse aynı token'la ikinci bir `verify` gider ve backend haklı
 * olarak 400 döner — kullanıcı DOĞRULANMIŞ hesabıyla "bağlantın geçersiz"
 * okur. Ölçülen tetikleyici: service worker güncelleme yeniden yüklemesi
 * (ağ izi: 200 verify -> SW reload -> 400 verify, DB is_verified=TRUE).
 * F5 ve StrictMode çift efekti de aynı sonucu verir.
 *
 * `sessionStorage` seçildi çünkü kapsam DOĞRU: sekme kapanınca silinir,
 * başka sekmeye sızmaz. `localStorage` kalıcı olurdu (gereksiz), bileşen
 * state'i ise yeniden yüklemede zaten kayboluyor.
 *
 * Anahtar token'ın kendisini taşıyor; bu bilgi sızıntısı DEĞİL — token zaten
 * adres çubuğunda ve tarayıcı geçmişinde duruyor, üstelik kayıt yalnız
 * TÜKETİLMİŞ (artık değersiz) token için yazılıyor.
 */
const BASARI_ONEK = 'eposta-dogrulama:';

function basariMesajiniOku(token: string): string | null {
  try {
    return sessionStorage.getItem(BASARI_ONEK + token);
  } catch {
    // Gizli mod / kota: koruma kaybolur ama akış çalışmaya devam eder.
    return null;
  }
}

function basariyiYaz(token: string, mesaj: string): void {
  try {
    sessionStorage.setItem(BASARI_ONEK + token, mesaj);
  } catch {
    /* yukarıdaki gerekçe */
  }
}

/**
 * L2 — A1 altın yolunun ikinci ayağı: "e-postasını doğrular".
 *
 * Kardeş ekran `VeliOnayPage` ile aynı şekil (token query param'dan gelir,
 * uç public çünkü token'ın KENDİSİ kimliktir). Tek farkı: token tek
 * kullanımlık ve süreli olduğu için burada bir KURTARMA yolu var — süresi
 * dolmuş linkle gelen kullanıcı çıkmaza girmemeli, yeni bağlantı isteyebilmeli.
 */
export function EpostaDogrulaPage() {
  const [params] = useSearchParams();
  const [message, setMessage] = useState('Doğrulanıyor...');
  const [ok, setOk] = useState<boolean | null>(null);
  const [email, setEmail] = useState('');
  const [yenidenDurum, setYenidenDurum] = useState<string | null>(null);
  const [gonderiliyor, setGonderiliyor] = useState(false);

  // Bu MOUNT içinde hangi token'ı zaten uca yolladık. React 18 StrictMode
  // efekti iki kez koşturur (`main.tsx:58`) — bu kilit olmadan tek açılışta
  // BİLE token iki kez tüketilir ve ikinci yanıt (400) ekranı hataya çevirir.
  const yollananToken = useRef<string | null>(null);

  useEffect(() => {
    const token = params.get('token');
    if (!token) {
      setMessage('Geçersiz bağlantı (token yok).');
      setOk(false);
      return;
    }
    if (yollananToken.current === token) {
      return;
    }
    yollananToken.current = token;

    // Yeniden yükleme sonrası: bu token bu sekmede ZATEN doğrulanmışsa uca
    // dokunma. Dokunsaydık 400 alır ve başarıyı başarısızlık gibi gösterirdik.
    const oncekiBasari = basariMesajiniOku(token);
    if (oncekiBasari !== null) {
      setMessage(oncekiBasari);
      setOk(true);
      return;
    }

    authService
      .epostaDogrulaVerify(token)
      .then((res) => {
        const mesaj = res.message || 'E-posta adresiniz doğrulandı.';
        basariyiYaz(token, mesaj);
        setMessage(mesaj);
        setOk(true);
      })
      .catch((e: Error) => {
        // Başarısızlık KAYDEDİLMEZ: süresi dolmuş sanılan bir token aslında
        // ağ hatası yüzünden düşmüş olabilir; yeniden denemek meşru.
        setMessage(e.message);
        setOk(false);
      });
  }, [params]);

  const yenidenGonder = async (e: React.FormEvent) => {
    e.preventDefault();
    setGonderiliyor(true);
    try {
      const res = await authService.epostaDogrulaGonder(email);
      // Backend numaralandırmaya kapalı — mesajı OLDUĞU GİBİ gösteriyoruz.
      // "Gönderildi" yazsaydık, backend'in kasten gizlediği "bu e-posta
      // sistemde var mı" bilgisini arayüz sızdırırdı.
      setYenidenDurum(res.message);
    } catch (err) {
      setYenidenDurum((err as Error).message);
    } finally {
      setGonderiliyor(false);
    }
  };

  return (
    <div style={{ maxWidth: 480, margin: '80px auto', textAlign: 'center' }}>
      <h1>E-posta Doğrulama</h1>
      <p role="status" aria-live="polite" style={{ color: ok === false ? '#c00' : '#080' }}>
        {message}
      </p>

      {ok === true && (
        <p>
          {/* `/giris` rotası HİÇ var olmadı; giriş ekranı `/login` (App.tsx:256).
              Eski hâli catch-all'a düşüp /404 açıyordu — doğrulama başarılı olduğu
              hâlde kullanıcı çıkmaza giriyordu. Bekçi: rotaButunlugu.test.ts */}
          <a href="/login">Giriş yap</a>
        </p>
      )}

      {ok === false && (
        <form onSubmit={yenidenGonder} style={{ marginTop: 24 }}>
          <label htmlFor="dogrulama-email" style={{ display: 'block', marginBottom: 8 }}>
            Bağlantının süresi dolduysa yeni bir tane isteyin:
          </label>
          <input
            id="dogrulama-email"
            type="email"
            required
            value={email}
            onChange={(ev) => setEmail(ev.target.value)}
            placeholder="ornek@eposta.com"
            style={{ padding: 8, width: '70%' }}
          />
          <button type="submit" disabled={gonderiliyor} style={{ padding: 8, marginLeft: 8 }}>
            {gonderiliyor ? 'Gönderiliyor...' : 'Yeniden gönder'}
          </button>
          {yenidenDurum && (
            <p role="status" aria-live="polite" style={{ marginTop: 12 }}>
              {yenidenDurum}
            </p>
          )}
        </form>
      )}
    </div>
  );
}

export default EpostaDogrulaPage;
