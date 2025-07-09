import csv
import difflib

from fastmcp import FastMCP, Client
from fastmcp.prompts import PromptMessage
from mcp.types import TextContent, PromptMessage
from starlette.requests import Request
from starlette.responses import JSONResponse

from utilities import geocode_location, get_tide_times

mcp = FastMCP(name="MA Beach Agent", version="0.1.0")

mcp_with_instructions = FastMCP(
    name="MA Beach Agent",
    instructions="This server enables a user to query the status of beaches in Massachusetts."
)

@mcp.prompt(
        name="Beach Status Prompt",
        description="Prompt to request the current status of a beach in Massachusetts.",
        tags={"beach", "status", "massachusetts"},
)
def beach_status_prompt_request(beach_name: str) -> PromptMessage:
    content = f"Please help provide me with the current status of the beach named '{beach_name}' in Massachusetts."
    return PromptMessage(role="user", content=TextContent(type="text", text=content))

@mcp.tool
def specific_beach_closure_tool(beach_name: str) -> str:
    """
    Tool to check if a specific beach in Massachusetts is closed, with fuzzy matching.
    """
    with open('ClosureTable_data.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip header row
        beach_names = []
        rows = []
        for row in reader:
            if row:
                beach_names.append(row[1])
                rows.append(row)
        # Fuzzy match
        matches = difflib.get_close_matches(beach_name, beach_names, n=2, cutoff=0.61)
        if matches:
            closed_list = []
            for matched_name in matches:
                for row in rows:
                    if row[1] == matched_name:
                        reason = row[2] if len(row) > 2 else "No reason provided"
                        closed_list.append(f"{matched_name} (Reason: {reason})")
                        break
            if len(closed_list) == 1:
                return f"The beach {closed_list[0]} is currently closed."
            elif len(closed_list) == 2:
                return f"The beaches {closed_list[0]} and {closed_list[1]} are currently closed."
            elif len(closed_list) > 2:
                return f"The beaches {', '.join(closed_list)} are currently closed."
        return f"The beach '{beach_name}' appears to be open."

@mcp.tool
def all_beach_closure_tool() -> str:
    """
    Tool to check the status of all beaches in Massachusetts.
    """
    closed_beaches = []
    with open('ClosureTable_data.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip the header row
        for row in reader:
            closed_beaches.append(row[1] + " in " + row[0])  # Assuming the first column is the beach name and the second is the status
    
    return f"The following beaches are currently closed: {', '.join(closed_beaches)}."

@mcp.tool
async def location_to_geocode_tool(location: str) -> str:
    """
    Tool to convert a location name provided as a string to latitude and longitude.
    """
    loc = location.strip()

    coords = await geocode_location(loc)
    if coords:
        lat, lon = coords
        return f"Coordinates for '{loc}': Latitude {lat}, Longitude {lon}"
    return f"Error retrieving coordinates for '{location}': Location not found."

@mcp.tool
async def tide_time_acquisition_tool(lat: float, lon: float) -> str:
    """
    Tool to acquire tide times for a given latitude and longitude. Send the latitude and longitude as floats to the Marea API.
    """
    data = await get_tide_times(lat, lon)
    if data:
        tide_times = data.get("extremes", [])
        heights = data.get("heights", [])
        return f"Tide times for location ({lat}, {lon}): {tide_times}, Heights: {heights}"
    return f"Error retrieving tide data for location ({lat}, {lon}): No data found."

@mcp.resource("file://ClosureTable_data.csv", name="Beach Closure Data", description="CSV file containing the closure status of beaches in Massachusetts.")
def beach_closure_data_resource() -> str:
    """
    Resource to provide the closure data of beaches in Massachusetts.
    """
    return "Beach Closure Data is available at 'mcp-one/Closure Table_data.csv'."

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy"})

if __name__ == "__main__":
    mcp.run()