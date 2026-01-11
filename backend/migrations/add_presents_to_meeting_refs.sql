-- Migration: Add presents column to meeting_refs table
-- This column stores a comma or semicolon separated list of meeting attendees

ALTER TABLE meeting_refs ADD COLUMN presents VARCHAR(2048) DEFAULT NULL;
