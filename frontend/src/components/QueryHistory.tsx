import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { HistoryItem } from '../types';

interface QueryHistoryProps {
  onSelect: (question: string) => void;
  refreshKey: number;
}

export function QueryHistory({ onSelect, refreshKey }: QueryHistoryProps) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    api
      .getHistory(1, 10)
      .then((data) => {
        if (mounted) setItems(data.items);
      })
      .catch(() => {
        if (mounted) setItems([]);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [refreshKey]);

  if (!loading && items.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-lg p-4">
        <div className="text-sm text-slate-500">No queries yet. Run one to get started.</div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200 bg-slate-50">
        <h3 className="font-semibold text-slate-900">Recent Queries</h3>
        <p className="text-xs text-slate-500 mt-0.5">click to re-run</p>
      </div>
      <div className="divide-y divide-slate-100 max-h-[300px] overflow-y-auto">
        {items.map((item) => (
          <button
            key={item.id}
            onClick={() => onSelect(item.natural_language)}
            className="w-full px-4 py-2.5 text-left hover:bg-slate-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full flex-shrink-0 ${
                  item.was_cached ? 'bg-emerald-500' : 'bg-slate-300'
                }`}
                title={item.was_cached ? `Cached (${item.cache_level})` : 'Fresh query'}
              />
              <span className="text-sm text-slate-900 truncate">{item.natural_language}</span>
            </div>
            <div className="ml-4 mt-0.5 text-xs text-slate-500">
              {item.error ? (
                <span className="text-red-600">error</span>
              ) : (
                <>
                  {item.row_count} rows · {item.execution_time_ms?.toFixed(0)}ms
                </>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
