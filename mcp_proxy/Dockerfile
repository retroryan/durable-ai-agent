# Simple Dockerfile for MCP Proxy demo
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_proxy/ ./mcp_proxy/

# Expose port
EXPOSE 8000

# Run the simple proxy server
CMD ["python", "-m", "mcp_proxy.simple_proxy"]