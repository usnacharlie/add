#!/bin/bash

# Member Registry System - Status Check Script

echo "========================================="
echo "Member Registry System - Status"
echo "========================================="
echo ""

# Check backend
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "✓ Backend:  Running (PID: $BACKEND_PID)"
        if curl -s http://localhost:9500/health > /dev/null 2>&1; then
            echo "  Status:   Healthy"
            echo "  URL:      http://localhost:9500"
        else
            echo "  Status:   Not responding"
        fi
    else
        echo "✗ Backend:  Not running (stale PID file)"
    fi
else
    echo "✗ Backend:  Not running"
fi

echo ""

# Check frontend
if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "✓ Frontend: Running (PID: $FRONTEND_PID)"
        if curl -s http://localhost:9100 > /dev/null 2>&1; then
            echo "  Status:   Healthy"
            echo "  URL:      http://localhost:9100"
        else
            echo "  Status:   Not responding"
        fi
    else
        echo "✗ Frontend: Not running (stale PID file)"
    fi
else
    echo "✗ Frontend: Not running"
fi

echo ""

# Check PostgreSQL
if pg_isready -q 2>/dev/null; then
    echo "✓ PostgreSQL: Running"
    if psql -lqt | cut -d \| -f 1 | grep -qw member_registry 2>/dev/null; then
        echo "  Database: member_registry exists"
    else
        echo "  Database: member_registry NOT found"
    fi
else
    echo "✗ PostgreSQL: Not running"
fi

echo ""
echo "========================================="
echo ""

# Show recent logs if running
if [ -f backend.log ]; then
    echo "Recent backend logs:"
    tail -n 3 backend.log
    echo ""
fi

if [ -f frontend.log ]; then
    echo "Recent frontend logs:"
    tail -n 3 frontend.log
    echo ""
fi

echo "Commands:"
echo "  ./start.sh  - Start the application"
echo "  ./stop.sh   - Stop the application"
echo "  ./status.sh - Check status"
echo ""
