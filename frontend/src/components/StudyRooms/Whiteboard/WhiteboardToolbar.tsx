/**
 * WhiteboardToolbar Component
 *
 * Toolbar for the collaborative whiteboard with drawing tools,
 * shape tools, text/equation tools, color picker, and zoom controls.
 */

import {
  Create as PenIcon,
  Highlight as HighlightIcon,
  Square as RectangleIcon,
  Circle as CircleIcon,
  Timeline as LineIcon,
  TextFields as TextIcon,
  Functions as EquationIcon,
  Undo as UndoIcon,
  Delete as DeleteIcon,
  Clear as ClearIcon,
  SaveAlt as SaveIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  ColorLens as ColorIcon,
} from '@mui/icons-material';
import {
  Paper,
  IconButton,
  Typography,
  Tooltip,
  Slider,
  Divider,
  ToggleButton,
  ToggleButtonGroup,
  Popover,
  Box,
} from '@mui/material';
import * as React from 'react';
import {  useState  } from 'react';

import {
  WhiteboardToolbarProps,
  WhiteboardTool,
  ShapeType,
  DEFAULT_COLORS,
  MIN_STROKE_WIDTH,
  MAX_STROKE_WIDTH,
} from './types';

const WhiteboardToolbar: React.FC<WhiteboardToolbarProps> = ({
  tool,
  shapeType,
  color,
  strokeWidth,
  zoom,
  canUndo,
  onToolChange,
  onShapeTypeChange,
  onColorChange,
  onStrokeWidthChange,
  onZoomIn,
  onZoomOut,
  onUndo,
  onClear,
  onSave,
}) => {
  const [colorAnchorEl, setColorAnchorEl] = useState<null | HTMLElement>(null);

  const handleToolChange = (_e: React.MouseEvent<HTMLElement>, value: WhiteboardTool | null) => {
    if (value) {
      onToolChange(value);
    }
  };

  const handleShapeToolChange = (_e: React.MouseEvent<HTMLElement>, value: string | null) => {
    if (value && ['rectangle', 'circle', 'line', 'arrow'].includes(value)) {
      onToolChange('shape');
      onShapeTypeChange(value as ShapeType);
    }
  };

  const handleColorSelect = (selectedColor: string) => {
    onColorChange(selectedColor);
    setColorAnchorEl(null);
  };

  return (
    <Paper sx={{ p: 1, display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
      {/* Drawing Tools */}
      <ToggleButtonGroup
        value={tool}
        exclusive
        onChange={handleToolChange}
        size="small"
        aria-label="Cizim araclari"
      >
        <ToggleButton value="pen" aria-label="Kalem">
          <Tooltip title="Kalem">
            <PenIcon />
          </Tooltip>
        </ToggleButton>
        <ToggleButton value="highlighter" aria-label="Fosforlu kalem">
          <Tooltip title="Fosforlu Kalem">
            <HighlightIcon />
          </Tooltip>
        </ToggleButton>
        <ToggleButton value="eraser" aria-label="Silgi">
          <Tooltip title="Silgi">
            <DeleteIcon />
          </Tooltip>
        </ToggleButton>
      </ToggleButtonGroup>

      <Divider orientation="vertical" flexItem />

      {/* Shape Tools */}
      <ToggleButtonGroup
        value={tool === 'shape' ? shapeType : null}
        exclusive
        onChange={handleShapeToolChange}
        size="small"
        aria-label="Sekil araclari"
      >
        <ToggleButton value="rectangle" aria-label="Dikdortgen">
          <Tooltip title="Dikdortgen">
            <RectangleIcon />
          </Tooltip>
        </ToggleButton>
        <ToggleButton value="circle" aria-label="Daire">
          <Tooltip title="Daire">
            <CircleIcon />
          </Tooltip>
        </ToggleButton>
        <ToggleButton value="line" aria-label="Cizgi">
          <Tooltip title="Cizgi">
            <LineIcon />
          </Tooltip>
        </ToggleButton>
      </ToggleButtonGroup>

      <Divider orientation="vertical" flexItem />

      {/* Text & Equation Tools */}
      <ToggleButtonGroup
        value={tool}
        exclusive
        onChange={handleToolChange}
        size="small"
        aria-label="Metin araclari"
      >
        <ToggleButton value="text" aria-label="Metin">
          <Tooltip title="Metin">
            <TextIcon />
          </Tooltip>
        </ToggleButton>
        <ToggleButton value="equation" aria-label="Denklem">
          <Tooltip title="Denklem (LaTeX)">
            <EquationIcon />
          </Tooltip>
        </ToggleButton>
      </ToggleButtonGroup>

      <Divider orientation="vertical" flexItem />

      {/* Color Picker */}
      <IconButton
        onClick={(e) => setColorAnchorEl(e.currentTarget)}
        size="small"
        aria-label="Renk sec"
        aria-haspopup="true"
      >
        <ColorIcon sx={{ color: color }} />
      </IconButton>

      <Popover
        open={Boolean(colorAnchorEl)}
        anchorEl={colorAnchorEl}
        onClose={() => setColorAnchorEl(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Box sx={{ p: 2, display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 1 }}>
          {DEFAULT_COLORS.map((c) => (
            <Box
              key={c}
              onClick={() => handleColorSelect(c)}
              role="button"
              tabIndex={0}
              aria-label={`Renk: ${c}`}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  handleColorSelect(c);
                }
              }}
              sx={{
                width: 32,
                height: 32,
                bgcolor: c,
                border: color === c ? 3 : 1,
                borderColor: color === c ? 'primary.main' : 'divider',
                cursor: 'pointer',
                borderRadius: 1,
                '&:hover': {
                  transform: 'scale(1.1)',
                },
                '&:focus': {
                  outline: '2px solid',
                  outlineColor: 'primary.main',
                  outlineOffset: 2,
                },
              }}
            />
          ))}
        </Box>
      </Popover>

      {/* Stroke Width Slider */}
      <Box sx={{ width: 120, mx: 1 }}>
        <Typography variant="caption" id="stroke-width-slider">
          Kalinlik: {strokeWidth}px
        </Typography>
        <Slider
          value={strokeWidth}
          onChange={(_e, value) => onStrokeWidthChange(value as number)}
          min={MIN_STROKE_WIDTH}
          max={MAX_STROKE_WIDTH}
          size="small"
          aria-labelledby="stroke-width-slider"
        />
      </Box>

      <Divider orientation="vertical" flexItem />

      {/* Action Buttons */}
      <Tooltip title="Geri Al">
        <span>
          <IconButton onClick={onUndo} size="small" disabled={!canUndo} aria-label="Geri al">
            <UndoIcon />
          </IconButton>
        </span>
      </Tooltip>
      <Tooltip title="Temizle">
        <IconButton onClick={onClear} size="small" aria-label="Tahtayi temizle">
          <ClearIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="Kaydet">
        <IconButton onClick={onSave} size="small" aria-label="Tahtayi kaydet">
          <SaveIcon />
        </IconButton>
      </Tooltip>

      <Divider orientation="vertical" flexItem />

      {/* Zoom Controls */}
      <Tooltip title="Yakinlastir">
        <IconButton onClick={onZoomIn} size="small" aria-label="Yakinlastir">
          <ZoomInIcon />
        </IconButton>
      </Tooltip>
      <Typography variant="caption" aria-live="polite">
        {Math.round(zoom * 100)}%
      </Typography>
      <Tooltip title="Uzaklastir">
        <IconButton onClick={onZoomOut} size="small" aria-label="Uzaklastir">
          <ZoomOutIcon />
        </IconButton>
      </Tooltip>
    </Paper>
  );
};

export default WhiteboardToolbar;
