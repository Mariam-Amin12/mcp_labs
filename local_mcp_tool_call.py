from fastmcp import Client
from fastmcp.client.transports import StdioTransport

stdio_transport = StdioTransport(
    command="npx",  
    args=["-y", "@upstash/context7-mcp"],
)

studio_cliend = Client(stdio_transport)

async def main   ():


    async with studio_cliend as client:
        response = await client.call_tool(
            "resolve-library-id",
            {
                "libraryName": "fastmcp",
                "query": "I want to create a new MCP server using the fastmcp Python framework"
            }
        
        )

        print(response.content[0].text)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())