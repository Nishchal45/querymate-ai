import axios from 'axios';
import type {
  QueryRequest,
  QueryResponse,
  HistoryResponse,
  SchemaResponse,
  CacheStats,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30_000,
});

export const api = {
  async query(request: QueryRequest): Promise<QueryResponse> {
    const { data } = await client.post<QueryResponse>('/query', request);
    return data;
  },

  async getHistory(page = 1, pageSize = 20, search?: string): Promise<HistoryResponse> {
    const { data } = await client.get<HistoryResponse>('/history', {
      params: { page, page_size: pageSize, search },
    });
    return data;
  },

  async clearHistory(): Promise<void> {
    await client.delete('/history');
  },

  async getSchema(): Promise<SchemaResponse> {
    const { data } = await client.get<SchemaResponse>('/schema');
    return data;
  },

  async getCacheStats(): Promise<CacheStats> {
    const { data } = await client.get<CacheStats>('/cache/stats');
    return data;
  },

  async invalidateCache(): Promise<void> {
    await client.post('/cache/invalidate');
  },
};
