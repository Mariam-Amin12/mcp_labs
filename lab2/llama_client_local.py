import asyncio


from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from mcp import ClientSession, StdioServerParameters, stdio_client
from fastmcp.client.transports import StdioTransport
server_param = StdioServerParameters(
    command="python",  
    args=["stdio_server.py"],
)

llm = ChatOllama(
    model="qwen2.5:3b-instruct",
    temperature=0,
)


async def main():

    async with stdio_client(server_param) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            print("Connected to MCP server!")

            tools = await load_mcp_tools(session)

            print(
                "Available tools:",
                [tool.name for tool in tools]
            )

            agent = create_agent(
                model=llm,
                tools=tools,
            )

            response = await agent.ainvoke(
                 {"messages": "Use the add tool to add 2 and 1 ."}
            )

            print("\nAgent response:")
            print(response["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())