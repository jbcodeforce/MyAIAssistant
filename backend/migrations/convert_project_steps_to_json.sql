-- Migration: Convert past_steps and next_steps from TEXT to JSON
-- This migration converts existing text data to JSON format
-- Each step in the text format (one per line, starting with "- ") becomes a JSON object with "what" and "who" fields

-- Step 1: Add new JSON columns
ALTER TABLE projects ADD COLUMN past_steps_json JSON;
ALTER TABLE projects ADD COLUMN next_steps_json JSON;

-- Step 2: The conversion of text to JSON should be done via Python script
-- since SQLite has limited JSON manipulation capabilities.
-- After running the Python migration script, execute the following:

-- Step 3: Drop old TEXT columns and rename new ones
-- ALTER TABLE projects DROP COLUMN past_steps;
-- ALTER TABLE projects DROP COLUMN next_steps;
-- ALTER TABLE projects RENAME COLUMN past_steps_json TO past_steps;
-- ALTER TABLE projects RENAME COLUMN next_steps_json TO next_steps;

-- Note: For SQLite, you may need to recreate the table since ALTER TABLE DROP COLUMN
-- has limited support. Use the Python migration script instead.
