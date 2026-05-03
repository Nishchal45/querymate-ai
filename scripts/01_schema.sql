-- ──────────────────────────────────────────────
-- QueryMate AI — E-Commerce Demo Schema
-- ──────────────────────────────────────────────
-- 8 tables with proper FK relationships.
-- Designed for interesting NL2SQL queries:
--   JOINs, aggregations, date ranges, subqueries.

-- ── Read-only role for QueryMate AI ──
-- Defense in depth: even if the SQL validator fails,
-- this role can only SELECT — never modify data.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'querymate_reader') THEN
        CREATE ROLE querymate_reader WITH LOGIN PASSWORD 'readonly';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE ecommerce_demo TO querymate_reader;

-- Set statement timeout at role level (Layer 4 of defense in depth)
ALTER ROLE querymate_reader SET statement_timeout = '10s';

-- ── Tables ──

CREATE TABLE IF NOT EXISTS customers (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(150) UNIQUE NOT NULL,
    city        VARCHAR(80),
    state       VARCHAR(2),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(60) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    category_id     INTEGER REFERENCES categories(id),
    price           NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    stock_quantity  INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id            SERIAL PRIMARY KEY,
    customer_id   INTEGER REFERENCES customers(id),
    order_date    DATE NOT NULL DEFAULT CURRENT_DATE,
    status        VARCHAR(20) NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')),
    total_amount  NUMERIC(10,2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS order_items (
    id          SERIAL PRIMARY KEY,
    order_id    INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id  INTEGER REFERENCES products(id),
    quantity    INTEGER NOT NULL CHECK (quantity > 0),
    unit_price  NUMERIC(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    id          SERIAL PRIMARY KEY,
    product_id  INTEGER REFERENCES products(id),
    customer_id INTEGER REFERENCES customers(id),
    rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shipping (
    id              SERIAL PRIMARY KEY,
    order_id        INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    carrier         VARCHAR(50) NOT NULL,
    tracking_number VARCHAR(50),
    shipped_date    DATE,
    delivered_date  DATE
);

CREATE TABLE IF NOT EXISTS payments (
    id              SERIAL PRIMARY KEY,
    order_id        INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    payment_method  VARCHAR(30) NOT NULL
                    CHECK (payment_method IN ('credit_card', 'debit_card', 'paypal', 'bank_transfer')),
    amount          NUMERIC(10,2) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    paid_at         TIMESTAMPTZ
);

-- ── Indexes for query performance ──
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);
CREATE INDEX IF NOT EXISTS idx_shipping_order ON shipping(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);

-- ── Grant SELECT-only access to the read-only role ──
GRANT USAGE ON SCHEMA public TO querymate_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO querymate_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO querymate_reader;
