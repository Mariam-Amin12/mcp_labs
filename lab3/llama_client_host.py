import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_ollama import ChatOllama
from langchain.agents import create_agent


PORT = 8000

# Local Qwen model running with Ollama
llm = ChatOllama(
    model="qwen2.5:3b-instruct",
    temperature=0,
)


async def main():

    # Connect to the MCP server
    async with streamable_http_client(
        f"http://127.0.0.1:{PORT}/mcp"
    ) as (read, write, _session_id):

        # Create MCP session
        async with ClientSession(read, write) as session:

            # Initialize MCP connection
            await session.initialize()

            print("Connected to MCP server!")

            # Get tools from MCP server
            tools = await load_mcp_tools(session)

            print(
                "Available tools:",
                [tool.name for tool in tools]
            )

            # Create LangGraph agent
            agent = create_agent(
                model=llm,
                tools=tools,
            )

            # Give the agent a task
            response = await agent.ainvoke(
                {
                    "messages": [
                        (
                            "user",
                            "Use the add tool to add 2 and 1. "
                            "Tell me the result and tell me "
                            "whether you used a tool."
                        )
                    ]
                }
            )

            # Print final answer
            print("\nAgent response:")
            print(response["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())