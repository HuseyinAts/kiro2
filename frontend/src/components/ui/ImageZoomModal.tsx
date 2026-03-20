/**
 * ImageZoomModal — Sınav görsellerini büyütmek için lightbox bileşeni.
 *
 * Özellikler:
 * - Tıkla → tam ekran modal (büyütülmüş görüntüleme)
 * - ESC veya backdrop click ile kapat
 * - Büyüteç ikonu overlay (hover/mobil)
 * - width/height ile CLS (layout shift) önleme
 * - Bozuk görsel için placeholder
 */

import { useState, useCallback } from 'react';
import { Box, Modal, IconButton, Typography } from '@mui/material';
import { ZoomIn, Close, BrokenImage } from '@mui/icons-material';

interface QuestionImageProps {
  src: string;
  alt?: string;
  width?: number;
  height?: number;
}

/** Tıklanabilir soru görseli + zoom modal */
export const QuestionImage: React.FC<QuestionImageProps> = ({
  src,
  alt = 'Soru görseli',
  width,
  height,
}) => {
  const [open, setOpen] = useState(false);
  const [imgError, setImgError] = useState(false);

  const handleOpen = useCallback(() => setOpen(true), []);
  const handleClose = useCallback(() => setOpen(false), []);

  // Bozuk görsel — placeholder göster (sessizce gizleme yerine)
  if (imgError) {
    return (
      <Box
        sx={{
          mb: 3,
          textAlign: 'center',
          p: 2,
          borderRadius: '12px',
          border: '1px dashed rgba(0,0,0,0.2)',
          backgroundColor: '#f5f5f5',
          color: 'text.secondary',
        }}
      >
        <BrokenImage sx={{ fontSize: 32, opacity: 0.4, mb: 0.5 }} />
        <Typography variant="caption" display="block">
          Görsel yüklenemedi
        </Typography>
      </Box>
    );
  }

  // CLS prevention: aspect-ratio from known dimensions
  const aspectStyle: React.CSSProperties =
    width && height ? { aspectRatio: `${width} / ${height}` } : {};

  return (
    <>
      {/* Clickable image with zoom overlay */}
      <Box
        onClick={handleOpen}
        sx={{
          mb: 3,
          textAlign: 'center',
          position: 'relative',
          cursor: 'zoom-in',
          '&:hover .zoom-overlay': { opacity: 1 },
        }}
      >
        <Box
          sx={{
            display: 'inline-block',
            position: 'relative',
            borderRadius: '12px',
            overflow: 'hidden',
            border: '1px solid rgba(0,0,0,0.12)',
            backgroundColor: '#fafafa',
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
          }}
        >
          <img
            src={src}
            alt={alt}
            width={width}
            height={height}
            style={{
              display: 'block',
              maxWidth: '100%',
              minWidth: 'min(280px, 100%)',
              height: 'auto',
              ...aspectStyle,
            }}
            loading="lazy"
            onError={() => setImgError(true)}
          />

          {/* Zoom icon — bottom-right corner */}
          <Box
            className="zoom-overlay"
            sx={{
              position: 'absolute',
              bottom: 8,
              right: 8,
              backgroundColor: 'rgba(0,0,0,0.55)',
              borderRadius: '50%',
              width: 32,
              height: 32,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              opacity: { xs: 0.8, md: 0 },
              transition: 'opacity 0.2s',
            }}
          >
            <ZoomIn sx={{ color: 'white', fontSize: 18 }} />
          </Box>
        </Box>
      </Box>

      {/* Fullscreen zoom modal */}
      <Modal
        open={open}
        onClose={handleClose}
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Box
          onClick={handleClose}
          sx={{
            position: 'relative',
            outline: 'none',
            maxWidth: '95vw',
            maxHeight: '95vh',
          }}
        >
          {/* Close button */}
          <IconButton
            onClick={handleClose}
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
              backgroundColor: 'rgba(0,0,0,0.7)',
              color: 'white',
              zIndex: 1,
              '&:hover': { backgroundColor: 'rgba(0,0,0,0.85)' },
            }}
          >
            <Close />
          </IconButton>

          <img
            src={src}
            alt={alt}
            style={{
              maxWidth: '95vw',
              maxHeight: '90vh',
              objectFit: 'contain',
              borderRadius: '8px',
              backgroundColor: 'white',
              padding: '16px',
              boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            }}
            onClick={(e) => e.stopPropagation()}
            onError={() => setImgError(true)}
          />
        </Box>
      </Modal>
    </>
  );
};

export default QuestionImage;
