/**
 * KiroDestanPage — /kiro-destan
 * 12 Turk/Anadolu donemi x YKS dersleri interaktif harita.
 */
import { useEffect, useState } from 'react';
import {
  Box, Card, CardContent, Chip, Dialog, DialogContent,
  DialogTitle, Grid, IconButton, LinearProgress,
  Stack, Tooltip, Typography,
} from '@mui/material';
import { Close, PlayArrow, Star } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { apiRequest } from '../utils/apiHelpers';

interface Donem {
  id: string; ad: string; yil: string;
  ders: string; dersAd: string;
  renk: string; acikRenk: string;
  emoji: string; npc: string; hikaye: string;
}

const DONEM_EMOJI: Record<string, string> = {
  swords:'⚔️', bow:'🏹', moon:'🌙', scroll:'📜', mosque:'🕌',
  lab:'⚗️', castle:'🏰', map:'🗺️', plant:'🌿', pen:'🖊️',
  scale:'⚖️', star:'🌟',
};

const DONEMLER: Donem[] = [
  { id:'orta-asya', ad:'Orta Asya Bozkiri', yil:'MS 552-744', ders:'mat',
    dersAd:'Matematik', renk:'#1565c0', acikRenk:'#e3f2fd', emoji:'swords',
    npc:'Bilge Kagan', hikaye:'Goktürk yazitlarinda matematiksel hesaplar gizlidir. Bilge Kagan izinde sayi sirlarini coz.' },
  { id:'hunlar', ad:'Hun Imparatorlugu', yil:'MO 209-MS 48', ders:'fen',
    dersAd:'Fen Bilimleri', renk:'#880e4f', acikRenk:'#fce4ec', emoji:'bow',
    npc:'Mete Han', hikaye:'Fen gucu ile ok yapiminda fizik ve kimya gizlidir. Hun bilgeligini kesfet.' },
  { id:'goktürkler', ad:'Goktürk Kaganlik', yil:'552-744', ders:'fizik',
    dersAd:'Fizik', renk:'#4a148c', acikRenk:'#f3e5f5', emoji:'moon',
    npc:'Kültigin', hikaye:'Atli okculugun fizigini, yayin gerilimini ve okun balistik gücünü anla.' },
  { id:'uygurlar', ad:'Uygur Kaganlik', yil:'744-840', ders:'turkce',
    dersAd:'Türkce', renk:'#1b5e20', acikRenk:'#e8f5e9', emoji:'scroll',
    npc:'Alp Er Tunga', hikaye:'Türkce ilk yazili destanlar. Dilin köküne in, sözcüklerin gücünü kesfet.' },
  { id:'selcuklular', ad:'Büyük Selcuklu', yil:'1037-1194', ders:'mat',
    dersAd:'Geometri', renk:'#e65100', acikRenk:'#fff3e0', emoji:'mosque',
    npc:'Nizamülmülk', hikaye:'Selcuklu mimarisinin geometrik sirlari — kubbelerde gizli matematik.' },
  { id:'beylikler', ad:'Anadolu Beylikleri', yil:'1243-1300', ders:'kimya',
    dersAd:'Kimya', renk:'#006064', acikRenk:'#e0f7fa', emoji:'lab',
    npc:'Ahi Evran', hikaye:'Ahi teskilatinin zanaat kimyasi — metal isleme, boyama ve ilac yapimi.' },
  { id:'osmkuruluş', ad:'Osmanli Kurulus', yil:'1299-1453', ders:'tarih1',
    dersAd:'Tarih', renk:'#bf360c', acikRenk:'#fbe9e7', emoji:'castle',
    npc:'Osman Gazi', hikaye:'Osmanli kurulus sirri: uc beylikler, akinci ve devlet insasi.' },
  { id:'osmyüksek', ad:'Osmanli Yükselis', yil:'1453-1566', ders:'cografya1',
    dersAd:'Cografya', renk:'#1a237e', acikRenk:'#e8eaf6', emoji:'map',
    npc:'Piri Reis', hikaye:'Piri Reis haritalarinda gizlenen cografya bilimi. Okyanus sirlari.' },
  { id:'osmdurak', ad:'Osmanli Duraklama', yil:'1566-1699', ders:'biyoloji',
    dersAd:'Biyoloji', renk:'#33691e', acikRenk:'#f1f8e9', emoji:'plant',
    npc:'Evliya Celebi', hikaye:'Seyahatname bitkiler ve hayvanlar. Osmanli doga bilimi.' },
  { id:'osmgerileme', ad:'Osmanli Gerileme', yil:'1699-1789', ders:'edebiyat',
    dersAd:'Edebiyat', renk:'#4e342e', acikRenk:'#efebe9', emoji:'pen',
    npc:'Nedim', hikaye:'Lale devri siirinin derinligi. Divan edebiyatinin zirvesi.' },
  { id:'tanzimat', ad:'Tanzimat Donemi', yil:'1839-1876', ders:'sosyal',
    dersAd:'Sosyal Bil.', renk:'#37474f', acikRenk:'#eceff1', emoji:'scale',
    npc:'Mustafa Resit Pasa', hikaye:'Modern devletin temelleri: hukuk, egitim ve sosyal degisim.' },
  { id:'cumhuriyet', ad:'Türkiye Cumhuriyeti', yil:'1923-', ders:'turkce',
    dersAd:'TYT Genel', renk:'#b71c1c', acikRenk:'#ffebee', emoji:'star',
    npc:'Ataturk', hikaye:'Tüm derslerin doruk noktasi. Cumhuriyetin bilgi mirasi.' },
];

function thetaToStars(theta: number): number {
  if (theta >= 1.5) return 5;
  if (theta >= 0.5) return 4;
  if (theta >= -0.5) return 3;
  if (theta >= -1.5) return 2;
  return 1;
}

function DonemKart({ donem, theta, onClick }: {
  donem: Donem; theta: number | null; onClick: () => void;
}) {
  const locked = theta === null;
  const stars  = theta !== null ? thetaToStars(theta) : 0;
  const pct    = theta !== null ? Math.min(100, Math.max(0, ((theta+3)/6)*100)) : 0;
  const emoji  = DONEM_EMOJI[donem.emoji] ?? '🌟';

  return (
    <Card onClick={locked ? undefined : onClick} sx={{
      borderRadius:3, cursor: locked ? 'default' : 'pointer',
      border:`2px solid ${locked ? '#ddd' : donem.renk}`,
      bgcolor: locked ? '#f5f5f5' : donem.acikRenk, opacity: locked ? 0.7 : 1,
      transition:'all 0.2s',
      '&:hover': locked ? {} : { transform:'translateY(-3px)', boxShadow:4 },
    }}>
      <CardContent sx={{ p:2, '&:last-child':{pb:2} }}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <Typography fontSize={28}>{locked ? '🔒' : emoji}</Typography>
          {!locked && (
            <Stack direction="row">
              {Array(5).fill(0).map((_,i) => (
                <Star key={i} sx={{ fontSize:14, color: i<stars ? donem.renk : '#e0e0e0' }} />
              ))}
            </Stack>
          )}
        </Stack>
        <Typography variant="subtitle2" fontWeight={700} mt={0.5}
          color={locked ? 'text.disabled' : donem.renk}>{donem.ad}</Typography>
        <Typography variant="caption" color="text.secondary">{donem.yil}</Typography>
        <Box mt={1}>
          <Chip size="small" label={donem.dersAd}
            sx={{ bgcolor: locked ? '#eee' : donem.renk, color: locked ? '#999' : '#fff', fontSize:11 }} />
        </Box>
        {!locked && (
          <LinearProgress variant="determinate" value={pct}
            sx={{ mt:1.5, height:4, borderRadius:2,
              '& .MuiLinearProgress-bar':{ bgcolor:donem.renk } }} />
        )}
        {locked && (
          <Typography variant="caption" color="text.disabled" display="block" mt={1}>
            CAT testi yap, kilidi ac
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}

function NPCDialog({ donem, theta, onClose, onStart }: {
  donem: Donem; theta: number | null;
  onClose: () => void; onStart: (d: Donem) => void;
}) {
  const stars = theta !== null ? thetaToStars(theta) : 0;
  const emoji = DONEM_EMOJI[donem.emoji] ?? '🌟';
  return (
    <Dialog open maxWidth="sm" fullWidth onClose={onClose}>
      <DialogTitle sx={{ bgcolor:donem.renk, color:'#fff', pb:1 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Stack direction="row" spacing={1.5} alignItems="center">
            <Typography fontSize={32}>{emoji}</Typography>
            <Box>
              <Typography fontWeight={700}>{donem.ad}</Typography>
              <Typography variant="caption" sx={{ opacity:0.85 }}>{donem.yil}</Typography>
            </Box>
          </Stack>
          <IconButton onClick={onClose} sx={{ color:'#fff' }}><Close /></IconButton>
        </Stack>
      </DialogTitle>
      <DialogContent sx={{ pt:3 }}>
        <Stack direction="row" spacing={2} alignItems="flex-start" mb={2}>
          <Box sx={{ width:52, height:52, borderRadius:'50%', bgcolor:donem.renk,
            display:'flex', alignItems:'center', justifyContent:'center', fontSize:26, flexShrink:0 }}>
            🧙
          </Box>
          <Box sx={{ bgcolor:donem.acikRenk, p:2, borderRadius:2, flex:1 }}>
            <Typography variant="caption" fontWeight={700} color={donem.renk}>
              {donem.npc} — Bilge Alp
            </Typography>
            <Typography variant="body2" mt={0.5}>{donem.hikaye}</Typography>
          </Box>
        </Stack>
        <Stack direction="row" spacing={2} mb={2}>
          <Chip label={donem.dersAd} sx={{ bgcolor:donem.renk, color:'#fff' }} />
          {theta !== null && (
            <Stack direction="row" spacing={0.3}>
              {Array(5).fill(0).map((_,i) => (
                <Star key={i} sx={{ color: i<stars ? donem.renk : '#e0e0e0' }} />
              ))}
            </Stack>
          )}
          {theta !== null && (
            <Typography variant="body2" color="text.secondary">
              theta = {theta.toFixed(2)}
            </Typography>
          )}
        </Stack>
        <Stack direction="row" spacing={1.5} justifyContent="flex-end">
          <Chip icon={<PlayArrow />} label="Adaptif Test Basla" clickable
            onClick={() => onStart(donem)}
            sx={{ bgcolor:donem.renk, color:'#fff',
              '&:hover':{ bgcolor:donem.renk, filter:'brightness(0.9)' } }} />
        </Stack>
      </DialogContent>
    </Dialog>
  );
}

export default function KiroDestanPage() {
  const navigate = useNavigate();
  const [thetaMap, setThetaMap] = useState<Record<string, number>>({});
  const [selected, setSelected] = useState<Donem | null>(null);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    apiRequest<{ders_kodu:string; theta:number}[]>('/api/v1/estimate/thetas')
      .then(arr => {
        const m: Record<string, number> = {};
        arr.forEach(d => { m[d.ders_kodu] = d.theta; });
        setThetaMap(m);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleStart = (donem: Donem) => {
    setSelected(null);
    navigate(`/cat?subject=${donem.ders}`);
  };

  const unlockedCount = DONEMLER.filter(d => thetaMap[d.ders] !== undefined).length;
  const totalStars = DONEMLER.reduce((acc, d) => {
    const t = thetaMap[d.ders];
    return acc + (t !== undefined ? thetaToStars(t) : 0);
  }, 0);

  return (
    <Box sx={{ pb:6 }}>
      <Box sx={{ background:'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        color:'#fff', py:4, px:3, mb:4 }}>
        <Typography variant="h4" fontWeight={800} mb={1}>⚔️ KIRO Destani</Typography>
        <Typography variant="body1" sx={{ opacity:0.85, mb:2 }}>
          12 Türk ve Anadolu dönemi — her biri bir YKS dersi. Bilge Alpler rehberlik eder.
        </Typography>
        <Stack direction="row" spacing={2}>
          <Chip label={`${unlockedCount}/12 Bolge Acik`}
            sx={{ bgcolor:'rgba(255,255,255,0.15)', color:'#fff' }} />
          <Chip label={`${totalStars}/${12*5} Yildiz`}
            sx={{ bgcolor:'rgba(255,255,255,0.15)', color:'#fff' }}
            icon={<Star sx={{ color:'#ffd700 !important' }} />} />
        </Stack>
        {loading && <LinearProgress sx={{ mt:2, bgcolor:'rgba(255,255,255,0.2)' }} />}
      </Box>

      <Box px={3}>
        <Grid container spacing={2}>
          {DONEMLER.map(donem => {
            const theta = thetaMap[donem.ders] ?? null;
            return (
              <Grid item xs={12} sm={6} md={4} key={donem.id}>
                <Tooltip
                  title={theta === null ? `${donem.dersAd} icin CAT testi yap` : donem.npc}
                  placement="top"
                >
                  <Box>
                    <DonemKart donem={donem} theta={theta} onClick={() => setSelected(donem)} />
                  </Box>
                </Tooltip>
              </Grid>
            );
          })}
        </Grid>
        <Box mt={4} p={2} bgcolor="action.hover" borderRadius={2}>
          <Typography variant="body2" color="text.secondary">
            Her bolge icin ilgili derste CAT veya Seviye Tespiti tamamla. Yildiz sayini theta degerine gore belirlenir.
          </Typography>
        </Box>
      </Box>

      {selected && (
        <NPCDialog
          donem={selected}
          theta={thetaMap[selected.ders] ?? null}
          onClose={() => setSelected(null)}
          onStart={handleStart}
        />
      )}
    </Box>
  );
}
