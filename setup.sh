#!/bin/bash

# Setup script for Order Management MCP Integration

echo "==================================="
echo "Order Management MCP Setup"
echo "==================================="
echo ""

# Check if we're in the project root
if [ ! -d "order_management_mcp" ] || [ ! -d "backend" ]; then
    echo "Error: Please run this script from the OmniHelp project root directory"
    exit 1
fi

# Setup MCP Server
echo "Setting up MCP Server..."
cd order_management_mcp

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment for MCP server..."
    python3 -m venv venv
fi

echo "Installing MCP server dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt
deactivate

echo "✓ MCP Server setup complete"
echo ""

# Setup Backend
echo "Setting up Backend..."
cd ../backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment for backend..."
    python3 -m venv venv
fi

echo "Installing backend dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt
# chromadb installed without deps: its onnxruntime dep has no Python 3.15 wheels and is unused here
pip install -q --no-deps -r requirements-chroma.txt
deactivate

echo "✓ Backend setup complete"
echo ""

# Check environment files
cd ..
if [ ! -f "backend/.env" ]; then
    echo "⚠ Warning: backend/.env not found. Please create it with required settings."
fi

if [ ! -f "order_management_mcp/.env" ]; then
    echo "⚠ Warning: order_management_mcp/.env not found. Using defaults."
fi

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "To run the system:"
echo ""
echo "Terminal 1 - Start MCP Server:"
echo "  cd order_management_mcp"
echo "  source venv/bin/activate"
echo "  python -m order_management_mcp"
echo ""
echo "Terminal 2 - Start Backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python -m app.main"
echo ""
echo "Then visit: http://localhost:8000/health"
echo ""
