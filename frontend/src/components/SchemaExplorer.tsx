import { useState } from 'react';
import { useSchema } from '../hooks/useSchema';
import type { TableSchema } from '../types';

export function SchemaExplorer() {
  const { schema, loading, error } = useSchema();
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const toggle = (table: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(table)) next.delete(table);
      else next.add(table);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="bg-white border border-slate-200 rounded-lg p-4">
        <div className="text-sm text-slate-500">Loading schema...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-slate-200 rounded-lg p-4">
        <div className="text-sm text-red-600">Failed to load schema: {error}</div>
      </div>
    );
  }

  if (!schema) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200 bg-slate-50">
        <h3 className="font-semibold text-slate-900">Database Schema</h3>
        <p className="text-xs text-slate-500 mt-0.5">
          {schema.table_count} tables · click to explore
        </p>
      </div>
      <div className="divide-y divide-slate-100 max-h-[500px] overflow-y-auto">
        {schema.tables.map((table) => (
          <TableRow
            key={table.name}
            table={table}
            isExpanded={expanded.has(table.name)}
            onToggle={() => toggle(table.name)}
          />
        ))}
      </div>
    </div>
  );
}

interface TableRowProps {
  table: TableSchema;
  isExpanded: boolean;
  onToggle: () => void;
}

function TableRow({ table, isExpanded, onToggle }: TableRowProps) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="w-full px-4 py-2.5 flex items-center justify-between
                   hover:bg-slate-50 transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-xs">{isExpanded ? '▼' : '▶'}</span>
          <span className="font-mono text-sm text-slate-900">{table.name}</span>
          {table.row_count !== null && (
            <span className="text-xs text-slate-500">~{table.row_count} rows</span>
          )}
        </div>
        <span className="text-xs text-slate-400">{table.columns.length} cols</span>
      </button>

      {isExpanded && (
        <div className="px-4 pb-3 bg-slate-50/50">
          <table className="w-full text-xs">
            <tbody className="divide-y divide-slate-100">
              {table.columns.map((col) => (
                <tr key={col.name}>
                  <td className="py-1.5 pr-2 font-mono text-slate-900">
                    {col.is_primary_key && <span title="Primary Key">🔑 </span>}
                    {col.name}
                  </td>
                  <td className="py-1.5 pr-2 text-slate-500">{col.data_type}</td>
                  <td className="py-1.5 text-slate-400">
                    {col.foreign_key && <span>→ {col.foreign_key}</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
