/**
 * WCAG 2.1 Level AA Uyumlu Tablo Bileşeni
 * Erişilebilir tablo yapısı ve klavye navigasyonu
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Paper,
  Typography,
  Box,
  IconButton,
  Tooltip,
  Pagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
  Chip,
  useTheme
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  GetApp as ExportIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { useAccessibilitySettings } from '../../hooks/useAccessibilitySettings';
import { useScreenReader } from '../../hooks/useScreenReader';
import { useKeyboardNavigation } from '../../hooks/useKeyboardNavigation';

export interface TableColumn {
  id: string;
  label: string;
  sortable?: boolean;
  width?: string | number;
  align?: 'left' | 'center' | 'right';
  format?: (value: any) => string;
  ariaLabel?: string;
}

export interface TableAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  onClick: (row: any) => void;
  disabled?: (row: any) => boolean;
  ariaLabel?: (row: any) => string;
}

interface AccessibleTableProps {
  columns: TableColumn[];
  data: any[];
  title?: string;
  caption?: string;
  sortBy?: string;
  sortDirection?: 'asc' | 'desc';
  onSort?: (column: string, direction: 'asc' | 'desc') => void;
  paginated?: boolean;
  page?: number;
  pageSize?: number;
  totalCount?: number;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  searchable?: boolean;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  filterable?: boolean;
  filters?: Record<string, any>;
  onFilterChange?: (filters: Record<string, any>) => void;
  actions?: TableAction[];
  selectable?: boolean;
  selectedRows?: string[];
  onSelectionChange?: (selectedIds: string[]) => void;
  loading?: boolean;
  emptyMessage?: string;
  ariaLabel?: string;
  ariaDescribedBy?: string;
}

const AccessibleTable: React.FC<AccessibleTableProps> = ({
  columns,
  data,
  title,
  caption,
  sortBy,
  sortDirection = 'asc',
  onSort,
  paginated = false,
  page = 1,
  pageSize = 10,
  totalCount,
  onPageChange,
  onPageSizeChange,
  searchable = false,
  searchValue = '',
  onSearchChange,
  filterable = false,
  filters = {},
  onFilterChange,
  actions = [],
  selectable = false,
  selectedRows = [],
  onSelectionChange,
  loading = false,
  emptyMessage = 'Veri bulunamadı',
  ariaLabel,
  ariaDescribedBy
}) => {
  const theme = useTheme();
  const { settings } = useAccessibilitySettings();
  const { announce, announceContentChange } = useScreenReader();
  const { focusNext, focusPrevious, focusFirst, focusLast } = useKeyboardNavigation();

  const tableRef = useRef<HTMLTableElement>(null);
  const [focusedCell, setFocusedCell] = useState<{ row: number; col: number } | null>(null);
  const [searchFocused, setSearchFocused] = useState(false);

  // Tablo ID'leri
  const tableId = `accessible-table-${Math.random().toString(36).substr(2, 9)}`;
  const captionId = `${tableId}-caption`;
  const summaryId = `${tableId}-summary`;

  // Sıralama işlevi
  const handleSort = useCallback((columnId: string) => {
    if (!onSort) return;

    const newDirection = sortBy === columnId && sortDirection === 'asc' ? 'desc' : 'asc';
    onSort(columnId, newDirection);

    // Ekran okuyucu duyurusu
    const column = columns.find(col => col.id === columnId);
    if (column) {
      announce(
        `Tablo ${column.label} sütununa göre ${newDirection === 'asc' ? 'artan' : 'azalan'} sırada sıralandı`,
        'polite'
      );
    }
  }, [sortBy, sortDirection, onSort, columns, announce]);

  // Klavye navigasyonu
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (!focusedCell) return;

    const { row, col } = focusedCell;
    const maxRow = data.length - 1;
    const maxCol = columns.length - 1 + (actions.length > 0 ? 1 : 0) + (selectable ? 1 : 0);

    switch (event.key) {
      case 'ArrowUp':
        event.preventDefault();
        if (row > 0) {
          setFocusedCell({ row: row - 1, col });
        }
        break;

      case 'ArrowDown':
        event.preventDefault();
        if (row < maxRow) {
          setFocusedCell({ row: row + 1, col });
        }
        break;

      case 'ArrowLeft':
        event.preventDefault();
        if (col > 0) {
          setFocusedCell({ row, col: col - 1 });
        }
        break;

      case 'ArrowRight':
        event.preventDefault();
        if (col < maxCol) {
          setFocusedCell({ row, col: col + 1 });
        }
        break;

      case 'Home':
        event.preventDefault();
        if (event.ctrlKey) {
          setFocusedCell({ row: 0, col: 0 });
        } else {
          setFocusedCell({ row, col: 0 });
        }
        break;

      case 'End':
        event.preventDefault();
        if (event.ctrlKey) {
          setFocusedCell({ row: maxRow, col: maxCol });
        } else {
          setFocusedCell({ row, col: maxCol });
        }
        break;

      case 'PageUp':
        event.preventDefault();
        setFocusedCell({ row: Math.max(0, row - 10), col });
        break;

      case 'PageDown':
        event.preventDefault();
        setFocusedCell({ row: Math.min(maxRow, row + 10), col });
        break;

      case 'Enter':
      case ' ':
        event.preventDefault();
        // Seçilebilir satır ise seçimi toggle et
        if (selectable && col === 0) {
          const rowId = data[row]?.id;
          if (rowId && onSelectionChange) {
            const newSelection = selectedRows.includes(rowId)
              ? selectedRows.filter(id => id !== rowId)
              : [...selectedRows, rowId];
            onSelectionChange(newSelection);
          }
        }
        break;

      case 'Escape':
        setFocusedCell(null);
        break;
    }
  }, [focusedCell, data, columns, actions, selectable, selectedRows, onSelectionChange]);

  // Hücre odaklanma
  const handleCellFocus = useCallback((row: number, col: number) => {
    setFocusedCell({ row, col });
  }, []);

  // Arama işlevi
  const handleSearchChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    if (onSearchChange) {
      onSearchChange(value);
    }
  }, [onSearchChange]);

  // Sayfa değişimi
  const handlePageChange = useCallback((event: React.ChangeEvent<unknown>, newPage: number) => {
    if (onPageChange) {
      onPageChange(newPage);
      announce(`Sayfa ${newPage}'ye geçildi`, 'polite');
    }
  }, [onPageChange, announce]);

  // Sayfa boyutu değişimi
  const handlePageSizeChange = useCallback((event: any) => {
    const newPageSize = event.target.value;
    if (onPageSizeChange) {
      onPageSizeChange(newPageSize);
      announce(`Sayfa boyutu ${newPageSize} olarak değiştirildi`, 'polite');
    }
  }, [onPageSizeChange, announce]);

  // Veri değişikliklerini duyur
  useEffect(() => {
    if (data.length > 0) {
      announceContentChange(`Tablo güncellendi. ${data.length} satır gösteriliyor.`);
    }
  }, [data.length, announceContentChange]);

  // Tablo özeti oluştur
  const getTableSummary = useCallback(() => {
    const totalRows = totalCount || data.length;
    const selectedCount = selectedRows.length;
    
    let summary = `${totalRows} satır içeren tablo.`;
    
    if (selectable && selectedCount > 0) {
      summary += ` ${selectedCount} satır seçili.`;
    }
    
    if (sortBy) {
      const column = columns.find(col => col.id === sortBy);
      if (column) {
        summary += ` ${column.label} sütununa göre ${sortDirection === 'asc' ? 'artan' : 'azalan'} sırada sıralı.`;
      }
    }
    
    return summary;
  }, [totalCount, data.length, selectedRows.length, selectable, sortBy, sortDirection, columns]);

  return (
    <Box
      role="region"
      aria-label={ariaLabel || title || 'Veri tablosu'}
      aria-describedby={ariaDescribedBy || summaryId}
    >
      {/* Başlık ve Kontroller */}
      {(title || searchable || filterable) && (
        <Box sx={{ mb: 2 }}>
          {title && (
            <Typography variant="h6" component="h2" gutterBottom>
              {title}
            </Typography>
          )}

          <Box sx={{ 
            display: 'flex', 
            gap: 2, 
            alignItems: 'center',
            flexWrap: 'wrap',
            mb: 1
          }}>
            {/* Arama */}
            {searchable && (
              <TextField
                size="small"
                placeholder="Tabloda ara..."
                value={searchValue}
                onChange={handleSearchChange}
                onFocus={() => setSearchFocused(true)}
                onBlur={() => setSearchFocused(false)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                sx={{ minWidth: 200 }}
                aria-label="Tabloda arama yap"
              />
            )}

            {/* Filtreler */}
            {filterable && (
              <IconButton
                aria-label="Filtreleri aç"
                onClick={() => {/* Filter dialog açılacak */}}
              >
                <FilterIcon />
              </IconButton>
            )}

            {/* Export */}
            <IconButton
              aria-label="Tabloyu dışa aktar"
              onClick={() => {/* Export işlemi */}}
            >
              <ExportIcon />
            </IconButton>
          </Box>

          {/* Sayfa boyutu seçimi */}
          {paginated && onPageSizeChange && (
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Sayfa boyutu</InputLabel>
              <Select
                value={pageSize}
                onChange={handlePageSizeChange}
                label="Sayfa boyutu"
              >
                <MenuItem value={10}>10</MenuItem>
                <MenuItem value={25}>25</MenuItem>
                <MenuItem value={50}>50</MenuItem>
                <MenuItem value={100}>100</MenuItem>
              </Select>
            </FormControl>
          )}
        </Box>
      )}

      {/* Tablo Özeti */}
      <Typography
        id={summaryId}
        variant="body2"
        color="textSecondary"
        sx={{ mb: 1, sr: settings.screenReaderOptimized ? 'only' : undefined }}
      >
        {getTableSummary()}
      </Typography>

      {/* Tablo */}
      <TableContainer 
        component={Paper} 
        sx={{ 
          maxHeight: 600,
          '& .MuiTable-root': {
            '& .wcag-aa-target-size': {
              minHeight: 44,
              minWidth: 44,
            }
          }
        }}
      >
        <Table
          ref={tableRef}
          id={tableId}
          stickyHeader
          aria-label={ariaLabel || title || 'Veri tablosu'}
          aria-describedby={captionId}
          onKeyDown={handleKeyDown}
          tabIndex={focusedCell ? -1 : 0}
        >
          {/* Caption */}
          {caption && (
            <caption id={captionId} style={{ captionSide: 'top', textAlign: 'left', padding: 8 }}>
              {caption}
            </caption>
          )}

          {/* Header */}
          <TableHead>
            <TableRow>
              {/* Seçim sütunu */}
              {selectable && (
                <TableCell
                  padding="checkbox"
                  scope="col"
                  aria-label="Satır seçimi"
                >
                  <Typography variant="body2" fontWeight="bold">
                    Seç
                  </Typography>
                </TableCell>
              )}

              {/* Veri sütunları */}
              {columns.map((column) => (
                <TableCell
                  key={column.id}
                  scope="col"
                  align={column.align || 'left'}
                  style={{ width: column.width }}
                  aria-sort={
                    sortBy === column.id
                      ? sortDirection === 'asc'
                        ? 'ascending'
                        : 'descending'
                      : 'none'
                  }
                >
                  {column.sortable && onSort ? (
                    <TableSortLabel
                      active={sortBy === column.id}
                      direction={sortBy === column.id ? sortDirection : 'asc'}
                      onClick={() => handleSort(column.id)}
                      aria-label={`${column.label} sütununa göre sırala`}
                      className="wcag-aa-target-size"
                    >
                      {column.label}
                    </TableSortLabel>
                  ) : (
                    <Typography variant="body2" fontWeight="bold">
                      {column.label}
                    </Typography>
                  )}
                </TableCell>
              ))}

              {/* Aksiyon sütunu */}
              {actions.length > 0 && (
                <TableCell scope="col" align="center" aria-label="İşlemler">
                  <Typography variant="body2" fontWeight="bold">
                    İşlemler
                  </Typography>
                </TableCell>
              )}
            </TableRow>
          </TableHead>

          {/* Body */}
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell 
                  colSpan={columns.length + (selectable ? 1 : 0) + (actions.length > 0 ? 1 : 0)}
                  align="center"
                  sx={{ py: 4 }}
                >
                  <Typography>Yükleniyor...</Typography>
                </TableCell>
              </TableRow>
            ) : data.length === 0 ? (
              <TableRow>
                <TableCell 
                  colSpan={columns.length + (selectable ? 1 : 0) + (actions.length > 0 ? 1 : 0)}
                  align="center"
                  sx={{ py: 4 }}
                >
                  <Typography color="textSecondary">{emptyMessage}</Typography>
                </TableCell>
              </TableRow>
            ) : (
              data.map((row, rowIndex) => {
                const isSelected = selectable && selectedRows.includes(row.id);
                const isFocused = focusedCell?.row === rowIndex;

                return (
                  <TableRow
                    key={row.id || rowIndex}
                    selected={isSelected}
                    hover
                    tabIndex={isFocused ? 0 : -1}
                    aria-selected={selectable ? isSelected : undefined}
                    sx={{
                      '&:focus': {
                        outline: `2px solid ${theme.palette.primary.main}`,
                        outlineOffset: -2,
                      },
                      '&.Mui-selected': {
                        backgroundColor: theme.palette.action.selected,
                      }
                    }}
                  >
                    {/* Seçim hücresi */}
                    {selectable && (
                      <TableCell
                        padding="checkbox"
                        onClick={() => {
                          if (onSelectionChange) {
                            const newSelection = isSelected
                              ? selectedRows.filter(id => id !== row.id)
                              : [...selectedRows, row.id];
                            onSelectionChange(newSelection);
                          }
                        }}
                        onFocus={() => handleCellFocus(rowIndex, 0)}
                        tabIndex={focusedCell?.row === rowIndex && focusedCell?.col === 0 ? 0 : -1}
                        role="gridcell"
                        aria-label={`${isSelected ? 'Seçimi kaldır' : 'Seç'}: Satır ${rowIndex + 1}`}
                        className="wcag-aa-target-size"
                        sx={{
                          cursor: 'pointer',
                          '&:focus': {
                            outline: `2px solid ${theme.palette.primary.main}`,
                            outlineOffset: -2,
                          }
                        }}
                      >
                        <Chip
                          size="small"
                          label={isSelected ? '✓' : '○'}
                          color={isSelected ? 'primary' : 'default'}
                          variant={isSelected ? 'filled' : 'outlined'}
                        />
                      </TableCell>
                    )}

                    {/* Veri hücreleri */}
                    {columns.map((column, colIndex) => {
                      const cellIndex = colIndex + (selectable ? 1 : 0);
                      const value = row[column.id];
                      const formattedValue = column.format ? column.format(value) : value;

                      return (
                        <TableCell
                          key={column.id}
                          align={column.align || 'left'}
                          onFocus={() => handleCellFocus(rowIndex, cellIndex)}
                          tabIndex={focusedCell?.row === rowIndex && focusedCell?.col === cellIndex ? 0 : -1}
                          role="gridcell"
                          aria-label={column.ariaLabel ? column.ariaLabel : `${column.label}: ${formattedValue}`}
                          sx={{
                            '&:focus': {
                              outline: `2px solid ${theme.palette.primary.main}`,
                              outlineOffset: -2,
                            }
                          }}
                        >
                          {formattedValue}
                        </TableCell>
                      );
                    })}

                    {/* Aksiyon hücreleri */}
                    {actions.length > 0 && (
                      <TableCell
                        align="center"
                        onFocus={() => handleCellFocus(rowIndex, columns.length + (selectable ? 1 : 0))}
                        tabIndex={focusedCell?.row === rowIndex && focusedCell?.col === columns.length + (selectable ? 1 : 0) ? 0 : -1}
                        role="gridcell"
                        aria-label="İşlemler"
                      >
                        <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                          {actions.map((action) => {
                            const isDisabled = action.disabled ? action.disabled(row) : false;
                            const ariaLabel = action.ariaLabel ? action.ariaLabel(row) : action.label;

                            return (
                              <Tooltip key={action.id} title={action.label}>
                                <span>
                                  <IconButton
                                    size="small"
                                    onClick={() => action.onClick(row)}
                                    disabled={isDisabled}
                                    aria-label={ariaLabel}
                                    className="wcag-aa-target-size"
                                  >
                                    {action.icon}
                                  </IconButton>
                                </span>
                              </Tooltip>
                            );
                          })}
                        </Box>
                      </TableCell>
                    )}
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      {paginated && totalCount && totalCount > pageSize && (
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          mt: 2,
          flexWrap: 'wrap',
          gap: 2
        }}>
          <Typography variant="body2" color="textSecondary">
            {`${(page - 1) * pageSize + 1}-${Math.min(page * pageSize, totalCount)} / ${totalCount} kayıt`}
          </Typography>
          
          <Pagination
            count={Math.ceil(totalCount / pageSize)}
            page={page}
            onChange={handlePageChange}
            color="primary"
            showFirstButton
            showLastButton
            aria-label="Tablo sayfalama"
          />
        </Box>
      )}

      {/* Klavye kısayolları yardımı */}
      {settings.keyboardNavigation && (
        <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="caption" color="textSecondary">
            <strong>Klavye Kısayolları:</strong> Ok tuşları: Navigasyon | Enter/Space: Seçim | 
            Home/End: Başlangıç/Son | Ctrl+Home/End: Tablo başı/sonu | Esc: Odağı kaldır
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default AccessibleTable;