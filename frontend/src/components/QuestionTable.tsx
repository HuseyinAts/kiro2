/**
 * QuestionTable Component
 *
 * Renders markdown tables from visual_content for ÖSYM-style questions.
 * Phase 1: Tables implementation.
 *
 * Features:
 * - Parses markdown table syntax
 * - Responsive design (mobile + desktop)
 * - WCAG 2.1 AA accessibility compliant
 * - Print-friendly styles
 * - Proper Turkish language support
 */

import * as React from 'react';
import './QuestionTable.css';

interface VisualContent {
  type: string;
  format: string;
  content: string;
  data?: any;
  metadata: {
    caption: string;
    alt_text: string;
    rows: number;
    columns: number;
  };
}

interface QuestionTableProps {
  visualContent: VisualContent;
  className?: string;
}

/**
 * Parse markdown table to HTML structure
 */
function parseMarkdownTable(markdown: string): { headers: string[]; rows: string[][] } {
  const lines = markdown.trim().split('\n');

  if (lines.length < 3) {
    console.warn('Invalid markdown table format');
    return { headers: [], rows: [] };
  }

  // Parse headers (first line)
  const headerLine = lines[0];
  const headers = headerLine
    .split('|')
    .map(cell => cell.trim())
    .filter(cell => cell !== '');

  // Skip separator line (second line with ---)
  // Parse data rows (remaining lines)
  const rows: string[][] = [];
  for (let i = 2; i < lines.length; i++) {
    const row = lines[i]
      .split('|')
      .map(cell => cell.trim())
      .filter(cell => cell !== '');

    if (row.length > 0) {
      rows.push(row);
    }
  }

  return { headers, rows };
}

/**
 * QuestionTable Component
 */
export const QuestionTable: React.FC<QuestionTableProps> = ({
  visualContent,
  className = '',
}) => {
  if (!visualContent || visualContent.type !== 'table') {
    return null;
  }

  const { headers, rows } = parseMarkdownTable(visualContent.content);

  if (headers.length === 0 && rows.length === 0) {
    return (
      <div className="question-table-error" role="alert">
        <p>Tablo görüntülenemiyor.</p>
      </div>
    );
  }

  return (
    <figure className={`question-table-wrapper ${className}`}>
      {/* Caption */}
      {visualContent.metadata.caption && (
        <figcaption className="question-table-caption">
          {visualContent.metadata.caption}
        </figcaption>
      )}

      {/* Table */}
      <div className="question-table-container">
        <table
          className="question-table"
          role="table"
          aria-label={visualContent.metadata.alt_text || visualContent.metadata.caption}
        >
          {/* Table Header */}
          <thead>
            <tr role="row">
              {headers.map((header, index) => (
                <th
                  key={`header-${index}`}
                  scope="col"
                  role="columnheader"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>

          {/* Table Body */}
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={`row-${rowIndex}`} role="row">
                {row.map((cell, cellIndex) => (
                  <td
                    key={`cell-${rowIndex}-${cellIndex}`}
                    role="cell"
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Metadata for screen readers */}
      <div className="sr-only" aria-live="polite">
        Tablo: {visualContent.metadata.rows} satır, {visualContent.metadata.columns} sütun
      </div>
    </figure>
  );
};

export default QuestionTable;
