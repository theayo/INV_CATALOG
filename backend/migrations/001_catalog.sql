CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin'))
);

CREATE TABLE products (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 200),
    image_key TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_key TEXT UNIQUE
);

CREATE INDEX products_created_at_idx ON products (created_at DESC, id DESC);
