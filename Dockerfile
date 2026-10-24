# T-Zero Context Engine MCP Server Dockerfile for Glama and Container Deployments
FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr (crucial for MCP stdio JSON-RPC transport)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_BREAK_SYSTEM_PACKAGES=1 \
    UV_PYTHON=3.11 \
    TZERO_MCP_TOOL_MODE=canonical

WORKDIR /app

# Copy project files
COPY pyproject.toml requirements.txt* uv.lock* uv.toml* ./
COPY . .

# Install package so tzero-mcp is registered on system PATH
RUN pip install --no-cache-dir --break-system-packages .

# Launch T-Zero MCP Server over stdio
ENTRYPOINT ["python", "-u", "tzero_mcp.py", "--stdio"]
