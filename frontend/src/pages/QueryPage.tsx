import { useState } from 'react';
import { ChartView } from '../components/ChartView';
import { QueryHistory } from '../components/QueryHistory';
import { QueryInput } from '../components/QueryInput';
import { ResultsTable } from '../components/ResultsTable';
import { SchemaExplorer } from '../components/SchemaExplorer';
import { SqlDisplay } from '../components/SqlDisplay';
import { useQuery } from '../hooks/useQuery';

export function QueryPage() {
  const { loading, error, violations, response, submit } = useQuery();
  const [historyKey, setHistoryKey] = useState(0);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);

  const handleSubmit = async (question: string) => {
    await submit(question);
    setHistoryKey((k) => k + 1);
  };

  const handleHistorySelect = (question: string) => {
    setPendingQuestion(question);
    handleSubmit(question);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
      <div className="space-y-4">
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-5">
          <QueryInput
            onSubmit={handleSubmit}
            loading={loading}
            initialValue={pendingQuestion}
          />
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
              <>
                <ChartView result={response.result} />
                <ResultsTable result={response.result} />
              </>
            )}
          </div>
        )}
      </div>

      <div className="space-y-4">
        <SchemaExplorer />
        <QueryHistory onSelect={handleHistorySelect} refreshKey={historyKey} />
      </div>
    </div>
  );
}
