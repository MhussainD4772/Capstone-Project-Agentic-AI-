"""MCP Tool server for file export operations.

This module implements an MCP (Model Context Protocol) Tool server that allows
QA Sentinel agents to export files (Markdown or JSON) to the local filesystem
under a controlled directory structure.

ADK agents can call these tools through the MCP protocol to save:
- Test cases, planner outputs, and other documentation as Markdown
- Pipeline results, configurations, and structured data as JSON

The server follows the MCP specification and can be executed as a standalone
process or integrated into the QA Sentinel agent ecosystem.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server


# Initialize MCP server
server = Server("qa-sentinel-file-export")

# Base export directory
EXPORT_BASE_DIR = Path("exports")
MARKDOWN_DIR = EXPORT_BASE_DIR / "markdown"
JSON_DIR = EXPORT_BASE_DIR / "json"


def ensure_export_directories():
    """Ensure export directories exist."""
    os.makedirs(MARKDOWN_DIR, exist_ok=True)
    os.makedirs(JSON_DIR, exist_ok=True)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available MCP tools.
    
    Returns:
        List of Tool definitions for save_markdown and save_json
    """
    return [
        Tool(
            name="save_markdown",
            description=(
                "Save Markdown content to a file in exports/markdown/.\n"
                "ADK agents can use this to export test cases, planner outputs, "
                "and other documentation as Markdown files."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Filename (must end with .md)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Markdown content to write"
                    }
                },
                "required": ["filename", "content"]
            }
        ),
        Tool(
            name="save_json",
            description=(
                "Save JSON data to a file in exports/json/.\n"
                "ADK agents can use this to export pipeline results, configurations, "
                "and structured data as prettified JSON files."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Filename (must end with .json)"
                    },
                    "data": {
                        "type": "object",
                        "description": "Dictionary data to write as JSON"
                    }
                },
                "required": ["filename", "data"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """
    Handle tool calls from MCP clients.
    
    Args:
        name: Name of the tool to call
        arguments: Tool arguments
    
    Returns:
        List of TextContent with tool execution results
    
    Raises:
        ValueError: If tool name is unknown or arguments are invalid
    """
    if name == "save_markdown":
        return await _save_markdown(arguments)
    elif name == "save_json":
        return await _save_json(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def _save_markdown(arguments: Dict[str, Any]) -> list[TextContent]:
    """
    Save Markdown content to exports/markdown/<filename>.
    
    Args:
        arguments: Dictionary with 'filename' and 'content' keys
    
    Returns:
        List containing a single TextContent with success result
    
    Raises:
        ValueError: If filename doesn't end with .md or arguments are missing
    """
    filename = arguments.get("filename")
    content = arguments.get("content")
    
    if not filename:
        raise ValueError("filename is required")
    if not filename.endswith(".md"):
        raise ValueError("filename must end with .md")
    if content is None:
        raise ValueError("content is required")
    
    # Ensure directories exist
    ensure_export_directories()
    
    # Write file
    file_path = MARKDOWN_DIR / filename
    with open(file_path, "w", encoding="utf-8") as f:
        bytes_written = f.write(content)
    
    result = {
        "status": "success",
        "path": str(file_path),
        "bytes_written": bytes_written
    }
    
    return [TextContent(type="text", text=json.dumps(result))]


async def _save_json(arguments: Dict[str, Any]) -> list[TextContent]:
    """
    Save JSON data to exports/json/<filename>.
    
    Args:
        arguments: Dictionary with 'filename' and 'data' keys
    
    Returns:
        List containing a single TextContent with success result
    
    Raises:
        ValueError: If filename doesn't end with .json or arguments are missing
    """
    filename = arguments.get("filename")
    data = arguments.get("data")
    
    if not filename:
        raise ValueError("filename is required")
    if not filename.endswith(".json"):
        raise ValueError("filename must end with .json")
    if data is None:
        raise ValueError("data is required")
    
    # Ensure directories exist
    ensure_export_directories()
    
    # Write prettified JSON
    file_path = JSON_DIR / filename
    with open(file_path, "w", encoding="utf-8") as f:
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        bytes_written = f.write(json_str)
    
    result = {
        "status": "success",
        "path": str(file_path),
        "bytes_written": bytes_written
    }
    
    return [TextContent(type="text", text=json.dumps(result))]


async def run():
    """
    Run the MCP server using stdio transport.
    
    This function starts the MCP server and handles communication
    via standard input/output, following the MCP specification.
    """
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(run())

