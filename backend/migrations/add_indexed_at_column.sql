-- Migration: Add indexed_at column to knowledge table
-- This column tracks when a document was indexed into the RAG system

ALTER TABLE knowledge ADD COLUMN indexed_at DATETIME;

