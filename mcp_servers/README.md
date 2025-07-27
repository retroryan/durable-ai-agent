# MCP Weather Server

A unified Model Context Protocol (MCP) server providing weather and agricultural data through the OpenMeteo API.

## Overview

This server provides three weather-related tools via a single MCP server:
- **get_weather_forecast** - Real-time and predictive weather data
- **get_historical_weather** - Historical weather patterns and trends
- **get_agricultural_conditions** - Farm-specific conditions and growing data

All tools are exposed through a single server running on port 7778, with proper Pydantic validation for type safety and AWS Bedrock compatibility.

## Quick Start

### 1. Start the Server

```bash
# Using the convenience script
poetry run python scripts/run_mcp_server.py

# Or run directly
poetry run python -m mcp_servers.agricultural_server
```

The server will start on `http://localhost:7778/mcp` with all three tools available.

### 2. Check Server Health

```bash
curl http://localhost:7778/health
```

Response:
```json
{
  "status": "healthy",
  "service": "weather-server",
  "tools": ["get_weather_forecast", "get_historical_weather", "get_agricultural_conditions"],
  "mock_mode": false
}
```

### 3. Stop the Server

```bash
poetry run python scripts/stop_mcp_server.py
```

## Running Tests

### Integration Tests

The integration tests verify all server functionality including Pydantic validation:

```bash
# Start the server first
poetry run python scripts/run_mcp_server.py

# In another terminal, run tests
poetry run python integration_tests/test_mcp_connections.py
```

The tests verify:
- All three tools are discoverable
- Pydantic model validation works correctly
- String-to-float coordinate conversion (AWS Bedrock compatibility)
- Validation error handling
- Performance differences between location names and coordinates

### Sample Client

A demonstration client showing proper Pydantic usage:

```bash
# Ensure server is running, then:
poetry run python mcp_servers/sample_pydantic_client.py
```

## Tools Documentation

### 1. get_weather_forecast

Get weather forecast for a location.

**Request Model**: `ForecastRequest`
```python
{
    "location": "Chicago, IL",  # Optional if coordinates provided
    "latitude": 41.8781,        # Optional, preferred for performance
    "longitude": -87.6298,      # Optional, preferred for performance
    "days": 7                   # 1-16 days (default: 7)
}
```

**Performance Tip**: Providing latitude/longitude is ~6x faster than location name (avoids geocoding).

### 2. get_historical_weather

Get historical weather data for a date range.

**Request Model**: `HistoricalRequest`
```python
{
    "location": "Seattle",
    "latitude": 47.6062,        # Optional, preferred
    "longitude": -122.3321,     # Optional, preferred
    "start_date": "2024-01-01", # YYYY-MM-DD format
    "end_date": "2024-01-07"    # Must be after start_date
}
```

### 3. get_agricultural_conditions

Get agricultural weather conditions including soil moisture and evapotranspiration.

**Request Model**: `AgriculturalRequest`
```python
{
    "location": "Iowa",
    "latitude": 42.0,           # Optional, preferred
    "longitude": -93.5,         # Optional, preferred
    "days": 7,                  # 1-7 days (default: 7)
    "crop_type": "corn"         # Optional crop specification
}
```

## Pydantic Models

All request models are defined in `models/mcp_models.py`:

- **LocationInput** - Base model with coordinate/location validation
- **ForecastRequest** - Weather forecast parameters
- **HistoricalRequest** - Historical weather query parameters
- **AgriculturalRequest** - Agricultural conditions parameters

### Key Features

1. **Automatic Type Conversion**: Handles string coordinates from AWS Bedrock
   ```python
   # These strings will be converted to floats automatically
   request = ForecastRequest(latitude="41.8781", longitude="-87.6298")
   ```

2. **Validation**: Range checking and business logic
   - Latitude: -90 to 90
   - Longitude: -180 to 180
   - Date ordering validation
   - At least one location method required

3. **Error Messages**: Clear validation feedback
   ```
   Either location name or coordinates (latitude, longitude) required
   Latitude must be between -90 and 90, got 91.0
   End date must be after start date
   ```




## Environment Variables

- `MCP_SERVER_URL` - Server URL (default: `http://localhost:7778/mcp`)
- `MOCK_WEATHER` - Enable mock mode for testing (default: `false`)
- `MCP_HOST` - Host to bind to (default: `127.0.0.1`, `0.0.0.0` in Docker)
- `MCP_PORT` - Port to bind to (default: `7778`)

## Docker Usage

Build and run the server in Docker:

```bash
# Build
docker build -f docker/Dockerfile.mcp -t weather-mcp .

# Run
docker run -p 7778:7778 weather-mcp

# Or use docker-compose
docker-compose up mcp-server
```

## Architecture

```
mcp_servers/
├── agricultural_server.py    # Main server exposing all tools
├── utils/
│   ├── weather_utils.py     # Core implementation logic
│   └── api_client.py        # OpenMeteo API client
├── mock_weather_utils.py    # Mock data for testing
└── sample_pydantic_client.py # Example client implementation
```

The server uses:
- **FastMCP** for the MCP protocol implementation
- **Pydantic** for request validation and type safety
- **httpx** for async HTTP requests to OpenMeteo
- **Starlette** for HTTP transport

## Troubleshooting

### Server Won't Start
- Check if port 7778 is already in use: `lsof -i :7778`
- Ensure all dependencies are installed: `poetry install`

### Import Errors
- Run as module: `python -m mcp_servers.agricultural_server`
- Or use the script: `poetry run python scripts/run_mcp_server.py`

### Connection Refused
- Verify server is running: `curl http://localhost:7778/health`
- Check firewall settings if accessing remotely

### Validation Errors
- Ensure you're using the correct Pydantic models from `models.mcp_models`
- Wrap models in `{"request": model.model_dump()}` when calling tools
- Check date formats (YYYY-MM-DD) and coordinate ranges

## Performance Tips

1. **Use Coordinates**: Directly providing latitude/longitude is ~6x faster than location names
2. **Connection Pooling**: Use MCPClientManager for connection reuse
3. **Mock Mode**: Enable MOCK_WEATHER=true for testing without API calls
4. **Batch Requests**: The OpenMeteo API supports batching for multiple locations

## Development

### Adding New Tools

1. Define the Pydantic model in `models/mcp_models.py`
2. Add the implementation in `utils/weather_utils.py`
3. Expose via `@server.tool` decorator in `agricultural_server.py`
4. Update tests and documentation

### Running in Development

```bash
# With auto-reload
poetry run python -m mcp_servers.agricultural_server --reload

# With debug logging
LOG_LEVEL=DEBUG poetry run python -m mcp_servers.agricultural_server
```

## License

This project is part of the Temporal Durable AI Agent demo and follows the same license terms.