#!/usr/bin/env python
"""
Stop the MCP weather server.

This script gracefully stops the unified MCP weather server running on port 7778.
"""
import subprocess
import sys
import time
import os
import signal

# The single MCP server port
MCP_PORT = 7778

def find_process_by_port(port):
    """Find process ID using a specific port."""
    try:
        # Use lsof to find process listening on the port
        result = subprocess.run(
            ['lsof', '-t', f'-i:{port}'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())
    except Exception as e:
        print(f"Error finding process on port {port}: {e}")
    return None

def kill_process(pid, force=False):
    """Kill a process by PID."""
    try:
        if force:
            os.kill(pid, signal.SIGKILL)
            print(f"  Force killed process {pid}")
        else:
            os.kill(pid, signal.SIGTERM)
            print(f"  Terminated process {pid}")
        return True
    except ProcessLookupError:
        return False
    except Exception as e:
        print(f"  Error killing process {pid}: {e}")
        return False

def main():
    """Stop the MCP weather server."""
    print(f"Checking for MCP weather server on port {MCP_PORT}...")
    
    pid = find_process_by_port(MCP_PORT)
    if pid:
        print(f"Found server (PID: {pid}), stopping...")
        
        # Try graceful termination first
        if kill_process(pid, force=False):
            # Wait a moment for graceful shutdown
            time.sleep(0.5)
            
            # Check if still running
            if find_process_by_port(MCP_PORT):
                print("Process still running, force killing...")
                kill_process(pid, force=True)
                time.sleep(0.5)
        
        # Final check
        if find_process_by_port(MCP_PORT):
            print(f"WARNING: Could not stop server on port {MCP_PORT}")
            sys.exit(1)
        else:
            print("Server stopped successfully")
    else:
        print("No MCP server running")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)