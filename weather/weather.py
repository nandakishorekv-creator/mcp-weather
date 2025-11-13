# Import sys at the top
import sys
from typing import Any
import httpx

# --- DEBUG 1 ---
# This will show up in your logs if the script starts at all
print("--- SCRIPT STARTED (weather.py) ---", file=sys.stderr)

try:
    from mcp.server.fastmcp import FastMCP
    
    # --- DEBUG 2 ---
    print("--- FastMCP IMPORTED ---", file=sys.stderr)

    # Initialize FastMCP server
    mcp = FastMCP("weather")
    
    # --- DEBUG---
    print("--- FastMCP INITIALIZED ---", file=sys.stderr)

except Exception as e:
    # --- DEBUG FAILED ---
    # If it fails here, we know it's an import or init problem
    print(f"--- FAILED ON IMPORT/INIT: {e} ---", file=sys.stderr)
    import time
    time.sleep(10) # Pause so we can read the log
    sys.exit(1) # Exit with an error

# --- Your code (unchanged) ---
#checking git
# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # --- DEBUG ERROR ---
            print(f"--- ERROR IN NWS REQUEST: {e} ---", file=sys.stderr)
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

# --- Your main function (with debug prints) ---

def main():
    # --- DEBUG 4 ---
    print("--- ENTERING main() ---", file=sys.stderr)
    try:
        # Initialize and run the server
        mcp.run(transport='stdio')
    except Exception as e:
        # --- DEBUG FAILED ---
        print(f"--- mcp.run() CRASHED: {e} ---", file=sys.stderr)
        import time
        time.sleep(10) # Pause to read
    
    # --- DEBUG 5 ---
    # We should never see this if the server runs correctly
    print("--- mcp.run() EXITED NORMALLY ---", file=sys.stderr)

if __name__ == "__main__":
    # --- DEBUG 6 ---
    print("--- __name__ == __main__ BLOCK REACHED ---", file=sys.stderr)
    main()
