/**
 * WCAG 2.1 Level AA Uyumlu Modal Bileşeni
 * Focus trap ve klavye navigasyonu
 */

import React, { useEffect, useRef, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Typography,
  Box,
  useTheme,
  Fade,
  Backdrop
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { useAccessibilitySettings } from '../../hooks/useAccessibilitySettings';
import { useScreenReader } from '../../hooks/useScreenReader';
import { useFocusTrap } from '../../hooks/useFocusTrap';

interface AccessibleModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  fullWidth?: boolean;
  fullScreen?: boolean;
  disableEscapeKeyDown?: boolean;
  disableBackdropClick?: boolean;
  showCloseButton?: boolean;
  ariaLabelledBy?: string;
  ariaDescribedBy?: string;
  className?: string;
}

const AccessibleModal: React.FC<AccessibleModalProps> = ({
  open,
  onClose,
  title,
  description,
  children,
  actions,
  maxWidth = 'sm',
  fullWidth = true,
  fullScreen = false,
  disableEscapeKeyDown = false,
  disableBackdropClick = false,
  showCloseButton = true,
  ariaLabelledBy,
  ariaDescribedBy,
  className
}) => {
  const theme = useTheme();
  const { settings } = useAccessibilitySettings();
  const { announce, manageFocus } = useScreenReader();

  const titleRef = useRef<HTMLHeadingElement>(null);

  // Modal ID'leri
  const modalId = `modal-${Math.random().toString(36).substr(2, 9)}`;
  const titleId = ariaLabelledBy || `${modalId}-title`;
  const descriptionId = ariaDescribedBy || (description ? `${modalId}-description` : undefined);

  // Focus trap with automatic focus restoration
  const dialogRef = useFocusTrap<HTMLDivElement>({
    enabled: open,
    autoFocus: true,
    returnFocus: true,
    escapeDeactivates: !disableEscapeKeyDown,
    onEscape: disableEscapeKeyDown ? undefined : onClose,
    initialFocus: titleRef.current || undefined,
  });

  // Modal açıldığında
  useEffect(() => {
    if (open) {
      // Modal açıldığını duyur
      announce(`Modal açıldı: ${title}`, 'polite');

      // İlk odaklanabilir elemente odaklan
      setTimeout(() => {
        if (titleRef.current) {
          manageFocus(titleRef.current, `${title} modalı açıldı`);
        }
      }, 100);
    } else {
      // Modal kapatıldığını duyur
      announce('Modal kapatıldı', 'polite');
    }
  }, [open, title, announce, manageFocus]);

  // Klavye event handler (useFocusTrap already handles Escape)
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    // Additional keyboard handling can be added here if needed
    // Escape key is already handled by useFocusTrap hook
  }, []);

  // Backdrop tıklama
  const handleBackdropClick = useCallback((event: React.MouseEvent) => {
    if (!disableBackdropClick) {
      onClose();
    }
  }, [onClose, disableBackdropClick]);

  // Close button handler
  const handleCloseClick = useCallback(() => {
    onClose();
  }, [onClose]);

  return (
    <Dialog
      ref={dialogRef}
      open={open}
      onClose={onClose}
      maxWidth={maxWidth}
      fullWidth={fullWidth}
      fullScreen={fullScreen}
      className={className}
      onKeyDown={handleKeyDown}
      aria-labelledby={titleId}
      aria-describedby={descriptionId}
      aria-modal="true"
      role="dialog"
      TransitionComponent={settings.reducedMotion ? undefined : Fade}
      TransitionProps={{
        timeout: settings.reducedMotion ? 0 : 300
      }}
      BackdropComponent={Backdrop}
      BackdropProps={{
        onClick: handleBackdropClick,
        sx: {
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          backdropFilter: 'blur(2px)'
        }
      }}
      PaperProps={{
        sx: {
          borderRadius: 2,
          boxShadow: theme.shadows[24],
          '&:focus': {
            outline: `2px solid ${theme.palette.primary.main}`,
            outlineOffset: 2
          },
          '& .wcag-aa-target-size': {
            minHeight: 44,
            minWidth: 44,
          }
        }
      }}
    >
      {/* Modal Header */}
      <DialogTitle
        id={titleId}
        ref={titleRef}
        tabIndex={-1}
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          pb: 1,
          fontSize: settings.fontSize === 'large' ? '1.5rem' : '1.25rem'
        }}
      >
        <Typography
          variant="h4"
          component="h2"
          sx={{
            fontSize: 'inherit',
            fontWeight: 'bold',
            flex: 1,
            pr: showCloseButton ? 2 : 0
          }}
        >
          {title}
        </Typography>
        
        {showCloseButton && (
          <IconButton
            onClick={handleCloseClick}
            aria-label="Modalı kapat"
            className="wcag-aa-target-size"
            sx={{
              color: 'text.secondary',
              '&:hover': {
                backgroundColor: 'action.hover'
              }
            }}
          >
            <CloseIcon />
          </IconButton>
        )}
      </DialogTitle>

      {/* Modal Description */}
      {description && (
        <Box sx={{ px: 3, pb: 1 }}>
          <Typography
            id={descriptionId}
            variant="body2"
            color="text.secondary"
            sx={{
              fontSize: settings.fontSize === 'large' ? '1.1rem' : '0.875rem'
            }}
          >
            {description}
          </Typography>
        </Box>
      )}

      {/* Modal Content */}
      <DialogContent
        sx={{
          px: 3,
          py: 2,
          '&:focus': {
            outline: 'none'
          }
        }}
      >
        <Box
          sx={{
            fontSize: settings.fontSize === 'large' ? '1.1rem' : '1rem',
            lineHeight: settings.screenReaderOptimized ? 1.8 : 1.5
          }}
        >
          {children}
        </Box>
      </DialogContent>

      {/* Modal Actions */}
      {actions && (
        <DialogActions
          sx={{
            px: 3,
            pb: 3,
            pt: 1,
            gap: 1,
            justifyContent: 'flex-end',
            flexWrap: 'wrap'
          }}
        >
          {actions}
        </DialogActions>
      )}

      {/* Klavye kısayolları yardımı */}
      {settings.keyboardNavigation && (
        <Box
          sx={{
            position: 'absolute',
            bottom: 8,
            left: 8,
            right: 8,
            textAlign: 'center',
            opacity: 0.7
          }}
        >
          <Typography variant="caption" color="text.secondary">
            <strong>Klavye:</strong> Tab: Navigasyon | Enter: Seç | Esc: Kapat
          </Typography>
        </Box>
      )}
    </Dialog>
  );
};

export default AccessibleModal;