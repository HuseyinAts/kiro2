/**
 * MasteryConfidenceBar — F13 Mastery Confidence Indicator
 *
 * Renders a horizontal progress bar showing the student's mastery level with
 * a translucent uncertainty band that visualises the 95% confidence interval.
 *
 * Design notes:
 *   - The green/amber/red fill represents the central mastery estimate.
 *   - The gray band overlaid on top of the fill shows the CI extent.
 *   - A compact variant (no text) is provided for use in dense lists.
 *   - When response_count < 5 a Turkish hint is shown urging more practice.
 */

import { Box, Tooltip, Typography } from '@mui/material';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface MasteryConfidenceBarProps {
  /** Mastery estimate in [0, 1]. */
  mastery: number;
  /** Lower bound of the 95% CI mapped to [0, 1].  Use 0 when unknown. */
  confidenceLow: number;
  /** Upper bound of the 95% CI mapped to [0, 1].  Use 1 when unknown. */
  confidenceHigh: number;
  /** Optional subject or topic label rendered above the bar. */
  label?: string;
  /** Number of questions already answered — drives the "need more data" hint. */
  responseCount?: number;
  /** Compact mode: renders only the bar without any surrounding text. */
  compact?: boolean;
}

// ---------------------------------------------------------------------------
// Colour helpers
// ---------------------------------------------------------------------------

/** Return a semantic colour based on mastery level. */
function getMasteryColor(mastery: number): string {
  if (mastery >= 0.7) return '#4CAF50'; // green
  if (mastery >= 0.3) return '#FF9800'; // amber
  return '#F44336'; // red
}

/** Muted variant of the mastery colour used for the CI band border. */
function getMasteryColorMuted(mastery: number): string {
  if (mastery >= 0.7) return 'rgba(76,175,80,0.25)';
  if (mastery >= 0.3) return 'rgba(255,152,0,0.25)';
  return 'rgba(244,67,54,0.25)';
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface BarProps {
  mastery: number;
  confidenceLow: number;
  confidenceHigh: number;
}

/**
 * The visual bar: a background track, a coloured mastery fill, and a
 * translucent CI band positioned absolutely over the track.
 */
function ConfidenceBarTrack({ mastery, confidenceLow, confidenceHigh }: BarProps) {
  const color = getMasteryColor(mastery);
  const bandColor = getMasteryColorMuted(mastery);

  // Convert [0,1] to percentage strings for CSS positioning.
  const masteryPct = `${Math.round(mastery * 100)}%`;
  const bandLeft = `${Math.round(confidenceLow * 100)}%`;
  const bandWidth = `${Math.round((confidenceHigh - confidenceLow) * 100)}%`;

  return (
    <Box
      role="progressbar"
      aria-valuenow={Math.round(mastery * 100)}
      aria-valuemin={0}
      aria-valuemax={100}
      sx={{
        position: 'relative',
        width: '100%',
        height: 10,
        borderRadius: 5,
        bgcolor: 'grey.200',
        overflow: 'hidden',
      }}
    >
      {/* Mastery fill */}
      <Box
        sx={{
          position: 'absolute',
          left: 0,
          top: 0,
          height: '100%',
          width: masteryPct,
          bgcolor: color,
          borderRadius: 5,
          transition: 'width 0.4s ease',
        }}
      />

      {/* CI band — rendered above the fill so it blends visually */}
      <Box
        sx={{
          position: 'absolute',
          left: bandLeft,
          top: 0,
          height: '100%',
          width: bandWidth,
          bgcolor: bandColor,
          border: `1px solid ${color}`,
          borderRadius: 2,
          opacity: 0.9,
          pointerEvents: 'none',
        }}
      />
    </Box>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

/**
 * Mastery confidence bar with optional label and data-sufficiency hint.
 *
 * @example
 * // Standard usage in a topic list
 * <MasteryConfidenceBar
 *   mastery={0.72}
 *   confidenceLow={0.58}
 *   confidenceHigh={0.86}
 *   label="Türev"
 *   responseCount={14}
 * />
 *
 * @example
 * // Compact (bar only) for use inside table cells
 * <MasteryConfidenceBar
 *   mastery={0.45}
 *   confidenceLow={0.30}
 *   confidenceHigh={0.60}
 *   compact
 * />
 */
export function MasteryConfidenceBar({
  mastery,
  confidenceLow,
  confidenceHigh,
  label,
  responseCount,
  compact = false,
}: MasteryConfidenceBarProps) {
  // Clamp all values to [0, 1] defensively.
  const m = Math.min(1, Math.max(0, mastery));
  const lo = Math.min(1, Math.max(0, confidenceLow));
  const hi = Math.min(1, Math.max(0, Math.max(lo, confidenceHigh)));

  const color = getMasteryColor(m);
  const masteryPct = Math.round(m * 100);
  const uncertaintyPct = Math.round((hi - lo) * 100);
  const needsMoreData = typeof responseCount === 'number' && responseCount < 5;

  // Tooltip text shown on hover regardless of compact mode.
  const tooltipText =
    `Hakimiyet: %${masteryPct} ± %${uncertaintyPct} (95% GA)` +
    (typeof responseCount === 'number' ? ` | ${responseCount} soru` : '');

  const bar = (
    <Tooltip title={tooltipText} arrow placement="top">
      <Box sx={{ width: '100%', cursor: 'default' }}>
        <ConfidenceBarTrack
          mastery={m}
          confidenceLow={lo}
          confidenceHigh={hi}
        />
      </Box>
    </Tooltip>
  );

  if (compact) {
    return bar;
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* Label row */}
      {label && (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'baseline',
            mb: 0.5,
          }}
        >
          <Typography variant="body2" fontWeight={600} noWrap>
            {label}
          </Typography>

          <Typography
            variant="caption"
            fontWeight={700}
            sx={{ color, ml: 1, whiteSpace: 'nowrap' }}
          >
            %{masteryPct}{' '}
            <Typography
              component="span"
              variant="caption"
              color="text.secondary"
              fontWeight={400}
            >
              ± %{uncertaintyPct}
            </Typography>
          </Typography>
        </Box>
      )}

      {/* Bar */}
      {bar}

      {/* Response count + optional hint */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mt: 0.5,
        }}
      >
        {typeof responseCount === 'number' ? (
          <Typography variant="caption" color="text.secondary">
            {responseCount} soru
          </Typography>
        ) : (
          <Box />
        )}

        {needsMoreData && (
          <Typography
            variant="caption"
            sx={{
              color: 'warning.main',
              fontStyle: 'italic',
              fontSize: '0.65rem',
            }}
          >
            Daha fazla soru çöz
          </Typography>
        )}
      </Box>
    </Box>
  );
}

export default MasteryConfidenceBar;
