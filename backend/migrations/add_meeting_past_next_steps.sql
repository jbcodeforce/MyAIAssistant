-- Add past_steps / next_steps JSON columns to meetings table (same shape as projects steps).
-- SQLite stores JSON as TEXT; PostgreSQL can use JSONB instead of TEXT if preferred.
-- Apply the statements appropriate to your database.

ALTER TABLE meetings ADD COLUMN past_steps TEXT;
ALTER TABLE meetings ADD COLUMN next_steps TEXT;
