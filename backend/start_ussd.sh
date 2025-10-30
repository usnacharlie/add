#!/bin/bash

# Alliance for Democracy and Development (ADD)
# Member Registry System - USSD Service Startup Script
# Port: 57023 (External accessible)

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../backend/venv" ]; then
    source ../backend/venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
fi

# Set port via environment variable (default 57023)
export USSD_PORT=${USSD_PORT:-57023}
export DATABASE_URL=${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/member_registry}

echo "========================================="
echo "ADD Member Registry - USSD Service"
echo "========================================="
echo ""
echo "Starting USSD Service on port $USSD_PORT"
echo ""
echo "Access URLs:"
echo "  External: http://31.97.113.202:$USSD_PORT/ussd"
echo "  Local:    http://localhost:$USSD_PORT/ussd"
echo ""
echo "Endpoints:"
echo "  - Main USSD:    POST /ussd"
echo "  - Callback:     POST /ussd/callback"
echo "  - Health:       GET  /health"
echo "  - Sessions:     GET  /sessions"
echo "  - Clear Cache:  POST /clear-cache"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================="
echo ""

# Start the USSD service
python3 ussd_service.py