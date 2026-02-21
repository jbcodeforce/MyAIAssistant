"""Entry point: python -m mcp_todos"""
import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())
