-- Add status and project_count columns to assets table
ALTER TABLE assets ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'Started';
ALTER TABLE assets ADD COLUMN project_count INTEGER NOT NULL DEFAULT 0;

