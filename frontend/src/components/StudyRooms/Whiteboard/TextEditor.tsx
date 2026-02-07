/**
 * TextEditor Component
 *
 * Text and LaTeX equation editor for the whiteboard.
 * Provides input dialogs for adding text and mathematical equations.
 */

import { Box, TextField, Button, Typography } from '@mui/material';
import * as React from 'react';
import {  useEffect, useRef  } from 'react';

import { TextEditorProps, Point, TextElement, EquationElement } from './types';

const TextEditor: React.FC<TextEditorProps> = ({
  position,
  zoom,
  pan,
  textInput,
  latexInput,
  tool,
  onTextChange,
  onLatexChange,
  onSubmit,
  onCancel,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus input when editor opens
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, [position]);

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    } else if (e.key === 'Escape') {
      onCancel();
    }
  };

  // Calculate position in screen coordinates
  const screenPosition = {
    top: position.y * zoom + pan.y,
    left: position.x * zoom + pan.x,
  };

  if (tool === 'text') {
    return (
      <Box
        sx={{
          position: 'absolute',
          top: screenPosition.top,
          left: screenPosition.left,
          bgcolor: 'background.paper',
          p: 2,
          borderRadius: 1,
          boxShadow: 3,
          zIndex: 1000,
          minWidth: 250,
        }}
        role="dialog"
        aria-labelledby="text-editor-title"
      >
        <Typography id="text-editor-title" variant="subtitle2" gutterBottom>
          Metin Ekle
        </Typography>
        <TextField
          inputRef={inputRef}
          autoFocus
          placeholder="Metin girin..."
          value={textInput}
          onChange={(e) => onTextChange(e.target.value)}
          onKeyDown={handleKeyDown}
          size="small"
          fullWidth
          aria-label="Metin icerigi"
        />
        <Box sx={{ display: 'flex', gap: 1, mt: 1, justifyContent: 'flex-end' }}>
          <Button size="small" onClick={onCancel}>
            Iptal
          </Button>
          <Button
            size="small"
            variant="contained"
            onClick={onSubmit}
            disabled={!textInput.trim()}
          >
            Ekle
          </Button>
        </Box>
      </Box>
    );
  }

  if (tool === 'equation') {
    return (
      <Box
        sx={{
          position: 'absolute',
          top: screenPosition.top,
          left: screenPosition.left,
          bgcolor: 'background.paper',
          p: 2,
          borderRadius: 1,
          boxShadow: 3,
          zIndex: 1000,
          minWidth: 300,
        }}
        role="dialog"
        aria-labelledby="equation-editor-title"
      >
        <Typography id="equation-editor-title" variant="subtitle2" gutterBottom>
          LaTeX Denklem Ekle
        </Typography>
        <TextField
          inputRef={inputRef}
          autoFocus
          placeholder="LaTeX kodu girin... (orn: x^2 + y^2 = r^2)"
          value={latexInput}
          onChange={(e) => onLatexChange(e.target.value)}
          onKeyDown={handleKeyDown}
          size="small"
          fullWidth
          multiline
          rows={2}
          aria-label="LaTeX kodu"
        />
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Ornekler: x^2, \frac{'{a}{b}'}, \sqrt{'{x}'}, \sum_{'{i=1}'}^{'{n}'} i
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, mt: 1, justifyContent: 'flex-end' }}>
          <Button size="small" onClick={onCancel}>
            Iptal
          </Button>
          <Button
            size="small"
            variant="contained"
            onClick={onSubmit}
            disabled={!latexInput.trim()}
          >
            Ekle
          </Button>
        </Box>
      </Box>
    );
  }

  return null;
};

// ============================================================
// Text Element Creation Helpers
// ============================================================

/**
 * Create a new text element
 */
export const createTextElement = (
  position: Point,
  content: string,
  fontSize: number,
  color: string,
  fontFamily: string = 'Arial',
): TextElement => ({
  id: `text-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
  position,
  content,
  fontSize,
  color,
  fontFamily,
});

/**
 * Create a new equation element
 */
export const createEquationElement = (
  position: Point,
  latex: string,
  fontSize: number,
  color: string,
): EquationElement => ({
  id: `equation-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
  position,
  latex,
  fontSize,
  color,
});

// ============================================================
// Text Rendering Helpers
// ============================================================

/**
 * Render text on canvas
 */
export const renderText = (
  ctx: CanvasRenderingContext2D,
  text: TextElement,
): void => {
  ctx.font = `${text.fontSize}px ${text.fontFamily}`;
  ctx.fillStyle = text.color;
  ctx.fillText(text.content, text.position.x, text.position.y);
};

/**
 * Render equation on canvas (simplified - in production use KaTeX or MathJax)
 */
export const renderEquation = (
  ctx: CanvasRenderingContext2D,
  equation: EquationElement,
): void => {
  ctx.font = `${equation.fontSize}px Arial`;
  ctx.fillStyle = equation.color;
  // Simplified rendering - in production, use KaTeX or MathJax for proper LaTeX rendering
  ctx.fillText(`LaTeX: ${equation.latex}`, equation.position.x, equation.position.y);
};

/**
 * Measure text dimensions
 */
export const measureText = (
  ctx: CanvasRenderingContext2D,
  text: string,
  fontSize: number,
  fontFamily: string = 'Arial',
): { width: number; height: number } => {
  ctx.font = `${fontSize}px ${fontFamily}`;
  const metrics = ctx.measureText(text);
  return {
    width: metrics.width,
    height: fontSize, // Approximation
  };
};

// ============================================================
// Common LaTeX Templates
// ============================================================

export const LATEX_TEMPLATES = {
  fraction: '\\frac{a}{b}',
  squareRoot: '\\sqrt{x}',
  nthRoot: '\\sqrt[n]{x}',
  power: 'x^{n}',
  subscript: 'x_{i}',
  sum: '\\sum_{i=1}^{n} i',
  integral: '\\int_{a}^{b} f(x) dx',
  limit: '\\lim_{x \\to \\infty} f(x)',
  matrix: '\\begin{matrix} a & b \\\\ c & d \\end{matrix}',
  quadraticFormula: 'x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}',
  pythagorean: 'a^2 + b^2 = c^2',
  circleArea: 'A = \\pi r^2',
  sine: '\\sin(\\theta)',
  cosine: '\\cos(\\theta)',
  tangent: '\\tan(\\theta)',
} as const;

export default TextEditor;
