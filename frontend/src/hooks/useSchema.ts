import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { SchemaResponse } from '../types';

export function useSchema() {
  const [schema, setSchema] = useState<SchemaResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api
      .getSchema()
      .then((data) => {
        if (mounted) setSchema(data);
      })
      .catch((err) => {
        if (mounted) setError(err.message ?? 'Failed to load schema');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return { schema, loading, error };
}
