


from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

client = MultiServerMCPClient(
    {
        "stdio-client": {
            "command": "python",
            "args": ["stdio_server.py"],
            "transport": "stdio"
        },
        "http-client": {
            "url": f"http://127.0.0.1:8000/mcp",
            "transport": "streamable_http"
        }
    }
)
ollama_llm = ChatOllama(
    model="qwen2.5:3b-instruct",
    temperature=0,
)

async def main():
    tools = await client.get_tools()

    for tool in tools:
        print(f"Tool: {tool.name}")
        print(f"Description: {tool.description}")
        
        print()

    model = create_agent(
        tools=tools,
        model=ollama_llm

    )
    response = await model.ainvoke(
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

    for i in response['messages']:
        if isinstance(i, HumanMessage):
            message_type = "HUMAN"
        elif isinstance(i, AIMessage):
            message_type = "AI"
        elif isinstance(i, ToolMessage):
            message_type = "TOOL"
        else:
            message_type = "OTHER"

        if i.content == '':
            i.content = "tool call"
        
        print(f"[{message_type}] {i.content}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())