-- Migration: Add tags column to todos table
-- Comma-separated tags for task classification (consistent with knowledge.tags).

ALTER TABLE todos ADD COLUMN tags VARCHAR(500);
