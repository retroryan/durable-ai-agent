🏗️  Durable AI Agent - API Endpoints Test
============================================================
🔍 Checking services...
✅ API server is running on port 8000

🚀 Starting API Endpoints Integration Test
📅 Test run at: 2025-07-14 02:13:52
============================================================

🏥 Testing health endpoint...
✅ Health endpoint passed

🏠 Testing root endpoint...
✅ Root endpoint passed

💬 Testing chat endpoint (workflow creation)...
✅ Chat endpoint passed - Workflow ID: durable-agent-d2e53ae4-071d-45eb-b168-2f30507709e4

🔖 Testing chat with specific workflow ID...
✅ Chat with specific workflow ID passed - ID: test-workflow-87de8582-4dcb-42ab-9f36-155a08328f1f

👤 Testing chat with user_name...
✅ Chat with user_name passed - User: test_user_123

📊 Testing workflow status endpoint...
✅ Workflow status endpoint passed - Query count: 0

🔍 Testing workflow query endpoint...
✅ Workflow query endpoint passed - Status: Workflow has processed 1 queries

🚫 Testing non-existent workflow status...
✅ Non-existent workflow status correctly returned 404

⚠️ Testing API error handling...
✅ API error handling passed - correctly returned 422 for invalid data

🌤️ Testing weather: prefix query routing...
✅ Weather prefix query routing passed

📊 Testing historical query routing...
Historical query response preview: sorry anonymous, i encountered an error: getting historical weather: unknown tool: historical_histor...
✅ Historical query routing passed (service not available)

🌱 Testing agriculture query routing...
Agriculture query response preview: hey anonymous! here are the agricultural conditions for central valley, california:

🌡️ current temp...
✅ Agriculture query routing passed

🎯 Testing default query routing...
✅ Default query routing passed

🌦️ Testing multiple weather query formats...
  [1/3] Testing: weather: What's the temperature in Boston?
  ✅ Query 1 passed
  [2/3] Testing: weather: Will it rain tomorrow in Seattle?
  ✅ Query 2 passed
  [3/3] Testing: weather: Give me a 3-day forecast for Miami
  ✅ Query 3 passed
✅ Multiple weather queries passed

============================================================
✨ Test completed! Results:
   ✅ Successful: 14/14
   ❌ Failed: 0/14

🎉 All tests passed!