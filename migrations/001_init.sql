CREATE TABLE IF NOT EXISTS products (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(500)  NOT NULL,
    url         TEXT          NOT NULL,
    store       VARCHAR(100)  NOT NULL,
    image_url   TEXT,
    category    VARCHAR(100),
    is_active   BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP     NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS price_history (
    id          SERIAL PRIMARY KEY,
    product_id  INTEGER       NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    price       NUMERIC(12,2) NOT NULL,
    currency    VARCHAR(10)   NOT NULL DEFAULT 'USD',
    in_stock    BOOLEAN       NOT NULL DEFAULT TRUE,
    scraped_at  TIMESTAMP     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_price_history_product_id ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_scraped_at ON price_history(scraped_at DESC);

CREATE TABLE IF NOT EXISTS alerts (
    id              SERIAL PRIMARY KEY,
    product_id      INTEGER        NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    email           VARCHAR(255)   NOT NULL,
    target_price    NUMERIC(12,2)  NOT NULL,
    is_active       BOOLEAN        NOT NULL DEFAULT TRUE,
    triggered_at    TIMESTAMP,
    created_at      TIMESTAMP      NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_product_id ON alerts(product_id);
