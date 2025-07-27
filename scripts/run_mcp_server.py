#!/usr/bin/env python
"""Start the unified MCP weather server."""
import subprocess
import signal
import sys

process = None

def signal_handler(sig, frame):
    print('\nStopping server...')
    if process:
        process.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print('Starting MCP Weather Server...')
print('Server running on http://localhost:7778/mcp')
print('Available tools:')
print('  - get_weather_forecast')
print('  - get_historical_weather')
print('  - get_agricultural_conditions')
print('\nPress Ctrl+C to stop')

try:
    process = subprocess.Popen(['python', '-m', 'mcp_servers.agricultural_server'])
    process.wait()
except KeyboardInterrupt:
    pass