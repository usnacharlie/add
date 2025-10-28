#!/bin/bash

# Member Registry System - Stop Script

echo "Stopping Member Registry System..."

# Stop backend
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        sleep 2
        # Force kill if still running
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            kill -9 $BACKEND_PID
        fi
        echo "Backend stopped"
    fi
    rm backend.pid
else
    echo "No backend PID file found, trying to find process..."
    pkill -f "python3 main.py" || pkill -f "backend/main.py"
fi

# Stop frontend
if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        sleep 2
        # Force kill if still running
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            kill -9 $FRONTEND_PID
        fi
        echo "Frontend stopped"
    fi
    rm frontend.pid
else
    echo "No frontend PID file found, trying to find process..."
    pkill -f "python3 app.py" || pkill -f "frontend/app.py"
fi

echo "Member Registry System stopped"
