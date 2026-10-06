# Generated Dockerfile for TZeroAlgorithm MCP Server
FROM python:3.11-slim

WORKDIR /app

# Copy dependency specifications and install
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run MCP server on stdio
ENTRYPOINT ["python", "tzero_mcp.py"]
