#!/bin/bash
# Import organization notes from markdown files into the database
# Usage: ./import_organization_notes.sh /path/to/organizations/folder [options]

cd "$(dirname "$0")"
uv run python -m tools.import_organization_notes "$@"

