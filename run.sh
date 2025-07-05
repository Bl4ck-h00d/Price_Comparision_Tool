#!/bin/bash

# Price Comparison Tool Runner

echo "=================================="
echo "Price Comparison Tool"
echo "=================================="

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "Docker found. Running with Docker Compose..."
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        echo "Creating .env file..."
        cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
API_PORT=8000
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=30

EOF
        echo "IMPORTANT: Please edit .env file with your OpenAI API key!"
        echo "OpenAI API key is REQUIRED for this tool to work."
    fi
    
    # Check if OpenAI API key is set
    if [ -f .env ]; then
        source .env
        if [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
            echo "WARNING: OpenAI API key is not set in .env file"
            echo "Please set your OpenAI API key in .env file before running"
            exit 1
        fi
    fi
    
    # Run with Docker Compose
    docker-compose up --build
    
elif command -v python3 &> /dev/null; then
    echo "Python found. Running locally..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -r requirements.txt
    
    # Install Playwright browsers
    echo "Installing Playwright browsers..."
    playwright install chromium
    
    # Check if OpenAI API key is set
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "ERROR: OPENAI_API_KEY environment variable is not set"
        echo "Please set your OpenAI API key:"
        echo "export OPENAI_API_KEY='your-api-key-here'"
        exit 1
    fi
    
    # Set environment variables
    export API_PORT="${API_PORT:-8000}"
    export LOG_LEVEL="${LOG_LEVEL:-INFO}"
    export USE_CRAWL4AI="${USE_CRAWL4AI:-true}"
    export USE_OPENAI_RANKING="${USE_OPENAI_RANKING:-true}"
    
    # Run the application
    echo "Starting Price Comparison Tool..."
    python main.py
    
else
    echo "Neither Docker nor Python 3 found. Please install one of them."
    exit 1
fi 