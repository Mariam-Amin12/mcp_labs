import asyncio

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


stdio_transport = StdioTransport(
    command="npx",
    args=["-y", "@upstash/context7-mcp"],
)

stdio_client = Client(stdio_transport)


async def main():
    async with stdio_client as client:
        tools = await client.list_tools()

        for tool in tools:
            print(f"Tool: {tool.name}")
            print(f"Description: {tool.description}")
            
            print()


if __name__ == "__main__":
    asyncio.run(main())