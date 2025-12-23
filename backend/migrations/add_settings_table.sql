-- Migration: Add settings table for application configuration
-- Date: 2024-12-20

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    llm_provider VARCHAR(100),
    llm_name VARCHAR(100),
    llm_api_endpoint VARCHAR(2048),
    api_key VARCHAR(500),
    default_temperature REAL,
    chunk_size INTEGER,
    overlap INTEGER,
    min_chunk_size INTEGER
);

-- Insert default settings row
INSERT INTO settings (
    llm_provider,
    llm_name,
    llm_api_endpoint,
    api_key,
    default_temperature,
    chunk_size,
    overlap,
    min_chunk_size
) VALUES (
    'ollama',
    'gpt-oss:20b',
    'http://localhost:11434',
    'a_non_needed_api_key',
    0.7,
    1000,
    200,
    100
);

