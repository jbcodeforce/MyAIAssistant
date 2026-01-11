-- Migration: Add persons table
-- Description: Creates the persons table for tracking people interactions during tasks/projects

-- SQLite version
CREATE TABLE IF NOT EXISTS persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    context TEXT,
    role TEXT,
    last_met_date TIMESTAMP,
    next_step TEXT,
    project_id INTEGER REFERENCES projects(id),
    organization_id INTEGER REFERENCES organizations(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for filtering by project
CREATE INDEX IF NOT EXISTS idx_persons_project_id ON persons(project_id);

-- Index for filtering by organization
CREATE INDEX IF NOT EXISTS idx_persons_organization_id ON persons(organization_id);

-- Index for ordering by updated_at
CREATE INDEX IF NOT EXISTS idx_persons_updated_at ON persons(updated_at DESC);

-- PostgreSQL version (uncomment if using PostgreSQL):
-- CREATE TABLE IF NOT EXISTS persons (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(255) NOT NULL,
--     context TEXT,
--     role VARCHAR(255),
--     last_met_date TIMESTAMP,
--     next_step TEXT,
--     project_id INTEGER REFERENCES projects(id),
--     organization_id INTEGER REFERENCES organizations(id),
--     created_at TIMESTAMP NOT NULL DEFAULT NOW(),
--     updated_at TIMESTAMP NOT NULL DEFAULT NOW()
-- );
