/**
 * Visual Supports Component - Görsel Destekler
 * Task 81: Görsel Destekler (REQ-50.73 - REQ-50.88)
 *
 * Disleksili öğrenciler için görsel öğrenme destekleri:
 * - Kavram haritaları (mind maps)
 * - İnfografikler
 * - Resimli sözlük
 * - Renk kodlama
 */

import {
  AccountTree as MindMapIcon,
  BarChart as InfographicIcon,
  MenuBook as VocabularyIcon,
  Palette as ColorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Grid,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import * as React from 'react';
import {  useState  } from 'react';

import ColorCodingPanel from './ColorCodingPanel';
import InfographicViewer from './InfographicViewer';
import MindMapViewer from './MindMapViewer';
import VisualVocabulary from './VisualVocabulary';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`visual-supports-tabpanel-${index}`}
      aria-labelledby={`visual-supports-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const VisualSupports: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [showInfo, setShowInfo] = useState(false);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const features = [
    {
      icon: <MindMapIcon />,
      title: 'Kavram Haritaları',
      description: 'Konuları görsel olarak organize edin',
      color: '#4A90E2',
    },
    {
      icon: <InfographicIcon />,
      title: 'İnfografikler',
      description: 'Bilgileri görsel özetlerle anlayın',
      color: '#50C878',
    },
    {
      icon: <VocabularyIcon />,
      title: 'Resimli Sözlük',
      description: 'Kelimeleri görsellerle öğrenin',
      color: '#FFB347',
    },
    {
      icon: <ColorIcon />,
      title: 'Renk Kodlama',
      description: 'Kategorileri renklerle ayırt edin',
      color: '#FF6B6B',
    },
  ];

  return (
    <Box sx={{ width: '100%', p: 2 }}>
      {/* Header */}
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h4" sx={{ color: 'white', fontWeight: 'bold', mb: 1 }}>
                🎨 Görsel Destekler
              </Typography>
              <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                Disleksi desteği için görsel öğrenme araçları
              </Typography>
            </Box>
            <Tooltip title="Bilgi">
              <IconButton
                onClick={() => setShowInfo(!showInfo)}
                sx={{ color: 'white' }}
              >
                <InfoIcon />
              </IconButton>
            </Tooltip>
          </Box>

          {/* Info Panel */}
          {showInfo && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'rgba(255,255,255,0.1)', borderRadius: 2 }}>
              <Typography variant="body2" sx={{ color: 'white', mb: 2 }}>
                <strong>Görsel Destekler Nedir?</strong>
              </Typography>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)', mb: 1 }}>
                • <strong>Kavram Haritaları:</strong> Konular arası ilişkileri görsel olarak gösterir
              </Typography>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)', mb: 1 }}>
                • <strong>İnfografikler:</strong> Karmaşık bilgileri basit görsellerle özetler
              </Typography>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)', mb: 1 }}>
                • <strong>Resimli Sözlük:</strong> Kelimeleri görsellerle ilişkilendirir
              </Typography>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                • <strong>Renk Kodlama:</strong> Kategorileri renklerle ayırt etmeyi kolaylaştırır
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Feature Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {features.map((feature, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card
              sx={{
                height: '100%',
                cursor: 'pointer',
                transition: 'all 0.3s',
                border: activeTab === index ? `3px solid ${feature.color}` : '1px solid #e0e0e0',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
              onClick={() => setActiveTab(index)}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Box sx={{ color: feature.color, mr: 1 }}>
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {feature.title}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {feature.description}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            aria-label="visual supports tabs"
            variant="fullWidth"
          >
            <Tab
              icon={<MindMapIcon />}
              label="Kavram Haritaları"
              id="visual-supports-tab-0"
              aria-controls="visual-supports-tabpanel-0"
            />
            <Tab
              icon={<InfographicIcon />}
              label="İnfografikler"
              id="visual-supports-tab-1"
              aria-controls="visual-supports-tabpanel-1"
            />
            <Tab
              icon={<VocabularyIcon />}
              label="Resimli Sözlük"
              id="visual-supports-tab-2"
              aria-controls="visual-supports-tabpanel-2"
            />
            <Tab
              icon={<ColorIcon />}
              label="Renk Kodlama"
              id="visual-supports-tab-3"
              aria-controls="visual-supports-tabpanel-3"
            />
          </Tabs>
        </Box>

        {/* Tab Panels */}
        <TabPanel value={activeTab} index={0}>
          <MindMapViewer />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <InfographicViewer />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <VisualVocabulary />
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <ColorCodingPanel />
        </TabPanel>
      </Card>

      {/* Benefits Section */}
      <Card sx={{ mt: 3, bgcolor: '#f5f5f5' }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
            📊 Görsel Öğrenmenin Faydaları
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'start', mb: 1 }}>
                <Chip label="✓" size="small" color="success" sx={{ mr: 1 }} />
                <Typography variant="body2">
                  <strong>Daha İyi Anlama:</strong> Görsel temsiller karmaşık kavramları basitleştirir
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'start', mb: 1 }}>
                <Chip label="✓" size="small" color="success" sx={{ mr: 1 }} />
                <Typography variant="body2">
                  <strong>Uzun Süreli Hafıza:</strong> Görsellerle öğrenilen bilgiler daha kalıcıdır
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'start', mb: 1 }}>
                <Chip label="✓" size="small" color="success" sx={{ mr: 1 }} />
                <Typography variant="body2">
                  <strong>Hızlı Gözden Geçirme:</strong> Görsel özetler hızlı tekrar sağlar
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'start', mb: 1 }}>
                <Chip label="✓" size="small" color="success" sx={{ mr: 1 }} />
                <Typography variant="body2">
                  <strong>Disleksi Dostu:</strong> Metin yoğunluğunu azaltır, anlamayı kolaylaştırır
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default VisualSupports;
