-- Migration: Add Organization and Project tables
-- Date: 2025-12-20
-- Note: This replaces the previous customers/projects structure with organizations/projects

-- Create organizations table (renamed from customers)
CREATE TABLE IF NOT EXISTS organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    stakeholders TEXT,
    team TEXT,
    description TEXT,
    related_products TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create projects table with organization_id foreign key
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization_id INTEGER REFERENCES organizations(id),
    status VARCHAR(50) NOT NULL DEFAULT 'Draft',
    tasks TEXT,
    past_steps TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Add project_id column to todos table
ALTER TABLE todos ADD COLUMN project_id INTEGER REFERENCES projects(id);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_projects_organization_id ON projects(organization_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_todos_project_id ON todos(project_id);

-- Migration from old customers table (if exists):
-- INSERT INTO organizations (id, name, stakeholders, team, description, related_products, created_at, updated_at)
-- SELECT id, name, stakeholders, team, description, related_products, created_at, updated_at FROM customers;
-- 
-- UPDATE projects SET organization_id = customer_id;
-- 
-- Then drop the customer_id column from projects and drop customers table

