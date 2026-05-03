import { useEffect, useState, type FormEvent, type KeyboardEvent } from 'react';

const EXAMPLE_QUERIES = [
  'How many customers are in California?',
  'What are the top 5 best-selling products?',
  'Show me orders placed last month',
  'What is the average order value by category?',
];

interface QueryInputProps {
  onSubmit: (question: string) => void;
  loading: boolean;
  initialValue?: string | null;
}

export function QueryInput({ onSubmit, loading, initialValue }: QueryInputProps) {
  const [question, setQuestion] = useState('');

  useEffect(() => {
    if (initialValue) setQuestion(initialValue);
  }, [initialValue]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;
    onSubmit(question.trim());
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit(e as unknown as FormEvent);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="relative">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about your data..."
          rows={3}
          className="w-full px-4 py-3 border border-slate-300 rounded-lg shadow-sm
                     focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent
                     resize-none text-slate-900 placeholder-slate-400"
          disabled={loading}
        />
        <div className="absolute bottom-3 right-3 text-xs text-slate-400">
          ⌘+Enter to submit
        </div>
      </div>

      <div className="flex flex-wrap gap-2 items-center">
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="px-5 py-2 bg-brand-600 text-white font-medium rounded-md
                     hover:bg-brand-700 disabled:bg-slate-300 disabled:cursor-not-allowed
                     transition-colors flex items-center gap-2"
        >
          {loading ? (
            <>
              <Spinner /> Generating SQL...
            </>
          ) : (
            'Run Query'
          )}
        </button>

        <span className="text-sm text-slate-500 ml-2">Try:</span>
        {EXAMPLE_QUERIES.slice(0, 3).map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => setQuestion(q)}
            disabled={loading}
            className="text-xs px-2.5 py-1 bg-slate-100 text-slate-700 rounded
                       hover:bg-slate-200 transition-colors disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>
    </form>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
      <path
        d="M4 12a8 8 0 018-8"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        className="opacity-75"
      />
    </svg>
  );
}
