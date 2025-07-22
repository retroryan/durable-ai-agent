#!/usr/bin/env python3
"""
Comprehensive test for all weather tools.
Tests mock responses by default, use --real to test actual API integration.
Outputs only JSON responses.
"""

import json
import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from tools.agriculture.agricultural_weather import AgriculturalWeatherTool
from tools.agriculture.historical_weather import HistoricalWeatherTool
from tools.agriculture.weather_forecast import WeatherForecastTool


def test_historical_weather(use_real=False):
    """Test historical weather tool."""
    # Create tool instance
    tool = HistoricalWeatherTool()

    # Test coordinates (Chicago, IL)
    latitude = 41.8781
    longitude = -87.6298

    # Use dates from 2 weeks ago to 1 week ago (historical data requirement)
    end_date = datetime.now() - timedelta(days=7)
    start_date = end_date - timedelta(days=7)

    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    try:
        result = tool.execute(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date_str,
            end_date=end_date_str,
            mock_answer=not use_real,
        )
        return {"tool": "get_historical_weather", "success": True, "response": result}
    except Exception as e:
        return {"tool": "get_historical_weather", "success": False, "error": str(e)}


def test_weather_forecast(use_real=False):
    """Test weather forecast tool."""
    # Create tool instance
    tool = WeatherForecastTool()

    # Test coordinates (New York City, NY)
    latitude = 40.7128
    longitude = -74.0060
    days = 7

    try:
        result = tool.execute(
            latitude=latitude, longitude=longitude, days=days, mock_answer=not use_real
        )
        return {"tool": "get_weather_forecast", "success": True, "response": result}
    except Exception as e:
        return {"tool": "get_weather_forecast", "success": False, "error": str(e)}


def test_agricultural_weather(use_real=False):
    """Test agricultural weather tool."""
    # Create tool instance
    tool = AgriculturalWeatherTool()

    # Test coordinates (Des Moines, IA - agricultural area)
    latitude = 41.5868
    longitude = -93.6250
    days = 5
    crop_type = "corn"

    try:
        result = tool.execute(
            latitude=latitude,
            longitude=longitude,
            days=days,
            crop_type=crop_type,
            mock_answer=not use_real,
        )
        return {
            "tool": "get_agricultural_conditions",
            "success": True,
            "response": result,
        }
    except Exception as e:
        return {
            "tool": "get_agricultural_conditions",
            "success": False,
            "error": str(e),
        }


def test_all_weather_tools(use_real=False):
    """Test all weather tools and return overall success status."""
    results = []

    # Test all tools
    results.append(test_historical_weather(use_real))
    results.append(test_weather_forecast(use_real))
    results.append(test_agricultural_weather(use_real))

    # Create summary
    summary = {
        "test_run_timestamp": datetime.now().isoformat(),
        "test_mode": "real" if use_real else "mock",
        "total_tests": len(results),
        "passed_tests": sum(1 for r in results if r["success"]),
        "failed_tests": sum(1 for r in results if not r["success"]),
        "results": results,
    }

    print(json.dumps(summary, indent=2, ensure_ascii=False))

    return all(r["success"] for r in results)


if __name__ == "__main__":
    # Check for --real flag
    use_real = "--real" in sys.argv
    success = test_all_weather_tools(use_real)
    sys.exit(0 if success else 1)
