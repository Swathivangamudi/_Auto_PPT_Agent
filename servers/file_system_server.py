# File system server
import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("file_system")

@mcp.tool()
def create_file(file_path: str) -> str:
    """
    Create a new empty file.
    """
    try:
        open(file_path, "w").close()
        return f"File created: {file_path}"
    except Exception as e:
        return str(e)


@mcp.tool()
def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file.
    """
    try:
        with open(file_path, "w") as f:
            f.write(content)
        return f"Content written to {file_path}"
    except Exception as e:
        return str(e)


@mcp.tool()
def list_files(folder_path: str) -> str:
    """
    List all files in a folder.
    """
    try:
        return "\n".join(os.listdir(folder_path))
    except Exception as e:
        return str(e)


if __name__ == "__main__":
    mcp.run()