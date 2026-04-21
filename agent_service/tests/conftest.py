"""Root conftest: ensure agent_service package is importable when running or debugging tests."""

import sys
from pathlib import Path

# Project root (agent_service/) so "import agent_service" resolves to agent_service/agent_service/
_root = Path(__file__).resolve().parent.parent
if _root not in (Path(p).resolve() for p in sys.path):
    sys.path.insert(0, str(_root))
