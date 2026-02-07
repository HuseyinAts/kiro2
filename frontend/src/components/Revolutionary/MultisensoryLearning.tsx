/**
 * Multisensory Learning Component - Çoklu Duyusal Öğrenme
 * Task 82: Çoklu Duyusal Öğrenme (REQ-50.89 - REQ-50.104)
 */

import {
  Visibility as VisualIcon,
  Hearing as AudioIcon,
  TouchApp as KinestheticIcon,
  Animation as AnimationIcon,
  VideoLibrary as VideoIcon,
  ViewInAr as VRIcon,
  PlayArrow, Pause, Replay, Speed,
} from '@mui/icons-material';
import {
  Box, Card, CardContent, Typography, Tabs, Tab,
  Button, Grid, Chip, IconButton, Tooltip, LinearProgress,
} from '@mui/material';
import * as React from 'react';
import {  useState  } from 'react';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const MultisensoryLearning: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [animationPlaying, setAnimationPlaying] = useState(false);
  const [animationSpeed, setAnimationSpeed] = useState(1.0);
  const [videoSpeed, setVideoSpeed] = useState(1.0);

  // REQ-50.95: Animation control
  const handleAnimationControl = async (action: string) => {
    try {
      const response = await fetch('/api/v1/multisensory/animations/demo/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      });
      if (response.ok) {
        if (action === 'play') {setAnimationPlaying(true);}
        if (action === 'pause') {setAnimationPlaying(false);}
      }
    } catch (error) {
      console.error('Animation control failed:', error);
    }
  };

  // REQ-50.96: Animation speed
  const handleAnimationSpeed = async (speed: number) => {
    try {
      await fetch(`/api/v1/multisensory/animations/demo/speed?speed=${speed}`, {
        method: 'PATCH',
      });
      setAnimationSpeed(speed);
    } catch (error) {
      console.error('Speed change failed:', error);
    }
  };

  return (
    <Box sx={{ width: '100%', p: 2 }}>
      {/* Header */}
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <CardContent>
          <Typography variant="h4" sx={{ color: 'white', fontWeight: 'bold', mb: 1 }}>
            🎭 Çoklu Duyusal Öğrenme
          </Typography>
          <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.9)' }}>
            Görsel, işitsel ve kinestetik öğrenme deneyimleri
          </Typography>
        </CardContent>
      </Card>

      {/* Learning Modalities */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', borderLeft: '4px solid #4A90E2' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <VisualIcon sx={{ color: '#4A90E2', mr: 1 }} />
                <Typography variant="h6">Görsel</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Diyagramlar, infografikler, renkli görseller
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', borderLeft: '4px solid #50C878' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AudioIcon sx={{ color: '#50C878', mr: 1 }} />
                <Typography variant="h6">İşitsel</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Sesli anlatım, müzik, ses efektleri
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', borderLeft: '4px solid #FFB347' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <KinestheticIcon sx={{ color: '#FFB347', mr: 1 }} />
                <Typography variant="h6">Kinestetik</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Sürükle-bırak, dokunmatik, interaktif
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={(_e, v) => setActiveTab(v)} variant="fullWidth">
            <Tab icon={<AnimationIcon />} label="Animasyonlar" />
            <Tab icon={<VideoIcon />} label="Videolar" />
            <Tab icon={<VRIcon />} label="VR/AR" />
          </Tabs>
        </Box>

        {/* Animations Tab (REQ-50.93-96) */}
        <TabPanel value={activeTab} index={0}>
          <Typography variant="h6" sx={{ mb: 2 }}>🎬 İnteraktif Animasyonlar</Typography>

          <Card sx={{ mb: 2, bgcolor: '#f5f5f5' }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Hücre Bölünmesi
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Mitoz bölünmenin adım adım animasyonu
              </Typography>

              {/* Animation Controls */}
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Tooltip title="Oynat">
                  <IconButton
                    color="primary"
                    onClick={() => handleAnimationControl('play')}
                    disabled={animationPlaying}
                  >
                    <PlayArrow />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Duraklat">
                  <IconButton
                    color="primary"
                    onClick={() => handleAnimationControl('pause')}
                    disabled={!animationPlaying}
                  >
                    <Pause />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Tekrar">
                  <IconButton color="primary" onClick={() => handleAnimationControl('replay')}>
                    <Replay />
                  </IconButton>
                </Tooltip>
              </Box>

              {/* Speed Control */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  <Speed sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                  Hız: {animationSpeed}x
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {[0.5, 0.75, 1.0, 1.25, 1.5, 2.0].map(speed => (
                    <Chip
                      key={speed}
                      label={`${speed}x`}
                      onClick={() => handleAnimationSpeed(speed)}
                      color={animationSpeed === speed ? 'primary' : 'default'}
                      size="small"
                    />
                  ))}
                </Box>
              </Box>

              {/* Progress */}
              <LinearProgress variant="determinate" value={animationPlaying ? 50 : 0} />
            </CardContent>
          </Card>

          <Typography variant="caption" color="text.secondary">
            💡 İpucu: Animasyon hızını ayarlayarak kendi öğrenme hızınıza göre izleyin
          </Typography>
        </TabPanel>

        {/* Videos Tab (REQ-50.97-100) */}
        <TabPanel value={activeTab} index={1}>
          <Typography variant="h6" sx={{ mb: 2 }}>📹 Eğitim Videoları</Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    Matematik: Kesirler
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Kesirlerin toplama ve çıkarma işlemleri
                  </Typography>

                  <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                    <Chip label="Altyazılı" size="small" color="success" />
                    <Chip label="10 dk" size="small" />
                    <Chip label="WCAG AA" size="small" color="primary" />
                  </Box>

                  <Typography variant="body2" sx={{ mb: 1 }}>
                    Oynatma Hızı: {videoSpeed}x
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {[0.5, 0.75, 1.0, 1.25, 1.5, 2.0].map(speed => (
                      <Chip
                        key={speed}
                        label={`${speed}x`}
                        onClick={() => setVideoSpeed(speed)}
                        color={videoSpeed === speed ? 'primary' : 'default'}
                        size="small"
                      />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* VR/AR Tab (REQ-50.101-104) */}
        <TabPanel value={activeTab} index={2}>
          <Typography variant="h6" sx={{ mb: 2 }}>🥽 VR/AR Deneyimleri</Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card sx={{ borderLeft: '4px solid #9B59B6' }}>
                <CardContent>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    VR: Güneş Sistemi Turu
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Gezegenleri 3D olarak keşfedin
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <Chip label="VR Headset" size="small" />
                    <Chip label="İmmersive" size="small" color="secondary" />
                  </Box>
                  <Button variant="contained" fullWidth disabled>
                    VR Deneyimini Başlat
                  </Button>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card sx={{ borderLeft: '4px solid #E74C3C' }}>
                <CardContent>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    AR: Geometrik Şekiller
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Şekilleri gerçek dünyada görün
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <Chip label="Kamera" size="small" />
                    <Chip label="Interaktif" size="small" color="secondary" />
                  </Box>
                  <Button variant="contained" fullWidth disabled>
                    AR Deneyimini Başlat
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            ⚠️ VR/AR özellikleri uyumlu cihaz gerektirir
          </Typography>
        </TabPanel>
      </Card>

      {/* Benefits */}
      <Card sx={{ mt: 3, bgcolor: '#f5f5f5' }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
            🌟 Çoklu Duyusal Öğrenmenin Faydaları
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                ✓ <strong>Daha İyi Kavrama:</strong> Birden fazla duyu ile öğrenme
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                ✓ <strong>Kalıcı Öğrenme:</strong> Çoklu modalite hafızayı güçlendirir
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                ✓ <strong>Kişiselleştirilmiş:</strong> Kendi öğrenme stilinize uygun
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                ✓ <strong>Eğlenceli:</strong> İnteraktif ve ilgi çekici
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default MultisensoryLearning;
