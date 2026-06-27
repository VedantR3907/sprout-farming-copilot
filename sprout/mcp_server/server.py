"""Sprout MCP server.

Exposes the agronomy tools (weather, market prices, soil) over the Model Context
Protocol via stdio. ADK connects to this with ``McpToolset`` (see
``sprout/sub_agents/field_advisor.py``).

Run standalone for debugging:
    python -m sprout.mcp_server.server
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from sprout.mcp_server import tools

mcp = FastMCP("sprout-field-tools")


@mcp.tool()
def get_weather_forecast(latitude: float, longitude: float, days: int = 3) -> dict:
    """Get a daily weather forecast for a farm location (free Open-Meteo, no key).

    Args:
        latitude: Farm latitude in degrees (-90 to 90).
        longitude: Farm longitude in degrees (-180 to 180).
        days: Number of forecast days, 1-7 (default 3).
    """
    return tools.get_weather_forecast(latitude, longitude, days)


@mcp.tool()
def get_market_prices(crop: str) -> dict:
    """Get recent mandi prices (INR/quintal) and a sell/hold hint for a crop.

    Args:
        crop: Crop name, e.g. "wheat", "tomato", "cotton".
    """
    return tools.get_market_prices(crop)


@mcp.tool()
def get_live_mandi_price(commodity: str, state: str = "") -> dict:
    """Get LIVE mandi prices (INR/quintal) from data.gov.in/Agmarknet for a commodity.

    Args:
        commodity: Commodity name, e.g. "Onion", "Tomato", "Wheat".
        state: Optional Indian state to filter by, e.g. "Maharashtra".
    """
    return tools.get_live_mandi_price(commodity, state)


@mcp.tool()
def get_soil_recommendation(crop: str, soil_type: str) -> dict:
    """Get crop+soil suitability notes and basic input guidance.

    Args:
        crop: Crop name, e.g. "rice".
        soil_type: One of sandy, clay, loam, black, red, silt.
    """
    return tools.get_soil_recommendation(crop, soil_type)


@mcp.tool()
def recommend_crop(
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    temperature: float,
    humidity: float,
    ph: float,
    rainfall: float,
) -> dict:
    """Recommend best crops for soil/climate using REAL data (k-NN, 22 crops).

    Args:
        nitrogen: Soil N (kg/ha).
        phosphorus: Soil P (kg/ha).
        potassium: Soil K (kg/ha).
        temperature: Average temperature (°C).
        humidity: Relative humidity (%).
        ph: Soil pH.
        rainfall: Rainfall (mm).
    """
    return tools.recommend_crop(
        nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall
    )


def main() -> None:
    # stdio transport: ADK launches this process and speaks MCP over stdin/stdout.
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
