"""
HEMAGON MCP Server
"""
import json
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from scraper import load_user_profile


app = Server("hemagon-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="load_user_profile",
            description="Load a HEMA fighter's profile from hemagon.com",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile_link": {
                        "type": "string",
                        "description": "Full URL to profile (e.g., 'https://hemagon.com/users/nekrasova')"
                    },
                    "target_dir": {
                        "type": "string",
                        "description": "Directory to save output files"
                    }
                },
                "required": ["profile_link", "target_dir"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    if name == "load_user_profile":
        profile_link = arguments.get("profile_link")
        target_dir = arguments.get("target_dir")
        
        result = load_user_profile(profile_link, target_dir)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
    
    return []


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())