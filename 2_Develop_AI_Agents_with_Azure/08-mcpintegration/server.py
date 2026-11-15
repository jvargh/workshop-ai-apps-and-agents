import sys

# Add references
from fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP(name="Inventory")

# Add an inventory check mcp tool
@mcp.tool()
def get_inventory_levels() -> dict:
    """Returns fixed sample inventory for all products."""
    print("[Server tool] Returning sample inventory levels for 10 products.", file=sys.stderr, flush=True)
    return {
        "Moisturizer": 6,
        "Shampoo": 8,
        "Body Spray": 28,
        "Hair Gel": 5, 
        "Lip Balm": 12,
        "Skin Serum": 9,
        "Cleanser": 30,
        "Conditioner": 3,
        "Setting Powder": 17,
        "Dry Shampoo": 45
    }

# Add a weekly sales mcp tool
@mcp.tool()
def get_weekly_sales() -> dict:
    """Returns fixed sample units sold last week for all products."""
    print("[Server tool] Returning sample last-week sales for 10 products.", file=sys.stderr, flush=True)
    return {
        "Moisturizer": 22,
        "Shampoo": 18,
        "Body Spray": 3,
        "Hair Gel": 2,
        "Lip Balm": 14,
        "Skin Serum": 19,
        "Cleanser": 4,
        "Conditioner": 1,
        "Setting Powder": 13,
        "Dry Shampoo": 17
    }

if __name__ == "__main__":
    # Stdout carries MCP protocol messages; diagnostics must use stderr.
    print("[Server] Starting the sample Inventory MCP server over stdio.", file=sys.stderr, flush=True)
    mcp.run(transport="stdio", show_banner=False)