CREATE TABLE IF NOT EXISTS analyses (
    id              SERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT now(),
    image_path      TEXT NOT NULL,
    ingredients     JSONB NOT NULL,
    total_kcal      NUMERIC(8, 2) NOT NULL,
    total_protein   NUMERIC(8, 2) NOT NULL,
    total_carbs     NUMERIC(8, 2) NOT NULL,
    total_fat       NUMERIC(8, 2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_analyses_timestamp ON analyses (timestamp DESC);