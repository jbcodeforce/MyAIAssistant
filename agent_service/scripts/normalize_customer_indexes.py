#!/usr/bin/env python3
"""Run from agent_service root: uv run python scripts/normalize_customer_indexes.py --help"""

from agent_service.tools.customer_index_normalize import main

if __name__ == "__main__":
    raise SystemExit(main())
