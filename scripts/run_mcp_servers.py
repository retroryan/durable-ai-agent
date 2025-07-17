#!/usr/bin/env python
import subprocess
import signal
import sys
import time

processes = []

def signal_handler(sig, frame):
    print('\nStopping all servers...')
    for p in processes:
        p.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print('Starting all MCP servers...')
print('Forecast server on http://localhost:7778/mcp')
print('Historical server on http://localhost:7779/mcp')
print('Agricultural server on http://localhost:7780/mcp')
print('')
print('Press Ctrl+C to stop all servers')

try:
    # Start all servers
    processes.append(subprocess.Popen(['python', 'mcp_servers/forecast_server.py']))
    time.sleep(0.5)
    processes.append(subprocess.Popen(['python', 'mcp_servers/historical_server.py']))
    time.sleep(0.5)
    processes.append(subprocess.Popen(['python', 'mcp_servers/agricultural_server.py']))
    
    # Wait for all processes
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    pass