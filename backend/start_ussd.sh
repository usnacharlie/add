#!/bin/bash

# ADD USSD Gateway Startup Script
# Port: 57023 (External accessible)

cd /var/member/backend

# Activate virtual environment if it exists
if [ -d "venv_ussd" ]; then
    source venv_ussd/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv_ussd
    source venv_ussd/bin/activate
    pip install flask flask-cors redis requests
fi

# Set port via environment variable (default 57023)
export USSD_PORT=57023

echo "Starting ADD USSD Gateway on port $USSD_PORT"
echo "External access: http://31.97.113.202:$USSD_PORT/ussd"
echo "Local access: http://localhost:$USSD_PORT/ussd"
echo ""
echo "Endpoints:"
echo "  - Main USSD: /ussd"
echo "  - Callback:  /ussd/callback"
echo "  - Health:    /health"
echo "  - Sessions:  /sessions"
echo ""
echo "Press Ctrl+C to stop"

# Start the USSD gateway
python ussd_gateway.py