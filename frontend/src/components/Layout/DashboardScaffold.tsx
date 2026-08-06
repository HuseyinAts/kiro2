import { ReactNode } from 'react';
import { Box, Container, Typography } from '@mui/material';
import { motion } from 'framer-motion';
import { ModernLoader } from '../ui/ModernLoader';
import { KiroThemeProvider } from '../../kiro/ui/theme';
import { color, font } from '../../kiro/tokens';

export interface DashboardScaffoldProps {
  loading?: boolean;
  loadingMessage?: string;
  icon: ReactNode;
  iconGradient?: string;
  title: string;
  titleGradient?: string;
  subtitle: string;
  children: ReactNode;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false;
  headerActions?: ReactNode;
}

export function DashboardScaffold({
  loading,
  loadingMessage = 'Yükleniyor...',
  icon,
  iconGradient = color.dawn.coralCtaBg,
  title,
  subtitle,
  children,
  maxWidth = 'lg',
  headerActions,
}: DashboardScaffoldProps) {
  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: color.paper.bg,
        }}
      >
        <ModernLoader message={loadingMessage} size="large" />
      </Box>
    );
  }

  return (
    <KiroThemeProvider theme="paper">
      <Box
        className="k-paper"
        sx={{
          minHeight: '100vh',
          background: color.paper.bg,
          color: color.ink.primary,
          fontFamily: font.sans,
          py: 4,
        }}
      >
        <Container maxWidth={maxWidth}>
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <Box
              sx={{
                mb: 4,
                p: 3,
                borderRadius: '16px',
                background: 'var(--k-surface, #FFFFFF)',
                border: `1px solid ${color.paper.borderFaint}`,
                boxShadow: '0 2px 12px rgba(42, 36, 51, 0.04)',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2.5 }}>
                <Box
                  sx={{
                    width: 52,
                    height: 52,
                    borderRadius: '14px',
                    background: iconGradient,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#ffffff',
                    flexShrink: 0,
                    boxShadow: `0 4px 14px ${color.dawn.coralCtaBg}40`,
                    '& > svg': {
                      fontSize: 28,
                      color: 'white',
                    },
                  }}
                >
                  {icon}
                </Box>
                <Box sx={{ flex: 1 }}>
                  <Typography
                    variant="h4"
                    sx={{
                      fontWeight: 800,
                      fontSize: '1.75rem',
                      letterSpacing: '-0.02em',
                      color: color.ink.primary,
                      fontFamily: font.sans,
                    }}
                  >
                    {title}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      color: color.ink.muted,
                      fontFamily: font.sans,
                      fontSize: '0.925rem',
                      mt: 0.5,
                    }}
                  >
                    {subtitle}
                  </Typography>
                </Box>
                {headerActions && <Box>{headerActions}</Box>}
              </Box>
            </Box>
          </motion.div>

          {children}
        </Container>
      </Box>
    </KiroThemeProvider>
  );
}

export default DashboardScaffold;
