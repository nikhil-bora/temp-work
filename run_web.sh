#!/bin/bash
# Start FinOps Agent Web UI

echo "🚀 Starting FinOps Agent Web UI..."
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "   Please ensure .env exists with your credentials"
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    echo "   Please install Python 3.8 or higher"
    exit 1
fi

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
fi

# Activate venv
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing dependencies..."
    pip install -q -r requirements.txt

    if [ $? -ne 0 ]; then
        echo "❌ Installation failed"
        exit 1
    fi
fi

echo "✓ Dependencies ready"
echo ""

# Run the web server
python3 web_server.py

# Deactivate venv on exit
deactivate
