-- Migration: Add asset_id column to todos table
-- Links a todo to an optional asset (code, document, or other resource).

ALTER TABLE todos ADD COLUMN asset_id INTEGER REFERENCES assets(id);

CREATE INDEX IF NOT EXISTS idx_todos_asset_id ON todos(asset_id);
