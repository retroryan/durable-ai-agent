🏗️  Durable AI Agent - Chat API Test
============================================================
🔍 Checking services...
✅ API server is running on port 8000

🚀 Starting Weather API Integration Test
📅 Test run at: 2025-07-14 02:12:59
============================================================

📊 Running 9 test cases from AgricultureToolSet
============================================================

📍 Test 1/9: Weather forecast with umbrella recommendation
🎯 Scenario: forecast
🔧 Expected tools: get_weather_forecast
----------------------------------------
Sending: 'weather: What's the weather like in New York and should I bring an umbrella?' from user: test_user_f501264d

Response:
{
  "workflow_id": "durable-agent-b51130c3-ee05-498a-b303-76c2e369f675",
  "status": "completed",
  "query_count": 1,
  "last_response": {
    "message": "Child workflow result: The weather in New York is currently pleasant with a temperature of 20\u00b0C (68\u00b0F), 65% humidity, and no rain. Today's forecast shows clear conditions with a high of 23\u00b0C and no precipitation expected.\n\nHowever, you should definitely bring an umbrella! While today will be dry, light rain is forecast for tomorrow (1.2mm) and moderate rain for the day after (3.5mm). It's better to be prepared for the upcoming wet weather over the next couple of days.",
    "event_count": 1,
    "query_count": 1
  }
}

✅ Success! Workflow ID: durable-agent-b51130c3-ee05-498a-b303-76c2e369f675
🌤️  Weather forecast information detected!

📍 Test 2/9: Basic weather forecast request
🎯 Scenario: forecast
🔧 Expected tools: get_weather_forecast
----------------------------------------
Sending: 'weather: What's the weather forecast for New York City?' from user: test_user_c2a6fdf8

Response:
{
  "workflow_id": "durable-agent-acf182da-3e0d-4895-98cc-6dc5a10ff7f3",
  "status": "completed",
  "query_count": 1,
  "last_response": {
    "message": "Child workflow result: Here's the weather forecast for New York City:\n\n**Current Conditions:**\n- Temperature: 20\u00b0C (68\u00b0F)\n- Humidity: 65%\n- Wind Speed: 10 km/h\n- Precipitation: 0 mm\n\n**3-Day Forecast:**\n- **January 15, 2025**: High 23\u00b0C (73\u00b0F), Low 16\u00b0C (61\u00b0F), No precipitation\n- **January 16, 2025**: High 24\u00b0C (75\u00b0F), Low 17\u00b0C (63\u00b0F), Light rain (1.2mm)\n- **January 17, 2025**: High 22\u00b0C (72\u00b0F), Low 15\u00b0C (59\u00b0F), Moderate rain (3.5mm)\n\nThe weather looks mild with temperatures in the low 20s Celsius. Expect some rain starting tomorrow, with the heaviest precipitation on January 17th.",
    "event_count": 1,
    "query_count": 1
  }
}

✅ Success! Workflow ID: durable-agent-acf182da-3e0d-4895-98cc-6dc5a10ff7f3
🌤️  Weather forecast information detected!

📍 Test 3/9: Weather forecast for international city
🎯 Scenario: forecast
🔧 Expected tools: get_weather_forecast
----------------------------------------
Sending: 'weather: I need the 10-day weather forecast for London' from user: test_user_62c9accc

Response:
{
  "workflow_id": "durable-agent-dd7a0971-d591-48c0-8a78-b0823df7303e",
  "status": "completed",
  "query_count": 1,
  "last_response": {
    "message": "Child workflow result: Here's the 10-day weather forecast for London:\n\n**Current Conditions:**\n- Temperature: 20\u00b0C\n- Humidity: 65%\n- Wind Speed: 10 km/h\n- Precipitation: 0 mm\n\n**Daily Forecast:**\n- January 15, 2025: High 23\u00b0C, Low 16\u00b0C, Precipitation 0mm\n- January 16, 2025: High 24\u00b0C, Low 17\u00b0C, Precipitation 1.2mm\n- January 17, 2025: High 22\u00b0C, Low 15\u00b0C, Precipitation 3.5mm\n\n*Note: The forecast system provided a summary showing the first 3 days of the 10-day forecast period. The complete 10-day forecast data was requested and the system confirmed it covers the full 10-day period as requested.*",
    "event_count": 1,
    "query_count": 1
  }
}

✅ Success! Workflow ID: durable-agent-dd7a0971-d591-48c0-8a78-b0823df7303e
🌤️  Weather forecast information detected!

📍 Test 4/9: Agricultural weather conditions
🎯 Scenario: agriculture
🔧 Expected tools: get_agricultural_conditions
----------------------------------------
Sending: 'weather: What are the agricultural conditions in Des Moines, Iowa?' from user: test_user_11ae04fb

Response:
{
  "workflow_id": "durable-agent-36d3b1dc-7e0f-462d-918a-57dc7a281d0b",
  "status": "completed",
  "query_count": 1,
  "last_response": {
    "message": "Child workflow result: The current agricultural conditions in Des Moines, Iowa show:\n\n**Soil Moisture Levels:**\n- Surface (0-1cm): 25.5% moisture\n- Shallow (1-3cm): 28.2% moisture  \n- Root Zone (3-9cm): 32.1% moisture\n- Deep (9-27cm): 35.8% moisture\n\n**Current Weather Conditions (January 15, 2025):**\n- Temperature range: 16-24\u00b0C (61-75\u00b0F)\n- No precipitation (0mm)\n- Evapotranspiration: 3.2mm\n- Vapor Pressure Deficit: 1.2kPa\n\nThe soil moisture increases with depth, indicating good water retention in deeper soil layers. The moderate evapotranspiration rate and vapor pressure deficit suggest reasonable growing conditions, though the lack of recent precipitation may require monitoring for irrigation needs.",
    "event_count": 1,
    "query_count": 1
  }
}

✅ Success! Workflow ID: durable-agent-36d3b1dc-7e0f-462d-918a-57dc7a281d0b
🌱 Agricultural information detected!

📍 Test 5/9: Agricultural planning query
🎯 Scenario: agriculture
🔧 Expected tools: get_agricultural_conditions
----------------------------------------
Sending: 'weather: Are conditions good for planting corn in Ames, Iowa?' from user: test_user_8733cc48

Response:
{
  "workflow_id": "durable-agent-f7f7268b-7091-4602-ab34-6f4e274a2ebe",
  "status": "completed",
  "query_count": 1,
  "last_response": {
    "message": "Child workflow result: No, conditions are not good for planting corn in Ames, Iowa at this time. While the soil moisture levels (25-36%) and temperatures (20-24\u00b0C) would normally be suitable for corn, we're in mid-July, which is far too late for corn planting in Iowa. Corn should be planted in late April to mid-May to allow sufficient growing time before fall frost. Any corn planted now would not have enough time to mature properly before the growing season ends. If you're planning for next year, the optimal planting window would be late April through mid-May when soil temperatures consistently reach 50\u00b0F (10\u00b0C).",
    "event_count": 2,
    "query_count": 1
  }
}

✅ Success! Workflow ID: durable-agent-f7f7268b-7091-4602-ab34-6f4e274a2ebe
🌱 Agricultural information detected!

📍 Test 6/9: Historical weather data query
🎯 Scenario: historical
🔧 Expected tools: get_historical_weather
----------------------------------------
Sending: 'weather: What was the weather like in San Francisco from 2025-06-07 to 2025-06-14?' from user: test_user_6c371a53

Response:
{
  "workflow_id": "durable-agent-e7e21f96-dc6c-46eb-8cfc-8dcf593c1868",
  "status": "completed",
  "query_count": 1,
  "last_response": {
    "message": "Child workflow result: Based on the historical weather data for San Francisco from June 7-14, 2025:\n\n**Temperature:** Average high of 22\u00b0C (72\u00b0F) and average low of 15\u00b0C (59\u00b0F)\n**Precipitation:** Total of 2.5mm of rain during the week\n**Wind:** Maximum wind speeds reached 15 km/h\n**UV Index:** Maximum UV index of 6\n\nThe weather was generally mild and typical for San Francisco in early June, with moderate temperatures, light precipitation, and gentle winds. It was a relatively pleasant week with comfortable temperatures and minimal rainfall.",
    "event_count": 1,
    "query_count": 1
  }
}

✅ Success! Workflow ID: durable-agent-e7e21f96-dc6c-46eb-8cfc-8dcf593c1868
📊 Historical weather data detected!

📍 Test 7/9: Multi-city weather comparison
🎯 Scenario: comparison
🔧 Expected tools: get_weather_forecast
----------------------------------------
Sending: 'weather: Compare the weather in New York and Los Angeles' from user: test_user_7c49ad7b

Response:
{
  "workflow_id": "durable-agent-454ea339-d8e2-4eb3-8490-d58db94aec1c",
  "status": "completed",
  "query_count": 1,
  "last_response": {
    "message": "Child workflow result: Based on the weather forecasts obtained, both New York and Los Angeles currently show identical weather conditions:\n\n**Current Conditions (both cities):**\n- Temperature: 20\u00b0C\n- Humidity: 65%\n- Wind Speed: 10 km/h\n- No precipitation\n\n**3-Day Forecast (both cities):**\n- January 15: High 23\u00b0C, Low 16\u00b0C, No precipitation\n- January 16: High 24\u00b0C, Low 17\u00b0C, Light precipitation (1.2mm)\n- January 17: High 22\u00b0C, Low 15\u00b0C, Moderate precipitation (3.5mm)\n\nNote: The identical weather data for both cities appears unusual, as New York and Los Angeles typically have significantly different weather patterns due to their different geographic locations and climates.",
    "event_count": 2,
    "query_count": 1
  }
}

✅ Success! Workflow ID: durable-agent-454ea339-d8e2-4eb3-8490-d58db94aec1c
⚖️  Comparison detected!

📍 Test 8/9: Tree farm agricultural conditions
🎯 Scenario: agriculture
🔧 Expected tools: get_agricultural_conditions
----------------------------------------
Sending: 'weather: What are the soil moisture levels at my tree farm in Olympia, Washington?' from user: test_user_f3b52f9d

Response:
{
  "workflow_id": "durable-agent-47a1ef59-9305-40fd-b5bc-098c63c08f0f",
  "status": "completed",
  "query_count": 1,
  "last_response": {
    "message": "Child workflow result: The current soil moisture levels at your tree farm in Olympia, Washington are:\n\n- **Surface layer (0-1cm)**: 25.5% moisture\n- **Shallow layer (1-3cm)**: 28.2% moisture  \n- **Root zone (3-9cm)**: 32.1% moisture\n- **Deep layer (9-27cm)**: 35.8% moisture\n\nThe soil moisture increases with depth, which is typical. The root zone moisture level of 32.1% should be adequate for most tree species, and the deeper soil layers show good moisture retention at 35.8%.",
    "event_count": 1,
    "query_count": 1
  }
}

✅ Success! Workflow ID: durable-agent-47a1ef59-9305-40fd-b5bc-098c63c08f0f
🌱 Agricultural information detected!

📍 Test 9/9: Historical and forecast comparison
🎯 Scenario: comparison
🔧 Expected tools: get_historical_weather, get_weather_forecast
----------------------------------------
Sending: 'weather: Compare the historical weather from 2025-06-14 with the current forecast for Miami' from user: test_user_3fd6f499

Response:
{
  "workflow_id": "durable-agent-dd578a7e-a5e7-4db9-b77f-e5c07cf80185",
  "status": "completed",
  "query_count": 1,
  "last_response": {
    "message": "Child workflow result: Comparing Miami's historical weather from June 14, 2025, with the current forecast:\n\n**Historical Weather (June 14, 2025):**\n- Temperature: High 22\u00b0C, Low 15\u00b0C\n- Precipitation: 2.5mm\n- Wind Speed: 15 km/h (max)\n- UV Index: 6 (max)\n\n**Current Forecast:**\n- Current Temperature: 20\u00b0C\n- Forecast Range: Highs 22-24\u00b0C, Lows 15-17\u00b0C\n- Precipitation: 0-3.5mm (varies by day)\n- Current Wind Speed: 10 km/h\n\n**Comparison:**\nThe historical June 14th weather shows very similar conditions to the current forecast. The historical high of 22\u00b0C matches the lower end of current forecast highs, while the historical low of 15\u00b0C matches the current forecast lows. Precipitation on the historical date (2.5mm) falls within the current forecast range. The main difference is wind speed, which was higher historically (15 km/h) compared to current conditions (10 km/h). Overall, Miami's weather patterns appear quite consistent between these time periods.",
    "event_count": 2,
    "query_count": 1
  }
}

✅ Success! Workflow ID: durable-agent-dd578a7e-a5e7-4db9-b77f-e5c07cf80185
⚖️  Comparison detected!

============================================================
✨ Test completed! Results:
   ✅ Successful: 9/9
   ❌ Failed: 0/9

🎉 All tests passed!
