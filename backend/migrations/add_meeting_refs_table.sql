-- Migration: Add meeting_refs table
-- Description: Create table for storing meeting note references

CREATE TABLE IF NOT EXISTS meeting_refs (
    id SERIAL PRIMARY KEY,
    meeting_id VARCHAR(255) NOT NULL UNIQUE,
    project_id INTEGER REFERENCES projects(id),
    org_id INTEGER REFERENCES organizations(id),
    file_ref VARCHAR(2048) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for foreign key lookups
CREATE INDEX IF NOT EXISTS idx_meeting_refs_project_id ON meeting_refs(project_id);
CREATE INDEX IF NOT EXISTS idx_meeting_refs_org_id ON meeting_refs(org_id);
CREATE INDEX IF NOT EXISTS idx_meeting_refs_meeting_id ON meeting_refs(meeting_id);

-- Create trigger to update updated_at timestamp on row changes
CREATE OR REPLACE FUNCTION update_meeting_refs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_meeting_refs_updated_at ON meeting_refs;
CREATE TRIGGER trigger_meeting_refs_updated_at
    BEFORE UPDATE ON meeting_refs
    FOR EACH ROW
    EXECUTE FUNCTION update_meeting_refs_updated_at();

