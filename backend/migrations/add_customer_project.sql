-- Migration: Add Customer and Project tables
-- Date: 2025-12-15

-- Create customers table
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    stakeholders TEXT,
    team TEXT,
    description TEXT,
    related_products TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    customer_id INTEGER REFERENCES customers(id),
    status VARCHAR(50) NOT NULL DEFAULT 'Draft',
    tasks TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Add project_id column to todos table
ALTER TABLE todos ADD COLUMN project_id INTEGER REFERENCES projects(id);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_projects_customer_id ON projects(customer_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_todos_project_id ON todos(project_id);

