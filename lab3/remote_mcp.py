from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


http_transport = StreamableHttpTransport(
    url="https://mcp.context7.com/mcp"
)

http_client= Client(http_transport)

async def main():
    async with http_client as client:
        tools = await client.list_tools()

        for tool in tools:
            print(f"Tool: {tool.name}")
            print(f"Description: {tool.description}")
            
            print()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
