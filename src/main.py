import asyncio

from mcp.server.stdio import stdio_server

from src.dependency_injection.application_bootstrap import ApplicationBootstrap
from src.logger import Logger

logger = Logger(__name__)


async def serve():
    Initializes and runs the MCP server using Dependency Injection.
    Eliminates hardcoded dependencies and implements DIP (Dependency Inversion Principle).
    logger.info(
        "Starting MCP web scrapper server with Dependency Injection (stdio mode)"
    bootstrap = ApplicationBootstrap()
    # Create server with all dependencies injected
            read_stream, write_stream, server.create_initialization_options()
