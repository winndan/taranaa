# app.py
from fastapi import FastAPI
from mcp_server import get_mcp

# Create the FastAPI application
app = FastAPI()

# Get the MCP application
subapi = get_mcp()  # This should return a FastAPI application

print(dir(subapi))
# Optionally define more routes
