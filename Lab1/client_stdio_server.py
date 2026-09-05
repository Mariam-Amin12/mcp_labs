from Lab1.stdio_server import mcp 

from fastmcp import Client


my_local_client = Client(mcp)

async def main():
    async with my_local_client as client:
        response = await client.call_tool(
            "add",
            {
                "a": 10,
                "b": 5
            }
        )
        print(f"Addition Result: {response.content[0].text}")

        response = await client.call_tool(
            "subtract",
            {
                "a": 10,
                "b": 5
            }
        )
        print(f"Subtraction Result: {response.content[0].text}")

    

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 