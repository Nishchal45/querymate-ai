# QueryMate AI — System Architecture

## 1. System Overview

```mermaid
graph TB
    User([User]) --> Frontend[React Frontend<br/>:3000]
    Frontend --> API[FastAPI Backend<br/>:8000]
    
    API --> Introspector[Schema Introspector]
    API --> LLM[LLM Service]
    API --> Validator[SQL Validator]
    API --> Executor[Query Executor]
    API --> Cache[Cache Service]
    
    Introspector --> TargetDB[(Target DB<br/>PostgreSQL :5433)]
    LLM --> OpenAI[OpenAI API<br/>gpt-4o-mini]
    Executor --> TargetDB
    Cache --> Redis[(Redis<br/>:6379)]
    API --> AppDB[(App DB<br/>PostgreSQL :5432)]
    
    style Frontend fill:#61DAFB,color:#000
    style API fill:#009688,color:#fff
    style TargetDB fill:#336791,color:#fff
    style AppDB fill:#336791,color:#fff
    style Redis fill:#DC382D,color:#fff
    style OpenAI fill:#412991,color:#fff
```

## 2. Request Flow — Query Execution

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as FastAPI
    participant C as Cache (Redis)
    participant I as Introspector
    participant L as LLM (OpenAI)
    participant V as Validator
    participant E as Executor
    participant D as Target DB
    participant H as App DB

    U->>F: Types "How many orders last month?"
    F->>A: POST /api/query {question}
    
    Note over A,C: Step 1: Check L1 Cache (NL → SQL)
    A->>C: GET querymate:nl:{hash}
    
    alt L1 Cache HIT
        C-->>A: Cached SQL
        Note over A: Skip LLM — saved ~1.5s
    else L1 Cache MISS
        Note over A,L: Step 2: Generate SQL
        A->>I: introspect_schema()
        I->>D: Query information_schema
        D-->>I: Tables, columns, PKs, FKs
        I-->>A: SchemaInfo (compressed)
        
        A->>L: generate_sql(question, schema)
        L-->>A: Generated SQL
        
        A->>C: SET querymate:nl:{hash} = SQL
    end
    
    Note over A,V: Step 3: Validate SQL
    A->>V: validate(sql)
    
    alt Validation FAILED
        V-->>A: {is_valid: false, violations: [...]}
        A-->>F: 400 — Query blocked
        F-->>U: Error: "Query blocked: contains DROP statement"
    else Validation PASSED
        V-->>A: {is_valid: true}
    end
    
    Note over A,C: Step 4: Check L2 Cache (SQL → Results)
    A->>C: GET querymate:sql:{hash}
    
    alt L2 Cache HIT
        C-->>A: Cached QueryResult
        Note over A: Skip DB — saved ~100ms
    else L2 Cache MISS
        Note over A,E: Step 5: Execute Query
        A->>E: execute(sql)
        E->>D: SELECT ... (timeout: 10s, limit: 1000 rows)
        D-->>E: Result rows
        E-->>A: QueryResult
        
        A->>C: SET querymate:sql:{hash} = result
    end
    
    Note over A,H: Step 6: Save to History (async)
    A->>H: INSERT INTO query_history
    
    A-->>F: {sql, result, timing, cache_info}
    F-->>U: Results table + chart
```

## 3. Security — Defense in Depth

```mermaid
graph TB
    Input[User Query] --> LLM[LLM Generates SQL]
    LLM --> L1{Layer 1<br/>SQL Validator}
    
    L1 -->|Blocked| Reject1[400: Query Blocked<br/>20+ patterns checked]
    L1 -->|Passed| L2{Layer 2<br/>Read-Only Connection}
    
    L2 -->|Write attempt| Reject2[psycopg2 error<br/>Connection is read-only]
    L2 -->|SELECT only| L3{Layer 3<br/>DB Role Privileges}
    
    L3 -->|Insufficient privilege| Reject3[PostgreSQL error<br/>Permission denied]
    L3 -->|Allowed| L4{Layer 4<br/>Statement Timeout}
    
    L4 -->|Timeout exceeded| Reject4[408: Query Timeout<br/>Cancelled after 10s]
    L4 -->|Completed| Result[Query Results]
    
    style L1 fill:#E53935,color:#fff
    style L2 fill:#FB8C00,color:#fff
    style L3 fill:#FDD835,color:#000
    style L4 fill:#43A047,color:#fff
    style Reject1 fill:#FFCDD2
    style Reject2 fill:#FFE0B2
    style Reject3 fill:#FFF9C4
    style Reject4 fill:#C8E6C9
    style Result fill:#4CAF50,color:#fff
```

## 4. Caching Strategy — Two-Level Cache

```mermaid
graph TD
    Q[User Question] --> Norm[Normalize Question<br/>lowercase, strip whitespace]
    Norm --> Hash1[SHA-256 Hash]
    Hash1 --> L1{L1 Cache Lookup<br/>querymate:nl:hash}
    
    L1 -->|HIT| SQL1[Cached SQL<br/>Skip LLM ~1.5s saved]
    L1 -->|MISS| LLM[Call OpenAI LLM<br/>~1.5s]
    LLM --> CacheL1[Cache NL→SQL<br/>TTL: 1 hour]
    CacheL1 --> SQL1
    
    SQL1 --> Hash2[SHA-256 Hash of SQL]
    Hash2 --> L2{L2 Cache Lookup<br/>querymate:sql:hash}
    
    L2 -->|HIT| Result1[Cached Results<br/>Skip DB ~100ms saved]
    L2 -->|MISS| DB[Execute Query<br/>~100ms]
    DB --> CacheL2[Cache SQL→Results<br/>TTL: 5 minutes]
    CacheL2 --> Result1
    
    Result1 --> Response[Return to User]
    
    style L1 fill:#1976D2,color:#fff
    style L2 fill:#7B1FA2,color:#fff
    style LLM fill:#412991,color:#fff
    style DB fill:#336791,color:#fff
```

## 5. Data Model — E-Commerce Demo Schema

```mermaid
erDiagram
    customers ||--o{ orders : places
    customers ||--o{ reviews : writes
    categories ||--o{ products : contains
    products ||--o{ order_items : "ordered as"
    products ||--o{ reviews : "reviewed in"
    orders ||--o{ order_items : contains
    orders ||--o{ shipping : "shipped via"
    orders ||--o{ payments : "paid with"
    
    customers {
        uuid id PK
        varchar name
        varchar email
        varchar city
        varchar state
        timestamptz created_at
    }
    
    categories {
        uuid id PK
        varchar name
        text description
    }
    
    products {
        uuid id PK
        varchar name
        uuid category_id FK
        decimal price
        integer stock_quantity
        timestamptz created_at
    }
    
    orders {
        uuid id PK
        uuid customer_id FK
        date order_date
        varchar status
        decimal total_amount
    }
    
    order_items {
        uuid id PK
        uuid order_id FK
        uuid product_id FK
        integer quantity
        decimal unit_price
    }
    
    reviews {
        uuid id PK
        uuid product_id FK
        uuid customer_id FK
        integer rating
        text comment
        timestamptz created_at
    }
    
    shipping {
        uuid id PK
        uuid order_id FK
        varchar carrier
        varchar tracking_number
        date shipped_date
        date delivered_date
    }
    
    payments {
        uuid id PK
        uuid order_id FK
        varchar payment_method
        decimal amount
        varchar status
        timestamptz paid_at
    }
```
