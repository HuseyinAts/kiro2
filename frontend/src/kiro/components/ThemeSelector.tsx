import { useState, useRef, useEffect } from 'react';
import { useAyar, KulturelTema } from '../lib/ayarStore';
import { font, shadow, radius, color } from '../tokens';

const TEMALAR: { id: KulturelTema; ad: string; desc: string; icon: string; bg: string; fg: string }[] = [
  { id: 'varsayilan', ad: 'Varsayılan', desc: 'Klasik KIRO2 Teması', icon: '🌌', bg: '#150E20', fg: '#F1E9F2' },
  { id: 'cezeri', ad: 'Cezeri\'nin Çarkları', desc: 'Mühendislik & Mekanik', icon: '⚙️', bg: '#221A15', fg: '#C5832B' },
  { id: 'fergani', ad: 'Fergani\'nin Gök Küresi', desc: 'Derin Uzay & Vizyon', icon: '🔭', bg: '#0A1128', fg: '#FCD34D' },
  { id: 'harezmi', ad: 'Harezmi\'nin Algoritması', desc: 'Saf Mantık & Geometri', icon: '📐', bg: '#121217', fg: '#00F0FF' },
  { id: 'killigil', ad: 'Killigil İradesi', desc: 'Çelik & Taktiksel Disiplin', icon: '🛡️', bg: '#1E1E1E', fg: '#D32F2F' },
  { id: 'ebru', ad: 'Ebru\'nun Akışı', desc: 'Zarafet & Esneklik', icon: '🎨', bg: '#342D3C', fg: '#B59CDA' },
  { id: 'ibnisina', ad: 'İbni Sina (El-Kanun)', desc: 'Tıp & Felsefe', icon: '🌿', bg: '#0A1A12', fg: '#2DD4A7' },
  { id: 'farabi', ad: 'Farabi (Muallim-i Sani)', desc: 'Felsefe & Uyum', icon: '🎶', bg: '#0F1626', fg: '#E3C263' },
  { id: 'biruni', ad: 'Biruni', desc: 'Yer Bilimleri & Astronomi', icon: '🌍', bg: '#1A1813', fg: '#4DB8B8' },
  { id: 'pirireis', ad: 'Piri Reis', desc: 'Haritacılık & Okyanus', icon: '🧭', bg: '#0B1C24', fg: '#66E0C2' },
  { id: 'evliyacelebi', ad: 'Evliya Çelebi', desc: 'Seyahat & Keşif', icon: '📜', bg: '#241B18', fg: '#D49A89' },
  { id: 'sairnabi', ad: 'Şair Nabi', desc: 'Divan & Hikmet', icon: '🪶', bg: '#1B0F1C', fg: '#C792EA' },
  { id: 'alikuscu', ad: 'Ali Kuşçu', desc: 'Ay Haritası & Matematik', icon: '🌙', bg: '#101216', fg: '#A3B8CC' },
  { id: 'vecihi', ad: 'Vecihi Hürkuş', desc: 'Havacılık & Cesaret', icon: '🛩️', bg: '#101B26', fg: '#7FB0FF' },
  { id: 'mimarsinan', ad: 'Mimar Sinan', desc: 'Mimari & Simetri', icon: '🏛️', bg: '#1A1C1C', fg: '#D1D5DB' },
  { id: 'bayraktar', ad: 'Selçuk Bayraktar', desc: 'Milli Teknoloji & İHA', icon: '✈️', bg: '#120A0A', fg: '#EF4444' },
  { id: 'azizsancar', ad: 'Aziz Sancar', desc: 'DNA Onarımı & Biyokimya', icon: '🧬', bg: '#0B1A1E', fg: '#1FB683' },
  { id: 'cahitarf', ad: 'Cahit Arf', desc: 'Arf Değişmezi & Topoloji', icon: '♾️', bg: '#12121A', fg: '#A78BFA' },
  { id: 'oktaysinanoglu', ad: 'Oktay Sinanoğlu', desc: 'Biyofizik & Kimya', icon: '⚛️', bg: '#221100', fg: '#FB923C' },
  { id: 'hulusibehcet', ad: 'Hulusi Behçet', desc: 'Tıp & Dermatoloji', icon: '🩸', bg: '#240F11', fg: '#F43F5E' },
  { id: 'canandagdeviren', ad: 'Canan Dağdeviren', desc: 'Biyomedikal & Malzeme', icon: '💓', bg: '#26141E', fg: '#F472B6' },
  { id: 'feryalozel', ad: 'Feryal Özel', desc: 'Kara Delikler & Astrofizik', icon: '🌌', bg: '#050505', fg: '#F97316' },
  { id: 'bilgedemirkoz', ad: 'Bilge Demirköz', desc: 'Yüksek Enerji & CERN', icon: '🛰️', bg: '#081226', fg: '#38BDF8' },
  { id: 'meteatature', ad: 'Mete Atatüre', desc: 'Kuantum Fiziği', icon: '💡', bg: '#1A1C08', fg: '#FDE047' },
  { id: 'gaziyasargil', ad: 'Gazi Yaşargil', desc: 'Nöroşirürji & Mikrocerrahi', icon: '🧠', bg: '#17101B', fg: '#E879F9' },
  { id: 'behramkursunoglu', ad: 'Behram Kurşunoğlu', desc: 'Teorik Fizik', icon: '📐', bg: '#0C0C11', fg: '#9CA3AF' },
  { id: 'nuzhetgokdogan', ad: 'Nüzhet Gökdoğan', desc: 'Astronom & Gözlemevi', icon: '🔭', bg: '#0E1526', fg: '#818CF8' },
  { id: 'halilinalcik', ad: 'Halil İnalcık', desc: 'Tarihçilerin Kutbu', icon: '📚', bg: '#260B12', fg: '#FCD34D' },
  { id: 'ilberortayli', ad: 'İlber Ortaylı', desc: 'Tarih Havası', icon: '🕰️', bg: '#1F1813', fg: '#D4A373' },
  { id: 'ulugbey', ad: 'Uluğ Bey', desc: 'Semerkant & Astronomi', icon: '🌠', bg: '#0A0C22', fg: '#60A5FA' },
  { id: 'elbuzcani', ad: 'Ebül Vefa el-Buzcani', desc: 'Trigonometri', icon: '📐', bg: '#0E1C18', fg: '#34D399' },
  { id: 'cemsid', ad: 'Gıyaseddin Cemşid', desc: 'Matematik & Pi', icon: '🧮', bg: '#0A1C12', fg: '#22C55E' },
  { id: 'hazini', ad: 'Hâzinî', desc: 'Hidrostatik & Mizan', icon: '⚖️', bg: '#0D1A26', fg: '#38BDF8' },
  { id: 'cabirbinhayyan', ad: 'Cabir bin Hayyan', desc: 'Kimya & Simya', icon: '🧪', bg: '#122615', fg: '#4ADE80' },
  { id: 'errazi', ad: 'Ebubekir er-Razi', desc: 'Klinik Tıp & Kimya', icon: '🥼', bg: '#1B1024', fg: '#C084FC' },
  { id: 'seydialireis', ad: 'Seydi Ali Reis', desc: 'Navigasyon & Okyanus', icon: '⛵', bg: '#061924', fg: '#06B6D4' },
  { id: 'lagari', ad: 'Lagari Hasan Çelebi', desc: 'Roket & İtki', icon: '🚀', bg: '#26120D', fg: '#FB7185' },
  { id: 'hezarfen', ad: 'Hezarfen Ahmed Çelebi', desc: 'Kanat & Uçuş', icon: '🦅', bg: '#101B24', fg: '#94A3B8' },
  { id: 'yusufhashacib', ad: 'Yusuf Has Hacib', desc: 'Kutadgu Bilig', icon: '📖', bg: '#0C1C1D', fg: '#2DD4A7' },
  { id: 'asikpasazade', ad: 'Aşıkpaşazade', desc: 'Tarihsel Kayıt', icon: '✒️', bg: '#171510', fg: '#EAB308' },
  { id: 'yanyaliesad', ad: 'Yanyalı Esad Efendi', desc: 'Felsefe Çevirileri', icon: '🏛️', bg: '#1B1C22', fg: '#A3A3A3' }
];

export function ThemeSelector() {
  const [acik, setAcik] = useState(false);
  const kulturelTema = useAyar((s) => s.kulturelTema);
  const setKulturelTema = useAyar((s) => s.setKulturelTema);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setAcik(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const aktif = TEMALAR.find((t) => t.id === kulturelTema) || TEMALAR[0];

  return (
    <div style={{ position: 'relative', display: 'inline-block' }} ref={menuRef}>
      <button
        onClick={() => setAcik((v) => !v)}
        style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          background: 'var(--k-surface-subtle, rgba(255,255,255,0.05))', border: `1px solid var(--k-border, rgba(255,255,255,0.1))`,
          padding: '6px 12px', borderRadius: radius.pill,
          color: 'var(--k-text, #fff)', fontFamily: font.sans, fontWeight: 600, fontSize: '13px',
          cursor: 'pointer', transition: 'background 0.2s',
        }}
      >
        <span>{aktif.icon}</span>
        <span>{aktif.ad}</span>
      </button>

      {acik && (
        <div
          style={{
            position: 'absolute', top: '100%', right: 0, marginTop: '8px',
            width: '280px', maxHeight: '420px', overflowY: 'auto',
            background: 'var(--k-surface, #150E20)', border: '1px solid var(--k-border)',
            borderRadius: radius.card, padding: '8px', boxShadow: shadow.cardFloat,
            zIndex: 100, display: 'flex', flexDirection: 'column', gap: '4px'
          }}
        >
          <div style={{ padding: '8px', fontSize: '11px', fontWeight: 800, color: 'var(--k-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Zihinsel Frekans (Tema)
          </div>
          {TEMALAR.map((t) => {
            const isSelected = t.id === kulturelTema;
            return (
              <button
                key={t.id}
                onClick={() => { setKulturelTema(t.id); setAcik(false); }}
                style={{
                  display: 'flex', alignItems: 'center', gap: '12px',
                  background: isSelected ? color.paper.card : 'transparent',
                  border: 'none', padding: '10px 12px', borderRadius: radius.button,
                  textAlign: 'left', cursor: 'pointer', transition: 'background 0.15s',
                  color: isSelected ? 'var(--k-text)' : 'var(--k-text-2)',
                }}
              >
                <div style={{
                  width: '32px', height: '32px', borderRadius: '8px', flexShrink: 0,
                  background: t.bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  border: `2px solid ${isSelected ? t.fg : 'transparent'}`,
                  fontSize: '16px'
                }}>
                  {t.icon}
                </div>
                <div>
                  <div style={{ fontFamily: font.sans, fontSize: '13.5px', fontWeight: 700, color: isSelected ? t.fg : 'var(--k-text)' }}>
                    {t.ad}
                  </div>
                  <div style={{ fontFamily: font.sans, fontSize: '11px', fontWeight: 500, color: 'var(--k-text-muted)' }}>
                    {t.desc}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
