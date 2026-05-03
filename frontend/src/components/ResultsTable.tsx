import { useMemo, useState } from 'react';
import type { QueryResult } from '../types';

const PAGE_SIZE = 25;

interface ResultsTableProps {
  result: QueryResult;
}

type SortDirection = 'asc' | 'desc';

export function ResultsTable({ result }: ResultsTableProps) {
  const [page, setPage] = useState(1);
  const [sortCol, setSortCol] = useState<number | null>(null);
  const [sortDir, setSortDir] = useState<SortDirection>('asc');

  const sortedRows = useMemo(() => {
    if (sortCol === null) return result.rows;
    const sorted = [...result.rows].sort((a, b) => {
      const av = a[sortCol];
      const bv = b[sortCol];
      if (av === bv) return 0;
      if (av === null) return 1;
      if (bv === null) return -1;
      const cmp = av < bv ? -1 : 1;
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return sorted;
  }, [result.rows, sortCol, sortDir]);

  const pagedRows = useMemo(
    () => sortedRows.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [sortedRows, page],
  );

  const totalPages = Math.max(1, Math.ceil(result.rows.length / PAGE_SIZE));

  const handleSort = (colIndex: number) => {
    if (sortCol === colIndex) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortCol(colIndex);
      setSortDir('asc');
    }
  };

  if (result.row_count === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-lg p-6 text-center">
        <div className="text-slate-500">No rows returned.</div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              {result.columns.map((col, idx) => (
                <th
                  key={col}
                  onClick={() => handleSort(idx)}
                  className="px-4 py-2.5 text-left font-semibold text-slate-700
                             cursor-pointer hover:bg-slate-100 select-none"
                >
                  <div className="flex items-center gap-1">
                    {col}
                    <span className="text-slate-400 text-xs">
                      {sortCol === idx ? (sortDir === 'asc' ? '▲' : '▼') : '⇅'}
                    </span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {pagedRows.map((row, rowIdx) => (
              <tr key={rowIdx} className="hover:bg-slate-50">
                {row.map((cell, cellIdx) => (
                  <td key={cellIdx} className="px-4 py-2 text-slate-900 font-mono text-xs">
                    {cell === null ? <span className="text-slate-400 italic">null</span> : String(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="px-4 py-2.5 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-600">
        <div>
          Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, result.row_count)} of{' '}
          {result.row_count}
          {result.truncated && <span className="ml-2 text-amber-600">(truncated to first 1000)</span>}
        </div>
        {totalPages > 1 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-2 py-1 border border-slate-300 rounded hover:bg-white disabled:opacity-40"
            >
              ←
            </button>
            <span>
              Page {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-2 py-1 border border-slate-300 rounded hover:bg-white disabled:opacity-40"
            >
              →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
