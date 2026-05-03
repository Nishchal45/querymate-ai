import { QueryInput } from '../components/QueryInput';
import { SchemaExplorer } from '../components/SchemaExplorer';
import { SqlDisplay } from '../components/SqlDisplay';
import { useQuery } from '../hooks/useQuery';

export function QueryPage() {
  const { loading, error, violations, response, submit } = useQuery();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
      {/* Main column */}
      <div className="space-y-4">
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-5">
          <QueryInput onSubmit={submit} loading={loading} />
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="font-medium text-red-900">{error}</div>
            {violations && violations.length > 0 && (
              <ul className="mt-2 text-sm text-red-800 list-disc list-inside space-y-0.5">
                {violations.map((v, i) => (
                  <li key={i}>{v}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {response && (
          <div className="space-y-4">
            <SqlDisplay
              sql={response.sql}
              cached={response.cached}
              cacheLevel={response.cache_level}
              executionTimeMs={response.execution_time_ms}
            />
            {response.result && (
              <div className="bg-white border border-slate-200 rounded-lg p-4">
                <div className="text-sm text-slate-600">
                  Got <span className="font-semibold">{response.result.row_count}</span> rows
                  in {response.result.execution_time_ms.toFixed(1)}ms
                  {response.result.truncated && ' (truncated)'}
                </div>
                <div className="mt-2 text-xs text-slate-400">
                  Results table & charts coming in the next PR.
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sidebar */}
      <div>
        <SchemaExplorer />
      </div>
    </div>
  );
}
