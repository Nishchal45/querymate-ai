export interface QueryRequest {
  question: string;
}

export interface QueryResult {
  columns: string[];
  rows: (string | number | null)[][];
  row_count: number;
  execution_time_ms: number;
  truncated: boolean;
}

export interface QueryResponse {
  query_id: string;
  question: string;
  sql: string;
  result: QueryResult | null;
  error: string | null;
  execution_time_ms: number;
  cached: boolean;
  cache_level: string | null;
}

export interface HistoryItem {
  id: string;
  natural_language: string;
  generated_sql: string;
  execution_time_ms: number | null;
  row_count: number | null;
  was_cached: boolean;
  cache_level: string | null;
  error: string | null;
  created_at: string;
}

export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface ColumnSchema {
  name: string;
  data_type: string;
  is_nullable: boolean;
  is_primary_key: boolean;
  foreign_key: string | null;
  sample_values: string[] | null;
}

export interface TableSchema {
  name: string;
  columns: ColumnSchema[];
  row_count: number | null;
}

export interface SchemaResponse {
  tables: TableSchema[];
  table_count: number;
}

export interface CacheStats {
  l1_hits: number;
  l1_misses: number;
  l2_hits: number;
  l2_misses: number;
  l1_hit_rate: number;
  l2_hit_rate: number;
}
