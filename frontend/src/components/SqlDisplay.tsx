import { useState } from 'react';

interface SqlDisplayProps {
  sql: string;
  cached?: boolean;
  cacheLevel?: string | null;
  executionTimeMs?: number;
}

export function SqlDisplay({ sql, cached, cacheLevel, executionTimeMs }: SqlDisplayProps) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="bg-slate-900 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-slate-300">Generated SQL</span>
          {cached && (
            <span
              className="text-xs px-2 py-0.5 bg-emerald-900/50 text-emerald-300 rounded
                         border border-emerald-800"
              title={`Cache hit at level ${cacheLevel}`}
            >
              ● cached ({cacheLevel})
            </span>
          )}
          {executionTimeMs !== undefined && (
            <span className="text-xs text-slate-400">{executionTimeMs.toFixed(1)}ms</span>
          )}
        </div>
        <button
          onClick={copy}
          className="text-xs text-slate-300 hover:text-white transition-colors"
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre className="p-4 text-sm text-slate-100 font-mono overflow-x-auto whitespace-pre-wrap">
        {sql}
      </pre>
    </div>
  );
}
