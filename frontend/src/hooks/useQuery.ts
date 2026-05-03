import { useState } from 'react';
import axios from 'axios';
import { api } from '../api/client';
import type { QueryResponse } from '../types';

interface UseQueryReturn {
  loading: boolean;
  error: string | null;
  violations: string[] | null;
  response: QueryResponse | null;
  submit: (question: string) => Promise<void>;
  reset: () => void;
}

export function useQuery(): UseQueryReturn {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [violations, setViolations] = useState<string[] | null>(null);
  const [response, setResponse] = useState<QueryResponse | null>(null);

  const submit = async (question: string) => {
    setLoading(true);
    setError(null);
    setViolations(null);
    setResponse(null);

    try {
      const data = await api.query({ question });
      setResponse(data);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response) {
        const detail = err.response.data?.detail;
        if (typeof detail === 'object' && detail.violations) {
          setError(detail.message || 'Query blocked');
          setViolations(detail.violations);
        } else if (typeof detail === 'object' && detail.message) {
          setError(detail.message);
        } else {
          setError(typeof detail === 'string' ? detail : 'Request failed');
        }
      } else {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setError(null);
    setViolations(null);
    setResponse(null);
  };

  return { loading, error, violations, response, submit, reset };
}
