import { OndemandVideo, CheckCircle, Warning } from '@mui/icons-material';
import { Grid, Box, Typography, Select, MenuItem, FormControl, InputLabel, Skeleton, Alert, CircularProgress, Chip, Tooltip } from '@mui/material';
import { useState, useRef } from 'react';

import { VideoResponse } from '../../api';

import { VideoResourceCard } from './VideoResourceCard';

interface VideoResourceGridProps {
  videos: VideoResponse[];
  loading?: boolean;
  error?: string;
  onVideoPlay?: (video: VideoResponse) => void;
}

export function VideoResourceGrid({ videos, loading, error, onVideoPlay }: VideoResourceGridProps) {
  const [difficulty, setDifficulty] = useState<string>('all');
  const [duration, setDuration] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('quality');
  const containerRef = useRef<HTMLDivElement>(null);

  // Filter videos
  const filteredVideos = videos.filter(video => {
    // Difficulty filter
    if (difficulty !== 'all' && video.difficulty !== difficulty) {
      return false;
    }

    // Duration filter
    if (duration !== 'all') {
      const durationMatch = video.duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?/);
      if (durationMatch) {
        const hours = durationMatch[1] ? parseInt(durationMatch[1]) : 0;
        const minutes = durationMatch[2] ? parseInt(durationMatch[2]) : 0;
        const totalMinutes = hours * 60 + minutes;

        if (duration === 'short' && totalMinutes >= 10) {return false;}
        if (duration === 'medium' && (totalMinutes < 10 || totalMinutes > 30)) {return false;}
        if (duration === 'long' && totalMinutes <= 30) {return false;}
      }
    }

    return true;
  });

  // Sort videos - Enhanced scoring desteği ile
  const sortedVideos = [...filteredVideos].sort((a, b) => {
    switch (sortBy) {
      case 'quality': {
        // Yeni skorlama sistemi varsa final_score kullan, yoksa eski quality_score
        const scoreA = a.scores?.final_score ?? a.quality_score;
        const scoreB = b.scores?.final_score ?? b.quality_score;
        return scoreB - scoreA;
      }
      case 'relevance': {
        // Konu uygunluğuna göre sırala
        const relevanceA = a.scores?.relevance_score ?? 0;
        const relevanceB = b.scores?.relevance_score ?? 0;
        return relevanceB - relevanceA;
      }
      case 'turkish': {
        // Türkçe skoruna göre sırala
        const turkishA = a.scores?.turkish_score ?? 0;
        const turkishB = b.scores?.turkish_score ?? 0;
        return turkishB - turkishA;
      }
      case 'views':
        return b.view_count - a.view_count;
      case 'date':
        return new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime();
      default:
        return 0;
    }
  });

  // Erişilebilirlik istatistikleri
  const accessibilityStats = {
    total: videos.length,
    accessible: videos.filter(v => v.is_accessible === true).length,
    inaccessible: videos.filter(v => v.is_accessible === false).length,
    turkish: videos.filter(v => v.is_turkish === true).length,
    withCaptions: videos.filter(v => v.caption_available === true).length,
    hd: videos.filter(v => v.definition === 'hd').length,
  };

  // Gelişmiş hata gösterimi
  if (error) {
    return (
      <Box>
        <Alert
          severity="error"
          sx={{ mb: 3 }}
          action={
            <Typography variant="caption" color="text.secondary">
              Lütfen daha sonra tekrar deneyin
            </Typography>
          }
        >
          <Typography variant="body2" fontWeight="bold" gutterBottom>
            Video yüklenirken bir hata oluştu
          </Typography>
          <Typography variant="body2">
            {error}
          </Typography>
        </Alert>

        {/* Hata durumunda yardımcı bilgiler */}
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2" fontWeight="bold" gutterBottom>
            Ne yapabilirsiniz?
          </Typography>
          <Typography variant="body2" component="ul" sx={{ pl: 2, mb: 0 }}>
            <li>İnternet bağlantınızı kontrol edin</li>
            <li>Sayfayı yenileyin</li>
            <li>Farklı bir konu veya ders seçin</li>
            <li>Sorun devam ederse destek ekibimizle iletişime geçin</li>
          </Typography>
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Filters */}
      <Box className="flex gap-3 mb-4 flex-wrap">
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Zorluk</InputLabel>
          <Select
            value={difficulty}
            label="Zorluk"
            onChange={(e) => setDifficulty(e.target.value)}
          >
            <MenuItem value="all">Tümü</MenuItem>
            <MenuItem value="başlangıç">Başlangıç</MenuItem>
            <MenuItem value="orta">Orta</MenuItem>
            <MenuItem value="ileri">İleri</MenuItem>
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Süre</InputLabel>
          <Select
            value={duration}
            label="Süre"
            onChange={(e) => setDuration(e.target.value)}
          >
            <MenuItem value="all">Tümü</MenuItem>
            <MenuItem value="short">Kısa (&lt; 10 dk)</MenuItem>
            <MenuItem value="medium">Orta (10-30 dk)</MenuItem>
            <MenuItem value="long">Uzun (&gt; 30 dk)</MenuItem>
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Sıralama</InputLabel>
          <Select
            value={sortBy}
            label="Sıralama"
            onChange={(e) => setSortBy(e.target.value)}
          >
            <MenuItem value="quality">Toplam Kaliteye Göre</MenuItem>
            <MenuItem value="relevance">Konu Uygunluğuna Göre</MenuItem>
            <MenuItem value="turkish">Türkçe Skoruna Göre</MenuItem>
            <MenuItem value="views">İzlenmeye Göre</MenuItem>
            <MenuItem value="date">Tarihe Göre</MenuItem>
          </Select>
        </FormControl>

        <Box className="flex-1" />

        <Typography variant="body2" color="text.secondary" className="flex items-center">
          {sortedVideos.length} video bulundu
        </Typography>
      </Box>

      {/* Kalite ve Erişilebilirlik İstatistikleri */}
      {!loading && videos.length > 0 && (
        <Box className="flex gap-2 mb-3 flex-wrap">
          {accessibilityStats.accessible > 0 && (
            <Tooltip title="Erişilebilir ve oynatılabilir videolar">
              <Chip
                icon={<CheckCircle fontSize="small" />}
                label={`${accessibilityStats.accessible} Erişilebilir`}
                size="small"
                color="success"
                variant="outlined"
              />
            </Tooltip>
          )}
          {accessibilityStats.inaccessible > 0 && (
            <Tooltip title="Erişim sorunu olabilecek videolar">
              <Chip
                icon={<Warning fontSize="small" />}
                label={`${accessibilityStats.inaccessible} Erişim Sorunu`}
                size="small"
                color="warning"
                variant="outlined"
              />
            </Tooltip>
          )}
          {accessibilityStats.turkish > 0 && (
            <Tooltip title="Türkçe içerik onaylı videolar">
              <Chip
                label={`${accessibilityStats.turkish} Türkçe`}
                size="small"
                color="primary"
                variant="outlined"
              />
            </Tooltip>
          )}
          {accessibilityStats.withCaptions > 0 && (
            <Tooltip title="Altyazılı videolar">
              <Chip
                label={`${accessibilityStats.withCaptions} Altyazılı`}
                size="small"
                color="info"
                variant="outlined"
              />
            </Tooltip>
          )}
          {accessibilityStats.hd > 0 && (
            <Tooltip title="HD kalitede videolar">
              <Chip
                label={`${accessibilityStats.hd} HD`}
                size="small"
                color="primary"
                variant="outlined"
              />
            </Tooltip>
          )}
        </Box>
      )}

      {/* Yükleme durumu bilgilendirmesi */}
      {loading && (
        <Alert severity="info" icon={<CircularProgress size={20} />} sx={{ mb: 3 }}>
          <Typography variant="body2">
            Sizin için en uygun Türkçe eğitim videoları aranıyor...
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Videolar Türkçe içerik, konu uygunluğu ve kalite kontrolünden geçiriliyor
          </Typography>
        </Alert>
      )}

      {/* Video Grid */}
      {loading ? (
        <Grid container spacing={3}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Box sx={{
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 2,
                overflow: 'hidden',
                backgroundColor: 'background.paper',
              }}>
                <Skeleton variant="rectangular" height={180} />
                <Box sx={{ p: 2 }}>
                  <Skeleton variant="text" height={32} />
                  <Skeleton variant="text" width="70%" />
                  <Box className="flex gap-1 mt-2">
                    <Skeleton variant="rectangular" width={60} height={24} sx={{ borderRadius: 1 }} />
                    <Skeleton variant="rectangular" width={60} height={24} sx={{ borderRadius: 1 }} />
                  </Box>
                  <Box className="mt-2">
                    <Skeleton variant="rectangular" height={6} sx={{ borderRadius: 1, mb: 1 }} />
                    <Skeleton variant="rectangular" height={6} sx={{ borderRadius: 1, mb: 1 }} />
                    <Skeleton variant="rectangular" height={6} sx={{ borderRadius: 1 }} />
                  </Box>
                  <Skeleton variant="rectangular" height={36} sx={{ borderRadius: 1, mt: 2 }} />
                </Box>
              </Box>
            </Grid>
          ))}
        </Grid>
      ) : sortedVideos.length === 0 ? (
        <Box
          className="flex flex-col items-center justify-center py-12"
          sx={{
            border: '2px dashed',
            borderColor: 'divider',
            borderRadius: 2,
            backgroundColor: 'background.paper',
          }}
        >
          <OndemandVideo sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            Video bulunamadı
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Farklı filtreler deneyebilirsiniz
          </Typography>
        </Box>
      ) : (
        <Box ref={containerRef} sx={{ width: '100%' }}>
          <Grid container spacing={3}>
            {sortedVideos.map((video) => (
              <Grid item xs={12} sm={6} md={4} key={video.video_id}>
                <VideoResourceCard video={video} onPlay={onVideoPlay} />
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
    </Box>
  );
}
