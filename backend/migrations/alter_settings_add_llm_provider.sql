-- Migration: Add llm_provider column to settings table
-- Date: 2024-12-21
-- Use this migration for existing databases that were created before llm_provider was added

ALTER TABLE settings ADD COLUMN llm_provider VARCHAR(100);

-- Optionally set a default value for existing rows
-- UPDATE settings SET llm_provider = 'ollama' WHERE llm_provider IS NULL;

