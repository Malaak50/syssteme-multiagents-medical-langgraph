"""
MCP Client - connects to the local MCP server for additional tools.
Falls back gracefully if MCP server is not available.
"""
import asyncio
import httpx
import json
from typing import Optional
import logging

logger = logging.getLogger(__name__)

MCP_SERVER_URL = "http://localhost:8001"


async def call_mcp_tool(tool_name: str, arguments: dict) -> Optional[str]:
    """Call a tool on the MCP server."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{MCP_SERVER_URL}/tools/call",
                json={"name": tool_name, "arguments": arguments}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("result", "")
    except Exception as e:
        logger.warning(f"MCP server not available: {e}")
    return None


async def get_medical_context(symptoms: str) -> Optional[str]:
    """Get medical context from MCP server for given symptoms."""
    result = await call_mcp_tool("get_medical_context", {"symptoms": symptoms})
    return result


async def get_care_guidelines(condition: str) -> Optional[str]:
    """Get care guidelines from MCP server."""
    result = await call_mcp_tool("get_care_guidelines", {"condition": condition})
    return result


def call_mcp_sync(tool_name: str, arguments: dict) -> Optional[str]:
    """Synchronous wrapper for MCP calls."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, call_mcp_tool(tool_name, arguments))
                return future.result(timeout=10)
        else:
            return loop.run_until_complete(call_mcp_tool(tool_name, arguments))
    except Exception as e:
        logger.warning(f"MCP sync call failed: {e}")
        return None
