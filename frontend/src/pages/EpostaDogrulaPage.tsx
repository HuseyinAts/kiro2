import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { authService } from '../services/authService';

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

  useEffect(() => {
    const token = params.get('token');
    if (!token) {
      setMessage('Geçersiz bağlantı (token yok).');
      setOk(false);
      return;
    }
    authService
      .epostaDogrulaVerify(token)
      .then((res) => {
        setMessage(res.message || 'E-posta adresiniz doğrulandı.');
        setOk(true);
      })
      .catch((e: Error) => {
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
