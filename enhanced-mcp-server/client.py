import asyncio
import sys
import json
from urllib.parse import quote
from contextlib import AsyncExitStack

# from fastmcp import Client

from fastmcp import Client
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientResult


class MCPClient:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.client = None
        self.agent = None

       
        self.llm = ChatOllama(
            model="qwen2.5:3b-instruct",
            temperature=0,
        )

    async def connect_to_server(self, server_script_path: str):
        """Connect to MCP server through stdio."""

        if not server_script_path.endswith((".py", ".js", ".ts")):
            raise ValueError(
                "Server script must be a .py, .js, or .ts file"
            )

        print(f"Connecting to server: {server_script_path}")

        self.client =  Client (
            server_script_path,
            elicitation_handler=self.handle_elicitation,
            progress_handler=self.handle_progress,
            message_handler=self.handle_message,
        )

        # Open MCP connection
        await self.exit_stack.enter_async_context(self.client)

        print("Connected to MCP server!")

        # Get the underlying MCP ClientSession
        session = self.client.session

        # LangChain MCP adapter expects ClientSession
        tools = await load_mcp_tools(session)

        print(f"\nLoaded {len(tools)} tools into LangChain.")

        self.agent = create_agent(
            model=self.llm,
            tools=tools,
        )

        print("Agent created successfully!\n")


    async def handle_elicitation(
        self,
        message: str,
        response_type: type,
        params,
        context,
    ):
        """Handle MCP elicitation requests."""

        print(f"\nServer asks: {message}")

        user_data = {}

        for field_name, field_type in response_type.__annotations__.items():

            user_input = input(
                f"Enter value for '{field_name}': "
            ).strip()

            if not user_input:
                return ClientResult(action="decline")

            user_data[field_name] = user_input

        return response_type(**user_data)


    async def handle_progress(
        self,
        progress: float,
        total: float | None,
        message: str | None,
    ):
        """Handle MCP progress notifications."""

        if total is not None:
            percentage = (progress / total) * 100
            print(
                f"Progress: {percentage:.1f}%"
                f" - {message or ''}"
            )
        else:
            print(
                f"Progress: {progress}"
                f" - {message or ''}"
            )

    async def handle_message(self, message):
        """Handle MCP server notifications."""

        if hasattr(message, "root"):
            method = message.root.method
            print(f"\nReceived MCP notification: {method}")

            if method == "notifications/tools/list_changed":
                print("Tools have changed.")

            elif method == "notifications/resources/list_changed":
                print("Resources have changed.")

    async def get_tools(self):
        """Get tools from MCP server."""
        tools = await self.client.list_tools()
        return tools


    async def process_query(self, query: str):
        """Send a query to Qwen agent."""

        if self.agent is None:
            raise RuntimeError(
                "Agent is not initialized. "
                "Connect to the MCP server first."
            )

        print(f"\nUser: {query}")

        response = await self.agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": query,
                    }
                ]
            }
        )

        return response

    async def converse(self):
        """Interactive conversation."""

        print("\n===================================")
        print(" Qwen + MCP Conversation")
        print(" Type 'quit' to exit")
        print("===================================")

        while True:

            query = input("\nYou: ").strip()

            if query.lower() in ("quit", "q"):
                break

            if not query:
                continue

            try:

                response = await self.process_query(query)

                print("\nAgent response:")

                # LangGraph/LangChain agent returns messages
                messages = response.get("messages", [])

                for message in messages:

                    message_type = message.__class__.__name__

                    if message_type == "HumanMessage":

                        print(
                            f"[HUMAN] "
                            f"{message.content}"
                        )

                    elif message_type == "AIMessage":

                        if message.content:
                            print(
                                f"[AI] "
                                f"{message.content}"
                            )

                        # Show tool calls
                        if getattr(
                            message,
                            "tool_calls",
                            None,
                        ):

                            for tool_call in message.tool_calls:

                                print(
                                    f"[TOOL CALL] "
                                    f"{tool_call['name']} "
                                    f"{tool_call['args']}"
                                )

                    elif message_type == "ToolMessage":

                        print(
                            f"[TOOL RESULT] "
                            f"{message.content}"
                        )

                    else:

                        print(
                            f"[{message_type}] "
                            f"{message.content}"
                        )

            except Exception as e:

                print(
                    f"\nError: "
                    f"{type(e).__name__}: {e}"
                )


    async def get_prompts(self):
        return await self.client.list_prompts()

    async def prompt(self, prompt_name: str):

        try:

            prompts = await self.get_prompts()

            prompt_obj = next(
                (
                    p
                    for p in prompts
                    if p.name == prompt_name
                ),
                None,
            )

            if prompt_obj is None:

                print(
                    f"Prompt '{prompt_name}' "
                    f"not found."
                )

                return

            print(
                f"\nPrompt: {prompt_obj.name}"
            )

            arguments = {}

            if prompt_obj.arguments:

                for argument in prompt_obj.arguments:

                    required = (
                        "required"
                        if argument.required
                        else "optional"
                    )

                    value = input(
                        f"{argument.name} "
                        f"({required}): "
                    ).strip()

                    if (
                        not value
                        and argument.required
                    ):

                        print(
                            f"{argument.name} "
                            f"is required."
                        )

                        return

                    if value:

                        arguments[
                            argument.name
                        ] = value

            # Get generated prompt from MCP
            prompt_result = await self.client.get_prompt(
                prompt_name,
                arguments=arguments,
            )

            prompt_text = ""

            for message in prompt_result.messages:

                if hasattr(
                    message.content,
                    "text",
                ):

                    prompt_text += (
                        message.content.text
                    )

            # Send prompt to Qwen
            response = await self.process_query(
                prompt_text
            )

            print("\nResult:")

            for message in response["messages"]:

                if (
                    message.__class__.__name__
                    == "AIMessage"
                ):

                    if message.content:

                        print(
                            message.content
                        )

        except Exception as e:

            print(
                f"Error: "
                f"{type(e).__name__}: {e}"
            )


    async def read_file(self):

        try:

            file_name = input( "Enter file path: ").strip()
            encoded_file_name = quote(file_name,safe="",)

            resource = await self.client.read_resource(
                f"file:///{encoded_file_name}"
            )

            file_content = json.loads(
                resource[0].text
            )["file_content"]

            print("\nFile Content:")
            print("--------------------------------")
            print(file_content)

        except Exception as e:

            print(
                f"Error reading file: "
                f"{type(e).__name__}: {e}"
            )

    async def read_dir(self):

        try:
            resource = await self.client.read_resource("dir://.")
            data = json.loads(resource[0].text)
            items = data["items"]
            print("\nDirectory Listing:")

            for item in items:
                icon = (
                    "📁"
                    if item["type"] == "directory"
                    else "📄"
                )

                print(
                    f"{icon} "
                    f"{item['name']}"
                )


        except Exception as e:
            print(
                f"Error reading directory: "
                f"{type(e).__name__}: {e}"
            )

    async def menu(self):

        while True:

            print(
                """
                ====================================
                            MCP CLIENT
                ====================================

                1. List MCP tools
                2. Generate Documentation
                3. Code Review
                4. Read File
                5. Read Directory
                6. Chat with Qwen Agent
                q. Quit
                """
            )

            choice = input(
                "Select: "
            ).strip()

 
            if choice == "1":
                tools = await self.get_tools()
                print("\nAvailable tools:")
                for tool in tools:
                    print(
                        f"- {tool.name}: "
                        f"{tool.description}"
                    )


            elif choice == "2":
                await self.prompt(
                    "documentation_generator"
                )

            elif choice == "3":
                await self.prompt("code_review" )

       
            elif choice == "4":
                await self.read_file()

            elif choice == "5":
                await self.read_dir()

    
            elif choice == "6":
                await self.converse()

            elif choice.lower() in (
                "q",
                "quit",
            ):
                break
            else:
                print(
                    "Invalid choice."
                )

    async def cleanup(self):
        if self.exit_stack:
            await self.exit_stack.aclose()


async def main():

    if len(sys.argv) < 2:

        print(
            "Usage:"
            "\n"
            "python client.py <server.py>"
        )

        sys.exit(1)

    server_path = sys.argv[1]
    client = MCPClient()
    try:
        await client.connect_to_server( server_path )
        await client.menu()

    except KeyboardInterrupt:
        print("\nClient stopped.")

    except Exception as e:
        print(
            f"\nError: "
            f"{type(e).__name__}: {e}"
        )
    finally:

        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())