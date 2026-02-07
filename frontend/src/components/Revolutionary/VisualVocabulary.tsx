/**
 * Visual Vocabulary Component - Resimli Sözlük
 * Task 81.3: Resimli sözlük (REQ-50.81-84)
 */

import { Search as SearchIcon } from '@mui/icons-material';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardMedia,
  Typography,
  TextField,
  Grid,
  Chip,
  LinearProgress,
} from '@mui/material';
import * as React from 'react';
import {  useState  } from 'react';

interface VocabularyCard {
  id: string;
  word: string;
  definition: string;
  image_url: string;
  category: string;
  difficulty_level: number;
  color_code: string;
}

const VisualVocabulary: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [cards, setCards] = useState<VocabularyCard[]>([]);
  const [progress, setProgress] = useState({
    total_cards: 100,
    learned_cards: 60,
    progress_percentage: 60,
  });

  // REQ-50.83: Searchable image database
  const handleSearch = async () => {
    try {
      const response = await fetch(
        `/api/v1/visual-supports/vocabulary-cards/search?query=${searchQuery}`,
      );
      if (response.ok) {
        const data = await response.json();
        setCards(data);
      }
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  // REQ-50.82: Visual vocabulary builder
  const loadProgress = async () => {
    try {
      const response = await fetch('/api/v1/visual-supports/vocabulary-cards/progress/user123');
      if (response.ok) {
        const data = await response.json();
        setProgress(data);
      }
    } catch (error) {
      console.error('Progress load failed:', error);
    }
  };

  React.useEffect(() => {
    loadProgress();
  }, []);

  return (
    <Box>
      {/* Progress */}
      <Card sx={{ mb: 3, bgcolor: '#f5f5f5' }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>📚 Kelime Öğrenme İlerlemesi</Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ flex: 1 }}>
              <LinearProgress
                variant="determinate"
                value={progress.progress_percentage}
                sx={{ height: 10, borderRadius: 5 }}
              />
            </Box>
            <Typography variant="body2" fontWeight="bold">
              {progress.learned_cards}/{progress.total_cards} (%{progress.progress_percentage.toFixed(0)})
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Search */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Kelime ara..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
        />
        <Button
          variant="contained"
          startIcon={<SearchIcon />}
          onClick={handleSearch}
        >
          Ara
        </Button>
      </Box>

      {/* Cards */}
      <Grid container spacing={2}>
        {cards.map(card => (
          <Grid item xs={12} sm={6} md={4} key={card.id}>
            <Card sx={{ height: '100%', borderLeft: `4px solid ${card.color_code}` }}>
              <CardMedia
                component="img"
                height="140"
                image={card.image_url}
                alt={card.word}
              />
              <CardContent>
                <Typography variant="h6" gutterBottom>{card.word}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {card.definition}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip label={card.category} size="small" />
                  <Chip label={`Seviye ${card.difficulty_level}`} size="small" color="primary" />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {cards.length === 0 && (
        <Card>
          <CardContent>
            <Typography variant="body1" color="text.secondary" align="center">
              Kelime aramak için yukarıdaki arama kutusunu kullanın
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default VisualVocabulary;
