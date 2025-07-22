#!/usr/bin/env python
"""
Stop MCP servers running on their default ports.

This script attempts to gracefully stop MCP servers and ensures they are
completely shut down by checking the ports.
"""
import subprocess
import sys
import time
import os
import signal

# Define the ports used by MCP servers
MCP_PORTS = {
    'forecast': 7778,
    'historical': 7779,
    'agricultural': 7780,
}

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
    """Main function to stop all MCP servers."""
    print("Stopping MCP servers...")
    
    servers_found = False
    
    for server_name, port in MCP_PORTS.items():
        print(f"\nChecking {server_name} server on port {port}...")
        
        # Find process using the port
        pid = find_process_by_port(port)
        
        if pid:
            servers_found = True
            print(f"  Found {server_name} server (PID: {pid})")
            
            # Try graceful termination first
            if kill_process(pid, force=False):
                # Wait a moment for graceful shutdown
                time.sleep(0.5)
                
                # Check if still running
                if find_process_by_port(port):
                    print(f"  Process still running, force killing...")
                    kill_process(pid, force=True)
                    time.sleep(0.5)
            
            # Final check
            if find_process_by_port(port):
                print(f"  WARNING: Could not stop {server_name} server on port {port}")
            else:
                print(f"  Successfully stopped {server_name} server")
        else:
            print(f"  No {server_name} server found on port {port}")
    
    if servers_found:
        print("\nAll MCP servers have been stopped.")
    else:
        print("\nNo MCP servers were running.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)