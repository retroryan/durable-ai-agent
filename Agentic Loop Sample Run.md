🏗️  Durable AI Agent - AI Tools Endpoint Test
============================================================
🔍 Checking services...
✅ API server is running on port 8000

🚀 Starting AI Tools Endpoint Integration Test
📅 Test run at: 2025-07-14 02:07:53
============================================================

🌽 Testing crop query: 'weather: Are conditions good for planting corn in Ames, Iowa?'
============================================================
🔤 User: test_user_27ba6d4a

1️⃣ Sending initial message...
✅ Workflow started: durable-agent-9ff22d6e-ae7a-4a3f-be3f-aad3bc44b0fa
📄 Initial response: {
  "workflow_id": "durable-agent-9ff22d6e-ae7a-4a3f-be3f-aad3bc44b0fa",
  "status": "completed",
  "query_count": 1,
  "last_response": {
    "message": "Child workflow result: No, conditions are not good for planting corn in Ames, Iowa at this time. While the soil moisture levels (25-36%) and temperatures (20-24\u00b0C) would normally be suitable for corn, we're in mid-July, which is far too late for corn planting in Iowa. Corn should be planted in late April to mid-May to allow sufficient growing time before fall frost. Any corn planted now would not have enough time to mature properly before the growing season ends. If you're planning for next year, the optimal planting window would be late April through mid-May when soil temperatures consistently reach 50\u00b0F (10\u00b0C).",
    "event_count": 2,
    "query_count": 1
  }
}

⏳ Waiting for workflow to process...

2️⃣ Querying AI trajectory early (after 3 seconds)...
📍 Early trajectory snapshot:
{
  "observation_0": "Agricultural Conditions for 42.0308, -93.6319\nLocation: Agricultural location at 42.0308, -93.6319 (corn farming)\nForecast Period: 7 days\n\nCurrent Soil Conditions:\n- Surface (0-1cm): 25.5% moisture\n- Shallow (1-3cm): 28.2% moisture\n- Root Zone (3-9cm): 32.1% moisture\n- Deep (9-27cm): 35.8% moisture\n\nDaily Agricultural Summary:\n- 2025-01-15:\n  Temperature: 24/16\u00b0C\n  Precipitation: 0mm\n  Evapotranspiration: 3.2mm\n  Vapor Pressure Deficit: 1.2kPa",
  "observation_1": "Weather Forecast for 42.0308, -93.6319\nLocation: Location at 42.0308, -93.6319\nForecast Period: 7 days\n\nCurrent Conditions:\n- Temperature: 20\u00b0C\n- Humidity: 65%\n- Wind Speed: 10 km/h\n- Precipitation: 0 mm\n\nDaily Forecast Summary:\n- 2025-01-15: High 23\u00b0C, Low 16\u00b0C, Precipitation 0mm\n- 2025-01-16: High 24\u00b0C, Low 17\u00b0C, Precipitation 1.2mm\n- 2025-01-17: High 22\u00b0C, Low 15\u00b0C, Precipitation 3.5mm",
  "observation_2": "Completed.",
  "thought_0": "The user is asking about planting conditions for corn in Ames, Iowa. To answer this question, I need to get agricultural conditions for that location. First, I need to extract the coordinates for Ames, Iowa. From my knowledge, Ames, Iowa is located at approximately latitude 42.0308 and longitude -93.6319. I'll use the get_agricultural_conditions tool with the crop_type specified as corn to get relevant agricultural weather data.",
  "thought_1": "I have received agricultural conditions data for Ames, Iowa with corn-specific information. The data shows current soil moisture levels and a daily summary. However, I notice the date shown is 2025-01-15, which seems to be winter conditions, but the current date is 2025-07-14 (mid-July). This is actually good timing for corn planting assessment since corn is typically planted in spring (April-May) and we're now in mid-summer growing season. Let me also get the current weather forecast to provide a more complete picture of planting conditions, as the agricultural data might be showing historical or projected data that doesn't align with the current date.",
  "thought_2": "I have gathered both agricultural conditions and weather forecast data for Ames, Iowa. However, I notice there's a discrepancy in the dates - the data shows January 2025 dates while the current date is July 14, 2025. This is concerning because corn planting timing is crucial. In Iowa, corn is typically planted in late April to mid-May when soil temperatures reach 50\u00b0F (10\u00b0C) consistently. Since we're in mid-July, we're well past the optimal planting window for corn in Iowa. The current season would be mid-growing season for corn that was planted in spring. I have enough information to provide a comprehensive answer about corn planting conditions in Ames, Iowa, considering both the agricultural data and the timing context.",
  "tool_args_0": {
    "crop_type": "corn",
    "days": 7,
    "latitude": 42.0308,
    "longitude": -93.6319
  },
  "tool_args_1": {
    "days": 7,
    "latitude": 42.0308,
    "longitude": -93.6319
  },
  "tool_args_2": {},
  "tool_name_0": "get_agricultural_conditions",
  "tool_name_1": "get_weather_forecast",
  "tool_name_2": "finish"
}

3️⃣ Querying AI tools endpoint for child workflow: agentic-ai-weather-durable-agent-9ff22d6e-ae7a-4a3f-be3f-aad3bc44b0fa

🔧 Tools used in workflow:
{
  "workflow_id": "agentic-ai-weather-durable-agent-9ff22d6e-ae7a-4a3f-be3f-aad3bc44b0fa",
  "tools_used": [
    "get_agricultural_conditions",
    "get_weather_forecast"
  ],
  "tool_count": 2
}

4️⃣ Querying full AI state with trajectory...

📊 AI Workflow State:
   Status: completed
   Query Count: 1
   Current Iteration: 3
   Execution Time: 0.14s
   Tools Used: get_agricultural_conditions, get_weather_forecast

📍 Final Trajectory:

   Iteration 0:
   💭 Thought: The user is asking about planting conditions for corn in Ames, Iowa. To answer this question, I need to get agricultural conditions for that location. First, I need to extract the coordinates for Ames, Iowa. From my knowledge, Ames, Iowa is located at approximately latitude 42.0308 and longitude -93.6319. I'll use the get_agricultural_conditions tool with the crop_type specified as corn to get relevant agricultural weather data.
   🔧 Tool: get_agricultural_conditions
   📝 Args: {"crop_type": "corn", "days": 7, "latitude": 42.0308, "longitude": -93.6319}
   👁️  Observation: Agricultural Conditions for 42.0308, -93.6319
Location: Agricultural location at 42.0308, -93.6319 (corn farming)
Forecast Period: 7 days

Current Soil Conditions:
- Surface (0-1cm): 25.5% moisture
- ...

   Iteration 1:
   💭 Thought: I have received agricultural conditions data for Ames, Iowa with corn-specific information. The data shows current soil moisture levels and a daily summary. However, I notice the date shown is 2025-01-15, which seems to be winter conditions, but the current date is 2025-07-14 (mid-July). This is actually good timing for corn planting assessment since corn is typically planted in spring (April-May) and we're now in mid-summer growing season. Let me also get the current weather forecast to provide a more complete picture of planting conditions, as the agricultural data might be showing historical or projected data that doesn't align with the current date.
   🔧 Tool: get_weather_forecast
   📝 Args: {"days": 7, "latitude": 42.0308, "longitude": -93.6319}
   👁️  Observation: Weather Forecast for 42.0308, -93.6319
Location: Location at 42.0308, -93.6319
Forecast Period: 7 days

Current Conditions:
- Temperature: 20°C
- Humidity: 65%
- Wind Speed: 10 km/h
- Precipitation: 0...

   Iteration 2:
   💭 Thought: I have gathered both agricultural conditions and weather forecast data for Ames, Iowa. However, I notice there's a discrepancy in the dates - the data shows January 2025 dates while the current date is July 14, 2025. This is concerning because corn planting timing is crucial. In Iowa, corn is typically planted in late April to mid-May when soil temperatures reach 50°F (10°C) consistently. Since we're in mid-July, we're well past the optimal planting window for corn in Iowa. The current season would be mid-growing season for corn that was planted in spring. I have enough information to provide a comprehensive answer about corn planting conditions in Ames, Iowa, considering both the agricultural data and the timing context.
   🔧 Tool: finish
   📝 Args: {}
   👁️  Observation: Completed.

📊 Total tools used: 2
📋 Tools: get_agricultural_conditions, get_weather_forecast
✅ Agricultural weather tool was used!
   - get_agricultural_conditions
✅ Weather forecast tool was used!
   - get_weather_forecast

5️⃣ Getting final parent workflow status...

📊 Parent Workflow State:
   Workflow ID: durable-agent-9ff22d6e-ae7a-4a3f-be3f-aad3bc44b0fa
   Status: completed
   Query Count: 0

📋 Parent Workflow Details:
   Event Count: 0

✅ Test completed successfully!