import React, { useState, useMemo } from 'react';
import './DataTable.css';

interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  emptyMessage?: string;
  error?: string | null;
  searchPlaceholder?: string;
  onSearch?: (query: string) => void;
  searchValue?: string;
  onSort?: (key: string, order: 'asc' | 'desc') => void;
  sortKey?: string;
  sortOrder?: 'asc' | 'desc';
  page?: number;
  pageSize?: number;
  total?: number;
  onPageChange?: (page: number) => void;
  onRowClick?: (row: T) => void;
}

export function DataTable<T extends object>({
  columns,
  data,
  loading = false,
  emptyMessage = 'No data found',
  error,
  searchPlaceholder = 'Search...',
  onSearch,
  searchValue,
  onSort,
  sortKey,
  sortOrder = 'desc',
  page = 1,
  pageSize = 50,
  total = 0,
  onPageChange,
  onRowClick,
}: DataTableProps<T>) {
  const [localSearch, setLocalSearch] = useState('');
  const displaySearch = searchValue !== undefined ? searchValue : localSearch;

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setLocalSearch(v);
    onSearch?.(v);
  };

  const handleSort = (key: string) => {
    if (!onSort) return;
    const newOrder = sortKey === key && sortOrder === 'asc' ? 'desc' : 'asc';
    onSort(key, newOrder);
  };

  return (
    <div className="data-table-wrapper">
      {/* Search bar */}
      {onSearch && (
        <div className="data-table__search">
          <svg className="data-table__search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
          </svg>
          <input
            type="text"
            className="data-table__search-input"
            placeholder={searchPlaceholder}
            value={displaySearch}
            onChange={handleSearch}
          />
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="data-table__error">
          <span>⚠</span> {error}
        </div>
      )}

      {/* Table */}
      <div className="data-table__container">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`data-table__th ${col.sortable ? 'data-table__th--sortable' : ''} ${sortKey === col.key ? 'data-table__th--active' : ''}`}
                  style={col.width ? { width: col.width } : undefined}
                  onClick={col.sortable ? () => handleSort(col.key) : undefined}
                >
                  <span className="text-label-caps">{col.header}</span>
                  {col.sortable && sortKey === col.key && (
                    <span className="data-table__sort-indicator">
                      {sortOrder === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={`skeleton-${i}`} className="data-table__row--skeleton">
                  {columns.map((col) => (
                    <td key={col.key}><div className="skeleton" style={{ height: 16, width: '80%' }} /></td>
                  ))}
                </tr>
              ))
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="data-table__empty">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row, idx) => (
                <tr
                  key={((row as any).id as string | number) || idx}
                  className={`data-table__row ${onRowClick ? 'data-table__row--clickable' : ''}`}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                >
                  {columns.map((col) => (
                    <td key={col.key} className="data-table__td">
                      {col.render ? col.render(row) : String((row as any)[col.key] ?? '—')}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {total > pageSize && onPageChange && (
        <div className="data-table__pagination">
          <span className="text-body-sm" style={{ color: 'var(--on-surface-variant)' }}>
            Showing {Math.min((page - 1) * pageSize + 1, total)}–{Math.min(page * pageSize, total)} of {total}
          </span>
          <div className="data-table__pagination-buttons">
            <button
              className="data-table__page-btn"
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
            >
              ← Prev
            </button>
            <span className="text-data-md">{page} / {totalPages}</span>
            <button
              className="data-table__page-btn"
              disabled={page >= totalPages}
              onClick={() => onPageChange(page + 1)}
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
