import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { QueryResult } from '../types';

interface ChartViewProps {
  result: QueryResult;
}

type ChartType = 'bar' | 'line' | 'none';

function detectChartType(result: QueryResult): ChartType {
  if (result.columns.length !== 2 || result.row_count === 0 || result.row_count > 100) {
    return 'none';
  }

  const sample = result.rows[0];
  const [first, second] = sample;

  // Numeric Y axis required
  if (typeof second !== 'number') return 'none';

  // Date-like X axis → line chart
  if (typeof first === 'string' && /^\d{4}-\d{2}/.test(first)) return 'line';

  // Categorical X axis → bar chart
  if (typeof first === 'string' || typeof first === 'number') return 'bar';

  return 'none';
}

export function ChartView({ result }: ChartViewProps) {
  const chartType = detectChartType(result);

  if (chartType === 'none') return null;

  const data = result.rows.map((row) => ({
    [result.columns[0]]: row[0],
    [result.columns[1]]: row[1],
  }));

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4">
      <div className="text-xs font-medium text-slate-500 mb-3 uppercase tracking-wide">
        {chartType === 'bar' ? 'Bar Chart' : 'Line Chart'} · auto-detected
      </div>
      <ResponsiveContainer width="100%" height={300}>
        {chartType === 'bar' ? (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey={result.columns[0]} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey={result.columns[1]} fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        ) : (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey={result.columns[0]} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Line
              type="monotone"
              dataKey={result.columns[1]}
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ r: 4 }}
            />
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
