import { Card, CardMedia, CardContent, CardActions, Typography, Chip, Button, Box, Rating, Tooltip, LinearProgress } from '@mui/material';
import { PlayCircle, AccessTime, Visibility, Star, CheckCircle, Language, School, HighQuality, ClosedCaption, Hd, WarningAmber } from '@mui/icons-material';
import { VideoResponse } from '../../api';

interface VideoResourceCardProps {
  video: VideoResponse;
  onPlay?: (video: VideoResponse) => void;
}

export function VideoResourceCard({ video, onPlay }: VideoResourceCardProps) {
  const formatDuration = (duration: string): string => {
    // PT15M30S → 15:30
    const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
    if (match) {
      const hours = match[1] ? parseInt(match[1]) : 0;
      const minutes = match[2] ? parseInt(match[2]) : 0;
      const seconds = match[3] ? parseInt(match[3]) : 0;
      
      if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      }
      return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
    return duration;
  };

  const formatViewCount = (count: number): string => {
    if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
    if (count >= 1000) return `${(count / 1000).toFixed(1)}K`;
    return count.toString();
  };

  const handlePlay = () => {
    if (onPlay) {
      onPlay(video);
    } else {
      window.open(video.url, '_blank');
    }
  };

  return (
    <Card 
      elevation={3} 
      className="hover:shadow-xl transition-all duration-300 h-full flex flex-col"
      sx={{ 
        '&:hover': { 
          transform: 'translateY(-4px)',
          boxShadow: 6
        }
      }}
    >
      {/* Thumbnail */}
      <CardMedia
        component="img"
        height="180"
        image={video.thumbnail}
        alt={video.title}
        className="cursor-pointer"
        onClick={handlePlay}
        sx={{ 
          objectFit: 'cover',
          position: 'relative',
          '&:hover::after': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.3)'
          }
        }}
      />

      <CardContent className="flex-1">
        {/* Başlık */}
        <Typography 
          variant="h6" 
          className="line-clamp-2 mb-2 font-semibold"
          sx={{ 
            fontSize: '1rem',
            minHeight: '3rem',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden'
          }}
        >
          {video.title}
        </Typography>

        {/* Kanal */}
        <Typography 
          variant="body2" 
          color="text.secondary" 
          className="mb-2 flex items-center gap-1"
        >
          📺 {video.channel}
        </Typography>

        {/* Metrikler */}
        <Box className="flex items-center gap-2 mb-2 flex-wrap">
          <Chip
            icon={<AccessTime fontSize="small" />}
            label={formatDuration(video.duration)}
            size="small"
            variant="outlined"
            color="primary"
          />
          <Chip
            icon={<Visibility fontSize="small" />}
            label={formatViewCount(video.view_count)}
            size="small"
            variant="outlined"
          />
        </Box>

        {/* Zorluk ve Sınav Tipi */}
        <Box className="flex items-center gap-1 mb-2">
          <Chip
            label={video.difficulty}
            size="small"
            color={
              video.difficulty === 'başlangıç' ? 'success' :
              video.difficulty === 'orta' ? 'warning' :
              'error'
            }
            sx={{ fontSize: '0.75rem' }}
          />
          <Chip
            label={video.exam_type}
            size="small"
            variant="outlined"
            sx={{ fontSize: '0.75rem' }}
          />
        </Box>

        {/* Enhanced Scores - Yeni skorlama sistemi */}
        {video.scores ? (
          <Box className="mt-2">
            <Typography variant="caption" color="text.secondary" className="block mb-1">
              Kalite Metrikleri:
            </Typography>
            
            {/* Türkçe Skoru */}
            <Box className="flex items-center gap-1 mb-1">
              <Tooltip title="Türkçe İçerik Skoru">
                <Language fontSize="small" color={video.scores.turkish_score >= 0.7 ? 'success' : 'warning'} />
              </Tooltip>
              <LinearProgress 
                variant="determinate" 
                value={video.scores.turkish_score * 100} 
                sx={{ flex: 1, height: 6, borderRadius: 1 }}
                color={video.scores.turkish_score >= 0.7 ? 'success' : 'warning'}
              />
              <Typography variant="caption" color="text.secondary" sx={{ minWidth: 35 }}>
                {(video.scores.turkish_score * 100).toFixed(0)}%
              </Typography>
            </Box>
            
            {/* Konu Uygunluğu Skoru */}
            <Box className="flex items-center gap-1 mb-1">
              <Tooltip title="Konu Uygunluğu Skoru">
                <School fontSize="small" color={video.scores.relevance_score >= 0.6 ? 'success' : 'warning'} />
              </Tooltip>
              <LinearProgress 
                variant="determinate" 
                value={video.scores.relevance_score * 100} 
                sx={{ flex: 1, height: 6, borderRadius: 1 }}
                color={video.scores.relevance_score >= 0.6 ? 'success' : 'warning'}
              />
              <Typography variant="caption" color="text.secondary" sx={{ minWidth: 35 }}>
                {(video.scores.relevance_score * 100).toFixed(0)}%
              </Typography>
            </Box>
            
            {/* Video Kalitesi Skoru */}
            <Box className="flex items-center gap-1 mb-1">
              <Tooltip title="Video Kalite Skoru">
                <HighQuality fontSize="small" color={video.scores.quality_score >= 0.5 ? 'success' : 'warning'} />
              </Tooltip>
              <LinearProgress 
                variant="determinate" 
                value={video.scores.quality_score * 100} 
                sx={{ flex: 1, height: 6, borderRadius: 1 }}
                color={video.scores.quality_score >= 0.5 ? 'success' : 'warning'}
              />
              <Typography variant="caption" color="text.secondary" sx={{ minWidth: 35 }}>
                {(video.scores.quality_score * 100).toFixed(0)}%
              </Typography>
            </Box>
            
            {/* Final Skor */}
            <Box className="flex items-center gap-1 mt-2">
              <Typography variant="caption" fontWeight="bold" color="primary">
                Toplam Skor:
              </Typography>
              <Rating
                value={video.scores.final_score * 5}
                precision={0.1}
                size="small"
                readOnly
                icon={<Star fontSize="inherit" />}
              />
              <Typography variant="caption" fontWeight="bold" color="primary">
                ({(video.scores.final_score * 5).toFixed(1)}/5)
              </Typography>
            </Box>
          </Box>
        ) : (
          /* Eski kalite skoru - geriye dönük uyumluluk */
          <Box className="flex items-center gap-1">
            <Typography variant="caption" color="text.secondary">
              Kalite:
            </Typography>
            <Rating
              value={video.quality_score * 5}
              precision={0.1}
              size="small"
              readOnly
              icon={<Star fontSize="inherit" />}
            />
            <Typography variant="caption" color="text.secondary">
              ({(video.quality_score * 5).toFixed(1)})
            </Typography>
          </Box>
        )}
        
        {/* Erişilebilirlik ve Özellik Rozetleri */}
        {(video.is_accessible !== undefined || video.caption_available || video.definition === 'hd') && (
          <Box className="flex items-center gap-1 mt-2 flex-wrap">
            {video.is_accessible === false && (
              <Tooltip title="Video erişilemeyebilir">
                <Chip
                  icon={<WarningAmber fontSize="small" />}
                  label="Erişim Sorunu"
                  size="small"
                  color="warning"
                  variant="outlined"
                  sx={{ fontSize: '0.65rem', height: 20 }}
                />
              </Tooltip>
            )}
            {video.is_accessible === true && (
              <Tooltip title="Video erişilebilir ve oynatılabilir">
                <Chip
                  icon={<CheckCircle fontSize="small" />}
                  label="Erişilebilir"
                  size="small"
                  color="success"
                  variant="outlined"
                  sx={{ fontSize: '0.65rem', height: 20 }}
                />
              </Tooltip>
            )}
            {video.caption_available && (
              <Tooltip title="Altyazı mevcut">
                <Chip
                  icon={<ClosedCaption fontSize="small" />}
                  label="Altyazılı"
                  size="small"
                  color="info"
                  variant="outlined"
                  sx={{ fontSize: '0.65rem', height: 20 }}
                />
              </Tooltip>
            )}
            {video.definition === 'hd' && (
              <Tooltip title="HD kalitede video">
                <Chip
                  icon={<Hd fontSize="small" />}
                  label="HD"
                  size="small"
                  color="primary"
                  variant="outlined"
                  sx={{ fontSize: '0.65rem', height: 20 }}
                />
              </Tooltip>
            )}
          </Box>
        )}
      </CardContent>

      {/* İzle Butonu */}
      <CardActions sx={{ padding: 2, paddingTop: 0 }}>
        <Button
          variant="contained"
          color="primary"
          fullWidth
          startIcon={<PlayCircle />}
          onClick={handlePlay}
          sx={{ 
            textTransform: 'none',
            fontWeight: 600
          }}
        >
          İzle
        </Button>
      </CardActions>
    </Card>
  );
}
