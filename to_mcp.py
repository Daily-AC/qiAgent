from fastmcp import FastMCP
from datetime import datetime
import os
from main import main as qiagent_main
mcp = FastMCP()

@mcp.tool
async def qiAgent(pdf_path: str) -> str:
    return await qiagent_main(pdf_path)

def main():
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000, path = "/mcp")

if __name__ == "__main__":
    main()