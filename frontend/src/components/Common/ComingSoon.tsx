/**
 * Coming Soon Component
 * Generic placeholder for pages under development
 */

import {
  Construction as ConstructionIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import {
  Box,
  Container,
  Typography,
  Paper,
  Button,
  Stack,
} from '@mui/material';
import * as React from 'react';
import { useNavigate } from 'react-router-dom';

interface ComingSoonProps {
  title: string
  description?: string
  estimatedDate?: string
  features?: string[]
}

export const ComingSoon: React.FC<ComingSoonProps> = ({
  title,
  description,
  estimatedDate,
  features,
}) => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          minHeight: '80vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          py: 4,
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            textAlign: 'center',
            width: '100%',
          }}
        >
          <ConstructionIcon
            sx={{
              fontSize: 80,
              color: 'primary.main',
              mb: 2,
            }}
          />

          <Typography variant="h3" gutterBottom>
            {title}
          </Typography>

          <Typography variant="h5" color="text.secondary" gutterBottom>
            Yakında Geliyor
          </Typography>

          {description && (
            <Typography variant="body1" sx={{ mt: 2, mb: 3 }}>
              {description}
            </Typography>
          )}

          {estimatedDate && (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Tahmini Yayın Tarihi: {estimatedDate}
            </Typography>
          )}

          {features && features.length > 0 && (
            <Box sx={{ mt: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Planlanan Özellikler:
              </Typography>
              <Stack spacing={1} sx={{ textAlign: 'left', maxWidth: 400, mx: 'auto' }}>
                {features.map((feature, index) => (
                  <Typography key={index} variant="body2">
                    • {feature}
                  </Typography>
                ))}
              </Stack>
            </Box>
          )}

          <Button
            variant="contained"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate(-1)}
            sx={{ mt: 3 }}
          >
            Geri Dön
          </Button>
        </Paper>
      </Box>
    </Container>
  );
};

export default ComingSoon;
