-- Migration: Add is_top_active column to organizations table
-- Date: 2025-03-13
-- Use this migration for existing databases created before is_top_active was added.
-- New DBs created from add_organization_project.sql may add this column there instead.

ALTER TABLE organizations ADD COLUMN is_top_active INTEGER NOT NULL DEFAULT 0;
