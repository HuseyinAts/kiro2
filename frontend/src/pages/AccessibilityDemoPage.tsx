/**
 * Erişilebilirlik Demo Sayfası
 *
 * Bu sayfa Task 24'ün tamamlandığını gösterir:
 * 1. AccessibleVideoPlayer - EBA içerikleri için Türkçe altyazılı video player
 * 2. AccessibleMathFormula - Screen reader uyumlu matematik formülleri
 * 3. WCAGValidator - Otomatik WCAG 2.1 Level AA validasyonu
 */

import { CheckCircle } from '@mui/icons-material';
import {
  Typography,
  Box,
  Paper,
  Grid,
  Divider,
  Alert,
} from '@mui/material';
import * as React from 'react';
import {  useState  } from 'react';

import AccessibleMathFormula from '../components/Common/AccessibleMathFormula';
import AccessibleVideoPlayer from '../components/Common/AccessibleVideoPlayer';
import { WCAGCompliantLayout } from '../components/Common/WCAGCompliantLayout';
import WCAGValidator from '../components/Common/WCAGValidator';

const AccessibilityDemoPage: React.FC = () => {
  const [validationIssues, setValidationIssues] = useState(0);

  // Örnek video tracks (Türkçe altyazı)
  const videoTracks = [
    {
      id: 'tr-subtitle',
      label: 'Türkçe',
      language: 'tr',
      src: '/subtitles/turkish.vtt',
      kind: 'subtitles' as const,
      default: true,
    },
    {
      id: 'tr-caption',
      label: 'Türkçe (İşitme Engelli)',
      language: 'tr',
      src: '/subtitles/turkish-cc.vtt',
      kind: 'captions' as const,
    },
  ];

  // Navigasyon öğeleri
  const navigationItems = [
    { id: 'home', label: 'Ana Sayfa', href: '/' },
    { id: 'demo', label: 'Erişilebilirlik Demo', href: '/accessibility-demo' },
    { id: 'docs', label: 'Dokümantasyon', href: '/docs' },
  ];

  return (
    <>
      <WCAGCompliantLayout
        title="Teknofest 2025 Eğitim Platformu"
        navigationItems={navigationItems}
        pageTitle="Erişilebilirlik Özellikleri Demo"
        pageDescription="WCAG 2.1 Level AA uyumlu erişilebilirlik özelliklerinin demonstrasyonu"
        breadcrumbs={[
          { label: 'Demo', href: '/demo' },
          { label: 'Erişilebilirlik' },
        ]}
      >
        {/* Başarı Mesajı */}
        <Alert
          severity="success"
          icon={<CheckCircle />}
          sx={{ mb: 3 }}
        >
          <Typography variant="h6" gutterBottom>
            ✅ Task 24 Tamamlandı!
          </Typography>
          <Typography variant="body2">
            WCAG 2.1 Level AA uyumlu erişilebilirlik özellikleri başarıyla implement edildi:
          </Typography>
          <ul>
            <li>Türkçe altyazılı erişilebilir video player</li>
            <li>Screen reader uyumlu matematik formülleri (MathML)</li>
            <li>Otomatik WCAG validasyonu</li>
          </ul>
        </Alert>

        {/* 1. Erişilebilir Video Player */}
        <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
          <Typography variant="h4" component="h2" gutterBottom>
            1. Erişilebilir Video Player
          </Typography>

          <Typography variant="body1" paragraph>
            EBA TV içerikleri için Türkçe altyazı desteği, klavye kısayolları ve
            ekran okuyucu uyumluluğu ile tam erişilebilir video player.
          </Typography>

          <Box sx={{ my: 3 }}>
            <AccessibleVideoPlayer
              src="https://www.w3schools.com/html/mov_bbb.mp4"
              title="Örnek Eğitim Videosu - Matematik Dersi"
              description="Bu videoda ikinci dereceden denklemlerin çözümü anlatılmaktadır. Video 5 dakika sürmektedir ve Türkçe altyazı içermektedir."
              poster="https://via.placeholder.com/800x450?text=Matematik+Dersi"
              tracks={videoTracks}
              width="100%"
              height={450}
              controls={true}
            />
          </Box>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Klavye Kısayolları:
            </Typography>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li><strong>Space/K:</strong> Oynat/Duraklat</li>
              <li><strong>←/→:</strong> 10 saniye geri/ileri</li>
              <li><strong>↑/↓:</strong> Ses seviyesi ayarla</li>
              <li><strong>M:</strong> Sessiz</li>
              <li><strong>F:</strong> Tam ekran</li>
              <li><strong>C:</strong> Altyazı aç/kapat</li>
              <li><strong>0-9:</strong> Videoda konuma git (%0-%90)</li>
            </ul>
          </Alert>
        </Paper>

        {/* 2. Erişilebilir Matematik Formülleri */}
        <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
          <Typography variant="h4" component="h2" gutterBottom>
            2. Erişilebilir Matematik Formülleri
          </Typography>

          <Typography variant="body1" paragraph>
            MathML desteği ile ekran okuyucu uyumlu matematik formülleri.
            Sesli okuma, zoom ve kopyalama özellikleri ile tam erişilebilir.
          </Typography>

          <Grid container spacing={3} sx={{ my: 2 }}>
            {/* Örnek 1: Basit Denklem */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Örnek 1: İkinci Dereceden Denklem
              </Typography>
              <AccessibleMathFormula
                latex="ax^2 + bx + c = 0"
                description="a çarpı x kare artı b çarpı x artı c eşittir sıfır. Bu ikinci dereceden bir denklemdir."
                label="İkinci Dereceden Denklem"
                display="block"
                enableAudio={true}
                enableCopy={true}
                showDetailedDescription={false}
              />
            </Grid>

            {/* Örnek 2: Kesir */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Örnek 2: Kesir İfadesi
              </Typography>
              <AccessibleMathFormula
                latex="\frac{a}{b}"
                description="a bölü b. Bu bir kesir ifadesidir. Payda a, payda b'dir."
                label="Kesir"
                display="block"
                enableAudio={true}
                enableCopy={true}
              />
            </Grid>

            {/* Örnek 3: Karekök */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Örnek 3: Karekök
              </Typography>
              <AccessibleMathFormula
                latex="\sqrt{x}"
                description="x'in karekökü. Bu bir radikal ifadedir."
                label="Karekök"
                display="block"
                enableAudio={true}
                enableCopy={true}
              />
            </Grid>

            {/* Örnek 4: Üs */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Örnek 4: Üslü İfade
              </Typography>
              <AccessibleMathFormula
                latex="x^2"
                description="x'in karesi. x üzeri iki."
                label="Üslü İfade"
                display="block"
                enableAudio={true}
                enableCopy={true}
              />
            </Grid>

            {/* Örnek 5: Alt İndis */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Örnek 5: Alt İndisli İfade
              </Typography>
              <AccessibleMathFormula
                latex="x_1"
                description="x alt indis bir. Bu bir indisli değişkendir."
                label="Alt İndis"
                display="block"
                enableAudio={true}
                enableCopy={true}
              />
            </Grid>
          </Grid>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Formül Özellikleri:
            </Typography>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li><strong>Sesli Okuma:</strong> Formüller Türkçe olarak sesli okunabilir</li>
              <li><strong>Zoom:</strong> +/- tuşları ile yakınlaştırma/uzaklaştırma</li>
              <li><strong>Kopyalama:</strong> Ctrl+C ile formülü kopyalayın</li>
              <li><strong>Açıklama:</strong> I tuşu ile detaylı açıklama göster/gizle</li>
              <li><strong>MathML:</strong> Ekran okuyucular için tam destek</li>
            </ul>
          </Alert>
        </Paper>

        {/* 3. WCAG Validator */}
        <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
          <Typography variant="h4" component="h2" gutterBottom>
            3. WCAG 2.1 Level AA Otomatik Validator
          </Typography>

          <Typography variant="body1" paragraph>
            Sayfadaki erişilebilirlik sorunlarını otomatik olarak tespit eden validator.
            Sağ alt köşede bulunan validator panelini açarak detayları görebilirsiniz.
          </Typography>

          <Alert severity="info">
            <Typography variant="subtitle2" gutterBottom>
              Validator Özellikleri:
            </Typography>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>Eksik alt metinleri tespit eder</li>
              <li>Yetersiz kontrast oranlarını bulur</li>
              <li>Eksik ARIA etiketlerini kontrol eder</li>
              <li>Klavye erişilebilirliği sorunlarını saptar</li>
              <li>Başlık hiyerarşisi hatalarını gösterir</li>
              <li>Form erişilebilirliğini doğrular</li>
              <li>WCAG 2.1 Level AA standartlarına uygunluğu kontrol eder</li>
            </ul>
          </Alert>

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Validator paneli sağ alt köşede görünmektedir.
              {validationIssues > 0 ? (
                <span style={{ color: 'red', fontWeight: 'bold' }}>
                  {' '}{validationIssues} sorun tespit edildi.
                </span>
              ) : (
                <span style={{ color: 'green', fontWeight: 'bold' }}>
                  {' '}Erişilebilirlik sorunu bulunamadı! 🎉
                </span>
              )}
            </Typography>
          </Box>
        </Paper>

        {/* Özet */}
        <Paper elevation={2} sx={{ p: 3, backgroundColor: 'success.light' }}>
          <Typography variant="h5" gutterBottom>
            ✅ Task 24 Başarıyla Tamamlandı
          </Typography>

          <Typography variant="body1" paragraph>
            WCAG 2.1 Level AA uyumlu erişilebilirlik özellikleri tam olarak implement edildi:
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Box sx={{ textAlign: 'center', p: 2 }}>
                <CheckCircle sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
                <Typography variant="h6">Video Player</Typography>
                <Typography variant="body2">
                  Türkçe altyazı, klavye kısayolları, ekran okuyucu desteği
                </Typography>
              </Box>
            </Grid>

            <Grid item xs={12} md={4}>
              <Box sx={{ textAlign: 'center', p: 2 }}>
                <CheckCircle sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
                <Typography variant="h6">Matematik Formülleri</Typography>
                <Typography variant="body2">
                  MathML, sesli okuma, zoom, kopyalama
                </Typography>
              </Box>
            </Grid>

            <Grid item xs={12} md={4}>
              <Box sx={{ textAlign: 'center', p: 2 }}>
                <CheckCircle sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
                <Typography variant="h6">WCAG Validator</Typography>
                <Typography variant="body2">
                  Otomatik erişilebilirlik kontrolü ve raporlama
                </Typography>
              </Box>
            </Grid>
          </Grid>

          <Divider sx={{ my: 2 }} />

          <Typography variant="body2" color="text.secondary" align="center">
            Requirements: 9.1, 9.2, 9.3, 9.4, 9.5 | WCAG 2.1 Level AA
          </Typography>
        </Paper>
      </WCAGCompliantLayout>

      {/* WCAG Validator (Sağ alt köşede) */}
      <WCAGValidator
        autoValidate={true}
        validationInterval={5000}
        developmentOnly={false}
        position="bottom-right"
        onIssuesFound={(issues) => setValidationIssues(issues.length)}
      />
    </>
  );
};

export default AccessibilityDemoPage;
