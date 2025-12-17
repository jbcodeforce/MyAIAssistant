#!/bin/bash
# Index customer notes from markdown files into the database
# Usage: ./index_customer_notes.sh /path/to/customers/folder [collection] [persist-dir]
#   collection defaults to: biz-notes
#   persist-dir defaults to: ~/Documents/Code/MyAIAssistant/workspaces/biz-db/data/chroma

set -e

if [ $# -lt 1 ]; then
    echo "Error: Missing required argument"
    echo "Usage: $0 /path/to/customers/folder [collection] [persist-dir]"
    exit 1
fi

FOLDER_PATH="$1"
COLLECTION="${2:-biz-notes}"
PERSIST_DIR="${3:-$HOME/Documents/Code/MyAIAssistant/workspaces/biz-db/data/chroma}"

cd "$(dirname "$0")"
uv run python ./tools/vectorize_folder.py "$FOLDER_PATH" --chunk-size 500 --collection "$COLLECTION" --persist-dir "$PERSIST_DIR"
