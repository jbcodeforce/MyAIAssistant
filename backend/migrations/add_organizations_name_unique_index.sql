-- Migration: Case-insensitive unique organization names
-- Run only after resolving duplicate names (e.g. merge script).
-- SQLite / PostgreSQL: prevents "ResMed" and "resmed" coexisting.

CREATE UNIQUE INDEX IF NOT EXISTS ix_organizations_name_lower ON organizations (lower(name));
