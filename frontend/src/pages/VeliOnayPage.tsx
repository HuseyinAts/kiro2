import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { authService } from '../services/authService';

export function VeliOnayPage() {
  const [params] = useSearchParams();
  const [message, setMessage] = useState('İşleniyor...');
  const [ok, setOk] = useState<boolean | null>(null);

  useEffect(() => {
    const token = params.get('token');
    const action = params.get('action');
    if (!token) {
      setMessage('Geçersiz bağlantı (token yok).');
      setOk(false);
      return;
    }
    const run =
      action === 'withdraw'
        ? authService.veliOnayWithdraw(token)
        : authService.veliOnayVerify(token);
    run
      .then((res) => {
        setMessage(res.message || 'İşlem tamamlandı.');
        setOk(true);
      })
      .catch((e: Error) => {
        setMessage(e.message);
        setOk(false);
      });
  }, [params]);

  return (
    <div style={{ maxWidth: 480, margin: '80px auto', textAlign: 'center' }}>
      <h1>Veli Onayı</h1>
      <p
        role="status"
        aria-live="polite"
        style={{ color: ok === false ? '#c00' : '#080' }}
      >
        {message}
      </p>
    </div>
  );
}

export default VeliOnayPage;
