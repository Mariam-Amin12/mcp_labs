
from fastmcp import FastMCP

mcp = FastMCP(
    name="CalculatorMCPServer", 
    instructions="""
        This server provides data analysis tools.
        Call the tools with the appropriate arguments to perform calculations.
    """
)
@mcp.tool
def add(a: int, b: int) -> int:
    """
    Add two integers together.

    Args:
        a (int): The first integer.
        b (int): The second integer.

    Returns:
        int: The sum of `a` and `b`.

    Example:
        >>> add(3, 5)
        8
    """
    return a + b


@mcp.tool
def subtract(a: int, b: int) -> int:
    """
    Subtract one integer from another.

    Args:
        a (int): The number to subtract from.
        b (int): The number to subtract.

    Returns:
        int: The result of `a - b`.

    Example:
        >>> subtract(10, 4)
        6
    """
    return a - b



@mcp.resource("file://endpoint2/{name}")
def read_document(name: str) -> str:
    """Read a document by name from the path directory"""
    try:
        # Read from the actual file system path
        with open(f"path/{name}", "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"Document '{name}' not found in path directory"
    except Exception as e:
        return f"Error reading document: {str(e)}"


@mcp.prompt(title="Code Review")
def review_code(code: str) -> str:
    return f"Please review this code: {code}"

if __name__ == "__main__":
    mcp.run()
    # mcp.run(
    #     transport="http",
    #     host="127.0.0.1",
    #     port=8000,
    # )
