#!/bin/bash
# Import customer notes from markdown files into the database
# Usage: ./import_customer_notes.sh /path/to/customers/folder [options]

cd "$(dirname "$0")"
uv run python -m tools.import_customer_notes "$@"

