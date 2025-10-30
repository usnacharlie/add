#!/bin/bash

# Member Registry System - Startup Script
# This script starts both backend and frontend on bare metal

echo "========================================="
echo "Member Registry System Startup"
echo "========================================="

# Check if PostgreSQL is running
echo "Checking PostgreSQL..."
if ! pg_isready -q; then
    echo "ERROR: PostgreSQL is not running!"
    echo "Please start PostgreSQL first:"
    echo "  sudo service postgresql start    # Ubuntu/Debian"
    echo "  brew services start postgresql   # macOS"
    exit 1
fi

# Check if database exists
echo "Checking database..."
if ! psql -lqt | cut -d \| -f 1 | grep -qw member_registry; then
    echo "Database 'member_registry' not found. Creating..."
    createdb member_registry
    echo "Database created successfully!"
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Ensure upload directories exist
if [ ! -d "frontend/static/uploads/profiles" ]; then
    echo "Creating upload directories..."
    mkdir -p frontend/static/uploads/profiles
    chmod 755 frontend/static/uploads
    chmod 755 frontend/static/uploads/profiles
fi

# Initialize database if needed
echo "Initializing database..."
cd backend
python3 -c "from backend.config.database import init_db; init_db()" 2>/dev/null || echo "Database already initialized"
cd ..

# Start backend in background
echo "Starting FastAPI backend on port 9500..."
cd backend
python3 main.py > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"
cd ..

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:9500/health > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "ERROR: Backend failed to start. Check backend.log for details."
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Start frontend in background
echo "Starting Flask frontend on port 9100..."
cd frontend
python3 app.py > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"
cd ..

# Wait for frontend to be ready
echo "Waiting for frontend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:9100 > /dev/null 2>&1; then
        echo "Frontend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "ERROR: Frontend failed to start. Check frontend.log for details."
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Save PIDs
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

echo ""
echo "========================================="
echo "✓ Member Registry System is running!"
echo "========================================="
echo ""
echo "Frontend:  http://localhost:9100"
echo "Backend:   http://localhost:9500"
echo "API Docs:  http://localhost:9500/docs"
echo ""
echo "Logs:"
echo "  Backend:  tail -f backend.log"
echo "  Frontend: tail -f frontend.log"
echo ""
echo "To stop: ./stop.sh"
echo "========================================="
