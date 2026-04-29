-- Migration: Add organization_id column to todos table
-- Links a todo directly to an organization (independent of project link).

ALTER TABLE todos ADD COLUMN organization_id INTEGER REFERENCES organizations(id);

CREATE INDEX IF NOT EXISTS idx_todos_organization_id ON todos(organization_id);

-- Backfill: copy parent organization from linked project where possible.
UPDATE todos
SET organization_id = (
    SELECT projects.organization_id FROM projects WHERE projects.id = todos.project_id
)
WHERE project_id IS NOT NULL AND organization_id IS NULL;
