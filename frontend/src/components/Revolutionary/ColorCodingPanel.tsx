/**
 * Color Coding Panel Component - Renk Kodlama Paneli
 * Task 81.4: Renk kodlama (REQ-50.85-88)
 */

import { Save as SaveIcon, Palette as PaletteIcon } from '@mui/icons-material';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

interface ColorScheme {
  id: string;
  name: string;
  description: string;
  categories: Record<string, string>;
  is_default: boolean;
}

const ColorCodingPanel: React.FC = () => {
  const [schemes, setSchemes] = useState<ColorScheme[]>([]);
  const [selectedScheme, setSelectedScheme] = useState<ColorScheme | null>(null);
  const [customColors, setCustomColors] = useState<Record<string, string>>({});

  // REQ-50.86: Load default color schemes
  useEffect(() => {
    loadDefaultSchemes();
  }, []);

  const loadDefaultSchemes = async () => {
    try {
      const response = await fetch('/api/v1/visual-supports/color-schemes');
      if (response.ok) {
        const data = await response.json();
        setSchemes(data);
        if (data.length > 0) {
          setSelectedScheme(data[0]);
          setCustomColors(data[0].categories);
        }
      }
    } catch (error) {
      console.error('Failed to load color schemes:', error);
    }
  };

  // REQ-50.87: Customize color mapping
  const handleColorChange = (category: string, newColor: string) => {
    setCustomColors(prev => ({
      ...prev,
      [category]: newColor,
    }));
  };

  // REQ-50.88: Save user preferences
  const handleSavePreferences = async () => {
    if (!selectedScheme) {return;}

    try {
      // Update color mappings
      for (const [category, color] of Object.entries(customColors)) {
        await fetch(`/api/v1/visual-supports/color-schemes/${selectedScheme.id}/mapping`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category, new_color: color }),
        });
      }

      // Save preferences
      await fetch(`/api/v1/visual-supports/color-schemes/${selectedScheme.id}/save-preferences?user_id=user123`, {
        method: 'POST',
      });

      alert('Renk tercihleri kaydedildi!');
    } catch (error) {
      console.error('Failed to save preferences:', error);
    }
  };

  return (
    <Box>
      {/* Scheme Selector */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <FormControl fullWidth>
            <InputLabel>Renk Şeması</InputLabel>
            <Select
              value={selectedScheme?.id || ''}
              label="Renk Şeması"
              onChange={(e) => {
                const scheme = schemes.find(s => s.id === e.target.value);
                if (scheme) {
                  setSelectedScheme(scheme);
                  setCustomColors(scheme.categories);
                }
              }}
            >
              {schemes.map(scheme => (
                <MenuItem key={scheme.id} value={scheme.id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PaletteIcon />
                    {scheme.name}
                    {scheme.is_default && <Chip label="Varsayılan" size="small" />}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {selectedScheme && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {selectedScheme.description}
            </Typography>
          )}
        </CardContent>
      </Card>

      {/* Color Customization */}
      {selectedScheme && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>🎨 Renk Özelleştirme</Typography>
            <Grid container spacing={2}>
              {Object.entries(customColors).map(([category, color]) => (
                <Grid item xs={12} sm={6} md={4} key={category}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box
                      sx={{
                        width: 40,
                        height: 40,
                        bgcolor: color,
                        borderRadius: 1,
                        border: '2px solid #e0e0e0',
                      }}
                    />
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="body2" fontWeight="bold">
                        {category}
                      </Typography>
                      <TextField
                        type="color"
                        value={color}
                        onChange={(e) => handleColorChange(category, e.target.value)}
                        size="small"
                        fullWidth
                      />
                    </Box>
                  </Box>
                </Grid>
              ))}
            </Grid>

            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSavePreferences}
              sx={{ mt: 3 }}
            >
              Tercihleri Kaydet
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Preview */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>👁️ Önizleme</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {Object.entries(customColors).map(([category, color]) => (
              <Chip
                key={category}
                label={category}
                sx={{
                  bgcolor: color,
                  color: '#fff',
                  fontWeight: 'bold',
                }}
              />
            ))}
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ColorCodingPanel;
